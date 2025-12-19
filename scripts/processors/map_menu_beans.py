"""
메뉴-원두 매핑 스크립트 v2

매핑 전략:
1. 가게 description에서 국가명 추출 → 그 가게의 전체 메뉴에 해당 국가 대표 원두 매핑
2. 메뉴명에 원두 정보(국가/지역/품종)가 있으면 더 정확한 개별 매핑
3. 국가별 대표 원두 + 세부 키워드 매칭으로 적절한 원두 선택
"""

import pandas as pd
import re
from pathlib import Path

# 경로 설정
DATA_DIR = Path(__file__).parent / "data"
STORES_DIR = DATA_DIR / "stores"
BEANS_DIR = DATA_DIR / "beans"


# === 국가별 대표 원두 사전 ===
# 각 국가의 default 원두 ID와 키워드별 원두 ID
# 키워드가 매칭되면 해당 원두를, 아니면 default 원두 사용

COUNTRY_BEANS = {
    "에티오피아": {
        "default": [4, 36, 68],  # 구지 함벨라, 예가체프 내추럴, 구지
        "구지": [4, 29, 33, 56, 66],  # 구지 관련 원두들
        "예가체프": [36, 42, 70, 156, 204],  # 예가체프 관련
        "시다모": [65, 81, 128, 337],  # 시다모 관련 (65: 시다마 74110)
        "시다마": [65, 81, 128, 337],
        "함벨라": [4, 30, 167, 305],  # 함벨라 관련
        "하라르": [585],
        "하라": [585],
        "게이샤": [4, 36],  # 에티오피아 게이샤는 일반적이지 않으므로 default
        "게샤": [4, 36],
    },
    "콜롬비아": {
        "default": [1, 11, 85],  # 플라나다스, 안티오키아, 산 페드로
        "게이샤": [94, 168, 215, 301, 321],  # 게이샤 품종
        "게샤": [25, 50, 52, 346, 412],  # 게샤 품종
        "핑크": [63, 150, 252, 401],  # 핑크 부르봉
        "부르봉": [63, 719, 969],
        "나리뇨": [301],  # 나리뇨 지역
    },
    "케냐": {
        "default": [2, 28, 47],  # 키안두, 투이킷 AA, 키리니아가
        "AA": [28, 83, 86],  # AA 등급
        "피베리": [2, 71],  # 피베리
    },
    "과테말라": {
        "default": [5, 9, 10],  # 5a 포니엔테, 발렌톤, 캄파멘토 알토
        "안티구아": [77],  # 안티구아 지역 (77: 안티구아 5a 수르)
        "아카테낭고": [87],  # 아카테낭고
        "파카마라": [13, 37, 87],  # 파카마라 품종
    },
    "코스타리카": {
        "default": [18, 44, 62],  # 타라주, 아네로빅, 루이스 캄포스
        "타라주": [18, 149, 653, 701],
        "아네로빅": [44, 62, 885],
        "게이샤": [39, 149],  # 볼칸 아줄 게이샤, 타라주 게이샤
        "게샤": [39, 149],
    },
    "파나마": {
        "default": [31, 32, 79],  # 에스메랄다, 부에노스 아이레스 게이샤, 핀카 라스 누베스
        "게이샤": [32, 79, 84],
        "게샤": [32, 79, 84],
        "에스메랄다": [31, 32],
        "보케테": [84],  # 엘리다 에스테이트
    },
    "인도네시아": {
        "default": [17, 46, 185],  # 가요 아체, 수마트라 아체 가요, 케린치
        "수마트라": [17, 46, 185, 193, 273],
        "만델링": [752],
        "자바": [898],
        "아체": [17, 46, 839],
        "가요": [17, 46, 839],
    },
    "하와이": {
        "default": [20, 41, 43],  # 코나 락틱, 코나 모카, 코나 내추럴스
        "코나": [20, 41, 43, 75],
    },
    "브라질": {
        "default": [38, 113, 289],  # 레드 카투아이, 세라도
        "세라도": [289],
        "카투아이": [38],
    },
    "르완다": {
        "default": [22, 74, 97, 98],  # 니루지사, 키부 벨트, 칸주, 르완다
    },
    "페루": {
        "default": [35, 93],  # 피우라, 파스코
        "게이샤": [93],
        "게샤": [93],
    },
    "에콰도르": {
        "default": [7, 60, 91],  # 크루즈 로마, 라 호세피나, 라 호르미가
    },
    "엘살바도르": {
        "default": [16, 40, 92],  # 마리오 아길라, 파카마라, 핀카 라스 두아나스
        "파카마라": [40, 92],
    },
    "온두라스": {
        "default": [12],  # 허니 온두라스 콤사
    },
    "예멘": {
        "default": [127, 354],  # 예멘 원두 IDs (확인 필요)
        "모카": [127],
    },
    "멕시코": {
        "default": [14, 59],  # 알투라, 게이샤 베라크루즈
        "게이샤": [59],
        "게샤": [59],
    },
    "니카라과": {
        "default": [37],  # 미에리쉬 핀카
    },
    "베트남": {
        "default": [799],  # 베트남 로부스타
    },
    "부룬디": {
        "default": [131, 333],
    },
    "타이완": {
        "default": [78],  # 올루링 센트
    },
}

