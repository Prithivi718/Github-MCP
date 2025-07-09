import json
import os
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from github import Github
from github.GithubException import GithubException
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
load_dotenv()

# Initialize FASTMCP
mcp= FastMCP("Github Agent")
GITHUB_API_KEY= os.getenv("GITHUB_TOKEN")

# Define enums for various options
class PullRequestState(str, Enum):
    open = "open"
    closed = "closed"
    all = "all"

class PullRequestSort(str, Enum):
    created = "created"
    updated = "updated"
    popularity = "popularity"
    long_running = "long-running"

class Direction(str, Enum):
    asc = "asc"
    desc = "desc"

class MergeMethod(str, Enum):
    merge = "merge"
    squash = "squash"
    rebase = "rebase"

# Define input schemas using Pydantic
class GetPullRequestInput(BaseModel):
    owner: str
    repo: str
    pull_number: int

class UpdatePullRequestInput(GetPullRequestInput):
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[PullRequestState] = None
    base: Optional[str] = None
    maintainer_can_modify: Optional[bool] = None

class ListPullRequestsInput(BaseModel):
    owner: str
    repo: str
    state: Optional[PullRequestState] = None
    head: Optional[str] = None
    base: Optional[str] = None
    sort: Optional[PullRequestSort] = None
    direction: Optional[Direction] = None
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class MergePullRequestInput(GetPullRequestInput):
    commit_title: Optional[str] = None
    commit_message: Optional[str] = None
    merge_method: Optional[MergeMethod] = None

class GetPullRequestFilesInput(GetPullRequestInput):
    per_page: Optional[int] = 30
    page: Optional[int] = 1

class UpdatePullRequestBranchInput(GetPullRequestInput):
    expected_head_sha: Optional[str] = None

class CreatePullRequestInput(BaseModel):
    owner: str
    repo: str
    title: str
    body: Optional[str] = None
    head: str
    base: str
    draft: Optional[bool] = False
    maintainer_can_modify: Optional[bool] = True

# --------------------------- Used for Later ------------------------
# Simulated MCP Server
# class McpServer:
#     def __init__(self):
#         self.tools = {}
#
#     def tool(self, name, description, schema_cls, func):
#         self.tools[name] = {
#             "description": description,
#             "schema": schema_cls,
#             "function": func
#         }

# Register tools
# def register_pull_request_tools():
# -----------------------------------------------------------


g = Github(GITHUB_API_KEY)

@mcp.tool()
def get_repo(owner, repo_name):
    """
      🔍 Internal helper tool

      Retrieves a GitHub repository object for a given owner and repository name.

      Parameters:
      - owner (str): GitHub username or organization.
      - repo_name (str): Repository name.

      Returns:
      - Repository object or None if not found.
      """
    try:
        return g.get_user(owner).get_repo(repo_name)
    except GithubException:
        return None


