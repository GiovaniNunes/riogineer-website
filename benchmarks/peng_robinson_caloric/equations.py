"""Benchmark-only, direct equations; no thermodynamic-library or production imports."""
from math import fsum, log, log1p, sqrt

R = 8.31446261815324
T_REF = 298.15
P_REF = 101325.0


def ideal_pure(T, coefficients, tref=T_REF):
    """Cp/R = sum(c_j T**j); definite integrals, never a 0-K reference."""
    cp = R * fsum(c*T**j for j, c in enumerate(coefficients))
    h = R * fsum(c*(T**(j+1)-tref**(j+1))/(j+1) for j, c in enumerate(coefficients))
    s = R * (coefficients[0]*log(T/tref) +
             fsum(c*(T**j-tref**j)/j for j, c in enumerate(coefficients) if j))
    return cp, h, s


def ideal(T, P, q, cp_data):
    pure = [ideal_pure(T, c['coefficients']) for c in cp_data]
    cp, h, st = [fsum(z*v[j] for z, v in zip(q, pure)) for j in range(3)]
    sp = -R*log(P/P_REF)
    sm = -R*fsum(z*log(z) for z in q if z)
    return dict(Cp_ig_J_mol_K=cp, h_ig_J_mol=h, s_ig_temperature_J_mol_K=st,
                s_ig_pressure_J_mol_K=sp, s_ig_mixing_J_mol_K=sm, s_ig_J_mol_K=st+sp+sm)


def parameters(T, q, components, kij):
    pure = []
    for c in components:
        tc, pc, w = c['Tc_K'], c['Pc_Pa_abs'], c['omega']
        k = .37464 + 1.54226*w - .26992*w*w
        g = 1+k*(1-sqrt(T/tc))
        a0 = .45724*R*R*tc*tc/pc
        pure.append(dict(alpha=g*g, dalpha_dT_K_inv=-k*g/sqrt(T*tc),
                         a_i_Pa_m6_mol2=a0*g*g, da_i_dT_Pa_m6_mol2_K=-a0*k*g/sqrt(T*tc),
                         b_i_m3_mol=.07780*R*tc/pc))
    a, da = 0., 0.
    for i, x in enumerate(pure):
        for j, y in enumerate(pure):
            aij = sqrt(x['a_i_Pa_m6_mol2']*y['a_i_Pa_m6_mol2'])*(1-kij[i][j])
            a += q[i]*q[j]*aij
            da += q[i]*q[j]*.5*aij*(x['da_i_dT_Pa_m6_mol2_K']/x['a_i_Pa_m6_mol2']+
                                               y['da_i_dT_Pa_m6_mol2_K']/y['a_i_Pa_m6_mol2'])
    return pure, a, da, fsum(z*c['b_i_m3_mol'] for z, c in zip(q, pure))


def departures(T, P, Z, a, da, b):
    B = b*P/(R*T)
    # log1p keeps the dilute-gas logarithm well conditioned.
    logarithm = log1p(2*sqrt(2)*B/(Z+(1-sqrt(2))*B))
    factor = logarithm/(2*sqrt(2)*b)
    return (R*T*(Z-1)+(T*da-a)*factor,
            R*log1p(Z-1-B)+da*factor)
