import json
import logging
from chat.entities import ChatConversation, ChatTurn
from chat.gemini import process_gemini_response
from chat.openai import process_openai_response
from chat.presenter import TerminalContentPresenter


logger = logging.getLogger(__name__)


def prompt_handler(
    prompt, conversation, tools, excluded_from_history, Presenter, model="openai"
):

    logger.info(f"prompt: '{prompt}'")

    # display user message in chat history
    Presenter("user", prompt, excluded_from_history=excluded_from_history)

    # create a user message
    user_message = ChatTurn(role="user", content=prompt, excluded=excluded_from_history)

    # add the user message to the conversation
    conversation.add(user_message)

    # consider using st.spinner or st.write_stream while waiting
    message_placeholder = Presenter(
        role="assistant",
        content="thinking...",
        static=False,
        excluded_from_history=excluded_from_history,
    )

    # process the request
    conversation = handle_prompt_request(
        conversation, message_placeholder, tools, excluded_from_history, model=model
    )
    return conversation


def handle_prompt_request(
    conversation, message_placeholder, tools={}, excluded=False, model="openai"
):

    logger.debug("=" * 20)
    logger.debug("====== starting_chat_request ======")
    logger.debug(conversation.to_api_format())

    logger.info(f"using model: {model}")

    if model == "gemini":
        conversation = process_gemini_response(
            conversation, tools, message_placeholder, excluded=False
        )

    elif model == "openai":
        conversation = process_openai_response(
            conversation, tools, message_placeholder, excluded=False
        )

    else:
        raise ValueError(f"Unknown model: {model}")

    if not conversation.is_user_turn:

        logger.info(f"recursive_call: -- calling api again with tool outputs --")

        # add the tool outputs to the conversation
        message_placeholder.update("verifying data...")

        # call the api again with the tool outputs and the conversation
        conversation = handle_prompt_request(
            conversation, message_placeholder, tools, excluded, model=model
        )

    # return conversation, stream_data, event
    return conversation


if __name__ == "__main__":

    def prompt_terminal(prompt: str):

        logger.info(f"prompt: '{prompt}'")

        # create a conversation object
        conversation = ChatConversation()
        conversation.add(
            ChatTurn(
                role="system",
                # content="you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                content="you are a down to earth, very simple person. always say more words than necessary. responses always leave a lot to be desired",
            )
        )
        # create a user message
        user_message = ChatTurn(role="user", content=prompt)
        # add the user message to the conversation
        conversation.add(user_message)

        # display user message in chat history
        TerminalContentPresenter(role="user", content=prompt)

        # consider using st.spinner or st.write_stream while waiting
        message_placeholder = TerminalContentPresenter(
            role="assistant",
            content="thinking...",
            static=False,
        )

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

        tools = {
            "get_current_weather": get_current_weather,
            "get_stock_price": get_stock_price,
        }

        # process the request
        conversation = handle_prompt_request(conversation, message_placeholder, tools)
        return conversation

    # # simulate a prompt
    # prompt = "What is apples stock price"
    # conversation = prompt_terminal(prompt)

    # prompt = "What is happening on grand junction co this weekend?"
    prompt = "is our galaxy spinning or is the giant ball enclosing our galaxy spinning, causing drag that pulls the galaxy in a spiral shape"
    conversation = prompt_terminal(prompt)

    conversation.save("test_conversation.json")
