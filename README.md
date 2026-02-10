# Atlassian Helper Agent

An AI-powered agent for Jira, Trello, and Confluence management.

## Quick Start

[User Manual](USER_MANUAL.md) | [Architecture](technical-details.md) | [Changelog](.gemini/antigravity/brain/bde097b5-98fd-4818-9228-6b3a9be0f302/changelog.md)

## Quick Start

1.  **Start the app**:
    ```bash
    make dev
    ```
2.  **Open UI**: [http://localhost:8081](http://localhost:8081)
3.  **Connect**: Click "Connect to Atlassian" in the chat.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Container health check |
| `GET /docs` | Swagger UI documentation |
| `POST /agent/run` | Invoke the agent (Phase 3) |

## Architecture

- **Supervisor Pattern**: Router → Subgraphs for extensibility
- **Dynamic Model Selection**: Runtime LLM configuration
- **MCP Integration**: Model Context Protocol for tool connectivity

## Development

```bash
make test    # Run tests
make lint    # Run linters
make format  # Auto-format code
```

---

## Copyright

© 2026 Gray. All Rights Reserved.

This software is proprietary and confidential. No license is granted for redistribution, modification, or commercial use without explicit written permission from the copyright holder.
