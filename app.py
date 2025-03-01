from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import uuid
import google.generativeai as genai  # Updated import
from dotenv import load_dotenv
import secrets
import json
from flask_socketio import SocketIO, emit, join_room, leave_room

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)  # This still works but we'll update the client usage below

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Game state storage
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    username = request.form.get('username')
    if not username:
        return redirect(url_for('index'))
    
    # Create a new game with a unique ID
    game_id = str(uuid.uuid4())[:8]
    games[game_id] = {
        'host': username,
        'players': [username],
        'status': 'waiting',
        'current_player_index': 0,
        'current_question': None,
        'answers': {},
        'scores': {username: 0}
    }
    
    # Set session data
    session['game_id'] = game_id
    session['username'] = username
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/join_game', methods=['POST'])
def join_game():
    username = request.form.get('username')
    game_id = request.form.get('game_id')
    
    if not username or not game_id:
        return redirect(url_for('index'))
    
    if game_id not in games:
        return "Game not found", 404
    
    if games[game_id]['status'] != 'waiting':
        return "Game already in progress", 403
    
    if len(games[game_id]['players']) >= 10:
        return "Game is full", 403
    
    # Add player to the game
    if username not in games[game_id]['players']:
        games[game_id]['players'].append(username)
        games[game_id]['scores'][username] = 0
    
    # Set session data
    session['game_id'] = game_id
    session['username'] = username
    
    return redirect(url_for('game', game_id=game_id))

@app.route('/game/<game_id>')
def game(game_id):
    if game_id not in games:
        return redirect(url_for('index'))
    
    username = session.get('username')
    if not username or username not in games[game_id]['players']:
        return redirect(url_for('index'))
    
    return render_template('game.html', game_id=game_id, username=username, is_host=(username == games[game_id]['host']))

def get_trivia_question(topic):
    try:
        # Using the updated Gemini client approach
        client = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Create a challenging trivia question about {topic}. 
        Return your response in the following JSON format:
        {{
            "question": "The trivia question",
            "answer": "The correct answer",
            "explanation": "A brief explanation of the answer"
        }}
        The question should be specific and have a clear, unambiguous answer.
        """
        
        response = client.generate_content(prompt)
        # Parse the response text as JSON
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback in case the response is not valid JSON
            print(f"Invalid JSON response: {response.text}")
            return {
                "question": f"What is a notable fact about {topic}?",
                "answer": "Unable to generate answer",
                "explanation": "There was an error parsing the AI response."
            }
            
    except Exception as e:
        print(f"Error generating question: {str(e)}")
        return {
            "question": f"What is a notable fact about {topic}?",
            "answer": "Unable to generate answer",
            "explanation": "There was an error with the AI service."
        }

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('join_game_room')
def handle_join_game_room(data):
    game_id = data.get('game_id')
    username = data.get('username')
    
    if game_id in games and username in games[game_id]['players']:
        join_room(game_id)
        emit('player_joined', {'username': username, 'players': games[game_id]['players']}, to=game_id)

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
            'scores': games[game_id]['scores']
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
        
        # Generate a question using the Gemini API
        question_data = get_trivia_question(topic)
        games[game_id]['current_question'] = question_data
        games[game_id]['answers'] = {}
        
        emit('question_ready', {
            'question': question_data['question'],
            'topic': topic
        }, to=game_id)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    game_id = data.get('game_id')
    username = data.get('username')
    answer = data.get('answer')
    
    if (game_id in games and 
        username in games[game_id]['players'] and 
        games[game_id]['status'] == 'in_progress' and
        games[game_id]['current_question']):
        
        # Store the player's answer
        games[game_id]['answers'][username] = answer
        
        # Notify all players that someone has answered
        emit('player_answered', {'username': username}, to=game_id)
        
        # Check if all players have answered
        if len(games[game_id]['answers']) == len(games[game_id]['players']):
            # Determine correct answers
            correct_answer = games[game_id]['current_question']['answer']
            correct_players = []
            
            for player, player_answer in games[game_id]['answers'].items():
                # Simple string comparison - in a real app, you might want more sophisticated matching
                if player_answer.lower().strip() == correct_answer.lower().strip():
                    correct_players.append(player)
                    games[game_id]['scores'][player] += 1
            
            # Move to the next player for the next round
            games[game_id]['current_player_index'] = (games[game_id]['current_player_index'] + 1) % len(games[game_id]['players'])
            next_player = games[game_id]['players'][games[game_id]['current_player_index']]
            
            # Send results to all players
            emit('round_results', {
                'correct_answer': correct_answer,
                'explanation': games[game_id]['current_question']['explanation'],
                'player_answers': games[game_id]['answers'],
                'correct_players': correct_players,
                'next_player': next_player,
                'scores': games[game_id]['scores']
            }, to=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    for game_id, game in list(games.items()):
        for player in list(game['players']):
            if session.get('username') == player:
                game['players'].remove(player)
                if player in game['scores']:
                    del game['scores'][player]
                
                if player == game['host'] and game['players']:
                    game['host'] = game['players'][0]
                
                emit('player_left', {'username': player, 'players': game['players']}, to=game_id)
                
                # If no players left, remove the game
                if not game['players']:
                    del games[game_id]
                    break

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
