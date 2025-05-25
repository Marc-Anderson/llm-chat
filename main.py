# %%
import json
import openai
import os
import logging
from pydantic import BaseModel, Field

# from pathlib import Path

# region config

MODEL_NAME = "gpt-4.1"
CHAT_LOG_FILEPATH = "chat_log.txt"
# CHAT_LOG_FILEPATH = Path("data") / "chat_log.txt"

# endregion config


# region configure logging


logging.basicConfig(
    filename=CHAT_LOG_FILEPATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
    force=True,
)


# endregion configure logging


# region api key handling


def load_env():
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.replace('"', "").strip()


load_env()

openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )


# endregion api key handling


# region entities


class ChatTurn(BaseModel):
    role: str
    content: str
    excluded: bool = False

    @classmethod
    def from_dict(cls, data: dict, excluded=False):
        # extract content from the data dictionary and combine if it's a list
        content = data.get("content", None)
        if isinstance(content, list):
            content = "".join([item.get("text", "") for item in content])

        # decode unicode escape sequences to proper characters
        content = content.encode("utf-8").decode("unicode_escape")

        return cls(role=data["role"], content=content, excluded=excluded)


class ToolCallTurn(BaseModel):
    call_id: str
    name: str
    type: str = "function_call"
    arguments: dict = Field(default_factory=dict)
    excluded: bool = False


class ToolOutputTurn(BaseModel):
    call_id: str
    output: int | str | list | dict
    type: str = "function_call_output"
    excluded: bool = False


class ChatConversation:

    def __init__(self, messages: list[ChatTurn] = None):
        self.messages = messages

    def add(self, turn: list | ChatTurn | ToolCallTurn | ToolOutputTurn):
        """add a turn or list of turns to the conversation"""

        if isinstance(turn, list):
            self.messages.extend(turn)
        else:
            self.messages.append(turn)

    def to_api_format(self, messages=None) -> list[dict]:
        """Convert the conversation to the API format, removes any excluded messages and format the conversation"""

        # if data is provided, use that instead of the current messages
        message_list = messages if messages else self.messages

        output_conv = []
        current_cycle = []

        for idx, message in reversed(list(enumerate(message_list))):

            # convert the message to a dict if it is not already
            if not isinstance(message, dict):
                message = message.model_dump()

            # clean up the message for the api
            message_excluded = message.pop("excluded", None)

            if "arguments" in message:
                # if this is a tool call, we need to convert the args to a string
                message["arguments"] = json.dumps(message["arguments"])

            if "output" in message:
                # if this is a tool call, we need to convert the args to a string
                message["output"] = str(message["output"])

            # if this is a system message or the first message, thats it, exit
            if idx == 0 or message.get("role") == "system":
                output_conv.append(message)
                break

            # otherwise, add the message to the current turn
            current_cycle.append(message)

            # if the message is a user
            if "role" in message and message["role"] == "user":

                # if this is the last message and its a user it must be included
                if idx == len(message_list) - 1:
                    output_conv.append(message)
                    current_cycle = []
                    continue

                # assume that the assistant response is the end of every turn
                # if the last message in this turn is not assistant, add it
                if current_cycle[0].get("role", "assistant") != "assistant":
                    output_conv.extend(current_cycle)
                    current_cycle = []
                    continue

                # if the current turn is excluded
                if message_excluded:
                    current_cycle = []
                    continue

                # add the current turn to the conversation
                output_conv.extend(current_cycle)
                current_cycle = []

        return list(reversed(output_conv))

    @property
    def is_user_turn(self):
        """check if the last message in the conversation is an assistant turn."""
        if not self.messages:
            return False
        return self.messages[-1].model_dump().get("role") == "assistant"

    def asdict(self):
        return [message.model_dump() for message in self.messages]

    def save(self, filename="conversation.json"):
        with open(filename, "w") as f:
            json.dump(self.asdict(), f, indent=4)


