import json
from pathlib import Path


def test_manifest_shard_paths_exist():
    manifest_path = Path("data/derived/index/manifest.json")
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shards = manifest.get("shards", [])
    if not shards:
        return
    for shard in shards:
        shard_path = Path(shard["path"])
        assert shard_path.exists()
