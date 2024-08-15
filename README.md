# git-matching-commits
This GitHub Action returns a space separated string of all git commit SHAs within a merged commit where the commit matches either a commit message pattern, or a GitHub label.
Note that the commit_message_pattern is against merged commits (i.e. Pull Request merges), not individual commits within the Pull Request.
The order of the returned commits is according to `committerdate`



> **NOTICE:** In v2 the `commit_message_pattern` is against merged commits e.g. PR commit messages not against individual commit messages. This means if a merged commit matches the `commit_message_pattern` all commits within that merged commit will be returned regardless of their individual commit messages.


## Usage
```yaml
    - uses: rmeneely/git-matching-commits@v2
      with:
        start_tag_pattern: regex
        end_tag_pattern: regex
        commit_message_pattern: regex
```

### Inputs
All inputs are optional. If not set the default value will be used.

| Name                   | Description                                 | Default              |
| ---------------------- |:------------------------------------------- | :------------------------------------------- |
| start_tag_pattern      | regex expression to match the starting tag  | v[0-9]*.[0-9]*.[0-9] |
| end_tag_pattern        | regex expression to match the ending tag    | HEAD |
| commit_message_pattern | regex expression to match a returned commit | '' |
| commit_type            | The type of commits to match (`merge`, `all`)    | merge |
| github_labels | Comma separated list of GitHub labels used to identify matching commit | none |
| github_repository | \<owner>/\<repository> - Required if either `gethub_labels` or `release_notes_file` is set | none  |
| github_token | GitHub token - Required if either `gethub_labels` or `release_notes_file` is set | none |
| release_notes_file | Write release notes to filename | none |

## Examples
```yaml
    # Returns a string containing all matching merged commits where the merged commit message contains the text [Hotfix] (case-insensative)
    # The range of merged commits is between the latest commit with tag matching the start tag pattern and the current branch HEAD
    - uses: rmeneely/git-matching-commits@v2
      id: git-matching-commits
      with:
        start_tag_pattern: 'v[0-9]*.[0-9]*.0'
        commit_message_pattern: '\[Hotfix\]'
    - name: Get matched commits
      run: echo "MATCHED_COMMITS=${{ steps.git-matching-commits.outputs.commits }}" >> $GITHUB_ENV
```

Matches either a string within the merged commit, or a GitHub Pull Request label 'hotfix'
```yaml
    # Returns a string containing all matching merged commits where the merged commit either:
    Has a PR title containing the text [Hotfix] (case-insensitive). The range of merged commits is between the latest commit with tag matching the start tag pattern and the current branch HEAD
     OR
    The merged commit Pull Request has a GitHub Pull Request label of 'hotfix'
    Creates a file named release-notes containing the GitHub PR release notes for matching commits
    - uses: rmeneely/git-matching-commits@v2
      id: git-matching-commits
      with:
        start_tag_pattern: 'v[0-9]*.[0-9]*.0'
        commit_message_pattern: '\[Hotfix\]'
        github_labels: hotfix
        github_repository: myorganization/myrepo
        github_token: ${ secrets.GITHUB_TOKEN }
        release_notes_file: release-notes
    - name: Get matched commits
      run: echo "MATCHED_COMMITS=${{ steps.git-matching-commits.outputs.commits }}" >> $GITHUB_ENV
```


## Output
```shell
steps.git-matching-commits.outputs.commits      # Set to space separated list of matched commit SHAs
steps.git-matching-commits.outputs.count        # The number of matched commits
steps.git-matching-commits.outputs.first_commit # The first commitSHA in the list
steps.git-matching-commits.outputs.last_commit  # The last commitSHA in the list

Example:
steps.git-matching-commits.outputs.commits=f9e96e6afbf893795c3c5f44d968b19fa51925cc e5b84631f0824d9e8c57d44893abdae96917aab9 186e65812e63c80fbf3690723454ebc5f09fb05b 0f3e43604075eafe0a432cc4d4f1bb421aa800c3 285f45cb9871d3b6cf9758700f85fb51436dbcd2
steps.git-matching-commits.outputs.count=5
steps.git-matching-commits.outputs.first_commit=f9e96e6afbf893795c3c5f44d968b19fa51925cc
steps.git-matching-commits.outputs.last_commit=285f45cb9871d3b6cf9758700f85fb51436dbcd2
```

## License
The MIT License (MIT)