# endregion entities


# region presenter


class ContentPresenter:
    """displays chat messages to the user"""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        self.role = role
        self.content = content
        self.excluded = excluded_from_history
        if static:
            pass
        else:
            pass

    def update(self, content: str):
        self.content = content
        pass


class TerminalContentPresenter(ContentPresenter):
    """displays chat messages to the user in the terminal"""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        super().__init__(role, content, static, excluded_from_history)
        if static:
            print(f"{role}: {self.content}")
        else:
            print(f"{role}: ", end="", flush=True)

    def update(self, content: str):
        self.content = content
        # Move cursor to start of line, clear it, re-print
        print("\r\033[K", end="", flush=True)
        print(f"{self.role}: {self.content}", end="", flush=True)


# endregion presenter


# region function calling


def tool_call_handler(tool_call_turn: ToolCallTurn):

    logging.info(
        f"tool_call: '{tool_call_turn.name}' with args: '{tool_call_turn.arguments}'"
    )

    tool_name = tool_call_turn.name
    tool_args = tool_call_turn.arguments

    # call the appropriate tool based on the tool name
    if tool_name == "get_stock_price":
        tool_result = {"price": 123}
    else:
        tool_result = "tool not recognized: " + tool_name

    # return a tooloutputturn with the result of the tool call
    tool_output_turn = ToolOutputTurn(
        call_id=tool_call_turn.call_id,
        output=tool_result,
        type="function_call_output",
        excluded=tool_call_turn.excluded,
    )

    logging.info(f"tool_result: '{tool_output_turn.model_dump()}'")

    return tool_output_turn


# endregion function calling


# region presenter


class ContentPresenter:
    """displays chat messages in the ui"""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        self.role = role
        self.content = content
        self.excluded_from_history = excluded_from_history
        if static:
            pass
        else:
            pass

    def update(self, content: str):
        self.content = content
        pass


class TerminalContentPresenter(ContentPresenter):
    """Displays chat messages in the terminal."""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        self.role = role
        self.content = content
        self.excluded_from_history = excluded_from_history
        if static:
            print(f"{role}: {self.content}")
        else:
            print(f"{role}: {self.content}", end="", flush=True)

    def update(self, content: str):
        self.content = content
        # Move cursor to start of line, clear it, re-print
        print("\r\033[K", end="", flush=True)
        print(f"{self.role}: {self.content}", end="", flush=True)


# endregion presenter


# region prompt handling


def handle_prompt(prompt, conversation, tools, excluded_from_history, Presenter):

    logging.info(f"prompt: '{prompt}'")

    # display user message in chat history
    Presenter("user", prompt, excluded_from_history=excluded_from_history)

    # create a user message
    user_message = ChatTurn("user", prompt, excluded=excluded_from_history)

    # add the user message to the conversation
    conversation.add(user_message)

    # consider using st.spinner or st.write_stream while waiting
    message_placeholder = Presenter(
        "assistant",
        "thinking...",
        static=False,
        excluded_from_history=excluded_from_history,
    )

    # process the request
    conversation = handle_prompt_request(
        conversation, message_placeholder, tools, excluded_from_history
    )
    return conversation


# load the openai api client
client = openai.OpenAI(api_key=openai_api_key)


