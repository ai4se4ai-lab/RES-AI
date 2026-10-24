"""Generate the hierarchical RES-AI architecture as vector PDF artwork."""
from pathlib import Path
import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white

OUT = Path(__file__).resolve().parents[1] / 'docs/EMSE/generated/approach_overview.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUT), pagesize=(690, 680), invariant=1)
c.setTitle('RES-AI: components, contracts and decision paths')
c.translate(0, 10)
NAVY, TEAL, BLUE, ORANGE, GRAY = map(HexColor, ['#19344B','#007F82','#426FA2','#B56820','#536574'])


def text(x,y,s,size=12,color=NAVY,bold=False,align='left'):
    c.setFillColor(color)
    c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
    getattr(c, {'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x,y,s)


def rect(x,y,w,h,fill='#F3F7FA',stroke='#C9D8E2',radius=6):
    c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.setLineWidth(.8)
    c.roundRect(x,y,w,h,radius,fill=1,stroke=1)


def panel(x,y,n,title,color=BLUE):
    rect(x,y,276,144,fill='#F5F8FB')
    c.setFillColor(color);c.roundRect(x,y+105,276,39,6,fill=1,stroke=0)
    c.rect(x,y+105,276,15,fill=1,stroke=0)
    c.setFillColor(white);c.circle(x+20,y+125,10,fill=1,stroke=0)
    text(x+20,y+121,str(n),12,color,True,'center')
    text(x+38,y+120,title,16,white,True)


def mini(x,y,w,h,title,body,color=BLUE):
    rect(x,y,w,h,fill='#FFFFFF',stroke='#D5E1E9',radius=4)
    text(x+8,y+h-15,title,13.6,color,True)
    for i,line in enumerate(body):text(x+8,y+h-30-14*i,line,13.6)


def pill(x,y,w,s,fill='#E5F2F2',color=TEAL,size=11):
    rect(x,y,w,21,fill=fill,stroke=fill,radius=4)
    text(x+w/2,y+6,s,size,color,True,'center')


def arrow(points,label='',lx=0,ly=0,dashed=False):
    color=ORANGE if dashed else TEAL
    c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(1.5)
    c.setDash(5,3) if dashed else c.setDash()
    p=c.beginPath();p.moveTo(*points[0])
    for point in points[1:]:p.lineTo(*point)
    c.drawPath(p);c.setDash()
    x,y=points[-1];px,py=points[-2];a=math.atan2(y-py,x-px)
    p=c.beginPath();p.moveTo(x,y)
    for d in [-.4,.4]:p.lineTo(x-8*math.cos(a+d),y-8*math.sin(a+d))
    p.close();c.drawPath(p,fill=1,stroke=0)
    if label:
        width=c.stringWidth(label,'Helvetica',13.6)
        c.setFillColor(white);c.rect(lx-width/2-2,ly-3,width+4,15,fill=1,stroke=0)
        text(lx,ly,label,13.6,GRAY,align='center')

# Restricted assessment access and human control are visible above the workflow.
rect(50,617,620,38,fill='#EAF0F6',stroke='#CBD9E4')
pill(59,625,51,'MCP',fill='#426FA2',color=white)
text(119,632,'snapshot | assess | propose',13.6,BLUE,True)
text(658,632,'Operator: run | review | submit',13.6,NAVY,True,'right')
text(360,602,'Agent observes / proposes; operator executes / submits',13.6,GRAY,align='center')

panel(50,430,1,'Experiment contract')
mini(62,476,122,53,'S  Science',['Model / data','Prompts / seeds'])
mini(192,476,122,53,'X  Execution',['GPU / memory','Batch / walltime'])
text(64,459,'O: probes   B: limits   I: input hashes',13.6)
pill(64,435,248,'Identity: h = H(S, X, O, B, I)',fill='#E6EDF6',color=BLUE,size=13.6)

panel(394,430,2,'Cluster observations')
mini(406,477,252,52,'Scheduler discovery',['Nodes / partitions / topology','Status + timestamp -> G_t'])
# A small advertised topology motif; not a measured network.
for px in [418,444,470]:
    rect(px,446,17,15,fill='#E3EDF8',stroke='#A7BED7',radius=2)
    c.setStrokeColor(BLUE);c.line(px+8.5,461,px+8.5,469)
c.line(426.5,469,478.5,469)
text(501,452,'Unknown metrics',13.6)
text(501,438,'stay unknown',13.6)

panel(50,239,3,'Bounded smoke execution')
for xx,title,body in [(62,'Graph',['Matrix','DAG']), (148,'Probes',['Adapter','Oracle']), (234,'Runner',['Slurm','GPU guard'])]:
    mini(xx,282,80,52,title,body)
text(64,266,'Inherited use-hpc execution',13.6,BLUE,True)
text(64,249,'Time limits | guard | audit records',13.6)

panel(394,239,4,'Attempt evidence ledger')
rect(406,279,252,55,fill='#FFFFFF',stroke='#D5E1E9',radius=4)
text(416,318,'attempt ID | plan h | status | cost',13.6,BLUE,True)
c.setStrokeColor(HexColor('#E0E7EC'));c.line(414,310,650,310)
text(416,294,'Fresh / failed / obsolete attempts',13.6)
pill(406,249,121,'Coverage / output',size=13)
pill(537,249,121,'Memory / time',size=13.6)

panel(50,48,5,'Readiness + refinement',TEAL)
mini(62,93,252,55,'Assess P against E',[
    'Identity | coverage | valid outputs',
    'Freshness | repeats | memory | budget'],TEAL)
pill(62,59,252,'Propose: halve batch if invariant OOM',fill='#FAEDDC',color=ORANGE,size=13)

panel(394,48,6,'Guarded dispatch',TEAL)
text(410,133,'1  Reassess P + E',13.6)
text(410,115,'2  Verify files + graph',13.6)
text(410,97,'3  Resources; fail -> BLOCKED',13.6)
pill(406,59,116,'DRY RUN',size=13.6)
pill(532,59,126,'SUBMIT (explicit)',fill='#E6EDF6',color=BLUE,size=13)

arrow([(532,574),(532,588),(188,588),(188,574)],'G_t informs reviewed X',360,584)
arrow([(188,430),(188,383)],'P, h and mandatory probes',195,405)
arrow([(326,311),(394,311)],'e_i',360,322)
arrow([(532,239),(532,215),(188,215),(188,192)],'E: all attempts, including failures',360,209)
arrow([(326,120),(394,120)],'READY',360,132)
arrow([(50,115),(26,115),(26,493),(50,493)],dashed=True)
c.saveState();c.translate(17,307);c.rotate(90)
text(0,0,'Proposal -> review -> new h -> fresh probes',13.6,ORANGE,align='center')
c.restoreState()
arrow([(188,48),(188,30)],'BLOCKED: missing / invalid evidence',188,14)
arrow([(532,48),(532,30)],'PASS: dry run / submit via use-hpc',532,14)
text(350,-3,'Solid: data / decisions    Dashed: reviewed revision; fresh evidence required',13,GRAY,align='center')
c.showPage();c.save()
print(OUT)
