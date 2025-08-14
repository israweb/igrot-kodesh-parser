#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест нового формата названий файлов и заголовков
"""

import sys
import os
sys.path.append('../main')

from letters_downloader import LettersDownloader


def test_new_format():
    """Тест нового формата для нескольких писем"""
    print("🧪 בדיקת פורמט שמות חדש")
    print("=" * 50)
    print("📝 פורמט כותרת בקובץ: אגרות קודש - כרך א - מכתב פד")
    print("📁 פורמט שם קובץ: אק - כרך א - מכתב פד.txt")
    print("=" * 50)
    
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    try:
        downloader = LettersDownloader(download_dir="test_new_format", headless=True)
        
        # Получаем главную страницу
        print("🔍 טעינת דף הראשי...")
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ לא ניתן לטעון את דף הראשי")
            return
        
        # Находим том א
        volume_links = downloader.find_volume_links(soup, start_url)
        target_volume = None
        for volume_info in volume_links:
            if 'כרך א' in volume_info['title']:
                target_volume = volume_info
                break
        
        if not target_volume:
            print("❌ כרך א לא נמצא")
            return
        
        print(f"✅ כרך נמצא: {target_volume['title']}")
        
        # Получаем страницу тома
        volume_soup = downloader.get_page_with_selenium(target_volume['url'])
        if not volume_soup:
            print("❌ לא ניתן לטעון את דף הכרך")
            return
        
        # Находим первые 3 письма для теста
        letter_links = downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
        
        if not letter_links:
            print("❌ מכתבים לא נמצאו")
            return
        
        print(f"📝 מכתבים נמצאו: {len(letter_links)}")
        print("📄 נבדוק את שלושת המכתבים הראשונים...")
        
        # Скачиваем первые 3 письма
        for i, letter_info in enumerate(letter_links[:3], 1):
            print(f"\n📧 מכתב {i}/3: {letter_info['title']}")
            
            # Получаем תוכן המכתב
            letter_soup = downloader.get_page_with_selenium(letter_info['url'])
            if letter_soup:
                content = downloader.extract_letter_content(letter_soup, letter_info['url'])
                if content:
                    success = downloader.save_letter(content, letter_info)
                    if success:
                        print(f"✅ מכתב נשמר בפורמט חדש")
                    else:
                        print(f"❌ שגיאה בשמירה")
                else:
                    print(f"⚠️ לא ניתן להוציא את תוכן המכתב")
            else:
                print(f"❌ לא ניתן לטעון את דף המכתב")
        
        # מציגים את התוצאות
        print(f"\n📂 תוצאות:")
        print("=" * 50)
        
        if os.path.exists("test_new_format"):
            files = [f for f in os.listdir("test_new_format") if f.endswith('.txt')]
            
            print(f"📁 קבצים נוצרו ({len(files)}):")
            for file in files[:5]:  # מציגים את שלושת הראשונים
                print(f"   📄 {file}")
                
                # מציגים את תוכן הקובץ הראשון
                if file == files[0]:
                    file_path = os.path.join("test_new_format", file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            first_lines = f.read()[:200]
                            print(f"\n📝 תחילת הקובץ '{file}':")
                            print("-" * 30)
                            print(first_lines)
                            print("-" * 30)
                    except Exception as e:
                        print(f"❌ שגיאה בקריאת הקובץ: {e}")
        else:
            print("❌ תיקייה test_new_format לא נוצרה")
        
        downloader.close()
        
        print(f"\n🎉 בדיקה בוצעה!")
        print(f"📂 בדוק את תיקייה 'test_new_format' לצפייה בתוצאות")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")


if __name__ == "__main__":
    test_new_format()
