#!/usr/bin/env python3

# Modules
import argparse
import re
import os
import subprocess
import requests
# See https://gitpython.readthedocs.io/en/stable/tutorial.html
from git import Repo
from github_action_utils import set_output
from github import Github
from github import Auth


# Global variables
GitHubRepository = ''
GitHubToken = ''
GitHubLabels = []
CommitType = ''

def parse_args():
    # Arguments
    parser = argparse.ArgumentParser(description='Match Git commits based on matching commit message')
    parser.add_argument('--path', type=str, help='Path to the Git repository')
    parser.add_argument('--start_tag_pattern', type=str, help='Start tag pattern')
    parser.add_argument('--end_tag_pattern', type=str, help='End tag pattern')
    parser.add_argument('--commit_message_pattern', type=str, help='Commit message pattern')
    parser.add_argument('--commit_type', type=str, help='Commit type')
    parser.add_argument('--github_labels', type=str, help='GitHub labels to match')
    parser.add_argument('--github_repository', type=str, help='GitHub repository')
    parser.add_argument('--github_token', type=str, help='GitHub token')
    parser.add_argument('--release_notes_file', type=str, help='Release notes file')
    parser.add_argument('--verbose', action="store_true", help='Verbose output')
    args = parser.parse_args()
    return args

def split_commits(text):
    commits = text.split("commit ")
    commits = commits[1:]
    _commits = []
    for commit in commits:
        _commits.append("commit " + commit)
    return _commits

def get_github_labels(commit_sha):
    global GitHubRepository
    global GitHubToken
    labels = []

    # Construct the API URL
    url = "https://api.github.com/repos/{0}/commits/{1}/pulls".format(GitHubRepository, commit_sha)

    # Set the headers with the access token
    headers = {
        'Authorization': 'Bearer {0}'.format(GitHubToken),
        'Accept': 'application/vnd.github.v3+json'
    }

    # Send a GET request to the API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the labels from the response
        _json = response.json()
        if _json and len(_json) > 0:
            _labels = response.json()[0]['labels']
            for label in _labels:
                labels.append(label['name'])
            return labels
        else:
            return []
    else:
        # Handle the error case
        print(f'Error: {response.status_code}')
        return []

def get_matching_commits(commits, commit_message_pattern):
    global GitHubLabels
    hotfix_commits = []
    for commit in commits:
        if commit.type != 'commit': # Only process commits
            continue
        if (CommitType in ['merge']) and (commit.parents and len(commit.parents) < 2): # Merge commits
            continue
        if re.search(commit_message_pattern, commit.message, re.IGNORECASE):
            hotfix_commits.append(commit)
        elif GitHubToken != '': # Check GitHub labels
            github_labels = get_github_labels(commit.hexsha)
            for label in GitHubLabels:
                if label in github_labels:
                    hotfix_commits.append(commit)
                    continue
    return hotfix_commits

def get_merge_commits(repo, commitSHA):
    merge_commits = []
    commits = list(repo.iter_commits(max_count=100))
    for commit in commits:
        if commitSHA == commit.hexsha:
            break
        else:
            merge_commits.append(commit)
    return merge_commits

def get_commitSHA_for_tag(repo, tag_name):
    commitSHA = repo.tags[tag_name].commit.hexsha
    return commitSHA

def get_pr_commit_range(pull_request):
    commit = ''
    commit_range = ''
    lines = pull_request.split('\n')
    pr_commit_range = {}
    for line in lines:
        if line.startswith("commit "):
            commit = line.split(' ')[1]
        if line.startswith("Merge:"):
            commit_range = line.split('Merge: ')[1]
    pr_commit_range[commit] = {}
    start = commit_range.split(' ')[0]
    end = commit_range.split(' ')[1]
    pr_commit_range[commit]['start'] = start
    pr_commit_range[commit]['end'] = end
    return pr_commit_range

def get_pr_commit_ranges(pull_requests):
    pr_commit_ranges = {}
    for pull_request in pull_requests:
        pr_commit_range = get_pr_commit_range(pull_request)
        pr_commit_ranges[pr_commit_range] = None
    return pr_commit_ranges

def extract_merge_values(string):
    merge_index = string.find('Merge:') + len('Merge:')
    merge_values = string[merge_index:].split()[:2]
    return merge_values

def extract_commit_value(string):
    commit_index = string.find('commit ') + len('commit ')
    commit_value = string[commit_index:].split()[0]
    return commit_value

def get_pr_release_note(commit_sha):
    global GitHubRepository
    global GitHubToken

    # Construct the API URL
    url = "https://api.github.com/repos/{0}/commits/{1}/pulls".format(GitHubRepository, commit_sha)

    # Set the headers with the access token
    headers = {
        'Authorization': 'Bearer {0}'.format(GitHubToken),
        'Accept': 'application/vnd.github.v3+json'
    }

    # Send a GET request to the API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the labels from the response
        _json = response.json()
        if _json and len(_json) > 0:
            _title = response.json()[0]['title']
            _user = response.json()[0]['user']['login']
            _url = response.json()[0]['url']
            release_note = f"* {_title} by {_user} in {_url}"
            return release_note
        else:
            return ''
    else:
        # Handle the error case
        print(f'Error: {response.status_code}')
        return ''

