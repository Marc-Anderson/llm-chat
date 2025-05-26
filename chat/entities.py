from pydantic import BaseModel, Field
import json


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

    def __init__(self, messages: list[ChatTurn | dict] = []):
        if messages and isinstance(messages[0], dict):
            self.messages = []
            self.load(data=messages)
        else:
            self.messages = messages

    def add(self, turn: list | ChatTurn | ToolCallTurn | ToolOutputTurn):
        """add a turn or list of turns to the conversation"""

        if isinstance(turn, list):
            self.messages.extend(turn)
        else:
            self.messages.append(turn)

    def to_api_format(self, messages=None, gemini=False) -> list[dict]:
        """Convert the conversation to the API format, removes any excluded messages and format the conversation"""

        # if data is provided, use that instead of the current messages
        message_list = messages if messages else self.messages

        output_conv = []
        current_cycle = []

        if gemini:
            # first pass: map call_id to function name for outputs
            call_id_to_name_map = {}
            for message in message_list:
                if hasattr(message, "type") and message.type == "function_call":
                    call_id_to_name_map[message.call_id] = message.name

        for idx, message in reversed(list(enumerate(message_list))):

            # convert the message to a dict if it is not already
            if not isinstance(message, dict):
                message = message.model_dump()

            # clean up the message for the api
            message_excluded = message.pop("excluded", None)

            if not gemini:
                if "arguments" in message:
                    # if this is a tool call, we need to convert the args to a string
                    message["arguments"] = json.dumps(message["arguments"])

                if "output" in message:
                    # if this is a tool call, we need to convert the args to a string
                    message["output"] = str(message["output"])

            # if this is a system message or the first message, thats it, exit
            if idx == 0 or message.get("role") == "system":
                current_cycle.append(message)
                output_conv.extend(current_cycle)
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

        result = list(reversed(output_conv))
        if gemini:
            # format the messages for gemini
            result = [
                self.gemini_formatter(message, call_id_to_name_map)
                for message in result
            ]
        return result

    @staticmethod
    def gemini_formatter(message, call_id_to_name_map):
        if message.get("role"):
            return {
                "parts": [{"text": message["content"]}],
                "role": (message["role"] if message["role"] == "user" else "model"),
            }
        elif message.get("type") == "function_call":
            return {
                "parts": [
                    {
                        "function_call": {
                            "name": message["name"],
                            "args": message["arguments"],
                        }
                    }
                ],
                "role": "model",
            }
        elif message.get("type") == "function_call_output":
            return {
                "parts": [
                    {
                        "function_response": {
                            "name": call_id_to_name_map.get(
                                message["call_id"], "unknown_function"
                            ),
                            "response": {"output": message["output"]},
                        }
                    }
                ],
                "role": "user",
            }

    @property
    def is_user_turn(self):
        """check if the last message in the conversation is an assistant turn."""
        if not self.messages:
            return False
        message_json = self.messages[-1].model_dump()
        # check if the last message is a user turn,
        if message_json.get("role") == "assistant":
            return True
        # check if the last message is a function response
        if message_json.get("type") == "function_call_output":
            return False
        return True

    def asdict(self):
        return [message.model_dump() for message in self.messages]

    def save(self, filename="conversation.json"):
        with open(filename, "w") as f:
            json.dump(self.asdict(), f, indent=4)

    def load(self, filename="conversation.json", data=None):
        if data:
            data = data
        else:
            with open(filename, "r") as f:
                data = json.load(f)

        for item in data:
            if item.get("type") == "function_call":
                turn = ToolCallTurn(**item)
            elif item.get("type") == "function_call_output":
                turn = ToolOutputTurn(**item)
            else:
                turn = ChatTurn(**item)
            self.add(turn)


if __name__ == "__main__":

    conversation_parts = [
        # {
        #     "role": "system",
        #     "content": "you are a helpful assistant",
        #     "excluded": False,
        # },
        {
            "role": "user",
            "content": "What is apples stock price",
            "excluded": False,
        },
        {
            "call_id": "call_HBMl7LmNPCAu9oca617LcciS",
            "name": "get_stock_price",
            "type": "function_call",
            "arguments": {"symbol": "AAPL"},
            "excluded": False,
        },
        {
            "call_id": "call_HBMl7LmNPCAu9oca617LcciS",
            "output": {"symbol": "AAPL", "price": 150.0},
            "type": "function_call_output",
            "excluded": False,
        },
    ]

    conversation = ChatConversation()
    conversation.load(data=conversation_parts)

    print(conversation.to_api_format())
    # conversation.save("example_conversation.json")
    # conversation.load("example_conversation.json")
    # print(conversation.asdict())
