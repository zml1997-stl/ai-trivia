# AI Trivia Game

An interactive multiplayer trivia game that uses Google's Gemini AI to generate questions based on player-selected topics.

## Features

- Create and join game rooms with up to 10 players
- Real-time game updates using WebSockets
- AI-generated trivia questions based on player-selected topics
- Score tracking and round results
- Responsive design for mobile and desktop

## Setup

### Prerequisites

- Python 3.8 or newer
- A Google AI Studio API key (Gemini)

### Local Development

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the project root and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
6. Run the application: `python app.py`
7. Open `http://localhost:5000` in your browser

### Deployment to Heroku

1. Create a Heroku account and install the Heroku CLI
2. Log in to Heroku: `heroku login`
3. Create a new Heroku app: `heroku create your-app-name`
4. Add your Gemini API key to Heroku config: `heroku config:set GEMINI_API_KEY=your_gemini_api_key_here`
5. Push to Heroku: `git push heroku main`
6. Open your app: `heroku open`

## File Structure

- `app.py`: Main application file with Flask routes and Socket.IO events
- `templates/`: HTML templates
  - `index.html`: Landing page with game creation and joining options
  - `game.html`: Main game interface
- `static/`: Static assets
  - `styles.css`: Custom CSS styles
- `requirements.txt`: Python dependencies
- `Procfile`: Heroku deployment configuration
- `runtime.txt`: Python version for Heroku

## How to Play

1. Create a new game or join an existing one by entering a Game ID
2. Wait for all players to join (up to 10)
3. The host starts the game
4. Players take turns selecting trivia topics
5. All players submit their answers to each question
6. View the results and scores after each round
7. Continue playing as many rounds as desired

## Technologies Used

- Flask: Web framework
- Socket.IO: Real-time communication
- Google Generative AI (Gemini): AI question generation
- Bootstrap: Frontend styling
