import json
import os
from textwrap import dedent
from datetime import datetime
from typing import Any, Dict, Optional

SHARED_MEMORY_PATH = os.getenv("AUTO_GITOPS_SHARED_MEMORY", "memory/shared_memory.json")
REPORTS_DIR = os.getenv("AUTO_GITOPS_REPORTS_DIR", "data/reports")


def ensure_memory_file():
    os.makedirs(os.path.dirname(SHARED_MEMORY_PATH), exist_ok=True)
    if not os.path.exists(SHARED_MEMORY_PATH):
        with open(SHARED_MEMORY_PATH, "w") as f:
            json.dump({}, f)


def read_shared_memory(key: Optional[str] = None) -> Any:
    """
    Read the shared memory JSON. If key is provided, return only that key's value.
    Tool shape: read_shared_memory(key: Optional[str]) -> JSON-string of value
    """
    ensure_memory_file()
    with open(SHARED_MEMORY_PATH, "r") as f:
        data = json.load(f)
    if key is None:
        return json.dumps(data)
    return json.dumps({key: data.get(key)})


def write_shared_memory(key: str, value: Any) -> str:
    """
    Write a key/value pair into shared memory.
    Returns a JSON string confirming the write.
    """
    ensure_memory_file()
    with open(SHARED_MEMORY_PATH, "r") as f:
        data = json.load(f)
    data[key] = value
    with open(SHARED_MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)
    return json.dumps({"status": "ok", "key": key, "value": value})


def validate_commit_message(message: str) -> str:
    """
    Validate commit message against a Conventional Commits-like prefix.
    Returns a JSON string with { valid: bool, reason?: str }.
    """
    import re

    pattern = r"^(feat|fix|chore|docs|refactor|style|perf|test)(\(.+\))?:\s.+"
    if re.match(pattern, message.strip(), flags=re.IGNORECASE):
        return json.dumps({"valid": True})
    else:
        return json.dumps({
            "valid": False,
            "reason": "Commit message must follow Conventional Commits, e.g. 'feat(module): short description'"
        })


def trigger_pipeline(repo_full_name: str, branch: str, pipeline_type: str = "mock") -> str:
    """
    Simulate triggering a CI/CD pipeline for the repo/branch.
    Output: JSON string with status and a mock pipeline id.
    For real pipelines, replace the internal logic with calls to your CI provider API.
    """
    ts = datetime.utcnow().isoformat() + "Z"
    pipeline_id = f"mock-pipeline-{repo_full_name.replace('/', '-')}-{branch}-{int(datetime.utcnow().timestamp())}"
    # In a real setup: call GitHub Actions, CircleCI, etc.
    payload = {
        "status": "triggered",
        "pipeline_id": pipeline_id,
        "repo": repo_full_name,
        "branch": branch,
        "type": pipeline_type,
        "triggered_at": ts
    }
    return json.dumps(payload)


def create_report_file(repo: str, title: str, content_md: str) -> str:
    """
    Create a markdown report in the reports directory and return path info as JSON.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_title = title.lower().replace(" ", "-")[:80]
    filename = f"{repo.replace('/', '_')}_{safe_title}_{ts}.md"
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"_Generated: {ts}_\n\n")
        f.write(content_md)
    return json.dumps({"status": "written", "path": path})
