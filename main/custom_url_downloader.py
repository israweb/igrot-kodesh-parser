#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик с возможностью задания URL через командную строку
"""

import argparse
from selenium_downloader import SeleniumTextDownloader


def main():
    parser = argparse.ArgumentParser(description='Скачивание текста с любого URL')
    parser.add_argument('url', help='URL для скачивания')
    parser.add_argument('--output-dir', default='downloaded_texts', 
                       help='Папка для сохранения (по умолчанию: downloaded_texts)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Запуск браузера в скрытом режиме (по умолчанию)')
    parser.add_argument('--visible', action='store_false', dest='headless',
                       help='Показать браузер при работе')
    
    args = parser.parse_args()
    
    print("🌐 מטעין עם URL מותאם")
    print("=" * 50)
    print(f"🎯 URL: {args.url}")
    print(f"📂 Папка: {args.output_dir}")
    print(f"👁️  Режим браузера: {'скрытый' if args.headless else 'видимый'}")
    print("=" * 50)
    
    try:
        downloader = SeleniumTextDownloader(args.url, args.output_dir, args.headless)
        downloader.run(extract_content=True, download_files=True)
        
        print("\n✅ Готово! Проверьте папку с результатами.")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
