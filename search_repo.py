from pydantic import BaseModel
from github import Github, GithubException
from typing import Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import os

load_dotenv()

mcp = FastMCP("Search Git-Repo Agent")

# Replace 'your_token_here' with your actual GitHub token or leave blank for unauthenticated (limited)
g = Github(os.getenv("GITHUB_TOKEN"))

class SearchReposParams(BaseModel):
    q: str
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class SearchCodeParams(BaseModel):
    q: str
    sort: Optional[str] = None  # 'indexed' only
    order: Optional[str] = None  # 'asc' or 'desc'
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class SearchUsersParams(BaseModel):
    q: str
    sort: Optional[str] = None  # 'followers', 'repositories', or 'joined'
    order: Optional[str] = None  # 'asc' or 'desc'
    per_page: Optional[int] = 30
    page: Optional[int] = 1


@mcp.tool()
def search_repositories(params: SearchReposParams):
    try:
        result = g.search_repositories(query=params.q)
        # Pagination
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        items = result[start:end]

        repos = []
        for repo in items:
            repos.append({
                "name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "language": repo.language,
            })

        return {"total_count": result.totalCount, "repositories": repos}
    except GithubException as e:
        return {"error": str(e)}


# Tool: Search Code
@mcp.tool()
def search_code(params:SearchCodeParams):
    try:
        # PyGithub search_code does not support sort or order params directly
        # So we only do query and pagination here
        result = g.search_code(query=params.q)
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        items = result[start:end]

        codes = []
        for code in items:
            codes.append({
                "name": code.name,
                "path": code.path,
                "repository": code.repository.full_name,
                "html_url": code.html_url,
            })

        return {"total_count": result.totalCount, "code_results": codes}
    except GithubException as e:
        return {"error": str(e)}


@mcp.tool()
def search_users(params: SearchUsersParams):
    try:
        result = g.search_users(query=params.q)
        start = (params.page - 1) * params.per_page
        end = start + params.per_page
        items = result[start:end]

        users = []
        for user in items:
            users.append({
                "login": user.login,
                "html_url": user.html_url,
                "type": user.type,
                "score": user.score,
            })

        return {"total_count": result.totalCount, "users": users}
    except GithubException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()