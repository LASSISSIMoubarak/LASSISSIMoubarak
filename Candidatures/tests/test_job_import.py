import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as candidatures_app
import job_import

DESCRIPTION = "Vous modélisez des risques avec Python et des méthodes statistiques. " * 5


def job_page(title="Statisticien H/F", company="Assur SA"):
    posting = {
        "@type": "JobPosting", "title": title, "description": f"<p>{DESCRIPTION}</p>",
        "hiringOrganization": {"name": company},
        "jobLocation": {"address": {"addressLocality": "Lyon"}},
    }
    return f'<html><script type="application/ld+json">{json.dumps(posting)}</script></html>'


class ParsingTests(unittest.TestCase):
    def test_parse_job_posting_json_ld(self):
        offer = job_import.parse_offer("https://exemple.fr/o/1", job_page())
        self.assertEqual(offer["position"], "Statisticien H/F")
        self.assertEqual(offer["company"], "Assur SA")
        self.assertEqual(offer["location"], "Lyon")
        self.assertIn("modélisez des risques", offer["description"])
        self.assertNotIn("<p>", offer["description"])

    def test_login_wall_is_reported(self):
        page = "<html><body><p>Connectez-vous pour voir cette offre</p></body></html>"
        with self.assertRaises(job_import.OfferError):
            job_import.parse_offer("https://exemple.fr", page)

    def test_internal_addresses_are_refused(self):
        for url in ("http://127.0.0.1:5000/", "http://localhost/", "ftp://exemple.fr/x"):
            with self.assertRaises(job_import.OfferError):
                job_import.fetch_page(url)

    def test_alert_links_are_filtered_and_deduplicated(self):
        text = (
            "https://www.linkedin.com/comm/jobs/view/123?trk=a "
            "https://www.linkedin.com/comm/jobs/view/123?trk=b "
            "https://www.linkedin.com/help/privacy https://exemple.fr/promo"
        )
        links = [u for u in job_import.extract_urls(text) if job_import.looks_like_job_link(u)]
        self.assertEqual(len(links), 1)

    def test_alert_cards_keep_details_and_skip_unsubscribe(self):
        card = (
            '<a href="https://engage.indeed.com/f/a/AAA~~/x~">'
            '<a href="https://engage.indeed.com/f/a/AAA~~/x~"><b>Data Analyst H/F - Lyon</b></a>'
            '<div>Acme Corp 3.4</div><div>- Lyon (69)</div><div>Analyse de données et statistiques.</div></a>'
            '<a href="https://engage.indeed.com/f/a/BBB~~/y~">vous désinscrire ici et ne plus recevoir ces e-mails</a>'
            '<a href="https://subscriptions.indeed.com/alerts/cancel?x=1">Annuler cette alerte pour toujours</a>'
        )
        items = job_import.extract_alert_items(card)
        self.assertEqual(len(items), 1)
        offer = candidatures_app.offer_from_snippet(items[0]["snippet"])
        self.assertEqual(offer["position"], "Data Analyst H/F - Lyon")
        self.assertEqual(offer["company"], "Acme Corp")
        self.assertEqual(offer["location"], "Lyon (69)")

    def test_parse_match(self):
        self.assertEqual(candidatures_app.parse_match("SCORE: 82\nRAISON: Poste de modélisation."),
                         (82, "Poste de modélisation."))
        self.assertEqual(candidatures_app.parse_match("SCORE: 250")[0], 100)
        self.assertEqual(candidatures_app.parse_match("n'importe quoi"), (None, ""))


class ImportRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        candidatures_app.app.config.update(
            TESTING=True, DATABASE=str(Path(self.temp_dir.name) / "t.sqlite3"))
        with candidatures_app.app.app_context():
            candidatures_app.init_db()
        self.client = candidatures_app.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def post_form(self, path, data):
        self.client.get("/")
        with self.client.session_transaction() as session:
            data["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=data)

    def test_import_links_scores_and_skips_duplicates(self):
        self.post_form("/profile", data={"resume_source": "Statisticien, Python."})
        offer = job_import.parse_offer("https://exemple.fr/o/1", job_page())
        offer["url"] = "https://exemple.fr/o/1"
        with patch("job_import.import_offer", return_value=offer), patch(
            "app.generate_with_ollama", return_value="SCORE: 88\nRAISON: Statistiques."
        ):
            self.post_form("/import-links", data={"links": "https://exemple.fr/o/1"})
            self.post_form("/import-links", data={"links": "https://exemple.fr/o/1"})
        with candidatures_app.app.app_context():
            rows = candidatures_app.get_db().execute("SELECT * FROM applications").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["match_score"], 88)
        self.assertEqual(rows[0]["company"], "Assur SA")

    def test_failed_import_keeps_going(self):
        with patch("job_import.import_offer", side_effect=job_import.OfferError("Page protégée")):
            response = self.post_form("/import-links", data={"links": "https://exemple.fr/x"})
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertEqual(candidatures_app.get_db().execute(
                "SELECT COUNT(*) FROM applications").fetchone()[0], 0)

    def extension_post(self, payload, token=None):
        with candidatures_app.app.app_context():
            valid = candidatures_app.get_extension_token()
        headers = {"Authorization": f"Bearer {valid if token is None else token}"}
        return self.client.post("/api/extension/offer", json=payload, headers=headers)

    def test_extension_requires_token_and_saves_offer_once(self):
        payload = {"url": "https://www.linkedin.com/jobs/view/42/", "title": "Data analyst",
                   "company": "Acme", "location": "Paris", "description": DESCRIPTION}
        self.assertEqual(self.extension_post(payload, token="faux").status_code, 401)
        self.assertEqual(self.client.post("/api/extension/offer", json=payload).status_code, 401)
        with patch("app.score_in_background") as scoring:
            self.assertEqual(self.extension_post(payload).status_code, 201)
            self.assertEqual(self.extension_post(payload).json["status"], "duplicate")
            scoring.assert_called_once()
        with candidatures_app.app.app_context():
            rows = candidatures_app.get_db().execute("SELECT * FROM applications").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Acme")

    def test_extension_rejects_bad_payloads(self):
        self.assertEqual(self.extension_post({"url": "ftp://x", "description": DESCRIPTION}).status_code, 400)
        self.assertEqual(self.extension_post({"url": "https://x.fr/o", "description": "court"}).status_code, 400)

    def test_delete_and_purge_keep_followed_applications(self):
        old = "2020-01-01T00:00:00"
        now = "2999-01-01T00:00:00"
        with candidatures_app.app.app_context():
            db = candidatures_app.get_db()
            rows = [
                ("Vieille faible", "A analyser", 20, old), ("Vieille forte", "A analyser", 90, old),
                ("Vieille envoyée", "Candidature envoyee", 10, old), ("Récente", "A analyser", 10, now),
            ]
            for position, status, score, created in rows:
                db.execute(
                    "INSERT INTO applications (company, position, status, match_score, created_at, updated_at)"
                    " VALUES ('X', ?, ?, ?, ?, ?)", (position, status, score, created, created))
            db.commit()
        self.post_form("/applications/purge", data={"days": "30", "max_score": "50"})
        with candidatures_app.app.app_context():
            left = {r["position"] for r in candidatures_app.get_db().execute("SELECT position FROM applications")}
        self.assertEqual(left, {"Vieille forte", "Vieille envoyée", "Récente"})
        self.post_form("/applications/purge", data={"days": "0"})
        with candidatures_app.app.app_context():
            target = candidatures_app.get_db().execute(
                "SELECT id FROM applications WHERE position = 'Récente'").fetchone()["id"]
        self.post_form(f"/applications/{target}/delete", data={})
        with candidatures_app.app.app_context():
            left = {r["position"] for r in candidatures_app.get_db().execute("SELECT position FROM applications")}
        self.assertEqual(left, {"Vieille forte", "Vieille envoyée"})

    def test_alerts_require_configuration(self):
        with patch.dict("os.environ", {"GMAIL_ADDRESS": "", "GMAIL_APP_PASSWORD": ""}):
            response = self.post_form("/import-alerts", data={})
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
