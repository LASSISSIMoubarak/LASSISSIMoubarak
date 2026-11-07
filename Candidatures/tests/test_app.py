import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
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
            data={
                "status": "Candidature envoyee",
                "notes": "Relancer lundi",
                "reply": "",
                "company": "Entreprise corrigée",
                "company_address": "20 avenue Exemple",
            },
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            self.assertEqual(application["status"], "Candidature envoyee")
            self.assertEqual(application["company"], "Entreprise corrigée")
            self.assertEqual(application["notes"], "Relancer lundi")
            self.assertEqual(application["company_address"], "20 avenue Exemple")

    def test_application_title_removes_company_and_linkedin_suffix_for_documents(self):
        application = {
            "position": "Data Scientist /AI Engineer | Eulidia | LinkedIn",
            "company": "Eulidia",
            "location": "",
        }
        self.assertEqual(
            candidatures_app.cv_role_title(application, upper=False),
            "Data Scientist /AI Engineer",
        )

    def test_profile_and_company_postal_addresses_are_saved(self):
        response = self.post_form(
            "/profile",
            data={
                "full_name": "Nom Exemple",
                "postal_address": "12 rue des Donnees\n49000 Angers",
                "resume_source": "SQL et Python",
            },
        )
        self.assertEqual(response.status_code, 302)
        response = self.post_form(
            "/applications",
            data={
                "company": "Exemple",
                "position": "Data Analyst",
                "company_address": "20 avenue des Donnees\n49000 Angers",
            },
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            profile = candidatures_app.get_profile()
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            self.assertIn("12 rue des Donnees", profile["postal_address"])
            self.assertIn("20 avenue des Donnees", application["company_address"])

    def test_profile_social_links_are_saved_and_rendered_in_cv_header(self):
        response = self.post_form(
            "/profile",
            data={
                "linkedin_url": "linkedin.com/in/moubarak",
                "portfolio_url": "https://portfolio.example/projects",
            },
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            profile = candidatures_app.get_profile()
            self.assertEqual(profile["linkedin_url"], "https://linkedin.com/in/moubarak")
            self.assertEqual(profile["portfolio_url"], "https://portfolio.example/projects")
            source = candidatures_app.make_cv_latex(
                profile, {"position": "Data", "company": "X"}, "PROFIL\nProfil court."
            )
            self.assertIn(r"\href{https://linkedin.com/in/moubarak}{LinkedIn}", source)
            self.assertIn(r"\href{https://portfolio.example/projects}{Portfolio}", source)
            if candidatures_app.shutil.which("xelatex"):
                pdf_text = PdfReader(candidatures_app.compile_latex(source)).pages[0].extract_text()
                self.assertIn("LinkedIn", pdf_text)
                self.assertIn("Portfolio", pdf_text)

    def test_profile_rejects_invalid_social_link(self):
        response = self.post_form("/profile", data={"linkedin_url": "javascript:alert(1)"})
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertEqual(candidatures_app.get_profile()["linkedin_url"], "")

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

    def test_project_library_and_detail_render_seeded_projects(self):
        library = self.client.get("/projects")
        self.assertEqual(library.status_code, 200)
        self.assertIn("SolarWatch".encode(), library.data)
        self.assertIn("Tableau de bord Power BI".encode(), library.data)
        self.assertIn("QuantDashboard".encode(), library.data)
        self.assertIn("Survie clinique bayésienne".encode(), library.data)
        self.assertIn("Prévision solaire bayésienne".encode(), library.data)
        self.assertIn("Ajouter un autre projet".encode(), library.data)

        detail = self.client.get("/projects/solarwatch")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Projet personnel".encode(), detail.data)
        self.assertIn("pas de pannes labellisées".encode(), detail.data)
        self.assertIn("pas encore accessible à un recruteur".encode(), detail.data)

        bi_detail = self.client.get("/projects/power-bi-transactions-india")
        self.assertEqual(bi_detail.status_code, 200)
        self.assertIn("Power Automate".encode(), bi_detail.data)
        self.assertIn("transactions par secteur".encode(), bi_detail.data)

        quant_detail = self.client.get("/projects/quantdashboard")
        self.assertEqual(quant_detail.status_code, 200)
        self.assertIn("RPostgres".encode(), quant_detail.data)
        self.assertIn("drawdown maximal".encode(), quant_detail.data)

        bayesian_detail = self.client.get("/projects/modelisation-bayesienne")
        self.assertEqual(bayesian_detail.status_code, 200)
        self.assertIn("inférence a posteriori".encode(), bayesian_detail.data)
        self.assertIn("Monte-Carlo".encode(), bayesian_detail.data)

        pbc_detail = self.client.get("/projects/pbc-rstan-survival")
        self.assertEqual(pbc_detail.status_code, 200)
        self.assertIn("zéro divergence".encode(), pbc_detail.data)
        self.assertIn("0,85".encode(), pbc_detail.data)

        solar_bayesian_detail = self.client.get("/projects/prevision-solaire-bayesienne")
        self.assertEqual(solar_bayesian_detail.status_code, 200)
        self.assertIn("Normal-Inverse-Gamma".encode(), solar_bayesian_detail.data)
        self.assertIn("2 495,88".encode(), solar_bayesian_detail.data)

    def test_bayesian_projects_rank_for_relevant_offers(self):
        with candidatures_app.app.app_context():
            projects = candidatures_app.get_projects()
            survival_ranked = candidatures_app.rank_projects(
                "Analyse de survie clinique avec RStan, modèle Weibull et données censurées",
                projects,
            )
            solar_ranked = candidatures_app.rank_projects(
                "Prévision solaire probabiliste en Python avec régression bayésienne et Gibbs",
                projects,
            )
            general_ranked = candidatures_app.rank_projects(
                "Data Analyst Python SQL tableaux de bord",
                projects,
            )

        self.assertEqual(survival_ranked[0]["slug"], "pbc-rstan-survival")
        self.assertEqual(solar_ranked[0]["slug"], "prevision-solaire-bayesienne")
        recommended_general = [
            item["slug"] for item in general_ranked if item["match_score"] > 0
        ][:2]
        self.assertNotIn("pbc-rstan-survival", recommended_general)
        self.assertNotIn("prevision-solaire-bayesienne", recommended_general)

    def test_gasoline_nir_project_is_ranked_for_chemometrics_offers(self):
        with candidatures_app.app.app_context():
            projects = candidatures_app.get_projects()
            ranked = candidatures_app.rank_projects(
                "Analyse de spectres NIR, chimiométrie PLS et prototype R Shiny",
                projects,
            )

        self.assertEqual(ranked[0]["slug"], "gasoline-nir-pcr-pls-shiny")
        self.assertEqual(
            ranked[0]["title"],
            "NIR Spectra Analysis: PCR, PLS, and Shiny Demo",
        )
        self.assertIn("does not use digestate samples", ranked[0]["description"])

    def test_existing_gasoline_project_title_is_migrated_without_overwriting_custom_title(self):
        with candidatures_app.app.app_context():
            database = candidatures_app.get_db()
            database.execute(
                """UPDATE projects SET title = ?, summary = ?
                   WHERE slug = ?""",
                (
                    "Chimiométrie NIR - PCR et PLS avec Shiny",
                    "Analyse de spectres NIR du jeu gasoline avec modèles PCR/PLS, "
                    "validation croisée et démonstration interactive Shiny.",
                    "gasoline-nir-pcr-pls-shiny",
                ),
            )
            database.commit()
            candidatures_app.init_db()
            title = database.execute(
                "SELECT title FROM projects WHERE slug = ?",
                ("gasoline-nir-pcr-pls-shiny",),
            ).fetchone()["title"]
            self.assertEqual(
                title, "NIR Spectra Analysis: PCR, PLS, and Shiny Demo"
            )
            summary = database.execute(
                "SELECT summary FROM projects WHERE slug = ?",
                ("gasoline-nir-pcr-pls-shiny",),
            ).fetchone()["summary"]
            self.assertIn("NIR spectra analysis", summary)

            database.execute(
                "UPDATE projects SET title = ? WHERE slug = ?",
                ("Mon titre personnalisé", "gasoline-nir-pcr-pls-shiny"),
            )
            database.commit()
            candidatures_app.init_db()
            title = database.execute(
                "SELECT title FROM projects WHERE slug = ?",
                ("gasoline-nir-pcr-pls-shiny",),
            ).fetchone()["title"]
            self.assertEqual(title, "Mon titre personnalisé")

    def test_bayesian_catalog_copy_is_added_to_cv_without_coursework_framing(self):
        with candidatures_app.app.app_context():
            project = candidatures_app.get_db().execute(
                "SELECT * FROM projects WHERE slug = 'modelisation-bayesienne'"
            ).fetchone()
            cv = candidatures_app.inject_selected_projects(
                "PROFIL\nStatisticien.", [project]
            )

        self.assertIn("lois a priori à l'inférence a posteriori", cv)
        self.assertIn("Monte-Carlo", cv)
        self.assertIn("Statistique bayésienne", cv)
        self.assertNotIn("Exercices R", cv)

    def test_quantdashboard_is_selected_for_relevant_offer_and_added_to_cv_context(self):
        response = self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Analyste quantitatif R Shiny",
            "job_description": (
                "Développer un dashboard R Shiny pour analyser les marchés financiers, "
                "la volatilité, la Value at Risk et les séries temporelles."
            ),
        })
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            candidatures_app.ensure_application_project_choices(application)
            projects = candidatures_app.selected_application_projects(application_id)
            self.assertEqual(projects[0]["slug"], "quantdashboard")
            prompt = candidatures_app.build_prompt(
                "cv",
                candidatures_app.get_profile(),
                application,
                selected_projects=projects,
            )
            cv = candidatures_app.inject_selected_projects(
                "PROFIL\nAnalyste quantitatif.", projects
            )
            self.assertIn("PostgreSQL hébergé sur Neon", prompt)
            self.assertIn("moyennes mobiles à 20, 50 et 200 jours", prompt)
            self.assertIn("R, Shiny", cv)

    def test_projects_can_be_added_and_updated_with_validated_public_url(self):
        with candidatures_app.app.app_context():
            project_id = candidatures_app.get_db().execute(
                "SELECT id FROM projects WHERE slug = 'solarwatch'"
            ).fetchone()["id"]

        response = self.post_form("/projects/save", data={
            "project_id": str(project_id),
            "title": "SolarWatch actualisé",
            "summary": "Résumé vérifié.",
            "description": "Périmètre documenté.",
            "skills": "Python, LSTM",
            "keywords": "solaire, prévision",
            "highlights": "Résultat réellement observé",
            "public_url": "github.com/exemple/solarwatch",
        })
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            project = candidatures_app.get_db().execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            self.assertEqual(project["title"], "SolarWatch actualisé")
            self.assertEqual(project["public_url"], "https://github.com/exemple/solarwatch")
            self.assertEqual(project["highlights"], "Résultat réellement observé")

        response = self.post_form("/projects/save", data={
            "title": "Projet ajouté",
            "summary": "Résumé du projet.",
            "description": "Description du projet.",
            "skills": "Python",
            "keywords": "python, analyse",
            "highlights": "Test documenté",
            "public_url": "javascript:alert(1)",
        })
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertIsNone(candidatures_app.get_db().execute(
                "SELECT id FROM projects WHERE slug = 'projet-ajoute'"
            ).fetchone())

        response = self.post_form("/projects/save", data={
            "title": "Projet ajouté",
            "summary": "Résumé du projet.",
            "description": "Description du projet.",
            "skills": "Python",
            "keywords": "python, analyse",
            "highlights": "Test documenté",
            "public_url": "",
        })
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertIsNotNone(candidatures_app.get_db().execute(
                "SELECT id FROM projects WHERE slug = 'projet-ajoute'"
            ).fetchone())

    def test_relevant_projects_are_persisted_and_used_in_cv_prompt_and_content(self):
        response = self.post_form("/applications", data={
            "company": "TotalEnergies",
            "position": "Ingénieur Data Solaire et IA",
            "job_description": (
                "Analyser la production photovoltaïque, détecter les anomalies "
                "des onduleurs et prévoir la production avec un modèle LSTM."
            ),
        })
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            choices = candidatures_app.ensure_application_project_choices(application)
            self.assertEqual(choices[0]["slug"], "solarwatch")
            solarwatch = next(item for item in choices if item["slug"] == "solarwatch")
            self.assertEqual(solarwatch["is_selected"], 1)
            projects = candidatures_app.selected_application_projects(application_id)
            prompt = candidatures_app.build_prompt(
                "cv",
                candidatures_app.get_profile(),
                application,
                selected_projects=projects,
            )
            self.assertIn("PROJETS PERSONNELS SÉLECTIONNÉS", prompt)
            self.assertIn("Le jeu ne contient pas de pannes labellisées", prompt)

            cv = candidatures_app.inject_selected_projects("PROFIL\nData analyst.", projects)
            self.assertIn("PROJETS", cv)
            self.assertIn("Projet personnel", cv)
            self.assertIn("alertes candidates", cv)
            self.assertNotIn("PROJETS\nSolarWatch\nUn résultat inventé", cv)
            self.assertLessEqual(len(projects), 2)

    def test_cv_includes_both_selected_projects_in_the_original_layout(self):
        projects = [
            {
                "title": "Projet le plus pertinent",
                "summary": "Surveillance photovoltaïque.",
                "skills": "Python, pandas, LSTM",
                "highlights": "C-index de 0,71 sur test chronologique",
                "public_url": "https://github.com/example/solar",
            },
            {
                "title": "Projet secondaire",
                "summary": "Autre projet de machine learning.",
                "skills": "Python, scikit-learn",
                "highlights": "Résultat secondaire",
                "public_url": "",
            },
            {
                "title": "Projet statistique",
                "summary": "Analyse statistique vérifiable.",
                "skills": "R, Stan",
                "highlights": "",
                "public_url": "",
            },
            {
                "title": "Projet supplémentaire",
                "summary": "Autre analyse de données.",
                "skills": "Python, SQL",
                "highlights": "",
                "public_url": "",
            },
        ]
        content = candidatures_app.inject_selected_projects(
            "PROFIL\nData analyst.\nFORMATION\nMaster Data", projects
        )
        self.assertIn("Projet le plus pertinent", content)
        self.assertIn("C-index de 0,71 sur test chronologique", content)
        self.assertIn("https://github.com/example/solar", content)
        self.assertIn("Projet secondaire", content)
        self.assertIn("Projet statistique", content)
        self.assertIn("Projet supplémentaire", content)

        source = candidatures_app.make_cv_latex(
            {"full_name": "Nom Exemple", "email": "", "phone": "", "location": ""},
            {"position": "Data Analyst", "company": "Exemple"},
            content,
        )
        self.assertIn(r"\cvsection{Projets}", source)
        self.assertIn(r"\href{\detokenize{https://github.com/example/solar}}", source)
        self.assertIn("Projet secondaire", source)
        self.assertIn("Projet statistique", source)
        self.assertIn("Projet supplémentaire", source)
        if candidatures_app.shutil.which("xelatex"):
            pdf = PdfReader(candidatures_app.compile_latex(source, one_page=True))
            self.assertEqual(len(pdf.pages), 1)
            self.assertIn("Projet le plus pertinent", pdf.pages[0].extract_text())

    def test_cv_project_title_uses_a_single_plain_hyphen(self):
        project = {
            "title": "Pipeline MLOps — classification du cancer du sein",
            "summary": "Pipeline reproductible.",
            "skills": "Python, scikit-learn",
            "highlights": "",
            "public_url": "",
        }
        cv = candidatures_app.inject_selected_projects("PROFIL\nData analyst.", [project])
        self.assertIn("Pipeline MLOps - classification du cancer du sein", cv)
        self.assertNotIn("—", cv)
        self.assertNotIn("–", cv)

    def test_cv_injection_replaces_all_duplicate_project_sections(self):
        draft = (
            "PROFIL\nData analyst.\n"
            "PROJETS\nAncien projet un\n- Description une.\n"
            "FORMATION\nMaster Data\n"
            "PROJECTS\nAncien projet deux\n- Description deux.\n"
        )
        projects = [{
            "title": "Projet sélectionné",
            "summary": "Résumé vérifié.",
            "skills": "Python",
            "highlights": "Résultat vérifiable",
            "public_url": "",
        }]
        updated = candidatures_app.inject_selected_projects(draft, projects)
        self.assertEqual(
            sum(
                candidatures_app.CV_SECTION_ALIASES.get(
                    candidatures_app.normalize_heading(line),
                    candidatures_app.normalize_heading(line),
                ) == "PROJETS"
                for line in updated.splitlines()
            ),
            1,
        )
        self.assertIn("Projet sélectionné", updated)
        self.assertNotIn("Ancien projet un", updated)
        self.assertNotIn("Ancien projet deux", updated)
        self.assertLess(updated.index("PROJETS"), updated.index("FORMATION"))

    def test_application_project_selection_is_limited_to_four(self):
        self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Data",
            "job_description": "machine learning data science Python analyse",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
            choices = candidatures_app.ensure_application_project_choices(
                candidatures_app.get_application(application_id)
            )
            project_ids = [str(choice["id"]) for choice in choices[:5]]
        response = self.post_form(
            f"/applications/{application_id}/projects",
            data={"project_ids": project_ids[:4]},
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            selected = candidatures_app.selected_application_projects(application_id)
            self.assertEqual(len(selected), 4)
        self.post_form(
            f"/applications/{application_id}/projects",
            data={"project_ids": project_ids},
        )
        with candidatures_app.app.app_context():
            selected = candidatures_app.selected_application_projects(application_id)
            self.assertEqual(len(selected), 4)

    def test_experience_selection_is_per_application_and_filters_base_cv(self):
        base_cv = (
            "PROFIL\nStatisticien.\n"
            "EXPERIENCES PROFESSIONNELLES\n"
            "Statisticien budgétaire\nDirection financière\n2022 - 2024\n"
            "- Suivi budgétaire et analyse des écarts.\n"
            "Assistant commercial\nEntreprise Exemple\n2020 - 2021\n"
            "- Gestion des ventes et suivi des clients.\n"
            "FORMATION\nMaster Statistique\n"
        )
        self.post_form("/profile", data={"resume_source": "Statisticien.", "base_cv": base_cv})
        self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Statisticien suivi budgétaire",
            "job_description": "Suivi budgétaire et analyse statistique.",
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            choices = candidatures_app.ensure_application_experience_choices(
                application, base_cv
            )
            selected_key = next(
                choice["experience_key"]
                for choice in choices
                if choice["organisation"] == "Direction financière"
            )

        response = self.post_form(
            f"/applications/{application_id}/experiences",
            data={"experience_keys": [selected_key]},
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            choices = candidatures_app.ensure_application_experience_choices(
                application, base_cv
            )
            self.assertEqual(
                [item["organisation"] for item in candidatures_app.selected_application_experiences(choices)],
                ["Direction financière"],
            )

        response = self.post_form(
            f"/applications/{application_id}/draft/from-base",
            data={},
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            draft = candidatures_app.get_application(application_id)["cv_draft"]
        self.assertIn("Direction financière", draft)
        self.assertNotIn("Entreprise Exemple", draft)

    def test_project_primary_choice_is_respected_and_generation_saves_unsaved_selection(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python, machine learning."})
        self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Ingénieur data énergie",
            "job_description": (
                "Projet solaire photovoltaïque, détection d'anomalies, prévision LSTM. "
                "Pipeline reproductible machine learning avec scikit-learn et régression logistique."
            ),
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            choices = candidatures_app.ensure_application_project_choices(application)
            solarwatch = next(item for item in choices if item["slug"] == "solarwatch")
            mlops = next(item for item in choices if item["slug"] == "mlops-breast-cancer")
            error = candidatures_app.save_application_project_selection(
                application,
                [str(solarwatch["id"]), str(mlops["id"])],
                str(solarwatch["id"]),
            )
            self.assertIsNone(error)
            selected = candidatures_app.selected_application_projects(application_id)
            self.assertEqual(selected[0]["slug"], "solarwatch")

        page = self.client.get(f"/?selected={application_id}")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'name="primary_project_id"', page.data)
        self.assertIn(b"project_selection_submitted", page.data)

        desired_id = str(mlops["id"])
        other_selected_id = str(solarwatch["id"])
        with patch(
            "app.generate_with_ollama",
            return_value="PROFIL\nAnalyste de données.\nFORMATION\nMaster Data.",
        ):
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv",
                    "provider": "ollama",
                    "project_selection_submitted": "1",
                    "project_ids": [other_selected_id, desired_id],
                    "primary_project_id": desired_id,
                },
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            selected = candidatures_app.selected_application_projects(application_id)
            self.assertEqual(
                [project["slug"] for project in selected],
                ["mlops-breast-cancer", "solarwatch"],
            )
            self.assertIn("Pipeline MLOps - classification du cancer du sein", application["cv_draft"])
            self.assertIn("SolarWatch - surveillance", application["cv_draft"])

    def test_home_page_renders_one_application_table_header(self):
        self.post_form(
            "/applications",
            data={"company": "Exemple SA", "position": "Analyste"},
        )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b"<th>Poste</th>"), 1)

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

    def test_latex_reference_extracts_readable_cv_content(self):
        source = r"""\documentclass{article}
\newcommand{\cvsection}[1]{command definition}
\begin{document}
\textcolor{accent}{DATA SCIENTIST}
\cvsection{Expériences professionnelles}
\cventry{DATA SCIENTIST}{ACME}{2024 - 2025}
\begin{cvitems}
\item Analyser les données avec Python.
\item Utiliser SQL et Power BI.
\end{cvitems}
\cvsection{Compétences clés}
\begin{cvitems}
\item Modélisation statistique
\end{cvitems}
\end{document}"""
        extracted = candidatures_app.extract_latex_text(source)
        self.assertIn("Expériences professionnelles", extracted)
        self.assertIn("DATA SCIENTIST", extracted)
        self.assertIn("Analyser les données avec Python.", extracted)
        self.assertIn("Modélisation statistique", extracted)
        self.assertNotIn("documentclass", extracted)
        self.assertNotIn("command definition", extracted)
        self.assertNotIn("accent", extracted)

    def test_reference_documents_are_combined_deduplicated_and_removable(self):
        response = self.post_form(
            "/reference-documents",
            data={
                "reference_files": [
                    (
                        io.BytesIO(
                            b"\\begin{document}\\cvsection{Competences}\\item SQL\\item Python\\end{document}"
                        ),
                        "cv-data.tex",
                    ),
                    (io.BytesIO(b"Python\nPower BI\nR"), "cv-bi.txt"),
                ]
            },
        )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            documents = candidatures_app.get_reference_documents()
            self.assertEqual(len(documents), 2)
            profile = dict(candidatures_app.get_profile())
            profile["resume_source"] = "SQL\nPython"
            prompt = candidatures_app.build_prompt(
                "cv",
                profile,
                {"position": "Data Analyst", "company": "Exemple", "location": "", "job_description": "SQL"},
                documents,
            )
            self.assertIn("Power BI", prompt)
            self.assertEqual(prompt.count("Python"), 1)
            document_id = documents[0]["id"]

        response = self.post_form(f"/reference-documents/{document_id}/delete", data={})
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertEqual(len(candidatures_app.get_reference_documents()), 1)

    def test_generation_can_use_reference_documents_without_primary_cv_text(self):
        self.post_form(
            "/applications",
            data={
                "company": "Exemple",
                "position": "Data Analyst",
                "job_description": "Power BI et SQL.",
            },
        )
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
        self.post_form(
            "/reference-documents",
            data={"reference_files": [(io.BytesIO(b"SQL\nPower BI\nReporting"), "cv.txt")]},
        )
        with patch("app.generate_with_ollama", return_value="PROFIL\nAnalyste.") as generate:
            response = self.post_form(
                f"/applications/{application_id}/draft", data={"kind": "cv"}
            )
        self.assertEqual(response.status_code, 302)
        self.assertIn("Power BI", generate.call_args.args[0])
        with candidatures_app.app.app_context():
            self.assertEqual(
                candidatures_app.get_application(application_id)["cv_draft"],
                    "PROFIL\nAnalyste.\n\nPROJETS\n"
                    "Tableau de bord Power BI - transactions en Inde\n"
                    "Projet personnel\n"
                    "- Rapport interactif orienté métier pour explorer les montants "
                    "de transactions par secteur, genre, État, année et âge.\n"
                    "- Technologies : Power BI, conception de tableaux de bord, "
                    "visualisation de données, analyse métier, Power Automate, "
                    "automatisation de l'actualisation",
                )

    def test_copilot_generation_requires_consent_and_uses_selected_provider(self):
        self.post_form(
            "/profile",
            data={"resume_source": "Analyste de données, Python et SQL."},
        )
        self.post_form(
            "/applications",
            data={
                "company": "Exemple",
                "position": "Data Analyst",
                "job_description": "Python et SQL.",
            },
        )
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]

        with patch("app.generate_with_copilot", return_value="PROFIL\nAnalyste.") as generate:
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={"kind": "cv", "provider": "copilot"},
            )
            self.assertEqual(response.status_code, 302)
            generate.assert_not_called()

            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv",
                    "provider": "copilot",
                    "allow_cloud": "yes",
                },
            )
        self.assertEqual(response.status_code, 302)
        generate.assert_called_once()
        with candidatures_app.app.app_context():
            self.assertEqual(
                candidatures_app.get_application(application_id)["cv_draft"],
                "PROFIL\nAnalyste.",
            )

    def test_empty_copilot_draft_is_not_saved(self):
        self.post_form("/profile", data={"resume_source": "SQL et Python."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst",
            "job_description": "SQL et Python.",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
        with patch("app.generate_with_copilot", return_value=""):
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={"kind": "cv", "provider": "copilot", "allow_cloud": "yes"},
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            self.assertEqual(
                candidatures_app.get_application(application_id)["cv_draft"], ""
            )
        page = self.client.get(f"/?selected={application_id}")
        self.assertIn(b"Copilot a renvoy", page.data)
        self.assertIn(b"Aucun brouillon", page.data)

    def test_style_examples_guide_qwen_only(self):
        self.post_form("/profile", data={"resume_source": "Analyste, Python."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst", "job_description": "Python."})
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications").fetchone()["id"]
        good = "PROFIL\nAnalyste rigoureux.\n" + "ligne\n" * 600
        with patch("app.generate_with_copilot", return_value=good):
            self.post_form(f"/applications/{application_id}/draft", data={
                "kind": "cv", "provider": "copilot", "allow_cloud": "yes"})
        self.post_form(f"/applications/{application_id}/example", data={"kind": "cv"})
        self.post_form(f"/applications/{application_id}/example", data={"kind": "cv"})
        with patch(
            "app.generate_with_copilot",
            return_value="Madame, Monsieur,\nVotre offre m'intéresse.\nJe vous prie d'agréer.",
        ):
            self.post_form(f"/applications/{application_id}/draft", data={
                "kind": "letter", "provider": "copilot", "allow_cloud": "yes"})
        self.post_form(f"/applications/{application_id}/example", data={"kind": "letter"})
        with candidatures_app.app.app_context():
            examples = candidatures_app.get_style_examples()
            self.assertEqual(len(examples), 2)
            application = candidatures_app.get_application(application_id)
            prompt = candidatures_app.build_prompt(
                "cv", candidatures_app.get_profile(), application, (), examples)
            self.assertIn("EXEMPLES DE CV VALIDÉS", prompt)
            self.assertIn("Analyste rigoureux", prompt)
            self.assertNotIn("Votre offre m'intéresse", prompt)
            self.assertLess(len(prompt) - len(candidatures_app.build_prompt(
                "cv", candidatures_app.get_profile(), application)), 2500)
            letter_prompt = candidatures_app.build_prompt(
                "letter", candidatures_app.get_profile(), application, (), examples)
            self.assertIn("EXEMPLES DE LETTRES DE MOTIVATION VALIDÉS", letter_prompt)
            self.assertIn("Votre offre m'intéresse", letter_prompt)
            self.assertNotIn("EXEMPLES DE CV VALIDÉS", letter_prompt)
            english_letter_prompt = candidatures_app.build_prompt(
                "letter", candidatures_app.get_profile(), application, (), examples, "en")
            self.assertIn("Votre offre m'intéresse", english_letter_prompt)

        with patch("app.generate_with_ollama", return_value="PROFIL\nOk.") as ollama:
            self.post_form(f"/applications/{application_id}/draft", data={"kind": "cv"})
        self.assertIn("Analyste rigoureux", ollama.call_args.args[0])
        self.assertEqual(ollama.call_args.kwargs["num_ctx"], candidatures_app.OLLAMA_CONTEXT_WITH_EXAMPLES)

        with patch("app.generate_with_ollama", return_value="Madame, Monsieur.\nCordialement.") as ollama:
            self.post_form(f"/applications/{application_id}/draft", data={
                "kind": "letter", "language": "en"})
        self.assertIn("Votre offre m'intéresse", ollama.call_args.args[0])
        self.assertEqual(ollama.call_args.kwargs["num_ctx"], candidatures_app.OLLAMA_CONTEXT_WITH_EXAMPLES)

        with patch("app.generate_with_copilot", return_value="Madame, Monsieur.\nCordialement.") as copilot:
            self.post_form(f"/applications/{application_id}/draft", data={
                "kind": "letter", "provider": "copilot", "allow_cloud": "yes"})
        self.assertNotIn("EXEMPLES", copilot.call_args.args[0])

        for example in examples:
            self.post_form(f"/style-examples/{example['id']}/delete", data={})
        with candidatures_app.app.app_context():
            self.assertEqual(candidatures_app.get_style_examples(), [])

    def test_free_api_uses_multiple_saved_cv_examples_and_requested_language(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst",
            "job_description": "Analyser des données avec Python.",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
            database = candidatures_app.get_db()
            for index in range(1, 5):
                database.execute(
                    """INSERT INTO style_examples (kind, label, content, created_at)
                       VALUES ('cv', ?, ?, ?)""",
                    (f"CV {index}", f"Validated CV example {index}", f"2026-01-0{index}"),
                )
            database.execute(
                """INSERT INTO style_examples (kind, label, content, created_at)
                   VALUES ('letter', 'Letter', 'Validated letter example', '2026-01-05')"""
            )
            database.commit()

        with patch("app.generate_with_free_api", return_value="PROFILE\nData analyst.") as generate:
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv", "provider": "api", "allow_cloud": "yes", "language": "en",
                },
            )
        self.assertEqual(response.status_code, 302)
        prompt = generate.call_args.args[0]
        self.assertIn("Validated CV example 4", prompt)
        self.assertIn("Validated CV example 3", prompt)
        self.assertIn("Validated CV example 2", prompt)
        self.assertNotIn("Validated CV example 1", prompt)
        self.assertNotIn("Validated letter example", prompt)
        self.assertIn("Respecte strictement la langue demandée", prompt)
        self.assertIn("reproduis au plus près la structure de l'exemple", prompt)

    def test_openrouter_truncated_response_is_not_saved_as_cv(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python."})
        self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Data Scientist",
            "job_description": "Classify activities from smartphone sensors.",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]

        response_body = json.dumps({
            "model": "provider/model",
            "choices": [{
                "message": {
                    "content": (
                        "PROFILE\nData analyst.\nPROJECTS\n"
                        "HUMAN ACTIVITY RECOGNITION FROM SMARTPHONE SENSORS\n"
                        "Personal project\n"
                        "• Comparative classification of physical activities "
                        "(walking, stairs, sitting"
                    )
                },
                "finish_reason": "length",
            }],
        }).encode()
        api_response = Mock()
        api_response.__enter__ = Mock(return_value=api_response)
        api_response.__exit__ = Mock(return_value=False)
        api_response.read.return_value = response_body
        with (
            patch.dict("os.environ", {"LLM_API_KEY": "test-key"}),
            patch.object(candidatures_app, "FREE_API_MODELS", ["openrouter/free"]),
            patch("app.urlopen", return_value=api_response),
        ):
            result = self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv",
                    "provider": "api",
                    "allow_cloud": "yes",
                    "language": "en",
                },
            )

        self.assertEqual(result.status_code, 302)
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            self.assertEqual(application["cv_draft"], "")

    def test_index_shows_keyword_gap_for_selected_offer(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python, SQL."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst",
            "job_description": "Python, SQL et Snowflake exigés.",
        })

        html = self.client.get("/").get_data(as_text=True)

        self.assertIn("Compatibilité ATS", html)
        self.assertIn("67 % couverts", html)
        self.assertIn("Snowflake", html)

    def test_spontaneous_application_without_offer_ranks_projects_and_builds_prompt(self):
        self.post_form("/profile", data={"resume_source": "Statisticien, R, analyse de survie."})
        self.post_form("/applications", data={
            "company": "Laboratoire Exemple", "position": "Biostatisticien",
            "job_description": "", "spontaneous_domain": "biostatistique",
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            self.assertTrue(candidatures_app.is_spontaneous(application["job_description"]))
            slugs = {
                project["slug"] for project in candidatures_app.get_projects()
            }
            ranked = candidatures_app.rank_projects(
                application["job_description"], candidatures_app.get_projects()
            )
            prompt = candidatures_app.build_prompt(
                "letter", candidatures_app.get_profile(), application, language="fr"
            )

        self.assertTrue({"detection-qtl-r", "inference-reseau", "challenge-qrt"} <= slugs)
        self.assertEqual(ranked[0]["match_score"], 100)
        self.assertIn("CANDIDATURE SPONTANEE", prompt)
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Compatibilité ATS", html)
        self.assertNotIn("disabled>Générer le brouillon", html)

    def test_offer_text_wins_over_spontaneous_domain(self):
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst",
            "job_description": "Offre réelle : Power BI.", "spontaneous_domain": "biostatistique",
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
        self.assertEqual(application["job_description"], "Offre réelle : Power BI.")

    def test_profile_variant_is_chosen_from_offer_and_hidden_from_cv(self):
        base = (
            "PROFIL\nProfil général.\nEXPERIENCES PROFESSIONNELLES\nAnalyste, Acme, Avr 2024 - Sep 2024\n- Rapports.\n"
            "PROFILS ALTERNATIFS\nbiostatistique : Profil biostatistique.\ndata-analyst : Profil BI.\n"
        )
        text, variants = candidatures_app.split_profile_variants(base)
        self.assertNotIn("ALTERNATIFS", text)
        self.assertEqual(set(variants), {"biostatistique", "data-analyst"})
        self.assertEqual(
            candidatures_app.choose_profile_variant(variants, "Analyse de survie, essais cliniques, R, SAS"),
            "Profil biostatistique.",
        )
        self.assertEqual(
            candidatures_app.choose_profile_variant(variants, "Power BI, DAX, tableaux de bord"),
            "Profil BI.",
        )
        field_variants = {
            "oceanographie": "Profil océanographique.",
            "aerospace": "Profil aérospatial.",
            "biostatistique": "Profil santé.",
        }
        self.assertEqual(
            candidatures_app.choose_profile_variant(
                field_variants,
                "Ingénieur statisticien en océanographie, données océaniques et Copernicus Marine",
            ),
            "Profil océanographique.",
        )
        self.assertEqual(
            candidatures_app.choose_profile_variant(
                field_variants,
                "Statisticien données aéronautiques, fiabilité des avions",
            ),
            "Profil aérospatial.",
        )
        self.assertEqual(
            candidatures_app.choose_profile_variant(
                {"oceanographie": "Profil océanographique."},
                "Analyse de NetCDF avec xarray et données marines",
            ),
            "Profil océanographique.",
        )
        self.assertEqual(
            candidatures_app.choose_profile_variant(
                {"data-analyst": "Profil Data Analyst.", "data-engineering": "Profil Data Engineer."},
                "Data Engineer, intégration de données, ETL et SQL",
            ),
            "Profil Data Engineer.",
        )
        self.assertIsNone(candidatures_app.choose_profile_variant(variants, "Boulanger"))
        draft = candidatures_app.apply_profile_variant(text, "Profil BI.")
        self.assertIn("Profil BI.", draft)
        self.assertNotIn("Profil général.", draft)
        self.assertIn("Acme", draft)

    def test_model_generated_cv_uses_offer_specific_validated_profile_variant(self):
        base_cv = (
            "PROFIL\nProfil général centré sur la génétique.\n"
            "EXPERIENCES PROFESSIONNELLES\nStatisticien, Exemple\n- Analyse statistique.\n"
            "PROFILS ALTERNATIFS\n"
            "oceanographie : Statisticien orienté vers l'analyse de données océaniques et la prévision environnementale.\n"
            "aerospace : Analyste de données appliqué aux systèmes aéronautiques et à la fiabilité industrielle.\n"
            "biostatistique : Statisticien en santé, analyse de survie et génétique statistique.\n"
        )
        self.post_form("/profile", data={
            "resume_source": (
                "Master en Ingénierie Statistique. Expérience en analyse de données "
                "océanographiques et en prévision environnementale."
            ),
            "base_cv": base_cv,
        })
        self.post_form("/applications", data={
            "company": "Institut océanographique",
            "position": "Ingénieur statisticien en océanographie",
            "job_description": (
                "Analyse de données océaniques, océanographie physique, Copernicus Marine."
            ),
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            prompt = candidatures_app.build_prompt(
                "cv",
                candidatures_app.get_profile(),
                application,
                language="fr",
            )
        self.assertIn("profil alternatif déjà validé", prompt.lower())
        self.assertIn("données océaniques", prompt.lower())

        generated_cv = (
            "PROFIL\nTitulaire d’un Master en Ingénierie Statistique, spécialisé "
            "en génétique statistique.\n"
            "EXPERIENCES PROFESSIONNELLES\nStatisticien, Exemple\n- Analyse statistique.\n"
        )
        with patch("app.generate_with_free_api", return_value=generated_cv):
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={"kind": "cv", "provider": "api", "allow_cloud": "yes", "language": "fr"},
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            saved_cv = candidatures_app.get_application(application_id)["cv_draft"]
        self.assertIn("données océaniques", saved_cv)
        self.assertNotIn("génétique statistique", saved_cv)

    def test_cv_built_from_base_without_model_and_manual_edit_is_saved(self):
        base = (
            "PROFIL\nStatisticien orienté données.\n"
            "EXPERIENCES PROFESSIONNELLES\nDATA SCIENTIST\nPOKAPOK\n- Modélisation prédictive.\n"
            "Compétences : Python, Docker\nFORMATION\nMaster Data Sciences | Angers Universités | 2025 - 2026"
        )
        self.post_form("/profile", data={"resume_source": "x", "base_cv": base})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Scientist", "job_description": "Docker et Python.",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
        with patch("app.generate_with_ollama") as model:
            response = self.post_form(f"/applications/{application_id}/draft/from-base", data={})
        self.assertEqual(response.status_code, 302)
        model.assert_not_called()
        with candidatures_app.app.app_context():
            draft = candidatures_app.get_application(application_id)["cv_draft"]
        self.assertIn("Statisticien orienté données.", draft)
        self.assertIn("POKAPOK", draft)

        self.post_form(
            f"/applications/{application_id}/draft/save",
            data={"kind": "cv", "content": draft + "\nLANGUES\nFrançais"},
        )
        with candidatures_app.app.app_context():
            saved = candidatures_app.get_application(application_id)["cv_draft"]
        self.assertTrue(saved.endswith("Français"))

    def test_english_cv_does_not_replace_translated_project_with_french_source(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Scientist",
            "job_description": "Build statistical models and data workflows.",
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            project = candidatures_app.get_db().execute(
                "SELECT id FROM projects WHERE slug = 'solarwatch'"
            ).fetchone()
            error = candidatures_app.save_application_project_selection(
                application, [str(project["id"])], str(project["id"])
            )
            self.assertIsNone(error)

        generated_cv = (
            "PROFILE\nData analyst.\n\nPROJECTS\nSolarWatch monitoring\n"
            "Personal project\n- Monitor photovoltaic performance.\n"
        )
        with patch("app.generate_with_free_api", return_value=generated_cv):
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv", "provider": "api", "allow_cloud": "yes", "language": "en",
                },
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            saved_cv = candidatures_app.get_application(application_id)["cv_draft"]
        self.assertIn("Personal project", saved_cv)
        self.assertIn("Monitor photovoltaic performance.", saved_cv)
        self.assertNotIn("Projet personnel", saved_cv)

    def test_copilot_generator_uses_sdk_without_local_tools(self):
        from copilot.generated.session_events import AssistantMessageData

        calls = {}

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def send_and_wait(self, prompt, timeout):
                calls["prompt"] = prompt
                calls["timeout"] = timeout
                return SimpleNamespace(
                    data=AssistantMessageData(content="Brouillon Copilot", message_id="test")
                )

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def create_session(self, **kwargs):
                calls["session_options"] = kwargs
                return FakeSession()

        with patch("copilot.CopilotClient", return_value=FakeClient()):
            result = candidatures_app.generate_with_copilot("Prompt de test", 100)

        self.assertEqual(result, "Brouillon Copilot")
        self.assertEqual(calls["prompt"], "Prompt de test")
        self.assertEqual(calls["timeout"], candidatures_app.COPILOT_TIMEOUT)
        self.assertEqual(calls["session_options"]["available_tools"], [])
        self.assertFalse(calls["session_options"]["enable_config_discovery"])
        self.assertEqual(
            calls["session_options"]["on_permission_request"](None, None).kind,
            "reject",
        )

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

    def test_ollama_uses_configured_remote_server(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = json.dumps(
            {"message": {"content": "OK"}}
        ).encode("utf-8")

        with patch("app.OLLAMA_BASE_URL", "https://colab.example"), patch(
            "app.urlopen", return_value=response
        ) as request:
            result = candidatures_app.generate_with_ollama("test", max_tokens=20)

        sent_request = request.call_args.args[0]
        self.assertEqual(result, "OK")
        self.assertEqual(sent_request.full_url, "https://colab.example/api/chat")
        self.assertEqual(sent_request.get_method(), "POST")

    def test_ollama_status_checks_configured_remote_server(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = json.dumps(
            {"models": [{"name": candidatures_app.MODEL_NAME}]}
        ).encode("utf-8")

        with patch("app.OLLAMA_BASE_URL", "https://colab.example"), patch(
            "app.urlopen", return_value=response
        ) as request:
            status = candidatures_app.ollama_status()

        self.assertTrue(status["ready"])
        self.assertEqual(request.call_args.args[0].full_url, "https://colab.example/api/tags")

    def test_french_cv_translates_english_degree_titles(self):
        result = candidatures_app.frenchify_degree_titles(
            "Master’s degree in Data Sciences\nMaster's degree in Engineering Statistics"
        )
        self.assertEqual(result, "Master Data Sciences\nMaster Engineering Statistics")

    def test_long_project_title_is_rendered_as_entry_header(self):
        title = "Classification de l’activité humaine à partir de capteurs de smartphone (Human Activity Recognition)"
        output = candidatures_app.latex_entries(
            [title, "Projet personnel", "- Résumé du projet.", "- Technologies : Python, SVM"],
            max_items=2, max_entries=1, max_header_chars=160,
        )
        self.assertTrue(output[0].startswith(r"\cventry"))
        self.assertIn("Projet personnel", output[0])
        self.assertTrue(any(line.startswith(r"\cvskills") for line in output))

    def test_hedged_project_phrases_are_removed(self):
        skills = (
            "Python, SVM, régression logistique, éventuellement un réseau de neurones "
            "(MLP, CNN 1D ou LSTM), PCA, matrice de confusion"
        )
        self.assertEqual(
            candidatures_app.remove_hedged_phrases(skills),
            "Python, SVM, régression logistique, PCA, matrice de confusion",
        )

    def test_ollama_timeout_does_not_repeat_long_generation(self):
        with patch("app.urlopen", side_effect=URLError(TimeoutError("timed out"))) as request:
            with self.assertRaisesRegex(RuntimeError, "modèle Ollama n'a pas terminé"):
                candidatures_app.generate_with_ollama("test", max_tokens=20)
        self.assertEqual(request.call_count, 1)

    def test_latex_export_rejects_unreadable_pdf_output(self):
        def write_invalid_pdf(*_args, **kwargs):
            (Path(kwargs["cwd"]) / "cv.pdf").write_bytes(b"not a PDF")
            return Mock()

        with patch("app.shutil.which", return_value="xelatex"), patch(
            "app.subprocess.run", side_effect=write_invalid_pdf
        ):
            with self.assertRaisesRegex(RuntimeError, "PDF compilé est illisible"):
                candidatures_app.compile_latex(r"\documentclass{article}\begin{document}CV\end{document}")

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

    def test_cv_draft_removes_contact_details_added_by_document_layout(self):
        draft = (
            "PROFIL\nNom : Nom Exemple\nE-mail : nom@example.com\n"
            "Telephone : 0600000000\nLocalisation : Angers\n"
            "Analyste de donnees.\nCOMPETENCES CLES\n- SQL"
        )
        cleaned = candidatures_app.clean_cv_draft(draft)
        self.assertNotIn("Nom :", cleaned)
        self.assertNotIn("E-mail :", cleaned)
        self.assertNotIn("Localisation :", cleaned)
        self.assertIn("Analyste de donnees.", cleaned)

    def test_letter_prompt_demands_offer_specific_evidence_and_short_body(self):
        profile = {
            "full_name": "Nom Exemple", "email": "nom@example.com", "phone": "",
            "location": "Angers", "resume_source": "SQL et Power BI chez ACME.",
            "certifications": "Power BI Bootcamp : DAX, visualisation interactive\n"
                              "Working with SSH : administration Linux",
        }
        application = {
            "position": "Data Analyst", "company": "Exemple", "location": "",
            "job_description": "SQL, Power BI et suivi d'indicateurs.",
            "cv_draft": (
                "PROFILE\nData analyst with documented SQL and Power BI experience.\n"
                "PROFESSIONAL EXPERIENCE\nData Analyst\nACME\n"
                "- Produced operational indicators with SQL and Power BI."
            ),
        }
        prompt = candidatures_app.build_prompt("letter", profile, application)
        self.assertIn("entièrement en français", prompt)
        self.assertIn("exactement 4 paragraphes de prose et 140 à 180 mots", prompt)
        self.assertIn("N'ajoute ni demande d'entretien", prompt)
        self.assertIn("coller le texte de son choix", prompt)
        self.assertIn("il est la source de référence prioritaire et limite les faits utilisables", prompt)
        self.assertIn("ne le mentionne que s'il figure dans le CV adapté", prompt)
        self.assertIn("ne copie aucune phrase anglaise", prompt)
        self.assertIn("Power BI Bootcamp : DAX, visualisation interactive", prompt)
        self.assertIn("Working with SSH : administration Linux", prompt)
        self.assertIn("N'invente aucun fait", prompt)
        english_prompt = candidatures_app.build_prompt(
            "letter", profile, application, language="en"
        )
        self.assertIn("Use only English throughout the letter", english_prompt)
        self.assertIn("it is the controlling source for the letter", english_prompt)
        self.assertIn("translate its descriptive title and details into English", english_prompt)
        self.assertIn("140 to 180 words total", english_prompt)

    def test_letter_uses_primary_selected_project_as_offer_evidence(self):
        self.post_form(
            "/profile",
            data={"resume_source": "Data analyst, Python, statistiques."},
        )
        self.post_form(
            "/applications",
            data={
                "company": "TotalEnergies",
                "position": "Ingénieur Data Solaire",
                "job_description": "Analyser la production photovoltaïque et prévoir l'énergie solaire.",
            },
        )
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            projects = {
                row["slug"]: row
                for row in candidatures_app.get_projects()
                if row["slug"] in {"solarwatch", "mlops-breast-cancer"}
            }
            error = candidatures_app.save_application_project_selection(
                application,
                [str(projects["solarwatch"]["id"]), str(projects["mlops-breast-cancer"]["id"])],
                str(projects["solarwatch"]["id"]),
            )
            self.assertIsNone(error)

        generated_letter = (
            "Je candidate au poste proposé chez TotalEnergies.\n\n"
            "Mon parcours comprend des expériences de data et de statistiques.\n\n"
            "Mon projet personnel SolarWatch documente la surveillance photovoltaïque avec Python. "
            "Ces compétences répondent aux besoins du poste et me permettront de contribuer aux analyses.\n\n"
            "Je souhaite rejoindre vos équipes et contribuer à vos missions."
        )
        with patch("app.generate_with_ollama", return_value=generated_letter) as generate:
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={"kind": "letter", "provider": "ollama", "language": "fr"},
            )
        self.assertEqual(response.status_code, 302)
        prompt = generate.call_args.args[0]
        self.assertIn("Projet personnel principal choisi", prompt)
        self.assertIn("SolarWatch - surveillance de performance photovoltaïque", prompt)
        self.assertNotIn("Pipeline MLOps", prompt)
        with candidatures_app.app.app_context():
            letter = candidatures_app.get_application(application_id)["letter_draft"]
            self.assertIn("Mon projet personnel SolarWatch", letter)
            self.assertNotIn("en mettant en pratique Python, pandas, scikit-learn, PyTorch", letter)
            self.assertNotIn("Pipeline MLOps", letter)
            self.assertLess(
                letter.index("SolarWatch"),
                letter.index("Ces compétences répondent"),
            )

    def test_english_letter_does_not_inject_a_french_project_title(self):
        self.post_form("/profile", data={"resume_source": "Data analyst, Python."})
        self.post_form("/applications", data={
            "company": "Example",
            "position": "Data Analyst",
            "job_description": "Analyze photovoltaic performance.",
        })
        with candidatures_app.app.app_context():
            application = candidatures_app.get_db().execute(
                "SELECT * FROM applications"
            ).fetchone()
            application_id = application["id"]
            project = candidatures_app.get_db().execute(
                "SELECT id FROM projects WHERE slug = 'solarwatch'"
            ).fetchone()
            error = candidatures_app.save_application_project_selection(
                application, [str(project["id"])], str(project["id"])
            )
            self.assertIsNone(error)
            candidatures_app.get_db().execute(
                "UPDATE applications SET cv_draft = ? WHERE id = ?",
                (
                    "PROFILE\nData analyst.\nPROJECTS\nSolarWatch monitoring.\n"
                    "Personal project\n- Monitor photovoltaic performance with Python.",
                    application_id,
                ),
            )
            candidatures_app.get_db().commit()

        generated_letter = (
            "I am applying for the Data Analyst position because it involves photovoltaic analysis.\n\n"
            "My documented data analysis experience includes Python.\n\n"
            "My personal project on photovoltaic monitoring demonstrates this approach.\n\n"
            "I would be pleased to contribute to the team's analytical work."
        )
        with patch("app.generate_with_free_api", return_value=generated_letter):
            self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "letter",
                    "provider": "api",
                    "allow_cloud": "yes",
                    "language": "en",
                },
            )
        with candidatures_app.app.app_context():
            letter = candidatures_app.get_application(application_id)["letter_draft"]
        self.assertEqual(letter, generated_letter)
        self.assertNotIn("surveillance de performance photovoltaïque", letter)

    def test_offer_matching_uses_certifications_without_misrepresenting_them(self):
        profile = {
            "resume_source": "",
            "certifications": "AWS Certified Machine Learning - Specialty : machine learning",
        }
        offer = {
            "position": "Machine Learning Engineer",
            "company": "Exemple",
            "description": "Développer et évaluer des modèles de machine learning.",
        }
        with patch("app.generate_with_ollama", return_value="SCORE: 81\nRAISON: Machine learning.") as generate:
            score, reason = candidatures_app.score_offer(profile, offer)
        self.assertEqual(score, 81)
        self.assertEqual(reason, "Machine learning.")
        prompt = generate.call_args.args[0]
        self.assertIn("AWS Certified Machine Learning - Specialty", prompt)
        self.assertIn("ne les confonds pas avec une expérience professionnelle", prompt)

    def test_letter_generation_uses_enough_tokens_for_complete_body(self):
        self.post_form(
            "/applications",
            data={"company": "Exemple", "position": "Data Analyst", "job_description": "SQL"},
        )
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
            candidatures_app.get_db().execute(
                "UPDATE profile SET resume_source = 'SQL chez ACME' WHERE id = 1"
            )
            candidatures_app.get_db().commit()
        with patch("app.generate_with_ollama", return_value="Paragraphe de test.") as generate:
            response = self.post_form(
                f"/applications/{application_id}/draft", data={"kind": "letter"}
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(generate.call_args.args[1], 600)

    def test_letter_generation_removes_automatic_interview_and_formal_closing(self):
        self.post_form("/profile", data={"resume_source": "SQL chez ACME."})
        self.post_form("/applications", data={
            "company": "Exemple", "position": "Data Analyst", "job_description": "SQL",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]
        response_body = (
            "Ma candidature correspond aux missions documentées.\n\n"
            "Je serai heureux de vous rencontrer lors d’un entretien.\n"
            "Je vous prie d’agréer, Madame, Monsieur, mes salutations distinguées."
        )
        with patch("app.generate_with_ollama", return_value=response_body):
            response = self.post_form(
                f"/applications/{application_id}/draft",
                data={"kind": "letter", "language": "fr"},
            )
        self.assertEqual(response.status_code, 302)
        with candidatures_app.app.app_context():
            saved = candidatures_app.get_application(application_id)["letter_draft"]
        self.assertIn("Ma candidature correspond", saved)
        self.assertNotIn("rencontrer", saved)
        self.assertNotIn("salutations distinguées", saved)

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
                "UPDATE profile SET full_name = ?, location = ?, email = ?, postal_address = ? WHERE id = 1",
                ("Nom Exemple", "Rennes", "nom@example.com", "12 rue des Donnees\n49000 Angers"),
            )
            application = database.execute("SELECT id FROM applications").fetchone()
            application_id = application["id"]
            database.execute(
                "UPDATE applications SET company = ?, letter_draft = ?, company_address = ? WHERE id = ?",
                (
                    "Baker Tilly",
                    "Motivation Letter\n\nMadame/Monsieur,\n\nÀ PROPOS\n"
                    "J'ai analyse des donnees et construit des modeles.\n\n"
                    "Je vous remercie pour l’attention portée à ma candidature.",
                    "20 avenue Exemple\n49000 Angers",
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
        self.assertIn("12 rue des Donnees", pdf_text)
        self.assertIn("Baker Tilly", pdf_text)
        self.assertIn("20 avenue Exemple", pdf_text)
        self.assertIn("Je vous remercie pour l’attention portée", pdf_text)
        self.assertNotIn("salutations distinguées", pdf_text)
        self.assertNotIn("rencontrer lors d’un entretien", pdf_text)
        self.assertGreaterEqual(pdf_text.count("Nom Exemple"), 2)
        self.assertNotIn("Motivation Letter", pdf_text)
        self.assertNotIn("A PROPOS", pdf_text)

    def test_cv_latex_escapes_special_characters_and_compiles(self):
        profile = {"full_name": "Jean & Co", "email": "a@b.fr", "phone": "0102", "location": "Lyon"}
        application = {"position": "Data_Analyst", "company": "X"}
        draft = (
            "PROFIL\nRigueur 100% \\input{secret} {x}\n"
            "EXPERIENCES PROFESSIONNELLES\nDATA ANALYST\nACME\n04/2026 - 09/2026\n- Dashboards #1\n"
        )
        source = candidatures_app.make_cv_latex(profile, application, draft)
        self.assertIn(r"Jean \& Co", source)
        self.assertIn(r"100\% \textbackslash{}input\{secret\} \{x\}", source)
        self.assertIn(r"\cventry{DATA ANALYST}{ACME}{04/2026 - 09/2026}", source)
        if candidatures_app.shutil.which("xelatex"):
            pdf_text = PdfReader(candidatures_app.compile_latex(source)).pages[0].extract_text()
            self.assertIn("Dashboards", pdf_text)

    def test_cv_prompt_and_layout_limit_experience_to_two_activities(self):
        profile = {
            "full_name": "Nom", "email": "", "phone": "", "location": "",
            "resume_source": "SQL, Python, Power BI",
        }
        application = {
            "position": "Data Analyst", "company": "Exemple",
            "location": "", "job_description": "SQL et Power BI.",
        }
        prompt = candidatures_app.build_prompt("cv", profile, application)
        self.assertIn("au plus deux puces courtes", prompt)
        self.assertIn("les expériences documentées les plus pertinentes", prompt)
        draft = (
            "EXPERIENCES PROFESSIONNELLES\nDATA ANALYST\nACME\n2024 – 2025\n"
            "- Activité une\n- Activité deux\n- Activité trois\n- Activité quatre\n"
            "Compétences : SQL, Power BI\nCOMPETENCES CLES\n- Analyse statistique\n"
            "APTITUDES\n- Esprit d'équipe\n"
        )
        source = candidatures_app.make_cv_latex(profile, application, draft)
        self.assertIn(r"\item Activité une", source)
        self.assertIn(r"\item Activité deux", source)
        self.assertNotIn(r"\item Activité trois", source)
        self.assertNotIn(r"\item Activité quatre", source)
        self.assertNotIn(r"\cvsection{Compétences clés}", source)
        self.assertNotIn(r"\cvsection{Aptitudes}", source)

    def test_cv_experiences_are_sorted_newest_to_oldest_across_formats(self):
        profile = {
            "full_name": "Nom Exemple",
            "email": "",
            "phone": "",
            "location": "",
        }
        application = {"position": "Data Analyst", "company": "Exemple"}
        draft = (
            "PROFIL\nAnalyste de données.\n"
            "EXPERIENCES PROFESSIONNELLES\n"
            "Data Scientist 03/2025 – 09/2025\nPOKAPOK\n"
            "- Mission POKAPOK.\n"
            "Data Analyst, Génétique Statistique\nUniversité d'Angers\n10/2025 – 02/2026\n"
            "- Mission Université.\n"
            "Data Analyst & BI Specialist 04/2026 – 09/2026\nParker Aerospace\n"
            "- Mission Parker.\n"
            "FORMATION\nMaster Data\n"
        )

        sorted_draft = candidatures_app.sort_cv_experience_sections(draft)
        self.assertLess(
            sorted_draft.index("Parker Aerospace"),
            sorted_draft.index("Université d'Angers"),
        )
        self.assertLess(
            sorted_draft.index("Université d'Angers"),
            sorted_draft.index("POKAPOK"),
        )

        source = candidatures_app.make_cv_latex(profile, application, draft)
        self.assertLess(
            source.index(r"\cventry{Data Analyst \& BI Specialist}"),
            source.index(r"\cventry{Data Analyst, Génétique Statistique}"),
        )
        self.assertLess(
            source.index(r"\cventry{Data Analyst, Génétique Statistique}"),
            source.index(r"\cventry{Data Scientist}"),
        )

        docx = Document(io.BytesIO(
            candidatures_app.make_cv_docx(profile, application, draft).getvalue()
        ))
        docx_text = "\n".join(paragraph.text for paragraph in docx.paragraphs)
        self.assertLess(docx_text.index("Parker Aerospace"), docx_text.index("Université d'Angers"))
        self.assertLess(docx_text.index("Université d'Angers"), docx_text.index("POKAPOK"))

        pdf = PdfReader(io.BytesIO(
            candidatures_app.make_pdf(profile, application, draft, "cv").getvalue()
        ))
        pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        self.assertLess(pdf_text.index("Parker Aerospace"), pdf_text.index("Université d'Angers"))
        self.assertLess(pdf_text.index("Université d'Angers"), pdf_text.index("POKAPOK"))

    def test_cv_experiences_with_named_months_are_sorted_and_dates_rendered(self):
        draft = (
            "PROFILE\nData analyst.\n"
            "PROFESSIONAL EXPERIENCE\n"
            "STATISTICIAN | BUDGET MONITORING Jan 2021 – Dec 2022\n"
            "Centre d'Enseignement Général\n- Managed budget monitoring.\n"
            "DATA ANALYST, GENETICS STATISTICS Oct 2025 – Feb 2026\n"
            "Université d'Angers\n- Analyzed genetic data.\n"
            "DATA ANALYST & BI SPECIALIST Apr 2026 – Sep 2026\n"
            "Parker Aerospace\n- Designed dashboards.\n"
            "EDUCATION\nMaster Data Sciences\n"
        )
        sorted_draft = candidatures_app.sort_cv_experience_sections(draft)
        self.assertLess(sorted_draft.index("Parker Aerospace"), sorted_draft.index("Université d'Angers"))
        self.assertLess(sorted_draft.index("Université d'Angers"), sorted_draft.index("Centre d'Enseignement Général"))

        latex = candidatures_app.make_cv_latex(
            {"full_name": "Nom", "email": "", "phone": "", "location": ""},
            {"position": "Data Analyst", "company": "Exemple"},
            draft,
        )
        self.assertLess(latex.index(r"\cventry{DATA ANALYST \& BI SPECIALIST}"), latex.index(r"\cventry{DATA ANALYST, GENETICS STATISTICS}"))
        self.assertIn("Apr 2026 - Sep 2026", latex)
        self.assertIn("Oct 2025 - Feb 2026", latex)
        self.assertEqual(
            candidatures_app.date_part_start_month("Oct 2025"),
            2025 * 12 + 10,
        )
        self.assertEqual(
            candidatures_app.date_part_start_month("Janvier 2021"),
            2021 * 12 + 1,
        )

    def test_cv_latex_splits_semicolon_education_and_fits_one_page(self):
        profile = {
            "full_name": "Moubarak LASSISSI",
            "location": "Angers",
            "email": "moubarak@example.com",
            "phone": "+33000000000",
            "certifications": (
                "AWS Certified Machine Learning - Specialty\nDocker and Kubernetes\n"
                "Foundations of Deep Reinforcement Learning with PyTorch\n"
                "Generative AI and LLMs: Architecture and Data Preparation\nWorking with SSH\n"
                "Databases and SQL for Data Science with Python\nPython with Jupyter Notebooks\n"
                "Power BI Bootcamp - Learn by Building a Real-World Project\n"
                "Azure DevOps and Continuous Delivery with Git\nAzure Devops Boards Projects\n"
                "Alteryx Mastery: Data Analytics & Workflow Automation\n"
                "Data Modeling with Power BI: Advanced DAX Calculations\n"
                "Creative Designing in Power BI\n"
                "Identifiant du diplôme : Creative Designing in Power BI\n"
                "Python for Data Science, AI & Development\n"
                "Developing AI Applications with Python and Flask"
            ),
            "languages": "Français : Langue maternelle\nAnglais : Professionnel",
        }
        application = {"position": "Data Scientist", "company": "Baker Tilly"}
        draft = """PROFIL
Data Scientist spécialisé en modélisation statistique et analyse de données. Expert R et SQL, maîtrise du traitement de données volumétriques et exploitation de sources administratives.
COMPETENCES CLES
- Conception et déploiement de modèles Machine Learning
- Analyse statistique avancée
- Préparation et structuration de données
- Conception de tableaux de bord interactifs
- Développement avec R, Python, SQL et Power BI
- Industrialisation avec Git, MLflow et Docker
EXPERIENCES PROFESSIONNELLES
DATA ANALYST & BI SPECIALIST 04/2026 – 09/2026
Parker Aerospace
- Produire et assurer la fiabilité des indicateurs de gestion et du reporting.
- Coordonner avec les équipes métier pour définir les besoins.
- Concevoir des tableaux de bord interactifs avec Power BI.
DATA ANALYST, GÉNÉTIQUE STATISTIQUE 10/2025 – 02/2026
Université d'Angers
- Analyser des données génétiques volumineuses.
- Réaliser des tests statistiques avancés.
- Développer du code statistique avec R.
DATA SCIENTIST 03/2025 – 09/2025
POKAPOK & IMT Atlantique
- Réaliser des analyses statistiques et modélisations prédictives.
- Industrialiser les analyses avec Git, MLflow et Docker.
- Analyser les erreurs de prédiction des modèles.
STATISTICIEN | SUIVI BUDGÉTAIRE 01/2021 – 12/2022
Centre d'Enseignement Général
- Gérer le suivi budgétaire et l'analyse des dépenses.
- Construire des indicateurs et tableaux de bord.
FORMATION
MASTER EN DATA SCIENCES 2025 – 2026 ; MASTER EN INGÉNIERIE STATISTIQUE ; Nantes Universités ; 2023 – 2025 ; LICENCE EN MATHÉMATIQUES ; Université de Brest ; 2022 – 2023 ; LICENCE MATHÉMATIQUES STATISTIQUES ; Université de Kara ; 2017 – 2020 ; APTITUDES
- Communication claire
- Flexibilité et adaptation
- Esprit d'équipe
LOGICIELS
- R
- Python
- SQL
- Power BI
- Git
- Spark
- Azure
"""
        source = candidatures_app.make_cv_latex(profile, application, draft)
        self.assertIn(r"\cventry{MASTER EN INGÉNIERIE STATISTIQUE}{Nantes Universités}{2023 - 2025}", source)
        self.assertIn(r"\cventry{MASTER EN DATA SCIENCES}{}{2025 - 2026}", source)
        self.assertNotIn("LICENCE", source)
        self.assertNotIn(r"\cvsection{Aptitudes}", source)
        self.assertNotIn(r"\cvsection{Compétences clés}", source)
        self.assertLess(source.index(r"\cvsection{Profil}"), source.index(r"\cvsection{Expériences professionnelles}"))
        self.assertNotIn("AWS Certified Machine Learning", source)
        self.assertNotIn("Developing AI Applications with Python and Flask", source)
        self.assertNotIn("Identifiant du diplôme", source)
        if candidatures_app.shutil.which("xelatex"):
            pdf = PdfReader(candidatures_app.compile_latex(source))
            self.assertEqual(len(pdf.pages), 1)
            text = pdf.pages[0].extract_text() or ""
            self.assertIn("Nantes Universités", text)
            self.assertNotIn("Université de Kara", text)
            self.assertNotIn("Communication claire", text)

    def test_cv_includes_only_certifications_relevant_to_job(self):
        profile = {
            "full_name": "Nom", "email": "", "phone": "", "location": "",
            "certifications": (
                "AWS Certified Machine Learning - Specialty\nDocker and Kubernetes\n"
                "Foundations of Deep Reinforcement Learning with PyTorch\n"
                "Generative AI and LLMs: Architecture and Data Preparation\n"
                "Working with SSH\nDatabases and SQL for Data Science with Python\n"
                "Power BI Bootcamp - Learn by Building a Real-World Project\n"
                "Alteryx Mastery: Data Analytics & Workflow Automation"
            ),
        }
        application = {
            "position": "Data Analyst",
            "job_description": "Créer des tableaux de bord Power BI et préparer les données avec SQL.",
        }
        source = candidatures_app.make_cv_latex(
            profile, application, "PROFIL\nAnalyste de données.\n"
        )
        self.assertIn("Power BI Bootcamp", source)
        self.assertIn("Databases and SQL for Data Science", source)
        self.assertNotIn("AWS Certified", source)
        self.assertNotIn("Working with SSH", source)
        self.assertEqual(
            candidatures_app.select_relevant_items(
                candidatures_app.profile_list(profile, "certifications"), application
            ),
            [
                "Power BI Bootcamp - Learn by Building a Real-World Project",
                "Databases and SQL for Data Science with Python",
            ],
        )

    def test_cv_project_public_link_is_clickable_in_exports(self):
        profile = {
            "full_name": "Nom Exemple",
            "email": "",
            "phone": "",
            "location": "",
        }
        application = {"position": "Data Analyst", "company": "Exemple"}
        url = "https://github.com/exemple/solarwatch"
        content = (
            "PROJETS\nSolarWatch\nProjet personnel\n"
            "- Résultat documenté : alertes candidates.\n"
            f"- À consulter : {url}"
        )

        latex = candidatures_app.make_cv_latex(profile, application, content)
        self.assertIn(rf"\href{{\detokenize{{{url}}}}}", latex)
        if candidatures_app.shutil.which("xelatex"):
            pdf_output = candidatures_app.compile_latex(latex, one_page=True)
            pdf = PdfReader(pdf_output)
            self.assertEqual(len(pdf.pages), 1)
            self.assertTrue(any(
                annotation.get_object().get("/A", {}).get("/URI") == url
                for annotation in pdf.pages[0].get("/Annots", [])
            ))

        docx_output = candidatures_app.make_cv_docx(profile, application, content)
        with zipfile.ZipFile(docx_output) as archive:
            relationships = archive.read("word/_rels/document.xml.rels").decode()
        self.assertIn(url, relationships)
        self.assertIn("TargetMode=\"External\"", relationships)

        pdf = PdfReader(io.BytesIO(candidatures_app.make_pdf(profile, application, content, "cv").getvalue()))
        annotations = pdf.pages[0].get("/Annots", [])
        self.assertTrue(any(
            annotation.get_object().get("/A", {}).get("/URI") == url
            for annotation in annotations
        ))

    def test_cv_keeps_only_tools_matching_the_job(self):
        profile = {
            "full_name": "Nom", "email": "", "phone": "", "location": "",
        }
        application = {
            "position": "Data Analyst",
            "job_description": "Créer des tableaux de bord Power BI avec DAX et SQL.",
        }
        draft = (
            "PROFIL\nAnalyste de données.\nLOGICIELS\n"
            "Power BI · SQL · Python · R · Excel · Power Query · DAX · Git · Docker · Azure DevOps"
        )
        source = candidatures_app.make_cv_latex(profile, application, draft)
        self.assertIn("Power BI", source)
        self.assertIn("SQL", source)
        self.assertIn("DAX", source)
        self.assertNotIn("Docker", source)
        self.assertNotIn("Azure DevOps", source)

    def test_cv_long_content_is_scaled_to_one_page(self):
        if not candidatures_app.shutil.which("xelatex"):
            self.skipTest("XeLaTeX is not installed")
        profile = {
            "full_name": "Nom Exemple", "email": "nom@example.com",
            "phone": "", "location": "Angers",
        }
        application = {"position": "Data Analyst", "company": "Exemple"}
        content = "PROFIL\n" + "\n".join(
            f"Expérience détaillée numéro {index} avec des missions d'analyse, "
            "de reporting et de traitement de données décrites avec précision."
            for index in range(1, 45)
        )
        pdf = PdfReader(io.BytesIO(
            candidatures_app.compile_latex(
                candidatures_app.make_cv_latex(profile, application, content)
            ).getvalue()
        ))
        self.assertEqual(len(pdf.pages), 1)

    def test_cv_fallback_pdf_keeps_long_content_to_one_page(self):
        profile = {
            "full_name": "Nom Exemple", "email": "nom@example.com",
            "phone": "", "location": "Angers",
        }
        application = {"position": "Data Analyst", "company": "Exemple"}
        content = "PROFIL\n" + "\n".join(
            f"Mission détaillée numéro {index} avec analyse, reporting et données."
            for index in range(1, 45)
        )
        pdf = PdfReader(io.BytesIO(
            candidatures_app.make_pdf(profile, application, content, "cv").getvalue()
        ))
        self.assertEqual(len(pdf.pages), 1)


    def test_profile_sections_and_experience_skills_in_latex(self):
        profile = {
            "full_name": "A", "email": "", "phone": "", "location": "",
            "languages": "Français – natif\nAnglais – B2", "hobbies": "Course; Échecs",
            "certifications": "PL-300 – 2025", "achievements": "",
        }
        draft = (
            "PROFIL\nTexte\nEXPERIENCES PROFESSIONNELLES\nDATA ANALYST 04/2026 – 09/2026\nACME\n"
            "- Réduit le reporting de 40 %\nCompétences : SQL, Power BI\n"
            "LANGUES\nChinois\n"
        )
        source = candidatures_app.make_cv_latex(
            profile, {"position": "Data Analyst", "company": "X"}, draft
        )
        self.assertIn(r"\cvskills{SQL, Power BI}", source)
        self.assertIn("Anglais: B2", source)
        self.assertNotIn("Chinois", source)
        self.assertIn(r"\cvsection{Certifications}", source)
        self.assertIn(r"\cvsection{Loisirs}", source)
        self.assertIn("Échecs", source)
        if candidatures_app.shutil.which("xelatex"):
            self.assertEqual(len(PdfReader(candidatures_app.compile_latex(source)).pages), 1)

    def test_cv_language_section_is_translated_from_profile_in_all_export_formats(self):
        profile = {
            "full_name": "Moubarak LASSISSI",
            "email": "candidate@example.com",
            "phone": "+33123456789",
            "location": "Angers",
            "languages": "Français : Langue maternelle\nAnglais : Professionnel",
        }
        application = {"position": "Statistical Assistant", "company": "UNESCO"}
        english_draft = (
            "PROFILE\nStatistical analyst.\n"
            "LANGUAGES\nFrançais : Langue maternelle\nAnglais : Professionnel\n"
        )

        latex = candidatures_app.make_cv_latex(profile, application, english_draft)
        self.assertIn("French: Native", latex)
        self.assertIn("English: Professional", latex)
        self.assertNotIn("Français", latex)
        self.assertNotIn("Langue maternelle", latex)
        self.assertNotIn("Professionnel", latex)

        docx = Document(io.BytesIO(
            candidatures_app.make_cv_docx(profile, application, english_draft).getvalue()
        ))
        docx_text = "\n".join(paragraph.text for paragraph in docx.paragraphs)
        self.assertIn("French: Native", docx_text)
        self.assertIn("English: Professional", docx_text)
        self.assertNotIn("Français", docx_text)
        self.assertNotIn("Langue maternelle", docx_text)

        pdf = PdfReader(io.BytesIO(
            candidatures_app.make_pdf(profile, application, english_draft, "cv").getvalue()
        ))
        pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        self.assertIn("French: Native", pdf_text)
        self.assertIn("English: Professional", pdf_text)
        self.assertNotIn("Français", pdf_text)

        french = candidatures_app.replace_cv_language_section(
            "PROFIL\nAnalyste.\nLANGUAGES\nFrench: Native\nEnglish: Professional",
            profile,
            "fr",
        )
        self.assertIn("LANGUES\nFrançais: Langue maternelle\nAnglais: Professionnel", french)
        self.assertNotIn("French: Native", french)

    def test_cv_prompts_leave_language_section_to_application(self):
        profile = {
            "full_name": "Nom",
            "email": "",
            "phone": "",
            "location": "",
            "resume_source": "Data analyst, Python.",
        }
        application = {
            "position": "Data Analyst",
            "company": "Exemple",
            "location": "",
            "job_description": "Data analysis.",
        }
        english_prompt = candidatures_app.build_prompt(
            "cv", profile, application, language="en"
        )
        french_prompt = candidatures_app.build_prompt(
            "cv", profile, application, language="fr"
        )
        self.assertIn("Do NOT write a LANGUAGES section", english_prompt)
        self.assertIn("Ne génère pas de rubrique LANGUES", french_prompt)
        self.assertIn("Use past-tense action verbs for roles that ended before today", english_prompt)
        self.assertIn("Candidate-confirmed facts and corrections in the current profile take precedence", english_prompt)
        self.assertIn("Le CV principal et les corrections confirmées par le candidat priment", french_prompt)
        self.assertIn("ne prétends pas établir une causalité", french_prompt)
        self.assertEqual(
            candidatures_app.cv_location({"location": "Angers"}, "en", {"location": "Montréal, QC"}),
            "Angers Open to international mobility",
        )
        self.assertEqual(
            candidatures_app.cv_location({"location": "Angers"}, "fr", {"location": "Brest"}),
            "Angers Mobilité nationale",
        )

    def test_generated_english_cv_uses_profile_languages_and_empty_response_stays_empty(self):
        self.post_form("/profile", data={
            "resume_source": "Data analyst, SQL.",
            "languages": "Français : Langue maternelle\nAnglais : Professionnel",
        })
        self.post_form("/applications", data={
            "company": "Exemple",
            "position": "Statistical Assistant",
            "job_description": "Prepare statistical reports.",
        })
        with candidatures_app.app.app_context():
            application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications"
            ).fetchone()["id"]

        with patch(
            "app.generate_with_free_api",
            return_value=(
                "PROFILE\nStatistical analyst.\nLANGUAGES\n"
                "Français : Langue maternelle\nAnglais : Professionnel"
            ),
        ):
            self.post_form(
                f"/applications/{application_id}/draft",
                data={
                    "kind": "cv",
                    "provider": "api",
                    "allow_cloud": "yes",
                    "language": "en",
                },
            )
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(application_id)
            self.assertIn(
                "LANGUAGES\nFrench: Native\nEnglish: Professional",
                application["cv_draft"],
            )
            self.assertNotIn("Français", application["cv_draft"])

        self.post_form("/applications", data={
            "company": "Autre",
            "position": "Data Analyst",
            "job_description": "Analyze datasets.",
        })
        with candidatures_app.app.app_context():
            empty_application_id = candidatures_app.get_db().execute(
                "SELECT id FROM applications WHERE company = 'Autre'"
            ).fetchone()["id"]
        with patch("app.generate_with_free_api", return_value=""):
            self.post_form(
                f"/applications/{empty_application_id}/draft",
                data={
                    "kind": "cv",
                    "provider": "api",
                    "allow_cloud": "yes",
                    "language": "en",
                },
            )
        with candidatures_app.app.app_context():
            application = candidatures_app.get_application(empty_application_id)
            self.assertEqual(application["cv_draft"], "")

    def test_cv_layout_is_validated_and_applied(self):
        self.assertEqual(candidatures_app.parse_cv_layout('{"font": 99, "accent": "zzz"}')["font"], 8.5)
        profile = {"full_name": "A", "email": "", "phone": "", "location": ""}
        application = {"position": "Data", "company": "X"}
        source = candidatures_app.make_cv_latex(
            profile, application, "PROFIL\nTexte\n", {"font": 9.5, "margin": 2, "accent": "1F3A5F"}
        )
        self.assertIn("margin=2.0cm", source)
        self.assertIn("{HTML}{1F3A5F}", source)
        self.assertNotIn("@@", source)


if __name__ == "__main__":
    unittest.main()
