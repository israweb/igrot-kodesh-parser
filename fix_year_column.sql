-- Возвращаем колонку year_number (год в цифрах)
-- Выполните в SQL Editor Supabase

-- Добавляем обратно колонку year_number
ALTER TABLE letters ADD COLUMN year_number INTEGER;

-- Добавляем индекс для быстрого поиска по годам
CREATE INDEX idx_letters_year_number ON letters(year_number) WHERE year_number IS NOT NULL;

-- Комментарий к колонке
COMMENT ON COLUMN letters.year_number IS 'השנה במספרים (5688, 5692...)';

-- Проверяем финальную структуру
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'letters' 
ORDER BY ordinal_position;
