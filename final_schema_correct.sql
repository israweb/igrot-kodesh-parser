-- Финальная правильная схема без ненужных колонок
-- Выполните в SQL Editor Supabase

-- Удаляем и пересоздаем таблицу letters с правильной структурой
DROP TABLE IF EXISTS letters CASCADE;

CREATE TABLE letters (
    id BIGSERIAL PRIMARY KEY,
    volume_id BIGINT REFERENCES volumes(id) ON DELETE CASCADE,
    
    -- Данные тома
    tom_hebrew TEXT NOT NULL,           -- том на иврите (א, ב, ג...)
    tom_number INTEGER NOT NULL,        -- том цифрой (1, 2, 3...)
    
    -- Данные письма
    letter_hebrew TEXT NOT NULL,        -- номер письма на иврите (א, ב, ג...)
    letter_number INTEGER NOT NULL,     -- номер письма цифрой (1, 2, 3...)
    
    -- Данные даты (БЕЗ day_numeric и year_numeric)
    full_date_hebrew TEXT,              -- дата письма целиком на иврите
    day_hebrew TEXT,                    -- день на иврите (א, כא, לב...)
    month_hebrew TEXT,                  -- месяц на иврите (אדר, ניסן, תשרי...)
    year_hebrew TEXT,                   -- год на иврите (תרפח, תרצב...)
    
    -- Технические данные
    url TEXT NOT NULL,                  -- ссылка на письмо
    content TEXT,                       -- текст письма
    date_parsed BOOLEAN DEFAULT FALSE,  -- был ли распознан תאריך
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(volume_id, letter_number)
);

-- Индексы
CREATE INDEX idx_letters_volume_id ON letters(volume_id);
CREATE INDEX idx_letters_tom_number ON letters(tom_number);
CREATE INDEX idx_letters_letter_number ON letters(letter_number);
CREATE INDEX idx_letters_date_parsed ON letters(date_parsed);

-- Комментарии
COMMENT ON TABLE letters IS 'מכתבי אגרות קודש עם מבנה מתוקן';
COMMENT ON COLUMN letters.tom_hebrew IS 'מספר הכרך בעברית (א, ב, ג...)';
COMMENT ON COLUMN letters.tom_number IS 'מספר הכרך במספרים (1, 2, 3...)';
COMMENT ON COLUMN letters.letter_hebrew IS 'מספר המכתב בעברית (א, ב, ג...)';
COMMENT ON COLUMN letters.letter_number IS 'מספר המכתב במספרים (1, 2, 3...)';
COMMENT ON COLUMN letters.full_date_hebrew IS 'תאריך המכתב המלא בעברית';
COMMENT ON COLUMN letters.day_hebrew IS 'היום בעברית בלבד (א, כא, לב...)';
COMMENT ON COLUMN letters.month_hebrew IS 'החודש בעברית (אדר, ניסן...)';
COMMENT ON COLUMN letters.year_hebrew IS 'השנה בעברית (תרפח, תרצב...)';

-- Проверка структуры
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'letters' 
ORDER BY ordinal_position;
