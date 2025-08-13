#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string
import logging

from config import WEB_PORT, WEB_HOST, TIMEZONE
from database import db

logger = logging.getLogger(__name__)

class WebServer:
    """ويب سيرفر للمراقبة والاستضافة"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """إعداد المسارات"""
        
        @self.app.route('/')
        def home():
            """الصفحة الرئيسية"""
            html_template = """
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>بوت تنظيم الملاحظات الذكي</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        color: #333;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 20px;
                        padding: 30px;
                        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                        backdrop-filter: blur(10px);
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .header h1 {
                        color: #4a5568;
                        margin: 0;
                        font-size: 2.5em;
                    }
                    .status-card {
                        background: #f7fafc;
                        border-radius: 15px;
                        padding: 20px;
                        margin: 20px 0;
                        border-left: 5px solid #48bb78;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }
                    .stat-item {
                        background: white;
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
                    }
                    .stat-number {
                        font-size: 2em;
                        font-weight: bold;
                        color: #667eea;
                        margin-bottom: 10px;
                    }
                    .stat-label {
                        color: #718096;
                        font-size: 0.9em;
                    }
                    .features {
                        margin-top: 30px;
                    }
                    .feature-item {
                        background: white;
                        margin: 10px 0;
                        padding: 15px;
                        border-radius: 10px;
                        border-right: 4px solid #667eea;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 30px;
                        color: #718096;
                        font-size: 0.9em;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 بوت تنظيم الملاحظات الذكي</h1>
                        <p>مساعدك الشخصي الذكي في تنظيم حياتك اليومية</p>
                    </div>
                    
                    <div class="status-card">
                        <h3>✅ البوت يعمل بشكل طبيعي</h3>
                        <p>📅 آخر تحديث: {{ current_time }}</p>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number">{{ stats.total_notes }}</div>
                            <div class="stat-label">إجمالي الملاحظات</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{{ stats.total_categories }}</div>
                            <div class="stat-label">إجمالي التصنيفات</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{{ stats.recent_notes }}</div>
                            <div class="stat-label">الملاحظات الحديثة</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">8</div>
                            <div class="stat-label">الأوامر المتاحة</div>
                        </div>
                    </div>
                    
                    <div class="features">
                        <h3>🌟 المميزات الرئيسية:</h3>
                        <div class="feature-item">
                            <strong>📝 إدارة الملاحظات:</strong> إضافة وتنظيم الملاحظات بتصنيفات مخصصة
                        </div>
                        <div class="feature-item">
                            <strong>🎯 نظام الأولويات:</strong> تصنيف الملاحظات حسب الأهمية مع رموز ملونة
                        </div>
                        <div class="feature-item">
                            <strong>⏰ التذكيرات الذكية:</strong> تذكيرات متقدمة مع خيارات وقت مخصصة
                        </div>
                        <div class="feature-item">
                            <strong>🔍 البحث المتقدم:</strong> البحث السريع في جميع الملاحظات
                        </div>
                        <div class="feature-item">
                            <strong>📊 الإحصائيات:</strong> تحليل مفصل لاستخدامك للبوت
                        </div>
                        <div class="feature-item">
                            <strong>💾 النسخ الاحتياطي:</strong> حفظ آمن لجميع بياناتك
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>للبدء، ابحث عن البوت في تليجرام وأرسل /start</p>
                        <p>© 2024 بوت تنظيم الملاحظات الذكي - جميع الحقوق محفوظة</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            stats = db.get_stats()
            current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
            
            return render_template_string(html_template, stats=stats, current_time=current_time)
        
        @self.app.route('/health')
        def health_check():
            """فحص صحة النظام"""
            try:
                stats = db.get_stats()
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now(TIMEZONE).isoformat(),
                    'stats': stats,
                    'services': {
                        'database': 'operational',
                        'reminder_system': 'operational',
                        'web_server': 'operational'
                    }
                })
            except Exception as e:
                logger.error(f"خطأ في فحص الصحة: {e}")
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now(TIMEZONE).isoformat(),
                    'error': str(e)
                }), 500
        
        @self.app.route('/status')
        def status():
            """حالة النظام المفصلة"""
            try:
                stats = db.get_stats()
                categories = db.get_category_names()
                
                return jsonify({
                    'bot_status': 'running',
                    'timestamp': datetime.now(TIMEZONE).isoformat(),
                    'statistics': stats,
                    'categories': categories,
                    'system_info': {
                        'version': '1.0.0',
                        'features': [
                            'notes_management',
                            'categories',
                            'priorities',
                            'reminders',
                            'search',
                            'statistics',
                            'backup'
                        ]
                    }
                })
            except Exception as e:
                logger.error(f"خطأ في حالة النظام: {e}")
                return jsonify({
                    'bot_status': 'error',
                    'timestamp': datetime.now(TIMEZONE).isoformat(),
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/stats')
        def api_stats():
            """API للإحصائيات"""
            try:
                stats = db.get_stats()
                return jsonify({
                    'success': True,
                    'data': stats,
                    'timestamp': datetime.now(TIMEZONE).isoformat()
                })
            except Exception as e:
                logger.error(f"خطأ في API الإحصائيات: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now(TIMEZONE).isoformat()
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            """صفحة 404"""
            return jsonify({
                'error': 'الصفحة غير موجودة',
                'status_code': 404,
                'timestamp': datetime.now(TIMEZONE).isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """صفحة 500"""
            return jsonify({
                'error': 'خطأ داخلي في الخادم',
                'status_code': 500,
                'timestamp': datetime.now(TIMEZONE).isoformat()
            }), 500
    
    def run(self):
        """تشغيل الويب سيرفر"""
        logger.info(f"بدء تشغيل الويب سيرفر على {WEB_HOST}:{WEB_PORT}")
        
        self.app.run(
            host=WEB_HOST,
            port=WEB_PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    
    def start_in_background(self):
        """تشغيل الويب سيرفر في الخلفية"""
        web_thread = threading.Thread(target=self.run, daemon=True)
        web_thread.start()
        logger.info("تم تشغيل الويب سيرفر في الخلفية")

# إنشاء مثيل واحد من الويب سيرفر
web_server = WebServer()