#!/usr/bin/env python3

# Modules
import argparse
import re
import os
import subprocess
# See https://gitpython.readthedocs.io/en/stable/tutorial.html
from git import Repo
from github_action_utils import set_output


def parse_args():
    # Arguments
    parser = argparse.ArgumentParser(description='Match Git commits based on matching commit message')
    parser.add_argument('--path', type=str, help='Path to the Git repository')
    parser.add_argument('--start_tag_pattern', type=str, help='Start tag pattern')
    parser.add_argument('--end_tag_pattern', type=str, help='End tag pattern')
    parser.add_argument('--commit_message_pattern', type=str, help='Commit message pattern')
    parser.add_argument('--pr_labels', type=str, help='Pull Request labels')
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

def get_matching_commits(text, commit_message_pattern):
    commits = split_commits(text)
    hotfix_commits = []
    for commit in commits:
        if re.search(commit_message_pattern, commit, re.IGNORECASE):
            hotfix_commits.append(commit)
    return hotfix_commits

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

def main():
    # Default values
    DefaultPath = '.'
    DefaultStartTagPattern = 'v[0-9]+.[0-9]+.[0-9]+'
    DefaultEndTagPattern = 'HEAD'
    DefaultCommitMessagePattern = '.*'
    DefaultPullRequestLabels = []
    DefaultVerbose = False

    # Get arguments
    args = parse_args()

	# Global variables
    StartTagPattern = args.start_tag_pattern if (args.start_tag_pattern != None) else DefaultStartTagPattern
    EndTagPattern = args.end_tag_pattern if (args.end_tag_pattern != None) else DefaultEndTagPattern
    CommitMessagePattern = args.commit_message_pattern if (args.commit_message_pattern != None) else DefaultCommitMessagePattern
    PullRequestLabels = args.pr_labels.split(',') if (args.pr_labels != None) else DefaultPullRequestLabels
    repo_path = args.path if (args.path != None) else DefaultPath
    matched_commits = []
    if args.verbose:
        Verbose = True
    else:
	    Verbose = False

    # Open the Git repository
    repo = Repo(repo_path)
    git = repo.git

	# Get most recent matching tags
    start_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(StartTagPattern)).split('\n')
    start_tag = start_tags[-1]
    tag = repo.tags[start_tag]
    start_commit = tag.commit
    end_tag = 'HEAD'
    head = repo.head.commit
    if Verbose:
        print("start_tag={0}".format(start_tag))
        print("start_commit={0}".format(start_commit))
        print("end_tag={0}".format(end_tag))
        print("")

	# Get matching Pull Requests within the start and end range
    HotFixPRs = get_matching_commits(git.log("--merges", "{}..{}".format(start_tag, end_tag)), CommitMessagePattern)
    if Verbose:
        print("HotFixPRs={0}\n".format(HotFixPRs))
    for pr in HotFixPRs:
        pr_commit = extract_commit_value(pr)
        matched_commits.append(pr_commit)
        # range = extract_merge_values(pr)
        # matched_commits.append(pr_commit)
        # # Add all commits within the PR range
        # tmpCommits = list(repo.iter_commits('{0}..{1}'.format(range[0], range[1]), reverse=False, paths=None, since=None, until=None, author=None, committer=None, message=None, name_only=False))
        # if Verbose:
        #     print("list(repo.iter_commits('{0}..{1}',  committer=None))".format(range[0], range[1]))
        #     print("tmpCommits={0}\n".format(tmpCommits))
        # for tmpCommit in tmpCommits:
        #     matched_commits.append(tmpCommit.hexsha)
    matched_commits.reverse()

	# Return matching commits
    matching_commits = ' '.join(matched_commits)
    print("commits={0}".format(matching_commits))
    if "GITHUB_OUTPUT" in os.environ:
	    set_output('commits', matching_commits)

if __name__ == '__main__':
    main()
# End of file
