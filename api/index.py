import os
import random
import string
from collections import Counter

from flask import Flask, render_template, request, jsonify
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    template_folder=os.path.join(ROOT, 'templates'),
    static_folder=os.path.join(ROOT, 'static'),
)

WORD_PAIRS = [
    ("Pizza", "Burger"), ("Cat", "Dog"), ("Coffee", "Tea"), ("Beach", "Pool"),
    ("Guitar", "Violin"), ("Summer", "Spring"), ("Apple", "Pear"), ("Castle", "Mansion"),
    ("Shark", "Dolphin"), ("Snow", "Rain"), ("Sword", "Dagger"), ("Detective", "Spy"),
    ("Lion", "Tiger"), ("Pilot", "Astronaut"), ("Nurse", "Doctor"), ("Chef", "Baker"),
    ("Football", "Rugby"), ("Cinema", "Theatre"), ("Vampire", "Werewolf"), ("Witch", "Wizard"),
]


def sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])


def _make_code():
    return ''.join(random.choices(string.ascii_uppercase, k=6))


def _unique_code(client):
    for _ in range(20):
        code = _make_code()
        res = client.table('rooms').select('id').eq('code', code).execute()
        if not res.data:
            return code
    raise RuntimeError('Could not generate unique room code')


# ── Pages ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/local')
def local():
    return render_template('local.html')


@app.route('/multi')
def multi_home():
    code = request.args.get('code', '')
    return render_template('multi_home.html', prefill_code=code)


@app.route('/room/<code>')
def room(code):
    return render_template(
        'room.html',
        code=code,
        supabase_url=os.environ.get('SUPABASE_URL', ''),
        supabase_anon_key=os.environ.get('SUPABASE_ANON_KEY', ''),
    )


# ── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/rooms', methods=['POST'])
def create_room():
    data = request.json or {}
    player_id = data.get('player_id', '').strip()
    player_name = data.get('player_name', '').strip()
    if not player_id or not player_name:
        return jsonify({'error': 'Missing player_id or player_name'}), 400

    client = sb()
    code = _unique_code(client)

    room_row = client.table('rooms').insert({
        'code': code,
        'host_id': player_id,
        'status': 'waiting',
    }).execute().data[0]

    client.table('players').insert({
        'id': player_id,
        'room_id': room_row['id'],
        'name': player_name,
        'is_host': True,
    }).execute()

    return jsonify({'code': code, 'room_id': room_row['id']})


@app.route('/api/rooms/<code>/join', methods=['POST'])
def join_room(code):
    data = request.json or {}
    player_id = data.get('player_id', '').strip()
    player_name = data.get('player_name', '').strip()
    if not player_id or not player_name:
        return jsonify({'error': 'Missing fields'}), 400

    client = sb()
    room_res = client.table('rooms').select('*').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    room = room_res.data

    if room['status'] != 'waiting':
        return jsonify({'error': 'Game already started'}), 400

    # Allow rejoin by same player_id
    existing = client.table('players').select('id').eq('id', player_id).eq('room_id', room['id']).execute()
    if existing.data:
        return jsonify({'room_id': room['id']})

    name_taken = client.table('players').select('id').eq('room_id', room['id']).eq('name', player_name).execute()
    if name_taken.data:
        return jsonify({'error': 'Name already taken in this room'}), 400

    client.table('players').insert({
        'id': player_id,
        'room_id': room['id'],
        'name': player_name,
        'is_host': False,
    }).execute()

    return jsonify({'room_id': room['id']})


@app.route('/api/rooms/<code>', methods=['GET'])
def get_room(code):
    """Current room state + player list — used for rejoin/refresh."""
    client = sb()
    room_res = client.table('rooms').select('*').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    room = room_res.data

    players_res = client.table('players').select('id, name, is_host, has_seen_word, has_voted').eq('room_id', room['id']).execute()
    return jsonify({'room': room, 'players': players_res.data})


