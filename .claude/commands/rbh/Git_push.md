# Git Add, Commit and Push

Perform a complete git workflow: add all changes, commit with a descriptive message, and push to the remote repository.

Usage: `/rbh git-push "commit message"`

## Steps:

1. Check git status to see what files have changed
2. Add all changes (including new files) to staging area with `git add .`
3. Commit all changes with the provided message using format: `git commit -am "message"` for tracked files and handle new files separately
4. Push to remote repository with `git push`
5. Confirm the push was successful

## Example:
```
/rbh git-push "feat: implement new financial calculation engine"
```

This will:
- Add all modified and new files automatically
- Commit with message "feat: implement new financial calculation engine"
- Push to the remote repository
- Handle pre-commit hooks automatically