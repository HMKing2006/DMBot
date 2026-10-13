#Defines a campaign class to keep all campaign information together.

import chromadb
import pathlib
import json
import random
import re
import llm
import pymupdf4llm


def roll(dice):
    """Roll dice like '4d6' or 'd20' and report each die plus the total."""
    count, sides = re.fullmatch(r"(\d*)d(\d+)", dice.strip().lower()).groups()
    rolls = [random.randint(1, int(sides)) for _ in range(int(count or 1))]
    return f"rolls={rolls} total={sum(rolls)}"


def merge(base, changes):
    """Recursively merge changes into base; non-dict values replace."""
    for key, value in changes.items():
        base[key] = merge(base[key], value) if isinstance(value, dict) and isinstance(base.get(key), dict) else value
    return base


class Campaign:

    def __init__(self, id=0):
        self.id = id
        self.path = pathlib.Path(f"data/{id}")
        for folder in ("players", "drafts"):
            (self.path / folder).mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(str(self.path))
        self.rules = chroma_client.get_or_create_collection("rules")
        self.lore = chroma_client.get_or_create_collection("lore")
        skeleton_path = self.path / "character_skeleton.json"
        self.character_skeleton = skeleton_path.read_text(encoding="utf-8") if skeleton_path.exists() else "{}"
        self.tools = {
            "roll": (roll, "Roll dice like '4d6' or 'd20'. Returns each die and the total.", {"dice": {"type": "string"}}),
            "update_sheet": (
                self.update_sheet,
                "Merge changes into a player's character sheet. Nested objects merge; other values (including lists) replace.",
                {"player_id": {"type": "string"}, "changes": {"type": "object"}},
            ),
        }

    def _ingest(self, path, collection, max_chars=500):
        path = pathlib.Path(path)
        text = pymupdf4llm.to_markdown(path) if path.suffix == ".pdf" else path.read_text(encoding="utf-8")
        chunks, header = [], ""
        for part in re.split(r"^(#{1,3} .+)$", text, flags=re.MULTILINE):
            if re.match(r"^#{1,3} ", part):
                header = part.strip("# ").strip()
            elif body := part.strip():
                # long sections still need splitting
                chunks += [(header, body[i:i + max_chars]) for i in range(0, len(body), max_chars)]
        collection.upsert(
            documents=[f"{h}\n\n{b}" if h else b for h, b in chunks],
            ids=[f"{path.stem}-{i}" for i in range(len(chunks))],
            metadatas=[{"source": path.stem, "section": h} for h, _ in chunks],
        )

    def _search(self, prompt, collection):
        results = collection.query(query_texts=[prompt], n_results=10)
        return "\n\n".join(
            f"**{meta['source']}-{meta['section']}**\n{doc}"
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        )

    def add_rules(self, path):
        self._ingest(path, self.rules)

    def add_lore(self, path):
        self._ingest(path, self.lore)

    def gen_character_skeleton(self):
        self.character_skeleton = self.query(
            "Give the skeleton of a character sheet in JSON format. "
            "Only fill in fields that are the same across all starting characters.",
            as_json=True,
        )
        (self.path / "character_skeleton.json").write_text(self.character_skeleton, encoding="utf-8")

    def query(self, prompt, as_json=False, tools=None):
        """Query the LLM with relevant rules and lore retrieved as context."""
        context = f"# RULES:\n{self._search(prompt, self.rules)}\n\n# LORE:\n{self._search(prompt, self.lore)}\n\n{prompt}"
        return llm.query_llm(context, as_json=as_json, tools=tools)

    def sheet_path(self, player_id):
        """A finished sheet in players/, otherwise the draft in drafts/."""
        done = self.path / "players" / f"{player_id}.json"
        return done if done.exists() else self.path / "drafts" / f"{player_id}.json"

    def sheet(self, player_id):
        return json.loads(self.sheet_path(player_id).read_text(encoding="utf-8"))

    def get_players(self):
        """Discord ids (as strings) of players with finished sheets."""
        return [path.stem for path in (self.path / "players").glob("*.json")]

    def start_character(self, player_id):
        (self.path / "drafts" / f"{player_id}.json").write_text(self.character_skeleton, encoding="utf-8")

    def update_sheet(self, player_id, changes):
        sheet = merge(self.sheet(player_id), changes)
        self.sheet_path(player_id).write_text(json.dumps(sheet, indent=2), encoding="utf-8")
        return "Saved."

    def finish_character(self, player_id):
        self.sheet_path(player_id).rename(self.path / "players" / f"{player_id}.json")
        return "Character finished."
