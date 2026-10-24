import importlib.util
from pathlib import Path
import unittest

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
