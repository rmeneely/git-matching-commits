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
    parser.add_argument('--commit_type', type=str, help='Commit type')
    parser.add_argument('--cherry_pick', action="store_true", help='Cherry-pick matching commits')
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

def get_matching_commits(commits, commit_message_pattern):
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
    # DefaultPath = '.'
    # DefaultStartTagPattern = 'v[0-9]+.[0-9]+.[0-9]+'
    # DefaultEndTagPattern = 'HEAD'
    # DefaultCommitMessagePattern = '.*'
    # DefaultPullRequestLabels = []
    # DefaultVerbose = False
    Default = {
        'path': '.',
        'start_tag_pattern': 'v[0-9]+.[0-9]+.[0-9]+',
        'end_tag_pattern': 'HEAD',
        'commit_message_pattern': '.*',
        'commit_type': 'merge',
        'cherry_pick': False,
        'pr_labels': [],
        'verbose': False
    }

    # Get arguments
    args = parse_args()

	# Global variables
    Global = Default    # Set Global to Default values
    StartTagPattern = args.start_tag_pattern if (args.start_tag_pattern != None) else Default['start_tag_pattern']
    EndTagPattern = args.end_tag_pattern if (args.end_tag_pattern != None) else Default['end_tag_pattern']
    CommitMessagePattern = args.commit_message_pattern if (args.commit_message_pattern != None) else Default['commit_message_pattern']
    CommitType = args.commit_type if (args.commit_type != None) else Default['commit_type']
    CherryPick = True if args.cherry_pick else Default['cherry_pick']
    PullRequestLabels = args.pr_labels.split(',') if (args.pr_labels != None) else Default['pr_labels']
    RepoPath = args.path if (args.path != None) else Default['path']
    Verbose = True if args.verbose else Default['verbose']
    matched_commits = []

    # Open the Git repository
    repo = Repo(RepoPath)
    git = repo.git

	# Get most recent matching tags
    start_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(StartTagPattern)).split('\n')
    if len(start_tags) > 0:
        print("start_tags={0}".format(start_tags))
        start_tag = start_tags[-1]
        if start_tag != '':
            print("start_tag={0}".format(start_tag))
            start_commit = repo.tags[start_tag].commit
            print("start_commit={0}".format(start_commit))
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
                print("CherryPick={0}".format(CherryPick))
                print("")

        	# Get matching Pull Requests within the start and end range
            merged_commits = split_commits(git.log("--merges", "{}..{}".format(start_tag, end_tag)))
            merged_commits.reverse()
            HotFixPRs = get_matching_commits(merged_commits, CommitMessagePattern)
            if Verbose:
                print("git log --merges {}..{}".format(start_tag, end_tag))
                print("HotFixPRs={0}\n".format(HotFixPRs))

            for pr in HotFixPRs:
                pr_commit = extract_commit_value(pr)
                if CommitType == 'all':
                    range = extract_merge_values(pr)
                    _commits = list(repo.iter_commits('{0}..{1}'.format(range[0], range[1]), reverse=False, paths=None, since=None, until=None, author=None, committer=None, message=None, name_only=False))
                    for commit in _commits:
                        if CherryPick:
                            #git.cherry_pick("{}".format(commit.hexsha))
                            #print("git.cherry_pick(\"{}\")".format(commit.hexsha))
                            nothing = 0
                        matched_commits.append(commit.hexsha)
                if CherryPick:
                    #git.cherry_pick("-m 1", "{}".format(pr_commit))
                    #print("git.cherry_pick(\"-m 1\", \"{}\"".format(pr_commit))
                    nothing = 0
                matched_commits.append(pr_commit)

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
