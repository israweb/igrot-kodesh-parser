#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Приложение для скачивания текстовых файлов с сайта chabad.org
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from urllib.parse import urljoin, urlparse
import re


class TextFileDownloader:
    def __init__(self, base_url, download_dir="downloaded_texts"):
        """
        Инициализация загрузчика текстовых файлов
        
        Args:
            base_url (str): Базовый URL для скачивания
            download_dir (str): Директория для сохранения файлов
        """
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        
        # Более реалистичные заголовки для обхода блокировок
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Настройка логирования
        # Создаем папку для логов если её нет
        os.makedirs('../logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/downloader.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Создание директории для скачивания
        os.makedirs(self.download_dir, exist_ok=True)
        
    def is_text_file(self, url):
        """
        Проверка, является ли файл текстовым
        
        Args:
            url (str): URL файла
            
        Returns:
            bool: True если файл текстовый
        """
        text_extensions = ['.txt', '.pdf', '.doc', '.docx', '.rtf']
        return any(url.lower().endswith(ext) for ext in text_extensions)
    
    def get_page_content(self, url, retries=3):
        """
        Получение содержимого страницы с повторными попытками
        
        Args:
            url (str): URL страницы
            retries (int): Количество попыток
            
        Returns:
            BeautifulSoup: Парсированное содержимое страницы или None
        """
        for attempt in range(retries):
            try:
                # Добавляем рефerer для большей реалистичности
                headers = {}
                if attempt > 0:
                    headers['Referer'] = url
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка при повторах
                
                response = self.session.get(url, timeout=15, headers=headers)
                
                # Специальная обработка для разных кодов ошибок
                if response.status_code == 403:
                    self.logger.warning(f"הגנה נדחתה (403) ל-{url}, נסיון {attempt + 1}/{retries}")
                    if attempt < retries - 1:
                        # Пробуем с другим User-Agent
                        user_agents = [
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
                        ]
                        self.session.headers['User-Agent'] = user_agents[attempt % len(user_agents)]
                        continue
                
                response.raise_for_status()
                
                # Проверяем, что получили HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    self.logger.warning(f"סוג תוכן לא צפוי: {content_type} ל-{url}")
                
                self.logger.info(f"דף נטען בהצלחה: {url} (גודל: {len(response.content)} בייטים)")
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"זמן חום לטעינת {url}, נסיון {attempt + 1}/{retries}")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"שגיאת חיבור ל-{url}, נסיון {attempt + 1}/{retries}")
            except requests.RequestException as e:
                self.logger.error(f"שגיאה בטעינת דף {url}, נסיון {attempt + 1}/{retries}: {e}")
            
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                self.logger.info(f"ממתין {wait_time} שניות לפני נסיון חוזר...")
                time.sleep(wait_time)
        
        self.logger.error(f"לא ניתן לטעון את הדף {url} אחרי {retries} נסיונות")
        return None
    
    def extract_text_links(self, soup, base_url):
        """
        Извлечение ссылок на текстовые файлы из HTML
        
        Args:
            soup (BeautifulSoup): Парсированная страница
            base_url (str): Базовый URL для относительных ссылок
            
        Returns:
            set: Множество URL текстовых файлов
        """
        text_links = set()
        
        # Поиск всех ссылок на странице
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Проверка на текстовые файлы
            if self.is_text_file(full_url):
                text_links.add(full_url)
        
        # Поиск ссылок в тексте страницы (может быть полезно)
        page_text = soup.get_text()
        # Поиск URL-адресов в тексте
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*\.(?:txt|pdf|doc|docx|rtf)'
        found_urls = re.findall(url_pattern, page_text, re.IGNORECASE)
        text_links.update(found_urls)
        
        return text_links
    
    def extract_page_text(self, soup, url):
        """
        Извлечение текстового содержимого прямо со страницы
        
        Args:
            soup (BeautifulSoup): Парсированная страница
            url (str): URL страницы
            
        Returns:
            str: Извлеченный текст или None
        """
        try:
            # Удаляем нежелательные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Ищем основной контент
            main_content = None
            
            # Попытки найти основной контент по различным селекторам
            content_selectors = [
                'main', 'article', '.content', '.post', '.entry', 
                '.article-body', '.post-content', '.entry-content',
                '[role="main"]', '.main-content', '#content'
            ]
            
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    main_content = content
                    break
            
            # Если не нашли специфичный контент, берем body
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Извлекаем текст
                text = main_content.get_text(separator='\n', strip=True)
                
                # Фильтруем слишком короткий или пустой текст
                if text and len(text.strip()) > 100:
                    self.logger.info(f"טקסט נלקח מדף {url} (אורך: {len(text)} תווים)")
                    return text
            
            return None
            
        except Exception as e:
            self.logger.error(f"שגיאה בזיהוי טקסט מדף {url}: {e}")
            return None
    
    def save_text_content(self, text, url, filename_prefix="page_content"):
        """
        Сохранение текстового содержимого в файл
        
        Args:
            text (str): Текст для сохранения
            url (str): URL источника
            filename_prefix (str): Префикс имени файла
            
        Returns:
            bool: True если файл успешно сохранен
        """
        try:
            # Создание имени файла на основе URL
            parsed_url = urlparse(url)
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', parsed_url.path.replace('/', '_'))
            if not safe_name:
                safe_name = f"{filename_prefix}_{int(time.time())}"
            
            filename = f"{filename_prefix}_{safe_name}.txt"
            file_path = os.path.join(self.download_dir, filename)
            
            # Проверка на существование файла
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Сохранение файла
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"מקור: {url}\n")
                f.write(f"תאריך הוצאה: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(text)
            
            self.logger.info(f"טקסט של דף נשמר: {os.path.basename(file_path)} ({len(text)} תווים)")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת הטקסט: {e}")
            return False
    
    def download_file(self, url, filename=None):
        """
        Скачивание файла
        
        Args:
            url (str): URL файла
            filename (str): Имя файла для сохранения (опционально)
            
        Returns:
            bool: True если файл успешно скачан
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Определение имени файла
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"file_{int(time.time())}.txt"
            
            # Создание безопасного имени файла
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            file_path = os.path.join(self.download_dir, safe_filename)
            
            # Проверка, не существует ли файл уже
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Сохранение файла
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"קובץ נורה: {safe_filename} ({len(response.content)} בייטים)")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"שגיאה בהורדת {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"שגיאה לא צפויה בהורדת {url}: {e}")
            return False
    
    def crawl_and_download(self, max_depth=2, delay=1, extract_page_content=True):
        """
        Основной метод для поиска и скачивания текстовых файлов
        
        Args:
            max_depth (int): Максимальная глубина обхода страниц
            delay (int): Задержка между запросами (в секундах)
            extract_page_content (bool): Извлекать ли текст прямо со страниц
        """
        visited_urls = set()
        urls_to_visit = [self.base_url]
        downloaded_files = set()
        saved_pages = set()
        
        self.logger.info(f"נתחיל חיפוש קבצי טקסט ב-{self.base_url}")
        self.logger.info(f"הוצאת תוכן דפים: {'כולל' if extract_page_content else 'מושמץ'}")
        
        for depth in range(max_depth):
            if not urls_to_visit:
                break
                
            self.logger.info(f"מעבר עומק {depth + 1}, דפים: {len(urls_to_visit)}")
            current_level_urls = urls_to_visit.copy()
            urls_to_visit = []
            
            for url in current_level_urls:
                if url in visited_urls:
                    continue
                    
                visited_urls.add(url)
                
                # Получение содержимого страницы
                soup = self.get_page_content(url)
                if not soup:
                    continue
                
                # Извлечение и сохранение текстового содержимого страницы
                if extract_page_content and url not in saved_pages:
                    page_text = self.extract_page_text(soup, url)
                    if page_text:
                        if self.save_text_content(page_text, url):
                            saved_pages.add(url)
                
                # Извлечение ссылок на текстовые файлы
                text_links = self.extract_text_links(soup, url)
                
                # Скачивание найденных текстовых файлов
                for text_url in text_links:
                    if text_url not in downloaded_files:
                        if self.download_file(text_url):
                            downloaded_files.add(text_url)
                        time.sleep(delay)  # Вежливая задержка
                
                # Добавление новых страниц для обхода (только с того же домена)
                if depth < max_depth - 1:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        # Проверка, что ссылка ведет на тот же домен
                        if (urlparse(full_url).netloc == urlparse(self.base_url).netloc and 
                            full_url not in visited_urls and 
                            full_url not in urls_to_visit and
                            not self.is_text_file(full_url)):
                            urls_to_visit.append(full_url)
                
                time.sleep(delay)  # Вежливая задержка между страницами
        
        total_items = len(downloaded_files) + len(saved_pages)
        self.logger.info(f"הסתיים. קובצים נורים: {len(downloaded_files)}, דפים נשמרים: {len(saved_pages)}")
        self.logger.info(f"סהכ פריטים: {total_items}")
        self.logger.info(f"קבצים נשמרים בתיקיית: {self.download_dir}")


def main():
    """Основная функция"""
    # URL להורדה
    target_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    # יצירת מופע של טוען הקבצים
    downloader = TextFileDownloader(target_url)
    
    # הפעלת חיפוש והורדת קבצים
    print("נתחיל חיפוש והורדת קבצים טקסטיים...")
    print(f"URL היעד: {target_url}")
    print(f"קבצים יושמרו בתיקיית: {downloader.download_dir}")
    
    try:
        downloader.crawl_and_download(max_depth=2, delay=1, extract_page_content=True)
        print("\nהתהליך הושלם. בדוק את קובץ הלוג '../logs/downloader.log' לפרטים.")
    except KeyboardInterrupt:
        print("\nהתהליך בוטל על ידי המשתמש.")
    except Exception as e:
        print(f"\nהתרה שגיאה: {e}")


if __name__ == "__main__":
    main()
