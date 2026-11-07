import importlib.util, json, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('sales',Path(__file__).parents[1]/'scripts/sync_sales.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Sales(unittest.TestCase):
 def sale(self,product='youryear',**overrides):
  return {'id':'fixture-only-1','product_id':m.PRODUCTS[product]['id'],'created_at':'2026-11-05T00:00:00Z','price':4900,'currency':'usd','email':'private@example.invalid','full_name':'Must not leave importer','shipping_information':{'address':'Must not leave importer'},'url_params':{'mid_analytics':'yes','utm_campaign':'film01','utm_medium':'qr','mid_visit':'ce5e56c7-4560-4205-9dec-38129d9feaa3','mid_year':'1953'},**overrides}
 def test_paid_attribution_no_pii_and_deterministic_id(self):
  a=m.events_for_sale(self.sale());self.assertEqual(a,m.events_for_sale(self.sale()));self.assertEqual(a[0]['event'],'order_paid');self.assertEqual(a[0]['properties']['amount'],49);self.assertEqual(a[0]['properties']['door'],'qr');self.assertNotIn('private@example.invalid',json.dumps(a));self.assertNotIn('Must not leave',json.dumps(a))
 def test_lead_is_completed_transaction_not_page_view(self):
  a=m.events_for_sale(self.sale('free_sheet',price=0));self.assertEqual(a[0]['event'],'signup_completed');self.assertNotIn('$revenue',a[0]['properties'])
 def test_refund_is_separate_and_net_zero(self):
  a=m.events_for_sale(self.sale(refunded=True));self.assertEqual([e['event'] for e in a],['order_paid','order_refunded']);self.assertEqual(sum(e['properties']['revenue'] for e in a),0)
 def test_test_and_other_products_excluded(self):
  for s in [self.sale(test=True),self.sale(product_id='another-product'),self.sale(id=None)]:self.assertEqual(m.events_for_sale(s),[])
 def test_unattributed_and_query_pii_ignored(self):
  a=m.events_for_sale(self.sale(url_params={'mid_analytics':'yes','email':'private@example.invalid','mid_visit':'private@example.invalid','utm_medium':'bad','utm_campaign':'bad'}));self.assertEqual(a[0]['properties']['film'],'none');self.assertNotIn('private@example.invalid',json.dumps(a))
 def test_free_discounted_paid_product_stays_an_order(self):
  self.assertEqual(m.events_for_sale(self.sale(price=0))[0]['event'],'order_paid')
 def test_declined_or_unknown_analytics_is_not_imported(self):
  for consent in [None,'no','']:
   self.assertEqual(m.events_for_sale(self.sale(url_params={'mid_analytics':consent})),[])
 def test_experiment_conversion_join(self):
  sale=self.sale();sale['url_params'].update(mid_experiment='launch-presentation-v1',mid_variant='variant')
  self.assertEqual(m.events_for_sale(sale)[0]['properties']['$feature/launch-presentation-v1'],'variant')
 def test_campaign_is_separate_from_film(self):
  sale=self.sale();sale['url_params'].update(mid_film='film01',mid_door='qr',utm_campaign='autumn',utm_source='newsletter')
  props=m.events_for_sale(sale)[0]['properties'];self.assertEqual(props['film'],'film01');self.assertEqual(props['utm_campaign'],'autumn');self.assertEqual(props['door'],'qr')
if __name__=='__main__': unittest.main()
