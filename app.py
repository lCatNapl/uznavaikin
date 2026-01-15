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

# ✅ СКРЫТЫЙ ФИЛЬТР СЛОВ (НЕ ВИДЕН В HTML)
banned_words = [
    'блять', 'блядь', 'пизд', 'пиздец', 'хуй', 'пидор', 'пидорас', 'ебать', 'нахуй', 
    'пиздуй', 'хуесос', 'мудак', 'пидрила', 'охуеть', 'пиздецки', 'еблан', 'дебил', 
    'идиот', 'урод', 'тварь', 'сука', 'шлюха', 'проститутка', 'блядина',
    'жид', 'чурка', 'хач', 'нигер', 'негр', 'цыган', 'кацап', 'укроп', 'пиндос',
    'трава', 'косяк', 'шишки', 'гашиш', 'план', 'солевой', 'спайс', 'меф', 'амфа',
    'путин', 'кирилл', 'медведев', 'зеленский', 'байден', 'навальный', 'хохол',
    'сиськи', 'залазь', 'трах', 'отсос', 'минет', 'порно', 'секс',
    '666', 'сатана', 'шайтан', 'гитлер', 'казино', 'ставки'
]

def filter_message(message):
    """🔒 СКРЫТЫЙ ФИЛЬТР — работает НЕВИДИМО"""
    for bad_word in banned_words:
        message = re.sub(bad_word, '[*ФИЛЬТР*]', message, flags=re.IGNORECASE)
    return message