def handle_prompt_request(conversation, message_placeholder, tools=[], excluded=False):

    logging.debug("=" * 20)
    logging.debug("starting_chat_request")
    logging.debug(conversation.to_api_format())

    # call the api with tool definitions
    response = client.responses.create(
        model=MODEL_NAME,
        input=conversation.to_api_format(),
        store=False,
        stream=True,
        tools=tools,
    )

    # initialize a dictionary to hold the streaming data
    stream_data = {"nosave": []}

    # for event in response:
    #     stream_data["nosave"].append(event)
    #     logging.info(f"event: {event.type} - {event}")

    # process the streaming data
    for event in response:
        logging.debug(f"event: {event.type} - {event}")

        # this is the start of any response
        if event.type == "response.output_item.added":
            # we add the response to the response data so we can assemble it
            stream_data[event.output_index] = event.item

        # this is the start of a streaming text response
        elif event.type == "response.content_part.added":
            # we add the response to the response data so we can assemble it
            stream_data[event.output_index].content = event.part

        # check if the event is a delta of a text response
        elif event.type == "response.output_text.delta":
            # identify the unique output item index
            output_index = event.output_index

            # ensure that the index exists in the response data
            if not stream_data[output_index]:
                raise ValueError(
                    "received 'response.output_text.delta' before 'response.output_item.added'"
                )

            # add the text delta to the response data
            stream_data[output_index].content.text += event.delta

            # web search results are not aligned with our personality, so we dont want to stream them to the user
            if stream_data[output_index].type == "web_search_call":
                message_placeholder.update("searching...▌")
                continue
            if (
                output_index > 0
                and stream_data.get(output_index - 1).type == "web_search_call"
            ):
                message_placeholder.update("searching...▌")
                continue

            # stream only the new delta to the console
            # gather for chat parts and display to user
            full_response = stream_data[output_index].content.text
            message_placeholder.update(full_response + "▌")

        # check if the event is a delta of a function call
        elif event.type == "response.function_call_arguments.delta":
            # identify the unique response item index
            index = event.output_index
            # assemble the function call arguments to the response data
            if stream_data[index]:
                stream_data[index].arguments += event.delta

            message_placeholder.update("checking tools...▌")
        else:
            stream_data["nosave"].append(event)

    # extract the final response from the stream data, this contains the full response
    final_event = event.response

    # after handling the streaming data, we use the response objects instead of the stream data
    for idx, output in enumerate(final_event.output):
        if output.type == "message":

            # web search results are not aligned with our personality, so we treat them as tool responses
            if idx != 0 and final_event.output[idx - 1].type == "web_search_call":
                message_placeholder.update("verifying data...")
                # set the output id to the previous web search call id so the model knows which tool call its for
                web_search_call_id = final_event.output[idx - 1].id

                # get all of the text from the web search response
                text_output = " ".join(out.text for out in output.content)
                tool_output_turn = ToolOutputTurn(
                    call_id=web_search_call_id, output=text_output, excluded=excluded
                )
                logging.info(f"tool_result: '{tool_output_turn.model_dump()}'")
                conversation.add(tool_output_turn)

            else:
                # get all of the text from the response
                text_output = " ".join(out.text for out in output.content)
                # create a chat turn for the assistant response and add it to the conversation
                assistant_turn = ChatTurn(
                    role=output.role, content=text_output, excluded=excluded
                )
                logging.info(f"response: '{text_output}'")
                message_placeholder.update(text_output)
                conversation.add(assistant_turn)

        # we process function calls in order they are received so we can assemble the conversation
        elif output.type == "function_call":
            message_placeholder.update(f"using tool: {output.name}...▌")
            # create a tool call turn from the output
            function_call_turn = ToolCallTurn(
                call_id=output.call_id,
                name=output.name,
                type=output.type,
                arguments=json.loads(output.arguments),
                excluded=excluded,
            )
            conversation.add(function_call_turn)

            # call the tool call handler to get the tool output
            tool_output_turn = tool_call_handler(function_call_turn)
            conversation.add(tool_output_turn)

        # we convert web search calls to tool calls
        elif output.type == "web_search_call":
            logging.info(f"tool_call: '{output.type}'")
            message_placeholder.update("searching...▌")
            # apply the necessary attributes to the tool call turn as a web search call
            tool_call_turn = ToolCallTurn(
                call_id=output.id,
                name=output.type,
                excluded=excluded,
            )
            conversation.add(tool_call_turn)

        else:
            # log an error for unknown output types so we have some visibility
            logging.warning(
                f"unknown output type: {output.type} for output: {str(output)}"
            )

    if not conversation.is_user_turn:

        logging.info(f"recursive_call: -- calling api again with tool outputs --")

        # add the tool outputs to the conversation
        message_placeholder.update("verifying data...")

        # call the api again with the tool outputs and the conversation
        conversation = handle_prompt_request(
            conversation, message_placeholder, tools, excluded
        )

    # return conversation, stream_data, event
    return conversation


