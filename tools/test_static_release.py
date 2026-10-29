"""The deployed catalogue must have no active or dormant personal-data intake."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from urllib.parse import urljoin,urlsplit,unquote
import xml.etree.ElementTree as ET
from build_site import ROOT,BRANDS,generate,bundle
from test_site import HTML

class StaticReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'site'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','dist','outputs','__pycache__','qa-screens'))
        config=self.root/'data/site.json';data=json.loads(config.read_text());data['catalog_publication_approved']=False;config.write_text(json.dumps(data))
        generate(self.root,static_catalog=True);self.out=bundle(self.root,static_catalog=True)
    def tearDown(self):self.tmp.cleanup()
    def test_exactly_45_files_no_private_routes(self):
        paths={p.relative_to(self.out).as_posix() for p in self.out.rglob('*') if p.is_file()};self.assertEqual(len(paths),45)
        for prefix in ['telegram/','outputs/','data/','tools/','api/','docs/','deploy/','.git/']:
            self.assertFalse(any(p.startswith(prefix) for p in paths),prefix)
    def test_no_form_controls_or_api_calls_in_entire_release(self):
        for p in self.out.rglob('*.html'):
            tags=HTML(p.read_text()).tags
            self.assertFalse(any(t in ['form','input','textarea','select'] for t,a in tags),str(p))
            self.assertNotIn('gutsu-api-origin',p.read_text());self.assertNotIn('data-lead-form',p.read_text())
        script=(self.out/'equipment/catalog.js').read_text()
        self.assertNotIn('fetch(',script);self.assertNotIn('/api/',script)
    def test_unapproved_policies_and_private_address_not_published(self):
        for name in ['privacy','consent']:
            text=(self.out/name/'index.html').read_text()
            self.assertNotIn('policy-draft',text);self.assertNotIn('Обязательный реквизит',text);self.assertIn('noindex,follow',text)
    def test_final_artifact_not_changed_by_approval_flag(self):
        before={p.relative_to(self.out):p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
        cfg=self.root/'data/site.json';d=json.loads(cfg.read_text());d['catalog_publication_approved']=True;cfg.write_text(json.dumps(d))
        # Legal/backend approvals remain false. A form-free catalogue does not activate them.
        generate(self.root,static_catalog=True);bundle(self.root,static_catalog=True,release=True)
        after={p.relative_to(self.out):p.read_bytes() for p in self.out.rglob('*') if p.is_file()};self.assertEqual(before,after)
    def test_publication_still_requires_catalogue_approval(self):
        with self.assertRaisesRegex(ValueError,'owner_approval'):bundle(self.root,release=True,static_catalog=True)
    def test_static_mode_refuses_live_intake_configuration(self):
        cfg=self.root/'data/site.json';d=json.loads(cfg.read_text());d['public_intake_enabled']=True;cfg.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'disabled_intake'):bundle(self.root,static_catalog=True)
    def test_refuses_accidental_form_in_existing_page(self):
        p=self.root/'ai/index.html';p.write_text(p.read_text()+'<form><input></form>')
        with self.assertRaisesRegex(ValueError,'interactive_or_draft'):bundle(self.root,static_catalog=True)
    def test_all_links_and_sitemap_resolve(self):
        for p in self.out.rglob('*.html'):
            route='/'+p.relative_to(self.out).as_posix()
            for tag,a in HTML(p.read_text()).tags:
                for key in ['href','src']:
                    value=a.get(key,'');url=urlsplit(value)
                    if not value or url.scheme or url.netloc or value.startswith('#'):continue
                    target=self.out/unquote(urlsplit(urljoin(route,value)).path).lstrip('/')
                    self.assertTrue(target.is_file() or (target/'index.html').is_file(),str(p)+' '+value)
        urls=[e.text for e in ET.parse(self.out/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(urls),26)
        for b in BRANDS:
            self.assertIn('https://gutsu.space/equipment/brands/'+b[0]+'/',urls)
            page=(self.out/'equipment/brands'/b[0]/'index.html').read_text();self.assertEqual(page.count('Код позиции GS-'),8);self.assertNotIn('noindex',page)
    def test_robots_allows_brand_indexing(self):
        import urllib.robotparser
        parser=urllib.robotparser.RobotFileParser();parser.parse((self.out/'robots.txt').read_text().splitlines())
        for b in BRANDS:self.assertTrue(parser.can_fetch('*','https://gutsu.space/equipment/brands/'+b[0]+'/'))

if __name__=='__main__':unittest.main()
