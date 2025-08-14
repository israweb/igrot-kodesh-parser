#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת חילוץ תאריכים מ-10 מכתבים ראשונים
"""

import sys
import os
import csv
import json
import re
from datetime import datetime
sys.path.append('../main')

from letters_downloader import LettersDownloader


def hebrew_letter_to_number(hebrew_letter):
    """המרת אות עברית למספר"""
    if not hebrew_letter:
        return 0
        
    # הסרת גרשיים וגרש
    clean_letter = hebrew_letter.replace('"', '').replace("'", '')
    
    hebrew_numbers = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
        'י': 10, 'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19,
        'כ': 20, 'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30,
        'לא': 31, 'לב': 32, 'לג': 33, 'לד': 34, 'לה': 35, 'לו': 36, 'לז': 37, 'לח': 38, 'לט': 39, 'מ': 40,
        'מא': 41, 'מב': 42, 'מג': 43, 'מד': 44, 'מה': 45, 'מו': 46, 'מז': 47, 'מח': 48, 'מט': 49, 'נ': 50
    }
    
    return hebrew_numbers.get(clean_letter) or hebrew_numbers.get(hebrew_letter, 0)


class HebrewDateParser:
    def __init__(self):
        # מילון חודשי השנה העברית
        self.hebrew_months = {
            'תשרי': 1, 'חשון': 2, 'חשוון': 2, 'כסלו': 3, 'טבת': 4, 'שבט': 5, 'אדר': 6,
            'אדר א': 6, 'אדר ב': 7, 'אד"ר': 6, 'אד"ש': 7, 'אדר ראשון': 6, 'אדר שני': 7,
            'ניסן': 8, 'אייר': 9, 'סיון': 10, 'סיוון': 10,
            'תמוז': 11, 'אב': 12, 'מנחם אב': 12, 'מנ"א': 12, 'אלול': 13
        }
        
        # מיפוי קיצורי חודשים מיוחדים
        self.month_abbreviations = {
            'אד"ר': 'אדר א',
            'אד"ש': 'אדר ב',
            'מנ"א': 'מנחם אב'
        }
    
    def extract_date_from_text(self, text):
        """חילוץ תאריך מתחילת טקסט המכתב - רק שורה ראשונה"""
        if not text:
            return None
        
        # רק השורה הראשונה - התאריך תמיד שם
        lines = text.strip().split('\n')
        if not lines:
            return None
            
        first_line = lines[0].strip()
        if not first_line:
            return None
        
        print(f"   🔍 בודק שורה ראשונה: {first_line}")
        
        # דפוס תאריך עברי
        hebrew_date = self._parse_hebrew_date(first_line)
        if hebrew_date:
            return hebrew_date
        else:
            print(f"   ❌ לא נמצא תאריך בשורה: {first_line}")
            return None
    
    def _parse_hebrew_date(self, line):
        """פרסור תאריך עברי - מחפש חודש ראשית"""
        try:
            print(f"      📝 מפרסר: '{line}'")
            
            # הסרת ב"ה ואותיות נוספות
            clean_line = re.sub(r'ב"ה,?\s*', '', line)
            clean_line = re.sub(r'[,.]', '', clean_line)
            print(f"      נוקה: '{clean_line}'")
            
            # מחפשים חודש תחילה
            words = clean_line.split()
            month_pos = -1
            month_str = None
            month_num = None
            
            # חיפוש חודש ברשימת המילים
            for i, word in enumerate(words):
                clean_word = word.replace('"', '').replace("'", '')
                if clean_word in self.hebrew_months or word in self.hebrew_months:
                    month_pos = i
                    month_str = word
                    month_num = self._parse_month(word)
                    print(f"      📅 חודש נמצא במיקום {i}: '{word}' = {month_num}")
                    break
            
            if month_pos == -1:
                print(f"      ❌ חודש לא נמצא")
                return None
            
            # חיפוש יום ושנה סביב החודש
            day_str = None
            year_str = None
            day_num = None
            year_num = None
            
            # חיפוש יום - יכול להיות לפני או אחרי החודש
            for i in range(max(0, month_pos-2), min(len(words), month_pos+2)):
                if i == month_pos:
                    continue
                word = words[i]
                # בדיקה אם זה יום (מספר קטן, עד 31)
                day_candidate = self._hebrew_letter_to_number_improved(word)
                if day_candidate and 1 <= day_candidate <= 31:
                    day_str = word
                    day_num = day_candidate
                    print(f"      📅 יום נמצא במיקום {i}: '{word}' = {day_num}")
                    break
            
            # חיפוש שנה - בדרך כלל בסוף
            for i in range(len(words)-1, -1, -1):
                if i == month_pos:
                    continue
                word = words[i]
                # בדיקה אם זה שנה
                year_candidate = self._parse_hebrew_year_improved(word)
                if year_candidate and year_candidate > 5600:  # שנות עולם
                    year_str = word
                    year_num = year_candidate
                    print(f"      📅 שנה נמצאה במיקום {i}: '{word}' = {year_num}")
                    break
            
            if day_num and month_num and year_num:
                month_hebrew_display = self.month_abbreviations.get(month_str, month_str)
                
                # הסרת גרשיים ואפוסטרופים וה' מהתצוגה
                clean_day_hebrew = day_str.replace('"', '').replace("'", '') if day_str else ''
                clean_month_hebrew = month_hebrew_display.replace('"', '').replace("'", '') if month_hebrew_display else ''
                raw_year_hebrew = year_str.replace('"', '').replace("'", '').replace('ה\'', '') if year_str else ''
                
                # הוספת תר/תש לשנים דו-ספרתיות
                enhanced_year_hebrew = self._enhance_year_hebrew(raw_year_hebrew, year_num)
                
                clean_full_date = f"{clean_day_hebrew} {clean_month_hebrew} {enhanced_year_hebrew}"
                
                return {
                    'day_numeric': day_num,  # יום בספרים
                    'day': day_num,
                    'day_hebrew': clean_day_hebrew,
                    'month': month_num,
                    'month_hebrew': clean_month_hebrew,
                    'year_numeric': year_num,  # שנה בספרים
                    'year': year_num,
                    'year_hebrew': enhanced_year_hebrew,  # שנה עברית עם תר/תש
                    'full_date_hebrew': clean_full_date,
                    'date_type': 'עברי'
                }
            else:
                print(f"      ❌ לא ניתן להמיר: יום={day_num}, חודש={month_num}, שנה={year_num}")
        
        except Exception as e:
            print(f"      ❌ שגיאה בפרסור: {e}")
        
        return None
    
    def _enhance_year_hebrew(self, raw_year_hebrew, year_numeric):
        """הוספת תר/תש לשנים דו-ספרתיות"""
        if not raw_year_hebrew or not year_numeric:
            return raw_year_hebrew
        
        # הסרת ה' מתחילת השנה
        clean_raw_year = raw_year_hebrew
        if raw_year_hebrew.startswith('ה'):
            clean_raw_year = raw_year_hebrew[1:]
            print(f"         🧹 הסרת ה' מתחילת השנה: {raw_year_hebrew} -> {clean_raw_year}")
        
        # בדיקה אם השנה היא דו-ספרתית (לא מתחילה ב-תר או תש)
        if not clean_raw_year.startswith(('תר', 'תש')) and len(clean_raw_year) <= 2:
            # חישוב השנה הדו-ספרתית
            short_year = year_numeric % 100
            
            if short_year > 60:
                enhanced = f"תר{clean_raw_year}"
                print(f"         ✨ שנה דו-ספרתית > 60: {clean_raw_year} -> {enhanced}")
                return enhanced
            elif short_year < 60:
                enhanced = f"תש{clean_raw_year}"
                print(f"         ✨ שנה דו-ספרתית < 60: {clean_raw_year} -> {enhanced}")
                return enhanced
        
        return clean_raw_year
    
    def _hebrew_letter_to_number_improved(self, hebrew_letter):
        """המרת אות עברית למספר - גרסה משופרת"""
        if not hebrew_letter:
            return 0
        
        # הסרת גרשיים וגרש
        clean_letter = hebrew_letter.replace('"', '').replace("'", '')
        
        # מילון מורחב כולל עם גרשיים
        hebrew_numbers = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
            'י': 10, 'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19,
            'כ': 20, 'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30,
            'לא': 31, 'לב': 32, 'לג': 33, 'לד': 34, 'לה': 35, 'לו': 36, 'לז': 37, 'לח': 38, 'לט': 39, 'מ': 40,
            'מא': 41, 'מב': 42, 'מג': 43, 'מד': 44, 'מה': 45, 'מו': 46, 'מז': 47, 'מח': 48, 'מט': 49, 'נ': 50,
            'נא': 51, 'נב': 52, 'נג': 53, 'נד': 54, 'נה': 55, 'נו': 56, 'נז': 57, 'נח': 58, 'נט': 59, 'ס': 60,
            'סא': 61, 'סב': 62, 'סג': 63, 'סד': 64, 'סה': 65, 'סו': 66, 'סז': 67, 'סח': 68, 'סט': 69, 'ע': 70,
            'עא': 71, 'עב': 72, 'עג': 73, 'עד': 74, 'עה': 75, 'עו': 76, 'עז': 77, 'עח': 78, 'עט': 79, 'פ': 80,
            'פא': 81, 'פב': 82, 'פג': 83, 'פד': 84, 'פה': 85, 'פו': 86, 'פז': 87, 'פח': 88, 'פט': 89, 'צ': 90,
            'צא': 91, 'צב': 92, 'צג': 93, 'צד': 94, 'צה': 95, 'צו': 96, 'צז': 97, 'צח': 98, 'צט': 99, 'ק': 100,
            # עם גרשיים
            'א"': 1, 'ב"': 2, 'ג"': 3, 'ד"': 4, 'ה"': 5, 'ו"': 6, 'ז"': 7, 'ח"': 8, 'ט"': 9,
            'י"': 10, 'כ"א': 21, 'כ"ב': 22, 'כ"ג': 23, 'כ"ד': 24, 'כ"ה': 25, 'כ"ו': 26, 'כ"ז': 27, 'כ"ח': 28, 'כ"ט': 29
        }
        
        # נסה גם עם הגרשיים המקוריים
        result = hebrew_numbers.get(clean_letter) or hebrew_numbers.get(hebrew_letter, 0)
        print(f"         🔢 המרת '{hebrew_letter}' -> {result}")
        return result
    
    def _parse_month(self, month_str):
        """פרסור חודש כולל קיצורים"""
        # הסרת גרשיים
        clean_month = month_str.replace('"', '').replace("'", '')
        
        month = self.hebrew_months.get(clean_month) or self.hebrew_months.get(month_str)
        print(f"         📅 חודש '{month_str}' -> {month}")
        return month
    
    def _parse_hebrew_year_improved(self, year_str):
        """פרסור שנה עברית משופר"""
        print(f"         🗓️ מפרסר שנה: '{year_str}'")
        
        # הסרת קידומות כמו ה' וגרשיים
        clean_year = re.sub(r'^ה\'', '', year_str)
        clean_year = clean_year.replace('"', '').replace("'", '')
        print(f"         🗓️ אחרי ניקוי: '{clean_year}'")
        
        # בדיקה אם זה שנה דו-ספרתית (שתי אותיות)
        if len(clean_year) == 2:
            year_value = self._hebrew_letter_to_number_improved(clean_year)
            print(f"         🗓️ שנה דו-ספרתית: {clean_year} = {year_value}")
            
            if year_value > 80:
                # שנות 80+ = 56 + המספר (5600 + המספר)
                result = 5600 + year_value
                print(f"         🗓️ שנה דו-ספרתית > 80: {year_value} -> 56{year_value:02d} = {result}")
                return result
            elif year_value < 60:
                # שנות עד 60 = 57 + המספר (5700 + המספר)  
                result = 5700 + year_value
                print(f"         🗓️ שנה דו-ספרתית < 60: {year_value} -> 57{year_value:02d} = {result}")
                return result
            else:
                # שנות 60-80 = 56 + המספר (5600 + המספר)
                result = 5600 + year_value
                print(f"         🗓️ שנה דו-ספרתית 60-80: {year_value} -> 56{year_value:02d} = {result}")
                return result
        
        # טיפול בשנים קצרות עם גרש מקורי (כמו פ"ח)
        original_clean = year_str.replace('ה\'', '')
        if len(original_clean) == 3 and original_clean[1] == '"':
            first_letter = original_clean[0]
            second_letter = original_clean[2]
            
            # ק = 100, צ = 90, פ = 80
            tens_map = {'ק': 100, 'צ': 90, 'פ': 80, 'ע': 70, 'ס': 60, 'נ': 50, 'מ': 40, 'ל': 30, 'כ': 20, 'י': 10}
            units_value = self._hebrew_letter_to_number_improved(second_letter)
            
            if first_letter in tens_map and units_value > 0:
                short_year = tens_map[first_letter] + units_value
                result = 5600 + short_year
                print(f"         🗓️ שנה עם גרש {original_clean} = {short_year} = {result}")
                return result

        
        # פרסור תרצ"ב = 5692
        if clean_year.startswith('תרצ'):
            # תרצ = תר (5600) + צ (90) = 5690
            suffix = clean_year[3:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5690 + suffix_val
                print(f"         🗓️ תרצ ({5690}) + {suffix} ({suffix_val}) = {result}")
                return result
            return 5690
        
        # פרסור תרפ"ט = 5689
        if clean_year.startswith('תרפ'):
            # תרפ = תר (5600) + פ (80) = 5680
            suffix = clean_year[3:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5680 + suffix_val
                print(f"         🗓️ תרפ ({5680}) + {suffix} ({suffix_val}) = {result}")
                return result
            return 5680
        
        # פרסור כללי של תר...
        if clean_year.startswith('תר'):
            # תר = 5600
            suffix = clean_year[2:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5600 + suffix_val
                print(f"         🗓️ תר ({5600}) + {suffix} ({suffix_val}) = {result}")
                return result
            return 5600
        
        # פורמטים אחרים
        base_years = {
            'תש': 5700, 'תשי': 5710, 'תשכ': 5720, 'תשל': 5730,
            'תשמ': 5740, 'תשנ': 5750, 'תש"': 5700
        }
        
        for prefix, base in base_years.items():
            if clean_year.startswith(prefix):
                suffix = clean_year[len(prefix):].replace('"', '').replace("'", '')
                suffix_value = self._hebrew_letter_to_number_improved(suffix) if suffix else 0
                result = base + suffix_value
                print(f"         🗓️ {prefix} ({base}) + {suffix} ({suffix_value}) = {result}")
                return result
        
        return None


def test_10_letters():
    print("📇 בדיקת חילוץ תאריכים - 10 מכתבים ראשונים")
    print("=" * 60)
    
    downloader = LettersDownloader(download_dir="temp_test", headless=True)
    date_parser = HebrewDateParser()
    
    try:
        # קבלת דף ראשי
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ לא ניתן לטעון דף ראשי")
            return
        
        # חיפוש כרך א
        volume_links = downloader.find_volume_links(soup, start_url)
        target_volume = None
        for volume_info in volume_links:
            if 'כרך א' in volume_info['title']:
                target_volume = volume_info
                break
        
        if not target_volume:
            print("❌ כרך א לא נמצא")
            return
        
        print(f"✅ נמצא: {target_volume['title']}")
        
        # קבלת דף הכרך
        volume_soup = downloader.get_page_with_selenium(target_volume['url'])
        if not volume_soup:
            print("❌ לא ניתן לטעון דף הכרך")
            return
        
        # חיפוש מכתבים
        letter_links = downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
        
        # בדיקת 10 מכתבים ראשונים
        test_results = []
        for i, letter in enumerate(letter_links[:10], 1):
            print(f"\n📝 מכתב {i}: {letter['title']}")
            print(f"🔗 URL: {letter['url']}")
            
            # חילוץ מספר המכתב המקורי
            letter_match = re.search(r'מכתב\s+([א-ת]+)', letter['title'])
            letter_hebrew = letter_match.group(1) if letter_match else f"מכתב {i}"
            
            # המרת מספר המכתב מעברית לערבית
            letter_arabic = hebrew_letter_to_number(letter_hebrew) or i
            
            # טעינת תוכן המכתב
            letter_soup = downloader.get_page_with_selenium(letter['url'])
            date_info = None
            
            if letter_soup:
                content = downloader.extract_letter_content(letter_soup, letter['url'])
                if content:
                    print(f"📄 אורך תוכן: {len(content)} תווים")
                    print(f"🔤 תחילת המכתב: {content[:100]}...")
                    
                    # חילוץ תאריך
                    date_info = date_parser.extract_date_from_text(content)
                    if date_info:
                        print(f"✅ תאריך נמצא: {date_info['full_date_hebrew']}")
                    else:
                        print("❌ תאריך לא נמצא")
                else:
                    print("❌ לא ניתן לחלץ תוכן")
            else:
                print("❌ לא ניתן לטעון מכתב")
            
            # הכנת רשומה
            result = {
                'volume_arabic': 1,
                'volume_hebrew': 'א',
                'letter_arabic': letter_arabic,
                'letter_hebrew': letter_hebrew,
                'day_numeric': date_info['day_numeric'] if date_info else '',
                'day_hebrew': date_info['day_hebrew'] if date_info else '',
                'month_hebrew': date_info['month_hebrew'] if date_info else '',
                'year_numeric': date_info['year_numeric'] if date_info else '',
                'year_hebrew': date_info['year_hebrew'] if date_info else '',
                'full_date_hebrew': date_info['full_date_hebrew'] if date_info else '',
                'url': letter['url']
            }
            
            test_results.append(result)
        
        # יצירת דוחות
        create_reports(test_results)
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
    finally:
        downloader.close()


def create_reports(data):
    """יצירת דוחות CSV ו-HTML"""
    
    # יצירת תיקייה
    os.makedirs('test_reports', exist_ok=True)
    
    # שמות קבועים (יחליפו גרסאות קודמות)
    csv_file = 'test_reports/test_10_letters.csv'
    html_file = 'test_reports/test_10_letters.html'
    
    # יצירת CSV
    create_csv_report(data, csv_file)
    
    # יצירת HTML
    create_html_report(data, html_file)
    
    print(f"\n🎉 דוחות נוצרו בהצלחה!")
    print(f"📄 CSV: {csv_file}")
    print(f"🌐 HTML: {html_file}")


def create_csv_report(data, filename):
    """יצירת דוח CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['volume_arabic', 'volume_hebrew', 'letter_arabic', 'letter_hebrew', 
                        'day_numeric', 'day_hebrew', 'month_hebrew', 'year_numeric', 'year_hebrew', 'full_date_hebrew', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # כותרות
            writer.writerow({
                'volume_arabic': 'מס\' כרך',
                'volume_hebrew': 'כרך',
                'letter_arabic': 'מס\' מכתב',
                'letter_hebrew': 'מכתב',
                'day_numeric': 'יום מספר',
                'day_hebrew': 'יום עברי',
                'month_hebrew': 'חודש',
                'year_numeric': 'שנה מספר',
                'year_hebrew': 'שנה עברית',
                'full_date_hebrew': 'תאריך מלא',
                'url': 'קישור'
            })
            
            # נתונים
            for row in data:
                writer.writerow(row)
        
        print(f"✅ דוח CSV נוצר: {filename}")
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת CSV: {e}")


def create_html_report(data, filename):
    """יצירת דוח HTML"""
    try:
        html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>בדיקת 10 מכתבים - מכתבי אגרות קודש עם תאריכים</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
            direction: rtl;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .search-box {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #e8f6f3;
            border-radius: 5px;
        }}
        .search-box input {{
            width: 22%;
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
            margin: 0 1%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #e8f4f8;
        }}
        .letter-link {{
            color: #2980b9;
            text-decoration: none;
            font-weight: bold;
        }}
        .letter-link:hover {{
            text-decoration: underline;
        }}
        .hebrew-number {{
            font-weight: bold;
            color: #8e44ad;
        }}
        .arabic-number {{
            font-weight: bold;
            color: #27ae60;
        }}
        .date-cell {{
            background-color: #fff3cd;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
    <script>
        function searchTable() {{
            var volumeInput = document.getElementById("volumeSearch").value.toLowerCase();
            var letterInput = document.getElementById("letterSearch").value.toLowerCase();
            var monthInput = document.getElementById("monthSearch").value.toLowerCase();
            var yearInput = document.getElementById("yearSearch").value.toLowerCase();
            var table = document.getElementById("indexTable");
            var tr = table.getElementsByTagName("tr");
            
            for (var i = 1; i < tr.length; i++) {{
                var td = tr[i].getElementsByTagName("td");
                if (td.length < 9) continue;
                
                var volumeMatch = true;
                var letterMatch = true;
                var monthMatch = true;
                var yearMatch = true;
                
                if (volumeInput) {{
                    var volumeText = (td[0].innerHTML + td[1].innerHTML).toLowerCase();
                    volumeMatch = volumeText.indexOf(volumeInput) > -1;
                }}
                
                if (letterInput) {{
                    var letterText = (td[2].innerHTML + td[3].innerHTML).toLowerCase();
                    letterMatch = letterText.indexOf(letterInput) > -1;
                }}
                
                if (monthInput) {{
                    var monthText = td[5].innerHTML.toLowerCase();
                    monthMatch = monthText.indexOf(monthInput) > -1;
                }}
                
                if (yearInput) {{
                    var yearText = td[6].innerHTML.toLowerCase();
                    yearMatch = yearText.indexOf(yearInput) > -1;
                }}
                
                if (volumeMatch && letterMatch && monthMatch && yearMatch) {{
                    tr[i].style.display = "";
                }} else {{
                    tr[i].style.display = "none";
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📇 בדיקת 10 מכתבים - מכתבי אגרות קודש עם תאריכים</h1>
        
        <div class="summary">
            <div><strong>📚 כרכים:</strong> 1 (א)</div>
            <div><strong>📝 מכתבים נבדקו:</strong> {len(data)}</div>
            <div><strong>🕐 תאריך יצירה:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</div>
            <div><strong>🧪 סוג:</strong> בדיקת פרסינג תאריכים</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="volumeSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש כרך">
            <input type="text" id="letterSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש מכתב">
            <input type="text" id="monthSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש חודש">
            <input type="text" id="yearSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש שנה">
        </div>
        
        <table id="indexTable">
            <thead>
                <tr>
                    <th>מס' כרך</th>
                    <th>כרך</th>
                    <th>מס' מכתב</th>
                    <th>מכתב</th>
                    <th>יום מספר</th>
                    <th>יום עברי</th>
                    <th>חודש</th>
                    <th>שנה מספר</th>
                    <th>שנה עברית</th>
                    <th>תאריך מלא</th>
                    <th>קישור</th>
                </tr>
            </thead>
            <tbody>
"""

        for entry in data:
            html_content += f"""
                <tr>
                    <td class="arabic-number">{entry['volume_arabic']}</td>
                    <td class="hebrew-number">{entry['volume_hebrew']}</td>
                    <td class="arabic-number">{entry['letter_arabic']}</td>
                    <td class="hebrew-number">{entry['letter_hebrew']}</td>
                    <td class="arabic-number date-cell">{entry.get('day_numeric', '')}</td>
                    <td class="hebrew-number date-cell">{entry.get('day_hebrew', '')}</td>
                    <td class="hebrew-number date-cell">{entry.get('month_hebrew', '')}</td>
                    <td class="arabic-number date-cell">{entry.get('year_numeric', '')}</td>
                    <td class="hebrew-number date-cell">{entry.get('year_hebrew', '')}</td>
                    <td class="date-cell">{entry.get('full_date_hebrew', '')}</td>
                    <td><a href="{entry['url']}" class="letter-link" target="_blank">פתח מכתב</a></td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>📇 דוח בדיקה נוצר אוטומטית למטרת בדיקת מערכת פרסינג התאריכים</p>
            <p>🗓️ תאריכים מוצגים בפורמט עברי בלבד</p>
            <p>🔗 קישורים מובילים ישירות למכתבים באתר chabad.org</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)
        
        print(f"✅ דוח HTML נוצר: {filename}")
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת HTML: {e}")


if __name__ == "__main__":
    test_10_letters()
