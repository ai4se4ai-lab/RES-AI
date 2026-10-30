"""Status fixtures verify completion reporting; these are not experiment data."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('status_updater',Path(__file__).resolve().parents[1]/'experiments/update_project_status.py')
updater=importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class CampaignCompletionTests(unittest.TestCase):
    def fixture(self):
        subject=dict(name='fixture',native_validation_passed=True)
        rows=[dict(episode_id=str(i),job_id=str(i),status='PRODUCTION_VALID') for i in range(2)]
        campaign=dict(potential_episodes=2,subjects=[subject],comparative_subsets={'fixture':dict(
            status='SUBSET_RESOLVED',comparative_episodes_completed=2,queue=rows)},
            gpu_budget_ledger={'reservations':[dict(subject='fixture',settled=True)]})
        return subject,campaign

    def test_native_pass_does_not_complete_campaign(self):
        subject,campaign=self.fixture()
        campaign['comparative_subsets']={}
        self.assertEqual(updater.candidate_campaign_status(subject,campaign,True),'NOT STARTED')

    def test_budget_stop_is_not_completion(self):
        subject,campaign=self.fixture()
        campaign['comparative_subsets']['fixture']['status']='INITIAL_BUDGET_LIMITED'
        self.assertEqual(updater.candidate_campaign_status(subject,campaign,True),'BUDGET LIMITED')

    def test_quarantine_prevents_completion(self):
        subject,campaign=self.fixture()
        campaign['comparative_subsets']['fixture']['quarantined_episodes']=1
        self.assertEqual(updater.candidate_campaign_status(subject,campaign,True),'STOPPED FOR AUDIT')

    def test_missing_collected_receipts_prevents_completion(self):
        subject,campaign=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(updater.candidate_campaign_status(subject,campaign,True,Path(directory)),
                'COLLECTION / ACCOUNTING PENDING')

    def test_complete_requires_receipts_integrity_and_settled_accounting(self):
        subject,campaign=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for row in campaign['comparative_subsets']['fixture']['queue']:
                p=root/'experiments/results/campaign/comparison'/row['job_id']/'episode.json'
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps(dict(row,artifact='fixture')))
            self.assertEqual(updater.candidate_campaign_status(subject,campaign,True,root),'COMPLETE')
            self.assertNotEqual(updater.candidate_campaign_status(subject,campaign,False,root),'COMPLETE')
            campaign['gpu_budget_ledger']['reservations'][0]['settled']=False
            self.assertNotEqual(updater.candidate_campaign_status(subject,campaign,True,root),'COMPLETE')

    def test_completion_accepts_collected_receipts_across_protocol_revisions(self):
        subject,campaign=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for folder,row in zip(('comparison','comparison-v2'),campaign['comparative_subsets']['fixture']['queue']):
                p=root/'experiments/results/campaign'/folder/row['job_id']/'episode.json'
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps(dict(row,artifact='fixture')))
            self.assertEqual(updater.candidate_campaign_status(subject,campaign,True,root),'COMPLETE')
            p.write_text(json.dumps(dict(row,artifact='fixture',status='PRODUCTION_INVALID')))
            self.assertEqual(updater.candidate_campaign_status(subject,campaign,True,root),'COLLECTION / ACCOUNTING PENDING')
