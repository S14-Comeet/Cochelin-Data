"""
네이버 플레이스 스페셜티 카페 크롤러
- 강남구, 성동구, 마포구의 스페셜티 카페 수집
- 메뉴에 원두 정보가 있는 카페만 필터링
- schema.sql 구조에 맞게 CSV 저장
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import csv
import os
from datetime import datetime

# 검색어 목록
SEARCH_QUERIES = [
    # 강남구
    "강남 스페셜티 커피",
    "강남 로스터리",
    "강남 핸드드립 카페",
    "강남 싱글오리진",
    "삼성동 스페셜티",
    "역삼 로스터리",
    "신사동 스페셜티 카페",
    "압구정 로스터리",
    "청담 스페셜티",

    # 성동구
    "성수 스페셜티 커피",
    "성수 로스터리",
    "성수 핸드드립",
    "성수동 카페 원두",
    "왕십리 스페셜티",
    "금호동 로스터리",

    # 마포구
    "합정 스페셜티 커피",
    "합정 로스터리",
    "망원 스페셜티",
    "연남동 로스터리",
    "홍대 스페셜티 카페",
    "상수 로스터리",
    "마포 핸드드립",
]

# 원두 정보 키워드
BEAN_KEYWORDS = [
    # 원산지
    '에티오피아', '케냐', '콜롬비아', '브라질', '과테말라', '코스타리카',
    '파나마', '예멘', '인도네시아', '르완다', '부룬디', '탄자니아',
    '게이샤', '예가체프', '시다모', '구지', '리무',

    # 가공법
    '워시드', '내추럴', '허니', '무산소', '발효', '프로세스',

    # 커피 용어
    '싱글오리진', '블렌드', '원두', '로스팅', '스페셜티', '드립',
    '아로마', '산미', '바디', '플레이버', '테이스팅',

    # 로스터리
    '로스터리', '자가로스팅', '직접 로스팅',
]

# 결과 저장 경로
OUTPUT_DIR = "data"
STORES_FILE = "stores.csv"
MENUS_FILE = "menus.csv"
CRAWL_LOG_FILE = "crawl_log.json"


def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def search_naver_map(driver, query):
    """네이버 지도에서 검색"""
    search_url = f"https://map.naver.com/p/search/{query}"
    driver.get(search_url)
    time.sleep(3)
    return driver


def get_search_results(driver, max_results=15):
    """검색 결과 목록 가져오기"""
    results = []

    try:
        wait = WebDriverWait(driver, 10)
        search_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "searchIframe"))
        )
        driver.switch_to.frame(search_iframe)

        time.sleep(2)

        # 검색 결과 목록 찾기
        place_items = driver.find_elements(By.CSS_SELECTOR, "li.UEzoS")

        for i, item in enumerate(place_items[:max_results]):
            try:
                name_el = item.find_element(By.CSS_SELECTOR, "span.TYaxT")
                name = name_el.text if name_el else ""

                try:
                    category_el = item.find_element(By.CSS_SELECTOR, "span.KCMnt")
                    category = category_el.text if category_el else ""
                except:
                    category = ""

                if name:
                    results.append({
                        'index': i,
                        'name': name,
                        'category': category,
                    })

            except Exception as e:
                pass

        driver.switch_to.default_content()

    except Exception as e:
        print(f"검색 결과 가져오기 오류: {e}")
        driver.switch_to.default_content()

    return results


def extract_store_info_from_page(page_source):
    """페이지 소스에서 가게 정보 추출"""
    store_info = {}

    try:
        name_match = re.search(r'"businessDisplayName":"([^"]+)"', page_source)
        if name_match:
            store_info['name'] = name_match.group(1)

        category_match = re.search(r'"placeCategoryName":"([^"]+)"', page_source)
        if category_match:
            store_info['category'] = category_match.group(1)

        addr_match = re.search(r'"roadAddr":"([^"]+)"', page_source)
        if addr_match:
            store_info['address'] = addr_match.group(1)

        lat_match = re.search(r'"posLat":([0-9.]+)', page_source)
        lon_match = re.search(r'"posLong":([0-9.]+)', page_source)
        if lat_match and lon_match:
            store_info['latitude'] = float(lat_match.group(1))
            store_info['longitude'] = float(lon_match.group(1))

        phone_match = re.search(r'"reprPhone":"([^"]+)"', page_source)
        if phone_match:
            store_info['phone'] = phone_match.group(1)

        desc_match = re.search(r'"desc":"([^"]*(?:\\.[^"]*)*)"', page_source)
        if desc_match:
            store_info['description'] = desc_match.group(1).replace('\\n', '\n')

    except Exception as e:
        pass

    return store_info


def get_cafe_detail_and_menus(driver, index):
    """카페 상세 정보와 메뉴 가져오기"""
    store_info = {}
    menus = []

    try:
        # searchIframe으로 전환
        wait = WebDriverWait(driver, 10)
        search_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "searchIframe"))
        )
        driver.switch_to.frame(search_iframe)

        # 장소 클릭
        place_items = driver.find_elements(By.CSS_SELECTOR, "li.UEzoS")
        if len(place_items) > index:
            place_items[index].click()

        driver.switch_to.default_content()
        time.sleep(3)

        # entryIframe으로 전환
        try:
            entry_iframe = wait.until(
                EC.presence_of_element_located((By.ID, "entryIframe"))
            )
            driver.switch_to.frame(entry_iframe)
        except:
            return store_info, menus

        time.sleep(2)

        # 먼저 홈 탭에서 기본 정보 추출
        page_source = driver.page_source
        store_info = extract_store_info_from_page(page_source)

        # 메뉴 탭 클릭 시도
        menu_clicked = False
        menu_tab_xpaths = [
            "//span[contains(text(), '메뉴')]/..",
            "//a[contains(@href, 'menu')]",
        ]

        for xpath in menu_tab_xpaths:
            try:
                menu_tab = driver.find_element(By.XPATH, xpath)
                menu_tab.click()
                menu_clicked = True
                time.sleep(2)
                break
            except:
                continue

        if menu_clicked:
            # 메뉴 페이지에서 추가 정보 업데이트
            page_source = driver.page_source
            menu_store_info = extract_store_info_from_page(page_source)
            # 기존 정보에 없는 것만 업데이트
            for key, value in menu_store_info.items():
                if key not in store_info or not store_info[key]:
                    store_info[key] = value

            # 메뉴 목록 가져오기
            menu_items = driver.find_elements(By.CSS_SELECTOR, "li[class*='MenuContent__order_list_item']")

            for item in menu_items[:30]:
                try:
                    menu = {}

                    try:
                        name_el = item.find_element(By.CSS_SELECTOR, "div[class*='MenuContent__tit']")
                        menu['name'] = name_el.text.strip()
                    except:
                        menu['name'] = ""

                    try:
                        price_el = item.find_element(By.CSS_SELECTOR, "div[class*='MenuContent__price']")
                        menu['price'] = price_el.text.strip()
                    except:
                        menu['price'] = ""

                    try:
                        desc_el = item.find_element(By.CSS_SELECTOR, "span.detail_txt")
                        menu['description'] = desc_el.text.strip()
                    except:
                        menu['description'] = ""

                    if menu.get('name'):
                        menus.append(menu)

                except Exception as e:
                    pass

        driver.switch_to.default_content()

    except Exception as e:
        print(f"상세 정보 가져오기 오류: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass

    return store_info, menus


def has_bean_info(store_info, menus):
    """원두 정보가 있는지 확인"""
    # 가게 설명에서 확인
    description = store_info.get('description', '')
    for keyword in BEAN_KEYWORDS:
        if keyword in description:
            return True

    # 메뉴 설명에서 확인
    for menu in menus:
        menu_desc = menu.get('description', '')
        menu_name = menu.get('name', '')
        for keyword in BEAN_KEYWORDS:
            if keyword in menu_desc or keyword in menu_name:
                return True

    return False


def is_target_district(address):
    """대상 구역인지 확인"""
    if not address:
        return False
    target_districts = ['강남구', '성동구', '마포구']
    return any(district in address for district in target_districts)


def save_results(stores, all_menus):
    """결과를 CSV로 저장"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # stores.csv 저장
    stores_path = os.path.join(OUTPUT_DIR, STORES_FILE)
    with open(stores_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'roastery_id', 'owner_id', 'name', 'description', 'address',
            'latitude', 'longitude', 'phone_number', 'category',
            'thumbnail_url', 'open_time', 'close_time'
        ])

        for i, store in enumerate(stores, 1):
            writer.writerow([
                i,  # id
                1,  # roastery_id (임시)
                '',  # owner_id
                store.get('name', ''),
                store.get('description', ''),
                store.get('address', ''),
                store.get('latitude', ''),
                store.get('longitude', ''),
                store.get('phone', ''),
                store.get('category', ''),
                '',  # thumbnail_url
                '',  # open_time
                '',  # close_time
            ])

    print(f"stores.csv 저장 완료: {len(stores)}개")

    # menus.csv 저장
    menus_path = os.path.join(OUTPUT_DIR, MENUS_FILE)
    with open(menus_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'store_id', 'name', 'description', 'price', 'category', 'image_url'
        ])

        menu_id = 1
        for store_id, menus in enumerate(all_menus, 1):
            for menu in menus:
                # 가격 파싱 (예: "3,800원" -> 3800)
                price_str = menu.get('price', '0')
                price = int(re.sub(r'[^\d]', '', price_str)) if price_str else 0

                writer.writerow([
                    menu_id,
                    store_id,
                    menu.get('name', ''),
                    menu.get('description', ''),
                    price,
                    '',  # category
                    '',  # image_url
                ])
                menu_id += 1

    print(f"menus.csv 저장 완료: {menu_id - 1}개")


