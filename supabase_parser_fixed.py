#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
פרסר אגרות קודש מתוקן עם אינטגרציה של Supabase
מבוסס על המבנה האמיתי של אתר Chabad.org
"""

import os
import sys
import logging
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from supabase import create_client, Client
import argparse

# הוספת נתיב לתיקיות הפרויקט
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))

from test_10_letters import HebrewDateParser

class SupabaseConfig:
    """הגדרות Supabase"""
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL', '')
        self.key = os.getenv('SUPABASE_ANON_KEY', '')
        
        if not self.url or not self.key:
            print("❌ נא להגדיר משתני סביבה:")
            print("   SUPABASE_URL=your_supabase_url")
            print("   SUPABASE_ANON_KEY=your_supabase_anon_key")
            sys.exit(1)

class FixedIgrotParser:
    """פרסר אגרות קודש מתוקן"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """אתחול הפרסר"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.date_parser = HebrewDateParser()
        self.setup_logging()
        
        # URLs מהמבנה האמיתי של האתר
        self.base_urls = {
            'main': 'https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm',
            'volume_1': 'https://www.chabad.org/therebbe/article_cdo/aid/4643805/jewish/page.htm',
            'first_letter': 'https://www.chabad.org/therebbe/article_cdo/aid/4645943/jewish/page.htm'
        }
        
        self.session_stats = {
            'letters_processed': 0,
            'letters_with_dates': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
    def setup_logging(self):
        """הגדרת רישום לוגים"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/fixed_supabase_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_to_supabase(self, level: str, message: str, volume_number: int = None, 
                       letter_number: int = None, url: str = None, error_details: dict = None):
        """רישום לוג ל-Supabase"""
        try:
            log_data = {
                'log_level': level,
                'message': message,
                'volume_number': volume_number,
                'letter_number': letter_number,
                'url': url,
                'error_details': error_details
            }
            self.supabase.table('parse_logs').insert(log_data).execute()
        except Exception as e:
            self.logger.error(f"שגיאה ברישום לוג ל-Supabase: {e}")

    def get_last_processed_entry(self) -> dict | None:
        """מחזיר את הרשומה האחרונה שנשמרה (לפי created_at)"""
        try:
            res = self.supabase.table('letters') \
                .select('tom_number,letter_number,letter_hebrew,url,created_at') \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            self.logger.warning(f"⚠️ לא ניתן לשלוף רשומה אחרונה: {e}")
        return None
    
    def setup_driver(self):
        """הגדרת WebDriver עם אפשרויות מתקדמות"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            # תמיכה ב-Colab / לינוקס
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
            chromium_binary = os.environ.get('CHROME_BINARY')

            # ברירת מחדל ידועה בקולאב
            if not chromedriver_path and os.path.exists('/usr/bin/chromedriver'):
                chromedriver_path = '/usr/bin/chromedriver'
            if not chromium_binary and os.path.exists('/usr/bin/chromium-browser'):
                chromium_binary = '/usr/bin/chromium-browser'

            if chromium_binary:
                chrome_options.binary_location = chromium_binary

            if chromedriver_path and os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # ניסיון דיפולטי במערכות מקומיות עם Chrome מותקן
                driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            self.logger.error(f"❌ שגיאה בהגדרת WebDriver: {e}")
            return None
    
    def hebrew_letter_to_number(self, hebrew_letter: str) -> int:
        """המרת אות עברית למספר"""
        hebrew_numbers = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10,
            'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19, 'כ': 20,
            'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30,
            'לא': 31, 'לב': 32, 'לג': 33, 'לד': 34, 'לה': 35, 'לו': 36, 'לז': 37, 'לח': 38, 'לט': 39, 'מ': 40,
            'מא': 41, 'מב': 42, 'מג': 43, 'מד': 44, 'מה': 45, 'מו': 46, 'מז': 47, 'מח': 48, 'מט': 49, 'נ': 50
        }
        return hebrew_numbers.get(hebrew_letter, 0)
    
    def number_to_hebrew_letter(self, number: int) -> str:
        """המרת מספר לאות עברית"""
        number_to_hebrew = {
            1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט', 10: 'י',
            11: 'יא', 12: 'יב', 13: 'יג', 14: 'יד', 15: 'טו', 16: 'טז', 17: 'יז', 18: 'יח', 19: 'יט', 20: 'כ',
            21: 'כא', 22: 'כב', 23: 'כג', 24: 'כד', 25: 'כה', 26: 'כו', 27: 'כז', 28: 'כח', 29: 'כט', 30: 'ל',
            31: 'לא', 32: 'לב', 33: 'לג', 34: 'לד', 35: 'לה', 36: 'לו', 37: 'לז', 38: 'לח', 39: 'לט', 40: 'מ',
            41: 'מא', 42: 'מב', 43: 'מג', 44: 'מד', 45: 'מה', 46: 'מו', 47: 'מז', 48: 'מח', 49: 'מט', 50: 'נ'
        }
        return number_to_hebrew.get(number, str(number))
    
    def get_or_create_volume(self, volume_number: int, volume_hebrew: str) -> int:
        """קבלת או יצירת כרך ב-Supabase"""
        try:
            # בדיקה אם הכרך קיים
            result = self.supabase.table('volumes').select('id').eq('volume_number', volume_number).execute()
            
            if result.data:
                volume_id = result.data[0]['id']
                self.logger.info(f"🔍 נמצא כרך קיים: {volume_hebrew} (ID: {volume_id})")
                return volume_id
            
            # יצירת כרך חדש
            volume_data = {
                'volume_number': volume_number,
                'volume_hebrew': volume_hebrew,
                'total_letters': 0,
                'total_pages': 0
            }
            
            result = self.supabase.table('volumes').insert(volume_data).execute()
            volume_id = result.data[0]['id']
            
            self.logger.info(f"✅ נוצר כרך חדש: {volume_hebrew} (ID: {volume_id})")
            self.log_to_supabase('INFO', f'נוצר כרך חדש: {volume_hebrew}', volume_number)
            
            return volume_id
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה ביצירת כרך: {e}")
            self.log_to_supabase('ERROR', f'שגיאה ביצירת כרך: {e}', volume_number, error_details={'error': str(e)})
            return None
    
    def extract_letter_number_from_title(self, driver) -> tuple:
        """חילוץ מספר המכתב מהכותרת - מחזיר tuple (מספר, עברית)"""
        try:
            # חיפוש הכותרת
            title_selectors = ['h1', '.title', '.article-title', 'title']
            
            for selector in title_selectors:
                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_element.text.strip()
                    self.logger.info(f"🔍 כותרת נמצאה: '{title_text}'")
                    
                    # חיפוש דפוס "מכתב X" או "אגרות קודש - מכתב X"
                    hebrew_letter_match = re.search(r'מכתב\s+([א-ת]+)', title_text)
                    if hebrew_letter_match:
                        hebrew_letter = hebrew_letter_match.group(1)
                        # המרה לעברית למספר
                        letter_number = self.hebrew_letter_to_number(hebrew_letter)
                        self.logger.info(f"📝 מספר מכתב מהכותרת: {hebrew_letter} = {letter_number}")
                        return letter_number, hebrew_letter
                    
                    # נסיון חלופי: חיפוש מספר רגיל
                    numbers = re.findall(r'\d+', title_text)
                    if numbers:
                        letter_number = int(numbers[-1])  # לוקח את המספר האחרון
                        hebrew_letter = self.number_to_hebrew_letter(letter_number)
                        self.logger.info(f"📝 מספר מכתב מהכותרת (מספר): {letter_number} = {hebrew_letter}")
                        return letter_number, hebrew_letter
                        
                except Exception as e:
                    self.logger.debug(f"   שגיאה בסלקטור {selector}: {e}")
                    continue
            
            self.logger.warning("⚠️ לא נמצא מספר מכתב בכותרת")
            return None, None
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בחילוץ מספר מכתב: {e}")
            return None, None
    
    def extract_letter_content_and_date(self, driver) -> tuple:
        """חילוץ תוכן המכתב והתאריך מהשורה הראשונה"""
        try:
            # חיפוש תוכן המכתב
            content_selectors = [
                '.article-content',
                '.content-body', 
                '.article-body',
                '#article-content',
                '.main-content',
                'article',
                '.post-content'
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    content_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    content = content_element.text.strip()
                    if content:
                        self.logger.info(f"📄 תוכן נמצא עם סלקטור: {selector}")
                        break
                except:
                    continue
            
            if not content:
                # נסיון אחרון - לוקח את כל הטקסט מהגוף
                body = driver.find_element(By.TAG_NAME, 'body')
                content = body.text.strip()
                self.logger.warning("⚠️ נלקח תוכן כללי מהגוף")
            
            # חילוץ התאריך מהשורה הראשונה
            if content:
                lines = content.split('\n')
                first_line = lines[0].strip() if lines else ""
                
                self.logger.info(f"📅 שורה ראשונה לפרסור תאריך: '{first_line}'")
                
                # פרסור התאריך
                date_info = self.date_parser.extract_date_from_text(first_line)
                
                return content, date_info
            
            return content, None
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בחילוץ תוכן: {e}")
            return "", None
    
    def save_letter_to_supabase(self, volume_id: int, letter_data: dict) -> bool:
        """שמירת מכתב ל-Supabase"""
        try:
            # בדיקה אם המכתב כבר קיים
            existing = self.supabase.table('letters').select('id').eq('volume_id', volume_id).eq('letter_number', letter_data['letter_number']).execute()
            
            if existing.data:
                # עדכון מכתב קיים
                result = self.supabase.table('letters').update(letter_data).eq('id', existing.data[0]['id']).execute()
                self.logger.info(f"🔄 עודכן מכתב קיים: {letter_data['letter_hebrew']}")
            else:
                # הוספת מכתב חדש
                letter_data['volume_id'] = volume_id
                result = self.supabase.table('letters').insert(letter_data).execute()
                self.logger.info(f"✅ נוסף מכתב חדש: {letter_data['letter_hebrew']}")
            
            self.session_stats['letters_processed'] += 1
            if letter_data.get('date_parsed'):
                self.session_stats['letters_with_dates'] += 1
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בשמירת מכתב: {e}")
            self.log_to_supabase('ERROR', f'שגיאה בשמירת מכתב {letter_data.get("letter_hebrew", "")}: {e}', 
                               error_details={'letter_data': letter_data, 'error': str(e)})
            self.session_stats['errors'] += 1
            return False
    
    def find_volume_letters_on_page(self, driver, volume_url: str, page_num: int) -> list:
        """מציאת קישורי מכתבים בכרך. מחזיר רשימת אובייקטים: {url, text, hebrew_letter, number_guess}"""
        try:
            page_url = volume_url if page_num == 1 else f"{volume_url}?page={page_num}"
            self.logger.info(f"🔍 סורק כרך: {page_url}")
            driver.get(page_url)
            time.sleep(3)
            
            # נסיון למצוא קישורים למכתבים בדרכים שונות
            letter_links: list[dict] = []
            
            # שיטה 1: חיפוש קישורים עם טקסט "מכתב" או מספרים
            text_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'מכתב') or contains(text(), 'Letter') or contains(@href, '4645')]")
            for link in text_links:
                href = link.get_attribute('href')
                text = link.text.strip()
                if href and '/aid/' in href:
                    heb_match = re.search(r'מכתב\s+([א-ת]+)', text)
                    heb = heb_match.group(1) if heb_match else None
                    num_guess = self.hebrew_letter_to_number(heb) if heb else None
                    letter_links.append({'url': href, 'text': text, 'hebrew_letter': heb, 'number_guess': num_guess})
            
            # שיטה 2: חיפוש קישורים בטווח ה-IDs הידוע (4645943 ואילך)
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/aid/' in href:
                    # חיפוש מספר ה-aid
                    aid_match = re.search(r'/aid/(\d+)/', href)
                    if aid_match:
                        aid_number = int(aid_match.group(1))
                        # בדיקה שזה בטווח הנכון למכתבים (כבר יודעים שהמכתב הראשון הוא 4645943)
                        if 4645940 <= aid_number <= 4646200:  # טווח סביר למכתבים
                            letter_links.append({'url': href, 'text': link.text.strip(), 'hebrew_letter': None, 'number_guess': None})
            
            # שיטה 3: אם לא מצאנו כלום, ננסה ליצור רשימה ידנית של המכתבים הראשונים
            if not letter_links:
                self.logger.warning("⚠️ לא נמצאו קישורים בדף, יוצר רשימה ידנית")
                # המכתבים הראשונים שאנחנו יודעים עליהם
                known_letters = [
                    'https://www.chabad.org/therebbe/article_cdo/aid/4645943/jewish/page.htm',  # מכתב 1
                    'https://www.chabad.org/therebbe/article_cdo/aid/4645963/jewish/page.htm',  # מכתב 2  
                    'https://www.chabad.org/therebbe/article_cdo/aid/4645964/jewish/page.htm',  # מכתב 3
                ]
                letter_links.extend([{'url': u, 'text': '', 'hebrew_letter': None, 'number_guess': None} for u in known_letters])
            
            # הסרת כפילויות וסידוק
            # הסרת כפילויות לפי URL ושמירת מטא-דאטה
            seen = set()
            unique_links: list[dict] = []
            for item in letter_links:
                if item['url'] not in seen:
                    seen.add(item['url'])
                    unique_links.append(item)
            
            self.logger.info(f"📚 נמצאו {len(unique_links)} מכתבים בכרך")
            
            # הדפסת הקישורים הראשונים לבדיקה
            for i, item in enumerate(unique_links[:5]):
                self.logger.info(f"   📄 מכתב {i+1}: {item['url']}  | text='{item.get('text','')}'  | guess={item.get('number_guess')}")
            
            return unique_links
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בחיפוש מכתבים בכרך: {e}")
            return []
    
    def parse_single_letter(self, driver, letter_url: str, volume_id: int, volume_hebrew: str) -> bool:
        """פרסור מכתב יחיד"""
        try:
            self.logger.info(f"📖 מפרסר מכתב: {letter_url}")
            
            # מעבר לדף המכתב
            driver.get(letter_url)
            time.sleep(2)
            
            # חילוץ מספר המכתב מהכותרת
            letter_number, letter_hebrew = self.extract_letter_number_from_title(driver)
            
            if not letter_number or not letter_hebrew:
                # נסיון לחלץ מה-URL כגיבוי
                aid_match = re.search(r'/aid/(\d+)/', letter_url)
                if aid_match:
                    # נשתמש ב-ID כמספר זמני
                    aid_id = int(aid_match.group(1))
                    letter_number = aid_id - 4645942  # התאמה לסדרה (המכתב הראשון הוא 4645943)
                    if letter_number <= 0:
                        letter_number = 1
                    letter_hebrew = self.number_to_hebrew_letter(letter_number)
                    self.logger.info(f"📝 מספר מכתב מ-URL: {aid_id} -> {letter_number} ({letter_hebrew})")
                else:
                    letter_number = 1
                    letter_hebrew = 'א'
                    self.logger.warning("⚠️ משתמש במספר ברירת מחדל: 1 (א)")
            
            # חילוץ תוכן ותאריך
            content, date_info = self.extract_letter_content_and_date(driver)
            
            # הכנת נתוני המכתב
            letter_data = {
                'tom_hebrew': volume_hebrew,
                'tom_number': 1,  # כרך א
                'letter_hebrew': letter_hebrew,
                'letter_number': letter_number,
                'url': letter_url,
                'content': content[:2000],  # מגביל את האורך
                'date_parsed': date_info is not None
            }
            
            # הוספת נתוני תאריך אם נמצאו
            if date_info:
                letter_data.update({
                    'full_date_hebrew': date_info.get('full_date_hebrew', ''),
                    'day_hebrew': date_info.get('day_hebrew', ''),
                    'month_hebrew': date_info.get('month_hebrew', ''),
                    'year_hebrew': date_info.get('year_hebrew', ''),
                    'year_number': date_info.get('year_numeric', 0)  # שנה בספרים
                })
                self.logger.info(f"📅 נמצא תאריך: {date_info.get('full_date_hebrew')} ({date_info.get('year_numeric', 0)})")
            else:
                self.logger.warning(f"❓ לא נמצא תאריך במכתב {letter_number}")
                # ערכי ברירת מחדל
                letter_data.update({
                    'full_date_hebrew': '',
                    'day_hebrew': '',
                    'month_hebrew': '',
                    'year_hebrew': '',
                    'year_number': 0
                })
            
            # שמירה ל-Supabase
            success = self.save_letter_to_supabase(volume_id, letter_data)
            
            if success:
                self.log_to_supabase('INFO', f'נשמר מכתב {letter_hebrew} בהצלחה', 
                                   volume_number=1, letter_number=letter_number, url=letter_url)
            
            return success
                
        except Exception as e:
            self.logger.error(f"❌ שגיאה בפרסור מכתב {letter_url}: {e}")
            self.log_to_supabase('ERROR', f'שגיאה בפרסור מכתב: {e}', 
                               url=letter_url, error_details={'error': str(e)})
            return False
    
    def parse_volume(self, volume_hebrew: str = 'א', volume_number: int | None = None, volume_url: str | None = None, max_letters: int = None, resume: bool = True):
        """פרסור כרך שלם"""
        if volume_number is None:
            volume_number = self.hebrew_letter_to_number(volume_hebrew)
            if not volume_number:
                volume_number = 1
        
        self.logger.info(f"🚀 מתחיל פרסור כרך {volume_hebrew}")
        self.log_to_supabase('INFO', f'התחלת פרסור כרך {volume_hebrew}', volume_number)
        
        # יצירת או קבלת כרך
        volume_id = self.get_or_create_volume(volume_number, volume_hebrew)
        if not volume_id:
            self.logger.error("❌ לא ניתן ליצור או למצוא כרך")
            return False
        
        # הגדרת WebDriver
        driver = self.setup_driver()
        if not driver:
            self.logger.error("❌ לא ניתן להגדיר WebDriver")
            return False
        
        try:
            # מציאת מכתבים בכרך על פני עמודים
            if not volume_url:
                # ברירת מחדל לכרך א
                volume_url = self.base_urls.get('volume_1', '')

            # נקודת חידוש
            resume_url = None
            if resume:
                last_entry = self.get_last_processed_entry()
                if last_entry and last_entry.get('tom_number') == volume_number:
                    resume_url = last_entry.get('url')
                    self.logger.info(f"🔁 חידוש מפרסר אחרי: {resume_url}")

            total_pages = 0
            successful_letters = 0
            letters_processed_this_run = 0
            page_num = 1
            reached_resume = False if resume_url else True

            while True:
                page_links = self.find_volume_letters_on_page(driver, volume_url, page_num)
                if not page_links:
                    break
                total_pages += 1

                # אם יש נקודת חידוש, לדלג עד שאנו עוברים את ה-URL האחרון
                for item in page_links:
                    url = item['url']
                    if not reached_resume:
                        if url == resume_url:
                            reached_resume = True
                        continue

                    # מגבלה למצב בדיקה
                    if max_letters and letters_processed_this_run >= max_letters:
                        break

                    self.logger.info(f"📝 מכתב: {url}")
                    if self.parse_single_letter(driver, url, volume_id, volume_hebrew):
                        successful_letters += 1
                    letters_processed_this_run += 1
                    time.sleep(1)

                if max_letters and letters_processed_this_run >= max_letters:
                    break
                page_num += 1
            
            # עדכון סטטיסטיקות הכרך
            self.update_volume_stats(volume_id, successful_letters)
            try:
                self.supabase.table('volumes').update({
                    'total_pages': total_pages
                }).eq('id', volume_id).execute()
            except Exception as e:
                self.logger.warning(f"⚠️ לא ניתן לעדכן עמודים: {e}")
            
            self.logger.info(f"✅ הושלם פרסור כרך {volume_hebrew}: {successful_letters} מכתבים")
            self.log_to_supabase('INFO', f'הושלם פרסור כרך {volume_hebrew}: {successful_letters} מכתבים', volume_number)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה כללית בפרסור כרך: {e}")
            self.log_to_supabase('ERROR', f'שגיאה כללית בפרסור כרך {volume_hebrew}: {e}', volume_number, error_details={'error': str(e)})
            return False
            
        finally:
            driver.quit()

    def find_all_volumes(self, driver) -> list:
        """איתור כל הכרכים מהעמוד הראשי"""
        try:
            main_url = self.base_urls['main']
            self.logger.info(f"🔎 סורק עמוד כרכים: {main_url}")
            driver.get(main_url)
            time.sleep(3)

            volumes = []
            links = driver.find_elements(By.TAG_NAME, 'a')
            for a in links:
                text = a.text.strip()
                href = a.get_attribute('href')
                if not href or 'aid/' not in href:
                    continue
                m = re.search(r'כרך\s+([א-ת]+)', text)
                if m:
                    heb = m.group(1)
                    num = self.hebrew_letter_to_number(heb)
                    volumes.append({'hebrew': heb, 'number': num, 'url': href, 'title': text})
            # ייחוד וסידור לפי מספר
            seen = set()
            uniq = []
            for v in volumes:
                key = (v['number'], v['hebrew'])
                if key not in seen:
                    seen.add(key)
                    uniq.append(v)
            uniq.sort(key=lambda x: x['number'] or 999)
            self.logger.info(f"📚 נמצאו {len(uniq)} כרכים")
            for v in uniq:
                self.logger.info(f"   כרך {v['hebrew']} ({v['number']}): {v['url']}")
            return uniq
        except Exception as e:
            self.logger.error(f"❌ שגיאה באיתור כרכים: {e}")
            return []
    
    def update_volume_stats(self, volume_id: int, total_letters: int):
        """עדכון סטטיסטיקות הכרך"""
        try:
            # חישוב טווח מכתבים מתוך המסד
            first_num = None
            last_num = None
            try:
                qmin = self.supabase.table('letters').select('letter_number').eq('volume_id', volume_id).order('letter_number', desc=False).limit(1).execute()
                qmax = self.supabase.table('letters').select('letter_number').eq('volume_id', volume_id).order('letter_number', desc=True).limit(1).execute()
                if qmin.data:
                    first_num = qmin.data[0]['letter_number']
                if qmax.data:
                    last_num = qmax.data[0]['letter_number']
            except Exception as e:
                self.logger.warning(f"⚠️ לא ניתן לחשב טווח מכתבים: {e}")

            update_data = {
                'total_letters': total_letters
            }
            if first_num is not None:
                update_data['first_letter_number'] = first_num
            if last_num is not None:
                update_data['last_letter_number'] = last_num

            self.supabase.table('volumes').update(update_data).eq('id', volume_id).execute()
            
            self.logger.info(f"📊 עודכנו סטטיסטיקות כרך: {total_letters} מכתבים")
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בעדכון סטטיסטיקות: {e}")
    
    def update_global_stats(self):
        """עדכון סטטיסטיקות כלליות"""
        try:
            # ספירת כל הנתונים
            volumes_count = self.supabase.table('volumes').select('id', count='exact').execute().count
            letters_count = self.supabase.table('letters').select('id', count='exact').execute().count
            dated_letters = self.supabase.table('letters').select('id', count='exact').eq('date_parsed', True).execute().count
            
            # עדכון טבלת הסטטיסטיקות
            stats_data = {
                'total_volumes': volumes_count,
                'total_letters': letters_count,
                'letters_with_dates': dated_letters,
                'last_parse_date': datetime.now().isoformat(),
                'parser_version': '2.1.0-fixed'
            }
            
            self.supabase.table('parsing_stats').update(stats_data).eq('id', 1).execute()
            
            self.logger.info(f"📊 סטטיסטיקות כלליות: {volumes_count} כרכים, {letters_count} מכתבים, {dated_letters} עם תאריכים")
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בעדכון סטטיסטיקות כלליות: {e}")
    
    def print_session_summary(self):
        """הדפסת סיכום הפעלה"""
        duration = datetime.now() - self.session_stats['start_time']
        
        print("\n" + "="*50)
        print("📊 סיכום פעלה - פרסר מתוקן")
        print("="*50)
        print(f"⏱️  זמן ריצה: {duration}")
        print(f"📝 מכתבים שעובדו: {self.session_stats['letters_processed']}")
        print(f"📅 מכתבים עם תאריכים: {self.session_stats['letters_with_dates']}")
        print(f"❌ שגיאות: {self.session_stats['errors']}")
        print(f"💾 נתונים נשמרו ב-Supabase")
        print("="*50)

