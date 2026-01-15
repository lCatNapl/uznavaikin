from flask import Flask, request, redirect, url_for, session
from datetime import datetime
import time

app = Flask(__name__, static_folder='static')
app.secret_key = 'uznavaykin-secret-2026'

users = {
    'CatNap': {'password': '120187', 'role': 'premium', 'admin': True, 'muted_until': 0},
    'Назар': {'password': '120187', 'role': 'premium', 'admin': True, 'muted_until': 0}
}
user_profiles = {}
user_roles = {}
user_activity = {}
chat_messages = []

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
    
    role = user_roles.get(current_user, 'start') if current_user else ''
    
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
        html += f'''
        <div class="header">
            <h1>🏠 Узнавайкин</h1>
            <p>👤 <b>{current_user}</b> | <span style="color:gold;">{role.upper()}</span></p>
        </div>
        '''
    else:
        html += '''
        <div class="header">
            <h1>🏠 Узнавайкин</h1>
            <p>Добро пожаловать!</p>
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
        <a href="/catalog" class="nav-btn">📁 Каталог</a>
        <a href="/chat" class="nav-btn">💬 Чат</a>
        <a href="/profiles" class="nav-btn">👥 Профили</a>
        <a href="/community" class="nav-btn">📢 TG</a>
    '''
    
    if current_user and users.get(current_user, {}).get('admin'):
        html += '<a href="/admin" class="nav-btn admin-btn">🔧 Админ</a>'
    
    if current_user:
        html += f'<a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>'
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
                users[username] = {'password': password, 'role': 'start', 'admin': False, 'muted_until': 0}
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

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/catalog')
def catalog():
    html = '''
    <!DOCTYPE html>
    <html><head><title>Каталог</title>
    <meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#f8f9fa;}
    .category-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:30px;}
    .category-card{background:white;padding:35px;border-radius:20px;box-shadow:0 15px 35px rgba(0,0,0,0.1);text-align:center;cursor:pointer;transition:all 0.3s;}
    .category-card:hover{transform:translateY(-10px);box-shadow:0 25px 50px rgba(0,0,0,0.2);}</style></head>
    <body>
    <h1 style="text-align:center;margin:50px 0;font-size:42px;">📁 ИГРЫ</h1>
    <div class="category-grid">
        <a href="/catalog?path=Minecraft" class="category-card" style="text-decoration:none;">
            <img src="/static/minecraft_logo.png" style="width:90px;height:90px;border-radius:15px;margin:0 auto 20px;display:block;">
            <h2 style="font-size:28px;color:#2d5a2d;">Minecraft</h2>
        </a>
        <a href="/catalog?path=World of Tanks" class="category-card" style="text-decoration:none;">
            <img src="/static/wot_logo.jpg" style="width:90px;height:90px;border-radius:15px;margin:0 auto 20px;display:block;">
            <h2 style="font-size:28px;color:#8b0000;">World of Tanks</h2>
        </a>
    </div>
    <div style="text-align:center;margin:60px 0;">
        <a href="/" style="background:#007bff;color:white;padding:18px 35px;border-radius:12px;font-size:18px;font-weight:bold;text-decoration:none;">🏠 Главная</a>
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
    
    is_admin = users[username].get('admin', False)
    role = user_roles.get(username, 'start')
    
    role_class = 'admin' if is_admin else role
    role_color = 'red' if is_admin else 'gold' if role == 'premium' else 'green' if role == 'vip' else 'gray'
    role_text = 'Администратор' if is_admin else role.upper()
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Профиль {username}</title>
    <style>body{{font-family:Arial;padding:40px;background:#f0f2f5;}}
    .profile-card{{background:white;max-width:800px;margin:auto;padding:40px;border-radius:25px;box-shadow:0 20px 60px rgba(0,0,0,0.1);}}</style></head>
    <body>
    <div class="profile-card">
        <h1 style="text-align:center;margin-bottom:30px;">{username}</h1>
        <div style="text-align:center;padding:15px;background:#e9ecef;border-radius:20px;margin-bottom:30px;">
            <span style="padding:10px 20px;background:{role_color};color:white;border-radius:25px;font-size:18px;font-weight:bold;">
                {role_text}
            </span>
        </div>
        <p style="text-align:center;font-size:18px;color:#666;">Профиль в разработке...</p>
        <div style="text-align:center;margin-top:40px;">
            <a href="/" style="background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
        </div>
    </div></body></html>
    '''

@app.route('/chat')
def chat():
    return '''
    <!DOCTYPE html>
    <html><head><title>Чат</title>
    <style>body{{font-family:Arial;padding:100px;text-align:center;background:#f8f9fa;}}</style></head>
    <body>
    <h1 style="font-size:48px;">💬 Чат</h1>
    <p style="font-size:24px;color:#666;">Чат в разработке...</p>
    <p style="margin-top:50px;">
        <a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
    </p>
    </body></html>
    '''

@app.route('/community')
def community():
    return '''
    <!DOCTYPE html>
    <html><head><title>Сообщество</title>
    <style>body{{font-family:Arial;padding:100px 20px;text-align:center;background:#f8f9fa;}}</style></head>
    <body>
    <h1 style="font-size:48px;">💬 Сообщество</h1>
    <p style="font-size:24px;"><a href="https://t.me/ssylkanatelegramkanalyznaikin" style="color:#0088cc;">Telegram канал</a></p>
    <p style="margin-top:50px;">
        <a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:18px;">🏠 Главная</a>
    </p>
    </body></html>
    '''

@app.route('/admin')
def admin():
    current_user = session.get('user')
    if not current_user or not users.get(current_user, {}).get('admin'):
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Только для админов!</h1>'
    return '''
    <!DOCTYPE html>
    <html><head><title>Админ</title></head>
    <body>
    <h1 style="text-align:center;padding:50px;">🔧 Админ панель</h1>
    <p style="text-align:center;">В разработке...</p>
    <p style="text-align:center;"><a href="/" style="background:#28a745;color:white;padding:15px 30px;border-radius:10px;">🏠 Главная</a></p>
    </body></html>
    '''

@app.route('/buy/<role>')
def buy(role):
    if session.get('user'):
        user_roles[session['user']] = role
    return redirect(url_for('index'))

@app.before_request
def update_activity():
    user = session.get('user')
    if user:
        user_activity[user] = get_timestamp()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

