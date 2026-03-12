def suggest(trace: str):
    t = (trace or "").lower()
    out = []
    if "indentationerror" in t: out.append("Restore last stable backup; avoid inline python pastes.")
    if "nameerror" in t and "not defined" in t: out.append("Replace missing symbol call or add helper in module.")
    if "unicodeencodeerror" in t or "cp1252" in t: out.append("Set PYTHONUTF8=1 and avoid emoji in console output.")
    if "unterminated string literal" in t: out.append("Broken quote/newline in generated patch; revert and re-apply safely.")
    if not out: out.append("Run compile gate on changed file: python -m py_compile <file>")
    return out

if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:])
    for x in suggest(msg):
        print("-", x)
