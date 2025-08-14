#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
יצירת דוחות בדיקה עם תאריכים מדומים
"""

import csv
import json
from datetime import datetime


def create_test_data():
    """יצירת נתוני בדיקה מדומים"""
    
    # נתונים מדומים המבוססים על הדוגמאות שלנו
    test_data = [
        {
            'volume_arabic': 1,
            'volume_hebrew': 'א',
            'letter_arabic': 21,
            'letter_hebrew': 'כ"א',
            'day': 21,
            'day_hebrew': 'כ"א',
            'month': 6,
            'month_hebrew': 'אדר',
            'year': 5688,
            'year_hebrew': 'פ"ח',
            'full_date_hebrew': 'כ"א אדר פ"ח',
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/example1/jewish/Letter1.htm'
        },
        {
            'volume_arabic': 1,
            'volume_hebrew': 'א',
            'letter_arabic': 28,
            'letter_hebrew': 'כח',
            'day': 28,
            'day_hebrew': 'כח',
            'month': 4,
            'month_hebrew': 'טבת',
            'year': 5689,
            'year_hebrew': 'תרפ"ט',
            'full_date_hebrew': 'כח טבת תרפ"ט',
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/example2/jewish/Letter2.htm'
        },
        {
            'volume_arabic': 1,
            'volume_hebrew': 'א',
            'letter_arabic': 35,
            'letter_hebrew': 'לה',
            'day': 21,
            'day_hebrew': 'כ"א',
            'month': 6,
            'month_hebrew': 'אד"ר',
            'year': 5692,
            'year_hebrew': 'תרצ"ב',
            'full_date_hebrew': 'כ"א אד"ר תרצ"ב',
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/example3/jewish/Letter3.htm'
        },
        {
            'volume_arabic': 1,
            'volume_hebrew': 'א',
            'letter_arabic': 15,
            'letter_hebrew': 'טו',
            'day': 15,
            'day_hebrew': 'טו',
            'month': 5,
            'month_hebrew': 'שבט',
            'year': 5704,
            'year_hebrew': 'תש"ד',
            'full_date_hebrew': 'טו שבט תש"ד',
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/example4/jewish/Letter4.htm'
        },
        {
            'volume_arabic': 1,
            'volume_hebrew': 'א',
            'letter_arabic': 50,
            'letter_hebrew': 'נ',
            'day': 5,
            'day_hebrew': 'ה',
            'month': 8,
            'month_hebrew': 'ניסן',
            'year': 5710,
            'year_hebrew': 'תשי"ד',
            'full_date_hebrew': 'ה ניסן תשי"ד',
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/example5/jewish/Letter5.htm'
        }
    ]
    
    return test_data


def generate_csv_report(data, filename):
    """יצירת דוח CSV"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['volume_arabic', 'volume_hebrew', 'letter_arabic', 'letter_hebrew', 
                        'day', 'day_hebrew', 'month', 'month_hebrew', 'year', 'year_hebrew', 
                        'full_date_hebrew', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            # כותרות
            writer.writerow({
                'volume_arabic': 'מס\' כרך',
                'volume_hebrew': 'כרך',
                'letter_arabic': 'מס\' מכתב',
                'letter_hebrew': 'מכתב',
                'day': 'יום',
                'day_hebrew': 'יום עברי',
                'month': 'חודש',
                'month_hebrew': 'חודש עברי',
                'year': 'שנה',
                'year_hebrew': 'שנה עברית',
                'full_date_hebrew': 'תאריך מלא',
                'url': 'קישור'
            })
            
            # נתונים
            for row in data:
                writer.writerow(row)
        
        print(f"✅ דוח CSV נוצר: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת CSV: {e}")
        return None


