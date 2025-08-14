#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת חילוץ תאריכים ממכתבים - מוגבל ל-3 מכתבים
"""

import sys
import os
import csv
import json
import re
from datetime import datetime
sys.path.append('../main')

from letters_downloader import LettersDownloader


class HebrewDateParser:
    def __init__(self):
        # מילון חודשי השנה העברית
        self.hebrew_months = {
            'תשרי': 1, 'חשון': 2, 'חשוון': 2, 'כסלו': 3, 'טבת': 4, 'שבט': 5, 'אדר': 6,
            'אדר א': 6, 'אדר ב': 7, 'אד"ר': 6, 'אד"ש': 7, 'אדר ראשון': 6, 'אדר שני': 7,
            'ניסן': 8, 'אייר': 9, 'סיון': 10, 'סיוון': 10,
            'תמוז': 11, 'אב': 12, 'אלול': 13
        }
        
        # מיפוי קיצורי חודשים מיוחדים
        self.month_abbreviations = {
            'אד"ר': 'אדר א',
            'אד"ש': 'אדר ב'
        }
    
    def extract_date_from_text(self, text):
        """חילוץ תאריך מתחילת טקסט המכתב"""
        if not text:
            return None
        
        # מחפשים את השורות הראשונות
        lines = text.strip().split('\n')[:3]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            print(f"   🔍 בודק שורה: {line[:50]}...")
            
            # דפוס תאריך עברי: ב"ה, ט' שבט תש"ד
            hebrew_date = self._parse_hebrew_date(line)
            if hebrew_date:
                return hebrew_date
        
        return None
    
    def _parse_hebrew_date(self, line):
        """פרסור תאריך עברי"""
        try:
            # הסרת ב"ה ואותיות נוספות
            clean_line = re.sub(r'ב"ה,?\s*', '', line)
            clean_line = re.sub(r'[,.]', '', clean_line)
            
            # דפוסים שונים לתאריכים:
            
            # דפוס 1: כ"א אדר פ"ח (יום חודש שנה קצרה)
            pattern1 = r'([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)'
            match1 = re.search(pattern1, clean_line)
            
            # דפוס 2: ב"ה א' כ"א אד"ר ה'תרצ"ב (עם קידומות)
            pattern2 = r'(?:א\'|ב\'|ג\'|ד\'|ה\'|ו\'|ש\')?\s*([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)\s+(?:ה\')?([א-ת]+"?[א-ת]*)'
            match2 = re.search(pattern2, clean_line)
            
            match = match1 or match2
            
            if match:
                day_str, month_str, year_str = match.groups()
                print(f"      📅 נמצא: יום={day_str}, חודש={month_str}, שנה={year_str}")
                
                # המרת יום
                day = self._hebrew_letter_to_number_improved(day_str)
                
                # המרת חודש (כולל קיצורים)
                month = self._parse_month(month_str)
                
                # המרת שנה (משופרת)
                year = self._parse_hebrew_year_improved(year_str)
                
                if day and month and year:
                    return {
                        'day': day,
                        'day_hebrew': day_str,
                        'month': month,
                        'month_hebrew': month_str,
                        'year': year,
                        'year_hebrew': year_str,
                        'full_date_hebrew': f"{day_str} {month_str} {year_str}",
                        'date_type': 'עברי'
                    }
        
        except Exception as e:
            print(f"      ❌ שגיאה בפרסור: {e}")
        
        return None
    
    def _parse_hebrew_year(self, year_str):
        """פרסור שנה עברית פשוט"""
        base_years = {
            'תש': 5700, 'תשי': 5710, 'תשכ': 5720, 'תשל': 5730,
            'תשמ': 5740, 'תשנ': 5750, 'תש"': 5700, 'תר': 5600
        }
        
        for prefix, base in base_years.items():
            if year_str.startswith(prefix):
                suffix = year_str[len(prefix):].replace('"', '').replace("'", '')
                suffix_value = self._hebrew_letter_to_number(suffix) or 0
                return base + suffix_value
        
        return None
    
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
            # עם גרשיים
            'א"': 1, 'ב"': 2, 'ג"': 3, 'ד"': 4, 'ה"': 5, 'ו"': 6, 'ז"': 7, 'ח"': 8, 'ט"': 9,
            'י"': 10, 'כ"א': 21, 'כ"ב': 22, 'כ"ג': 23, 'כ"ד': 24, 'כ"ה': 25, 'כ"ו': 26, 'כ"ז': 27, 'כ"ח': 28, 'כ"ט': 29,
            # פורמטים נוספים
            'כח': 28, 'כט': 29, 'לא': 31
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
        
        # הסרת קידומות כמו ה'
        clean_year = re.sub(r'^ה\'', '', year_str)
        
        # פרסור תרצ"ב כמו 5692
        if clean_year.startswith('תר'):
            # תר = 5600
            suffix = clean_year[2:].replace('"', '').replace("'", '')
            
            # צ = 90
            if suffix.startswith('צ'):
                base = 5690
                remainder = suffix[1:]
                if remainder:
                    remainder_val = self._hebrew_letter_to_number_improved(remainder)
                    result = base + remainder_val
                    print(f"         🗓️ תרצ + {remainder} = {result}")
                    return result
                return 5690
        
        # פורמטים אחרים
        base_years = {
            'תש': 5700, 'תשי': 5710, 'תשכ': 5720, 'תשל': 5730,
            'תשמ': 5740, 'תשנ': 5750, 'תש"': 5700, 'תר': 5600,
            'תרפ': 5680, 'תרצ': 5690, 'פ"ח': 88  # שנה קצרה
        }
        
        for prefix, base in base_years.items():
            if clean_year.startswith(prefix):
                suffix = clean_year[len(prefix):].replace('"', '').replace("'", '')
                suffix_value = self._hebrew_letter_to_number_improved(suffix) if suffix else 0
                
                # אם זו שנה קצרה (פ"ח = 88), הוסף לבסיס גבוה יותר
                if prefix == 'פ"ח':
                    result = 5600 + 88  # תרפ"ח = 5688
                else:
                    result = base + suffix_value
                
                print(f"         🗓️ {prefix} + {suffix_value} = {result}")
                return result
        
        return None
    
    def _hebrew_letter_to_number(self, hebrew_letter):
        """המרת אות עברית למספר - גרסה ישנה לתאימות"""
        return self._hebrew_letter_to_number_improved(hebrew_letter)


def test_date_extraction():
    print("📇 בדיקת חילוץ תאריכים - 3 מכתבים ראשונים")
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
        
        # בדיקת 3 מכתבים ראשונים
        test_results = []
        for i, letter in enumerate(letter_links[:3], 1):
            print(f"\n📝 מכתב {i}: {letter['title']}")
            print(f"🔗 URL: {letter['url']}")
            
            # טעינת תוכן המכתב
            letter_soup = downloader.get_page_with_selenium(letter['url'])
            if letter_soup:
                content = downloader.extract_letter_content(letter_soup, letter['url'])
                if content:
                    print(f"📄 אורך תוכן: {len(content)} תווים")
                    print(f"🔤 תחילת המכתב: {content[:100]}...")
                    
                    # חילוץ תאריך
                    date_info = date_parser.extract_date_from_text(content)
                    if date_info:
                        print(f"✅ תאריך נמצא: {date_info['full_date_hebrew']}")
                        test_results.append({
                            'letter_title': letter['title'],
                            'url': letter['url'],
                            'date_found': date_info['full_date_hebrew'],
                            'day': date_info['day'],
                            'month_hebrew': date_info['month_hebrew'],
                            'year': date_info['year']
                        })
                    else:
                        print("❌ תאריך לא נמצא")
                        test_results.append({
                            'letter_title': letter['title'],
                            'url': letter['url'],
                            'date_found': 'לא נמצא',
                            'day': '',
                            'month_hebrew': '',
                            'year': ''
                        })
                else:
                    print("❌ לא ניתן לחלץ תוכן")
            else:
                print("❌ לא ניתן לטעון מכתב")
        
        # יצירת דוח קטן
        print(f"\n📊 סיכום תוצאות:")
        print("-" * 60)
        for result in test_results:
            print(f"📝 {result['letter_title']}")
            print(f"   תאריך: {result['date_found']}")
            print()
        
        # שמירת CSV קטן
        csv_path = "test_dates_sample.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['letter_title', 'date_found', 'day', 'month_hebrew', 'year', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            writer.writerow({
                'letter_title': 'שם המכתב',
                'date_found': 'תאריך',
                'day': 'יום',
                'month_hebrew': 'חודש',
                'year': 'שנה',
                'url': 'קישור'
            })
            
            for result in test_results:
                writer.writerow(result)
        
        print(f"✅ דוח נשמר: {csv_path}")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
    finally:
        downloader.close()


if __name__ == "__main__":
    test_date_extraction()
