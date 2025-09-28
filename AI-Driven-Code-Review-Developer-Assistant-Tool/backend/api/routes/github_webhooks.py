from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import hashlib
import hmac
import json
from typing import Dict, Any

from core.config import get_settings
from services.github_service import GitHubService
from services.code_analysis_service import CodeAnalysisService

router = APIRouter()

@router.post("/github")
async def handle_github_webhook(
    request: Request,
    github_service: GitHubService = Depends(),
    analysis_service: CodeAnalysisService = Depends()
):
    """Handle GitHub webhook events for pull requests."""
    settings = get_settings()

    # Verify webhook signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()

    if not verify_github_signature(body, signature, settings.github_webhook_secret):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "pull_request":
        return await handle_pull_request_event(payload, github_service, analysis_service)
    elif event_type == "push":
        return await handle_push_event(payload, github_service, analysis_service)

    return JSONResponse(content={"message": "Event received but not processed"})

async def handle_pull_request_event(
    payload: Dict[str, Any],
    github_service: GitHubService,
    analysis_service: CodeAnalysisService
):
    """Process pull request events."""
    action = payload.get("action")

    if action in ["opened", "synchronize", "reopened"]:
        pr_data = payload["pull_request"]
        repo_data = payload["repository"]

        # Extract PR information
        pr_number = pr_data["number"]
        repo_full_name = repo_data["full_name"]
        base_sha = pr_data["base"]["sha"]
        head_sha = pr_data["head"]["sha"]

        # Get changed files
        changed_files = await github_service.get_pr_changed_files(
            repo_full_name, pr_number
        )

        # Analyze the changes
        analysis_result = await analysis_service.analyze_pr_changes(
            repo_full_name, base_sha, head_sha, changed_files
        )

        # Post review comments
        await github_service.post_pr_review(
            repo_full_name, pr_number, analysis_result
        )

        return JSONResponse(content={
            "message": "PR analysis completed",
            "pr_number": pr_number,
            "files_analyzed": len(changed_files)
        })

    return JSONResponse(content={"message": "PR action not processed"})

async def handle_push_event(
    payload: Dict[str, Any],
    github_service: GitHubService,
    analysis_service: CodeAnalysisService
):
    """Process push events."""
    # For now, just acknowledge the push
    return JSONResponse(content={"message": "Push event received"})

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not secret:
        return True  # Skip verification if no secret is configured

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)