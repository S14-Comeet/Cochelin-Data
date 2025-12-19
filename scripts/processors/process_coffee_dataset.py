"""
coffee_clean.csv 데이터셋을 처리하여 beans 관련 CSV 생성

사용법:
    python process_coffee_dataset.py

필요한 환경변수:
    GMS_KEY 또는 OPENAI_API_KEY: API 키

출력 파일:
    - data/beans.csv: 원두 기본 정보 (farm, variety, processing 포함)
    - data/bean_flavor_notes.csv: 원두-향미 매핑
    - data/bean_scores.csv: 원두별 맛 점수
"""

import os
import json
import time
import getpass
from pathlib import Path
from typing import Optional

import pandas as pd

# LangChain import
try:
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    print("Warning: langchain 패키지가 설치되지 않았습니다.")
    print("pip install langchain langchain-openai")


# ============================================================================
# 설정
# ============================================================================

DATA_DIR = Path(__file__).parent / 'data'
INPUT_FILE = DATA_DIR / 'beans' / 'coffee_clean.csv'
SAVE_INTERVAL = 10  # 중간 저장 간격
DEFAULT_ROASTERY_ID = 1  # 임의의 로스터리 ID (DB에 해당 ID의 더미 데이터가 있어야 함)

# 로스팅 레벨 매핑 (Coffee Review → 우리 스키마) - 1:1 매핑
ROAST_MAPPING = {
    'Light': 'LIGHT',
    'Medium-Light': 'LIGHT',
    'Medium': 'MEDIUM',
    'Medium-Dark': 'HEAVY',
    'Dark': 'HEAVY',
}

# GPT 프롬프트에 필요한 컬럼 (토큰 비용 절감)
REQUIRED_COLUMNS = ['name', 'roaster', 'origin', 'roast', 'desc_1', 'desc_3',
                    'rating', 'aroma', 'acid', 'body', 'flavor', 'aftertaste']

# 랜덤 샘플링 개수
SAMPLE_SIZE = 1000

# 원두 이름으로 부적절한 키워드 (영어)
INVALID_NAME_KEYWORDS = [
    'Roasting', 'Roaster', 'Roasters', 'Coffee Co', 'Coffee Company',
    'Cafe', 'Café', 'Espresso Bar', 'Trading', 'Import', 'Imports',
]

# 커피 생산 국가 목록 (다중 국가 블렌드 필터링용)
COFFEE_COUNTRIES = [
    'Ethiopia', 'Kenya', 'Colombia', 'Guatemala', 'Brazil', 'Costa Rica',
    'Panama', 'Peru', 'Honduras', 'El Salvador', 'Rwanda', 'Burundi',
    'Indonesia', 'Yemen', 'Mexico', 'Nicaragua', 'Uganda', 'Tanzania',
    'Thailand', 'Vietnam', 'India', 'Papua New Guinea', 'Ecuador', 'Bolivia',
    'Congo', "Hawai'i", 'Hawaii', 'Jamaica', 'China', 'Myanmar',
]


# ============================================================================
# Flavor 데이터 (RAG용) - flavors_rag.json에서 로드
# ============================================================================

