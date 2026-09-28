"""Standalone M8 regression; independent references plus recomputed closure."""
import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import json
from math import exp, isfinite, log
from pathlib import Path
import unittest
from unittest.mock import patch
from test_pr_eos import BIP, IDS, REFERENCE, eos
from riogineer_engine.pr_eos import BinaryInteractions, MODEL, ThermodynamicError, safe_exp
from riogineer_engine.pr_flash import SolverSettings, wilson
from riogineer_engine.property_packages import PengRobinsonProvider, property_package
from riogineer_engine.pr_stability import stability
from riogineer_engine.rachford_rice import solve_rr, residual, reconstruct
from riogineer_engine.thermodynamics import ThermodynamicState, MolarComposition, StateSpecificationProvenance, MolecularCompositionProvider


def state(t=300.,p=300000.,z=(.5,.5),ids=IDS,bip=BIP):
    return ThermodynamicState(t,p,MolarComposition(ids,z),StateSpecificationProvenance(MODEL,bip.identifier))


def flash(s=None,bip=BIP,settings=SolverSettings()):
    return PengRobinsonProvider().flash_PT(s or state(),bip,settings)


class RRTests(unittest.TestCase):
    def test_frozen_K_isolated(self):
        b=REFERENCE['cases'][1]; r=solve_rr(b['z'],b['K'])
        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.beta,b['beta'],delta=1e-9)
        self.assertLess(abs(r.residual),1e-10)
        x,y,sums,m=reconstruct(b['z'],b['K'],r.beta)
        self.assertLess(max(abs(v) for v in sums),1e-12)
        self.assertLess(max(abs(v) for v in m),1e-10)
        self.assertAlmostEqual(x[0],b['liquid']['composition'][0],delta=1e-9)

    def test_endpoint_tendencies_are_not_stability(self):
        self.assertEqual(solve_rr((.5,.5),(.1,.2)).status,'liquid_tendency')
        self.assertEqual(solve_rr((.5,.5),(2,3)).status,'vapor_tendency')

    def test_invalid_domains(self):
        for k in [(0,1),(-1,1),(float('inf'),1),(1,)]:
            with self.assertRaises(ThermodynamicError): solve_rr((.5,.5),k)
        with self.assertRaises(ThermodynamicError): residual((.5,.5),(0,1),1.)
        with self.assertRaises(ThermodynamicError): residual((.5,.5),(2,.1),1.1)
        with self.assertRaises(ThermodynamicError): reconstruct((.5,.5),(50,.1),.2)

    def test_iteration_failure(self):
        r=solve_rr((.5,.5),REFERENCE['cases'][1]['K'],1)
        self.assertFalse(r.converged); self.assertIsNone(r.beta)


class StabilityTests(unittest.TestCase):
    def test_frozen_classifications_and_tpd(self):
        for c,label in zip(REFERENCE['cases'],('single_liquid','vapor_liquid','single_vapor')):
            r=stability(eos(c['T_K'],c['P_Pa_abs']),c['z'])
            self.assertTrue(r.converged)
            self.assertEqual(r.classification,label)
            self.assertEqual(r.stable,c['stability']['homogeneous_feed_stable'])
            self.assertAlmostEqual(r.minimum_tpd_RT,c['stability']['binary_TPD_scan']['refined_min_TPD_RT'],delta=1e-9)
            self.assertTrue(all(t.converged for t in r.trials))

    def test_nonconvergence_never_classifies(self):
        r=stability(eos(),(.5,.5),1)
        self.assertFalse(r.converged); self.assertIsNone(r.stable); self.assertIsNone(r.classification)

    def test_common_tangent(self):
        c=REFERENCE['cases'][1]
        tangent=tuple(log(x)+lp for x,lp in zip(c['liquid']['composition'],c['liquid']['ln_phi']))
        r=stability(eos(),(.5,.5),reference_potentials=tangent)
        self.assertTrue(r.stable); self.assertIsNone(r.classification)
        self.assertGreaterEqual(r.minimum_tpd_RT,-1e-9)


