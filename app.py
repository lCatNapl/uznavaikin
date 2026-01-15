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
moderators = {}  # {username: end_time}
mutes = {}  # {username: end_time}

# КАТАЛОГ (пустой!)
catalog = {
    'Каталог': {
        'Minecraft': {},
        'World of Tanks': {}
    }
}

def get_timestamp():
    return time.time()

def get_role_display(username):
    if users.get(username, {}).get('admin'):
        return 'Администратор'
    role = user_roles.get(username, 'start')
    if role == 'vip': return 'VIP'
    if role == 'premium': return 'Premium'
    return 'Start'

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'admin': 0}
    now = get_timestamp()
    for username in users:
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

def is_muted(username):
    if username in mutes and get_timestamp() < mutes[username]:
        return True
    if username in mutes:
        del mutes[username]
    return False

def is_moderator(username):
    if username in moderators and get_timestamp() < moderators[username]:
        return True
    if username in moderators:
        del moderators[username]
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    current_user = session.get('user', '')
    stats = calculate_stats()
    
    if request.method == 'POST' and current_user and not is_muted(current_user):
        message = request.form.get('message', '').strip()
        if message and message.startswith('/profile '):
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
    
    html = f'''
    <!DOCTYPE html>
    <html><head><title>Узнавайкин</title><meta charset="utf-8">
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px;}}.container{{max-width:1400px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}}.header{{padding:30px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}}.stats{{display:flex;gap:15px;justify-content:center;padding:20px;background:#e9ecef;flex-wrap:wrap;}}.stat-card{{background:white;padding:15px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center;min-width:100px;}}.nav{{display:flex;justify-content:center;gap:10px;padding:20px;flex-wrap:wrap;}}.nav-btn{{padding:12px 25px;background:#007bff;color:white;text-decoration:none;border-radius:8px;font-weight:bold;}}.nav-btn:hover{{background:#0056b3;transform:translateY(-2px);}}.admin-btn{{background:#dc3545;}}#chat-container{{max-width:800px;margin:20px auto;background:#f8f9fa;border-radius:15px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.1);}}#chat-messages{{max-height:400px;overflow-y:auto;padding:20px;background:#e8f5e8;}}.chat-msg{{margin-bottom:15px;padding:12px;background:white;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}.chat-header{{font-weight:bold;color:#2e7d32;font-size:14px;margin-bottom:5px;}}.chat-mute{{background:#ffcdd2;color:#c62828 !important;}}#chat-input{{padding:20px;border-top:1px solid #ddd;background:white;}}input[type="text"]{{width:70%;padding:12px;border:2px solid #4caf50;border-radius:8px;}}button[type="submit"]{{width:28%;padding:12px;background:#4caf50;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px;}}</style></head>
    <body><div class="container">
    '''
    
    if current_user:
        html += f'<div class="header"><h1>🏠 Узнавайкин</h1><p>👤 <b>{current_user}</b> | <span style="color:gold;">{get_role_display(current_user)}</span></p></div>'
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
    <div id="chat-container">
        <div id="chat-messages">
    '''
    
    for msg in chat_messages[-20:]:
        mute_class = 'chat-mute' if is_muted(msg['user']) else ''
        html += f'''
        <div class="chat-msg {mute_class}">
            <div class="chat-header">[{datetime.fromtimestamp(msg["time"]).strftime("%H:%M")}] <b>{msg["user"]}</b> <span style="color:#666;">({msg["role"]})</span></div>
            <div>{msg["text"]}</div>
        </div>
        '''
    
    html += '</div>'
    
    if current_user:
        if is_muted(current_user):
            html += f'<div style="padding:20px;text-align:center;color:#c62828;">🔇 Вы замучены</div>'
        else:
            html += '''
            <div id="chat-input">
                <form method="post">
                    <input type="text" name="message" placeholder="/profile @username или сообщение" maxlength="200" required>
                    <button type="submit">Отправить</button>
                </form>
            </div>
            '''
    
    html += '''
    </div><div class="nav">
        <a href="/catalog" class="nav-btn">📁 КАТАЛОГ</a>
        <a href="/profiles" class="nav-btn">👥 ПРОФИЛИ</a>
        <a href="/community" class="nav-btn">📢 TG</a>
    '''
    
    if current_user:
        html += f'<a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>'
        if users.get(current_user, {}).get('admin') or is_moderator(current_user):
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
            user_profiles[username] = {'bio': '', 'games': [], 'achievements': [], 'status': 'Онлайн'}
        user_activity[username] = get_timestamp()
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html><html><head><title>Вход</title>
    <style>body{font-family:Arial;padding:50px;text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);}form{max-width:400px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}</style></head>
    <body><h1 style="color:white;margin-bottom:30px;">🔐 Узнавайкин</h1>
    <form method="post">
        <input name="username" placeholder="Логин" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <input name="password" type="password" placeholder="Пароль" style="width:100%;padding:15px;font-size:18px;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;margin:10px 0;" required>
        <button style="width:100%;padding:18px;background:#4ecdc4;color:white;border:none;border-radius:10px;font-size:20px;">ВОЙТИ</button>
    </form></body></html>
    '''

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog(path=''):
    current_path = [p for p in path.split('/') if p.strip()]
    
    # Найти текущую папку
    current_folder = catalog
    for part in current_path:
        if part in current_folder and isinstance(current_folder[part], dict):
            current_folder = current_folder[part]
        else:
            current_folder = {{}}
            break
    
    html = '''
    <!DOCTYPE html><html><head><title>Каталог</title><meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#f8f9fa;}.container{max-width:1200px;margin:0 auto;}.breadcrumbs{{margin:30px 0;font-size:18px;}}.breadcrumbs a{{color:#007bff;}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}.folder-card{{background:#e3f2fd;padding:25px;border-radius:20px;border-left:5px solid #2196f3;text-decoration:none;display:block;transition:all 0.3s;}}.folder-card:hover{{transform:translateY(-5px);box-shadow:0 15px 30px rgba(0,0,0,0.2);}}.item-card{{background:#f3e5f5;padding:25px;border-radius:20px;border-left:5px solid #9c27b0;}}.item-title{{font-size:20px;font-weight:bold;margin-bottom:10px;color:#333;}}.item-info{{color:#666;line-height:1.6;}}.back-btn{{background:#007bff;color:white;padding:15px 30px;border-radius:12px;font-size:18px;font-weight:bold;text-decoration:none;display:inline-block;margin:40px 0;}}.empty-folder{{text-align:center;color:#666;font-size:24px;margin:80px 0;}}</style></head>
    <body><div class="container">
    '''
    
    # Хлебные крошки
    html += '<div class="breadcrumbs">📁 <a href="/catalog">Каталог</a>'
    breadcrumb_parts = []
    for part in current_path:
        breadcrumb_parts.append(part)
        path_str = '/'.join(breadcrumb_parts)
        html += f' → <a href="/catalog/{path_str}">{part}</a>'
    html += '</div>'
    
    if current_folder:
        folders = [k for k in current_folder if isinstance(current_folder[k], dict)]
        items = [k for k in current_folder if not isinstance(current_folder[k], dict)]
        
        if folders or items:
            html += '<div class="grid">'
            for folder_name in sorted(folders):
                full_path = '/catalog/' + '/'.join(current_path + [folder_name])
                html += f'<a href="{full_path}" class="folder-card"><h3 style="margin:0 0 10px 0;color:#2196f3;">📁 {folder_name}</h3><p style="margin:0;color:#666;">Папка</p></a>'
            
            for item_name in sorted(items):
                item = current_folder[item_name]
                html += f'''
                <div class="item-card">
                    <h3 class="item-title">{item_name}</h3>
                    <p><b>Нахождение:</b> {item.get("location", "Каталог")}</p>
                    <div class="item-info">{item.get("info", "")}</div>
                    {f'<img src="/static/{item.get("photo", "")}" style="max-width:100%;border-radius:10px;margin-top:15px;" alt="Фото">' if item.get("photo") else ""}
                </div>
                '''
            html += '</div>'
        else:
            html += '<div class="empty-folder">📭 Папка пустая</div>'
    else:
        html += '<div class="empty-folder"><a href="/catalog">📁 Вернуться в Каталог</a></div>'
    
    html += f'<div style="text-align:center;"><a href="/" class="back-btn">🏠 Главная</a></div></div></body></html>'
    return html

