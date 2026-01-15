from flask import Flask, request, redirect, url_for, session
from datetime import datetime
import time
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'uznavaykin-secret-2026'

# ДАННЫЕ (без изменений)
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
            chat_messages.append({'user': current_user, 'text': message, 'time': get_timestamp(), 'role': get_role_display(current_user)})
            chat_messages[:] = chat_messages[-100:]
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Узнавайкин</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:10px;line-height:1.4;}}
    .container{{max-width:100%;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden;}}
    .header{{padding:20px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;position:sticky;top:0;z-index:100;}}
    .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(80px,1fr));gap:10px;padding:15px;background:#f8f9fa;}}
    .stat-card{{background:#fff;padding:12px;border-radius:12px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.1);font-weight:500;}}
    .nav{{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;padding:15px;background:#f8f9fa;border-top:1px solid #eee;overflow-x:auto;}}
    .nav-btn{{padding:12px 16px;background:#007bff;color:white;text-decoration:none;border-radius:12px;font-size:14px;font-weight:600;flex:1 1 120px;text-align:center;min-height:44px;display:flex;align-items:center;justify-content:center;}}
    .nav-btn:hover{{background:#0056b3;transform:translateY(-2px);}}
    .admin-btn{{background:#dc3545;flex:0 0 auto;}}
    #chat-container{{max-width:100%;margin:15px;background:#f8f9fa;border-radius:16px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,0.1);}}
    #chat-messages{{max-height:50vh;overflow-y:auto;padding:15px;background:#e8f5e8;}}
    .chat-msg{{margin-bottom:12px;padding:12px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}}
    .chat-header{{font-weight:600;color:#2e7d32;font-size:13px;margin-bottom:4px;}}
    .chat-mute{{background:#ffcdd2 !important;border-left:4px solid #f44336;}}
    #chat-input{{padding:15px;border-top:1px solid #ddd;background:white;}}
    input[type="text"]{{width:100%;max-width:70%;padding:12px;border:2px solid #4caf50;border-radius:10px;font-size:16px;margin-right:8px;box-sizing:border-box;}}
    button[type="submit"]{{padding:12px 20px;background:#4caf50;color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;flex-shrink:0;min-height:48px;}}
    @media (max-width:768px){{
        body{{padding:5px;}}
        .header{{padding:15px;}}
        .nav{{padding:10px;gap:5px;}}
        .nav-btn{{padding:10px 12px;font-size:13px;flex:1 1 100px;}}
        #chat-messages{{max-height:40vh;}}
        input[type="text"]{{margin-right:0;margin-bottom:8px;width:100%;max-width:none;}}
        button[type="submit"]{{width:100%;}}
        .stats{{grid-template-columns:repeat(3,1fr);gap:8px;padding:10px;}}
    }}
    @media (max-width:480px){{
        .stats{{grid-template-columns:2fr 1fr;}}
        .nav-btn{{font-size:12px;padding:8px 10px;}}
    }}
    </style></head>
    <body>
    <div class="container">
    '''

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
    <!DOCTYPE html><html><head><title>Вход</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px;display:flex;align-items:center;justify-content:center;}
    .login-form{max-width:400px;width:100%;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);}
    input{width:100%;padding:16px;margin:12px 0;border:2px solid #ddd;border-radius:12px;font-size:16px;box-sizing:border-box;}
    button{width:100%;padding:16px;background:#4ecdc4;color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;}
    h1{color:white;text-align:center;margin-bottom:30px;font-size:28px;}
    @media (max-width:480px){.login-form{padding:30px 20px;}}</style></head>
    <body><h1>🔐 Узнавайкин</h1><form method="post" class="login-form">
        <input name="username" placeholder="Логин" required>
        <input name="password" type="password" placeholder="Пароль" required>
        <button>ВОЙТИ</button></form></body></html>
    '''

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog(path=''):
    current_path = [p for p in path.split('/') if p.strip()]
    current_folder = catalog
    for part in current_path:
        if part in current_folder and isinstance(current_folder[part], dict):
            current_folder = current_folder[part]
        else:
            current_folder = {}
    
    return f'''
    <!DOCTYPE html><html><head><title>Каталог</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:15px;background:#f8f9fa;}}
    .container{{max-width:100%;margin:auto;background:white;border-radius:20px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}}
    .breadcrumbs{{margin:25px 0;font-size:16px;padding:15px;background:#e9ecef;border-radius:12px;}}
    .breadcrumbs a{{color:#007bff;text-decoration:none;font-weight:500;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px;}}
    .folder-card{{background:#e3f2fd;padding:20px;border-radius:16px;border-left:5px solid #2196f3;text-decoration:none;display:block;text-align:center;transition:all 0.3s;}}
    .folder-card:hover{{transform:translateY(-3px);box-shadow:0 10px 25px rgba(0,0,0,0.15);}}
    .item-card{{background:#f3e5f5;padding:20px;border-radius:16px;border-left:5px solid #9c27b0;}}
    .item-title{{font-size:18px;font-weight:600;margin-bottom:8px;color:#333;}}
    .item-info{{color:#666;line-height:1.5;font-size:14px;}}
    .back-btn{{display:inline-block;background:#007bff;color:white;padding:14px 28px;border-radius:12px;font-size:16px;font-weight:600;text-decoration:none;margin:30px auto;}}
    .empty-folder{{text-align:center;color:#666;font-size:20px;margin:60px 0;padding:40px;background:#f8f9fa;border-radius:16px;border:2px dashed #ccc;}}
    @media (max-width:768px){{.grid{{grid-template-columns:1fr;}}.folder-card{{padding:25px;}}.container{{padding:15px;margin:5px;border-radius:15px;}}}}</style></head>
    <body><div class="container">
    <div class="breadcrumbs">📁 <a href="/catalog">Каталог</a>''' + ''.join([f' → <a href="/catalog/{'/'.join(current_path[:i+1])}">{part}</a>' for i,part in enumerate(current_path)]) + '</div>' + '''
    ''' + ('''
    <div class="grid">''' + ''.join([f'<a href="/catalog/{'/'.join(current_path)}/{folder}" class="folder-card"><h3 style="margin:0 0 8px 0;color:#2196f3;font-size:18px;">📁 {folder}</h3><p style="margin:0;color:#666;font-size:14px;">Папка</p></a>' for folder in sorted([k for k in current_folder if isinstance(current_folder[k], dict)])]) + ''.join([f'''
    <div class="item-card">
        <h3 class="item-title">{item}</h3>
        <p><b>Нахождение:</b> {current_folder[item].get("location", "Каталог")}</p>
        <div class="item-info">{current_folder[item].get("info", "")}</div>
        {f'<img src="/static/{current_folder[item].get("photo", "")}" style="max-width:100%;border-radius:10px;margin-top:12px;" alt="Фото">' if current_folder[item].get("photo") else ""}
    </div>''' for item in sorted([k for k in current_folder if not isinstance(current_folder[k], dict)])]) + '''</div>''' if current_folder and (any(isinstance(current_folder[k], dict) for k in current_folder) or any(not isinstance(current_folder[k], dict) for k in current_folder)) else '<div class="empty-folder">📭 Папка пустая</div>') + f'''
    <div style="text-align:center;"><a href="/" class="back-btn">🏠 Главная</a></div>
    </div></body></html>
    '''

# Остальные роуты остаются такими же, но с мобильными стилями
@app.route('/profiles')
def profiles():
    return '''
    <!DOCTYPE html><html><head><title>Профили</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:15px;background:#f0f2f5;}
    .profiles-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:15px;}
    .profile-card{background:white;padding:25px;border-radius:16px;box-shadow:0 8px 25px rgba(0,0,0,0.1);text-align:center;}
    .back-btn{display:block;background:#007bff;color:white;padding:16px;border-radius:12px;font-size:16px;font-weight:600;text-decoration:none;margin:30px auto;max-width:300px;}
    @media (max-width:768px){.profiles-grid{grid-template-columns:1fr;}}</style></head>
    <body><h1 style="text-align:center;margin-bottom:30px;">👥 Все профили</h1>
    <div class="profiles-grid">''' + ''.join([f'<div class="profile-card"><h3 style="margin-bottom:15px;">{user}</h3><a href="/profile/{user}" style="display:inline-block;padding:12px 20px;background:#007bff;color:white;border-radius:10px;font-weight:500;">👁️ Профиль</a></div>' for user in sorted(users)]) + f'''
    </div><a href="/" class="back-btn">🏠 Главная</a></body></html>
    '''

@app.route('/profile/<username>')
def profile(username):
    if username not in users: return '<h1 style="color:red;text-align:center;padding:100px;">❌ Пользователь не найден</h1><a href="/" style="display:block;text-align:center;">🏠 Главная</a>'
    profile = user_profiles.get(username, {'status': 'Онлайн'})
    role_display = get_role_display(username)
    role_color = 'red' if users[username].get('admin') else 'gold'
    return f'''
    <!DOCTYPE html><html><head><title>Профиль {username}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:20px;background:#f0f2f5;}}
    .profile-card{{background:white;max-width:500px;margin:auto;padding:30px;border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.1);text-align:center;}}
    .role-badge{{padding:12px 24px;background:{role_color};color:white;border-radius:20px;font-size:16px;font-weight:600;display:inline-block;margin:15px 0;}}
    .status{{font-size:16px;color:#666;margin:20px 0;padding:15px;background:#e8f5e8;border-radius:12px;}}
    .back-btn{{background:#007bff;color:white;padding:16px 32px;border-radius:12px;font-size:16px;font-weight:600;display:inline-block;margin-top:30px;}}
    @media (max-width:480px){{.profile-card{{padding:20px;margin:10px;border-radius:15px;}}}}</style></head>
    <body><div class="profile-card">
        <h1 style="margin-bottom:20px;font-size:28px;">{username}</h1>
        <div class="role-badge">{role_display}</div>
        <div class="status">{profile.get("status", "Онлайн")}</div>
        <a href="/" class="back-btn">🏠 Главная</a>
    </div></body></html>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user', '')
    if not (users.get(current_user, {}).get('admin') or is_moderator(current_user)):
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Нет доступа!</h1>'
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'mute':
            target = request.form['target'].strip()
            duration = float(request.form.get('duration', 5)) * 60
            reason = request.form['reason'].strip()
            if target in users and target != current_user:
                mutes[target] = get_timestamp() + duration
                chat_messages.append({'user': current_user, 'text': f'🔇 {target} замучен на {duration/60}мин {current_user}: {reason}', 'time': get_timestamp(), 'role': get_role_display(current_user)})
        elif action == 'add_mod' and users.get(current_user, {}).get('admin'):
            target = request.form['target'].strip()
            duration = float(request.form.get('duration', 1)) * 3600
            if target in users: moderators[target] = get_timestamp() + duration
    
    can_add_mod = users.get(current_user, {}).get('admin')
    return f'''
    <!DOCTYPE html><html><head><title>Админка</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:15px;background:#f8f9fa;}}
    .container{{max-width:100%;background:white;border-radius:20px;padding:25px;box-shadow:0 10px 30px rgba(0,0,0,0.1);margin:10px;}}
    .section{{background:#f8f9fa;margin:20px 0;padding:25px;border-radius:16px;box-shadow:0 5px 15px rgba(0,0,0,0.08);}}
    input,textarea{{width:100%;padding:14px;margin:8px 0;border:2px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box;}}
    button{{width:100%;padding:16px;background:#28a745;color:white;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;margin:8px 0;}}
    h1{{text-align:center;color:#333;margin-bottom:30px;}}
    h2{{color:#333;margin-bottom:15px;border-left:4px solid #28a745;padding-left:12px;}}
    .back-btn{{background:#007bff;display:block;margin:30px auto;padding:16px 32px;max-width:300px;border-radius:12px;font-size:16px;}}
    @media (max-width:480px){{.container{{margin:5px;padding:20px;}}.section{{padding:20px;margin:15px 0;}}}}</style></head>
    <body><div class="container">
    <h1>🔧 ПАНЕЛЬ УПРАВЛЕНИЯ</h1>
    <div class="section">
        <h2>🔇 МУТИТЬ ИГРОКА</h2>
        <form method="post">
            <input type="hidden" name="action" value="mute">
            <input name="target" placeholder="Имя игрока" required>
            <input name="duration" type="number" placeholder="Минуты (5)" value="5" min="1">
            <input name="reason" placeholder="Причина мута" required>
            <button>🔇 ЗАМУТИТЬ</button>
        </form>
    </div>
    ''' + ('''
    <div class="section">
        <h2>👮 ДАТЬ МОДЕРАТОРА</h2>
        <form method="post">
            <input type="hidden" name="action" value="add_mod">
            <input name="target" placeholder="Имя игрока" required>
            <input name="duration" type="number" placeholder="Часы (1)" value="1" min="1">
            <button>👮 НАЗНАЧИТЬ</button>
        </form>
    </div>''' if can_add_mod else '') + '''
    <a href="/" class="back-btn">🏠 Главная</a>
    </div></body></html>
    '''

@app.route('/community')
def community():
    return '''
    <!DOCTYPE html><html><head><title>Сообщество</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:40px 20px;text-align:center;background:#f8f9fa;}
    h1{font-size:clamp(28px,8vw,48px);margin-bottom:30px;}
    .tg-link{font-size:clamp(20px,6vw,28px);color:#0088cc;text-decoration:none;font-weight:600;}
    .back-btn{background:#007bff;color:white;padding:18px 36px;border-radius:15px;font-size:18px;font-weight:600;display:inline-block;margin-top:40px;text-decoration:none;}
    @media (max-width:480px){body{padding:20px 15px;}}</style></head>
    <body><h1>💬 Сообщество</h1><a href="https://t.me/ssylkanatelegramkanalyznaikin" class="tg-link">Telegram канал</a><br><a href="/" class="back-btn">🏠 Главная</a></body></html>
    '''

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
