# Auto GitOps Manager — Module Handbook

> Managerial-focused, detailed handbook for the Auto GitOps Manager module (Agno + GithubTools). Use this as the single-source module document for stakeholders, product owners, and engineering leads.

---

# 1. Executive summary

**Auto GitOps Manager** is a compact multi-agent system built on the Agno agent framework with GitHub integration (`GithubTools`). It automates and governs core GitOps tasks—branch lifecycle, automated commits, deployment triggering (simulated), and compliance reporting—so product teams can run reproducible, policy-driven infrastructure and application changes with minimal manual DevOps effort.

This handbook describes the module at a managerial level: goals, capabilities, architecture, agent responsibilities, and operational guardrails. It is intentionally practical and focused: implementers can convert these guidelines into an MVP within a single sprint.

---

# 2. Goals and value proposition

**Primary goals**

* Reduce manual overhead for routine repository operations (configs, small infra edits).
* Enforce consistent branching and commit discipline automatically.
* Provide predictable, auditable simulation of deployments and compliance reporting.

**Business value**

* Faster, safer operational changes; fewer human errors when updating infra/config.
* Clear audit trail and compliance artifacts for security and QA.
* Easier onboarding: developers can rely on automated agents for repetitive Git workflows.

---

# 3. Main features (high level)

* **Automated branch creation & governance** (prefixed `auto/*`).
* **Conventional commit enforcement** (message generation + validation).
* **Simulated CI/CD triggers** on merges to `main` and deployment logging.
* **Knowledge-driven behavior** using domain Markdown KBs (branching, commits, GitOps principles).
* **Scheduled and on-demand compliance reports** (Markdown files).
* **Shared JSON memory** for inter-agent state (shared_memory.json).

---

# 4. Architecture & workflow (managerial)

## High-Level Flow
```
        ┌──────────────────────────────────────────┐
        │              Auto GitOps Team            │
        └──────────────────────────────────────────┘
                          │
          ┌───────────────┼──────────────────┐
          │               │                  │
   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
   │ Branch Mgr. │  │ Commit Agent │  │ Deploy Agent │
   └─────────────┘  └──────────────┘  └──────────────┘
          │               │                  │
          └───────┬───────┴──────────────┬───┘
                  │                      │
          ┌──────────────┐        ┌──────────────┐
          │ Repo Watcher │        │ Report Agent │
          └──────────────┘        └──────────────┘
```

**Core components**

* *Agents*: independent worker programs (Repo Watcher, Commit Agent, Branch Manager, Deployment Agent, Report Agent).
* *Tools*: `GithubTools` (Agno toolkit) and small custom utilities (validation, pipeline simulation, shared-memory I/O).
* *Knowledge*: three Markdown knowledge bases (branching strategy, commit conventions, GitOps principles) indexed with PgVector for semantic retrieval.
* *Shared memory*: a JSON file (`shared_memory.json`) holding short-lived coordination variables (last commit SHAs, branch maps, last deployed commit).

**Typical flow**

1. **Repo Watcher** observes repository activity (commits, PRs, branches).
2. If changes are detected, it emits a structured event to trigger **Commit Agent** or **Branch Manager**.
3. **Commit Agent** creates/updates files and commits following conventions; optionally opens PRs.
4. **Branch Manager** ensures branch naming policy, creates `auto/*` branches, and checks sync with `main`.
5. When PRs merge into `main`, **Deployment Agent** simulates a pipeline run and logs the deployment.
6. **Report Agent** periodically or on-demand generates compliance and activity reports.

**Safety pattern**: agents prefer non-destructive actions and human-in-the-loop for risky ops (merges, deletions). Policies enforced via KB and guardrails.

---

# 5. Knowledge bases (KB) summary

The module uses three Markdown KBs. Each KB is short, clear, and written to be read by agents to guide decisions. They are stored in `knowledge/*.md` and indexed in PgVector.

* **branching_strategy.md** — naming rules, lifecycles, sync & deletion policy.
* **commit_conventions.md** — Conventional Commits format, allowed types/scopes, validation rules.
* **gitops_principles.md** — declarative infra, versioning, automated delivery, observability, security.

KBs are used at runtime for decisioning: e.g., Commit Agent uses `commit_conventions` to validate messages before committing.

