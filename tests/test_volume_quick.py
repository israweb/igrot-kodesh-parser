#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест одного тома для проверки парсера
"""

import sys
import os
sys.path.append('../main')

from letters_downloader import LettersDownloader
import argparse


def quick_test_volume(volume_name="א", expected_count=None, max_pages_to_test=3):
    """
    Быстрый тест тома с ограничением по страницам
    
    Args:
        volume_name (str): Название тома (א, ב, ג и т.д.)
        expected_count (int): Ожидаемое количество писем
        max_pages_to_test (int): Максимум страниц для тестирования
    """
    print(f"⚡ בדיקה מהירה של פרסר מכתבים {volume_name}")
    print("=" * 50)
    
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    try:
        downloader = LettersDownloader(download_dir="test_quick", headless=True)
        
        # Получаем главную страницу
        print("🔍 טעינת דף ראשי...")
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ לא ניתן לטעון את הדף הראשי")
            return False
        
        # Находим тома
        volume_links = downloader.find_volume_links(soup, start_url)
        
        # Ищем нужный том
        target_volume = None
        for volume_info in volume_links:
            if f'כרך {volume_name}' in volume_info['title']:
                target_volume = volume_info
                break
        
        if not target_volume:
            print(f"❌ ספר 'כרך {volume_name}' לא נמצא")
            available = [v['title'] for v in volume_links]
            print(f"ספרים זמינים: {', '.join(available)}")
            return False
        
        print(f"✅ ספר נמצא: {target_volume['title']}")
        
        # Получаем страницу тома
        print("📄 טעינת דף ספר...")
        volume_soup = downloader.get_page_with_selenium(target_volume['url'])
        if not volume_soup:
            print("❌ לא ניתן לטעון את דף הספר")
            return False
        
        # Тестируем поиск писем (с ограничением по страницам для быстроты)
        print(f"📝 בדיקת חיפוש מכתבים (מקסימום {max_pages_to_test} דפים)...")
        
        # Модифицируем метод для ограничения тестирования
        original_max_pages = 50
        
        # Временно патчим максимальное количество страниц в парсере
        letters = []
        current_page = 1
        
        while current_page <= max_pages_to_test:
            if current_page == 1:
                page_url = target_volume['url']
                page_soup = volume_soup
            else:
                page_url = f"{target_volume['url']}/page/{current_page}"
                print(f"  📄 טעינת דף {current_page}: {page_url}")
                page_soup = downloader.get_page_with_selenium(page_url)
                if not page_soup:
                    print(f"  ❌ דף {current_page} לא נמצא")
                    break
            
            # Извлекаем письма со страницы
            page_letters = downloader._extract_letters_from_page(
                page_soup, page_url, target_volume['title'], current_page
            )
            
            if page_letters:
                letters.extend(page_letters)
                print(f"  📝 דף {current_page}: נמצאו {len(page_letters)} מכתבים")
            else:
                print(f"  📝 דף {current_page}: מכתבים לא נמצאו")
            
            # Проверяем наличие следующей страницы
            next_page_link = page_soup.find('a', {'id': 'Paginator_NextPage'})
            if not next_page_link:
                next_link = page_soup.find('link', {'rel': 'next'})
                if not next_link:
                    print(f"  📄 הגענו לדף האחרון: {current_page}")
                    break
            
            current_page += 1
        
        # Убираем дубликаты
        unique_letters = []
        seen_urls = set()
        for letter in letters:
            if letter['url'] not in seen_urls:
                seen_urls.add(letter['url'])
                unique_letters.append(letter)
        
        # Результаты
        print(f"\n📊 תוצאות בדיקה מהירה:")
        print("-" * 50)
        print(f"📄 דפים שנבדקו: {min(current_page, max_pages_to_test)}")
        print(f"📝 מכתבים נמצאו: {len(unique_letters)}")
        print(f"🔗 URL ייחודיים: {len(seen_urls)}")
        
        if expected_count:
            estimated_total = len(unique_letters) * (expected_count / (50 * max_pages_to_test))
            print(f"🎯 כמות כוללת צפויה: {expected_count}")
            print(f"📈 הערכה לפי דפים שנבדקו: ~{estimated_total:.0f}")
            
            if abs(estimated_total - expected_count) < expected_count * 0.2:  # 20% допуск
                print("✅ הערכה קרובה לצפויה - הפרסר עובד כראוי")
                success = True
            else:
                print("⚠️  הערכה רחוקה מהצפויה - ייתכן בעיות")
                success = False
        else:
            success = len(unique_letters) > 0
        
        # דוגמאות למכתבים שנמצאו
        if unique_letters:
            print(f"\n📋 דוגמאות למכתבים שנמצאו:")
            for i, letter in enumerate(unique_letters[:5], 1):
                print(f"   {i}. {letter['title']}")
        
        # בדיקת מבנה
        pages_found = set(letter.get('page', 1) for letter in unique_letters)
        print(f"\n📄 מכתבים נמצאו בדפים: {sorted(pages_found)}")
        
        downloader.close()
        return success
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='בדיקה מהירה של פרסר מכתבים')
    parser.add_argument('--volume', default='א', help='ספר לבדיקה (א, ב, ג...)')
    parser.add_argument('--expected', type=int, help='כמות מכתבים צפויה')
    parser.add_argument('--pages', type=int, default=3, help='מקסימום דפים לבדיקה')
    
    args = parser.parse_args()
    
    print("⚡ בדיקה מהירה של פרסר מכתבים")
    print("=" * 50)
    print(f"📖 ספר: כרך {args.volume}")
    expected_count = args.expected or (169 if args.volume == 'א' else None)
    if expected_count:
        print(f"🎯 מכתבים צפויים: {expected_count}")
    print(f"📄 מקסימום דפים: {args.pages}")
    print("=" * 50)
    
    success = quick_test_volume(args.volume, expected_count, args.pages)
    
    if success:
        print("\n✅ בדיקה מהירה בוצעה!")
        print("💡 לבדיקה מלאה יופעל: python test_volume_completeness.py")
    else:
        print("\n❌ בדיקה מהירה גילה בעיות!")
        print("🔧 מומלץ להפעיל בדיקה מלאה לניתוח מפורט")


if __name__ == "__main__":
    main()
