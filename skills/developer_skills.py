"""
skills/developer_skills.py

Module 9: Coding and Developer Assistant
Implements Git & GitHub workflow assistance, project scaffolding,
test runners, and security-oriented code review.
Auto-registered via engine.py.
"""

import os
import re
import subprocess
from datetime import datetime


def git_status(repo_path: str = "") -> str:
    """Checks the Git repository status including branch, modified, and untracked files. Defaults to current workspace."""
    target_dir = repo_path.strip() or os.getcwd()
    try:
        res = subprocess.run(["git", "status", "--short", "--branch"], cwd=target_dir, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return f"Git error: {res.stderr.strip() or 'Not a git repository.'}"
        output = res.stdout.strip()
        if not output:
            return "Git status: Working directory clean, nothing to commit."
        return f"Git status:\n{output}"
    except Exception as e:
        return f"Error checking git status: {e}"


def git_diff_summary(repo_path: str = "") -> str:
    """Provides a concise summary of uncommitted changes and modified lines across files."""
    target_dir = repo_path.strip() or os.getcwd()
    try:
        res = subprocess.run(["git", "diff", "--stat"], cwd=target_dir, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return f"Git error: {res.stderr.strip()}"
        out = res.stdout.strip()
        return f"Git diff summary:\n{out}" if out else "No uncommitted differences found."
    except Exception as e:
        return f"Error running git diff: {e}"


def git_log_recent(repo_path: str = "", count: str = "5") -> str:
    """Shows the recent commit history for the repository. count: number of commits (default 5)."""
    target_dir = repo_path.strip() or os.getcwd()
    n = ''.join(filter(str.isdigit, count)) or '5'
    try:
        res = subprocess.run(["git", "log", f"-n{n}", "--oneline"], cwd=target_dir, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return f"Git error: {res.stderr.strip()}"
        out = res.stdout.strip()
        return f"Recent {n} commits:\n{out}" if out else "No commit history found."
    except Exception as e:
        return f"Error checking git log: {e}"


def git_commit_and_push_assistant(commit_message: str, repo_path: str = "") -> str:
    """Assists in staging changes and creating a Git commit with the provided message."""
    target_dir = repo_path.strip() or os.getcwd()
    msg = commit_message.strip()
    if not msg:
        return "Please provide a valid commit message."
    try:
        # Stage modified files
        add_res = subprocess.run(["git", "add", "-u"], cwd=target_dir, capture_output=True, text=True, timeout=10)
        commit_res = subprocess.run(["git", "commit", "-m", msg], cwd=target_dir, capture_output=True, text=True, timeout=10)
        if commit_res.returncode == 0:
            return f"Git commit successful: '{msg}'. Staged and committed."
        return f"Git commit notice: {commit_res.stdout.strip() or commit_res.stderr.strip()}"
    except Exception as e:
        return f"Error executing git commit: {e}"


def create_project_scaffold(project_type: str, project_name: str, target_dir: str = "") -> str:
    """Generates project scaffolding and standard starter structure. project_type: 'python_cli', 'fastapi', 'flask', or 'html_js'."""
    ptype = project_type.lower().strip()
    pname = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name.strip()) or "my_project"
    base_path = target_dir.strip() or os.path.join(os.getcwd(), pname)

    try:
        os.makedirs(base_path, exist_ok=True)
        if "fastapi" in ptype:
            main_py = os.path.join(base_path, "main.py")
            with open(main_py, "w", encoding="utf-8") as f:
                f.write('from fastapi import FastAPI\n\napp = FastAPI(title="' + pname + '")\n\n@app.get("/")\ndef root():\n    return {"message": "Hello from ' + pname + '"}\n')
            req_txt = os.path.join(base_path, "requirements.txt")
            with open(req_txt, "w", encoding="utf-8") as f:
                f.write("fastapi\nuvicorn\n")
        elif "flask" in ptype:
            app_py = os.path.join(base_path, "app.py")
            with open(app_py, "w", encoding="utf-8") as f:
                f.write('from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Welcome to ' + pname + '"\n\nif __name__ == "__main__":\n    app.run(debug=True)\n')
        elif "html" in ptype or "web" in ptype:
            idx = os.path.join(base_path, "index.html")
            with open(idx, "w", encoding="utf-8") as f:
                f.write(f'<!DOCTYPE html><html><head><title>{pname}</title></head><body><h1>{pname}</h1><p>Created by Maya Assistant.</p></body></html>')
        else: # python_cli
            main_py = os.path.join(base_path, "main.py")
            with open(main_py, "w", encoding="utf-8") as f:
                f.write('def main():\n    print("Welcome to ' + pname + '")\n\nif __name__ == "__main__":\n    main()\n')

        readme = os.path.join(base_path, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(f"# {pname}\n\nProject scaffold generated autonomously by Maya.\n")

        return f"Scaffolded {ptype} project '{pname}' at {base_path}."
    except Exception as e:
        return f"Error creating project scaffold: {e}"


def run_project_tests(test_command: str = "pytest", project_path: str = "") -> str:
    """Runs automated unit tests in the project and summarizes the output. Example: test_command='pytest' or 'python -m unittest'."""
    cwd = project_path.strip() or os.getcwd()
    cmd = test_command.strip() or "pytest"
    try:
        res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=30)
        out = (res.stdout + "\n" + res.stderr).strip()
        status = "PASSED" if res.returncode == 0 else "TEST FAILURES"
        summary = out.splitlines()[-5:] if out else ["No output."]
        return f"Test Run ({status}):\n" + "\n".join(summary)
    except Exception as e:
        return f"Error executing tests: {e}"


def security_code_review(code_or_file_path: str) -> str:
    """Performs a security-oriented code review for credentials, SQL injection, insecure imports, and unsafe eval patterns."""
    text_to_check = ""
    target = code_or_file_path.strip()
    if os.path.exists(target) and os.path.isfile(target):
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            text_to_check = f.read()
    else:
        text_to_check = target

    issues = []
    # Check for hardcoded API keys/passwords
    if re.search(r'(api_key|secret|password|token)\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']', text_to_check, re.IGNORECASE):
        issues.append("⚠️ Potential hardcoded secret or API key detected. Use environment variables.")
    # Check for eval / exec
    if re.search(r'\b(eval|exec)\s*\(', text_to_check):
        issues.append("⚠️ Unsafe dynamic code execution (`eval()` or `exec()`) detected.")
    # Check for raw string formatting in SQL
    if re.search(r'(execute|cursor\.execute)\s*\(\s*f["\']', text_to_check):
        issues.append("⚠️ Potential SQL injection risk: f-string detected in SQL execution. Use parameterized queries.")
    # Shell injection in subprocess
    if re.search(r'subprocess\.(Popen|run|call)\s*\([^,]+,\s*shell\s*=\s*True', text_to_check):
        issues.append("⚠️ `shell=True` detected in subprocess call. Ensure arguments are sanitized.")

    if not issues:
        return "Security Review: No critical security vulnerabilities identified in the inspected code. All primary checks passed."
    return "Security Review Findings:\n" + "\n".join(issues)
