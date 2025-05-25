# purpose: generate tool schemas for api services
import re
import inspect
import logging
from chat.entities import ToolCallTurn, ToolOutputTurn

logger = logging.getLogger(__name__)


# region function calling


def tool_call_handler(
    tool_call_turn: ToolCallTurn, tools: dict[str, callable]
) -> ToolOutputTurn:
    """
    handles a tool call by dynamically invoking the appropriate tool function
    based on the tool name

    Args:
        tool_call_turn (ToolCallTurn): The tool call turn containing the tool name and arguments.
        tools (dict[str, callable]): A mapping from tool names to callable functions.

    Returns:
        ToolOutputTurn: The result of the tool call.
    """
    logger.info(
        f"tool_call: '{tool_call_turn.name}' with args: '{tool_call_turn.arguments}'"
    )

    tool_name = tool_call_turn.name
    tool_args = tool_call_turn.arguments

    tool_func = tools.get(tool_name)
    if tool_func:
        try:
            # if tool_args is a dict, unpack as kwargs
            if isinstance(tool_args, dict):
                tool_result = tool_func(**tool_args)
            else:
                tool_result = tool_func(tool_args)
        except Exception as e:
            tool_result = f"error executing tool '{tool_name}': {e}"
    else:
        tool_result = f"tool not recognized: '{tool_name}'"

    tool_output_turn = ToolOutputTurn(
        call_id=tool_call_turn.call_id,
        output=tool_result,
        type="function_call_output",
        excluded=tool_call_turn.excluded,
    )

    logger.info(f"tool_result: '{tool_output_turn.model_dump()}'")

    return tool_output_turn


# endregion function calling


# region parser


def parse_google_docstring(docstring: str) -> dict:
    """Extracts parameter descriptions from a Google-style docstring."""
    param_descriptions = {}
    in_args_section = False
    for line in docstring.splitlines():
        line = line.strip()
        if line.startswith("Args:"):
            in_args_section = True
            continue
        if in_args_section:
            if not line:
                break
            match = re.match(r"^(\w+)\s*\(([^)]*)\):\s*(.+)", line)
            if match:
                name, _, description = match.groups()
                param_descriptions[name] = description
    return param_descriptions


# endregion parser


# region tool schema generation


def generate_tool_schema_openai(func: callable) -> dict[str, any]:
    base_schema = generate_tool_schema(func)
    base_schema["type"] = "function"
    base_schema["parameters"]["additionalProperties"] = False
    base_schema["strict"] = True
    return base_schema


def generate_tool_schema_gemini(func: callable) -> dict[str, any]:
    base_schema = generate_tool_schema(func)
    base_schema["response"] = None
    return {"function_declarations": [base_schema]}


def generate_tool_schema(func: callable) -> dict[str, any]:
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func) or ""
    func_name = func.__name__

    param_docs = parse_google_docstring(docstring)

    parameters = {"type": "object", "properties": {}, "required": []}

    for name, param in signature.parameters.items():
        param_type = (
            param.annotation.__name__
            if param.annotation != inspect._empty
            else "string"
        )
        parameters["properties"][name] = {
            "type": param_type.lower()
            .replace("int", "integer")
            .replace("str", "string"),
            "description": param_docs.get(name, f"{name} parameter"),
        }
        parameters["required"].append(name)

    return {
        "description": docstring.splitlines()[0] if docstring else "",
        "name": func_name,
        "parameters": parameters,
    }


# endregion tool schema generation


if __name__ == "__main__":

    def get_current_weather(city: str):
        """get the current weather information

        Args:
            city (str): The name of the city
        """
        return {"temperature": "20°C", "condition": "Sunny"}

    def get_current_time(city: str):
        """get the current time

        Args:
            city (str): The name of the city
        """
        return "12:34 PM"

    def get_stock_price(symbol: str):
        """get the current stock price

        Args:
            symbol (str): The stock symbol
        """
        return {"symbol": symbol, "price": 150.00}

    tools = {
        "get_current_weather": get_current_weather,
        "get_current_time": get_current_time,
        "get_stock_price": get_stock_price,
    }

    for tool_name, tool_func in tools.items():
        schema = generate_tool_schema_openai(tool_func)
        print(f"Tool: {tool_name}")
        print("Schema:", schema)
        print()


x = {
    "type": "function",
    "name": "get_stock_price",
    "description": "get the current stock price",
    "parameters": {
        "type": "object",
        "properties": {"symbol": {"type": "string", "description": "The stock symbol"}},
        "additionalProperties": False,
        "required": ["symbol"],
    },
}

y = {
    "type": "function",
    "name": "get_stock_price",
    "description": "Get the current stock price",
    "parameters": {
        "type": "object",
        "properties": {"symbol": {"type": "string", "description": "The stock symbol"}},
        "additionalProperties": False,
        "required": ["symbol"],
    },
    "strict": True,
}
