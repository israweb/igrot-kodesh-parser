#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест полноты скачивания писем из тома
Проверяет, что количество найденных писем соответствует ожидаемому количеству
"""

import sys
import os
import re
sys.path.append('../main')

from letters_downloader import LettersDownloader
import time
from bs4 import BeautifulSoup


class VolumeCompletenessTest:
    def __init__(self):
        self.downloader = LettersDownloader(download_dir="test_completeness", headless=True)
        self.hebrew_to_number = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10,
            'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'יז': 17, 'יח': 18, 'יט': 19, 'כ': 20,
            'כא': 21, 'כב': 22, 'כג': 23, 'כד': 24, 'כה': 25, 'כו': 26, 'כז': 27, 'כח': 28, 'כט': 29, 'ל': 30,
            'לא': 31, 'לב': 32, 'לג': 33, 'לד': 34, 'לה': 35, 'לו': 36, 'לז': 37, 'לח': 38, 'לט': 39, 'מ': 40,
            'מא': 41, 'מב': 42, 'מג': 43, 'מד': 44, 'מה': 45, 'מו': 46, 'מז': 47, 'מח': 48, 'מט': 49, 'נ': 50,
            'נא': 51, 'נב': 52, 'נג': 53, 'נד': 54, 'נה': 55, 'נו': 56, 'נז': 57, 'נח': 58, 'נט': 59, 'ס': 60,
            'סא': 61, 'סב': 62, 'סג': 63, 'סד': 64, 'סה': 65, 'סו': 66, 'סז': 67, 'סח': 68, 'סט': 69, 'ע': 70,
            'עא': 71, 'עב': 72, 'עג': 73, 'עד': 74, 'עה': 75, 'עו': 76, 'עז': 77, 'עח': 78, 'עט': 79, 'פ': 80,
            'פא': 81, 'פב': 82, 'פג': 83, 'פד': 84, 'פה': 85, 'פו': 86, 'פז': 87, 'פח': 88, 'פט': 89, 'צ': 90,
            'צא': 91, 'צב': 92, 'צג': 93, 'צד': 94, 'צה': 95, 'צו': 96, 'צז': 97, 'צח': 98, 'צט': 99, 'ק': 100,
            'קא': 101, 'קב': 102, 'קג': 103, 'קד': 104, 'קה': 105, 'קו': 106, 'קז': 107, 'קח': 108, 'קט': 109, 'קי': 110,
            'קיא': 111, 'קיב': 112, 'קיג': 113, 'קיד': 114, 'קטו': 115, 'קטז': 116, 'קיז': 117, 'קיח': 118, 'קיט': 119, 'קכ': 120,
            'קכא': 121, 'קכב': 122, 'קכג': 123, 'קכד': 124, 'קכה': 125, 'קכו': 126, 'קכז': 127, 'קכח': 128, 'קכט': 129, 'קל': 130,
            'קלא': 131, 'קלב': 132, 'קלג': 133, 'קלד': 134, 'קלה': 135, 'קלו': 136, 'קלז': 137, 'קלח': 138, 'קלט': 139, 'קמ': 140,
            'קמא': 141, 'קמב': 142, 'קמג': 143, 'קמד': 144, 'קמה': 145, 'קמו': 146, 'קמז': 147, 'קמח': 148, 'קמט': 149, 'קנ': 150,
            'קנא': 151, 'קנב': 152, 'קנג': 153, 'קנד': 154, 'קנה': 155, 'קנו': 156, 'קנז': 157, 'קנח': 158, 'קנט': 159, 'קס': 160,
            'קסא': 161, 'קסב': 162, 'קסג': 163, 'קסד': 164, 'קסה': 165, 'קסו': 166, 'קסז': 167, 'קסח': 168, 'קסט': 169, 'קע': 170,
            'קעא': 171, 'קעב': 172, 'קעג': 173, 'קעד': 174, 'קעה': 175, 'קעו': 176, 'קעז': 177, 'קעח': 178, 'קעט': 179, 'קפ': 180,
            'קפא': 181, 'קפב': 182, 'קפג': 183, 'קפד': 184, 'קפה': 185, 'קפו': 186, 'קפז': 187, 'קפח': 188, 'קפט': 189, 'קצ': 190,
            'קצא': 191, 'קצב': 192, 'קצג': 193, 'קצד': 194, 'קצה': 195, 'קצו': 196, 'קצז': 197, 'קצח': 198, 'קצט': 199, 'ר': 200,
            'רא': 201, 'רב': 202, 'רג': 203, 'רד': 204, 'רה': 205, 'רו': 206, 'רז': 207, 'רח': 208, 'רט': 209, 'רי': 210
        }

    def hebrew_number_to_int(self, hebrew_num):
        """Конвертация еврейского числа в арабское"""
        if hebrew_num in self.hebrew_to_number:
            return self.hebrew_to_number[hebrew_num]
        
        # Попытка разбора составных чисел
        for key, value in sorted(self.hebrew_to_number.items(), key=lambda x: x[1], reverse=True):
            if hebrew_num.startswith(key):
                remaining = hebrew_num[len(key):]
                if remaining in self.hebrew_to_number:
                    return value + self.hebrew_to_number[remaining]
        
        return None

    def extract_expected_letter_count(self, soup, volume_title):
        """
        Извлечение ожидаемого количества писем из заголовка или описания тома
        """
        print(f"🔍 Поиск ожидаемого количества писем в томе {volume_title}")
        
        # Ищем паттерны с номерами писем в тексте страницы
        text = soup.get_text()
        
        # Паттерн: מכתב + еврейское число
        letter_patterns = re.findall(r'מכתב\s+([א-ת]+)', text)
        
        if letter_patterns:
            max_number = 0
            max_hebrew = ""
            
            for hebrew_num in letter_patterns:
                number = self.hebrew_number_to_int(hebrew_num)
                if number and number > max_number:
                    max_number = number
                    max_hebrew = hebrew_num
            
            if max_number > 0:
                print(f"📊 Найдено максимальное число письма: מכתב {max_hebrew} = {max_number}")
                return max_number
        
        # Альтернативный поиск: числовые паттерны
        number_patterns = re.findall(r'(\d{1,3})\s*(?:letters|писем|מכתבים)', text, re.IGNORECASE)
        if number_patterns:
            numbers = [int(n) for n in number_patterns]
            max_num = max(numbers)
            print(f"📊 Найдено количество из числового паттерна: {max_num}")
            return max_num
        
        print("⚠️ Не удалось определить ожидаемое количество писем")
        return None

    def analyze_pagination_info(self, soup):
        """Анализ информации о пагинации"""
        print("\n📄 Анализ пагинации:")
        
        # Ищем информацию о страницах
        pagination_info = {}
        
        # Поиск элементов пагинации
        pagination_elements = soup.find_all(['div', 'span'], class_=re.compile(r'pag', re.I))
        for elem in pagination_elements:
            text = elem.get_text(strip=True)
            if text and any(char.isdigit() for char in text):
                print(f"   Элемент пагинации: {text}")
        
        # Поиск ссылок на страницы
        page_links = soup.find_all('a', href=re.compile(r'/page/\d+'))
        if page_links:
            page_numbers = []
            for link in page_links:
                match = re.search(r'/page/(\d+)', link['href'])
                if match:
                    page_numbers.append(int(match.group(1)))
            
            if page_numbers:
                max_page = max(page_numbers)
                print(f"   📑 Найдены ссылки на страницы до: {max_page}")
                pagination_info['max_page'] = max_page
        
        # Поиск информации "X из Y"
        pattern_info = re.findall(r'(\d+)\s*(?:из|of|from)\s*(\d+)', soup.get_text())
        if pattern_info:
            for current, total in pattern_info:
                print(f"   📊 Найдено: {current} из {total}")
                pagination_info['items_per_page'] = int(total)
        
        return pagination_info

    def test_volume_completeness(self, volume_title="כרך א", expected_count=None):
        """
        Тестирование полноты парсинга тома
        
        Args:
            volume_title (str): Название тома для тестирования
            expected_count (int): Ожидаемое количество писем (если известно)
        """
        print("🧪 ТЕСТ ПОЛНОТЫ ПАРСИНГА ТОМА")
        print("=" * 60)
        print(f"📖 Тестируемый том: {volume_title}")
        
        if expected_count:
            print(f"📊 Ожидаемое количество писем: {expected_count}")
        
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        
        try:
            # Получаем главную страницу
            print("\n🔍 Загрузка главной страницы...")
            soup = self.downloader.get_page_with_selenium(start_url)
            if not soup:
                print("❌ Не удалось загрузить главную страницу")
                return False
            
            # Находим тома
            print("📚 Поиск томов...")
            volume_links = self.downloader.find_volume_links(soup, start_url)
            
            # Ищем нужный том
            target_volume = None
            for volume_info in volume_links:
                if volume_title in volume_info['title']:
                    target_volume = volume_info
                    break
            
            if not target_volume:
                print(f"❌ Том '{volume_title}' не найден")
                return False
            
            print(f"✅ Найден том: {target_volume['title']}")
            print(f"🔗 URL: {target_volume['url']}")
            
            # Получаем страницу тома
            print("\n📄 Загрузка страницы тома...")
            volume_soup = self.downloader.get_page_with_selenium(target_volume['url'])
            if not volume_soup:
                print("❌ Не удалось загрузить страницу тома")
                return False
            
            # Определяем ожидаемое количество писем
            if not expected_count:
                expected_count = self.extract_expected_letter_count(volume_soup, volume_title)
            
            # Анализируем пагинацию
            pagination_info = self.analyze_pagination_info(volume_soup)
            
            # Запускаем парсинг всех писем
            print(f"\n📝 Начинаем парсинг всех писем из тома...")
            print("=" * 60)
            
            start_time = time.time()
            letter_links = self.downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
            end_time = time.time()
            
            # Результаты
            print(f"\n📊 РЕЗУЛЬТАТЫ ПАРСИНГА:")
            print("=" * 60)
            print(f"⏱️  Время парсинга: {end_time - start_time:.2f} секунд")
            print(f"📝 Найдено писем: {len(letter_links)}")
            
            if expected_count:
                print(f"🎯 Ожидалось писем: {expected_count}")
                difference = len(letter_links) - expected_count
                
                if difference == 0:
                    print("✅ ПОЛНОЕ СООТВЕТСТВИЕ! Найдено ровно столько писем, сколько ожидалось")
                    success = True
                elif difference > 0:
                    print(f"⚠️  НАЙДЕНО БОЛЬШЕ: +{difference} писем от ожидаемого")
                    print("   Возможно, парсер находит дубликаты или неправильные ссылки")
                    success = False
                else:
                    print(f"❌ НАЙДЕНО МЕНЬШЕ: {difference} писем от ожидаемого")
                    print("   Возможно, парсер пропускает некоторые страницы или письма")
                    success = False
            else:
                print("⚠️  Ожидаемое количество не определено, проверка на корректность невозможна")
                success = len(letter_links) > 0
            
            # Анализ найденных писем
            if letter_links:
                print(f"\n📋 АНАЛИЗ НАЙДЕННЫХ ПИСЕМ:")
                print("-" * 40)
                
                # Группировка по страницам
                pages = {}
                for letter in letter_links:
                    page = letter.get('page', 1)
                    if page not in pages:
                        pages[page] = []
                    pages[page].append(letter)
                
                print(f"📄 Обработано страниц: {len(pages)}")
                for page_num in sorted(pages.keys()):
                    count = len(pages[page_num])
                    print(f"   Страница {page_num}: {count} писем")
                
                # Примеры найденных писем
                print(f"\n📝 Примеры найденных писем:")
                for i, letter in enumerate(letter_links[:10], 1):
                    print(f"   {i}. {letter['title']}")
                    print(f"      URL: {letter['url']}")
                
                if len(letter_links) > 10:
                    print(f"   ... и еще {len(letter_links) - 10} писем")
                
                # Проверка на дубликаты
                unique_urls = set(letter['url'] for letter in letter_links)
                if len(unique_urls) != len(letter_links):
                    duplicates = len(letter_links) - len(unique_urls)
                    print(f"⚠️  Найдено дубликатов: {duplicates}")
                else:
                    print("✅ Дубликаты не найдены")
            
            # Рекомендации
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print("-" * 40)
            
            if expected_count and len(letter_links) != expected_count:
                if len(letter_links) < expected_count:
                    print("🔧 Для исправления недостающих писем:")
                    print("   - Проверьте обход всех страниц тома")
                    print("   - Улучшите алгоритм поиска ссылок на письма")
                    print("   - Проверьте селекторы для поиска писем")
                elif len(letter_links) > expected_count:
                    print("🔧 Для исправления лишних писем:")
                    print("   - Добавьте фильтрацию нерелевантных ссылок")
                    print("   - Улучшите детекцию дубликатов")
                    print("   - Проверьте логику исключения навигационных ссылок")
            else:
                print("🎉 Парсер работает корректно!")
            
            return success
            
        except Exception as e:
            print(f"❌ Ошибка во время теста: {e}")
            return False
        finally:
            self.downloader.close()

    def run_comprehensive_test(self):
        """Запуск комплексного теста"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТА ПАРСЕРА")
        print("=" * 70)
        
        # Тестируем первый том (известно, что там 169 писем)
        print("\n📖 Тест 1: Том א (ожидается 169 писем)")
        success1 = self.test_volume_completeness("כרך א", expected_count=169)
        
        # Можно добавить тесты других томов
        # print("\n📖 Тест 2: Том ב")
        # success2 = self.test_volume_completeness("כרך ב")
        
        print(f"\n🏁 ИТОГИ ТЕСТИРОВАНИЯ:")
        print("=" * 70)
        print(f"📖 Том א: {'✅ ПРОЙДЕН' if success1 else '❌ ПРОВАЛЕН'}")
        
        if success1:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Парсер работает корректно.")
        else:
            print("\n⚠️  ЕСТЬ ПРОБЛЕМЫ. Парсер требует доработки.")
        
        return success1


def main():
    """Основная функция"""
    print("🧪 ТЕСТ ПОЛНОТЫ ПАРСИНГА ПИСЕМ")
    print("=" * 70)
    print("🎯 Цель: Проверить, что парсер находит все письма в томе")
    print("📊 Метод: Сравнение найденного и ожидаемого количества")
    print("=" * 70)
    
    test = VolumeCompletenessTest()
    
    try:
        success = test.run_comprehensive_test()
        
        if success:
            print("\n✅ Тест завершен успешно!")
            exit(0)
        else:
            print("\n❌ Тест выявил проблемы!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        exit(2)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        exit(3)


if __name__ == "__main__":
    main()
