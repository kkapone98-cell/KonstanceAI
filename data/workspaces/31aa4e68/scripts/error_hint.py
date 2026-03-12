import re

def suggest(trace: str):
    t = (trace or "").lower()
    tips = []
    if "indentationerror" in t:
        tips.append("Indentation broken. Restore from last stable backup and patch via file-based scripts only.")
    if "nameerror" in t and "not defined" in t:
        tips.append("Missing symbol. Replace call site with existing helper or add function in modular script.")
    if "unicodeencodeerror" in t or "cp1252" in t:
        tips.append("Set PYTHONUTF8=1 and avoid emoji in console outputs.")
    if "jsondecodeerror" in t and "bom" in t:
        tips.append("Read JSON with utf-8-sig and rewrite file without BOM.")
    if "unterminated string literal" in t:
        tips.append("Broken quote/newline in generated patch. Restore backup and re-apply conservative patch.")
    if not tips:
        tips.append("Run compile gate on changed file: python -m py_compile <file>")
    return tips

if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:])
    for x in suggest(msg):
        print("-", x)