---

# 6. Agents — detailed managerial view

This section has a dedicated, consistent template for each agent: Purpose, Core responsibilities (bullet list), Tools used (developer-facing), Knowledge required, Memory/storage, Guardrails (policy), Example outputs, and Typical scenarios.

## 6.1 Repo Watcher Agent

**Purpose**

Observe repository state (commits, branches, pull requests) and produce structured events to trigger other agents.

**Core responsibilities**

* Poll or react to repository changes (pushes, new PRs, new branches).
* Compare last-seen state vs current state using shared memory (short-term).
* Emit events: `commit_detected`, `pr_opened`, `branch_created`.
* Optionally annotate events with minimal metadata: commit SHA, branch name, PR id, timestamp.

**Tools used**

* `GithubTools.list_branches`
* `GithubTools.get_pull_requests`
* `GithubTools.get_repository_with_stats`
* Custom tool: `read_shared_memory(key)`

**Knowledge required**

* Minimal; this agent reads repository state. It does not need KB texts because it only detects changes (no policy decisioning).

**Memory / storage**

* Uses **storage** (short-term) recorded in `shared_memory.json` keys: `last_checked_commit_sha`, `last_checked_pr_id`.
* Writes only detection markers; does not persist large logs.

**Guardrails**

* Read-only: must not write to the repository (no commits, no branches, no comments).
* Throttle API calls to avoid rate limiting.
* When in doubt (ambiguous event), prefer returning `status: 'monitor'` and let human operator request action.

**Example outputs**

```json
{
  "new_commits": ["abc123"],
  "new_prs": [45],
  "timestamp": "2025-10-06T12:00:00Z"
}
```

**Typical scenarios**

* Developer pushes to `feature/*`: Repo Watcher sees new commit and triggers Commit Agent to validate and produce a PR.
* A PR is opened targeting `main`: Repo Watcher notifies Deployment Agent and Report Agent for tracking.

---

## 6.2 Commit Agent

**Purpose**

Create and update repository files programmatically while enforcing commit message conventions and path whitelists.

**Core responsibilities**

* Accept structured file-change payloads (path, content, commit message).
* Validate commit messages against the `commit_conventions` KB.
* Read the current file (if exists) and compute a short diff summary before updating.
* Create or update files via the GitHub API; optionally open a PR for human review.
* Log commit metadata to shared memory for traceability.

**Tools used**

* `GithubTools.get_file_content`
* `GithubTools.create_file`
* `GithubTools.update_file`
* `GithubTools.create_pull_request` (optional)
* Custom: `validate_commit_message(message)`
* Custom: `read_shared_memory`, `write_shared_memory`

**Knowledge required**

* `commit_conventions.md` — agent searches this KB to confirm allowed commit types, scopes, and phrasing. The agent should quote or cite the rule if it rejects a message.

**Memory / storage**

* **storage**: `last_commit_sha`, `recent_commit_message` (in `shared_memory.json`).
* Commit metadata must be short; do not store file contents in shared memory.

**Guardrails**

* **Whitelist-only**: Only modify files under configured directories (e.g., `configs/`, `infra/`, `data/`). Any attempt to modify outside whitelist must be rejected with a clear error.
* **No deletes**: Agent cannot remove files. Deletions require human confirmation.
* **PR required for main**: Direct commits to `main` are disallowed—create PRs instead.
* **Validation mandatory**: commit messages must pass `validate_commit_message`. If invalid, return clear guidance and do not perform write.

**Expected outputs**

```json
{
  "status": "success",
  "commit_sha": "abc123",
  "branch": "auto/config-sync",
  "pr_number": 42,
  "files_updated": ["configs/app.yaml"]
}
```

**Typical scenarios**

* Automatic config sync: periodic script produces changes under `configs/`; Commit Agent validates messages and opens a PR to `develop`.
* Emergency non-invasive patch: small doc fix under `docs/` — Commit Agent may commit directly to `develop` if policy allows.

---

## 6.3 Branch Manager Agent

**Purpose**

Control the lifecycle of automation branches (`auto/*`), enforce naming and sync rules, and provide safe branch recommendations.

**Core responsibilities**

