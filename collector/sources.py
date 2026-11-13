"""Descarga de fuentes permitidas. Cada funcion devuelve una lista de dicts
normalizados con 'raw_*' para que classify.py decida. Solo APIs/feeds publicos
cuyos terminos permiten mostrar las vacantes con atribucion y enlace.
Ver SOURCES (terminos verificados el 2026-11-12)."""
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = "RemotoJunior/0.1 (boletin de vacantes remotas para LatAm; bussnestjesus2005@gmail.com)"

SOURCES = {
    "himalayas": {
        "nombre": "Himalayas", "home": "https://himalayas.app",
        "terminos": "https://himalayas.app/terms (seccion 'Terms and Conditions for API Users', #113)",
        "condiciones": "Uso comercial permitido; el boton Aplicar debe usar applicationLink; identificar a Himalayas con enlace visible; no pasar a terceros.",
    },
    "getonboard": {
        "nombre": "Get on Board", "home": "https://www.getonbrd.com",
        "terminos": "https://www.getonbrd.com/help/que-puedo-hacer-con-la-api-de-get-on-board?lang=en (la API publica permite 'Display published jobs on another site')",
        "condiciones": "API publica sin llave; se enlaza siempre a la oferta publica y se nombra la fuente.",
    },
    "remoteok": {
        "nombre": "Remote OK", "home": "https://remoteok.com",
        "terminos": "https://remoteok.com/api (aviso 'legal' en el primer elemento del JSON)",
        "condiciones": "Enlazar a la URL de Remote OK (follow, sin nofollow) y mencionar Remote OK como fuente. No usar su logo.",
    },
    "weworkremotely": {
        "nombre": "We Work Remotely", "home": "https://weworkremotely.com",
        "terminos": "https://weworkremotely.com/remote-job-rss-feed",
        "condiciones": "Feed publico; 'anyone can use the feed, all we ask is that you attribute the links back to We Work Remotely'.",
    },
    "jobicy": {
        "nombre": "Jobicy", "home": "https://jobicy.com",
        "terminos": "https://jobi.cy/apidocs (friendlyNotice del JSON de la API)",
        "condiciones": "Acreditar a Jobicy con enlace directo; todos los botones de aplicar llevan a la URL original del feed.",
    },
}
DESCARTADAS = {
    "remotive": "Sus terminos (github.com/remotive-com/remote-jobs-api) prohiben pasar sus vacantes a terceros y usarlas para 'collect signups/email addresses'; un boletin con suscripcion lo incumple. Ademas retrasa 24 h.",
    "arbeitnow": "Foco Alemania/UE; no encontre terminos de redistribucion verificables y casi nada aplica a LatAm.",
}


