#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузчик писем из одного конкретного тома
"""

import argparse
from letters_downloader import LettersDownloader


def main():
    parser = argparse.ArgumentParser(description='Скачивание писем из конкретного тома')
    parser.add_argument('--volume', type=str, default='א', 
                       help='Номер тома (א, ב, ג, ד, ה, ו, ז, ח, ט, י, יא, יב, יג, יד, טו, טז, יז, יח, יט, כ, כא, כב, כג)')
    parser.add_argument('--output-dir', default='igrot_kodesh_single', 
                       help='Папка для сохранения (по умолчанию: igrot_kodesh_single)')
    parser.add_argument('--visible', action='store_true',
                       help='Показать браузер при работе')
    
    args = parser.parse_args()
    
    print("📚 מטעין מכתבים מכרך אחד")
    print("=" * 50)
    print(f"📖 כרך: כרך {args.volume}")
    print(f"📂 תיקייה: {args.output_dir}")
    print(f"👁️  גלרה: {'גלובלי' if args.visible else 'מוסתר'}")
    print("=" * 50)
    
    # URL главной страницы
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    try:
        downloader = LettersDownloader(download_dir=args.output_dir, headless=not args.visible)
        
        # Получаем главную страницу
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ לא ניתן לטעון את הדף הראשי")
            return
        
        # Находим все тома
        volume_links = downloader.find_volume_links(soup, start_url)
        
        # Ищем нужный том
        target_volume = None
        for volume_info in volume_links:
            if f'כרך {args.volume}' in volume_info['title']:
                target_volume = volume_info
                break
        
        if not target_volume:
            print(f"❌ כרך 'כרך {args.volume}' לא נמצא")
            print("כרכים זמינים:")
            for vol in volume_links:
                print(f"  - {vol['title']}")
            return
        
        print(f"✅ כרך נמצא: {target_volume['title']}")
        print(f"🔗 כתובת URL: {target_volume['url']}")
        
        # Скачиваем письма из этого тома
        letters_count = downloader.download_letters_from_volume(target_volume)
        
        print(f"\n🎉 סיום! נוראו כתבים: {letters_count}")
        print(f"📂 כתבים נשמרו ב: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")


if __name__ == "__main__":
    main()
