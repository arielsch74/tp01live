# Evidencias — TP1

Las cuatro capturas marcadas 📸 en la guía, cada una tomada **en el momento en que ocurrió el
hecho**. Tres de las cuatro son irrepetibles: el aviso de conflicto y los marcadores dejan de
existir en cuanto el conflicto se resuelve, y la release solo se publica una vez.

---

## 1. Push directo a `main` rechazado

![push directo rechazado](img/01-push-rechazado.png)

Ventana real de terminal, con `main` ya protegida. Se hizo un commit local (`142e15b`) y se intentó
`git push`. El objeto viajó —se ven el `Enumerating objects` y el `Writing objects`— y el rechazo
llegó **del lado del servidor**:

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
 ! [remote rejected] main -> main (protected branch hook declined)
```

Lo importante no es que rechazó: es **a quién** rechazó. El que empujó es el dueño del repositorio.
La protección se creó con *Do not allow bypassing the above settings* (`enforce_admins: true`), así
que la regla lo alcanza igual. Una protección que el administrador puede saltear no protege nada:
protege mientras nadie tenga apuro.

Después de la captura el commit local se descartó con `git reset --hard HEAD~1`; nunca existió en el
remoto.

---

## 2. El PR de la rama B no se puede mergear: conflicto

![aviso de conflicto en el PR](img/02-conflicto-en-pr.png)

Pull Request [#3](https://github.com/arielsch74/tp01live/pull/3) (`feature/titulo-b` → `main`),
inmediatamente después de mergear el PR [#2](https://github.com/arielsch74/tp01live/pull/2)
(`feature/titulo-a`). Se ven el badge rojo **Merge conflicts** arriba a la derecha, el cartel *This
branch has conflicts that must be resolved* con `README.md` como único archivo afectado, y el botón
**Squash and merge** deshabilitado.

El detalle que vale la pena mirar: **hasta un minuto antes, este mismo PR figuraba como mergeable.**
Las dos ramas habían nacido del mismo commit de `main` (`301f094`) y reescribieron la misma línea,
pero mientras ninguna estaba integrada no había nada que chocara. El conflicto no nace cuando se
escribe el cambio: nace cuando se lo intenta integrar contra un `main` que ya se movió.

---

## 3. Los marcadores del conflicto

![marcadores del conflicto](img/03-marcadores-conflicto.png)

Editor de conflictos de GitHub (`/pull/3/conflicts`), antes de tocar nada. Ahí están las tres
fronteras que deja Git cuando no puede decidir:

```
<<<<<<< feature/titulo-b   (Current change)
# Proyecto IngSoft3 - versión B
=======
# Proyecto IngSoft3 - versión A
>>>>>>> main               (Incoming change)
```

Arriba de `=======` está la versión de la rama actual; abajo, la que ya está en `main`. Arriba a la
derecha se lee **1 conflict** y el botón **Mark as resolved** está deshabilitado: GitHub no deja
marcar el archivo como resuelto mientras quede un marcador.

Y lo que **no** está en conflicto es igual de informativo: las líneas 6 a 13 —la sección
`## Instalación` que venía del PR #1— aparecen limpias. Ninguna de las dos ramas las tocó, así que
Git las fusionó solo, sin preguntar. El conflicto es quirúrgico: cae sobre la línea disputada, no
sobre el archivo entero.

Esta captura es la más frágil de las cuatro, porque el paso inmediatamente siguiente es borrar esos
marcadores.

---

## 4. La release `v1.0.0` publicada

![release v1.0.0 publicada](img/04-release-publicada.png)

Release `v1.0.0` con el badge **Latest**, apuntando al tag `v1.0.0` y al commit `d1baff1` — la punta
de `main` después de mergear los tres PRs. Las notas dicen qué incluye la versión escritas para que
las lea una persona, e incluyen la justificación de por qué el número es `1.0.0` y no `0.1.0`.

El tag se creó **anotado** desde la máquina (`git tag -a v1.0.0 -m "..."` + `git push origin
v1.0.0`) y la release se publicó sobre ese tag ya existente. Un tag anotado es un objeto de Git con
autor, fecha y mensaje propios; un tag liviano sería solo un puntero sin metadatos. Para marcar una
entrega, el anotado es el que corresponde.
