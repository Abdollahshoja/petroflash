"""Sample TPD at specified compositions; sampling is not global minimization."""

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.pr_mixing import zero_kij
from petroflash.tpd import evaluate_mixture_pr_tpd


def main():
    db = ComponentDatabase.from_file('data/components.json')
    mixture = Mixture.from_mole_percentages(db,
        ['methane', 'ethane', 'propane'], [50, 30, 20])
    tp = TPConditions.from_units(-20, 200, temperature_unit='C', pressure_unit='bar')
    kij = zero_kij(len(mixture.components))
    print('PR1976; explicit demonstration assumption: all kij = 0')
    print('Component order:', mixture.names)
    print('Reference composition:', mixture.mole_fractions)
    for w in (mixture.mole_fractions, (0.8, 0.15, 0.05), (0.1, 0.3, 0.6)):
        q = evaluate_mixture_pr_tpd(mixture, tp, trial_mole_fractions=w, kij=kij)
        print('\nTrial composition:', w)
        for state, value in zip(q.trial_evaluation.candidates, q.tpd_values):
            print(f'  Z = {state.z:.12g}; dimensionless TPD = {value:.12g}')
        print('Minimum over roots at THIS trial composition:', q.minimum_tpd)
    print('\nOnly three compositions were sampled. No global stability conclusion is made.')
    print('No vapor fraction or flash result is calculated.')


if __name__ == '__main__':
    main()
