const APP_URL = "http://127.0.0.1:5000/api/extension/offer";
const statusBox = document.getElementById("status");
const tokenInput = document.getElementById("token");

function show(message, kind) {
  statusBox.textContent = message;
  statusBox.className = kind || "";
}

// Exécutée dans la page : lit uniquement l'onglet actif, à la demande de l'utilisateur.
function extractOffer() {
  const clean = (text) => (text || "").replace(/\s+\n/g, "\n").replace(/[ \t]+/g, " ").trim();
  const first = (selectors) => {
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      if (node && clean(node.innerText)) return clean(node.innerText);
    }
    return "";
  };
  const meta = (name) =>
    (document.querySelector(`meta[property="${name}"], meta[name="${name}"]`) || {}).content || "";

  let title = "", company = "", place = "", description = "";
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const stack = [JSON.parse(script.textContent)];
      while (stack.length) {
        const node = stack.pop();
        if (Array.isArray(node)) { stack.push(...node); continue; }
        if (!node || typeof node !== "object") continue;
        if (node["@type"] === "JobPosting") {
          const holder = document.createElement("div");
          holder.innerHTML = node.description || "";
          title = node.title || title;
          company = (node.hiringOrganization || {}).name || company;
          const spot = Array.isArray(node.jobLocation) ? node.jobLocation[0] : node.jobLocation;
          place = ((spot || {}).address || {}).addressLocality || place;
          description = clean(holder.innerText || holder.textContent);
        }
        stack.push(...Object.values(node).filter((v) => v && typeof v === "object"));
      }
    } catch (error) { /* JSON-LD illisible : on passe au repli */ }
  }

  const selection = clean(String(window.getSelection()));
  if (selection.length >= 100) description = selection;
  if (!title) {
    title = first(["h1", ".job-details-jobs-unified-top-card__job-title", ".top-card-layout__title"])
      || meta("og:title") || document.title;
  }
  if (!company) {
    company = first([
      ".job-details-jobs-unified-top-card__company-name", ".topcard__org-name-link",
      '[data-testid="company-name"]', '[itemprop="hiringOrganization"]',
    ]) || meta("og:site_name");
  }
  if (!description) {
    description = first([
      ".jobs-description__content", ".jobs-box__html-content", ".show-more-less-html__markup",
      "#jobDescriptionText", '[class*="job-description"]', '[class*="JobDescription"]',
      "article", "main",
    ]);
  }
  if (!description) description = clean(document.body.innerText);

  const current = new URL(window.location.href);
  const onLinkedIn = current.hostname.endsWith("linkedin.com");
  const jobId = current.searchParams.get("currentJobId");
  const url = onLinkedIn && jobId
    ? `https://www.linkedin.com/jobs/view/${jobId}/`
    : current.origin + current.pathname + (onLinkedIn ? "" : current.search);
  return { url, title, company, location: place, description: description.slice(0, 6000) };
}

async function save() {
  const token = tokenInput.value.trim();
  if (!token) { show("Colle d'abord le jeton affiché dans l'app.", "error"); return; }
  await chrome.storage.local.set({ token });
  show("Lecture de la page…");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: extractOffer });
    const response = await fetch(APP_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(result),
    });
    const data = await response.json().catch(() => ({}));
    if (response.status === 201) show(`Offre enregistrée : ${result.title}`, "ok");
    else if (data.status === "updated") show("Offre déjà suivie : description mise à jour.", "ok");
    else if (data.status === "duplicate") show("Cette offre est déjà dans ton suivi.", "ok");
    else show(data.error || `Erreur ${response.status}`, "error");
  } catch (error) {
    show("Impossible de lire cette page ou de joindre l'app (127.0.0.1:5000).", "error");
  }
}

chrome.storage.local.get("token").then(({ token }) => { if (token) tokenInput.value = token; });
document.getElementById("save").addEventListener("click", save);
