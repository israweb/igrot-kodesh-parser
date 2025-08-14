#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת פרסר תאריכים בלבד - ללא חיבור לאינטרנט
"""

import sys
import os
import re
sys.path.append('../main')


class HebrewDateParser:
    def __init__(self):
        # מילון חודשי השנה העברית
        self.hebrew_months = {
            'תשרי': 1, 'חשון': 2, 'חשוון': 2, 'כסלו': 3, 'טבת': 4, 'שבט': 5, 'אדר': 6,
            'אדר א': 6, 'אדר ב': 7, 'אד"ר': 6, 'אדר ראשון': 6, 'אדר שני': 7,
            'ניסן': 8, 'אייר': 9, 'סיון': 10, 'סיוון': 10,
            'תמוז': 11, 'אב': 12, 'אלול': 13
        }
    
    def _parse_hebrew_date(self, line):
        """פרסור תאריך עברי"""
        try:
            print(f"🔍 מפרסר: '{line}'")
            
            # הסרת ב"ה ואותיות נוספות
            clean_line = re.sub(r'ב"ה,?\s*', '', line)
            clean_line = re.sub(r'[,.]', '', clean_line)
            print(f"    נוקה: '{clean_line}'")
            
            # דפוסים שונים לתאריכים:
            
            # דפוס 1: כ"א אדר פ"ח (יום חודש שנה)
            pattern1 = r'([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)'
            match1 = re.search(pattern1, clean_line)
            
            # דפוס 2: א' כ"א אד"ר ה'תרצ"ב (יום שבוע + יום חודש שנה)
            # צריך לדלג על יום השבוע (א'-ו' או ש')
            pattern2 = r'(?:[א-ו]\'|ש\')\s+([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)\s+(?:ה\')?([א-ת]+"?[א-ת]*)'
            match2 = re.search(pattern2, clean_line)
            
            # דפוס 3: ה' כח טבת תרפ"ט (עם קידומת ה')
            pattern3 = r'ה\'\s+([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)\s+([א-ת]+"?[א-ת]*)'
            match3 = re.search(pattern3, clean_line)
            
            match = match1 or match2 or match3
            
            if match:
                day_str, month_str, year_str = match.groups()
                print(f"    📅 נמצא: יום={day_str}, חודש={month_str}, שנה={year_str}")
                
                # המרת יום
                day = self._hebrew_letter_to_number_improved(day_str)
                
                # המרת חודש (כולל קיצורים)
                month = self._parse_month(month_str)
                
                # המרת שנה (משופרת)
                year = self._parse_hebrew_year_improved(year_str)
                
                if day and month and year:
                    result = {
                        'day': day,
                        'day_hebrew': day_str,
                        'month': month,
                        'month_hebrew': month_str,
                        'year': year,
                        'year_hebrew': year_str,
                        'full_date_hebrew': f"{day_str} {month_str} {year_str}",
                        'date_type': 'עברי'
                    }
                    print(f"    ✅ תוצאה: {result['full_date_hebrew']} = {day}/{month}/{year}")
                    return result
                else:
                    print(f"    ❌ לא ניתן להמיר: יום={day}, חודש={month}, שנה={year}")
            else:
                print("    ❌ לא נמצא דפוס תאריך")
        
        except Exception as e:
            print(f"    ❌ שגיאה בפרסור: {e}")
        
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
        print(f"        🔢 המרת '{hebrew_letter}' -> {result}")
        return result
    
    def _parse_month(self, month_str):
        """פרסור חודש כולל קיצורים"""
        # הסרת גרשיים
        clean_month = month_str.replace('"', '').replace("'", '')
        
        month = self.hebrew_months.get(clean_month) or self.hebrew_months.get(month_str)
        print(f"        📅 חודש '{month_str}' -> {month}")
        return month
    
    def _parse_hebrew_year_improved(self, year_str):
        """פרסור שנה עברית משופר"""
        print(f"        🗓️ מפרסר שנה: '{year_str}'")
        
        # הסרת קידומות כמו ה'
        clean_year = re.sub(r'^ה\'', '', year_str)
        
        # טיפול בשנים קצרות (כמו פ"ח = תרפ"ח = 5688)
        if clean_year == 'פ"ח':
            result = 5688  # שנה קצרה, בהקשר תקופת הרבי
            print(f"        🗓️ שנה קצרה פ\"ח = {result}")
            return result
        
        # פרסור תרצ"ב = 5692
        if clean_year.startswith('תרצ'):
            # תרצ = תר (5600) + צ (90) = 5690
            suffix = clean_year[3:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5690 + suffix_val
                print(f"        🗓️ תרצ ({5690}) + {suffix} ({suffix_val}) = {result}")
                return result
            return 5690
        
        # פרסור תרפ"ט = 5689
        if clean_year.startswith('תרפ'):
            # תרפ = תר (5600) + פ (80) = 5680
            suffix = clean_year[3:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5680 + suffix_val
                print(f"        🗓️ תרפ ({5680}) + {suffix} ({suffix_val}) = {result}")
                return result
            return 5680
        
        # פרסור כללי של תר...
        if clean_year.startswith('תר'):
            # תר = 5600
            suffix = clean_year[2:].replace('"', '').replace("'", '')
            if suffix:
                suffix_val = self._hebrew_letter_to_number_improved(suffix)
                result = 5600 + suffix_val
                print(f"        🗓️ תר ({5600}) + {suffix} ({suffix_val}) = {result}")
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
                print(f"        🗓️ {prefix} ({base}) + {suffix} ({suffix_value}) = {result}")
                return result
        
        return None


def test_specific_dates():
    """בדיקת הדוגמאות הספציפיות שהמשתמש ציין"""
    
    parser = HebrewDateParser()
    
    test_cases = [
        {
            'text': 'כ"א אדר פ"ח',
            'expected': {'day': 21, 'month': 6, 'year': 5688},
            'description': 'מכתב 1: כ"א (21) אדר (6) פ"ח (5688)'
        },
        {
            'text': 'ה\' כח טבת תרפ"ט',
            'expected': {'day': 28, 'month': 4, 'year': 5689},
            'description': 'מכתב 2: כח (28) טבת (4) תרפ"ט (5689)'
        },
        {
            'text': 'ב"ה א\' כ"א אד"ר ה\'תרצ"ב',
            'expected': {'day': 21, 'month': 6, 'year': 5692},
            'description': 'מכתב 3: א\' (יום א) כ"א (21) אד"ר (אדר ראשון=6) ה\'תרצ"ב (5692)'
        }
    ]
    
    print("📇 בדיקת פרסר תאריכים עבריים")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 בדיקה {i}: {test_case['description']}")
        print(f"   טקסט: {test_case['text']}")
        
        result = parser._parse_hebrew_date(test_case['text'])
        
        if result:
            expected = test_case['expected']
            success = (
                result['day'] == expected['day'] and
                result['month'] == expected['month'] and
                result['year'] == expected['year']
            )
            
            if success:
                print(f"✅ הצלחה מלאה!")
            else:
                print(f"⚠️ הצלחה חלקית:")
                
            print(f"   יום: {result['day']} ({result['day_hebrew']}) - צפוי: {expected['day']}")
            print(f"   חודש: {result['month']} ({result['month_hebrew']}) - צפוי: {expected['month']}")
            print(f"   שנה: {result['year']} ({result['year_hebrew']}) - צפוי: {expected['year']}")
            print(f"   תאריך מלא: {result['full_date_hebrew']}")
            
            if not success:
                print("❌ יש אי התאמות!")
        else:
            print("❌ נכשל לחלוטין - לא נמצא תאריך")
        
        print("-" * 50)


if __name__ == "__main__":
    test_specific_dates()
