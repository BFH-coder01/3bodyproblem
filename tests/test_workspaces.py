import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'scripts' / 'workspaces.py'

class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='three body workspaces ')
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo with spaces'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'workspace-tests@example.invalid')
        self.git('config', 'user.name', 'Workspace test')
        (self.repo / 'ops' / 'tasks').mkdir(parents=True)
        self.task = {'task_id':'TBL-020','slug':'reference-cli','role':'numerical',
                     'status':'ready','allowed_paths':['native/core/'],
                     'accepted_base_sha':None,'dependencies':[]}
        self.write_task()
        (self.repo / 'README.md').write_text('temporary test seed\n')
        self.git('add', '.')
        self.git('commit', '-m', 'Seed disposable workspace test')
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()

    def tearDown(self):
        # Worktrees are all inside the disposable temporary directory.
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git','-C',str(self.repo),*args],text=True,
                              capture_output=True,check=True)

    def write_task(self):
        (self.repo/'ops/tasks/TBL-020.json').write_text(json.dumps(self.task))

    def run_helper(self, action='plan', *extra):
        return subprocess.run([sys.executable,str(HELPER),action,'--repo',str(self.repo),
            '--task','TBL-020','--agent','numerical-a','--role','numerical',
            '--base','main',*extra],text=True,capture_output=True)

    def test_plan_does_not_mutate(self):
        before=self.git('show-ref').stdout
        result=self.run_helper()
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['base_sha'],self.base)
        self.assertFalse(Path(data['worktree']).exists())
        self.assertEqual(self.git('show-ref').stdout,before)
        self.assertEqual(self.git('status','--porcelain').stdout,'')

    def test_create_exact_branch_base_and_envelope(self):
        result=self.run_helper('create')
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(self.git('rev-parse',data['branch']).stdout.strip(),self.base)
        wt=Path(data['worktree'])
        head=subprocess.run(['git','-C',str(wt),'rev-parse','HEAD'],text=True,
                            capture_output=True,check=True).stdout.strip()
        self.assertEqual(head,self.base)
        self.assertEqual(json.loads(Path(data['assignment_envelope']).read_text())['task_id'],'TBL-020')
        self.assertEqual(self.git('status','--porcelain').stdout,'')

    def test_existing_workspace_is_preserved(self):
        first=self.run_helper('create'); self.assertEqual(first.returncode,0)
        data=json.loads(first.stdout); sentinel=Path(data['worktree'])/'do-not-delete.txt'
        sentinel.write_text('preserve')
        second=self.run_helper('create')
        self.assertNotEqual(second.returncode,0)
        self.assertEqual(sentinel.read_text(),'preserve')

    def test_unready_task_refused(self):
        self.task['status']='planned'; self.write_task()
        self.git('add','.'); self.git('commit','-m','Mark planned')
        result=self.run_helper('create')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('not ready',result.stderr)

    def test_dirty_root_refused(self):
        (self.repo/'README.md').write_text('uncommitted work')
        result=self.run_helper('create')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('dirty',result.stderr)
        self.assertEqual((self.repo/'README.md').read_text(),'uncommitted work')

    def test_role_mismatch_refused(self):
        self.task['role']='gpu'; self.write_task()
        result=self.run_helper()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('role',result.stderr)

    def test_base_mismatch_refused(self):
        self.task['accepted_base_sha']='0'*40; self.write_task()
        result=self.run_helper()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('accepted SHA',result.stderr)

    def test_nested_worktrees_refused(self):
        result=self.run_helper('plan','--root',str(self.repo/'nested'))
        self.assertNotEqual(result.returncode,0)
        self.assertIn('outside',result.stderr)

if __name__=='__main__':
    unittest.main()
