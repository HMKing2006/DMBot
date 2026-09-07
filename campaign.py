#Defines a campaign class to keep all campaign information together.

import uuid
import chromadb
import pathlib
import re
import llm

from discord.ui.item import C

class Campaign:

    def __init__(self, id=0):
        chroma_client = chromadb.PersistentClient(path=f"data/{id}")
        self.rules = chroma_client.get_or_create_collection("rules")
        self.lore = chroma_client.get_or_create_collection("lore")


    def _ingest_md(self, path, collection, max_chars = 500):
        text = pathlib.Path(path).read_text(encoding="utf-8")
        parts = re.split(r"^(#{1,3} .+)$", text, flags=re.MULTILINE)

        chunks, header = [], ""
        for part in parts:
            if re.match(r"^#{1,3} ", part):
                header = part.strip("# ").strip()
            elif part.strip():
                body = part.strip()
                # long sections still need splitting
                for i in range(0, len(body), max_chars):
                    chunks.append((header, body[i:i + max_chars]))

        name = pathlib.Path(path).stem
        collection.upsert(
            documents=[f"{h}\n\n{b}" if h else b for h, b in chunks],
            ids=[f"{name}-{i}" for i in range(len(chunks))],
            metadatas=[
                {"source": name, "section": h}
                for h, _ in chunks
            ],
        )
    
    def _search_collection(self, prompt, collection, memory_count=10):
        output = []

        results = collection.query(query_texts=[prompt], n_results=memory_count)
        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            body_text = results["documents"][0][i]
            output.append(f"**{metadata["source"]}-{metadata["section"]}**\n{body_text}")
        
        return "\n\n".join(output)
            

    def add_rules(self, path):
        self._ingest_md(path, self.rules)
    
    def add_lore(self, path):
        self._ingest_md(path, self.lore)

    def query(self, prompt, effort="none", read_rules = True, read_lore = True, memory_count=10):
        '''
        Queries an LLM with campaign context included and returns the model's response.
        Only relevant parts of the lore and rules are retrieved as context.

        prompt (str): The prompt for the LLM to complete.
        read_rules (bool): Whether to query the game's ruleset.
        read_lore (bool): Whether to query the game's lore (campaign books and setting books).
        memory_count (int): How many sections of the ruleset and lore should be read.
            memory_count = 100 makes the model read 100 sections of the ruleset and
            100 sections of lore, each section being 2000 characters or less.
        
        str: The model's response.
        '''
        context = []
        if read_rules:
            rules_context = self._search_collection(prompt, self.rules, memory_count=memory_count)
            context.append(f"# RULES:\n{rules_context}")
        if read_lore:
            lore_context = self._search_collection(prompt, self.lore, memory_count=memory_count)
            context.append(f"# LORE:\n{lore_context}")
        context.append(prompt)

        context = "\n\n".join(context)
        return llm.query_llm(context, effort=effort)
        

c = Campaign()
c.add_rules("books/md/DnD_BasicRules_2018.md")
c.add_rules("books/md/Monster Manual.md")
print("Rules uploaded!")
c.add_lore("books/md/the_wild_sheep_chase_v2.md")
print("Lore uploaded!")
print(c.query("Plan an encounter to run on the way to the campaign. Include stat blocks."))