#Convert a pdf to markdown and save it.
import pymupdf4llm

def book_to_md(book_title):
    md_content = pymupdf4llm.to_markdown(f"books/pdf/{book_title}.pdf")  # preserves headers, tables, reading order

    with open(f"books/md/{book_title}.md", "w") as md:
        md.write(md_content)
    
    return md_content