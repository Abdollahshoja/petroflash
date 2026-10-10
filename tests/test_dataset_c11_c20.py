"""HEOS coverage and preservation contract; no optional provider import."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

class TestDatasetC11C20(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        self.data=json.loads((self.root/'data/components.json').read_text(encoding='utf-8-sig'))
        self.audit=json.loads((self.root/'docs/data-audit-c11-c20.json').read_text())

    def test_original_sixteen_preserved(self):
        raw=json.dumps(self.data['components'][:16],sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'b8941727525cd739e3e96686357c156549261a3c06c2028055ed81fc3e90bd3d')

    def test_selected_heavy_records_and_inventory(self):
        expected=[('n-undecane','1120-21-4','C11H24',638.8,1990400.,.539,.15630826),
            ('n-dodecane','112-40-3','C12H26',658.1,1817000.,.574,.17033484),
            ('n-hexadecane','544-76-3','C16H34',722.1,1479850.,.749,.22644116)]
        index={c['name']:c for c in self.data['components']}
        for name,cas,formula,tc,pc,w,mw in expected:
            with self.subTest(name=name):
                c=index[name];self.assertEqual((c['cas_number'],c['formula']),(cas,formula))
                digits=cas.replace('-','');self.assertEqual(sum(i*int(d) for i,d in enumerate(reversed(digits[:-1]),1))%10,int(digits[-1]))
                for field,value,unit in [('critical_temperature',tc,'K'),('critical_pressure',pc,'Pa'),('acentric_factor',w,'1'),('molar_mass',mw,'kg/mol')]:
                    r=c[field];self.assertAlmostEqual(r['value'],value,places=12)
                    self.assertEqual(r['unit'],unit);self.assertEqual(r['source'],'chemicals 1.5.2')
                    self.assertEqual(r['data_kind'],'evaluated');self.assertIsNone(r['uncertainty'])
                    if field!='molar_mass':self.assertEqual(r['method'],'HEOS')
        tree=ast.parse((self.root/'tools/build_component_database.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COMPONENTS' for t in n.targets))
        self.assertEqual(ast.literal_eval(node.value),tuple((c['name'],c['cas_number']) for c in self.data['components']))

    def test_coverage_gaps_remain_explicit(self):
        rows=self.audit['coverage'];self.assertEqual([r['carbon_number'] for r in rows],list(range(11,21)))
        self.assertEqual([r['carbon_number'] for r in rows if r['included']],[11,12,16])
        names={c['name'] for c in self.data['components']}
        for r in rows:
            if r['included']: self.assertIn(r['name'], names)
            # Excluded-from-HEOS no longer means absent from the multisource bank.
            if r['included']:self.assertEqual(r['missing_fields'],[])
            else:
                self.assertEqual(len(r['missing_fields']),3)
                for f in r['missing_fields']:self.assertNotIn('HEOS',r['available_methods'][f])

if __name__=='__main__':unittest.main()
