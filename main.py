import sys
import logging
import os
import json
from flask import Flask
from theoriq import AgentConfig, ExecuteContext, ExecuteResponse
from theoriq.biscuit import TheoriqCost
from theoriq.extra.flask import theoriq_blueprint
from theoriq.schemas import ExecuteRequestBody, TextItemBlock
from theoriq.types import Currency
from cryptogame import CryptoGame
import redis
import uuid

# Configure logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Redis client using environment variables
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD')
)

def generate_session_token():
    """Generate a unique session token."""
    return str(uuid.uuid4())

def get_session_token(context: ExecuteContext):
    """Get or create a session token for the current user."""
    session_key = f"session:{context.agent_address}"
    session_token = redis_client.get(session_key)
    if not session_token:
        session_token = generate_session_token()
        redis_client.set(session_key, session_token)
    return session_token.decode() if isinstance(session_token, bytes) else session_token

def get_game_state(session_token):
    """Get the game state for a given session token."""
    game_state_key = f"game_state:{session_token}"
    game_state = redis_client.get(game_state_key)
    return json.loads(game_state) if game_state else None

def save_game_state(session_token, game_state):
    """Save the game state for a given session token."""
    game_state_key = f"game_state:{session_token}"
    redis_client.set(game_state_key, json.dumps(game_state))

def is_new_game_request(game, user_input):
    """
    Checks if the user input indicates a new game should be started.
    """
    start_phrases = [
        "Begin the crypto adventure",
        "Welcome to the crypto adventure navigate your choices",
        "Enter the world of Web3 and start your journey",
        "Shape the future of crypto with every choice",
        ""
    ]
    return game is None or user_input.lower() in [phrase.lower() for phrase in start_phrases]

def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    """
    Handles game execution by either starting a new game, continuing an existing game, or ending a game session.
    Uses session tokens to manage individual game states for each user.
    """
    logger.info(f"Received request: {context.request_id}")
    
    # Get or create session token
    session_token = get_session_token(context)
    logger.info(f"Session token: {session_token}")

    # Extract user input from request
    last_block = req.last_item.blocks[0]
    user_input = last_block.data.text.strip()

    try:
        # Get game state for this session
        game_state = get_game_state(session_token)
        logger.info(f"Retrieved game state for session: {session_token}")
    except redis.RedisError as e:
        logger.error(f"Redis error when retrieving game state: {str(e)}")
        return context.new_response(
            blocks=[TextItemBlock(text="Sorry, we're experiencing technical difficulties. Please try again later.")],
            cost=TheoriqCost(amount=1, currency=Currency.USDC),
        )

    # Handle different game states
    if game_state is None or is_new_game_request(game_state, user_input):
        # Start new game
        game = CryptoGame()
        response = game.start_game()
    elif game_state == "GAME_OVER":
        if user_input.lower() == "yes":
            game = CryptoGame()
            response = game.start_game()
        elif user_input.lower() == "no":
            response = "Thank you for playing! The game session has ended. 🎮✨"
            try:
                redis_client.delete(f"game_state:{session_token}")
                logger.info(f"Deleted game state for session: {session_token}")
            except redis.RedisError as e:
                logger.error(f"Redis error when deleting game state: {str(e)}")
            return context.new_response(blocks=[TextItemBlock(text=response)], cost=TheoriqCost(amount=1, currency=Currency.USDC))
        else:
            response = "**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
            game = None
    else:
        # Continue existing game
        game = CryptoGame()
        game.__dict__ = game_state
        if user_input in ['1', '2', '3']:
            response = game.player_action(user_input)
        else:
            response = "Please choose option 1, 2, or 3 to continue the game."

    # Save game state
    if game is not None:
        if game.game_over:
            try:
                save_game_state(session_token, "GAME_OVER")
                logger.info(f"Set game state to GAME_OVER for session: {session_token}")
            except redis.RedisError as e:
                logger.error(f"Redis error when setting game state to GAME_OVER: {str(e)}")
            response += "\n\n**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
        else:
            try:
                save_game_state(session_token, game.__dict__)
                logger.info(f"Updated game state for session: {session_token}")
            except redis.RedisError as e:
                logger.error(f"Redis error when updating game state: {str(e)}")

    logger.info(f"The budget/cost associated with this Request: {context.budget}")

    # Create the response
    execute_response = context.new_response(
        blocks=[TextItemBlock(text=response)],
        cost=TheoriqCost(amount=1, currency=Currency.USDC),
    )

    # Log the cost of the request
    logger.info(f"Request {context.request_id} cost: {execute_response.theoriq_cost.amount} {execute_response.theoriq_cost.currency}")

    # Return response
    return execute_response

def create_app():
    """
    Create a Flask app with a single route to handle Theoriq protocol requests.
    """
    app = Flask(__name__)
    app.config['DEBUG'] = True

    agent_config = AgentConfig.from_env()
    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)

    return app

# Create Flask application
application = create_app()

# Run the application if script is executed directly
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000)