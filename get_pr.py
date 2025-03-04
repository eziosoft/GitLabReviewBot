import requests
import os
import argparse
import json
import hashlib
import re
from dotenv import load_dotenv
from system_prompt import prompt
from cachetools import TTLCache
from time import sleep

# Load environment variables from .env file
load_dotenv()

# Cache for storing MR diffs (avoids redundant API calls)
diff_cache = TTLCache(maxsize=100, ttl=300)  # Store up to 100 diffs, expire after 5 minutes


class GitLabMergeRequests:
    def __init__(self, gitlab_url: str, access_token: str, project_id: str, llm_api_url: str, llm_api_key: str,
                 model_name: str):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.access_token = access_token
        self.project_id = project_id
        self.headers = {"Private-Token": self.access_token}
        self.llm_api_url = llm_api_url
        self.llm_api_key = llm_api_key
        self.model_name = model_name

    def get_merge_requests(self, state: str = None, per_page: int = 20, page: int = 1):
        """Fetch a list of merge requests with optional state filtering."""
        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/merge_requests?state=opened"
        params = {"per_page": per_page, "page": page}
        if state:
            params["state"] = state
        return self._make_request("GET", url, params=params)

    def get_merge_request_diff(self, merge_request_iid: int):
        """Fetch the diff of a specific merge request using its IID."""
        if merge_request_iid in diff_cache:
            return diff_cache[merge_request_iid]  # Return cached result

        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/merge_requests/{merge_request_iid}/changes"
        diff = self._make_request("GET", url).get("changes", [])
        diff_cache[merge_request_iid] = diff  # Store in cache
        return diff

    def send_diff_to_llm(self, diff: list, merge_request_iid: int):
        """Send the diff and commit messages to an LLM API for code review."""
        commit_messages = self.get_merge_request_commits(merge_request_iid)
        commit_context = "\n".join(commit_messages)

        diff_chunks = split_diff_by_files(diff)

        reviews = []
        for chunk in diff_chunks:
            messages = [
                {"role": "system",
                 "content": f"{prompt}"},
                {"role": "user", "content": f"Commit Messages:\n{commit_context}\n\nDiff:\n```diff\n{chunk}\n```"}
            ]
            payload = {"model": self.model_name, "messages": messages}
            headers = {"Authorization": f"Bearer {self.llm_api_key}", "Content-Type": "application/json"}

            response = self._make_request("POST", self.llm_api_url, json=payload, headers=headers)
            reviews.append(safe_extract_llm_response(response))

        return "\n\n".join(reviews)

    def post_comment_to_gitlab(self, mr_iid: int, comment: str):
        """Post the LLM review to GitLab as a comment on the merge request."""
        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": f"🤖 AI Review:\n{comment}"}
        return self._make_request("POST", url, json=data)

    def get_merge_request_commits(self, merge_request_iid: int):
        """Fetch the commit messages for a specific merge request."""
        url = f"{self.gitlab_url}/api/v4/projects/{self.project_id}/merge_requests/{merge_request_iid}/commits"
        commits = self._make_request("GET", url)
        return [commit["message"] for commit in commits]  # Extract commit messages

    def _make_request(self, method, url, **kwargs):
        """Handle API requests with retries for rate limits."""
        headers = {**self.headers, **kwargs.get("headers", {})}  # Merge headers
        kwargs.pop("headers", None)  # Remove redundant key

        for _ in range(3):  # Retry up to 3 times
            response = requests.request(method, url, headers=headers, **kwargs)
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                sleep(5)
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")

        raise Exception("API request failed after retries.")


def split_diff_by_files(diff):
    """Splits diff into separate file changes."""
    file_diffs = []
    current_diff = []

    for change in diff:
        file_diffs.append(f"File: {change['new_path']}\n{change['diff']}")

    return file_diffs


def safe_extract_llm_response(response):
    """Safely extracts and validates LLM response."""
    try:
        content = response.get('choices', [{}])[0].get('message', {}).get('content', "").strip()
        return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL) or "⚠️ No valid response received."
    except Exception as e:
        return f"⚠️ Error processing LLM response: {str(e)}"


def get_diff_hash(diff):
    """Generate a hash of the diff for change tracking."""
    return hashlib.sha256(diff.encode()).hexdigest()


def was_diff_already_reviewed(diff):
    """Check if this diff was already reviewed by comparing hashes."""
    try:
        with open(".ai_review_cache.json", "r") as f:
            cache = json.load(f)
            return get_diff_hash(diff) in cache
    except FileNotFoundError:
        return False


def store_reviewed_diff(diff):
    """Store reviewed diff hashes to avoid duplicate reviews."""
    hash_value = get_diff_hash(diff)
    try:
        with open(".ai_review_cache.json", "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    cache[hash_value] = True
    with open(".ai_review_cache.json", "w") as f:
        json.dump(cache, f)


if __name__ == "__main__":
    GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    PROJECT_ID = os.getenv("PROJECT_ID")
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:4000/api/chat/completions")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME")

    if not ACCESS_TOKEN or not PROJECT_ID or not LLM_API_KEY:
        raise ValueError("ACCESS_TOKEN, PROJECT_ID, and LLM_API_KEY must be set in the .env file")

    gitlab_mr = GitLabMergeRequests(GITLAB_URL, ACCESS_TOKEN, PROJECT_ID, LLM_API_URL, LLM_API_KEY, MODEL_NAME)

    parser = argparse.ArgumentParser(description="GitLab Merge Request CLI Tool")
    parser.add_argument("command", choices=["list", "get-diff", "review-diff", "post-review"],
                        help="Command to execute")
    parser.add_argument("--mr-id", type=int, help="Merge request ID for fetching diff or posting review")
    parser.add_argument("--output", choices=["text", "json", "markdown"], default="text", help="Output format")
    args = parser.parse_args()

    if args.command == "list":
        merge_requests = gitlab_mr.get_merge_requests()
        for mr in merge_requests:
            print(f"IID: {mr['iid']}, Title: {mr['title']}, State: {mr['state']}, Author: {mr['author']['name']}")

    elif args.command == "get-diff":
        if not args.mr_id:
            print("Error: --mr-id is required for 'get-diff' command.")
        else:
            diff = gitlab_mr.get_merge_request_diff(args.mr_id)
            print(f"Diff for MR {args.mr_id}:\n" + json.dumps(diff, indent=2) if args.output == "json" else diff)

    elif args.command == "review-diff":
        if not args.mr_id:
            print("Error: --mr-id is required for 'review-diff' command.")
        else:
            diff = gitlab_mr.get_merge_request_diff(args.mr_id)
            review = gitlab_mr.send_diff_to_llm(diff, args.mr_id) if not was_diff_already_reviewed(
                diff) else "✅ Already reviewed."
            store_reviewed_diff(diff)
            print(f"LLM Review for MR {args.mr_id}:\n" + review)

    elif args.command == "post-review":
        if not args.mr_id:
            print("Error: --mr-id is required for 'post-review' command.")
        else:
            diff = gitlab_mr.get_merge_request_diff(args.mr_id)
            review = gitlab_mr.send_diff_to_llm(diff, args.mr_id)
            gitlab_mr.post_comment_to_gitlab(args.mr_id, review)
            print(f"📌 Review posted to MR {args.mr_id}!")
