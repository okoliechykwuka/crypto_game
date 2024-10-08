# CryptoGame Theoriq Agent

This project integrates the CryptoGame into the Theoriq Agent SDK. It allows players to interact with a dynamic crypto decision-making game, track their decisions, and receive final analysis after five game scenarios. The game is deployed as a Flask application, utilizing Redis for session management.

## Features

- Dynamic crypto adventure game with multiple decision paths.
- Uses Theoriq SDK for game logic and cost management.
- Redis for session persistence across game scenarios.
- Flask-based API with Gunicorn for serving the application.

## Installation

### Prerequisites
- Python 3.11
- Redis instance

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/okoliechykwuka/crypto_game.git
   cd crypto_game
   ```

2. Create a `.env` file and populate it with the required environment variables (use the `env` file template provided).

3. Build and run the Docker container:
   ```bash
   docker build -t cryptogame .
   docker run -p 8000:8000 cryptogame
   ```

4. Alternatively, to run locally:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

## Environment Variables

Ensure that the `.env` file includes the following:

- `THEORIQ_URI`: The Theoriq backend URL.
- `OPENAI_API_KEY`: OpenAI API key for processing.
- `AGENT_PRIVATE_KEY`: Agent's private key for Theoriq.
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis server details.

## Usage

The game can be started with prompts like:
- "Begin the crypto adventure"
- "Welcome to the crypto adventure"

Players make decisions through numbered choices, and the game session is managed via Redis, allowing users to continue where they left off.

