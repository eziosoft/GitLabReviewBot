# GitLabReviewBot

A bot for reviewing GitLab merge requests by analyzing code changes and providing feedback.

## Features
- Retrieves merge requests from GitLab
- Analyzes code changes using custom logic
- Provides automated review comments

## Key Files
- `get_pr.py`: Main script for handling merge request processing
- `system_prompt.py`: Contains the AI review prompt template

## Setup
```bash
git clone https://github.com/eziosoft/GitLabReviewBot.git
```

## Configuration
Set environment variables for GitLab access:
```python
GITLAB_TOKEN = "your_token_here"
PROJECT_ID = "your_project_id"
```

## Usage
Run the bot with:
```python
python3 get_pr.py
```