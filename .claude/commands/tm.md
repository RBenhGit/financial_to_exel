# Task Master (tm) - Main Entry Point

Quick access to Task Master AI workflow management.

**Arguments**: $ARGUMENTS

## Quick Commands

Use tab completion to explore: `/tm/` and press Tab to see all available commands.

## Most Common Commands

### Daily Workflow
- `/tm/next` - Get next available task to work on
- `/tm/list` - Show all tasks (add filters: pending, done, blocked, etc.)
- `/tm/show <id>` - View detailed task information
- `/tm/set-status/to-done <id>` - Mark task complete

### Task Management
- `/tm/add-task <description>` - Create new task with AI
- `/tm/expand <id>` - Break task into subtasks
- `/tm/update <id> <changes>` - Update specific task

### Analysis & Planning
- `/tm/analyze-complexity` - Analyze task complexity
- `/tm/complexity-report` - View complexity report

### Project Setup
- `/tm/init` - Initialize Task Master in project
- `/tm/parse-prd` - Generate tasks from PRD
- `/tm/models` - View/configure AI models

## Usage Examples

```bash
/tm/next                              # Find next task
/tm/show 45                          # View task 45 details
/tm/list pending high priority       # Filter tasks
/tm/add-task create login system     # Create new task
/tm/set-status/to-done 45            # Mark task 45 done
/tm/expand 23                        # Expand task 23
```

## Getting Help

- `/tm/help` - Full command reference
- `/tm/learn` - Interactive learning guide

## Command Structure

All commands follow the pattern: `/tm/<command>/<subcommand> [arguments]`

For complete list, type `/tm/` and use tab completion or see `/tm/help`
