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
    "Famous movie quotes from the 80s", "Quantum physics discoveries", "Major battles in world history", "Action movie stunts of the 90s", "Inventions that changed daily life",
    "Ancient Egyptian artifacts", "Greek mythology heroes", "Unusual animal adaptations", "NASA space mission milestones", "Science fiction novel predictions",
    "Craft beer styles around the world", "Iconic landmarks and their builders", "Olympic gold medal moments", "Netflix original series trivia", "Catchphrases from classic films",
    "Lost civilizations of the Americas", "Marvel superhero origins", "Famous street artists", "AI breakthroughs in the 21st century", "Wild parties in history",
    "Pets of US presidents", "Fashion trends of the 2000s", "Dark origins of nursery rhymes", "Broadway musical flops", "Medical uses of nanotechnology",
    "Viking exploration routes", "Legendary video game bosses", "Emerging tech gadgets", "Sports team mascot origins", "Hidden symbols in famous paintings",
    "Sitcoms with iconic theme songs", "Music festival controversies", "Origins of global superstitions", "Eccentric habits of world leaders", "Horror movie monster designs",
    "Guitar solos from the 70s", "Pirate ships and their captains", "Renaissance artist rivalries", "Time travel in blockbuster movies", "Notable heists of the 20th century",
    "Car chases in action films", "Zombie movie survival rules", "Pop art movement pioneers", "Disco hits of the 70s", "Political scandals of the 21st century",
    "Nicknames of world capitals", "Winter holiday customs worldwide", "Breakdance moves and pioneers", "Board game championship wins", "Street art scenes by city",
    "Haunted locations in the US", "Plot twists in thriller films", "Women pioneers in technology", "World War II espionage tools", "Game show prize scandals",
    "Famous duos in TV history", "Con artists and their scams", "Failed gadgets of the 90s", "Myths about lost continents", "Life aboard the International Space Station",
    "Revived ancient languages", "Tattoo styles across cultures", "Underdog wins in sports history", "Creatures of the deep ocean", "Beaches with infamous events",
    "Fashion revolutions by decade", "Explorers of the New World", "Wild West outlaw legends", "Alien invasion film tropes", "Underground music genres",
    "Rulers of African empires", "Unconventional war tactics", "Habits of tech moguls", "Myths about climate change", "Ancient sports arenas",
    "Songs of the civil rights era", "Snack foods of the 90s", "Sea monster legends", "Conspiracy theories in history", "Mind-bending physics concepts",
    "Treaties that shaped nations", "Odd exhibits at world fairs", "Hollywood scandals of the 50s", "Math problems solved by geniuses", "Stand-up comedy specials",
    "Surrealist painting techniques", "UFO incidents by country", "Silk Road trade goods", "Chinese dynasty warriors", "Egyptian tomb discoveries",
    "Key changes in music theory", "Efforts to save extinct species", "Speeches that changed history", "Viral dances of the 2010s", "Cult TV show episodes",
    "Femme fatales in film noir", "Rock band breakup stories", "Hip-hop rivalries of the 90s", "Fashion show disasters", "Sunken ships and their treasures",
    "Volcanic eruptions in history", "Ballet performances gone wrong", "Slasher film kill counts", "Cyberpunk themes in media", "Urban gardening innovations",
    "Dictators’ strange outfits", "Nobel Prize winner controversies", "Classical composer feuds", "Odd philosophical theories", "Cold War spy missions",
    "Moon landing mission details", "Famous bridges by design", "Boy band hits of the 90s", "Meditation practices worldwide", "Roller coaster engineering feats",
    "Shipwrecks with survivors", "Secret bunkers of the Cold War", "Video game world records", "Chocolate recipes through time", "Historic courtroom dramas",
    "Signature dishes by chefs", "Epic sports comebacks", "Toy fads of the 80s", "Unsolved treasure mysteries", "Urban legends by region",
    "Wine regions and their grapes", "Space debris incidents", "Medieval punishment devices", "Protest art movements", "Internet memes of the 2000s",
    "Rollerblading trick history", "Movie soundtrack composers", "Cryptozoology creature sightings", "Celebrity breakup headlines", "Ancient Olympic events",
    "Fast food chain secrets", "Victorian era ghost tales", "Whistleblowers who made history", "Arcade game hidden features", "Bizarre laws by country",
    "Books banned in history", "Extreme weather events", "Emoji evolution milestones", "Magicians and their illusions", "Cursed film productions",
    "Scientific rivalries", "Beauty trends by era", "Plane crash survival stories", "Comedy duo partnerships", "Lost films rediscovered",
    "Soda brand rivalries", "Daredevil stunt records", "Secret society symbols", "Album cover controversies", "Roller derby team names",
    "Literary rivalries", "Retro fashion revivals", "Bank robbery masterminds", "Popcorn flavor inventions", "TV show cancellation dramas",
    "Oldest recipes still used", "Cartoon voice actor roles", "Skateboarding trick inventors", "Missing persons solved cases", "Train robbery tales",
    "Virtual reality milestones", "Theme park ride failures", "Bubble gum flavor origins", "Spy gadgets in real life", "Sibling rivalries in history",
    "Pinball machine designs", "Courtroom sketch artists", "Firework display records", "Celebrity pet stories", "Yo-yo trick champions",
    "Movie car chase vehicles", "Hot sauce spice levels", "Prison escape masterminds", "Kite designs through time", "Stunt double injuries",
    "Ice cream flavor origins", "Survival show challenges", "Graffiti tag styles", "Monster truck event wins", "Jigsaw puzzle records",
    "Celebrity nickname origins", "Karaoke song hits", "TV cliffhanger resolutions", "Glow stick invention uses", "Circus act disasters",
    "Slapstick comedy stars", "Reality TV dramatic moments", "Breakdance battle victories", "Celebrity tattoo meanings", "Snow globe designs",
    "Movie blooper reels", "Fortune cookie messages", "TV theme song composers", "Hacky sack trick records", "Stunt failure stories",
    "Rubber duck variations", "Celebrity prank wars", "Yo-yo competition wins", "TV spin-off successes", "Frisbee trick inventors",
    "Movie props at auctions", "Trick-or-treat traditions", "Celebrity feud timelines", "Glow-in-the-dark toy fads", "TV reboot ratings",
    "Jump rope game variations", "Movie poster designers", "Silly string uses", "Celebrity impersonator acts", "Dodgeball rule changes",
    "TV crossover episode plots", "Water balloon fight records", "Movie trailer iconic lines", "Pogo stick jump records", "Celebrity memoir reveals",
    "Hacky sack game rules", "Movie set accident reports", "Slinky toy variations", "TV award show winners", "Hula hoop contest records",
    "Celebrity cameo roles", "Paper airplane distance records", "Movie opening scene shocks", "Yo-yo championship tricks", "TV finale plot twists",
    "Bubble wrap invention uses", "Celebrity roast highlights", "Kite surfing competition wins", "Movie sequel disappointments", "Bouncy ball trick records",
    "TV pilot episode ratings", "Glow stick rave moments", "Movie villain death scenes", "Hopscotch game styles", "Celebrity scandal timelines",
    "Taffy candy flavor history", "Movie monster designs", "Limbo dance record holders", "TV guest star surprises", "Pinata design traditions",
    "Movie dance scene classics", "Twister game rule changes", "Celebrity arrest stories", "Balloon animal art styles", "TV show filming locations",
    "Tug-of-war competition wins", "Movie fight scene choreography", "Jacks game variations", "Celebrity apology moments", "Yo-yo fad timelines",
    "Movie costume designer awards", "Hoppy taw game rules", "TV show controversy moments", "Fidget spinner design trends", "Movie tagline origins",
    "Kite fighting tournament wins", "Celebrity wedding details", "Silly putty trick uses", "TV show catchphrase origins", "Water gun battle records",
    "Movie chase scene music", "Hacky sack record holders", "Celebrity endorsement deals", "Bubble blowing contest wins", "TV show prop auctions",
    "Jump rope trick inventors", "Movie cliffhanger endings", "Dodgeball variant rules", "Celebrity lawsuit outcomes", "Slinky race records"
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
    - Provide four multiple-choice options: one correct answer and three plausible but incorrect distractors.
    - Do not repeat or hint at the answer within the question.
    - Ensure the question is broad enough that an average person might reasonably know or guess it if it is super specific.
    - Keep the question modern and widely recognizable unless the topic requires historical context. 
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