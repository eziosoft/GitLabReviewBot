prompt = """
Task: Perform a concise yet insightful code review of the following Git diff, incorporating commit messages for additional context. Your review should be structured as follows:

1. **Summary of Changes** – Briefly describe what was modified in the code, referencing relevant commit messages.
2. **Key Review Comments** – Highlight the most important improvements and concerns, avoiding unnecessary verbosity.
3. **Suggested Actions** – Recommend practical steps to refine the changes if needed.
4. **Verdict** – A short, clear conclusion on whether the changes are solid or need revision.

### Important Notes on Git Diff:
- Lines that **start with "-"** were removed from the code.
- Lines that **start with "+"** were added to the code.
- Unchanged lines **do not have a "+" or "-"** and are included for context.
- **Focus only on the modified lines**, but consider their broader impact.

### Commit Message Context:
- Review the provided commit messages to understand the intent behind the changes.
- If discrepancies exist between the commit messages and the code changes, highlight them.

Ensure your feedback is:
- **Concise but meaningful**
- **Focused on the most critical aspects**
- **Actionable and constructive**

Here is the Git diff:
"""