"""Admission orchestration tests; fixtures here are not experiment evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
from resai.core import digest

spec=importlib.util.spec_from_file_location('campaign_controller',Path(__file__).resolve().parents[1]/'experiments/campaign/controller.py')
controller=importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class Adapter:
    def __init__(self,mutate=None):
        self.events=[]
        self.mutate=mutate
    def validate_upstream(self,plan):
        self.events.append('static')
        return []
    def upstream_smoke(self,plan):
        self.events.append('actual_upstream_smoke')
        return dict(returncode=0,outputs_present=True,raw_trace='test-fixture-only')
    def validate_binding(self,plan):
        return []
    def probe(self,plan,index):
        self.events.append('probe')
        row=dict(attempt_id=str(index),plan_hash=digest(plan),status='ok',passed_probes=['native','oracle'],
            output_valid=True,gpu_seconds=1,timestamp=1000,peak_memory_fraction=.3)
        if self.mutate:
            self.mutate(row)
        return row
    def production(self,plan):
        self.events.append('production')
        return {'status':'test-fixture-only'}


class CampaignControllerTests(unittest.TestCase):
    def setUp(self):
        self.plan=dict(scientific={'fixture':'not experimental data','batch_invariant':False},
            execution=dict(nodes=1,gpus_per_node=1,batch_size=1,wall_seconds=900,partition='fixture'),
            required_probes=['native','oracle'],budget_gpu_seconds=100,max_attempts=4)
    def test_conditions_do_distinct_work(self):
        expected={
            'direct_native':['production'],
            'upstream_static':['static','production'],
            'upstream_smoke_then_production':['static','actual_upstream_smoke','production'],
            'resai_full':['static','probe','probe','production'],
            'no_refinement':['static','probe','probe','production']}
        for condition,events in expected.items():
            with self.subTest(condition=condition):
                adapter=Adapter()
                self.assertTrue(controller.execute(condition,self.plan,adapter,lambda:1000)['admitted'])
                self.assertEqual(adapter.events,events)
    def test_coverage_ablation_does_not_remove_output_contract(self):
        def mutate(row):
            row['passed_probes']=['native']
        self.assertFalse(controller.execute('resai_full',self.plan,Adapter(mutate),lambda:1000)['admitted'])
        self.assertTrue(controller.execute('no_coverage',self.plan,Adapter(mutate),lambda:1000)['admitted'])
        def corrupt(row):
            mutate(row)
            row['output_valid']=False
        self.assertFalse(controller.execute('no_coverage',self.plan,Adapter(corrupt),lambda:1000)['admitted'])
    def test_identity_ablation_retains_raw_mismatch_and_checks_outcome(self):
        def mutate(row):
            row.update(plan_hash='old',timestamp=-10000)
        result=controller.execute('no_identity_freshness',self.plan,Adapter(mutate),lambda:1000)
        self.assertTrue(result['admitted'])
        self.assertTrue(all(r['plan_hash']=='old' for r in result['attempts']))
        self.assertNotEqual(result['decision']['raw_evidence_hash'],result['decision']['policy_projection_hash'])
        def failed(row):
            mutate(row)
            row['status']='failed'
        self.assertFalse(controller.execute('no_identity_freshness',self.plan,Adapter(failed),lambda:1000)['admitted'])
    def test_noninvariant_oom_never_refines_science(self):
        def oom(row):
            row.update(status='failed',fault='oom')
        before=copy.deepcopy(self.plan)
        result=controller.execute('resai_full',self.plan,Adapter(oom),lambda:1000)
        self.assertFalse(result['production_attempted'])
        self.assertEqual(result['refinements'],[])
        self.assertEqual(self.plan,before)
    def test_missing_obligation_blocks_before_another_expensive_probe(self):
        adapter=Adapter(lambda row: row.update(passed_probes=['native']))
        result=controller.execute('resai_full',self.plan,adapter,lambda:1000)
        self.assertFalse(result['admitted'])
        self.assertEqual(adapter.events,['static','probe'])
