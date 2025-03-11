from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
import secrets
import json
import random
import re
import string
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# List of random trivia topics
RANDOM_TOPICS = [
    "Famous movie quotes from the 80s", "Inventions everyone uses", "Major battles in world history", "Action movie stunts of the 90s", "Inventions that changed daily life",
    "Ancient Egyptian pyramids", "Greek mythology stories", "Unusual animal facts", "NASA moon missions", "Science fiction movie classics",
    "Popular beer brands", "Iconic landmarks everyone knows", "Olympic gold medal moments", "Netflix hit shows", "Catchphrases from classic films",
    "Lost cities in movies", "Marvel superhero movies", "Famous graffiti tags", "AI in everyday tech", "Wild parties in history",
    "Pets of US presidents", "Fashion trends of the 2000s", "Dark origins of nursery rhymes", "Broadway musical hits", "Medical breakthroughs we all know",
    "Viking warrior tales", "Legendary video game heroes", "Cool tech gadgets", "Sports team mascot stories", "Secrets in famous paintings",
    "Sitcoms with great theme songs", "Music festival moments", "Superstitions we all know", "Weird habits of world leaders", "Horror movie monsters",
    "Guitar riffs from the 70s", "Pirate adventure stories", "Renaissance artist legends", "Time travel in blockbuster movies", "Famous bank heists",
    "Car chases in action films", "Zombie movie rules", "Pop art everyone recognizes", "Disco hits of the 70s", "Political scandals everyone heard about",
    "Nicknames of big cities", "Winter holiday traditions", "Breakdance moves we’ve seen", "Board games everyone plays", "Street art in famous cities",
    "Haunted houses in movies", "Plot twists in popular films", "Women who shaped tech", "World War II spy stories", "Game show funny moments",
    "Famous duos on TV", "Con artists in the news", "Failed gadgets from the 90s", "Myths about lost islands", "Life on space stations",
    "Languages we’ve heard of", "Tattoo trends today", "Underdog sports wins", "Creatures in the ocean", "Beaches with famous stories",
    "Fashion fads by decade", "Explorers everyone knows", "Wild West cowboy tales", "Alien invasion movies", "Music genres we love",
    "Kings and queens of Africa", "Crazy war stories", "Habits of tech billionaires", "Climate change facts we know", "Ancient sports games",
    "Songs from the 60s protests", "Snacks from the 90s", "Sea monster myths", "Conspiracy theories we’ve heard", "Science facts from school",
    "Treaties that ended wars", "Cool stuff at world fairs", "Hollywood scandals of the 50s", "Math tricks we learned", "Stand-up comedy stars",
    "Weird paintings we know", "UFO stories in the news", "Silk Road treasures", "Chinese dynasty tales", "Egyptian mummy facts",
    "Music beats we recognize", "Animals we thought were gone", "Speeches we’ve heard", "Viral dances online", "Cult TV show moments",
    "Bad girls in old movies", "Rock band breakup drama", "Hip-hop fights of the 90s", "Fashion show oops moments", "Sunken ship stories",
    "Volcano eruptions we know", "Ballet dances we’ve seen", "Slasher movie deaths", "Cyber worlds in movies", "City gardening trends",
    "Dictators’ funny outfits", "Nobel Prize winners we know", "Classical music we’ve heard", "Weird ideas we’ve debated", "Cold War spy tricks",
    "Moon landing fun facts", "Famous bridges we’ve crossed", "Boy band songs of the 90s", "Meditation tips we’ve tried", "Roller coaster records",
    "Shipwrecks in movies", "Secret hideouts in history", "Video game high scores", "Chocolate candy history", "Courtroom scenes in TV",
    "Dishes by famous chefs", "Epic sports comebacks", "Toys from the 80s", "Treasure hunt legends", "Urban legends we tell",
    "Wine types we’ve tasted", "Space junk we’ve heard about", "Medieval castle tales", "Protest signs we’ve seen", "Internet memes we love",
    "Rollerblading in the 90s", "Movie soundtrack hits", "Monster sightings in lore", "Celebrity breakup gossip", "Ancient Olympic games",
    "Fast food menu hacks", "Victorian ghost stories", "Whistleblowers in the news", "Arcade game classics", "Weird laws we laugh at",
    "Books banned in school", "Extreme weather we’ve seen", "Emoji meanings we use", "Magicians we’ve watched", "Cursed movie rumors",
    "Scientists we’ve heard of", "Beauty trends we’ve tried", "Plane crash stories", "Comedy teams we love", "Lost movies found again",
    "Soda brands we drink", "Daredevil stunts on TV", "Secret clubs we’ve heard of", "Album covers we know", "Roller derby fun facts",
    "Book rivalries we’ve read", "Retro fashion we’ve worn", "Bank robbery stories", "Popcorn flavors we’ve tried", "TV shows that got canceled",
    "Recipes from grandma", "Cartoon voices we know", "Skateboarding tricks we’ve seen", "Missing person mysteries", "Train robbery legends",
    "VR games we’ve played", "Theme park ride flops", "Bubble gum brands", "Spy tricks in movies", "Sibling fights in history",
    "Pinball game themes", "Courtroom TV moments", "Firework show stories", "Celebrity pet names", "Yo-yo tricks we’ve tried",
    "Movie car chase scenes", "Hot sauce brands", "Prison escape stories", "Kite flying fun", "Stunt doubles in films",
    "Ice cream flavors we love", "Survival shows we watch", "Graffiti tags we’ve seen", "Monster truck crashes", "Jigsaw puzzle fun",
    "Celebrity nicknames we know", "Karaoke songs we sing", "TV cliffhanger endings", "Glow stick party tricks", "Circus acts we’ve seen",
    "Slapstick comedy gags", "Reality TV meltdowns", "Breakdance battles on TV", "Celebrity tattoo stories", "Snow globe scenes",
    "Movie bloopers we’ve laughed at", "Fortune cookie sayings", "TV theme song hits", "Hacky sack games", "Stunt fails on video",
    "Rubber duck designs", "Celebrity pranks we’ve seen", "Yo-yo moves we know", "TV spin-offs we’ve watched", "Frisbee games we’ve played",
    "Movie props we recognize", "Trick-or-treat stories", "Celebrity feuds in the news", "Glow-in-the-dark toys", "TV reboots we’ve seen",
    "Jump rope rhymes", "Movie poster art", "Silly string pranks", "Celebrity impersonators on TV", "Dodgeball games we’ve played",
    "TV crossover episodes", "Water balloon fight stories", "Movie trailer lines we know", "Pogo stick fun", "Celebrity book deals",
    "Hacky sack tricks we’ve tried", "Movie set mishaps", "Slinky toy fun", "TV award show moments", "Hula hoop games",
    "Celebrity cameos we’ve spotted", "Paper airplane games", "Movie opening scenes we love", "Yo-yo contest stories", "TV finale surprises",
    "Bubble wrap popping fun", "Celebrity roast jokes", "Kite surfing crashes", "Movie sequel flops", "Bouncy ball games",
    "TV pilot episodes we’ve seen", "Glow stick rave stories", "Movie villain deaths", "Hopscotch games we played", "Celebrity scandals we know",
    "Taffy candy flavors", "Movie monster looks", "Limbo dance parties", "TV guest stars we love", "Pinata party stories",
    "Movie dance scene hits", "Twister game nights", "Celebrity arrest headlines", "Balloon animal fun", "TV show locations we know",
    "Tug-of-war games", "Movie fight scenes we love", "Jacks game tricks", "Celebrity apology clips", "Yo-yo fad stories",
    "Movie costumes we recognize", "Hoppy taw fun", "TV show drama moments", "Fidget spinner crazes", "Movie taglines we quote",
    "Kite fighting stories", "Celebrity wedding gossip", "Silly putty play", "TV catchphrases we say", "Water gun fight tales",
    "Movie chase music hits", "Hacky sack champs", "Celebrity ads we’ve seen", "Bubble blowing fun", "TV show props we know",
    "Jump rope games we played", "Movie cliffhanger scenes", "Dodgeball rule twists", "Celebrity lawsuit news", "Slinky race fun"
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
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

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
        'player_emojis': {username: random.choice(PLAYER_EMOJIS)},
        'questions_asked': []
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
    
    # Allow rejoining only if the player was already in the game
    if username in games[game_id]['players']:
        session['game_id'] = game_id
        session['username'] = username
        return redirect(url_for('game', game_id=game_id))
    
    # Block new players if game is in progress or full
    if games[game_id]['status'] != 'waiting':
        return "Game already in progress", 403
    
    if len(games[game_id]['players']) >= 10:
        return "Game is full", 403
    
    # Add new player during waiting phase
    games[game_id]['players'].append(username)
    games[game_id]['scores'][username] = 0
    available_emojis = [e for e in PLAYER_EMOJIS if e not in games[game_id]['player_emojis'].values()]
    if available_emojis:
        games[game_id]['player_emojis'][username] = random.choice(available_emojis)
    else:
        games[game_id]['player_emojis'][username] = random.choice(PLAYER_EMOJIS)
    
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

@app.route('/final_scoreboard/<game_id>')
def final_scoreboard(game_id):
    if game_id not in games:
        return redirect(url_for('welcome'))
    return render_template('final_scoreboard.html', game_id=game_id, scores=games[game_id]['scores'], player_emojis=games[game_id]['player_emojis'])

@app.route('/reset_game/<game_id>', methods=['POST'])
def reset_game(game_id):
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    game['status'] = 'waiting'
    game['current_player_index'] = 0
    game['current_question'] = None
    game['answers'] = {}
    game['scores'] = {player: 0 for player in game['players']}
    game['question_start_time'] = None
    game['questions_asked'] = []
    
    logger.debug(f"Game {game_id} reset by request")
    socketio.emit('game_reset', {
        'players': game['players'],
        'scores': game['scores'],
        'player_emojis': game['player_emojis']
    }, to=game_id)
    
    return Response(status=200)

def get_trivia_question(topic):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
    Generate a well-structured trivia question about "{topic}" with a single, clear, and unambiguous answer.
    
    Requirements:
    - The question should be engaging, specific, and of average difficulty, similar to a standard trivia game.
    - The answer must be accurate and verifiable.
    - Provide four multiple-choice options: one correct answer and three plausible but incorrect distractors. At least one of these should be very plausible. 
    - Do not repeat, hint at, or include any part of the answer within the question. The wording should not make the correct answer obvious.
    - Ensure the question is broad enough that an average person might reasonably know or guess it if it is super specific.
    - The wording should feel natural and match the style of a well-crafted trivia question.
    - Keep the question modern and widely recognizable unless the topic requires historical context or are super specific topics. 
    - Return your response strictly in the following JSON format, with no additional text outside the JSON:
        {{
            "question": "The trivia question",
            "answer": "The correct answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "A concise explanation of why the answer is correct"
        }}
        """
        response = model.generate_content(prompt)
        try:
            cleaned_text = response.text.replace('`json', '').replace('`', '').strip()
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e} - Raw response text: {response.text}")
            return {
                "question": f"What is a notable fact about {topic}?",
                "answer": "Unable to generate answer",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "explanation": "There was an error parsing the AI response (JSONDecodeError)."
            }
    except Exception as e:
        logger.error(f"Error generating question: {str(e)}")
        return {
            "question": f"What is a notable fact about {topic}?",
            "answer": "Unable to generate answer",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "explanation": "There was an error with the AI service (General Exception)."
        }

# Helper function to get the next active player
def get_next_active_player(game_id):
    game = games[game_id]
    current_index = game['current_player_index']
    players = game['players']
    num_players = len(players)
    
    for _ in range(num_players):
        current_index = (current_index + 1) % num_players
        next_player = players[current_index]
        if next_player not in game['disconnected']:
            game['current_player_index'] = current_index
            return next_player
    return None

@socketio.on('connect')
def handle_connect():
    logger.debug("Client connected")

@socketio.on('join_game_room')
def handle_join_game_room(data):
    game_id = data.get('game_id')
    username = data.get('username')
    
    if game_id in games:
        if username in games[game_id]['players']:
            # Player is reconnecting
            games[game_id]['disconnected'].discard(username)
            join_room(game_id)
            logger.debug(f"Player {username} rejoined room {game_id}")
            emit('player_rejoined', {
                'username': username,
                'players': games[game_id]['players'],
                'scores': games[game_id]['scores'],
                'player_emojis': games[game_id]['player_emojis'],
                'status': games[game_id]['status'],
                'current_player': games[game_id]['players'][games[game_id]['current_player_index']] if games[game_id]['status'] == 'in_progress' else None,
                'current_question': games[game_id]['current_question'] if games[game_id]['status'] == 'in_progress' else None
            }, to=game_id)
        elif games[game_id]['status'] == 'waiting' and len(games[game_id]['players']) < 10:
            # New player joining in waiting phase
            games[game_id]['players'].append(username)
            games[game_id]['scores'][username] = 0
            available_emojis = [e for e in PLAYER_EMOJIS if e not in games[game_id]['player_emojis'].values()]
            games[game_id]['player_emojis'][username] = random.choice(available_emojis) if available_emojis else random.choice(PLAYER_EMOJIS)
            join_room(game_id)
            emit('player_joined', {
                'username': username,
                'players': games[game_id]['players'],
                'player_emojis': games[game_id]['player_emojis']
            }, to=game_id)

@socketio.on('start_game')
def handle_start_game(data):
    game_id = data.get('game_id')
    username = data.get('username')
    
    try:
        if game_id in games and username == games[game_id]['host'] and games[game_id]['status'] == 'waiting':
            games[game_id]['status'] = 'in_progress'
            current_player = games[game_id]['players'][games[game_id]['current_player_index']]
            if current_player in games[game_id]['disconnected']:
                current_player = get_next_active_player(game_id)
            logger.debug(f"Game {game_id} started by host {username}, current player: {current_player}")
            
            emit('game_started', {
                'current_player': current_player,
                'players': games[game_id]['players'],
                'scores': games[game_id]['scores'],
                'player_emojis': games[game_id]['player_emojis']
            }, to=game_id)
        else:
            logger.warning(f"Invalid start game request for game {game_id} by {username}")
    except Exception as e:
        logger.error(f"Error starting game {game_id}: {str(e)}")
        emit('error', {'message': 'Failed to start game. Please try again.'}, to=game_id)

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

        max_attempts = 10
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
                socketio.start_background_task(question_timer, game_id)
                return

        emit('error', {'message': "Couldn't generate a unique question. Try another topic."}, to=game_id)

def question_timer(game_id):
    import time
    time.sleep(30)  # 30-second timeout
    if game_id in games and games[game_id]['status'] == 'in_progress':
        active_players = [p for p in games[game_id]['players'] if p not in games[game_id]['disconnected']]
        for player in active_players:
            if player not in games[game_id]['answers']:
                games[game_id]['answers'][player] = None
        for player in games[game_id]['disconnected']:
            if player in games[game_id]['players']:
                games[game_id]['answers'][player] = None
        
        correct_answer = games[game_id]['current_question']['answer']
        correct_players = [p for p, a in games[game_id]['answers'].items() if a == correct_answer]
        for p in correct_players:
            games[game_id]['scores'][p] += 1
        
        max_score = max(games[game_id]['scores'].values())
        if max_score >= 10:
            emit('game_ended', {
                'scores': games[game_id]['scores'],
                'player_emojis': games[game_id]['player_emojis']
            }, to=game_id)
            return
        
        next_player = get_next_active_player(game_id)
        if next_player:
            games[game_id]['current_player_index'] = games[game_id]['players'].index(next_player)
            emit('round_results', {
                'correct_answer': correct_answer,
                'explanation': games[game_id]['current_question']['explanation'],
                'player_answers': games[game_id]['answers'],
                'correct_players': correct_players,
                'next_player': next_player,
                'scores': games[game_id]['scores'],
                'player_emojis': games[game_id]['player_emojis']
            }, to=game_id)
        else:
            emit('game_paused', {'message': 'No active players remaining'}, to=game_id)

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
        
        active_players = [p for p in games[game_id]['players'] if p not in games[game_id]['disconnected']]
        if len(games[game_id]['answers']) == len(active_players):
            correct_answer = games[game_id]['current_question']['answer']
            correct_players = []
            
            for player, player_answer in games[game_id]['answers'].items():
                if player_answer == correct_answer:
                    correct_players.append(player)
                    games[game_id]['scores'][player] += 1
            
            max_score = max(games[game_id]['scores'].values())
            if max_score >= 10:
                emit('game_ended', {
                    'scores': games[game_id]['scores'],
                    'player_emojis': games[game_id]['player_emojis']
                }, to=game_id)
                return

            next_player = get_next_active_player(game_id)
            if next_player:
                games[game_id]['current_player_index'] = games[game_id]['players'].index(next_player)
                emit('round_results', {
                    'correct_answer': correct_answer,
                    'explanation': games[game_id]['current_question']['explanation'],
                    'player_answers': games[game_id]['answers'],
                    'correct_players': correct_players,
                    'next_player': next_player,
                    'scores': games[game_id]['scores'],
                    'player_emojis': games[game_id]['player_emojis']
                }, to=game_id)
            else:
                emit('game_paused', {'message': 'No active players remaining'}, to=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    for game_id, game in games.items():
        if username in game['players']:
            game['disconnected'].add(username)
            emit('player_disconnected', {'username': username}, to=game_id)
            if (game['status'] == 'in_progress' and 
                game['players'][game['current_player_index']] == username):
                next_player = get_next_active_player(game_id)
                if next_player:
                    game['current_player_index'] = game['players'].index(next_player)
                    emit('turn_skipped', {
                        'disconnected_player': username,
                        'next_player': next_player
                    }, to=game_id)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)