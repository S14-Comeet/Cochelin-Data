-- SCA Coffee Taster's Flavor Wheel 데이터
-- 계층 구조: Level 1 (대분류) -> Level 2 (중분류) -> Level 3 (소분류)

-- ============================================================================
-- Level 1: 대분류 (9개)
-- ============================================================================

INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (1, 'FRUITY', NULL, 1, 'fruity', '과일향', '과일의 신선하고 달콤한 향미', '#ED1C24'),
       (2, 'SOUR_FERMENTED', NULL, 1, 'sour_fermented', '발효/신맛', '발효된 듯한 신맛과 알코올성 향미', '#F16521'),
       (3, 'GREEN_VEGETATIVE', NULL, 1, 'green_vegetative', '녹색/채소향', '풀, 채소, 허브 같은 향미', '#017E3B'),
       (4, 'OTHER', NULL, 1, 'other', '기타', '기타 특이한 향미', '#00A5D0'),
       (5, 'ROASTED', NULL, 1, 'roasted', '로스팅향', '로스팅으로 인한 구수하고 탄 향미', '#6F4E37'),
       (6, 'SPICES', NULL, 1, 'spices', '향신료', '향신료의 자극적이고 따뜻한 향미', '#D2691E'),
       (7, 'NUTTY_COCOA', NULL, 1, 'nutty_cocoa', '견과/코코아', '견과류와 초콜릿의 고소한 향미', '#8B4513'),
       (8, 'SWEET', NULL, 1, 'sweet', '단맛', '설탕, 꿀, 캐러멜의 단 향미', '#F4CD00'),
       (9, 'FLORAL', NULL, 1, 'floral', '꽃향', '꽃의 우아하고 향긋한 향미', '#EC008B');

-- ============================================================================
-- Level 2: 중분류
-- ============================================================================

-- FRUITY (1) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (101, 'BERRY', 1, 2, 'fruity/berry', '베리류', '블랙베리, 라즈베리 등 베리류의 향미', '#B81141'),
       (102, 'DRIED_FRUIT', 1, 2, 'fruity/dried_fruit', '건과일', '건포도, 자두 등 말린 과일의 향미', '#D23828'),
       (103, 'OTHER_FRUIT', 1, 2, 'fruity/other_fruit', '기타 과일', '코코넛, 체리, 석류 등', '#F16D79'),
       (104, 'CITRUS_FRUIT', 1, 2, 'fruity/citrus_fruit', '감귤류', '레몬, 오렌지 등 시트러스 향미', '#F89E4F');

-- SOUR/FERMENTED (2) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (201, 'SOUR', 2, 2, 'sour_fermented/sour', '신맛', '산도가 높은 신 맛', '#F7A44C'),
       (202, 'ALCOHOL_FERMENTED', 2, 2, 'sour_fermented/alcohol_fermented', '알코올/발효', '발효된 알코올성 향미', '#F89E4F');

-- GREEN/VEGETATIVE (3) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (301, 'OLIVE_OIL', 3, 2, 'green_vegetative/olive_oil', '올리브 오일', '올리브 오일의 부드럽고 기름진 향미', '#7AB51D'),
       (302, 'RAW', 3, 2, 'green_vegetative/raw', '날것', '날것의 풋풋한 향미', '#6FB03F'),
       (303, 'GREEN_VEGETATIVE_SUB', 3, 2, 'green_vegetative/vegetative', '채소향', '채소의 향미', '#5FA84C'),
       (304, 'BEANY', 3, 2, 'green_vegetative/beany', '콩 향', '콩의 향미', '#4F9C52');

-- OTHER (4) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (401, 'PAPERY_MUSTY', 4, 2, 'other/papery_musty', '종이/곰팡이', '종이나 곰팡이 냄새', '#5B8FA3'),
       (402, 'CHEMICAL', 4, 2, 'other/chemical', '화학적', '화학약품 같은 향미', '#4682B4');

-- ROASTED (5) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (501, 'PIPE_TOBACCO', 5, 2, 'roasted/pipe_tobacco', '파이프 담배', '담배의 향미', '#8B6F47'),
       (502, 'TOBACCO', 5, 2, 'roasted/tobacco', '담배', '담배 향', '#7D5A3C'),
       (503, 'BURNT', 5, 2, 'roasted/burnt', '탄', '탄 향미', '#3E2723'),
       (504, 'CEREAL', 5, 2, 'roasted/cereal', '시리얼', '곡물의 구수한 향미', '#A67C52');