# 국가명 변형 처리 (변형 -> 정규화된 이름)
COUNTRY_ALIASES = {
    # 에티오피아
    "에디오피아": "에티오피아",
    "이디오피아": "에티오피아",
    "예가체프": "에티오피아",
    "예가체페": "에티오피아",
    "이르가체프": "에티오피아",
    "시다모": "에티오피아",
    "시다마": "에티오피아",
    "구지": "에티오피아",
    "굿지": "에티오피아",
    "하라": "에티오피아",
    "하라르": "에티오피아",
    "함벨라": "에티오피아",

    # 인도네시아
    "수마트라": "인도네시아",
    "만델링": "인도네시아",
    "자바": "인도네시아",
    "발리": "인도네시아",
    "술라웨시": "인도네시아",
    "토라자": "인도네시아",
    "아체": "인도네시아",
    "가요": "인도네시아",

    # 코스타리카
    "코스타 리카": "코스타리카",
    "코스타리까": "코스타리카",
    "타라주": "코스타리카",

    # 과테말라
    "안티구아": "과테말라",
    "아카테낭고": "과테말라",

    # 케냐
    "케니아": "케냐",

    # 콜롬비아
    "콜럼비아": "콜롬비아",
    "나리뇨": "콜롬비아",

    # 파나마
    "보케테": "파나마",

    # 브라질
    "브라질리안": "브라질",
    "세라도": "브라질",

    # 하와이
    "코나": "하와이",

    # 엘살바도르
    "엘 살바도르": "엘살바도르",

    # 예멘
    "모카": "예멘",
}

# beans.csv에 있는 실제 국가명 목록
BEAN_COUNTRIES = list(COUNTRY_BEANS.keys())


def load_data():
    """데이터 로드"""
    stores = pd.read_csv(STORES_DIR / "stores_final.csv")
    menus = pd.read_csv(STORES_DIR / "menus.csv")
    beans = pd.read_csv(BEANS_DIR / "beans.csv")

    print(f"Loaded: {len(stores)} stores, {len(menus)} menus, {len(beans)} beans")
    return stores, menus, beans


def normalize_country(text):
    """국가명/지역명을 정규화된 국가명으로 변환"""
    if not text:
        return None

    text = text.strip()

    # 직접 매핑된 경우
    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    # 정확히 국가명인 경우
    if text in BEAN_COUNTRIES:
        return text

    return None


def extract_keywords_from_text(text):
    """텍스트에서 국가명 및 세부 키워드 추출"""
    if not text or pd.isna(text):
        return []

    text = str(text)
    found = []

    # 모든 키워드 검색 (국가명 + 지역명 + 품종명)
    all_terms = list(BEAN_COUNTRIES) + list(COUNTRY_ALIASES.keys())

    # 추가 키워드 (품종, 등급 등)
    extra_keywords = [
        "게이샤", "게샤", "파카마라", "부르봉", "핑크", "AA",
        "피베리", "내추럴", "워시드", "허니", "아네로빅"
    ]
    all_terms.extend(extra_keywords)

    for term in all_terms:
        if term in text:
            found.append(term)

    return found


def get_country_from_keywords(keywords):
    """키워드에서 국가 추출"""
    for kw in keywords:
        country = normalize_country(kw)
        if country:
            return country
        if kw in BEAN_COUNTRIES:
            return kw
    return None


def select_bean_for_country(country, keywords):
    """국가와 키워드에 맞는 대표 원두 선택"""
    if country not in COUNTRY_BEANS:
        return None

    country_data = COUNTRY_BEANS[country]

    # 세부 키워드가 있으면 해당 원두 사용
    for kw in keywords:
        kw_lower = kw.lower() if kw else ""
        if kw in country_data:
            bean_ids = country_data[kw]
            return bean_ids[0] if bean_ids else None

    # 키워드 매칭 안되면 default 사용
    default_beans = country_data.get("default", [])
    return default_beans[0] if default_beans else None


def extract_countries_from_store_description(description):
    """가게 설명에서 원두 국가 정보 추출"""
    if not description or pd.isna(description):
        return set()

    keywords = extract_keywords_from_text(description)
    countries = set()

    for kw in keywords:
        country = normalize_country(kw)
        if country:
            countries.add(country)
        elif kw in BEAN_COUNTRIES:
            countries.add(kw)

    return countries


