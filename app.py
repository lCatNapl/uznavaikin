from flask import Flask, request, redirect, url_for, session, render_template_string
from datetime import datetime
import time
import os
import traceback

app = Flask(__name__, static_folder='static')
app.secret_key = 'uznavaykin-secret-2026'

# ДАННЫЕ
users = {
    'CatNap': {'password': '120187', 'role': 'premium', 'admin': True},
    'Назар': {'password': '120187', 'role': 'premium', 'admin': True}
}
user_profiles = {}
user_roles = {}
user_activity = {}
chat_messages = []
moderators = {}
mutes = {}
catalog = {
    'Каталог': {
        'Minecraft': {},
        'World of Tanks': {}
    }
}

def get_timestamp(): return time.time()
def get_role_display(username):
    if users.get(username, {}).get('admin'): return 'Администратор'
    role = user_roles.get(username, 'start')
    return {'vip': 'VIP', 'premium': 'Premium'}.get(role, 'Start')

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'admin': 0}
    now = get_timestamp()
    for username in list(users.keys()):
        if username in user_activity and now - user_activity[username] < 300:
            stats['online'] += 1
            role = user_roles.get(username, 'start')
            if now - user_activity[username] > 60: stats['afk'] += 1
            elif users.get(username, {}).get('admin'): stats['admin'] += 1
            elif role == 'premium': stats['premium'] += 1
            elif role == 'vip': stats['vip'] += 1
            else: stats['start'] += 1
    return stats

def is_muted(username):
    if username in mutes and get_timestamp() < mutes[username]: return True
    if username in mutes: del mutes[username]
    return False

def is_moderator(username):
    if username in moderators and get_timestamp() < moderators[username]: return True
    if username in moderators: del moderators[username]
    return False

