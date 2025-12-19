# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Comeet-Data is a data collection and processing pipeline for building a dataset of **Specialty Cafes** in Seoul. The project collects cafe data through two approaches:
1. **Public Data Processing**: Filtering SEMAS (Small Enterprise and Market Service) datasets to identify specialty cafes
2. **Web Crawling**: Scraping Naver Map for detailed store information including menus and bean details

## Commands

### Run the Naver Map crawler
```bash
# Version 1: Targets Gangnam-gu, Seongdong-gu, Mapo-gu only
python crawlers/crawl_specialty_cafes.py

# Version 2: Targets all of Seoul (up to 200 stores)
python crawlers_v2/crawl_seoul_specialty.py
```

### Run preprocessing scripts
```bash
# Process SEMAS public data (소상공인시장진흥공단 data)
python preprocess_cafes.py

# Process cafe_dataset.csv
python preprocess_cafe_dataset.py
```

### Install dependencies
```bash
pip install selenium webdriver_manager pandas
```

## Architecture

### Data Flow
1. **Input Sources**:
   - SEMAS CSV data (Korean public data on businesses)
   - `cafe_dataset.csv` (alternative dataset)
   - Naver Map (crawled data)

2. **Processing Logic** (shared across scripts):
   - Include only target districts (강남구, 성동구, 마포구 for preprocessing; configurable for crawlers)
   - Include known specialty franchises (테라로사, 프릳츠, 블루보틀, etc.)
   - Exclude mass-market franchises (이디야, 투썸플레이스, 메가커피, etc.)
   - Exclude non-cafe keywords (디저트, 베이커리, 스터디, etc.)

3. **Output**: CSV files matching `schema.sql` structure for `stores` and `menus` tables

### Crawler Versions
- `crawlers/`: Original version - filters by specific districts and requires bean info keywords
- `crawlers_v2/`: Updated version - targets all Seoul, filters coffee menus from non-coffee items, collects up to 200 stores

### Key Filtering Lists (defined in preprocessing scripts and crawlers)
- `SPECIALTY_FRANCHISES`: Brands to always include
- `EXCLUDE_FRANCHISES`: Mass-market chains to exclude
- `EXCLUDE_KEYWORDS`: Non-cafe business indicators
- `BEAN_KEYWORDS`: Terms indicating specialty coffee (원산지, 가공법, 커피용어)

## Database Schema

The `schema.sql` defines the target MySQL schema with key tables:
- `stores`: Core cafe information (name, address, coordinates, ratings)
- `menus`: Menu items linked to stores
- `beans`: Coffee bean details (origin, variety, processing method)
- `menu_bean_mappings`: Links menus to specific beans
- `flavors`: Hierarchical flavor notes (SCA Flavor Wheel based)
- `cupping_notes`: Detailed sensory scores for reviews
