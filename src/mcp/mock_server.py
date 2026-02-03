from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any


_tickets: dict[str, dict[str, Any]] = {}

_SEED_DATA = [
    {
        "id": "PROJ-1",
        "key": "PROJ-1",
        "summary": "Implement user authentication",
        "status": "In Progress",
        "assignee": "gray@example.com",
        "priority": "High",
        "description": "Add OAuth2 login flow with Google and GitHub providers.",
        "labels": ["backend", "security"],
    },
    {
        "id": "PROJ-2",
        "key": "PROJ-2",
        "summary": "Fix dashboard loading speed",
        "status": "Open",
        "assignee": None,
        "priority": "Medium",
        "description": "Dashboard takes 5+ seconds to load. Investigate N+1 queries.",
        "labels": ["performance", "frontend"],
    },
    {
        "id": "PROJ-3",
        "key": "PROJ-3",
        "summary": "Add unit tests for payment module",
        "status": "Done",
        "assignee": "gray@example.com",
        "priority": "Low",
        "description": "Increase test coverage to 80% for payment processing.",
        "labels": ["testing"],
    },
]


def _seed_tickets() -> None:
    for ticket in _SEED_DATA:
        _tickets[ticket["id"]] = ticket.copy()


class TicketCreate(BaseModel):
    summary: str
    description: str | None = None
    priority: str = "Medium"
    assignee: str | None = None
    labels: list[str] = []


class TicketUpdate(BaseModel):
    summary: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    labels: list[str] | None = None


def create_mock_jira_app() -> FastAPI:
    app = FastAPI(
        title="Mock Jira Server",
        description="Fake Jira API for testing",
        version="1.0.0",
    )
    
    @app.on_event("startup")
    async def startup():
        _seed_tickets()
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "mock-jira"}
    
    @app.get("/rest/api/3/issue/{issue_id}")
    async def get_issue(issue_id: str) -> dict[str, Any]:
        if issue_id not in _tickets:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        return _tickets[issue_id]
    
    @app.put("/rest/api/3/issue/{issue_id}")
    async def update_issue(issue_id: str, update: TicketUpdate) -> dict[str, Any]:
        if issue_id not in _tickets:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        
        ticket = _tickets[issue_id]
        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            ticket[key] = value
        return ticket
    
    @app.post("/rest/api/3/issue", status_code=201)
    async def create_issue(create: TicketCreate) -> dict[str, Any]:
        ticket_num = len(_tickets) + 1
        ticket_id = f"PROJ-{ticket_num}"
        ticket = {
            "id": ticket_id,
            "key": ticket_id,
            "summary": create.summary,
            "description": create.description,
            "status": "Open",
            "priority": create.priority,
            "assignee": create.assignee,
            "labels": create.labels,
        }
        _tickets[ticket_id] = ticket
        return ticket
    
    @app.get("/rest/api/3/search")
    async def search_issues(jql: str | None = None, maxResults: int = 50) -> dict[str, Any]:
        results = list(_tickets.values())
        if jql:
            jql_lower = jql.lower()
            if 'status = ' in jql_lower:
                status_match = jql.split('status = ')[1].split(' ')[0].strip('"\'')
                results = [t for t in results if t.get("status", "").lower() == status_match.lower()]
            if 'assignee = ' in jql_lower:
                assignee_match = jql.split('assignee = ')[1].split(' ')[0].strip('"\'')
                results = [t for t in results if t.get("assignee") == assignee_match]
        return {"startAt": 0, "maxResults": maxResults, "total": len(results), "issues": results[:maxResults]}
    
    @app.delete("/rest/api/3/issue/{issue_id}", status_code=204)
    async def delete_issue(issue_id: str):
        if issue_id not in _tickets:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        del _tickets[issue_id]
    
    @app.post("/reset")
    async def reset_data():
        _tickets.clear()
        _seed_tickets()
        return {"status": "reset", "ticket_count": len(_tickets)}
    
    return app


app = create_mock_jira_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.mcp.mock_server:app", host="0.0.0.0", port=8001, reload=True)