# Error handler
@app.errorhandler(500)
def internal_error(error):
    return f'''
    <!DOCTYPE html>
    <html><head><title>Ошибка</title>
    <style>body{{font-family:Arial;padding:50px;background:#f8f9fa;text-align:center;}}
    .error-card{{background:white;max-width:600px;margin:auto;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}}
    </style></head>
    <body>
    <div class="error-card">
        <h1 style="color:#dc3545;">🚨 Internal Server Error</h1>
        <p>Произошла ошибка на сервере. Попробуйте обновить страницу.</p>
        <a href="/" style="background:#007bff;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block;">🏠 На главную</a>
    </div>
    </body></html>
    ''', 500

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        current_user = session.get('user', '')
        stats = calculate_stats()
        
        if request.method == 'POST' and current_user and not is_muted(current_user):
            message = request.form.get('message', '').strip()
            if message.startswith('/profile '):
                target = message[9:].strip()
                if target in users:
                    return redirect(f'/profile/{target}')
            elif message:
                chat_messages.append({
                    'user': current_user, 
                    'text': message, 
                    'time': get_timestamp(), 
                    'role': get_role_display(current_user)
                })
                chat_messages[:] = chat_messages[-100:]
        
        # HTML ГЛАВНАЯ (упрощенный)
        html_header = '''
<!DOCTYPE html>
<html><head><title>Узнавайкин</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:10px;}
.container{max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden;}
.header{padding:25px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:15px;padding:20px;background:#f8f9fa;}
.stat-card{background:#fff;padding:15px;border-radius:12px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.1);}
.nav{display:flex;flex-wrap:wrap;gap:10px;padding:20px;background:#f8f9fa;justify-content:center;}
.nav-btn{padding:12px 20px;background:#007bff;color:white;text-decoration:none;border-radius:10px;font-weight:bold;flex:1;max-width:150px;text-align:center;}
.nav-btn:hover{background:#0056b3;}
.admin-btn{background:#dc3545;max-width:none;flex:0 0 auto;}
#chat-container{max-width:800px;margin:20px auto;background:#f8f9fa;border-radius:15px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
#chat-messages{max-height:400px;overflow-y:auto;padding:20px;background:#e8f5e8;}
.chat-msg{margin-bottom:15px;padding:15px;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
.chat-header{font-weight:bold;color:#2e7d32;font-size:14px;margin-bottom:8px;}
.chat-mute{background:#ffcdd2;border-left:4px solid #f44336;}
#chat-input{padding:20px;border-top:1px solid #ddd;background:white;}
input[type="text"]{width:70%;padding:12px;border:2px solid #4caf50;border-radius:8px;font-size:16px;}
button[type="submit"]{width:27%;padding:12px;background:#4caf50;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px;margin-left:3%;}
@media (max-width:768px){.stats{grid-template-columns:repeat(3,1fr);}.nav{flex-direction:column;}.nav-btn{max-width:none;}input[type="text"]{width:100%;margin-bottom:10px;}button[type="submit"]{width:100%;margin-left:0;}}</style></head>
<body><div class="container">
        '''
        
        if current_user:
            html_header += f'<div class="header"><h1>🏠 Узнавайкин</h1><p>👤 <b>{current_user}</b> | <span style="color:gold;">{get_role_display(current_user)}</span></p></div>'
        else:
            html_header += '<div class="header"><h1>🏠 Узнавайкин</h1><p>Добро пожаловать!</p></div>'
        
        html_stats = f'''
<div class="stats">
    <div class="stat-card"><b>{stats['online']}</b><br>Онлайн</div>
    <div class="stat-card"><b>{stats['afk']}</b><br>АФК</div>
    <div class="stat-card"><b>{stats['start']}</b><br>Start</div>
    <div class="stat-card"><b>{stats['vip']}</b><br>VIP</div>
    <div class="stat-card"><b>{stats['premium']}</b><br>Premium</div>
    <div class="stat-card"><b>{stats['admin']}</b><br>Админы</div>
</div>
<div id="chat-container"><div id="chat-messages">
        '''
        
        for msg in chat_messages[-20:]:
            mute_class = 'chat-mute' if is_muted(msg['user']) else ''
            html_stats += f'''
<div class="chat-msg {mute_class}">
    <div class="chat-header">[{datetime.fromtimestamp(msg["time"]).strftime("%H:%M")}] <b>{msg["user"]}</b> <span style="color:#666;">({msg["role"]})</span></div>
    <div>{msg["text"]}</div>
</div>'''
        
        html_chat = '</div>'
        if current_user:
            if is_muted(current_user):
                html_chat += '<div style="padding:20px;text-align:center;color:#c62828;font-size:18px;">🔇 Вы замучены</div>'
            else:
                html_chat += '''
<div id="chat-input">
    <form method="post">
        <input type="text" name="message" placeholder="/profile @username или сообщение" maxlength="200" required>
        <button type="submit">Отправить</button>
    </form>
</div>'''
        
        html_chat += '</div><div class="nav">'
        html_nav = '''
<a href="/catalog" class="nav-btn">📁 КАТАЛОГ</a>
<a href="/profiles" class="nav-btn">👥 ПРОФИЛИ</a>
<a href="/community" class="nav-btn">📢 TG</a>'''
        
        if current_user:
            html_nav += f'<a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>'
            if users.get(current_user, {}).get('admin') or is_moderator(current_user):
                html_nav += '<a href="/admin" class="nav-btn admin-btn">🔧 Админ</a>'
            html_nav += '<a href="/logout" class="nav-btn">🚪 Выход</a>'
        else:
            html_nav += '<a href="/login" class="nav-btn">🔐 Войти</a>'
        
        html_footer = '</div></div></body></html>'
        
        return html_header + html_stats + html_chat + html_nav + html_footer
        
    except Exception:
        return "Ошибка на главной", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        session['user'] = username
        if username not in user_roles: user_roles[username] = 'start'
        if username not in users:
            users[username] = {'password': password, 'role': 'start', 'admin': False}
            user_profiles[username] = {'bio': '', 'status': 'Онлайн'}
        user_activity[username] = get_timestamp()
        return redirect(url_for('index'))
    return '''
<!DOCTYPE html><html><head><title>Вход</title><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:40px;display:flex;align-items:center;justify-content:center;}
form{max-width:400px;width:100%;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);}input{width:100%;padding:15px;margin:10px 0;border:2px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box;}
button{width:100%;padding:18px;background:#4ecdc4;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;}h1{color:white;text-align:center;margin-bottom:30px;}</style></head>
<body><h1>🔐 Узнавайкин</h1><form method="post">
<input name="username" placeholder="Логин" required><input name="password" type="password" placeholder="Пароль" required><button>ВОЙТИ / РЕГИСТРАЦИЯ</button></form></body></html>
    '''

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog(path=''):
    try:
        current_path = [p for p in path.split('/') if p.strip()]
        current_folder = catalog
        
        for part in current_path:
            if part in current_folder and isinstance(current_folder[part], dict):
                current_folder = current_folder[part]
            else:
                current_folder = {}
                break
        
        breadcrumbs = '<a href="/catalog">Каталог</a>'
        for i, part in enumerate(current_path):
            path_str = '/'.join(current_path[:i+1])
            breadcrumbs += f' → <a href="/catalog/{path_str}">{part}</a>'
        
        content = ''
        if current_folder:
            folders = [k for k in current_folder if isinstance(current_folder[k], dict)]
            items = [k for k in current_folder if not isinstance(current_folder[k], dict)]
            
            if folders or items:
                content = '<div class="grid">'
                for folder in sorted(folders):
                    full_path = '/catalog/' + '/'.join(current_path + [folder])
                    content += f'<a href="{full_path}" class="folder-card"><h3 style="margin:0 0 10px 0;color:#2196f3;">📁 {folder}</h3><p style="margin:0;color:#666;">Папка</p></a>'
                for item in sorted(items):
                    item_data = current_folder[item]
                    photo_html = f'<img src="/static/{item_data.get("photo", "")}" style="max-width:100%;border-radius:10px;margin-top:15px;" alt="Фото">' if item_data.get("photo") else ''
                    content += f'<div class="item-card"><h3 class="item-title">{item}</h3><p><b>Нахождение:</b> {item_data.get("location", "Каталог")}</p><div class="item-info">{item_data.get("info", "")}</div>{photo_html}</div>'
                content += '</div>'
            else:
                content = '<div class="empty-folder">📭 Папка пустая</div>'
        else:
            content = '<div class="empty-folder"><a href="/catalog">📁 Вернуться в Каталог</a></div>'
        
        return f'''
<!DOCTYPE html><html><head><title>Каталог</title><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{{font-family:Arial,sans-serif;padding:20px;background:#f8f9fa;}}.container{{max-width:1200px;margin:0 auto;background:white;border-radius:20px;padding:30px;box-shadow:0 15px 35px rgba(0,0,0,0.1);}}.breadcrumbs{{margin:30px 0;padding:20px;background:#e9ecef;border-radius:15px;font-size:16px;}}.breadcrumbs a{{color:#007bff;text-decoration:none;}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}.folder-card{{background:#e3f2fd;padding:25px;border-radius:20px;border-left:5px solid #2196f3;text-decoration:none;display:block;text-align:center;transition:all 0.3s;}}.folder-card:hover{{transform:translateY(-5px);box-shadow:0 15px 30px rgba(0,0,0,0.2);}}.item-card{{background:#f3e5f5;padding:25px;border-radius:20px;border-left:5px solid #9c27b0;}}.item-title{{font-size:20px;font-weight:bold;margin-bottom:10px;color:#333;}}.item-info{{color:#666;line-height:1.6;}}.back-btn{{background:#007bff;color:white;padding:15px 30px;border-radius:12px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin:40px 0;}}.empty-folder{{text-align:center;color:#666;font-size:24px;margin:80px 0;padding:40px;background:#f8f9fa;border-radius:20px;border:2px dashed #ddd;}}@media (max-width:768px){{.grid{{grid-template-columns:1fr;gap:15px;}}.container{{padding:20px;margin:10px;border-radius:15px;}}}}</style></head>
<body><div class="container"><div class="breadcrumbs">📁 {breadcrumbs}</div>{content}<div style="text-align:center;"><a href="/" class="back-btn">🏠 Главная</a></div></div></body></html>
        '''
    except Exception:
        return "Ошибка в каталоге", 500

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user', '')
    if not (users.get(current_user, {}).get('admin') or is_moderator(current_user)):
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Нет доступа!</h1>'
    
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'mute':
                target = request.form['target'].strip()
                duration = float(request.form.get('duration', 5)) * 60
                reason = request.form['reason'].strip()
                if target in users and target != current_user:
                    mutes[target] = get_timestamp() + duration
                    chat_messages.append({
                        'user': current_user, 
                        'text': f'🔇 {target} замучен на {duration/60}мин {current_user}: {reason}', 
                        'time': get_timestamp(), 
                        'role': get_role_display(current_user)
                    })
            
            elif action == 'add_mod' and users.get(current_user, {}).get('admin'):
                target = request.form['target'].strip()
                duration = float(request.form['duration', 1]) * 3600
                if target in users:
                    moderators[target] = get_timestamp() + duration
            
            elif action == 'add_folder' and users.get(current_user, {}).get('admin'):
                folder_name = request.form['folder_name'].strip()
                parent_path = request.form.get('parent_path', 'Каталог')
                if folder_name:
                    parent_parts = [p for p in parent_path.split('/') if p.strip()]
                    parent_folder = catalog
                    for part in parent_parts:
                        parent_folder = parent_folder.get(part, {})
                    parent_folder[folder_name] = {}
            
            elif action == 'add_item' and users.get(current_user, {}).get('admin'):
                item_name = request.form['item_name'].strip()
                parent_path = request.form.get('parent_path', 'Каталог')
                location = request.form.get('location', 'Каталог')
                info = request.form['info'].strip()
                photo = request.form.get('photo', '')
                if item_name:
                    parent_parts = [p for p in parent_path.split('/') if p.strip()]
                    parent_folder = catalog
                    for part in parent_parts:
                        parent_folder = parent_folder.get(part, {})
                    parent_folder[item_name] = {'location': location, 'info': info, 'photo': photo}
        except Exception as e:
            pass  # Игнорируем ошибки админки
    
    can_add_mod = users.get(current_user, {}).get('admin')
    is_admin = users.get(current_user, {}).get('admin')
    
    return f'''
<!DOCTYPE html><html><head><title>Админка</title><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{{font-family:Arial,sans-serif;padding:20px;background:#f8f9fa;}}.container{{max-width:800px;margin:auto;background:white;border-radius:20px;padding:30px;box-shadow:0 15px 40px rgba(0,0,0,0.1);}}.section{{background:#f8f9fa;margin:25px 0;padding:30px;border-radius:16px;box-shadow:0 5px 20px rgba(0,0,0,0.08);}}.section h2{{color:#333;margin-bottom:20px;border-left:5px solid #28a745;padding-left:15px;}}input,textarea{{width:100%;padding:15px;margin:10px 0;border:2px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box;}}button{{width:100%;padding:18px;background:#28a745;color:white;border:none;border-radius:12px;font-size:16px;font-weight:bold;cursor:pointer;margin:10px 0;}}.back-btn{{background:#007bff;display:block;margin:40px auto;padding:20px 40px;max-width:300px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;text-align:center;}}</style></head>
<body><div class="container">
<h1 style="text-align:center;color:#333;margin-bottom:30px;">🔧 ПОЛНАЯ АДМИН ПАНЕЛЬ</h1>

<div class="section"><h2>🔇 МУТИТЬ ИГРОКА</h2><form method="post">
<input type="hidden" name="action" value="mute">
<input name="target" placeholder="Имя игрока" required>
<input name="duration" type="number" placeholder="Минуты" value="5" min="1">
<input name="reason" placeholder="Причина" required>
<button>🔇 ЗАМУТИТЬ</button></form></div>

{"""<div class="section"><h2>👮 ДАТЬ МОДЕРАТОРА</h2><form method="post">
<input type="hidden" name="action" value="add_mod">
<input name="target" placeholder="Имя игрока" required>
<input name="duration" type="number" placeholder="Часы" value="1" min="1">
<button>👮 НАЗНАЧИТЬ</button></form></div>""" if can_add_mod else ""}

{"""<div class="section"><h2>📁 ДОБАВИТЬ ПАПКУ</h2><form method="post">
<input type="hidden" name="action" value="add_folder">
<input name="folder_name" placeholder="Название папки" required>
<input name="parent_path" placeholder="Родитель (Каталог/Minecraft)" value="Каталог">
<button>📁 ДОБАВИТЬ</button></form></div>

<div class="section"><h2>📦 ДОБАВИТЬ ПРЕДМЕТ</h2><form method="post">
<input type="hidden" name="action" value="add_item">
<input name="item_name" placeholder="Название предмета" required>
<input name="parent_path" placeholder="Папка (Каталог)" value="Каталог">
<input name="location" placeholder="Нахождение" value="Каталог">
<textarea name="info" placeholder="Описание" rows="3"></textarea>
<input name="photo" placeholder="Фото (image.jpg)">
<button>📦 ДОБАВИТЬ</button></form></div>""" if is_admin else ""}

<a href="/" class="back-btn">🏠 Главная</a></div></body></html>
    '''

