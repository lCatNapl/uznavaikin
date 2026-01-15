from flask import Flask, request, redirect, url_for, session
from datetime import datetime
import time
import os

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

# 🔥 ПОЛНЫЙ КАТАЛОГ С ВЕЩАМИ
catalog = {
    'Каталог': {
        'Minecraft': {
            'Кремний': {'location': 'Каталог/Minecraft', 'info': 'Для крафта электроники', 'photo': ''},
            'Железная руда': {'location': 'Каталог/Minecraft', 'info': 'Добывается киркой, плавится в железо', 'photo': ''}
        },
        'World of Tanks': {
            'Т-34': {'location': 'Каталог/World of Tanks', 'info': 'СССР, 6 уровень, отличная мобильность', 'photo': ''},
            'Тигр': {'location': 'Каталог/World of Tanks', 'info': 'Германия, 7 уровень, мощная броня', 'photo': ''}
        }
    }
}

def get_timestamp(): return time.time()
def get_role_display(username):
    if users.get(username, {}).get('admin'): return '👑 Администратор'
    role = user_roles.get(username, 'start')
    return {'vip': '⭐ VIP', 'premium': '💎 Premium'}.get(role, '📚 Start')

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'admin': 0}
    now = get_timestamp()
    for username in users:
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

# 🔥 ФУНКЦИИ КАТАЛОГА
def add_item(path, name, info='', location='', photo=''):
    """Добавить предмет"""
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if not parts: return False
    
    parent = catalog['Каталог']
    for part in parts[:-1]:
        if part not in parent: parent[part] = {}
        parent = parent[part]
    
    parent[name] = {'location': location or f"{path}/{name}", 'info': info, 'photo': photo}
    return True

def add_folder(path, name):
    """Добавить папку"""
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if not parts: return False
    
    parent = catalog['Каталог']
    for part in parts:
        if part not in parent: parent[part] = {}
        parent = parent[part]
    return True

def delete_item(path):
    """Удалить предмет/папку"""
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if len(parts) < 1: return False
    
    parent = catalog['Каталог']
    for i in range(len(parts)-1):
        if parts[i] not in parent or not isinstance(parent[parts[i]], dict):
            return False
        parent = parent[parts[i]]
    
    if parts[-1] in parent:
        del parent[parts[-1]]
        return True
    return False

def get_catalog_content(path=''):
    """Получить содержимое каталога"""
    parts = [p.strip() for p in path.split('/') if p.strip()]
    folder = catalog['Каталог']
    
    for part in parts:
        if part in folder and isinstance(folder[part], dict):
            folder = folder[part]
        else:
            return {'error': 'Папка не найдена'}
    
    folders = []
    items = []
    for key, value in folder.items():
        if isinstance(value, dict) and value:  # Папка
            folders.append(key)
        elif isinstance(value, dict):  # Пустая папка
            folders.append(key)
        else:  # Предмет
            items.append((key, value))
    
    return {'folders': folders, 'items': items, 'path': path}

