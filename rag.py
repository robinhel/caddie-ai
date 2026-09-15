import pathlib

import chromadb

DOCS = pathlib.Path("docs")
CHUNK = 800
OVERLAP = 100
LIMIT = CHUNK - OVERLAP - 2  # plats för överlappet och "\n\n" i nästa bit

_col = None


def paragraphs(text):
    """Stycken, där ett stycke längre än LIMIT bryts vid närmaste meningsslut,
    i andra hand vid närmaste mellanslag."""
    for para in text.split("\n\n"):
        while len(para) > LIMIT:
            cut = para.rfind(". ", LIMIT // 2, LIMIT)
            cut = cut + 2 if cut > 0 else para.rfind(" ", LIMIT // 2, LIMIT) + 1 or LIMIT
            yield para[:cut]
            para = para[cut:]
        yield para


def collection():
    """Chromas "docs"-collection. Lat: första anropet laddar ner embeddingmodellen."""
    global _col
    if _col is None:
        _col = chromadb.PersistentClient("chroma").get_or_create_collection("docs")
    return _col


def chunks(text):
    """Dela text i bitar på ~CHUNK tecken, brutet på tomrad, med OVERLAP tecken
    av föregående bit inledande nästa."""
    out, cur = [], ""
    for para in paragraphs(text):
        para = para.strip()
        if not para:
            continue
        if cur and len(cur) + len(para) + 2 > CHUNK:
            out.append(cur)
            tail = cur[-OVERLAP:]
            cur = tail[tail.find(" ") + 1 :]  # börja överlappet på ett helt ord
        cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out


def ingest():
    """Chunka alla dokument under DOCS och lägg in dem i collection()."""
    ids, docs = [], []
    for path in sorted(DOCS.rglob("*.md")) + sorted(DOCS.rglob("*.txt")):
        for i, chunk in enumerate(chunks(path.read_text())):
            ids.append(f"{path}#{i}")
            docs.append(chunk)
    if not docs:
        return f"inga .md- eller .txt-filer i {DOCS}/ — lägg in dokument först"
    collection().upsert(ids=ids, documents=docs)  # upsert: omkörning skriver över
    return f"{len(docs)} chunks indexerade"


if __name__ == "__main__":
    print(ingest())
