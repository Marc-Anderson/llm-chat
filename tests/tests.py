# region test conversations


from chat.chat import handle_prompt_request
from chat.entities import ChatConversation, ChatTurn
from chat.presenter import TerminalContentPresenter


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
        def get_stock_price(symbol: str):
            """get the current stock price

            Args:
                symbol (str): The stock symbol
            """
            return {"symbol": symbol, "price": 123}

        available_tools = {
            "get_stock_price": get_stock_price,
        }

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
        available_tools = {}
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
    print("running api.test_function_call_real()")
    api.test_function_call_real()
    print("running api.test_web_search_real()")
    api.test_web_search_real()


# endregion tests

# %%

if __name__ == "__main__":
    run_tests()
