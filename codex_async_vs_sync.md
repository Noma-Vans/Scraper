# Codex Async vs Sync Modes

This document describes the differences between Codex working in asynchronous (background) mode versus synchronous (interactive) mode.

## Tools and Environment

### Async Mode
- Commands are executed in a non-interactive environment. The agent sends shell commands to the orchestrator and waits for the captured output.
- Each command runs in its own ephemeral container; there is no persistent shell history.
- Typical tools include:
  - `git` for version control (`git status`, `git add`, `git commit`, `git diff`).
  - File system utilities (`ls`, `cat`, `sed`, `grep`, etc.) to read and modify files.
  - Test runners such as `pytest -q` and linters like `ruff` or formatters like `black` when specified in instructions.
  - Packaging or build tools (e.g., `pip`, `npm`) if the repository requires them.
- Resource consumption is controlled by the orchestrator, which limits CPU time and memory per command.
- Because the agent cannot maintain a continuous shell, multi-step operations are broken into individual commands that are executed sequentially by the orchestrator.

### Sync Mode
- The agent interacts with a live shell session, sending commands and seeing outputs immediately.
- Access to the same command-line tools as async mode but with persistent context (current directory, environment variables, shell history).
- User can interrupt or modify the workflow by sending messages between commands, effectively steering the agent in real time.

## Orchestration Layer Differences

- In async mode, the orchestration layer manages queued jobs, executes commands sequentially, and feeds results back to the agent when it wakes for the next step.
- Sync mode maintains an active session where the agent immediately receives command output.
- Error handling in async mode often involves automatic retries or fallback procedures defined by the orchestrator, whereas in sync mode the agent can immediately ask the user for guidance.
- Async jobs are scheduled on shared workers, so the agent may be paused between commands while the worker processes other tasks.
- Sync sessions reserve a worker exclusively for the duration of the conversation, enabling continuous interaction but using more compute time.

## Instructions to the LLM/Agent

- Async mode typically includes instructions to autonomously reach the goal with minimal user interaction, using background compute cycles.
- Sync mode emphasizes interactive steps, following user prompts and waiting for confirmation before long-running or risky actions.
- Example async instructions might include:
  ```
  - Use `git config --global` to set author information.
  - After modifying files, run `pytest -q` and `ruff`.
  - If tests pass, commit with a descriptive message and push a branch.
  - Create a pull request summarizing the changes.
  ```
- Sync instructions often mention asking the user before performing destructive operations and showing intermediate diffs for review.

## User Experience

- Async mode behaves like a background worker: the user submits a request and later receives a pull request or result when the agent finishes. There may be limited opportunities for clarification after the job starts.
- Sync mode is conversational. The user can inspect intermediate outputs, clarify requirements, or stop the agent at any time.
- In async mode the user typically receives a single summary message with a link to the PR, whereas sync sessions provide step-by-step responses and allow dialogue.

## Agent Behavior

- In async mode, the agent handles failures via predefined retries and may proceed without immediate user feedback.
- In sync mode, the agent can pause on errors, explain what happened, and request user input to continue.
- Clarification questions are more common in sync mode because the agent can dialogue with the user.
- Async mode may retry commands automatically if a transient failure occurs (e.g., network hiccups), and the agent reports the final outcome in the PR description.
- Sync mode surfaces errors directly to the chat so the user can suggest remedies or adjust the request.

## Tool Usage and Resource Consumption

- Async execution focuses on efficiency and may batch multiple commands or tests in one run to conserve resources.
- Sync sessions consume resources as the conversation unfolds but give the user finer control over each step.
- Because async jobs are queued, they can run during off-peak hours. Sync sessions require the user and agent to be present simultaneously, so compute must be available in real time.

## Development Tools and Output

- Both modes support code editing, running tests, and creating pull requests, but the workflow differs.
- Async mode usually ends with a single PR summarizing the changes.
- Sync mode allows incremental updates and iterative feedback before finalizing the PR.
- Async PR descriptions often include a checklist of commands run and their outputs, while sync sessions give the user a narrative of what happened step by step.

## Comparison with Other Systems

- ChatGPT or IDE copilots (Cursor, Windsurf) operate synchronously, responding immediately to user input without persistent background execution.
- Codex async mode offers more automation at the cost of interactivity, while sync mode mirrors the conversational style of typical coding assistants.

