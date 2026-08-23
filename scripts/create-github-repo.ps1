#requires -Version 7.0
param(
    [string]$RepoName = 'Genre_test',
    [ValidateSet('private','public')][string]$Visibility = 'private'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) not found.'
}

gh auth status
if (-not (Test-Path .git)) {
    git init -b main
    git add .
    git commit -m 'Initial Genre_test MVP'
}

gh repo create $RepoName "--$Visibility" --source . --remote origin --push
