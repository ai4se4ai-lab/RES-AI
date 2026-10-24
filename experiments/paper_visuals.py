"""Evidence-preserving visualizations and diagnostic tables for the manuscript."""
import csv
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# Okabe-Ito colors remain distinguishable for color-vision deficiencies and in grayscale via markers.
BLUE, ORANGE, GREEN, VERMILION, PURPLE, SKY, GRAY = '#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9', '#555555'
SERIES = [(BLUE, 'o', '-'), (VERMILION, 's', '--'), (GREEN, '^', '-.'), (PURPLE, 'D', ':'), (ORANGE, 'v', '-')]
CMAP = LinearSegmentedColormap.from_list('blocked', ['#F7F7F7', '#9ECAE1', '#08306B'])
POLICY_GROUPS = [
    ('Graph', [('missing_gpu', 'GPU request absent'), ('bad_dependency', 'Dependency invalid')]),
    ('Process', [('runtime_failure', 'Process failed')]),
    ('Outcome', [('missing_probe', 'Required probe absent'), ('malformed_output', 'Output invalid')]),
    ('Scope', [('stale_identity', 'Plan identity changed'), ('duplicate_attempt', 'Attempt ID duplicated')]),
    ('Age', [('stale_time', 'Evidence expired')]),
    ('Memory', [('oom', 'Memory limit exceeded'), ('unstable_memory', 'Memory unstable')]),
    ('Cost', [('over_budget', 'Validation budget exceeded'), ('missing_accounting', 'Accounting absent')])]
ABLATIONS = {'without_identity': r'$-$Identity', 'without_outcome': r'$-$Outcome', 'without_freshness': r'$-$Freshness',
             'without_memory': r'$-$Memory', 'without_budget': r'$-$Budget'}


def style():
    """Match the manuscript's Latin Modern typeface when the TeX installation provides it."""
    family = 'serif'
    kpsewhich = shutil.which('kpsewhich')
    if kpsewhich:
        for name in ['lmroman10-regular.otf', 'lmroman10-bold.otf', 'lmroman10-italic.otf']:
            path = subprocess.run([kpsewhich, name], capture_output=True, text=True).stdout.strip()
            if path:
                font_manager.fontManager.addfont(path)
                family = font_manager.FontProperties(fname=path).get_name()
    plt.rcParams.update({'font.family': family, 'mathtext.fontset': 'cm', 'font.size': 7.5,
        'axes.labelsize': 7.5, 'axes.titlesize': 7.5, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'legend.fontsize': 6.5, 'axes.linewidth': .6, 'xtick.major.width': .6, 'ytick.major.width': .6,
        'lines.linewidth': 1.1, 'lines.markersize': 3.2, 'pdf.fonttype': 42, 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25, 'grid.linewidth': .5})


def save(fig, out, name):
    fig.savefig(out / (name + '.pdf'), bbox_inches='tight')
    fig.savefig(out / (name + '.png'), dpi=220, bbox_inches='tight')
    plt.close(fig)


def _heat(ax, values, counts, denominators, xlabels, title):
    im = ax.imshow(values, vmin=0, vmax=1, cmap=CMAP, aspect='auto')
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=35, ha='left', rotation_mode='anchor')
    ax.xaxis.tick_top()
    ax.tick_params(length=0, pad=4)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f'{counts[i, j]}/{denominators[i, j]}', ha='center', va='center', fontsize=6.3,
                    color='white' if values[i, j] > .55 else '#222222')
    ax.set_title(title, pad=22, loc='left')
    return im


