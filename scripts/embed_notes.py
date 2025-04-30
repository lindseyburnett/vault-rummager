import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
from parse_notes import parse_vault


def hash_chunk(chunk: str) -> str:
    """Create a unique hash for each chunk to use as an ID in Chroma."""
    return hashlib.md5(chunk.encode("utf-8")).hexdigest()


def embed_and_store(chunks, collection_name="vault-rummager"):
    # ✅ Connect to Chroma REST API
    client = chromadb.HttpClient(host="localhost", port=8000)

    # 💓 Optional heartbeat check
    try:
        if client.heartbeat():
            print("✅ Chroma server is up and responding.")
    except Exception as e:
        print("❌ Failed to connect to Chroma server:", e)
        return

    # 🗃️ Get or create collection
    collection = client.get_or_create_collection(name=collection_name)
    print(f"📚 Using Chroma collection: {collection_name}")

    # 🧠 Load local embedding model (CPU/GPU OK)
    print("🔄 Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 📦 Prepare data
    texts = [c["chunk"] for c in chunks]
    ids = [hash_chunk(c["chunk"]) for c in chunks]
    metadatas = [{
        "title": c["title"],
        "tags": ", ".join(c["tags"]) if isinstance(c["tags"], list) else c["tags"],
        "source": c["source"],
        "chunk_id": c["chunk_id"]
    } for c in chunks]

    # 🚀 Generate embeddings
    print(f"🧠 Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # 💾 Store in Chroma
    print("📥 Storing embeddings in Chroma...")
    collection.add(
        documents=texts,
        embeddings=embeddings.tolist(),
        ids=ids,
        metadatas=metadatas
    )

    print("✅ Embeddings stored successfully!")


if __name__ == "__main__":
    print("🔍 Parsing vault...")
    vault_chunks = parse_vault("notes")
    print(f"✅ Found {len(vault_chunks)} chunks to embed.")
    embed_and_store(vault_chunks)
