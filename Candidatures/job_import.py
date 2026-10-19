"""Récupération d'offres d'emploi à partir de liens et d'alertes e-mail Gmail."""

import email
import html
import imaplib
import ipaddress
import json
import os
import re
import socket
from datetime import date, timedelta
from email import policy
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_PAGE_BYTES = 1_500_000
FETCH_TIMEOUT = 20
MAX_DESCRIPTION_CHARS = 6000
MIN_DESCRIPTION_CHARS = 200
USER_AGENT = "Mozilla/5.0 (compatible; CandidaturesLocal/1.0; usage personnel)"

JOB_HOSTS = (
    "linkedin.com", "indeed.com", "indeed.fr", "welcometothejungle.com", "apec.fr",
    "francetravail.fr", "pole-emploi.fr", "hellowork.com", "jobteaser.com",
    "glassdoor.fr", "glassdoor.com", "monster.fr", "cadremploi.fr", "talent.com",
)
JOB_PATH_HINTS = ("job", "offre", "emploi", "viewjob", "clk", "career")


class OfferError(Exception):
    pass


def _check_public_host(hostname):
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise OfferError("Adresse introuvable.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%")[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise OfferError("Adresse interne refusée par sécurité.")


def _check_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise OfferError("Le lien doit commencer par http:// ou https://.")
    _check_public_host(parsed.hostname)


class _SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url):
    _check_url(url)
    request = Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
    })
    try:
        with build_opener(_SafeRedirect).open(request, timeout=FETCH_TIMEOUT) as response:
            final_url = response.geturl()
            raw = response.read(MAX_PAGE_BYTES + 1)
            charset = response.headers.get_content_charset() or "utf-8"
    except HTTPError as exc:
        raise OfferError(f"Le site a refusé l'accès (code {exc.code}).") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OfferError("Le site est injoignable.") from exc
    if len(raw) > MAX_PAGE_BYTES:
        raise OfferError("Page trop volumineuse.")
    return final_url, raw.decode(charset, errors="replace")


