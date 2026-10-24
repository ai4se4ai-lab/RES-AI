import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('reconcile_budget',Path(__file__).resolve().parents[1]/'experiments/campaign/reconcile_budget.py')
reconciliation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconciliation)


class ReconciliationTests(unittest.TestCase):
    def test_reservation_added_during_query_is_not_lost(self):
        ledger={'reservations':[{'ticket':'old','job_id':'1','settled':False,'reserved_seconds':960},
            {'ticket':'new','job_id':'2','settled':False,'reserved_seconds':2460}]}
        updated,allocated,reserved=reconciliation.reconcile(ledger,{'1':{'State':'COMPLETED','ElapsedRaw':'200'}},'now')
        self.assertEqual(len(updated['reservations']),2)
        self.assertEqual((allocated,reserved),(200,2460))
        self.assertFalse(ledger['reservations'][0]['settled'])
    def test_old_running_snapshot_cannot_unsettle_final_accounting(self):
        ledger={'reservations':[{'ticket':'a','job_id':'1','settled':True,'allocated_seconds':238,'reserved_seconds':1260}]}
        updated,allocated,reserved=reconciliation.reconcile(ledger,{'1':{'State':'RUNNING','ElapsedRaw':'100'}},'now')
        self.assertEqual((allocated,reserved),(238,0))
        self.assertTrue(updated['reservations'][0]['settled'])
