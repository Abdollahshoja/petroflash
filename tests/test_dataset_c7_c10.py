"""C7-C10 identity, source and preservation checks; no provider needed at runtime."""
import hashlib
import json
from pathlib import Path
import unittest

class TestDatasetC7C10(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((Path(__file__).resolve().parents[1]/'data/components.json').read_text(encoding='utf-8-sig'))

    def test_original_records_preserved(self):
        raw=json.dumps(self.data['components'][:12],sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'c5c50a5da21799189233218e718272365241d150da68e5ca871dcffc36bfb09c')

    def test_new_identities_and_values(self):
        expected=[('n-heptane','142-82-5','C7H16',540.2,2735730.,.349,.10020194),
            ('n-octane','111-65-9','C8H18',568.74,2483590.,.398,.11422852),
            ('n-nonane','111-84-2','C9H20',594.55,2281000.,.4433,.1282551),
            ('n-decane','124-18-5','C10H22',617.7,2103000.,.4884,.14228168)]
        index={c['name']:c for c in self.data['components']}
        for name,cas,formula,tc,pc,w,mw in expected:
            with self.subTest(name=name):
                c=index[name]
                self.assertEqual((c['cas_number'],c['formula']),(cas,formula))
                digits=cas.replace('-','')
                self.assertEqual(sum(i*int(d) for i,d in enumerate(reversed(digits[:-1]),1))%10,int(digits[-1]))
                for field,value,unit in [('critical_temperature',tc,'K'),('critical_pressure',pc,'Pa'),('acentric_factor',w,'1'),('molar_mass',mw,'kg/mol')]:
                    r=c[field]
                    self.assertAlmostEqual(r['value'],value,places=12)
                    self.assertEqual(r['unit'],unit)
                    self.assertEqual(r['source'],'chemicals 1.5.2')
                    self.assertEqual(r['data_kind'],'evaluated')
                    self.assertTrue(r['reference'])
                    self.assertIsNone(r['uncertainty'])

    def test_builder_inventory_matches_dataset(self):
        # Parse the explicit inventory without importing optional provider packages.
        import ast
        source=Path(__file__).resolve().parents[1]/'tools/build_component_database.py'
        tree=ast.parse(source.read_text(encoding='utf-8-sig'))
        node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in n.targets))
        self.assertEqual(ast.literal_eval(node.value),tuple((c['name'],c['cas_number']) for c in self.data['components']))

if __name__=='__main__':unittest.main()
