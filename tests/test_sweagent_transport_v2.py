"""Regression checks for native SWE-agent cache blocks sent to Ollama."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'sweagent_transport_v2', Path(__file__).resolve().parents[1]
    / 'experiments/campaign/sweagent_transport_v2.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class NativeCacheBlockTests(unittest.TestCase):
    def test_cache_blocks_preserve_text_and_tool_links_without_mutating_history(self):
        history = [
            dict(role='user', content=[dict(type='text', text='first\n',
                 cache_control={'type': 'ephemeral'}), dict(type='text', text='second')]),
            dict(role='assistant', content=None, tool_calls=[dict(id='call_1',
                 function=dict(name='bash', arguments='{"command":"pwd"}'))]),
            dict(role='tool', tool_call_id='call_1', cache_control={'type': 'ephemeral'},
                 content=[dict(type='text', text='/testrepo\n')]),
        ]
        original = copy.deepcopy(history)
        result = transport.ollama_messages(history)
        self.assertEqual([m['content'] for m in result], ['first\nsecond', '', '/testrepo\n'])
        self.assertEqual(result[2]['tool_name'], 'bash')
        self.assertNotIn('cache_control', result[2])
        self.assertEqual(history, original)

    def test_unsupported_content_fails_before_sending_a_request(self):
        for content in ([dict(type='image_url', image_url={'url': 'example'})],
                        [dict(type='text', text=12)], 12):
            with self.assertRaises(RuntimeError):
                transport.ollama_messages([dict(role='user', content=content)])
