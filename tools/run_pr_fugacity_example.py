"""Display ln(phi) for every admissible root of the specified feed."""

from math import exp

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.pr_fugacity import mixture_pr_log_fugacity
from petroflash.pr_mixing import mixture_pr_parameters, zero_kij
from petroflash.pr_roots import solve_pr_roots


def main():
    db = ComponentDatabase.from_file('data/components.json')
    mixture = Mixture.from_mole_percentages(db,
        ['methane', 'ethane', 'propane', 'n-butane'], [20, 30, 30, 20])
    tp = TPConditions.from_units(-10, 100, temperature_unit='C', pressure_unit='bar')
    kij = zero_kij(len(mixture.components))
    parameters = mixture_pr_parameters(mixture, tp, kij=kij)
    roots = solve_pr_roots(A=parameters.A, B=parameters.B)
    print('Model: PR1976; explicit demonstration assumption: all kij = 0')
    for z in roots.admissible_roots:
        result = mixture_pr_log_fugacity(mixture, tp, kij=kij, z=z)
        print('\nZ =', z)
        print(f'{"Component":<18} {"ln(phi)":>14} {"phi":>14} {"f_i [Pa]":>16}')
        for name, x, ln_phi in zip(mixture.names, mixture.mole_fractions, result.ln_phi):
            try:
                phi = exp(ln_phi)
                fugacity = x*phi*tp.pressure_pa
                print(f'{name:<18} {ln_phi:14.8f} {phi:14.8g} {fugacity:16.8g}')
            except OverflowError:
                print(f'{name:<18} ln(phi)={ln_phi}; exp exceeds numerical range')
        print('g_residual/(RT) =', result.g_residual_rt)
    print('\nNo phase stability analysis or flash has been performed.')


if __name__ == '__main__':
    main()