def main():
    print("=" * 50)
    print("스페셜티 카페 크롤링 시작")
    print(f"검색어: {len(SEARCH_QUERIES)}개")
    print("=" * 50)

    driver = setup_driver()

    all_stores = {}  # 주소를 키로 사용하여 중복 제거
    crawl_log = {
        'start_time': datetime.now().isoformat(),
        'queries': [],
        'errors': [],
    }

    try:
        for query_idx, query in enumerate(SEARCH_QUERIES):
            print(f"\n[{query_idx + 1}/{len(SEARCH_QUERIES)}] 검색: {query}")

            query_log = {
                'query': query,
                'found': 0,
                'added': 0,
            }

            try:
                search_naver_map(driver, query)
                results = get_search_results(driver, max_results=10)
                query_log['found'] = len(results)
                print(f"  검색 결과: {len(results)}개")

                for i, result in enumerate(results):
                    try:
                        print(f"    [{i + 1}] {result['name']} 처리 중...", end=" ")

                        # 다시 검색 페이지로
                        search_naver_map(driver, query)
                        time.sleep(1)

                        store_info, menus = get_cafe_detail_and_menus(driver, i)

                        if not store_info.get('name'):
                            print("정보 없음")
                            continue

                        address = store_info.get('address', '')

                        # 대상 구역 확인
                        if not is_target_district(address):
                            print(f"대상 구역 아님 ({address[:20]}...)")
                            continue

                        # 중복 확인
                        if address in all_stores:
                            print("중복")
                            continue

                        # 원두 정보 확인
                        if not has_bean_info(store_info, menus):
                            print("원두 정보 없음")
                            continue

                        # 저장
                        all_stores[address] = {
                            'store': store_info,
                            'menus': menus,
                        }
                        query_log['added'] += 1
                        print(f"추가! (메뉴 {len(menus)}개)")

                        # 딜레이
                        time.sleep(2)

                    except Exception as e:
                        print(f"오류: {e}")
                        crawl_log['errors'].append({
                            'query': query,
                            'index': i,
                            'error': str(e),
                        })

            except Exception as e:
                print(f"  검색 오류: {e}")
                crawl_log['errors'].append({
                    'query': query,
                    'error': str(e),
                })

            crawl_log['queries'].append(query_log)

            # 검색어 간 딜레이
            time.sleep(3)

    finally:
        driver.quit()

    # 결과 저장
    print("\n" + "=" * 50)
    print("크롤링 완료!")
    print(f"총 수집 카페: {len(all_stores)}개")
    print("=" * 50)

    stores = [v['store'] for v in all_stores.values()]
    all_menus = [v['menus'] for v in all_stores.values()]

    save_results(stores, all_menus)

    # 크롤링 로그 저장
    crawl_log['end_time'] = datetime.now().isoformat()
    crawl_log['total_stores'] = len(stores)
    crawl_log['total_menus'] = sum(len(m) for m in all_menus)

    log_path = os.path.join(OUTPUT_DIR, CRAWL_LOG_FILE)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(crawl_log, f, ensure_ascii=False, indent=2)

    print(f"\n로그 저장: {log_path}")

    # 요약 출력
    print("\n=== 수집된 카페 목록 ===")
    for i, store in enumerate(stores[:10], 1):
        print(f"{i}. {store.get('name')} - {store.get('address', '')[:30]}...")
    if len(stores) > 10:
        print(f"... 외 {len(stores) - 10}개")


if __name__ == '__main__':
    main()
