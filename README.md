# GitLabReviewBot

A bot for reviewing GitLab merge requests by analyzing code changes and providing feedback.

## Features  
- **Automated Code Review** – AI analyzes diffs and offers structured feedback.  
- **Commit-Aware Analysis** – Uses commit messages to improve review accuracy.  
- **Clear & Actionable Insights** – Short, focused suggestions on improvements.  
- **GitLab Integration** – Fetches MRs and posts reviews as comments.  
- **Caching & Rate Limiting** – Optimized to reduce redundant API calls. 

## Key Files
- `get_pr.py`: Main script for handling merge request processing
- `system_prompt.py`: Contains the AI review prompt template

## Setup
```bash
git clone https://github.com/eziosoft/GitLabReviewBot.git
```

## Install dependencies
```bash
pip install -r requirements.txt
```

## Configuration
Set environment variables for GitLab access:
```python
GITLAB_URL=https://gitlab.com
ACCESS_TOKEN=your_gitlab_access_token
PROJECT_ID=your_project_id
LLM_API_URL=http://localhost:4000/api/chat/completions
LLM_API_KEY=your_llm_api_key
MODEL_NAME=your_model_name

```

## Usage
Run the bot with:
```python
python main.py list
python main.py get-diff --mr-id 123
python main.py review-diff --mr-id 123
python main.py post-review --mr-id 123
```

## How It Works
1. Fetches the latest open merge requests from GitLab.
2. Retrieves the diff and commit messages for context.
3. Sends the diff to an AI model for structured review.
4. Outputs the review or posts it as a comment on GitLab.