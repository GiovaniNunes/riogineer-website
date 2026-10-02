"""Verification adapter: real provider APIs, no AST or monkey-patching."""
from dataclasses import dataclass,asdict
from .common import *
import sys
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.numerical_profiles import NumericalProfile,PT200
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine import pump_energy

@dataclass(frozen=True)
class Profile:
    cap:int
    def __post_init__(self):
        if self.cap not in CAPS:raise ValueError('Production verification supports only legacy100 and PT200')
    @property
    def selection(self):return NumericalProfile.PT200 if self.cap==200 else None
    @property
    def identifier(self):return self.selection.value if self.selection else 'pr_high_accuracy_pt100@1'
    @property
    def settings(self):return PT200 if self.cap==200 else SolverSettings.high_accuracy()
    def record(self):return dict(identifier=self.identifier,settings=asdict(self.settings),fallback=None)

def inverse(spec,bip,profile,kind,evaluator=None,settings=None):
    class ObservedProvider(PengRobinsonProvider):
        def equilibrium_caloric_PT(self,state,bip,settings=None,*,numerical_profile=None):
            return evaluator(state,bip,settings) if evaluator else super().equilibrium_caloric_PT(state,bip,settings,numerical_profile=numerical_profile)
    provider=ObservedProvider();fn=provider.flash_PS if kind=='PS' else provider.flash_PH
    kwargs=dict(numerical_profile=profile.selection)
    if settings is not None:kwargs['settings']=settings
    return fn(spec,bip,**kwargs)

def guard(result,spec,profile,kind):
    return pump_energy.inverse(result,spec,kind,numerical_profile=profile.selection)
