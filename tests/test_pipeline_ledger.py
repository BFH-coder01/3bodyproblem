import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from services.ledger import Ledger, LedgerError, initial_positions
from services.pipeline import make_server, strict_json

EXP = 'a' * 64
SOLVER = 'b' * 64
MANIFEST = {'protocol':'threebody.pipeline.v1','model':'point-close-stop-v1','radius':2,'duration':6,'dt':.002}
DESC = {'manifest':MANIFEST,'experiment_id':EXP,'total':'2300','solver_digest':SOLVER}


def result(ordinal, replay=True):
    p = initial_positions(2, ordinal)
    state = {'p':p,'v':[0]*6}
    return {'protocol':'threebody.pipeline.v1','experiment_id':EXP,'trial_id':f'{EXP}:{ordinal}',
            'ordinal':str(ordinal),'solver_digest':SOLVER,'runtime':{'node':'v24.19.0','platform':'linux','arch':'x64'},'engine':'js-baseline-v2','precision':'fp64','outcome':'Bounded',
            'time':6,'initial':copy.deepcopy(state),'final':copy.deepcopy(state),'steps':100,
            'energyError':0,'minSeparation':1,'orbit':{'detected':False,'reason':'No repeating orbit detected','cycles':0,'tolerance':.02},
            'replayEligible':True,'replay':{'frames':[[0,*p],[6,*p]],'velocityFrames':[[0]*6,[0]*6]} if replay else None}


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name)/'pipeline.sqlite'
        self.now = 100
        self.ledger = Ledger(self.db, clock=lambda:self.now, lease_seconds=10)
        self.ledger.add_experiment(copy.deepcopy(DESC),0,4,2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_retry_restart_and_pagination(self):
        lease=self.ledger.acquire('one')
        accepted=self.ledger.submit(lease['task_id'],'one',1,[result(1),result(0)])
        self.assertEqual(accepted,{'accepted':2,'idempotent':False})
        self.assertTrue(self.ledger.submit(lease['task_id'],'one',1,[result(0),result(1)])['idempotent'])
        restarted=Ledger(self.db, clock=lambda:self.now)
        self.assertEqual(restarted.status()['experiments'][0]['accepted'],2)
        page=restarted.trials(EXP,limit=1)
        self.assertEqual(page['trials'][0]['ordinal'],'0')
        self.assertNotIn('replay',page['trials'][0])
        self.assertEqual(page['next_after'],'0')
        self.assertEqual(restarted.trials(EXP,after='0')['trials'][0]['ordinal'],'1')
        self.assertIsNotNone(restarted.replay(f'{EXP}:0')['replay'])
        self.assertEqual(restarted.status()['experiments'][0]['total'],4)

    def test_expiry_fencing_and_heartbeat(self):
        first=self.ledger.acquire('old')
        self.now=105
        self.ledger.heartbeat(first['task_id'],'old',1)
        self.now=114
        self.assertEqual(self.ledger.status()['experiments'][0]['running'],2)
        self.now=115
        self.assertEqual(self.ledger.status()['experiments'][0]['pending'],4)
        with self.assertRaises(LedgerError): self.ledger.heartbeat(first['task_id'],'old',1)
        new=self.ledger.acquire('new')
        self.assertEqual(new['task_id'],first['task_id'])
        self.assertEqual(new['epoch'],2)
        with self.assertRaises(LedgerError): self.ledger.submit(first['task_id'],'old',1,[result(0),result(1)])
        self.ledger.submit(new['task_id'],'new',2,[result(0),result(1)])

    def test_gaps_duplicates_and_atomic_reject(self):
        lease=self.ledger.acquire('one')
        for values in ([result(0)], [result(0),result(0)], [result(0),result(2)]):
            with self.subTest(values=[r['ordinal'] for r in values]):
                with self.assertRaises(LedgerError): self.ledger.submit(lease['task_id'],'one',1,values)
                self.assertEqual(self.ledger.status()['experiments'][0]['accepted'],0)
        self.ledger.submit(lease['task_id'],'one',1,[result(0),result(1)])
        changed=result(0); changed['steps']=101
        with self.assertRaises(LedgerError): self.ledger.submit(lease['task_id'],'one',1,[changed,result(1)])
        self.assertEqual(self.ledger.status()['experiments'][0]['accepted'],2)

    def test_invalid_results_never_publish(self):
        lease=self.ledger.acquire('one')
        mutations=[lambda r:r.update(time=float('nan')),
                   lambda r:r.update(ordinal='00'),
                   lambda r:r.update(ordinal='9'*5000),
                   lambda r:r.update(trial_id='other'),
                   lambda r:r.update(solver_digest='c'*64),
                   lambda r:r.update(runtime={}),
                   lambda r:r['runtime'].update(node=''),
                   lambda r:r['runtime'].update(node=' '),
                   lambda r:r['runtime'].update(node='x'*129),
                   lambda r:r['runtime'].update(node='bad\nvalue'),
                   lambda r:r['runtime'].update(node=24),
                   lambda r:r['runtime'].update(extra='unsupported'),
                   lambda r:r.update(replayEligible=False),
                   lambda r:r.update(outcome='Escaped'),
                   lambda r:r.update(outcome='Close encounter'),
                   lambda r:r['initial']['v'].__setitem__(0,1),
                   lambda r:r['initial']['p'].__setitem__(0,1),
                   lambda r:r['replay']['frames'][-1].__setitem__(0,7),
                   lambda r:r['final']['p'].append(1),
                   lambda r:r['orbit'].update(detected=True),
                   lambda r:r.update(extra='unsupported')]
        for mutation in mutations:
            r=result(0);mutation(r)
            with self.subTest(result=r):
                with self.assertRaises(LedgerError):self.ledger.submit(lease['task_id'],'one',1,[r,result(1)])
        self.assertEqual(self.ledger.status()['experiments'][0]['accepted'],0)

    def test_release_and_campaign_validation(self):
        lease=self.ledger.acquire('one')
        self.ledger.release(lease['task_id'],'one',1,'solver failed')
        status=self.ledger.status()['experiments'][0]
        self.assertEqual(status['pending'],4)
        self.assertEqual(status['errors'][0]['error'],'solver failed')
        self.assertEqual(self.ledger.acquire('two')['epoch'],2)
        changed=copy.deepcopy(DESC);changed['solver_digest']='c'*64
        with self.assertRaises(LedgerError):self.ledger.add_experiment(changed,0,4,2)
        with self.assertRaises(LedgerError):self.ledger.add_experiment(DESC,0,5,2)
        with self.assertRaises(LedgerError):self.ledger.add_experiment(DESC,0,4,33)
        with self.assertRaises(LedgerError):self.ledger.trials(EXP,after='01')
        with self.assertRaises(LedgerError):self.ledger.trials(EXP,limit=201)

    def test_http_validation_and_protocol(self):
        server=make_server(self.ledger,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        def request(path,body=None):
            req=Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=5) as response:return json.load(response)
        try:
            self.assertEqual(request('/v1/experiments')['experiments'][0]['total'],4)
            lease=request('/v1/lease',{'worker_id':'http'})['lease']
            self.assertTrue(request('/v1/heartbeat',{key:lease[key] for key in ('task_id','worker_id','epoch')})['ok'])
            payload={key:lease[key] for key in ('task_id','worker_id','epoch')};payload['results']=[result(0),result(1)]
            self.assertEqual(request('/v1/results',payload)['accepted'],2)
            self.assertEqual(request(f'/v1/trials?experiment_id={EXP}&limit=1')['next_after'],'0')
            self.assertEqual(request(f'/v1/trials/{EXP}:0/replay')['ordinal'],'0')
            for body in (b'{"worker_id":"a","worker_id":"b"}',b'{"worker_id":NaN}',b'[]'):
                with self.assertRaises(HTTPError) as exc:urlopen(Request(base+'/v1/lease',data=body,headers={'Content-Type':'application/json'}),timeout=5)
                self.assertEqual(exc.exception.code,400)
            for path in ('/viewer/../../LICENSE','/viewer/%2e%2e/LICENSE','/v1/trials?experiment_id=x&limit=bogus',f'/v1/trials?experiment_id={EXP}&after='+('9'*5000)):
                with self.assertRaises(HTTPError) as exc:request(path)
                self.assertIn(exc.exception.code,(400,404))
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_malformed_types_and_impossible_orbits_reject_through_http(self):
        server=make_server(self.ledger,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        lease=self.ledger.acquire('malformed')
        mutations=[lambda r:r.update(ordinal='9'*5000), lambda r:r.update(outcome=[]), lambda r:r.update(outcome={}),
                   lambda r:r.update(time=10**1000),
                   lambda r:r.update(orbit={'detected':True,'reason':'fake','cycles':3,'period':100,'tolerance':999,'maxNormalizedError':1}),
                   lambda r:r.update(orbit={'detected':True,'reason':'fake','cycles':3,'period':100,'tolerance':.02,'maxNormalizedError':.001}),
                   lambda r:r.update(orbit={'detected':True,'reason':'fake','cycles':3,'period':1,'tolerance':.02,'maxNormalizedError':.03}),
                   lambda r:r.update(orbit={'detected':True,'reason':'fake','cycles':4,'period':1,'tolerance':.02,'maxNormalizedError':.001}),
                   lambda r:r.update(orbit={'detected':True,'reason':'fake','cycles':3,'period':.09,'tolerance':.02,'maxNormalizedError':.001})]
        try:
            for mutation in mutations:
                malformed=result(0);mutation(malformed)
                payload={key:lease[key] for key in ('task_id','worker_id','epoch')}
                payload['results']=[malformed,result(1)]
                request=Request(base+'/v1/results',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with self.assertRaises(HTTPError) as exc:urlopen(request,timeout=5)
                self.assertEqual(exc.exception.code,400)
                self.assertEqual(json.load(exc.exception)['error']['code'],'invalid_request')
                self.assertEqual(self.ledger.status()['experiments'][0]['accepted'],0)
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_strict_json(self):
        for raw in ('{"x":NaN}','{"x":Infinity}','{"x":1e400}','{"x":1,"x":2}'):
            with self.assertRaises(LedgerError):strict_json(raw)


if __name__=='__main__':unittest.main()
