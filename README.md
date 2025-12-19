# Comeet-Data

서울 스페셜티 카페 데이터 수집 및 처리 파이프라인

## 프로젝트 개요

Comeet 서비스를 위한 스페셜티 카페 데이터셋을 구축하는 프로젝트입니다.

- 네이버 지도에서 서울 스페셜티 카페 정보 크롤링
- 커피 원두 데이터셋 처리 및 플레이버 노트 추출
- 메뉴-원두 매핑 생성
- DB Import용 SQL 파일 생성

## 데이터 통계

| 테이블 | 레코드 수 | 설명 |
|--------|-----------|------|
| roasteries | 231 | 로스터리 정보 |
| stores | 246 | 카페 매장 정보 |
| beans | 1,000 | 커피 원두 정보 |
| menus | 1,355 | 메뉴 정보 (커피만) |
| bean_flavor_notes | 4,823 | 원두별 플레이버 노트 |
| menu_bean_mappings | 270 | 메뉴-원두 매핑 |

## 폴더 구조

```
Comeet-Data/
├── README.md
├── CLAUDE.md                         # Claude Code 가이드
│
├── scripts/
│   ├── crawlers/
│   │   ├── crawl_seoul_cafes.py      # 네이버 지도 카페 크롤러
│   │   └── crawl_beans.py            # 원두 데이터 처리
│   └── processors/
│       ├── process_coffee_dataset.py # 원두 데이터셋 전처리
│       ├── preprocess_for_db.py      # DB용 데이터 전처리
│       ├── map_menu_beans.py         # 메뉴-원두 매핑 생성
│       └── csv_to_sql.py             # CSV → SQL 변환
│
├── data/
│   ├── raw/                          # 원본 데이터
│   │   ├── coffee_clean.csv          # 원두 원본 데이터셋
│   │   ├── stores_crawled.csv        # 크롤링된 카페 데이터
│   │   └── crawl_log.json            # 크롤링 로그
│   │
│   ├── final/                        # DB Import용 최종 데이터
│   │   ├── roasteries.csv
│   │   ├── stores.csv
│   │   ├── menus.csv
│   │   ├── beans.csv
│   │   ├── bean_flavor_notes.csv
│   │   └── menu_bean_mappings.csv
│   │
│   └── debug/                        # 디버그/참조용
│       ├── menus_removed.csv         # 제거된 비커피 메뉴
│       ├── menu_bean_mappings_debug.csv
│       └── bean_scores.csv
│
├── sql/
│   ├── schema/
│   │   ├── schema.sql                # DB 스키마
│   │   └── flavor_prod.sql           # Flavor 테이블 데이터
│   └── data_import.sql               # 전체 데이터 INSERT문
│
└── deprecated/                       # 구버전 백업
```

## 사용법

### 1. 의존성 설치

```bash
pip install selenium webdriver_manager pandas
```

### 2. 카페 크롤링

```bash
python scripts/crawlers/crawl_seoul_cafes.py
```

### 3. 원두 데이터 처리

```bash
python scripts/processors/process_coffee_dataset.py
```

### 4. 메뉴-원두 매핑 생성

```bash
python scripts/processors/map_menu_beans.py
```

### 5. SQL 파일 생성

```bash
python scripts/processors/csv_to_sql.py
```

### 6. DB Import

```bash
# 스키마 생성
mysql -u username -p database_name < sql/schema/schema.sql

# Flavor 데이터 입력
mysql -u username -p database_name < sql/schema/flavor_prod.sql

# 전체 데이터 입력
mysql -u username -p database_name < sql/data_import.sql
```

## 데이터 스키마

### roasteries (로스터리)
- `id`: PK
- `name`: 로스터리 이름
- `logo_url`, `website_url`: 로고/웹사이트 URL

### stores (매장)
- `id`: PK
- `roastery_id`: FK → roasteries
- `name`, `description`: 매장명, 설명
- `address`, `latitude`, `longitude`: 주소, 좌표
- `phone_number`, `category`: 연락처, 카테고리

### beans (원두)
- `id`: PK
- `roastery_id`: FK → roasteries (1 = Admin Roastery)
- `name`, `country`: 원두명, 원산지
- `farm`, `variety`: 농장, 품종
- `processing_method`, `roasting_level`: 가공법, 로스팅 레벨

### menus (메뉴)
- `id`: PK
- `store_id`: FK → stores
- `name`, `description`, `price`: 메뉴명, 설명, 가격

### menu_bean_mappings (메뉴-원두 매핑)
- `menu_id`: FK → menus
- `bean_id`: FK → beans
- `is_blended`: 블렌드 여부

### bean_flavor_notes (원두 플레이버 노트)
- `bean_id`: FK → beans
- `flavor_id`: FK → flavors

## 메뉴-원두 매핑 로직

1. **메뉴명 기반 매핑**: 메뉴 이름에 국가/지역명이 있으면 해당 국가 대표 원두 매핑
   - "에티오피아 아바야 게이샤" → 에티오피아 원두
   - "예가체프 G1" → 에티오피아 예가체프 원두

2. **가게 설명 기반 매핑**: 가게 description에 원두 국가 정보가 있으면 해당 가게 메뉴에 매핑
   - "브라질, 콜롬비아, 에티오피아 원두 사용" → 해당 국가 원두들 매핑

## 비커피 메뉴 필터링

다음 키워드가 포함된 메뉴는 제거됨:
- 차류: 녹차, 말차, 마차, 홍차, 카모마일 등
- 베이커리: 크로아상, 치아바타, 케이크 등
- 기타: 에이드, 스무디, 주스, 빙수 등

제거된 메뉴는 `data/debug/menus_removed.csv`에 백업됨.

## 특이사항

- `beans.roastery_id = 1`: Admin Roastery (출처 미정 원두)
- `stores.owner_id = 1`: 기본 관리자
- Flavor 데이터는 SCA Flavor Wheel 기반
