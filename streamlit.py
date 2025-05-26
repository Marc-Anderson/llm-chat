# pip install streamlit
import datetime
from chat.chat import prompt_handler
from chat.presenter import ContentPresenter
import streamlit as st
from chat.entities import ChatConversation, ChatTurn

# streamlit run streamlit.py
# streamlit run streamlit.py --server.fileWatcherType none
today_str = datetime.datetime.today().strftime("%Y-%m-%d")


# region tools


def get_stock_price(symbol: str):
    """get the current stock price

    Args:
        symbol (str): The stock symbol
    """
    return {"symbol": symbol, "price": 150.00}


available_tools = {
    "get_stock_price": get_stock_price,
}

# endregion tools


# region system instructions


personas = {
    "Sarcastic Bot": {
        "tools": {},
        "system_prompt": "You are a sarcastic assistant. Respond to everything with excessive detail and a biting, witty tone—as if you're amazed the user even needed to ask. you are a down to earth, very simple person, dont get too wordy. just be chill, you know the drill",
        "description": "Full of dry sarcasm and wit.",
        "model": "openai",
    },
    "Gemini": {
        "tools": available_tools,
        "system_prompt": "Be eloquent, concise but very detailed, and always thoughtful. never use more words than necessary, but always provide a complete answer",
        "description": "A balanced and thoughtful conversationalist.",
        "model": "gemini",
    },
    "OpenAi": {
        "tools": available_tools,
        "system_prompt": "Be professional, polite, and comprehensive. Leave no stone unturned in your explanations, even for the simplest of questions but all responses should be very short and to the point",
        "description": "A knowledgeable and thorough assistant.",
        "model": "openai",
    },
}

# endregion system instructions


# region content presenter


class StreamlitContentPresenter(ContentPresenter):
    def __init__(
        self,
        role: str,  # who is this message from
        content: str,  # the text of the message
        static: bool = True,  # is this going to be updated?
        excluded_from_history: bool = False,  # format the message in streamlit
    ):
        self.role = role
        self.content = content
        self.excluded_from_history = excluded_from_history
        if static:
            # if the message is static, display it immediately
            with st.chat_message(role):
                st.markdown(
                    self.format_message(self.content, self.excluded_from_history)
                )
        else:
            # if the message is dynamic, create a placeholder
            with st.chat_message(role):
                self.message_placeholder = st.empty()
                self.update(self.content)

    def format_message(self, text_content, disabled=False):
        """format the message for display in the chat."""
        if disabled:
            content = f":red-background[{str(text_content)}]"
        else:
            content = text_content
        return content

    def update(self, content: str):
        self.content = content
        self.message_placeholder.markdown(
            self.format_message(self.content, self.excluded_from_history)
        )


# endregion content presenter


# region prompt handler


def handle_prompt(prompt, conversation, tools, model, excluded_from_history=False):
    # process the prompt and update the conversation
    conversation = prompt_handler(
        prompt,  # the user prompt
        conversation,  # the conversation(without the user prompt)
        tools,  # your tools lookup dictionary
        excluded_from_history,  # whether this turn should be remembered
        StreamlitContentPresenter,  # the class thats used to show the messages to the user
        model,  # the ai service you want to use
    )

    return conversation


# endregion prompt handler


# region config

st.set_page_config(initial_sidebar_state="collapsed")

# endregion config


# region sidebar

# include a sidebar with persona selection
st.sidebar.title("Chatbot Persona")
selected_persona = st.sidebar.selectbox(
    "Choose a personality:",
    list(personas.keys()),
)

# set the system prompt based on the selected persona
system_prompt = f"todays date is {today_str}. " + str(
    personas[selected_persona]["system_prompt"]
)

# endregion sidebar


# region page title

st.title("Simple Chatbot")
st.markdown(
    f"""CHATBOT PERSONA:  
    {personas[selected_persona]["description"]}"""
)

# endregion page title


# region session state

# checkbox for disabling history
if "disable_history" not in st.session_state:
    st.session_state.disable_history = False

st.checkbox(
    "Disable History",
    key="disable_history",
    value=st.session_state.disable_history,
    help="When checked, the bot will respond to your message, but will not know about the the prompt or its response in future messages. this is useful when you need to do the same task multiple times, like generating descriptions for different products.",
)

# initialize the persona in session state if it doesn't exist
if "previous_persona" not in st.session_state:
    st.session_state.previous_persona = selected_persona

# detect change in selected persona and add the new system prompt to the conversation
if selected_persona != st.session_state.previous_persona:
    # add a new system prompt to the conversation
    st.session_state.conversation.add(
        [ChatTurn(**{"role": "system", "content": system_prompt})]
    )
    # update the persona in the session state
    st.session_state.previous_persona = selected_persona

# initialize chat history in session state if it doesn't exist
if "conversation" not in st.session_state:
    # initialize a new conversation
    new_conversation = ChatConversation([{"role": "system", "content": system_prompt}])

    # add the conversation to the session state
    st.session_state.conversation = new_conversation

# endregion session state


# region utilities


def formatted_message(text_content, disabled=False):
    """format the message for display in the chat."""
    # with open("conversation.txt", "a") as f:
    #     f.write(f"{'d:' if disabled else ''} {text_content}\n")
    if disabled:
        content = f":red-background[{str(text_content)}]"
    else:
        content = text_content
    return content


# endregion utilities


# region conversation display

# display chat messages from history on every app rerun
conversation_dict_list = st.session_state.conversation.asdict()
for idx, message in enumerate(conversation_dict_list):

    # skip function call outputs, well handle them in the function calls
    if message.get("type") == "function_call_output":
        continue

    # exclude system messages from the chat history
    if message.get("role") in ["user", "assistant"] and message.get("content"):
        with st.chat_message(message["role"]):
            st.markdown(formatted_message(message["content"], message["excluded"]))

    # print function calls and their outputs in a status block
    if message.get("type") == "function_call":
        with st.status(f"calling: {message['name']}", expanded=False) as status:
            st.write(f"args: {message['arguments']}")
            if len(conversation_dict_list) > idx + 1:
                st.write(f"output: {conversation_dict_list[idx + 1]['output']}")

# region conversation display

# prompt the user for input
prompt_text = st.chat_input("Your message:")

# process user input
if prompt_text:

    try:
        conversation = handle_prompt(
            prompt_text,
            st.session_state.conversation,
            personas[selected_persona]["tools"],
            model=personas[selected_persona]["model"],
            excluded_from_history=st.session_state.disable_history,
        )

        # update the conversation in session state
        st.session_state.conversation = conversation

    except Exception as e:
        st.error(f"{e}")
        st.warning(
            "unfortunately, the bot is unable to process your request at this time. please refresh the page or try again later"
        )
