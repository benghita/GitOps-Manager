# Branching Strategy Guidelines

## 1. Naming Conventions
- All automation branches must begin with the prefix `auto/`.
- Feature branches use `feature/<short-description>`.
- Hotfix branches use `hotfix/<ticket-id>-<summary>`.
- Release branches use `release/<version>`.

Example:
auto/config-sync
feature/add-login-endpoint
hotfix/bug-1234-crash-on-start


## 2. Branch Lifecycles
- `main`: Always stable, production-ready code.
- `develop`: Integration branch for new features.
- `auto/*`: Temporary branches created by automation (agents, pipelines).
- `feature/*`: Created from `develop` and merged back via Pull Request.
- `hotfix/*`: Created from `main` and merged into both `main` and `develop`.

## 3. Sync Rules
- Automation branches (`auto/*`) must be rebased on `main` before creating pull requests.
- Merge conflicts in automation branches must be resolved by human review before PR merge.

## 4. Access Control
- Only CI/CD systems or designated agents may create branches prefixed with `auto/`.
- Only maintainers may merge to `main` and `release/*`.

## 5. Deletion Policy
- `auto/*` branches are ephemeral — automatically deleted after successful merge or 7 days of inactivity.
