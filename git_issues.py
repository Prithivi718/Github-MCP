from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional
from github import Github
from datetime import datetime

from dotenv import load_dotenv
import os
import json

load_dotenv()


mcp = FastMCP("Git-Repo Agent")
g = Github(os.getenv("GITHUB_TOKEN"))

# -------------------- Request Schemas -------------------- #

class IssueParams(BaseModel):
    owner: str
    repo: str
    issue_number: int

class CreateIssueParams(BaseModel):
    owner: str
    repo: str
    title: str
    body: Optional[str] = None
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    milestone: Optional[int] = None

# class UpdateIssueParams(IssueParams):
#     title: Optional[str] = None
#     body: Optional[str] = None
#     state: Optional[str] = Field(None, regex="^(open|closed)$")
#     assignees: Optional[List[str]] = None
#     labels: Optional[List[str]] = None
#     milestone: Optional[int] = None

class CommentParams(IssueParams):
    body: str

class SearchParams(BaseModel):
    q: str
    sort: Optional[str] = None
    order: Optional[str] = None
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class ListIssuesParams(BaseModel):
    owner: str
    repo: str
    state: Optional[str] = "open"
    labels: Optional[List[str]] = None
    sort: Optional[str] = None
    direction: Optional[str] = None
    since: Optional[str] = None
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class CommentsListParams(IssueParams):
    page: Optional[int] = 1
    per_page: Optional[int] = 30

# -------------------- TOOLS -------------------- #

@mcp.tool()
def get_issue(params: IssueParams):
    """Retrieve a GitHub issue."""
    repo = g.get_repo(f"{params.owner}/{params.repo}")
    issue = repo.get_issue(number=params.issue_number)
    return {"content": [{"type": "text", "text": json.dumps(issue.raw_data)}]}

@mcp.tool()
def add_issue_comment(params: CommentParams):
    """Add a comment to a GitHub issue."""
    repo = g.get_repo(f"{params.owner}/{params.repo}")
    issue = repo.get_issue(number=params.issue_number)
    comment = issue.create_comment(params.body)
    return {"content": [{"type": "text", "text": json.dumps(comment.raw_data)}]}

@mcp.tool()
def search_issues(params: SearchParams):
    """Search GitHub issues."""
    results = g.search_issues(query=params.q, sort=params.sort, order=params.order)
    return [issue.raw_data for issue in results.get_page(params.page - 1)]

@mcp.tool()
def create_issue(params: CreateIssueParams):
    """Create a new GitHub issue."""
    repo = g.get_repo(f"{params.owner}/{params.repo}")
    # Build kwargs safely, skipping None values
    issue_data = {
        "title": params.title,
        "body": params.body,
        "assignees": params.assignees,
        "labels": params.labels,
        "milestone": params.milestone
    }

    # Clean up any fields still set to None
    issue_data = {k: v for k, v in issue_data.items() if v is not None}
    issue = repo.create_issue(**issue_data)
    return issue
    #return {"content": [{"type": "text", "text": json.dumps(issue.raw_data)}]}

@mcp.tool()
def list_issues(params: ListIssuesParams):
    """List GitHub issues in a repository."""
    repo = g.get_repo(f"{params.owner}/{params.repo}")
    issue_data = {
        "state": params.state,
        "labels": params.labels,
        "sort":params.sort,
        "direction":params.direction,
        "since" : datetime.fromisoformat(params.since)
    }
    issue_data = {k: v for k, v in issue_data.items() if v is not None}
    issue= repo.get_issues(**issue_data)
    return issue
    # return [issue.raw_data for issue in issues[:params.per_page]]

@mcp.tool()
def get_issue_comments(params: CommentsListParams):
    """Get comments from a GitHub issue."""
    repo = g.get_repo(f"{params.owner}/{params.repo}")
    issue = repo.get_issue(number=params.issue_number)
    comments = issue.get_comments()
    return [comment.raw_data for comment in comments[:params.per_page]]


if __name__ == "__main__":
    mcp.run()


# @app.tool()
# def update_issue(params: UpdateIssueParams):
#     """Update an existing GitHub issue."""
#     repo = g.get_repo(f"{params.owner}/{params.repo}")
#     issue = repo.get_issue(number=params.issue_number)
#     updated_issue = issue.edit(
#         title=params.title,
#         body=params.body,
#         state=params.state,
#         assignees=params.assignees,
#         labels=params.labels,
#         milestone=params.milestone
#     )
#     return updated_issue.raw_data

