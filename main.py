import logging
from pathlib import Path
from chat.chat import prompt_handler
from chat.entities import ChatConversation
from chat.presenter import TerminalContentPresenter

logger = logging.getLogger(__name__)


# region tools


def get_stock_price(symbol: str):
    """get the current stock price

    Args:
        symbol (str): The stock symbol
    """
    return {"symbol": symbol, "price": 150.00}


available_tools = {
    "get_stock_price": get_stock_price,
    # "get_current_weather": get_current_weather,
}

# endregion tools


# region conversation

conversation = ChatConversation(
    [
        {
            "role": "system",
            "content": "you are a down to earth, very simple person, dont get too wordy. just be chill, you know the drill",
        }
    ]
)

# endregion conversation


# region main


def handle_prompt(prompt: str, excluded_from_history=False):
    # make the global conversation available in the function
    global conversation
    # process the prompt and update the conversation
    conversation = prompt_handler(
        prompt,  # the user prompt
        conversation,  # the conversation(without the user prompt)
        available_tools,  # your tools lookup dictionary
        excluded_from_history,  # whether this turn should be remembered
        TerminalContentPresenter,  # the class thats used to show the messages to the user
        "openai",  # the ai service you want to use
    )

    return conversation


# endregion main


# region terminal chat


def terminal_chat():

    print("Welcome to the terminal chat!")
    print("Type your messages below. Type 'q', 'exit' or 'quit' to end the chat.")

    while True:
        prompt = input("You: ")
        # remove what you just typed so the content presenter can update the line
        print("\033[F\033[K", end="")
        if prompt.lower() in ["exit", "quit", "q"]:
            break
        conversation = handle_prompt(prompt)
        print("")

    conversation.save("chat_history.json")


# endregion terminal chat


if __name__ == "__main__":

    # sample conversation
    conversation = handle_prompt("What's the stock price of AAPL?")
    conversation.save("sample_conversation.json")

    # # terminal chat
    # terminal_chat()
