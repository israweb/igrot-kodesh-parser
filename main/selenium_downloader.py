#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная версия загрузчика с поддержкой Selenium для обхода защиты от ботов
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
import requests


class SeleniumTextDownloader:
    def __init__(self, base_url, download_dir="downloaded_texts", headless=True):
        """
        Инициализация загрузчика с Selenium
        
        Args:
            base_url (str): Базовый URL для скачивания
            download_dir (str): Директория для сохранения файлов
            headless (bool): Запускать браузер в headless режиме
        """
        self.base_url = base_url
        self.download_dir = download_dir
        self.headless = headless
        self.driver = None
        
        # Настройка логирования
        # Создаем папку для логов если её нет
        os.makedirs('../logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('../logs/selenium_downloader.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Создание директории для скачивания
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Инициализация драйвера
        self._init_driver()
    
    def _init_driver(self):
        """Инициализация Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Настройки для обхода детекции
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            # Реалистичный User-Agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Удаление маркера автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome WebDriver успешно инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации WebDriver: {e}")
            self.logger.info("Убедитесь, что ChromeDriver установлен и находится в PATH")
            raise
    
    def get_page_with_selenium(self, url, wait_time=10):
        """
        Получение страницы с помощью Selenium
        
        Args:
            url (str): URL страницы
            wait_time (int): Время ожидания загрузки
            
        Returns:
            BeautifulSoup: Парсированное содержимое или None
        """
        try:
            self.logger.info(f"טוען דף עם Selenium: {url}")
            self.driver.get(url)
            
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Дополнительная пауза для полной загрузки
            time.sleep(3)
            
            # Получение HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            self.logger.info(f"דף טוען בהצלחה ({len(html)} תווים)")
            return soup
            
        except TimeoutException:
            self.logger.error(f"טיימאוט בטעינת הדף: {url}")
            return None
        except WebDriverException as e:
            self.logger.error(f"שגיאת WebDriver בטעינת {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"שגיאה לא צפויה בטעינת {url}: {e}")
            return None
    
    def extract_text_content(self, soup, url):
        """
        Извлечение текстового содержимого со страницы
        
        Args:
            soup (BeautifulSoup): Парсированная страница
            url (str): URL страницы
            
        Returns:
            str: Извлеченный текст или None
        """
        try:
            # Удаляем нежелательные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Поиск основного контента
            content_selectors = [
                'main', 'article', '.content', '.post', '.entry', 
                '.article-body', '.post-content', '.entry-content',
                '[role="main"]', '.main-content', '#content',
                '.text-content', '.article-text'
            ]
            
            main_content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    main_content = content
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Извлекаем текст
                text = main_content.get_text(separator='\n', strip=True)
                
                # Очистка от лишних пробелов и переносов
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r'[ \t]+', ' ', text)
                
                if text and len(text.strip()) > 200:
                    self.logger.info(f"טקסט נלקח מדף {url} (אורך: {len(text)} תווים)")
                    return text.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"שגיאה בזיהוי טקסט מדף {url}: {e}")
            return None
    
    def save_content(self, content, url, content_type="page"):
        """
        Сохранение содержимого в файл
        
        Args:
            content (str): Содержимое для сохранения
            url (str): URL источника
            content_type (str): Тип содержимого
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            # Создание имени файла
            parsed_url = urlparse(url)
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', parsed_url.path.replace('/', '_'))
            if not safe_name:
                safe_name = f"{content_type}_{int(time.time())}"
            
            filename = f"{content_type}_{safe_name}.txt"
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
                f.write(f"תאריך שיעור: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"סוג: {content_type}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)
            
            self.logger.info(f"קובץ נשמר: {os.path.basename(file_path)} ({len(content)} תווים)")
            return True
            
        except Exception as e:
            self.logger.error(f"שגיאה בשמירת הקובץ: {e}")
            return False
    
    def find_and_download_files(self, soup, base_url):
        """
        Поиск и скачивание файлов по ссылкам
        
        Args:
            soup (BeautifulSoup): Парсированная страница
            base_url (str): Базовый URL
            
        Returns:
            int: Количество скачанных файлов
        """
        downloaded_count = 0
        text_extensions = ['.txt', '.pdf', '.doc', '.docx', '.rtf']
        
        try:
            # Поиск ссылок на файлы
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Проверка расширения файла
                if any(full_url.lower().endswith(ext) for ext in text_extensions):
                    try:
                        self.logger.info(f"נמצא קישור לקובץ: {full_url}")
                        
                        # Попытка скачать файл
                        response = requests.get(full_url, timeout=30, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        response.raise_for_status()
                        
                        # Сохранение файла
                        filename = os.path.basename(urlparse(full_url).path)
                        if not filename:
                            filename = f"file_{int(time.time())}{os.path.splitext(full_url)[1]}"
                        
                        file_path = os.path.join(self.download_dir, filename)
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        
                        self.logger.info(f"קובץ נשמר: {filename}")
                        downloaded_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"שגיאה בטעינת קובץ {full_url}: {e}")
                
                time.sleep(1)  # Задержка между скачиваниями
        
        except Exception as e:
            self.logger.error(f"שגיאה בחיפוש קבצים: {e}")
        
        return downloaded_count
    
    def process_url(self, url, extract_content=True, download_files=True):
        """
        Обработка одного URL
        
        Args:
            url (str): URL для обработки
            extract_content (bool): Извлекать ли текстовое содержимое
            download_files (bool): Скачивать ли файлы
            
        Returns:
            dict: Результаты обработки
        """
        results = {
            'success': False,
            'content_saved': False,
            'files_downloaded': 0,
            'error': None
        }
        
        try:
            # Получение страницы
            soup = self.get_page_with_selenium(url)
            if not soup:
                results['error'] = "לא ניתן לטעון את הדף"
                return results
            
            # Извлечение и сохранение текстового содержимого
            if extract_content:
                text_content = self.extract_text_content(soup, url)
                if text_content:
                    if self.save_content(text_content, url, "content"):
                        results['content_saved'] = True
            
            # Поиск и скачивание файлов
            if download_files:
                files_count = self.find_and_download_files(soup, url)
                results['files_downloaded'] = files_count
            
            results['success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(f"שגיאה בעיבוד URL {url}: {e}")
        
        return results
    
    def run(self, extract_content=True, download_files=True):
        """
        Запуск процесса обработки
        
        Args:
            extract_content (bool): Извлекать ли текстовое содержимое
            download_files (bool): Скачивать ли файлы
        """
        self.logger.info(f"מתחילים עיבוד: {self.base_url}")
        
        try:
            results = self.process_url(
                self.base_url, 
                extract_content=extract_content, 
                download_files=download_files
            )
            
            if results['success']:
                self.logger.info("✅ עיבוד שלם!")
                if results['content_saved']:
                    self.logger.info("📄 תוכן טקסטי נשמר")
                if results['files_downloaded'] > 0:
                    self.logger.info(f"📁 קבצים נשמרים: {results['files_downloaded']}")
                if not results['content_saved'] and results['files_downloaded'] == 0:
                    self.logger.warning("⚠️ לא נמצא תוכן לשמירה")
            else:
                self.logger.error(f"❌ שגיאה בעיבוד: {results.get('error', 'שגיאה לא ידועה')}")
        
        except Exception as e:
            self.logger.error(f"שגיאה קריטית: {e}")
        
        finally:
            self.close()
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver נסגר")
            except Exception as e:
                self.logger.error(f"שגיאה בסגירת WebDriver: {e}")


def main():
    """Основная функция"""
    target_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    print("🌐 SELENIUM טוען טקסט קבצים")
    print("=" * 50)
    print(f"🎯 URL: {target_url}")
    print("⏳ תחילת גיבוי דפדפן...")
    
    try:
        downloader = SeleniumTextDownloader(target_url, headless=True)
        downloader.run(extract_content=True, download_files=True)
        
        print("✅ תהליך שלם!")
        print("📋 בדוק את קובץ הלוג '../logs/selenium_downloader.log' לפרטים מפורטים")
        print("📂 קבצים נשמרים בתיקיית 'downloaded_texts'")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        print("💡 ודא ש-ChromeDriver מותקן וזמין ב-PATH")


if __name__ == "__main__":
    main()
