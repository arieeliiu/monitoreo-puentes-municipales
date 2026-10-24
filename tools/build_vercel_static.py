"""Publica los mismos recursos estáticos en el CDN de Vercel."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
shutil.copytree(root/'static',root/'public/static',dirs_exist_ok=True)