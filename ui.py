from flask import Flask, render_template, request, jsonify
from get_pr import GitLabMergeRequests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PROJECT_ID = os.getenv("PROJECT_ID")
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:4000/api/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

if not ACCESS_TOKEN or not PROJECT_ID or not LLM_API_KEY:
    raise ValueError("ACCESS_TOKEN, PROJECT_ID, and LLM_API_KEY must be set in the .env file")

# Initialize GitLabMergeRequests
gitlab_mr = GitLabMergeRequests(GITLAB_URL, ACCESS_TOKEN, PROJECT_ID, LLM_API_URL, LLM_API_KEY, MODEL_NAME)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge_requests', methods=['GET'])
def list_merge_requests():
    merge_requests = gitlab_mr.get_merge_requests()
    return jsonify(merge_requests)

@app.route('/merge_request/<int:mr_id>/diff', methods=['GET'])
def get_merge_request_diff(mr_id):
    diff = gitlab_mr.get_merge_request_diff(mr_id)
    return jsonify(diff)

@app.route('/merge_request/<int:mr_id>/review', methods=['POST'])
def review_merge_request(mr_id):
    diff = gitlab_mr.get_merge_request_diff(mr_id)
    if gitlab_mr.was_diff_already_reviewed(diff):
        return jsonify({"review": "✅ Already reviewed."})
    review = gitlab_mr.send_diff_to_llm(diff, mr_id)
    # gitlab_mr.store_reviewed_diff(diff)
    return jsonify({"review": review})

@app.route('/merge_request/<int:mr_id>/post_review', methods=['POST'])
def post_review(mr_id):
    diff = gitlab_mr.get_merge_request_diff(mr_id)
    review = gitlab_mr.send_diff_to_llm(diff, mr_id)
    gitlab_mr.post_comment_to_gitlab(mr_id, review)
    return jsonify({"message": f"📌 Review posted to MR {mr_id}!"})

if __name__ == '__main__':
    app.run(debug=True)