def create_menu_bean_mappings(stores, menus, beans):
    """메뉴-원두 매핑 생성"""
    mappings = []
    stats = {
        'total_menus': len(menus),
        'menus_with_country_in_name': 0,
        'menus_mapped_by_store': 0,
        'stores_with_bean_info': 0,
        'total_mappings': 0,
    }

    # store_id -> description 매핑
    store_descriptions = dict(zip(stores['id'], stores['description']))

    # 각 store의 description에서 추출한 국가 정보
    store_countries = {}
    for store_id, desc in store_descriptions.items():
        countries = extract_countries_from_store_description(desc)
        if countries:
            store_countries[store_id] = countries

    stats['stores_with_bean_info'] = len(store_countries)
    print(f"\n가게 description에서 원두 정보 발견: {len(store_countries)}개 가게")

    # 메뉴별 매핑
    mapped_menus = set()  # 이미 매핑된 메뉴 추적

    for _, menu in menus.iterrows():
        menu_id = menu['id']
        store_id = menu['store_id']
        menu_name = menu['name']

        # 1. 메뉴 이름에서 국가명/키워드 추출
        menu_keywords = extract_keywords_from_text(menu_name)
        menu_country = get_country_from_keywords(menu_keywords)

        if menu_country:
            stats['menus_with_country_in_name'] += 1
            bean_id = select_bean_for_country(menu_country, menu_keywords)

            if bean_id:
                mappings.append({
                    'menu_id': menu_id,
                    'bean_id': bean_id,
                    'is_blended': False,
                    'match_source': 'menu_name',
                    'match_country': menu_country,
                    'match_keywords': ','.join(menu_keywords),
                })
                mapped_menus.add(menu_id)

        # 2. 가게에 원두 정보가 있고, 아직 매핑 안된 메뉴면 가게 기반 매핑
        if menu_id not in mapped_menus and store_id in store_countries:
            for country in store_countries[store_id]:
                bean_id = select_bean_for_country(country, [])
                if bean_id:
                    mappings.append({
                        'menu_id': menu_id,
                        'bean_id': bean_id,
                        'is_blended': False,
                        'match_source': 'store_description',
                        'match_country': country,
                        'match_keywords': '',
                    })
                    stats['menus_mapped_by_store'] += 1

    stats['total_mappings'] = len(mappings)

    return mappings, stats


def deduplicate_mappings(mappings):
    """중복 매핑 제거 (같은 menu_id, bean_id 조합)"""
    seen = set()
    unique_mappings = []

    for m in mappings:
        key = (m['menu_id'], m['bean_id'])
        if key not in seen:
            seen.add(key)
            unique_mappings.append(m)

    return unique_mappings


def main():
    print("=== 메뉴-원두 매핑 v2 시작 ===\n")

    # 데이터 로드
    stores, menus, beans = load_data()

    # 매핑 생성
    mappings, stats = create_menu_bean_mappings(stores, menus, beans)

    # 중복 제거
    mappings = deduplicate_mappings(mappings)

    # 통계 출력
    print(f"\n=== 매핑 통계 ===")
    print(f"전체 메뉴 수: {stats['total_menus']}")
    print(f"메뉴명에 국가명 포함: {stats['menus_with_country_in_name']}")
    print(f"가게 기반 매핑: {stats['menus_mapped_by_store']}")
    print(f"원두 정보 있는 가게 수: {stats['stores_with_bean_info']}")
    print(f"총 매핑 수 (중복 제거 후): {len(mappings)}")

    # DataFrame 생성
    if mappings:
        mappings_df = pd.DataFrame(mappings)

        # DB 스키마에 맞게 컬럼 정리
        output_df = mappings_df[['menu_id', 'bean_id', 'is_blended']].copy()
        output_df['id'] = range(1, len(output_df) + 1)
        output_df = output_df[['id', 'menu_id', 'bean_id', 'is_blended']]

        # 저장
        output_path = STORES_DIR / "menu_bean_mappings.csv"
        output_df.to_csv(output_path, index=False)
        print(f"\n저장 완료: {output_path}")

        # 디버그용 상세 정보 저장
        debug_path = STORES_DIR / "menu_bean_mappings_debug.csv"
        mappings_df['id'] = range(1, len(mappings_df) + 1)
        mappings_df.to_csv(debug_path, index=False)
        print(f"디버그 정보 저장: {debug_path}")

        # 샘플 출력
        print(f"\n=== 매핑 샘플 (처음 15개) ===")
        sample = mappings_df.head(15)
        for _, row in sample.iterrows():
            menu_row = menus[menus['id'] == row['menu_id']]
            bean_row = beans[beans['id'] == row['bean_id']]

            if len(menu_row) > 0 and len(bean_row) > 0:
                menu_name = menu_row['name'].values[0]
                bean_name = bean_row['name'].values[0]
                print(f"  메뉴 [{row['menu_id']}] {menu_name}")
                print(f"    -> 원두 [{row['bean_id']}] {bean_name}")
                print(f"       ({row['match_source']}, {row['match_country']})")
    else:
        print("\n매핑된 결과가 없습니다.")


if __name__ == "__main__":
    main()
