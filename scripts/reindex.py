import argparse
from parse_notes import parse_vault
from embed_notes import embed_and_store

def reindex_notes(reset=False):
    print("🔁 Re-parsing and embedding notes...")
    chunks = parse_vault("notes")
    print(f"✅ Parsed {len(chunks)} chunks.")
    embed_and_store(chunks, reset=reset)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reindex vault notes into Chroma.")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the Chroma collection from scratch.")
    args = parser.parse_args()

    reindex_notes(reset=args.reset)
