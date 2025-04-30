import os
import re
import frontmatter
from pathlib import Path
from typing import List, Dict


def clean_markdown_note(path: Path) -> Dict:
    """Clean and extract text from a single Obsidian markdown note."""
    post = frontmatter.load(path)
    content = post.content

    # Remove image embeds and markdown image syntax
    content = re.sub(r'!\[\[.*?\]\]', '', content)             # Obsidian: ![[image.png]]
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)          # Markdown: ![](path)

    # Convert wiki-style links to plain text: [[Note Name]] → Note Name
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)

    # Remove HTML tags (just in case)
    content = re.sub(r'<[^>]+>', '', content)

    # Normalize whitespace
    content = re.sub(r'\n{2,}', '\n\n', content).strip()

    return {
        "title": post.get("title", path.stem),
        "tags": post.get("tags", []),
        "content": content,
        "source": str(path)
    }


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Split text into chunks of ~max_chars (approx 500 tokens)."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_chars:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def parse_vault(vault_dir: str = "notes") -> List[Dict]:
    """Parse all notes in the given directory and return a list of chunked text entries."""
    vault_path = Path(vault_dir)
    all_chunks = []

    for md_file in vault_path.rglob("*.md"):
        cleaned = clean_markdown_note(md_file)
        chunks = chunk_text(cleaned["content"])

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk": chunk,
                "title": cleaned["title"],
                "tags": cleaned["tags"],
                "source": cleaned["source"],
                "chunk_id": f"{md_file.stem}_{i}"
            })

    return all_chunks


if __name__ == "__main__":
    import json

    chunks = parse_vault("notes")
    print(f"✅ Parsed {len(chunks)} chunks from notes/")
    print(json.dumps(chunks[:2], indent=2))  # Preview first 2
