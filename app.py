from flask import Flask, request, redirect, url_for, session, jsonify
from datetime import datetime
import time
import re
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'uznavaykin-2026-super-ultra-secret'

# ГЛОБАЛЬНЫЕ ДАННЫЕ
users = {
    'CatNap': {'password': '***', 'role': 'premium', 'admin': True, 'muted_until': 0, 'mute_reason': ''},
    'Назар': {'password': '***', 'role': 'premium', 'admin': True, 'muted_until': 0, 'mute_reason': ''}
}
user_profiles = {}
user_roles = {}
user_activity = {}
afk_users = set()
chat_messages = []
banned_words = ['плохое_слово1', 'плохое_слово2']
category_structure = {
    'Minecraft': {
        'logo': '<img src="/static/minecraft_logo.png" style="width:90px;height:90px;border-radius:15px;">',
        'subcategories': {}
    },
    'World of Tanks': {
        'logo': '<img src="/static/wot_logo.jpg" style="width:90px;height:90px;border-radius:15px;">', 
        'subcategories': {}
    }
}
catalog_items = {}

def get_timestamp():
    return time.time()

def is_online(username):
    return username in user_activity and (get_timestamp() - user_activity[username] < 300)

def is_afk(username):
    inactive_time = get_timestamp() - user_activity.get(username, 0)
    return 60 < inactive_time < 300

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'admin': 0}
    for username in list(users.keys()) + list(user_roles.keys()):
        if is_online(username):
            stats['online'] += 1
            role = user_roles.get(username, 'start')
            if is_afk(username):
                stats['afk'] += 1
            elif users.get(username, {}).get('admin'):
                stats['admin'] += 1
            elif role == 'premium':
                stats['premium'] += 1
            elif role == 'vip':
                stats['vip'] += 1
            else:
                stats['start'] += 1
    return stats

