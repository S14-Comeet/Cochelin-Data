-- 한스브로스 카페 데이터 추가

-- Roasteries
INSERT INTO roasteries (id, name, logo_url, website_url) VALUES
(232, '한스브로스', NULL, NULL);

-- Stores
INSERT INTO stores (id, roastery_id, owner_id, name, description, address, latitude, longitude, phone_number, category, thumbnail_url, open_time, close_time, average_rating, review_count, visit_count, is_closed) VALUES
(247, 232, NULL, '한스브로스', NULL, '경기 용인시 수지구 문인로 64-1 1층 상가', 37.3595704, 127.105399, NULL, '아메리카노', NULL, '09:00:00', '21:00:00', 0, 0, 0, FALSE);

-- Menus
INSERT INTO menus (id, store_id, name, description, price, category, image_url) VALUES
(1366, 247, '핸드드립 커피', '직접 내리는 핸드드립 커피', 6000, '핸드드립', NULL),
(1367, 247, '아메리카노', '깔끔한 아메리카노', 4000, '아메리카노', NULL),
(1368, 247, '카페라떼', '부드러운 우유가 들어간 라떼', 5000, '라떼', NULL),
(1369, 247, '카푸치노', '풍성한 거품의 카푸치노', 5000, '라떼', NULL),
(1370, 247, '바닐라빈 라떼', '천연 바닐라빈이 들어간 달콤한 라떼', 5500, '라떼', NULL);