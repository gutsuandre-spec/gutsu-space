from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import urlsplit,unquote,urljoin
import xml.etree.ElementTree as ET

from build_site import ROOT,BRANDS,CATEGORIES,generate,bundle
from catalog_public import validate,category_for
from security_audit import scan_public,private_filename

class HTML(HTMLParser):
    def __init__(self,text):
        super().__init__();self.tags=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)/'site'
        shutil.copytree(ROOT,cls.root,ignore=shutil.ignore_patterns('.git','dist','outputs','__pycache__','qa-screens'))
        config=cls.root/'data/site.json';data=json.loads(config.read_text());data['catalog_publication_approved']=False;config.write_text(json.dumps(data))
        cls.paths=generate(cls.root);cls.out=bundle(cls.root)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_ten_brands_eighty_real_models_no_godox(self):
        products=validate(json.loads((self.root/'data/equipment-public.json').read_text()))
        self.assertEqual(len(products),80);self.assertEqual(len({p['brand'] for p in products}),10)
        self.assertNotIn('godox',json.dumps(products).lower())
        for b in BRANDS:self.assertEqual(sum(p['brand']==b[0] for p in products),8)
    def test_categories_follow_item_not_brand(self):
        products=json.loads((self.root/'data/equipment-public.json').read_text())
        for p in products:
            for slug in CATEGORIES:
                text=(self.out/'equipment/categories'/slug/'index.html').read_text()
                self.assertEqual(p['id'] in text, category_for(p)==slug, p['id']+' '+slug)
    def test_public_schema_cannot_export_purchase_prices(self):
        p=json.loads((self.root/'data/equipment-public.json').read_text());p[0]['cashless_price']='999'
        with self.assertRaises(ValueError):validate(p)
    def test_unique_meta_h1_canonical_and_schema(self):
        titles=set();descriptions=set()
        for route in self.paths:
            text=(self.out/route.strip('/')/'index.html').read_text();html=HTML(text)
            self.assertEqual(sum(tag=='h1' for tag,a in html.tags),1)
            title=re.search(r'<title>(.*?)</title>',text).group(1);self.assertNotIn(title,titles);titles.add(title)
            desc=[a['content'] for tag,a in html.tags if tag=='meta' and a.get('name')=='description'][0];self.assertNotIn(desc,descriptions);descriptions.add(desc)
            self.assertIn(('link',{'rel':'canonical','href':'https://gutsu.space'+route}),html.tags)
            for schema in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text):self.assertEqual(json.loads(schema)['@context'],'https://schema.org')
    def test_all_local_links_resolve_in_public_bundle(self):
        for p in self.out.rglob('*.html'):
            route='/'+str(p.relative_to(self.out))
            for tag,a in HTML(p.read_text()).tags:
                for attr in ['href','src']:
                    value=a.get(attr,'');parsed=urlsplit(value)
                    if not value or parsed.scheme or parsed.netloc or value.startswith('#'):continue
                    target=self.out/unquote(urlsplit(urljoin(route,value)).path).lstrip('/')
                    self.assertTrue(target.is_file() or (target/'index.html').is_file(),str(p)+' -> '+value)
    def test_no_private_files_in_bundle(self):
        for p in self.out.rglob('*'):
            if not p.is_file():continue
            rel=str(p.relative_to(self.out));self.assertFalse(any(x in rel for x in ['outputs/','telegram/','data/','.git','sqlite','xlsx','.env']))
    def test_allowlist_excludes_accidental_internal_html(self):
        p=self.root/'equipment/internal.html';p.write_text('PRIVATE TEST CONTENT')
        try:self.assertFalse((bundle(self.root)/'equipment/internal.html').exists())
        finally:p.unlink()
    def test_source_symlink_rejected(self):
        p=self.root/'equipment/catalog.css';body=p.read_text();p.unlink();p.symlink_to(self.root/'styles.css')
        try:
            with self.assertRaisesRegex(ValueError,'invalid_public_input'):bundle(self.root)
        finally:p.unlink();p.write_text(body)
    def test_bundle_refuses_arbitrary_delete(self):
        folder=Path(self.tmp.name)/'precious';folder.mkdir();(folder/'keep').write_text('keep')
        with self.assertRaisesRegex(ValueError,'output_must_be_dist'):bundle(self.root,folder)
        self.assertTrue((folder/'keep').exists())
    def test_publication_is_blocked_until_owner_review(self):
        with self.assertRaisesRegex(ValueError,'owner_approval'):bundle(self.root,release=True)
    def test_flags_alone_cannot_publish_draft_documents(self):
        p=self.root/'data/site.json';original=p.read_text();cfg=json.loads(original)
        cfg.update(catalog_publication_approved=True,privacy_documents_final=True,privacy_approved_at='2026-10-28',consent_approved_at='2026-10-28',privacy_contact_address='SYNTHETIC',privacy_version='final-test')
        p.write_text(json.dumps(cfg))
        try:
            with self.assertRaisesRegex(ValueError,'draft_privacy_documents'):bundle(self.root,release=True)
        finally:p.write_text(original)
    def test_default_forms_disabled_and_consent_unchecked(self):
        config=json.loads((self.root/'data/site.json').read_text());self.assertFalse(config['public_intake_enabled']);self.assertIsNone(config['privacy_contact_address'])
        for route in ['/equipment/request/']+['/equipment/brands/'+b[0]+'/' for b in BRANDS]:
            tags=HTML((self.out/route.strip('/')/'index.html').read_text()).tags
            self.assertTrue(any(t=='fieldset' and 'disabled'in a for t,a in tags));self.assertTrue(any(t=='input' and a.get('name')=='consent' and 'checked' not in a for t,a in tags))
    def test_sitemap_includes_new_pages_but_not_draft_documents(self):
        urls=[e.text for e in ET.parse(self.out/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        for b in BRANDS:self.assertIn('https://gutsu.space/equipment/brands/'+b[0]+'/',urls)
        self.assertIn('https://gutsu.space/ai/services/',urls);self.assertNotIn('https://gutsu.space/privacy/',urls);self.assertEqual(len(urls),len(set(urls)))
    def test_existing_brand_assets_unchanged(self):
        for asset in ['gutsu-lockup-horizontal.svg','gutsu-wordmark.svg','gutsu-symbol.svg']:
            self.assertEqual((self.out/'assets'/asset).read_bytes(),(ROOT/'assets'/asset).read_bytes())
    def test_scan_blocks_private_content_and_credential(self):
        p=self.root/'equipment/unsafe.html'
        for data in [b'{"cashless_price": "1"}',b'SQLite format 3',b'ghp_'+b'A'*36]:
            p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'private_public_input'):scan_public([p],self.root)
        p.unlink()
    def test_real_leads_and_new_supplier_csv_cannot_enter_git(self):
        self.assertFalse(private_filename('telegram/lead-tracker.csv',b'date,company\n'))
        self.assertTrue(private_filename('telegram/lead-tracker.csv',b'date,company\nTEST,TEST\n'))
        self.assertTrue(private_filename('new-prices.csv',b'price\n123\n'))
    def test_workflow_only_uploads_dist(self):
        workflow=(ROOT/'.github/workflows/pages.yml').read_text();self.assertIn('path: "dist"',workflow);self.assertNotIn('path: "."',workflow);self.assertIn('build_site.py --release',workflow)

if __name__=='__main__':unittest.main()
