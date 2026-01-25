-- テスト用スキーマを作成
CREATE SCHEMA IF NOT EXISTS sc_test_1;

-- 読み込み元テーブル：元のデータ（暗号化なし）
CREATE TABLE IF NOT EXISTS sc_test_1.user_order (
    id VARCHAR(32),
    name VARCHAR(100),
    birthdate DATE
);

-- 書き込み先テーブル：暗号化済みデータ
CREATE TABLE IF NOT EXISTS sc_test_1.user_order_encrypted (
    id VARCHAR(32),
    name VARCHAR(100),
    birthdate DATE,
    encrypted_id VARCHAR(4096)
);

-- 読み込み元テーブルにサンプルデータを挿入
INSERT INTO sc_test_1.user_order (id, name, birthdate) VALUES
('10000000000000000000000000000007', 'Alice', '1990-01-01'),
('10000000000000000000000000000007', 'Bob', '1995-06-15'),
('10000000000000000000000000000002', 'Charlie', '1988-12-25'),
('10000000000000000000000000000001', 'whisky', '1988-12-25');