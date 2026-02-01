# Atlassian Helper Agent

An AI-powered agent for Jira, Trello, and Confluence management.

## Quick Start

```bash
# Start the development stack
make dev

# Or manually
docker compose up --build
```

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
