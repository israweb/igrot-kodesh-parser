#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
פרסר אגרות קודש עם אינטגרציה של Supabase
"""

import os
import sys
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from supabase import create_client, Client
import argparse
import json

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

class SupabaseIgrotParser:
    """פרסר אגרות קודש עם Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """אתחול הפרסר"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.date_parser = HebrewDateParser()
        self.setup_logging()
        self.session_stats = {
            'letters_processed': 0,
            'letters_with_dates': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
    def setup_logging(self):
        """הגדרת רישום לוגים"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/supabase_parser.log', encoding='utf-8'),
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
    
    def save_letter_to_supabase(self, volume_id: int, letter_data: dict) -> bool:
        """שמירת מכתב ל-Supabase"""
        try:
            # בדיקה אם המכתב כבר קיים
            existing = self.supabase.table('letters').select('id').eq('volume_id', volume_id).eq('letter_number', letter_data['letter_number']).execute()
            
            # הכנת נתוני המכתב
            letter_record = {
                'volume_id': volume_id,
                'letter_number': letter_data['letter_number'],
                'letter_hebrew': letter_data['letter_hebrew'],
                'day_numeric': letter_data.get('day_numeric'),
                'day_hebrew': letter_data.get('day_hebrew'),
                'month_hebrew': letter_data.get('month_hebrew'),
                'year_numeric': letter_data.get('year_numeric'),
                'year_hebrew': letter_data.get('year_hebrew'),
                'full_date_hebrew': letter_data.get('full_date_hebrew'),
                'url': letter_data['url'],
                'content': letter_data.get('content', ''),
                'date_parsed': letter_data.get('date_parsed', False)
            }
            
            if existing.data:
                # עדכון מכתב קיים
                result = self.supabase.table('letters').update(letter_record).eq('id', existing.data[0]['id']).execute()
                self.logger.info(f"🔄 עודכן מכתב קיים: {letter_data['letter_hebrew']}")
            else:
                # הוספת מכתב חדש
                result = self.supabase.table('letters').insert(letter_record).execute()
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
    
    def setup_driver(self):
        """הגדרת WebDriver עם אפשרויות מתקדמות"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            self.logger.error(f"❌ שגיאה בהגדרת WebDriver: {e}")
            return None
    
    def extract_letter_content(self, driver, url: str) -> str:
        """חילוץ תוכן המכתב מהדף"""
        try:
            driver.get(url)
            time.sleep(2)
            
            # נסיון למצוא את תוכן המכתב
            content_selectors = [
                '.articleContent',
                '.article-content', 
                '#articleContent',
                '.content-body',
                '.main-content'
            ]
            
            for selector in content_selectors:
                try:
                    content_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    return content_element.text.strip()
                except:
                    continue
            
            # אם לא נמצא content ספציפי, ניקח את הטקסט הכללי
            body = driver.find_element(By.TAG_NAME, 'body')
            return body.text.strip()[:1000]  # מגביל ל-1000 תווים
            
        except Exception as e:
            self.logger.warning(f"⚠️ לא ניתן לחלץ תוכן מ-{url}: {e}")
            return ""
    
    def find_letters_on_page(self, driver, base_url: str, page_num: int = 1) -> list:
        """מציאת קישורי מכתבים בעמוד"""
        try:
            if page_num > 1:
                page_url = f"{base_url}?page={page_num}"
            else:
                page_url = base_url
                
            self.logger.info(f"🔍 סורק עמוד {page_num}: {page_url}")
            driver.get(page_url)
            time.sleep(3)
            
            # חיפוש קישורי מכתבים - סלקטורים מרובים
            letter_links = []
            
            # רשימת סלקטורים אפשריים למכתבים
            selectors = [
                'a[href*="Letter"]',
                'a[href*="letter"]', 
                'a[href*="מכתב"]',
                'a[href*="aid"]',
                'a[title*="מכתב"]',
                '.letter-link',
                '.letter a',
                'a:contains("מכתב")'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.info(f"   🔍 סלקטור '{selector}': נמצאו {len(elements)} אלמנטים")
                    
                    for link in elements:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        
                        if href and ('aid' in href or 'Letter' in href or 'מכתב' in href) and text:
                            letter_links.append({
                                'url': href,
                                'text': text
                            })
                            
                    if letter_links:
                        break  # אם מצאנו קישורים, לא צריך לנסות סלקטורים נוספים
                        
                except Exception as e:
                    self.logger.debug(f"   ⚠️ סלקטור '{selector}' נכשל: {e}")
                    continue
            
            self.logger.info(f"📄 נמצאו {len(letter_links)} מכתבים בעמוד {page_num}")
            return letter_links
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בסריקת עמוד {page_num}: {e}")
            self.log_to_supabase('ERROR', f'שגיאה בסריקת עמוד {page_num}: {e}', error_details={'page_url': page_url, 'error': str(e)})
            return []
    
    def parse_single_letter(self, driver, letter_info: dict, volume_id: int, letter_number: int) -> dict:
        """פרסור מכתב יחיד"""
        try:
            self.logger.info(f"📖 מפרסר מכתב {letter_number}: {letter_info['url']}")
            
            # חילוץ תוכן המכתב
            content = self.extract_letter_content(driver, letter_info['url'])
            
            # המרת מספר מכתב לעברית
            hebrew_numbers = {1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט', 10: 'י'}
            letter_hebrew = hebrew_numbers.get(letter_number, str(letter_number))
            
            # פרסור תאריך מתוכן המכתב
            date_info = None
            date_parsed = False
            
            if content:
                date_info = self.date_parser.extract_date_from_text(content)
                date_parsed = date_info is not None
            
            # הכנת נתוני המכתב
            letter_data = {
                'letter_number': letter_number,
                'letter_hebrew': letter_hebrew,
                'url': letter_info['url'],
                'content': content,
                'date_parsed': date_parsed
            }
            
            # הוספת נתוני תאריך אם נמצאו
            if date_info:
                letter_data.update({
                    'day_numeric': date_info.get('day_numeric'),
                    'day_hebrew': date_info.get('day_hebrew'),
                    'month_hebrew': date_info.get('month_hebrew'),
                    'year_numeric': date_info.get('year_numeric'),
                    'year_hebrew': date_info.get('year_hebrew'),
                    'full_date_hebrew': date_info.get('full_date_hebrew')
                })
                self.logger.info(f"📅 נמצא תאריך: {date_info.get('full_date_hebrew')}")
            else:
                self.logger.warning(f"❓ לא נמצא תאריך במכתב {letter_number}")
            
            # שמירה ל-Supabase
            if self.save_letter_to_supabase(volume_id, letter_data):
                self.log_to_supabase('INFO', f'נשמר מכתב {letter_hebrew} בהצלחה', letter_number=letter_number, url=letter_info['url'])
                return letter_data
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ שגיאה בפרסור מכתב {letter_number}: {e}")
            self.log_to_supabase('ERROR', f'שגיאה בפרסור מכתב {letter_number}: {e}', 
                               letter_number=letter_number, url=letter_info.get('url'), error_details={'error': str(e)})
            return None
    
    def parse_volume(self, volume_number: int, volume_hebrew: str, base_url: str, max_letters: int = None):
        """פרסור כרך שלם"""
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
            letters_processed = 0
            page_num = 1
            
            while True:
                # סריקת עמוד עבור מכתבים
                letter_links = self.find_letters_on_page(driver, base_url, page_num)
                
                if not letter_links:
                    self.logger.info(f"✅ לא נמצאו עוד מכתבים בעמוד {page_num}")
                    break
                
                # פרסור כל מכתב בעמוד
                for i, letter_info in enumerate(letter_links):
                    letter_number = letters_processed + i + 1
                    
                    if max_letters and letter_number > max_letters:
                        self.logger.info(f"🔢 הגעתי למגבלה: {max_letters} מכתבים")
                        break
                    
                    self.parse_single_letter(driver, letter_info, volume_id, letter_number)
                    time.sleep(1)  # הפסקה בין מכתבים
                
                letters_processed += len(letter_links)
                
                if max_letters and letters_processed >= max_letters:
                    break
                
                page_num += 1
                time.sleep(2)  # הפסקה בין עמודים
            
            # עדכון סטטיסטיקות הכרך
            self.update_volume_stats(volume_id, letters_processed)
            
            self.logger.info(f"✅ הושלם פרסור כרך {volume_hebrew}: {letters_processed} מכתבים")
            self.log_to_supabase('INFO', f'הושלם פרסור כרך {volume_hebrew}: {letters_processed} מכתבים', volume_number)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה כללית בפרסור כרך: {e}")
            self.log_to_supabase('ERROR', f'שגיאה כללית בפרסור כרך {volume_hebrew}: {e}', volume_number, error_details={'error': str(e)})
            return False
            
        finally:
            driver.quit()
    
    def update_volume_stats(self, volume_id: int, total_letters: int):
        """עדכון סטטיסטיקות הכרך"""
        try:
            self.supabase.table('volumes').update({
                'total_letters': total_letters
            }).eq('id', volume_id).execute()
            
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
                'parser_version': '2.0.0'
            }
            
            self.supabase.table('parsing_stats').update(stats_data).eq('id', 1).execute()
            
            self.logger.info(f"📊 סטטיסטיקות כלליות: {volumes_count} כרכים, {letters_count} מכתבים, {dated_letters} עם תאריכים")
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בעדכון סטטיסטיקות כלליות: {e}")
    
    def print_session_summary(self):
        """הדפסת סיכום הפעלה"""
        duration = datetime.now() - self.session_stats['start_time']
        
        print("\n" + "="*50)
        print("📊 סיכום פעלה")
        print("="*50)
        print(f"⏱️  זמן ריצה: {duration}")
        print(f"📝 מכתבים שעובדו: {self.session_stats['letters_processed']}")
        print(f"📅 מכתבים עם תאריכים: {self.session_stats['letters_with_dates']}")
        print(f"❌ שגיאות: {self.session_stats['errors']}")
        print(f"💾 נתונים נשמרו ב-Supabase")
        print("="*50)

def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='פרסר אגרות קודש עם Supabase')
    parser.add_argument('--volume', type=str, default='א', help='כרך לפרסור (א, ב, ג...)')
    parser.add_argument('--max-letters', type=int, help='מספר מכתבים מקסימלי לפרסור')
    parser.add_argument('--test', action='store_true', help='מצב בדיקה (3 מכתבים בלבד)')
    
    args = parser.parse_args()
    
    print("🗄️ פרסר אגרות קודש עם Supabase")
    print("="*50)
    
    # בדיקת הגדרות Supabase
    config = SupabaseConfig()
    
    # יצירת פרסר
    supabase_parser = SupabaseIgrotParser(config.url, config.key)
    
    # הגדרת פרמטרים
    volume_mapping = {'א': 1, 'ב': 2, 'ג': 3}
    volume_number = volume_mapping.get(args.volume, 1)
    
    base_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    max_letters = 3 if args.test else args.max_letters
    
    try:
        # פרסור הכרך
        success = supabase_parser.parse_volume(
            volume_number=volume_number,
            volume_hebrew=args.volume,
            base_url=base_url,
            max_letters=max_letters
        )
        
        if success:
            # עדכון סטטיסטיקות כלליות
            supabase_parser.update_global_stats()
            
            # הדפסת סיכום
            supabase_parser.print_session_summary()
            
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
