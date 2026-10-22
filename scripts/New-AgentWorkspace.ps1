# Convenience wrapper. Requires an installed Python 3.11+ executable.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Repo,
    [Parameter(Mandatory=$true)][string]$Task,
    [Parameter(Mandatory=$true)][string]$Agent,
    [Parameter(Mandatory=$true)][string]$Role,
    [string]$Base = 'origin/main',
    [string]$Root,
    [string]$Python = 'python',
    [switch]$Create,
    [switch]$Fetch
)
$ErrorActionPreference = 'Stop'
$Mode = if ($Create) { 'create' } else { 'plan' }
$Script = Join-Path $PSScriptRoot 'workspaces.py'
$Arguments = @($Script, $Mode, '--repo', $Repo, '--task', $Task, '--agent', $Agent, '--role', $Role, '--base', $Base)
if ($Root) { $Arguments += @('--root', $Root) }
if ($Fetch) { $Arguments += '--fetch' }
& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Workspace helper failed with exit code $LASTEXITCODE" }
