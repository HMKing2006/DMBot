#Convert a setting book pdf into model-readable context.

book_title = "the_wild_sheep_chase_v2"

import pymupdf4llm
md_content = pymupdf4llm.to_markdown(f"books/pdf/{book_title}.pdf")  # preserves headers, tables, reading order

with open(f"books/md/{book_title}.md", "w") as md:
    md.write(md_content)

print(f"Converted {book_title} to markdown!")