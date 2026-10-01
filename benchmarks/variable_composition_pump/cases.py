"""Predeclared study matrix, no production imports."""
from itertools import product

def cases():
 rows=[]
 def add(name,group,z=.25,T=300.,P=20e6,P2=30e6,eta=.8,F=100.):
  rows.append(dict(case_id=name,group=group,inputs=dict(z=[z,1-z],T1=T,P1=P,P2=P2,eta=eta,flow=F)))
 for j,(z,T,P,eta,mode) in enumerate(product((.01,.55),(300.,350.),(20e6,25e6),(.6,1.),('floor','max'))):
  add('CORNER_'+str(j),'corner',z,T,P,P+10000 if mode=='floor' else 30e6,eta)
 for j,(z,T,P,eta) in enumerate(product((.01,.55),(300.,350.),(22.5e6,),(.8,))):add('IDENTITY_'+str(j),'identity',z,T,P,P,eta)
 for j,z in enumerate((.05,.1,.25,.4)):add('INTERIOR_'+str(j),'interior',z,325.,22.5e6,27e6,.75)
 for j,(u,v,w,e) in enumerate(((.137,.731,.419,.283),(.863,.269,.781,.917),(.419,.113,.637,.541),(.677,.887,.193,.139),(.053,.457,.913,.763),(.947,.593,.347,.397),(.311,.967,.557,.031),(.789,.037,.071,.669))):
  P=20e6+5e6*v;add('HOLDOUT_'+str(j),'holdout',.01+.54*u,300+50*w,P,P+(30e6-P)*e,.6+.4*v)
 add('EQUIMOLAR','compatibility',.5);add('NEW_CANONICAL','demonstration',.25)
 for F in (5.,17.3,200.):add('FLOW_'+str(F),'flow',F=F)
 for z in (.01,.55):add('SUBFLOOR_'+str(z),'conditioning',z,P2=20001000.)
 for z in (0.,.009,.551,.6,.65,.75,.9,1.):add('EXCLUDED_'+str(z),'composition_challenge',z,T=335.)
 add('VAPOR','phase_challenge',.25,T=400.,P=1000.,P2=2000.)
 return rows

def input_reason(i):
 if not .01<=i['z'][0]<=.55:return 'composition_scope'
 if not(300<=i['T1']<=350 and 20e6<=i['P1']<=25e6 and i['P1']<=i['P2']<=30e6 and .6<=i['eta']<=1 and 5<=i['flow']<=200):return 'input_range'
 if i['P1']!=i['P2'] and i['P2']-i['P1']<10000:return 'positive_rise_below_floor'
 return None