@app.route('/', methods=['GET', 'POST'])
def index():
    current_user = session.get('user', '')
    stats = calculate_stats()
    
    if request.method == 'POST' and current_user and not is_muted(current_user):
        message = request.form.get('message', '').strip()
        if message.startswith('/profile '):
            target = message[9:].strip()
            if target in users: return redirect(f'/profile/{target}')
        elif message:
            chat_messages.append({
                'user': current_user, 'text': message, 'time': get_timestamp(), 
                'role': get_role_display(current_user)
            })
            chat_messages[:] = chat_messages[-100:]
    
    html = '''<!DOCTYPE html>
<html><head><title>Узнавайкин</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* {margin:0;padding:0;box-sizing:border-box;}
body {font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:10px;}
.container {max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden;}
.header {padding:25px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}
.stats {display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:15px;padding:20px;background:#f8f9fa;}
.stat-card {background:#fff;padding:15px;border-radius:12px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.1);}
.nav {display:flex;flex-wrap:wrap;gap:10px;padding:20px;background:#f8f9fa;justify-content:center;}
.nav-btn {padding:12px 20px;background:#007bff;color:white;text-decoration:none;border-radius:10px;font-weight:bold;flex:1;max-width:150px;text-align:center;}
.nav-btn:hover {background:#0056b3;}
.admin-btn {background:#dc3545;max-width:none;flex:0 0 auto;}
#chat-container {max-width:800px;margin:20px auto;background:#f8f9fa;border-radius:15px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
#chat-messages {max-height:400px;overflow-y:auto;padding:20px;background:#e8f5e8;}
.chat-msg {margin-bottom:15px;padding:15px;background:white;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
.chat-header {font-weight:bold;color:#2e7d32;font-size:14px;margin-bottom:8px;}
.chat-mute {background:#ffcdd2;border-left:4px solid #f44336;}
#chat-input {padding:20px;border-top:1px solid #ddd;background:white;}
input[type="text"] {width:70%;padding:12px;border:2px solid #4caf50;border-radius:8px;font-size:16px;}
button[type="submit"] {width:27%;padding:12px;background:#4caf50;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px;margin-left:3%;}
@media (max-width:768px) {.stats {grid-template-columns:repeat(3,1fr);} .nav {flex-direction:column;} .nav-btn {max-width:none;} input[type="text"] {width:100%;margin-bottom:10px;} button[type="submit"] {width:100%;margin-left:0;}}
</style></head>
<body><div class="container">'''
    
    if current_user:
        html += f'<div class="header"><h1>🏠 Узнавайкин</h1><p>👤 <b>{current_user}</b> | <span style="color:gold;">{get_role_display(current_user)}</span></p></div>'
    else:
        html += '<div class="header"><h1>🏠 Узнавайкин</h1><p>Добро пожаловать!</p></div>'
    
    # Продолжение HTML остается как в v25.0 (статистика, чат, навигация)
    html += f'''
<div class="stats">
    <div class="stat-card"><b>{stats['online']}</b><br>Онлайн</div>
    <div class="stat-card"><b>{stats['afk']}</b><br>АФК</div>
    <div class="stat-card"><b>{stats['start']}</b><br>Start</div>
    <div class="stat-card"><b>{stats['vip']}</b><br>VIP</div>
    <div class="stat-card"><b>{stats['premium']}</b><br>Premium</div>
    <div class="stat-card"><b>{stats['admin']}</b><br>Админы</div>
</div>
<div id="chat-container">
    <div id="chat-messages">'''
    
    for msg in chat_messages[-20:]:
        mute_class = 'chat-mute' if is_muted(msg['user']) else ''
        html += f'''
    <div class="chat-msg {mute_class}">
        <div class="chat-header">[{datetime.fromtimestamp(msg["time"]).strftime("%H:%M")}] <b>{msg["user"]}</b> <span style="color:#666;">({msg["role"]})</span></div>
        <div>{msg["text"]}</div>
    </div>'''
    
    html += '</div>'
    
    if current_user:
        if is_muted(current_user):
            html += '<div style="padding:20px;text-align:center;color:#c62828;font-size:18px;">🔇 Вы замучены</div>'
        else:
            html += '''
    <div id="chat-input">
        <form method="post">
            <input type="text" name="message" placeholder="/profile @username или сообщение" maxlength="200" required>
            <button type="submit">Отправить</button>
        </form>
    </div>'''
    
    html += '''
</div>
<div class="nav">
    <a href="/catalog" class="nav-btn">📁 КАТАЛОГ</a>
    <a href="/profiles" class="nav-btn">👥 ПРОФИЛИ</a>
    <a href="/community" class="nav-btn">📢 TG</a>'''
    
    if current_user:
        html += f'<a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>'
        if users.get(current_user, {}).get('admin'):
            html += '<a href="/admin" class="nav-btn admin-btn">🔧 Админ</a>'
        html += '<a href="/logout" class="nav-btn">🚪 Выход</a>'
    else:
        html += '<a href="/login" class="nav-btn">🔐 Войти</a>'
    
    html += '</div></div></body></html>'
    return html

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog(path=''):
    content = get_catalog_content(path)
    
    if 'error' in content:
        return f'''<!DOCTYPE html><html><body style="padding:50px;font-family:Arial;text-align:center;background:#f8f9fa;">
<h1 style="color:#dc3545;">❌ {content["error"]}</h1>
<a href="/catalog" style="background:#007bff;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block;">📁 В Каталог</a>
<a href="/" style="background:#28a745;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block;margin-left:10px;">🏠 Главная</a>
</body></html>'''
    
    breadcrumbs = '📁 <a href="/catalog">Каталог</a>'
    parts = [p.strip() for p in path.split('/') if p.strip()]
    temp_path = []
    for part in parts:
        temp_path.append(part)
        path_str = '/'.join(temp_path)
        breadcrumbs += f' → <a href="/catalog/{path_str}">{part}</a>'
    
    content_html = '<div class="grid">'
    
    # ПАПКИ
    for folder in sorted(content['folders']):
        content_html += f'<a href="/catalog/{path}/{folder}" class="folder-card"><h3 style="margin:0 0 10px 0;color:#2196f3;">📁 {folder}</h3><p style="margin:0;color:#666;">Папка</p></a>'
    
    # ПРЕДМЕТЫ
    for item_name, item_data in sorted(content['items']):
        photo_html = ''  # Пока без фото
        content_html += f'''
        <div class="item-card">
            <h3 class="item-title">{item_name}</h3>
            <p><b>📍 Нахождение:</b> {item_data.get("location", "Каталог")}</p>
            <p><b>ℹ️ Инфо:</b> {item_data.get("info", "—")}</p>
            {photo_html}
        </div>'''
    
    content_html += '</div>'
    
    if not content['folders'] and not content['items']:
        content_html = '<div class="empty-folder">📭 Папка пустая</div>'
    
    return f'''<!DOCTYPE html>
<html><head><title>Каталог {path or ""}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{{font-family:Arial,sans-serif;padding:20px;background:#f8f9fa;}}.container{{max-width:1200px;margin:0 auto;background:white;border-radius:20px;padding:30px;box-shadow:0 15px 35px rgba(0,0,0,0.1);}}.breadcrumbs{{margin:30px 0;padding:20px;background:#e9ecef;border-radius:15px;font-size:16px;}}.breadcrumbs a{{color:#007bff;text-decoration:none;}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}.folder-card{{background:#e3f2fd;padding:25px;border-radius:20px;border-left:5px solid #2196f3;text-decoration:none;display:block;text-align:center;transition:all 0.3s;}}.folder-card:hover{{transform:translateY(-5px);box-shadow:0 15px 30px rgba(0,0,0,0.2);}}.item-card{{background:#f3e5f5;padding:25px;border-radius:20px;border-left:5px solid #9c27b0;}}.item-title{{font-size:20px;font-weight:bold;margin-bottom:10px;color:#333;}}.back-btn{{background:#007bff;color:white;padding:15px 30px;border-radius:12px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin:40px 0;}}.empty-folder{{text-align:center;color:#666;font-size:24px;margin:80px 0;padding:40px;background:#f8f9fa;border-radius:20px;border:2px dashed #ddd;}}@media (max-width:768px){{.grid{{grid-template-columns:1fr;gap:15px;}}.container{{padding:20px;margin:10px;border-radius:15px;}}}}</style></head>
<body><div class="container">
    <div class="breadcrumbs">{breadcrumbs}</div>
    {content_html}
    <div style="text-align:center;">
        <a href="/catalog" class="back-btn">📁 Каталог</a>
        <a href="/" class="back-btn" style="background:#28a745;margin-left:10px;">🏠 Главная</a>
    </div>
</div></body></html>'''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user', '')
    if not users.get(current_user, {}).get('admin'):
        return '<h1 style="color:red;text-align:center;padding:100px;font-family:Arial;">❌ Нет доступа!</h1>'
    
    message = ''
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 🔇 МУТ
        if action == 'mute':
            target = request.form['target'].strip()
            duration = float(request.form.get('duration', 5)) * 60
            mutes[target] = get_timestamp() + duration
            message = f'✅ {target} замучен на {duration/60} мин!'
        
        # ➕ ДОБАВИТЬ ПРЕДМЕТ
        elif action == 'add_item':
            path = request.form['path'].strip()
            name = request.form['name'].strip()
            info = request.form['info'].strip()
            if add_item(path, name, info):
                message = f'✅ Добавлен: {path}/{name}'
            else:
                message = '❌ Ошибка добавления!'
        
        # ➕ ДОБАВИТЬ ПАПКУ
        elif action == 'add_folder':
            path = request.form['path'].strip()
            name = request.form['name'].strip()
            if add_folder(path, name):
                message = f'✅ Создана папка: {path}/{name}'
            else:
                message = '❌ Ошибка создания!'
        
        # 🗑️ УДАЛИТЬ
        elif action == 'delete':
            path = request.form['path'].strip()
            if delete_item(path):
                message = f'✅ Удален: {path}'
            else:
                message = '❌ Не найдено для удаления!'
    
    return f'''<!DOCTYPE html>
<html><head><title>🔧 Админка v27</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{{font-family:Arial,sans-serif;padding:20px;background:#f8f9fa;}}.container{{max-width:900px;margin:auto;background:white;border-radius:20px;padding:30px;box-shadow:0 15px 40px rgba(0,0,0,0.1);}}.section{{background:#f8f9fa;margin:25px 0;padding:25px;border-radius:16px;box-shadow:0 5px 20px rgba(0,0,0,0.08);}}h2{{color:#333;margin-bottom:20px;border-left:5px solid #28a745;padding-left:15px;}}input{{width:100%;padding:12px;margin:8px 0;border:2px solid #ddd;border-radius:8px;font-size:16px;box-sizing:border-box;}}button{{width:100%;padding:15px;margin:10px 0;border:none;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer;}}.btn-mute{{background:#ffcdd2;color:#d32f2f;}}.btn-add{{background:#4caf50;color:white;}}.btn-delete{{background:#dc3545;color:white;}}.message{{padding:15px;margin:20px 0;border-radius:10px;font-weight:bold;text-align:center;}}.catalog-list{{background:#e3f2fd;padding:15px;border-radius:10px;max-height:200px;overflow:auto;margin:15px 0;}}.back-btn{{background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;display:block;margin:40px auto;max-width:300px;text-align:center;}}</style></head>
<body><div class="container">
<h1 style="text-align:center;color:#333;margin-bottom:30px;">🔧 АДМИН ПАНЕЛЬ v27</h1>

{message and f'<div class="message" style="background:#d4edda;color:#155724;border:1px solid #c3e6cb;">{message}</div>' or ''}

<!-- 🔇 МУТ -->
<div class="section"><h2>🔇 МУТИТЬ ИГРОКА</h2>
<form method="post"><input type="hidden" name="action" value="mute">
<input name="target" placeholder="Имя игрока" required>
<input name="duration" type="number" value="5" placeholder="Минуты" min="1">
<button class="btn-mute">🔇 ЗАМУТИТЬ</button></form></div>

<!-- ➕ ДОБАВИТЬ ПРЕДМЕТ -->
<div class="section"><h2>➕ ДОБАВИТЬ ПРЕДМЕТ</h2>
<form method="post"><input type="hidden" name="action" value="add_item">
<input name="path" placeholder="Путь (Minecraft)" required>
<input name="name" placeholder="Название (Кремний)" required>
<input name="info" placeholder="Описание" required>
<button class="btn-add">➕ ДОБАВИТЬ</button></form></div>

<!-- ➕ ДОБАВИТЬ ПАПКУ -->
<div class="section"><h2>📁 ДОБАВИТЬ ПАПКУ</h2>
<form method="post"><input type="hidden" name="action" value="add_folder">
<input name="path" placeholder="Путь (Каталог)" required>
<input name="name" placeholder="Название (CS2)" required>
<button class="btn-add">📁 СОЗДАТЬ</button></form></div>

<!-- 🗑️ УДАЛИТЬ -->
<div class="section"><h2>🗑️ УДАЛИТЬ</h2>
<form method="post"><input type="hidden" name="action" value="delete">
<input name="path" placeholder="Полный путь (Каталог/Minecraft/Кремний)" required>
<button class="btn-delete">🗑️ УДАЛИТЬ</button></form>

<div class="catalog-list">
<h3>📋 Текущий каталог:</h3>
<pre>{str(catalog.get("Каталог", {}))[:500]}...</pre>
</div></div>

<a href="/" class="back-btn">🏠 Главная</a>
</div></body></html>'''

