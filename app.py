from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
import secrets
import json
import random
import re
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta

# List of random trivia topics
RANDOM_TOPICS = [
    "3rd grade math", "Business", "2010s music", "80s nostalgia", "Famous inventions",
    "World history", "Mythology", "Animal kingdom", "Space exploration", "Famous authors",
    "Food and cuisine", "Famous landmarks", "Olympic history", "Pop culture", "Famous movie quotes",
    # ... (keeping the full list as is for brevity, you can include all items from the original)
    "History of theater", "The art of brewing", "The history of toys and games"
]

# List of emojis for player icons
PLAYER_EMOJIS = [
    "😄", "😂", "😎", "🤓", "🎉", "🚀", "🌟", "🍕", "🎸", "🎮",
    "🏆", "💡", "🌍", "🎨", "📚", "🔥", "💎", "🐱", "🐶", "🌸"
]

def generate_game_id():
    while True:
        game_id = ''.join(random.choices(string.ascii_uppercase, k=4))
        if game_id not in games:
            return game_id

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state storage
games = {}

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/play')
def play():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    username = request.form.get('username')
    if not username:
        return redirect(url_for('play'))
    
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
        'question_start_time': None,
        'player_emojis': {username: random.choice(PLAYER_EMOJIS)}  # Assign random emoji to host
    }
    
    session['game_id'] = game_id
    session['username'] = username
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/join_game', methods=['POST'])
def join_game():
    username = request.form.get('username')
    game_id = request.form.get('game_id')
    
    if not username or not game_id:
        return redirect(url_for('play'))
    
    if game_id not in games:
        return "Game not found", 404
    
    if games[game_id]['status'] != 'waiting':
        return "Game already in progress", 403
    
    if len(games[game_id]['players']) >= 10:
        return "Game is full", 403
    
    if username not in games[game_id]['players']:
        games[game_id]['players'].append(username)
        games[game_id]['scores'][username] = 0
        # Assign a unique emoji not already used in this game
        available_emojis = [e for e in PLAYER_EMOJIS if e not in games[game_id]['player_emojis'].values()]
        if available_emojis:
            games[game_id]['player_emojis'][username] = random.choice(available_emojis)
        else:
            games[game_id]['player_emojis'][username] = random.choice(PLAYER_EMOJIS)  # Fallback if no unique emoji available
    
    session['game_id'] = game_id
    session['username'] = username
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/game/<game_id>')
def game(game_id):
    if game_id not in games:
        return redirect(url_for('welcome'))
    
    username = session.get('username')
    if not username or username not in games[game_id]['players']:
        return redirect(url_for('welcome'))
    
    return render_template('game.html', game_id=game_id, username=username, is_host=(username == games[game_id]['host']))

def get_trivia_question(topic):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = f"""
        Create a trivia question about {topic}. 
        The question must be engaging, specific, and have a single, clear, unambiguous answer. 
        Return your response strictly in the following JSON format, with no additional text outside the JSON:
        {{
            "question": "The trivia question",
            "answer": "The correct answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "A concise explanation of why the answer is correct"
        }}
        Ensure the options include one correct answer and three plausible but incorrect distractors.
        Do not include any part of the answer in the question.
        Tailor the difficulty to a general audience unless otherwise specified. Try to keep questions modern,
        and something that most people would know unless the topic is specifically related to pre-modern topics.
        """

        response = model.generate_content(prompt)

        try:
            cleaned_text = response.text.replace('`json', '').replace('`', '').strip()
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Raw response text: {response.text}")
            return {
                "question": f"What is a notable fact about {topic}?",
                "answer": "Unable to generate answer",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "explanation": "There was an error parsing the AI response (JSONDecodeError)."
            }

    except Exception as e:
        print(f"Error generating question: {str(e)}")
        return {
            "question": f"What is a notable fact about {topic}?",
            "answer": "Unable to generate answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "There was an error with the AI service (General Exception)."
        }

@app.route('/final_scoreboard/<game_id>')
def final_scoreboard(game_id):
    if game_id not in games:
        return redirect(url_for('welcome'))
    return render_template('final_scoreboard.html', game_id=game_id, scores=games[game_id]['scores'], player_emojis=games[game_id]['player_emojis'])

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
        emit('player_joined', {'username': username, 'players': games[game_id]['players'], 'player_emojis': games[game_id]['player_emojis']}, to=game_id)

