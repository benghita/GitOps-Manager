# Commit Message Conventions

We follow **Conventional Commits** to ensure consistent and parseable history.

## 1. Format
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]

### Example
feat(api): add user authentication
fix(ui): correct modal alignment issue
chore(ci): update GitHub Actions version
docs(readme): improve setup instructions


## 2. Allowed Types
- **feat**: A new feature.
- **fix**: A bug fix.
- **docs**: Documentation only changes.
- **style**: Changes that do not affect code meaning (white-space, formatting).
- **refactor**: Code change that neither fixes a bug nor adds a feature.
- **perf**: Performance improvement.
- **test**: Adding or correcting tests.
- **chore**: Routine tasks such as dependency updates or CI adjustments.

## 3. Scopes
- Use the scope to clarify where the change applies, e.g., `(ui)`, `(backend)`, `(config)`.
- Scope is optional but recommended.

## 4. Body and Footer
- The body should explain *why* the change was made.
- Use footer to link issues:  
  `Closes #123` or `Related to #456`

## 5. Validation
Automated systems must reject commits that do not match the format:
`<type>(<scope>): <summary>`

Agents creating commits should:
1. Generate a commit message automatically when possible.
2. Validate message format before committing.
3. Log any invalid messages to shared memory for later correction.
