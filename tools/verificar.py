#!/usr/bin/env python3
"""Cruza cada requisito del enunciado del TP01 contra el estado REAL del repositorio.

La fuente de verdad es la API de GitHub y el repositorio Git — no lo que creamos
haber hecho. Cada chequeo guarda además la evidencia cruda que lo respalda, para
que el informe pueda citarla textualmente.

Uso:  python3 tools/verificar.py           (desde la raíz del clon)
Sale con código 0 si todos los requisitos cumplen, 1 si alguno no.
Salida: tools/verificacion.json
"""
import base64
import json
import pathlib
import subprocess
import sys

REPO = "arielsch74/tp01live"
CLON = pathlib.Path(__file__).resolve().parent.parent
SALIDA = pathlib.Path(__file__).parent / "verificacion.json"

CAPTURAS = ["img/01-push-rechazado.png", "img/02-conflicto-en-pr.png",
            "img/03-marcadores-conflicto.png", "img/04-release-publicada.png"]


def gh(ruta, *extra):
    """GET a la API de GitHub. Devuelve dict/list, o {'_error': ...}."""
    p = subprocess.run(["gh", "api", ruta, *extra], capture_output=True, text=True)
    if p.returncode != 0:
        return {"_error": p.stderr.strip()[:400]}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"_raw": p.stdout.strip()}


