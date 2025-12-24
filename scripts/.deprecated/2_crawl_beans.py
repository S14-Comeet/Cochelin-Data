"""
unspecialty.com에서 원두 데이터 크롤링 + GPT-4o로 flavor 매칭

사용법:
    python crawl_beans.py

필요한 환경변수:
    GMS_KEY 또는 OPENAI_API_KEY: API 키

출력 파일:
    - data/beans_raw.json: 크롤링한 원시 데이터
    - data/beans.csv: schema에 맞게 정제된 원두 데이터
    - data/bean_flavor_notes.csv: 원두-향미 매핑 데이터
"""

import os
import json
import time
import getpass
from pathlib import Path
from typing import Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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

DATA_DIR = Path(__file__).parent.parent / 'data'
MAX_BEANS = 500  # 최대 수집할 원두 수
SCROLL_PAUSE = 2  # 스크롤 후 대기 시간

# 데이터 관리용 roastery ID (roasteries.csv의 마지막 ID + 1 또는 0)
DATA_ROASTERY_ID = 0  # 나중에 업데이트

# 유효한 국가 목록 (국가명 없으면 스킵용)
VALID_COUNTRIES = [
    'Ethiopia', 'Colombia', 'Kenya', 'Panama', 'Guatemala', 'Costa Rica',
    'Brazil', 'Honduras', 'Peru', 'Rwanda', 'Burundi', 'Yemen', 'Indonesia',
    'El Salvador', 'Nicaragua', 'Mexico', 'Bolivia', 'Ecuador', 'Tanzania',
    'Uganda', 'Malawi', 'Papua New Guinea', 'India', 'Vietnam', 'Myanmar',
    'Thailand', 'China', 'Taiwan', 'Hawaii', 'Jamaica', 'Puerto Rico',
    'Democratic Republic of Congo', 'Congo', 'Geisha', 'Sumatra', 'Java',
]

# ============================================================================
# Flavor 데이터 (RAG용) - flavors_rag.json에서 로드
# ============================================================================

def load_flavors_rag():
    """flavors_rag.json에서 향미 데이터 로드"""
    rag_path = Path(__file__).parent.parent / 'data' / 'debug' / 'flavors_rag.json'
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
# 크롤링 함수
# ============================================================================

