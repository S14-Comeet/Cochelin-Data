"""
crawlers_v3 데이터를 schema.sql에 맞게 전처리하는 스크립트

생성 파일:
- roasteries.csv: 로스터리(브랜드) 테이블
- stores_final.csv: roastery_id가 매핑된 stores 테이블
"""

import pandas as pd
from pathlib import Path
from typing import Optional

# 프랜차이즈 브랜드 목록 (2개 이상 매장이 있는 브랜드)
FRANCHISE_BRANDS = [
    '테라로사',
    '블루보틀',
    '펠트커피',
    '텐퍼센트커피',
    '카페일분',
    '커피스니퍼',
    '만랩커피',
    '옵션스페셜티커피',
    '커피붕붕 커피볶는집',
    '원유로 스페셜티',
]


def extract_brand_from_name(store_name: str) -> Optional[str]:
    """
    가게 이름에서 프랜차이즈 브랜드를 추출합니다.

    Returns:
        프랜차이즈 브랜드명 또는 None (독립 카페인 경우)
    """
    for brand in FRANCHISE_BRANDS:
        if brand in store_name:
            return brand
    return None


def create_roasteries(stores_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    roasteries 테이블 데이터를 생성합니다.

    Returns:
        (roasteries_df, brand_to_roastery_id): roasteries 데이터프레임과 브랜드-ID 매핑
    """
    roasteries = []
    brand_to_roastery_id = {}
    roastery_id = 1

    # 1. 프랜차이즈 브랜드 먼저 추가
    for brand in FRANCHISE_BRANDS:
        # 해당 브랜드 매장이 실제로 있는지 확인
        has_stores = stores_df['name'].str.contains(brand, na=False).any()
        if has_stores:
            roasteries.append({
                'id': roastery_id,
                'name': brand,
                'logo_url': '',
                'website_url': '',
            })
            brand_to_roastery_id[brand] = roastery_id
            roastery_id += 1

    # 2. 독립 카페 추가 (프랜차이즈가 아닌 가게들)
    for _, store in stores_df.iterrows():
        store_name = store['name']
        brand = extract_brand_from_name(store_name)

        if brand is None:  # 독립 카페
            roasteries.append({
                'id': roastery_id,
                'name': store_name,
                'logo_url': '',
                'website_url': '',
            })
            # store_id를 키로 사용하여 나중에 매핑
            brand_to_roastery_id[f"store_{store['id']}"] = roastery_id
            roastery_id += 1

    roasteries_df = pd.DataFrame(roasteries)
    return roasteries_df, brand_to_roastery_id


def update_stores_with_roastery_id(stores_df: pd.DataFrame, brand_to_roastery_id: dict) -> pd.DataFrame:
    """
    stores 데이터프레임에 올바른 roastery_id를 매핑합니다.
    """
    def get_roastery_id(row):
        store_name = row['name']
        store_id = row['id']

        # 프랜차이즈인지 확인
        brand = extract_brand_from_name(store_name)
        if brand:
            return brand_to_roastery_id[brand]
        else:
            # 독립 카페
            return brand_to_roastery_id[f"store_{store_id}"]

    stores_df = stores_df.copy()
    stores_df['roastery_id'] = stores_df.apply(get_roastery_id, axis=1)

    # schema에 맞게 누락된 컬럼 추가 (기본값 설정)
    stores_df['average_rating'] = 0.0
    stores_df['review_count'] = 0
    stores_df['visit_count'] = 0
    stores_df['is_closed'] = False

    # 컬럼 순서 정리 (schema.sql 순서에 맞춤)
    columns = [
        'id', 'roastery_id', 'owner_id', 'name', 'description', 'address',
        'latitude', 'longitude', 'phone_number', 'category', 'thumbnail_url',
        'open_time', 'close_time', 'average_rating', 'review_count',
        'visit_count', 'is_closed'
    ]

    # 존재하는 컬럼만 선택
    existing_columns = [col for col in columns if col in stores_df.columns]
    stores_df = stores_df[existing_columns]

    return stores_df


def main():
    # 경로 설정
    data_dir = Path(__file__).parent / 'data'
    stores_path = data_dir / 'stores.csv'

    print("=" * 50)
    print("crawlers_v3 데이터 전처리 시작")
    print("=" * 50)

    # 1. 원본 데이터 로드
    print("\n[1/4] stores.csv 로드 중...")
    stores_df = pd.read_csv(stores_path)
    print(f"  - 총 {len(stores_df)}개 stores 로드됨")

    # 2. roasteries 생성
    print("\n[2/4] roasteries 테이블 생성 중...")
    roasteries_df, brand_to_roastery_id = create_roasteries(stores_df)

    # 프랜차이즈 수 계산
    franchise_count = len([b for b in brand_to_roastery_id.keys() if not b.startswith('store_')])
    independent_count = len(roasteries_df) - franchise_count

    print(f"  - 프랜차이즈 브랜드: {franchise_count}개")
    print(f"  - 독립 카페: {independent_count}개")
    print(f"  - 총 roasteries: {len(roasteries_df)}개")

    # 3. stores에 roastery_id 매핑
    print("\n[3/4] stores에 roastery_id 매핑 중...")
    stores_final_df = update_stores_with_roastery_id(stores_df, brand_to_roastery_id)

    # 프랜차이즈별 매핑 확인
    print("\n  프랜차이즈 매핑 결과:")
    for brand in FRANCHISE_BRANDS:
        if brand in brand_to_roastery_id:
            roastery_id = brand_to_roastery_id[brand]
            count = (stores_final_df['roastery_id'] == roastery_id).sum()
            print(f"    - {brand} (roastery_id={roastery_id}): {count}개 매장")

    # 4. CSV 파일 저장
    print("\n[4/4] CSV 파일 저장 중...")

    roasteries_path = data_dir / 'roasteries.csv'
    stores_final_path = data_dir / 'stores_final.csv'

    roasteries_df.to_csv(roasteries_path, index=False, encoding='utf-8-sig')
    stores_final_df.to_csv(stores_final_path, index=False, encoding='utf-8-sig')

    print(f"  - {roasteries_path}")
    print(f"  - {stores_final_path}")

    print("\n" + "=" * 50)
    print("전처리 완료!")
    print("=" * 50)

    # 결과 요약
    print("\n[결과 요약]")
    print(f"  roasteries.csv: {len(roasteries_df)}개 레코드")
    print(f"  stores_final.csv: {len(stores_final_df)}개 레코드")
    print(f"\n  stores 컬럼: {list(stores_final_df.columns)}")


if __name__ == '__main__':
    main()