@app.route('/')
def index():
    current_user = session.get('user')
    stats = calculate_stats()
    
    html = f'''
    <!DOCTYPE html>
    <html><head><title>Узнавайкин</title>
    <meta charset="utf-8">
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}}
    .container{{max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden;}}
    .header{{padding:30px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}}
    .user-info{{padding:20px;background:#f8f9fa;border-bottom:1px solid #eee;}}
    .stats{{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;padding:20px;background:#e9ecef;}}
    .stat-card{{background:white;padding:15px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center;min-width:120px;}}
    .nav{{display:flex;justify-content:center;gap:15px;padding:20px;flex-wrap:wrap;}}
    .nav-btn{{padding:15px 30px;background:#007bff;color:white;text-decoration:none;border-radius:10px;font-weight:bold;transition:all 0.3s;}}
    .nav-btn:hover{{transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,0,0,0.2);}}
    .admin-btn{{background:#dc3545 !important;}}</style></head>
    <body>
    <div class="container">
    '''
    
    if current_user:
        role = user_roles.get(current_user, 'start')
        html += f'''
        <div class="header">
            <h1>🏠 Узнавайкин</h1>
            <div>👤 <b>{current_user}</b> <span style="color:gold;font-weight:bold;">{role.upper()}</span></div>
        </div>
        <div class="user-info">
            <a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>
            <a href="/logout" class="nav-btn">🚪 Выход</a>
            {'<a href="/buy/vip" class="nav-btn">VIP</a><a href="/buy/premium" class="nav-btn">PREMIUM</a>' if role != 'premium' else ''}
        </div>
        '''
    else:
        html += '''
        <div class="header"><h1>🏠 Узнавайкин</h1></div>
        <div class="user-info" style="text-align:center;">
            <a href="/login" class="nav-btn">🔐 ВОЙТИ</a>
            <a href="/register" class="nav-btn">📝 РЕГИСТРАЦИЯ</a>
        </div>
        '''
    
    html += f'''
    <div class="stats">
        <div class="stat-card"><b>{stats['online']}</b><br>Онлайн</div>
        <div class="stat-card"><b>{stats['afk']}</b><br>АФК</div>
        <div class="stat-card"><b>{stats['start']}</b><br>Start</div>
        <div class="stat-card"><b>{stats['vip']}</b><br>VIP</div>
        <div class="stat-card"><b>{stats['premium']}</b><br>Premium</div>
        <div class="stat-card"><b>{stats['admin']}</b><br>Админы</div>
    </div>
    <div class="nav">
        <a href="/catalog" class="nav-btn">📁 КАТАЛОГ</a>
        <a href="/chat" class="nav-btn">💬 ЧАТ</a>
        <a href="/profiles" class="nav-btn">👥 ПРОФИЛИ</a>
        <a href="/community" class="nav-btn">📢 TG</a>
    '''
    if current_user and users.get(current_user, {}).get('admin'):
        html += '<a href="/admin" class="nav-btn admin-btn">🔧 АДМИН</a>'
    html += '</div></div></body></html>'
    return html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if username in users:  # Админ
            session['user'] = username
            user_roles[username] = users[username]['role']
        else:  # Новый пользователь
            users[username] = {'password': password, 'role': 'start', 'admin': False, 'muted_until': 0, 'mute_reason': ''}
            user_roles[username] = 'start'
            session['user'] = username
        
        user_activity[username] = get_timestamp()
        user_profiles[username] = {'bio': '', 'games': [], 'achievements': [], 'join_date': '2026-01-15'}
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html><html><head><title>Вход</title>
    <style>body{font-family:Arial;padding:50px;text-align:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);}
    form{max-width:400px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}</style></head>
    <body>
    <h1 style="color:white;margin-bottom:30px;">🔐 Узнавайкин</h1>
    <form method="post">
        <input name="username" placeholder="Логин" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <input name="password" type="password" placeholder="Пароль" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <button style="width:100%;padding:18px;background:#4ecdc4;color:white;border:none;border-radius:10px;font-size:20px;cursor:pointer;">🚀 ВОЙТИ / РЕГИСТРАЦИЯ</button>
    </form>
    <p style="margin-top:30px;color:white;font-size:14px;">👑 Админы: CatNap, Назар</p>
    </body></html>
    '''

@app.route('/register')
def register():
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/buy/<role>')
def buy_role(role):
    if 'user' in session:
        user_roles[session['user']] = role
        user_activity[session['user']] = get_timestamp()
    return redirect(url_for('index'))

@app.route('/catalog')
def catalog():
    current_path = request.args.get('path', '').strip('/')
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Каталог</title>
    <meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#f8f9fa;}
    .breadcrumbs a{color:#007bff;text-decoration:none;font-size:18px;}
    .category-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:30px;}
    .category-card{background:linear-gradient(145deg,#ffffff,#f0f0f0);padding:35px;border-radius:20px;box-shadow:0 15px 35px rgba(0,0,0,0.1);text-align:center;cursor:pointer;transition:all 0.3s;border:3px solid transparent;}
    .category-card:hover{transform:translateY(-10px);box-shadow:0 25px 50px rgba(0,0,0,0.2);border-color:#007bff;}
    .logo{margin:0 auto 20px;display:block;}
    .info-card{background:#e9ecef;padding:30px;border-radius:20px;margin:20px 0;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
    .back-btn{background:#6c757d;color:white;padding:18px 35px;border-radius:12px;text-decoration:none;display:inline-block;margin:30px 0;font-weight:bold;}</style></head>
    <body>
    '''
    
    # Breadcrumbs
    if current_path:
        paths = current_path.split('/')
        current = ''
        html += '<div style="margin-bottom:40px;font-size:18px;"><a href="/catalog" style="color:#007bff;">🏠 Каталог</a>'
        for path in paths:
            current += ('' if current == '' else '/') + path
            html += f' / <a href="/catalog?path={current}" style="color:#007bff;">{path}</a>'
        html += '</div>'
    else:
        html += '<h1 style="text-align:center;margin:50px 0;font-size:42px;color:#333;">📁 ИГРЫ</h1>'
    
    # Главные игры
    if not current_path:
        html += f'''
        <div class="category-grid">
            <a href="/catalog?path=Minecraft" class="category-card">
                <div class="logo">{category_structure['Minecraft']['logo']}</div>
                <h2 style="font-size:28px;margin:15px 0;color:#2d5a2d;">Minecraft</h2>
            </a>
            <a href="/catalog?path=World of Tanks" class="category-card">
                <div class="logo">{category_structure['World of Tanks']['logo']}</div>
                <h2 style="font-size:28px;margin:15px 0;color:#8b0000;">World of Tanks</h2>
            </a>
        </div>
        '''
    
    # Подкатегории/Контент
    elif current_path in category_structure:
        subs = category_structure[current_path]['subcategories']
        if subs:
            html += f'<h2 style="text-align:center;margin:50px 0;font-size:34px;color:#333;">📂 {current_path}</h2><div class="category-grid">'
            for sub_name, sub_data in subs.items():
                html += f'''
                <a href="/catalog?path={current_path}/{sub_name}" class="category-card">
                    <div class="logo">{sub_data.get("logo", "📂")}</div>
                    <h2 style="font-size:24px;margin:15px 0;">{sub_name}</h2>
                </a>
                '''
            html += '</div>'
        else:
            html += f'<h2 style="text-align:center;margin:50px 0;font-size:34px;color:#333;">📄 {current_path}</h2>'
            if current_path in catalog_items and catalog_items[current_path]:
                for item in catalog_items[current_path]:
                    html += f'''
                    <div class="info-card">
                        <h3 style="color:#007bff;margin-bottom:20px;font-size:24px;">{item["title"]}</h3>
                        <p style="line-height:1.7;font-size:16px;color:#333;">{item["info"]}</p>
                        {f'<img src="{item["photo"]}" style="max-width:100%;border-radius:20px;margin-top:25px;box-shadow:0 15px 40px rgba(0,0,0,0.2);" alt="Фото">' if item.get("photo") else ''}
                    </div>
                    '''
            else:
                html += '<p style="text-align:center;color:#666;font-size:20px;margin:60px 0;">Пока пусто... 👈 Админы, добавьте контент!</p>'
    
    html += '''
    <div style="text-align:center;margin:60px 0;">
        <a href="/" class="back-btn">🏠 Главная страница</a>
    </div></body></html>
    '''
    return html

