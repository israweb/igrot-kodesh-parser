#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
אגרות קודש - שרת מקומי פשוט
מאפשר צפייה בדוחות דרך שרת HTTP מקומי
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time
from datetime import datetime

def create_index_page():
    """יצירת עמוד ראשי עם קישורים לדוחות"""
    
    # חיפוש קבצי דוחות
    reports = []
    for folder in ['reports', 'test_reports']:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.endswith('.html'):
                    reports.append({
                        'name': file,
                        'path': f'{folder}/{file}',
                        'size': os.path.getsize(os.path.join(folder, file)),
                        'modified': datetime.fromtimestamp(os.path.getmtime(os.path.join(folder, file)))
                    })
    
    # יצירת רשימת דוחות
    reports_list = ""
    if reports:
        for report in sorted(reports, key=lambda x: x['modified'], reverse=True):
            reports_list += f"""
            <div class="report-card">
                <h3>📄 {report['name']}</h3>
                <p>📅 עודכן: {report['modified'].strftime('%Y-%m-%d %H:%M')}</p>
                <p>📊 גודל: {report['size']} bytes</p>
                <a href="{report['path']}" target="_blank" class="btn">פתח דוח</a>
            </div>
            """
    else:
        reports_list = """
        <div class="no-reports">
            <h3>📂 אין דוחות זמינים</h3>
            <p>הרץ את הפרסר כדי ליצור דוחות</p>
            <code>python run_local_parser.py --mode test</code>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>אגרות קודש - פרסר מקומי</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1200px; 
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
            .reports-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .report-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
            }}
            .report-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                border-color: #3498db;
            }}
            .btn {{
                display: inline-block;
                padding: 10px 20px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background 0.3s ease;
            }}
            .btn:hover {{
                background: #2980b9;
            }}
            .commands {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-right: 4px solid #3498db;
            }}
            .command {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                margin: 10px 0;
                cursor: pointer;
            }}
            .no-reports {{
                text-align: center;
                padding: 40px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 אגרות קודש - פרסר מקומי</h1>
                <p>שרת מקומי פועל בפורט 8000</p>
                <p>עדכון: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="commands">
                <h2>🚀 פקודות זמינות:</h2>
                <div class="command" onclick="navigator.clipboard.writeText(this.innerText)">
                    python run_local_parser.py --mode test
                </div>
                <div class="command" onclick="navigator.clipboard.writeText(this.innerText)">
                    python run_local_parser.py --mode single --volume א
                </div>
                <div class="command" onclick="navigator.clipboard.writeText(this.innerText)">
                    python start_local_server.py
                </div>
                <p><small>💡 לחץ על פקודה כדי להעתיק אותה</small></p>
            </div>
            
            <h2>📄 דוחות זמינים:</h2>
            <div class="reports-grid">
                {reports_list}
            </div>
            
            <div style="text-align: center; margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <p>🔗 <a href="https://github.com/israweb/igrot-kodesh-parser" style="color: #3498db;">GitHub Repository</a></p>
                <p>🌐 שרת מקומי: http://localhost:8000</p>
            </div>
        </div>
        
        <script>
            // רענון אוטומטי כל 30 שניות
            setTimeout(() => window.location.reload(), 30000);
        </script>
    </body>
    </html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def start_server(port=8000):
    """הפעלת שרת HTTP מקומי"""
    
    create_index_page()
    
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-cache')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
        print(f"🌐 שרת מקומי פועל בכתובת: http://localhost:{port}")
        print("📂 תיקיית עבודה:", os.getcwd())
        print("⏹️  ללחוץ Ctrl+C לעצירת השרת")
        
        # פתיחה אוטומטית בדפדפן
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{port}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️  השרת נעצר")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ פורט לא תקין, משתמש בפורט 8000")
    
    start_server(port)
