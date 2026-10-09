"""Evaluate feed roots with an explicit zero-kij demonstration assumption."""

from petroflash import ComponentDatabase, Mixture
from petroflash.conditions import TPConditions
from petroflash.pr_mixing import mixture_pr_parameters, zero_kij
from petroflash.pr_roots import solve_pr_roots


def main():
    database = ComponentDatabase.from_file('data/components.json')
    mixture = Mixture.from_mole_percentages(database,
        ['methane', 'ethane', 'propane', 'n-butane'], [20, 30, 30, 20])
    conditions = TPConditions.from_units(-10, 100,
        temperature_unit='C', pressure_unit='bar')
    parameters = mixture_pr_parameters(mixture, conditions,
        kij=zero_kij(len(mixture.components)))
    roots = solve_pr_roots(A=parameters.A, B=parameters.B)
    print('Component order:', mixture.names)
    print('PR1976; explicit assumption: all kij = 0')
    print('A =', parameters.A, 'B =', parameters.B)
    print('Distinct real roots:', roots.real_roots)
    print('Roots satisfying Z>B:', roots.admissible_roots)
    print('Scaled polynomial residuals:', roots.scaled_residuals)
    print('Root count does not establish phase stability or vapor fraction.')


if __name__ == '__main__':
    main()
