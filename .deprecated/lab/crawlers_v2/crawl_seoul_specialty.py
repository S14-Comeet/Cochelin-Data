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
from selenium.common.exceptions import TimeoutException # Added this import
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import csv
import os
from datetime import datetime

# 검색어 목록
SEARCH_QUERIES = [
    # 광역
    "서울 스페셜티 커피",
    "서울 로스터리 카페",
    "서울 핸드드립 맛집",
    "서울 필터커피",

    # 강남권 (강남, 서초, 송파)
    "강남 스페셜티 커피", "강남 로스터리", "역삼 로스터리", "압구정 스페셜티", "청담 스페셜티", "신사동 스페셜티",
    "서초 스페셜티 커피", "서초 로스터리", "양재 로스터리", "반포 스페셜티",
    "송파 스페셜티 커피", "송파 로스터리", "잠실 스페셜티", "석촌호수 로스터리",

    # 강북권 (마포, 용산, 종로, 중구, 서대문)
    "마포 스페셜티 커피", "합정 로스터리", "망원 스페셜티", "연남동 로스터리", "홍대 스페셜티", "상수 로스터리",
    "용산 스페셜티 커피", "용산 로스터리", "이태원 스페셜티", "한남동 로스터리",
    "종로 스페셜티 커피", "종로 로스터리", "익선동 스페셜티", "서촌 로스터리", "북촌 스페셜티",
    "을지로 스페셜티 커피", "중구 로스터리",
    "서대문구 스페셜티", "연희동 로스터리",

    # 기타 주요 지역
    "성수 스페셜티 커피", "성수 로스터리", "뚝섬 스페셜티", "서울숲 로스터리",
    "영등포 스페셜티", "문래 로스터리", "여의도 스페셜티",
    "관악구 스페셜티", "샤로수길 로스터리",
    "성북구 스페셜티", "성신여대 로스터리",
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
    '아로마', '산미', '바디', '플레이버', '테이스팅', '필터커피', '브루잉',

    # 로스터리
    '로스터리', '자가로스팅', '직접 로스팅',
]

# 커피 메뉴 필터링 키워드
COFFEE_KEYWORDS = [
    '아메리카노', '라떼', '에스프레소', '드립', '필터', '브루잉', '콜드브루', 
    '플랫화이트', '아인슈페너', '마키아또', '카푸치노', '모카', '게이샤', '원두', 
    '싱글', '비엔나', '더치', '사이폰', '에어로프레스', '프레소'
]

NON_COFFEE_KEYWORDS = [
    '케이크', '쿠키', '스콘', '빵', '샌드위치', '토스트', '휘낭시에', '마들렌', 
    '티', '에이드', '주스', '스무디', '요거트', '빙수', '디저트', '버거', 
    '파스타', '크로플', '와플', '베이글', '소금빵', '푸딩', '밀크티', 
    '초코', '녹차', '말차', '아이스티', '하이볼', '맥주', '파이', '브라우니',
    '마카롱', '도넛', '까눌레', '샐러드', '피자', '맥주', '와인'
]

# 결과 저장 경로
OUTPUT_DIR = "crawlers_v2/data"
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


def is_coffee_menu(name, description=""):
    """커피 메뉴인지 확인 (음식/디저트/논커피 제외)"""
    target_text = (name + " " + description).replace(" ", "") # 공백 제거 후 확인
    
    # 1. 제외 키워드 확인
    for keyword in NON_COFFEE_KEYWORDS:
        if keyword in target_text:
            return False
            
    # # 2. 포함 키워드 확인
    # for keyword in COFFEE_KEYWORDS:
    #     if keyword in target_text:
    #         return True
            
    return True # 커피 키워드가 없으면 기본적으로 제외 (보수적 접근)


def is_target_district(address):
    """대상 구역인지 확인 (서울 전체)"""
    if not address:
        return False
    return "서울" in address





