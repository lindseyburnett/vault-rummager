# scripts/chat.py
import chromadb
from sentence_transformers import SentenceTransformer
import requests
from datetime import datetime

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_URL = "http://localhost:11434/api/generate"
COLLECTION_NAME = "vault-rummager"
MODEL_NAME = "mistral"
TOP_K = 10
MAX_CONTEXT_CHARS = None

def embed_query(query: str, model) -> list:
    return model.encode([query])[0].tolist()

def query_chroma(embedding: list, client) -> list:
    collection = client.get_collection(name=COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"]
    )
    return results

def build_prompt(query: str, contexts: list) -> str:
    context_str = "\n\n".join(contexts)
    if MAX_CONTEXT_CHARS:
        context_str = context_str[:MAX_CONTEXT_CHARS]

    prompt = f"""You are a helpful assistant with access to my personal notes.

Answer the question as accurately as possible using only the information provided in the context below. Do not guess. If the answer is not in the provided notes, respond with: "The answer is not in the provided notes."

---

Context:
{context_str}

---

Question:
{query}
"""

    return prompt

def ask_ollama(prompt: str, model=MODEL_NAME) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False}
    )
    if response.status_code == 200:
        return response.json().get("response", "").strip()
    else:
        return f"❌ Ollama API error {response.status_code}: {response.text}"

def log_interaction(question: str, answer: str):
    log_entry = f"""[{datetime.now().isoformat()}]

Q: {question}

A:
{answer}

{'='*80}\n"""
    with open("answers.log", "a") as f:
        f.write(log_entry)

def main():
    print("💬 Vault Rummager Chat (type 'exit' to quit)\n")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    while True:
        try:
            question = input("🧠 You: ").strip()
            if question.lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break

            embedded_query = embed_query(question, model)
            results = query_chroma(embedded_query, chroma_client)

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if not documents:
                print("🤷 No relevant context found.\n")
                continue

            prompt = build_prompt(question, documents)
            answer = ask_ollama(prompt)

            print(f"\n🤖 VaultBot: {answer}\n")
            log_interaction(question, answer)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
