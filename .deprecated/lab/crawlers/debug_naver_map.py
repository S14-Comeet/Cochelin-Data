"""
네이버 지도 크롤링 디버깅 스크립트
- 현재 페이지 구조 분석
- CSS 선택자 확인
- JSON 데이터 키 확인
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import json


def setup_driver(headless=False):
    """Chrome 드라이버 설정 (디버깅용으로 headless=False 기본)"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 봇 감지 우회 옵션
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # navigator.webdriver 속성 제거
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def debug_search_results(driver, query):
    """검색 결과 페이지 구조 분석"""
    print(f"\n{'='*60}")
    print(f"검색어: {query}")
    print('='*60)

    search_url = f"https://map.naver.com/p/search/{query}"
    driver.get(search_url)
    time.sleep(4)

    # searchIframe 확인
    try:
        wait = WebDriverWait(driver, 10)
        search_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "searchIframe"))
        )
        print("✓ searchIframe 발견")
        driver.switch_to.frame(search_iframe)
        time.sleep(2)

        # 페이지 소스 저장
        page_source = driver.page_source
        with open('data/debug_search_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("✓ 검색 페이지 소스 저장: data/debug_search_page.html")

        # 다양한 선택자로 검색 결과 찾기
        selectors_to_try = [
            ("li.UEzoS", "기존 선택자"),
            ("li[class*='_item']", "item 클래스 포함"),
            ("li[data-id]", "data-id 속성"),
            ("div.Ryr1F", "Ryr1F 클래스"),
            ("a.tzwk0", "tzwk0 링크"),
            ("div[class*='search']", "search 클래스 포함"),
            ("ul > li", "일반 li"),
        ]

        print("\n[검색 결과 목록 선택자 테스트]")
        for selector, desc in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  ✓ {desc} ({selector}): {len(elements)}개")
                    if len(elements) <= 20:
                        for i, el in enumerate(elements[:3]):
                            text = el.text[:50].replace('\n', ' ') if el.text else "(텍스트 없음)"
                            print(f"      [{i}] {text}")
            except Exception as e:
                print(f"  ✗ {desc}: 오류 - {e}")

        # 이름 선택자 테스트
        name_selectors = [
            ("span.TYaxT", "기존 이름 선택자"),
            ("span[class*='name']", "name 클래스"),
            ("a[class*='name']", "name 링크"),
            ("span.YwYLL", "YwYLL 클래스"),
            ("div.CHC5F a", "CHC5F 내 링크"),
        ]

        print("\n[이름 선택자 테스트]")
        for selector, desc in name_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  ✓ {desc} ({selector}): {len(elements)}개")
                    for i, el in enumerate(elements[:3]):
                        print(f"      [{i}] {el.text}")
            except Exception as e:
                print(f"  ✗ {desc}: 오류")

        driver.switch_to.default_content()

    except Exception as e:
        print(f"✗ searchIframe 오류: {e}")
        driver.switch_to.default_content()


def debug_place_detail(driver, query, place_index=0):
    """장소 상세 페이지 구조 분석"""
    print(f"\n{'='*60}")
    print(f"상세 페이지 디버깅 (검색어: {query}, 인덱스: {place_index})")
    print('='*60)

    search_url = f"https://map.naver.com/p/search/{query}"
    driver.get(search_url)
    time.sleep(4)

    try:
        wait = WebDriverWait(driver, 10)
        search_iframe = wait.until(
            EC.presence_of_element_located((By.ID, "searchIframe"))
        )
        driver.switch_to.frame(search_iframe)
        time.sleep(2)

        # 검색 결과에서 장소 클릭
        # 다양한 선택자 시도
        place_items = None
        for selector in ["li.UEzoS", "li[data-id]", "li[class*='_item']"]:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            if items:
                place_items = items
                print(f"✓ 장소 목록 발견: {selector} ({len(items)}개)")
                break

        if not place_items or len(place_items) <= place_index:
            print("✗ 클릭할 장소가 없음")
            driver.switch_to.default_content()
            return

        # 장소 클릭
        place_items[place_index].click()
        print(f"✓ {place_index}번 장소 클릭")

        driver.switch_to.default_content()
        time.sleep(3)

        # entryIframe 확인
        try:
            entry_iframe = wait.until(
                EC.presence_of_element_located((By.ID, "entryIframe"))
            )
            print("✓ entryIframe 발견")
            driver.switch_to.frame(entry_iframe)
            time.sleep(2)

            # 상세 페이지 소스 저장
            page_source = driver.page_source
            with open('data/debug_detail_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("✓ 상세 페이지 소스 저장: data/debug_detail_page.html")

            # JSON 데이터 키 찾기
            print("\n[JSON 데이터 키 분석]")
            json_patterns = [
                (r'"businessDisplayName":"([^"]+)"', "businessDisplayName"),
                (r'"name":"([^"]+)"', "name"),
                (r'"placeName":"([^"]+)"', "placeName"),
                (r'"title":"([^"]+)"', "title"),
                (r'"roadAddr":"([^"]+)"', "roadAddr"),
                (r'"address":"([^"]+)"', "address"),
                (r'"posLat":([0-9.]+)', "posLat"),
                (r'"posLong":([0-9.]+)', "posLong"),
                (r'"x":"([^"]+)"', "x (경도)"),
                (r'"y":"([^"]+)"', "y (위도)"),
                (r'"tel":"([^"]+)"', "tel"),
                (r'"reprPhone":"([^"]+)"', "reprPhone"),
                (r'"category":"([^"]+)"', "category"),
                (r'"categoryName":"([^"]+)"', "categoryName"),
            ]

            for pattern, desc in json_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    print(f"  ✓ {desc}: {matches[0][:50]}...")
                else:
                    print(f"  ✗ {desc}: 없음")

            # 메뉴 탭 찾기
            print("\n[메뉴 탭 찾기]")
            menu_selectors = [
                ("//span[contains(text(), '메뉴')]/..", "메뉴 텍스트 xpath"),
                ("a[href*='menu']", "menu href"),
                ("span.veBoZ", "veBoZ 클래스"),
                ("a.tpj9w", "tpj9w 클래스"),
            ]

            for selector, desc in menu_selectors:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  ✓ {desc}: {len(elements)}개 발견")
                        elements[0].click()
                        print("  → 메뉴 탭 클릭 성공")
                        time.sleep(2)
                        break
                except Exception as e:
                    print(f"  ✗ {desc}: {e}")

            # 메뉴 페이지 소스
            menu_source = driver.page_source
            with open('data/debug_menu_page.html', 'w', encoding='utf-8') as f:
                f.write(menu_source)
            print("✓ 메뉴 페이지 소스 저장: data/debug_menu_page.html")

            # 메뉴 아이템 찾기
            print("\n[메뉴 아이템 선택자 테스트]")
            menu_item_selectors = [
                ("li[class*='MenuContent']", "MenuContent 클래스"),
                ("li[class*='menu']", "menu 클래스"),
                ("div[class*='menu_item']", "menu_item 클래스"),
                ("ul.mpoxR li", "mpoxR 리스트"),
                ("div.place_section_content li", "place_section li"),
            ]

            for selector, desc in menu_item_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  ✓ {desc} ({selector}): {len(elements)}개")
                        for i, el in enumerate(elements[:2]):
                            text = el.text[:80].replace('\n', ' | ') if el.text else "(텍스트 없음)"
                            print(f"      [{i}] {text}")
                except Exception as e:
                    print(f"  ✗ {desc}: 오류")

            driver.switch_to.default_content()

        except Exception as e:
            print(f"✗ entryIframe 오류: {e}")
            driver.switch_to.default_content()

    except Exception as e:
        print(f"✗ 오류: {e}")
        driver.switch_to.default_content()


def main():
    import os
    os.makedirs('data', exist_ok=True)

    print("="*60)
    print("네이버 지도 크롤링 디버깅 시작")
    print("="*60)

    # headless=False로 실제 브라우저에서 확인
    driver = setup_driver(headless=True)

    try:
        # 1. 검색 결과 구조 분석
        debug_search_results(driver, "강남 스페셜티 카페")

        # 2. 상세 페이지 구조 분석
        debug_place_detail(driver, "강남 스페셜티 카페", place_index=0)

        print("\n" + "="*60)
        print("디버깅 완료!")
        print("저장된 파일:")
        print("  - data/debug_search_page.html")
        print("  - data/debug_detail_page.html")
        print("  - data/debug_menu_page.html")
        print("="*60)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
