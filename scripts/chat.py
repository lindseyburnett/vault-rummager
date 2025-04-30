# scripts/chat.py
import chromadb
from sentence_transformers import SentenceTransformer
import requests
from datetime import datetime, date
from rich.console import Console
from rich.prompt import Prompt
import json
import time

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
OLLAMA_URL = "http://localhost:11434/api/generate"
COLLECTION_NAME = "vault-rummager"
MODEL_NAME = "gemma:2b"
TOP_K = 10

console = Console()


def embed_query(query: str, model) -> list:
    return model.encode([query])[0].tolist()


def query_chroma(embedding: list, client, distance_threshold: float = 0.6) -> list:
    collection = client.get_collection(name=COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"🔎 Chunk distance: {dist:.3f}")
        if dist < distance_threshold:
            chunks.append(doc)

    if not chunks and results["documents"][0]:
        # Use top-1 fallback chunk
        fallback_chunk = results["documents"][0][0]
        chunks.append(fallback_chunk)
        print("⚠️ No chunks passed threshold — using top-1 fallback chunk.")

    return chunks




def build_prompt(query: str, context_chunks: list[str]) -> tuple[str, bool]:
    today = date.today().strftime("%B %d, %Y")
    # Filter out empty or whitespace-only chunks
    filtered_chunks = [chunk.strip() for chunk in context_chunks if chunk.strip()]

    size = len(filtered_chunks)

    from_notes = size > 0

    print(from_notes)
    print(size)



    if from_notes:
        context_str = "\n\n---\n\n".join(filtered_chunks)
        prompt = f"""Today is {today}.

You are a helpful assistant with access to my personal notes.

Answer the question as accurately as possible using only the context provided. 
If the answer is not in the context, respond with: "The answer is not in the provided notes."
Do not make up facts or assume information not present in the context.

---

Context:
{context_str}

---

Question:
{query}
"""
    else:
        # No valid notes → fallback
        prompt = f"""Today is {today}.

You are a helpful assistant.

The user has asked a question without relevant note context. 
Please answer it using your general knowledge.

---

Question:
{query}
"""
    return prompt, from_notes




def ask_ollama(prompt: str, model=MODEL_NAME) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True
    )
    if response.status_code != 200:
        return f"❌ Ollama API error {response.status_code}: {response.text}"

    answer = ""
    for line in response.iter_lines():
        if line:
            try:
                data = line.decode("utf-8")
                if data.startswith("data: "):
                    data = data[len("data: "):]
                if data.strip() == "[DONE]":
                    break
                chunk = json.loads(data)
                token = chunk.get("response", "")
                console.print(token, end="", soft_wrap=True)
                answer += token
            except Exception as e:
                console.print(f"\n[red]Streaming error:[/red] {e}")
    print()  # final newline
    return answer.strip()


def log_interaction(question: str, answer: str):
    log_entry = f"""[{datetime.now().isoformat()}]

Q: {question}

A:
{answer}

{'='*80}\n"""
    with open("answers.log", "a") as f:
        f.write(log_entry)


def main():
    console.print("💬 [bold cyan]Vault Rummager Chat[/bold cyan] ([dim]type 'exit' to quit[/dim])\n")

    with console.status("🔄 Loading embedding model...", spinner="dots"):
        model = SentenceTransformer("all-MiniLM-L6-v2")

    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    while True:
        try:
            question = Prompt.ask("[bold green]🧠 You[/bold green]").strip()
            if question.lower() in {"exit", "quit"}:
                console.print("👋 [bold yellow]Goodbye![/bold yellow]")
                break

            embedded_query = embed_query(question, model)
            documents = query_chroma(embedded_query, chroma_client)

            if documents:
                console.rule("[dim]🔍 Top Context Chunk Used[/dim]")
                console.print(documents[0][:1000].strip(), soft_wrap=True)
                console.rule()


            prompt, from_notes = build_prompt(question, documents)

            if from_notes:
                console.print("\n🤖 [bold magenta]VaultBot[/bold magenta]: ", end="")
            else:
                console.print("\n🤖 [bold magenta]VaultBot[/bold magenta] [dim](general knowledge fallback)[/dim]: ", end="")

            answer = ask_ollama(prompt)
            log_interaction(question, answer)
            time.sleep(0.25)

        except KeyboardInterrupt:
            console.print("\n👋 [bold yellow]Goodbye![/bold yellow]")
            break


if __name__ == "__main__":
    main()
