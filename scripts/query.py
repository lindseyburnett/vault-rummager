import chromadb
from sentence_transformers import SentenceTransformer
import requests
import argparse

# --- Config ---
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_URL = "http://localhost:11434/api/generate"
COLLECTION_NAME = "vault-rummager"
MODEL_NAME = "mistral"
TOP_K = 5
MAX_CONTEXT_CHARS = 3000


def embed_query(query: str, model) -> list:
    """Embed the user's question."""
    return model.encode([query])[0].tolist()


def query_chroma(embedding: list, client) -> list:
    """Search for the most relevant chunks."""
    collection = client.get_collection(name=COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"]
    )
    return results


def build_prompt(query: str, contexts: list) -> str:
    """Construct the prompt to send to the LLM."""
    context_str = "\n\n".join(contexts)[:MAX_CONTEXT_CHARS]
    prompt = f"""You are a helpful assistant with access to my personal notes.

Answer the following question using the context below. If the context isn't helpful, say you don't know.

---

Context:
{context_str}

---

Question:
{query}
"""
    return prompt


def ask_ollama(prompt: str, model=MODEL_NAME) -> str:
    """Send the prompt to the local Ollama model and return the response."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False}
    )

    if response.status_code == 200:
        return response.json().get("response", "").strip()
    else:
        return f"❌ Ollama API error {response.status_code}: {response.text}"


def main():
    parser = argparse.ArgumentParser(description="Ask a question to Vault Rummager.")
    parser.add_argument("question", type=str, help="Your natural language question")
    args = parser.parse_args()

    print("🔄 Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("💬 Embedding question...")
    embedded_query = embed_query(args.question, model)

    print("📡 Querying Chroma...")
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    results = query_chroma(embedded_query, chroma_client)

    documents = results.get("documents", [[]])[0]
    if not documents:
        print("❌ No relevant results found.")
        return

    print(f"📚 Retrieved {len(documents)} relevant chunk(s).")

    prompt = build_prompt(args.question, documents)

    print("🤖 Sending to Ollama...")
    answer = ask_ollama(prompt)
    print("\n💡 Answer:\n")
    print(answer)


if __name__ == "__main__":
    main()
