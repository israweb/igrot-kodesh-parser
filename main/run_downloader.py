#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой запускаемый скрипт для текстового загрузчика с настройками
"""

from text_file_downloader import TextFileDownloader
import argparse


def main():
    parser = argparse.ArgumentParser(description='Скачивание текстовых файлов с веб-сайта')
    parser.add_argument('--url', 
                       default='https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm',
                       help='URL для сканирования (по умолчанию: chabad.org статья)')
    parser.add_argument('--output-dir', 
                       default='downloaded_texts',
                       help='Директория для сохранения файлов (по умолчанию: downloaded_texts)')
    parser.add_argument('--max-depth', 
                       type=int, 
                       default=2,
                       help='Максимальная глубина сканирования (по умолчанию: 2)')
    parser.add_argument('--delay', 
                       type=float, 
                       default=1.0,
                       help='Задержка между запросами в секундах (по умолчанию: 1.0)')
    parser.add_argument('--extract-content', 
                       action='store_true',
                       default=True,
                       help='Извлекать текстовое содержимое прямо со страниц (по умолчанию: включено)')
    parser.add_argument('--no-extract-content', 
                       action='store_false',
                       dest='extract_content',
                       help='Отключить извлечение содержимого со страниц')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📄 מטעין קבצי טקסט")
    print("=" * 60)
    print(f"🌐 URL: {args.url}")
    print(f"📁 Директория: {args.output_dir}")
    print(f"🔍 Глубина сканирования: {args.max_depth}")
    print(f"⏱️  Задержка: {args.delay} сек")
    print(f"📄 Извлечение содержимого: {'включено' if args.extract_content else 'отключено'}")
    print("=" * 60)
    
    # Создание экземпляра загрузчика
    downloader = TextFileDownloader(args.url, args.output_dir)
    
    try:
        # Запуск процесса
        downloader.crawl_and_download(max_depth=args.max_depth, delay=args.delay, extract_page_content=args.extract_content)
        print("\n✅ Процесс успешно завершен!")
        print(f"📋 Проверьте лог-файл '../logs/downloader.log' для подробностей")
        print(f"📂 Скачанные файлы находятся в: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Процесс прерван пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