class _TextExtractor(HTMLParser):
    SKIPPED = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form"}
    BLOCKS = {"p", "div", "br", "li", "ul", "h1", "h2", "h3", "h4", "tr", "section"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIPPED:
            self.depth += 1
        elif tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIPPED and self.depth:
            self.depth -= 1
        elif tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def html_to_text(markup):
    extractor = _TextExtractor()
    extractor.feed(html.unescape(markup) if "&lt;" in markup else markup)
    text = "".join(extractor.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def _walk_json(node):
    if isinstance(node, list):
        for item in node:
            yield from _walk_json(item)
    elif isinstance(node, dict):
        yield node
        for value in node.values():
            if isinstance(value, (list, dict)):
                yield from _walk_json(value)


def _job_postings(markup):
    pattern = r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>'
    for block in re.findall(pattern, markup, flags=re.I | re.S):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        for node in _walk_json(data):
            node_type = node.get("@type")
            types = node_type if isinstance(node_type, list) else [node_type]
            if "JobPosting" in types:
                yield node


def _location_of(posting):
    place = posting.get("jobLocation")
    if isinstance(place, list) and place:
        place = place[0]
    if isinstance(place, dict):
        address = place.get("address")
        if isinstance(address, dict):
            return ", ".join(
                str(address[key]) for key in ("addressLocality", "addressRegion") if address.get(key)
            )
    if posting.get("jobLocationType") == "TELECOMMUTE":
        return "Télétravail"
    return ""


def _meta(markup, name):
    for pattern in (
        rf'<meta[^>]+(?:property|name)=["\']{name}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{name}["\']',
    ):
        match = re.search(pattern, markup, flags=re.I)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def parse_offer(url, markup):
    """Retourne un dict position/company/location/description, ou lève OfferError."""
    for posting in _job_postings(markup):
        organization = posting.get("hiringOrganization")
        company = organization.get("name", "") if isinstance(organization, dict) else str(organization or "")
        description = html_to_text(str(posting.get("description", "")))
        if len(description) >= MIN_DESCRIPTION_CHARS:
            return {
                "position": html.unescape(str(posting.get("title", ""))).strip(),
                "company": html.unescape(company).strip(),
                "location": _location_of(posting),
                "description": description[:MAX_DESCRIPTION_CHARS],
            }
    title_match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    title = _meta(markup, "og:title") or (html.unescape(title_match.group(1)).strip() if title_match else "")
    body = re.search(r"<body[^>]*>(.*)</body>", markup, flags=re.I | re.S)
    description = html_to_text(body.group(1) if body else markup)
    lowered = description.lower()[:1500]
    if len(description) < MIN_DESCRIPTION_CHARS or any(
        word in lowered for word in ("authwall", "connectez-vous pour", "sign in to view", "captcha")
    ):
        raise OfferError("Page protégée ou vide : colle la description à la main.")
    company = _meta(markup, "og:site_name") or (urlsplit(url).hostname or "").removeprefix("www.")
    return {
        "position": title[:200] or "Offre importée", "company": company[:120],
        "location": "", "description": description[:MAX_DESCRIPTION_CHARS],
    }


def import_offer(url):
    final_url, markup = fetch_page(url)
    offer = parse_offer(final_url, markup)
    offer["url"] = url
    return offer


def url_key(url):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").removeprefix("www.")
    keep_query = not (host.endswith("linkedin.com") and "/jobs/view" in parsed.path)
    return urlunsplit((parsed.scheme, host, parsed.path.rstrip("/"), parsed.query if keep_query else "", ""))


def extract_urls(text):
    seen, urls = set(), []
    for url in re.findall(r"https?://[^\s<>\"')\]]+", text or ""):
        url = url.rstrip(".,;")
        if url_key(url) not in seen:
            seen.add(url_key(url))
            urls.append(url)
    return urls


def looks_like_job_link(url):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    return any(host == h or host.endswith("." + h) for h in JOB_HOSTS) and any(
        hint in path for hint in JOB_PATH_HINTS
    )


def gmail_settings():
    address = os.environ.get("GMAIL_ADDRESS", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    label = os.environ.get("GMAIL_ALERT_LABEL", "Alertes-emploi").strip() or "Alertes-emploi"
    return {"address": address, "password": password, "label": label,
            "configured": bool(address and password)}


ALERT_SENDERS = (
    "indeed", "linkedin", "welcometothejungle", "apec", "francetravail", "pole-emploi",
    "hellowork", "glassdoor", "monster", "jobteaser", "cadremploi", "talent.com",
)
# Liens à ne jamais ouvrir : désinscription, gestion d'alerte, mentions légales.
NOISE_WORDS = (
    "désinscri", "desinscri", "unsubscribe", "désabonn", "préférences", "preferences",
    "confidentialité", "privacy", "afficher dans le navigateur", "voir tous", "gérer",
    "supprimer l", "modifier l", "aide", "help",
)
NOISE_PATHS = ("/alerts", "/imgping", "/static/", "/assets/", "/unsubscribe", "/optout")


class _AnchorCollector(HTMLParser):
    BLOCKS = {"p", "div", "br", "li", "tr", "td", "h1", "h2", "h3", "h4", "span"}

    def __init__(self):
        super().__init__()
        self.anchors = []
        self._href = None
        self._depth = 0
        self._parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            if self._depth == 0:
                self._href = dict(attrs).get("href")
                self._parts = []
            self._depth += 1
        elif self._depth and tag in self.BLOCKS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "a" and self._depth:
            self._depth -= 1
            if self._depth == 0 and self._href is not None:
                text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self._parts))
                text = re.sub(r"\n\s*\n+", "\n", text).strip()
                self.anchors.append((self._href, text))
                self._href = None
        elif self._depth and tag in self.BLOCKS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._depth:
            self._parts.append(data)


def _is_job_host(url):
    host = (urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in JOB_HOSTS) and "statics" not in host


def extract_alert_items(markup, is_html=True):
    """Renvoie les offres d'un e-mail d'alerte : [{'url', 'snippet'}], sans liens de désinscription."""
    if is_html:
        collector = _AnchorCollector()
        collector.feed(markup)
        candidates = collector.anchors
    else:
        candidates = [(url, "") for url in extract_urls(markup)]
    items, seen = [], set()
    for url, text in candidates:
        if not url.startswith(("http://", "https://")) or not _is_job_host(url):
            continue
        path = urlsplit(url).path.lower()
        lowered = text.lower()
        if any(word in lowered for word in NOISE_WORDS) or any(path.startswith(p) for p in NOISE_PATHS):
            continue
        if len(text) < 30 and not looks_like_job_link(url):
            continue
        key = (url_key(url), text[:60])
        if key in seen:
            continue
        seen.add(key)
        items.append({"url": url, "snippet": text})
    return items


def _sender_is_alert(message):
    sender = str(message.get("from", "")).lower()
    return any(name in sender for name in ALERT_SENDERS)


def fetch_alert_links(days=7, limit=40):
    """Lit en lecture seule le libellé d'alertes et les e-mails d'emploi de la boîte de réception."""
    settings = gmail_settings()
    if not settings["configured"]:
        raise OfferError("Gmail n'est pas configuré (GMAIL_ADDRESS et GMAIL_APP_PASSWORD).")
    since = (date.today() - timedelta(days=days)).strftime("%d-%b-%Y")
    items, seen = [], set()
    try:
        mailbox = imaplib.IMAP4_SSL("imap.gmail.com", timeout=30)
        try:
            mailbox.login(settings["address"], settings["password"])
            for box, must_match_sender in ((f'"{settings["label"]}"', False), ("INBOX", True)):
                status, _ = mailbox.select(box, readonly=True)
                if status != "OK":
                    continue
                status, data = mailbox.search(None, "SINCE", since)
                for number in reversed((data[0] or b"").split()):
                    _, fetched = mailbox.fetch(number, "(BODY.PEEK[])")
                    message = email.message_from_bytes(fetched[0][1], policy=policy.default)
                    if must_match_sender and not _sender_is_alert(message):
                        continue
                    for part in message.walk():
                        kind = part.get_content_type()
                        if kind not in {"text/html", "text/plain"}:
                            continue
                        if kind == "text/plain" and message.get_body(("html",)) is not None:
                            continue
                        for item in extract_alert_items(part.get_content(), is_html=kind == "text/html"):
                            if url_key(item["url"]) not in seen:
                                seen.add(url_key(item["url"]))
                                items.append(item)
                    if len(items) >= limit * 3:
                        break
        finally:
            try:
                mailbox.logout()
            except (imaplib.IMAP4.error, OSError):
                pass
    except imaplib.IMAP4.error as exc:
        raise OfferError("Connexion Gmail refusée : vérifie l'adresse et le mot de passe d'application.") from exc
    except (OSError, TimeoutError) as exc:
        raise OfferError("Gmail est injoignable.") from exc
    return items[:limit]