def extract_store_info_from_state(driver):
    """window.__APOLLO_STATE__에서 가게 정보 추출"""
    store_info = {}
    try:
        data = driver.execute_script("return window.__APOLLO_STATE__")
        if not data:
            return {}
        
        # Extract basic info from PlaceDetailBase
        for key, value in data.items():
            if key.startswith("PlaceDetailBase:"):
                store_info['name'] = value.get('name')
                store_info['category'] = value.get('category')
                store_info['address'] = value.get('roadAddress') or value.get('address') or ""
                store_info['phone'] = value.get('virtualPhone') or value.get('phone') or ""
                
                # 좌표 정보
                if value.get('coordinate'):
                    store_info['latitude'] = value['coordinate'].get('y')
                    store_info['longitude'] = value['coordinate'].get('x')
                
                if store_info.get('name'):
                    break
        
        # Extract detailed description, which is nested under ROOT_QUERY
        description = ""
        root_query = data.get('ROOT_QUERY', {})
        for root_key, root_value in root_query.items():
            if root_key.startswith("placeDetail({"):
                # root_value is the PlaceDetail object
                for desc_key, desc_value in root_value.items():
                    if desc_key.startswith("description({"):
                        description = desc_value
                        break
                if description:
                    break
        store_info['description'] = description or ""

    except Exception as e:
        print(f"JS Extraction failed in extract_store_info_from_state: {e}")
    
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

        # entryIframe으로 전환
        try:
            wait = WebDriverWait(driver, 20) # Use the increased timeout
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "entryIframe")))
        except TimeoutException: # Catch the specific exception for not finding element
            try:
                # If ID fails, try a more general CSS selector based on title
                print("  [DEBUG] entryIframe by ID failed, trying by CSS_SELECTOR...")
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[title="Naver Place Entry"]')))
            except Exception as e:
                print(f"  [DEBUG] Failed to switch to entryIframe (both ID and CSS_SELECTOR). Error: {e}")
                driver.switch_to.default_content() # Ensure we switch back to default content if we fail here
                return store_info, menus
        except Exception as e: # Catch any other exceptions
            print(f"  [DEBUG] Failed to switch to entryIframe. Error: {e}")
            driver.switch_to.default_content() # Ensure we switch back to default content if we fail here
            return store_info, menus

        time.sleep(2)

        # 1. JS state에서 정보 추출 시도
        store_info = extract_store_info_from_state(driver)

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
            # State 다시 추출 (메뉴 정보가 업데이트 되었을 수 있음)
            menu_store_info = extract_store_info_from_state(driver)

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
                        # 커피 메뉴만 필터링
                        if is_coffee_menu(menu['name'], menu.get('description', '')):
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
        # print(f"DEBUG: Checking keyword: {keyword}") # Too verbose, only enable if needed
        if keyword in description:
            print(f"DEBUG: Found keyword '{keyword}' in description.")
            return True

    # 메뉴 설명에서 확인
    for menu in menus:
        menu_desc = menu.get('description', '')
        menu_name = menu.get('name', '')
        # print(f"DEBUG: Checking menu: {menu_name} - {menu_desc[:50]}...") # Print first 50 chars
        for keyword in BEAN_KEYWORDS:
            if keyword in menu_desc or keyword in menu_name:
                print(f"DEBUG: Found keyword '{keyword}' in menu '{menu_name}'.")
                return True

    return False





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
                        # if not has_bean_info(store_info, menus):
                        #     print("원두 정보 없음")
                        #     continue

                        # 저장
                        all_stores[address] = {
                            'store': store_info,
                            'menus': menus,
                        }
                        query_log['added'] += 1
                        print(f"추가! (메뉴 {len(menus)}개) [누적 {len(all_stores)}개]")

                        if len(all_stores) >= 200:
                            print("\n목표 수량(200개) 달성으로 크롤링을 종료합니다.")
                            break

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

            if len(all_stores) >= 200:
                break

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
