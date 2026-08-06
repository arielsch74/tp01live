# Decisiones — TP1

---

## 1. Por qué Git no pudo resolver el conflicto solo

### Qué pasó exactamente

Las dos ramas nacieron del **mismo** commit de `main`:

```
                    ┌── 04b72a6  feature/titulo-a   "# Proyecto IngSoft3 - versión A"
301f094 (main) ─────┤
                    └── 41a496a  feature/titulo-b   "# Proyecto IngSoft3 - versión B"
```

Las dos reescribieron la **línea 1** del `README.md`. Cuando `feature/titulo-a` se mergeó, `main`
pasó a tener `versión A`. Al intentar integrar `feature/titulo-b`, Git hizo lo que hace siempre: un
merge de 3 vías, comparando las dos puntas contra el **ancestro común** (`301f094`, donde la línea
decía `# tp01live`).

El resultado de esa comparación fue:

| | Línea 1 del README |
|---|---|
| Ancestro común (`301f094`) | `# tp01live` |
| `main` | `# Proyecto IngSoft3 - versión A` |
| `feature/titulo-b` | `# Proyecto IngSoft3 - versión B` |

**Las dos ramas cambiaron la misma línea respecto del ancestro, y la cambiaron distinto.** Ahí Git
se detiene. No es una limitación técnica que se pueda mejorar con un algoritmo más listo: Git
compara texto, no entiende de qué habla el texto. No existe ninguna regla mecánica que le permita
decidir si el título correcto del proyecto es "versión A" o "versión B", porque esa respuesta no
está en los archivos — está en la cabeza del equipo.

Por eso Git hace lo único honesto que puede hacer: **escribe las dos versiones en el archivo,
marca dónde empieza y termina cada una, y le devuelve la decisión a una persona.** El conflicto no
es un error de Git; es Git negándose a inventar una respuesta que no tiene.

La prueba de que el criterio es "misma línea" y no "mismo archivo" está en la captura 3: la sección
`## Instalación`, en el mismo archivo, **se fusionó sola**. Ninguna de las dos ramas la había
tocado, así que no había nada que decidir.

### Qué habría tenido que pasar para que nunca apareciera

Tres caminos, de más realista a más ilusorio:

1. **Integrar antes.** Si `feature/titulo-b` se hubiera creado *después* de mergear
   `feature/titulo-a` —o si hubiera hecho `git pull` de `main` antes de tocar el README—, habría
   partido de un `main` que ya tenía `versión A`. Su cambio habría sido una edición secuencial, no
   paralela: sin conflicto. Esta es la razón concreta por la que la investigación DORA insiste con
   integrar a *trunk* al menos una vez por día. **Ramas cortas no evitan los conflictos: los hacen
   chicos y triviales.** El *merge hell* es lo que pasa cuando una rama vivió tres semanas.

2. **Que las dos ramas no tocaran la misma línea.** Si el trabajo estuviera repartido de manera que
   cada rama toca una zona distinta del archivo, Git fusiona sin preguntar. Es un argumento a favor
   de dividir el trabajo por archivo o por sección, no de que dos personas editen el mismo párrafo
   en paralelo.

3. **Que alguien decidiera antes de escribir.** El conflicto de Git es el síntoma; la causa es que
   dos personas tomaron decisiones incompatibles sobre lo mismo sin hablar. Ninguna herramienta
   arregla eso.

Vale decir lo obvio: en este TP el conflicto **se fabricó a propósito**, siguiendo la §4.6. El
objetivo no era evitarlo sino provocarlo en un entorno controlado, que es mucho mejor que
encontrárselo por primera vez en un repositorio de trabajo.

---

## 2. Qué problemas encontré y cómo los solucioné

### a) El README no terminaba en salto de línea, y la sección nueva quedó pegada al título

Al agregar la sección de instalación al final del `README.md` con `>>`, el diff del PR #1 salió así:

```diff
-# tp01live
\ No newline at end of file
+# tp01live
+## Instalación
```

El archivo original —el que crea GitHub al inicializar el repo— **no tenía salto de línea final**,
así que la línea nueva se pegó al título en vez de quedar separada. En Markdown eso rompe el
encabezado.