-- SPICES (6) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (601, 'PUNGENT', 6, 2, 'spices/pungent', '자극적', '강한 자극성 향신료', '#CD853F'),
       (602, 'PEPPER', 6, 2, 'spices/pepper', '후추', '후추의 향미', '#D2691E'),
       (603, 'BROWN_SPICE', 6, 2, 'spices/brown_spice', '갈색 향신료', '시나몬, 정향 등', '#8B4513');

-- NUTTY/COCOA (7) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (701, 'NUTTY', 7, 2, 'nutty_cocoa/nutty', '견과류', '견과류의 고소한 향미', '#8B7355'),
       (702, 'COCOA', 7, 2, 'nutty_cocoa/cocoa', '코코아', '초콜릿의 향미', '#3E2723');

-- SWEET (8) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (801, 'BROWN_SUGAR', 8, 2, 'sweet/brown_sugar', '흑설탕', '흑설탕의 단맛', '#F4D03F'),
       (802, 'VANILLA', 8, 2, 'sweet/vanilla', '바닐라', '바닐라의 부드러운 단맛', '#F8E08E'),
       (803, 'VANILLIN', 8, 2, 'sweet/vanillin', '바닐린', '바닐라 향', '#FCF3CF'),
       (804, 'OVERALL_SWEET', 8, 2, 'sweet/overall_sweet', '전반적 단맛', '전체적인 단맛', '#FEF9E7'),
       (805, 'SWEET_AROMATICS', 8, 2, 'sweet/sweet_aromatics', '달콤한 향', '달콤한 향기', '#F9E79F');

-- FLORAL (9) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (901, 'BLACK_TEA', 9, 2, 'floral/black_tea', '홍차', '홍차의 향미', '#E91E63'),
       (902, 'FLORAL_SUB', 9, 2, 'floral/floral', '꽃향', '꽃의 향기', '#EC008B');

-- ============================================================================
-- Level 3: 소분류
-- ============================================================================

-- BERRY (101) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (10101, 'BLACKBERRY', 101, 3, 'fruity/berry/blackberry', '블랙베리', '블랙베리의 진하고 달콤한 향미', '#4A0E29'),
       (10102, 'RASPBERRY', 101, 3, 'fruity/berry/raspberry', '라즈베리', '라즈베리의 새콤달콤한 향미', '#8B1538'),
       (10103, 'BLUEBERRY', 101, 3, 'fruity/berry/blueberry', '블루베리', '블루베리의 부드럽고 달콤한 향미', '#6B1F42'),
       (10104, 'STRAWBERRY', 101, 3, 'fruity/berry/strawberry', '딸기', '딸기의 상큼하고 달콤한 향미', '#B81141');

-- DRIED FRUIT (102) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (10201, 'RAISIN', 102, 3, 'fruity/dried_fruit/raisin', '건포도', '건포도의 농축된 단맛', '#A93226'),
       (10202, 'PRUNE', 102, 3, 'fruity/dried_fruit/prune', '자두', '말린 자두의 향미', '#943126');

-- OTHER FRUIT (103) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (10301, 'COCONUT', 103, 3, 'fruity/other_fruit/coconut', '코코넛', '코코넛의 향미', '#E85D75'),
       (10302, 'CHERRY', 103, 3, 'fruity/other_fruit/cherry', '체리', '체리의 향미', '#D23539'),
       (10303, 'POMEGRANATE', 103, 3, 'fruity/other_fruit/pomegranate', '석류', '석류의 새콤달콤한 향미', '#C44B4F'),
       (10304, 'PINEAPPLE', 103, 3, 'fruity/other_fruit/pineapple', '파인애플', '파인애플의 열대 과일 향미', '#F7856D'),
       (10305, 'GRAPE', 103, 3, 'fruity/other_fruit/grape', '포도', '포도의 향미', '#D45D79'),
       (10306, 'APPLE', 103, 3, 'fruity/other_fruit/apple', '사과', '사과의 상큼한 향미', '#F08080'),
       (10307, 'PEACH', 103, 3, 'fruity/other_fruit/peach', '복숭아', '복숭아의 부드러운 향미', '#F7A191'),
       (10308, 'PEAR', 103, 3, 'fruity/other_fruit/pear', '배', '배의 청량한 향미', '#F9B59F');

-- CITRUS FRUIT (104) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (10401, 'GRAPEFRUIT', 104, 3, 'fruity/citrus_fruit/grapefruit', '자몽', '자몽의 쌉싸름한 감귤 향미', '#FCAF58'),
       (10402, 'ORANGE', 104, 3, 'fruity/citrus_fruit/orange', '오렌지', '오렌지의 달콤한 감귤 향미', '#FCB045'),
       (10403, 'LEMON', 104, 3, 'fruity/citrus_fruit/lemon', '레몬', '레몬의 신 감귤 향미', '#F9C74F'),
       (10404, 'LIME', 104, 3, 'fruity/citrus_fruit/lime', '라임', '라임의 강한 신맛', '#F4D56D');

