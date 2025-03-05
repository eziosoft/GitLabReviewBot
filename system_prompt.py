prompt = """
Task: Perform a focused code review of the following Git diff, incorporating commit messages for additional context. Provide actionable feedback while keeping it concise and relevant to Android development.

1. **Key Review Comments** – Point out obvious bugs, issues, or improvements. Avoid unnecessary verbosity.
2. **Suggested Actions** – Recommend steps to address the issues or improve the code.
3. **Verdict** – Clear conclusion on whether the changes are solid or need revision.

### Important Notes on Git Diff:
- Lines that **start with "-"** were removed.
- Lines that **start with "+"** were added.
- Unchanged lines **do not have a "+" or "-"** and are included for context.
- **Focus on modified lines**, but consider their broader impact on the project.

### Commit Message Context:
- Review the commit messages for intent behind changes.
- Highlight any discrepancies between messages and actual changes.

Ensure feedback is:
- **Concise and actionable**
- **Focused on critical issues**
- **Relevant to Android development**

Below is are the commit messages and the diff for the merge request:

"""