def _get(url, tries=3, wait=3.0):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/xml"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(wait * (i + 1) * (3 if e.code == 429 else 1))
        except Exception as e:  # red, timeout
            last = e
            time.sleep(wait * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def _txt(s):
    s = re.sub(r"<(script|style).*?</\1>", " ", s or "", flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def arreglar_mojibake(s):
    """Remote OK a veces entrega UTF-8 mal decodificado (aparece 'â' + control). Se revierte si aplica."""
    if not isinstance(s, str) or ("â" not in s and "Ã" not in s):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except Exception:
        return s


def _iso(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(int(ts), timezone.utc).isoformat(timespec="seconds")


def himalayas(max_pages=15):
    """Search endpoint: entry-level abiertos a Mexico (incluye worldwide) + palabras junior."""
    out = []
    plan = [("seniority=Entry-level&country=MX", max_pages)]
    for kw in ("junior", "trainee", "intern", "associate developer"):
        plan.append((f"q={urllib.parse.quote(kw)}&country=MX", 3))
    for q, pages in plan:
        for p in range(1, pages + 1):
            d = json.loads(_get(f"https://himalayas.app/jobs/api/search?{q}&sort=recent&page={p}"))
            jobs = d.get("jobs") or []
            if not jobs:
                break
            for j in jobs:
                out.append({
                    "fuente": "himalayas", "id": j.get("guid"), "titulo": j.get("title"),
                    "empresa": j.get("companyName"), "url": j.get("applicationLink") or j.get("guid"),
                    "fecha": _iso(j["pubDate"]) if j.get("pubDate") else None,
                    "descripcion": _txt(j.get("description")),
                    "seniority_fuente": j.get("seniority") or [],
                    "categorias": (j.get("categories") or []) + (j.get("parentCategories") or []),
                    "restr_paises": j.get("locationRestrictions") or [],
                    "restr_tz": j.get("timezoneRestrictions") or [],
                    "salario": ({"min": j.get("minSalary"), "max": j.get("maxSalary"),
                                 "moneda": j.get("currency"), "periodo": j.get("salaryPeriod")}
                                if j.get("minSalary") or j.get("maxSalary") else None),
                    "ubicacion_txt": "",
                })
            time.sleep(2.0)
    return out


GOB_CATS = ["programming", "data-science-analytics", "sysadmin-devops-qa", "machine-learning-ai",
            "cybersecurity", "mobile-development", "technical-support"]


def getonboard(cats=GOB_CATS):
    out = []
    for cat in cats:
        page = 1
        while True:
            u = (f"https://www.getonbrd.com/api/v0/categories/{cat}/jobs?per_page=100&page={page}"
                 "&expand%5B%5D=company&expand%5B%5D=seniority&expand%5B%5D=location_regions")
            try:
                d = json.loads(_get(u))
            except RuntimeError:
                break  # categoria inexistente u otro error: no frena a las demas
            for j in d.get("data", []):
                a = j["attributes"]
                if a.get("remote_modality") not in ("fully_remote", "remote_local"):
                    out.append(None)  # cuenta como entrada, se descarta como presencial/hibrido
                    continue
                sen = (a.get("seniority") or {}).get("data") or {}
                emp = (a.get("company") or {}).get("data") or {}
                body = " ".join(_txt(a.get(k)) for k in ("description", "projects", "functions", "desirable"))
                out.append({
                    "fuente": "getonboard", "id": j["id"], "titulo": a.get("title"),
                    "empresa": (emp.get("attributes") or {}).get("name"),
                    "url": (j.get("links") or {}).get("public_url"),
                    "fecha": _iso(a["published_at"]) if a.get("published_at") else None,
                    "descripcion": body,
                    "seniority_fuente": [((sen.get("attributes") or {}).get("name"))] if sen else [],
                    "categorias": [a.get("category_name")],
                    "modalidad": a["remote_modality"],
                    "regiones_fuente": [r["id"] for r in ((a.get("location_regions") or {}).get("data") or [])],
                    "pais_empresa": (emp.get("attributes") or {}).get("country"),
                    "lang_fuente": a.get("lang"),
                    "salario": ({"min": a["min_salary"], "max": a["max_salary"], "moneda": "USD", "periodo": "monthly"}
                                if a.get("min_salary") else None),
                    "ubicacion_txt": "",
                })
            if page >= (d.get("meta") or {}).get("total_pages", 1):
                break
            page += 1
            time.sleep(0.5)
    return out


def remoteok():
    data = json.loads(_get("https://remoteok.com/api"))[1:]  # [0] = aviso legal
    out = []
    for j in data:
        out.append({
            "fuente": "remoteok", "id": j.get("id"), "titulo": arreglar_mojibake(j.get("position")), "empresa": arreglar_mojibake(j.get("company")),
            "url": j.get("url") or j.get("apply_url"), "fecha": j.get("date"),
            "descripcion": arreglar_mojibake(_txt(j.get("description"))), "seniority_fuente": [],
            "categorias": j.get("tags") or [], "ubicacion_txt": j.get("location") or "",
            "salario": ({"min": j["salary_min"], "max": j["salary_max"], "moneda": "USD", "periodo": "yearly"}
                        if j.get("salary_min") else None),
        })
    return out


def weworkremotely():
    root = ET.fromstring(_get("https://weworkremotely.com/remote-jobs.rss"))
    out = []
    for it in root.iter("item"):
        g = lambda t: (it.findtext(t) or "").strip()
        titulo = g("title")
        empresa = ""
        if ":" in titulo:
            empresa, titulo = [x.strip() for x in titulo.split(":", 1)]
        try:
            fecha = parsedate_to_datetime(g("pubDate")).isoformat(timespec="seconds")
        except Exception:
            fecha = None
        out.append({
            "fuente": "weworkremotely", "id": g("guid"), "titulo": titulo, "empresa": empresa,
            "url": g("link"), "fecha": fecha, "descripcion": _txt(g("description")),
            "seniority_fuente": [], "categorias": [g("category")] + [s.strip() for s in g("skills").split(",")],
            "ubicacion_txt": g("region") + " | " + g("country"), "region_fuente": g("region"), "salario": None,
        })
    return out


def jobicy():
    out, seen = [], set()
    for geo in ("latam", "anywhere"):
        cursor = None
        for _ in range(3):
            u = f"https://jobicy.com/api/v2/remote-jobs?count=100&geo={geo}" + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else "")
            d = json.loads(_get(u))
            for j in d.get("jobs", []):
                if j["id"] in seen:
                    continue
                seen.add(j["id"])
                sal = None
                if j.get("salaryMin"):
                    sal = {"min": int(j["salaryMin"]), "max": int(j.get("salaryMax") or j["salaryMin"]),
                           "moneda": j.get("salaryCurrency"), "periodo": j.get("salaryPeriod")}
                out.append({
                    "fuente": "jobicy", "id": str(j["id"]), "titulo": _txt(j.get("jobTitle")),
                    "empresa": _txt(j.get("companyName")), "url": j.get("url"), "fecha": j.get("pubDate"),
                    "descripcion": _txt(j.get("jobDescription")),
                    "seniority_fuente": [s.strip() for s in str(j.get("jobLevel") or "").split(",")],
                    "categorias": (j.get("jobIndustry") or []), "geo_fuente": j.get("jobGeo") or "",
                    "ubicacion_txt": j.get("jobGeo") or "", "salario": sal,
                })
            cursor = d.get("nextCursor")
            if not d.get("hasMore") or not cursor:
                break
            time.sleep(1.0)
    return out


FETCHERS = {"himalayas": himalayas, "getonboard": getonboard, "remoteok": remoteok,
            "weworkremotely": weworkremotely, "jobicy": jobicy}
