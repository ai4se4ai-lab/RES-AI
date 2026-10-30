import importlib.util
from pathlib import Path
import unittest
import tempfile
import json
import hashlib
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('campaign_budget',Path(__file__).resolve().parents[1]/'experiments/campaign/budget.py')
budget=importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class CampaignBudgetTests(unittest.TestCase):
    def setUp(self):
        self.plan={'subjects':[{'name':'A'},{'name':'B'}], 'initial_h100_budget_seconds':86400,
            'maximum_reserved_h100_seconds_per_artifact':7200}
        self.proof=dict(native_smoke_passed=True,oracle_passed=True,sandbox_validated=True,model_endpoint_verified=True)

    def test_unvalidated_native_adapter_cannot_reserve_gpu(self):
        with self.assertRaisesRegex(ValueError,'eligibility'):
            budget.reserve(self.plan,{},'A',60,{})

    def test_setup_failures_and_pending_allocations_consume_budget(self):
        self.plan['maximum_reserved_h100_seconds_per_artifact']=86400
        ledger={'reservations':[{'subject':'A','settled':True,'allocated_seconds':86,'reserved_seconds':960}]}
        budget.reserve(self.plan,ledger,'B',86254,self.proof)  # 86 + 86,254 + 60 grace = 86,400.
        with self.assertRaisesRegex(ValueError,'24 H100'):
            budget.reserve(self.plan,ledger,'B',1,self.proof)

    def test_per_artifact_cap_includes_termination_grace(self):
        ledger={}
        budget.reserve(self.plan,ledger,'A',7140,self.proof)
        with self.assertRaisesRegex(ValueError,'per-artifact'):
            budget.reserve(self.plan,ledger,'A',1,self.proof)

    def test_native_validation_reserves_cost_before_model_smoke_is_available(self):
        proof=dict(source_locked=True,dependencies_imported=True,sandbox_validated=True,local_transport_configured=True)
        ledger={}
        row=budget.reserve(self.plan,ledger,'A',300,proof,purpose='native_validation')
        self.assertEqual(row['reserved_seconds'],360)
        self.assertEqual(row['purpose'],'native_validation')
        with self.assertRaisesRegex(ValueError,'eligibility'):
            budget.reserve(self.plan,ledger,'A',300,proof,purpose='comparison')

    def test_prospective_allocation_preserves_global_cap_and_old_costs(self):
        self.plan['campaign_id']='fixture'
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            folder=root/'experiments/campaign/budget-allocations'
            folder.mkdir(parents=True)
            master=folder.parent/'plan.json'
            master.write_text(json.dumps(self.plan))
            amendment=dict(amendment_id='fixture',campaign_id='fixture',
                master_protocol_sha256=hashlib.sha256(master.read_bytes()).hexdigest(),
                global_h100_cap_seconds=86400,artifact_ceilings_seconds={'A':28800})
            path=folder/'fixture.json';path.write_text(json.dumps(amendment))
            (root/'budget-allocation-active.json').write_text(json.dumps(dict(
                path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
            ledger={'reservations':[dict(subject='A',settled=True,allocated_seconds=6385,reserved_seconds=960)]}
            with patch.object(budget,'ROOT',root):
                row=budget.reserve(self.plan,ledger,'A',900,self.proof)
                self.assertEqual(row['artifact_ceiling_seconds'],28800)
                self.assertEqual(row['budget_allocation_amendment']['amendment_id'],'fixture')
                self.assertEqual(budget.allocation_for(self.plan,'B')[0],7200)
                ledger['reservations'].append(dict(subject='B',settled=True,allocated_seconds=79055,reserved_seconds=960))
                with self.assertRaisesRegex(ValueError,'24 H100'):
                    budget.reserve(self.plan,ledger,'A',1,self.proof)
                amendment['global_h100_cap_seconds']=100000
                with self.assertRaisesRegex(ValueError,'global cap'):
                    budget.validate_allocation(self.plan,amendment,amendment['master_protocol_sha256'])

    def test_amendment_cannot_change_campaign_identity_or_ceiling_bounds(self):
        self.plan['campaign_id']='fixture'
        amendment=dict(campaign_id='other',master_protocol_sha256='abc',
            global_h100_cap_seconds=86400,artifact_ceilings_seconds={'A':28800})
        with self.assertRaisesRegex(ValueError,'frozen campaign'):
            budget.validate_allocation(self.plan,amendment,'abc')
        amendment['campaign_id']='fixture';amendment['artifact_ceilings_seconds']={'A':86401}
        with self.assertRaisesRegex(ValueError,'ceiling'):
            budget.validate_allocation(self.plan,amendment,'abc')
