-- Очистка базы данных для нового теста
-- Выполните в SQL Editor Supabase

-- Очистка таблицы писем
DELETE FROM letters;

-- Очистка логов парсинга
DELETE FROM parse_logs;

-- Сброс счетчиков в статистике
UPDATE parsing_stats SET 
    total_letters = 0,
    letters_with_dates = 0,
    last_parse_date = NOW()
WHERE id = 1;

-- Сброс статистики томов
UPDATE volumes SET 
    total_letters = 0
WHERE id = 1;

-- Перезапуск последовательности ID для таблицы писем
ALTER SEQUENCE letters_id_seq RESTART WITH 1;
ALTER SEQUENCE parse_logs_id_seq RESTART WITH 1;

-- Проверка что все очищено
SELECT 'letters' as table_name, COUNT(*) as count FROM letters
UNION ALL
SELECT 'parse_logs' as table_name, COUNT(*) as count FROM parse_logs
UNION ALL  
SELECT 'volumes' as table_name, COUNT(*) as count FROM volumes;
