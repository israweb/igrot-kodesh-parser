#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מחולל מפתח קישורים למכתבים עם המרה של מספרים וחילוץ תאריכים
"""

import sys
import os
import csv
import json
import re
from datetime import datetime
try:
    from dateutil.parser import parse as date_parse
    import convertdate.hebrew as hebrew
except ImportError:
    print("התקנת חבילות נדרשות: pip install python-dateutil convertdate")
    date_parse = None
    hebrew = None

sys.path.append('../main')

from letters_downloader import LettersDownloader
import argparse


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
        
        # מילון הפוך (מספר -> שם חודש)
        self.month_names = {v: k for k, v in self.hebrew_months.items() if 'א' not in k}
        self.month_names[6] = 'אדר'  # ברירת מחדל לאדר
    
    def extract_date_from_text(self, text):
        """חילוץ תאריך מתחילת טקסט המכתב"""
        if not text:
            return None
        
        # מחפשים את השורות הראשונות
        lines = text.strip().split('\n')[:3]  # 3 שורות ראשונות
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
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
            
            # דפוס: יום חודש שנה (למשל: ט' שבט תש"ד)
            pattern = r'([א-ת]{1,3}\'?)\s+([א-ת]+)\s+([א-ת]+"?[א-ת]*)'
            match = re.search(pattern, clean_line)
            
            if match:
                day_str, month_str, year_str = match.groups()
                
                # המרת יום
                day = self._hebrew_letter_to_number(day_str.replace("'", ""))
                
                # המרת חודש
                month = self.hebrew_months.get(month_str)
                
                # המרת שנה (פשוטה)
                year = self._parse_hebrew_year(year_str)
                
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
            pass
        
        return None
    
    def _parse_hebrew_year(self, year_str):
        """פרסור שנה עברית פשוט"""
        # דוגמאות: תש"ד, תש"ה, תשי"ד וכו'
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
    
    def _hebrew_letter_to_number(self, hebrew_letter):
        """המרת אות עברית למספר"""
        if not hebrew_letter:
            return 0
            
        hebrew_numbers = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
            'י': 10, 'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19,
            'כ': 20, 'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30
        }
        return hebrew_numbers.get(hebrew_letter, 0)


class LinksIndexGenerator:
    def __init__(self):
        self.downloader = LettersDownloader(download_dir="temp_index", headless=True)
        self.date_parser = HebrewDateParser()
        
        # מיפוי קיצורי חודשים מיוחדים
        self.month_abbreviations = {
            'אד"ר': 'אדר א',
            'אד"ש': 'אדר ב'
        }
        
        # מילון להמרת אותיות עבריות למספרים
        self.hebrew_to_number = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10,
            'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19, 'כ': 20,
            'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30,
            'לא': 31, 'לב': 32, 'לג': 33, 'לד': 34, 'לה': 35, 'לו': 36, 'לז': 37, 'לח': 38, 'לט': 39, 'מ': 40,
            'מא': 41, 'מב': 42, 'מג': 43, 'מד': 44, 'מה': 45, 'מו': 46, 'מז': 47, 'מח': 48, 'מט': 49, 'נ': 50,
            'נא': 51, 'נב': 52, 'נג': 53, 'נד': 54, 'נה': 55, 'נו': 56, 'נז': 57, 'נח': 58, 'נט': 59, 'ס': 60,
            'סא': 61, 'סב': 62, 'סג': 63, 'סד': 64, 'סה': 65, 'סו': 66, 'סז': 67, 'סח': 68, 'סט': 69, 'ע': 70,
            'עא': 71, 'עב': 72, 'עג': 73, 'עד': 74, 'עה': 75, 'עו': 76, 'עז': 77, 'עח': 78, 'עט': 79, 'פ': 80,
            'פא': 81, 'פב': 82, 'פג': 83, 'פד': 84, 'פה': 85, 'פו': 86, 'פז': 87, 'פח': 88, 'פט': 89, 'צ': 90,
            'צא': 91, 'צב': 92, 'צג': 93, 'צד': 94, 'צה': 95, 'צו': 96, 'צז': 97, 'צח': 98, 'צט': 99, 'ק': 100,
            'קא': 101, 'קב': 102, 'קג': 103, 'קד': 104, 'קה': 105, 'קו': 106, 'קז': 107, 'קח': 108, 'קט': 109, 'קי': 110,
            'קיא': 111, 'קיב': 112, 'קיג': 113, 'קיד': 114, 'קטו': 115, 'קטז': 116, 'קיז': 117, 'קיח': 118, 'קיט': 119, 'קכ': 120,
            'קכא': 121, 'קכב': 122, 'קכג': 123, 'קכד': 124, 'קכה': 125, 'קכו': 126, 'קכז': 127, 'קכח': 128, 'קכט': 129, 'קל': 130,
            'קלא': 131, 'קלב': 132, 'קלג': 133, 'קלד': 134, 'קלה': 135, 'קלו': 136, 'קלז': 137, 'קלח': 138, 'קלט': 139, 'קמ': 140,
            'קמא': 141, 'קמב': 142, 'קמג': 143, 'קמד': 144, 'קמה': 145, 'קמו': 146, 'קמז': 147, 'קמח': 148, 'קמט': 149, 'קנ': 150,
            'קנא': 151, 'קנב': 152, 'קנג': 153, 'קנד': 154, 'קנה': 155, 'קנו': 156, 'קנז': 157, 'קנח': 158, 'קנט': 159, 'קס': 160,
            'קסא': 161, 'קסב': 162, 'קסג': 163, 'קסד': 164, 'קסה': 165, 'קסו': 166, 'קסז': 167, 'קסח': 168, 'קסט': 169, 'קע': 170,
            'קעא': 171, 'קעב': 172, 'קעג': 173, 'קעד': 174, 'קעה': 175, 'קעו': 176, 'קעז': 177, 'קעח': 178, 'קעט': 179, 'קפ': 180,
            'קפא': 181, 'קפב': 182, 'קפג': 183, 'קפד': 184, 'קפה': 185, 'קפו': 186, 'קפז': 187, 'קפח': 188, 'קפט': 189, 'קצ': 190,
            'קצא': 191, 'קצב': 192, 'קצג': 193, 'קצד': 194, 'קצה': 195, 'קצו': 196, 'קצז': 197, 'קצח': 198, 'קצט': 199, 'ר': 200,
            'רא': 201, 'רב': 202, 'רג': 203, 'רד': 204, 'רה': 205, 'רו': 206, 'רז': 207, 'רח': 208, 'רט': 209, 'רי': 210
        }
        
        # מילון הפוך (מספר -> אות עברית)
        self.number_to_hebrew = {v: k for k, v in self.hebrew_to_number.items()}

        # מילון חודשים אנגלית לעברית (לתמיכה בהמרה)
        self.months_english_to_hebrew = {
            'Nissan': 'ניסן',
            'Iyar': 'אייר',
            'Sivan': 'סיון',
            'Tammuz': 'תמוז',
            'Menachem Av': 'מנחם אב',
            'Elul': 'אלול',
            'Tishrei': 'תשרי',
            'Cheshvan': 'חשון',
            'Kislev': 'כסלו',
            'Teves': 'טבת',
            'Shevat': 'שבט',
            'Adar': 'אדר',
            # Добавьте если нужно больше
        }
    
    def hebrew_to_arabic(self, hebrew_text):
        """המרת מספר עברי למספר ערבי"""
        if not hebrew_text:
            return None
            
        # מחיקת רווחים מיותרים
        hebrew_clean = hebrew_text.strip()
        
        if hebrew_clean in self.hebrew_to_number:
            return self.hebrew_to_number[hebrew_clean]
        
        # ניסיון לפרוש מספרים מורכבים
        for key, value in sorted(self.hebrew_to_number.items(), key=lambda x: x[1], reverse=True):
            if hebrew_clean.startswith(key):
                remaining = hebrew_clean[len(key):]
                if remaining in self.hebrew_to_number:
                    return value + self.hebrew_to_number[remaining]
        
        return None
    
    def arabic_to_hebrew(self, number):
        """המרת מספר ערבי למספר עברי"""
        if not isinstance(number, int) or number < 1:
            return None
            
        if number in self.number_to_hebrew:
            return self.number_to_hebrew[number]
        
        # מספרים מורכבים
        for base in sorted(self.number_to_hebrew.keys(), reverse=True):
            if number >= base:
                remainder = number - base
                if remainder == 0:
                    return self.number_to_hebrew[base]
                elif remainder in self.number_to_hebrew:
                    return self.number_to_hebrew[base] + self.number_to_hebrew[remainder]
        
        return None
    
    def extract_volume_and_letter_numbers(self, volume_title, letter_title, letter_url=None):
        """חילוץ מספרי כרך ומכתב ותאריך"""
        result = {
            'volume_hebrew': None,
            'volume_arabic': None,
            'letter_hebrew': None,
            'letter_arabic': None,
            'date_info': None
        }
        
        # חילוץ מספר כרך (כרך X)
        volume_match = re.search(r'כרך\s+([א-ת]+)', volume_title)
        if volume_match:
            volume_hebrew = volume_match.group(1)
            result['volume_hebrew'] = volume_hebrew
            result['volume_arabic'] = self.hebrew_to_arabic(volume_hebrew)
        
        # חילוץ מספר מכתב (מכתב X)
        letter_match = re.search(r'מכתב\s+([א-ת]+)', letter_title)
        if letter_match:
            letter_hebrew = letter_match.group(1)
            result['letter_hebrew'] = letter_hebrew  
            result['letter_arabic'] = self.hebrew_to_arabic(letter_hebrew)
        
        # חילוץ תאריך (אם יש URL למכתב)
        if letter_url:
            try:
                print(f"🔍 חילוץ תאריך למכתב: {letter_title}")
                letter_soup = self.downloader.get_page_with_selenium(letter_url)
                if letter_soup:
                    content = self.downloader.extract_letter_content(letter_soup, letter_url)
                    if content:
                        date_info = self.date_parser.extract_date_from_text(content)
                        result['date_info'] = date_info
                        if date_info:
                            print(f"✅ תאריך נמצא: {date_info['full_date_hebrew']}")
                        else:
                            print("❌ לא נמצא תאריך")
            except Exception as e:
                print(f"⚠️ שגיאה בחילוץ תאריך: {e}")
        
        return result
    



    def generate_full_index(self, volumes_to_process=None, output_format="csv"):
        """
        יצירת מפתח קישורים מלא
        
        Args:
            volumes_to_process (list): רשימת כרכים לעיבוד (None = כולם)
            output_format (str): פורמט פלט (csv, json, html)
        """
        print("📇 יצירת מפתח קישורים מלא")
        print("=" * 70)
        
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        
        try:
            # טעינת דף ראשי
            print("🔍 טוען דף ראשי...")
            soup = self.downloader.get_page_with_selenium(start_url)
            if not soup:
                print("❌ לא ניתן לטעון דף ראשי")
                return None
            
            # חיפוש כל הכרכים
            volume_links = self.downloader.find_volume_links(soup, start_url)
            if not volume_links:
                print("❌ לא נמצאו כרכים")
                return None
            
            # סינון כרכים אם צוינו
            if volumes_to_process:
                filtered_volumes = []
                for volume_info in volume_links:
                    for vol in volumes_to_process:
                        if f'כרך {vol}' in volume_info['title']:
                            filtered_volumes.append(volume_info)
                            break
                volume_links = filtered_volumes
            
            print(f"📚 נמצאו כרכים לעיבוד: {len(volume_links)}")
            
            all_index_data = []
            
            # עיבוד כל כרך
            for i, volume_info in enumerate(volume_links, 1):
                print(f"\n📖 מעבד כרך {i}/{len(volume_links)}: {volume_info['title']}")
                
                # טעינת דף כרך
                volume_soup = self.downloader.get_page_with_selenium(volume_info['url'])
                if not volume_soup:
                    print(f"❌ לא ניתן לטעון כרך {volume_info['title']}")
                    continue
                
                # חיפוש כל המכתבים בכרך
                letter_links = self.downloader.find_letter_links(volume_soup, volume_info['url'], volume_info['title'])
                
                print(f"📝 נמצאו מכתבים בכרך: {len(letter_links)}")
                
                # עיבוד כל מכתב
                for j, letter in enumerate(letter_links, 1):
                    print(f"   מכתב {j}/{len(letter_links)}: {letter['title']}")
                    numbers = self.extract_volume_and_letter_numbers(volume_info['title'], letter['title'], letter['url'])
                    
                    # הכנת נתוני התאריך
                    date_info = numbers.get('date_info')
                    date_fields = {
                        'day': date_info['day'] if date_info else '',
                        'day_hebrew': date_info['day_hebrew'] if date_info else '',
                        'month': date_info['month'] if date_info else '',
                        'month_hebrew': date_info['month_hebrew'] if date_info else '',
                        'year': date_info['year'] if date_info else '',
                        'year_hebrew': date_info['year_hebrew'] if date_info else '',
                        'full_date_hebrew': date_info['full_date_hebrew'] if date_info else ''
                    }
                    
                    index_entry = {
                        'volume_arabic': numbers['volume_arabic'] or 0,
                        'volume_hebrew': numbers['volume_hebrew'] or '?',
                        'letter_arabic': numbers['letter_arabic'] or 0,
                        'letter_hebrew': numbers['letter_hebrew'] or '?',
                        'url': letter['url'],
                        'volume_title': volume_info['title'],
                        'letter_title': letter['title'],
                        **date_fields  # הוספת שדות התאריך
                    }
                    
                    all_index_data.append(index_entry)
            
            # מיון לפי מספר כרך, אחר כך מספר מכתב
            all_index_data.sort(key=lambda x: (x['volume_arabic'], x['letter_arabic']))
            
            print(f"\n📊 סטטיסטיקה כללית:")
            print(f"📚 כרכים מעובדים: {len(volume_links)}")
            print(f"📝 סה\"כ רשומות במפתח: {len(all_index_data)}")
            
            # יצירת קובץ מפתח
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format.lower() == 'csv':
                return self.generate_csv_index(all_index_data, f"links_index_{timestamp}.csv")
            elif output_format.lower() == 'json':
                return self.generate_json_index(all_index_data, f"links_index_{timestamp}.json")
            elif output_format.lower() == 'html':
                return self.generate_html_index(all_index_data, f"links_index_{timestamp}.html")
            else:
                print(f"❌ פורמט לא נתמך: {output_format}")
                return None
                
        except Exception as e:
            print(f"❌ שגיאה: {e}")
            return None
        finally:
            self.downloader.close()
    
    def generate_csv_index(self, data, filename):
        """יצירת מפתח CSV"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['volume_arabic', 'volume_hebrew', 'letter_arabic', 'letter_hebrew', 
                            'day', 'day_hebrew', 'month', 'month_hebrew', 'year', 'year_hebrew', 'full_date_hebrew', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                
                # כותרות
                writer.writerow({
                    'volume_arabic': 'מס\' כרך',
                    'volume_hebrew': 'כרך',
                    'letter_arabic': 'מס\' מכתב',
                    'letter_hebrew': 'מכתב',
                    'day': 'יום',
                    'day_hebrew': 'יום עברי',
                    'month': 'חודש',
                    'month_hebrew': 'חודש עברי',
                    'year': 'שנה',
                    'year_hebrew': 'שנה עברית',
                    'full_date_hebrew': 'תאריך מלא',
                    'url': 'קישור'
                })
                
                # נתונים
                for row in data:
                    writer.writerow({
                        'volume_arabic': row['volume_arabic'],
                        'volume_hebrew': row['volume_hebrew'],
                        'letter_arabic': row['letter_arabic'],
                        'letter_hebrew': row['letter_hebrew'],
                        'day': row.get('day', ''),
                        'day_hebrew': row.get('day_hebrew', ''),
                        'month': row.get('month', ''),
                        'month_hebrew': row.get('month_hebrew', ''),
                        'year': row.get('year', ''),
                        'year_hebrew': row.get('year_hebrew', ''),
                        'full_date_hebrew': row.get('full_date_hebrew', ''),
                        'url': row['url']
                    })
            
            print(f"✅ מפתח CSV נשמר: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת CSV: {e}")
            return None
    
    def generate_json_index(self, data, filename):
        """יצירת מפתח JSON"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            index = {
                'generated_at': datetime.now().isoformat(),
                'total_entries': len(data),
                'volumes_count': len(set(item['volume_arabic'] for item in data)),
                'format_description': {
                    'volume_arabic': 'מספר כרך במספרים ערביים',
                    'volume_hebrew': 'מספר כרך באותיות עבריות',
                    'letter_arabic': 'מספר מכתב במספרים ערביים',
                    'letter_hebrew': 'מספר מכתב באותיות עבריות',
                    'url': 'קישור ישיר למכתב'
                },
                'index': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(index, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"✅ מפתח JSON נשמר: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת JSON: {e}")
            return None
    
    def generate_html_index(self, data, filename):
        """יצירת מפתח HTML"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            volumes_count = len(set(item['volume_arabic'] for item in data))
            
            html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מפתח קישורים - מכתבי אגרות קודש</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
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
            width: 45%;
            padding: 10px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 16px;
            margin: 0 2.5%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
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
        .volume-header {{
            background-color: #2c3e50 !important;
            color: white !important;
        }}
        .hebrew-number {{
            font-weight: bold;
            color: #8e44ad;
        }}
        .arabic-number {{
            font-weight: bold;
            color: #27ae60;
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
            var dayInput = document.getElementById("daySearch").value.toLowerCase();
            var monthInput = document.getElementById("monthSearch").value.toLowerCase();
            var yearInput = document.getElementById("yearSearch").value.toLowerCase();
            var table = document.getElementById("indexTable");
            var tr = table.getElementsByTagName("tr");
            
            for (var i = 1; i < tr.length; i++) {{
                if (tr[i].classList.contains('volume-header')) {{
                    tr[i].style.display = "";  // Всегда показываем заголовки томов
                    continue;
                }}
                
                var td = tr[i].getElementsByTagName("td");
                if (td.length < 8) continue;  // Пропускаем неполные строки
                
                var volumeMatch = true;
                var letterMatch = true;
                var dayMatch = true;
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
                
                if (dayInput) {{
                    dayMatch = td[4].innerHTML.toLowerCase().indexOf(dayInput) > -1;
                }}
                
                if (monthInput) {{
                    monthMatch = td[5].innerHTML.toLowerCase().indexOf(monthInput) > -1;
                }}
                
                if (yearInput) {{
                    yearMatch = td[6].innerHTML.toLowerCase().indexOf(yearInput) > -1;
                }}
                
                if (volumeMatch && letterMatch && dayMatch && monthMatch && yearMatch) {{
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
        <h1>📇 מפתח קישורים - מכתבי אגרות קודש</h1>
        
        <div class="summary">
            <div><strong>📚 כרכים:</strong> {volumes_count}</div>
            <div><strong>📝 סה\"כ מכתבים:</strong> {len(data)}</div>
            <div><strong>🕐 תאריך יצירה:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="volumeSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש לפי מספר כרך (מספר או אותיות)">
            <input type="text" id="letterSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש לפי מספר מכתב (מספר או אותיות)">
            <input type="text" id="daySearch" onkeyup="searchTable()" placeholder="🔍 חיפוש לפי יום">
            <input type="text" id="monthSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש לפי חודש">
            <input type="text" id="yearSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש לפי שנה">
        </div>
        
        <table id="indexTable">
            <thead>
                <tr>
                    <th>מס\' כרך</th>
                    <th>כרך</th>
                    <th>מס\' מכתב</th>
                    <th>מכתב</th>
                    <th>יום</th>
                    <th>חודש</th>
                    <th>שנה</th>
                    <th>קישור</th>
                </tr>
            </thead>
            <tbody>
"""

            current_volume = None
            for entry in data:
                if current_volume != entry['volume_arabic']:
                    current_volume = entry['volume_arabic']
                    # מפריד בין כרכים
                    html_content += f"""
                    <tr class="volume-header">
                        <td colspan="8">📚 כרך {current_volume} ({entry['volume_hebrew']})</td>
                    </tr>
"""

                html_content += f"""
                    <tr>
                        <td class="arabic-number">{entry['volume_arabic']}</td>
                        <td class="hebrew-number">{entry['volume_hebrew']}</td>
                        <td class="arabic-number">{entry['letter_arabic']}</td>
                        <td class="hebrew-number">{entry['letter_hebrew']}</td>
                        <td class="hebrew-number">{entry.get('day_hebrew', '')}</td>
                        <td class="hebrew-number">{entry.get('month_hebrew', '')}</td>
                        <td class="hebrew-number">{entry.get('year_hebrew', '')}</td>
                        <td><a href="{entry['url']}" class="letter-link" target="_blank">פתח מכתב</a></td>
                    </tr>
"""

            html_content += """
                </tbody>
            </table>
            
            <div class="footer">
                <p>📇 מפתח קישורים נוצר אוטומטית על ידי מערכת פרסינג מכתבי אגרות קודש</p>
                <p>🔗 כל הקישורים מובילים לאתר הרשמי chabad.org</p>
            </div>
        </div>
    </body>
    </html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            print(f"✅ מפתח HTML נשמר: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת HTML: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='יצירת מפתח קישורים לכל המכתבים')
    parser.add_argument('--volumes', nargs='+', 
                        help='רשימת כרכים ליצירת מפתח (א ב ג...) או ריק לכולם')
    parser.add_argument('--format', choices=['csv', 'json', 'html'], default='csv',
                        help='פורמט מפתח (csv, json, html)')
    
    args = parser.parse_args()
    
    print("📇 מחולל מפתח קישורים למכתבי אגרות קודש")
    print("=" * 70)
    
    if args.volumes:
        print(f"📚 כרכים לעיבוד: {', '.join(args.volumes)}")
    else:
        print("📚 עיבוד: כל הכרכים הזמינים")
    
    print(f"📄 פורמט: {args.format.upper()}")
    print("=" * 70)
    
    generator = LinksIndexGenerator()
    
    try:
        result = generator.generate_full_index(
            volumes_to_process=args.volumes,
            output_format=args.format
        )
        
        if result:
            print(f"\n🎉 מפתח קישורים נוצר בהצלחה!")
            print(f"📁 קובץ: {result}")
            print(f"📂 תיקייה: reports/")
            
            if args.format == 'html':
                print(f"🌐 פתח את הקובץ בדפדפן לצפייה")
                print(f"🔍 בגרסת HTML יש חיפוש נפרד לכרך ולמכתב")
        else:
            print("\n❌ לא ניתן ליצור מפתח")
            
    except Exception as e:
        print(f"❌ שגיאה קריטית: {e}")


if __name__ == "__main__":
    main()
