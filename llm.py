from litellm import completion
from os import getenv

def query_llm(prompt, model="openai/gpt-5.6-luna", effort="none", json=False, json_blueprint=None):
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt
    type = "text"
    if json:
        if json_blueprint == None:
            type = "json_object"
        else:
            type = "json_schema"
    response = completion(
    model=model,
    messages=messages,
    stream=False,
    reasoning_effort=effort,
    response_format={"type":type}
    )
    return response.choices[0].message.content