import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError
from unittest.mock import Mock, patch

from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as candidatures_app


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        candidatures_app.app.config.update(
            TESTING=True,
            DATABASE=str(Path(self.temp_dir.name) / "test.sqlite3"),
        )
        with candidatures_app.app.app_context():
            candidatures_app.init_db()
        self.client = candidatures_app.app.test_client()

    def post_form(self, path, data):
        self.client.get("/")
        with self.client.session_transaction() as session:
            data["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_offer_and_update_status(self):
        response = self.post_form(
            "/applications",
            data={
                "company": "Exemple SA",
                "position": "Analyste",
                "job_description": "Analyser des donnees.",
            },
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
        response = self.post_form(
            f"/applications/{application_id}/update",
            data={"status": "Candidature envoyee", "notes": "Relancer lundi", "reply": ""},
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            self.assertEqual(application["status"], "Candidature envoyee")
            self.assertEqual(application["notes"], "Relancer lundi")

    def test_export_contains_headers_and_offer(self):
        self.post_form(
            "/applications",
            data={"company": "Exemple SA", "position": "Analyste"},
        )
        response = self.client.get("/export.xlsx")
        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(io.BytesIO(response.data), read_only=True)
        sheet = workbook["Candidatures"]
        self.assertEqual(sheet.cell(1, 1).value, "Entreprise")
        self.assertEqual(sheet.cell(2, 1).value, "Exemple SA")

    def test_home_page_renders_empty_state(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Le tableau est prêt".encode(), response.data)

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post(
            "/applications", data={"company": "X", "position": "Y"}
        )
        self.assertEqual(response.status_code, 400)

    def test_pdf_resume_text_is_extracted_and_saved(self):
        page = Mock()
        page.extract_text.return_value = "Nom Exemple\nCompetence Python"
        reader = Mock()
        reader.pages = [page]
        with patch("app.PdfReader", return_value=reader):
            response = self.post_form(
                "/profile",
                data={
                    "full_name": "Nom Exemple",
                    "resume_pdf": (io.BytesIO(b"%PDF-test"), "cv.pdf"),
                },
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            profile = candidatures_app.get_profile()
            self.assertIn("Competence Python", profile["resume_source"])

    def test_ollama_retries_after_transient_connection_error(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = json.dumps(
            {"message": {"content": "OK"}}
        ).encode("utf-8")
        with patch(
            "app.urlopen",
            side_effect=[URLError(ConnectionRefusedError("refused")), response],
        ) as request:
            with patch("app.time.sleep"):
                result = candidatures_app.generate_with_ollama("test", max_tokens=20)
        self.assertEqual(result, "OK")
        self.assertEqual(request.call_count, 2)

    def test_ollama_timeout_does_not_repeat_long_generation(self):
        with patch("app.urlopen", side_effect=URLError(TimeoutError("timed out"))) as request:
            with self.assertRaisesRegex(RuntimeError, "Qwen n'a pas termine"):
                candidatures_app.generate_with_ollama("test", max_tokens=20)
        self.assertEqual(request.call_count, 1)

    def test_data_cv_docx_uses_candidate_and_role_not_board_name(self):
        profile = {
            "full_name": "Nom Exemple",
            "location": "Angers",
            "email": "test@example.com",
            "phone": "0600000000",
        }
        application = {"position": "Data Analyst"}
        source = "CV adapte - Hellowork\n**PROFIL**\nAnalyste de donnees.\nCOMPETENCES CLES\n- SQL"
        document = Document(
            io.BytesIO(candidatures_app.make_cv_docx(profile, application, source).getvalue())
        )
        visible_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("Nom Exemple", visible_text)
        self.assertIn("DATA ANALYST", visible_text)
        self.assertIn("COMPETENCES CLES", visible_text)
        self.assertNotIn("CV adapte - Hellowork", visible_text)

    def test_letter_pdf_has_french_letter_layout_without_cv_headings(self):
        self.post_form(
            "/applications",
            data={
                "company": "Hellowork",
                "position": "Data Scientist",
                "job_description": "Prevision de la demande et modelisation.",
            },
        )
        with candidatures_app.app.app_context():
            database = candidatures_app.get_db()
            database.execute(
                "UPDATE profile SET full_name = ?, location = ?, email = ? WHERE id = 1",
                ("Nom Exemple", "Rennes", "nom@example.com"),
            )
            application = database.execute("SELECT id FROM applications").fetchone()
            application_id = application["id"]
            database.execute(
                "UPDATE applications SET letter_draft = ? WHERE id = ?",
                (
                    "Motivation Letter\n\nMadame/Monsieur,\n\nÀ PROPOS\n"
                    "J'ai analyse des donnees et construit des modeles.\n\n"
                    "Je vous prie d'agreer, Madame, Monsieur, mes salutations distinguees.",
                    application_id,
                ),
            )
            database.commit()

        response = self.client.get(f"/applications/{application_id}/download/letter/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        pdf_text = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(io.BytesIO(response.data)).pages
        )
        self.assertIn("Nom Exemple", pdf_text)
        self.assertIn("Objet : Candidature au poste de Data Scientist", pdf_text)
        self.assertIn("Madame, Monsieur", pdf_text)
        self.assertNotIn("Motivation Letter", pdf_text)
        self.assertNotIn("A PROPOS", pdf_text)


if __name__ == "__main__":
    unittest.main()
