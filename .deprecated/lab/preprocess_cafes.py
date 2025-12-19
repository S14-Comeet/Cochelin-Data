import csv
import re

# 설정
INPUT_FILE = '소상공인시장진흥공단_상가(상권)정보_20250630/소상공인시장진흥공단_상가(상권)정보_서울_202506.csv'
OUTPUT_FILE = 'stores_preprocessed.csv'

# 포함할 구 (이 구만 포함)
INCLUDE_DISTRICTS = ['강남구', '성동구', '마포구']

# 포함할 스페셜티 프렌차이즈 (이 키워드가 있으면 무조건 포함)
SPECIALTY_FRANCHISES = [
    '테라로사', '프릳츠', '블루보틀', '센터커피', '모모스',
    '커피리브레', '앤트러사이트', '펠트', '커피몽타주', '나무사이로'
]

# 제외할 일반 프렌차이즈
EXCLUDE_FRANCHISES = [
    '이디야', '투썸플레이스', '투썸', '메가커피', '메가MGC',
    '빽다방', '컴포즈', '커피빈', '할리스', '파스쿠찌',
    '엔제리너스', '카페베네', '폴바셋', '매머드', '더벤티',
    '감성커피', '탐앤탐스', '커피나무', '커피에반하다', '토프레소',
    '드롭탑', '공차', '카페봄봄', '달콤', '만랩커피', '메가엠지씨',
    '바나프레소', '만월경'
]

# 제외할 키워드 (상호명에 포함되면 제외)
EXCLUDE_KEYWORDS = [
    '디저트', '스터디', '베이커리', '브런치', '와플', '빙수',
    '떡', '케이크', '베이킹', '아이스크림', '요거트', '크로플',
    '마카롱', '타르트', '쿠키', '도넛', '빵', '제과', '당고',
    '베이크', '베이글', '식당', '비스트로', '파스타', '키친', '푸드'
]


def is_specialty(name):
    """스페셜티 프렌차이즈인지 확인"""
    for specialty in SPECIALTY_FRANCHISES:
        if specialty in name:
            return True
    return False


def is_excluded_franchise(name):
    """제외할 일반 프렌차이즈인지 확인"""
    for franchise in EXCLUDE_FRANCHISES:
        if franchise in name:
            return True
    return False


def has_exclude_keyword(name):
    """제외 키워드가 포함되어 있는지 확인"""
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in name:
            return True
    return False


def should_include(name):
    """포함 여부 결정"""
    # 1. 스페셜티 프렌차이즈면 무조건 포함
    if is_specialty(name):
        return True

    # 2. 일반 프렌차이즈면 제외
    if is_excluded_franchise(name):
        return False

    # 3. 제외 키워드가 있으면 제외
    if has_exclude_keyword(name):
        return False

    # 4. 나머지는 포함
    return True


def main():
    included = []
    excluded_franchise = []
    excluded_keyword = []
    excluded_district = []
    total_cafe = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            # 상권업종소분류명이 "카페"인 것만
            if row[8] != '카페':
                continue

            total_cafe += 1
            name = row[1]  # 상호명
            district = row[14]  # 시군구명

            # 구 필터링 (강남구, 성동구, 마포구만 포함)
            if district not in INCLUDE_DISTRICTS:
                excluded_district.append(name)
                continue

            if should_include(name):
                included.append({
                    'name': name,
                    'address': row[31],  # 도로명주소
                    'latitude': row[38],  # 위도
                    'longitude': row[37],  # 경도
                })
            elif is_excluded_franchise(name):
                excluded_franchise.append(name)
            else:
                excluded_keyword.append(name)

    # 결과 출력
    print(f"=== 전처리 결과 ===")
    print(f"전체 카페 수: {total_cafe}")
    print(f"포함: {len(included)}")
    print(f"제외 (다른 구): {len(excluded_district)}")
    print(f"제외 (프렌차이즈): {len(excluded_franchise)}")
    print(f"제외 (키워드): {len(excluded_keyword)}")
    print()

    # 제외된 프렌차이즈 통계
    print("=== 제외된 프렌차이즈 상위 10개 ===")
    from collections import Counter
    franchise_counts = Counter()
    for name in excluded_franchise:
        for f in EXCLUDE_FRANCHISES:
            if f in name:
                franchise_counts[f] += 1
                break
    for f, count in franchise_counts.most_common(10):
        print(f"  {f}: {count}개")
    print()

    # 제외된 키워드 샘플
    print("=== 제외된 키워드 샘플 (처음 10개) ===")
    for name in excluded_keyword[:10]:
        print(f"  {name}")
    print()

    # CSV 출력
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # stores 테이블 구조에 맞는 헤더
        writer.writerow([
            'roastery_id', 'owner_id', 'name', 'description', 'address',
            'latitude', 'longitude', 'phone_number', 'category',
            'thumbnail_url', 'open_time', 'close_time'
        ])

        for cafe in included:
            writer.writerow([
                1,  # roastery_id (임시값)
                '',  # owner_id (NULL)
                cafe['name'],
                '',  # description (NULL)
                cafe['address'],
                cafe['latitude'],
                cafe['longitude'],
                '',  # phone_number (NULL)
                '',  # category (NULL)
                '',  # thumbnail_url (NULL)
                '',  # open_time (NULL)
                '',  # close_time (NULL)
            ])

    print(f"=== CSV 파일 생성 완료 ===")
    print(f"출력 파일: {OUTPUT_FILE}")
    print(f"총 {len(included)}개 레코드")


if __name__ == '__main__':
    main()