# Остальные роуты без изменений (profiles, profile, community, logout)
@app.route('/profiles')
def profiles():
    profiles_html = ''.join([f'<div style="background:white;padding:25px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);text-align:center;"><h3>{user}</h3><a href="/profile/{user}" style="display:inline-block;padding:12px 24px;background:#007bff;color:white;border-radius:10px;font-weight:bold;">👁️ Профиль</a></div>' for user in sorted(users)])
    return f'<!DOCTYPE html><html><head><title>Профили</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:30px;background:#f0f2f5;}}.profiles-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}.back-btn{{background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;display:block;margin:50px auto;max-width:300px;text-align:center;}}@media (max-width:768px){{.profiles-grid{{grid-template-columns:1fr;}}}}</style></head><body><h1 style="text-align:center;margin-bottom:40px;">👥 Все профили</h1><div class="profiles-grid">{profiles_html}</div><a href="/" class="back-btn">🏠 Главная</a></body></html>'

@app.route('/profile/<username>')
def profile(username):
    if username not in users:
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Пользователь не найден</h1><a href="/" style="display:block;text-align:center;margin-top:20px;background:#007bff;color:white;padding:15px 30px;border-radius:10px;font-size:18px;text-decoration:none;margin:auto;max-width:300px;">🏠 Главная</a>'
    profile_data = user_profiles.get(username, {'status': 'Онлайн'})
    role_display = get_role_display(username)
    role_color = 'red' if users[username].get('admin') else 'gold'
    return f'<html><head><title>Профиль {username}</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:40px;background:#f0f2f5;}}.profile-card{{background:white;max-width:800px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);text-align:center;}}.role-badge{{padding:15px 30px;background:{role_color};color:white;border-radius:25px;font-size:20px;font-weight:bold;display:inline-block;margin:20px 0;}}.status{{font-size:18px;color:#666;margin:30px 0;padding:20px;background:#e8f5e8;border-radius:15px;}}.back-btn{{background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:18px;font-weight:bold;display:inline-block;margin-top:40px;}}</style></head><body><div class="profile-card"><h1>{username}</h1><div class="role-badge">{role_display}</div><div class="status">{profile_data.get("status", "Онлайн")}</div><a href="/" class="back-btn">🏠 Главная</a></div></body></html>'

@app.route('/community')
def community():
    return '''<!DOCTYPE html><html><head><title>Сообщество</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:100px 20px;text-align:center;background:#f8f9fa;}}h1{{font-size:48px;margin-bottom:30px;}}a[href="https://t.me/ssylkanatelegramkanalyznaikin"]{{font-size:28px;color:#0088cc;text-decoration:none;font-weight:bold;}}.back-btn{{background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin-top:50px;}}</style></head><body><h1>💬 Сообщество</h1><p><a href="https://t.me/ssylkanatelegramkanalyznaikin">Telegram канал</a></p><a href="/" class="back-btn">🏠 Главная</a></body></html>'''

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.before_request
def update_activity():
    user = session.get('user')
    if user:
        user_activity[user] = get_timestamp()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
