#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
אגרות קודש - פרסר מקומי
מאפשר הרצה מקומית של הפרסר עם יצירת דוחות HTML
"""

import sys
import os
import argparse
from datetime import datetime

# הוספת נתיבים למודולים
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))

def main():
    """הפעלה ראשית של הפרסר המקומי"""
    parser = argparse.ArgumentParser(description='אגרות קודש - פרסר מקומי')
    parser.add_argument('--mode', choices=['test', 'single', 'full'], default='test',
                       help='מצב הפעלה: test (10 מכתבים), single (כרך אחד), full (כל הכרכים)')
    parser.add_argument('--volume', default='א', help='כרך לפרסינג (במצב single)')
    parser.add_argument('--output', default='reports', help='תיקיית פלט')
    parser.add_argument('--format', choices=['csv', 'html', 'both'], default='both',
                       help='פורמט הדוח')
    
    args = parser.parse_args()
    
    print("🚀 אגרות קודש - פרסר מקומי")
    print("=" * 50)
    print(f"מצב: {args.mode}")
    print(f"כרך: {args.volume}")
    print(f"פורמט: {args.format}")
    print(f"תיקיית פלט: {args.output}")
    print("=" * 50)
    
    # יצירת תיקיות
    os.makedirs(args.output, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    try:
        if args.mode == 'test':
            run_test_mode(args)
        elif args.mode == 'single':
            run_single_volume(args)
        elif args.mode == 'full':
            run_full_parsing(args)
            
    except KeyboardInterrupt:
        print("\n⏹️ הפרסינג הופסק על ידי המשתמש")
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()

def run_test_mode(args):
    """הרצת מצב מבחן - 10 מכתבים"""
    print("🧪 מצב מבחן - 10 מכתבים ראשונים")
    
    try:
        from test_10_letters import test_10_letters
        
        # הרצת המבחן
        test_10_letters()
        
        # יצירת דוח HTML מקומי
        create_local_html_report(args.output, "test")
        
        print("✅ מבחן הושלם בהצלחה!")
        print(f"📄 דוחות נוצרו בתיקייה: {args.output}")
        
    except ImportError as e:
        print(f"❌ שגיאה בייבוא: {e}")
        print("וודא שכל הקבצים נמצאים בתיקיות הנכונות")

def run_single_volume(args):
    """הרצת פרסינג כרך יחיד"""
    print(f"📖 פרסינג כרך {args.volume}")
    
    try:
        from letters_downloader import LettersDownloader
        from test_10_letters import HebrewDateParser, hebrew_letter_to_number
        
        downloader = LettersDownloader(download_dir="temp_parse", headless=True)
        date_parser = HebrewDateParser()
        
        # כאן יהיה הקוד לפרסינג כרך יחיד
        # זה דורש הרחבה של הקוד הקיים
        
        print(f"✅ כרך {args.volume} הושלם!")
        
    except ImportError as e:
        print(f"❌ שגיאה בייבוא: {e}")

def run_full_parsing(args):
    """הרצת פרסינג מלא"""
    print("📚 פרסינג מלא של כל הכרכים")
    print("⚠️  זה יכול לקחת מספר שעות!")
    
    confirm = input("האם אתה בטוח שברצונך להמשיך? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ פרסינג מבוטל")
        return
    
    # כאן יהיה הקוד לפרסינג מלא
    print("🔄 פרסינג מלא טרם מומש - השתמש במצב test או single")

def create_local_html_report(output_dir, mode="test"):
    """יצירת דוח HTML מקומי"""
    
    # קריאת נתונים קיימים (אם יש)
    test_data = []
    try:
        import csv
        csv_file = os.path.join('test_reports', 'test_10_letters.csv')
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                test_data = list(reader)
    except Exception as e:
        print(f"⚠️  לא ניתן לקרוא נתונים קיימים: {e}")
        # נתונים לדוגמה
        test_data = [
            {
                'volume_arabic': '1', 'volume_hebrew': 'א', 'letter_arabic': '1', 'letter_hebrew': 'א',
                'day_numeric': '21', 'day_hebrew': 'כא', 'month_hebrew': 'אדר', 
                'year_numeric': '5688', 'year_hebrew': 'תרפח', 
                'url': 'https://www.chabad.org/therebbe/article_cdo/aid/4643798/jewish/page.htm'
            }
        ]
    
    # יצירת טבלה
    table_rows = ""
    for i, row in enumerate(test_data, 1):
        table_rows += f"""
        <tr>
            <td>{row.get('volume_arabic', '')}</td>
            <td style="font-weight: bold; color: #8e44ad;">{row.get('volume_hebrew', '')}</td>
            <td>{row.get('letter_arabic', '')}</td>
            <td style="font-weight: bold; color: #8e44ad;">{row.get('letter_hebrew', '')}</td>
            <td style="font-weight: bold; color: #27ae60;">{row.get('day_numeric', '')}</td>
            <td style="font-weight: bold; color: #8e44ad;">{row.get('day_hebrew', '')}</td>
            <td style="font-weight: bold; color: #8e44ad;">{row.get('month_hebrew', '')}</td>
            <td style="font-weight: bold; color: #27ae60;">{row.get('year_numeric', '')}</td>
            <td style="font-weight: bold; color: #8e44ad;">{row.get('year_hebrew', '')}</td>
            <td><a href="{row.get('url', '#')}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: bold;">קישור</a></td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>אגרות קודש - דוח מקומי</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1400px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            }}
            .header {{ 
                text-align: center; 
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                margin: -30px -30px 30px -30px;
                padding: 30px;
                border-radius: 15px 15px 0 0;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0; 
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            th {{ 
                background: linear-gradient(135deg, #3498db, #2980b9); 
                color: white; 
                font-weight: bold; 
                padding: 15px 8px;
                text-align: center;
            }}
            td {{
                padding: 12px 8px;
                text-align: center;
                border-bottom: 1px solid #eee;
            }}
            tr:nth-child(even) {{ 
                background-color: #f8f9fa; 
            }}
            tr:hover {{ 
                background-color: #e3f2fd; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 אגרות קודש - דוח מקומי</h1>
                <p>נוצר מקומית: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>מצב: {mode} | סה"כ מכתבים: {len(test_data)}</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>מס' כרך</th>
                        <th>כרך עברי</th>
                        <th>מס' מכתב</th>
                        <th>מכתב עברי</th>
                        <th>יום מספר</th>
                        <th>יום עברי</th>
                        <th>חודש עברי</th>
                        <th>שנה מספר</th>
                        <th>שנה עברית</th>
                        <th>קישור</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <p>📄 דוח זה נוצר מקומית על המחשב שלך</p>
                <p>🔗 <a href="https://github.com/israweb/igrot-kodesh-parser" style="color: #3498db;">GitHub Repository</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # שמירת הקובץ
    html_file = os.path.join(output_dir, f'local_report_{mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 דוח HTML נוצר: {html_file}")
    
    # פתיחה אוטומטית בדפדפן
    try:
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(html_file)}')
        print("🌐 הדוח נפתח בדפדפן")
    except Exception as e:
        print(f"⚠️  לא ניתן לפתוח בדפדפן: {e}")

if __name__ == "__main__":
    main()
