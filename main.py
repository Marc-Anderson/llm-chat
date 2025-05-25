# %%
import logging
from pathlib import Path
from chat.chat import handle_prompt as _handle_prompt
from chat.entities import ChatConversation
from chat.presenter import TerminalContentPresenter

logger = logging.getLogger(__name__)


# region tools


def get_current_weather(city: str):
    """get the current weather information

    Args:
        city (str): The name of the city
    """
    return {"temperature": "25°C", "condition": "Sunny"}


def get_stock_price(symbol: str):
    """get the current stock price

    Args:
        symbol (str): The stock symbol
    """
    return {"symbol": symbol, "price": 150.00}


# endregion tools

# region setup

# choose a system prompt
system_prompt = "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired"

# initialize the conversation with the system prompt
conversation = ChatConversation([{"role": "system", "content": system_prompt}])

# define the tools available to the assistant
available_tools = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price,
}

# endregion setup


# region prompt handling


def handle_prompt(prompt: str, excluded_from_history=False):
    global conversation

    conversation = _handle_prompt(
        prompt,
        conversation,
        available_tools,
        excluded_from_history,
        TerminalContentPresenter,
    )

    return conversation


# # simulate a prompt
# prompt = "What is apples stock price"
# conversation = prompt_terminal(prompt)

# prompt = "What is happening on grand junction co this weekend?"
# conversation = handle_prompt(prompt)

while True:
    prompt = input("You: ")
    if prompt.lower() in ["exit", "quit"]:
        break
    print("")
    conversation = handle_prompt(prompt)
    print("")

conversation.save("chat_history.json")
