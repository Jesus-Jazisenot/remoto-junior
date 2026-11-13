"""Reglas transparentes de clasificacion. Nada de IA ni puntajes opacos:
cada decision devuelve un motivo legible. Las mismas reglas estan descritas en
site/como-filtramos.html. REGLAS_VERSION cambia cuando cambia cualquier regla."""
import re

REGLAS_VERSION = "2026-11-12.1"
MAX_DIAS = 45          # vacantes mas viejas se descartan
MAX_ANIOS_JUNIOR = 2   # se pide 3+ anios -> fuera

LATAM = {
    "mexico", "méxico", "argentina", "bolivia", "brazil", "brasil", "chile", "colombia", "costa rica", "cuba",
    "dominican republic", "república dominicana", "republica dominicana", "ecuador", "el salvador", "guatemala",
    "honduras", "nicaragua", "panama", "panamá", "paraguay", "peru", "perú", "uruguay", "venezuela",
    "puerto rico",
}
# nombre canonico para mostrar
CANON = {"méxico": "Mexico", "brasil": "Brazil", "república dominicana": "Dominican Republic",
         "republica dominicana": "Dominican Republic", "panamá": "Panama", "perú": "Peru"}

ISO_LATAM = {"MX": "Mexico", "AR": "Argentina", "BO": "Bolivia", "BR": "Brazil", "CL": "Chile", "CO": "Colombia",
             "CR": "Costa Rica", "CU": "Cuba", "DO": "Dominican Republic", "EC": "Ecuador", "SV": "El Salvador",
             "GT": "Guatemala", "HN": "Honduras", "NI": "Nicaragua", "PA": "Panama", "PY": "Paraguay", "PE": "Peru",
             "UY": "Uruguay", "VE": "Venezuela", "PR": "Puerto Rico"}

# --- residencia / autorizacion de trabajo (se busca en titulo + descripcion) ---
RE_RESIDENCIA = re.compile(
    r"(must\s+(be\s+)?(located|based|reside|living|live|resident)\s+(in|within)\s+(the\s+)?(u\.?s\.?a?\.?|united states|uk|united kingdom|canada|eu|europe|european union))"
    r"|(u\.?s\.?\s*(citizen|citizenship|resident|residents|person|based only))"
    r"|((authori[sz]ed|eligible|legally entitled|right)\s+to\s+work\s+(in|within)\s+(the\s+)?(u\.?s\.?a?\.?|united states|uk|united kingdom|canada|eu|european union))"
    r"|(security clearance)|(green card)|(\bw-?2\b)|(must\s+reside\s+in\s+the\s+(us|u\.s))"
    r"|(candidates?\s+(must\s+)?(be\s+)?(located|based)\s+in\s+the\s+(us|u\.s|united states))"
    r"|(only\s+(open\s+)?to\s+(candidates|applicants)\s+(located\s+)?in\s+(the\s+)?(us|u\.s|united states|europe|eu|uk|canada))"
    r"|(eu\s*/?\s*eea\s+(only|citizens|residents))|(work\s+permit\s+for\s+(the\s+)?(eu|uk|us))"
    r"|(ciudadan[oa]\s+(estadounidense|europe[oa]|de\s+ee\.?\s*uu))|(residencia\s+(legal\s+)?en\s+(ee\.?\s*uu|estados unidos|espa[nñ]a|europa))",
    re.I)

# --- profesiones reguladas / no tecnicas (en el titulo) ---
RE_NO_TECH = re.compile(
    r"\b(physician|nurse|doctor|surgeon|attorney|lawyer|pharmacist|dentist|therapist|veterinar\w*|cpa|accountant|"
    r"interpreter|translator|teacher|tutor of|truck|driver|recruiter|sales|ventas|marketing|travel advisor|"
    r"real estate|insurance|cashier|receptionist|data\s+entry|intake|accounting|bookkeep\w*)\b|\bMD\b", re.I)

# titulo que declara un pais/region fuera de LatAm: "(US)", "- USA", "(CAN)", "UK only"...
RE_TITULO_PAIS = re.compile(
    r"(\((us|usa|can|canada|uk|eu|emea|apac)\)|[-–|]\s*(us|usa|uk|canada)\s*$|\bus[- ]based\b|\b(us|usa|uk|canada|europe)\s+only\b|\bremote[- ]eligible\s+in\b|\b(based|located)\s+in\b)", re.I)

