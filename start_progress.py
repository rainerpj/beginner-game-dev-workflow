"""ASCII-named Windows entrypoint; keep Unicode paths in Python, not CMD."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / '04_本地进度网页'))
import server

if __name__ == '__main__':
    server.main()
