from git import Repo
import os

from rich.prompt import Prompt

def commit_and_push(commit_message, repo_path, remote_name='origin', branch='main'):
    repo = Repo(repo_path)
    repo.git.add(all=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name=remote_name)
    origin.push(refspec=f"{branch}:{branch}")

commit = Prompt.ask("📝 Enter commit message")
commit_and_push(commit, repo_path=os.getcwd())