def load_flavors_rag():
    """flavors_rag.json에서 향미 데이터 로드"""
    rag_path = Path(__file__).parent / 'flavors_rag.json'
    with open(rag_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_flavor_prompt_from_rag() -> str:
    """RAG JSON에서 GPT 프롬프트 생성 (계층 구조 + 키워드 포함)"""
    rag_data = load_flavors_rag()
    flavors = rag_data['flavors']
    profiles = rag_data['profiles']

    prompt = """## 향미(Flavor) 데이터 - SCA Coffee Flavor Wheel 기반

### 중요 규칙:
1. 가장 구체적인 레벨(Level 3 소분류)을 우선 선택
2. 자식 flavor를 선택하면 부모는 자동 포함되므로 부모는 선택하지 말 것
3. 예: "블루베리" 향이면 10103(BLUEBERRY)만 선택, 101(BERRY)나 1(FRUITY)는 선택하지 않음
4. keywords 필드의 단어가 원두 설명에 있으면 해당 flavor 선택

### Level 3 (소분류) - 우선 선택:
"""

    # Level 3 먼저 출력
    for f in flavors:
        if f['level'] == 3:
            keywords = ', '.join(f.get('keywords', []))
            prompt += f"- ID {f['id']}: {f['name']} ({f['code']}) - keywords: [{keywords}]\n"

    prompt += "\n### Level 2 (중분류) - 구체적인 소분류가 없을 때만:\n"
    for f in flavors:
        if f['level'] == 2:
            keywords = ', '.join(f.get('keywords', []))
            children = f.get('children', [])
            if children:
                prompt += f"- ID {f['id']}: {f['name']} ({f['code']}) - keywords: [{keywords}] (하위: {children})\n"
            else:
                prompt += f"- ID {f['id']}: {f['name']} ({f['code']}) - keywords: [{keywords}]\n"

    prompt += "\n### Level 1 (대분류) - 사용하지 말 것 (너무 일반적):\n"
    for f in flavors:
        if f['level'] == 1:
            prompt += f"- ID {f['id']}: {f['name']} ({f['code']})\n"

    prompt += "\n### 국가/품종/가공법별 일반적인 향미 프로파일 (참고용):\n"
    for key, profile in profiles.items():
        if key != "_description":
            prompt += f"- {key}: {profile['description']} → {profile['typical_flavors']}\n"

    return prompt


# ============================================================================
# LangChain + GMS API 처리 함수
# ============================================================================

def setup_langchain():
    """LangChain 설정 (GMS API)"""
    if not os.environ.get("OPENAI_API_KEY"):
        gms_key = os.environ.get("GMS_KEY")
        if gms_key:
            os.environ["OPENAI_API_KEY"] = gms_key
        else:
            os.environ["OPENAI_API_KEY"] = getpass.getpass("GMS KEY를 입력하세요: ")

    os.environ["OPENAI_API_BASE"] = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"

    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    return model


def process_bean_with_langchain(model, row: dict) -> Optional[dict]:
    """LangChain으로 원두 정보 정제 및 flavor 매칭"""

    flavor_context = get_flavor_prompt_from_rag()

    prompt = f"""다음 커피 원두 정보를 분석하고, JSON 형식으로 정제된 데이터를 반환해주세요.

원두 정보:
- 로스터리: {row['roaster']}
- 이름: {row['name']}
- 원산지: {row['origin']}
- 로스팅: {row['roast']}
- 향미 설명: {row['desc_1']}
- 추가 설명: {row.get('desc_3', '')}

{flavor_context}

다음 JSON 형식으로 응답해주세요:
{{
    "skip": false,
    "name": "원두 이름 (한국어, 예: 에티오피아 예가체프 첼베사)",
    "country": "원산지 국가 (한글, 예: 에티오피아)",
    "farm": "농장명 또는 스테이션 (한글, 없으면 null)",
    "variety": "품종 (영어 원어, 예: Gesha, Bourbon, Typica, Robusta ,Liberica 없으면 null)",
    "processing_method": "가공 방식 (영어, 예: Washed, Natural, Anaerobic, 없으면 null)",
    "flavor_ids": [해당 원두의 특성에 맞는 flavor ID들 선택 - Level 3 소분류 우선!]
}}

### 중요:
- name, country는 반드시 **한국어**로 작성하세요. (영어인 경우 한국어 발음으로 음역)
- farm, variety, processing_method는 반드시 **영어 원어**로 작성하세요.
- farm, variety, processing_method 정보가 명시되어 있지 않으면 null로 설정
- flavor_ids는 desc_1, desc_3의 향미 설명을 기반으로 가장 구체적인 Level 3 (5자리 ID)를 우선 선택
- 부모 ID는 선택하지 말 것 (예: 블루베리면 10103만, 101이나 1은 선택 안함)

### 스킵 규칙 (skip: true로 설정):
- 원두 이름이 원산지, 품종, 가공법, 농장 등 **커피 특성**을 반영하지 않고,
  로스터리가 임의로 붙인 **마케팅/브랜딩 네임**인 경우 스킵
- 예시: "Morning Glory", "Velvet Dream", "Signature Blend", "House Special", "Founder's Choice"
- 이런 경우 {{"skip": true}} 만 반환

JSON만 응답해주세요."""

    try:
        messages = [
            SystemMessage(content="당신은 스페셜티 커피 전문가입니다. 원두의 특성을 분석하고 적절한 향미 프로파일을 매칭합니다."),
            HumanMessage(content=prompt)
        ]

        response = model.invoke(messages)
        result_text = response.content

        # JSON 파싱 (```json ... ``` 형식 처리)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0]
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0]

        result = json.loads(result_text.strip())

        # 마케팅/브랜딩 네임인 경우 스킵
        if result.get('skip', False):
            return None

        # flavor_ids 검증 (비어있으면 스킵)
        if not result.get('flavor_ids') or len(result['flavor_ids']) == 0:
            return None

        return result

    except Exception as e:
        print(f"\n  GPT 처리 오류: {e}")
        return None


