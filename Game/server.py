"""
CrayonMonsters Game Server
Flask + SocketIO multiplayer server for LAN play.
"""
import sys
import os
import base64
import io
from uuid import uuid4

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ImagePredictor'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'StatGen'))

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

import config
from database import init_db, create_user, verify_user, record_match, get_user_stats
from battle_engine import BattleEngine

# Import AI modules
try:
    import numpy as np
    import tensorflow as tf
    from PIL import Image, ImageOps
    
    MODEL_PATH = os.path.join(config.IMAGE_PREDICTOR_PATH, 'doodle_model.h5')
    LABEL_PATH = os.path.join(config.IMAGE_PREDICTOR_PATH, 'label_map.npy')
    
    print("Loading ImagePredictor model...")
    model = tf.keras.models.load_model(MODEL_PATH)
    label_map = np.load(LABEL_PATH, allow_pickle=True).item()
    print("Model loaded!")
    
    from llm_client import generate_creature_stats
    from stat_engine import validate_creature
    STATGEN_AVAILABLE = True
    print("StatGen modules loaded!")
except Exception as e:
    print(f"Warning: AI modules not fully loaded: {e}")
    model = None
    label_map = None
    STATGEN_AVAILABLE = False

# Initialize Flask
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
init_db()

# ============== Game State ==============
# Active users: {username: sid}
online_users = {}

# Pending challenges: {target_username: challenger_username}
pending_challenges = {}

# Active games: {game_id: {'players': [p1, p2], 'phase': 'draw'|'battle', 'engine': BattleEngine, ...}}
active_games = {}

# User to game mapping
user_to_game = {}


