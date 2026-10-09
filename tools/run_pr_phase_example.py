"""Fixed-composition root comparison for a feed, not global stability."""

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.pr_mixing import zero_kij
from petroflash.pr_phase import evaluate_mixture_pr_phase


def main():
    db = ComponentDatabase.from_file('data/components.json')
    mix = Mixture.from_mole_percentages(db, ['methane', 'ethane', 'propane'], [50, 30, 20])
    tp = TPConditions.from_units(-20, 200, temperature_unit='C', pressure_unit='bar')
    q = evaluate_mixture_pr_phase(mix, tp, kij=zero_kij(len(mix.components)))
    print('Model: PR1976; explicit demonstration assumption: all kij = 0')
    print('Comparison at the SAME feed composition:', mix.mole_fractions)
    print(f'{"Index":>6} {"Z":>18} {"g_residual/(RT)":>20} {"Preferred at fixed composition":>32}')
    for i, state in enumerate(q.candidates):
        print(f'{i:6d} {state.z:18.12g} {state.g_residual_rt:20.12g} '
              f'{str(i in q.preferred_indices):>32}')
    print('Gibbs comparison tolerance:', q.gibbs_tolerance)
    print('Preferred root(s):', tuple(s.z for s in q.preferred_candidates))
    print('Global composition stability (TPD) has not been tested. No flash is performed.')


if __name__ == '__main__':
    main()
