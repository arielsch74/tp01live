#!/usr/bin/env python3
"""Arma el informe de completitud del TP01 en PDF.

Lee tools/verificacion.json —generado consultando la API de GitHub en vivo— y las
capturas del repositorio, y produce un PDF con: la tabla requisito → estado, el
estado real del repositorio, las evidencias embebidas y la preparación para la
defensa oral. Los estados y los hashes NO se escriben a mano: salen del JSON.

Uso:  python3 tools/informe.py     (requiere playwright instalado)
"""
import base64
import html
import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
REPO_DIR = AQUI.parent
D = json.loads((AQUI / "verificacion.json").read_text())
SALIDA_PDF = REPO_DIR / "informe-completitud-tp01.pdf"
FECHA = "5 de agosto de 2026"

BASE = D["merge_base"][:7]
RESOL = D["sha_resolucion"][:7]
TAGC = D["tag_commit"][:7]
NCONF = D["pr_conflicto"]


def img64(rel):
    return "data:image/png;base64," + base64.b64encode((REPO_DIR / rel).read_bytes()).decode()


def e(x):
    return html.escape(str(x))


def crudo(rid):
    return next((r["crudo"] for r in D["resultados"] if r["id"] == rid), "")


def detalle(rid):
    return next((r["detalle"] for r in D["resultados"] if r["id"] == rid), "")


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
       font-size: 10.2pt; line-height: 1.5; color: #1c2128; margin: 0; }