@app.route('/profiles')
def profiles():
    html = '''
    <!DOCTYPE html>
    <html><head><title>Профили</title>
    <style>body{font-family:Arial;padding:30px;background:#f0f2f5;}
    .profiles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:25px;}
    .profile-card{background:white;padding:25px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);transition:transform 0.3s;}
    .profile-card:hover{transform:translateY(-5px);}</style></head>
    <body>
    <h1 style="text-align:center;margin-bottom:40px;font-size:36px;">👥 Все профили</h1>
    <div class="profiles-grid">
    '''
    for username in users.keys():
        role = user_roles.get(username, 'start')
        html += f'''
        <div class="profile-card">
            <h3 style="margin-bottom:15px;">{username}</h3>
            <span style="padding:8px 16px;background:{'gold' if role=='premium' else '#00ff88' if role=='vip' else '#ccc'};border-radius:20px;font-weight:bold;font-size:14px;">
                {role.upper()}
            </span>
            <a href="/profile/{username}" style="display:block;margin-top:20px;padding:12px 25px;background:#007bff;color:white;border-radius:10px;text-align:center;">👁️ Просмотреть</a>
        </div>
        '''
    html += '''
    </div><div style="text-align:center;margin-top:50px;">
        <a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;">🏠 Главная</a>
    </div></body></html>
    '''
    return html

