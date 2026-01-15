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
minecraft_chat = []

# КАТАЛОГ (пустые папки)
catalog = {
    'Каталог': {
        'Minecraft': {},
        'World of Tanks': {}
    }
}

def get_timestamp():
    return time.time()

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'admin': 0}
    now = get_timestamp()
    for username in list(users.keys()):
        if username in user_activity and now - user_activity[username] < 300:
            stats['online'] += 1
            role = user_roles.get(username, 'start')
            if now - user_activity[username] > 60:
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
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Узнавайкин</title>
    <meta charset="utf-8">
    <style>*{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px;}
    .container{max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}
    .header{padding:30px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}
    .stats{display:flex;gap:15px;justify-content:center;padding:20px;background:#e9ecef;flex-wrap:wrap;}
    .stat-card{background:white;padding:15px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center;min-width:100px;}
    .nav{display:flex;justify-content:center;gap:10px;padding:20px;flex-wrap:wrap;}
    .nav-btn{padding:12px 25px;background:#007bff;color:white;text-decoration:none;border-radius:8px;font-weight:bold;}
    .nav-btn:hover{background:#0056b3;transform:translateY(-2px);}
    .admin-btn{background:#dc3545;}</style></head>
    <body>
    <div class="container">
    '''
    
    if current_user:
        role = user_roles.get(current_user, 'start')
        html += f'<div class="header"><h1>🏠 Узнавайкин</h1><p>👤 <b>{current_user}</b> | <span style="color:gold;">{role.upper()}</span></p></div>'
    else:
        html += '<div class="header"><h1>🏠 Узнавайкин</h1><p>Добро пожаловать!</p></div>'
    
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
        <a href="/profiles" class="nav-btn">👥 ПРОФИЛИ</a>
        <a href="/community" class="nav-btn">📢 TG</a>
    '''
    
    if current_user:
        html += f'<a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>'
        if users.get(current_user, {}).get('admin'):
            html += '<a href="/admin" class="nav-btn admin-btn">🔧 Админ</a>'
        html += '<a href="/logout" class="nav-btn">🚪 Выход</a>'
    else:
        html += '<a href="/login" class="nav-btn">🔐 Войти</a>'
    
    html += '</div></div></body></html>'
    return html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        session['user'] = username
        if username not in user_roles:
            user_roles[username] = 'start'
            if username not in users:
                users[username] = {'password': password, 'role': 'start', 'admin': False}
                user_profiles[username] = {'bio': '', 'achievements': [], 'join_date': '2026-01-15'}
        user_activity[username] = get_timestamp()
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html>
    <html><head><title>Вход</title>
    <style>body{font-family:Arial;padding:50px;text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);}
    form{max-width:400px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}</style></head>
    <body>
    <h1 style="color:white;margin-bottom:30px;">🔐 Узнавайкин</h1>
    <form method="post">
        <input name="username" placeholder="Логин" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <input name="password" type="password" placeholder="Пароль" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <button style="width:100%;padding:18px;background:#4ecdc4;color:white;border:none;border-radius:10px;font-size:20px;">ВОЙТИ / РЕГИСТРАЦИЯ</button>
    </form>
    <p style="margin-top:30px;color:white;">👑 Админы: CatNap, Назар</p>
    </body></html>
    '''

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog(path=''):
    current_path = path.split('/') if path else []
    
    # Построить путь
    current_folder = catalog
    for part in current_path:
        if part in current_folder:
            current_folder = current_folder[part]
        else:
            current_folder = {}
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Каталог</title>
    <meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#f8f9fa;}
    .container{max-width:1200px;margin:0 auto;}
    .breadcrumbs{margin:30px 0;font-size:18px;}
    .breadcrumbs a{color:#007bff;text-decoration:none;}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}
    .folder-card{background:#e3f2fd;padding:25px;border-radius:20px;border-left:5px solid #2196f3;cursor:pointer;transition:all 0.3s;}
    .folder-card:hover{transform:translateY(-5px);box-shadow:0 15px 30px rgba(0,0,0,0.2);}
    .item-card{background:#f3e5f5;padding:25px;border-radius:20px;border-left:5px solid #9c27b0;}
    .item-title{font-size:20px;font-weight:bold;margin-bottom:10px;color:#333;}
    .item-info{color:#666;line-height:1.6;}
    .back-btn{background:#007bff;color:white;padding:15px 30px;border-radius:12px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin:40px 0;}
    .minecraft-chat{background:#4caf50;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;margin:20px 0;}</style></head>
    <body>
    <div class="container">
    '''
    
    # Хлебные крошки
    html += '<div class="breadcrumbs">📁 '
    breadcrumb_path = ''
    html += '<a href="/catalog">Каталог</a>'
    for i, part in enumerate(current_path):
        breadcrumb_path += part + '/'
        html += f' → <a href="/catalog/{breadcrumb_path[:-1]}">{part}</a>'
    html += '</div>'
    
    # Чат только в Minecraft
    if current_path == ['Каталог', 'Minecraft']:
        html += '''
        <div class="minecraft-chat">
            <a href="/minecraft-chat" style="color:white;text-decoration:none;">💬 ЧАТ MINECRAFT</a>
        </div>
        '''
    
    # Содержимое папки
    if current_folder:
        folders = {k for k in current_folder.keys() if isinstance(current_folder[k], dict)}
        items = {k for k in current_folder.keys() if not isinstance(current_folder[k], dict)}
        
        if folders or items:
            html += '<div class="grid">'
            
            # Папки
            for folder_name in sorted(folders):
                full_path = '/catalog/' + '/'.join(current_path + [folder_name])
                html += f'''
                <a href="{full_path}" class="folder-card">
                    <h3 style="margin:0 0 10px 0;color:#2196f3;">📁 {folder_name}</h3>
                    <p style="margin:0;color:#666;">Папка</p>
                </a>
                '''
            
            # Предметы
            for item_name in sorted(items):
                item = current_folder[item_name]
                photo = item.get('photo', '')
                html += f'''
                <div class="item-card">
                    <h3 class="item-title">{item_name}</h3>
                    <p><b>Нахождение:</b> {item.get("location", "Каталог")}</p>
                    <div class="item-info">{item.get("info", "")}</div>
                    {f'<img src="/static/{photo}" style="max-width:100%;border-radius:10px;margin-top:15px;" alt="Фото">' if photo else ''}
                </div>
                '''
            
            html += '</div>'
        else:
            html += '<p style="text-align:center;color:#666;font-size:20px;margin:60px 0;">📭 Папка пустая</p>'
    else:
        html += '<p style="text-align:center;color:#666;font-size:20px;margin:60px 0;">📁 <a href="/catalog">Вернуться в Каталог</a></p>'
    
    html += '''
        <div style="text-align:center;">
            <a href="/" class="back-btn">🏠 Главная</a>
        </div>
    </div></body></html>
    '''
    return html

@app.route('/minecraft-chat', methods=['GET', 'POST'])
def minecraft_chat():
    current_user = session.get('user')
    if not current_user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form['message'].strip()
        if message and len(message) <= 200:
            minecraft_chat.append({
                'user': current_user,
                'text': message,
                'time': get_timestamp()
            })
            minecraft_chat[:] = minecraft_chat[-50:]
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Minecraft Чат</title>
    <meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#4caf50;}
    #chat{max-width:800px;margin:0 auto;background:white;border-radius:20px;overflow:hidden;box-shadow:0 15px 40px rgba(0,0,0,0.3);}
    #messages{max-height:400px;overflow-y:auto;padding:20px;background:#e8f5e8;}
    .msg{margin-bottom:15px;padding:12px;background:#c8e6c9;border-radius:10px;}
    .msg-header{font-weight:bold;color:#2e7d32;font-size:14px;margin-bottom:5px;}
    #input{padding:20px;border-top:1px solid #ddd;}
    input{width:70%;padding:10px;border:2px solid #4caf50;border-radius:8px;}
    button{width:28%;padding:10px;background:#4caf50;color:white;border:none;border-radius:8px;cursor:pointer;}</style></head>
    <body>
    <div id="chat">
        <div style="padding:20px;background:#2e7d32;color:white;text-align:center;">
            <h2>🟩 MINECRAFT ЧАТ</h2>
        </div>
        <div id="messages">
    '''
    
    for msg in minecraft_chat[-20:]:
        html += f'''
        <div class="msg">
            <div class="msg-header">[{datetime.fromtimestamp(msg["time"]).strftime("%H:%M")}] <b>{msg["user"]}</b></div>
            <div>{msg["text"]}</div>
        </div>
        '''
    
    html += '''
        </div>
        <div id="input">
            <form method="post">
                <input name="message" placeholder="Сообщение..." maxlength="200" required>
                <button>Отправить</button>
            </form>
        </div>
    </div>
    <div style="text-align:center;margin-top:20px;">
        <a href="/catalog/Каталог/Minecraft" style="background:#007bff;color:white;padding:15px 30px;border-radius:10px;">📁 В каталог</a>
    </div>
    </body></html>
    '''
    return html

@app.route('/profiles')
def profiles():
    html = '''
    <!DOCTYPE html>
    <html><head><title>Профили</title>
    <style>body{font-family:Arial;padding:30px;background:#f0f2f5;}
    .profiles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}</style></head>
    <body>
    <h1 style="text-align:center;margin-bottom:40px;">👥 Все профили</h1>
    <div class="profiles-grid">
    '''
    for username in users.keys():
        html += f'''
        <div style="background:white;padding:25px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
            <h3>{username}</h3>
            <a href="/profile/{username}" style="display:block;margin-top:15px;padding:10px;background:#007bff;color:white;border-radius:8px;text-align:center;">👁️ Профиль</a>
        </div>
        '''
    html += '''
    </div>
    <p style="text-align:center;margin-top:50px;">
        <a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
    </p></body></html>
    '''
    return html

@app.route('/profile/<username>')
def profile(username):
    if username not in users:
        return '<h1 style="color:red;text-align:center;padding:100px;">Пользователь не найден</h1><a href="/" style="display:block;text-align:center;">🏠 Главная</a>'
    
    profile = user_profiles.get(username, {'bio': '', 'achievements': []})
    is_admin = users[username].get('admin', False)
    role = user_roles.get(username, 'start')
    
    role_color = 'red' if is_admin else 'gold' if role == 'premium' else 'green' if role == 'vip' else 'gray'
    role_text = 'Администратор' if is_admin else role.upper()
    
    ach_list = ''.join([f'<li style="margin:8px 0;">{ach}</li>' for ach in profile.get('achievements', [])])
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Профиль {username}</title>
    <style>body{{font-family:Arial;padding:40px;background:#f0f2f5;}}
    .profile-card{{background:white;max-width:900px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);}}</style></head>
    <body>
    <div class="profile-card">
        <div style="display:flex;align-items:center;gap:30px;margin-bottom:30px;">
            <div style="font-size:64px;">👤</div>
            <h1>{username}</h1>
            <span style="padding:12px 24px;background:{role_color};color:white;border-radius:25px;font-size:18px;font-weight:bold;">{role_text}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;">
            <div>
                <h3 style="margin-bottom:15px;">📝 О себе</h3>
                <p style="font-size:16px;color:#555;">{profile.get('bio', 'Пока ничего не написал...')}</p>
            </div>
            <div>
                <h3 style="margin-bottom:15px;">🏆 Достижения</h3>
                <ul style="font-size:16px;">{ach_list or '<li>Пока нет достижений</li>'}</ul>
            </div>
        </div>
        <div style="text-align:center;margin-top:40px;">
            <a href="/" style="background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
        </div>
    </div></body></html>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user')
    if not current_user or not users.get(current_user, {}).get('admin'):
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Только для админов!</h1>'
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_folder':
            folder_name = request.form['folder_name'].strip()
            location = request.form['folder_location'].strip()
            if folder_name:
                current_folder = catalog
                loc_parts = location.split('/')
                for part in loc_parts:
                    if part not in current_folder:
                        current_folder[part] = {}
                    current_folder = current_folder[part]
                current_folder[folder_name] = {}
        
        elif action == 'add_item':
            item_name = request.form['item_name'].strip()
            location = request.form['item_location'].strip()
            info = request.form['item_info'].strip()
            photo = request.form.get('item_photo', '').strip()
            if item_name and location:
                current_folder = catalog
                loc_parts = location.split('/')
                for part in loc_parts:
                    if part not in current_folder:
                        current_folder[part] = {}
                    current_folder = current_folder[part]
                current_folder[item_name] = {
                    'location': location,
                    'info': info,
                    'photo': photo
                }
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Админ панель</title>
    <style>body{font-family:Arial;padding:30px;background:#f8f9fa;}
    .section{background:white;margin:20px 0;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
    input,textarea,select{width:100%;padding:12px;margin:8px 0;border:2px solid #ddd;border-radius:8px;box-sizing:border-box;}
    button{padding:12px 24px;background:#28a745;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px;}
    .back-btn{background:#007bff;}</style></head>
    <body>
    <h1 style="text-align:center;">🔧 Админ панель</h1>
    
    <div class="section">
        <h2>📁 Добавить папку</h2>
        <form method="post">
            <input type="hidden" name="action" value="add_folder">
            <input name="folder_name" placeholder="Название папки" required>
            <input name="folder_location" placeholder="Нахождение (Каталог/Minecraft)" value="Каталог">
            <button type="submit">➕ Добавить папку</button>
        </form>
    </div>
    
    <div class="section">
        <h2>📦 Добавить предмет</h2>
        <form method="post">
            <input type="hidden" name="action" value="add_item">
            <input name="item_name" placeholder="Название предмета" required>
            <input name="item_location" placeholder="Нахождение (Каталог/Minecraft)" value="Каталог" required>
            <textarea name="item_info" placeholder="Информация о предмете" rows="3"></textarea>
            <input name="item_photo" placeholder="Фото (файл в static/, опционально)">
            <button type="submit">➕ Добавить предмет</button>
        </form>
    </div>
    
    <div style="text-align:center;margin-top:40px;">
        <a href="/" class="back-btn" style="padding:20px 40px;font-size:18px;">🏠 Главная</a>
    </div>
    </body></html>
    '''
    return html

@app.route('/community')
def community():
    return '''
    <!DOCTYPE html>
    <html><head><title>Сообщество</title>
    <style>body{font-family:Arial;padding:100px 20px;text-align:center;background:#f8f9fa;}</style></head>
    <body>
    <h1 style="font-size:48px;">💬 Сообщество</h1>
    <p style="font-size:24px;"><a href="https://t.me/ssylkanatelegramkanalyznaikin" style="color:#0088cc;">Telegram канал</a></p>
    <p style="margin-top:50px;">
        <a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
    </p>
    </body></html>
    '''

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
