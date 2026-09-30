"""Independent entropy oracle; only historical benchmark helpers are reused."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmarks.peng_robinson_ph.equilibrium import IndependentPT, TrialFailure, IDS, finite
from benchmarks.peng_robinson_caloric import reference as caloric


class EntropyPT(IndependentPT):
    def __init__(self, pt_tolerance=1e-26):
        super().__init__()
        self.flash.PT_SS_TOL = pt_tolerance
        self.pt_tolerance = pt_tolerance

    def evaluate(self, T, P, z):
        state = super().evaluate(T, P, z)
        beta = state['beta']
        weights = {'liquid': 1-beta, 'vapor': beta}
        state['S_eq_J_mol_K'] = math.fsum(weights[k]*p['s_J_mol_K'] for k,p in state['phases'].items())
        state['S_eq_direct_J_mol_K'] = math.fsum(weights[k]*p['direct_s_J_mol_K'] for k,p in state['phases'].items())
        if not all(finite(state[k]) for k in ('S_eq_J_mol_K', 'S_eq_direct_J_mol_K')):
            raise TrialFailure('caloric', 'Nonfinite equilibrium entropy')
        caloric.close(state['S_eq_J_mol_K'], state['S_eq_direct_J_mol_K'], 's_total')
        state['PT_diagnostics']['PT_SS_TOL'] = self.pt_tolerance
        return state

    def identities(self, state):
        return {name: caloric.phase_record(state['T_K'], state['P_Pa_abs'], p['composition'],
                    name, self.kw, self.cp)['consistency']
                for name,p in state['phases'].items()}
