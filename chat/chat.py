import json
from chat.config import MODEL_NAME, openai_api_key
import logging
import openai
from chat.entities import ChatConversation, ChatTurn, ToolCallTurn, ToolOutputTurn
from chat.presenter import TerminalContentPresenter
from chat.tools import tool_call_handler, generate_tool_schema_openai


logger = logging.getLogger(__name__)

# load the openai api client
client = openai.OpenAI(api_key=openai_api_key)


def handle_prompt(prompt, conversation, tools, excluded_from_history, Presenter):

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
        conversation, message_placeholder, tools, excluded_from_history
    )
    return conversation


def handle_prompt_request(conversation, message_placeholder, tools={}, excluded=False):

    logger.debug("=" * 20)
    logger.debug("====== starting_chat_request ======")
    logger.debug(conversation.to_api_format())

    tool_schemas = [generate_tool_schema_openai(tool) for tool in tools.values()] + [
        {"type": "web_search_preview", "search_context_size": "low"}
    ]

    # call the api with tool definitions
    response = client.responses.create(
        model=MODEL_NAME,
        input=conversation.to_api_format(),
        store=False,
        stream=True,
        tools=tool_schemas,
    )

    # initialize a dictionary to hold the streaming data
    stream_data = {"nosave": []}

    # for event in response:
    #     stream_data["nosave"].append(event)
    #     logger.info(f"event: {event.type} - {event}")

    # process the streaming data
    for event in response:
        logger.debug(f"event: {event.type} - {event}")

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
                logger.info(f"tool_result: '{tool_output_turn.model_dump()}'")
                conversation.add(tool_output_turn)

            else:
                # get all of the text from the response
                text_output = " ".join(out.text for out in output.content)
                # create a chat turn for the assistant response and add it to the conversation
                assistant_turn = ChatTurn(
                    role=output.role, content=text_output, excluded=excluded
                )
                logger.info(f"response: '{text_output}'")
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
            tool_output_turn = tool_call_handler(function_call_turn, tools)
            conversation.add(tool_output_turn)

        # we convert web search calls to tool calls
        elif output.type == "web_search_call":
            logger.info(f"tool_call: '{output.type}'")
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
            logger.warning(
                f"unknown output type: {output.type} for output: {str(output)}"
            )

    if not conversation.is_user_turn:

        logger.info(f"recursive_call: -- calling api again with tool outputs --")

        # add the tool outputs to the conversation
        message_placeholder.update("verifying data...")

        # call the api again with the tool outputs and the conversation
        conversation = handle_prompt_request(
            conversation, message_placeholder, tools, excluded
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
                content="you are a down to earth, very simple person. never say more words than necessary. responses always leave a lot to be desired",
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

    prompt = "What is happening on grand junction co this weekend?"
    conversation = prompt_terminal(prompt)

    conversation.save("test_conversation.json")