# ============================================================================
# 메인 함수
# ============================================================================

def main():
    print("=" * 60)
    print("Coffee Dataset 처리")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)

    # 1. 데이터 로드 및 전처리
    print(f"\n[1/4] 데이터 로드: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"  - 전체: {len(df)}개")

    # with_milk 컬럼 제거
    if 'with_milk' in df.columns:
        df = df.drop(columns=['with_milk'])
        print(f"  - with_milk 컬럼 제거")

    # 결측치 제거 (사용하는 컬럼 기준)
    dropna_cols = ['roast', 'aroma', 'acid', 'body', 'flavor', 'aftertaste', 'desc_1', 'desc_3']
    before_dropna = len(df)
    df = df.dropna(subset=[col for col in dropna_cols if col in df.columns])
    print(f"  - 결측치 제거: {before_dropna}개 → {len(df)}개")

    # 필요한 컬럼만 유지 (토큰 비용 절감)
    available_cols = [col for col in REQUIRED_COLUMNS if col in df.columns]
    df = df[available_cols]
    print(f"  - 필요 컬럼만 유지: {len(available_cols)}개 컬럼")

    # Blend 제외
    df = df[~df['name'].str.contains('Blend', case=False, na=False)]
    print(f"  - Blend 제외 후: {len(df)}개")

    # 다중 국가 블렌드 제외 - 국가명이 2개 이상 포함된 경우
    def is_multi_country(origin):
        if pd.isna(origin):
            return False
        count = sum(1 for country in COFFEE_COUNTRIES if country in origin)
        return count >= 2

    df = df[~df['origin'].apply(is_multi_country)]
    print(f"  - 다중 국가 제외 후: {len(df)}개")

    # 부적절한 이름 키워드 제외 (1차 필터링)
    pattern = '|'.join(INVALID_NAME_KEYWORDS)
    df = df[~df['name'].str.contains(pattern, case=False, na=False)]
    print(f"  - 부적절한 이름 제외 후: {len(df)}개")

    # 랜덤 샘플링 (토큰 비용 절감)
    if len(df) > SAMPLE_SIZE:
        df = df.sample(n=SAMPLE_SIZE, random_state=42)
        print(f"  - 랜덤 샘플링: {SAMPLE_SIZE}개")

    # 2. LangChain 설정
    print("\n[2/4] GPT-4o-mini 설정...")

    if not HAS_LANGCHAIN:
        print("  LangChain 패키지가 없어 스킵합니다.")
        print("  pip install langchain langchain-openai")
        return

    model = setup_langchain()

    # 3. 처리
    print("\n[3/4] 원두 정보 처리 중...")

    # 이전 처리 결과 로드 (이어서 처리)
    beans_path = DATA_DIR / 'beans.csv'
    bean_flavor_path = DATA_DIR / 'bean_flavor_notes.csv'
    bean_scores_path = DATA_DIR / 'bean_scores.csv'
    processed_path = DATA_DIR / 'processed_indices.json'

    beans_processed = []
    bean_flavor_notes = []
    bean_scores = []
    processed_indices = set()

    if processed_path.exists():
        with open(processed_path, 'r') as f:
            processed_indices = set(json.load(f))
        print(f"  [이어서 처리] 이미 처리된 원두: {len(processed_indices)}개")

        # 기존 CSV 로드
        if beans_path.exists():
            existing_beans = pd.read_csv(beans_path)
            beans_processed = existing_beans.to_dict('records')
        if bean_flavor_path.exists():
            existing_flavors = pd.read_csv(bean_flavor_path)
            bean_flavor_notes = existing_flavors.to_dict('records')
        if bean_scores_path.exists():
            existing_scores = pd.read_csv(bean_scores_path)
            bean_scores = existing_scores.to_dict('records')

    skipped_count = 0

    for idx, row in df.iterrows():
        # 이미 처리된 원두는 스킵
        if idx in processed_indices:
            continue

        print(f"  처리 중: {len(processed_indices)+1}/{len(df)} - {row['name'][:40]}...", end='\r')

        result = process_bean_with_langchain(model, row.to_dict())

        if result is None:
            skipped_count += 1
            processed_indices.add(idx)
            continue

        # 1. Roastery 처리 - 고정 ID 사용
        roastery_id = DEFAULT_ROASTERY_ID

        # 2. Bean 처리 - 데이터셋의 roast 값을 1:1 매핑
        roast_original = row.get('roast', 'Medium-Light')
        roasting_level = ROAST_MAPPING.get(roast_original, 'MEDIUM')

        bean_id = len(beans_processed) + 1

        beans_processed.append({
            "id": bean_id,
            "roastery_id": roastery_id,
            "name": result.get('name', row['name']),
            "country": result.get('country', ''),
            "farm": result.get('farm', ''),
            "variety": result.get('variety', ''),
            "processing_method": result.get('processing_method', ''),
            "roasting_level": roasting_level,
        })

        # 점수 저장
        bean_scores.append({
            "bean_id": bean_id,
            "rating": row.get('rating', None),
            "aroma": row.get('aroma', None),
            "acidity": row.get('acid', None),
            "body": row.get('body', None),
            "flavor": row.get('flavor', None),
            "aftertaste": row.get('aftertaste', None),
        })

        # flavor 매핑
        for flavor_id in result.get('flavor_ids', []):
            bean_flavor_notes.append({
                "bean_id": bean_id,
                "flavor_id": flavor_id,
            })

        processed_indices.add(idx)

        # 중간 저장
        if len(processed_indices) % SAVE_INTERVAL == 0:
            pd.DataFrame(beans_processed).to_csv(beans_path, index=False, encoding='utf-8-sig')
            pd.DataFrame(bean_flavor_notes).to_csv(bean_flavor_path, index=False, encoding='utf-8-sig')
            pd.DataFrame(bean_scores).to_csv(bean_scores_path, index=False, encoding='utf-8-sig')
            with open(processed_path, 'w') as f:
                json.dump(list(processed_indices), f)
            print(f"\n  [중간 저장] {len(beans_processed)}개 원두 처리됨")

        # Rate limiting
        time.sleep(0.3)

    print(f"\n  - {len(beans_processed)}개 원두 처리 완료 (스킵: {skipped_count}개)")

    # processed_indices 파일 삭제 (완료 시)
    if processed_path.exists():
        processed_path.unlink()

    # 4. CSV 저장
    print("\n[4/4] CSV 파일 저장...")

    beans_df = pd.DataFrame(beans_processed)
    beans_df.to_csv(beans_path, index=False, encoding='utf-8-sig')
    print(f"  - {beans_path}")

    bean_flavor_df = pd.DataFrame(bean_flavor_notes)
    bean_flavor_df.to_csv(bean_flavor_path, index=False, encoding='utf-8-sig')
    print(f"  - {bean_flavor_path}")

    bean_scores_df = pd.DataFrame(bean_scores)
    bean_scores_df.to_csv(bean_scores_path, index=False, encoding='utf-8-sig')
    print(f"  - {bean_scores_path}")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"\n결과 요약:")
    print(f"  - beans.csv: {len(beans_processed)}개 원두")
    print(f"  - bean_flavor_notes.csv: {len(bean_flavor_notes)}개 매핑")
    print(f"  - bean_scores.csv: {len(bean_scores)}개 점수")
    print(f"  - 스킵된 원두: {skipped_count}개")


if __name__ == '__main__':
    main()
