"""OpenAI-shaped native tool messages over the pinned job-local Ollama API."""
import copy
import json


def ollama_messages(messages):
    result=[]
    names={}
    for original in messages:
        message=copy.deepcopy(original)
        content=message.get('content')
        if content is None:
            content=''
        elif isinstance(content,list):
            if any(not isinstance(block,dict) or block.get('type')!='text' or not isinstance(block.get('text'),str) for block in content):
                raise RuntimeError('unsupported non-text native message content')
            # SWE-agent adds Anthropic cache metadata to text blocks. Ollama's
            # native API requires a string; preserve the exact ordered text.
            content=''.join(block['text'] for block in content)
        elif not isinstance(content,str):
            raise RuntimeError('unsupported native message content')
        message['content']=content
        message.pop('cache_control',None)
        message.pop('thinking_blocks',None)
        for call in message.get('tool_calls') or []:
            function=call['function']
            if call.get('id'):
                names[call['id']]=function['name']
            if isinstance(function.get('arguments'),str):
                function['arguments']=json.loads(function['arguments'])
            if not isinstance(function.get('arguments'),dict):
                raise RuntimeError('native tool arguments must be a JSON object')
        if message['role']=='tool':
            identifier=message.get('tool_call_id')
            if identifier not in names:
                raise RuntimeError('tool result has no preceding native tool call')
            message['tool_name']=names[identifier]
        result.append(message)
    return result


def native_response(response,index):
    if not response.get('done') or response.get('done_reason')=='length':
        raise RuntimeError('incomplete native model generation')
    message=copy.deepcopy(response['message'])
    tools=[]
    for number,call in enumerate(message.get('tool_calls') or []):
        function=call['function']
        arguments=function.get('arguments',{})
        if isinstance(arguments,str):
            arguments=json.loads(arguments)
        if not isinstance(arguments,dict):
            raise RuntimeError('model tool arguments must be a JSON object')
        tools.append(dict(id=f'call_{index}_{number}',type='function',
            function=dict(name=function['name'],arguments=json.dumps(arguments))))
    content=message.get('content') or ''
    if not content.strip() and not tools:
        raise RuntimeError('empty native model response')
    inputs,outputs=response['prompt_eval_count'],response['eval_count']
    return dict(id=f'resai-local-{index}',model='openai/qwen3.8:27b',
        choices=[dict(index=0,finish_reason='tool_calls' if tools else 'stop',
            message=dict(role='assistant',content=content,tool_calls=tools or None))],
        usage=dict(prompt_tokens=inputs,completion_tokens=outputs,total_tokens=inputs+outputs))


class NativeToolTransport:
    def __init__(self,backend,max_calls):
        self.backend,self.max_calls=backend,max_calls

    def __call__(self,*args,**kwargs):
        import litellm
        if args or kwargs.get('n') not in (None,1) or kwargs.get('model')!='openai/qwen3.8:27b':
            raise RuntimeError('unsupported native model transport request')
        if len(self.backend.calls)>=self.max_calls:
            raise RuntimeError('native 32-call feasibility limit reached')
        science=self.backend.science
        body=dict(model=science['model'],messages=ollama_messages(kwargs['messages']),
            tools=kwargs.get('tools',[]),think=False,stream=False,keep_alive='10m',
            options=dict(temperature=0,seed=0,num_predict=science['max_new_tokens'],
                num_ctx=science['max_input_tokens']+science['max_new_tokens'],num_gpu=999))
        response=self.backend.request('/api/chat',body)
        self.backend.calls.append(dict(request=body,response=response))
        (self.backend.out/'calls.json').write_text(json.dumps(self.backend.calls,indent=2)+'\n')
        for key,limit in [('prompt_eval_count',science['max_input_tokens']),('eval_count',science['max_new_tokens'])]:
            if type(response.get(key)) is not int or not 0<=response[key]<=limit:
                raise RuntimeError('declared native model token envelope exceeded: '+key)
        return litellm.ModelResponse(**native_response(response,len(self.backend.calls)))