-- SOUR (201) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (20101, 'SOUR_AROMATICS', 201, 3, 'sour_fermented/sour/sour_aromatics', '신 향', '신 향기', '#F9C74F'),
       (20102, 'ACETIC_ACID', 201, 3, 'sour_fermented/sour/acetic_acid', '아세트산', '식초 같은 신맛', '#F7B32B'),
       (20103, 'BUTYRIC_ACID', 201, 3, 'sour_fermented/sour/butyric_acid', '부티르산', '버터 같은 신맛', '#F39C12'),
       (20104, 'ISOVALERIC_ACID', 201, 3, 'sour_fermented/sour/isovaleric_acid', '이소발레르산', '치즈 같은 신맛', '#E67E22'),
       (20105, 'CITRIC_ACID', 201, 3, 'sour_fermented/sour/citric_acid', '시트르산', '감귤류의 신맛', '#F8C471'),
       (20106, 'MALIC_ACID', 201, 3, 'sour_fermented/sour/malic_acid', '말산', '사과의 신맛', '#F5B041');

-- ALCOHOL/FERMENTED (202) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (20201, 'WINEY', 202, 3, 'sour_fermented/alcohol_fermented/winey', '와인 같은', '와인의 향미', '#F39C12'),
       (20202, 'WHISKEY', 202, 3, 'sour_fermented/alcohol_fermented/whiskey', '위스키', '위스키의 향미', '#E67E22'),
       (20203, 'FERMENTED', 202, 3, 'sour_fermented/alcohol_fermented/fermented', '발효', '발효된 향미', '#D68910'),
       (20204, 'OVERRIPE', 202, 3, 'sour_fermented/alcohol_fermented/overripe', '과숙', '과하게 익은 과일 향', '#CA6F1E');

-- RAW (302) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (30201, 'UNDER_RIPE', 302, 3, 'green_vegetative/raw/under_ripe', '덜 익음', '덜 익은 향미', '#82B74B'),
       (30202, 'PEAPOD', 302, 3, 'green_vegetative/raw/peapod', '완두콩 꼬투리', '완두콩 껍질의 향미', '#7AB51D');

-- GREEN/VEGETATIVE (303) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (30301, 'FRESH', 303, 3, 'green_vegetative/vegetative/fresh', '신선한', '신선한 채소 향', '#78B159'),
       (30302, 'DARK_GREEN', 303, 3, 'green_vegetative/vegetative/dark_green', '진한 녹색', '진한 녹색 채소', '#6FAE4E'),
       (30303, 'VEGETATIVE', 303, 3, 'green_vegetative/vegetative/vegetative', '채소', '채소 향', '#66AB43'),
       (30304, 'HAY_LIKE', 303, 3, 'green_vegetative/vegetative/hay_like', '건초', '건초 향', '#5FA43D'),
       (30305, 'HERB_LIKE', 303, 3, 'green_vegetative/vegetative/herb_like', '허브', '허브 향', '#579E37');

-- PAPERY/MUSTY (401) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (40101, 'STALE', 401, 3, 'other/papery_musty/stale', '묵은', '묵은 향미', '#7FA99B'),
       (40102, 'CARDBOARD', 401, 3, 'other/papery_musty/cardboard', '골판지', '골판지 냄새', '#75A594'),
       (40103, 'PAPERY', 401, 3, 'other/papery_musty/papery', '종이', '종이 냄새', '#6BA18D'),
       (40104, 'WOODY', 401, 3, 'other/papery_musty/woody', '나무', '나무 향', '#619D86'),
       (40105, 'MOLDY_DAMP', 401, 3, 'other/papery_musty/moldy_damp', '곰팡이/습함', '곰팡이 냄새', '#579980'),
       (40106, 'MUSTY_DUSTY', 401, 3, 'other/papery_musty/musty_dusty', '곰팡이/먼지', '먼지 냄새', '#4D9579'),
       (40107, 'MUSTY_EARTHY', 401, 3, 'other/papery_musty/musty_earthy', '곰팡이/흙', '흙 냄새', '#439172'),
       (40108, 'ANIMALIC', 401, 3, 'other/papery_musty/animalic', '동물성', '동물 같은 향', '#398D6B');