def create_driver():
    """Selenium 드라이버 생성"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)


def is_valid_country(country: str) -> bool:
    """유효한 국가명인지 확인"""
    country_lower = country.lower()
    for valid in VALID_COUNTRIES:
        if valid.lower() == country_lower or valid.lower() in country_lower:
            return True
    return False


def parse_bean_card(card_text: str) -> Optional[dict]:
    """
    원두 카드 텍스트를 파싱

    예시 입력:
    "warning Ethiopia Benti Nenka ETHIOPIAN LANDRACE WASHED
    Sey Coffee
    add
    위시리스트
    done
    마셔봤어요"
    """
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]

    if len(lines) < 2:
        return None

    # 첫 줄: warning {Country} {Farm} {Variety} {Process}
    first_line = lines[0]
    if first_line.startswith('warning'):
        first_line = first_line[7:].strip()

    # 두 번째 줄: 로스터리 이름
    roastery = lines[1] if len(lines) > 1 else ""

    # 파싱 시도: 국가명 추출 (대문자로 시작)
    parts = first_line.split()
    if not parts:
        return None

    # 첫 단어가 국가명일 가능성 높음
    country = parts[0] if parts else ""

    # 국가명 유효성 검사
    if not is_valid_country(country):
        return None

    # 나머지에서 품종과 가공법 추출 (대문자 단어들)
    remaining = ' '.join(parts[1:]) if len(parts) > 1 else ""

    # 일반적인 가공법 키워드
    process_keywords = ['WASHED', 'NATURAL', 'HONEY', 'ANAEROBIC', 'FERMENTED', 'WET', 'DRY', 'SEMI-WASHED']
    process = ""
    for kw in process_keywords:
        if kw in remaining.upper():
            process = kw
            break

    # 가공법이 없으면 스킵 (향미 추정이 어려움)
    if not process:
        return None

    # 품종 추출 (가공법 제외한 대문자 단어들)
    variety_parts = []
    for word in remaining.split():
        if word.upper() not in process_keywords and word.isupper():
            variety_parts.append(word)
    variety = ' '.join(variety_parts) if variety_parts else ""

    # 농장/이름 (대문자가 아닌 부분)
    farm_parts = []
    for word in remaining.split():
        if not word.isupper():
            farm_parts.append(word)
    farm = ' '.join(farm_parts) if farm_parts else ""

    return {
        "raw_text": first_line,
        "country": country,
        "farm": farm,
        "variety": variety,
        "processing_method": process,
        "roastery": roastery,
    }


def crawl_beans(max_beans: int = MAX_BEANS, save_interval: int = 50) -> list:
    """unspecialty.com에서 원두 데이터 크롤링 (중간 저장 지원)"""
    print(f"\n[크롤링 시작] 최대 {max_beans}개 원두 수집 (매 {save_interval}개마다 저장)")

    beans_raw_path = DATA_DIR / 'beans_raw.json'
    driver = create_driver()
    beans = []
    skipped = 0
    last_saved = 0

    try:
        driver.get('https://community.unspecialty.com/bean/search')
        time.sleep(5)  # 초기 로딩

        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 50

        while len(beans) < max_beans and scroll_attempts < max_scroll_attempts:
            # 현재 카드들 수집
            cards = driver.find_elements(By.CSS_SELECTOR, 'mat-card')

            for card in cards:
                try:
                    text = card.text
                    if not text:
                        continue

                    parsed = parse_bean_card(text)
                    if parsed:
                        # 중복 체크 (raw_text 기준)
                        if not any(b['raw_text'] == parsed['raw_text'] for b in beans):
                            beans.append(parsed)
                    else:
                        skipped += 1

                except Exception:
                    continue

            print(f"  수집: {len(beans)}개 / 스킵: {skipped}개", end='\r')

            # 중간 저장 (save_interval 개마다)
            if len(beans) >= last_saved + save_interval:
                with open(beans_raw_path, 'w', encoding='utf-8') as f:
                    json.dump(beans, f, ensure_ascii=False, indent=2)
                last_saved = len(beans)
                print(f"\n  [중간 저장] {len(beans)}개 저장됨")

            # 더 이상 새로운 데이터가 없으면 종료
            if len(beans) == last_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                last_count = len(beans)

            # 스크롤 다운
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)

            if len(beans) >= max_beans:
                break

        print(f"\n[크롤링 완료] 수집: {len(beans)}개 / 스킵: {skipped}개")

    finally:
        driver.quit()
        # 종료 시에도 저장
        if beans:
            with open(beans_raw_path, 'w', encoding='utf-8') as f:
                json.dump(beans, f, ensure_ascii=False, indent=2)
            print(f"  [최종 저장] {len(beans)}개")

    return beans[:max_beans]


# ============================================================================
# LangChain + GMS API 처리 함수
# ============================================================================

def setup_langchain():
    """LangChain 설정 (GMS API)"""
    # GMS API 설정
    if not os.environ.get("OPENAI_API_KEY"):
        gms_key = os.environ.get("GMS_KEY")
        if gms_key:
            os.environ["OPENAI_API_KEY"] = gms_key
        else:
            os.environ["OPENAI_API_KEY"] = getpass.getpass("GMS KEY를 입력하세요: ")

    # GMS BASE URL 설정
    os.environ["OPENAI_API_BASE"] = "https://gms.ssafy.io/gmsapi/api.openai.com/v1"

    model = init_chat_model("gpt-5-mini", model_provider="openai")
    return model


def process_bean_with_langchain(model, bean: dict) -> Optional[dict]:
    """LangChain으로 원두 정보 정제 및 flavor 매칭"""

    flavor_context = get_flavor_prompt_from_rag()

    prompt = f"""다음 커피 원두 정보를 분석하고, JSON 형식으로 정제된 데이터를 반환해주세요.

원두 정보:
- 원문: {bean['raw_text']}
- 국가: {bean['country']}
- 농장: {bean['farm']}
- 품종: {bean['variety']}
- 가공법: {bean['processing_method']}
- 로스터리: {bean['roastery']}

{flavor_context}

다음 JSON 형식으로 응답해주세요:
{{
    "name": "원두 이름 (한국어, 예: 에티오피아 벤티 넨카)",
    "country": "원산지 국가 (한글, 예: 에티오피아)",
    "country_en": "원산지 국가 (영문, 예: Ethiopia)",
    "farm": "농장명",
    "variety": "품종명",
    "processing_method": "가공법 (WASHED, NATURAL, HONEY 등)",
    "roasting_levels": ["적합한 로스팅 레벨들 - LIGHT, MEDIUM, HEAVY 중 선택"],
    "flavor_ids": [해당 원두의 특성에 맞는 flavor ID 3-5개 선택 - Level 3 소분류 우선!]
}}