* Create `auto/<task>` branches when requested by other agents.
* List and audit branch states; report branches behind `main`.
* Enforce naming prefixes and refuse unexpected branch names.
* Provide human-readable recommendations for merges and rebases.

**Tools used**

* `GithubTools.list_branches`
* `GithubTools.create_branch`
* `GithubTools.get_branch_content`
* `read_shared_memory`, `write_shared_memory`

**Knowledge required**

* `branching_strategy.md` — to interpret naming rules, lifecycles, and deletion policies.

**Memory / storage**

* **storage**: mapping of `auto` branch -> base branch + creation timestamp in `shared_memory.json`.
* Branch expiry reminders can be based on these timestamps.

**Guardrails**

* Branch creation only for prefix `auto/`. Reject any create requests that do not match policy.
* Do not delete branches automatically unless retention policy and human opt-in are configured.
* Merges must be suggested, not performed; human approval required for merging to `main`.

**Expected outputs**

```json
{ "status": "created", "branch": "auto/config-sync", "base": "main" }
```

**Typical scenarios**

* Automation creates `auto/config-sync` to stage configuration changes; Branch Manager ensures branch exists and points at latest `main`.
* Periodic housekeeping: Branch Manager lists `auto/*` branches older than 7 days and flags them for deletion.

---

## 6.4 Deployment Agent

**Purpose**

Simulate or trigger CI/CD pipelines for merges into `main`, and reliably log deployment events for auditing.

**Core responsibilities**

* Detect merged PRs into `main`.
* Trigger a simulated pipeline (`trigger_pipeline`) or call real CI/CD webhooks (if configured).
* Write deployment metadata to `shared_memory.json` (last_deployed_commit, pipeline_id, status).
* Optionally create an issue or comment documenting the deployment outcome.

**Tools used**

* `GithubTools.get_pull_requests`
* `GithubTools.get_pull_request_with_details`
* `GithubTools.create_issue` (optional logging)
* Custom: `trigger_pipeline(repo, branch)`
* `read_shared_memory`, `write_shared_memory`

**Knowledge required**

* `gitops_principles.md` — to ensure deployment behavior follows GitOps practices (immutable changes, observability requirements, and remediation guidance).

**Memory / storage**

* **storage**: `last_deployed_commit_sha`, `last_pipeline_id`, `last_deployment_status` in `shared_memory.json`.

**Guardrails**

* Only trigger pipelines for merges to `main` (or other configured release branches).
* Do not perform repository edits—only logging and optional issue creation permitted.
* If pipeline fails, write a clear failure entry and avoid automatic rollback actions (rollback decisions must be human-approved).

**Expected outputs**

```json
{ "status": "deployment_triggered", "pipeline": {"pipeline_id":"mock-pipeline-..."}, "deployed_commit": "def456" }
```

**Typical scenarios**

* A PR is merged into `main`: Deployment Agent triggers a mock pipeline, logs success, and Report Agent later picks up the result for the weekly compliance report.
* Pipeline failure: Deployment Agent writes failure reason to shared memory and creates an internal issue for ops to investigate.

---

## 6.5 Report Agent

**Purpose**

Produce readable compliance and activity reports for stakeholders (engineering leads, security, product). Reports are human-friendly Markdown files stored under `data/reports/`.

**Core responsibilities**

* Collect metrics: PR counts, merge frequency, invalid commit counts, branch-staleness.
* Validate commit messages using `commit_conventions.md` rules and list violations.
* Summarize deployment outcomes from `shared_memory.json`.
* Produce a dated Markdown report and save it via `create_report_file`.

**Tools used**

* `GithubTools.get_pull_requests`
* `GithubTools.list_issues`
* `GithubTools.get_repository_with_stats`
* Custom: `create_report_file(repo, title, content_md)`
* `validate_commit_message`

**Knowledge required**

* All three KBs: `branching_strategy.md`, `commit_conventions.md`, and `gitops_principles.md` — used to ground compliance checks and recommendations.

**Memory / storage**

* Does not persist runtime variables; writes report files to `data/reports/`.
* Report metadata (path, generated_at) can be appended to `shared_memory.json` if needed for discovery.

**Guardrails**