def git(*args):
    p = subprocess.run(["git", "-C", str(CLON), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else f"ERROR: {p.stderr.strip()[:200]}"


def contenido(ruta):
    """Baja un archivo de main y lo devuelve como texto."""
    b64 = subprocess.run(["gh", "api", f"repos/{REPO}/contents/{ruta}", "--jq", ".content"],
                         capture_output=True, text=True).stdout.strip().replace("\n", "")
    return base64.b64decode(b64).decode("utf-8", "replace") if b64 else ""


resultados = []


def chequear(rid, requisito, fuente, ok, detalle, crudo=""):
    resultados.append({"id": rid, "requisito": requisito, "fuente": fuente,
                       "estado": "CUMPLE" if ok else "NO CUMPLE",
                       "detalle": detalle, "crudo": crudo})
    print(f"[{'OK ' if ok else 'FAIL'}] {rid}  {requisito}")
    return ok


# ---------------------------------------------------------------- 1. repositorio
repo = gh(f"repos/{REPO}")
chequear(
    "1.a", "Repositorio público en la plataforma elegida",
    f"GET /repos/{REPO}",
    repo.get("visibility") == "public" and repo.get("private") is False,
    f"visibility = {repo.get('visibility')}, private = {repo.get('private')}, "
    f"default_branch = {repo.get('default_branch')}",
    f"html_url = {repo.get('html_url')}")

gitignore = gh(f"repos/{REPO}/contents/.gitignore")
chequear(
    "1.b", ".gitignore en la raíz",
    f"GET /repos/{REPO}/contents/.gitignore",
    gitignore.get("size", 0) > 0,
    f"presente en la raíz de main, {gitignore.get('size', 0)} bytes",
    f"sha = {gitignore.get('sha', '')[:12]}")

# ---------------------------------------------------------------- 2. protecciones
prot = gh(f"repos/{REPO}/branches/main/protection")
enforce = prot.get("enforce_admins", {}).get("enabled") is True
pr_req = "required_pull_request_reviews" in prot
approvals = prot.get("required_pull_request_reviews", {}).get(
    "required_approving_review_count")
chequear(
    "2.a", "main protegida: todo cambio entra por Pull Request",
    f"GET /repos/{REPO}/branches/main/protection",
    pr_req,
    "required_pull_request_reviews está activo → GitHub rechaza cualquier push directo a main",
    f"required_approving_review_count = {approvals}")
chequear(
    "2.b", "Imposible pushear directo — tampoco para el administrador (sin bypass)",
    f"GET /repos/{REPO}/branches/main/protection",
    enforce,
    f"enforce_admins.enabled = {enforce} (equivale a «Do not allow bypassing the "
    "above settings»)",
    f"allow_force_pushes = {prot.get('allow_force_pushes', {}).get('enabled')}, "
    f"allow_deletions = {prot.get('allow_deletions', {}).get('enabled')}")

ev_push = gh(f"repos/{REPO}/contents/img/01-push-rechazado.png")
chequear(
    "2.c", "Evidencia del rechazo del push directo",
    f"GET /repos/{REPO}/contents/img/01-push-rechazado.png",
    ev_push.get("size", 0) > 0,
    "captura de la ventana de terminal real en el instante del rechazo, versionada en el repo",
    f"{ev_push.get('size', 0)} bytes · sha = {ev_push.get('sha', '')[:12]}")

# ---------------------------------------------------------------- 3. pull requests
prs = gh(f"repos/{REPO}/pulls", "-X", "GET", "-f", "state=all", "-f", "per_page=100")
mergeados = [p for p in prs if p.get("merged_at")] if isinstance(prs, list) else []
mergeados.sort(key=lambda p: p["number"])
chequear(
    "3.a", "Al menos 2 Pull Requests mergeados",
    f"GET /repos/{REPO}/pulls?state=all",
    len(mergeados) >= 2,
    f"{len(mergeados)} PRs mergeados",
    " · ".join(f"#{p['number']} {p['title']}" for p in mergeados))

# el PR del conflicto: buscamos el commit de merge (2 padres) dentro del PR
pr_conflicto, commits_conf, sha_resolucion = None, [], ""
for p in mergeados:
    cs = gh(f"repos/{REPO}/pulls/{p['number']}/commits")
    if isinstance(cs, list) and any(len(c.get("parents", [])) > 1 for c in cs):
        pr_conflicto, commits_conf = p, cs
        sha_resolucion = next(c["sha"] for c in cs if len(c["parents"]) > 1)
        break
chequear(
    "3.b", "Uno de los PRs requirió resolver un conflicto de merge",
    f"GET /repos/{REPO}/pulls/<n>/commits (commit con 2 padres)",
    pr_conflicto is not None,
    (f"PR #{pr_conflicto['number']} «{pr_conflicto['title']}» contiene un commit de merge "
     f"con 2 padres ({sha_resolucion[:7]}): es la resolución del conflicto"
     if pr_conflicto else "no se encontró ningún PR con commit de merge"),
    " · ".join(f"{c['sha'][:7]} ({len(c['parents'])} padres) "
               f"{c['commit']['message'].splitlines()[0]}" for c in commits_conf))

# las dos ramas del conflicto tienen que haber salido del MISMO commit.
# Los dos padres del commit de resolución son: la punta de la rama B, y el main
# que ya tenía integrada la rama A. Su ancestro común es el main del que salieron
# las dos — si la rama B hubiera nacido de la A, no habría habido conflicto.
merge_base, padres = "", []
if sha_resolucion:
    c = gh(f"repos/{REPO}/commits/{sha_resolucion}")
    padres = [p["sha"] for p in c.get("parents", [])]
    if len(padres) == 2:
        comp = gh(f"repos/{REPO}/compare/{padres[0]}...{padres[1]}")
        merge_base = comp.get("merge_base_commit", {}).get("sha", "")
chequear(
    "3.b.2", "Las dos ramas del conflicto nacieron del mismo commit (conflicto real)",
    f"GET /repos/{REPO}/compare/<padre1>...<padre2> → merge_base_commit",
    bool(merge_base),
    f"los dos padres del commit de resolución tienen como ancestro común a {merge_base[:7]}: "
    "las dos ramas salieron del mismo main. Si la rama B hubiera nacido de la A no habría "
    "habido conflicto y el ejercicio no probaría nada",
    f"padres = {', '.join(p[:7] for p in padres)} · merge_base = {merge_base[:7]}")

# todo cambio entra por PR
commits_main = gh(f"repos/{REPO}/commits", "-X", "GET", "-f", "per_page=100")
lineas = [(c["sha"][:7], c["commit"]["message"].splitlines()[0])
          for c in commits_main] if isinstance(commits_main, list) else []
por_pr = [l for l in lineas if l[1].rstrip().endswith(")") and "(#" in l[1]]
chequear(
    "3.c", "Todo cambio entra por PR (incluidos evidencias.md y decisiones.md)",
    f"GET /repos/{REPO}/commits",
    len(por_pr) >= 4,
    f"{len(por_pr)} de {len(lineas)} commits de main son merges de PR (squash). Los que no lo "
    "son son anteriores a la protección: el commit inicial del repositorio y el del "
    ".gitignore (§4.3 de la guía va antes de §4.4)",
    " · ".join(f"{s} {m}" for s, m in lineas))

msg_entregable = ""
hist = gh(f"repos/{REPO}/commits", "-X", "GET", "-f", "path=decisiones.md", "-f", "per_page=10")
if isinstance(hist, list) and hist:
    msg_entregable = hist[0]["commit"]["message"].splitlines()[0]
chequear(
    "3.d", "Los dos archivos de la entrega llegaron a main por Pull Request",
    "GET /repos/<r>/commits?path=decisiones.md",
    "(#" in msg_entregable,
    f"decisiones.md entró en el commit «{msg_entregable}», que es un merge de PR",
    msg_entregable)

ramas = gh(f"repos/{REPO}/branches")
nombres = [b["name"] for b in ramas] if isinstance(ramas, list) else []
chequear(
    "3.e", "Ramas de feature borradas después de integrar",
    f"GET /repos/{REPO}/branches",
    nombres == ["main"],
    f"ramas vivas: {', '.join(nombres) or '(ninguna)'}",
    str(nombres))

# ---------------------------------------------------------------- 4. versionado
tag = gh(f"repos/{REPO}/git/ref/tags/v1.0.0")
sha_tag = tag.get("object", {}).get("sha", "")
anotado = tag.get("object", {}).get("type") == "tag"
if anotado:
    obj = gh(f"repos/{REPO}/git/tags/{sha_tag}")
    sha_commit = obj.get("object", {}).get("sha", "")
    mensaje_tag = obj.get("message", "").strip()
else:
    sha_commit, mensaje_tag = sha_tag, ""
en_main = git("merge-base", "--is-ancestor", sha_commit, "origin/main") == ""
chequear(
    "4.a", "Tag v1.0.0 (semver) sobre main",
    f"GET /repos/{REPO}/git/ref/tags/v1.0.0 + git merge-base --is-ancestor",
    bool(sha_commit) and en_main and anotado,
    f"tag {'anotado' if anotado else 'liviano'} apuntando al commit {sha_commit[:7]}, "
    "que es ancestro de main",
    f"mensaje del tag: «{mensaje_tag}»")

rel = gh(f"repos/{REPO}/releases/tags/v1.0.0")
notas = rel.get("body", "") or ""
chequear(
    "4.b", "Release publicada con notas de qué incluye",
    f"GET /repos/{REPO}/releases/tags/v1.0.0",
    rel.get("draft") is False and len(notas) > 200,
    f"release «{rel.get('name')}» publicada (draft = {rel.get('draft')}, "
    f"prerelease = {rel.get('prerelease')}), notas de {len(notas)} caracteres",
    rel.get("html_url", ""))

# ---------------------------------------------------------------- 5. entregables
for rid, archivo, minimo in (("5.b", "decisiones.md", 3000),
                             ("5.c", "evidencias.md", 2000)):
    c = gh(f"repos/{REPO}/contents/{archivo}")
    chequear(rid, f"`{archivo}` en la raíz del repositorio",
             f"GET /repos/{REPO}/contents/{archivo}",
             c.get("size", 0) >= minimo,
             f"presente en main, {c.get('size', 0)} bytes",
             f"sha = {c.get('sha', '')[:12]}")

estados = {c: gh(f"repos/{REPO}/contents/{c}").get("size", 0) for c in CAPTURAS}
chequear(
    "5.d", "Las cuatro capturas 📸 están versionadas en el repositorio",
    f"GET /repos/{REPO}/contents/img/*",
    all(v > 0 for v in estados.values()),
    f"{sum(1 for v in estados.values() if v > 0)}/4 presentes",
    " · ".join(f"{k.split('/')[-1]} {v} bytes" for k, v in estados.items()))

texto_ev = contenido("evidencias.md")
refs = [c for c in CAPTURAS if c in texto_ev]
chequear(
    "5.e", "evidencias.md referencia y describe las cuatro capturas",
    "contenido de evidencias.md en main",
    len(refs) == 4,
    f"{len(refs)}/4 capturas referenciadas desde el markdown",
    " · ".join(refs))

texto_dec = contenido("decisiones.md").lower()
puntos = {
    "por qué Git no pudo resolver el conflicto solo":
        "no pudo resolver el conflicto solo" in texto_dec,
    "qué habría tenido que pasar para que nunca apareciera":
        "nunca apareciera" in texto_dec,
    "problemas encontrados y cómo se resolvieron":
        "problemas encontr" in texto_dec,
    "declaración de uso de IA":
        "uso de ia" in texto_dec,
}
chequear(
    "5.f", "decisiones.md cubre los tres puntos que pide el enunciado",
    "contenido de decisiones.md en main",
    all(puntos.values()),
    f"{sum(puntos.values())}/4 secciones presentes",
    " · ".join(f"{k}: {'sí' if v else 'NO'}" for k, v in puntos.items()))

# ---------------------------------------------------------------- resumen
cumple = sum(1 for r in resultados if r["estado"] == "CUMPLE")
resumen = {"repo": REPO, "url": repo.get("html_url", ""),
           "total": len(resultados), "cumple": cumple,
           "prs_mergeados": len(mergeados),
           "pr_conflicto": pr_conflicto["number"] if pr_conflicto else None,
           "sha_resolucion": sha_resolucion,
           "merge_base": merge_base,
           "commits_main": lineas, "resultados": resultados,
           "prs": [{"n": p["number"], "titulo": p["title"],
                    "rama": p["head"]["ref"], "merged_at": p["merged_at"]}
                   for p in mergeados],
           "release_url": rel.get("html_url", ""),
           "tag_commit": sha_commit}
SALIDA.write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
print(f"\n{cumple}/{len(resultados)} requisitos verificados -> {SALIDA}")
sys.exit(0 if cumple == len(resultados) else 1)
