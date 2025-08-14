#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор отчетов с таблицей писем и ссылок
"""

import sys
import os
import csv
import json
import re
from datetime import datetime
sys.path.append('../main')

from letters_downloader import LettersDownloader
import argparse


class LettersReportGenerator:
    def __init__(self):
        self.downloader = LettersDownloader(download_dir="temp_report", headless=True)
        
    def extract_letter_number_from_title(self, title):
        """Извлечение номера письма из названия"""
        # Ищем паттерн "מכתב X" где X - номер
        match = re.search(r'מכתב\s+([א-ת]+|\d+)', title)
        if match:
            return match.group(1)
        
        # Альтернативные паттерны
        match = re.search(r'(\d+)', title)
        if match:
            return match.group(1)
            
        return "?"
    
    def format_letter_title(self, volume_title, original_title):
        """Формирование названия письма в новом формате"""
        # Извлекаем том (כרך X)
        volume_match = re.search(r'(כרך\s+[א-ת]+)', volume_title)
        volume_part = volume_match.group(1) if volume_match else "כרך א"
        
        # Извлекаем номер письма (מכתב X)
        letter_match = re.search(r'(מכתב\s+[א-ת]+)', original_title)
        letter_part = letter_match.group(1) if letter_match else "מכתב א"
        
        # Формат: אגרות קודש - כרך א - מכתב פד
        return f"אגרות קודש - {volume_part} - {letter_part}"
    
    def generate_volume_report(self, volume_title="כרך א", output_format="csv"):
        """
        Генерация отчета для одного тома
        
        Args:
            volume_title (str): Название тома
            output_format (str): Формат вывода (csv, json, html)
        """
        print(f"📊 גילוי דוח לטובת טובה {volume_title}")
        print("=" * 60)
        
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        
        try:
            # Получаем главную страницу
            print("🔍 טעינת דף הראשי...")
            soup = self.downloader.get_page_with_selenium(start_url)
            if not soup:
                print("❌ לא ניתן לטעון את דף הראשי")
                return None
            
            # Находим тома
            volume_links = self.downloader.find_volume_links(soup, start_url)
            
            # Ищем нужный том
            target_volume = None
            for volume_info in volume_links:
                if volume_title in volume_info['title']:
                    target_volume = volume_info
                    break
            
            if not target_volume:
                print(f"❌ הטובה '{volume_title}' לא נמצאה")
                return None
            
            print(f"✅ טובה נמצאה: {target_volume['title']}")
            
            # Получаем страницу тома
            print("📄 טעינת דף הטובה...")
            volume_soup = self.downloader.get_page_with_selenium(target_volume['url'])
            if not volume_soup:
                print("❌ לא ניתן לטעון את דף הטובה")
                return None
            
            # Находим все письма
            print("📝 חיפוש כל המכתבים...")
            letter_links = self.downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
            
            if not letter_links:
                print("❌ לא נמצאו מכתבים")
                return None
                
            print(f"📝 מכתבים נמצאו: {len(letter_links)}")
            
            # Подготавливаем данные для отчета
            report_data = []
            for i, letter in enumerate(letter_links, 1):
                letter_number = self.extract_letter_number_from_title(letter['title'])
                formatted_title = self.format_letter_title(target_volume['title'], letter['title'])
                
                row = {
                    'sequence_number': i,  # Порядковый номер
                    'volume': target_volume['title'],  # Полный том
                    'letter_number': letter_number,  # Номер письма
                    'title': formatted_title,  # Название в новом формате
                    'original_title': letter['title'],  # Оригинальное название
                    'url': letter['url'],  # Ссылка
                    'page': letter.get('page', 1)  # Страница в томе
                }
                report_data.append(row)
            
            # Генерируем отчет в нужном формате
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            volume_safe = re.sub(r'[<>:"/\\|?*]', '_', volume_title)
            
            if output_format.lower() == 'csv':
                return self.generate_csv_report(report_data, f"letters_report_{volume_safe}_{timestamp}.csv")
            elif output_format.lower() == 'json':
                return self.generate_json_report(report_data, f"letters_report_{volume_safe}_{timestamp}.json")
            elif output_format.lower() == 'html':
                return self.generate_html_report(report_data, f"letters_report_{volume_safe}_{timestamp}.html")
            else:
                print(f"❌ פורמט לא תמיד: {output_format}")
                return None
                
        except Exception as e:
            print(f"❌ שגיאה: {e}")
            return None
        finally:
            self.downloader.close()
    
    def generate_csv_report(self, data, filename):
        """Генерация CSV отчета"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['sequence_number', 'volume', 'letter_number', 'title', 'url', 'page']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Заголовки
                writer.writerow({
                    'sequence_number': '№ פ/פ',
                    'volume': 'טובה',
                    'letter_number': 'מספר מכתב', 
                    'title': 'שם מכתב',
                    'url': 'קישור',
                    'page': 'דף'
                })
                
                # Данные (только нужные поля)
                for row in data:
                    writer.writerow({
                        'sequence_number': row['sequence_number'],
                        'volume': row['volume'],
                        'letter_number': row['letter_number'],
                        'title': row['title'],  # Уже отформатированное название
                        'url': row['url'],
                        'page': row['page']
                    })
            
            print(f"✅ דוח CSV נשמר: {filepath}")
            print(f"📊 רשומות: {len(data)}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת CSV: {e}")
            return None
    
    def generate_json_report(self, data, filename):
        """Генерация JSON отчета"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_letters': len(data),
                'volume': data[0]['volume'] if data else '',
                'letters': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(report, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"✅ דוח JSON נשמר: {filepath}")
            print(f"📊 רשומות: {len(data)}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת JSON: {e}")
            return None
    
    def generate_html_report(self, data, filename):
        """Генерация HTML отчета"""
        try:
            os.makedirs('reports', exist_ok=True)
            filepath = os.path.join('reports', filename)
            
            volume_name = data[0]['volume'] if data else 'טובה לא ידועה'
            
            html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דוח מכתבי אגרות קודש - {volume_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: right;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #e8f4f8;
        }}
        .letter-link {{
            color: #2980b9;
            text-decoration: none;
        }}
        .letter-link:hover {{
            text-decoration: underline;
        }}
        .letter-number {{
            font-weight: bold;
            color: #8e44ad;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 דוח מכתבי אגרות קודש</h1>
        
        <div class="summary">
            <h3>📊 סיכום:</h3>
            <p><strong>טובה:</strong> {volume_name}</p>
            <p><strong>כל המכתבים:</strong> {len(data)}</p>
            <p><strong>תאריך יצירה:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>№ פ/פ</th>
                    <th>טובה</th>
                    <th>מספר מכתב</th>
                    <th>שם</th>
                    <th>קישור</th>
                    <th>דף</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for row in data:
                html_content += f"""
                <tr>
                    <td>{row['sequence_number']}</td>
                    <td>{row['volume']}</td>
                    <td class="letter-number">{row['letter_number']}</td>
                    <td>{row['title']}</td>
                    <td><a href="{row['url']}" class="letter-link" target="_blank">פתוח מכתב</a></td>
                    <td>{row['page']}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>דוח יוצר על ידי מערכת הורדת מכתבי אגרות קודש</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            print(f"✅ דוח HTML נשמר: {filepath}")
            print(f"📊 רשומות: {len(data)}")
            return filepath
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת HTML: {e}")
            return None
    
    def generate_multiple_volumes_report(self, volumes=None, output_format="csv"):
        """Генерация отчета для нескольких томов"""
        if volumes is None:
            volumes = ["כרך א", "כרך ב", "כרך ג"]  # По умолчанию первые 3 тома
        
        print(f"📊 גילוי דוח לטובה {len(volumes)} טובות")
        print("=" * 60)
        
        all_data = []
        
        for volume in volumes:
            print(f"\n📖 עיבוד טובה: {volume}")
            
            # Генерируем отчет для тома (но не сохраняем файл)
            volume_data = self.generate_volume_data(volume)
            if volume_data:
                all_data.extend(volume_data)
                print(f"✅ טובה {volume}: {len(volume_data)} מכתבים")
            else:
                print(f"❌ טובה {volume}: שגיאה")
        
        if all_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format.lower() == 'csv':
                return self.generate_csv_report(all_data, f"letters_report_multiple_volumes_{timestamp}.csv")
            elif output_format.lower() == 'json':
                return self.generate_json_report(all_data, f"letters_report_multiple_volumes_{timestamp}.json")
            elif output_format.lower() == 'html':
                return self.generate_html_report(all_data, f"letters_report_multiple_volumes_{timestamp}.html")
        
        return None
    
    def generate_volume_data(self, volume_title):
        """Получение данных для одного тома (без сохранения файла)"""
        start_url = "https://www.chabad.org/therebbe/article_cdo/aid/4643797/jewish/page.htm"
        
        try:
            # Получаем главную страницу
            soup = self.downloader.get_page_with_selenium(start_url)
            if not soup:
                return None
            
            # Находим тома
            volume_links = self.downloader.find_volume_links(soup, start_url)
            
            # Ищем нужный том
            target_volume = None
            for volume_info in volume_links:
                if volume_title in volume_info['title']:
                    target_volume = volume_info
                    break
            
            if not target_volume:
                return None
            
            # Получаем страницу тома
            volume_soup = self.downloader.get_page_with_selenium(target_volume['url'])
            if not volume_soup:
                return None
            
            # Находим все письма
            letter_links = self.downloader.find_letter_links(volume_soup, target_volume['url'], target_volume['title'])
            
            if not letter_links:
                return None
            
            # Подготавливаем данные
            report_data = []
            for i, letter in enumerate(letter_links, 1):
                letter_number = self.extract_letter_number_from_title(letter['title'])
                formatted_title = self.format_letter_title(target_volume['title'], letter['title'])
                
                row = {
                    'sequence_number': i,
                    'volume': target_volume['title'],
                    'letter_number': letter_number,
                    'title': formatted_title,
                    'original_title': letter['title'],
                    'url': letter['url'],
                    'page': letter.get('page', 1)
                }
                report_data.append(row)
            
            return report_data
            
        except Exception as e:
            print(f"❌ שגיאה בעיבוד טובה {volume_title}: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Генерация отчетов с таблицей писем')
    parser.add_argument('--volume', default='א', help='טובה לדוח (א, ב, ג...)')
    parser.add_argument('--format', choices=['csv', 'json', 'html'], default='csv', 
                       help='פורמט דוח (csv, json, html)')
    parser.add_argument('--multiple', action='store_true', 
                       help='גילוי דוח לטובות רבות')
    parser.add_argument('--volumes', nargs='+', 
                       help='רשימת טובות לדוח רב-טובות')
    
    args = parser.parse_args()
    
    print("📊 מחולל דוחות מכתבי אגרות קודש")
    print("=" * 60)
    
    generator = LettersReportGenerator()
    
    try:
        if args.multiple:
            volumes = args.volumes or ["כרך א", "כרך ב", "כרך ג"]
            volumes = [f"כרך {v}" if not v.startswith("כרך") else v for v in volumes]
            
            print(f"📚 גילוי דוח לטובות: {', '.join(volumes)}")
            print(f"📄 פורמט: {args.format.upper()}")
            
            result = generator.generate_multiple_volumes_report(volumes, args.format)
        else:
            volume = f"כרך {args.volume}" if not args.volume.startswith("כרך") else args.volume
            
            print(f"📖 גילוי דוח לטובה: {volume}")
            print(f"📄 פורמט: {args.format.upper()}")
            
            result = generator.generate_volume_report(volume, args.format)
        
        if result:
            print(f"\n🎉 דוח נוצר בהצלחה!")
            print(f"📁 קובץ: {result}")
            print(f"📂 תיקייה: reports/")
            
            if args.format == 'html':
                print(f"🌐 פתחו את הקובץ בדפדפן לצפייה")
        else:
            print("\n❌ לא ניתן ליצור דוח")
            
    except Exception as e:
        print(f"❌ שגיאה קריטית: {e}")


if __name__ == "__main__":
    main()
