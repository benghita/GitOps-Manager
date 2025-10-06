import os
from pathlib import Path
from textwrap import dedent
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.github import GithubTools
from agno.knowledge.reader.markdown_reader import MarkdownReader
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.db.sqlite import SqliteDb 

# Import custom tools (functions) from our tools module
from tools.auto_gitops_tools import (
    read_shared_memory,
    write_shared_memory,
    validate_commit_message,
    trigger_pipeline,
    create_report_file,
)

# Optionally load environment variables
from dotenv import load_dotenv
load_dotenv()

# Model configuration - adjust as needed (OpenAIChat id used as example)
MODEL = Gemini('gemini-2.0-flash')

# Defer/guard GitHub tool creation to avoid requiring a token during import (e.g., in tests)
GITHUB_TOOLS = GithubTools()

# --- Knowledge Base Configuration ---

# Add Contents DB for content tracking
contents_db = SqliteDb(db_file="knowledge_contents.db")

knowledge_branching = Knowledge(
    vector_db=LanceDb(
        table_name="kb_branching", 
        uri="/tmp/lancedb",  # Local storage path
        embedder=GeminiEmbedder(),  # Add Gemini embedder
    ),
    contents_db=contents_db, 
)
knowledge_branching.add_content(
    skip_if_exists=True,
    path=Path("./data/knowledge/branching_strategy.md"),
    reader=MarkdownReader(),
)

knowledge_commits = Knowledge(
    vector_db=LanceDb(
        table_name="kb_commits", 
        uri="/tmp/lancedb",  # Local storage path
        embedder=GeminiEmbedder(),  # Add Gemini embedder
    ),
    contents_db=contents_db, 
)
knowledge_commits.add_content(
    skip_if_exists=True,
    path=Path("./data/knowledge/commit_conventions.md"),
    reader=MarkdownReader(),
)

knowledge_gitops = Knowledge(
    vector_db=LanceDb(
        table_name="kb_gitops", 
        uri="/tmp/lancedb",  # Local storage path
        embedder=GeminiEmbedder(),  # Add Gemini embedder
    ),
    contents_db=contents_db, 
)
knowledge_gitops.add_content(
    skip_if_exists=True,
    path=Path("./data/knowledge/gitops_principles.md"),
    reader=MarkdownReader(),
)

def create_repo_watcher_agent(repo_full_name: str = None) -> Agent:
    """
    RepoWatcher Agent:
    - Monitors the repository for new commits, branches, and pull requests.
    - Does read-only GitHub operations.
    - Uses shared memory to store last seen commit/PR.
    """
    repo_name = repo_full_name or "owner/repo"

    instructions = dedent(f"""
    You are Repo Watcher Agent.

    Purpose:
    - Monitor the GitHub repository '{repo_name}' for new commits, branches, and pull requests.
    - Produce a small JSON event when change is detected: {{ 'new_commits': [...], 'new_prs': [...], 'timestamp': '...' }}.

    Rules and guardrails:
    1. You only perform read-only GitHub operations (no writes, no comments, no PR merges).
    2. Use GithubTools methods to list branches, get pull requests and get repository with stats.
    3. Use the provided tool `read_shared_memory(key)` to fetch last_known_commit or last_known_pr.
    4. When a new commit or PR is detected, return a JSON string containing:
       - new_commits: list of commit SHAs
       - new_prs: list of PR numbers
       - summary: short human string
       - timestamp: ISO datetime
    5. Rate-limiting: do not loop aggressively. If you are called in a loop, behave idempotently.
    6. If nothing new is found, return '{{ "status": "no_change" }}'.

    Output format:
    - Always return a JSON string. Example:
      {{ "new_commits": ["abc123"], "new_prs": [12], "summary": "1 commit, 1 PR", "timestamp": "..." }}
    """)

    tools = [GITHUB_TOOLS, read_shared_memory]
    tools = [t for t in tools if t is not None]
    return Agent(
        name="Repo Watcher",
        model=MODEL,
        role="Monitor GitHub repo activity (read-only).",
        description=dedent(f"""
            Watches repository {repo_name}. It periodically inspects branches and pull requests,
            compares them to stored state in shared memory, and returns a compact JSON event when changes occur.
        """),
        instructions=instructions,
        tools=tools,
        markdown=False,
    )


