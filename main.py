# import logging
# import os
# import json
# from flask import Flask
# from theoriq import AgentConfig, ExecuteContext, ExecuteResponse
# from theoriq.biscuit import TheoriqCost
# from theoriq.extra.flask import theoriq_blueprint
# from theoriq.schemas import ExecuteRequestBody, TextItemBlock
# from theoriq.types import Currency
# from cryptogame import CryptoGame
# import redis



# logger = logging.getLogger(__name__)

# # Dictionary to store game instances for each user
# game_instances = {}

# def is_new_game_request(game, user_input):
#     start_phrases = [
#         "Begin the crypto adventure",
#         "Welcome to the crypto adventure navigate your choices",
#         "Enter the world of Web3 and start your journey",
#         "Shape the future of crypto with every choice"
#         ""
#     ]
#     return game is None or user_input in start_phrases

# def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
#     logger.info(f"Received request: {context.request_id}")
    
#     # Get the user's input from the last TextItemBlock
#     last_block = req.last_item.blocks[0]
#     user_input = last_block.data.text.strip().lower()

#     # Get or create a game instance for this user
#     game = game_instances.get(context.agent_address)
    
#     if is_new_game_request(game, user_input):
#         game = CryptoGame()
#         game_instances[context.agent_address] = game
#         response = game.start_game()
#     elif game.game_over:
#         if user_input == "yes":
#             game = CryptoGame()
#             game_instances[context.agent_address] = game
#             response = game.start_game()
#         elif user_input == "no":
#             response = "Thank you for playing! The game session has ended. 🎮✨"
#             del game_instances[context.agent_address]
#         else:
#             response = game.generate_final_feedback() + "\n\n**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
#     elif user_input in ['1', '2', '3']:
#         response = game.player_action(user_input)
#         if game.game_over:
#             response += "\n\n**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
#     else:
#         response = "Please choose option 1, 2, or 3 to continue the game."

#     # Wrap the result into an ExecuteResponse
#     return context.new_response(
#         blocks=[
#             TextItemBlock(text=response),
#         ],
#         cost=TheoriqCost(amount=1, currency=Currency.USDC),
#     )

# def create_app():
#     app = Flask(__name__)
#     app.config['DEBUG'] = True

#     agent_config = AgentConfig.from_env()
#     blueprint = theoriq_blueprint(agent_config, execute)
#     app.register_blueprint(blueprint)

#     return app

# application = create_app()

# if __name__ == "__main__":
#     application.run(host="0.0.0.0", port=8000)


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

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'))

def is_new_game_request(game, user_input):
    start_phrases = [
        "Begin the crypto adventure",
        "Welcome to the crypto adventure navigate your choices",
        "Enter the world of Web3 and start your journey",
        "Shape the future of crypto with every choice"
        ""
    ]
    return game is None or user_input in start_phrases

def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(f"Received request: {context.request_id}")
    
    # Get the user's input from the last TextItemBlock
    last_block = req.last_item.blocks[0]
    user_input = last_block.data.text.strip().lower()

    # Get or create a game instance for this user
    game_state = redis_client.get(context.agent_address)
    
    if is_new_game_request(game_state, user_input):
        game = CryptoGame()
        response = game.start_game()
    elif game_state == b"GAME_OVER":
        if user_input == "yes":
            game = CryptoGame()
            response = game.start_game()
        elif user_input == "no":
            response = "Thank you for playing! The game session has ended. 🎮✨"
            redis_client.delete(context.agent_address)
            return context.new_response(blocks=[TextItemBlock(text=response)], cost=TheoriqCost(amount=1, currency=Currency.USDC))
        else:
            response = "**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
    else:
        game = CryptoGame()
        game.__dict__ = json.loads(game_state)
        if user_input in ['1', '2', '3']:
            response = game.player_action(user_input)
        else:
            response = "Please choose option 1, 2, or 3 to continue the game."

    # Save game state
    if game.game_over:
        redis_client.set(context.agent_address, "GAME_OVER")
        response += "\n\n**Would you like to start a new game?**\n\n✅ YES\n❌ NO"
    else:
        redis_client.set(context.agent_address, json.dumps(game.__dict__))

    # Wrap the result into an ExecuteResponse
    return context.new_response(
        blocks=[
            TextItemBlock(text=response),
        ],
        cost=TheoriqCost(amount=1, currency=Currency.USDC),
    )

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True

    agent_config = AgentConfig.from_env()
    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)

    return app

application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000)