def fault_heatmap(rows, summary, labels, out, ablation_rows):
    """Blocked fraction per fault family for the comparator policies and the leave-one-out ablations."""
    faults = [f for _, fs in POLICY_GROUPS for f, _ in fs]
    assert set(faults) == {r['fault'] for r in rows if r['fault'] != 'clean'}
    counts = np.array([[sum(r['admitted'] == '0' for r in rows if r['condition'] == c and r['fault'] == f)
                        for c in labels] for f in faults])
    denominators = np.array([[sum(r['condition'] == c and r['fault'] == f for r in rows)
                              for c in labels] for f in faults])
    assert np.all(denominators == summary['seeds'])
    full = np.array([[sum(r['full'] == '0' for r in ablation_rows if r['fault'] == f)] for f in faults])
    assert np.array_equal(full[:, 0], counts[:, -1])
    ab_counts = np.array([[sum(r[k] == '0' for r in ablation_rows if r['fault'] == f) for k in ABLATIONS] for f in faults])
    ab_den = np.full_like(ab_counts, summary['seeds'])
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 4.1), sharey=True, width_ratios=[4, 5], layout='constrained')
    _heat(axes[0], counts/denominators, counts, denominators, list(labels.values()), '(a) Comparator policies')
    im = _heat(axes[1], ab_counts/ab_den, ab_counts, ab_den, [k.removeprefix('without_').title() for k in ABLATIONS],
               '(b) RES-AI with one conjunct removed')
    axes[0].set_yticks(range(len(faults)), [label for _, fs in POLICY_GROUPS for _, label in fs])
    start = 0
    for name, fs in POLICY_GROUPS:
        end = start+len(fs)
        for ax in axes:
            ax.axhline(end-.5, color='white', lw=2.5)
        axes[1].text(len(ABLATIONS)-.35, (start+end-1)/2, name, va='center', ha='left', fontsize=6.3,
                     color=GRAY, style='italic')
        start = end
    axes[1].set_xlim(-.5, len(ABLATIONS)+.45)
    cb = fig.colorbar(im, ax=axes, fraction=.03, pad=.01, shrink=.7, ticks=[0, .5, 1])
    cb.set_label('Blocked fraction of seed variants')
    cb.outline.set_linewidth(.5)
    save(fig, out, 'fault_detection')
    return faults, counts, ab_counts


def sensitivity_plot(rows, out):
    panels = [('evidence_ttl_seconds', '(a) Evidence age', 'Age of both matching records (s)', '$T={}$ s', 1),
              ('memory_limit', '(b) Memory headroom', 'Footprint scale relative to baseline input', r'$m_{{\max}}={}$', 1),
              ('stability_epsilon', '(c) Repeat stability', r'Between-attempt difference $|m_a-m_b|$', r'$\epsilon={}$', 1),
              ('budget_gpu_seconds', '(d) Validation budget', r'Charged validation time $\sum c_i$ (s)', '$C={}$ s', 1)]
    fig, axes = plt.subplots(2, 2, figsize=(5.2, 4.0), layout='constrained')
    for ax, (parameter, title, xlabel, legend, _) in zip(axes.flat, panels):
        subset = [r for r in rows if r['parameter'] == parameter]
        settings = sorted({float(r['setting']) for r in subset})
        for (color, marker, line), setting in zip(SERIES, settings):
            points = sorted((float(r['x']), int(r['admitted'])/int(r['seeds'])) for r in subset if float(r['setting']) == setting)
            x, y = zip(*points)
            label = legend.format(int(setting) if setting.is_integer() else setting)
            ax.plot(x, y, color=color, ls=line, marker=marker, markevery=max(1, len(x)//10), label=label,
                    drawstyle='default' if parameter == 'memory_limit' else 'steps-post')
        x_all = [float(r['x']) for r in subset]
        ax.axhline(1, color=GRAY, lw=.9, ls=(0, (1, 1.5)), zorder=-1)
        ax.set(xlabel=xlabel, ylim=(-.05, 1.42), xlim=(min(x_all), max(x_all)), yticks=[0, .25, .5, .75, 1])
        ax.set_title(title, loc='left')
        ax.legend(frameon=False, loc='upper center', ncol=3, handlelength=2.2, columnspacing=1.2)
    for ax in axes[:, 0]:
        ax.set_ylabel('Admitted fraction\n(20 seeds)')
    save(fig, out, 'threshold_sensitivity')


def refinement_plot(rows, out):
    batches, caps = [8, 16, 32, 64, 128], list(range(2, 9))
    invariant = [r for r in rows if r['batch_invariant'] == '1']
    ready = np.array([[sum(r['decision'] == 'ready' for r in invariant if int(r['initial_batch']) == b and int(r['max_attempts']) == k)
                       for k in caps] for b in batches])
    total = np.array([[sum(int(r['initial_batch']) == b and int(r['max_attempts']) == k for r in invariant)
                       for k in caps] for b in batches])
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.35), width_ratios=[1, 1.1], layout='constrained')
    ax = axes[0]
    im = ax.imshow(ready/total, vmin=0, vmax=1, cmap=CMAP, aspect='auto', origin='lower')
    for i in range(len(batches)):
        for j in range(len(caps)):
            ax.text(j, i, f'{ready[i, j]}', ha='center', va='center', fontsize=6.3,
                    color='white' if ready[i, j]/total[i, j] > .55 else '#222222')
    ax.set_xticks(range(len(caps)), caps)
    ax.set_yticks(range(len(batches)), batches)
    ax.set(xlabel='Attempt cap $K$', ylabel='Initial batch size')
    ax.set_title('(a) READY episodes out of 20 (batch-invariant)', loc='left')
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=.05, pad=.02, ticks=[0, .5, 1]).outline.set_linewidth(.5)
    ax = axes[1]
    for (color, marker, line), b in zip(SERIES, batches):
        mean = [np.mean([float(r['charged_seconds']) for r in invariant if int(r['initial_batch']) == b and int(r['max_attempts']) == k]) for k in caps]
        ax.plot(caps, mean, color=color, marker=marker, ls=line, label=f'batch {b}')
    ax.plot(caps, [60*k for k in caps], color=GRAY, lw=.9, ls=(0, (1, 1.5)), label='Cap $60K$ s')
    ax.set(xlabel='Attempt cap $K$', ylabel='Mean charged validation (s)', xticks=caps)
    ax.set_title('(b) Validation cost stays within the cap', loc='left')
    ax.legend(frameon=False, ncol=2, loc='upper left')
    save(fig, out, 'refinement_bounds')