category_structure = {
    'Minecraft': {
        'logo': '<img src="/static/minecraft_logo.png" style="width:90px;height:90px;border-radius:15px;box-shadow:0 5px 15px rgba(0,0,0,0.3);">',
        'subcategories': {}
    },
    'World of Tanks': {
        'logo': '<img src="/static/wot_logo.jpg" style="width:90px;height:90px;border-radius:15px;box-shadow:0 5px 15px rgba(0,0,0,0.3);">', 
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

@app.route('/', methods=['GET', 'POST'])
def index():
    current_user = session.get('user')
    stats = calculate_stats()
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Узнавайкин</title>
    <meta charset="utf-8">
    <style>*{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
    .container{max-width:1200px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);overflow:hidden;}
    .header{padding:30px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;text-align:center;}
    .user-info{padding:20px;background:#f8f9fa;border-bottom:1px solid #eee;}
    .stats{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;padding:20px;background:#e9ecef;}
    .stat-card{background:white;padding:15px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center;min-width:120px;}
    .nav{display:flex;justify-content:center;gap:15px;padding:20px;flex-wrap:wrap;}
    .nav-btn{padding:15px 30px;background:#007bff;color:white;text-decoration:none;border-radius:10px;font-weight:bold;transition:all 0.3s;}
    .nav-btn:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,0,0,0.2);}
    .admin-btn{background:#dc3545 !important;}</style></head>
    <body>
    <div class="container">
    '''
    
    if current_user:
        role = user_roles.get(current_user, 'start')
        html += f'''
        <div class="header">
            <h1>🏠 Узнавайкин</h1>
            <div style="font-size:18px;">👤 <b>{current_user}</b> <span style="color:gold;font-weight:bold;">{role.upper()}</span></div>
        </div>
        <div class="user-info">
            <a href="/profile/{current_user}" class="nav-btn">👤 Профиль</a>
            <a href="/logout" class="nav-btn">🚪 Выход</a>
        '''
        if role != 'premium':
            html += '''
            <a href="/buy/vip" class="nav-btn">VIP 100₽</a>
            <a href="/buy/premium" class="nav-btn">PREMIUM 200₽</a>
            '''
        html += '</div>'
    else:
        html += '''
        <div class="header">
            <h1>🏠 Добро пожаловать!</h1>
        </div>
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
    <!DOCTYPE html>
    <html><head><title>Вход</title>
    <style>body{font-family:Arial;padding:50px;text-align:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);}
    form{max-width:400px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.1);}</style></head>
    <body>
    <h1 style="color:white;margin-bottom:30px;font-size:36px;">🔐 Узнавайкин</h1>
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
    current_user = session.get('user')
    
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
    '''
    if current_user and users.get(current_user, {}).get('admin'):
        html += ' <a href="/admin" class="back-btn" style="background:#dc3545;">🔧 Админ панель</a>'
    html += '</div></body></html>'
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
        return '<h1 style="color:red;text-align:center;margin:100px;">❌ Пользователь не найден</h1><a href="/" style="display:block;text-align:center;font-size:18px;">🏠 Главная</a>'
    
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
                <span class="status-badge {'admin' if users[username].get('admin') else 'premium' if role==\'premium\' else 'vip' if role==\'vip\' else 'start'}">
                    {'Администратор' if users[username].get('admin') else role.upper()}
                </span>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;">
            <div>
                <h3 style="margin-bottom:20px;color:#333;">📝 О себе</h3>
                <p style="font-size:16px;line-height:1.6;color:#555;">{profile_data.get('bio', 'Пока ничего не написал...')}</p>
                <h3 style="margin:30px 0 20px 0;color:#333;">🎮 Любимые игры</h3>
                <ul style="font-size:16px;">{''.join([f'<li style="margin:8px 0;color:#555;">{game}</li>' for game in profile_data.get('games', [])]) or '<li style="color:#999;">Пока не указаны</li>'}</ul>
            </div>
            <div>
                <h3 style="margin-bottom:20px;color:#333;">🏆 Достижения</h3>
                <ul style="font-size:16px;">{''.join([f'<li style="margin:8px 0;color:#555;">{ach}</li>' for ach in profile_data.get('achievements', [])]) or '<li style="color:#999;">Пока нет достижений</li>'}</ul>
                <h3 style="margin:30px 0 20px 0;color:#333;">📅 Дата регистрации</h3>
                <p style="font-size:18px;color:#007bff;">{profile_data.get('join_date', 'Неизвестно')}</p>
            </div>
        </div>
        <div style="margin-top:50px;text-align:center;">
            <a href="/" style="background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:20px;font-weight:bold;">🏠 На главную</a>
        </div>
    </div></body></html>
    '''

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    current_user = session.get('user')
    if not current_user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        message = request.form['message'].strip()
        if message:
            # ✅ СКРЫТЫЙ ФИЛЬТР — РАБОТАЕТ НЕВИДИМО!
            message = filter_message(message)
            
            if users[current_user]['muted_until'] > get_timestamp():
                return jsonify({'error': 'Вы в муте!'})
            
            # Антиспам (3 одинаковых сообщения)
            if len(chat_messages) >= 3 and all(msg['text'] == message for msg in chat_messages[-3:]):
                return jsonify({'error': 'Спам запрещён!'})
            
            chat_messages.append({
                'username': current_user,
                'role': user_roles.get(current_user, 'start'),
                'text': message,
                'timestamp': get_timestamp(),
                'id': len(chat_messages)
            })
            user_activity[current_user] = get_timestamp()
    
    chat_messages[:] = chat_messages[-50:]  # Последние 50 сообщений
    
    html = '''
    <!DOCTYPE html>
    <html><head><title>Чат</title>
    <meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;background:#f0f2f5;}
    #chat-container{max-width:1000px;margin:0 auto;background:white;border-radius:20px;overflow:hidden;box-shadow:0 15px 40px rgba(0,0,0,0.1);}
    #messages{max-height:500px;overflow-y:auto;padding:25px;border-bottom:1px solid #eee;}
    .message{margin-bottom:20px;padding:20px;background:#f8f9fa;border-radius:15px;position:relative;}
    .message-header{display:flex;align-items:center;gap:12px;margin-bottom:8px;}
    .username{font-weight:bold;font-size:16px;}
    .time{font-size:12px;color:#666;}
    .status{padding:4px 10px;border-radius:12px;color:white;font-size:12px;font-weight:bold;}
    .start{background:#999;} .vip{background:#00ff88;} .premium{background:gold;} .admin{background:#ff4444;}
    #chat-input{background:white;padding:25px;border-top:1px solid #eee;}
    #message-input{width:70%;padding:15px;border:2px solid #ddd;border-radius:10px;font-size:16px;}
    button{width:25%;padding:15px;background:#007bff;color:white;border:none;border-radius:10px;cursor:pointer;font-size:16px;}
    .admin-controls{display:flex;gap:8px;margin-top:10px;}
    .admin-btn{padding:6px 12px;font-size:12px;background:#dc3545;color:white;border:none;border-radius:6px;cursor:pointer;}</style></head>
    <body>
    <div id="chat-container">
        <div style="padding:25px;background:#007bff;color:white;text-align:center;">
            <h1 style="margin:0;font-size:28px;">💬 ГЛОБАЛЬНЫЙ ЧАТ</h1>
        </div>
        <div id="messages">
    '''
    
    for msg in chat_messages:
        role_class = msg['role']
        role_display = "Администратор" if msg['username'] in users and users[msg['username']].get('admin') else msg['role'].upper()
        time_str = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M')
        
        html += f'''
        <div class="message">
            <div class="message-header">
                <span class="username">{msg['username']}</span>
                <span class="status {role_class}">{role_display}</span>
                <span class="time">{time_str}</span>
            </div>
            <div style="font-size:16px;line-height:1.4;">{msg['text']}</div>
        '''
        
        current_user_admin = current_user and current_user in users and users[current_user].get('admin')
        if current_user_admin and msg['username'] != current_user:
            html += f'''
            <div class="admin-controls">
                <button onclick="deleteMsg({msg['id']})" class="admin-btn">Удалить</button>
                <button onclick="muteUser('{msg['username']}')" class="admin-btn">Мут</button>
            </div>
            '''
        html += '</div>'
    
    html += '''
        </div>
        <div id="chat-input">
            <form onsubmit="sendMessage(event)">
                <input type="text" id="message-input" placeholder="Напишите сообщение... (Enter)" maxlength="500">
                <button type="submit">Отправить</button>
            </form>
        </div>
    </div>
    <script>
        function sendMessage(event) {
            event.preventDefault();
            const msg = document.getElementById('message-input').value;
            if (!msg.trim()) return;
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'message=' + encodeURIComponent(msg)
            }).then(response => response.json()).then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    document.getElementById('message-input').value = '';
                    location.reload();
                }
            });
        }
        
        function deleteMsg(id) {
            if (confirm('Удалить сообщение?')) {
                fetch('/admin/delete_msg/' + id, {method: 'POST'})
                .then(() => location.reload());
            }
        }
        
        function muteUser(username) {
            const time = prompt('Мут на минуты:');
            const reason = prompt('Причина мутa:');
            if (time && reason) {
                fetch(`/admin/mute/${username}?time=${time}&reason=${encodeURIComponent(reason)}`, {method: 'POST'})
                .then(() => location.reload());
            }
        }
        
        // Автообновление каждые 3 секунды
        setInterval(() => location.reload(), 3000);
        document.getElementById('message-input').focus();
    </script>
    </body></html>
    '''
    return html

@app.route('/admin/delete_msg/<int:msg_id>', methods=['POST'])
def delete_msg(msg_id):
    current_user = session.get('user')
    if current_user and users.get(current_user, {}).get('admin'):
        if 0 <= msg_id < len(chat_messages):
            del chat_messages[msg_id]
    return jsonify({'status': 'ok'})

@app.route('/admin/mute/<username>', methods=['POST'])
def mute_user(username):
    current_user = session.get('user')
    if current_user and users.get(current_user, {}).get('admin'):
        time_min = int(request.args.get('time', 5))
        reason = request.args.get('reason', 'Спам')
        if username in users:
            users[username]['muted_until'] = get_timestamp() + (time_min * 60)
            users[username]['mute_reason'] = reason
    return jsonify({'status': 'ok'})

@app.route('/admin')
def admin():
    current_user = session.get('user')
    if not current_user or not users.get(current_user, {}).get('admin'):
        return '<h1 style="color:red;text-align:center;padding:100px;">❌ Только для админов!</h1>'
    
    return '''
    <!DOCTYPE html>
    <html><head><title>Админ панель</title>
    <style>body{font-family:Arial;padding:30px;background:#f8f9fa;}
    .section{background:white;margin:20px 0;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
    input,textarea,select{width:100%;padding:15px;margin:10px 0;border:2px solid #ddd;border-radius:10px;box-sizing:border-box;font-size:16px;}
    button{padding:15px 30px;background:#dc3545;color:white;border:none;border-radius:10px;cursor:pointer;font-size:16px;font-weight:bold;}
    h2{margin-bottom:25px;color:#333;}</style></head>
    <body>
    <h1 style="text-align:center;margin-bottom:40px;">🔧 Админ панель</h1>
    <div style="text-align:center;margin-bottom:40px;">
        <a href="/" style="background:#28a745;color:white;padding:20px 40px;border-radius:15px;font-size:20px;font-weight:bold;">🏠 Главная</a>
    </div>
    
    <div class="section">
        <h2>📁 Каталог (пока без админки)</h2>
        <p style="color:#666;">Добавление категорий и контента — в разработке</p>
    </div>
    
    <div class="section">
        <h2>👥 Управление пользователями</h2>
        <p style="color:#666;">Муты и бан через чат (клик по сообщению)</p>
    </div>
    </body></html>
    '''

@app.route('/community')
def community():
    return '''
    <!DOCTYPE html>
    <html><head><title>Сообщество</title>
    <style>body{font-family:Arial;padding:100px 20px;text-align:center;background:#f8f9fa;}
    h1{font-size:48px;margin-bottom:30px;color:#333;}
    h2{font-size:32px;color:#0088cc;}</style></head>
    <body>
    <h1>💬 Сообщество Узнавайкин</h1>
    <h2><a href="https://t.me/ssylkanatelegramkanalyznaikin" style="color:#0088cc;">Telegram канал</a></h2>
    <p style="font-size:20px;margin:40px 0;color:#666;">Присоединяйся к нам для новостей и общения!</p>
    <a href="/" style="background:#007bff;color:white;padding:25px 50px;border-radius:15px;font-size:22px;font-weight:bold;">🏠 На главную</a>
    </body></html>
    '''

@app.before_request
def update_activity():
    current_user = session.get('user')
    if current_user:
        user_activity[current_user] = get_timestamp()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
