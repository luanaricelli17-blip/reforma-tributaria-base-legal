import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"sync"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"monitor"))

from validate_records import official, load_validated, validate
from check_sources import normalize

class TestGuards(unittest.TestCase):
    def test_allowlist_urls(self):
        self.assertTrue(official("https://www.gov.br/receitafederal"))
        self.assertTrue(official("https://www.planalto.gov.br/ccivil_03"))
        self.assertFalse(official("https://www.gov.br.attacker.example"))
        self.assertFalse(official("http://www.gov.br"))

    def test_strip_script(self):
        self.assertEqual(normalize(b"<html><script>BAD</script><p>Norma oficial</p></html>","text/html"),"Norma oficial")

    def test_all_approved_records_validate(self):
        # A base pode ter zero OU mais versões aprovadas; nenhum teste pressupõe
        # que ficará para sempre vazia.
        rows=load_validated()
        self.assertIsInstance(rows,list)
        for row in rows:
            with self.subTest(record_id=row["record_id"]):
                self.assertEqual(row["publication_state"],"published")
                self.assertTrue(row["reviewed_by"].strip())
                self.assertTrue(row["reviewed_at"].strip())
                self.assertTrue(row["review_pr_url"].startswith("https://github.com/"))

    def test_invalid_record_rejected(self):
        # A revisão humana é requisito: não deve passar com o campo em branco.
        example={
            "record_id":"lc214-2025-art1-v1",
            "document_key":"lc214-2025-art1",
            "version":1,
            "norm_type":"Lei Complementar",
            "norm_number":"214/2025",
            "title":"Teste de validação",
            "summary":"Registro de teste para validação estrutural, não publicar.",
            "official_url":"https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
            "reference_label":"LC 214 art. 1º",
            "verified_excerpt":"Trecho exclusivo de teste com caracteres suficientes",
            "source_id":"lc214",
            "source_snapshot_sha256":"a"*64,
            "retrieved_on":"2026-11-13",
            "published_on":"2025-01-16",
            "effective_from":"2026-01-01",
            "applicability":"Apenas teste",
            "reviewed_by":"",
            "reviewed_at":None,
            "review_pr_url":"https://github.com/example/repo/pull/1",
            "publication_state":"published",
        }
        with self.assertRaises(ValueError):
            validate(example,{"lc214":"a"*64})

if __name__=="__main__":
    unittest.main()