# Остальные роуты остаются как в v25.0 (login, profiles, profile, community, logout)

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
    return '''<!DOCTYPE html>
<html><head><title>Вход</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:40px;display:flex;align-items:center;justify-content:center;}
form{max-width:400px;width:100%;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);}input{width:100%;padding:15px;margin:10px 0;border:2px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box;}
button{width:100%;padding:18px;background:#4ecdc4;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;}h1{color:white;text-align:center;margin-bottom:30px;}</style></head>
<body><h1>🔐 Узнавайкин</h1>
<form method="post">
    <input name="username" placeholder="Логин" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button>ВОЙТИ / РЕГИСТРАЦИЯ</button>
</form></body></html>'''

@app.route('/profiles')
def profiles():
    profiles_html = ''.join([f'<div style="background:white;padding:25px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);text-align:center;"><h3>{user}</h3><a href="/profile/{user}" style="display:inline-block;padding:12px 24px;background:#007bff;color:white;border-radius:10px;font-weight:bold;">👁️ Профиль</a></div>' for user in sorted(users)])
    return f'''<!DOCTYPE html><html><head><title>Профили</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:30px;background:#f0f2f5;}}.profiles-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}.back-btn{{background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;display:block;margin:50px auto;max-width:300px;text-align:center;}}@media (max-width:768px){{.profiles-grid{{grid-template-columns:1fr;}}}}</style></head><body><h1 style="text-align:center;margin-bottom:40px;">👥 Все профили</h1><div class="profiles-grid">{profiles_html}</div><a href="/" class="back-btn">🏠 Главная</a></body></html>'''