# ============== Helper Functions ==============
def smart_preprocess(image_bytes):
    """Preprocess canvas image for model prediction."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("L")
        img = ImageOps.invert(img)
        
        bbox = img.getbbox()
        if bbox:
            left, upper, right, lower = bbox
            width, height = right - left, lower - upper
            pad = max(width, height) * 0.1
            cx, cy = (left + right) / 2, (upper + lower) / 2
            size = max(width, height) + pad * 2
            box = (int(cx - size / 2), int(cy - size / 2), int(cx + size / 2), int(cy + size / 2))
            img = img.crop(box)
        
        img = img.resize((28, 28), Image.Resampling.LANCZOS)
        arr = np.array(img).astype("float32") / 255.0
        
        min_val, max_val = arr.min(), arr.max()
        if max_val - min_val > 0:
            arr = (arr - min_val) / (max_val - min_val)
        arr[arr < 0.2] = 0.0
        
        return arr.reshape(1, 28, 28, 1)
    except:
        return None


def process_drawing(image_data: str) -> dict:
    """Process a drawing into a creature with stats."""
    # Set to True to enable LLM stat generation
    USE_LLM = True
    
    if not model or not STATGEN_AVAILABLE or not USE_LLM:
        # Fallback: generate mock creature with random stats
        import random
        names = ['Sketch Beast', 'Doodle Dragon', 'Crayon Critter', 'Ink Monster', 'Scribble Spirit']
        natures = ['fire', 'water', 'electric', 'normal', 'ice', 'poison']
        
        return {
            'name': random.choice(names),
            'stats': {
                'hp': random.randint(60, 120),
                'attack': random.randint(40, 90),
                'defense': random.randint(40, 90),
                'speed': random.randint(40, 90),
                'nature': random.choice(natures)
            },
            'moves': [
                {'name': 'Sketch Strike', 'category': 'active', 'effect_type': 'damage', 'effect_data': {'power': random.randint(35, 60)}, 'accuracy': 95, 'description': 'A quick drawn attack.'},
                {'name': 'Ink Splash', 'category': 'active', 'effect_type': 'stat_debuff', 'effect_data': {'target_stat': 'speed', 'percent': 15}, 'accuracy': 90, 'description': 'Slows the opponent.'},
                {'name': 'Color Boost', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'attack', 'percent': 15}, 'accuracy': 100, 'description': 'Powers up attack.'},
                {'name': 'Paper Shield', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'defense', 'percent': 15}, 'accuracy': 100, 'description': 'Raises defense.'}
            ],
            'original_image': image_data
        }
    
    try:
        # Decode image
        if "base64," in image_data:
            image_data_clean = image_data.split("base64,")[1]
        else:
            image_data_clean = image_data
        image_bytes = base64.b64decode(image_data_clean)
        
        # Predict
        tensor = smart_preprocess(image_bytes)
        if tensor is None:
            raise Exception("Preprocessing failed")
        
        preds = model.predict(tensor, verbose=0)[0]
        top_idx = preds.argmax()
        label = label_map[top_idx]
        confidence = float(preds[top_idx])
        
        # Generate stats
        raw = generate_creature_stats(label, confidence)
        if 'error' in raw:
            raise Exception(raw['error'])
        
        validated, _ = validate_creature(raw)
        validated['original_image'] = image_data
        
        return validated
        
    except Exception as e:
        print(f"Error processing drawing: {e}")
        return {
            'name': 'Sketch Monster',
            'stats': {'hp': 80, 'attack': 60, 'defense': 40, 'speed': 60, 'nature': 'normal'},
            'moves': [
                {'name': 'Scratch', 'category': 'active', 'effect_type': 'damage', 'effect_data': {'power': 35}, 'accuracy': 100, 'description': 'A quick scratch.'},
                {'name': 'Glare', 'category': 'active', 'effect_type': 'stat_debuff', 'effect_data': {'target_stat': 'speed', 'percent': 10}, 'accuracy': 90, 'description': 'An intimidating look.'},
                {'name': 'Rest', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'defense', 'percent': 15}, 'accuracy': 100, 'description': 'Defensive stance.'},
                {'name': 'Charge', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'attack', 'percent': 15}, 'accuracy': 100, 'description': 'Powers up.'}
            ],
            'original_image': image_data
        }


# ============== Routes ==============
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('lobby'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message = verify_user(username, password)
        if success:
            session['username'] = username
            return redirect(url_for('lobby'))
        else:
            error = message
    
    return render_template('login.html', error=error, mode='login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, message = create_user(username, password)
        if success:
            session['username'] = username
            return redirect(url_for('lobby'))
        else:
            error = message
    
    return render_template('login.html', error=error, mode='signup')


@app.route('/logout')
def logout():
    username = session.pop('username', None)
    if username and username in online_users:
        del online_users[username]
    return redirect(url_for('login'))


@app.route('/lobby')
def lobby():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    stats = get_user_stats(session['username'])
    return render_template('lobby.html', 
                           username=session['username'], 
                           stats=stats,
                           lan_ip=config.LAN_IP,
                           port=config.PORT)


@app.route('/draw/<game_id>')
def draw_phase(game_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if game_id not in active_games:
        return redirect(url_for('lobby'))
    return render_template('draw.html', 
                           game_id=game_id,
                           draw_time=config.DRAW_TIME_SECONDS,
                           creatures_count=config.CREATURES_PER_PLAYER)


@app.route('/team/<game_id>')
def team_preview(game_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('team.html', game_id=game_id)


@app.route('/battle/<game_id>')
def battle(game_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('battle.html', game_id=game_id)


# ============== SocketIO Events ==============
@socketio.on('connect')
def handle_connect():
    pass


@socketio.on('join_lobby')
def handle_join_lobby():
    if 'username' not in session:
        return
    
    username = session['username']
    online_users[username] = request.sid
    
    # Broadcast updated player list
    emit('player_list', list(online_users.keys()), broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    # Find and remove disconnected user
    for username, sid in list(online_users.items()):
        if sid == request.sid:
            del online_users[username]
            emit('player_list', list(online_users.keys()), broadcast=True)
            break


@socketio.on('send_challenge')
def handle_send_challenge(data):
    if 'username' not in session:
        return
    
    challenger = session['username']
    target = data.get('target')
    
    if target == challenger:
        return
    
    if target not in online_users:
        emit('error', {'message': 'Player not online'})
        return
    
    pending_challenges[target] = challenger
    
    # Send challenge notification to target
    target_sid = online_users.get(target)
    if target_sid:
        emit('challenge_received', {'from': challenger}, room=target_sid)


@socketio.on('respond_challenge')
def handle_respond_challenge(data):
    if 'username' not in session:
        return
    
    username = session['username']
    accepted = data.get('accepted', False)
    
    challenger = pending_challenges.pop(username, None)
    if not challenger:
        return
    
    if accepted:
        # Create game
        game_id = str(uuid4())[:8]
        active_games[game_id] = {
            'players': [challenger, username],
            'phase': 'draw',
            'drawings': {challenger: [], username: []},
            'creatures': {challenger: [], username: []},
            'ready': {challenger: False, username: False},
            'engine': None
        }
        user_to_game[challenger] = game_id
        user_to_game[username] = game_id
        
        # Notify both players
        challenger_sid = online_users.get(challenger)
        accepter_sid = online_users.get(username)
        
        if challenger_sid:
            emit('game_start', {'game_id': game_id}, room=challenger_sid)
        if accepter_sid:
            emit('game_start', {'game_id': game_id}, room=accepter_sid)
    else:
        # Notify challenger of decline
        challenger_sid = online_users.get(challenger)
        if challenger_sid:
            emit('challenge_declined', {'by': username}, room=challenger_sid)


@socketio.on('join_game')
def handle_join_game(data):
    game_id = data.get('game_id')
    if game_id in active_games:
        join_room(game_id)


@socketio.on('submit_drawings')
def handle_submit_drawings(data):
    if 'username' not in session:
        return
    
    username = session['username']
    game_id = user_to_game.get(username)
    
    if not game_id or game_id not in active_games:
        return
    
    game = active_games[game_id]
    drawings = data.get('drawings', [])
    
    print(f"[GAME] {username} submitted {len(drawings)} drawings")
    
    # Process each drawing into a creature
    creatures = []
    for i, drawing_data in enumerate(drawings[:config.CREATURES_PER_PLAYER]):
        print(f"[GAME] Processing drawing {i+1} of {len(drawings)} for {username}")
        creature = process_drawing(drawing_data)
        print(f"[GAME] Generated creature: {creature.get('name', 'Unknown')}")
        creatures.append(creature)
    
    # Pad with default creatures if needed
    while len(creatures) < config.CREATURES_PER_PLAYER:
        creatures.append({
            'name': 'Backup Monster',
            'stats': {'hp': 70, 'attack': 50, 'defense': 50, 'speed': 50, 'nature': 'normal'},
            'moves': [
                {'name': 'Strike', 'category': 'active', 'effect_type': 'damage', 'effect_data': {'power': 40}, 'accuracy': 100, 'description': 'Basic attack.'},
                {'name': 'Guard', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'defense', 'percent': 10}, 'accuracy': 100, 'description': 'Defensive stance.'},
                {'name': 'Haste', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'speed', 'percent': 10}, 'accuracy': 100, 'description': 'Speed up.'},
                {'name': 'Power Up', 'category': 'passive', 'effect_type': 'stat_boost', 'effect_data': {'target_stat': 'attack', 'percent': 10}, 'accuracy': 100, 'description': 'Attack up.'}
            ],
            'original_image': None
        })
    
    game['creatures'][username] = creatures
    game['ready'][username] = True
    
    # Send creatures back to player
    emit('creatures_ready', {'creatures': creatures})
    
    # Check if both players ready
    if all(game['ready'].values()):
        game['phase'] = 'battle'
        
        # Create battle engine
        p1, p2 = game['players']
        engine = BattleEngine(p1, p2)
        engine.set_team(p1, game['creatures'][p1])
        engine.set_team(p2, game['creatures'][p2])
        game['engine'] = engine
        
        # Notify both players to go to battle
        emit('go_to_battle', {'game_id': game_id}, room=game_id)


@socketio.on('get_team')
def handle_get_team(data):
    if 'username' not in session:
        return
    
    username = session['username']
    game_id = data.get('game_id')
    
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    creatures = game['creatures'].get(username, [])
    
    emit('team_data', {'creatures': creatures})


@socketio.on('ready_for_battle')
def handle_ready_for_battle(data):
    if 'username' not in session:
        return
    
    game_id = data.get('game_id')
    if game_id not in active_games:
        return
    
    # Just redirect to battle - team preview is optional viewing
    pass


@socketio.on('get_battle_state')
def handle_get_battle_state(data):
    if 'username' not in session:
        return
    
    username = session['username']
    game_id = data.get('game_id')
    
    if game_id not in active_games:
        return
    
    game = active_games[game_id]
    engine = game.get('engine')
    
    if not engine:
        return
    
    state = engine.get_state(username)
    emit('battle_state', state)


@socketio.on('select_move')
def handle_select_move(data):
    if 'username' not in session:
        return
    
    username = session['username']
    game_id = user_to_game.get(username)
    
    if not game_id or game_id not in active_games:
        return
    
    game = active_games[game_id]
    engine = game.get('engine')
    
    if not engine:
        return
    
    move_index = data.get('move_index', 0)
    engine.select_move(username, move_index)
    
    # Check if both players have selected
    if engine.both_moves_selected():
        events = engine.resolve_turn()
        
        # Send turn results to both players
        emit('turn_result', {'events': events}, room=game_id)
        
        # Check for victory
        if engine.winner:
            record_match(game['players'][0], game['players'][1], engine.winner)
            emit('battle_ended', {'winner': engine.winner}, room=game_id)
            
            # Cleanup
            for p in game['players']:
                if p in user_to_game:
                    del user_to_game[p]
            del active_games[game_id]
        else:
            # Send updated state
            for player in game['players']:
                sid = online_users.get(player)
                if sid:
                    state = engine.get_state(player)
                    emit('battle_state', state, room=sid)
    else:
        emit('waiting_for_opponent', {})


@socketio.on('switch_creature')
def handle_switch_creature(data):
    if 'username' not in session:
        return
    
    username = session['username']
    game_id = user_to_game.get(username)
    
    if not game_id or game_id not in active_games:
        return
    
    game = active_games[game_id]
    engine = game.get('engine')
    
    if not engine:
        return
    
    creature_index = data.get('index', 0)
    success = engine.switch_creature(username, creature_index)
    
    if success:
        emit('switch_complete', {})
        state = engine.get_state(username)
        emit('battle_state', state)


# ============== Main ==============
if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  CrayonMonsters Game Server")
    print(f"{'='*50}")
    print(f"  LAN IP: {config.LAN_IP}")
    print(f"  Port:   {config.PORT}")
    print(f"  URL:    http://{config.LAN_IP}:{config.PORT}")
    print(f"{'='*50}\n")
    
    socketio.run(app, host=config.HOST, port=config.PORT, debug=False)
