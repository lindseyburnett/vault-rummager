import os
import re
import frontmatter
from pathlib import Path
from typing import List, Dict
import nltk
from dotenv import load_dotenv
from datetime import datetime
import shlex
import hashlib
from nltk.tokenize import sent_tokenize

load_dotenv()

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

def chunk_text(text: str, title: str, max_chars: int = 750) -> List[str]:
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sent in sentences:
        if len(current_chunk) + len(sent) < max_chars:
            current_chunk += sent + " "
        else:
            chunks.append(f"{title}\n\n{current_chunk.strip()}")
            current_chunk = sent + " "

    if current_chunk:
        chunks.append(f"{title}\n\n{current_chunk.strip()}")

    return chunks


def make_chunk_id(path: Path, chunk_text: str) -> str:
    full_hash = hashlib.md5((str(path.resolve()) + chunk_text).encode()).hexdigest()
    return f"{full_hash}"

def parse_vault(vault_dirs: str = None) -> List[Dict]:
    all_chunks = []
    paths = [Path(p) for p in vault_dirs]

    print("📁 Parsed paths:", paths)
    seen_files = set()

    for base_path in paths:
        for vault_path in base_path.rglob("*.md"):
            resolved = vault_path.resolve()
            if resolved in seen_files:
                print(f"⚠️ Skipping duplicate file: {resolved}")
                continue
            seen_files.add(resolved)
            
            cleaned = clean_markdown_note(vault_path)
            chunks = chunk_text(cleaned["content"], cleaned["title"])
            
            for i, chunk in enumerate(chunks):
                chunk_id = make_chunk_id(resolved, chunk)
                all_chunks.append({
                    "chunk": chunk,
                    "title": cleaned["title"],
                    "tags": cleaned["tags"],
                    "source": str(vault_path),
                    "chunk_id": chunk_id
                })

    return all_chunks

# NOTE: current date helper for prompt injection (if used externally)
def current_date_string():
    return datetime.today().strftime("%B %d, %Y")
