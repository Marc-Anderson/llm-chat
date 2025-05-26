# LLM Chat

# what is this

a terribly designed but simple, lightweight, and universal template for interacting with openai and gemini apis in the same application.

# what does it do

* integrates openai and google gemini apis in a single app
* provides a plug-and-play interface for tool usage
* handles prompt history and system messages
* lets you swap out display logic (terminal, streamlit, etc.)

---

## installation and setup

1. set up the python environment:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install openai google-genai
   ```

2. create a `.env` file with your api keys:

   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   ```

---

## using the template

1. **define tool functions using google-style docstrings:**

   ```py
    def get_stock_price(symbol: str):
        """get the current stock price

        Args:
            symbol (str): The stock symbol
        """
        return {"symbol": symbol, "price": 150.00}
   ```

2. **create a tool lookup dictionary:**

   ```py
   available_tools = {
       "get_stock_price": get_stock_price,
       "get_current_weather": get_current_weather,
   }
   ```

3. **initialize the conversation with a system prompt:**

   ```py
   conversation = ChatConversation([
        {"role": "system", "content": "you are a down to earth, very simple person, dont get too wordy. just be chill, you know the drill"}
    ])
   ```

4. **create a prompt handler function:**

    ```py
    def handle_prompt(prompt: str, excluded_from_history=False):
        # make the global conversation available in the function
        global conversation
        # process the prompt and update the conversation
        conversation = prompt_handler(
            prompt,                   # the user prompt
            conversation,             # the conversation(without the user prompt)
            available_tools,          # your tools lookup dictionary
            excluded_from_history,    # whether this turn should be remembered
            TerminalContentPresenter, # the class thats used to show the messages to the user
            "openai",                 # the ai service you want to use
        )

        return conversation
    ```

5. **use the handler to process user input:**

   ```py
   conversation = handle_prompt("What's the stock price of AAPL?")
   ```

6. **save the conversation to a file:**

   ```py
   conversation.save("chat_history.json")
   ```

---

## features

### excluded messages

You can hide messages from previous turns from the model, excluding messages from the history


### content presenters

You can customize how messages are displayed to users. The project includes two presenters:

* `TerminalContentPresenter`: displays messages in the terminal.
* `StreamlitContentPresenter`: displays messages using streamlit.

you can build your own presenter by inheriting from the `ContentPresenter` base class.

---

## streamlit presenter example

```py
class StreamlitContentPresenter(ContentPresenter):
    def __init__(
        self,
        role: str,                           # who is this message from
        content: str,                        # the text of the message
        static: bool = True,                 # is this going to be updated?
        excluded_from_history: bool = False, # format the message in streamlit
    ):
        self.role = role
        self.content = content
        self.excluded_from_history = excluded_from_history
        if static:
            # if the message is static, display it immediately
            with st.chat_message(role):
                st.markdown(self.format_message(self.content, self.excluded_from_history))
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
```

---

## Tests

you can hardly call these tests. they dont really test anything of substance, but they helped during development to ensure nothing broke.

run them with:

```sh
python3 -m tests.tests
```