@app.route('/profile/<username>')
def profile(username):
    if username not in users:
        return '<h1 style="color:red;text-align:center;margin:100px;">❌ Пользователь не найден</h1><a href="/" style="display:block;text-align:center;">🏠 Главная</a>'
    
    profile_data = user_profiles.get(username, {'bio': '', 'games': [], 'achievements': [], 'join_date': '2026-01-15'})
    role = user_roles.get(username, 'start')
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Профиль {username}</title>
    <style>body{{font-family:Arial;padding:40px;background:#f0f2f5;}}
    .profile-card{{background:white;max-width:900px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);}}
    .status-badge{{padding:8px 20px;border-radius:25px;color:white;font-weight:bold;font-size:16px;}}
    .premium{{background:gold;}} .vip{{background:#00ff88;}} .admin{{background:#ff4444;}} .start{{background:#999;}}</style></head>
    <body>
    <div class="profile-card">
        <div style="display:flex;align-items:center;gap:30px;margin-bottom:40px;">
            <div style="font-size:64px;">👤</div>
            <div>
                <h1 style="margin-bottom:10px;">{username}</h1>
                <span class="status-badge {"admin" if users[username].get("admin") else "premium" if role=="premium" else "vip" if role=="vip" else "start"}">
                    { "Администратор" if users[username].get("admin") else role.upper() }
                </span>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;">
            <div>
                <h3 style="margin-bottom:20px;color:#333;">📝 О себе</h3>
                <p style="font-size:16px;line-height:1.6;color:#555;">{profile_data.get("bio", "Пока ничего не написал...")}</p>
                <h3 style="margin:30px 0 20px 0;color:#333;">🎮 Любимые игры</h3>
                <ul style="font-size:16px;">{ "".join([f"<li style='margin:8px 0;color:#555;'>{game}</li>" for game in profile_data.get("games", [])]) or "<li style='color:#999;'>Пока не указаны</li>" }</ul>
            </div>
            <div>
                <h3 style="margin-bottom:20px;color:#333;">🏆 Достижения</h3>
                <ul style="font-size:16px;">{ "".join([f"<li style='margin:8px 0;color:#555;'>{ach}</li>" for ach in profile_data.get("achievements", [])]) or "<li style='color:#999;'>Пока нет достижений</li>" }</ul>
                <h3 style="margin:30px 0 20px 0;color:#333;">📅 Дата регистрации</h3>
                <p style="font-size:18px;color:#007bff;">{profile_data.get("join_date", "Неизвестно")}</p>
            </div>
        </div>
        <div style="margin-top:50px;text-align:center;">
            <a href="/" style="background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:20px;font-weight:bold;">🏠 На главную</a>
        </div>
    </div></body></html>
    '''

@app.route('/chat')
def chat():
    current_user = session.get('user')
    if not current_user:
        return redirect(url_for('login'))
    return '<h1>💬 Чат (временно отключён)</h1><a href="/">🏠</a>'

@app.route('/community')
def community():
    return '''
    <h1 style="text-align:center;padding:100px 20px;font-size:48px;">💬 Сообщество</h1>
    <p style="text-align:center;font-size:24px;"><a href="https://t.me/ssylkanatelegramkanalyznaikin" style="color:#0088cc;">Telegram канал</a></p>
    <p style="text-align:center;"><a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:20px;">🏠 Главная</a></p>
    '''

@app.route('/admin')
def admin():
    current_user = session.get('user')
    if not current_user or not users.get(current_user, {}).get('admin'):
        return '<h1 style="color:red;">❌ Только админы!</h1>'
    return '''
    <h1>🔧 Админка (временно)</h1>
    <a href="/" style="background:#28a745;color:white;padding:15px 30px;border-radius:10px;">🏠 Главная</a>
    '''

@app.before_request
def update_activity():
    current_user = session.get('user')
    if current_user:
        user_activity[current_user] = get_timestamp()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
