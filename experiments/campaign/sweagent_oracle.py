"""Independent restricted oracle for the official division syntax-repair fixture."""
import ast
import json
import sys


def check(source):
    tree=ast.parse(source)
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='division']
    if len(functions)!=1:
        raise ValueError('exactly one division function required')
    function=functions[0]
    if function.decorator_list or function.args.defaults or function.args.kw_defaults or function.args.vararg or function.args.kwarg:
        raise ValueError('unsupported function definition')
    if len(function.args.args)!=2 or function.args.posonlyargs or function.args.kwonlyargs:
        raise ValueError('unexpected division signature')
    function.returns=None
    for argument in function.args.args:
        argument.annotation=None
    allowed=(ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.BinOp,ast.Div,ast.Name,ast.Load,ast.Constant,
        ast.Expr,ast.If,ast.Compare,ast.Eq,ast.NotEq,ast.Raise,ast.Call,ast.UnaryOp,ast.USub)
    names={arg.arg for arg in function.args.args}|{'ZeroDivisionError'}
    for node in ast.walk(function):
        if not isinstance(node,allowed):
            raise ValueError('unsupported oracle syntax: '+type(node).__name__)
        if isinstance(node,ast.Name) and node.id not in names:
            raise ValueError('unsupported oracle name')
        if isinstance(node,ast.Call) and not (isinstance(node.func,ast.Name) and node.func.id=='ZeroDivisionError'):
            raise ValueError('unsupported oracle call')
    module=ast.Module(body=[function],type_ignores=[])
    namespace={'__builtins__':{'ZeroDivisionError':ZeroDivisionError}}
    exec(compile(module,'<division-oracle>','exec'),namespace)
    for a,b in ((123,15),(0,7),(-9,2),(9,-2),(1.5,.5),(10,4)):
        result=namespace['division'](a,b)
        if type(result) not in (int,float) or result!=a/b:
            raise AssertionError('division result mismatch')
    try:
        namespace['division'](1,0)
    except ZeroDivisionError:
        return True
    raise AssertionError('division by zero no longer raises ZeroDivisionError')


if __name__=='__main__':
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    check(json.loads(sys.stdin.read())['source'])
