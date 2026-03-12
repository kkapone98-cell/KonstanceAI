from pathlib import Path
def read_file(path):
    path=Path(path)
    if path.exists():
        return path.read_text(encoding='utf-8')
    return ''
def write_file(path,content):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')
