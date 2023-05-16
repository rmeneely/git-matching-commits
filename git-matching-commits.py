#!/usr/bin/env python3

# Modules
import argparse
import re
import os
import subprocess
from git import Repo

# Default values
DefaultStartTagPattern = 'v[0-9]+.[0-9]+.[0-9]+'
DefaultEndTagPattern = 'HEAD'
DefaultCommitMessagePattern = '.*'

# Arguments
parser = argparse.ArgumentParser(description='Match Git commits based on matching commit message')
parser.add_argument('--start_tag_pattern', type=str, help='Start tag pattern')
parser.add_argument('--end_tag_pattern', type=str, help='End tag pattern')
parser.add_argument('--commit_message_pattern', type=str, help='Commit message pattern')
args = parser.parse_args()

# Global variables
StartTagPattern = args.start_tag_pattern if (args.start_tag_pattern != None) else DefaultStartTagPattern
EndTagPattern = args.end_tag_pattern if (args.end_tag_pattern != None) else DefaultEndTagPattern
CommitMessagePattern = args.commit_message_pattern if (args.commit_message_pattern != None) else DefaultCommitMessagePattern

# Path to the Git repository
repo_path = '.'

# Open the Git repository
repo = Repo(repo_path)
git = repo.git

# Get most recent matching tags
start_tags = git.tag('--sort=committerdate', '--list', '{0}'.format(StartTagPattern)).split('\n')
start_tag = start_tags[-1]
end_tag = 'HEAD'
if EndTagPattern != 'HEAD':
    end_tag = git.tag('--sort=committerdate', '--list', '{0}'.format(EndTagPattern))

# Get all commits between the two tags (not including the start tag)
commits = list(repo.iter_commits("{0}..{1}".format(start_tag, end_tag)))
matched_commits = []
for commit in commits:
    if re.search(CommitMessagePattern, commit.message):
        matched_commits.append(commit.hexsha)
matched_commits.reverse() # Reverse the list so they are in chronological order

# Return matching commits
print("{0}".format(','.join(matched_commits)))
# os.environ['MATCHED_COMMITS'] = ','.join(matched_commits)

# End of file
