"""Isolated parameter injection; production modules/defaults/metadata stay intact.

Only inverse orchestration and its existing guard are parameterized in private
namespaces. All EOS/PT/stability/caloric work calls unchanged production code.
No solver is monkey-patched and no property provenance is rewritten.
"""
import ast,inspect,difflib,textwrap,sys
from dataclasses import dataclass,replace,asdict
from pathlib import Path
from .common import ROOT,HERE,hashed,read,digest
sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine import pr_ps_flash,pr_ph_flash,pump_energy
from riogineer_engine.pr_flash import SolverSettings
from riogineer_engine.property_packages import PengRobinsonProvider
from riogineer_engine.pr_eos import ThermodynamicError

@dataclass(frozen=True)
class Profile:
    cap:int
    def __post_init__(self):
        if type(self.cap) is not int or self.cap not in (100,200,400):raise ValueError('Unknown study profile')
    @property
    def identifier(self):return 'pr_high_accuracy_pt'+str(self.cap)+'@1'
    @property
    def settings(self):return replace(SolverSettings.high_accuracy(),flash_max_iterations=self.cap)
    def record(self):return dict(identifier=self.identifier,settings=asdict(self.settings),fallback=None)

class Inject(ast.NodeTransformer):
    count=0
    def visit_Call(self,node):
        if ast.dump(node)==ast.dump(ast.parse('SolverSettings.high_accuracy()',mode='eval').body):
            self.count+=1
            return ast.copy_location(ast.Name(id='selected_pt_settings',ctx=ast.Load()),node)
        return self.generic_visit(node)

def parameterize(module,name):
    path=Path(inspect.getfile(module));relative=str(path.relative_to(ROOT))
    assert digest(path)==read(HERE/'baseline.json')['files'][relative], 'Production source changed'
    original=ast.parse(textwrap.dedent(inspect.getsource(getattr(module,name))))
    before=ast.unparse(original);tree=ast.parse(before);fn=tree.body[0]
    assert isinstance(fn,ast.FunctionDef) and not fn.args.kwonlyargs
    fn.args.kwonlyargs.append(ast.arg(arg='selected_pt_settings'));fn.args.kw_defaults.append(None)
    change=Inject();tree=change.visit(tree);assert change.count==1
    ast.fix_missing_locations(tree)
    scope=dict(vars(module));exec(compile(tree,str(Path(inspect.getfile(module)))+'::isolated_profile','exec'),scope)
    diff=''.join(difflib.unified_diff(before.splitlines(True),ast.unparse(tree).splitlines(True),fromfile=name+' baseline AST',tofile=name+' isolated AST'))
    return scope[name],dict(function=name,source=relative,baseline_ast_sha256=hashed(before),parameterized_ast_sha256=hashed(ast.unparse(tree)),replacement_count=change.count,diff=diff)

PS,PS_TRANSFORM=parameterize(pr_ps_flash,'flash_ps')
PH,PH_TRANSFORM=parameterize(pr_ph_flash,'flash_ph')
GUARD,GUARD_TRANSFORM=parameterize(pump_energy,'inverse')

def inverse(spec,bip,profile,kind,evaluator=None,settings=None):
    profile.settings.validate()
    fn=PS if kind=='PS' else PH
    controls=settings or (pr_ps_flash.PSSettings() if kind=='PS' else pr_ph_flash.PHSettings())
    return fn(spec,bip,evaluator or PengRobinsonProvider().equilibrium_caloric_PT,controls,selected_pt_settings=profile.settings)

def guard(result,spec,profile,kind):
    # Existing guard retains settings, scan, failure, association and residual rules.
    out=GUARD(result,spec,kind,selected_pt_settings=profile.settings)
    if result.caloric.equilibrium.provenance.settings!=profile.settings:
        raise pump_energy.PumpFailure(kind,'final_PT_controls','Final PT must use declared profile')
    actual=result.caloric.equilibrium.overall_state
    if actual.pressure_Pa_abs!=spec.pressure_Pa_abs or actual.composition!=spec.composition:
        raise pump_energy.PumpFailure(kind,'final_PT_association','Final PT must retain specified P and composition')
    return out|dict(numerical_profile=profile.identifier,pt_settings=asdict(profile.settings))
