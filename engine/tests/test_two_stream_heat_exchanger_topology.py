"""M15 contract gate: no thermodynamic implementation is used by these tests."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from riogineer_engine.core import ROOT, build_flowsheet, validate_requirements, validate_schema, Invalid
from riogineer_engine.network import execute_exchanger_graph
from riogineer_engine.network_models import MODELS, EquipmentResult


def requirements():
    old = json.loads((ROOT/'contracts/examples/milestone-6-requirements.json').read_text())
    r = {k: old[k] for k in ('kind','case_id','units','required_outputs')}
    r.update(schema_version='1.7', profile='two_stream_heat_exchanger_energy',
        provenance={'source':'M15 contract fixture','basis':'qualified_equilibrium_energy'},
        components=['methane','n_hexane'], feeds=[], sinks=[], equipment=[], streams=[], connections=[])
    p = dict(mode='specified_hot_outlet_temperature',hot_outlet_temperature_K=390.,
        hot_outlet_pressure_Pa_abs=300000.,cold_outlet_pressure_Pa_abs=100000.,property_package='peng_robinson@1.0',
        bip=dict(identifier='m15_zero@1.0',component_ids=['methane','n_hexane'],values=[[0.,0.],[0.,0.]],source='Explicit zero',model='peng_robinson@1.0'))
    r['equipment']=[dict(id='HX',type='two_stream_heat_exchanger',model=dict(id='rigorous_two_stream_pr',version='1.0'),parameters=p)]
    for side,T,P,rates in [('hot',430.,300000.,dict(methane=900.,n_hexane=100.)),('cold',300.,100000.,dict(methane=20.,n_hexane=180.))]:
        source=side.upper()+'_SOURCE';sink=side.upper()+'_SINK'
        r['feeds'].append(dict(id=source,state=dict(temperature_K=T,pressure_Pa_abs=P,component_mass_flow_kg_h=rates)))
        r['sinks'].append(dict(id=sink))
        for direction in ('in','out'):
            sid=side.upper()+'_'+direction.upper(); port=side+'_'+direction
            r['streams'].append(dict(id=sid,service=port))
            r['connections'].append(dict(id='C_'+sid,stream_id=sid,
                source=dict(owner_id=source,port_id='outlet') if direction=='in' else dict(owner_id='HX',port_id=port),
                target=dict(owner_id='HX',port_id=port) if direction=='in' else dict(owner_id=sink,port_id='inlet')))
    return r


def fake(unit, inputs, evaluate):
    return EquipmentResult({side+'_out':deepcopy(inputs[side+'_in']) for side in ('hot','cold')},0.,0.)


class FourPortGate(unittest.TestCase):
    def test_requirements_and_modes(self):
        for side in ('hot','cold'):
            r=requirements();p=r['equipment'][0]['parameters'];p.pop('hot_outlet_temperature_K');p.update(mode='specified_'+side+'_outlet_temperature');p[side+'_outlet_temperature_K']=350.
            validate_requirements(r);validate_schema('flowsheet',build_flowsheet(r))

    def test_missing_duplicate_ports_and_connections(self):
        for index in range(4):
            f=build_flowsheet(requirements());f['equipment'][0]['ports'].pop(index)
            with self.assertRaises(Invalid):execute_exchanger_graph(f)
            f=build_flowsheet(requirements());f['connections'].pop(index)
            with self.assertRaises(Invalid):execute_exchanger_graph(f)
        f=build_flowsheet(requirements());f['equipment'][0]['ports'][2]=f['equipment'][0]['ports'][0]
        with self.assertRaises(Invalid):execute_exchanger_graph(f)

    def test_independent_paths_and_no_stale_state(self):
        f=build_flowsheet(requirements());before=deepcopy(f)
        with patch.dict(MODELS['two_stream_heat_exchanger'],execute=fake):
            states,records=execute_exchanger_graph(f)
            for side in ('HOT','COLD'):self.assertEqual(states[side+'_IN'],states[side+'_OUT'])
            self.assertNotEqual(states['HOT_OUT'],states['COLD_OUT'])
            self.assertEqual(len(records),1);self.assertEqual(f,before)
            r=requirements();r['feeds'][0]['state']['temperature_K']=440.
            changed,_=execute_exchanger_graph(build_flowsheet(r))
            self.assertEqual(changed['HOT_OUT']['temperature_K'],440.)
            self.assertEqual(states['HOT_OUT']['temperature_K'],430.)

    def test_swapped_or_partial_outputs_fail_atomically(self):
        for mode in ('swap','partial','raise'):
            def wrong(u,i,e):
                r=fake(u,i,e)
                if mode=='swap':r.streams['hot_out'],r.streams['cold_out']=r.streams['cold_out'],r.streams['hot_out']
                elif mode=='partial':del r.streams['cold_out']
                else:raise ValueError('controlled failure')
                return r
            f=build_flowsheet(requirements());before=deepcopy(f)
            with patch.dict(MODELS['two_stream_heat_exchanger'],execute=wrong):
                with self.assertRaises(Invalid):execute_exchanger_graph(f)
            self.assertEqual(f,before)

    def test_two_unit_dependency_uses_both_current_outputs(self):
        r=requirements();second=deepcopy(r['equipment'][0]);second['id']='HX2';r['equipment'].insert(0,second)
        for side in ('hot','cold'):
            sid=side.upper()+'_OUT';link=next(c for c in r['connections'] if c['stream_id']==sid);sink=link['target']
            link['target']=dict(owner_id='HX2',port_id=side+'_in')
            r['streams'].append(dict(id=sid+'2',service=side+'_out2'))
            r['connections'].append(dict(id='C_'+sid+'2',stream_id=sid+'2',source=dict(owner_id='HX2',port_id=side+'_out'),target=sink))
        calls=[]
        def spy(u,i,e):calls.append(u['id']);return fake(u,i,e)
        with patch.dict(MODELS['two_stream_heat_exchanger'],execute=spy):
            states,_=execute_exchanger_graph(build_flowsheet(r))
        self.assertEqual(calls,['HX','HX2'])
        self.assertEqual(states['HOT_IN'],states['HOT_OUT2']);self.assertEqual(states['COLD_IN'],states['COLD_OUT2'])

if __name__=='__main__':
    import sys
    if '--fixture' in sys.argv:print(json.dumps(dict(requirements=requirements(),flowsheet=build_flowsheet(requirements()))))
    else:unittest.main()