# --- nivel ---
RE_SENIOR_TITULO = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|head of|director|manager|gerente|architect|arquitect[oa]|vp|"
    r"semi[- ]?senior|ssr|mid[- ]?level|mid|intermediate|expert|specialist ii|ii|iii|iv)\b", re.I)
RE_JUNIOR_TITULO = re.compile(
    r"\b(junior|jr\.?|entry[- ]level|trainee|intern(ship)?|becari[oa]|practicante|pasante|graduate|"
    r"apprentice|aprendiz|sin experiencia|no experience)\b", re.I)
JUNIOR_FUENTE = {"entry-level", "junior", "sin experiencia", "entry level"}
SENIOR_FUENTE = {"mid-level", "senior", "manager", "director", "executive", "semi senior", "expert",
                 "midweight", "lead"}
RE_JUNIOR_DESC = re.compile(
    r"(no\s+(previous\s+|prior\s+)?(work\s+)?experience\s+(is\s+)?(required|needed|necessary))"
    r"|(sin\s+experiencia(\s+previa)?)|(entry[- ]level)|(recent\s+graduates?)|(fresh\s+graduates?)"
    r"|(reci[eé]n\s+egresad[oa]s?)|(0\s*[-–a]\s*1\s+years?)|(will\s+train\s+you)|(we\s+train)|(estudiantes?\s+de\s+(ingenier|sistemas|inform))",
    re.I)
RE_ANIOS = re.compile(
    r"(?:(?:at least|minimum(?: of)?|min\.?|m[ií]nimo(?: de)?|al menos|más de|more than)\s*)?"
    r"(\d{1,2})\s*\+?\s*(?:(?:-|–|to|a)\s*\d{1,2}\s*)?(?:\+\s*)?(?:years?|yrs?|a[nñ]os)"
    r"(?:['’]s)?\s*(?:of\s+|de\s+)?(?:[\w/\-\.,]+\s+){0,5}?(?:experience|experiencia)", re.I)
RE_ANIOS_ES = re.compile(r"experiencia(?:\s+\w+){0,4}?\s+(?:de|m[ií]nima de|m[ií]nimo de)\s+(\d{1,2})\s*\+?\s*a[nñ]os", re.I)

# --- area (titulo manda; categoria de la fuente solo como respaldo) ---
AREAS = [  # orden = prioridad
    ("ia", re.compile(r"(annotat|anotaci|etiquetad|labell?ing|ai\s+(trainer|tutor|rater|evaluator|data)|"
                      r"(conversation|response|search|content|model)\s+(evaluator|rater|reviewer)|\brlhf\b|"
                      r"\bprompt\b|\bllm\b|ai\s+training|data\s+collector|raters?\b)", re.I)),
    ("qa", re.compile(r"(\bqa\b|quality\s+assurance|\btesters?\b|test\s+engineer|\bsdet\b|software\s+testing|"
                      r"calidad\s+de\s+software|pruebas\s+de\s+software|automation\s+test)", re.I)),
    ("soporte", re.compile(r"(technical\s+support|tech\s+support|\bit\s+support|support\s+engineer|help\s*desk|service\s+desk|"
                           r"soporte\s+(t[eé]cnico|ti|inform)|t[eé]cnico\s+de\s+soporte|application\s+support|desktop\s+support|"
                           r"support\s+technician|technical\s+(customer\s+)?(specialist|analyst)|customer\s+support\s+engineer)", re.I)),
    ("datos", re.compile(r"(data\s+(analyst|scientist|engineer|science|entry|analytics|specialist)|analista\s+de\s+datos|"
                         r"business\s+intelligence|\bbi\s+(analyst|developer)|\bsql\b|power\s*bi|tableau|analytics|"
                         r"machine\s+learning|\bml\s+engineer|\bml\b|estad[ií]stic|ciencia\s+de\s+datos|"
                         r"ingenier[oa]\s+de\s+datos|big\s+data|\betl\b)", re.I)),
    ("devops", re.compile(r"(devops|\bsre\b|site\s+reliability|sysadmin|system\s+administrator|administrador\s+de\s+sistemas|"
                          r"cloud\s+(engineer|support|operations)|infrastructure|network\s+(engineer|admin|technician)|"
                          r"redes|ciberseguridad|cyber\s*security|security\s+(analyst|engineer)|soc\s+analyst|analista\s+(de\s+)?(soc|seguridad|ciberseguridad)|\baws\b|\bazure\b)", re.I)),
    ("dev", re.compile(r"((?<!business\s)(?<!sales\s)(?<!real estate\s)(?<!account\s)developer|programmer|programador|desarrollador|"
                       r"(software|web|mobile|front[- ]?end|back[- ]?end|full[- ]?stack|platform|application|"
                       r"integration|automation|systems?|python|java|node|react|ios|android|rpa)\s+(engineer|developer|dev)|"
                       r"\bsoftware\b|front[- ]?end|back[- ]?end|full[- ]?stack|\brpa\b|ingenier[oa]\s+de\s+software|"
                       r"\bwordpress\b|\bphp\b|\bflutter\b|\bunity\b)", re.I)),
]
CAT_FUENTE_AREA = {"programming": "dev", "mobile-development": "dev", "data-science-analytics": "datos",
                   "machine-learning-ai": "datos", "sysadmin-devops-qa": "devops", "cybersecurity": "devops",
                   "technical-support": "soporte"}
