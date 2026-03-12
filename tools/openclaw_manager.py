from pathlib import Path
def edit_file_openclaw(file_path, content):
    p = Path(file_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'[OpenClaw] Updated {file_path}')