def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='פרסר אגרות קודש מתוקן עם Supabase')
    parser.add_argument('--volume', type=str, default='א', help='כרך לפרסור (א, ב, ג...)')
    parser.add_argument('--max-letters', type=int, help='מספר מכתבים מקסימלי לפרסור')
    parser.add_argument('--test', action='store_true', help='מצב בדיקה (3 מכתבים בלבד)')
    parser.add_argument('--all-volumes', action='store_true', help='פרסור כל הכרכים ברצף עם חידוש אוטומטי')
    
    args = parser.parse_args()
    
    print("🗄️ פרסר אגרות קודש מתוקן עם Supabase")
    print("="*50)
    print("📋 מבוסס על המבנה האמיתי של אתר Chabad.org")
    print("🔗 מקורות:")
    print("   📚 כרך א: https://www.chabad.org/therebbe/article_cdo/aid/4643805/jewish/page.htm")
    print("   📄 מכתב 1: https://www.chabad.org/therebbe/article_cdo/aid/4645943/jewish/page.htm")
    print("="*50)
    
    # בדיקת הגדרות Supabase
    config = SupabaseConfig()
    
    # יצירת פרסר מתוקן
    fixed_parser = FixedIgrotParser(config.url, config.key)
    
    # הגדרת פרמטרים
    max_letters = 3 if args.test else args.max_letters
    
    try:
        if args.all_volumes:
            # איתור כל הכרכים ופרסור מדורג
            driver = fixed_parser.setup_driver()
            volumes = fixed_parser.find_all_volumes(driver) if driver else []
            if driver:
                driver.quit()
            for v in volumes:
                print(f"\n===== כרך {v['hebrew']} ({v['number']}) =====")
                fixed_parser.parse_volume(
                    volume_hebrew=v['hebrew'],
                    volume_number=v['number'],
                    volume_url=v['url'],
                    max_letters=max_letters,
                    resume=True
                )
            success = True
        else:
            # פרסור כרך בודד
            success = fixed_parser.parse_volume(
                volume_hebrew=args.volume,
                max_letters=max_letters,
                resume=True
            )
        
        if success:
            # עדכון סטטיסטיקות כלליות
            fixed_parser.update_global_stats()
            
            # הדפסת סיכום
            fixed_parser.print_session_summary()
            
            print("\n🎉 פרסור הושלם בהצלחה!")
            print("🌐 תוכל לראות את הנתונים ב-Supabase Dashboard")
        else:
            print("\n❌ פרסור נכשל")
            
    except KeyboardInterrupt:
        print("\n⚠️ פרסור הופסק על ידי המשתמש")
    except Exception as e:
        print(f"\n❌ שגיאה כללית: {e}")

if __name__ == "__main__":
    main()
