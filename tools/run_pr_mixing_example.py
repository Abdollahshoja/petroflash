"""Run from repository root after installing the mixing module.

Zero kij is an explicit demonstration assumption, not validated pair data.
"""

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.pr_mixing import mixture_pr_parameters, zero_kij


def main():
    database = ComponentDatabase.from_file('data/components.json')
    mixture = Mixture.from_mole_percentages(
        database, ['methane', 'ethane', 'propane', 'n-butane'], [20, 30, 30, 20])
    conditions = TPConditions.from_units(
        -10, 100, temperature_unit='C', pressure_unit='bar')
    kij = zero_kij(len(mixture.components))
    result = mixture_pr_parameters(mixture, conditions, kij=kij)
    print('Component order:', mixture.names)
    print('Overall feed mole fractions:', mixture.mole_fractions)
    print('Model: original PR1976; explicit demonstration assumption: all kij = 0')
    print('Feed parameters (not an equilibrium phase determination):')
    print(result)
    print('Flash and phase stability are not calculated by this example.')


if __name__ == '__main__':
    main()
