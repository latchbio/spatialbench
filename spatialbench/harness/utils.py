import hashlib
import json
import os
import subprocess
from pathlib import Path

def get_project_root():
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()

def get_cache_dir():
    project_root = get_project_root()
    cache_dir = project_root / ".spatialbench" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_cache_manifest():
    cache_dir = get_cache_dir()
    manifest_file = cache_dir / "manifest.json"

    if manifest_file.exists():
        return json.loads(manifest_file.read_text())
    return {}

def save_cache_manifest(manifest: dict):
    cache_dir = get_cache_dir()
    manifest_file = cache_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))

def get_cache_key(uri: str) -> str:
    uri_hash = hashlib.sha256(uri.encode()).hexdigest()[:16]
    filename = Path(uri).name
    return f"{uri_hash}__{filename}"

def download_single_dataset(uri: str, show_progress: bool = True) -> Path:
    cache_dir = get_cache_dir()
    manifest = get_cache_manifest()

    if uri in manifest:
        cached_file = cache_dir / manifest[uri]
        if cached_file.exists():
            if show_progress:
                print(f"Using cached: {Path(uri).name}")
            return cached_file

    cache_key = get_cache_key(uri)
    cached_file = cache_dir / cache_key

    if show_progress:
        print(f"Downloading: {uri}")
    subprocess.run(
        ["latch", "cp", uri, str(cached_file)],
        check=True,
        capture_output=True
    )
    if show_progress:
        print(f"Cached as: {cache_key}")

    manifest[uri] = cache_key
    save_cache_manifest(manifest)

    return cached_file

def download_data(data_node: str | list[str], work_dir: Path) -> list[dict]:
    data_nodes = data_node if isinstance(data_node, list) else ([data_node] if data_node else [])

    contextual_data = []

    for node in data_nodes:
        cached_file = download_single_dataset(node)
        data_filename = Path(node).name

        target_file = work_dir / data_filename
        if target_file.exists():
            target_file.unlink()
        os.symlink(cached_file, target_file)
        print(f"Linked: {data_filename} -> workspace")

        contextual_data.append({
            "type": "File",
            "path": node,
            "local_path": data_filename,
            "id": node.replace("latch:///", "").replace(".csv", "").replace(".h5ad", ""),
        })

    return contextual_data

def batch_download_datasets(uris: list[str], show_progress: bool = True):
    if show_progress and uris:
        print(f"Preparing to download {len(uris)} unique dataset(s)...")
        print("=" * 80)

    for i, uri in enumerate(uris, 1):
        if show_progress:
            print(f"[{i}/{len(uris)}] ", end="")
        download_single_dataset(uri, show_progress=show_progress)

    if show_progress and uris:
        print("=" * 80)
        print(f"Downloaded/verified {len(uris)} dataset(s)")
        print()

def setup_workspace(eval_id: str, run_id: str | None = None) -> Path:
    project_root = get_project_root()
    if run_id:
        work_dir = project_root / ".spatialbench" / "workspace" / run_id / eval_id
    else:
        work_dir = project_root / ".spatialbench" / "workspace" / eval_id

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