def generate_html_report(data, filename):
    """יצירת דוח HTML"""
    try:
        html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דוח בדיקה - מכתבי אגרות קודש עם תאריכים</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
            direction: rtl;
        }}
        .container {{
            max-width: 1400px;
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .search-box {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #e8f6f3;
            border-radius: 5px;
        }}
        .search-box input {{
            width: 18%;
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 14px;
            margin: 0 1%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
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
            font-weight: bold;
        }}
        .letter-link:hover {{
            text-decoration: underline;
        }}
        .hebrew-number {{
            font-weight: bold;
            color: #8e44ad;
        }}
        .arabic-number {{
            font-weight: bold;
            color: #27ae60;
        }}
        .date-cell {{
            background-color: #fff3cd;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
    <script>
        function searchTable() {{
            var volumeInput = document.getElementById("volumeSearch").value.toLowerCase();
            var letterInput = document.getElementById("letterSearch").value.toLowerCase();
            var dayInput = document.getElementById("daySearch").value.toLowerCase();
            var monthInput = document.getElementById("monthSearch").value.toLowerCase();
            var yearInput = document.getElementById("yearSearch").value.toLowerCase();
            var table = document.getElementById("indexTable");
            var tr = table.getElementsByTagName("tr");
            
            for (var i = 1; i < tr.length; i++) {{
                var td = tr[i].getElementsByTagName("td");
                if (td.length < 12) continue;
                
                var volumeMatch = true;
                var letterMatch = true;
                var dayMatch = true;
                var monthMatch = true;
                var yearMatch = true;
                
                if (volumeInput) {{
                    var volumeText = (td[0].innerHTML + td[1].innerHTML).toLowerCase();
                    volumeMatch = volumeText.indexOf(volumeInput) > -1;
                }}
                
                if (letterInput) {{
                    var letterText = (td[2].innerHTML + td[3].innerHTML).toLowerCase();
                    letterMatch = letterText.indexOf(letterInput) > -1;
                }}
                
                if (dayInput) {{
                    var dayText = (td[4].innerHTML + td[5].innerHTML).toLowerCase();
                    dayMatch = dayText.indexOf(dayInput) > -1;
                }}
                
                if (monthInput) {{
                    var monthText = (td[6].innerHTML + td[7].innerHTML).toLowerCase();
                    monthMatch = monthText.indexOf(monthInput) > -1;
                }}
                
                if (yearInput) {{
                    var yearText = (td[8].innerHTML + td[9].innerHTML).toLowerCase();
                    yearMatch = yearText.indexOf(yearInput) > -1;
                }}
                
                if (volumeMatch && letterMatch && dayMatch && monthMatch && yearMatch) {{
                    tr[i].style.display = "";
                }} else {{
                    tr[i].style.display = "none";
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📇 דוח בדיקה - מכתבי אגרות קודש עם תאריכים</h1>
        
        <div class="summary">
            <div><strong>📚 כרכים:</strong> 1</div>
            <div><strong>📝 סה"כ מכתבים:</strong> {len(data)}</div>
            <div><strong>🕐 תאריך יצירה:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</div>
            <div><strong>🧪 סוג:</strong> דוח בדיקה עם תאריכים מתוקנים</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="volumeSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש כרך">
            <input type="text" id="letterSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש מכתב">
            <input type="text" id="daySearch" onkeyup="searchTable()" placeholder="🔍 חיפוש יום">
            <input type="text" id="monthSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש חודש">
            <input type="text" id="yearSearch" onkeyup="searchTable()" placeholder="🔍 חיפוש שנה">
        </div>
        
        <table id="indexTable">
            <thead>
                <tr>
                    <th>מס' כרך</th>
                    <th>כרך</th>
                    <th>מס' מכתב</th>
                    <th>מכתב</th>
                    <th>יום</th>
                    <th>יום עברי</th>
                    <th>חודש</th>
                    <th>חודש עברי</th>
                    <th>שנה</th>
                    <th>שנה עברית</th>
                    <th>תאריך מלא</th>
                    <th>קישור</th>
                </tr>
            </thead>
            <tbody>
"""

        for entry in data:
            html_content += f"""
                <tr>
                    <td class="arabic-number">{entry['volume_arabic']}</td>
                    <td class="hebrew-number">{entry['volume_hebrew']}</td>
                    <td class="arabic-number">{entry['letter_arabic']}</td>
                    <td class="hebrew-number">{entry['letter_hebrew']}</td>
                    <td class="arabic-number date-cell">{entry['day']}</td>
                    <td class="hebrew-number date-cell">{entry['day_hebrew']}</td>
                    <td class="arabic-number date-cell">{entry['month']}</td>
                    <td class="hebrew-number date-cell">{entry['month_hebrew']}</td>
                    <td class="arabic-number date-cell">{entry['year']}</td>
                    <td class="hebrew-number date-cell">{entry['year_hebrew']}</td>
                    <td class="date-cell">{entry['full_date_hebrew']}</td>
                    <td><a href="{entry['url']}" class="letter-link" target="_blank">פתח מכתב</a></td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>📇 דוח בדיקה נוצר אוטומטית למטרת בדיקת מערכת פרסינג התאריכים</p>
            <p>🗓️ תאריכים מוצגים בפורמט עברי עם המרה למספרים</p>
            <p>🔍 ניתן לחפש בכל השדות באמצעות שדות החיפוש</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)
        
        print(f"✅ דוח HTML נוצר: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת HTML: {e}")
        return None


def main():
    print("📊 יוצר דוחות בדיקה עם תאריכים מתוקנים")
    print("=" * 50)
    
    # יצירת נתוני בדיקה
    test_data = create_test_data()
    
    print(f"📝 נוצרו {len(test_data)} רשומות בדיקה")
    
    # יצירת דוחות
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_file = f"test_report_{timestamp}.csv"
    html_file = f"test_report_{timestamp}.html"
    
    csv_result = generate_csv_report(test_data, csv_file)
    html_result = generate_html_report(test_data, html_file)
    
    if csv_result and html_result:
        print(f"\n🎉 דוחות בדיקה נוצרו בהצלחה!")
        print(f"📄 CSV: {csv_result}")
        print(f"🌐 HTML: {html_result}")
        print(f"\n💡 פתח את קובץ ה-HTML בדפדפן לצפייה אינטראקטיבית")
        print(f"📋 קובץ ה-CSV ניתן לפתיחה ב-Excel")
    else:
        print("❌ שגיאה ביצירת הדוחות")


if __name__ == "__main__":
    main()
