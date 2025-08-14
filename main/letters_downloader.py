#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик всех писем Аврат Кодеш (Священных писем) с chabad.org
"""

import time
import os
import logging
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup


class LettersDownloader:
    def __init__(self, download_dir="igrot_kodesh", headless=True):
        """
        אתחול מטעין המכתבים
        
        Args:
            download_dir (str): תיקייה לשמירת המכתבים
            headless (bool): להפעיל את הדפדפן במצב headless
        """
        self.download_dir = download_dir
        self.headless = headless
        self.driver = None
        self.processed_urls = set()
        self.saved_letters = 0
        
        # שינוי תצורת הלוגים עם force=True לשינוי
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # יצירת תיקייה ללוגים אם היא לא קיימת
        os.makedirs('../logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/letters_downloader.log', encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )
        self.logger = logging.getLogger(__name__)
        
        # יצירת תיקייה למכתבים
        os.makedirs(self.download_dir, exist_ok=True)
        
        # אתחול דרייבר
        self._init_driver()
    
    def _init_driver(self):
        """אתחול דרייבר Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # הגדרות להפרעת גיבוי דפדפן
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            # User-Agent ממשקלי ממשקל
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # מחיקת סמל האוטומציה
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome WebDriver נטען בהצלחה")
            
        except Exception as e:
            self.logger.error(f"שגיאה באתחול דרייבר WebDriver: {e}")
            raise
    
    def get_page_with_selenium(self, url, wait_time=10):
        """קבלת דף עם עזרת Selenium"""
        try:
            self.logger.info(f"טוען דף: {url}")
            self.driver.get(url)
            
            # המתן לטעינת הדף
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # המנהלת תפוסה נוספת לטעינה מלאה
            time.sleep(2)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            self.logger.info(f"דף נטען ({len(html)} תווים)")
            return soup
            
        except Exception as e:
            self.logger.error(f"שגיאה בטעינת {url}: {e}")
            return None
    
    def find_volume_links(self, soup, base_url):
        """
        חיפוש קישורים לכרכים (כרכים)
        
        Args:
            soup (BeautifulSoup): דף נטען מחדש
            base_url (str): URL בסיסי
            
        Returns:
            list: רשימת URL של הכרכים
        """
        volume_links = []
        
        try:
            # חיפוש כל הקישורים שמכילים "אגרות קודש - כרך"
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                if 'אגרות קודש - כרך' in link_text and link_text not in ['אגרות קודש »']:
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    volume_links.append({
                        'url': full_url,
                        'title': link_text,
                        'volume': link_text
                    })
                    self.logger.info(f"כרך נמצא: {link_text} -> {full_url}")
            
            self.logger.info(f"כרכים נמצאו: {len(volume_links)}")
            return volume_links
            
        except Exception as e:
            self.logger.error(f"שגיאה בחיפוש כרכים: {e}")
            return []
    
    def find_letter_links(self, soup, base_url, volume_title):
        """
        חיפוש קישורים למכתבים בודדים עם תמיכה בפיגינציה
        
        Args:
            soup (BeautifulSoup): דף נטען של כרך
            base_url (str): URL בסיסי
            volume_title (str): כותרת הכרך
            
        Returns:
            list: רשימת URL של המכתבים
        """
        all_letters = []
        
        try:
            self.logger.info(f"🔍 מתחילים חיפוש מכתבים בכרך {volume_title}")
            self.logger.info(f"🌐 URL כרך: {base_url}")
            
            # טיפול בכל דף של הכרך (פיגינציה)
            current_page = 1
            max_pages = 50  # הגבלה לטובת בטיחות
            
            while current_page <= max_pages:
                if current_page == 1:
                    page_url = base_url
                    page_soup = soup
                else:
                    page_url = f"{base_url}/page/{current_page}"
                    self.logger.info(f"📄 טוען דף {current_page}: {page_url}")
                    page_soup = self.get_page_with_selenium(page_url)
                    if not page_soup:
                        self.logger.info(f"❌ דף {current_page} לא נמצא, סיימנו את החיפוש המכתבים")
                        break
                
                # חיפוש מכתבים בדף הנוכחי
                page_letters = self._extract_letters_from_page(page_soup, page_url, volume_title, current_page)
                
                if page_letters:
                    all_letters.extend(page_letters)
                    self.logger.info(f"📝 מכתבים נמצאו בדף {current_page}: {len(page_letters)}")
                else:
                    self.logger.info(f"📝 בדף {current_page} מכתבים לא נמצאו")
                
                # בדיקת קישור לדף הבא
                next_page_link = page_soup.find('a', {'id': 'Paginator_NextPage'})
                if not next_page_link:
                    # חיפוש אלטרנטיבי לקישור לדף הבא
                    next_link = page_soup.find('link', {'rel': 'next'})
                    if not next_link:
                        self.logger.info(f"📄 הגענו לדף האחרון: {current_page}")
                        break
                
                current_page += 1
                time.sleep(1)  # המנהלת תפוסה בין דפים
            
            # מחיקת הכפילויות
            unique_letters = []
            seen_urls = set()
            for letter in all_letters:
                if letter['url'] not in seen_urls:
                    seen_urls.add(letter['url'])
                    unique_letters.append(letter)
            
            self.logger.info(f"📊 סה\"כ בכרך {volume_title}:")
            self.logger.info(f"   📄 דפים שנטענו: {current_page}")
            self.logger.info(f"   📝 מכתבים נמצאו: {len(unique_letters)}")
            
            # רישום דוגמאות של המכתבים הראשונים
            if unique_letters:
                self.logger.info(f"📋 דוגמאות למכתבים נמצאו:")
                for i, letter in enumerate(unique_letters[:5], 1):
                    self.logger.info(f"   {i}. {letter['title']}")
            
            return unique_letters
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בחיפוש מכתבים בכרך {volume_title}: {e}")
            return []
    
    def _extract_letters_from_page(self, soup, page_url, volume_title, page_num):
        """
        הוצאת מכתבים מדף אחד
        
        Args:
            soup (BeautifulSoup): דף נטען
            page_url (str): URL של הדף
            volume_title (str): כותרת הכרך
            page_num (int): מספר הדף
            
        Returns:
            list: רשימת המכתבים בדף
        """
        letters = []
        
        try:
            # חיפוש אלמנטים עם טקסט "מכתב" (מכתב)
            letter_elements = soup.find_all(text=re.compile(r'מכתב'))
            self.logger.info(f"🔤 בדף {page_num} נמצאו אלמנטים עם 'מכתב': {len(letter_elements)}")
            
            for element in letter_elements:
                # מציאת האלמנט ההורה עם קישור
                parent = element.parent
                while parent and parent.name != 'html':
                    link = parent.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        text = element.strip()
                        
                        # בדיקת קישור למכתב
                        if href and 'letter' in href.lower() or 'aid=' in href:
                            full_url = urljoin(page_url, href)
                            letters.append({
                                'url': full_url,
                                'title': text,
                                'volume': volume_title,
                                'page': page_num,
                                'href': href
                            })
                            break
                    parent = parent.parent
            
            # חיפוש אלטרנטיבי: חיפוש קישורים עם תבניות מסוימות בטקסט
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # בדיקת תבניות למכתבים
                if (text and 
                    ('מכתב' in text or 
                     re.search(r'\d+', text) and len(text) < 20 and
                     any(char in 'אבגדהוזחטיכלמנסעפצקרשת' for char in text))):
                    
                    # סילוק קישורים ניווטיים
                    if not any(pattern in text.lower() for pattern in 
                              ['browse', 'next', 'previous', 'page', 'home']):
                        
                        full_url = urljoin(page_url, href)
                        # סילוק כפילויות
                        if not any(l['url'] == full_url for l in letters):
                            letters.append({
                                'url': full_url,
                                'title': text,
                                'volume': volume_title,
                                'page': page_num,
                                'href': href
                            })
            
            return letters
            
        except Exception as e:
            self.logger.error(f"❌ שגיאה בהוצאת מכתבים מדף {page_num}: {e}")
            return []
    
    def extract_letter_content(self, soup, url):
        """הוצאת תוכן המכתב"""
        try:
            # סילוק טיפוסים לא רצויים
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # חיפוש תוכן המכתב העיקרי
            content_selectors = [
                '.article-body', '.post-content', '.entry-content',
                '.content', '.text-content', '.letter-content',
                'main', 'article', '[role="main"]'
            ]
            
            main_content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    main_content = content
                    break
            
            if not main_content:
                # אם לא מצאנו טיפוס ספציפי, חיפוש דיב עם הרבה טקסט
                divs = soup.find_all('div')
                for div in divs:
                    text = div.get_text(strip=True)
                    if len(text) > 500:  # מינימום 500 תווים
                        main_content = div
                        break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # הוצאת טקסט
                text = main_content.get_text(separator='\n', strip=True)
                
                # ניקוי מרווחים ושורות חדשות
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r'[ \t]+', ' ', text)
                
                if text and len(text.strip()) > 100:
                    return text.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"שגיאה בהוצאת תוכן המכתב {url}: {e}")
            return None
    
    def save_letter(self, content, letter_info):
        """שמירת מכתב בקובץ"""
        try:
            # הוצאת כרך ומספר המכתב
            volume_title = letter_info['volume']  # למשל: "אגרות קודש - כרך א"
            original_title = letter_info['title']  # למשל: "אגרות קודש - מכתב פד"
            
            # הוצאת כרך (כרך X)
            volume_match = re.search(r'(כרך\s+[א-ת]+)', volume_title)
            volume_part = volume_match.group(1) if volume_match else "כרך א"
            
            # הוצאת מספר המכתב (מכתב X)
            letter_match = re.search(r'(מכתב\s+[א-ת]+)', original_title)
            letter_part = letter_match.group(1) if letter_match else "מכתב א"
            
            # יצירת כותרת לתוכן הקובץ
            # פורמט: אגרות קודש - כרך א - מכתב פד
            file_header = f"אגרות קודש - {volume_part} - {letter_part}"
            
            # יצירת שם קובץ עם שמות קצרים
            # פורמט: אק - כרך א - מכתב פד
            filename_base = f"אק - {volume_part} - {letter_part}"
            
            # ניקוי שמות קבצים מתווכים (משאיר רק אותיות וסימנים בסיסיים)
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename_base)
            safe_filename = re.sub(r'[^\w\s\-_\u0590-\u05FF]', '', safe_filename)
            
            filename = f"{safe_filename}.txt"
            if len(filename) > 200:  # הגבלת אורך שם הקובץ
                filename = filename[:190] + ".txt"
            
            file_path = os.path.join(self.download_dir, filename)
            
            # בדיקת קיום קובץ
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # שמירת הקובץ עם פורמט כותרת חדש
            with open(file_path, 'w', encoding='utf-8') as f:
                # רק כותרת המכתב בפורמט החדש
                f.write(f"{file_header}\n\n")
                f.write(content)
            
            self.logger.info(f"מכתב נשמר: {os.path.basename(file_path)} ({len(content)} תווים)")
            self.saved_letters += 1
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת המכתב: {e}")
            return False
    
    def download_letters_from_volume(self, volume_info):
        """הורדת כל המכתבים מכרך אחד"""
        self.logger.info(f"מתחילים טיפול בכרך: {volume_info['title']}")
        
        # קבלת דף הכרך
        soup = self.get_page_with_selenium(volume_info['url'])
        if not soup:
            return 0
        
        # חיפוש קישורים למכתבים
        letter_links = self.find_letter_links(soup, volume_info['url'], volume_info['title'])
        
        downloaded_count = 0
        for i, letter_info in enumerate(letter_links, 1):
            if letter_info['url'] in self.processed_urls:
                continue
                
            self.processed_urls.add(letter_info['url'])
            
            self.logger.info(f"טיפול במכתב {i}/{len(letter_links)}: {letter_info['title']}")
            
            # קבלת תוכן המכתב
            letter_soup = self.get_page_with_selenium(letter_info['url'])
            if letter_soup:
                content = self.extract_letter_content(letter_soup, letter_info['url'])
                if content:
                    if self.save_letter(content, letter_info):
                        downloaded_count += 1
                else:
                    self.logger.warning(f"לא ניתן להוציא תוכן: {letter_info['title']}")
            
            # המנהלת תפוסה בין מכתבים
            time.sleep(2)
        
        self.logger.info(f"מכתבים נשמרו מכרך {volume_info['title']}: {downloaded_count}")
        return downloaded_count
    
    def download_all_letters(self, start_url):
        """שיטה ראשית להורדת כל המכתבים"""
        self.logger.info("🚀 מתחילים הורדת כל המכתבים של אברט קודש")
        self.logger.info(f"דף מפתח: {start_url}")
        
        try:
            # קבלת דף הראשי עם רשימת הכרכים
            soup = self.get_page_with_selenium(start_url)
            if not soup:
                self.logger.error("לא ניתן לטעון את דף הראשי")
                return
            
            # חיפוש כל הכרכים
            volume_links = self.find_volume_links(soup, start_url)
            if not volume_links:
                self.logger.error("לא נמצאו קישורים לכרכים")
                return
            
            total_letters = 0
            
            # טיפול בכל כרך
            for i, volume_info in enumerate(volume_links, 1):
                self.logger.info(f"📚 טיפול בכרך {i}/{len(volume_links)}: {volume_info['title']}")
                
                letters_count = self.download_letters_from_volume(volume_info)
                total_letters += letters_count
                
                # המנהלת תפוסה בין כרכים
                if i < len(volume_links):
                    self.logger.info("⏳ המנהלת תפוסה 5 שניות בין כרכים...")
                    time.sleep(5)
            
            self.logger.info(f"🎉 סיימנו! סה\"כ נשמרו מכתבים: {total_letters}")
            self.logger.info(f"📂 המכתבים נשמרו בתיקייה: {self.download_dir}")
            
        except Exception as e:
            self.logger.error(f"שגיאה קריטית: {e}")
        finally:
            self.close()
    
    def close(self):
        """סגירת הדפדפן"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver נסגר")
            except Exception as e:
                self.logger.error(f"שגיאה בסגירת WebDriver: {e}")


def main():
    """שיטה ראשית"""
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    print("📚 מטעין מכתבי אגרות קודש")
    print("=" * 50)
    print("🎯 מתחילים הורדת כל המכתבים מכל הכרכים")
    print("📂 התוצאה תושמר בתיקייה 'igrot_kodesh'")
    print("⏰ זה יכול לקחת כמה שעות...")
    print("=" * 50)
    
    try:
        downloader = LettersDownloader(download_dir="igrot_kodesh", headless=True)
        downloader.download_all_letters(start_url)
        
        print("\n✅ התהליך סיים!")
        print("📋 בדוק את קובץ הלוג '../logs/letters_downloader.log' לפרטים")
        print("📂 המכתבים נמצאים בתיקייה 'igrot_kodesh'")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")


if __name__ == "__main__":
    main()
