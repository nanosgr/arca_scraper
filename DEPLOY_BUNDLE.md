# Despliegue sin GitHub (git bundle)

Guía para actualizar el código en el servidor de producción cuando el servidor
**no tiene acceso a GitHub**. Por ejemplo, si `git pull` falla con:

```
fatal: unable to access 'https://github.com/nanosgr/arca_scraper.git/': Could not resolve host: github.com
```

La idea es sacar los commits de la máquina de desarrollo en un archivo
(el *bundle*), copiarlo por `scp` y aplicarlo en el servidor con `git fetch`,
como si fuera un remoto más.

---

## ¿Qué es un git bundle?

Un **bundle** es un único archivo que contiene commits, árboles y blobs de un
repositorio git, junto con las referencias (ramas o tags) que apuntan a ellos. Es
el mismo paquete de datos que git manda por la red en un `push` o un `fetch`, pero
guardado en disco.

Git trata ese archivo **como si fuera un remoto de solo lectura**:

```bash
git bundle create repo.bundle master   # empaqueta la rama master
git fetch repo.bundle master           # la trae, como si fuera "origin"
git clone repo.bundle carpeta/         # incluso se puede clonar
```

Características:

- **Conserva la historia**: el servidor recibe los mismos commits, con los mismos
  hashes, que existen en GitHub. Cuando vuelva a tener acceso a GitHub, `git pull`
  funciona normalmente sin conflictos.
- **Solo lleva lo commiteado**: los cambios sin commitear y los archivos ignorados
  (`.env`, `data/`, `logs/`) no viajan. Las credenciales del servidor quedan intactas.
- **Se puede verificar**: `git bundle verify` comprueba que el archivo esté completo
  y que el repo destino tenga los commits previos que necesita.
- **Puede ser completo o incremental**: `git bundle create f master` incluye toda
  la historia. `git bundle create f v1..master` incluye solo los commits nuevos, y
  en ese caso el destino ya debe tener `v1`. Como este repo es chico, el script usa
  el bundle completo, que siempre funciona.

Comparación con otras alternativas:

| Opción                      | Historia git | Riesgo                                        |
|-----------------------------|--------------|-----------------------------------------------|
| `git bundle`                | Sí           | Bajo: fast-forward o falla sin tocar nada     |
| `scp`/`rsync` de archivos   | No           | Deja el repo del servidor "sucio" y divergente |
| `git format-patch` + `am`   | Sí           | Hashes distintos a los de GitHub              |

---

## Despliegue automático (script)

Desde la **máquina de desarrollo**, en la raíz del repo, con los cambios ya
commiteados en `master`:

```bash
./scripts/deploy_bundle.sh                     # usa sebastianr@172.16.140.98
./scripts/deploy_bundle.sh usuario@servidor    # otro destino
ARCA_SERVER=usuario@servidor ./scripts/deploy_bundle.sh
```

El script:

1. Aborta si hay cambios sin commitear, porque no se desplegarían.
2. Crea el bundle de `master`.
3. Lo copia a `/tmp/` del servidor con `scp`.
4. Se conecta por `ssh` (pide la contraseña de `sudo`) y, **como usuario `arca`**:
   - verifica el bundle (`git bundle verify`),
   - trae `master` (`git fetch <bundle> master`),
   - aplica con `git merge --ff-only FETCH_HEAD`,
   - si cambió `requirements.txt`, corre `pip install -r requirements.txt`,
   - borra el bundle.

**No ejecuta el scraper.** La próxima corrida la hace el timer. Para probar en el momento:

```bash
sudo systemctl start arca-scraper.service
sudo journalctl -u arca-scraper.service -f
```

---

## Despliegue manual (paso a paso)

Si preferís hacerlo a mano o el script falla en algún paso.

### En la máquina de desarrollo

```bash
git status                                  # sin cambios pendientes
git bundle create /tmp/arca_scraper.bundle master
scp /tmp/arca_scraper.bundle sebastianr@172.16.140.98:/tmp/
```

### En el servidor (vía ssh)

```bash
chmod 644 /tmp/arca_scraper.bundle
cd /opt/arca_scraper

# Siempre como usuario arca: el repo es suyo
sudo -u arca git bundle verify /tmp/arca_scraper.bundle
sudo -u arca git fetch /tmp/arca_scraper.bundle master
sudo -u arca git log --oneline HEAD..FETCH_HEAD   # qué commits entran
sudo -u arca git merge --ff-only FETCH_HEAD

# Solo si cambió requirements.txt
sudo -u arca /opt/arca_scraper/venv/bin/pip install -r requirements.txt

rm /tmp/arca_scraper.bundle
```

No hace falta reiniciar el timer: en cada corrida el servicio lanza un proceso
Python nuevo, que ya usa el código actualizado.

---

## Problemas frecuentes

**`fatal: Not possible to fast-forward, aborting.`**
El servidor tiene commits locales que no están en tu `master`. Revisá con
`sudo -u arca git log --oneline FETCH_HEAD..HEAD`. Traé esos commits a tu máquina
o descartalos antes de reintentar.

**`error: Your local changes to the following files would be overwritten by merge`**
Hay archivos versionados modificados directamente en el servidor. Suele pasar con
`config/empresas.json`. Revisalos con `sudo -u arca git diff`. Si hay que conservarlos,
guardalos (`sudo -u arca git stash`), hacé el merge y recuperalos
(`sudo -u arca git stash pop`).

**`fatal: detected dubious ownership in repository`**
Ejecutaste git con tu usuario en lugar de `arca`. Usá siempre `sudo -u arca git ...`.

**`sudo: a terminal is required to read the password`**
Faltó `-t` en `ssh`. El script ya lo incluye; si lo hacés a mano, usá `ssh -t`.

---

## Volver a usar GitHub

El bundle no modifica el remoto `origin`. Cuando el servidor vuelva a resolver
`github.com`, alcanza con `sudo -u arca git pull`: los commits son los mismos,
así que no hay conflictos.

Para diagnosticar el acceso a GitHub desde el servidor:

```bash
getent hosts github.com        # ¿resuelve el DNS?
resolvectl status              # servidores DNS configurados
curl -sI https://github.com    # ¿hay salida HTTPS?
```
