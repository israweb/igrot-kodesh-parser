#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный интерфейс для управления скачиванием писем Аврат Кодеш
"""

import os
import sys
from letters_downloader import LettersDownloader


def print_header():
    """Печать заголовка"""
    print("=" * 70)
    print("📚 מנהל מכתבי אגרות קודש")
    print("=" * 70)
    print("מערכת להורדת מכתבי הרבי מאתר chabad.org")
    print("=" * 70)


def print_menu():
    """Печать меню"""
    print("\n🔸 בחר פעולה:")
    print("1. 👀 תצוגה מקדימה של כרכים ומכתבים")
    print("2. 📖 גיט מכתבים מכרך אחד") 
    print("3. 📚 גיט כל המכתבים מכל הכרכים")
    print("4. 🔍 הצג סטטיסטיקה של קבצי הורדה")
    print("5. 🗑️  נקה תיקיות מכתבי הורדה")
    print("6. ❓ ספרות")
    print("0. 🚪 יציאה")
    print("-" * 50)


def preview_letters():
    """Предварительный просмотр"""
    print("\n🔍 תחילת תצוגה מקדימה...")
    print("זה ייקח כמה דקות, כי יש לבדוק את כל הכרכים.")
    
    confirm = input("המשך? (y/n): ").lower()
    if confirm != 'y':
        return
    
    try:
        sys.path.append('../tests')
        from preview_letters import preview_volumes_and_letters
        preview_volumes_and_letters(max_letters_per_volume=3)
    except Exception as e:
        print(f"❌ שגיאה: {e}")


def download_single_volume():
    """Скачивание одного тома"""
    print("\n📖 גיט כרך אחד")
    print("כרכים זמינים: א, ב, ג, ד, ה, ו, ז, ח, ט, י, יא, יב, יג, יד, טו, טז, יז, יח, יט, כ, כא, כב, כג")
    
    volume = input("הזן מספר כרך (למשל, א או ב): ").strip()
    if not volume:
        print("❌ כרך לא צוין")
        return
    
    output_dir = input(f"תיקייה לשמירה (הקיש Enter ל- 'igrot_kodesh_volume_{volume}'): ").strip()
    if not output_dir:
        output_dir = f"igrot_kodesh_volume_{volume}"
    
    show_browser = input("הצג דפדפן בעת עבודה? (y/n): ").lower() == 'y'
    
    print(f"\n🚀 נתחיל גיט כרך כרך {volume}")
    print(f"📂 תיקייה: {output_dir}")
    print(f"👁️  דפדפן: {'נראה' if show_browser else 'מוסתר'}")
    
    confirm = input("התחיל גיט? (y/n): ").lower()
    if confirm != 'y':
        return
    
    try:
        from single_volume_downloader import main as single_main
        # מימוש ארגומנטים של שורת הפקודה
        sys.argv = ['single_volume_downloader.py', '--volume', volume, '--output-dir', output_dir]
        if show_browser:
            sys.argv.append('--visible')
        single_main()
    except Exception as e:
        print(f"❌ שגיאה: {e}")


def download_all_letters():
    """Скачивание всех писем"""
    print("\n📚 גיט כל המכתבים מכל הכרכים")
    print("⚠️  התראה: זה ייקח כמה שעות!")
    print("⚠️  תורדו מאות או אלפי מכתבים!")
    
    output_dir = input("תיקייה לשמירה (הקיש Enter ל- 'igrot_kodesh_all'): ").strip()
    if not output_dir:
        output_dir = "igrot_kodesh_all"
    
    show_browser = input("הצג דפדפן בעת עבודה? (y/n): ").lower() == 'y'
    
    print(f"\n🚀 הגדרות גיטה:")
    print(f"📂 תיקייה: {output_dir}")
    print(f"👁️  דפדפן: {'נראה' if show_browser else 'מוסתר'}")
    print(f"⏱️  זמן כמותי: כמה שעות")
    
    print("\n❗ התראה אחרונה:")
    print("זה הפעולה תורדת את כל המכתבים מכל הכרכים!")
    
    confirm = input("האם אתה בטוח שברצונך להתחיל? הזן 'YES' לאישור: ")
    if confirm != 'YES':
        print("ביטול.")
        return
    
    try:
        downloader = LettersDownloader(download_dir=output_dir, headless=not show_browser)
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        downloader.download_all_letters(start_url)
    except Exception as e:
        print(f"❌ שגיאה: {e}")


def show_statistics():
    """Показ статистики скачанных файлов"""
    print("\n📊 סטטיסטיקה של קבצי הורדה")
    print("-" * 50)
    
    # חיפוש תיקיות מכתבי הורדה
    folders_to_check = [
        "igrot_kodesh",
        "igrot_kodesh_all", 
        "igrot_kodesh_single",
        "downloaded_texts"
    ]
    
    # גם חיפוש תיקיות מספרי הכרכים
    for vol in ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט', 'כ', 'כא', 'כב', 'כג']:
        folders_to_check.append(f"igrot_kodesh_volume_{vol}")
    
    total_files = 0
    total_size = 0
    
    for folder in folders_to_check:
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.txt')]
            if files:
                folder_size = sum(os.path.getsize(os.path.join(folder, f)) for f in files)
                print(f"📂 {folder}: {len(files)} קבצים ({folder_size//1024} קב)")
                total_files += len(files)
                total_size += folder_size
    
    if total_files > 0:
        print("-" * 50)
        print(f"📝 כל המכתבים: {total_files}")
        print(f"💾 גודל כולל: {total_size//1024} קב ({total_size//1024//1024} מב)")
    else:
        print("📝 מכתבי הורדה לא נמצאו")


def clean_folders():
    """Очистка папок с письмами"""
    print("\n🗑️  ניקוי תיקיות מכתבי הורדה")
    print("⚠️  זה ימחק את כל המכתבים שהורדו!")
    
    # הצגת מה יורד
    show_statistics()
    
    confirm = input("\nהאם אתה בטוח שברצונך למחוק את כל המכתבים שהורדו? הזן 'DELETE' לאישור: ")
    if confirm != 'DELETE':
        print("ביטול.")
        return
    
    folders_to_clean = [
        "igrot_kodesh", "igrot_kodesh_all", "igrot_kodesh_single", "downloaded_texts"
    ]
    
    # הוספת תיקיות כרכים
    for vol in ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט', 'כ', 'כא', 'כב', 'כג']:
        folders_to_clean.append(f"igrot_kodesh_volume_{vol}")
    
    deleted_files = 0
    for folder in folders_to_clean:
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.txt')]
            for file in files:
                try:
                    os.remove(os.path.join(folder, file))
                    deleted_files += 1
                except:
                    pass
    
    print(f"✅ נמחק קבצים: {deleted_files}")


def show_help():
    """Показ справки"""
    print("\n❓ ספרות")
    print("=" * 50)
    print("📚 על התוכנה:")
    print("  זה התוכנה גורמת להורדת מכתבי הרבי (אגרות קודש)")
    print("  מאתר האתר הרשמי chabad.org")
    print()
    print("🔧 דרישות:")
    print("   - Python 3.6+")
    print("   - דפדפן Chrome")
    print("   - חיבור אינטרנט")
    print()
    print("📖 מצבי עבודה:")
    print("   1. תצוגה מקדימה - מציג את הכרכים הזמינים")
    print("   2. גיט כרך אחד - בחר כרך ספציפי")
    print("   3. גיט כל הכרכים - גיט מלא (שעות)")
    print()
    print("📂 תוצאות:")
    print("  מכתבי הורדה נשמרים בקבצי טקסט (.txt)")
    print("  כל קובץ מכיל מכתב אחד עם נתוני מטא-נתונים")
    print()
    print("⚠️  חשוב:")
    print("   - השתמש בתוכנה בזהירות")
    print("   - שמור על חוקים של האתר chabad.org")
    print("   - עשה נישואים בין הגיטות")


def main():
    """Главная функция"""
    print_header()
    
    while True:
        print_menu()
        
        try:
            choice = input("הזן מספר (0-6): ").strip()
            
            if choice == '0':
                print("👋 ביי וואי!")
                break
            elif choice == '1':
                preview_letters()
            elif choice == '2':
                download_single_volume()
            elif choice == '3':
                download_all_letters()
            elif choice == '4':
                show_statistics()
            elif choice == '5':
                clean_folders()
            elif choice == '6':
                show_help()
            else:
                print("❌ בחירה לא תקינה. נסה שוב.")
                
        except KeyboardInterrupt:
            print("\n\n👋 התוכנה נפסקה על ידי המשתמש. ביי וואי!")
            break
        except Exception as e:
            print(f"❌ שגיאה לא צפויה: {e}")
        
        input("\nלחץ Enter להמשך...")


if __name__ == "__main__":
    main()
