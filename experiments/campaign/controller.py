"""Seven-condition orchestration over an actual, separately validated native adapter.

No execution backend or synthetic observation generator is supplied here.
An adapter's upstream_smoke must execute the inherited upstream stage runner;
native probes and production must execute the artifact, retaining raw outputs.
"""
import copy
from resai.core import digest,readiness,refine,validate

CONDITIONS={'direct_native','upstream_static','upstream_smoke_then_production',
    'resai_full','no_coverage','no_identity_freshness','no_refinement'}


def assess(condition,plan,evidence,now):
    projection=copy.deepcopy(evidence)
    if condition=='no_identity_freshness':
        # Policy-only projection: ignore plan matching, while still requiring
        # two distinct observations. Never change the retained raw evidence.
        for row in projection['attempts']:
            row['plan_hash']=digest(plan)
    decision=readiness(plan,projection,now=now)
    ignored={'coverage'} if condition=='no_coverage' else {'stale_evidence'} if condition=='no_identity_freshness' else set()
    decision['reasons']=[r for r in decision['reasons'] if r not in ignored]
    decision['ready']=not decision['reasons']
    decision['raw_evidence_hash']=digest(evidence)
    decision['policy_projection_hash']=digest(projection)
    return decision


def execute(condition,plan,adapter,clock):
    """Execute one already budget-admitted episode; outer Slurm accounting is separate.

    Adapter interface: validate_upstream(plan) -> errors; upstream_smoke(plan) ->
    {returncode, outputs_present, raw_trace}; probe(plan,index) -> a measured
    resai record; production(plan) -> native output/oracle record. All adapter
    calls are genuine executions, not receipt mutations or inferred successes.
    """
    if condition not in CONDITIONS:
        raise ValueError('unknown campaign condition')
    errors=validate(plan)
    if errors:
        raise ValueError('invalid frozen episode plan: '+','.join(errors))
    current=copy.deepcopy(plan)
    result=dict(condition=condition,initial_plan_hash=digest(plan),admitted=False,
        production_attempted=False,attempts=[],refinements=[],smoke=None,decision=None)
    if condition!='direct_native':
        errors=adapter.validate_upstream(current)
        result['upstream_errors']=errors
        if errors:
            result['decision']={'ready':False,'reasons':['upstream_static_validation']}
            return result
    if condition=='upstream_smoke_then_production':
        smoke=adapter.upstream_smoke(current)
        result['smoke']=smoke
        if smoke['returncode']!=0 or smoke['outputs_present'] is not True:
            result['decision']={'ready':False,'reasons':['upstream_smoke_failed']}
            return result
    if condition in {'resai_full','no_coverage','no_identity_freshness','no_refinement'}:
        bindings=adapter.validate_binding(current)
        result['binding_errors']=bindings
        if bindings:
            result['decision']={'ready':False,'reasons':['input_or_graph_binding']}
            return result
        evidence={'attempts':result['attempts']}
        while len(result['attempts'])<current['max_attempts']:
            record=adapter.probe(current,len(result['attempts']))
            result['attempts'].append(copy.deepcopy(record))
            decision=assess(condition,current,evidence,clock())
            result['decision']=decision
            if decision['ready']:
                break
            if record.get('status')!='ok':
                proposal=refine(current,evidence) if condition!='no_refinement' else None
                if proposal is None:
                    return result
                if proposal['scientific']!=current['scientific']:
                    raise RuntimeError('refinement changed the scientific specification')
                result['refinements'].append({'before':digest(current),'after':digest(proposal)})
                current=proposal
                continue
            if condition!='no_identity_freshness' and record.get('plan_hash')!=digest(current):
                decision['reasons'].append('plan_mismatch')
                return result
            if set(decision['reasons'])-{'two_distinct_attempts'}:
                return result
            # Once two current observations exist, a failed conjunction is a
            # block, not permission to repeatedly sample until admission.
            relevant=evidence['attempts'] if condition=='no_identity_freshness' else [r for r in evidence['attempts'] if r.get('plan_hash')==digest(current)]
            if len(relevant)>=2:
                return result
        if not result['decision'] or not result['decision']['ready']:
            return result
    result.update(admitted=True,production_attempted=True,final_plan_hash=digest(current))
    result['production']=adapter.production(current)
    return result
