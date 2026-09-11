# Requirements Map

| Requirement | Location |
|---|---|
| Full-stack Django + HTML/CSS/JS | `config/`, `templates/`, `static/` |
| PostgreSQL | `config/settings.py` |
| MVT | Django apps + templates |
| Authentication | `accounts/` |
| RBAC | `accounts/models.py` Profile.role |
| 3NF + relations | `courses/models.py`, `tasks/models.py` |
| Context-aware chatbot | `chat/models.py`, `chat/views.py`, agent receives authenticated user |
| Agentic workflow | `chat/agent.py` |
| Python tools | `chat/tools.py` |
| Permission checks | `delete_task()` scopes by authenticated owner |
| Validation | `add_task()` and Django forms |
| Explicit delete confirmation | `delete_task(... confirmed=False)` |
| Prompt/persona documentation | `chat/agent.py`, `docs/` |
| Git/GitHub strategy | `docs/GIT_STRATEGY.md` |
| SRS | `docs/SRS_OUTLINE.md` |

The exact training file requires the AI Agent to execute real functions/tools, not just answer questions, and requires validation, authorization, and explicit confirmation before deletion or financial operations.
