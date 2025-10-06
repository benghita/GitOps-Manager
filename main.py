import os
from datetime import datetime


def main():

    from modules.auto_gitops import (
        create_repo_watcher_agent,
        create_commit_agent,
        create_branch_manager_agent,
        create_deployment_agent,
        create_report_agent,
    )
    from tools.auto_gitops_tools import ensure_memory_file, SHARED_MEMORY_PATH
    import json

    repo = os.getenv("REPO_FULL_NAME", "benghita/PropertyValuation")

    # Ensure shared memory file is valid JSON ({} if missing/empty)
    ensure_memory_file()
    try:
        with open(SHARED_MEMORY_PATH, "r") as f:
            content = f.read().strip()
        if not content:
            raise ValueError("empty")
        json.loads(content)
    except Exception:
        with open(SHARED_MEMORY_PATH, "w") as f:
            f.write("{}")

    watcher = create_repo_watcher_agent(repo)
    watcher.print_response(
        f"Scan repository {repo} for new commits and PRs and return a compact JSON summary as a string."
    )

    commit_agent = create_commit_agent(repo)
    commit_agent.print_response(
        "Create or update the file configs/app.yaml with content 'key: value'. "
        "Use commit message 'chore(config): sync'. Work on branch 'auto/config-sync'. Do not open a PR. "
        "Return a JSON string with status, commit_sha, branch, and files_updated."
    )

    branch_manager = create_branch_manager_agent(repo)
    branch_manager.print_response(
        "List branches (action=list). Return a JSON string describing the result."
    )

    deployment = create_deployment_agent(repo)
    deployment.print_response(
        "Check for merged PRs into main since 2025-10-06T00:00:00Z and simulate triggering deployment if there are new commits. "
        "Return a JSON string with status and any pipeline/deployed_commit details."
    )

    report = create_report_agent(repo)
    report.print_response(
        "Generate a repository report since 2025-10-01T00:00:00Z including sections: summary, compliance, recent_prs, open_issues. "
        "Save it via the provided tool and return a JSON string with the written path."
    )


if __name__ == "__main__":
    main()
