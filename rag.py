import pathlib

DOCS = pathlib.Path("docs")
CHUNK = 800
OVERLAP = 100
LIMIT = CHUNK - OVERLAP - 2  # plats för överlappet och "\n\n" i nästa bit


def paragraphs(text):
    """Stycken, där ett stycke längre än LIMIT bryts på närmaste mellanslag."""
    for para in text.split("\n\n"):
        while len(para) > LIMIT:
            cut = para.rfind(" ", 0, LIMIT) + 1 or LIMIT
            yield para[:cut]
            para = para[cut:]
        yield para


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
            cur = cur[-OVERLAP:]
        cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        out.append(cur)
    return out


if __name__ == "__main__":
    para = "Detta är en mening som fyller ut stycket. " * 5  # ~210 tecken
    long = "\n\n".join(f"Stycke {i}. {para}" for i in range(20))

    cs = chunks(long)
    assert len(cs) > 1, cs
    assert all(len(c) <= CHUNK for c in cs), [len(c) for c in cs]
    assert all(len(c) > CHUNK / 2 for c in cs[:-1]), [len(c) for c in cs]
    assert all(cs[i][-OVERLAP:] in cs[i + 1] for i in range(len(cs) - 1))

    # en vägg text utan tomrader ska också delas, och inte mitt i ett ord
    wall = chunks(para * 20)
    assert len(wall) > 1 and all(len(c) <= CHUNK for c in wall), [len(c) for c in wall]
    assert not any(c.endswith(("stycke", "fyll")) for c in wall)

    assert chunks("Kort text.") == ["Kort text."]
    print(f"ok: {len(cs)} bitar, längder {[len(c) for c in cs]}")
