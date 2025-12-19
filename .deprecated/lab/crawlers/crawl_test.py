"""
테스트용 - 검색어 3개만 실행
"""

from crawl_specialty_cafes import *

# 테스트용 검색어 (3개만)
TEST_QUERIES = [
    "강남 스페셜티 커피",
    "성수 스페셜티 커피",
    "합정 스페셜티 커피",
]

if __name__ == '__main__':
    print("=" * 50)
    print("스페셜티 카페 크롤링 테스트 (3개 검색어)")
    print("=" * 50)

    driver = setup_driver()

    all_stores = {}

    try:
        for query_idx, query in enumerate(TEST_QUERIES):
            print(f"\n[{query_idx + 1}/{len(TEST_QUERIES)}] 검색: {query}")

            try:
                search_naver_map(driver, query)
                results = get_search_results(driver, max_results=5)  # 5개만
                print(f"  검색 결과: {len(results)}개")

                for i, result in enumerate(results):
                    try:
                        print(f"    [{i + 1}] {result['name']} 처리 중...", end=" ")

                        search_naver_map(driver, query)
                        time.sleep(1)

                        store_info, menus = get_cafe_detail_and_menus(driver, i)

                        if not store_info.get('name') or not store_info.get('address'):
                            print("정보 없음")
                            continue

                        address = store_info.get('address', '')

                        if not is_target_district(address):
                            print(f"대상 구역 아님")
                            continue

                        if address in all_stores:
                            print("중복")
                            continue

                        if not has_bean_info(store_info, menus):
                            print("원두 정보 없음")
                            continue

                        all_stores[address] = {
                            'store': store_info,
                            'menus': menus,
                        }
                        print(f"추가! (메뉴 {len(menus)}개)")

                        time.sleep(2)

                    except Exception as e:
                        print(f"오류: {e}")

            except Exception as e:
                print(f"  검색 오류: {e}")

            time.sleep(2)

    finally:
        driver.quit()

    print("\n" + "=" * 50)
    print(f"테스트 완료! 총 수집: {len(all_stores)}개")
    print("=" * 50)

    # 결과 출력
    for addr, data in all_stores.items():
        store = data['store']
        menus = data['menus']
        print(f"\n[{store.get('name')}]")
        print(f"  주소: {store.get('address')}")
        print(f"  전화: {store.get('phone')}")
        print(f"  메뉴: {len(menus)}개")
        if menus:
            print(f"  메뉴 예시: {menus[0].get('name')} - {menus[0].get('price')}")
            if menus[0].get('description'):
                print(f"    설명: {menus[0].get('description')[:50]}...")
