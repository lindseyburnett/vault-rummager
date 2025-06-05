## 🧠 vault-rummager

**A private, local-first chatbot that rummages through your Obsidian vault to answer your questions.**  
Powered by embeddings, vector search, and local LLMs — no cloud, no leaks, just your second brain on demand.

---

## 🚀 Features

- ✅ Local-only LLMs using [Ollama](https://ollama.com/)
- 🗃️ Fast vector search with [ChromaDB](https://github.com/chroma-core/chroma)
- 🧾 Markdown + Obsidian note parsing (handles embeds, wiki-links, frontmatter)
- 🔒 Keeps your data offline and secure

---

## 🛠️ Setup Guide

### 1. Clone the Repo

```bash
git clone https://github.com/yourname/vault-rummager.git
cd vault-rummager
```

---

### 2. Set Up Python Environment (Poetry)

Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed:

```bash
poetry install
poetry shell
```

This will:
- Create a virtual environment
- Install all required dependencies (parsing, embeddings, Chroma, LLMs)

---

### 3. Run Infrastructure with Podman

Start ChromaDB and Ollama locally:

```bash
podman-compose -f podman-compose.yml up -d
```

- `localhost:8000` → ChromaDB
- `localhost:11434` → Ollama REST API


![Podman compose demo](imgs/podmancompose.gif)

---

### 4. Pull a Local LLM via Ollama

You must download a model before generating text.

#### Using API (no CLI):

```bash
curl http://localhost:11434/api/pull -d '{"name": "gemma:2b"}'
```

### 5. Project Structure

```
vault-rummager/
├── docker-compose.yml        # Infrastructure (Chroma + Ollama)
├── podman-compose.yml        # Same as above for Podman users
├── README.md                 # This file
├── .gitignore
├── pyproject.toml            # Poetry-managed dependencies
├── poetry.lock
├── notes/                    # Place your knowledge base files here
└── scripts/                  # (coming soon) parsing, embedding, querying scripts
```

---

## 📌 Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- [Podman](https://podman.io/) or Docker
- [podman-compose](https://github.com/containers/podman-compose)
- ~8GB+ RAM recommended (LLMs need headroom)

---

## Usage
### Indexing your notes

```bash
poetry run python scripts/reindex.py --reset
```

![Reindexing in action](imgs/reindex.gif)


### Chat about them
```bash
poetry run python scripts/chat.py
```
![Ask about Taylor Swift](imgs/correct-answer.gif)