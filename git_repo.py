#import base64
import json
from github import Github
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from git import Repo, InvalidGitRepositoryError
import os

from pydantic import BaseModel, Field
from typing import Optional

load_dotenv()

mcp = FastMCP("Git-Repo Agent")
gh = Github(os.getenv("GITHUB_TOKEN"))



# ---- Get Commit ----
class GetCommitParams(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    sha: str = Field(..., description="Commit SHA, branch name, or tag name")


# ---- List Commits ----
class ListCommitsParams(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    sha: Optional[str] = Field(None, description="SHA or Branch name")
    per_page: Optional[int] = Field(30, description="Results per page (default 30, max 100)")
    page: Optional[int] = Field(1, description="Page number (default 1)")


# ---- List Branches ----
class ListBranchesParams(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    per_page: Optional[int] = Field(30, description="Results per page (default 30, max 100)")
    page: Optional[int] = Field(1, description="Page number (default 1)")


# ---- Create or Update File ----
class CreateOrUpdateFileParams(BaseModel):
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    path: str = Field(..., description="Path where to create/update the file")
    content: str = Field(..., description="Content of the file (will be base64-encoded)")
    message: str = Field(..., description="Commit message")
    branch: str = Field(..., description="Branch to create/update the file in")
    sha: Optional[str] = Field(None, description="SHA of file being replaced (for updates)")


# ---- Create Repository ----
class CreateRepositoryParams(BaseModel):
    name: str = Field(..., description="Repository name")
    description: Optional[str] = Field(None, description="Repository description")
    private: Optional[bool] = Field(None, description="Whether repo should be private")
    autoInit: Optional[bool] = Field(None, description="Initialize with README")


# ---- Fork Repository ----
class ForkRepositoryParams(BaseModel):
    owner: str = Field(..., description="Owner of the repository to fork")
    repo: str = Field(..., description="Repository name to fork")
    organization: Optional[str] = Field(None, description="Organization to fork into (optional)")

# ---- Push locally to Github ----
class GitPushLocalTOGIT(BaseModel):
    repo_path: str = Field(..., description="Full local path to the Git repository")
    remote_url: str = Field(..., description="GitHub repository URL to push to")
    branch: str = Field(..., description="Branch to push to (e.g., 'main')")
    commit_msg: Optional[str] = Field(None, description="Optional commit message. If not provided, defaults to 'Update'")


# Tool: Get Commit
@mcp.tool()
def get_commit(params:GetCommitParams):
    owner = params.owner
    repo_name = params.repo
    sha = params.sha
    try:
        repo = gh.get_repo(f"{owner}/{repo_name}")
        commit = repo.get_commit(sha)
        return {"content": [{"type": "text", "text": json.dumps(commit.raw_data)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Tool: List Commits
@mcp.tool()
def list_commits(params:ListCommitsParams):
    owner = params.owner
    repo_name = params.repo
    sha = params.sha
    per_page = params.per_page
    page = params.page
    try:
        repo = gh.get_repo(f"{owner}/{repo_name}")
        commits = repo.get_commits(sha=sha)
        start = (page - 1) * per_page
        end = start + per_page
        commits_list = commits[start:end]
        data = [commit.raw_data for commit in commits_list]
        return {"content": [{"type": "text", "text": json.dumps(data)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Tool: List Branches
@mcp.tool()
def list_branches(params:ListBranchesParams):
    owner = params.owner
    repo_name = params.repo
    per_page = params.per_page
    page = params.page
    try:
        repo = gh.get_repo(f"{owner}/{repo_name}")
        branches = repo.get_branches()
        start = (page - 1) * per_page
        end = start + per_page
        branch_list = branches[start:end]
        data = [branch.raw_data for branch in branch_list]
        return {"content": [{"type": "text", "text": json.dumps(data)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Tool: Create or Update File
@mcp.tool()
def create_or_update_file(params:CreateOrUpdateFileParams):
    owner = params.owner
    repo_name = params.repo
    path = params.path
    content = params.content
    message = params.message
    branch = params.branch
    sha = params.sha
    try:
        repo = gh.get_repo(f"{owner}/{repo_name}")
        #content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        if sha:
            esp = repo.update_file(path, message, content, sha, branch=branch)
            return {"content": [{"type": "text", "text": json.dumps(esp, indent=2)}]}
        else:
            resp = repo.create_file(path, message, content, branch=branch)
            return {"content": [{"type": "text", "text": json.dumps(resp, indent=2)}]}

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


# Tool: Create Repository
@mcp.tool()
async def create_repository(params:CreateRepositoryParams):
    name = params.name
    description = params.description
    is_private = params.private
    auto_init = params.autoInit
    try:
        user = gh.get_user()
        repo = user.create_repo(name, description=description, private=is_private, auto_init=auto_init)
        return {"content": [{"type": "text", "text": json.dumps(repo.raw_data)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}

# Tool: Fork Repository
@mcp.tool()
async def fork_repository(params:ForkRepositoryParams):
    owner = params.owner
    repo_name = params.repo
    organization = params.organization
    try:
        repo = gh.get_repo(f"{owner}/{repo_name}")
        if organization:
            forked = repo.create_fork(organization=organization)
        else:
            forked = repo.create_fork()
        return {"content": [{"type": "text", "text": json.dumps(forked.raw_data)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}]}


@mcp.tool()
def push_to_github(params: GitPushLocalTOGIT):
    repo_path = params.repo_path
    remote_url = params.remote_url
    branch = params.branch or "main"
    commit_msg = params.commit_msg or "Initial commit"

    try:
        # Ensure path exists
        if not os.path.exists(repo_path):
            return {"content": [{"type": "text", "text": "❌ Repo path does not exist."}]}

        # Init repo if not already
        try:
            repo = Repo(repo_path)
            json.dumps("✅ Repo loaded.")
        except InvalidGitRepositoryError:
            repo = Repo.init(repo_path)
            json.dumps("🆕 Repo initialized.")

        # # Create a default README if no files exist
        # if not os.listdir(repo_path):
        #     with open(os.path.join(repo_path, "README.md"), "w") as f:
        #         f.write("# JARVIS-AI\n")

        # Stage all files
        repo.git.add(all=True)

        # Commit if no commits exist
        if not repo.head.is_valid():
            repo.index.commit(commit_msg)
        repo.git.branch("-M", branch)  # Ensure branch is named 'main'

        # Set remote
        if "origin" not in [r.name for r in repo.remotes]:
            origin = repo.create_remote("origin", remote_url)
        else:
            origin = repo.remote("origin")

        # Push with correct refspec
        origin.push(refspec=f"{branch}:{branch}")

        return {
            "content": [{"type": "text", "text": f"✅ Successfully pushed to {remote_url} on branch '{branch}'."}]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}]
        }


if __name__ == "__main__":
    mcp.run()