def create_pull_request(data: CreatePullRequestInput):
    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = {
            "title": data.title,
            "body": data.body,
            "head": data.head,
            "base": data.base,
            "draft": data.draft,
            "maintainer_can_modify": data.maintainer_can_modify
        }
        pr_data= {k: v for k,v in pr.items() if v is not None}
        prs= repo.create_pull(**pr_data)
        return prs
        #return {"content": [{"type": "text", "text": json.dumps(pr.raw_data)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def get_pull_request(data: GetPullRequestInput):
    """
       📋 Get Pull Request Details

       Retrieves metadata for a specific pull request in a GitHub repository.

       Parameters:
       - owner (str): Repository owner.
       - repo (str): Repository name.
       - pull_number (int): Pull request number.

       Returns:
       - Raw JSON data of the pull request.
       """

    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = repo.get_pull(data.pull_number)
        return {"content": [{"type": "text", "text": json.dumps(pr.raw_data)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def update_pull_request(data: UpdatePullRequestInput):
    """
        ✏️ Update Pull Request

        Edits the title, body, state, base branch, or modification rights of a pull request.

        Parameters:
        - owner (str): Repository owner.
        - repo (str): Repository name.
        - pull_number (int): Pull request number.
        - title (Optional[str]): New title.
        - body (Optional[str]): New body/description.
        - state (Optional[Literal]): New state ("open" or "closed").
        - base (Optional[str]): Target base branch.
        - maintainer_can_modify (bool): Allow maintainers to edit.

        Returns:
        - Updated pull request metadata.
        """

    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = repo.get_pull(data.pull_number)
        pr.edit(
            title=data.title,
            body=data.body,
            state=data.state.value if data.state else None,
            base=data.base,
            maintainer_can_modify=data.maintainer_can_modify
        )
        return {"content": [{"type": "text", "text": json.dumps(pr.raw_data)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def list_pull_requests(data: ListPullRequestsInput):
    """
        📄 List Pull Requests

        Returns a list of pull requests for the specified repository,
        filtered by state, sort order, and direction.

        Parameters:
        - owner (str): Repository owner.
        - repo (str): Repository name.
        - state (Optional[Literal]): Filter by state (open, closed, all).
        - sort (Optional[Literal]): Sort key (created, updated, etc.).
        - direction (Optional[Literal]): Sort direction (asc, desc).

        Returns:
        - List of pull request metadata.
        """

    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pulls = repo.get_pulls(
            state=data.state.value if data.state else "open",
            sort=data.sort.value if data.sort else "created",
            direction=data.direction.value if data.direction else "desc"
        )
        pr_list = [pr.raw_data for pr in pulls]
        return {"content": [{"type": "text", "text": json.dumps(pr_list)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def merge_pull_request(data: MergePullRequestInput):
    """
        ✅ Merge Pull Request

        Merges a pull request using a specified method (merge, squash, rebase).

        Parameters:
        - owner (str): Repository owner.
        - repo (str): Repository name.
        - pull_number (int): Pull request number.
        - commit_title (Optional[str]): Title of the merge commit.
        - commit_message (Optional[str]): Body of the merge commit.
        - merge_method (Optional[Literal]): Merge method.

        Returns:
        - Merge result data (success, SHA, etc.)
        """

    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = repo.get_pull(data.pull_number)
        merge_result = pr.merge(
            commit_title=data.commit_title,
            commit_message=data.commit_message,
            merge_method=data.merge_method.value if data.merge_method else "merge"
        )
        return {"content": [{"type": "text", "text": json.dumps(merge_result.raw_data)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def get_pull_request_files(data: GetPullRequestFilesInput):
    """
        📂 Get Pull Request Files

        Returns a list of all files changed in a pull request.

        Parameters:
        - owner (str): Repository owner.
        - repo (str): Repository name.
        - pull_number (int): Pull request number.

        Returns:
        - List of file metadata in the pull request.
        """

    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = repo.get_pull(data.pull_number)
        files = pr.get_files()
        file_list = [file.raw_data for file in files]
        return {"content": [{"type": "text", "text": json.dumps(file_list)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

@mcp.tool()
def get_pull_request_status(data: GetPullRequestInput):
    """
        🔄 Get Pull Request Status

        Retrieves the combined commit status of the latest head commit
        for a given pull request (e.g., CI results).

        Parameters:
        - owner (str): Repository owner.
        - repo (str): Repository name.
        - pull_number (int): Pull request number.

        Returns:
        - Combined status of the head commit (pending, success, failure, etc.)
        """
    repo = get_repo(data.owner, data.repo)
    if not repo:
        return {"content": [{"type": "text", "text": "Repository not found."}]}
    try:
        pr = repo.get_pull(data.pull_number)
        sha = pr.head.sha
        combined_status = repo.get_commit(sha).get_combined_status()
        return {"content": [{"type": "text", "text": json.dumps(combined_status.raw_data)}]}
    except GithubException as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

# ---------------------Used for later-----------------------
# def update_pull_request_branch(data: UpdatePullRequestBranchInput):
#     return {"content": [{"type": "text", "text": "Not implemented yet"}]}
#
#
# def get_pull_request_comments(data: GetPullRequestInput):
#     return {"content": [{"type": "text", "text": "Not implemented yet"}]}
# -----------------------------------------------------------


# ---------------------Used for later-----------------------
    # Registering tools
    # mcp.tool("get_pull_request", "Get details of a specific pull request", GetPullRequestInput, get_pull_request)
    # mcp.tool("update_pull_request", "Update an existing pull request", UpdatePullRequestInput, update_pull_request)
    # mcp.tool("list_pull_requests", "List pull requests", ListPullRequestsInput, list_pull_requests)
    # mcp.tool("merge_pull_request", "Merge a pull request", MergePullRequestInput, merge_pull_request)
    # mcp.tool("get_pull_request_files", "Get files changed in a pull request", GetPullRequestFilesInput, get_pull_request_files)
    # mcp.tool("get_pull_request_status", "Get pull request status", GetPullRequestInput, get_pull_request_status)
    # mcp.tool("update_pull_request_branch", "Update pull request branch (not implemented)", UpdatePullRequestBranchInput, update_pull_request_branch)
    # mcp.tool("get_pull_request_comments", "Get pull request comments (not implemented)", GetPullRequestInput, get_pull_request_comments)
    # mcp.tool("create_pull_request", "Create a new pull request", CreatePullRequestInput, create_pull_request)
# -----------------------------------------------------------

if __name__ == "__main__":
    # print("Pull Request Tool Activated! 🤖")
    mcp.run()