AREA_NOMBRE = {"dev": "Desarrollo", "datos": "Datos", "qa": "QA / Pruebas", "soporte": "Soporte técnico",
               "ia": "IA / Anotación", "devops": "Infra / DevOps / Seguridad"}

# --- idioma ---
RE_INGLES = re.compile(r"\b(english|ingl[eé]s|bilingual|biling[uü]e)\b", re.I)
RE_ING_AVANZADO = re.compile(
    r"(fluent|fluency|c1|c2|advanced\s+english|english\s+(?:\w+\s+){0,3}(advanced|native|fluent)|native\s+english|"
    r"ingl[eé]s\s+(avanzado|fluido|nativo|c1|c2)|ingl[eé]s\s+(?:\w+\s+){0,2}(avanzado|fluido)|excellent\s+(written\s+and\s+(verbal|spoken)\s+)?english|"
    r"biling[uü]e|bilingual)", re.I)
RE_ING_INTER = re.compile(r"(\bb1\b|\bb2\b|intermediate|intermedio|conversational|upper[- ]intermediate)", re.I)
ES_WORDS = {"de", "la", "el", "en", "y", "con", "para", "los", "las", "del", "una", "un", "que", "por", "se", "experiencia"}
EN_WORDS = {"the", "and", "of", "to", "in", "for", "with", "you", "we", "a", "is", "our", "will", "are", "experience"}


