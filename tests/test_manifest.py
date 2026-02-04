import json
from pathlib import Path


def test_manifest_shard_paths_exist():
    manifest_path = Path("data/derived/index/manifest.json")
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shards = manifest.get("shards", [])
    assert shards
    for shard in shards:
        shard_path = Path(shard["path"])
        assert shard_path.exists()