def overhead_plot(rows, out, allocation_seconds):
    n = np.array([int(r['attempts']) for r in rows])
    med, q1, q3 = (np.array([float(r[k]) for r in rows]) for k in ('median_ms', 'q1_ms', 'q3_ms'))
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.0), layout='constrained')
    ax = axes[0]
    ax.fill_between(n, q1, q3, color=SKY, alpha=.35, lw=0, label='Interquartile range')
    ax.plot(n, med, color=BLUE, marker='o', label='Median')
    ax.set(xscale='log', yscale='log', xlabel='Attempt records in ledger $|E|$', ylabel='Assessment time (ms)')
    ax.set_title('(a) Readiness assessment latency', loc='left')
    ax.legend(frameon=False, loc='upper left')
    ax = axes[1]
    ratio = med/(allocation_seconds*1000)
    ax.plot(n, ratio, color=VERMILION, marker='s', ls='--')
    ax.set(xscale='log', yscale='log', xlabel='Attempt records in ledger $|E|$',
           ylabel='Fraction of one probe\nallocation (%.0f s)' % allocation_seconds)
    ax.set_title('(b) Relative to a measured Nibi probe allocation', loc='left')
    save(fig, out, 'assessment_overhead')


def gpu_diagnostics(root, out):
    records=[json.loads(p.read_text()) for p in sorted((root/'results/gpu').glob('*.json'))]
    modes=['clean','corrupt_output','missing_checkpoint','runtime_failure']
    expected={(m,r) for m in modes for r in [0,1]}
    assert len(records)==8 and {(r['mode'],r['rep']) for r in records}==expected
    indexed={(r['mode'],r['rep']):r for r in records}
    accounting=list(csv.DictReader((root/'logs/sacct.psv').open(),delimiter='|'))
    cells=[r for r in accounting if '.' not in r['JobID'] and r['JobID'].startswith('24888989_')]
    cells.sort(key=lambda r:r['JobID'])
    assert len(cells)==2 and all(r['State']=='COMPLETED' for r in cells)
    origin=min(datetime.fromisoformat(r['Submit']) for r in cells)
    intervals=[((datetime.fromisoformat(r['Start'])-origin).total_seconds(),
                (datetime.fromisoformat(r['End'])-origin).total_seconds()) for r in cells]
    for (start,end),cell in zip(intervals,cells):
        assert end-start==int(cell['ElapsedRaw'])
    events=sorted({0.,*(v for pair in intervals for v in pair)})
    t=np.array(events)
    fig,axes=plt.subplots(1,2,figsize=(5.2,2.3),layout='constrained')
    ax=axes[0]
    total=np.zeros(len(t))
    for rep,(start,end) in enumerate(intervals):
        values=np.clip(t-start,0,end-start)
        total+=values
        color,marker,line=SERIES[rep]
        ax.plot(t,values,marker=marker,ls=line,color=color,label=f'Cell {rep}')
    ax.plot(t,total,marker='D',color=GREEN,label='Total')
    queue_end=min(s for s,_ in intervals)
    ax.axvspan(0,queue_end,color='#EEEEEE',zorder=-1,lw=0)
    ax.text(queue_end*.5,max(total)*.55,f'Queued {queue_end:.0f} s\n(no allocation)',ha='center',va='center',fontsize=6.5,color=GRAY)
    ax.annotate(f'{total[-1]:.0f} instance-s',xy=(t[-1],total[-1]),xytext=(-6,-12),textcoords='offset points',ha='right',fontsize=6.5,color=GREEN)
    ax.set(xlabel='Wall time since common submission (s)',ylabel='Cumulative allocated\nMIG-instance seconds',
           xlim=(0,t[-1]+8),ylim=(-2,total[-1]*1.2))
    ax.set_title('(a) Allocation cost from Slurm accounting',loc='left')
    ax.legend(frameon=False,loc='upper left',ncol=3,handlelength=1.8)
    ax=axes[1]
    exports=[]
    for rep in (0,1):
        color,marker,line=SERIES[rep]
        times=[indexed[(m,rep)]['gpu_seconds'] for m in modes]
        cumulative=np.cumsum(times)
        ax.plot(range(1,5),cumulative,marker=marker,ls=line,color=color,label=f'Repeat {rep}')
        for i,(m,cost,value) in enumerate(zip(modes,times,cumulative),1):
            exports.append({'mode_order':i,'mode':m,'rep':rep,'process_seconds':cost,'cumulative_process_seconds':value})
        ax.annotate(f'{cumulative[-1]:.3f} s',(4,cumulative[-1]),xytext=(6,0),textcoords='offset points',va='center',fontsize=6.5,color=color)
    ax.set(xticks=range(1,5),xlabel='Probe mode (execution order)',ylabel='Cumulative timed\nprobe seconds',xlim=(.85,4.75),ylim=(0,2.25))
    ax.set_xticklabels(['Clean','Corrupt\noutput','Missing\ncheckpoint','Runtime\nfailure'])
    ax.set_title('(b) Probe computation from eight CUDA records',loc='left')
    ax.legend(frameon=False,loc='upper left')
    save(fig,out,'gpu_cost_timeline')
    assert total[-1] == sum(int(r['ElapsedRaw']) for r in cells)
    metadata={'allocation_source':'experiments/results/nibi/logs/sacct.psv',
              'probe_source':'experiments/results/nibi/results/gpu/*.json',
              'time_origin':'common submission; no timezone conversion',
              'allocated_unit':'one H100 1g.10gb MIG instance-second',
              'intervals_seconds_since_submission':intervals,
              'total_allocated_instance_seconds':float(total[-1]),
              'total_probe_process_seconds':sum(r['gpu_seconds'] for r in records),
              'comparative_savings_estimated':False}
    (out/'gpu_cost_timeline.json').write_text(json.dumps(metadata,indent=2)+'\n')
    csv_path=out/'gpu_cost_timeline.csv'
    with csv_path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(exports[0]));w.writeheader();w.writerows(exports)
    table=[r'\begin{tabularx}{\textwidth}{lrrccY}',
           r'\toprule Mode & $t_0$ (s) & $t_1$ (s) & Probes & Output & Assessment / reasons \\',r'\midrule']
    pretty={'clean':'Clean','corrupt_output':'Corrupt output','missing_checkpoint':'No checkpoint','runtime_failure':'Runtime failure'}
    reasons={'clean':'Ready','corrupt_output':'Blocked: coverage; output validity',
             'missing_checkpoint':'Blocked: coverage','runtime_failure':'Blocked: process failure; coverage; output validity'}
    for mode in modes:
        pair=[indexed[(mode,r)] for r in [0,1]]
        coverage=[len(r['passed_probes']) for r in pair]
        assert len(set(coverage))==1
        valid=sum(r['output_valid'] for r in pair)
        table.append(f"{pretty[mode]} & {pair[0]['gpu_seconds']:.3f} & {pair[1]['gpu_seconds']:.3f} & {coverage[0]}/5 & {valid}/2 & {reasons[mode]} "+r'\\')
    table += [r'\bottomrule',r'\end{tabularx}']
    (out/'gpu_diagnostics.tex').write_text('\n'.join(table)+'\n')
    return [int(r['ElapsedRaw']) for r in cells]