-- CHEMICAL (402) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (40201, 'BITTER', 402, 3, 'other/chemical/bitter', '쓴맛', '화학적 쓴맛', '#5499C7'),
       (40202, 'SALTY', 402, 3, 'other/chemical/salty', '짠맛', '짠 맛', '#5DADE2'),
       (40203, 'MEDICINAL', 402, 3, 'other/chemical/medicinal', '약품', '약품 냄새', '#85C1E9'),
       (40204, 'PETROLEUM', 402, 3, 'other/chemical/petroleum', '석유', '석유 냄새', '#AED6F1'),
       (40205, 'SKUNKY', 402, 3, 'other/chemical/skunky', '스컹크', '스컹크 냄새', '#D6EAF8'),
       (40206, 'RUBBER', 402, 3, 'other/chemical/rubber', '고무', '고무 냄새', '#EBF5FB');

-- BURNT (503) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (50301, 'ACRID', 503, 3, 'roasted/burnt/acrid', '매캐한', '매캐한 탄 냄새', '#5D4037'),
       (50302, 'ASHY', 503, 3, 'roasted/burnt/ashy', '재', '재의 향미', '#6D4C41'),
       (50303, 'SMOKY', 503, 3, 'roasted/burnt/smoky', '연기', '연기 향', '#795548'),
       (50304, 'BROWN_ROAST', 503, 3, 'roasted/burnt/brown_roast', '갈색 로스트', '진하게 로스팅된 향미', '#8D6E63');

-- CEREAL (504) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (50401, 'GRAIN', 504, 3, 'roasted/cereal/grain', '곡물', '곡물의 구수한 향', '#A1887F'),
       (50402, 'MALT', 504, 3, 'roasted/cereal/malt', '맥아', '맥아의 향미', '#BCAAA4');

-- BROWN SPICE (603) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (60301, 'ANISE', 603, 3, 'spices/brown_spice/anise', '아니스', '아니스(회향)의 향미', '#CD853F'),
       (60302, 'NUTMEG', 603, 3, 'spices/brown_spice/nutmeg', '육두구', '육두구의 향미', '#D2691E'),
       (60303, 'CINNAMON', 603, 3, 'spices/brown_spice/cinnamon', '시나몬', '시나몬의 향미', '#8B4513'),
       (60304, 'CLOVE', 603, 3, 'spices/brown_spice/clove', '정향', '정향의 향미', '#A0522D');

-- NUTTY (701) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (70101, 'PEANUTS', 701, 3, 'nutty_cocoa/nutty/peanuts', '땅콩', '땅콩의 고소한 향미', '#C19A6B'),
       (70102, 'HAZELNUT', 701, 3, 'nutty_cocoa/nutty/hazelnut', '헤이즐넛', '헤이즐넛의 고소한 향미', '#8B7355'),
       (70103, 'ALMOND', 701, 3, 'nutty_cocoa/nutty/almond', '아몬드', '아몬드의 향미', '#EFDECD');

-- COCOA (702) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (70201, 'CHOCOLATE', 702, 3, 'nutty_cocoa/cocoa/chocolate', '초콜릿', '밀크 초콜릿의 향미', '#4A2511'),
       (70202, 'DARK_CHOCOLATE', 702, 3, 'nutty_cocoa/cocoa/dark_chocolate', '다크 초콜릿', '다크 초콜릿의 진한 향미', '#1B0A03');

-- BROWN SUGAR (801) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (80101, 'MOLASSES', 801, 3, 'sweet/brown_sugar/molasses', '당밀', '당밀의 진한 단맛', '#F4D03F'),
       (80102, 'MAPLE_SYRUP', 801, 3, 'sweet/brown_sugar/maple_syrup', '메이플 시럽', '메이플 시럽의 단맛', '#F9E79F'),
       (80103, 'CARAMELIZED', 801, 3, 'sweet/brown_sugar/caramelized', '캐러멜화', '캐러멜의 향미', '#F8E08E'),
       (80104, 'HONEY', 801, 3, 'sweet/brown_sugar/honey', '꿀', '꿀의 단맛', '#FEF9E7');

-- FLORAL (902) 하위
INSERT INTO flavors (id, code, parent_id, level, path, name, description, color_hex)
VALUES (90201, 'CHAMOMILE', 902, 3, 'floral/floral/chamomile', '카모마일', '카모마일의 향기', '#F5B7B1'),
       (90202, 'ROSE', 902, 3, 'floral/floral/rose', '장미', '장미의 향기', '#EC7063'),
       (90203, 'JASMINE', 902, 3, 'floral/floral/jasmine', '자스민', '자스민의 향기', '#E74C3C');