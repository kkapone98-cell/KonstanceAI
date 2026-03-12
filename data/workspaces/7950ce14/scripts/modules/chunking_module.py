def chunk_text(text: str, limit: int = 3000):
    t = text or ""
    if len(t) <= limit: return [t]
    out = []
    while t:
        if len(t) <= limit:
            out.append(t)
            break
        cut = t.rfind("\n", 0, limit)
        if cut <= 0: cut = limit
        out.append(t[:cut])
        t = t[cut:].lstrip("\n")
    return out

if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:])
    parts = chunk_text(msg, 3000)
    for i,p in enumerate(parts,1):
        print(f"[{i}/{len(parts)}]\n{p}")
