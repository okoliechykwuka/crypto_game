import os
import openai
import random
import dotenv
import logging

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


# Set up OpenAI API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not client.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY in Colab Secrets.")


class CryptoGame:
    def __init__(self):
        self.history = []
        self.choices_summary = []  # Store choices for final LLM analysis
        self.max_scenarios = 3  # End the game after 3 scenarios
        self.current_state = ""  # Initialize story state
        self.current_scenario = 0  # Track the current scenario number
        self.game_over = False  # Initialize game_over to False
        self.scenario_types = [
            "DeFi", "NFTs", "DAOs", "Market Trends", "Community",
            "Security", "Regulations", "Innovation", "Ethical Dilemmas",
            "New Projects", "Web3", "Partnerships", "Announcements", "TGE", "Web3 and AI Convergence", "Convergence", "AI"
        ]
        random.shuffle(self.scenario_types)
        self.emojis = ["🚀", "🔥", "💎", "💰", "🌐", "🔐", "📈", "🤝", "⚙️", "✨"]

    def generate_response(self, prompt):
        """Generate the response from the LLM with the given prompt."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a retired award-winning fiction writer who is now a crypto enthusiast with a witty and edgy sense of humor. "
                    "You are optimistic about AI and crypto, you see the positive and fun aspects, and you often have a happy ending. "
                    "Your scenarios should reflect both the highs and lows of the crypto world. "
                    "You're guiding a player through a story-rich crypto strategy game. Each decision the player makes should affect the storyline in subsequent scenarios. "
                    "Create engaging situations using typical crypto personas and backgrounds. "
                    "Where relevant, use ridiculous, multi-syllabic names for fictional coins or projects that combine popular crypto and AI terms (e.g., 'UnburdenedPepeAI', 'QuantumDeFiPup', 'MoonSharkGPT'). "
                    "Do not assume the player's experience level. "
                    "Provide 3 different choices that are specific to the scenario and represent different types of risks in crypto: moral, financial, social, and regulatory. DO NOT name the risk type in the option. "
                    "Keep the scenarios short but engaging, around 150 words. "
                    "Begin the scenario with an emoji and format choices clearly for mobile reading. "
                    "Always end with three numbered choices for the player to choose from. "
                    "Ensure that the choices are presented only once and avoid any repetition."
                )
            },
            {"role": "user", "content": prompt}
        ]

        for entry in self.history[-3:]:  # Keep context relevant but limited
            role = "user" if entry.startswith("Player:") else "assistant"
            messages.append({"role": role, "content": entry})

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                n=1,
                temperature=0.8,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return "🚨 Sorry, there was an error generating the response. Try again."

    def validate_response(self, response):
        """Check if the response contains three choices."""
        return "1." in response and "2." in response and "3." in response

    def start_game(self):
        """Start the game by generating the first scenario."""
        prompt = (
            "You are starting the game at the Token2049 Conference in Singapore. "
            "🚨 Highlight this is a game and scenarios are fiction 🚨. ""\n"
            "Present the initial scenario involving a classic Web3 and Crypto topic that will grip the user (e.g., happiness, anger, curiosity). "
            "Include different personas in the scenarios and after the scenario, offer 3 distinct choices based on the scenario. "
            "Keep it around 150 words, begin with an emoji, and you can include numbers and prices of fictitious coins or projects with ridiculous, unbelievable names. "
            "Ensure that the choices are numbered and presented only once, avoiding any repetition."
        )
        response = self.generate_response(prompt)
        # Regenerate if choices are missing
        if not self.validate_response(response):
            logger.info("Regenerating scenario to include choices...")
            response = self.generate_response(prompt + " Always end with three distinct numbered choices for the player.")
        self.history.append(f"Game: {response}")
        self.current_state = response
        return "Welcome to the AI-powered crypto strategy game!\nTest your instincts in the unpredictable world of Crypto!\n\n" + response

    def player_action(self, action):
        """Handle player actions and generate the next scenario."""
        action = action.strip()
        if action not in ['1', '2', '3']:
            return "Please enter a valid choice (1️⃣, 2️⃣, or 3️⃣)."

        self.current_scenario += 1
        self.history.append(f"Player: {action}")
        self.choices_summary.append(f"Scenario {self.current_scenario}: Chose option {action}")

        if self.current_scenario >= self.max_scenarios:
            self.game_over = True
            return self.generate_final_feedback()
        else:
            emoji = self.emojis[self.current_scenario % len(self.emojis)]
            prompt = (
                f"Based on the current storyline where the player chose option {action}, continue the narrative. "
                f"ALWAYS begin the scenario with an emoji {emoji}. Keep the scenario around 150 words and avoid specific numbers. "
                "Include different personas and offer 3 distinct choices specific to the new scenario, ensuring that the story has twists and turns. "
                "Make the outcome of each choice impactful and realistic within the crypto world, such as gaining or losing money, facing regulatory issues, or building alliances. "
                "Ensure that the choices are presented only once and avoid any repetition."
            )
            response = self.generate_response(prompt)
            if not self.validate_response(response):
                logger.info("Regenerating scenario to include choices...")
                response = self.generate_response(prompt + " Always end with three distinct numbered choices for the player.")
            self.history.append(f"Game: {response}")
            self.current_state = response
            return response


    def generate_final_feedback(self):
        """Use the LLM to generate final feedback based on user choices."""
        summary = "\n".join(self.choices_summary)
        prompt = (
            "You are a retired award-winning fiction writer turned crypto enthusiast known for your sharp wit and edgy sense of humor. "
            "You just observed a player navigate through five crypto scenarios in a strategy game. Each scenario presented them with three choices, and they made their selections thoughtfully. "
            "Now, analyze their choices and give them a final score out of 100 based on how well they navigated the volatile world of crypto. "
            "Be very brief, humorous, insightful, and engaging in your evaluation. Highlight the strengths of their decision-making, but be mindful not to encourage risky or bad behavior. "
            "Commend them for prudent decisions, and provide a final score with a very short explanation. Mention any 'penalties' if relevant (e.g., 'I should deduct 20 for degen madness, but I'll let it slide!'). "
            "Tell them to share their game score and tag @TheoriqAI."
        )
        final_feedback = self.generate_response(prompt + "\n\n" + summary)
        print(final_feedback)
        return final_feedback + "\n\n🎭 Thanks for playing! 🤖 \n🔍 Learn more about AI and Agents for Web3 at theoriq.ai 🌍 \n💡 @TheoriqAI -- Join the revolution! Our Testnet 1 is live 🚀"