def get_pr_release_notes(commits):
    pr_release_notes = []
    for commit in commits:
        release_note = get_pr_release_note(commit.hexsha)
        if release_note not in pr_release_notes:
            pr_release_notes.append(release_note)
    return pr_release_notes

def main():
    # Global variables
    global GitHubRepository
    global GitHubToken
    global GitHubLabels
    global CommitType
    Default = {
        'path': '.',
        'start_tag_pattern': 'v[0-9]+.[0-9]+.[0-9]+',
        'end_tag_pattern': 'HEAD',
        'commit_message_pattern': '.*',
        'commit_type': 'merge',
        'github_labels': [],
        'github_repository': '',
        'github_token': '',
        'release_notes_file': '',
        'verbose': False,
        'auth': None
    }

    # Get arguments
    args = parse_args()

	# Global variables
    Global = Default    # Set Global to Default values
    StartTagPattern = args.start_tag_pattern if (args.start_tag_pattern != None) else Default['start_tag_pattern']
    EndTagPattern = args.end_tag_pattern if (args.end_tag_pattern != None) else Default['end_tag_pattern']
    CommitMessagePattern = args.commit_message_pattern if (args.commit_message_pattern != None) else Default['commit_message_pattern']
    CommitType = args.commit_type if (args.commit_type != None) else Default['commit_type']
    GitHubLabels = args.github_labels.split(',') if (args.github_labels != None) else Default['github_labels']
    RepoPath = args.path if (args.path != None) else Default['path']
    GitHubRepository = args.github_repository if (args.github_repository != None) else Default['github_repository']
    GitHubToken = args.github_token if (args.github_token != None) else Default['github_token']
    ReleaseNotesFile = args.release_notes_file if (args.release_notes_file != None) else Default['release_notes_file']
    Verbose = True if args.verbose else Default['verbose']
    matched_commits = []
    releaseNotes = []
    # Auth = Default['auth']

    # Open the Git repository
    repo = Repo(RepoPath)
    git = repo.git

    # Create a GitHub instance
    gh = Github(GitHubToken)
    gh_repo = gh.get_repo(GitHubRepository)

	# Get most recent matching tags
    start_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(StartTagPattern)).split('\n')
    if len(start_tags) > 0:
        start_tag = start_tags[-1]
        if start_tag != '':
            start_commit = repo.tags[start_tag].commit
            end_tag = ''
            if EndTagPattern == 'HEAD':
                end_commit = repo.head.commit
                end_tag = 'HEAD'
            else:
                end_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(EndTagPattern)).split('\n')
                end_tag = end_tags[-1]
                end_commit = repo.tags[end_tag].commit
            head = repo.head.commit
            if Verbose:
                print("Settings:")
                print("start_tag={0}".format(start_tag))
                print("start_commit={0}".format(start_commit))
                print("end_tag={0}".format(end_tag))
                print("end_commit={0}".format(end_commit))
                print("")

        	# Get matching Pull Requests within the start and end range
            merged_commits = get_merge_commits(repo, start_commit.hexsha)
            merged_commits.reverse()
            hotFixCommits = get_matching_commits(merged_commits, CommitMessagePattern)
            if ReleaseNotesFile != '' and GitHubToken != '':
                releaseNotes = get_pr_release_notes(hotFixCommits)
            if Verbose:
                print("HotFixPRs={0}\n".format(hotFixCommits))

            for pr in hotFixCommits:
                matched_commits.append(pr.hexsha)

    # Create release notes file
    if ReleaseNotesFile != '' and GitHubToken != '':
        with open(ReleaseNotesFile, 'w') as f:
            f.write("## What's Changed\\n")
            for releaseNote in releaseNotes:
                f.write(releaseNote + "\\n")
        f.close()

	# Return matching commits
    matching_commits = ' '.join(matched_commits)
    print("commits={0}".format(matching_commits))
    print("count={0}".format(len(matching_commits.split())))
    if len(matched_commits) > 0:
        first_commit = matched_commits[0]
        last_commit = matched_commits[-1]
    else:
        first_commit = ''
        last_commit = ''
    print("first_commit={0}".format(first_commit))
    print("last_commit={0}".format(last_commit))
    if "GITHUB_OUTPUT" in os.environ:
        set_output('commits', matching_commits)
        set_output('count', len(matching_commits.split()))
        set_output('first_commit', first_commit)
        set_output('last_commit', last_commit)

if __name__ == '__main__':
    main()
# End of file
