"""
네이버 플레이스 크롤링 테스트
- 검색 결과 페이지 구조 파악
- 상세 페이지 구조 파악
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


def setup_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    options.add_argument('--headless')  # headless 모드
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
    # 네이버 지도 검색 URL
    search_url = f"https://map.naver.com/p/search/{query}"
    driver.get(search_url)
    time.sleep(3)

    print(f"검색어: {query}")
    print(f"현재 URL: {driver.current_url}")

    return driver


def get_search_results(driver):
    """검색 결과 목록 가져오기"""
    results = []

    try:
        # searchIframe으로 전환
        wait = WebDriverWait(driver, 10)
        search_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "searchIframe"))
        )
        driver.switch_to.frame(search_iframe)
        print("searchIframe으로 전환 성공")

        time.sleep(2)

        # 검색 결과 목록 찾기
        place_items = driver.find_elements(By.CSS_SELECTOR, "li.UEzoS")
        print(f"찾은 장소 수: {len(place_items)}")

        for i, item in enumerate(place_items[:5]):  # 처음 5개만
            try:
                # 장소명
                name_el = item.find_element(By.CSS_SELECTOR, "span.TYaxT")
                name = name_el.text if name_el else "N/A"

                # 카테고리
                try:
                    category_el = item.find_element(By.CSS_SELECTOR, "span.KCMnt")
                    category = category_el.text if category_el else "N/A"
                except:
                    category = "N/A"

                # 주소
                try:
                    addr_el = item.find_element(By.CSS_SELECTOR, "span.Pb4bU")
                    address = addr_el.text if addr_el else "N/A"
                except:
                    address = "N/A"

                results.append({
                    'index': i,
                    'name': name,
                    'category': category,
                    'address': address
                })

                print(f"\n[{i+1}] {name}")
                print(f"    카테고리: {category}")
                print(f"    주소: {address}")

            except Exception as e:
                print(f"항목 {i} 파싱 오류: {e}")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"검색 결과 가져오기 오류: {e}")
        driver.switch_to.default_content()

    return results


def click_place_and_get_detail(driver, index=0):
    """검색 결과에서 특정 장소 클릭하고 상세 정보 가져오기"""
    detail = {}

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
            print(f"\n{index+1}번째 장소 클릭")

        driver.switch_to.default_content()
        time.sleep(3)

        # entryIframe으로 전환 (상세 정보)
        entry_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "entryIframe"))
        )
        driver.switch_to.frame(entry_iframe)
        print("entryIframe으로 전환 성공")

        time.sleep(2)

        # HTML 저장 (디버깅용)
        page_source = driver.page_source
        with open('debug_entry_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("debug_entry_page.html 저장됨")

        # APOLLO_STATE에서 상세 정보 추출 시도
        apollo_match = re.search(r'window\.__APOLLO_STATE__=(\{.+?\});</script>', page_source, re.DOTALL)
        if apollo_match:
            try:
                apollo_data = json.loads(apollo_match.group(1))
                # Business 데이터 찾기
                for key, value in apollo_data.items():
                    if key.startswith('Business:') and isinstance(value, dict):
                        # 이름
                        detail['name'] = value.get('name', value.get('businessDisplayName', 'N/A'))
                        print(f"가게명: {detail['name']}")

                        # 카테고리
                        detail['category'] = value.get('placeCategoryName', 'N/A')
                        print(f"카테고리: {detail['category']}")

                        # 주소 정보
                        addr_json = value.get('addressJson', {})
                        if addr_json:
                            detail['address'] = addr_json.get('roadAddr', addr_json.get('jibun', 'N/A'))
                            detail['latitude'] = addr_json.get('posLat')
                            detail['longitude'] = addr_json.get('posLong')
                            print(f"주소: {detail['address']}")
                            print(f"좌표: {detail['latitude']}, {detail['longitude']}")

                        # 전화번호
                        phone_json = value.get('phoneInformationJson', {})
                        if phone_json:
                            detail['phone'] = phone_json.get('reprPhone', 'N/A')
                            print(f"전화번호: {detail['phone']}")

                        # 설명
                        detail['description'] = value.get('desc', '')
                        if detail['description']:
                            print(f"설명: {detail['description'][:100]}...")

                        break
            except json.JSONDecodeError as e:
                print(f"APOLLO_STATE JSON 파싱 실패: {e}")

        # APOLLO_STATE에서 못 찾은 경우 DOM에서 추출
        if 'name' not in detail or detail.get('name') == 'N/A':
            name_selectors = ["span.GHAhO", "h1[class*='title']", "div.zD5Nm"]
            for sel in name_selectors:
                try:
                    name_el = driver.find_element(By.CSS_SELECTOR, sel)
                    if name_el.text:
                        detail['name'] = name_el.text
                        print(f"가게명 (DOM): {detail['name']}")
                        break
                except:
                    continue

        driver.switch_to.default_content()

    except Exception as e:
        print(f"상세 정보 가져오기 오류: {e}")
        driver.switch_to.default_content()

    return detail


def get_menu_info(driver):
    """메뉴 정보 가져오기"""
    menus = []
    store_info = {}

    try:
        # entryIframe으로 전환
        wait = WebDriverWait(driver, 10)
        entry_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "entryIframe"))
        )
        driver.switch_to.frame(entry_iframe)

        # 메뉴 탭 클릭 시도 - 여러 방법
        menu_clicked = False
        menu_tab_selectors = [
            "//span[contains(text(), '메뉴')]/..",
            "//a[contains(@href, 'menu')]",
            "//div[contains(@class, 'flicking-camera')]//span[text()='메뉴']/.."
        ]

        for xpath in menu_tab_selectors:
            try:
                menu_tab = driver.find_element(By.XPATH, xpath)
                menu_tab.click()
                menu_clicked = True
                print("\n메뉴 탭 클릭 성공")
                time.sleep(2)
                break
            except:
                continue

        if not menu_clicked:
            print("메뉴 탭을 찾을 수 없습니다")

        # 메뉴 페이지 HTML 저장
        page_source = driver.page_source
        with open('debug_menu_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("debug_menu_page.html 저장됨")

        # APOLLO_STATE에서 가게 정보 추출 (정규식으로 직접 추출)
        try:
            # 가게명
            name_match = re.search(r'"businessDisplayName":"([^"]+)"', page_source)
            if name_match:
                store_info['name'] = name_match.group(1)

            # 카테고리
            category_match = re.search(r'"placeCategoryName":"([^"]+)"', page_source)
            if category_match:
                store_info['category'] = category_match.group(1)

            # 주소
            addr_match = re.search(r'"roadAddr":"([^"]+)"', page_source)
            if addr_match:
                store_info['address'] = addr_match.group(1)

            # 좌표
            lat_match = re.search(r'"posLat":([0-9.]+)', page_source)
            lon_match = re.search(r'"posLong":([0-9.]+)', page_source)
            if lat_match and lon_match:
                store_info['latitude'] = float(lat_match.group(1))
                store_info['longitude'] = float(lon_match.group(1))

            # 전화번호
            phone_match = re.search(r'"reprPhone":"([^"]+)"', page_source)
            if phone_match:
                store_info['phone'] = phone_match.group(1)

            # 설명
            desc_match = re.search(r'"desc":"([^"]*(?:\\.[^"]*)*)"', page_source)
            if desc_match:
                store_info['description'] = desc_match.group(1).replace('\\n', '\n')

            if store_info:
                print(f"\n=== 가게 정보 (APOLLO_STATE) ===")
                print(f"가게명: {store_info.get('name')}")
                print(f"주소: {store_info.get('address')}")
                print(f"좌표: {store_info.get('latitude')}, {store_info.get('longitude')}")
                print(f"전화: {store_info.get('phone')}")

        except Exception as e:
            print(f"APOLLO_STATE 파싱 실패: {e}")

        # 메뉴 목록 가져오기 - 네이버 플레이스 최신 셀렉터
        menu_items = driver.find_elements(By.CSS_SELECTOR, "li[class*='MenuContent__order_list_item']")
        print(f"메뉴 항목 수: {len(menu_items)}")

        if not menu_items:
            print("메뉴 항목을 찾을 수 없습니다")

        for item in menu_items[:20]:  # 처음 20개
            try:
                menu = {}

                # 메뉴명
                try:
                    name_el = item.find_element(By.CSS_SELECTOR, "div[class*='MenuContent__tit']")
                    menu['name'] = name_el.text.strip()
                except:
                    menu['name'] = ""

                # 가격
                try:
                    price_el = item.find_element(By.CSS_SELECTOR, "div[class*='MenuContent__price']")
                    menu['price'] = price_el.text.strip()
                except:
                    menu['price'] = ""

                # 설명 (원두 정보 등)
                try:
                    desc_el = item.find_element(By.CSS_SELECTOR, "span.detail_txt")
                    menu['description'] = desc_el.text.strip()
                except:
                    menu['description'] = ""

                if menu.get('name'):
                    menus.append(menu)
                    print(f"  - {menu['name']}: {menu.get('price', 'N/A')}")
                    if menu.get('description'):
                        print(f"    설명: {menu['description']}")

            except Exception as e:
                print(f"메뉴 항목 파싱 오류: {e}")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"메뉴 정보 가져오기 오류: {e}")
        driver.switch_to.default_content()

    return menus, store_info


def main():
    driver = setup_driver()

    try:
        # 1. 검색
        search_naver_map(driver, "강남 스페셜티 커피")

        # 2. 검색 결과 목록 가져오기
        results = get_search_results(driver)

        # 3. 첫 번째 장소 상세 정보 가져오기
        if results:
            detail = click_place_and_get_detail(driver, 0)

            # 4. 메뉴 정보 가져오기
            menus, store_info = get_menu_info(driver)

            # store_info로 detail 보완
            if store_info:
                detail.update(store_info)

            # 결과 저장
            result = {
                'store': detail,
                'menus': menus
            }

            with open('test_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print("\n\n=== 테스트 결과 저장 완료: test_result.json ===")

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
