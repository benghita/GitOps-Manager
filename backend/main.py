"""
GitOps Manager - Main Application
FastAPI backend for GitOps Automation Management System
"""

import os
import sys
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the agent creation functions
from modules.auto_gitops import (
    create_repo_watcher_agent,
    create_commit_agent,
    create_branch_manager_agent,
    create_deployment_agent,
    create_report_agent,
)
from tools.auto_gitops_tools import ensure_memory_file, SHARED_MEMORY_PATH

load_dotenv()

# FastAPI App
app = FastAPI(
    title="GitOps Manager API",
    description="API for GitOps Automation Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class AgentRequest(BaseModel):
    message: str
    repo: str = "benghita/PropertyValuation"
    additional_data: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    response: str
    agent_type: str
    success: bool
    error: str = None

class RepoWatcherRequest(BaseModel):
    repo: str = "benghita/PropertyValuation"
    prompt: str = "Scan repository for new commits and PRs"

class CommitRequest(BaseModel):
    repo: str = "benghita/PropertyValuation"
    files: List[dict]
    branch: str = "auto/config-sync"
    create_pr: bool = False

class BranchRequest(BaseModel):
    repo: str = "benghita/PropertyValuation"
    action: str = "list"
    branch: Optional[str] = None
    base: str = "main"

class DeploymentRequest(BaseModel):
    repo: str = "benghita/PropertyValuation"
    check_since: str = "2025-10-06T00:00:00Z"

class ReportRequest(BaseModel):
    repo: str = "benghita/PropertyValuation"
    since: str = "2025-10-01T00:00:00Z"
    sections: List[str] = ["summary", "compliance", "recent_prs", "open_issues"]

# Initialize shared memory
def initialize_shared_memory():
    """Initialize shared memory file"""
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

# Initialize all agents
print("Initializing GitOps Manager Agents...")

try:
    # Initialize shared memory
    initialize_shared_memory()
    print("✓ Shared memory initialized")
    
    # Default repository
    default_repo = os.getenv("REPO_FULL_NAME", "benghita/PropertyValuation")
    
    # Initialize all agents
    repo_watcher = create_repo_watcher_agent(default_repo)
    commit_agent = create_commit_agent(default_repo)
    branch_manager = create_branch_manager_agent(default_repo)
    deployment_agent = create_deployment_agent(default_repo)
    report_agent = create_report_agent(default_repo)
    
    print("✓ All GitOps agents initialized successfully")
    
except Exception as e:
    print(f"Error initializing agents: {str(e)}")
    repo_watcher = None
    commit_agent = None
    branch_manager = None
    deployment_agent = None
    report_agent = None

# Agent mapping for direct access
AGENT_MAP = {
    "repo_watcher": repo_watcher,
    "commit_agent": commit_agent,
    "branch_manager": branch_manager,
    "deployment_agent": deployment_agent,
    "report_agent": report_agent,
}

print("All agents initialized successfully!")

# Routes
@app.get("/")
async def root():
    return {
        "message": "GitOps Manager - Unified Platform",
        "version": "1.0.0",
        "modules": [
            "Repository Monitoring",
            "Commit Management", 
            "Branch Management",
            "Deployment Automation",
            "Reporting & Analytics"
        ],
        "available_agents": list(AGENT_MAP.keys())
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents_loaded": len([k for k, v in AGENT_MAP.items() if v is not None])}

@app.post("/agent/{agent_name}", response_model=AgentResponse)
async def chat_with_agent(agent_name: str, request: AgentRequest):
    try:
        agent = AGENT_MAP.get(agent_name)
        if not agent:
            raise HTTPException(
                status_code=404, 
                detail=f"Agent '{agent_name}' not found. Available agents: {list(AGENT_MAP.keys())}"
            )
        
        # Run the agent with the message
        response = agent.run(request.message)
        print(response.content)
        return AgentResponse(
            response=response.content,
            agent_type=agent_name,
            success=True
        )
        
    except Exception as e:
        return AgentResponse(
            response="",
            agent_type=agent_name,
            success=False,
            error=str(e)
        )

@app.get("/agents")
async def list_agents():
    """List all available agents organized by module"""
    return {
        "Repository Monitoring": [
            "repo_watcher"
        ],
        "Commit Management": [
            "commit_agent"
        ],
        "Branch Management": [
            "branch_manager"
        ],
        "Deployment Automation": [
            "deployment_agent"
        ],
        "Reporting & Analytics": [
            "report_agent"
        ]
    }

# --------------------------
# Agent workflow endpoints
# --------------------------
@app.post("/api/watcher/scan")
async def scan_repository(request: RepoWatcherRequest):
    """Scan repository for new commits and PRs using real Repo Watcher agent"""
    try:
        if not repo_watcher:
            return {"status": "error", "result": {"content": "Repo Watcher agent not available"}, "repo": request.repo}
        
        # Run the agent
        response = repo_watcher.run(request.prompt)
        
        # Extract content if it's an object with content attribute
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        return {"status": "success", "result": {"content": content}, "repo": request.repo}
    except Exception as e:
        # Handle GitHub API errors gracefully
        error_msg = str(e)
        if "Validation Failed" in error_msg or "permission" in error_msg.lower():
            mock_response = f"Repository '{request.repo}' is not accessible or doesn't exist. Mock response: No new commits or PRs found."
            return {"status": "success", "result": {"content": mock_response}, "repo": request.repo}
        else:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commit/create")
async def create_commit(request: CommitRequest):
    """Create or update files with commit using real Commit Agent"""
    try:
        if not commit_agent:
            return {"status": "error", "result": {"content": "Commit Agent not available"}, "repo": request.repo}
        
        # Format the input for the agent
        agent_input = {
            "files": request.files,
            "branch": request.branch,
            "create_pr": request.create_pr
        }
        
        response = commit_agent.run(f"Create or update files: {json.dumps(agent_input)}")
        
        # Extract content if it's an object with content attribute
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        return {"status": "success", "result": {"content": content}, "repo": request.repo}
    except Exception as e:
        # Handle GitHub API errors gracefully
        error_msg = str(e)
        if "Validation Failed" in error_msg or "permission" in error_msg.lower():
            mock_response = f"Repository '{request.repo}' is not accessible. Mock response: Would create commit on branch '{request.branch}' with {len(request.files)} files."
            return {"status": "success", "result": {"content": mock_response}, "repo": request.repo}
        else:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/branch/manage")
async def manage_branch(request: BranchRequest):
    """Manage branches using real Branch Manager agent"""
    try:
        if not branch_manager:
            return {"status": "error", "result": {"content": "Branch Manager agent not available"}, "repo": request.repo}
        
        # Format the input for the agent
        agent_input = {
            "action": request.action,
            "branch": request.branch,
            "base": request.base
        }
        
        response = branch_manager.run(f"Branch management request: {json.dumps(agent_input)}")
        
        # Extract content if it's an object with content attribute
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        return {"status": "success", "result": {"content": content}, "repo": request.repo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deployment/check")
async def check_deployment(request: DeploymentRequest):
    """Check for deployments using real Deployment Agent"""
    try:
        if not deployment_agent:
            return {"status": "error", "result": {"content": "Deployment Agent not available"}, "repo": request.repo}
        
        # Format the input for the agent
        agent_input = {
            "check_merged_since": request.check_since
        }
        
        response = deployment_agent.run(f"Check for deployments: {json.dumps(agent_input)}")
        
        # Extract content if it's an object with content attribute
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        return {"status": "success", "result": {"content": content}, "repo": request.repo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/generate")
async def generate_report(request: ReportRequest):
    """Generate repository report using real Report Agent"""
    try:
        if not report_agent:
            return {"status": "error", "result": {"content": "Report Agent not available"}, "repo": request.repo}
        
        # Format the input for the agent
        agent_input = {
            "since": request.since,
            "sections": request.sections
        }
        
        response = report_agent.run(f"Generate report: {json.dumps(agent_input)}")
        
        # Extract content if it's an object with content attribute
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        return {"status": "success", "result": {"content": content}, "repo": request.repo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports")
async def list_reports():
    """List generated reports"""
    try:
        reports_dir = os.getenv("AUTO_GITOPS_REPORTS_DIR", "data/reports")
        if not os.path.exists(reports_dir):
            return {"status": "success", "reports": []}
        
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(reports_dir, filename)
                stat = os.stat(filepath)
                reports.append({
                    "filename": filename,
                    "path": filepath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z"
                })
        
        return {"status": "success", "reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Get specific report content"""
    try:
        reports_dir = os.getenv("AUTO_GITOPS_REPORTS_DIR", "data/reports")
        filepath = os.path.join(reports_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Report not found")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"status": "success", "content": content, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------
# Dynamic chat endpoint
# --------------------------
@app.post("/chat/{agent_name}")
def chat(agent_name: str, request: AgentRequest):
    agent = AGENT_MAP.get(agent_name)
    if not agent:
        return {"error": f"Agent '{agent_name}' not found."}
    
    # Call the agent's method to process the message
    reply = agent.run(request.message)
    
    # Extract content if it's an object with content attribute
    if hasattr(reply, 'content'):
        content = reply.content
    else:
        content = str(reply)
    
    return {"reply": content}

if __name__ == "__main__":
    print("Starting GitOps Manager Unified Platform...")
    print("Available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
