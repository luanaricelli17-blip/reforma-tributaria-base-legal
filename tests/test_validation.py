import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"sync"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"monitor"))
from validate_records import official, load_validated
from check_sources import normalize

class TestGuards(unittest.TestCase):
    def test_allowlist_urls(self):
        self.assertTrue(official("https://www.gov.br/receitafederal"))
        self.assertTrue(official("https://www.planalto.gov.br/ccivil_03"))
        self.assertFalse(official("https://www.gov.br.attacker.example"))
        self.assertFalse(official("http://www.gov.br"))
    def test_strip_script(self):
        self.assertEqual(normalize(b"<html><script>BAD</script><p>Norma oficial</p></html>","text/html"),"Norma oficial")
    def test_empty_records(self):
        self.assertEqual(load_validated(), [])

if __name__ == "__main__":
    unittest.main()
