# 🚀 Инструкции по настройке Supabase для парсера Игрот Кодеш

## Шаг 1: Настройка базы данных в Supabase

1. **Откройте SQL Editor в вашем проекте Supabase**
2. **Скопируйте и выполните содержимое файла `supabase_schema.sql`**
3. **Убедитесь, что все таблицы созданы успешно**

## Шаг 2: Получение ключей API

1. В проекте Supabase переходите в **Settings → API**
2. Копируйте:
   - **Project URL** (например: `https://abcdefgh.supabase.co`)
   - **anon public** ключ

## Шаг 3: Настройка переменных окружения

### На Windows (PowerShell):
```powershell
$env:SUPABASE_URL="https://your-project-id.supabase.co"
$env:SUPABASE_ANON_KEY="your_anon_key_here"
```

### На Windows (Command Prompt):
```cmd
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_ANON_KEY=your_anon_key_here
```

### На macOS/Linux:
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key_here"
```

## Шаг 4: Установка зависимостей

```bash
pip install supabase python-dotenv
```

## Шаг 5: Запуск парсера

### Тестовый запуск (3 письма):
```bash
python supabase_parser.py --test
```

### Парсинг первых 10 писем:
```bash
python supabase_parser.py --volume א --max-letters 10
```

### Парсинг всего тома א:
```bash
python supabase_parser.py --volume א
```

## Шаг 6: Просмотр данных

1. Переходите в **Table Editor** в Supabase
2. Выбираете таблицу `letters` для просмотра писем
3. Выбираете таблицу `volumes` для просмотра томов
4. Выбираете таблицу `parse_logs` для просмотра логов

## Возможности парсера:

✅ **Автоматическое извлечение дат** из текста писем
✅ **Сохранение в Supabase** в реальном времени  
✅ **Логирование всех действий**
✅ **Обработка ошибок** и повторных попыток
✅ **Статистика парсинга**
✅ **Веб-интерфейс** через Supabase Dashboard

## Структура данных:

- **volumes**: информация о томах
- **letters**: письма с полными данными
- **parsing_stats**: общая статистика
- **parse_logs**: детальные логи парсинга

## Дополнительные возможности:

- **REST API**: автоматически генерируется Supabase
- **Realtime subscriptions**: обновления в реальном времени
- **Веб-интерфейс**: готовый дашборд для просмотра данных