### 중요:
- name은 반드시 한국어로 작성 (농장명, 지역명 등 모두 한국어 음역)
- flavor_ids는 가장 구체적인 Level 3 (5자리 ID)를 우선 선택
- 부모 ID는 선택하지 말 것 (예: 블루베리면 10103만, 101이나 1은 선택 안함)
- 정보가 부족하면 국가/품종/가공법 프로파일 참고
- roasting_levels 판단 기준:
  - 이 원두가 라이트 로스팅 전용 원두가 아니라면 여러 로스팅 레벨을 배열에 포함
  - 밝은 산미와 과일향이 특징인 원두 → LIGHT 포함
  - 균형잡힌 바디감과 단맛이 어울리는 원두 → MEDIUM 포함
  - 초콜릿, 견과류 향이 어울리는 바디감 강한 원두 → HEAVY 포함
  - 대부분의 원두는 ["LIGHT", "MEDIUM"] 또는 ["LIGHT"] 선택
  - Natural/Honey 가공은 MEDIUM도 잘 어울림

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
    print("원두 데이터 수집 및 처리")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)

    # 1. 크롤링
    beans_raw_path = DATA_DIR / 'beans_raw.json'

    if beans_raw_path.exists():
        print(f"\n[1/3] 기존 크롤링 데이터 로드: {beans_raw_path}")
        with open(beans_raw_path, 'r', encoding='utf-8') as f:
            beans_raw = json.load(f)
        print(f"  - {len(beans_raw)}개 원두 로드됨")
    else:
        print("\n[1/3] 원두 크롤링 시작...")
        beans_raw = crawl_beans(MAX_BEANS)

        with open(beans_raw_path, 'w', encoding='utf-8') as f:
            json.dump(beans_raw, f, ensure_ascii=False, indent=2)
        print(f"  - 저장됨: {beans_raw_path}")

    # 2. LangChain 처리
    print("\n[2/3] GPT-4o-mini로 원두 정보 정제 및 flavor 매칭...")

    if not HAS_LANGCHAIN:
        print("  LangChain 패키지가 없어 스킵합니다.")
        print("  pip install langchain langchain-openai")
        return

    model = setup_langchain()

    # 이전 처리 결과 로드 (이어서 처리)
    beans_path = DATA_DIR / 'beans.csv'
    bean_flavor_path = DATA_DIR / 'bean_flavor_notes.csv'
    processed_path = DATA_DIR / 'processed_indices.json'

    beans_processed = []
    bean_flavor_notes = []
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

    skipped_count = 0
    save_interval = 10  # 10개마다 중간 저장

    for i, bean in enumerate(beans_raw):
        # 이미 처리된 원두는 스킵
        if i in processed_indices:
            continue

        print(f"  처리 중: {i+1}/{len(beans_raw)} - {bean['raw_text'][:40]}...", end='\r')

        result = process_bean_with_langchain(model, bean)

        if result is None:
            skipped_count += 1
            processed_indices.add(i)
            continue

        # roasting_levels 배열 처리 - 각 로스팅 레벨별로 별도 row 생성
        roasting_levels = result.get('roasting_levels', ['LIGHT'])
        if not isinstance(roasting_levels, list):
            roasting_levels = [roasting_levels]

        # 각 로스팅 레벨별로 별도의 bean row 생성
        bean_ids_for_this_result = []
        for roasting_level in roasting_levels:
            bean_id = len(beans_processed) + 1
            bean_ids_for_this_result.append(bean_id)

            beans_processed.append({
                "id": bean_id,
                "roastery_id": DATA_ROASTERY_ID,
                "name": result.get('name', bean['raw_text']),
                "country": result.get('country', bean['country']),
                "farm": result.get('farm', bean['farm']),
                "variety": result.get('variety', bean['variety']),
                "processing_method": result.get('processing_method', bean['processing_method']),
                "roasting_level": roasting_level,
            })

        # flavor 매핑 - 각 bean_id에 동일한 flavor_ids 적용
        for bean_id in bean_ids_for_this_result:
            for flavor_id in result.get('flavor_ids', []):
                bean_flavor_notes.append({
                    "bean_id": bean_id,
                    "flavor_id": flavor_id,
                })

        processed_indices.add(i)

        # 중간 저장 (save_interval 개마다)
        if len(processed_indices) % save_interval == 0:
            pd.DataFrame(beans_processed).to_csv(beans_path, index=False, encoding='utf-8-sig')
            pd.DataFrame(bean_flavor_notes).to_csv(bean_flavor_path, index=False, encoding='utf-8-sig')
            with open(processed_path, 'w') as f:
                json.dump(list(processed_indices), f)
            print(f"\n  [중간 저장] {len(beans_processed)}개 처리됨")

        # Rate limiting
        time.sleep(0.3)

    print(f"\n  - {len(beans_processed)}개 원두 처리 완료 (스킵: {skipped_count}개)")

    # processed_indices 파일 삭제 (완료 시)
    if processed_path.exists():
        processed_path.unlink()

    # 3. CSV 저장
    print("\n[3/3] CSV 파일 저장...")

    beans_df = pd.DataFrame(beans_processed)
    beans_path = DATA_DIR / 'beans.csv'
    beans_df.to_csv(beans_path, index=False, encoding='utf-8-sig')
    print(f"  - {beans_path}")

    bean_flavor_df = pd.DataFrame(bean_flavor_notes)
    bean_flavor_path = DATA_DIR / 'bean_flavor_notes.csv'
    bean_flavor_df.to_csv(bean_flavor_path, index=False, encoding='utf-8-sig')
    print(f"  - {bean_flavor_path}")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"\n결과 요약:")
    print(f"  - beans.csv: {len(beans_processed)}개 원두")
    print(f"  - bean_flavor_notes.csv: {len(bean_flavor_notes)}개 매핑")
    print(f"  - 스킵된 원두: {skipped_count}개 (국가명/가공법/향미 정보 부족)")


if __name__ == '__main__':
    main()