@app.route('/api/rooms/<code>/start', methods=['POST'])
def start_game(code):
    data = request.json or {}
    player_id = data.get('player_id', '').strip()
    if not player_id:
        return jsonify({'error': 'Missing player_id'}), 400

    client = sb()
    room_res = client.table('rooms').select('*').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    room = room_res.data

    if room['host_id'] != player_id:
        return jsonify({'error': 'Only the host can start the game'}), 403
    if room['status'] != 'waiting':
        return jsonify({'error': 'Game already started'}), 400

    players_res = client.table('players').select('id').eq('room_id', room['id']).execute()
    players = players_res.data
    if len(players) < 3:
        return jsonify({'error': f'Need at least 3 players (have {len(players)})'}), 400

    word = (data.get('word') or '').strip()
    imposter_word = (data.get('imposter_word') or '').strip()
    if not word or not imposter_word:
        pair = random.choice(WORD_PAIRS)
        word = word or pair[0]
        imposter_word = imposter_word or pair[1]

    imposter = random.choice(players)

    secrets = [
        {
            'player_id': p['id'],
            'word': imposter_word if p['id'] == imposter['id'] else word,
            'is_imposter': p['id'] == imposter['id'],
        }
        for p in players
    ]
    client.table('player_secrets').insert(secrets).execute()

    client.table('rooms').update({
        'status': 'playing',
        'word': word,
        'imposter_word': imposter_word,
        'imposter_id': imposter['id'],
    }).eq('id', room['id']).execute()

    return jsonify({'ok': True})


@app.route('/api/rooms/<code>/word', methods=['GET'])
def get_word(code):
    player_id = request.args.get('player_id', '').strip()
    if not player_id:
        return jsonify({'error': 'Missing player_id'}), 400

    client = sb()
    room_res = client.table('rooms').select('id').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    room_id = room_res.data['id']

    player_res = client.table('players').select('id').eq('id', player_id).eq('room_id', room_id).execute()
    if not player_res.data:
        return jsonify({'error': 'Player not in this room'}), 403

    secret_res = client.table('player_secrets').select('word, is_imposter').eq('player_id', player_id).execute()
    if not secret_res.data:
        return jsonify({'error': 'Word not assigned yet'}), 404

    s = secret_res.data[0]
    return jsonify({'word': s['word'], 'is_imposter': s['is_imposter']})


@app.route('/api/rooms/<code>/ready', methods=['POST'])
def mark_ready(code):
    data = request.json or {}
    player_id = data.get('player_id', '').strip()
    if not player_id:
        return jsonify({'error': 'Missing player_id'}), 400

    client = sb()
    client.table('players').update({'has_seen_word': True}).eq('id', player_id).execute()

    # Try atomic transition to voting
    client.rpc('try_start_voting', {'p_code': code}).execute()

    return jsonify({'ok': True})


@app.route('/api/rooms/<code>/vote', methods=['POST'])
def vote(code):
    data = request.json or {}
    player_id = data.get('player_id', '').strip()
    voted_for = data.get('voted_for', '').strip()
    if not player_id or not voted_for:
        return jsonify({'error': 'Missing player_id or voted_for'}), 400

    client = sb()
    room_res = client.table('rooms').select('status').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    if room_res.data['status'] != 'voting':
        return jsonify({'error': 'Not in voting phase'}), 400

    client.table('player_secrets').update({'vote': voted_for}).eq('player_id', player_id).execute()
    client.table('players').update({'has_voted': True}).eq('id', player_id).execute()

    # Try atomic transition to finished
    client.rpc('try_finish_game', {'p_code': code}).execute()

    return jsonify({'ok': True})


@app.route('/api/rooms/<code>/result', methods=['GET'])
def get_result(code):
    client = sb()
    room_res = client.table('rooms').select('*').eq('code', code).maybe_single().execute()
    if not room_res.data:
        return jsonify({'error': 'Room not found'}), 404
    room = room_res.data
    if room['status'] != 'finished':
        return jsonify({'error': 'Game not finished yet'}), 400

    players_res = client.table('players').select('id, name').eq('room_id', room['id']).execute()
    player_map = {p['id']: p['name'] for p in players_res.data}

    return jsonify({
        'word': room['word'],
        'imposter_word': room['imposter_word'],
        'imposter_id': room['imposter_id'],
        'imposter_name': player_map.get(room['imposter_id']),
        'voted_out_id': room['voted_out_id'],
        'voted_out_name': player_map.get(room['voted_out_id']),
        'players': [{'id': k, 'name': v} for k, v in player_map.items()],
    })