@socketio.on('start_game')
def handle_start_game(data):
    game_id = data.get('game_id')
    username = data.get('username')
    
    if game_id in games and username == games[game_id]['host'] and games[game_id]['status'] == 'waiting':
        games[game_id]['status'] = 'in_progress'
        current_player = games[game_id]['players'][games[game_id]['current_player_index']]
        
        emit('game_started', {
            'current_player': current_player,
            'players': games[game_id]['players'],
            'scores': games[game_id]['scores'],
            'player_emojis': games[game_id]['player_emojis']
        }, to=game_id)

@socketio.on('select_topic')
def handle_select_topic(data):
    game_id = data.get('game_id')
    username = data.get('username')
    topic = data.get('topic')

    if (game_id in games and 
        username in games[game_id]['players'] and 
        games[game_id]['status'] == 'in_progress' and
        games[game_id]['players'][games[game_id]['current_player_index']] == username):

        if 'questions_asked' not in games[game_id]:
            games[game_id]['questions_asked'] = []

        max_attempts = 5

        for _ in range(max_attempts):
            if not topic:
                topic = random.choice(RANDOM_TOPICS)
                emit('random_topic_selected', {'topic': topic}, to=game_id)

            question_data = get_trivia_question(topic)
            question_text = question_data['question']
            answer_text = question_data['answer']

            duplicate_found = False
            for prev_question, prev_answer in games[game_id]['questions_asked']:
                if answer_text == prev_answer or question_text == prev_question:
                    duplicate_found = True
                    break

            if not duplicate_found:
                games[game_id]['questions_asked'].append((question_text, answer_text))
                games[game_id]['current_question'] = question_data
                games[game_id]['answers'] = {}
                games[game_id]['question_start_time'] = datetime.now()

                emit('question_ready', {
                    'question': question_data['question'],
                    'options': question_data['options'],
                    'topic': topic
                }, to=game_id)
                return

        emit('error', {'message': "Couldn't generate a unique question. Try another topic."}, to=game_id)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    game_id = data.get('game_id')
    username = data.get('username')
    answer = data.get('answer')
    
    if (game_id in games and 
        username in games[game_id]['players'] and 
        games[game_id]['status'] == 'in_progress' and
        games[game_id]['current_question']):
        
        time_elapsed = datetime.now() - games[game_id]['question_start_time']
        if time_elapsed.total_seconds() > 30:
            answer = None

        if answer in ['A', 'B', 'C', 'D']:
            option_index = ord(answer) - ord('A')
            answer = games[game_id]['current_question']['options'][option_index]
        
        games[game_id]['answers'][username] = answer
        emit('player_answered', {'username': username}, to=game_id)
        
        if len(games[game_id]['answers']) == len(games[game_id]['players']):
            correct_answer = games[game_id]['current_question']['answer']
            correct_players = []
            
            for player, player_answer in games[game_id]['answers'].items():
                if player_answer == correct_answer:
                    correct_players.append(player)
                    games[game_id]['scores'][player] += 1
            
            # Check for game end condition (first player to 10 points)
            max_score = max(games[game_id]['scores'].values())
            if max_score >= 10:
                emit('game_ended', {
                    'scores': games[game_id]['scores'],
                    'player_emojis': games[game_id]['player_emojis']
                }, to=game_id)
                return

            # Update to the next player's turn
            games[game_id]['current_player_index'] = (games[game_id]['current_player_index'] + 1) % len(games[game_id]['players'])
            next_player = games[game_id]['players'][games[game_id]['current_player_index']]
            
            emit('round_results', {
                'correct_answer': correct_answer,
                'explanation': games[game_id]['current_question']['explanation'],
                'player_answers': games[game_id]['answers'],
                'correct_players': correct_players,
                'next_player': next_player,
                'scores': games[game_id]['scores'],
                'player_emojis': games[game_id]['player_emojis']
            }, to=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    for game_id, game in games.items():
        if username in game['players']:
            game.setdefault('disconnected', set()).add(username)
            emit('player_disconnected', {'username': username}, to=game_id)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)