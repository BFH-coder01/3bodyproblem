#!/usr/bin/env python3
"""Create one task worktree safely. Python 3.11+, Git; no third-party packages.

Plan reads repository state only. Create never pushes, merges, installs, deletes,
starts an agent, or rewrites branches. Local envelopes live outside the checkout.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import socket
import subprocess
import sys

ROLES = ('coordinator', 'contracts', 'numerical', 'scheduler', 'worker', 'gpu',
         'viewer', 'verifier', 'platform')

class WorkspaceError(RuntimeError):
    pass

def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(['git', '-C', str(repo), *args], text=True,
                            capture_output=True, check=False)
    if check and result.returncode:
        raise WorkspaceError(result.stderr.strip() or 'Git command failed')
    return result

def load_assignment(repo: Path, task: str) -> dict:
    path = repo / 'ops' / 'tasks' / f'{task}.json'
    if not path.is_file():
        raise WorkspaceError(f'Missing task definition: {path}')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise WorkspaceError(f'Invalid task JSON: {exc}') from exc
    if data.get('task_id') != task:
        raise WorkspaceError('Task ID does not match its definition')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', data.get('slug', '')):
        raise WorkspaceError('Task slug must use lowercase letters/digits/hyphens')
    if not isinstance(data.get('allowed_paths'), list) or not data['allowed_paths']:
        raise WorkspaceError('Task must declare allowed_paths')
    for entry in data['allowed_paths']:
        if not isinstance(entry, str) or entry.startswith(('/', '\\')) or '..' in Path(entry.replace('\\', '/')).parts or ':' in entry:
            raise WorkspaceError('Task allowed_paths must be relative without parent traversal')
    return data

def prepare(args: argparse.Namespace) -> dict:
    if not re.fullmatch(r'TBL-\d{3}', args.task):
        raise WorkspaceError('Use a task ID such as TBL-020')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.agent):
        raise WorkspaceError('Agent name must use lowercase letters/digits/hyphens')
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise WorkspaceError('Repository directory does not exist')
    top = Path(git(repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()
    if top != repo:
        raise WorkspaceError('Point --repo at the repository root, not a subdirectory')
    assignment = load_assignment(repo, args.task)
    if assignment.get('role') != args.role:
        raise WorkspaceError('Requested role does not match the task definition')
    root = Path(args.root).expanduser().resolve() if args.root else (repo.parent / 'worktrees').resolve()
    if root == repo or root.is_relative_to(repo):
        raise WorkspaceError('Worktrees must be outside the root checkout')
    branch = f'agent/{args.agent}/{args.task.lower()}-{assignment["slug"]}'
    destination = root / f'{args.task.lower()}-{args.agent}'
    envelope = root / '.assignments' / f'{args.task.lower()}-{args.agent}.json'
    if args.action == 'create':
        if assignment.get('status') != 'ready':
            raise WorkspaceError('Task is not ready; coordinator must accept dependencies and dispatch it first')
        if git(repo, 'status', '--porcelain').stdout.strip():
            raise WorkspaceError('Root checkout is dirty; preserve/commit its work before creating a workspace')
        if destination.exists() or envelope.exists():
            raise WorkspaceError('Workspace or assignment envelope already exists; refusing to overwrite')
        if git(repo, 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}', check=False).returncode == 0:
            raise WorkspaceError('Task branch already exists; inspect it before resuming or choosing a new assignment')
        if args.fetch:
            git(repo, 'fetch', '--prune', 'origin')
    if args.base.startswith('-'):
        raise WorkspaceError('Invalid base revision')
    base_sha = git(repo, 'rev-parse', '--verify', f'{args.base}^{{commit}}').stdout.strip()
    accepted = assignment.get('accepted_base_sha')
    if accepted and accepted != base_sha:
        raise WorkspaceError('Resolved base differs from the coordinator-accepted SHA')
    return {
        'task_id': args.task, 'agent': args.agent, 'role': args.role,
        'repository_root': str(repo), 'worktree_root': str(root),
        'worktree': str(destination), 'branch': branch, 'base_ref': args.base,
        'base_sha': base_sha, 'assignment_envelope': str(envelope),
        'task_definition': assignment,
        'git_command': ['git', '-C', str(repo), 'worktree', 'add', '-b', branch,
                        str(destination), base_sha],
        'fetch_requested': args.fetch,
        'changes_repository': args.action == 'create',
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'create'))
    parser.add_argument('--repo', required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--agent', required=True)
    parser.add_argument('--role', required=True, choices=ROLES)
    parser.add_argument('--base', default='origin/main')
    parser.add_argument('--root', help='Sibling worktree root; default: repo parent/worktrees')
    parser.add_argument('--fetch', action='store_true', help='Fetch origin before create; plan never fetches')
    args = parser.parse_args(argv)
    try:
        result = prepare(args)
        if args.action == 'create':
            root = Path(result['worktree_root'])
            root.mkdir(parents=True, exist_ok=True)
            git(Path(result['repository_root']), 'worktree', 'add', '-b',
                result['branch'], result['worktree'], result['base_sha'])
            result['created_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
            result['host'] = socket.gethostname()
            result['status'] = 'created-not-agent-launched'
            envelope = Path(result['assignment_envelope'])
            envelope.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive create: never overwrite an assignment, even after a race.
            with envelope.open('x', encoding='utf-8') as handle:
                json.dump(result, handle, indent=2)
                handle.write('\n')
        else:
            result['status'] = 'plan-only'
        print(json.dumps(result, indent=2))
        return 0
    except (WorkspaceError, OSError) as exc:
        print(json.dumps({'error': str(exc), 'action': args.action}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