# region test conversations


def testContentPresenter():
    import time

    prompt = "Can you tell me about the weather?"
    response = "The weather is sunny and warm today with a high of 25 degrees Celsius."
    # display a message in chat
    TerminalContentPresenter("user", prompt)
    # stream a message in the chat
    message_placeholder = TerminalContentPresenter(
        "assistant", "thinking...", static=False
    )
    time.sleep(2)

    full_response = ""
    for word in response.split():
        full_response += word
        message_placeholder.update(full_response)
        full_response += " "
        time.sleep(0.4)
    print("")


# endregion test conversations


# region test conversations


class ApiConversationConversionTests:

    def test_one(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[0]["role"] == "system"
        assert result[1]["content"] == "Hello, how are you?"

    def test_two(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[0]["role"] == "system"
        assert len(result) == 1

    def test_three(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
            #
            {
                "role": "user",
                "content": "Can you tell me about the weather?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "Fetching weather data...",
                "excluded": False,
            },
            {"role": "tool", "content": "the weather is sunny", "excluded": False},
            {
                "role": "assistant",
                "content": "Sure, let me check that for you.",
                "excluded": False,
            },
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[1]["content"] == "Can you tell me about the weather?"
        assert result[3]["role"] == "tool"
        assert len(result) == 5

    def test_four(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
            #
            {
                "role": "user",
                "content": "Can you tell me about the weather?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "Fetching weather data...",
                "excluded": False,
            },
            {"role": "tool", "content": "the weather is sunny", "excluded": False},
            {
                "role": "assistant",
                "content": "it looks like the weather in your area is going to be sunny",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the capital of France?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "The capital of France is Paris.",
                "excluded": True,
            },
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[1]["content"] == "Can you tell me about the weather?"
        assert result[3]["role"] == "tool"
        assert len(result) == 5

    def test_five(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
            #
            {
                "role": "user",
                "content": "Can you tell me about the weather?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "Fetching weather data...",
                "excluded": False,
            },
            {"role": "tool", "content": "the weather is sunny", "excluded": False},
            {
                "role": "assistant",
                "content": "it looks like the weather in your area is going to be sunny",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the capital of France?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "The capital of France is Paris.",
                "excluded": True,
            },
            #
            {"role": "user", "content": "Can you calculate 25 * 4?", "excluded": False},
            {
                "role": "assistant",
                "content": "The result of 25 * 4 is 100.",
                "excluded": False,
            },
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[1]["content"] == "Can you tell me about the weather?"
        assert result[3]["role"] == "tool"
        assert len(result) == 7

    def test_six(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
            #
            {
                "role": "user",
                "content": "Can you tell me about the weather?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "Fetching weather data...",
                "excluded": False,
            },
            {"role": "tool", "content": "the weather is sunny", "excluded": False},
            {
                "role": "assistant",
                "content": "it looks like the weather in your area is going to be sunny",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the capital of France?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "The capital of France is Paris.",
                "excluded": True,
            },
            #
            {"role": "user", "content": "Can you calculate 25 * 4?", "excluded": False},
            {
                "role": "assistant",
                "content": "The result of 25 * 4 is 100.",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the square root of 144?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "The square root of 144 is 12.",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "Can you recommend a good book?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "fetching movie recommendations",
                "excluded": True,
            },
            {"role": "tool", "content": "recommendations result", "excluded": True},
            # {"role": "assistant", "content": "Sure! 'To Kill a Mockingbird' by Harper Lee is a great choice.", "excluded": True},
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[-1]["content"] == "recommendations result"
        assert result[-2]["content"] == "fetching movie recommendations"
        assert result[-3]["content"] == "Can you recommend a good book?"
        assert len(result) == 12

    def test_seven(self):
        conversation = [
            {"role": "system", "content": "you are an assistant", "excluded": True},
            {"role": "user", "content": "Hello, how are you?", "excluded": True},
            {
                "role": "assistant",
                "content": "I'm good, thank you! How can I assist you today?",
                "excluded": True,
            },
            #
            {
                "role": "user",
                "content": "Can you tell me about the weather?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "Fetching weather data...",
                "excluded": False,
            },
            {"role": "tool", "content": "the weather is sunny", "excluded": False},
            {
                "role": "assistant",
                "content": "it looks like the weather in your area is going to be sunny",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the capital of France?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "The capital of France is Paris.",
                "excluded": True,
            },
            #
            {"role": "user", "content": "Can you calculate 25 * 4?", "excluded": False},
            {
                "role": "assistant",
                "content": "The result of 25 * 4 is 100.",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "What is the square root of 144?",
                "excluded": False,
            },
            {
                "role": "assistant",
                "content": "The square root of 144 is 12.",
                "excluded": False,
            },
            #
            {
                "role": "user",
                "content": "Can you recommend a good book?",
                "excluded": True,
            },
            {
                "role": "assistant",
                "content": "fetching movie recommendations",
                "excluded": True,
            },
            {"role": "tool", "content": "recommendations result", "excluded": True},
            {
                "role": "assistant",
                "content": "Sure! 'To Kill a Mockingbird' by Harper Lee is a great choice.",
                "excluded": True,
            },
        ]
        Convo = ChatConversation()
        result = Convo.to_api_format(conversation)
        assert result[-1]["content"] == "The square root of 144 is 12."
        assert result[-2]["content"] == "What is the square root of 144?"
        assert (
            result[-5]["content"]
            == "it looks like the weather in your area is going to be sunny"
        )
        assert len(result) == 9


# endregion test conversations


# region test api calls


class ApiTests:

    def test_simple(self):
        conversation_json = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "hi, how are you"}],
            },
        ]

    def test_function_call_mock(self):
        conversation_json = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "what is apples stock price now"}
                ],
            },
            {
                "type": "function_call",
                "id": "fc_68324cff2cb08191ba457dd31d4a82740ad0e8d51c2118a1",
                "call_id": "call_3bGWNi2BtdzBjtzE2gccw9AG",
                "name": "get_stock_price",
                "arguments": '{"symbol":"AAPL"}',
            },
            {
                "type": "function_call_output",
                "call_id": "call_3bGWNi2BtdzBjtzE2gccw9AG",
                "output": '{"price": 123}',
            },
        ]

    def test_web_search_mock(self):
        conversation_json = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "whats happening in town this weekend",
                    }
                ],
            },
            {
                "id": "ws_6831eca4d2788191ad10e69c74da234b0ad0e8d51c2118a1",
                "type": "web_search_call",
                "status": "completed",
            },
            {
                "id": "msg_6831eca605fc81919267979bd99a44f60ad0e8d51c2118a1",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "This weekend in Grand Junction, you can attend the Colorado Stampede PRCA Pro Rodeo at the Mesa County Fairgrounds. The rodeo features events like bareback riding, barrel racing, and bull riding. Doors open at 5:30 p.m., and the events start at 7:00 p.m. Tickets are available starting at $55. ([rodeo.tickets](https://rodeo.tickets/venue/mesa-county-fairgrounds-grand-junction/?utm_source=openai))\n\nAdditionally, the Junior College World Series begins today at Sam Suplizio Field. This event showcases top collegiate baseball talent from across the nation. ([visitgrandjunction.com](https://www.visitgrandjunction.com/blog/post/memorial-day-weekend-in-grand-junction/?utm_source=openai))\n\nFor a more relaxed experience, consider visiting the Western Colorado Botanical Gardens and Butterfly House. Located on 15 acres along the Colorado River, the gardens feature a tropical rainforest greenhouse, a butterfly house, and various outdoor gardens. ([en.wikipedia.org](https://en.wikipedia.org/wiki/Western_Colorado_Botanical_Gardens?utm_source=openai))\n\nIf you're interested in outdoor activities, the Colorado National Monument offers scenic drives, hiking, and wildlife viewing. The monument features sheer-walled canyons and unique rock formations. ([en.wikipedia.org](https://en.wikipedia.org/wiki/Colorado_National_Monument?utm_source=openai))\n\nEnjoy your weekend! ",
                    }
                ],
            },
        ]

    def test_function_call_real(self):
        available_tools = [
            {
                "type": "function",
                "name": "get_stock_price",
                "description": "Get the current stock price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The stock symbol"}
                    },
                    "additionalProperties": False,
                    "required": ["symbol"],
                },
                "strict": True,
            }
        ]
        conversation_json = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "what is apples stock price now"}
                ],
            },
        ]
        messages = [
            ChatTurn.from_dict(conversation_json[0]),
            ChatTurn.from_dict(conversation_json[1]),
        ]
        conversation = ChatConversation(messages)

        # consider using st.spinner or st.write_stream while waiting
        message_placeholder = TerminalContentPresenter(
            "assistant",
            "thinking...",
            static=False,
            excluded_from_history=False,
        )

        conversation = handle_prompt_request(
            conversation, message_placeholder, tools=available_tools, excluded=False
        )

        conversation_list = conversation.asdict()

        assert conversation_list[0]["role"] == "system"
        assert conversation_list[1]["content"] == "what is apples stock price now"
        assert conversation_list[2]["name"] == "get_stock_price"
        assert conversation_list[2]["arguments"]["symbol"] == "AAPL"
        assert conversation_list[2]["call_id"] == conversation_list[3]["call_id"]
        assert conversation_list[3]["output"]["price"] == 123
        assert conversation_list[3]["type"] == "function_call_output"

        return conversation

    def test_web_search_real(self):
        available_tools = [{"type": "web_search_preview", "search_context_size": "low"}]
        conversation_json = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "whats happwning in new york today"}
                ],
            },
        ]
        messages = [
            ChatTurn.from_dict(conversation_json[0]),
            ChatTurn.from_dict(conversation_json[1]),
        ]
        conversation = ChatConversation(messages)

        # consider using st.spinner or st.write_stream while waiting
        message_placeholder = TerminalContentPresenter(
            "assistant",
            "thinking...",
            static=False,
            excluded_from_history=False,
        )

        conversation = handle_prompt_request(
            conversation, message_placeholder, tools=available_tools, excluded=False
        )

        conversation_list = conversation.asdict()

        assert conversation_list[0]["role"] == "system"
        assert conversation_list[1]["content"] == "whats happwning in new york today"
        assert conversation_list[2]["name"] == "web_search_call"
        assert conversation_list[2]["call_id"] == conversation_list[3]["call_id"]
        assert conversation_list[3]["type"] == "function_call_output"

        return conversation


# endregion test api calls


# region tests


def run_tests():

    testContentPresenter()
    conversion = ApiConversationConversionTests()
    conversion.test_one()
    conversion.test_two()
    conversion.test_three()
    conversion.test_four()
    conversion.test_five()
    conversion.test_six()
    conversion.test_seven()
    api = ApiTests()
    api.test_function_call_real()
    api.test_web_search_real()


# endregion tests

# %%

if __name__ == "__main__":
    api = ApiTests()
    api.test_function_call_real()
    print("")
    api.test_web_search_real()
