from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import uuid
import json
import difflib
import re
import string
import random
from datetime import datetime, timedelta
import secrets
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/v1/chat/completions"

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state storage
games = {}

# List of random trivia topics
RANDOM_TOPICS = [
    "World history", "Mythology", "Space exploration", "Famous authors",
    "Food and cuisine", "Famous landmarks", "Olympic history", "Pop culture"
]

def generate_game_id():
    """Generate a unique 4-character game ID."""
    while True:
        game_id = ''.join(random.choices(string.ascii_uppercase, k=4))
        if game_id not in games:
            return game_id

def get_trivia_question(topic):
    """Fetch a trivia question using the Groq API with DeepSeek."""
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        prompt = f"""
        Create a trivia question about {topic}. 
        Return your response in the following JSON format:
        {{
            "question": "The trivia question",
            "answer": "The correct answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "A brief explanation of the answer"
        }}
        Ensure the question is specific, challenging, and has a clear answer.
        """

        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response_data = response.json()

        # Extract text response
        response_text = response_data["choices"][0]["message"]["content"]
        cleaned_text = response_text.replace('`json', '').replace('`', '').strip()
        return json.loads(cleaned_text)

    except Exception as e:
        print(f"Error generating question: {str(e)}")
        return {
            "question": f"What is a notable fact about {topic}?",
            "answer": "Unable to generate answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "There was an error with the AI service."
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    username = request.form.get('username')
    if not username:
        return redirect(url_for('index'))

    game_id = generate_game_id()
    games[game_id] = {
        'host': username,
        'players': [username],
        'disconnected': set(),
        'status': 'waiting',
        'current_player_index': 0,
        'current_question': None,
        'answers': {},
        'scores': {username: 0},
        'question_start_time': None
    }

    session['game_id'] = game_id
    session['username'] = username

    return redirect(url_for('game', game_id=game_id))

@app.route('/join_game', methods=['POST'])
def join_game():
    username = request.form.get('username')
    game_id = request.form.get('game_id')

    if not username or not game_id or game_id not in games:
        return "Game not found", 404

    if games[game_id]['status'] != 'waiting':
        return "Game already in progress", 403

    if username not in games[game_id]['players']:
        games[game_id]['players'].append(username)
        games[game_id]['scores'][username] = 0

    session['game_id'] = game_id
    session['username'] = username

    return redirect(url_for('game', game_id=game_id))

@app.route('/game/<game_id>')
def game(game_id):
    if game_id not in games or session.get('username') not in games[game_id]['players']:
        return redirect(url_for('index'))

    username = session['username']
    return render_template('game.html', game_id=game_id, username=username, is_host=(username == games[game_id]['host']))

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('join_game_room')
def handle_join_game_room(data):
    game_id = data.get('game_id')
    username = data.get('username')

    if game_id in games and username in games[game_id]['players']:
        games[game_id].setdefault('disconnected', set()).discard(username)
        join_room(game_id)
        emit('player_joined', {'username': username, 'players': games[game_id]['players']}, to=game_id)

@socketio.on('start_game')
def handle_start_game(data):
    game_id = data.get('game_id')
    username = data.get('username')

    if game_id in games and username == games[game_id]['host'] and games[game_id]['status'] == 'waiting':
        games[game_id]['status'] = 'in_progress'
        emit('game_started', {
            'current_player': games[game_id]['players'][0],
            'players': games[game_id]['players'],
            'scores': games[game_id]['scores']
        }, to=game_id)

@socketio.on('select_topic')
def handle_select_topic(data):
    game_id = data.get('game_id')
    username = data.get('username')
    topic = data.get('topic')

    if game_id in games and username in games[game_id]['players'] and games[game_id]['status'] == 'in_progress':
        question_data = get_trivia_question(topic)

        games[game_id]['current_question'] = question_data
        games[game_id]['answers'] = {}
        games[game_id]['question_start_time'] = datetime.now()

        emit('question_ready', {
            'question': question_data['question'],
            'options': question_data['options'],
            'topic': topic
        }, to=game_id)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    game_id = data.get('game_id')
    username = data.get('username')
    answer = data.get('answer')

    if game_id in games and username in games[game_id]['players'] and games[game_id]['status'] == 'in_progress':
        time_elapsed = datetime.now() - games[game_id]['question_start_time']
        if time_elapsed.total_seconds() > 30:
            return  # Time is up

        correct_answer = games[game_id]['current_question']['answer']
        is_correct = answer.lower().strip() == correct_answer.lower().strip()

        if is_correct:
            games[game_id]['scores'][username] += 1

        emit('answer_result', {
            'username': username,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'scores': games[game_id]['scores']
        }, to=game_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)
