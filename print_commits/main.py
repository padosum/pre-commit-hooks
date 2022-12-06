import sys
import re
import datetime
import requests
from functools import reduce


def commits_by_repo(acc, cur):
    repo = cur["repo"]["name"]
    if repo not in acc:
        acc[repo] = []
    acc[repo].append(*cur["payload"]["commits"])
    return acc


def get_today_commits(username, title):
    today_commits = []
    today_commits.append(title)
    url = f"https://api.github.com/users/{username}/events"
    response = requests.get(url)

    if response.status_code == 200:
        github_activity = response.json()
        push_events = list(filter(lambda d: d["type"] == "PushEvent", github_activity))
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_activity = list(filter(lambda d: d["created_at"].split("T")[0] == today, push_events))

        repos = reduce(commits_by_repo, today_activity, {})

        for repo in repos.keys():
            commits_count = len(repos[repo])
            today_commits.append(f"- [{repo}](https://github.com/{repo}) {commits_count} commits")
            for commit in repos[repo]:
                sha = commit["sha"]
                message = commit["message"].split("\n")[0]
                today_commits.append(f"  - [{message}](https://github.com/{repo}/commit/{sha})")

    return "\n".join(today_commits)


def get_doc(file):
    with open(file) as f:
        return f.read()


def save_doc(file, contents):
    with open(file, "w") as f:
        return f.write(contents)


def insert_log(username, title, path):
    contents = get_doc(path)
    if "<!-- commit -->" not in contents:
        return None
    if "<!-- commitstop -->" not in contents:
        return "<!-- commitstop --> Not Found"

    commits = ["<!-- commit -->", get_today_commits(username, title), "<!-- commitstop -->"]
    regex = "<!-- commit -->.*?<!-- commitstop -->"
    updated_contents = re.sub(regex, "\n".join(commits), contents, flags=re.S)

    if updated_contents != contents:
        save_doc(path, updated_contents)

    return None


def main():
    [_, username, title, *paths] = sys.argv

    exit_code = 0

    for path in paths:
        if not path.endswith(".md"):
            continue
        msg = insert_log(username, title, path)
        if msg:
            exit_code = 1
            print(f"{msg}: {path}")

    return exit_code


if __name__ == "__main__":
    main()