h1 { font-size: 21pt; margin: 0 0 4px; letter-spacing: -.4px; }
h2 { font-size: 13.5pt; margin: 26px 0 8px; padding-bottom: 5px;
     border-bottom: 2px solid #0969da; color: #0b3d6b; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 16px 0 5px; color: #24292f; page-break-after: avoid; }
p  { margin: 0 0 8px; }
.sub { color: #57606a; font-size: 10pt; margin-bottom: 2px; }
.portada { border-bottom: 3px solid #0969da; padding-bottom: 14px; margin-bottom: 4px; }
.badge { display: inline-block; background: #1a7f37; color: #fff; font-weight: 700;
         padding: 3px 12px; border-radius: 20px; font-size: 10pt; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 12px;
        font-size: 8.6pt; page-break-inside: auto; }
th { background: #eef3f8; text-align: left; padding: 6px 7px; font-weight: 700;
     border: 1px solid #d0d7de; color: #0b3d6b; }
td { padding: 6px 7px; border: 1px solid #d0d7de; vertical-align: top; }
tr { page-break-inside: avoid; }
td.ok { color: #1a7f37; font-weight: 700; white-space: nowrap; }
code, .mono { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.3pt;
              background: #f6f8fa; padding: 1px 4px; border-radius: 3px; }
pre { background: #0d1117; color: #c9d1d9; padding: 10px 12px; border-radius: 6px;
      font-family: "SF Mono", Menlo, monospace; font-size: 8.2pt; line-height: 1.5;
      overflow-wrap: break-word; white-space: pre-wrap; page-break-inside: avoid; }
figure { margin: 10px 0 16px; page-break-inside: avoid; }
figure img { width: 100%; border: 1px solid #d0d7de; border-radius: 6px; }
figcaption { font-size: 8.6pt; color: #57606a; margin-top: 5px; }
.nota { background: #f6f8fa; border-left: 4px solid #0969da; padding: 9px 12px;
        margin: 10px 0; font-size: 9.4pt; page-break-inside: avoid; }
.q { background: #fff8e6; border-left: 4px solid #d4a72c; padding: 10px 12px;
     margin: 12px 0; page-break-inside: avoid; }
.q .preg { font-weight: 700; color: #7a5c00; margin-bottom: 6px; }
.q .most { font-size: 9pt; color: #57606a; margin-top: 7px;
           border-top: 1px dashed #d4a72c; padding-top: 6px; }
.salto { page-break-before: always; }
ul { margin: 4px 0 8px; padding-left: 20px; } li { margin-bottom: 4px; }
"""

filas = "".join(
    f"<tr><td class='mono'>{e(r['id'])}</td><td>{e(r['requisito'])}</td>"
    f"<td class='ok'>{e(r['estado'])}</td>"
    f"<td class='mono'>{e(r['fuente'])}</td><td>{e(r['detalle'])}</td></tr>"
    for r in D["resultados"])

commits = "\n".join(f"{s}  {m}" for s, m in D["commits_main"])
prs = "".join(
    f"<tr><td class='mono'>#{p['n']}</td><td>{e(p['titulo'])}</td>"
    f"<td class='mono'>{e(p['rama'])}</td><td class='mono'>{e(p['merged_at'])}</td>"
    f"<td>{'conflicto resuelto a mano' if p['n'] == NCONF else 'limpio'}</td></tr>"
    for p in D["prs"])

CAPTURAS = [
    ("img/01-push-rechazado.png",
     "Evidencia 1 — Push directo a <code>main</code> rechazado por el servidor.",
     "Ventana de terminal real en el instante del rechazo. El <code>commit</code> local se "
     "hizo; lo que falló es el <code>push</code>. La política vive en GitHub, no en la "
     "máquina, y con <code>enforce_admins</code> activo alcanza también al dueño del "
     "repositorio."),
    ("img/02-conflicto-en-pr.png",
     f"Evidencia 2 — El PR #{NCONF} no se puede mergear: conflicto.",
     "Chapa <em>Merge conflicts</em> y el cartel «This branch has conflicts that must be "
     "resolved», con <code>README.md</code> como archivo en conflicto y el botón de merge "
     "deshabilitado. Estado irrepetible: desaparece al resolver."),
    ("img/03-marcadores-conflicto.png",
     "Evidencia 3 — Los marcadores del conflicto.",
     "Editor de conflictos de GitHub antes de tocar nada. Arriba la versión de la rama "
     "actual, abajo la que ya estaba en <code>main</code>. El resto del archivo aparece sin "
     "marcar: Git fusionó solo todo lo que no chocaba."),
    ("img/04-release-publicada.png",
     "Evidencia 4 — Release <code>v1.0.0</code> publicada.",
     "Release sobre el tag <code>v1.0.0</code>, apuntando al commit de <code>main</code> con "
     "el conflicto ya resuelto, con notas que explican qué incluye la versión y por qué el "
     "número es <code>1.0.0</code>."),
]
figuras = "".join(
    f"<figure><img src='{img64(rel)}'><figcaption><strong>{cap}</strong><br>{txt}"
    f"</figcaption></figure>" for rel, cap, txt in CAPTURAS)

DEFENSA = [
    ("¿Para qué sirve proteger <code>main</code> si en el equipo «se tienen confianza»? "
     "¿Qué pasó cuando intentaste pushear directo?",
     "La confianza no es el problema: el problema es el error involuntario, y que un acuerdo "
     "que sólo vive en la cabeza de la gente no se puede auditar ni sobrevive a una "
     "incorporación nueva. La protección convierte el acuerdo del equipo en una regla que la "
     "plataforma hace cumplir — <em>policy as configuration</em>, el mismo patrón que un "
     "pipeline aplica a los tests.<br><br>"
     "Cuando intenté pushear directo, el <code>commit</code> local funcionó y el "
     "<code>push</code> fue rechazado con <code>GH006: Protected branch update failed</code> y "
     "<code>! [remote rejected] main -&gt; main (protected branch hook declined)</code>. Dos "
     "cosas para señalar: el rechazo ocurre <strong>en el servidor</strong> —mi commit local "
     "quedó hecho y hubo que descartarlo con <code>git reset --hard HEAD~1</code>—, y me "
     "rechazó <strong>a mí</strong>, que soy el dueño del repositorio, porque la regla está "
     "con <code>enforce_admins</code>. Una protección que el admin puede saltear es de adorno.",
     "Evidencia 1 · Settings → Branches · "
     "<code>gh api repos/.../branches/main/protection</code>"),

    ("¿Qué es una rama <em>realmente</em> para Git? ¿Y por qué el merge que hiciste en GitHub "
     "no aparecía en tu máquina hasta que hiciste <code>pull</code>?",
     "Una rama es <strong>un puntero móvil a un commit</strong>: un archivo de 41 bytes con un "
     "hash adentro. No es una copia de los archivos ni una carpeta. Por eso crear una rama es "
     "instantáneo y gratis, y por eso el flujo moderno crea ramas sin miedo. Al commitear, el "
     "puntero de la rama actual avanza; <code>HEAD</code> dice en cuál estoy parado.<br><br>"
     "El merge no apareció solo porque <strong>mi clon y GitHub son dos repositorios completos "
     "e independientes</strong>. Cuando aprieto «Merge» en la web, el que avanza es el puntero "
     "<code>main</code> <em>del servidor</em>. Mi <code>main</code> local sigue apuntando al "
     "commit viejo hasta que traigo las novedades: <code>fetch</code> las baja sin tocar mi "
     "trabajo, <code>pull</code> es <code>fetch</code> + <code>merge</code>. Olvidarse este "
     "paso es la causa número uno del próximo conflicto tonto — y es, de hecho, exactamente lo "
     "que se hace a propósito en el ejercicio del conflicto.",
     "<code>git log --oneline --graph --all</code> antes y después del <code>pull</code>"),

    ("¿Qué pasa cuando dos personas modifican la misma línea? Mostrame tu conflicto y "
     "explicame por qué Git no pudo resolverlo solo.",
     "Git fusiona con un <strong>merge de tres vías</strong>: compara las dos puntas contra el "
     "<strong>ancestro común</strong>. Si un solo lado cambió una región, la aplica sin "
     "preguntar; si la cambiaron los dos y distinto, se detiene. No es una limitación del "
     "algoritmo: la pregunta que queda —<em>¿cuál de los dos títulos es el correcto?</em>— no "
     "tiene respuesta técnica. Es contenido, y el contenido lo decide una persona.<br><br>"
     f"En mi repositorio: <code>feature/titulo-a</code> y <code>feature/titulo-b</code> "
     f"salieron las dos del commit <code>{BASE}</code> —el <code>compare</code> de la API lo "
     "confirma— y cambiaron la misma primera línea del <code>README.md</code>. Mergeé A, y B "
     "quedó en conflicto. Lo resolví <strong>a mano</strong>: dejé la versión B, borré las "
     "tres líneas de marcadores y verifiqué con <code>grep</code> que no quedara ninguno antes "
     f"de commitear (<code>{RESOL}</code>). No usé «aceptar la mía» porque eso no resuelve el "
     "conflicto: decide de antemano que el otro lado no importa.<br><br>"
     "Detalle que vale la pena mostrar: el resto del README —la sección Instalación— "
     "<strong>no</strong> tiene marcadores. El conflicto no fue el archivo: fue esa línea.",
     f"Evidencias 2 y 3 · PR #{NCONF}, pestaña <em>Commits</em> · "
     "<code>gh api repos/.../compare/&lt;p1&gt;...&lt;p2&gt;</code>"),

    ("El code review es la práctica central de un equipo y en este TP trabajaste solo: ¿qué "
     "buscarías vos en el Pull Request de un compañero, y qué NO discutirías nunca?",
     "<strong>Buscaría:</strong> que el cambio haga lo que dice el título (que el diff no "
     "traiga cosas de contrabando); que se entienda sin que el autor esté al lado, porque el "
     "que lo va a mantener puede ser otro; que tenga tests si toca comportamiento; que no "
     "introduzca riesgos de seguridad o performance; y que sea coherente con el diseño que ya "
     "existe en vez de inventar una forma nueva de hacer lo mismo.<br><br>"
     "<strong>No discutiría nunca:</strong> estilo y formato — comillas, indentación, dónde va "
     "la llave. Eso se automatiza con un linter y un formateador. Discutirlo entre humanos "
     "gasta el capital del review en lo único que una máquina hace mejor, y encima genera "
     "roce.<br><br>El review además no es sólo cazar bugs: reparte conocimiento y convierte el "
     "código en propiedad del equipo. Y la regla práctica que más importa: <strong>PRs "
     "chicos</strong>. Uno de 100 líneas recibe un review de verdad; uno de 3.000 recibe un "
     "«LGTM» sin leer.<br><br>Un ejemplo concreto de este repositorio: revisando el diff del "
     "PR #1 encontré que el README original no terminaba en salto de línea, así que el "
     "encabezado nuevo había quedado pegado al título. Nada lo marcaba como roto; sólo se ve "
     "leyendo el diff. Se corrigió con un segundo commit en la misma rama, antes de mergear.",
     "Los PRs del repositorio con sus descripciones · el segundo commit del PR #1"),

    ("¿Qué significa el número de versión que le pusiste al tag?",
     "<code>v1.0.0</code> es <strong>SemVer</strong>: <code>MAJOR.MINOR.PATCH</code>. MAJOR "
     "sube cuando rompo compatibilidad («si actualizás, algo tuyo puede dejar de andar»); "
     "MINOR cuando agrego funcionalidad que no rompe nada; PATCH cuando corrijo un bug sin "
     "cambiar el comportamiento esperado.<br><br>Lo estable que este <code>1.0.0</code> marca "
     "no es una funcionalidad: es <strong>el contrato de trabajo</strong> —todo entra por Pull "
     "Request, nada se pushea directo a <code>main</code>—, que a esa altura ya estaba "
     "configurado y verificado.<br><br>El número no es decorativo: es <strong>información para "
     "el que consume</strong> el software. Y la diferencia entre tag y release: el "
     "<strong>tag</strong> es una etiqueta inmutable sobre un commit («acá estaba el código de "
     "la v1.0.0»); la <strong>release</strong> le agrega la comunicación — qué cambió, escrito "
     f"para humanos. Mi tag es <em>anotado</em> (lleva autor, fecha y mensaje propios) y apunta "
     f"al commit <code>{TAGC}</code>, el <code>main</code> con el conflicto ya resuelto.",
     "La página de la release · <code>git show v1.0.0</code> · "
     "<code>gh release view v1.0.0</code>"),
]
defensa = "".join(
    f"<div class='q'><div class='preg'>{i}. {p}</div><div>{r}</div>"
    f"<div class='most'><strong>Qué mostrar en pantalla:</strong> {m}</div></div>"
    for i, (p, r, m) in enumerate(DEFENSA, 1))

DOC = f"""<!doctype html><meta charset="utf-8"><title>Informe de completitud — TP01</title>
<style>{CSS}</style>

<div class="portada">
  <div class="sub">Ingeniería de Software 3 · UCC · 2026 — Trabajo Práctico 01</div>
  <h1>Git colaborativo — Informe de completitud</h1>
  <div class="sub">Repositorio:
    <strong>{e(D['url'])}</strong> · Alumno: arielsch74 · {FECHA}</div>
  <div style="margin-top:10px"><span class="badge">
    {D['cumple']} / {D['total']} requisitos verificados contra el estado real del repositorio
  </span></div>
</div>

<h2>1. Qué es este documento y cómo se produjo</h2>
<p>Este informe cruza <strong>cada requisito del enunciado del TP01</strong> contra
<strong>lo que el repositorio efectivamente tiene</strong>. La distinción no es retórica:
cada fila de la tabla de la sección 2 sale de una consulta a la API de GitHub o a Git
ejecutada en el momento de generar este PDF, no de lo que creemos haber hecho. Si un
requisito no estuviera cumplido, la fila lo diría.</p>
<p>El chequeo está scripteado y es reproducible: el script vive en
<code>tools/verificar.py</code>, dentro del propio repositorio, y cualquiera con acceso al
repositorio público puede volver a correrlo —las consultas están citadas una por una en la
columna <em>Fuente</em>— y obtener las mismas respuestas. La única afirmación de este
documento que no se puede verificar contra la API es su propia presencia en el repositorio,
porque se incorpora por Pull Request después de haber sido generado.</p>

<div class="nota"><strong>Por qué se verifica por API y no de memoria.</strong>
La ejecución de este TP fue asistida por IA (declarado en detalle en
<code>decisiones.md</code>). Un agente puede reportar con total seguridad que hizo algo que
no hizo — y ése es exactamente el riesgo que este informe está diseñado para cerrar: la
fuente de verdad es el servidor de GitHub, no el relato de quien ejecutó. Durante este
trabajo el riesgo se materializó dos veces, con capturas que el proceso dio por buenas y
estaban arruinadas; se detectaron abriendo los archivos, no preguntando.</div>

<h2>2. Requisito por requisito</h2>
<table>
  <tr><th style="width:34px">#</th><th style="width:200px">Requisito del enunciado</th>
      <th style="width:64px">Estado</th><th style="width:150px">Fuente (consulta real)</th>
      <th>Qué devolvió</th></tr>
  {filas}
</table>

<div class="salto"></div>
<h2>3. El estado real del repositorio</h2>

<h3>3.1 Historial de <code>main</code></h3>
<pre>{e(commits)}</pre>
<p>Los commits que terminan en <code>(#n)</code> son merges de Pull Request con estrategia
<em>squash</em>: un commit por PR. Los dos que no —el commit inicial y el del
<code>.gitignore</code>— son <strong>anteriores a la protección</strong>, porque la guía crea
el <code>.gitignore</code> en §4.3 y protege <code>main</code> en §4.4. Desde que la
protección existe, no hay ningún commit en <code>main</code> que no haya entrado por un PR.</p>

<h3>3.2 Pull Requests mergeados</h3>
<table>
  <tr><th style="width:44px">PR</th><th>Título</th><th style="width:170px">Rama</th>
      <th style="width:130px">Mergeado (UTC)</th><th style="width:120px">Integración</th></tr>
  {prs}
</table>
<p>Ninguna rama de feature quedó viva: se borraron al mergear, y hoy el repositorio tiene
únicamente <code>main</code>. Las ramas de feature son descartables, no mascotas.</p>
<p><em>Nota sobre el conteo:</em> este informe se generó con {D['prs_mergeados']} PRs
mergeados. El siguiente —el que incorpora este mismo PDF al repositorio— no puede figurar
acá, por la misma razón por la que un informe no puede verificar su propia llegada: se
genera antes de existir en <code>main</code>.</p>

<h3>3.3 Protección de <code>main</code></h3>
<pre>required_pull_request_reviews     = activo
{e(crudo('2.a'))}
enforce_admins.enabled            = True
{e(crudo('2.b'))}</pre>
<p><code>enforce_admins</code> activo es el equivalente de <em>Do not allow bypassing the
above settings</em>: la regla alcanza al dueño del repositorio. Las aprobaciones obligatorias
están en <strong>cero</strong> a propósito: el TP es individual y GitHub no permite aprobar
el propio PR (la API responde <code>422 Can not approve your own pull request</code>), así
que exigir una aprobación dejaría todos los PRs imposibles de mergear. En un equipo real ese
número va en 1 o más.</p>

<h3>3.4 El conflicto, verificado</h3>
<pre>{e(crudo('3.b'))}

{e(crudo('3.b.2'))}</pre>
<p>El commit <code>{RESOL}</code> tiene <strong>dos padres</strong>: es el merge que resolvió
el conflicto, y es la prueba estructural —no anecdótica— de que ese PR pasó por una
resolución. El ancestro común de sus dos padres es <code>{BASE}</code>: el <code>main</code>
del que salieron las dos ramas. Ese dato es el que descarta el error clásico del ejercicio
—que la rama B nazca de la A—, en cuyo caso no habría habido conflicto alguno.</p>

<h3>3.5 Tag y release</h3>
<pre>tag        v1.0.0 (anotado)  -&gt;  commit {e(TAGC)}   [ancestro de main: sí]
mensaje    {e(crudo('4.a').split('«')[-1].rstrip('»'))}
release    {e(detalle('4.b'))}
url        {e(D['release_url'])}</pre>
<p>El tag es <strong>anotado</strong> (no <em>lightweight</em>): lleva autor, fecha y mensaje
propios, que es lo que corresponde para marcar una entrega. Apunta a <code>{e(TAGC)}</code>,
el commit de <code>main</code> resultante del merge del PR #{NCONF} — o sea, el estado
<em>con el conflicto ya resuelto</em>.</p>

<h2>4. Evidencias</h2>
<p>Las cuatro capturas marcadas con 📸 en la guía, tomadas en el instante en que ocurrió cada
hecho. Tres de ellas son irrepetibles: el aviso de conflicto desaparece del PR al resolverlo,
y los marcadores desaparecen del archivo al borrarlos —que es, literalmente, lo que significa
resolver el conflicto.</p>
{figuras}

<div class="salto"></div>
<h2>5. Preparación para la defensa oral</h2>
<p>El enunciado adelanta las preguntas y advierte que el TP se aprueba <strong>sólo si se
puede explicar qué se hizo, por qué pasa lo que pasa y cómo se resolvió</strong>. Abajo, cada
pregunta respondida contra los datos concretos de <em>este</em> repositorio, con lo que
conviene tener abierto en pantalla al responderla.</p>
{defensa}

<h3>Recorrido sugerido para la defensa en vivo</h3>
<ul>
<li><strong>Empezar por Settings → Branches</strong>: mostrar la regla, y en particular las
cero aprobaciones y el <em>Do not allow bypassing</em>. Explicar por qué cada tilde está donde
está antes de mostrar ninguna consecuencia.</li>
<li><strong>Después la evidencia 1</strong>: el rechazo. Es la consecuencia de lo anterior, y
lo demuestra sobre uno mismo.</li>
<li><strong>Recorrer el PR #{NCONF} entero</strong>: la descripción, los commits (ahí está el
de merge con dos padres) y el diff. Es el lugar donde vive la historia del conflicto, porque
el squash la aplana en <code>main</code>.</li>
<li><strong>Cerrar en la release</strong>: qué significa <code>1.0.0</code> y por qué un tag
sin notas no es lo mismo que una release.</li>
<li><strong>Si preguntan por la IA</strong>: <code>decisiones.md</code> §3 tiene la
declaración literal —qué se delegó, qué no— y la tabla de cómo se verificó cada resultado
contra el repositorio.</li>
</ul>

<div class="nota"><strong>Punto débil conocido, dicho de frente.</strong> El tag
<code>v1.0.0</code> se creó siguiendo el orden de la guía (§4.7 antes de §4.8), así que apunta
a un commit que todavía no incluye <code>evidencias.md</code> ni <code>decisiones.md</code>.
Es deliberado y está explicado en las notas de la release: <code>v1.0.0</code> marca el punto
donde quedó operativo el <strong>flujo de trabajo</strong>, y los dos archivos son
documentación <em>sobre</em> ese flujo. Si se considerara que forman parte del artefacto
entregado, lo correcto sería un <code>v1.1.0</code> —funcionalidad nueva compatible— y no
mover el tag existente, porque un tag es inmutable por definición.</div>
"""

(AQUI / "informe.html").write_text(DOC)

from playwright.sync_api import sync_playwright                       # noqa: E402

with sync_playwright() as pw:
    nav = pw.chromium.launch()
    pg = nav.new_page()
    pg.goto((AQUI / "informe.html").as_uri(), wait_until="load")
    pg.wait_for_timeout(1500)
    pg.pdf(path=str(SALIDA_PDF), format="A4", print_background=True,
           display_header_footer=True,
           header_template="<div></div>",
           footer_template="<div style='font-size:7.5pt;color:#8b949e;width:100%;"
                           "padding:0 14mm;font-family:Helvetica'>"
                           "TP01 — Git colaborativo · arielsch74/tp01live"
                           "<span style='float:right'>"
                           "<span class='pageNumber'></span> / "
                           "<span class='totalPages'></span></span></div>")
    nav.close()

print(f"OK -> {SALIDA_PDF}  ({SALIDA_PDF.stat().st_size // 1024} KB)")
