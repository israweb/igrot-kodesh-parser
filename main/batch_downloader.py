#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пакетный загрузчик для нескольких URL с chabad.org
"""

from selenium_downloader import SeleniumTextDownloader
import time


def download_multiple_pages():
    """Скачивание нескольких страниц"""
    
    # Список URL для скачивания
    urls = [
        "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm",
        # Добавьте другие URL здесь:
        # "https://www.chabad.org/другая_страница",
        # "https://www.chabad.org/еще_одна_страница",
    ]
    
    print(f"🚀 הורדה אצווה של {len(urls)} דפים")
    print("=" * 50)
    
    for i, url in enumerate(urls, 1):
        print(f"\n📄 טיפול {i}/{len(urls)}: {url}")
        
        try:
            downloader = SeleniumTextDownloader(url, "downloaded_texts", headless=True)
            results = downloader.process_url(url, extract_content=True, download_files=True)
            
            if results['success']:
                print(f"✅ דף {i} טיפול בהצלחה")
                if results['content_saved']:
                    print("📝 תוכן שמור")
                if results['files_downloaded'] > 0:
                    print(f"📁 קבצים שורדים: {results['files_downloaded']}")
            else:
                print(f"❌ שגיאה: {results.get('error', 'שגיאה לא ידועה')}")
                
            downloader.close()
            
            # תפריט בין דפים
            if i < len(urls):
                print("⏳ המתן 5 שניות...")
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ שגיאה קריטית: {e}")
    
    print("\n🎉 הורדה אצווה שלם!")
    print("📂 בדוק את התיקייה 'downloaded_texts'")


if __name__ == "__main__":
    download_multiple_pages()