def create_commit_agent(repo_full_name: str = None, whitelist_paths: list = None) -> Agent:
    """
    Commit Agent:
    - Stages and commits changes (via create_file/update_file on GitHub).
    - Enforces commit message conventions using validate_commit_message().
    - Optionally opens a PR for the changes.
    """
    repo_name = repo_full_name or "owner/repo"
    whitelist_paths = whitelist_paths or ["configs/", "infra/", "data/"]

    instructions = dedent(f"""
    You are Commit Agent.

    Purpose:
    - Create or update files in the repository '{repo_name}' when given file changes.
    - Generate standardized commit messages. Validate them with validate_commit_message(message).
    - Optionally create a pull request for the change (if 'create_pr' flag is true).

    Inputs expected (as a JSON-like dict in your prompt):
    {{
      "files": [
        {{ "path": "configs/app.yaml", "content": "<file contents>", "message": "chore(config): sync app config" }}
      ],
      "branch": "auto/config-sync",
      "create_pr": true,
      "pr_title": "chore: sync app config",
      "pr_body": "Automated update by Commit Agent"
    }}

    Rules & Guardrails:
    1. Only operate on files whose paths start with one of: {whitelist_paths}
       - If a file path is outside these paths, refuse and return an error JSON.
    2. Validate the provided commit message with validate_commit_message(). If invalid, return a validation error.
    3. Before updating a file, fetch the current file content via GithubTools methods to get file content and include a short summary
       of diff in your output.
    4. If 'create_pr' is true, create the commit on the branch and open a PR. Return PR number and commit SHA.
    5. Do not delete files. If a file is missing and the action would delete, return an error.

    Expected Output (JSON string):
    {{
      "status": "success",
      "commit_sha": "abc123",
      "branch": "auto/config-sync",
      "pr_number": 42,
      "files_updated": ["configs/app.yaml"]
    }}
    """)

    tools = [
            GITHUB_TOOLS,
            validate_commit_message,
            read_shared_memory,
            write_shared_memory,
        ]
    tools = [t for t in tools if t is not None]
    return Agent(
        name="Commit Agent",
        model=MODEL,
        role="Create/update files and commits in GitHub (with safeguards).",
        description=dedent(f"""
            Commits configuration and small changes to {repo_name}. Validates commit messages, limits modified paths,
            and optionally opens a PR for human review.
        """),
        instructions=instructions,
        tools=tools,
        markdown=False,
        knowledge=knowledge_commits,
        search_knowledge=True,
    )


def create_branch_manager_agent(repo_full_name: str = None) -> Agent:
    """
    Branch Manager Agent:
    - Create branches prefixed with 'auto/'.
    - Inspect existence and ensure branches are up-to-date with main (recommendations only).
    """
    repo_name = repo_full_name or "owner/repo"

    instructions = dedent(f"""
    You are Branch Manager Agent.

    Purpose:
    - Create and validate branches for automation tasks in repository '{repo_name}'.
    - Only create branches with prefix 'auto/'.
    - Provide a JSON report after any action.

    Inputs:
    {{
      "action": "create" | "list" | "check_sync",
      "branch": "auto/feature-xyz",
      "base": "main"
    }}

    Rules & Guardrails:
    1. Allowed actions: create, list, check_sync.
    2. When creating a branch:
       - Use GithubTools methods to create branch with base and branch_name.
       - Enforce branch prefix 'auto/'.
    3. Do NOT delete branches.
    4. When checking sync, inspect commit differences between branch and base using GithubTools methods to get branch content or git diff via API,
       and produce a small recommendation (e.g., 'branch behind by N commits' or 'in sync').
    5. Output must be a JSON string. Example:
       {{ "status": "created", "branch": "auto/feature-xyz", "base": "main" }}
    """)

    tools = [GITHUB_TOOLS, read_shared_memory, write_shared_memory]
    tools = [t for t in tools if t is not None]
    return Agent(
        name="Branch Manager",
        model=MODEL,
        role="Manage and validate branches used by automation.",
        description=dedent(f"""
            Responsible for creating 'auto/*' branches, listing branch states, and providing sync recommendations relative to base branches.
        """),
        instructions=instructions,
        knowledge=knowledge_branching,
        search_knowledge=True,
        tools=tools,
        markdown=False,
    )


