import httpx
import base64
from typing import List, Dict, Any, Optional
from github import Github
import git

from core.config import get_settings

class GitHubService:
    def __init__(self):
        self.settings = get_settings()
        self.github = Github(self.settings.github_token)

    async def get_pr_details(
        self,
        repo_full_name: str,
        pr_number: int,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get pull request details."""
        token = access_token or self.settings.github_token
        github_client = Github(token)

        try:
            repo = github_client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha
                },
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha
                },
                "user": {
                    "login": pr.user.login
                },
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to get PR details: {str(e)}")

    async def get_pr_changed_files(
        self,
        repo_full_name: str,
        pr_number: int,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of changed files in a pull request."""
        token = access_token or self.settings.github_token
        github_client = Github(token)

        try:
            repo = github_client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            changed_files = []
            for file in pr.get_files():
                file_data = {
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed, renamed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') else None
                }

                # Get file content if it's a text file
                if file.status != "removed":
                    try:
                        file_content = repo.get_contents(file.filename, ref=pr.head.sha)
                        if file_content.encoding == "base64":
                            content = base64.b64decode(file_content.content).decode('utf-8')
                            file_data["content"] = content
                    except Exception:
                        # File might be binary or too large
                        file_data["content"] = None

                changed_files.append(file_data)

            return changed_files
        except Exception as e:
            raise Exception(f"Failed to get changed files: {str(e)}")

    async def post_pr_review(
        self,
        repo_full_name: str,
        pr_number: int,
        analysis_result: Dict[str, Any],
        access_token: Optional[str] = None
    ):
        """Post review comments on a pull request."""
        token = access_token or self.settings.github_token
        github_client = Github(token)

        try:
            repo = github_client.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)

            # Create main review comment
            review_body = self._format_review_body(analysis_result)

            # Post review with comments
            review = pr.create_review(
                body=review_body,
                event="COMMENT"  # Can be "APPROVE", "REQUEST_CHANGES", or "COMMENT"
            )

            # Post inline comments for specific suggestions
            if "file_suggestions" in analysis_result:
                for file_suggestion in analysis_result["file_suggestions"]:
                    filename = file_suggestion.get("filename")
                    suggestions = file_suggestion.get("suggestions", [])

                    for suggestion in suggestions:
                        try:
                            pr.create_review_comment(
                                body=suggestion.get("message", ""),
                                commit=pr.get_commits().reversed[0],
                                path=filename,
                                line=suggestion.get("line_number", 1)
                            )
                        except Exception as e:
                            # Skip if unable to post inline comment
                            print(f"Failed to post inline comment: {e}")

            return review

        except Exception as e:
            raise Exception(f"Failed to post review: {str(e)}")

    def _format_review_body(self, analysis_result: Dict[str, Any]) -> str:
        """Format the analysis result into a review comment."""
        body = "## 🤖 AI Code Review\n\n"

        if "summary" in analysis_result:
            body += f"**Summary:** {analysis_result['summary']}\n\n"

        if "overall_score" in analysis_result:
            score = analysis_result["overall_score"]
            body += f"**Overall Quality Score:** {score}/10\n\n"

        if "suggestions" in analysis_result and analysis_result["suggestions"]:
            body += "### 📋 General Suggestions:\n"
            for suggestion in analysis_result["suggestions"]:
                body += f"- {suggestion}\n"
            body += "\n"

        if "security_issues" in analysis_result and analysis_result["security_issues"]:
            body += "### 🔒 Security Considerations:\n"
            for issue in analysis_result["security_issues"]:
                body += f"- ⚠️ {issue}\n"
            body += "\n"

        if "test_suggestions" in analysis_result and analysis_result["test_suggestions"]:
            body += "### 🧪 Test Suggestions:\n"
            for test in analysis_result["test_suggestions"]:
                body += f"- {test}\n"
            body += "\n"

        body += "---\n*Generated by AI Code Review Assistant*"

        return body

    async def get_file_content(
        self,
        repo_full_name: str,
        file_path: str,
        ref: str = "main"
    ) -> str:
        """Get content of a specific file from repository."""
        try:
            repo = self.github.get_repo(repo_full_name)
            file_content = repo.get_contents(file_path, ref=ref)

            if file_content.encoding == "base64":
                return base64.b64decode(file_content.content).decode('utf-8')
            else:
                return file_content.content

        except Exception as e:
            raise Exception(f"Failed to get file content: {str(e)}")