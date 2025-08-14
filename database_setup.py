#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הגדרת בסיס נתונים לפרסר אגרות קודש
"""

import sqlite3
import csv
import json
from datetime import datetime
import os

class IgrotKodeshDB:
    def __init__(self, db_file='igrot_kodesh.db'):
        """אתחול בסיס הנתונים"""
        self.db_file = db_file
        self.conn = None
        self.setup_database()
    
    def setup_database(self):
        """יצירת בסיס הנתונים וטבלאות"""
        self.conn = sqlite3.connect(self.db_file)
        self.conn.execute('PRAGMA foreign_keys = ON')
        
        # טבלת כרכים
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS volumes (
                id INTEGER PRIMARY KEY,
                volume_number INTEGER UNIQUE,
                volume_hebrew TEXT,
                total_letters INTEGER,
                total_pages INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # טבלת מכתבים
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS letters (
                id INTEGER PRIMARY KEY,
                volume_id INTEGER,
                letter_number INTEGER,
                letter_hebrew TEXT,
                day_numeric INTEGER,
                day_hebrew TEXT,
                month_hebrew TEXT,
                year_numeric INTEGER,
                year_hebrew TEXT,
                full_date_hebrew TEXT,
                url TEXT,
                content TEXT,
                parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (volume_id) REFERENCES volumes (id)
            )
        ''')
        
        # טבלת סטטיסטיקות
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY,
                total_volumes INTEGER,
                total_letters INTEGER,
                total_with_dates INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # טבלת לוגים
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS parse_logs (
                id INTEGER PRIMARY KEY,
                action TEXT,
                volume_number INTEGER,
                letter_number INTEGER,
                status TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("✅ בסיס הנתונים הוגדר בהצלחה")
    
    def add_volume(self, volume_number, volume_hebrew, total_letters=0, total_pages=0):
        """הוספת כרך חדש"""
        try:
            cursor = self.conn.execute('''
                INSERT OR REPLACE INTO volumes 
                (volume_number, volume_hebrew, total_letters, total_pages)
                VALUES (?, ?, ?, ?)
            ''', (volume_number, volume_hebrew, total_letters, total_pages))
            self.conn.commit()
            print(f"✅ נוסף כרך {volume_hebrew} ({volume_number})")
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ שגיאה בהוספת כרך: {e}")
            return None
    
    def add_letter(self, volume_id, letter_data):
        """הוספת מכתב חדש"""
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO letters 
                (volume_id, letter_number, letter_hebrew, day_numeric, day_hebrew,
                 month_hebrew, year_numeric, year_hebrew, full_date_hebrew, url, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                volume_id,
                letter_data.get('letter_number'),
                letter_data.get('letter_hebrew'),
                letter_data.get('day_numeric'),
                letter_data.get('day_hebrew'),
                letter_data.get('month_hebrew'),
                letter_data.get('year_numeric'),
                letter_data.get('year_hebrew'),
                letter_data.get('full_date_hebrew'),
                letter_data.get('url'),
                letter_data.get('content', '')
            ))
            self.conn.commit()
            print(f"✅ נוסף מכתב {letter_data.get('letter_hebrew')}")
            return True
        except Exception as e:
            print(f"❌ שגיאה בהוספת מכתב: {e}")
            return False
    
    def import_from_csv(self, csv_file):
        """יבוא נתונים מקובץ CSV"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # יצירת כרך א'
                volume_id = self.add_volume(1, 'א')
                
                count = 0
                for row in reader:
                    letter_data = {
                        'letter_number': int(row.get('מס\' מכתב', 0)),
                        'letter_hebrew': row.get('מכתב', ''),
                        'day_numeric': int(row.get('יום מספר', 0)),
                        'day_hebrew': row.get('יום עברי', ''),
                        'month_hebrew': row.get('חודש', ''),
                        'year_numeric': int(row.get('שנה מספר', 0)),
                        'year_hebrew': row.get('שנה עברית', ''),
                        'full_date_hebrew': row.get('תאריך מלא', ''),
                        'url': row.get('קישור', '')
                    }
                    
                    if self.add_letter(volume_id, letter_data):
                        count += 1
                
                print(f"📊 יובאו {count} מכתבים מקובץ {csv_file}")
                self.update_statistics()
                return True
                
        except Exception as e:
            print(f"❌ שגיאה ביבוא מ-CSV: {e}")
            return False
    
    def get_all_letters(self):
        """קבלת כל המכתבים"""
        cursor = self.conn.execute('''
            SELECT l.*, v.volume_hebrew, v.volume_number
            FROM letters l
            JOIN volumes v ON l.volume_id = v.id
            ORDER BY v.volume_number, l.letter_number
        ''')
        return cursor.fetchall()
    
    def search_letters(self, **kwargs):
        """חיפוש מכתבים לפי קריטריונים"""
        conditions = []
        params = []
        
        if kwargs.get('volume'):
            conditions.append("v.volume_hebrew = ?")
            params.append(kwargs['volume'])
        
        if kwargs.get('year'):
            conditions.append("l.year_numeric = ?")
            params.append(kwargs['year'])
        
        if kwargs.get('month'):
            conditions.append("l.month_hebrew LIKE ?")
            params.append(f"%{kwargs['month']}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor = self.conn.execute(f'''
            SELECT l.*, v.volume_hebrew, v.volume_number
            FROM letters l
            JOIN volumes v ON l.volume_id = v.id
            WHERE {where_clause}
            ORDER BY v.volume_number, l.letter_number
        ''', params)
        
        return cursor.fetchall()
    
    def update_statistics(self):
        """עדכון סטטיסטיקות"""
        # ספירת כרכים
        total_volumes = self.conn.execute('SELECT COUNT(*) FROM volumes').fetchone()[0]
        
        # ספירת מכתבים
        total_letters = self.conn.execute('SELECT COUNT(*) FROM letters').fetchone()[0]
        
        # ספירת מכתבים עם תאריכים
        total_with_dates = self.conn.execute('''
            SELECT COUNT(*) FROM letters 
            WHERE day_numeric > 0 AND year_numeric > 0
        ''').fetchone()[0]
        
        # עדכון הטבלה
        self.conn.execute('''
            INSERT OR REPLACE INTO statistics 
            (id, total_volumes, total_letters, total_with_dates, last_updated)
            VALUES (1, ?, ?, ?, ?)
        ''', (total_volumes, total_letters, total_with_dates, datetime.now()))
        
        self.conn.commit()
        print(f"📊 סטטיסטיקות: {total_volumes} כרכים, {total_letters} מכתבים")
    
    def export_to_json(self, output_file):
        """יצוא לקובץ JSON"""
        letters = self.get_all_letters()
        
        # המרה לפורמט JSON
        json_data = []
        for letter in letters:
            json_data.append({
                'volume_number': letter[12],
                'volume_hebrew': letter[11],
                'letter_number': letter[2],
                'letter_hebrew': letter[3],
                'day_numeric': letter[4],
                'day_hebrew': letter[5],
                'month_hebrew': letter[6],
                'year_numeric': letter[7],
                'year_hebrew': letter[8],
                'full_date_hebrew': letter[9],
                'url': letter[10]
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ יוצא ל-JSON: {output_file}")
        return output_file
    
    def create_web_api_endpoint(self):
        """יצירת endpoint לAPI"""
        letters = self.get_all_letters()
        
        api_data = {
            'metadata': {
                'total_letters': len(letters),
                'last_updated': datetime.now().isoformat(),
                'source': 'igrot-kodesh-parser'
            },
            'letters': []
        }
        
        for letter in letters:
            api_data['letters'].append({
                'id': letter[0],
                'volume': {
                    'number': letter[12],
                    'hebrew': letter[11]
                },
                'letter': {
                    'number': letter[2],
                    'hebrew': letter[3]
                },
                'date': {
                    'day_numeric': letter[4],
                    'day_hebrew': letter[5],
                    'month_hebrew': letter[6],
                    'year_numeric': letter[7],
                    'year_hebrew': letter[8],
                    'full_hebrew': letter[9]
                },
                'url': letter[10]
            })
        
        with open('api_data.json', 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        
        print("✅ נוצר endpoint API: api_data.json")
        return api_data
    
    def close(self):
        """סגירת חיבור לבסיס הנתונים"""
        if self.conn:
            self.conn.close()
            print("📤 חיבור בסיס הנתונים נסגר")

def main():
    """פונקציה ראשית"""
    print("🗄️ הגדרת בסיס נתונים לאגרות קודש")
    print("=" * 50)
    
    # יצירת בסיס נתונים
    db = IgrotKodeshDB()
    
    # בדיקה אם יש CSV קיים לייבא
    csv_file = "test_reports/test_10_letters.csv"
    if os.path.exists(csv_file):
        print(f"📄 מייבא נתונים מ-{csv_file}")
        db.import_from_csv(csv_file)
        
        # יצוא ל-JSON
        db.export_to_json('igrot_kodesh_data.json')
        
        # יצירת API endpoint
        db.create_web_api_endpoint()
    
    else:
        print(f"⚠️ קובץ CSV לא נמצא: {csv_file}")
    
    # סגירת החיבור
    db.close()
    
    print("\n🎉 הגדרת בסיס הנתונים הושלמה!")

if __name__ == "__main__":
    main()
