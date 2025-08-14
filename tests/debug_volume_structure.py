#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный скрипт для изучения структуры страниц томов
"""

import sys
import os
sys.path.append('../main')

from letters_downloader import LettersDownloader
import re


def debug_volume_structure():
    """Изучение структуры страницы тома"""
    
    # Возьмем первый том для анализа
    volume_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643805/jewish/page.htm"
    
    print("🔍 חקר מבנה דף כרך")
    print("=" * 50)
    print(f"📖 ניתוח כרך: {volume_url}")
    
    try:
        downloader = LettersDownloader(download_dir="temp", headless=False)  # Показываем браузер
        
        # Получаем страницу
        soup = downloader.get_page_with_selenium(volume_url)
        if not soup:
            print("❌ לא ניתן לטעון את הדף")
            return
        
        print(f"✅ הדף טעון בהצלחה")
        print(f"📄 גודל HTML: {len(str(soup))} תווים")
        
        # Анализируем все ссылки
        print("\n🔗 ניתוח כל הקישורים:")
        print("-" * 50)
        
        all_links = soup.find_all('a', href=True)
        print(f"סך הכל נמצאו קישורים: {len(all_links)}")
        
        # Группируем ссылки по типам
        letter_candidates = []
        navigation_links = []
        other_links = []
        
        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Пропускаем пустые или очень короткие тексты
            if not text or len(text) < 2:
                continue
                
            # Классифицируем ссылки
            if 'article_cdo' in href and any(char.isdigit() for char in text):
                if 'page.htm' not in href:  # Исключаем ссылки на другие страницы томов
                    letter_candidates.append((text, href))
            elif any(nav in text.lower() for nav in ['browse', 'next', 'previous', 'home', 'back']):
                navigation_links.append((text, href))
            else:
                other_links.append((text, href))
        
        print(f"\n📝 כתבים פוטנציאליים ({len(letter_candidates)}):")
        for i, (text, href) in enumerate(letter_candidates[:10], 1):  # Показываем первые 10
            print(f"   {i}. {text}")
            print(f"      URL: {href}")
        
        if len(letter_candidates) > 10:
            print(f"   ... ועוד {len(letter_candidates) - 10} חוקרים")
        
        print(f"\n🧭 קישורים ניווט ({len(navigation_links)}):")
        for text, href in navigation_links[:5]:
            print(f"   - {text} -> {href}")
        
        print(f"\n🔗 קישורים אחרים ({len(other_links)}):")
        for text, href in other_links[:5]:
            print(f"   - {text} -> {href}")
        
        # Поиск специфичных паттернов
        print(f"\n🔍 חיפוש פטרנים ספציפיים:")
        print("-" * 50)
        
        # Ищем ссылки с датами
        date_pattern = r'\d{1,2}[./]\d{1,2}[./]\d{2,4}'
        date_links = []
        for link in all_links:
            text = link.get_text(strip=True)
            if re.search(date_pattern, text):
                date_links.append((text, link['href']))
        
        print(f"📅 קישורים עם תאריכים ({len(date_links)}):")
        for text, href in date_links[:10]:
            print(f"   - {text} -> {href}")
        
        # Ищем ссылки с номерами писем
        number_pattern = r'(?:letter|письмо|מכתב).*?\d+|^\d+\.'
        numbered_links = []
        for link in all_links:
            text = link.get_text(strip=True)
            if re.search(number_pattern, text, re.IGNORECASE):
                numbered_links.append((text, link['href']))
        
        print(f"\n🔢 קישורים עם מספרים ({len(numbered_links)}):")
        for text, href in numbered_links[:10]:
            print(f"   - {text} -> {href}")
        
        # Проверяем содержимое страницы на предмет списков
        print(f"\n📋 ניתוח מבנה דף:")
        print("-" * 50)
        
        # Ищем списки (ul, ol)
        lists = soup.find_all(['ul', 'ol'])
        print(f"נמצאו רשימות: {len(lists)}")
        
        for i, lst in enumerate(lists[:3], 1):
            items = lst.find_all('li')
            print(f" רשימה {i}: {len(items)} פריטים")
            if items:
                for j, item in enumerate(items[:3], 1):
                    link = item.find('a')
                    if link:
                        print(f"    {j}. {link.get_text(strip=True)[:50]}...")
        
        # Ищем таблицы
        tables = soup.find_all('table')
        print(f"\nנמצאו טבלאות: {len(tables)}")
        
        for i, table in enumerate(tables[:2], 1):
            rows = table.find_all('tr')
            print(f"  טבלה {i}: {len(rows)} שורות")
            if rows:
                for j, row in enumerate(rows[:3], 1):
                    cells = row.find_all(['td', 'th'])
                    if cells and len(cells) > 0:
                        text = cells[0].get_text(strip=True)[:30]
                        print(f"    {j}. {text}...")
        
        # Ищем div-ы с классами, которые могут содержать письма
        print(f"\n📦 ניתוח שינויים DIV:")
        divs_with_class = soup.find_all('div', class_=True)
        class_counts = {}
        for div in divs_with_class:
            classes = ' '.join(div.get('class', []))
            class_counts[classes] = class_counts.get(classes, 0) + 1
        
        print("כינויים ראשונים של שינויים DIV:")
        for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  .{cls}: {count} שינויים")
        
        input("\n⏸️  לחץ על Enter כדי לסגור את הדפדפן ולהשלים את החקירה...")
        
        downloader.close()
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")


if __name__ == "__main__":
    debug_volume_structure()