Lo encontré **leyendo el diff antes de mergear**, que es exactamente para lo que existe el paso 4 de
la §4.5. Se arregló con un segundo commit en la misma rama (`docs: separa el encabezado de la
sección de instalación`) y recién ahí se mergeó. Es un error minúsculo, pero es la demostración
literal de para qué sirve mirar el diff: nada lo habría marcado como roto, el archivo compilaba
igual, y habría entrado a `main` con un encabezado mal formado. La marca `\ No newline at end of
file` del diff es la pista, y es fácil pasarla por alto.

### b) GitHub tarda unos segundos en darse cuenta de que hay conflicto

Inmediatamente después de mergear el PR #2, consulté el estado del PR #3 y la API devolvió
`mergeable=UNKNOWN, mergeStateStatus=UNKNOWN`. No era que no hubiera conflicto: GitHub calcula la
mergeabilidad **en background** y todavía no había terminado. Consultado de nuevo unos segundos
después devolvió `mergeable=CONFLICTING, mergeStateStatus=DIRTY`.

Importaba porque la captura del aviso de conflicto había que sacarla en ese momento exacto. Si la
hubiera sacado apenas mergeado el PR #2, habría fotografiado una pantalla que todavía no mostraba el
conflicto. La solución fue esperar y **verificar el estado antes de capturar**, no capturar y
suponer. La misma guía lo menciona al revés en §4.6 ("si GitHub no te deja mergear inmediatamente
después de resolver, esperá unos segundos").

### c) Casi destruyo una evidencia irrepetible al recortar la imagen

Las capturas salían con mucho espacio en blanco abajo, así que las recorté con `sips` (la
herramienta de imágenes de macOS). Resultado: `sips -c alto ancho` recorta **desde el centro**, no
desde arriba, y su opción `--cropOffset` no cambió ese comportamiento en ninguna de las dos
posiciones en que la probé. La captura del push rechazado perdió la barra de título y los dos
primeros comandos; la de los marcadores del conflicto perdió los marcadores — o sea, todo su
contenido.

Las dos se recuperaron, pero por motivos distintos, y esa diferencia es la lección:

- La del **push rechazado es repetible**: la protección sigue activa, así que alcanzó con volver a
  intentar el push y capturar de nuevo.
- La de los **marcadores no lo es**: el conflicto ya estaba por resolverse y esa pantalla no vuelve.
  Se salvó únicamente porque antes de tocar el archivo había hecho una copia de respaldo.

Corregido: el recorte se hizo con Pillow (`Image.crop`), que sí toma coordenadas explícitas, y el
criterio quedó en **respaldar antes de transformar** cualquier evidencia irrepetible. Fue el
tropiezo más útil del TP, porque no fue un problema de Git sino de la disciplina con la que se
tratan las evidencias — y las tres capturas frágiles de este trabajo no se pueden reconstruir
después.

### d) El push rechazado (que no es un problema, pero lo parece)

`git push` devolviendo `! [remote rejected] main -> main (protected branch hook declined)` es el
resultado **buscado**, no un error a arreglar: es la prueba de que la protección funciona. Lo anoto
porque la primera reacción natural frente a un `error:` en rojo es intentar dar vuelta la
configuración, y acá el rojo era el éxito. El commit local quedó descartado con
`git reset --hard HEAD~1`.

### e) Las aprobaciones obligatorias, que la guía avisa y conviene no olvidar

La protección se creó con `required_approving_review_count: 0` a propósito. GitHub **no permite que
el autor de un PR apruebe su propio PR** —no es configurable, la opción aparece deshabilitada y por
API devuelve `422 Can not approve your own pull request`—, así que en un TP individual pedir aunque
sea 1 aprobación deja los PRs imposibles de mergear, con un mensaje de error que no señala la causa
real. En un equipo de verdad ese número va en 1 o más; acá va en 0 y la revisión la hace igual una
persona: yo, leyendo el diff antes de apretar el botón.

---

## 3. Declaración de uso de IA

### Qué se delegó

**La ejecución completa de la guía**, delegada a un agente de IA (Claude, corriendo en Claude Code)
con acceso a la terminal de mi máquina, a `git`, a la CLI `gh` de GitHub y a un navegador
automatizado con mi sesión de GitHub ya iniciada. Concretamente hizo:

- Los comandos de Git y de la CLI de GitHub: `clone`, `add`, `commit`, `push`, `switch`, `merge`,
  `tag`; la creación de la protección de rama por API; la creación, revisión y merge (squash) de todos los
  Pull Requests; el borrado de las ramas; la creación del tag y la publicación de la release.
- La redacción de los textos: descripciones y títulos de los PRs, mensajes de commit, notas de la
  release, y estos dos archivos (`evidencias.md` y `decisiones.md`).
- La toma de las cuatro capturas: la del push rechazado en una ventana real de Terminal.app
  capturada con `screencapture`, y las tres de GitHub con Playwright reutilizando el estado de mi
  sesión, sin volver a pedirme login.
- El informe de completitud en PDF y el script que lo genera.

### Qué NO se delegó

- **La decisión de contenido del conflicto.** Que ganara la **versión B** fue una instrucción mía,
  dada antes de que el conflicto existiera. También fue instrucción mía **cómo** resolverlo: a mano,
  decidiendo el texto final y borrando los marcadores, y no con un botón de *Accept current change*
  ni con `git checkout --ours`. Ese era el punto del ejercicio y delegarlo lo habría vaciado.
- **La plataforma y las reglas del juego**: GitHub, repositorio público, `main` protegida sin
  bypass, squash merge, convención `feature/<descripción>`. Vienen dadas por la guía (§4.9) y por el
  enunciado; no fueron elección del agente.
- **La defensa oral.** Todo lo que está acá escrito tengo que poder explicarlo yo. Este archivo no
  reemplaza haber entendido el ejercicio: lo documenta.

### Cómo verifiqué cada resultado contra el estado real del repositorio

El criterio fue no darle por cierto al agente **ninguna** afirmación sobre el estado del repositorio.
Todo lo que se afirma acá y en `evidencias.md` está verificado contra la fuente real —la API de
GitHub y el repositorio local—, no contra el relato de lo que se hizo:

| Qué se afirma | Cómo se comprobó |
|---|---|
| `main` está protegida, sin bypass, con 0 aprobaciones | `GET /repos/arielsch74/tp01live/branches/main/protection` → `enforce_admins.enabled = true`, `required_approving_review_count = 0` |
| El push directo se rechaza de verdad | Se intentó realmente, con `main` ya protegida. La captura 1 es la salida de esa terminal, no una reconstrucción. El rechazo lo emite el servidor (`remote: error: GH006`) |
| Todos los cambios entraron por PR mergeado con squash | `GET /repos/.../pulls?state=closed` → cada PR con `merged_at` no nulo; cada uno deja **un solo** commit en `main` (`git log --oneline` muestra un commit por PR, y ningún commit en `main` sin PR salvo el inicial y el del `.gitignore`, anterior a la protección) |
| Las ramas A y B partieron del mismo commit | `git merge-base feature/titulo-a feature/titulo-b` → `301f094`, el mismo commit que era la punta de `main`. Si hubieran estado encadenadas no habría habido conflicto y el ejercicio no probaría nada |
| El PR #3 tuvo conflicto real | La API devolvió `mergeable=CONFLICTING` y `mergeStateStatus=DIRTY` **antes** de resolverlo, y `MERGEABLE / CLEAN` después. Las capturas 2 y 3 se sacaron en la ventana entre esos dos estados |
| El conflicto se resolvió a mano y ganó B | El commit de resolución (`1edc426`) está en el historial del PR #3, y la línea 1 del `README.md` en `main` dice `# Proyecto IngSoft3 - versión B`. Se verificó además que no quedara ningún marcador (`grep -nE '^(<{7}\|={7}\|>{7})' README.md` → sin resultados) |
| El tag y la release existen y apuntan a `main` | `git ls-remote --tags` y `GET /repos/.../releases/tags/v1.0.0` → el tag resuelve a `d1baff1`, que es la punta de `main` |
| Las capturas muestran lo que dicen mostrar | Las abrí y las miré una por una. Dos veces el recorte había arruinado la imagen (problema *c*) y en las dos el archivo se veía perfectamente válido "según el proceso": solo mirarlo lo mostró |

Esa última fila es la que resume el método. El agente puede reportar que un paso salió bien y
haber, sin mentir, producido un artefacto inservible. La verificación no consiste en preguntarle si
funcionó: consiste en ir a mirar el estado real, que en este TP es la API de GitHub, el historial
de Git y las imágenes abiertas de a una.

El informe de completitud (`informe-completitud-tp01.pdf`) automatiza esa verificación: cada
requisito del enunciado se contrasta contra una consulta concreta a la API o al repositorio local, y
el PDF deja registrada la respuesta cruda que devolvió cada consulta. El script que lo genera está
en `tools/verificar.py`, para que cualquiera pueda volver a correrlo y comprobar que el informe no
dice más de lo que el repositorio efectivamente tiene.
