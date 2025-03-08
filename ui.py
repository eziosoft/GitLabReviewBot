import streamlit as st
import json
import re
from get_pr import GitLabMergeRequests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PROJECT_ID = os.getenv("PROJECT_ID")
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:4000/api/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Ensure required environment variables are set
if not ACCESS_TOKEN or not PROJECT_ID or not LLM_API_KEY:
    st.error("ACCESS_TOKEN, PROJECT_ID, and LLM_API_KEY must be set in the .env file")
    st.stop()

# Initialize GitLabMergeRequests instance
gitlab_mr = GitLabMergeRequests(GITLAB_URL, ACCESS_TOKEN, PROJECT_ID, LLM_API_URL, LLM_API_KEY, MODEL_NAME)

st.title("🚀 GitLab Merge Request Review")


def highlight_diff(diff_text):
    """
    Apply color coding to diff text.
    - Lines starting with '-' (deletions) are red
    - Lines starting with '+' (additions) are green
    - Everything else is default
    """
    highlighted_lines = []
    for line in diff_text.split("\n"):
        if line.startswith("-"):
            highlighted_lines.append(f'<span style="color:#FF6B6B;">{line}</span>')  # Red for deletions
        elif line.startswith("+"):
            highlighted_lines.append(f'<span style="color:#4CAF50;">{line}</span>')  # Green for additions
        else:
            highlighted_lines.append(line)

    return "<br>".join(highlighted_lines)


def display_diff(diff_data):
    """Display a formatted Git diff for better readability."""
    for change in diff_data:
        file_path = change.get("new_path", "Unknown File")
        raw_diff = change.get("diff", "")

        # Apply syntax highlighting
        formatted_diff = highlight_diff(raw_diff)

        # Display filename
        st.markdown(f"### 📄 `{file_path}`")

        # Render formatted diff in a box
        st.markdown(
            f'<div style="background-color:#1E1E1E; padding:10px; border-radius:5px; font-family:monospace; overflow-x:auto;">{formatted_diff}</div>',
            unsafe_allow_html=True
        )


# Fetch and display Merge Requests
merge_requests = gitlab_mr.get_merge_requests()

if not merge_requests:
    st.write("❌ No open merge requests found.")
else:
    for mr in merge_requests:
        with st.expander(f"📌 MR {mr['iid']}: {mr['title']} (by {mr['author']['name']})"):
            st.write(f"**State**: {mr['state']}  |  **Created At**: {mr['created_at']}")

            # View Diff Button
            if st.button(f"View Diff - MR {mr['iid']}", key=f"view_{mr['iid']}"):
                diff_data = gitlab_mr.get_merge_request_diff(mr['iid'])
                display_diff(diff_data)

            # Generate Review Button
            if st.button(f"📝 Generate Review - MR {mr['iid']}", key=f"review_{mr['iid']}"):
                diff = gitlab_mr.get_merge_request_diff(mr['iid'])

                if gitlab_mr.was_diff_already_reviewed(diff):
                    review = "✅ Already reviewed."
                else:
                    review = gitlab_mr.send_diff_to_llm(diff, mr['iid'])
                    gitlab_mr.store_reviewed_diff(diff)

                st.text_area("💡 AI Review:", review, height=300)

            # Post Review Button
            if st.button(f"🚀 Post Review - MR {mr['iid']}", key=f"post_{mr['iid']}"):
                review = gitlab_mr.send_diff_to_llm(diff, mr['iid'])  # Ensure review content is available
                gitlab_mr.post_comment_to_gitlab(mr['iid'], review)
                st.success(f"📌 Review posted to MR {mr['iid']}!")
