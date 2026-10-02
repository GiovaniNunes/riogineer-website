"""Deterministic M9 fixture builder; mass inputs derive from authoritative M7 MWs."""
from .components import component


def requirements(pressure_Pa_abs=300000):
    ids = ['methane', 'n_hexane']
    links = [
        ('HYDROCARBON_FEED', 'HYDROCARBON_FEED', 'outlet', 'SEP_PR_1', 'inlet'),
        ('VAPOR_PRODUCT', 'SEP_PR_1', 'vapor', 'VAPOR_PRODUCT_SINK', 'inlet'),
        ('LIQUID_PRODUCT', 'SEP_PR_1', 'liquid', 'LIQUID_PRODUCT_SINK', 'inlet'),
    ]
    return dict(schema_version='1.4', kind='requirements', case_id='MILESTONE_9_PT_FLASH_SEPARATOR',
        profile='pt_flash_separator',
        units=dict(temperature='K', pressure='Pa_abs', component_mass_flow='kg/h', heat_capacity='J/(kg K)', duty='W', recovery='mass_fraction'),
        provenance=dict(source='M8 frozen Case B: 300 K, 300000 Pa absolute, 1000 kmol/h, equimolar methane/n_hexane. Mass inputs = 500 kmol/h * M7 MW.', basis='qualified_pt_flash_reference'),
        components=ids,
        feeds=[dict(id='HYDROCARBON_FEED', state=dict(temperature_K=300, pressure_Pa_abs=pressure_Pa_abs,
                    component_mass_flow_kg_h={i: 500 * component(i).molecular_weight for i in ids}))],
        equipment=[dict(id='SEP_PR_1', type='equilibrium_separator_2phase', model=dict(id='pt_flash_separator', version='1.0'),
            parameters=dict(property_package='peng_robinson@1.0', bip=dict(identifier='m9_methane_nhexane_zero_kij@1.0',
                component_ids=list(ids), values=[[0, 0], [0, 0]], model='peng_robinson@1.0',
                source='Explicit zero kij mathematical benchmark from pre_m8_methane_nhexane_canonical_pr@1.0; not calibrated physical BIPs.')))],
        sinks=[dict(id=i) for i in ('VAPOR_PRODUCT_SINK', 'LIQUID_PRODUCT_SINK')],
        streams=[dict(id=s, service=s) for s, *_ in links],
        connections=[dict(id='C_'+s, stream_id=s, source=dict(owner_id=a, port_id=p), target=dict(owner_id=b, port_id=q))
                     for s, a, p, b, q in links],
        required_outputs=['streams', 'mass_balance', 'pt_flash'])


if __name__ == '__main__':
    import json
    print(json.dumps(requirements(), indent=2))
