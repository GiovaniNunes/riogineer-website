"""M19 real canonical/identity checks and explicitly synthetic failure injection."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json, unittest
from unittest.mock import patch
from types import SimpleNamespace
from riogineer_engine import variable_pump_energy as m
from riogineer_engine.milestone19 import requirements
from riogineer_engine.network_models import state_from_rates
from riogineer_engine.core import build_flowsheet,calculate,validate_requirements,Invalid
from riogineer_engine.property_packages import property_package


def unit_feed(**kw):
    r=requirements(**kw);u=r['equipment'][0];s=r['feeds'][0]['state']
    return dict(u,operating_parameters=u['parameters']),state_from_rates(s['component_mass_flow_kg_h'],s['temperature_K'],s['pressure_Pa_abs'],None)


class PumpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.u,cls.feed=unit_feed();cls.provider=property_package('peng_robinson@1.0')
        cls.bip=m.parameters(cls.u['operating_parameters']);molecular,_=m.inlet_specification(cls.feed,cls.u['operating_parameters'])
        cls.state=replace(molecular,provenance=m.StateSpecificationProvenance('peng_robinson@1.0',cls.bip.identifier,'component_mass_flow_kg_h'))
        cls.pt=cls.provider.equilibrium_caloric_PT(cls.state,cls.bip,m.SolverSettings.high_accuracy())
        cls.psspec=m.PSSpecification(30e6,cls.pt.aggregate.s_J_mol_K,cls.state.composition,cls.state.provenance)
        cls.ps=cls.provider.flash_PS(cls.psspec,cls.bip)
        cls.phspec=m.PHSpecification(30e6,cls.pt.aggregate.h_J_mol+(cls.ps.caloric.aggregate.h_J_mol-cls.pt.aggregate.h_J_mol)/.8,cls.state.composition,cls.state.provenance)
        cls.ph=cls.provider.flash_PH(cls.phspec,cls.bip)

    def test_canonical_adapter_and_molecular_table(self):
        r=calculate(build_flowsheet(requirements()));d=r['equipment'][0]['thermodynamics']
        self.assertEqual(r['schema_version'],'1.13');self.assertAlmostEqual(d['actual_outlet']['temperature_K'],304.0978037329853,places=7)
        self.assertAlmostEqual(d['fluid_power_W'],132548.17411927288,places=5)
        for s in r['streams'].values():
            self.assertAlmostEqual(s['properties']['molar_flow']['value'],360.)
            self.assertAlmostEqual(s['properties']['molecular_mass']['value'],68.64222)
            self.assertEqual(s['properties']['molar_composition']['value'],dict(methane=.25,n_hexane=.75))
            self.assertIsNone(s['properties']['density']['value'])
        self.assertEqual(r['streams']['PUMP_PRODUCT']['component_mass_flow_kg_h'],self.feed['component_mass_flow_kg_h'])

    def test_identity_never_calls_inverse_and_has_one_witness(self):
        u,feed=unit_feed(Pout=20e6)
        with patch.object(type(self.provider),'flash_PS',side_effect=AssertionError('unnecessary PS')),patch.object(type(self.provider),'flash_PH',side_effect=AssertionError('unnecessary PH')):
            r=m.pump(u,{'inlet':feed})
        d=r.details['thermodynamics'];self.assertIsNone(d['isentropic_outlet']);self.assertIsNone(d['reconstructed_efficiency'])
        self.assertEqual(d['actual_outlet'],d['inlet']);self.assertEqual(len(d['witnesses']),1)
        self.assertEqual(d['ps'],dict(status='not_applicable'));self.assertEqual(r.work_W,0)
        self.assertEqual(r.streams['outlet']['temperature_K'],300)
        calculate(build_flowsheet(requirements(Pout=20e6)))

    def test_representation_roundoff_without_recipe_or_rate_overwrite(self):
        for F in (5.,17.3,100.,200.):
            u,s=unit_feed(F=F);original=deepcopy(s);state,actual=m.inlet_specification(s,u['operating_parameters'])
            self.assertAlmostEqual(actual,F,places=12);self.assertEqual(s,original)
        for z in ((.009,.991),(.551,.449),(0.,1.),(1.,0.),(.9,.1)):
            u,s=unit_feed(z=z)
            with self.assertRaisesRegex(m.PumpFailure,'composition_scope'):m.pump(u,{'inlet':s})
        u,s=unit_feed();s['component_mass_flow_kg_h']=dict(methane=100,n_hexane=100);s['mass_flow_kg_h']=200
        with self.assertRaisesRegex(m.PumpFailure,'composition_scope'):m.pump(u,{'inlet':s})

    def test_out_of_scope_scalar_inputs(self):
        for kw in (dict(Tin=299.999),dict(Tin=350.001),dict(Pin=19e6),dict(Pin=25e6+1),dict(Pout=30e6+1),dict(Pout=20e6-1),dict(Pout=20e6+9999.999999),dict(eta=.59999),dict(eta=1.0001),dict(F=4.999999999),dict(F=200.0000001),dict(Tin=float('nan'))):
            with self.subTest(kw=kw):
                u,s=unit_feed(**kw)
                with self.assertRaises(m.PumpFailure):m.pump(u,{'inlet':s})
                with self.assertRaises((Invalid,ValueError)):validate_requirements(requirements(**kw))

    def test_exact_pressure_equality_not_epsilon(self):
        u,s=unit_feed(Pout=20000000.000000004)
        with self.assertRaisesRegex(m.PumpFailure,'below_floor'):m.pump(u,{'inlet':s})
        u,s=unit_feed(Pout=20010000.);m.inlet_specification(s,u['operating_parameters'])

    def test_independent_caloric_input_and_invalid_payload(self):
        for field,value in [('enthalpy_flow_W',0.),('H_eq_J_mol',1.),('entropy_J_mol_K',1.)]:
            s=dict(self.feed,**{field:value})
            with self.assertRaisesRegex(m.PumpFailure,'independent_caloric_input'):m.pump(self.u,{'inlet':s})
        for field in ('enthalpy_flow_W','entropy_J_mol_K'):
            r=requirements();r['feeds'][0]['state'][field]=0
            with self.assertRaises(Invalid):validate_requirements(r)

    def test_model_bip_and_parameter_contract(self):
        for key,value in [('isentropic_efficiency',False),('outlet_pressure_Pa_abs',float('inf')),('extra',0),('property_package','unknown')]:
            p=deepcopy(self.u['operating_parameters']);p[key]=value
            with self.assertRaises(m.PumpFailure):m.parameters(p)
        p=deepcopy(self.u['operating_parameters']);p['bip']['values']=[[0,.01],[.01,0]]
        with self.assertRaises(m.PumpFailure):m.parameters(p)

    def test_topology_rejects_disconnected_cycle_duplicate_ports(self):
        for mutation in ('reverse','duplicate','missing','mixed'):
            r=requirements()
            if mutation=='reverse':r['connections'][0]['target']['port_id']='outlet'
            if mutation=='duplicate':r['connections'][1]['stream_id']=r['connections'][0]['stream_id']
            if mutation=='missing':r['connections'].pop()
            if mutation=='mixed':r['equipment'][0]['type']='compressor'
            with self.assertRaises(Invalid):build_flowsheet(r)

    def test_synthetic_phase_payload_guard_injections(self):
        pt=self.pt.equilibrium;d=pt.diagnostics
        variants=[replace(self.pt,status='failed'),replace(self.pt,aggregate=None),replace(self.pt,equilibrium=replace(pt,classification='single_vapor')),
            replace(self.pt,equilibrium=replace(pt,diagnostics=replace(d,stability=None))),
            replace(self.pt,equilibrium=replace(pt,diagnostics=replace(d,stability=replace(d.stability,stable=False)))),
            replace(self.pt,equilibrium=replace(pt,diagnostics=replace(d,stability=replace(d.stability,converged=False)))),
            replace(self.pt,equilibrium=replace(pt,diagnostics=replace(d,stability=replace(d.stability,phase_identification_parameter=1.)))),
            replace(self.pt,equilibrium=replace(pt,diagnostics=replace(d,stability=replace(d.stability,phase_identification_parameter=float('nan'))))),
            replace(self.pt,equilibrium=replace(pt,overall_state=replace(self.state,pressure_Pa_abs=21e6))),
            replace(self.pt,aggregate=replace(self.pt.aggregate,h_J_mol=float('nan'))),
            replace(self.pt,phases=()),replace(self.pt,equilibrium=replace(pt,phases=(replace(pt.phases[0],composition=(.4,.6)),))),
            replace(self.pt,equilibrium=replace(pt,provenance=replace(pt.provenance,settings=m.SolverSettings())))]
        for v in variants:
            with self.subTest(v=v.status),self.assertRaises(m.PumpFailure):m.accepted(v,self.state,self.bip,'synthetic')

    def test_synthetic_missing_ambiguous_inconsistent_inverse_diagnostics(self):
        for r,spec,key in ((self.ps,self.psspec,'PS'),(self.ph,self.phspec,'PH')):
            d=r.diagnostics
            variants=[replace(r,status='failed'),replace(r,caloric=None),replace(r,diagnostics=replace(d,brackets_K=d.brackets_K*2)),
                replace(r,diagnostics=replace(d,trials=d.trials[:-1])),replace(r,diagnostics=replace(d,trials=d.trials[1:])),
                replace(r,diagnostics=replace(d,settings=replace(d.settings,temperature_bounds_K=(250.,400.)))),
                replace(r,temperature_K=r.temperature_K+1),replace(r,diagnostics=replace(d,pt_settings=m.SolverSettings())),
                replace(r,diagnostics=replace(d,trials=d.trials+(d.trials[-1],)))]
            for v in variants:
                with self.subTest(key=key),self.assertRaises(m.PumpFailure):m.inverse(v,spec,key)

    def test_synthetic_ps_holes_and_ph_valid_intervals(self):
        for r,spec,key in ((self.ps,self.psspec,'PS'),(self.ph,self.phspec,'PH')):
            d=r.diagnostics;trials=list(d.trials);trials[0]=replace(trials[0],status='pt_evaluation_failure')
            altered=replace(r,diagnostics=replace(d,trials=tuple(trials)))
            if key=='PS':
                with self.assertRaises(m.PumpFailure):m.inverse(altered,spec,key)
            else:self.assertEqual(m.inverse(altered,spec,key)['failure_count'],1)
            trials=list(d.trials);idx=next(j for j,t in enumerate(trials) if t.temperature_K==d.selected_bracket_K[0]);trials[idx]=replace(trials[idx],status='pt_evaluation_failure')
            with self.assertRaises(m.PumpFailure):m.inverse(replace(r,diagnostics=replace(d,trials=tuple(trials))),spec,key)

    def test_synthetic_witness_failure_is_atomic(self):
        real=self.provider.equilibrium_caloric_PT
        def fail(state,bip,settings):
            c=real(state,bip,settings)
            return replace(c,status='synthetic_witness_failure') if state.pressure_Pa_abs==16e6 else c
        with patch.object(type(self.provider),'equilibrium_caloric_PT',side_effect=fail):
            with self.assertRaisesRegex(m.PumpFailure,'inlet_witness'):m.pump(self.u,{'inlet':self.feed})
            with self.assertRaisesRegex(Invalid,'inlet_witness'):calculate(build_flowsheet(requirements()))

    def test_synthetic_work_and_entropy_guards(self):
        # Keep solver checks independently covered above; isolate work-screen policy.
        def run(hs,h2,s2,eta=.8):
            u=deepcopy(self.u);u['operating_parameters']['isentropic_efficiency']=eta
            def fake_accepted(c,expected,bip,stage,witness=False):
                from riogineer_engine.compressor_energy import caloric_state
                out=caloric_state(c)
                if not witness and stage=='isentropic':out['H_eq_J_mol']=hs;out['S_eq_J_mol_K']=self.pt.aggregate.s_J_mol_K
                if not witness and stage=='outlet':out['H_eq_J_mol']=h2;out['S_eq_J_mol_K']=s2
                return out
            provider=SimpleNamespace(equilibrium_caloric_PT=lambda *a:self.pt,flash_PS=lambda *a:self.ps,flash_PH=lambda *a:self.ph)
            with patch.object(m,'property_package',return_value=provider),patch.object(m,'accepted',side_effect=fake_accepted),patch.object(m,'inverse',return_value={}):
                return m.pump(u,{'inlet':self.feed})
        h=self.pt.aggregate.h_J_mol;s=self.pt.aggregate.s_J_mol_K
        for hs,h2,s2,status in [(h,h+1,s,'nonpositive'),(h+.001,h+.001/.8,s,'unresolved_work'),(h+1,h+1.25,s-1,'entropy_generation'),(h+1,h+2,s,'inverse_residual')]:
            with self.assertRaisesRegex(m.PumpFailure,status):run(hs,h2,s2)
        with self.assertRaisesRegex(m.PumpFailure,'ideal_efficiency'):run(h+1,h+1,s,eta=1.)

    def test_synthetic_inverse_failures_are_atomic(self):
        for key in ('PS','PH'):
            provider=SimpleNamespace(equilibrium_caloric_PT=self.provider.equilibrium_caloric_PT,
                flash_PS=lambda *a:replace(self.ps,status='synthetic_failure') if key=='PS' else self.ps,
                flash_PH=lambda *a:replace(self.ph,status='synthetic_failure'))
            with patch.object(m,'property_package',return_value=provider):
                with self.assertRaisesRegex(m.PumpFailure,key+': synthetic_failure'):m.pump(self.u,{'inlet':self.feed})
                with self.assertRaisesRegex(Invalid,key+': synthetic_failure'):calculate(build_flowsheet(requirements()))

    def test_synthetic_later_witness_failures_are_atomic(self):
        for fail_at in (2,3):
            count=[0]
            def pt(state,bip,settings):
                c=self.provider.equilibrium_caloric_PT(state,bip,settings)
                if state.pressure_Pa_abs==16e6:
                    count[0]+=1
                    if count[0]==fail_at:return replace(c,status='synthetic_witness_failure')
                return c
            provider=SimpleNamespace(equilibrium_caloric_PT=pt,flash_PS=lambda *a:self.ps,flash_PH=lambda *a:self.ph)
            with patch.object(m,'property_package',return_value=provider):
                with self.assertRaisesRegex(m.PumpFailure,('isentropic' if fail_at==2 else 'outlet')+'_witness'):
                    m.pump(self.u,{'inlet':self.feed})

    def test_version_isolation_and_equimolar_compatibility(self):
        from riogineer_engine.milestone18 import requirements as old
        a=calculate(build_flowsheet(old()))
        b=calculate(build_flowsheet(requirements(z=(.5,.5))))
        self.assertEqual(a['equipment'][0]['thermodynamics'],b['equipment'][0]['thermodynamics'])
        self.assertEqual(a['streams'],b['streams'])
        r=requirements();r['equipment'][0]['model']['version']='1.0'
        with self.assertRaises(Invalid):build_flowsheet(r)
        with self.assertRaises(Invalid):build_flowsheet(old(z=(.25,.75)))

    def test_supported_bounds_and_no_clipping(self):
        for z in (.01,.010001,.05473,.5,.55):
            u,s=unit_feed(z=(z,1-z));original=deepcopy(s)
            state,F=m.inlet_specification(s,u['operating_parameters'])
            self.assertAlmostEqual(state.composition.molar_fractions['methane'],z,places=14)
            self.assertEqual(s,original)
        for z in (.01-1e-10,.55+1e-10):
            u,s=unit_feed(z=(z,1-z))
            with self.assertRaisesRegex(m.PumpFailure,'composition_scope'):m.pump(u,{'inlet':s})

    def test_ui_fixture_matches_cli(self):
        p=Path(__file__).resolve().parents[2]/'contracts/examples/milestone-19-pump-requirements.json'
        self.assertEqual(json.loads(p.read_text()),requirements())

if __name__=='__main__':unittest.main()
