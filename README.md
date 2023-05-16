# git-matching-commits
This GitHub Action returns a comma separated string of matching git commit SHAs.

## Usage
```yaml
    - uses: rmeneely/git-matching-commits@v1
      with:
        start_tag_pattern: regex
        end_tag_pattern: regex
        commit_message_pattern: regex
```

### Inputs
All inputs are optional. If not set the default value will be used.

| Name                   | Description                                 | Default              |
| ---------------------- |:------------------------------------------- | :--------------------|
| start_tag_pattern      | regex expression to match the starting tag  | v[0-9]*.[0-9]*.[0-9] |
| end_tag_pattern        | regex expression to match the ending tag    | HEAD |
| commit_message_pattern | regex expression to match a returned commit | .* |


## Examples
```yaml
    # Returns a list of commits between the latest commit with tag matching the start tag pattern and the current branch HEAD which commit messages contain '[Hotfix]'
    - uses: rmeneely/git-matching-commits@v1
      with:
        start_tag_pattern: 'v[0-9]*.[0-9]*.0'
        commit_message_pattern: '\[Hotfix\]'
```


## Output
```shell
steps.git-matching-commits.outputs.commits - Set to comma separated list of matched commit SHAs
```

## License
The MIT License (MIT)
