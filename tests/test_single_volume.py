#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест скачивания одного тома с улучшенным алгоритмом
"""

import sys
import os
sys.path.append('../main')

from letters_downloader import LettersDownloader


def test_single_volume():
    """Тестируем том א с подробным логированием"""
    
    print("🧪 בדיקת הורדת כרך אחד")
    print("=" * 50)
    print("📖 Тестируем улучшенный алгоритм поиска писем")
    
    # URL главной страницы
    start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
    
    try:
        downloader = LettersDownloader(download_dir="test_volume_aleph", headless=True)
        
        # Получаем главную страницу
        print("🔍 Загружаем главную страницу...")
        soup = downloader.get_page_with_selenium(start_url)
        if not soup:
            print("❌ Не удалось загрузить главную страницу")
            return
        
        # Находим все тома
        print("📚 Ищем тома...")
        volume_links = downloader.find_volume_links(soup, start_url)
        
        # Ищем том א
        target_volume = None
        for volume_info in volume_links:
            if 'כרך א' in volume_info['title']:
                target_volume = volume_info
                break
        
        if not target_volume:
            print("❌ Том א не найден")
            return
        
        print(f"✅ Найден том: {target_volume['title']}")
        print(f"🔗 URL: {target_volume['url']}")
        
        # Скачиваем письма из этого тома (только первые 3 для теста)
        print("\n📝 Начинаем поиск писем в томе...")
        
        # Получаем страницу тома
        volume_soup = downloader.get_page_with_selenium(target_volume['url'])
        if not volume_soup:
            print("❌ Не удалось загрузить страницу тома")
            return
        
        # Находим письма в томе
        letter_links = downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ПОИСКА:")
        print(f"📝 Найдено писем: {len(letter_links)}")
        
        if letter_links:
            print("\n📋 Список найденных писем:")
            for i, letter in enumerate(letter_links[:10], 1):  # Показываем первые 10
                print(f"   {i}. {letter['title']}")
                print(f"      URL: {letter['url']}")
            
            if len(letter_links) > 10:
                print(f"   ... и еще {len(letter_links) - 10} писем")
            
            # Скачиваем первые 3 письма для теста
            print(f"\n⬇️ Скачиваем первые 3 письма для проверки...")
            
            downloaded_count = 0
            for i, letter_info in enumerate(letter_links[:3], 1):
                print(f"\n📄 Обработка письма {i}/3: {letter_info['title'][:50]}...")
                
                # Получаем содержимое письма
                letter_soup = downloader.get_page_with_selenium(letter_info['url'])
                if letter_soup:
                    content = downloader.extract_letter_content(letter_soup, letter_info['url'])
                    if content:
                        if downloader.save_letter(content, letter_info):
                            downloaded_count += 1
                            print(f"✅ Письмо сохранено ({len(content)} символов)")
                        else:
                            print("❌ Ошибка при сохранении")
                    else:
                        print("⚠️ Не удалось извлечь содержимое")
                else:
                    print("❌ Не удалось загрузить страницу письма")
            
            print(f"\n🎉 ИТОГ ТЕСТА:")
            print(f"📝 Найдено писем: {len(letter_links)}")
            print(f"💾 Скачано тестовых писем: {downloaded_count}/3")
            print(f"📂 Письма сохранены в: test_volume_aleph/")
            
        else:
            print("❌ Письма в томе не найдены")
            print("🔍 Проверьте debug файлы для анализа структуры страницы")
        
        downloader.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    test_single_volume()
