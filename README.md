# DMBot: A Discord bot that runs your roleplaying games.
Add him to your server and send him your ruleset and setting book. DMBot will:
- Memorize your setting and learn your game's rules
- Guide your server members through character creation
- Narrate and respond to players actions dynamically

You will need an OpenAI key and a Discord bot token. Duplicate the ".env.example" file, rename it to ".env", open it, and fill in your keys/tokens.

## Warning: This project is a work in progress. You should probably wait for future releases.

Technical details:
- This project is a harness for ChatGPT Luna with a ChromaDB retrieval-augmented generation system to track campaign details.
- Character sheet templates are generated dynamically as JSON files based on your ruleset. Character sheet structure is enforced, so the LLM cannot hallucinate fields.
- The LLM has access to tools for rolling dice and updating character sheets.
