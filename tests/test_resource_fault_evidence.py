"""Synthetic file fixtures check rejection of ineffective or unobserved faults."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('resource_fault_evidence',Path(__file__).resolve().parents[1]/'experiments/campaign/resource_fault_evidence.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ResourceFaultEvidenceTests(unittest.TestCase):
    def test_fault_warmup_is_bounded_and_does_not_generate(self):
        spec=importlib.util.spec_from_file_location('fault_warmup',Path(__file__).resolve().parents[1]/'experiments/campaign/resource_fault_warmup_v3.py')
        warmup_module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(warmup_module)
        with tempfile.TemporaryDirectory() as temporary:
            class Model:
                out=Path(temporary)
                science={'model':'qwen3.8:27b','max_input_tokens':12288,'max_new_tokens':4096}
                requests=[]
                def request(self,path,body=None):
                    self.requests.append((path,body))
                    return {'models':[{'name':'qwen3.8:27b','size_vram':0,'size':123}]} if path=='/api/ps' else {}
            model=Model()
            with self.assertRaisesRegex(RuntimeError,'model did not load fully into GPU memory'):
                warmup_module.warmup(model)
            self.assertEqual([p for p,b in model.requests],['/api/generate','/api/ps'])
            self.assertEqual(model.requests[0][1]['prompt'],'')
            self.assertEqual(model.requests[0][1]['options']['num_batch'],32)
            self.assertEqual(model.requests[0][1]['options']['num_thread'],4)

    def test_isolation_and_real_cpu_residency_both_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'resource-isolation').mkdir()
            (root/'results/probe').mkdir(parents=True)
            log=root/'resource-isolation/ollama.log'
            log.write_text('CPU model buffer size = 123 MiB\n')
            isolation=root/'resource-isolation/device-isolation.json'
            isolation.write_text(json.dumps({'accelerator_devices':[]}))
            self.assertFalse(module.established(root))
            models=root/'results/probe/loaded-model.json'
            models.write_text(json.dumps([{'name':'qwen3.8:27b','size_vram':0}]))
            self.assertTrue(module.established(root))
            models.write_text(json.dumps([{'name':'qwen3.8:27b','size_vram':123}]))
            self.assertTrue(module.established(root))
            log.write_text('CPU model buffer size = 123 MiB\noffloaded 66/66 layers to GPU\n')
            self.assertFalse(module.established(root))
            log.write_text('CPU model buffer size = 123 MiB\n')
            models.write_text(json.dumps([{'name':'qwen3.8:27b','size_vram':0}]))
            isolation.write_text(json.dumps({'accelerator_devices':['/dev/nvidia0']}))
            self.assertFalse(module.established(root))
