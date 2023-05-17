#!/usr/bin/env python3

# Modules
import argparse
import re
import os
import subprocess
from git import Repo
from github_action_utils import set_output

# Default values
DefaultPath = '.'
DefaultStartTagPattern = 'v[0-9]+.[0-9]+.[0-9]+'
DefaultEndTagPattern = 'HEAD'
DefaultCommitMessagePattern = '.*'
Debug = True

# Arguments
parser = argparse.ArgumentParser(description='Match Git commits based on matching commit message')
parser.add_argument('--path', type=str, help='Path to the Git repository')
parser.add_argument('--start_tag_pattern', type=str, help='Start tag pattern')
parser.add_argument('--end_tag_pattern', type=str, help='End tag pattern')
parser.add_argument('--commit_message_pattern', type=str, help='Commit message pattern')
args = parser.parse_args()

# Global variables
StartTagPattern = args.start_tag_pattern if (args.start_tag_pattern != None) else DefaultStartTagPattern
EndTagPattern = args.end_tag_pattern if (args.end_tag_pattern != None) else DefaultEndTagPattern
CommitMessagePattern = args.commit_message_pattern if (args.commit_message_pattern != None) else DefaultCommitMessagePattern
repo_path = args.path if (args.path != None) else DefaultPath

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
if Debug:
    print("start_tag={0}".format(start_tag))
    print("start_commit={0}".format(start_commit))
    print("end_tag={0}".format(end_tag))

# if EndTagPattern != 'HEAD':
#     end_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(EndTagPattern))
#     end_tag = end_tags[-1]

# Get all commits between the two tags (not including the start tag)
# commits = list(repo.iter_commits('{0}..{1}'.format(start_tag, end_tag), reverse=True, paths=None, since=None, until=None, author=None, committer=None, message=None, name_only=False))

with open('commits.txt', 'r') as f:
    commits = list(f)
    commits = [c.strip() for c in commits]
print("# of commits={0}".format(len(commits)))
matched_commits = []
for commit in commits:
    # commits = list(repo.iter_commits(max_count=50, skip=skip))
    # skip += len(commits)
    theCommit = repo.commit(commit)
    if Debug:
        print("commit={0}".format(theCommit.hexsha))
    if theCommit.hexsha == start_commit.hexsha:
        next # Skip start commit
    if re.search(CommitMessagePattern, theCommit.message):
        print("Matched commit={0}".format(theCommit.hexsha))
        matched_commits.append(commit)
    # if theCommit.hexsha == head.hexsha:
    #     done = True
    #     break

# Return matching commits
matching_commits = ','.join(matched_commits)
# os.environ['COMMITS'] = matching_commits
print("commits={0}".format(matching_commits))
# set_output('commits', matching_commits)
if "GITHUB_OUTPUT" in os.environ:
    print("GITHUB_OUTPUT={0}".format(os.environ.get('GITHUB_OUTPUT')))
    github_output = os.environ.get('GITHUB_OUTPUT')
    f = open('git-matching-commits.output', 'a')
    f.write("commits={0}\n".format(matching_commits))
    f.close
    os.system("echo commits={0} >> {1}".format(matching_commits, github_output))

# End of file