@app.route('/profiles')
def profiles():
    html = '''
    <!DOCTYPE html><html><head><title>Профили</title>
    <style>body{font-family:Arial;padding:30px;background:#f0f2f5;}.profiles-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;}}</style></head>
    <body><h1 style="text-align:center;margin-bottom:40px;">👥 Все профили</h1><div class="profiles-grid">
    '''
    for username in sorted(users.keys()):
        html += f'<div style="background:white;padding:25px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);"><h3>{username}</h3><a href="/profile/{username}" style="display:block;margin-top:15px;padding:10px;background:#007bff;color:white;border-radius:8px;text-align:center;">👁️ Профиль</a></div>'
    html += '''
    </div><p style="text-align:center;margin-top:50px;"><a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a></p></body></html>
    '''
    return html

@app.route('/profile/<username>')
def profile(username):
    if username not in users:
        return '<h1 style="color:red;text-align:center;padding:100px;">Пользователь не найден</h1><a href="/" style="display:block;text-align:center;margin-top:20px;">🏠 Главная</a>'
    
    profile = user_profiles.get(username, {'bio': '', 'status': 'Онлайн'})
    role_display = get_role_display(username)
    role_color = 'red' if users[username].get('admin') else 'gold'
    
    return f'''
    <!DOCTYPE html><html><head><title>Профиль {username}</title>
    <style>body{{font-family:Arial;padding:40px;background:#f0f2f5;}}.profile-card{{background:white;max-width:900px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);}}</style></head>
    <body><div class="profile-card">
        <h1 style="text-align:center;margin-bottom:30px;">{username}</h1>
        <div style="text-align:center;padding:15px;background:#e9ecef;border-radius:20px;margin-bottom:30px;">
            <span style="padding:12px 24px;background:{role_color};color:white;border-radius:25px;font-size:18px;font-weight:bold;">{role_display}</span>
        </div>
        <p style="text-align:center;font-size:18px;color:#666;">{profile.get("status", "Онлайн")}</p>
        <p style="text-align:center;margin-top:40px;"><a href="/" style="background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a></p>
    </div></body></html>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user', '')
    is_admin_access = users.get(current_user, {}).get('admin') or is_moderator(current_user)
    
    if not is_admin_access:
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Нет доступа!</h1>'
    
    if request.method == 'POST':
        action = request.form.get('action')
        
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
            duration = float(request.form.get('duration', 1)) * 3600
            if target in users and target != current_user:
                moderators[target] = get_timestamp() + duration
    
    can_add_mod = users.get(current_user, {}).get('admin')
    html = f'''
    <!DOCTYPE html><html><head><title>Админка</title>
    <style>body{{font-family:Arial;padding:30px;background:#f8f9fa;}}.section{{background:white;margin:20px 0;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}}input,textarea{{width:100%;padding:12px;margin:8px 0;border:2px solid #ddd;border-radius:8px;box-sizing:border-box;}}button{{padding:12px 24px;background:#28a745;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px;}}.back-btn{{background:#007bff;}}</style></head>
    <body><h1 style="text-align:center;">🔧 ПАНЕЛЬ УПРАВЛЕНИЯ</h1>
    
    <div class="section">
        <h2>🔇 МУТИТЬ ИГРОКА</h2>
        <form method="post">
            <input type="hidden" name="action" value="mute">
            <input name="target" placeholder="Имя игрока" required>
            <input name="duration" type="number" placeholder="Минуты" value="5" min="1">
            <input name="reason" placeholder="Причина" required>
            <button type="submit">🔇 ЗАМУТИТЬ</button>
        </form>
    </div>
    '''
    
    if can_add_mod:
        html += '''
        <div class="section">
            <h2>👮 ДАТЬ МОДЕРАТОРА</h2>
            <form method="post">
                <input type="hidden" name="action" value="add_mod">
                <input name="target" placeholder="Имя игрока" required>
                <input name="duration" type="number" placeholder="Часы" value="1" min="1">
                <button type="submit">👮 НАЗНАЧИТЬ</button>
            </form>
        </div>
        '''
    
    html += f'<div style="text-align:center;margin-top:40px;"><a href="/" class="back-btn" style="padding:20px 40px;font-size:18px;">🏠 Главная</a></div></body></html>'
    return html

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