@app.route('/profile/<username>')
def profile(username):
    if username not in users:
        return '<!DOCTYPE html><html><body style="background:#f0f2f5;padding:100px;text-align:center;font-family:Arial;"><h1 style="color:#dc3545;">❌ Пользователь не найден</h1><a href="/" style="background:#007bff;color:white;padding:15px 30px;border-radius:10px;font-size:18px;text-decoration:none;display:inline-block;margin-top:20px;">🏠 Главная</a></body></html>'
    
    profile_data = user_profiles.get(username, {'status': 'Онлайн'})
    role_display = get_role_display(username)
    role_color = 'red' if users[username].get('admin') else 'gold'
    return f'''<!DOCTYPE html><html><head><title>Профиль {username}</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:40px;background:#f0f2f5;}}.profile-card{{background:white;max-width:800px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);text-align:center;}}.role-badge{{padding:15px 30px;background:{role_color};color:white;border-radius:25px;font-size:20px;font-weight:bold;display:inline-block;margin:20px 0;}}.status{{font-size:18px;color:#666;margin:30px 0;padding:20px;background:#e8f5e8;border-radius:15px;}}.back-btn{{background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:18px;font-weight:bold;display:inline-block;margin-top:40px;}}</style></head><body><div class="profile-card"><h1>{username}</h1><div class="role-badge">{role_display}</div><div class="status">{profile_data.get("status", "Онлайн")}</div><a href="/" class="back-btn">🏠 Главная</a></div></body></html>'''

@app.route('/community')
def community():
    return '''<!DOCTYPE html><html><head><title>Сообщество</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{font-family:Arial,sans-serif;padding:100px 20px;text-align:center;background:#f8f9fa;}h1{font-size:48px;margin-bottom:30px;}a[href="https://t.me/ssylkanatelegramkanalyznaikin"]{font-size:28px;color:#0088cc;text-decoration:none;font-weight:bold;}.back-btn{background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin-top:50px;}</style></head><body><h1>💬 Сообщество</h1><p><a href="https://t.me/ssylkanatelegramkanalyznaikin">Telegram канал</a></p><a href="/" class="back-btn">🏠 Главная</a></body></html>'''

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.before_request
def update_activity():
    user = session.get('user')
    if user: user_activity[user] = get_timestamp()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
