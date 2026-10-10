"""Source selection, units and preservation checks for the C13-C20 supplement."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

class TestDatasetMultisource(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        self.data=json.loads((self.root/'data/components.json').read_text(encoding='utf-8-sig'))
        self.supp=json.loads((self.root/'data/component-supplement-nist-pd.json').read_text())

    def test_previous_nineteen_preserved(self):
        raw=json.dumps(self.data['components'][:19],sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'28b35f7f5883a487baa88a752cc8921af6cdaafcce32418550f3d6c2bb3d09bd')

    def test_supplement_matches_selected_rows_and_conversion(self):
        expected=[('n-tridecane',675,16.79,.6231),('n-tetradecane',693,15.73,.6797),
            ('n-pentadecane',708,14.79,.706),('n-heptadecane',736,13.42,.7699),
            ('n-octadecane',747,12.92,.7895),('n-nonadecane',755,11.60,.8271),
            ('n-eicosane',768,10.70,.9065)]
        self.assertEqual(len(self.supp['components']),7)
        self.assertEqual(self.data['components'][19:],self.supp['components'])
        for c,(name,tc,bar,w) in zip(self.supp['components'],expected):
            with self.subTest(name=name):
                self.assertEqual(c['name'],name)
                self.assertEqual(c['critical_temperature']['value'],tc)
                self.assertAlmostEqual(c['critical_pressure']['value'],bar*100000,places=8)
                self.assertEqual(c['acentric_factor']['value'],w)
                for f,u in [('critical_temperature','K'),('critical_pressure','Pa'),('acentric_factor','1'),('molar_mass','kg/mol')]:
                    self.assertEqual(c[f]['unit'],u)
                    self.assertEqual(c[f]['data_kind'],'evaluated')
                    self.assertIsNone(c[f]['uncertainty'])

    def test_per_property_source_and_uncertainty_annotation(self):
        for c in self.supp['components']:
            for f in ['critical_temperature','critical_pressure']:
                self.assertEqual(c[f]['source'],'NIST Chemistry WebBook, SRD 69')
                self.assertIn('webbook.nist.gov',c[f]['reference'])
                self.assertIn('2026-10-10',c[f]['notes'])
            self.assertIn('Printed +/-',c['critical_temperature']['notes'])
            self.assertIn('TRC uncertainty',c['critical_pressure']['notes'])
            self.assertEqual(c['acentric_factor']['method'],'PD')
            self.assertEqual(c['acentric_factor']['reference'],'https://doi.org/10.1021/i260047a026')
            self.assertIn('via chemicals 1.5.2',c['acentric_factor']['source'])
            self.assertEqual(c['molar_mass']['source'],'chemicals 1.5.2')

    def test_complete_n_alkane_chain_and_unique_cas(self):
        names=['methane','ethane','propane','n-butane','n-pentane','n-hexane','n-heptane','n-octane','n-nonane','n-decane','n-undecane','n-dodecane','n-tridecane','n-tetradecane','n-pentadecane','n-hexadecane','n-heptadecane','n-octadecane','n-nonadecane','n-eicosane']
        index={c['name']:c for c in self.data['components']}
        self.assertEqual(len(index),26)
        self.assertEqual(len({c['cas_number'] for c in index.values()}),26)
        for n,name in enumerate(names,1):
            c=index[name]
            self.assertEqual(c['formula'],('CH4' if n==1 else f'C{n}H{2*n+2}'))
            digits=c['cas_number'].replace('-','')
            self.assertEqual(sum(i*int(d) for i,d in enumerate(reversed(digits[:-1]),1))%10,int(digits[-1]))

    def test_builder_inventory_matches_bank(self):
        tree=ast.parse((self.root/'tools/build_component_database.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in n.targets))
        self.assertEqual(ast.literal_eval(node.value),tuple((c['name'],c['cas_number']) for c in self.data['components']))

if __name__=='__main__':unittest.main()