def create_deployment_agent(repo_full_name: str = None) -> Agent:
    """
    Deployment Agent:
    - Detect merged PRs to main and simulate triggering deployment pipeline via trigger_pipeline()
    - Log deployment events to shared memory and create a GitHub issue summarizing the deployment (optional)
    """
    repo_name = repo_full_name or "owner/repo"

    instructions = dedent(f"""
    You are Deployment Agent.

    Purpose:
    - When a PR merges into 'main', create a deployment event (simulation) and log it.
    - Use trigger_pipeline(repo_full_name, branch) to simulate running CI/CD.
    - Optionally create a GitHub issue documenting deployment results.

    Inputs:
    {{
      "check_merged_since": "2025-10-06T00:00:00Z"
    }}

    Rules & Guardrails:
    1. Only act when main branch has new merged commits since the last recorded deployed commit in shared memory.
    2. Use read_shared_memory('last_deployed_commit') to determine last deployment.
    3. If a new deployment is simulated:
       - Call trigger_pipeline(repo_full_name, "main")
       - write_shared_memory('last_deployed_commit', <commit_sha>)
       - Optionally create an issue to log the deployment using GithubTools methods to create issue (if configured)
    4. NEVER perform destructive operations (no repo file edits).
    5. Return JSON string: {{ "status": "deployment_triggered", "pipeline": {...}, "deployed_commit": "sha" }}

    Expected behavior:
    - If no changes since last deployment: return {{ "status": "no_new_deploy" }}
    """)

    tools = [GITHUB_TOOLS, trigger_pipeline, read_shared_memory, write_shared_memory]
    tools = [t for t in tools if t is not None]
    return Agent(
        name="Deployment Agent",
        model=MODEL,
        role="Simulate or trigger CI/CD and log deployments.",
        description=dedent(f"""
            Watches for merged PRs into main and triggers a mock pipeline. Logs the last deployed commit to shared memory.
        """),
        instructions=instructions,
        knowledge=knowledge_gitops,
        search_knowledge=True,
        tools=tools,
        markdown=False,
    )


def create_report_agent(repo_full_name: str = None) -> Agent:
    """
    Report Agent:
    - Collect repo metrics, PR/issue statistics, verify compliance (commit messages),
      and write a markdown report via create_report_file().
    - This agent is read-only with respect to GitHub data.
    """
    repo_name = repo_full_name or "owner/repo"

    instructions = dedent(f"""
    You are Report Agent.

    Purpose:
    - Produce a compliance and activity report for the repository '{repo_name}'.
    - Use GithubTools methods to get pull requests, list issues, and get repository with stats to gather data.
    - Use validate_commit_message to check commit messages of recent commits.
    - Save the final report with create_report_file(repo, title, content_md).

    Inputs:
    {{
      "since": "2025-10-01T00:00:00Z",
      "sections": ["summary", "compliance", "recent_prs", "open_issues"]
    }}

    Rules & Guardrails:
    1. Read-only operations only.
    2. Reports must not include secrets, tokens, or private keys.
    3. Use provided compliance checklist logic:
       - Check commit messages for Conventional Commit style.
       - Check PRs for reviewers (if PR has 0 reviewers, mark as 'needs review').
    4. Return JSON string: {{ "status": "report_generated", "path": "data/reports/..." }}

    Expected output:
    - JSON containing status and path to the markdown report file.
    """)

    # Reuse gitops knowledge for reports if available
    knowledge_report = knowledge_gitops

    tools = [GITHUB_TOOLS, create_report_file, validate_commit_message]
    tools = [t for t in tools if t is not None]
    return Agent(
        name="Report Agent",
        model=MODEL,
        role="Audit and report repository activity and compliance.",
        description=dedent(f"""
            Uses GithubTools to gather repo metrics and writes a dated markdown report using create_report_file.
        """),
        instructions=instructions,
        knowledge=knowledge_report,
        search_knowledge=True,
        tools=tools,
        markdown=False,
    )
