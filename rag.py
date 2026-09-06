"""RAG: dela upp dokument i bitar, lagra dem som vektorer, sök på betydelse."""

import pathlib

import chromadb

DOCS = pathlib.Path("docs")
CHUNK = 800  # tecken, inte tokens - grovt men tillräckligt bra
OVERLAP = 100  # så en mening som hamnar på gränsen finns med i båda bitarna

_collection = None


def collection():
    """Chroma laddar ner sin embedding-modell vid första anropet, därför lat."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient("chroma")
        _collection = client.get_or_create_collection("docs")
    return _collection


def chunks(text):
    """Slå ihop hela stycken till ~CHUNK tecken, så att inget klipps mitt i en mening."""
    out, buf = [], ""
    for para in text.split("\n\n"):
        if buf and len(buf) + len(para) > CHUNK:
            out.append(buf.strip())
            buf = buf[-OVERLAP:]
        buf += para + "\n\n"
    if buf.strip():
        out.append(buf.strip())
    return out


def ingest():
    ids, texts = [], []
    for path in sorted(DOCS.rglob("*")):
        if path.suffix not in (".md", ".txt"):
            continue
        for i, chunk in enumerate(chunks(path.read_text(encoding="utf-8"))):
            ids.append(f"{path}#{i}")
            texts.append(chunk)
    if not texts:
        return f"Inga .md/.txt-filer i {DOCS}/ - lägg dokument där först."
    collection().upsert(ids=ids, documents=texts)
    return f"{len(texts)} chunks indexerade från {DOCS}/"


def search_knowledge_base(query):
    col = collection()
    if col.count() == 0:
        return "ERROR: kunskapsbasen är tom. Kör 'uv run rag.py' först."
    hits = col.query(query_texts=[query], n_results=3)
    return "\n\n---\n\n".join(
        f"[{name}]\n{text}"
        for name, text in zip(hits["ids"][0], hits["documents"][0])
    )


if __name__ == "__main__":
    long = "\n\n".join("mening ett. mening två." * 5 for _ in range(10))
    assert len(chunks(long)) > 1, "långt dokument ska delas"
    assert all(len(c) < CHUNK * 2 for c in chunks(long)), "bitarna ska hålla sig nära CHUNK"
    assert chunks("kort text") == ["kort text"], "kort dokument ska bli en bit"
    print(ingest())
