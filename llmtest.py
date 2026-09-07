from litellm import completion
from os import getenv

setting_md = "books/md/the_wild_sheep_chase_v2.md"

with open(setting_md, "r") as md:
    setting_str = md.read()

for chunk in completion(
  model="openai/gpt-5.4-mini",
  messages=[{"role": "user", "content": f"You are J.R.R Tolkien, and you're the Dungeon Master of a Dungeons and Dragons campaign. Here's the setting:\n\n{setting_str}\n\nGive an opening to describe to the players where they start. Do not offer alternative versions, variations, or follow-up options."}],
  stream=True,
):
    print(chunk.choices[0].delta.content or "", end="")