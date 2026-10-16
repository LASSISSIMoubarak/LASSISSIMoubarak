import io
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, RGBColor
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape


MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
STATUSES = ["A analyser", "A preparer", "Candidature envoyee", "Entretien", "Refus", "Offre recue"]

app = Flask(__name__, instance_relative_config=True)
app.config.update(
    DATABASE=os.environ.get("CANDIDATURES_DATABASE", str(Path(app.instance_path) / "candidatures.sqlite3")),
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
)


def get_db():
    if "db" not in g:
        database_path = Path(app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    database = get_db()
    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            full_name TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '', location TEXT NOT NULL DEFAULT '',
            resume_source TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL, position TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '',
            job_description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'A analyser',
            notes TEXT NOT NULL DEFAULT '', reply TEXT NOT NULL DEFAULT '',
            cv_draft TEXT NOT NULL DEFAULT '', letter_draft TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        INSERT OR IGNORE INTO profile (id) VALUES (1);
        """
    )
    database.commit()


def get_profile():
    return get_db().execute("SELECT * FROM profile WHERE id = 1").fetchone()


def get_application(application_id):
    return get_db().execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()


def ollama_status():
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=1) as response:
            models = json.loads(response.read().decode("utf-8")).get("models", [])
        return {"ready": any(model.get("name") == MODEL_NAME for model in models), "model": MODEL_NAME}
    except (OSError, ValueError, TimeoutError):
        return {"ready": False, "model": MODEL_NAME}


def build_prompt(kind, profile, application):
    profile_text = "\n".join(
        [
            f"Nom : {profile['full_name']}", f"E-mail : {profile['email']}",
            f"Telephone : {profile['phone']}", f"Localisation : {profile['location']}",
            "CV de reference (seule source autorisee pour les faits personnels) :",
            profile["resume_source"][:4500],
        ]
    )
    offer_text = "\n".join(
        [
            f"Poste : {application['position']}", f"Entreprise : {application['company']}",
            f"Localisation : {application['location']}", "Description de l'offre :",
            application["job_description"][:3500],
        ]
    )
    if kind == "cv":
        task = (
            "Tu es specialiste des CV ATS pour les metiers de la data (Data Analyst, BI, Data Scientist). "
            "Redige le contenu d'un CV francais concis, cible sur le poste et l'offre ci-dessous. "
            "Reorganise les informations du CV source en priorisant seulement les competences et experiences "
            "pertinentes pour l'offre. Conserve exactement les noms d'employeurs, intitules et dates du CV. "
            "N'invente aucun fait, chiffre, outil, diplome, resultat ni niveau de langue. Ne transforme pas "
            "une responsabilite en resultat chiffre. Si une donnee indispensable manque, ecris [A COMPLETER]. "
            "Retourne uniquement le contenu, sans introduction, sans commentaire et sans titre du type "
            "'CV adapte - entreprise' ou 'Voici le CV'. Utilise exactement ces rubriques, dans cet ordre, "
            "et omets celles sans information source : PROFIL, COMPETENCES CLES, EXPERIENCES "
            "PROFESSIONNELLES, FORMATION, PROJETS, LANGUES. Sous chaque experience, mets l'intitule "
            "sur une ligne, puis entreprise et dates, puis 2 ou 3 puces courtes. Limite l'ensemble a environ "
            "450 mots pour eviter une reponse tronquee. Format texte simple compatible ATS, sans tableau, "
            "colonnes, icones, jauges, photo ni mise en page graphique."
        )
    else:
        task = (
            "Redige le corps d'une lettre de motivation professionnelle en francais pour cette offre. "
            "N'ecris ni titre, ni en-tete, ni objet, ni nom d'entreprise comme titre : l'application les "
            "ajoutera. Retourne uniquement la lettre en texte simple, sans Markdown, sans rubriques de CV "
            "et sans liste a puces. Commence par 'Madame, Monsieur,'. Ecris exactement 3 paragraphes courts : "
            "1) motivation precise pour le poste et lien avec l'offre ; 2) deux exemples pertinents et "
            "verifiables du CV source ; 3) proposition d'entretien. Termine par 'Je vous prie d'agreer, "
            "Madame, Monsieur, l'expression de mes salutations distinguees.' N'ajoute pas de signature. "
            "N'ecris jamais 'Motivation Letter', 'A propos', 'Profil', 'Experiences', 'Formation' ou "
            "'Competences'. Utilise uniquement les faits du CV et de l'offre. N'invente aucune experience, "
            "date, responsabilite, resultat chiffre, outil, connaissance de l'entreprise ou coordonnee. "
            "Chaque affirmation sur le candidat doit etre directement attestee dans le CV source. "
            "Ne deduis aucun impact, gain, tendance, croissance, amelioration, taille de donnees ou "
            "resultat a partir d'une responsabilite. N'utilise pas de formulations comme 'ce qui a permis' "
            "ou 'a contribue a' sauf si le CV indique explicitement ce resultat. Ne recopie pas le CV et "
            "ne transforme pas le corps de la lettre en CV. Ne transforme jamais une exigence de l'offre "
            "en experience ou competence du candidat si elle n'est pas presente dans son CV. N'affirme pas "
            "un niveau d'expertise ou une capacite qui n'est pas explicitement indiquee. Maximum 180 mots. "
            "Si un fait manque, omets-le."
        )
    return f"{task}\n\nPROFIL\n{profile_text}\n\nOFFRE\n{offer_text}"


def clean_cv_draft(content):
    cleaned_lines = []
    for line in content.splitlines():
        line = re.sub(r"^\s{0,3}#{1,3}\s*", "", line.strip())
        line = line.replace("**", "").replace("__", "")
        if not line:
            continue
        if not cleaned_lines and re.match(
            r"(?i)^cv\s+(adapte|adapt\u00e9)(\s*[-:\u2013\u2014].*)?$", line
        ):
            continue
        if not cleaned_lines and re.match(r"(?i)^(voici|bien s\u00fbr|certainement)\b", line):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def clean_letter_draft(content):
    cv_headings = {
        "A PROPOS", "PROFIL", "COMPETENCES", "COMPETENCES CLES", "EXPERIENCE",
        "EXPERIENCES", "EXPERIENCES PROFESSIONNELLES", "FORMATION", "PROJETS", "LANGUES",
        "EDUCATION", "EXPERIENCE PROFESSIONNELLE", "COMPETENCES TECHNIQUES",
    }
    cleaned_lines = []
    for line in content.splitlines():
        line = re.sub(r"^\s{0,3}#{1,3}\s*", "", line.strip())
        line = line.replace("**", "").replace("__", "").replace("`", "").strip().strip("*").strip()
        if not line:
            cleaned_lines.append("")
            continue
        normalized = "".join(
            character
            for character in unicodedata.normalize("NFKD", line.strip().rstrip(":").strip().upper())
            if not unicodedata.combining(character)
        )
        if normalized in cv_headings or normalized in {"MOTIVATION LETTER", "LETTRE DE MOTIVATION"}:
            continue
        if normalized.startswith(("OBJET :", "OBJECT:")):
            continue
        if not cleaned_lines and re.match(r"(?i)^(voici|bien s\u00fbr|certainement)\b", line):
            continue
        if normalized in {"MONSIEUR/MADAME,", "MADAME/MONSIEUR,", "MONSIEUR, MADAME,"}:
            line = "Madame, Monsieur,"
        cleaned_lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def generate_with_ollama(prompt, max_tokens):
    payload = json.dumps(
        {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}],
         "stream": False, "options": {
             "temperature": 0.2, "num_predict": max_tokens, "num_ctx": 4096
         }}
    ).encode("utf-8")
    for attempt in range(3):
        req = Request(
            "http://127.0.0.1:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urlopen(req, timeout=240) as response:
                result = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Ollama a repondu avec le code {error.code}: {detail}") from error
        except (URLError, TimeoutError) as error:
            reason = getattr(error, "reason", error)
            connection_refused = isinstance(reason, ConnectionRefusedError)
            app.logger.warning("Echec Ollama, tentative %s/3: %s", attempt + 1, error)
            if connection_refused and attempt < 2:
                time.sleep(attempt + 1)
                continue
            if isinstance(reason, TimeoutError):
                raise RuntimeError(
                    "Qwen n'a pas termine dans le delai imparti. Il tourne sur CPU : "
                    "essaie une annonce plus courte ou relance avec moins de texte."
                ) from error
            raise RuntimeError(
                "Ollama ne repond pas sur 127.0.0.1:11434. Ouvre Ollama, puis reessaie. "
                f"Detail : {reason}"
            ) from error
    content = result.get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("Ollama n'a retourne aucun texte.")
    return content


def make_docx(title, content):
    document = Document()
    document.add_heading(title, level=0)
    for line in content.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("### "):
            document.add_heading(cleaned[4:], level=2)
        elif cleaned.startswith("## "):
            document.add_heading(cleaned[3:], level=1)
        elif cleaned.startswith("# "):
            document.add_heading(cleaned[2:], level=1)
        elif cleaned.startswith(("- ", "* ")):
            document.add_paragraph(cleaned[2:], style="List Bullet")
        else:
            document.add_paragraph(cleaned)
    output = io.BytesIO()
    document.save(output)
    output.seek(0)
    return output


def french_date():
    months = [
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
    ]
    today = datetime.now()
    return f"{today.day} {months[today.month - 1]} {today.year}"


def letter_header_lines(profile, application):
    contacts = [
        value.strip()
        for value in (profile["location"], profile["email"], profile["phone"])
        if value and value.strip()
    ]
    return contacts


def make_letter_docx(profile, application, content):
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = 11
    normal.paragraph_format.space_after = 9

    name = document.add_paragraph()
    name.paragraph_format.space_after = 2
    name_run = name.add_run(profile["full_name"].strip() or "Nom a completer")
    name_run.bold = True
    name_run.font.name = "Aptos Display"
    name_run.font.size = 16
    contacts = letter_header_lines(profile, application)
    if contacts:
        contact = document.add_paragraph("  |  ".join(contacts))
        contact.paragraph_format.space_after = 14

    date_line = document.add_paragraph()
    date_line.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    date_line.add_run(f"{profile['location'].strip()}, le {french_date()}" if profile["location"].strip() else french_date())
    document.add_paragraph(f"A l'attention du service recrutement - {application['company']}")
    subject = document.add_paragraph()
    subject.paragraph_format.space_before = 8
    subject.paragraph_format.space_after = 14
    subject_run = subject.add_run(f"Objet : Candidature au poste de {application['position']}")
    subject_run.bold = True

    for paragraph_text in re.split(r"\n\s*\n", clean_letter_draft(content)):
        paragraph_text = paragraph_text.strip()
        if paragraph_text:
            document.add_paragraph(paragraph_text)
    document.add_paragraph(profile["full_name"].strip() or "[Nom a completer]")

    output = io.BytesIO()
    document.save(output)
    output.seek(0)
    return output


def make_cv_docx(profile, application, content):
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = 10
    normal.paragraph_format.space_after = 4

    name = profile["full_name"].strip() or "Nom a completer"
    heading = document.add_paragraph()
    heading.paragraph_format.space_after = 2
    run = heading.add_run(name)
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = 21

    role_line = document.add_paragraph()
    role_line.paragraph_format.space_after = 5
    role = role_line.add_run(application["position"].upper())
    role.bold = True
    role.font.size = 11
    role.font.color.rgb = RGBColor(33, 73, 63)

    contacts = [
        value.strip()
        for value in (profile["location"], profile["email"], profile["phone"])
        if value and value.strip()
    ]
    if contacts:
        contact_line = document.add_paragraph("  |  ".join(contacts))
        contact_line.paragraph_format.space_after = 10

    headings = {
        "PROFIL", "COMPETENCES CLES", "COMPÉTENCES CLÉS",
        "EXPERIENCES PROFESSIONNELLES", "EXPÉRIENCES PROFESSIONNELLES",
        "FORMATION", "PROJETS", "LANGUES",
    }
    for line in clean_cv_draft(content).splitlines():
        text = line.strip()
        plain = text.strip("*# ").rstrip(":").strip()
        if plain.upper() in headings:
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.space_before = 8
            paragraph.paragraph_format.space_after = 3
            run = paragraph.add_run(plain.upper())
            run.bold = True
            run.font.size = 11
            run.font.color.rgb = RGBColor(33, 73, 63)
        elif text.startswith(("- ", "* ", "• ")):
            document.add_paragraph(text[2:].strip(), style="List Bullet")
        else:
            document.add_paragraph(text)

    output = io.BytesIO()
    document.save(output)
    output.seek(0)
    return output


def pdf_styles():
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("CandidateName", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19, leading=22, textColor=colors.HexColor("#202922"), alignment=0, spaceAfter=3),
        "role": ParagraphStyle("CandidateRole", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.HexColor("#21493f"), spaceAfter=5),
        "contact": ParagraphStyle("CandidateContact", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#59645c"), spaceAfter=10),
        "section": ParagraphStyle("CVSection", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.HexColor("#21493f"), spaceBefore=8, spaceAfter=3, keepWithNext=True),
        "body": ParagraphStyle("DocumentBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#202922"), spaceAfter=7),
        "date": ParagraphStyle("LetterDate", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12, alignment=TA_RIGHT, spaceBefore=10, spaceAfter=12),
        "subject": ParagraphStyle("LetterSubject", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, spaceBefore=8, spaceAfter=14),
    }


def make_pdf(profile, application, content, kind):
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=2.1 * cm, leftMargin=2.1 * cm,
        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
        title=f"{'CV' if kind == 'cv' else 'Lettre de motivation'} - {application['company']}",
    )
    styles = pdf_styles()
    story = []
    name = escape(profile["full_name"].strip() or "Nom a completer")
    contacts = "  |  ".join(escape(value) for value in letter_header_lines(profile, application))

    story.append(Paragraph(name, styles["name"]))
    if kind == "cv":
        story.append(Paragraph(escape(application["position"].upper()), styles["role"]))
        if contacts:
            story.append(Paragraph(contacts, styles["contact"]))
        content = clean_cv_draft(content)
        headings = {
            "PROFIL", "COMPETENCES CLES", "COMPÉTENCES CLÉS",
            "EXPERIENCES PROFESSIONNELLES", "EXPÉRIENCES PROFESSIONNELLES",
            "FORMATION", "PROJETS", "LANGUES",
        }
    else:
        if contacts:
            story.append(Paragraph(contacts, styles["contact"]))
        place = profile["location"].strip()
        date_text = f"{escape(place)}, le {escape(french_date())}" if place else escape(french_date())
        story.append(Paragraph(date_text, styles["date"]))
        story.append(Paragraph(f"A l'attention du service recrutement - {escape(application['company'])}", styles["body"]))
        story.append(Paragraph(f"Objet : Candidature au poste de {escape(application['position'])}", styles["subject"]))
        content = clean_letter_draft(content)
        headings = set()

    for line in content.splitlines():
        text = line.strip()
        if not text:
            story.append(Spacer(1, 3))
            continue
        plain = text.strip("*# ").rstrip(":").strip()
        if kind == "cv" and plain.upper() in headings:
            story.append(Paragraph(escape(plain.upper()), styles["section"]))
        elif text.startswith(("- ", "* ", "• ")):
            story.append(Paragraph("&bull; " + escape(text[2:].strip()), styles["body"]))
        else:
            story.append(Paragraph(escape(text.replace("**", "")), styles["body"]))
    if kind == "letter":
        story.append(Spacer(1, 8))
        story.append(Paragraph(name, styles["body"]))

    document.build(story)
    output.seek(0)
    return output


@app.teardown_appcontext
def teardown_db(_error):
    close_db(_error)


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        provided = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected, provided):
            abort(400)


@app.context_processor
def inject_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


@app.get("/")
def index():
    applications = get_db().execute(
        "SELECT * FROM applications ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    selected_id = request.args.get("selected", type=int)
    selected = get_application(selected_id) if selected_id else None
    if selected is None and applications:
        selected = applications[0]
    profile = get_profile()
    ollama = ollama_status()
    return render_template(
        "index.html", profile=profile, applications=applications,
        selected=selected, statuses=STATUSES, ollama=ollama,
        has_resume=bool(profile["resume_source"].strip()),
        has_job_description=bool(selected and selected["job_description"].strip()),
        can_generate=bool(profile["resume_source"].strip() and selected
                          and selected["job_description"].strip() and ollama["ready"]),
        counts={
            "total": len(applications),
            "sent": sum(item["status"] == "Candidature envoyee" for item in applications),
            "interviews": sum(item["status"] == "Entretien" for item in applications),
        },
    )


@app.post("/profile")
def save_profile():
    resume_source = request.form.get("resume_source", "").strip()
    resume_pdf = request.files.get("resume_pdf")
    pdf_uploaded = bool(resume_pdf and resume_pdf.filename)
    if pdf_uploaded:
        if Path(resume_pdf.filename).suffix.lower() != ".pdf":
            flash("Choisis un fichier PDF pour importer ton CV.", "error")
            return redirect(url_for("index", selected=request.form.get("selected", type=int)))
        pdf_content = resume_pdf.read()
        if not pdf_content.startswith(b"%PDF-"):
            flash("Le fichier choisi ne semble pas etre un PDF valide.", "error")
            return redirect(url_for("index", selected=request.form.get("selected", type=int)))
        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            resume_source = "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception:
            flash("Le PDF n'a pas pu etre lu. Verifie le fichier puis reessaie.", "error")
            return redirect(url_for("index", selected=request.form.get("selected", type=int)))
        if not resume_source:
            flash(
                "Aucun texte n'a ete extrait. Le PDF est peut-etre scanne ; utilise un PDF "
                "avec du texte selectionnable ou colle le texte du CV.",
                "error",
            )
            return redirect(url_for("index", selected=request.form.get("selected", type=int)))

    get_db().execute(
        """UPDATE profile SET full_name = ?, email = ?, phone = ?, location = ?, resume_source = ?
           WHERE id = 1""",
        (
            request.form.get("full_name", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("location", "").strip(),
            resume_source,
        ),
    )
    get_db().commit()
    flash(
        "Texte du PDF extrait et enregistre sur cet ordinateur. Verifie le texte dans le profil."
        if pdf_uploaded else "Profil enregistre sur cet ordinateur.",
        "success",
    )
    return redirect(url_for("index", selected=request.form.get("selected", type=int)))


@app.post("/applications")
def add_application():
    company = request.form.get("company", "").strip()
    position = request.form.get("position", "").strip()
    offer_url = request.form.get("url", "").strip()
    if not company or not position:
        flash("Indique au minimum l'entreprise et le poste.", "error")
        return redirect(url_for("index"))
    if offer_url:
        parsed_url = urlsplit(offer_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            flash("Le lien de l'offre doit commencer par http:// ou https://.", "error")
            return redirect(url_for("index"))
    now = datetime.now().isoformat(timespec="seconds")
    cursor = get_db().execute(
        """INSERT INTO applications
           (company, position, location, url, job_description, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (company, position, request.form.get("location", "").strip(),
         offer_url, request.form.get("job_description", "").strip(), now, now),
    )
    get_db().commit()
    flash("Offre ajoutee au suivi.", "success")
    return redirect(url_for("index", selected=cursor.lastrowid))


@app.post("/applications/<int:application_id>/update")
def update_application(application_id):
    if get_application(application_id) is None:
        flash("Cette candidature n'existe pas.", "error")
        return redirect(url_for("index"))
    status = request.form.get("status", "A analyser")
    if status not in STATUSES:
        status = "A analyser"
    get_db().execute(
        "UPDATE applications SET status = ?, notes = ?, reply = ?, updated_at = ? WHERE id = ?",
        (status, request.form.get("notes", "").strip(), request.form.get("reply", "").strip(),
         datetime.now().isoformat(timespec="seconds"), application_id),
    )
    get_db().commit()
    flash("Suivi mis a jour.", "success")
    return redirect(url_for("index", selected=application_id))


@app.post("/applications/<int:application_id>/draft")
def generate_draft(application_id):
    application = get_application(application_id)
    profile = get_profile()
    kind = request.form.get("kind")
    if application is None or kind not in {"cv", "letter"}:
        flash("Demande de brouillon invalide.", "error")
        return redirect(url_for("index"))
    if not profile["resume_source"].strip():
        flash("Ajoute d'abord ton CV de reference dans le profil.", "error")
        return redirect(url_for("index", selected=application_id))
    if not application["job_description"].strip():
        flash("Ajoute la description de l'offre avant de generer un brouillon.", "error")
        return redirect(url_for("index", selected=application_id))
    try:
        max_tokens = 450 if kind == "cv" else 240
        draft = generate_with_ollama(build_prompt(kind, profile, application), max_tokens)
        draft = clean_cv_draft(draft) if kind == "cv" else clean_letter_draft(draft)
    except RuntimeError as error:
        flash(str(error), "error")
        return redirect(url_for("index", selected=application_id))
    field = "cv_draft" if kind == "cv" else "letter_draft"
    get_db().execute(
        f"UPDATE applications SET {field} = ?, updated_at = ? WHERE id = ?",
        (draft, datetime.now().isoformat(timespec="seconds"), application_id),
    )
    get_db().commit()
    flash("Brouillon genere. Relis-le et verifie chaque information avant utilisation.", "success")
    return redirect(url_for("index", selected=application_id))


@app.get(
    "/applications/<int:application_id>/download/<kind>",
    defaults={"file_format": "docx"},
)
@app.get("/applications/<int:application_id>/download/<kind>/<file_format>")
def download_draft(application_id, kind, file_format):
    application = get_application(application_id)
    if application is None or kind not in {"cv", "letter"} or file_format not in {"docx", "pdf"}:
        flash("Document introuvable.", "error")
        return redirect(url_for("index"))
    content = application["cv_draft" if kind == "cv" else "letter_draft"]
    if not content:
        flash("Genere d'abord ce brouillon.", "error")
        return redirect(url_for("index", selected=application_id))
    safe_name = re.sub(r'[<>:"/\\|?*]+', "_", f"{kind}_{application['company']}_{application['position']}")
    profile = get_profile()
    if file_format == "pdf":
        output = make_pdf(profile, application, content, kind)
        mimetype = "application/pdf"
    else:
        output = (
            make_cv_docx(profile, application, content)
            if kind == "cv"
            else make_letter_docx(profile, application, content)
        )
        mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return send_file(
        output, as_attachment=True, download_name=f"{safe_name}.{file_format}",
        mimetype=mimetype,
    )


@app.get("/export.xlsx")
def export_xlsx():
    rows = get_db().execute(
        "SELECT * FROM applications ORDER BY created_at DESC, id DESC"
    ).fetchall()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Candidatures"
    headers = ["Entreprise", "Poste", "Localisation", "Lien", "Statut", "Date ajoutee",
               "Description de l'offre", "Notes", "Reponse recue", "CV adapte", "Lettre de motivation"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="21493F")
    for row in rows:
        sheet.append([row["company"], row["position"], row["location"], row["url"], row["status"],
                      row["created_at"], row["job_description"], row["notes"], row["reply"],
                      row["cv_draft"], row["letter_draft"]])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in {"A": 24, "B": 28, "C": 20, "D": 42, "E": 24, "F": 22}.items():
        sheet.column_dimensions[column].width = width
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="suivi_candidatures.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/health")
def health():
    return {"status": "ok", "ollama": ollama_status()}


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)