def _n(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def idioma_desc(texto):
    w = re.findall(r"[a-záéíóúñ]+", (texto or "")[:2000].lower())
    es = sum(x in ES_WORDS for x in w)
    en = sum(x in EN_WORDS for x in w)
    return "es" if es > en * 1.1 else "en"


def _latam_en(lista):
    out = []
    for p in lista:
        k = p.strip().lower()
        if k in LATAM:
            c = CANON.get(k, p.strip().title() if k != p.strip() else p.strip())
            if c not in out:
                out.append(c)
    return out


# ---------------------------------------------------------------- elegibilidad
NEG_REGION = re.compile(r"(usa|us|u\.s\.?|united states|canada|north america|europe|eu|uk|emea|apac|asia|africa|oceania|australia|india|philippines|germany|spain)", re.I)
RE_MUNDO = re.compile(r"(worldwide|anywhere|work from anywhere|global|everywhere|any location|world)", re.I)
RE_LATAM_TXT = re.compile(r"(latam|latin america|latinoam[eé]rica|south america|am[eé]rica latina)", re.I)
RE_PAIS_LATAM_TITULO = re.compile(
    r"\b(m[eé]xico|argentina|colombia|chile|per[uú]|brasil|brazil|uruguay|ecuador|bolivia|paraguay|venezuela|"
    r"costa rica|panam[aá]|guatemala|honduras|el salvador|nicaragua|rep[uú]blica dominicana|dominican republic)\b", re.I)


def elegibilidad(j):
    """-> (acepta, paises, motivo). acepta: mundo | latam | pais | no | desconocido"""
    f = j["fuente"]
    if f == "himalayas":
        rp = j.get("restr_paises") or []
        tz = j.get("restr_tz") or []
        if tz and not any(-7 <= t <= -3 for t in tz):
            return "no", [], "zona horaria exigida no incluye LatAm"
        if not rp:
            return "mundo", [], "sin restricción de país (Himalayas)"
        lat = _latam_en(rp)
        if not lat:
            return "no", [], "restringida a países sin LatAm"
        return ("latam" if len(lat) >= 3 else "pais"), lat, f"restringida a: {', '.join(lat)} (+otros)"
    if f == "getonboard":
        regs = j.get("regiones_fuente") or []
        pais = ISO_LATAM.get((j.get("pais_empresa") or "").upper())
        lat_reg = [r for r in regs if r in ("south_america", "central_america", "north_america", "caribbean")]
        if regs and not lat_reg:
            return "no", [], "regiones permitidas fuera de LatAm (Get on Board)"
        if lat_reg:
            return "latam", [], "región permitida: " + ", ".join(lat_reg) + " (Get on Board)"
        if j.get("modalidad") == "fully_remote":
            return "latam", [], "100% remoto, sin región restringida (Get on Board, bolsa de LatAm)"
        if pais:  # remote_local sin region: remoto dentro del pais de la empresa
            return "pais", [pais], f"remoto solo dentro de {pais} (país de la empresa en Get on Board)"
        return "no", [], "remoto local fuera de LatAm (Get on Board)"
    if f == "weworkremotely":
        r = (j.get("region_fuente") or "").lower()
        if "anywhere" in r:
            return "mundo", [], "región 'Anywhere in the World' (WWR)"
        if RE_LATAM_TXT.search(r):
            return "latam", [], "región LatAm (WWR)"
        return "no", [], f"región '{j.get('region_fuente')}' (WWR)"
    if f == "jobicy":
        toks = [t.strip() for t in re.split(r",", j.get("geo_fuente") or "") if t.strip()]
        low = [t.lower() for t in toks]
        lat = _latam_en(toks)
        if "anywhere" in low:
            return "mundo", [], "geo 'Anywhere' (Jobicy)"
        if "latam" in low:
            return "latam", lat, "geo 'LATAM' (Jobicy)"
        if lat:
            return ("latam" if len(lat) >= 3 else "pais"), lat, f"geo: {', '.join(toks)} (Jobicy)"
        return "no", [], f"geo '{j.get('geo_fuente')}' (Jobicy)"
    if f == "remoteok":
        loc = j.get("ubicacion_txt") or ""
        desc = j.get("descripcion") or ""
        if loc:
            lat = _latam_en(re.split(r"[,;/|]", loc))
            if RE_LATAM_TXT.search(loc):
                return "latam", lat, f"ubicación '{loc}' menciona LatAm (Remote OK)"
            if lat:
                return ("latam" if len(lat) >= 3 else "pais"), lat, f"ubicación '{loc}' (Remote OK)"
            if RE_MUNDO.search(loc):
                return "mundo", [], f"ubicación '{loc}' (Remote OK)"
            return "no", [], f"ubicación '{loc}' no incluye LatAm (Remote OK)"
        head = desc[:1500]
        if RE_MUNDO.search(head) and re.search(r"(work\s+from\s+anywhere|anywhere\s+in\s+the\s+world|worldwide|fully\s+remote\s+.*anywhere)", head, re.I):
            return "mundo", [], "descripción dice worldwide/anywhere (Remote OK, sin campo de ubicación)"
        if RE_LATAM_TXT.search(head):
            return "latam", [], "descripción menciona LatAm (Remote OK)"
        return "desconocido", [], "sin ubicación declarada y sin mención de worldwide (Remote OK)"
    return "desconocido", [], "fuente sin regla"


# ---------------------------------------------------------------- nivel
def anios_requeridos(texto):
    vals = []
    for m in RE_ANIOS.finditer(texto or ""):
        vals.append(int(m.group(1)))
    for m in RE_ANIOS_ES.finditer(texto or ""):
        vals.append(int(m.group(1)))
    vals = [v for v in vals if v <= 20]
    return max(vals) if vals else None


def nivel(j):
    """-> (nivel, motivo). nivel: junior | entrada | no_junior | sin_senal"""
    t = j.get("titulo") or ""
    texto = (j.get("descripcion") or "")
    src = {s.lower() for s in (j.get("seniority_fuente") or []) if s}
    anios = anios_requeridos(texto)
    if src & SENIOR_FUENTE:
        return "no_junior", f"nivel de la fuente: {', '.join(sorted(src & SENIOR_FUENTE))}", anios
    if RE_SENIOR_TITULO.search(t) and not RE_JUNIOR_TITULO.search(t):
        return "no_junior", "título de nivel senior/medio", anios
    if anios is not None and anios > MAX_ANIOS_JUNIOR:
        return "no_junior", f"pide {anios}+ años de experiencia", anios
    if RE_JUNIOR_TITULO.search(t):
        return "junior", "título dice junior/entry/trainee/becario", anios
    if src & JUNIOR_FUENTE:
        return "junior", f"nivel de la fuente: {', '.join(sorted(src & JUNIOR_FUENTE))}", anios
    if RE_JUNIOR_DESC.search(texto):
        return "entrada", "la descripción dice sin experiencia / entry-level / recién egresado", anios
    if anios is not None:
        return "entrada", f"pide solo {anios} año(s) de experiencia", anios
    return "sin_senal", "no hay señal de nivel junior", anios


def area(j):
    t = j.get("titulo") or ""
    for nombre, rx in AREAS:
        if rx.search(t):
            return nombre
    for c in j.get("categorias") or []:
        k = (c or "").strip().lower()
        if j["fuente"] == "getonboard":
            for slug, a in CAT_FUENTE_AREA.items():
                if slug.replace("-", " ") in k.replace("/", " ").replace("&", " "):
                    return a
            if k in ("programming", "data science / analytics", "machine learning & ai", "sysadmin / devops / qa",
                     "cybersecurity", "mobile development", "technical support"):
                return {"programming": "dev", "data science / analytics": "datos", "machine learning & ai": "datos",
                        "sysadmin / devops / qa": "devops", "cybersecurity": "devops",
                        "mobile development": "dev", "technical support": "soporte"}[k]
    return None


def ingles(j):
    texto = f"{j.get('titulo') or ''} {j.get('descripcion') or ''}"
    lang = j.get("lang_fuente")
    d = "es" if lang in ("es",) else ("en" if lang in ("en",) else idioma_desc(j.get("descripcion")))
    if RE_INGLES.search(texto) or RE_ING_AVANZADO.search(texto):
        if RE_ING_AVANZADO.search(texto):
            return d, "avanzado"
        if RE_ING_INTER.search(texto):
            return d, "intermedio"
        return d, "si"
    if d == "en":
        return d, "si"  # descripcion y proceso en ingles
    return d, "no_requerido"


def salario_texto(s):
    if not s:
        return None
    per = {"hourly": "hora", "monthly": "mes", "yearly": "año", "annual": "año", "annually": "año", "weekly": "semana"}
    p = per.get((s.get("periodo") or "").lower(), s.get("periodo") or "")
    a, b = s.get("min"), s.get("max")
    if not a and not b:
        return None
    rango = f"{a:,.0f}" if (not b or a == b) else f"{a:,.0f}–{b:,.0f}"
    return f"{s.get('moneda') or '?'} {rango}" + (f" / {p}" if p else "")


def clasificar(j):
    """Devuelve (job_normalizado | None, motivo_descarte | None)."""
    texto = f"{j.get('titulo') or ''}. {j.get('descripcion') or ''}"
    acepta, paises, m_el = elegibilidad(j)
    if acepta in ("no", "desconocido"):
        return None, ("ubicacion_no_latam" if acepta == "no" else "ubicacion_desconocida")
    mres = RE_RESIDENCIA.search(texto)
    if mres:
        return None, "exige_residencia_ciudadania"
    if (RE_TITULO_PAIS.search(j.get("titulo") or "") and not RE_LATAM_TXT.search(j.get("titulo") or "")
            and not RE_PAIS_LATAM_TITULO.search(j.get("titulo") or "")):
        return None, "titulo_indica_pais_fuera_de_latam"
    if RE_NO_TECH.search(j.get("titulo") or ""):
        return None, "profesion_no_tecnica"
    a = area(j)
    if not a:
        return None, "area_fuera_de_tecnologia"
    niv, m_niv, anios = nivel(j)
    if niv == "no_junior":
        return None, "nivel_no_junior"
    if niv == "sin_senal":
        return None, "sin_senal_de_nivel_junior"
    lang, ing = ingles(j)
    paises_tot = paises
    incluye_mx = acepta in ("mundo", "latam") or "Mexico" in paises
    return {
        "id": f"{j['fuente']}:{j['id']}", "titulo": j["titulo"], "empresa": j.get("empresa") or "",
        "fuente": j["fuente"], "url": j["url"], "fecha": j.get("fecha"),
        "area": a, "nivel": niv, "acepta": acepta, "paises": paises_tot, "incluye_mexico": incluye_mx,
        "idioma": lang, "ingles": ing, "salario": j.get("salario"), "salario_texto": salario_texto(j.get("salario")),
        "anios_pedidos": anios,
        "motivos": {"ubicacion": m_el, "nivel": m_niv},
        "resumen": (j.get("descripcion") or "")[:240].rsplit(" ", 1)[0] + ("…" if len(j.get("descripcion") or "") > 240 else ""),
    }, None


def clave_dedup(j):
    return _n(j.get("empresa")) + "|" + _n(j.get("titulo"))
