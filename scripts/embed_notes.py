import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
from parse_notes import parse_vault


def hash_chunk(chunk: str) -> str:
    return hashlib.md5(chunk.encode("utf-8")).hexdigest()


def embed_and_store(chunks, collection_name="vault-rummager", reset=False):
    client = chromadb.HttpClient(host="localhost", port=8000)

    if client.heartbeat():
        print("✅ Chroma server is up and responding.")
    else:
        print("❌ Chroma is not responding.")
        return

    if reset:
        print(f"🧨 Resetting collection: {collection_name}")
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(name=collection_name)
    print(f"📚 Using Chroma collection: {collection_name}")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"📦 Processing {len(chunks)} chunks...")
    existing_ids = set(collection.get()["ids"])

    all_texts, all_ids, all_metadata = [], [], []
    new_count = 0

    for c in chunks:
        chunk_text = c["chunk"]
        chunk_id = c.get("chunk_id") or hash_chunk(chunk_text)

        if chunk_id in existing_ids:
            continue

        all_texts.append(chunk_text)
        all_ids.append(chunk_id)
        all_metadata.append({
            "title": c["title"],
            "tags": ", ".join(c["tags"]) if isinstance(c["tags"], list) else c["tags"],
            "source": c["source"],
            "chunk_id": chunk_id,
        })
        new_count += 1

    if not all_texts:
        print("⏩ No new chunks to embed.")
        return

    print(f"🧠 Embedding {new_count} new chunks...")
    embeddings = model.encode(all_texts, show_progress_bar=True)

    print("📥 Storing new embeddings in Chroma...")
    collection.add(
        documents=all_texts,
        embeddings=embeddings.tolist(),
        ids=all_ids,
        metadatas=all_metadata,
    )

    print("✅ Stored new embeddings.")
