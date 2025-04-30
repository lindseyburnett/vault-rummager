# scripts/parse_notes.py
import os
import re
import frontmatter
from pathlib import Path
from typing import List, Dict
import nltk
nltk.download("punkt")
from nltk.tokenize import sent_tokenize

def clean_markdown_note(path: Path) -> Dict:
    post = frontmatter.load(path)
    content = post.content

    # Remove image embeds and markdown images
    content = re.sub(r'!\[\[.*?\]\]', '', content)             # Obsidian: ![[image.png]]
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)          # Markdown: ![](path)

    # Convert wiki-style links to plain text: [[Note Name]] → Note Name
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)

    # Replace markdown links with readable inline format: [text](url) → text (url)
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', content)

    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Normalize whitespace
    content = re.sub(r'\n{2,}', '\n\n', content).strip()

    return {
        "title": post.get("title", path.stem),
        "tags": post.get("tags", []),
        "content": content,
        "source": str(path)
    }

def chunk_text(text: str, title: str, max_chars: int = 2000) -> List[str]:
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sent in sentences:
        if len(current_chunk) + len(sent) <= max_chars:
            current_chunk += sent + " "
        else:
            chunks.append(f"{title}\n\n{current_chunk.strip()}")
            current_chunk = sent + " "

    if current_chunk:
        chunks.append(f"{title}\n\n{current_chunk.strip()}")

    return chunks

def parse_vault(vault_dir: str = "notes") -> List[Dict]:
    vault_path = Path(vault_dir)
    all_chunks = []

    for md_file in vault_path.rglob("*.md"):
        cleaned = clean_markdown_note(md_file)
        chunks = chunk_text(cleaned["content"], cleaned["title"])

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk": chunk,
                "title": cleaned["title"],
                "tags": cleaned["tags"],
                "source": cleaned["source"],
                "chunk_id": f"{md_file.stem}_{i}"
            })

    return all_chunks
