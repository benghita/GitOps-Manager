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

# Install Python dependencies
uv install

# Install Node.js dependencies for frontend
cd frontend
npm install
cd ..
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required for GitHub operations
export GITHUB_ACCESS_TOKEN="your_github_token"

# Optional: API keys for AI models
export GOOGLE_API_KEY="your_google_api_key"
export GEMINI_API_KEY="your_gemini_api_key"

# Optional: Repository to monitor
export REPO_FULL_NAME="owner/repository"
```

### Knowledge Base

The system includes a knowledge base with:
- `backend/data/knowledge/branching_strategy.md` - Git branching best practices
- `backend/data/knowledge/commit_conventions.md` - Conventional commit standards
- `backend/data/knowledge/gitops_principles.md` - GitOps methodology

## 🏃‍♂️ Quick Start

### Start the Full System
```bash
# Install dependencies
uv install
cd frontend && npm install && cd ..

# Start the backend API server
cd backend
python main.py
```

In a new terminal:
```bash
# Start the frontend development server
cd frontend
npm run dev
```

Then open your browser to: **http://localhost:3000**

### API Documentation
Visit **http://localhost:8000/docs** for interactive API documentation.

### Run Tests
```bash
cd backend
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

## 🌐 Web Dashboard & API

### Dashboard Features
- **Interactive forms** for each agent with validation
- **Results display** with syntax highlighting and IDE-like dark theme
- **Real-time agent responses** from agno AI agents
- **Reports management** with view/download options
- **Responsive design** for mobile and desktop

### API Endpoints
- `GET /` - System overview and available agents
- `GET /health` - Health check with agent status
- `GET /agents` - List all available agents by module
- `POST /agent/{agent_name}` - Direct agent communication
- `POST /api/watcher/scan` - Scan repository using Repo Watcher agent
- `POST /api/commit/create` - Create commits using Commit Agent
- `POST /api/branch/manage` - Manage branches using Branch Manager
- `POST /api/deployment/check` - Check deployments using Deployment Agent
- `POST /api/report/generate` - Generate reports using Report Agent
- `GET /api/reports` - List generated reports
- `GET /api/reports/{filename}` - Get specific report content
- `POST /chat/{agent_name}` - Chat with specific agent

### API Documentation
- Visit **http://localhost:8000/docs** for interactive API documentation.

## 📁 Project Structure

```
gitops-manager/
├── backend/
│   ├── main.py                 # FastAPI backend with agno agents
│   ├── modules/
│   │   └── auto_gitops.py      # Agent definitions
│   ├── tools/
│   │   └── auto_gitops_tools.py # Custom tools
│   ├── data/
│   │   ├── knowledge/          # Knowledge base
│   │   └── reports/            # Generated reports
│   └── tests/
│       └── test_agents.py      # Agent tests
├── frontend/
│   ├── pages/
│   │   ├── index.tsx           # Main dashboard
│   │   └── _app.tsx            # App wrapper
│   ├── styles/
│   │   └── globals.css         # IDE-like dark theme
│   └── package.json            # Frontend dependencies
└── pyproject.toml             # Python dependencies
```

## 🔧 Customization

### Adding New Agents
1. Create agent function in `backend/modules/auto_gitops.py`
2. Define instructions, tools, and knowledge
3. Add API endpoint in `backend/main.py`
4. Add frontend component in `frontend/pages/index.tsx`

### Custom Tools
Add new tools in `backend/tools/auto_gitops_tools.py`:
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
cd backend
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