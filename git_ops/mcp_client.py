from github import Github
from config import Config
import logging
import datetime

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.github_token = Config.GITHUB_TOKEN
        self.repo_name = Config.GITHUB_REPO
        self.g = Github(self.github_token) if self.github_token else None

    def create_migration_pr(self, suggestions):
        if not self.g:
            logger.warning("No GitHub token provided. Skipping PR creation. Suggestions:")
            for s in suggestions:
                logger.warning(s)
            return

        if not suggestions:
            logger.info("No migrations to create.")
            return
            
        try:
            repo = self.g.get_repo(self.repo_name)
            base_branch = repo.default_branch
            sb = repo.get_branch(base_branch)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_branch_name = f"dbre-optimization-{timestamp}"
            
            repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=sb.commit.sha)
            
            migration_content = "-- Automated DBRE Migration\n\n"
            migration_content += "\n".join(suggestions)
            
            file_path = f"migrations/V{timestamp}__dbre_optimization.sql"
            commit_message = f"chore(db): Add automated optimizations from DBRE"
            
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=migration_content,
                branch=new_branch_name
            )
            
            pr_title = f"Database Performance Optimizations - {timestamp}"
            pr_body = (
                "## OmniQuery DBRE Automated Migration\n\n"
                "The following optimizations have been suggested based on live telemetry:\n"
                "```sql\n"
                f"{migration_content}\n"
                "```\n\n"
                "Please review before merging. Do not apply directly to production without testing."
            )
            
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=new_branch_name,
                base=base_branch
            )
            logger.info(f"Successfully created PR: {pr.html_url}")
            
        except Exception as e:
            logger.error(f"Error creating GitHub PR: {e}")
