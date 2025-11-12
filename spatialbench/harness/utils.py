import json
import os
import subprocess
import tempfile
from pathlib import Path

def get_cache_dir():
    cache_dir = Path(tempfile.gettempdir()) / "spatialbench" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def download_data(data_node: str | list[str], work_dir: Path) -> list[dict]:
    cache_dir = get_cache_dir()
    data_nodes = data_node if isinstance(data_node, list) else ([data_node] if data_node else [])

    contextual_data = []

    for node in data_nodes:
        data_filename = Path(node).name
        cached_file = cache_dir / data_filename

        if not cached_file.exists():
            print(f"Downloading data: {node}")
            subprocess.run(
                ["latch", "cp", node, str(cached_file)],
                check=True,
                capture_output=True
            )
            print(f"Data cached: {cached_file}")
        else:
            print(f"Using cached data: {data_filename}")

        target_file = work_dir / data_filename
        if target_file.exists():
            target_file.unlink()
        os.symlink(cached_file, target_file)
        print(f"Linked: {data_filename} -> {cached_file}")

        contextual_data.append({
            "type": "File",
            "path": node,
            "id": node.replace("latch:///", "").replace(".csv", "").replace(".h5ad", ""),
        })

    return contextual_data

def setup_workspace(eval_id: str) -> Path:
    tmpdir = Path(tempfile.gettempdir()) / "spatialbench"
    work_dir = tmpdir / eval_id

    if work_dir.exists():
        import shutil
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    return work_dir

def cleanup_workspace(work_dir: Path, keep: bool = False):
    if keep:
        print(f"Workspace preserved at: {work_dir}")
    else:
        import shutil
        shutil.rmtree(work_dir)
        print(f"Workspace deleted: {work_dir}")
