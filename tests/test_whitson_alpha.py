"""Explicit book correlation and independent published-input regression."""
import unittest
from types import SimpleNamespace as S
from petroflash.conditions import TPConditions
from petroflash.flash import flash_tp
from petroflash.pr_pure import pr_pure_parameters
from petroflash.stability import search_pr_stability


def fixture():
    cs=tuple(S(name=n,formula=f,critical_temperature=S(value=t*5/9),
        critical_pressure=S(value=p*6894.757293168),acentric_factor=S(value=o))
        for n,f,t,p,o in zip(('methane','n-butane','n-decane'),('CH4','C4H10','C10H22'),
                            (343,765.3,1111.8),(667.8,550.7,304),(.0115,.1928,.4902)))
    return S(components=cs,mole_fractions=(.5,.42,.08))


class TestWhitsonAlpha(unittest.TestCase):
    def parameters(self,omega,**kwargs):
        return pr_pure_parameters(temperature_k=400,pressure_pa=1e6,
            critical_temperature_k=600,critical_pressure_pa=2e6,acentric_factor=omega,**kwargs)

    def test_default_remains_original_quadratic(self):
        w=.4902
        self.assertEqual(self.parameters(w),self.parameters(w,alpha_model='PR1976'))
        self.assertAlmostEqual(self.parameters(w).m,.37464+1.54226*w-.26992*w*w,places=14)
        self.assertNotEqual(self.parameters(w).m,self.parameters(w,alpha_model='WHITSON_PROBLEM18').m)

    def test_book_threshold_is_explicit(self):
        for w in (.0115,.1928,.4):
            self.assertEqual(self.parameters(w),self.parameters(w,alpha_model='WHITSON_PROBLEM18'))
        w=.4902
        q=self.parameters(w,alpha_model='WHITSON_PROBLEM18')
        self.assertAlmostEqual(q.m,.3796+1.485*w-.1644*w*w+.01667*w**3,places=14)

    def test_invalid_model_rejected_before_early_outcomes(self):
        mix=fixture();tp=TPConditions(500,1e5);kk=((0,0,0),)*3
        for name in ('unknown',None,True):
            with self.subTest(name=name),self.assertRaises((TypeError,ValueError)):
                flash_tp(mix,tp,kij=kk,alpha_model=name)
            with self.subTest(name=name),self.assertRaises((TypeError,ValueError)):
                search_pr_stability(mix,tp,kij=kk,alpha_model=name)

    def check_flash(self,pressure,beta,x,y):
        q=flash_tp(fixture(),TPConditions((280+459.67)*5/9,pressure*6894.757293168),
                   kij=((0,0,0),)*3,alpha_model='WHITSON_PROBLEM18')
        self.assertEqual(q.status,'two_phase')
        self.assertEqual(q.alpha_model,'WHITSON_PROBLEM18')
        self.assertAlmostEqual(q.beta,beta,delta=1e-7)
        for a,b in zip(q.liquid_composition,x):self.assertAlmostEqual(a,b,delta=1e-7)
        for a,b in zip(q.vapor_composition,y):self.assertAlmostEqual(a,b,delta=1e-7)
        self.assertLess(q.material_residual,1e-10)
        self.assertLess(q.fugacity_residual,1e-8)
        self.assertTrue(all(p.status=='no_negative_tpd_found' for p in q.phase_stability))

    def test_500_psia_independent_same_printed_inputs(self):
        # Independent NumPy roots / simultaneous least-squares solution, not
        # an assertion of equality to the book's rounded final numbers.
        self.check_flash(500,.853428911377607,
            (0.08586060524888978, 0.4634230918102361, 0.45071630294087417),
            (0.571125856085782, 0.4125423550185301, 0.01633178889568785))

    def test_1500_psia_independent_same_printed_inputs(self):
        self.check_flash(1500,.5669826857325102,
            (0.33002403902527055, 0.5133226126753032, 0.15665334829942623),
            (0.6298144298995985, 0.3487274406821171, 0.021458129418284407))

if __name__=='__main__':unittest.main()
