import argparse
import os

from pathlib import Path
from dotenv import load_dotenv
from parse_notes import parse_vault
from embed_notes import embed_and_store

load_dotenv()

def reindex_notes(reset=False):
    print("🔁 Re-parsing and embedding notes...")
    vault_dirs = [p.strip() for p in os.getenv("VAULT_DIRS").split(",")]
    chunks = parse_vault(vault_dirs)


    # Ensure unique chunk IDs across all entries
    seen_ids = set()
    deduped_chunks = []
    for chunk in chunks:
        if chunk["chunk_id"] not in seen_ids:
            seen_ids.add(chunk["chunk_id"])
            deduped_chunks.append(chunk)
        else:
            print(f"⚠️ Duplicate chunk_id skipped: {chunk['chunk_id']}")

    print(f"✅ Parsed {len(deduped_chunks)} unique chunks.")
    embed_and_store(deduped_chunks, reset=reset)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reindex vault notes into Chroma.")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the Chroma collection from scratch.")
    args = parser.parse_args()

    reindex_notes(reset=args.reset)