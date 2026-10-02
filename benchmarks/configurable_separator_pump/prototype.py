"""Isolated connected-sample inverse diagnostic, not an accepted runtime solver.

No benchmark answer is used to select a bracket or set a target. Any holes remain
in diagnostics and prevent a complete-domain claim even when a local root exists.
"""
import math

def solve(evaluate,target,key,points,tolerance,xtol=1e-10):
    trials=[];samples=[];brackets=[]
    def call(t,stage):
        try:
            s=evaluate(t);v=s[key]-target
            if not math.isfinite(v):raise ValueError('nonfinite residual')
            trials.append(dict(T_K=t,stage=stage,status='success',residual=v,classification=s['classification']))
            return s,v
        except Exception as e:
            trials.append(dict(T_K=t,stage=stage,status='failed',reason=type(e).__name__+': '+str(e)))
            return None,None
    for k in range(points):
        t=200+300*k/(points-1);s,v=call(t,'scan');samples.append((t,v))
    for t,v in samples:
        if v==0:brackets.append((t,t))
    for (a,fa),(b,fb) in zip(samples,samples[1:]):
        if fa is not None and fb is not None and fa*fb<0:brackets.append((a,b))
    holes=[r for r in trials if r['status']=='failed']
    out=dict(trials=trials,brackets=brackets,coverage='incomplete' if holes else 'sampled_complete',global_uniqueness=False)
    if len(brackets)!=1:return out|dict(status='ambiguous' if brackets else 'unbracketed')
    lo,hi=brackets[0];_,fl=call(lo,'bracket');_,fh=call(hi,'bracket')
    if fl is None or fh is None:return out|dict(status='bracket_failed')
    for _ in range(100):
        if hi-lo<=xtol:break
        mid=(lo+hi)/2;_,fm=call(mid,'root')
        if fm is None:return out|dict(status='root_evaluation_failed')
        if fm==0:lo=hi=mid;fl=fh=0.;break
        if fl*fm<0:hi,fh=mid,fm
        else:lo,fl=mid,fm
    else:return out|dict(status='iteration_limit')
    t=lo if abs(fl)<=abs(fh) else hi;s,v=call(t,'fresh_final')
    if v is None or abs(v)>tolerance:return out|dict(status='fresh_residual_failed')
    return out|dict(status='local_candidate',state=s,residual=v,final_bracket=[lo,hi])
