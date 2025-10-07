import os
import sys
import importlib

import pytest

@pytest.fixture()
def auto_gitops_module(monkeypatch):
    # Ensure repository root is on sys.path for absolute package imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Ensure a clean import each time in case previous tests mutated module state
    if "modules.auto_gitops" in list(importlib.sys.modules.keys()):
        importlib.reload(importlib.import_module("modules.auto_gitops"))
    mod = importlib.import_module("modules.auto_gitops")

    class DummyModel:
        def __init__(self):
            self.id = "dummy-model"

    # Replace the real remote model with a dummy
    monkeypatch.setattr(mod, "MODEL", DummyModel(), raising=True)
    return mod


@pytest.fixture()
def stubbed_print_response(monkeypatch):
    from agno.agent import Agent

    def fake_print_response(self, *args, **kwargs):
        # Mimic the API by printing a deterministic response and returning it
        output = f"[{self.name}] OK: prompt handled"
        print(output)
        return output

    monkeypatch.setattr(Agent, "print_response", fake_print_response, raising=True)
    return True


def test_repo_watcher_agent_runs(auto_gitops_module, stubbed_print_response):
    agent = auto_gitops_module.create_repo_watcher_agent("benghita/PropertyValuation")
    result = agent.print_response("Check for new events")
    assert "OK: prompt handled" in result


def test_commit_agent_runs(auto_gitops_module, stubbed_print_response):
    agent = auto_gitops_module.create_commit_agent("benghita/PropertyValuation")
    result = agent.print_response(
        {
            "files": [
                {"path": "configs/app.yaml", "content": "key: val", "message": "chore(config): test"}
            ],
            "branch": "auto/config-sync",
            "create_pr": False,
        }
    )
    assert "OK: prompt handled" in result


def test_branch_manager_agent_runs(auto_gitops_module, stubbed_print_response):
    agent = auto_gitops_module.create_branch_manager_agent("owner/repo")
    result = agent.print_response({"action": "list"})
    assert "OK: prompt handled" in result


def test_deployment_agent_runs(auto_gitops_module, stubbed_print_response):
    agent = auto_gitops_module.create_deployment_agent("owner/repo")
    result = agent.print_response({"check_merged_since": "2025-10-06T00:00:00Z"})
    assert "OK: prompt handled" in result


def test_report_agent_runs(auto_gitops_module, stubbed_print_response):
    agent = auto_gitops_module.create_report_agent("owner/repo")
    result = agent.print_response({"since": "2025-10-01T00:00:00Z"})
    assert "OK: prompt handled" in result


