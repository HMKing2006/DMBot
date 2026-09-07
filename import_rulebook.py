from book_to_md import book_to_md
from llm import query_llm

rulebook_title = "DnD_BasicRules_2018"

rules_str = book_to_md(rulebook_title)
char_creation_qs = query_llm("Here are the game rules:\n\n" + rules_str + "\n\nWrite a list of questions that you must ask a player in order to make their character. Ensure questions cover all parts of one player's character sheet and nothing else. Give the minimum number of questions needed for a player at the beginning of a campaign. When a roll is needed, write ROLL[num_sides], eg. ROLL20 where d20 is needed.")
print(char_creation_qs)
