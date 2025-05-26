import json
from chat.config import GEMINI_MODEL_NAME, gemini_api_key
import logging
from google import genai
from chat.entities import ChatTurn, ToolCallTurn
from chat.tools import (
    generate_tool_schema_gemini,
    tool_call_handler,
)

logger = logging.getLogger(__name__)

# load the gemini api client
client = genai.Client(api_key=gemini_api_key)


def process_gemini_response(conversation, tools, message_placeholder, excluded=False):

    tool_schemas = [generate_tool_schema_gemini(tool) for tool in tools.values()]

    # call the api with tool definitions
    response = client.models.generate_content_stream(
        model=GEMINI_MODEL_NAME,
        contents=conversation.to_api_format(gemini=True),
        config={
            "response_mime_type": "text/plain",
            "tools": tool_schemas,
        },
    )

    # initialize a dictionary to hold the streaming data
    stream_data = {"nosave": [], "text": "", "function_calls": []}

    # process the streaming data
    for idx, event in enumerate(response):
        logger.debug(f"event: {event}")

        # check if the event is a delta of a text response
        if event.function_calls is None:
            # identify the unique output item index
            output_index = "text"

            # add the text delta to the response data
            if event.text.endswith("\n"):
                # if the text ends with a newline, remove it
                stream_data[output_index] += event.text[:-1]
            else:
                stream_data[output_index] += event.text

            # stream only the new delta to the console
            # gather for chat parts and display to user
            full_response = stream_data[output_index]
            message_placeholder.update(full_response + "▌")

        else:

            for fn_idx, fn in enumerate(event.function_calls):

                message_placeholder.update(f"using tool: {fn.name}...▌")

                # create a tool call turn from the output
                function_call_turn = ToolCallTurn(
                    call_id=f"fn_{idx:03d}_{fn_idx:03d}",
                    name=fn.name,
                    arguments=fn.args,
                    excluded=excluded,
                )
                conversation.add(function_call_turn)

                # call the tool call handler to get the tool output
                tool_output_turn = tool_call_handler(function_call_turn, tools)
                conversation.add(tool_output_turn)

    if stream_data["text"]:

        # create a chat turn for the assistant response and add it to the conversation
        assistant_turn = ChatTurn(
            role="assistant", content=stream_data["text"], excluded=excluded
        )
        logger.info(f"response: '{stream_data['text']}'")
        message_placeholder.update(stream_data["text"])
        conversation.add(assistant_turn)

    return conversation
