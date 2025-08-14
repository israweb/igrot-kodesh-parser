#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для запуска различных тестов парсера писем
"""

import sys
import os
import subprocess


def print_menu():
    """Печать меню тестов"""
    print("🧪 תפריט בדיקות ומפתחות למכתבים")
    print("=" * 60)
    print("📊 בדיקות:")
    print("1. ⚡ בדיקה מהירה של כרך א (3 דפים)")
    print("2. 📊 בדיקה מלאה של שלמות הפרסום")
    print("3. 🔍 בדיקה של כרך ספציפי")
    print("4. 🎯 בדיקה של כרך א עם בדיקה מלאה (169 מכתבים)")
    print()
    print("📋 דוחות:")
    print("5. 📄 ייצור דוח CSV לכרך אחד")
    print("6. 🌐 ייצור דוח HTML לכרך אחד")
    print("7. 📊 ייצור דוח JSON לכרך אחד")
    print("8. 📚 ייצור דוח לכמה כרכים")
    print()
    print("📇 אינדקסים:")
    print("9. 📇 ייצור אינדקס קישורים (כל הכרכים)")
    print("10. 🔗 ייצור אינדקס לכרכים ספציפיים")
    print()
    print("🔧 תיקון:")
    print("11. 🔧 תיקון מבנה דף")
    print("12. 👀 תצוגה מקדימה של מכתבים")
    print("13. 🆕 בדיקה של פורמט חדש")
    print()
    print("0. 🚪 יציאה")
    print("-" * 60)


def run_quick_test():
    """Запуск быстрого теста"""
    print("\n⚡ תחילת בדיקה מהירה...")
    result = subprocess.run([sys.executable, "test_volume_quick.py", "--volume", "א", "--expected", "169", "--pages", "3"])
    return result.returncode == 0


def run_full_completeness_test():
    """Запуск полного теста полноты"""
    print("\n📊 תחילת בדיקה מלאה של שלמות הפרסום...")
    result = subprocess.run([sys.executable, "test_volume_completeness.py"])
    return result.returncode == 0


def run_custom_volume_test():
    """Тест конкретного тома"""
    print("\nכרכים זמינים: א, ב, ג, ד, ה, ו, ז, ח, ט, י, יא, יב, יג, יד, טו, טז, יז, יח, יט, כ, כא, כב, כג")
    volume = input("הזן את הכרך לבדיקה: ").strip()
    
    if not volume:
        print("❌ הכרך לא נזכר")
        return False
    
    expected = input("מספר המכתבים המוצפן (לחץ על מספר לאוטומציה): ").strip()
    expected_arg = ["--expected", expected] if expected.isdigit() else []
    
    print(f"\n🔍 בדיקה של כרך {volume}...")
    result = subprocess.run([sys.executable, "test_volume_quick.py", "--volume", volume] + expected_arg)
    return result.returncode == 0


def run_full_aleph_test():
    """Полный тест тома א"""
    print("\n🎯 בדיקה מלאה של כרך א (169 מכתבים)...")
    
    # Импортируем тест напрямую для детального контроля
    try:
        from test_volume_completeness import VolumeCompletenessTest
        test = VolumeCompletenessTest()
        return test.test_volume_completeness("כרך א", expected_count=169)
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return False


def run_debug_structure():
    """Отладка структуры"""
    print("\n🔧 תחילת תיקון מבנה...")
    result = subprocess.run([sys.executable, "debug_volume_structure.py"])
    return result.returncode == 0


def run_csv_report():
    """Генерация CSV отчета"""
    volume = input("הזן את הכרך לדוח (א, ב, ג...): ").strip()
    if not volume:
        volume = "א"
    
    print(f"\n📄 ייצור דוח CSV לכרך {volume}...")
    result = subprocess.run([sys.executable, "generate_letters_report.py", "--volume", volume, "--format", "csv"])
    return result.returncode == 0


def run_html_report():
    """Генерация HTML отчета"""
    volume = input("הזן את הכרך לדוח (א, ב, ג...): ").strip()
    if not volume:
        volume = "א"
    
    print(f"\n🌐 ייצור דוח HTML לכרך {volume}...")
    result = subprocess.run([sys.executable, "generate_letters_report.py", "--volume", volume, "--format", "html"])
    return result.returncode == 0


def run_json_report():
    """Генерация JSON отчета"""
    volume = input("הזן את הכרך לדוח (א, ב, ג...): ").strip()
    if not volume:
        volume = "א"
    
    print(f"\n📊 ייצור דוח JSON לכרך {volume}...")
    result = subprocess.run([sys.executable, "generate_letters_report.py", "--volume", volume, "--format", "json"])
    return result.returncode == 0


def run_multiple_volumes_report():
    """Генерация отчета для нескольких томов"""
    print("\nהזן כרכים דרך רווח (למשל: א ב ג) או לחץ על מקום לכרכים ראשונים 3:")
    volumes_input = input("כרכים: ").strip()
    
    volumes_args = []
    if volumes_input:
        volumes = volumes_input.split()
        volumes_args = ["--volumes"] + volumes
    
    format_choice = input("פורמט דוח (csv/html/json) [csv]: ").strip().lower()
    if not format_choice:
        format_choice = "csv"
    
    print(f"\n📚 ייצור דוח לכמה כרכים ({format_choice.upper()})...")
    
    cmd = [sys.executable, "generate_letters_report.py", "--multiple", "--format", format_choice] + volumes_args
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_debug_structure():
    """Отладка структуры"""
    print("\n🔧 תחילת תיקון מבנה...")
    result = subprocess.run([sys.executable, "debug_volume_structure.py"])
    return result.returncode == 0


def run_preview():
    """Предварительный просмотр"""
    print("\n👀 תחילת תצוגה מקדימה...")
    result = subprocess.run([sys.executable, "preview_letters.py", "--preview-letters", "2"])
    return result.returncode == 0


def run_full_links_index():
    """Генерация полного индекса ссылок"""
    format_choice = input("פורמט אינדקס (csv/html/json) [html]: ").strip().lower()
    if not format_choice:
        format_choice = "html"
    
    print(f"\n📇 ייצור אינדקס קישורים מלא ({format_choice.upper()})...")
    print("⚠️  זיהוי: זה ייקח הרבה זמן!")
    
    confirm = input("המשך? (y/n): ").lower()
    if confirm != 'y':
        print("ביטול.")
        return False
    
    result = subprocess.run([sys.executable, "generate_links_index.py", "--format", format_choice])
    return result.returncode == 0


def run_custom_links_index():
    """Генерация индекса для конкретных томов"""
    print("\nהזן כרכים דרך רווח (למשל: א ב ג):")
    volumes_input = input("כרכים: ").strip()
    
    if not volumes_input:
        print("❌ הכרכים לא נזכרו")
        return False
    
    volumes = volumes_input.split()
    
    format_choice = input("פורמט אינדקס (csv/html/json) [html]: ").strip().lower()
    if not format_choice:
        format_choice = "html"
    
    print(f"\n🔗 ייצור אינדקס לכרכים {' '.join(volumes)} ({format_choice.upper()})...")
    
    cmd = [sys.executable, "generate_links_index.py", "--volumes"] + volumes + ["--format", format_choice]
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_new_format_test():
    """Тест нового формата"""
    print("\n🆕 בדיקה של פורמט חדש...")
    result = subprocess.run([sys.executable, "test_new_format.py"])
    return result.returncode == 0


def main():
    """Главная функция"""
    while True:
        print_menu()
        
        try:
            choice = input("בחר פעולה (0-13): ").strip()
            
            if choice == '0':
                print("👋 ביי!")
                break
            elif choice == '1':
                success = run_quick_test()
            elif choice == '2':
                success = run_full_completeness_test()
            elif choice == '3':
                success = run_custom_volume_test()
            elif choice == '4':
                success = run_full_aleph_test()
            elif choice == '5':
                success = run_csv_report()
            elif choice == '6':
                success = run_html_report()
            elif choice == '7':
                success = run_json_report()
            elif choice == '8':
                success = run_multiple_volumes_report()
            elif choice == '9':
                success = run_full_links_index()
            elif choice == '10':
                success = run_custom_links_index()
            elif choice == '11':
                success = run_debug_structure()
            elif choice == '12':
                success = run_preview()
            elif choice == '13':
                success = run_new_format_test()
            else:
                print("❌ בחירה לא תקינה")
                continue
            
            print(f"\n📊 תוצאת הבדיקה: {'✅ הצלחה' if success else '❌ הפסקה'}")
            
        except KeyboardInterrupt:
            print("\n\n👋 יציאה בהתראה")
            break
        except Exception as e:
            print(f"❌ שגיאה: {e}")
        
        input("\nלחץ על Enter להמשך...")


if __name__ == "__main__":
    main()
