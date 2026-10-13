import json
from litellm import completion


def query_llm(prompt, model="openai/gpt-5.6-luna", effort="none", as_json=False, tools=None):
    """Query the model, running any tool calls until it gives a final answer.

    tools maps name -> (function, description, JSON-schema properties).
    """
    tools = tools or {}
    specs = [
        {"type": "function", "function": {"name": name, "description": desc,
         "parameters": {"type": "object", "properties": props, "required": list(props)}}}
        for name, (_, desc, props) in tools.items()
    ]
    messages, text = [{"role": "user", "content": prompt}], ""
    while True:
        message = completion(
            model=model,
            messages=messages,
            reasoning_effort=effort,
            response_format={"type": "json_object" if as_json else "text"},
            tools=specs or None,
        ).choices[0].message
        text = message.content or text  # some turns put the reply beside the tool call, not after it
        if not message.tool_calls:
            return text
        messages.append(message)
        for call in message.tool_calls:
            try:
                result = tools[call.function.name][0](**json.loads(call.function.arguments or "{}"))
            except Exception as e:
                result = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
