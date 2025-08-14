#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
אינטגרציות רשת לפרסר אגרות קודש
"""

import requests
import json
import os
from datetime import datetime

class WebIntegrations:
    def __init__(self):
        """אתחול אינטגרציות"""
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        
    def setup_airtable(self):
        """הגדרת Airtable"""
        print("🔧 הגדרת Airtable:")
        print("1. עבור לאתר https://airtable.com")
        print("2. צור בסיס נתונים חדש")
        print("3. הוסף שדות: כרך, מכתב, תאריך, שנה, קישור")
        print("4. קבל API Key מ-Account Settings")
        
    def upload_to_airtable(self, data):
        """העלאה ל-Airtable"""
        if not self.airtable_api_key:
            print("❌ חסר Airtable API Key")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://api.airtable.com/v0/{self.airtable_base_id}/Letters'
        
        # מגביל ל-10 רשומות (limit של Airtable API)
        batch_data = {
            "records": []
        }
        
        for item in data[:10]:
            record = {
                "fields": {
                    "כרך": item.get('volume_hebrew', ''),
                    "מכתב": item.get('letter_hebrew', ''),
                    "תאריך": item.get('full_date_hebrew', ''),
                    "שנה": item.get('year_numeric', 0),
                    "קישור": item.get('url', '')
                }
            }
            batch_data["records"].append(record)
        
        try:
            response = requests.post(url, headers=headers, json=batch_data)
            if response.status_code == 200:
                print("✅ הועלה ל-Airtable בהצלחה")
                return True
            else:
                print(f"❌ שגיאה ב-Airtable: {response.text}")
                return False
        except Exception as e:
            print(f"❌ שגיאת חיבור ל-Airtable: {e}")
            return False
    
    def setup_google_sheets(self):
        """הגדרת Google Sheets"""
        print("🔧 הגדרת Google Sheets:")
        print("1. עבור ל-Google Cloud Console")
        print("2. אפשר Google Sheets API")
        print("3. צור Service Account")
        print("4. הורד credentials.json")
        print("5. התקן: pip install gspread")
        
    def upload_to_google_sheets(self, data, sheet_id):
        """העלאה ל-Google Sheets"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # הגדרת אישורים
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                'credentials.json', scopes=scopes
            )
            
            client = gspread.authorize(creds)
            sheet = client.open_by_key(sheet_id).sheet1
            
            # מחיקת תוכן קיים
            sheet.clear()
            
            # הוספת כותרות
            headers = ['כרך', 'מכתב', 'תאריך', 'שנה', 'קישור']
            sheet.append_row(headers)
            
            # הוספת נתונים
            for item in data:
                row = [
                    item.get('volume_hebrew', ''),
                    item.get('letter_hebrew', ''),
                    item.get('full_date_hebrew', ''),
                    item.get('year_numeric', 0),
                    item.get('url', '')
                ]
                sheet.append_row(row)
            
            print("✅ הועלה ל-Google Sheets בהצלחה")
            return True
            
        except ImportError:
            print("❌ חסר gspread. התקן: pip install gspread")
            return False
        except Exception as e:
            print(f"❌ שגיאה ב-Google Sheets: {e}")
            return False
    
    def setup_supabase(self):
        """הגדרת Supabase"""
        print("🔧 הגדרת Supabase:")
        print("1. עבור ל-https://supabase.com")
        print("2. צור פרויקט חדש")
        print("3. צור טבלה 'letters' עם השדות הנדרשים")
        print("4. קבל URL ו-API Key")
        print("5. התקן: pip install supabase")
    
    def upload_to_supabase(self, data, url, key):
        """העלאה ל-Supabase"""
        try:
            from supabase import create_client
            
            supabase = create_client(url, key)
            
            # המרת נתונים לפורמט Supabase
            supabase_data = []
            for item in data:
                supabase_data.append({
                    'volume_hebrew': item.get('volume_hebrew', ''),
                    'letter_hebrew': item.get('letter_hebrew', ''),
                    'full_date_hebrew': item.get('full_date_hebrew', ''),
                    'year_numeric': item.get('year_numeric', 0),
                    'url': item.get('url', '')
                })
            
            # העלאה לטבלה
            response = supabase.table('letters').insert(supabase_data).execute()
            
            print("✅ הועלה ל-Supabase בהצלחה")
            return True
            
        except ImportError:
            print("❌ חסר supabase. התקן: pip install supabase")
            return False
        except Exception as e:
            print(f"❌ שגיאה ב-Supabase: {e}")
            return False
    
    def create_github_pages_data(self, data):
        """יצירת נתונים ל-GitHub Pages"""
        
        # יצירת קובץ נתונים עבור האתר
        website_data = {
            'metadata': {
                'title': 'אגרות קודש - פרסר',
                'description': 'מאגר נתונים של אגרות קודש',
                'total_letters': len(data),
                'last_updated': datetime.now().isoformat(),
                'source': 'https://github.com/israweb/igrot-kodesh-parser'
            },
            'letters': data
        }
        
        # שמירת הנתונים
        with open('docs/data.json', 'w', encoding='utf-8') as f:
            json.dump(website_data, f, ensure_ascii=False, indent=2)
        
        # יצירת קובץ HTML לאתר
        html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>אגרות קודש - פרסר</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; border: 1px solid #ddd; text-align: center; }}
        th {{ background: #f4f4f4; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 אגרות קודש - פרסר נתונים</h1>
        <p>סה"כ מכתבים: {len(data)}</p>
        <p>עדכון אחרון: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <table id="lettersTable">
            <thead>
                <tr>
                    <th>כרך</th>
                    <th>מכתב</th>
                    <th>תאריך</th>
                    <th>שנה</th>
                    <th>קישור</th>
                </tr>
            </thead>
            <tbody>
                <!-- נתונים יטענו דרך JavaScript -->
            </tbody>
        </table>
    </div>
    
    <script>
        fetch('data.json')
            .then(response => response.json())
            .then(data => {{
                const tbody = document.querySelector('#lettersTable tbody');
                data.letters.forEach(letter => {{
                    const row = `
                        <tr>
                            <td>${{letter.volume_hebrew}}</td>
                            <td>${{letter.letter_hebrew}}</td>
                            <td>${{letter.full_date_hebrew}}</td>
                            <td>${{letter.year_numeric}}</td>
                            <td><a href="${{letter.url}}" target="_blank">פתח</a></td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                }});
            }});
    </script>
</body>
</html>"""
        
        # יצירת תיקיית docs אם לא קיימת
        os.makedirs('docs', exist_ok=True)
        
        with open('docs/index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ נוצרו קבצים ל-GitHub Pages:")
        print("   📄 docs/data.json")
        print("   🌐 docs/index.html")
        
        return True

def main():
    """פונקציה ראשית"""
    print("🌐 אינטגרציות רשת לפרסר אגרות קודש")
    print("=" * 50)
    
    # טעינת נתונים לדוגמה
    sample_data = [
        {
            'volume_hebrew': 'א',
            'letter_hebrew': 'א',
            'full_date_hebrew': 'כא אדר תרפח',
            'year_numeric': 5688,
            'url': 'https://www.chabad.org/therebbe/article_cdo/aid/4645943/jewish/page.htm'
        }
    ]
    
    integrations = WebIntegrations()
    
    print("\n📋 אפשרויות אינטגרציה:")
    print("1. SQLite (מקומי) - מומלץ")
    print("2. Airtable (1,200 רשומות חינם)")
    print("3. Google Sheets (ללא הגבלה)")
    print("4. Supabase (500MB חינם)")
    print("5. GitHub Pages (סטטי)")
    
    # יצירת נתונים ל-GitHub Pages
    integrations.create_github_pages_data(sample_data)
    
    print("\n💡 הצעה: התחל עם SQLite מקומי ו-GitHub Pages לתצוגה!")

if __name__ == "__main__":
    main()
