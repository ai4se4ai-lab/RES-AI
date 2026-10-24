"""Transport fixtures are control checks, never model experiment observations."""
import importlib.util
from pathlib import Path
import unittest


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/'experiments/campaign'/f'{name}.py')
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


transport=module('sweagent_transport')
oracle=module('sweagent_oracle')


class NativeTransportTests(unittest.TestCase):
    def test_tool_only_response_round_trip_preserves_arguments_and_links(self):
        response=dict(done=True,done_reason='stop',prompt_eval_count=10,eval_count=5,
            message=dict(content='',tool_calls=[dict(function=dict(name='bash',arguments={'command':'echo "a\\b"'}))]))
        native=transport.native_response(response,3)
        assistant=native['choices'][0]['message']
        messages=transport.ollama_messages([assistant,dict(role='tool',content='ok',tool_call_id='call_3_0')])
        self.assertEqual(messages[0]['tool_calls'][0]['function']['arguments'],{'command':'echo "a\\b"'})
        self.assertEqual(messages[1]['tool_name'],'bash')
        self.assertEqual(response['message']['tool_calls'][0]['function']['arguments'],{'command':'echo "a\\b"'})

    def test_orphan_tool_result_and_truncated_generation_fail(self):
        with self.assertRaises(RuntimeError):
            transport.ollama_messages([dict(role='tool',content='ok',tool_call_id='unknown')])
        with self.assertRaises(RuntimeError):
            transport.native_response(dict(done=True,done_reason='length'),1)

    def test_oracle_accepts_repair_and_rejects_changed_behavior(self):
        self.assertTrue(oracle.check('def division(a: float,b: float) -> float:\n    return a/b\n'))
        for code in ['def division(a,b):\n    return a*b\n',
                     'def division(a,b):\n    return 0 if b==0 else a/b\n',
                     'def division(a,b):\n    return __import__("os").system("id")\n']:
            with self.assertRaises((ValueError,AssertionError)):
                oracle.check(code)