class FlashTests(unittest.TestCase):
    def close(self,actual,expected,quantity):
        t=REFERENCE['acceptance_tolerances'][quantity]
        self.assertLessEqual(abs(actual-expected),t['atol']+t['rtol']*abs(expected))

    def test_cases_abc_frozen(self):
        for c,label in zip(REFERENCE['cases'],('single_liquid','vapor_liquid','single_vapor')):
            r=flash(state(c['T_K'],c['P_Pa_abs'],c['z']))
            self.assertEqual(r.classification,label)
            self.assertEqual(r.status,'success_two_phase' if label=='vapor_liquid' else 'success_single_phase')
            self.close(r.beta,c['beta'],'beta')
            self.assertEqual(len(r.phases),2 if label=='vapor_liquid' else 1)
            for phase in r.phases:
                ref=c[phase.identifier]
                self.close(phase.Z,ref['Z'],'Z_roots')
                for x,y in zip(phase.composition,ref['composition']): self.close(x,y,'x' if phase.identifier=='liquid' else 'y')
                for x,y in zip(phase.ln_phi,ref['ln_phi']): self.close(x,y,'ln_phi')
                for phi,refphi,lp in zip(phase.phi,ref['phi'],ref['ln_phi']):
                    tol=REFERENCE['acceptance_tolerances']['ln_phi']
                    self.assertLessEqual(abs(phi-refphi),refphi*(exp(tol['atol']+tol['rtol']*abs(lp))-1))
            json.dumps(asdict(r),allow_nan=False)

    def test_independent_returned_equilibrium_closure(self):
        r=flash(); l,v=r.phases
        self.assertLessEqual(abs(sum(l.composition)-1),1e-12)
        self.assertLessEqual(abs(sum(v.composition)-1),1e-12)
        for x,y,pl,pv in zip(l.composition,v.composition,l.phi,v.phi):
            self.assertLessEqual(abs(log(x*pl)-log(y*pv)),1e-9)
            self.assertLessEqual(abs((1-r.beta)*x+r.beta*y-.5),1e-10)
        rr=sum(.5*(k-1)/(1+r.beta*(k-1)) for k in r.final_K)
        self.assertLess(abs(rr),1e-10)
        self.assertTrue(r.diagnostics.equilibrium_stability.stable)
        self.assertTrue(0 < r.beta < 1)
        self.assertLess(r.diagnostics.iterations,100)

    def test_all_27_independent_nearby_states(self):
        for c in REFERENCE['cases']:
            for near in c['neighborhood']:
                with self.subTest(near=near):
                    r=flash(state(near['T_K'],near['P_Pa_abs']))
                    self.assertEqual(r.classification,{'L':'single_liquid','V':'single_vapor','VL':'vapor_liquid'}[near['phase']])
                    self.close(r.beta,near['beta'],'beta')
                    json.dumps(asdict(r),allow_nan=False)

    def test_pressure_scan_independent(self):
        for c in REFERENCE['phase_scan']:
            r=flash(state(c['T_K'],c['P_Pa_abs']))
            self.assertEqual(r.classification,{'L':'single_liquid','V':'single_vapor','VL':'vapor_liquid'}[c['phase']])
            self.close(r.beta,c['beta'],'beta')

    def test_nonzero_bip_independent(self):
        ref=REFERENCE['optional_nonzero_kij']
        bip=BinaryInteractions('explicit_002',IDS,ref['kij'],'sensitivity, not calibrated physical data')
        r=flash(state(bip=bip),bip)
        self.close(r.beta,ref['beta'],'beta')
        for phase,key in zip(r.phases,('x','y')):
            for a,b in zip(phase.composition,ref[key]): self.close(a,b,key)

    def test_temperature_pressure_composition_sensitivity(self):
        base=flash()
        for s in (state(t=301),state(p=310000),state(z=(.51,.49))):
            r=flash(s)
            self.assertEqual(r.status,'success_two_phase'); self.assertNotEqual(r.beta,base.beta)
            self.assertTrue(all(isfinite(v) for p in r.phases for v in p.phi))

    def test_permutation_and_immutable_inputs(self):
        b=BinaryInteractions('permuted',IDS[::-1],BIP.values,BIP.source)
        s=state(z=(.6,.4)); before=asdict(s); a=flash(s)
        r=flash(state(z=(.4,.6),ids=IDS[::-1],bip=b),b)
        self.close(a.beta,r.beta,'beta')
        for p,q in zip(a.phases,r.phases):
            for x,y in zip(p.composition,q.composition[::-1]): self.close(x,y,'x')
        self.assertEqual(asdict(s),before)
        self.assertIs(a.overall_state,s)

    def test_call_history_and_thread_isolation(self):
        a=flash()
        flash(state(p=1e3)); flash(state(p=3e7))
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(lambda _:flash(),range(3)))
        self.assertTrue(all(r==a for r in results))

    def test_provider_registry_and_scope(self):
        self.assertEqual(property_package(MODEL),PengRobinsonProvider())
        self.assertIsInstance(property_package('molecular_composition@1.0'),MolecularCompositionProvider)
        self.assertEqual(PengRobinsonProvider().qualified_components,frozenset(IDS))
        for name in ('PH_flash','PS_flash','VLLE','density','enthalpy','water'):
            self.assertNotIn(name,PengRobinsonProvider().capabilities)
        r=flash(); self.assertEqual(r.provenance.component_dataset,REFERENCE['component_dataset'])
        self.assertEqual(r.provenance.bip,BIP)

    def test_m7_molar_projection_adapter_is_explicit(self):
        m=MolecularCompositionProvider().enrich(dict(temperature_K=300,pressure_Pa_abs=300000,
             component_mass_flow_kg_h={'methane':16.0428,'n_hexane':86.17536},mass_flow_kg_h=102.21816))
        self.assertEqual(flash(m).status,'invalid_input')
        selected=replace(m,provenance=StateSpecificationProvenance(MODEL,BIP.identifier))
        self.close(flash(selected).beta,REFERENCE['cases'][1]['beta'],'beta')

    def test_invalid_temperature_pressure(self):
        for value in (0,-1,float('nan'),float('inf'),True,'300'):
            for s in (state(t=value),state(p=value)):
                r=flash(s); self.assertEqual(r.status,'invalid_input'); self.assertEqual(r.phases,())

    def test_invalid_composition_and_order(self):
        for z in ((-.1,1.1),(.2,.5),(float('nan'),.5),(float('inf'),0),(.5,),(),(True,0)):
            self.assertEqual(flash(state(z=z)).status,'invalid_input')
        self.assertEqual(flash(state(ids=IDS[::-1])).status,'invalid_input')
        s=state(z=(.5,.5+1e-13)); r=flash(s)
        self.assertEqual(r.status,'success_two_phase')
        self.assertEqual(r.overall_state.composition.molar_fractions,s.composition.molar_fractions)
        self.assertAlmostEqual(sum(r.evaluated_molar_composition),1,delta=1e-15)

    def test_water_and_unknown_components_not_removed(self):
        for ids,z in [(('methane','n_hexane','water'),(.4,.4,.2)),(('methane','water'),(1.,0.)),(('methane','unknown'),(.5,.5))]:
            b=BinaryInteractions('unsupported',ids,tuple(tuple(0 for _ in ids) for _ in ids),'explicit')
            r=flash(state(z=z,ids=ids,bip=b),b)
            self.assertEqual(r.status,'unsupported_components'); self.assertEqual(r.phases,())

    def test_bip_identity_absence_and_validation(self):
        self.assertEqual(flash(state(),None).status,'invalid_input')
        self.assertEqual(flash(replace(state(),provenance=StateSpecificationProvenance(MODEL,'other'))).status,'invalid_input')
        for matrix in [((0,None),(None,0)),((0,float('inf')),(float('inf'),0))]:
            with self.assertRaises(ThermodynamicError): BinaryInteractions('bad',IDS,matrix,'explicit')

    def test_exp_and_extreme_numerical_failure(self):
        for v in (-701,701,float('nan')):
            with self.assertRaises(ThermodynamicError): safe_exp(v)
        r=flash(state(t=1e-200))
        self.assertEqual(r.status,'numerical_domain_error'); self.assertEqual(r.phases,())

    def test_nonconvergence_taxonomy_and_no_valid_last_iterate(self):
        for settings,status in [(SolverSettings(stability_max_iterations=1),'stability_not_converged'),
                                (SolverSettings(rr_max_iterations=1),'rachford_rice_not_converged'),
                                (SolverSettings(flash_max_iterations=1),'flash_not_converged')]:
            r=flash(settings=settings)
            self.assertEqual(r.status,status); self.assertEqual(r.phases,()); self.assertIsNone(r.beta); self.assertEqual(r.final_K,())
            self.assertIsNotNone(r.diagnostics.stability)
        r=flash(settings=SolverSettings(flash_max_iterations=1))
        self.assertTrue(r.diagnostics.fugacity_residual)
        self.assertTrue(r.diagnostics.material_residual)

    def test_unstable_state_without_rr_bracket_is_failure(self):
        with patch('riogineer_engine.pr_flash.wilson',return_value=(2.,3.)):
            r=flash()
        self.assertEqual(r.status,'rachford_rice_not_converged'); self.assertEqual(r.phases,())

    def test_wilson_is_only_initialization(self):
        k=wilson(eos())
        for a,b in zip(k,REFERENCE['cases'][1]['Wilson_initial_K']): self.assertAlmostEqual(a,b,delta=1e-10)
        self.assertNotEqual(k,flash().final_K)

    def test_runtime_dependency_isolation(self):
        root=Path(__file__).resolve().parents[1]/'riogineer_engine'
        for file in root.glob('*.py'):
            tree=ast.parse(file.read_text())
            imports=[]
            for n in ast.walk(tree):
                if isinstance(n,ast.Import): imports.extend(a.name for a in n.names)
                if isinstance(n,ast.ImportFrom): imports.append(n.module or '')
            for name in imports:
                self.assertNotIn(name.split('.')[0],('thermo','teqp','benchmarks','reference','numpy','scipy'),str(file))
