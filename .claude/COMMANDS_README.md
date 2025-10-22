# Claude Code Commands Reference

This project has two main command namespaces:

## 📋 Task Master Commands (`/tm`)

Access comprehensive task management and workflow automation.

### Quick Access
- `/tm` - Main entry point with usage guide
- `/tm/help` - Complete command reference
- `/tm/learn` - Interactive learning guide

### Most Used Commands

#### Daily Workflow
```bash
/tm/next                          # Get next available task
/tm/list                          # Show all tasks
/tm/show <id>                     # View task details
/tm/set-status/to-done <id>       # Mark task complete
```

#### Task Management
```bash
/tm/add-task <description>        # Create new task
/tm/expand <id>                   # Break into subtasks
/tm/update <id> <changes>         # Update task
/tm/remove-task <id>              # Remove task
```

#### Analysis
```bash
/tm/analyze-complexity            # Analyze task complexity
/tm/complexity-report             # View complexity report
```

#### Project Setup
```bash
/tm/init                          # Initialize Task Master
/tm/parse-prd                     # Generate tasks from PRD
/tm/models                        # Configure AI models
```

### Full Command List

See `/tm/help` for complete list of 50+ commands organized by category:
- Setup & Installation
- Project Initialization
- Task Generation & Management
- Status Management
- Subtask Operations
- Analysis & Breakdown
- Dependencies
- Workflows & Automation
- Utilities

## 🚀 Project Commands (`/rbh`)

Project-specific commands for financial analysis workflows.

### Quick Access
- `/rbh` - Main entry point with usage guide

### Available Commands

#### Git Workflow
```bash
/rbh/git-push "commit message"    # Add, commit, and push
```

#### Testing & Quality
```bash
/rbh/run-tests                    # Run test suite
/rbh/run-tests-coverage           # Tests with coverage
/rbh/lint                         # Run linting checks
/rbh/format                       # Format code (black/isort)
```

#### Application Launch
```bash
/rbh/run-app                      # Start Streamlit app
/rbh/run-fcf                      # Run FCF analysis app
```

#### Data Management
```bash
/rbh/clear-cache [type]           # Clear data cache
/rbh/refresh-data [symbols]       # Refresh financial data
```

## ⚡ Keyboard Shortcuts

Defined in [.claude/settings.json](.claude/settings.json):

```bash
tm-next         → /tm/next
tm-list         → /tm/list
tm-status       → /tm/status
tm-show         → /tm/show
git-push        → /rbh/git-push
run-tests       → /rbh/run-tests
run-app         → /rbh/run-fcf
```

To use shortcuts, you can type them directly or use tab completion.

## 📂 Command Structure

```
.claude/commands/
├── tm.md                    # Task Master main entry
├── rbh.md                   # Project commands main entry
├── tm/                      # Task Master commands
│   ├── help.md
│   ├── learn.md
│   ├── next/
│   ├── list/
│   ├── show/
│   ├── add-task/
│   ├── expand/
│   ├── set-status/
│   └── ... (50+ total commands)
└── rbh/                     # Project-specific commands
    ├── git-push.md
    ├── run-tests.md
    ├── run-tests-coverage.md
    ├── lint.md
    ├── format.md
    ├── run-app.md
    ├── run-fcf.md
    ├── clear-cache.md
    └── refresh-data.md
```

## 🎯 Usage Tips

### Tab Completion
Type `/tm/` or `/rbh/` and press Tab to see all available commands.

### Natural Language
Many commands accept natural language:
```bash
/tm/list pending high priority
/tm/add-task create user authentication system
/tm/update mark all API tasks as done
```

### Argument Passing
Commands use `$ARGUMENTS` to receive parameters:
```bash
/tm/show 45                       # ID as argument
/rbh/git-push "feat: new feature" # Message as argument
/rbh/clear-cache disk             # Type as argument
```

### Chaining Commands
Use Task Master workflows for complex operations:
```bash
/tm/workflows/smart-flow          # Intelligent workflow
/tm/workflows/pipeline            # Chain commands
```

## 🔧 Configuration

### Allowed Tools
See [.claude/settings.json](.claude/settings.json) for allowed Bash commands and MCP tools.

Current allowed tools:
- Task Master CLI (`task-master *`)
- Git operations (`git *`)
- Python execution (`python *`)
- Testing (`pytest *`)
- Linting (`flake8 *`)
- Formatting (`black *`, `isort *`)
- Streamlit (`streamlit *`)
- MCP Task Master (`mcp__task_master_ai__*`)

### Adding New Commands

1. Create markdown file in appropriate directory:
   - `/tm/` for Task Master commands
   - `/rbh/` for project commands

2. Use standard format:
   ```markdown
   # Command Title

   Description of what the command does.

   **Usage**: `/namespace/command-name [arguments]`

   **Arguments**: $ARGUMENTS

   ## Steps:
   1. Step one
   2. Step two

   ## Examples:
   ```bash
   /command example
   ```

   ## Implementation:
   ```bash
   actual commands to run
   ```
   ```

3. Restart Claude Code or use `/reload` to refresh commands

## 📚 Additional Resources

- Task Master Documentation: See `CLAUDE.md` for integration guide
- MCP Configuration: See `.mcp.json` for MCP server setup
- Git Workflow: See `/rbh/git-push` for commit conventions

## 🆘 Getting Help

- `/tm/help` - Task Master command reference
- `/tm/learn` - Interactive Task Master tutorial
- Type any command without arguments to see usage information
- Use tab completion to explore available commands
