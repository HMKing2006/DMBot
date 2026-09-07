from litellm import completion
from os import getenv

setting_md = "books/md/the_wild_sheep_chase_v2.md"

with open(setting_md, "r") as md:
    setting_str = md.read()

def query_llm(prompt, model="openai/gpt-5.6-luna", effort="none"):
    response = completion(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    stream=False,
    reasoning_effort=effort
    )
    return response.choices[0].message.content