* Read-only: do not alter repository data.
* Ensure reports do not include sensitive values (tokens, secret contents, private keys).
* When reporting violations, include remediation steps and responsible teams (if known) rather than prescriptive automatic fixes.

**Expected outputs**

A Markdown file such as `data/reports/gitops_audit_2025-10-06.md` with sections: Executive summary, Highlights, Issues & Remediation, Recent deployments, Recommendations.

**Typical scenarios**

* Weekly governance report: lists PR velocity, top commit message violations, recommended policy updates.
* Pre-release check: run Report Agent to confirm branch hygiene and commit compliance before release planning.

---

# 7. Example scenarios (managerial case studies)

These short case studies show how agents collaborate in realistic situations.

## 7.1 Config sync (low risk)

* Cron job writes new config changes to a staging file. Repo Watcher detects new file.
* Commit Agent validates commit message `chore(config): update feature flags` (passes) and opens PR to `develop`.
* Branch Manager ensures PR branch uses `auto/` prefix.
* After human review, PR is merged into `develop` (not `main`). Deployment Agent not triggered. Report Agent records activity.

## 7.2 Critical hotfix (human-in-loop)

* Hotfix required: changes to `infra/` that could be disruptive. A human engineer opens a PR.
* Repo Watcher notifies agents. Commit Agent validates message. Branch Manager checks branch lifecycle.
* Deployment Agent is configured to require manual confirmation before pipeline trigger. Ops reviews and triggers pipeline. Report Agent adds a postmortem entry if any step failed.

## 7.3 Policy violation detection

* Developer pushes many small commits with non-conventional messages.
* Commit Agent rejects automated commit and logs validation failures to shared memory.
* Report Agent generates a report noting repeated violations and recommends a short training session or stricter gating in CI.

---

# 8. Operational notes for managers

**Who should run this?**

* A small DevOps or platform team (1–2 engineers) can manage the system; it's designed for low operational overhead.

**Onboarding**

* Provide the team with the KB documents (they can modify them to tighten or relax rules).
* Configure `GITHUB_ACCESS_TOKEN` with repository-level least privilege for the automation (create branches, create commits, read content, create issues if needed).
* Run the system in watch-only mode for 1–2 weeks before enabling writes: Repo Watcher detects and Report Agent produces reports without any agent performing writes.

**KPIs to monitor**

* % of commits that pass Conventional Commit validation.
* Average time to open PR after detected change.
* Number of `auto/*` branches created per week.
* Deployment success rate (simulated or actual pipelines).

**Risk & mitigation**

* *Risk*: accidental commits to `main`.
  *Mitigation*: block direct writes to `main` in code/config and require PR-based workflows.
* *Risk*: wrong KB leads to incorrect automated decisions.
  *Mitigation*: keep KB under version control and review KB changes in PRs.

---

# 9. Quickstart checklist for engineers (manager-friendly)

1. Clone repo and set environment variables (`OPENAI_API_KEY`, `GITHUB_ACCESS_TOKEN`, `PGVECTOR_URL`).
2. Populate `knowledge/` Markdown files and run KB ingest script (or the provided loader).
3. Start agents in read-only mode and watch Report Agent outputs for anomalies.
4. Turn on Commit Agent in `auto` mode for `configs/` only.
5. Gradually expand whitelist and allow PR creation for more directories.

---

# 10. Appendix — short reference

**File locations**

* Agents: `auto_gitops_agents.py`
* Custom tools: `auto_gitops_tools.py`
* KBs: `knowledge/branching_strategy.md`, `knowledge/commit_conventions.md`, `knowledge/gitops_principles.md`
* Shared memory: `memory/shared_memory.json`
* Reports: `data/reports/`

**Contact & ownership**

* Module owner: Platform Team / DevOps Lead
* Maintainers: Platform engineers (add names / rotation schedule here)

---

# 11. Closing notes (voice of the product owner)

Auto GitOps Manager is intentionally conservative: it favors observability and human-in-the-loop for high-risk operations while automating low-risk, high-volume tasks. For managers, the value is predictable execution, auditability, and measurable governance outcomes.

If you want, I can now produce: a one-page slide summarizing the module, a sample `settings.yaml`, or a quick `main.py` orchestrator scaffold wired to these agents (developer deliverables). Which would help you next?
