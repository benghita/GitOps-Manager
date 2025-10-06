# GitOps Manager

An intelligent GitOps automation system powered by AI agents that monitor, manage, and deploy changes to GitHub repositories.

## 🚀 Features

- **Repo Watcher Agent**: Monitors repositories for new commits, branches, and pull requests
- **Commit Agent**: Automatically creates and validates commits with conventional commit standards
- **Branch Manager Agent**: Manages automation branches with `auto/` prefix
- **Deployment Agent**: Triggers deployment pipelines when PRs merge to main
- **Report Agent**: Generates compliance and activity reports

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd gitops-manager

# Install dependencies
uv install
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required for GitHub operations
export GITHUB_ACCESS_TOKEN="your_github_token"

# API keys for AI models
export GOOGLE_API_KEY="your_google_api_key"

# Repository to monitor
export REPO_FULL_NAME="owner/repository"
```

### Knowledge Base

The system includes a knowledge base with:
- `data/kb/branching_strategy.md` - Git branching best practices
- `data/kb/commit_conventions.md` - Conventional commit standards
- `data/kb/gitops_principles.md` - GitOps methodology

## 🏃‍♂️ Quick Start

### Run All Agents
```bash
uv run python main.py
```

### Run Tests
```bash
uv run pytest
```

## 🤖 Agents Overview

### Repo Watcher Agent
- **Purpose**: Monitor repository activity
- **Input**: Repository name
- **Output**: JSON with new commits/PRs detected
- **Tools**: GithubTools, shared memory

### Commit Agent
- **Purpose**: Create and validate commits
- **Input**: File changes with commit message
- **Output**: Commit SHA and branch info
- **Tools**: GithubTools, commit validation, shared memory

### Branch Manager Agent
- **Purpose**: Manage automation branches
- **Input**: Action (create/list/check_sync), branch name
- **Output**: Branch status and sync recommendations
- **Tools**: GithubTools, shared memory

### Deployment Agent
- **Purpose**: Trigger deployments on main branch changes
- **Input**: Check date for merged PRs
- **Output**: Deployment status and pipeline info
- **Tools**: GithubTools, pipeline trigger, shared memory

### Report Agent
- **Purpose**: Generate repository reports
- **Input**: Date range and report sections
- **Output**: Markdown report file path
- **Tools**: GithubTools, report generation

## 📁 Project Structure

```
gitops-manager/
├── modules/
│   └── auto_gitops.py          # Agent definitions
├── tools/
│   └── auto_gitops_tools.py    # Custom tools
├── data/
│   ├── kb/                     # Knowledge base
│   └── reports/                # Generated reports
├── tests/
│   └── test_agents.py          # Agent tests
├── main.py                     # Main workflow
└── pyproject.toml             # Dependencies
```

## 🔧 Customization

### Adding New Agents
1. Create agent function in `modules/auto_gitops.py`
2. Define instructions, tools, and knowledge
3. Add to main workflow in `main.py`

### Custom Tools
Add new tools in `tools/auto_gitops_tools.py`:
```python
def your_custom_tool(param: str) -> str:
    """Your tool description."""
    # Implementation
    return json.dumps({"status": "success"})
```

## 🧪 Testing

The project includes comprehensive tests:
- Agent instantiation tests
- Tool functionality tests
- Mock GitHub operations

Run tests with:
```bash
uv run pytest -v
```

## 📊 Knowledge Base

The system uses LanceDB for vector storage and includes:
- **Branching Strategy**: Git flow and branching best practices
- **Commit Conventions**: Conventional commit standards
- **GitOps Principles**: Deployment and infrastructure management

## 🔒 Security

- GitHub tokens are required for real operations
- Agents operate with read-only permissions by default
- File operations are restricted to whitelisted paths
- No destructive operations without explicit configuration

## 🚀 Deployment

For production use:
1. Set up proper GitHub token with required permissions
2. Configure knowledge base with your organization's standards
3. Set up monitoring for agent operations
4. Configure CI/CD pipelines for automated deployments

