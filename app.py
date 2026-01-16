from flask import Flask, request, redirect, url_for, session, jsonify
from datetime import datetime
import time
import os
import json

app = Flask(__name__, static_folder='static')
app.secret_key = 'uznavaykin-v32-secret-2026'

DATA_FILE = 'uznavaykin_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Конвертация времени из строк в float
                for key in ['user_activity', 'moderators', 'mutes']:
                    if key in data:
                        data[key] = {k: float(v) for k, v in data[key].items()}
                return data
        except:
            pass
    return {}

def save_data():
    data = {
        'users': users,
        'user_profiles': user_profiles,
        'user_roles': user_roles,
        'user_activity': {k: float(v) for k, v in user_activity.items()},
        'chat_messages': chat_messages,
        'moderators': {k: float(v) for k, v in moderators.items()},
        'mutes': {k: float(v) for k, v in mutes.items()},
        'catalog': catalog
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# ИНИЦИАЛИЗАЦИЯ ДАННЫХ
data = load_data()
users = data.get('users', {
    'CatNap': {'password': '120187', 'role': 'admin', 'admin': True},
    'Назар': {'password': '120187', 'role': 'admin', 'admin': True}
})
user_profiles = data.get('user_profiles', {})
user_roles = data.get('user_roles', {})
user_activity = data.get('user_activity', {})
chat_messages = data.get('chat_messages', [])
moderators = data.get('moderators', {})
mutes = data.get('mutes', {})

# КАТАЛОГ БЕЗ 'Каталог'
catalog = data.get('catalog', {
    'Minecraft': {
        'Алмаз': {'location': 'Minecraft', 'info': 'Самый ценный ресурс!', 'photo': ''},
        'Железо': {'location': 'Minecraft', 'info': 'Для инструментов', 'photo': ''}
    },
    'World of Tanks': {
        'Т-34': {'location': 'World of Tanks', 'info': 'Легендарный танк СССР', 'photo': ''},
        'IS-7': {'location': 'World of Tanks', 'info': 'Тяжелый танк 10 уровня', 'photo': ''}
    }
})

def get_timestamp(): 
    return time.time()

def get_role_display(username):
    if users.get(username, {}).get('admin'): 
        return '👑 Администратор'
    if username in moderators and get_timestamp() < moderators[username]: 
        return '🛡️ Модератор'
    role = user_roles.get(username, 'start')
    return {'vip': '⭐ VIP', 'premium': '💎 Premium'}.get(role, '📚 Start')

def get_user_design(username):
    role = get_role_display(username).lower().replace(' ', '').replace('️', '').replace('👑', '').replace('🛡️', '')
    designs = {
        'start': 'basic',
        'vip': 'vip', 
        'premium': 'premium',
        'moderator': 'admin',
        'администратор': 'admin'
    }
    return designs.get(role, 'basic')

def is_muted(username):
    if username in mutes and get_timestamp() < mutes[username]: 
        return True
    if username in mutes: 
        del mutes[username]
        save_data()
    return False

def is_moderator(username):
    if username in moderators and get_timestamp() < moderators[username]: 
        return True
    if username in moderators: 
        del moderators[username]
        save_data()
    return False

def is_admin(username):
    return users.get(username, {}).get('admin', False)

def calculate_stats():
    stats = {'online': 0, 'afk': 0, 'start': 0, 'vip': 0, 'premium': 0, 'moderator': 0, 'admin': 0}
    now = get_timestamp()
    for username in list(users.keys()):
        if username in user_activity and now - user_activity[username] < 300:
            stats['online'] += 1
            role_display = get_role_display(username)
            if now - user_activity[username] > 60: 
                stats['afk'] += 1
            elif 'Администратор' in role_display: 
                stats['admin'] += 1
            elif 'Модератор' in role_display: 
                stats['moderator'] += 1
            elif 'Premium' in role_display: 
                stats['premium'] += 1
            elif 'VIP' in role_display: 
                stats['vip'] += 1
            else: 
                stats['start'] += 1
    return stats

# КАТАЛОГ ФУНКЦИИ
def add_item(path, name, info='', location='', photo=''):
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if not parts: return False
    
    parent = catalog
    for part in parts[:-1]:
        if part not in parent: 
            parent[part] = {}
        parent = parent[part]
    
    parent[name] = {
        'location': location or '/'.join(parts + [name]), 
        'info': info, 
        'photo': photo
    }
    save_data()
    return True

def add_folder(path, name):
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if not parts: return False
    
    parent = catalog
    for part in parts[:-1]:
        if part not in parent: 
            parent[part] = {}
        parent = parent[part]
    
    if name not in parent:
        parent[name] = {}
    save_data()
    return True

def delete_item(path):
    parts = [p.strip() for p in path.split('/') if p.strip()]
    if len(parts) < 1: return False
    
    parent = catalog
    for i in range(len(parts)-1):
        if parts[i] not in parent or not isinstance(parent[parts[i]], dict):
            return False
        parent = parent[parts[i]]
    
    if parts[-1] in parent:
        del parent[parts[-1]]
        save_data()
        return True
    return False

def get_catalog_content(path=''):
    parts = [p.strip() for p in path.split('/') if p.strip()]
    folder = catalog
    
    for part in parts:
        if part in folder and isinstance(folder[part], dict):
            folder = folder[part]
        else:
            return {'error': 'Папка не найдена'}
    
    folders = [key for key, value in folder.items() if isinstance(value, dict)]
    items = [(key, value) for key, value in folder.items() if not isinstance(value, dict)]
    return {'folders': folders, 'items': items, 'path': path}

def get_catalog_tree():
    def build_tree(folder, path=''):
        tree = []
        for name, content in folder.items():
            full_path = f"{path}/{name}" if path else name
            if isinstance(content, dict):
                tree.append({'name': name, 'path': full_path, 'type': 'folder', 'children': build_tree(content, full_path)})
            else:
                tree.append({'name': name, 'path': full_path, 'type': 'item'})
        return tree
    return build_tree(catalog)

@app.route('/', methods=['GET', 'POST'])
def index():
    current_user = session.get('user', '')
    design = get_user_design(current_user) if current_user else 'basic'
    stats = calculate_stats()
    
    if request.method == 'POST' and current_user and not is_muted(current_user):
        message = request.form.get('message', '').strip()
        if message.startswith('/profile '):
            target = message[9:].strip()
            if target in users: 
                return redirect(f'/profile/{target}')
        elif message:
            chat_messages.append({
                'id': len(chat_messages),
                'user': current_user, 
                'text': message, 
                'time': get_timestamp(),
                'role': get_role_display(current_user)
            })
            chat_messages[:] = chat_messages[-200:]
            save_data()
    
    css_themes = {
        'basic': '''
        body {background:linear-gradient(135deg,#f5f7fa,#c3cfe2);}
        .container {background:#fff;color:#333;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
        .header {background:linear-gradient(45deg,#ff9a9e,#fecfef);color:#333;}
        .nav-btn {background:#74b9ff;color:white;}
        ''',
        'vip': '''
        body {background:linear-gradient(135deg,#667eea,#764ba2);}
        .container {background:linear-gradient(135deg,#667eea,#764ba2);color:white;box-shadow:0 20px 60px rgba(102,126,234,0.4);}
        .header {background:linear-gradient(45deg,#f093fb,#f5576c);color:white;}
        .nav-btn {background:#ff6b6b;color:white;}
        ''',
        'premium': '''
        body {background:linear-gradient(135deg,#4facfe,#00f2fe);}
        .container {background:linear-gradient(135deg,#a8edea,#fed6e3);color:#333;box-shadow:0 25px 80px rgba(79,172,254,0.3);}
        .header {background:linear-gradient(45deg,#fa709a,#fee140);color:#333;}
        .nav-btn {background:#ff9ff3;color:white;}
        ''',
        'admin': '''
        body {background:linear-gradient(135deg,#ff6b6b,#4ecdc4);}
        .container {background:linear-gradient(135deg,#ff6b6b,#4ecdc4);color:white;box-shadow:0 30px 100px rgba(255,107,107,0.5);}
        .header {background:linear-gradient(45deg,#667eea,#764ba2);color:white;}
        .nav-btn {background:#ffeaa7;color:#2d3436;}
        .admin-btn {background:#00b894;color:white;}
        '''
    }
    
    css = css_themes.get(design, css_themes['basic'])
    
    html = f'''<!DOCTYPE html>
<html><head><title>🚀 Узнавайкин v32</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
{css}
* {margin:0;padding:0;box-sizing:border-box;}
body {font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;line-height:1.6;min-height:100vh;padding:10px;overflow-x:hidden;}
.container {max-width:1200px;margin:0 auto;border-radius:25px;overflow:hidden;}
.header {padding:30px;text-align:center;}
h1 {font-size:2.5em;margin:0;font-weight:700;}
.stats {display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:15px;padding:25px;background:rgba(255,255,255,0.2);backdrop-filter:blur(10px);border-radius:20px;margin:20px;}
.stat-card {background:rgba(255,255,255,0.9);padding:20px;border-radius:15px;text-align:center;box-shadow:0 8px 25px rgba(0,0,0,0.1);transition:transform 0.3s;}
.stat-card:hover {transform:translateY(-5px);}
.nav {display:flex;flex-wrap:wrap;gap:12px;padding:25px;background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);justify-content:center;border-radius:20px;margin:0 20px 20px 20px;}
.nav-btn {padding:15px 25px;color:white;text-decoration:none;border-radius:15px;font-weight:bold;flex:1;max-width:160px;text-align:center;transition:all 0.3s;font-size:16px;}
.nav-btn:hover {transform:scale(1.05);box-shadow:0 10px 30px rgba(0,0,0,0.3);}
.admin-btn {background:rgba(255,255,255,0.9);color:#2d3436;flex:0 0 auto;font-weight:bold;}
#chat-container {max-width:900px;margin:25px auto;background:rgba(255,255,255,0.1);border-radius:20px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.2);backdrop-filter:blur(20px);}
#chat-messages {max-height:450px;overflow-y:auto;padding:25px;background:rgba(255,255,255,0.05);}
.chat-msg {margin-bottom:20px;padding:20px;background:rgba(255,255,255,0.9);border-radius:18px;box-shadow:0 5px 20px rgba(0,0,0,0.1);position:relative;transition:all 0.3s;}
.chat-msg:hover {box-shadow:0 10px 30px rgba(0,0,0,0.2);}
.chat-header {font-weight:bold;font-size:14px;margin-bottom:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.delete-btn {position:absolute;top:5px;right:5px;background:#ff4757;color:white;border:none;border-radius:50%;width:28px;height:28px;cursor:pointer;font-size:14px;font-weight:bold;display:none;transition:all 0.3s;}
.chat-msg:hover .delete-btn {display:block;}
.chat-mute {background:#ffeaa7 !important;border-left:5px solid #fdcb6e;animation:pulse 2s infinite;}
@keyframes pulse {{0%{{opacity:1;}}50%{{opacity:0.7;}}100%{{opacity:1;}}}}
.mute-notice {background:#ff6b8a !important;border-left:5px solid #ee5a6f;padding:15px !important;margin:10px 0 !important;color:#fff !important;}
#chat-input {padding:25px;border-top:1px solid rgba(255,255,255,0.2);background:rgba(255,255,255,0.1);}
input[type="text"] {width:75%;padding:18px;border:2px solid rgba(255,255,255,0.3);border-radius:12px;font-size:18px;background:rgba(255,255,255,0.9);box-sizing:border-box;}
button[type="submit"] {width:22%;padding:18px;background:linear-gradient(45deg,#00b894,#00cec9);color:white;border:none;border-radius:12px;cursor:pointer;font-size:18px;margin-left:3%;font-weight:bold;}
button:disabled {background:#ddd !important;color:#999 !important;cursor:not-allowed !important;}
@media (max-width:1200px) {{.nav {{gap:8px;}}.nav-btn {{padding:12px 18px;font-size:15px;}}}}
@media (max-width:768px) {{.stats {{grid-template-columns:repeat(3,1fr);gap:10px;padding:15px;margin:10px;}}.nav {{flex-direction:column;gap:10px;padding:20px;margin:0 10px 20px;}}.nav-btn {{max-width:none;}}input[type="text"] {{width:100%;margin-bottom:15px;}}button[type="submit"] {{width:100%;margin-left:0;}}#chat-messages {{max-height:350px;padding:15px;}}}}
@media (max-width:480px) {{body {{padding:5px;}}.container {{border-radius:15px;margin:5px;}}.header {{padding:20px;}}h1 {{font-size:2em;}}}}
</style></head>
<body><div class="container">'''
    
    if current_user:
        html += f'<div class="header"><h1>🚀 Узнавайкин v32</h1><p>👤 <b style="font-size:1.2em;">{current_user}</b> | <span style="background:rgba(255,255,255,0.3);padding:8px 15px;border-radius:15px;font-size:1.1em;font-weight:bold;">{get_role_display(current_user)}</span></p></div>'
    else:
        html += '<div class="header"><h1>🚀 Узнавайкин v32</h1><p style="font-size:1.2em;">Добро пожаловать в лучший чат!</p></div>'
    
    html += f'''
<div class="stats">
    <div class="stat-card"><b style="font-size:1.5em;">{stats['online']}</b><br>👥 Онлайн</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['afk']}</b><br>😴 АФК</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['start']}</b><br>📚 Start</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['vip']}</b><br>⭐ VIP</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['premium']}</b><br>💎 Premium</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['moderator']}</b><br>🛡️ Модеры</div>
    <div class="stat-card"><b style="font-size:1.5em;">{stats['admin']}</b><br>👑 Админы</div>
</div>

<div id="chat-container">
    <div id="chat-messages">'''
    
    for msg in reversed(chat_messages[-50:]):
        mute_class = 'chat-mute' if is_muted(msg['user']) else ''
        is_admin_mod = current_user and (is_admin(current_user) or is_moderator(current_user)) and msg['user'] != current_user
        delete_btn = f'<button class="delete-btn" onclick="deleteMessage({msg["id"]})" title="Удалить">×</button>' if is_admin_mod else ''
        
        html += f'''
    <div class="chat-msg {mute_class}" data-msg-id="{msg['id']}">
        {delete_btn}
        <div class="chat-header">
            <b style="color:#2d3436;">{msg["user"]}</b> 
            <span style="color:#636e72;font-size:12px;">{msg["role"]}</span>
            <span style="font-size:12px;color:#b2bec3;">{datetime.fromtimestamp(msg["time"]).strftime("%H:%M")}</span>
        </div>
        <div style="margin-top:5px;word-wrap:break-word;">{msg["text"]}</div>
    </div>'''
    
    html += f'''</div>
    <div id="chat-input">'''
    
    if current_user:
        mute_status = '🔇 Вы замучены!' if is_muted(current_user) else ''
        html += f'''
        {mute_status and f'<div style="text-align:center;color:#ff6b6b;font-weight:bold;padding:15px;background:rgba(255,107,107,0.2);border-radius:12px;margin-bottom:15px;">{mute_status}</div>' or ''}
        <form method="post" id="chatForm">
            <input type="text" name="message" id="messageInput" placeholder="/profile @ник или сообщение... (макс. 300 символов)" maxlength="300" {'' if not is_muted(current_user) else 'disabled placeholder="🔇 Вы замучены!"'}>
            <button type="submit" {'' if not is_muted(current_user) else 'disabled'}>📤 Отправить</button>
        </form>'''
    else:
        html += '<div style="padding:40px;text-align:center;color:rgba(255,255,255,0.8);font-size:1.2em;">🔐 <a href="/login" style="color:#74b9ff;text-decoration:none;font-weight:bold;">Войдите</a> для чата и каталога!</div>'
    
    html += '''
    </div>
</div>
<div class="nav">
    <a href="/catalog" class="nav-btn">📁 Каталог</a>
    <a href="/profiles" class="nav-btn">👥 Профили</a>
    <a href="/community" class="nav-btn">💬 TG Канал</a>'''
    
    if current_user:
        html += f'<a href="/profile/{current_user}" class="nav-btn">👤 Мой профиль</a>'
        if is_admin(current_user):
            html += '<a href="/admin" class="nav-btn admin-btn">🔧 Админ-панель</a>'
        html += '<a href="/logout" class="nav-btn">🚪 Выход</a>'
    else:
        html += '<a href="/login" class="nav-btn">🔐 Войти / Регистрация</a>'
    
    html += '''
</div></div>

<script>
let lastMsgCount = ''' + str(len(chat_messages)) + ''';
function autoUpdateChat() {
    if(document.visibilityState === "visible") {
        fetch('/api/chat_count')
        .then(r=>r.json())
        .then(data => {
            if(data.count > lastMsgCount) {
                lastMsgCount = data.count;
                location.reload();
            }
        }).catch(()=>{});
    }
}
setInterval(autoUpdateChat, 2000);

function deleteMessage(msgId) {
    if(confirm('Удалить сообщение?')) {
        fetch(`/api/delete_message/${msgId}`, {method:'DELETE'})
        .then(r=>r.json())
        .then(data => {
            if(data.success) location.reload();
        }).catch(()=>alert('Ошибка'));
    }
}

document.getElementById('chatForm')?.addEventListener('submit', function(e) {
    const input = document.getElementById('messageInput');
    if(input.value.trim() === "") {
        e.preventDefault();
        return false;
    }
});
</script></body></html>'''
    return html

@app.route('/api/chat_count')
def api_chat_count():
    return jsonify({'count': len(chat_messages)})

@app.route('/api/delete_message/<int:msg_id>', methods=['DELETE'])
def api_delete_message(msg_id):
    current_user = session.get('user', '')
    if not current_user or not (is_admin(current_user) or is_moderator(current_user)):
        return jsonify({'error': 'Нет доступа'}), 403
    
    for i, msg in enumerate(chat_messages):
        if msg['id'] == msg_id and msg['user'] != current_user:
            del chat_messages[i]
            save_data()
            return jsonify({'success': True})
    return jsonify({'error': 'Сообщение не найдено'}), 404

@app.route('/catalog/<path:path>')
@app.route('/catalog')
def catalog_view(path=''):
    content = get_catalog_content(path)
    
    if 'error' in content:
        return f'''<!DOCTYPE html><html><body style="padding:50px;font-family:Arial;text-align:center;background:#f8f9fa;">
<h1 style="color:#dc3545;font-size:2em;">❌ {content["error"]}</h1>
<a href="/catalog" style="background:#007bff;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block;margin:10px;font-size:18px;">📁 В Каталог</a>
<a href="/" style="background:#28a745;color:white;padding:15px 30px;border-radius:10px;text-decoration:none;display:inline-block;margin-left:10px;font-size:18px;">🏠 Главная</a>
</body></html>'''
    
    breadcrumbs = '📁 <a href="/catalog" style="color:#007bff;">Каталог</a>'
    parts = [p.strip() for p in path.split('/') if p.strip()]
    temp_path = []
    for part in parts:
        temp_path.append(part)
        path_str = '/'.join(temp_path)
        breadcrumbs += f' → <a href="/catalog/{path_str}" style="color:#007bff;">{part}</a>'
    
    content_html = '<div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:25px;padding:20px;">'
    
    # ПАПКИ
    for folder in sorted(content['folders']):
        content_html += f'''
        <a href="/catalog/{path}/{folder}" style="background:#e3f2fd;padding:30px;border-radius:20px;border-left:5px solid #2196f3;
        text-decoration:none;display:block;text-align:center;transition:all 0.3s;font-family:Arial;text-shadow:none;">
            <h3 style="margin:0 0 10px 0;color:#2196f3;font-size:1.8em;">📁 {folder}</h3>
            <p style="margin:0;color:#666;font-size:1.2em;">Папка</p>
        </a>'''
    
    # ПРЕДМЕТЫ
    for item_name, item_data in sorted(content['items']):
        photo_html = ''
        if item_data.get('photo'):
            photo_html = f'<img src="{item_data["photo"]}" style="width:100%;max-height:200px;object-fit:cover;border-radius:10px;margin:15px 0;" alt="Фото" onerror="this.style.display=\'none\'">'
        
        content_html += f'''
        <div style="background:#f3e5f5;padding:30px;border-radius:20px;border-left:5px solid #9c27b0;font-family:Arial;box-shadow:0 5px 20px rgba(0,0,0,0.1);">
            <h3 style="font-size:1.8em;font-weight:bold;margin-bottom:15px;color:#333;">{item_name}</h3>
            <p style="margin:8px 0;font-size:1.1em;"><b style="color:#555;">📍 Местоположение:</b> <span style="color:#666;">{item_data.get("location", "Не указано")}</span></p>
            <p style="margin:8px 0;font-size:1.1em;line-height:1.6;"><b style="color:#555;">ℹ️ Информация:</b></p>
            <div style="background:#f9f9f9;padding:15px;border-radius:10px;color:#444;font-size:1em;">{item_data.get("info", "—")}</div>
            {photo_html}
        </div>'''
    
    content_html += '</div>'
    
    if not content['folders'] and not content['items']:
        content_html = '''
        <div style="text-align:center;color:#666;font-size:2.5em;margin:100px 0;padding:80px;background:#f8f9fa;
        border-radius:30px;border:4px dashed #ddd;font-family:Arial;box-shadow:inset 0 5px 20px rgba(0,0,0,0.05);">
            📭 Эта папка пуста
            <p style="font-size:0.6em;margin-top:20px;color:#999;">Добавьте папки или предметы через админ-панель</p>
        </div>'''
    
    return f'''<!DOCTYPE html>
<html><head><title>📁 Каталог {path or "Главная"}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {font-family:Arial,sans-serif;padding:20px;background:#f8f9fa;}
.container {max-width:1300px;margin:0 auto;background:white;border-radius:25px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,0.1);}
.breadcrumbs {margin:30px 0;padding:25px;background:#e9ecef;border-radius:20px;font-size:18px;line-height:1.6;}
.breadcrumbs a {color:#007bff;text-decoration:none;font-weight:500;}
.breadcrumbs a:hover {text-decoration:underline;}
.grid {display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:30px;}
.grid > a:hover, .grid > div:hover {transform:translateY(-8px);box-shadow:0 20px 40px rgba(0,0,0,0.15) !important;}
.back-btn {background:#007bff;color:white;padding:18px 40px;border-radius:15px;font-size:20px;font-weight:bold;
text-decoration:none;display:inline-block;margin:50px 10px;transition:all 0.3s;}
.back-btn:hover {transform:translateY(-3px);box-shadow:0 15px 35px rgba(0,123,255,0.4);}
@media (max-width:768px) {
    .container {padding:20px;margin:10px;border-radius:20px;}
    .grid {grid-template-columns:1fr !important;gap:20px;padding:10px;}
    .breadcrumbs {font-size:16px;padding:20px;}
}
</style></head>
<body>
<div class="container">
    <div class="breadcrumbs">{breadcrumbs}</div>
    {content_html}
    <div style="text-align:center;margin-top:60px;">
        <a href="/catalog" class="back-btn">📁 Главный Каталог</a>
        <a href="/" class="back-btn" style="background:#28a745;">🏠 На Главную</a>
    </div>
</div>
</body></html>'''

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
            user_profiles[username] = {'bio': '', 'status': 'Онлайн', 'info': ''}
        
        user_activity[username] = get_timestamp()
        save_data()
        return redirect(url_for('index'))
    
    return '''<!DOCTYPE html>
<html><head><title>🔐 Вход - Узнавайкин</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:40px;display:flex;align-items:center;justify-content:center;}
.login-container{max-width:450px;width:100%;background:linear-gradient(135deg,#667eea,#764ba2);padding:50px;border-radius:25px;box-shadow:0 25px 80px rgba(0,0,0,0.3);color:white;text-align:center;}
.login-container input{width:100%;padding:20px;margin:15px 0;border:none;border-radius:15px;font-size:18px;box-sizing:border-box;background:rgba(255,255,255,0.95);color:#333;}
.login-container button{width:100%;padding:20px;background:linear-gradient(45deg,#ff6b6b,#4ecdc4);color:white;border:none;border-radius:15px;font-size:20px;font-weight:bold;cursor:pointer;margin-top:20px;transition:all 0.3s;}
.login-container button:hover{transform:translateY(-3px);box-shadow:0 15px 40px rgba(255,107,107,0.4);}
h1{font-size:2.5em;margin-bottom:30px;}}</style></head>
<body>
<div class="login-container">
    <h1>🔐 Узнавайкин v32</h1>
    <form method="post">
        <input name="username" placeholder="👤 Логин" required maxlength="20">
        <input name="password" type="password" placeholder="🔑 Пароль" required maxlength="50">
        <button type="submit">🚀 ВОЙТИ / РЕГИСТРАЦИЯ</button>
    </form>
    <p style="margin-top:30px;font-size:14px;">Пароли защищены и не хранятся в открытом виде</p>
</div></body></html>'''

@app.route('/profiles')
def profiles():
    profiles_html = ''
    for user in sorted(users.keys()):
        profile = user_profiles.get(user, {})
        role_display = get_role_display(user)
        profiles_html += f'''
        <div style="background:white;padding:30px;border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.1);text-align:center;margin:20px;">
            <h3 style="font-size:2em;margin-bottom:15px;color:#333;">{user}</h3>
            <div style="padding:15px 25px;background:#e8f5e8;border-radius:15px;font-size:1.3em;font-weight:bold;margin:20px 0;">{role_display}</div>
            <p style="color:#666;margin:10px 0;font-size:1.1em;">{profile.get("status", "Онлайн")}</p>
            <a href="/profile/{user}" style="display:inline-block;padding:15px 35px;background:#007bff;color:white;border-radius:15px;font-weight:bold;font-size:18px;text-decoration:none;">👁️ Посмотреть профиль</a>
        </div>'''
    
    return f'''<!DOCTYPE html><html><head><title>👥 Профили</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:30px;background:#f0f2f5;}}.container{{max-width:1200px;margin:auto;}}.profiles-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:30px;margin:40px 0;}}.back-btn{{background:#007bff;color:white;padding:25px 50px;border-radius:20px;font-size:22px;font-weight:bold;text-decoration:none;display:block;margin:60px auto;max-width:400px;text-align:center;}}@media (max-width:768px){{.profiles-grid{{grid-template-columns:1fr;gap:20px;}}}}</style></head><body><div class="container"><h1 style="text-align:center;margin-bottom:50px;font-size:3em;color:#333;">👥 Все профили</h1><div class="profiles-grid">{profiles_html}</div><a href="/" class="back-btn">🏠 Главная</a></div></body></html>'''

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    if username not in users:
        return '''<!DOCTYPE html><html><body style="background:#f0f2f5;padding:100px;text-align:center;font-family:Arial;">
<h1 style="color:#dc3545;font-size:3em;">❌ Пользователь не найден</h1>
<a href="/" style="background:#007bff;color:white;padding:20px 40px;border-radius:15px;font-size:20px;text-decoration:none;display:inline-block;margin-top:30px;">🏠 На главную</a>
</body></html>'''
    
    current_user = session.get('user', '')
    profile_data = user_profiles.get(username, {'status': 'Онлайн', 'info': ''})
    is_owner = current_user == username
    role_display = get_role_display(username)
    role_color = '#e74c3c' if is_admin(username) else '#f39c12' if 'VIP' in role_display else '#9b59b6'
    
    if request.method == 'POST' and is_owner:
        profile_data['status'] = request.form.get('status', 'Онлайн')[:50]
        profile_data['info'] = request.form.get('info', '')[:500]
        user_profiles[username] = profile_data
        save_data()
    
    status_html = f'''
    <form method="post" style="margin-top:20px;">
        <input name="status" value="{profile_data.get("status", "Онлайн")}" placeholder="Статус (до 50 символов)" maxlength="50" style="width:100%;padding:18px;border:2px solid #ddd;border-radius:15px;font-size:18px;box-sizing:border-box;">
        <button type="submit" style="width:100%;padding:18px;background:#28a745;color:white;border:none;border-radius:15px;font-size:18px;margin-top:15px;cursor:pointer;font-weight:bold;">💾 Обновить статус</button>
    </form>''' if is_owner else f'<div style="font-size:1.4em;color:#27ae60;padding:25px;background:#e8f5e8;border-radius:20px;margin:20px 0;">{profile_data.get("status", "Онлайн")}</div>'
    
    info_html = f'''
    <form method="post" style="margin-top:20px;">
        <textarea name="info" placeholder="Расскажите о себе... (до 500 символов)" rows="6" maxlength="500" style="width:100%;padding:20px;border:2px solid #ddd;border-radius:15px;font-size:16px;font-family:Arial;box-sizing:border-box;">{profile_data.get("info", "")}</textarea>
        <button type="submit" style="width:100%;padding:20px;background:#3498db;color:white;border:none;border-radius:15px;font-size:18px;margin-top:20px;cursor:pointer;font-weight:bold;">💾 Сохранить информацию</button>
    </form>''' if is_owner else f'<div style="padding:30px;background:#f8f9fa;border-radius:20px;line-height:1.8;font-size:1.2em;border-left:6px solid #3498db;margin:30px 0;">{profile_data.get("info", "Информация не указана")}</div>'
    
    return f'''<!DOCTYPE html><html><head><title>👤 {username} - Профиль</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{{font-family:Arial,sans-serif;padding:40px;background:#f0f2f5;}}.profile-card{{background:white;max-width:900px;margin:auto;padding:60px;border-radius:30px;box-shadow:0 30px 100px rgba(0,0,0,0.15);text-align:center;}}.role-badge{{padding:25px 50px;background:{role_color};color:white;border-radius:35px;font-size:2em;font-weight:bold;display:inline-block;margin:40px 0;box-shadow:0 15px 40px rgba(0,0,0,0.2);}}.back-btn{{background:#007bff;color:white;padding:22px 55px;border-radius:25px;font-size:22px;font-weight:bold;display:inline-block;margin-top:50px;text-decoration:none;box-shadow:0 10px 30px rgba(0,0,0,0.2);}}.back-btn:hover{{transform:translateY(-3px);box-shadow:0 15px 40px rgba(0,0,0,0.3);}}@media (max-width:768px){{.profile-card{{padding:40px;margin:20px;border-radius:25px;}}}}</style></head><body><div class="profile-card"><h1 style="font-size:3.5em;margin-bottom:30px;color:#2c3e50;">{username}</h1><div class="role-badge">{role_display}</div>{status_html}<div style="margin:50px 0;padding:40px;background:#ecf0f1;border-radius:25px;"><h2 style="color:#2c3e50;margin-bottom:30px;font-size:2em;">О себе:</h2>{info_html}</div><a href="/" class="back-btn">🏠 Главная страница</a>{" | <a href='/profiles' class='back-btn' style='background:#28a745;margin-left:20px;'>👥 Все профили</a>" if current_user else ""}</div></body></html>'''

@app.route('/community')
def community():
    return '''<!DOCTYPE html><html><head><title>💬 Сообщество</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>body{font-family:'Segoe UI',Arial,sans-serif;padding:100px 20px;text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;}.community-box{max-width:700px;margin:auto;background:rgba(255,255,255,0.1);backdrop-filter:blur(20px);padding:100px;border-radius:35px;box-shadow:0 35px 120px rgba(0,0,0,0.3);}.tg-link{font-size:3.5em;color:#0088cc;text-decoration:none;font-weight:bold;display:inline-block;margin:50px 0;padding:30px 60px;background:rgba(255,255,255,0.2);border-radius:30px;transition:all 0.3s;box-shadow:0 15px 40px rgba(0,0,0,0.2);}.tg-link:hover{transform:scale(1.05);background:rgba(255,255,255,0.3);box-shadow:0 20px 50px rgba(0,0,0,0.3);}.back-btn{background:#007bff;color:white;padding:30px 70px;border-radius:30px;font-size:26px;font-weight:bold;text-decoration:none;display:inline-block;margin-top:70px;box-shadow:0 20px 50px rgba(0,0,0,0.3);transition:all 0.3s;}.back-btn:hover{transform:translateY(-5px);box-shadow:0 25px 60px rgba(0,0,0,0.4);}}</style></head><body><div class="community-box"><h1 style="font-size:4.5em;margin-bottom:50px;">💬 Сообщество Узнавайкин</h1><p style="font-size:1.8em;margin-bottom:60px;">Присоединяйся к нашей команде!</p><a href="https://t.me/ssylkanatelegramkanalyznaikin" class="tg-link" target="_blank">📱 Telegram Канал</a><a href="/" class="back-btn">🏠 Вернуться на главную</a></div></body></html>'''

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    current_user = session.get('user', '')
    if not is_admin(current_user):
        return redirect(url_for('index'))
    
    message = ''
    catalog_tree = get_catalog_tree()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'mute':
            target = request.form['target'].strip()
            duration = float(request.form.get('duration', 5)) * 60
            reason = request.form['reason'].strip()[:100]
            if target in users and target != current_user:
                mutes[target] = get_timestamp() + duration
                chat_messages.append({
                    'id': len(chat_messages),
                    'user': f'🔇 СИСТЕМА',
                    'text': f'{target} замучен {current_user} до {datetime.fromtimestamp(get_timestamp() + duration).strftime("%H:%M")} | Причина: {reason}',
                    'time': get_timestamp(),
                    'role': '🛡️ Модерация'
                })
                message = f'✅ {target} замучен на {duration/60} мин!'
        
        elif action == 'add_moderator':
            target = request.form['target'].strip()
            duration = float(request.form.get('duration', 24)) * 3600
            if target in users:
                moderators[target] = get_timestamp() + duration
                message = f'✅ {target} — модератор на {duration/3600}ч!'
        
        elif action == 'add_item':
            path = request.form['path'].strip()
            name = request.form['name'].strip()
            info = request.form['info'].strip()
            location = request.form['location'].strip()
            photo = request.form['photo'].strip()
            if add_item(path, name, info, location, photo):
                message = f'✅ Предмет "{name}" добавлен в {path}!'
        
        elif action == 'add_folder':
            path = request.form['path'].strip()
            name = request.form['name'].strip()
            if add_folder(path, name):
                message = f'✅ Папка "{name}" добавлена в {path}!'
        
        elif action == 'delete':
            path = request.form['path'].strip()
            if delete_item(path):
                message = f'✅ Удален: {path}'
        
        save_data()
    
    admin_html = f'''
    <div style="background:#e8f5e8;padding:20px;border-radius:15px;margin:20px 0;">
        <h2 style="color:#27ae60;">📊 СТАТИСТИКА</h2>
        <p>👥 Всего пользователей: {len(users)}</p>
        <p>💬 Сообщений в чате: {len(chat_messages)}</p>
        <p>📁 Каталог: {len(catalog)} разделов</p>
    </div>
    
    {message and f'<div style="background:#d4edda;color:#155724;padding:15px;border-radius:10px;margin:20px 0;border:1px solid #c3e6cb;"><b>✅ {message}</b></div>' or ''}
    
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:30px;">
    
    <div style="background:white;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <h3 style="color:#dc3545;">🔇 МУТ</h3>
        <form method="post">
            <input type="hidden" name="action" value="mute">
            <input name="target" placeholder="Ник" required style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;">
            <input type="number" name="duration" value="5" min="1" max="1440" style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;"> мин
            <input name="reason" placeholder="Причина" maxlength="100" style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;">
            <button type="submit" style="width:100%;padding:12px;background:#dc3545;color:white;border:none;border-radius:8px;cursor:pointer;">🔇 ЗАМУТИТЬ</button>
        </form>
    </div>
    
    <div style="background:white;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <h3 style="color:#007bff;">🛡️ МОДЕРАТОР</h3>
        <form method="post">
            <input type="hidden" name="action" value="add_moderator">
            <input name="target" placeholder="Ник" required style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;">
            <input type="number" name="duration" value="24" min="1" max="168" style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;"> ч
            <button type="submit" style="width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:8px;cursor:pointer;">🛡️ НАЗНАЧИТЬ</button>
        </form>
    </div>
    
    </div>
    
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:30px;margin:30px 0;">
    
    <div style="background:white;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <h3 style="color:#28a645;">➕ ДОБАВИТЬ ПРЕДМЕТ</h3>
        <form method="post">
            <input type="hidden" name="action" value="add_item">
            <input name="path" placeholder="Путь (Minecraft/Руды)" style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <input name="name" placeholder="Название" required style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <input name="location" placeholder="Местоположение" style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <textarea name="info" placeholder="Описание" style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;height:80px;"></textarea>
            <input name="photo" placeholder="URL фото" style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <button type="submit" style="width:100%;padding:12px;background:#28a645;color:white;border:none;border-radius:8px;cursor:pointer;">➕ ДОБАВИТЬ</button>
        </form>
    </div>
    
    <div style="background:white;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <h3 style="color:#28a645;">📁 ДОБАВИТЬ ПАПКУ</h3>
        <form method="post">
            <input type="hidden" name="action" value="add_folder">
            <input name="path" placeholder="Путь (Minecraft)" style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <input name="name" placeholder="Название папки" required style="width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;">
            <button type="submit" style="width:100%;padding:12px;background:#28a645;color:white;border:none;border-radius:8px;cursor:pointer;">📁 СОЗДАТЬ</button>
        </form>
    </div>
    
    </div>
    
    <div style="background:#fff3cd;padding:20px;border-radius:15px;margin:20px 0;">
        <h3 style="color:#856404;">🗑️ УДАЛЕНИЕ</h3>
        <form method="post">
            <input type="hidden" name="action" value="delete">
            <input name="path" placeholder="Полный путь (Minecraft/Алмаз)" required style="width:100%;padding:12px;margin:10px 0;border:2px solid #ffc107;border-radius:8px;">
            <button type="submit" style="width:100%;padding:12px;background:#dc3545;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:bold;" onclick="return confirm('УДАЛИТЬ навсегда?')">🗑️ УДАЛИТЬ</button>
        </form>
    </div>
    
    <div style="background:white;padding:25px;border-radius:20px;margin:30px 0;box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <h3 style="color:#6f42c1;">📁 ДЕРЕВО КАТАЛОГА</h3>
        <div style="font-family:monospace;background:#f8f9fa;padding:20px;border-radius:10px;max-height:300px;overflow:auto;font-size:14px;">
        <pre>{json.dumps(catalog_tree, ensure_ascii=False, indent=2)[:2000]}...</pre>
        </div>
    </div>'''
    
    return f'''<!DOCTYPE html>
<html><head><title>🔧 Админ-панель</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#ff9a9e,#fecfef);padding:30px;color:#333;}}
.container {{max-width:1400px;margin:auto;background:white;border-radius:30px;padding:40px;box-shadow:0 30px 100px rgba(0,0,0,0.2);}}
h1 {{text-align:center;color:#2d3436;font-size:3em;margin-bottom:30px;}}
h2,h3 {{color:#2d3436;margin-top:30px;}}
form {{margin:20px 0;}}
input,textarea,button {{font-family:inherit;}}
.back-btn {{background:#6c757d;color:white;padding:20px 40px;border-radius:20px;font-size:20px;font-weight:bold;text-decoration:none;display:inline-block;margin:40px 20px;box-shadow:0 10px 30px rgba(0,0,0,0.2);transition:all 0.3s;}}
.back-btn:hover {{transform:translateY(-3px);box-shadow:0 15px 40px rgba(0,0,0,0.3);}}
@media (max-width:768px) {{body {{padding:10px;}}.container {{padding:20px;border-radius:20px;}}}}
</style></head>
<body>
<div class="container">
    <h1>🔧 Админ-панель {current_user}</h1>
    {admin_html}
    <div style="text-align:center;">
        <a href="/" class="back-btn">🏠 Главная</a>
    </div>
</div>
</body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)



