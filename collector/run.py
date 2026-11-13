"""Recolector de Remoto Junior.  Uso:  python collector/run.py  [--offline DIR]
Descarga fuentes permitidas -> normaliza -> deduplica -> clasifica -> site/data/jobs.json
--offline DIR : lee JSON crudos guardados antes (para depurar reglas sin volver a llamar APIs)."""
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import classify  # noqa: E402
import sources  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "jobs.json"
RAW = Path(__file__).parent / "out"


def main():
    RAW.mkdir(exist_ok=True)
    ahora = datetime.now(timezone.utc)
    crudo, estado = [], {}
    offline = "--offline" in sys.argv
    for nombre, fn in sources.FETCHERS.items():
        try:
            if offline:
                lst = json.loads((RAW / f"raw_{nombre}.json").read_text("utf-8"))
            else:
                lst = fn()
                (RAW / f"raw_{nombre}.json").write_text(json.dumps(lst, ensure_ascii=False), "utf-8")
            entradas = len(lst)
            lst = [x for x in lst if x]  # None = presencial/hibrido de GoB (cuenta como entrada)
            estado[nombre] = {"ok": True, "entradas": entradas, "remotas_o_utiles": len(lst)}
            crudo += lst
            print(f"[ok] {nombre}: {entradas} entradas", flush=True)
        except Exception as e:  # una fuente caida no tumba a las demas
            estado[nombre] = {"ok": False, "error": str(e)[:200], "entradas": 0}
            print(f"[FALLO] {nombre}: {e}", flush=True)

    entradas_total = sum(v["entradas"] for v in estado.values())
    # dedup por id exacto y luego por empresa+titulo (se prefiere la que trae salario, luego la mas nueva)
    por_id = {}
    for j in crudo:
        por_id.setdefault((j["fuente"], j["id"]), j)
    unicas = {}
    for j in por_id.values():
        k = classify.clave_dedup(j)
        o = unicas.get(k)
        if o is None or (bool(j.get("salario")), j.get("fecha") or "") > (bool(o.get("salario")), o.get("fecha") or ""):
            unicas[k] = j
    descartes, buenas, auditoria = Counter(), [], []
    limite = ahora - timedelta(days=classify.MAX_DIAS)
    for j in unicas.values():
        if not j.get("url") or not j.get("titulo"):
            descartes["datos_incompletos"] += 1
            continue
        try:
            f = datetime.fromisoformat(j["fecha"].replace("Z", "+00:00")) if j.get("fecha") else None
            if f and f.tzinfo is None:
                f = f.replace(tzinfo=timezone.utc)
        except Exception:
            f = None
        if f and f < limite:
            descartes["vieja_mas_de_%d_dias" % classify.MAX_DIAS] += 1
            continue
        r, motivo = classify.clasificar(j)
        if r:
            buenas.append(r)
        else:
            descartes[motivo] += 1
            auditoria.append({"id": f"{j['fuente']}:{j['id']}", "titulo": j["titulo"], "empresa": j.get("empresa"), "motivo": motivo})
    orden = {"junior": 0, "entrada": 1}
    buenas.sort(key=lambda r: (r["fecha"] or "") , reverse=True)
    buenas.sort(key=lambda r: (orden[r["nivel"]], not r["incluye_mexico"], r["acepta"] != "mundo"))
    # nota: sort estable -> dentro de cada grupo, mas recientes primero
    por_fuente = Counter(r["fuente"] for r in buenas)
    for n in estado:
        estado[n]["sobreviven"] = por_fuente.get(n, 0)
    meta = {
        "actualizado": ahora.isoformat(timespec="seconds"), "reglas_version": classify.REGLAS_VERSION,
        "entradas_total": entradas_total, "tras_dedup": len(unicas), "sobreviven": len(buenas),
        "descartes": dict(descartes.most_common()), "fuentes": estado,
        "fuentes_info": sources.SOURCES, "fuentes_descartadas": sources.DESCARTADAS,
        "max_dias": classify.MAX_DIAS, "max_anios": classify.MAX_ANIOS_JUNIOR,
        "areas": classify.AREA_NOMBRE,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "jobs": buenas}, ensure_ascii=False, indent=1), "utf-8")
    (RAW / "descartadas.json").write_text(json.dumps(auditoria, ensure_ascii=False, indent=1), "utf-8")
    print(f"\nEntradas: {entradas_total} | tras dedup: {len(unicas)} | sobreviven: {len(buenas)}")
    for k, v in descartes.most_common():
        print(f"  descartadas por {k}: {v}")
    print("  por fuente:", dict(por_fuente))
    if not buenas and entradas_total == 0:
        sys.exit(1)  # que Actions marque error y no publique una pagina vacia


if __name__ == "__main__":
    main()
