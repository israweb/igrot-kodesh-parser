#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки загрузчика на доступном сайте
"""

import sys
import os
sys.path.append('../main')

from text_file_downloader import TextFileDownloader
import time


def test_basic_functionality():
    """Тест базового функционала на простом сайте"""
    
    # Используем httpbin.org для тестирования (не блокирует ботов)
    test_url = "https://httpbin.org/html"
    
    print("🧪 בדיקת מטעין")
    print("=" * 40)
    print(f"🎯 Тестовый URL: {test_url}")
    print("📂 Директория: test_downloads")
    
    try:
        # Создаем тестовый загрузчик
        downloader = TextFileDownloader(test_url, "test_downloads")
        
        print("⏳ Запуск тестирования...")
        start_time = time.time()
        
        # Запускаем с минимальными параметрами
        downloader.crawl_and_download(
            max_depth=1, 
            delay=0.5, 
            extract_page_content=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Тест завершен за {duration:.2f} секунд")
        print("📋 Проверьте папку 'test_downloads' и лог '../logs/downloader.log'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False


def test_with_alternative_url():
    """Тест с альтернативным сайтом"""
    
    # Попробуем example.com - простая страница
    test_url = "http://example.com"
    
    print("\n🧪 בדיקת מטעין עם EXAMPLE.COM")
    print("=" * 40)
    print(f"🎯 URL: {test_url}")
    
    try:
        downloader = TextFileDownloader(test_url, "test_downloads")
        downloader.crawl_and_download(
            max_depth=1, 
            delay=0.5, 
            extract_page_content=True
        )
        
        print("✅ Тест с example.com завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    print("🚀 ЗАПУСК ТЕСТОВ ЗАГРУЗЧИКА")
    print("=" * 50)
    
    # Тест 1: Базовый функционал
    success1 = test_basic_functionality()
    
    # Тест 2: Альтернативный сайт
    success2 = test_with_alternative_url()
    
    # Итоги
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 50)
    print(f"✅ Тест httpbin.org: {'ПРОЙДЕН' if success1 else 'ПРОВАЛЕН'}")
    print(f"✅ Тест example.com: {'ПРОЙДЕН' if success2 else 'ПРОВАЛЕН'}")
    
    if success1 or success2:
        print("\n🎉 Загрузчик работает! Теперь можно использовать его на других сайтах.")
        print("\n💡 Для использования на chabad.org попробуйте:")
        print("   - Использовать selenium_downloader.py (если установлен ChromeDriver)")
        print("   - Связаться с администрацией сайта для получения разрешения")
        print("   - Попробовать VPN или другой IP-адрес")
    else:
        print("\n⚠️ Все тесты провалены. Проверьте интернет-соединение.")


if __name__ == "__main__":
    main()
