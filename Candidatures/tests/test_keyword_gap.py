import unittest

from keyword_gap import analyze_keyword_gap


class KeywordGapTests(unittest.TestCase):
    def test_separates_documented_and_missing_keywords(self):
        offer = "Nous cherchons un profil maîtrisant Python, SQL, Power BI et Snowflake. Docker apprécié."
        candidate = "Data analyst : Python, pandas, requêtes SQL, tableaux Power BI, conteneurs Docker."

        result = analyze_keyword_gap(offer, candidate)

        self.assertEqual(result["total"], 5)
        self.assertEqual(set(result["covered"]), {"Python", "SQL", "Power BI", "Docker"})
        self.assertEqual([item["term"] for item in result["missing"]], ["Snowflake"])
        self.assertEqual(result["score"], 80)
        self.assertTrue(result["missing"][0]["links"])

    def test_matches_whole_words_and_ignores_accents(self):
        result = analyze_keyword_gap("Modélisation statistique et séries temporelles", "")

        self.assertEqual(
            {item["term"] for item in result["missing"]},
            {"Modélisation statistique", "Statistiques", "Séries temporelles"},
        )
        # « r » dans un mot ne doit pas déclencher le langage R.
        self.assertEqual(analyze_keyword_gap("Notre équipe recrute", "")["total"], 0)

    def test_detects_unknown_acronyms_but_skips_contract_terms(self):
        result = analyze_keyword_gap("CDI à Paris. Maîtrise de GDPR et de SIEM.", "")

        self.assertEqual({item["term"] for item in result["missing"]}, {"GDPR", "SIEM"})

    def test_empty_offer_has_no_score(self):
        result = analyze_keyword_gap("", "Python")

        self.assertEqual(result["total"], 0)
        self.assertIsNone(result["score"])


if __name__ == "__main__":
    unittest.main()
