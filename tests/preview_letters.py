#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Предварительный просмотр доступных томов и писем без скачивания
"""

import sys
import os
sys.path.append('../main')

from letters_downloader import LettersDownloader
import argparse


def preview_volumes_and_letters(max_letters_per_volume=5):
    """Предварительный просмотр томов и писем"""
    
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    print("📚 תצוגה מקדימה של מכתבי אגרות קודש")
    print("=" * 60)
    print("🔍 נסה לגשת לכל הספרים ומכתבי הספרים הזמינים...")
    print("=" * 60)
    
    try:
        downloader = LettersDownloader(download_dir="temp", headless=True)
        
        # קבל את הדף הראשי
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ לא ניתן לטעון את הדף הראשי")
            return
        
        # מצא את כל הספרים
        volume_links = downloader.find_volume_links(soup, start_url)
        
        if not volume_links:
            print("❌ לא נמצאו ספרים")
            return
        
        print(f"📖 נמצאו ספרים: {len(volume_links)}")
        print("=" * 60)
        
        total_letters_found = 0
        
        for i, volume_info in enumerate(volume_links, 1):
            print(f"\n📚 ספר {i}: {volume_info['title']}")
            print(f"🔗 URL: {volume_info['url']}")
            
            # קבל את דף הספר
            volume_soup = downloader.get_page_with_selenium(volume_info['url'])
            if volume_soup:
                # מצא את המכתבים בספר
                letter_links = downloader.find_letter_links(volume_soup, volume_info['url'], volume_info['title'])
                
                if letter_links:
                    print(f"📝 נמצאו מכתבים: {len(letter_links)}")
                    total_letters_found += len(letter_links)
                    
                    # הצג כמה מכתבים ראשונים כדוגמה
                    print("📋 דוגמאות למכתבים:")
                    for j, letter in enumerate(letter_links[:max_letters_per_volume], 1):
                        print(f"   {j}. {letter['title']}")
                        print(f"      URL: {letter['url']}")
                    
                    if len(letter_links) > max_letters_per_volume:
                        print(f"   ... ועוד {len(letter_links) - max_letters_per_volume} מכתבים")
                else:
                    print("📝 לא נמצאו מכתבים")
            else:
                print("❌ לא ניתן לטעון את הספר")
            
            print("-" * 60)
        
        print(f"\n📊 סיכום:")
        print(f"📚 ספרים: {len(volume_links)}")
        print(f"📝 בסך הכל נמצאו מכתבים: {total_letters_found}")
        print(f"⏱️  זמן כולל להורדה: {total_letters_found * 3 // 60} דקות")
        
        downloader.close()
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")


def main():
    parser = argparse.ArgumentParser(description='תצוגה מקדימה של מכתבי אגרות קודש')
    parser.add_argument('--preview-letters', type=int, default=3,
                       help='מספר המכתבים להצגה בכל ספר (ברירה ברירה: 3)')
    
    args = parser.parse_args()
    
    preview_volumes_and_letters(max_letters_per_volume=args.preview_letters)


if __name__ == "__main__":
    main()
