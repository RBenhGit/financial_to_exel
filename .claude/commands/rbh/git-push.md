# Git Add, Commit and Push

Perform a complete git workflow: add all changes, commit with a descriptive message, and push to the remote repository.

**Usage**: `/rbh/git-push <commit message>`

**Arguments**: $ARGUMENTS

## Steps:

1. Check git status to see what files have changed
2. Add all changes to staging area
   - Use `git add .` for all files
   - Handle both tracked and untracked files
3. Create commit with provided message
   - Follow conventional commit format if applicable
   - Include Claude Code co-authorship
4. Push to remote repository
5. Confirm push was successful
6. Handle pre-commit hooks if configured

## Example:

```bash
/rbh/git-push "feat: implement new financial calculation engine"
/rbh/git-push "fix: resolve cache invalidation issue"
/rbh/git-push "docs: update API documentation"
```

## Commit Message Format:

Follows conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks

## Implementation:

```bash
# Check status
git status

# Add all changes
git add .

# Commit with message
git commit -m "$ARGUMENTS

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push
```

## Safety Checks:

- Verifies git repository exists
- Checks for uncommitted changes
- Handles merge conflicts
- Respects pre-commit hooks
- Confirms remote is reachable

## Notes:

- This command will NOT force push
- Pre-commit hooks will run automatically (if configured)
- Failed hooks will prevent the commit
- Use git CLI directly for complex scenarios (rebase, force push, etc.)
