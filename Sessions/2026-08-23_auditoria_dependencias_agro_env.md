# Sesión: Auditoría de dependencias de `agro_env` y reparación del demonio Docker

**Fecha:** 2026-08-23 (mañana)
**Agente:** opencode

## Tema tratado
El entorno conda **`agro_env`** se creó tiempo después de haber comenzado el desarrollo del
Agente-IA-Agro-Inteligente, por lo que se sospechaba que algunos requerimientos necesarios
para el correcto funcionamiento del agente habían quedado fuera del entorno. Se pidió
verificarlo y, de confirmarse, corregirlo.

## Estado inicial
- `requirements.txt` declaraba 20 paquetes; **todos** estaban instalados en `agro_env`
  (el problema no era una instalación incompleta del archivo).
- El análisis inverso —imports reales del código vs entorno— reveló **1 dependencia usada
  pero jamás declarada ni instalada**: el **Docker SDK para Python (`docker`)**, pieza del
  sandbox de ejecución segura.
- El demonio de Docker estaba **caído**: `docker.service` en estado *failed*, socket
  `/var/run/docker.sock` huérfano (connection refused).
- `agro_env` usa **Python 3.10.19**.

## Actividades realizadas

### 1. Comparación `requirements.txt` vs paquetes instalados
- Listado con `/home/cero/anaconda3/envs/agro_env/bin/pip list --format=freeze`.
- Los 20 paquetes declarados presentes (autopep8, beautifulsoup4, chromadb,
  duckduckgo-search, google-generativeai, psutil, pytest, PyAudio, python-dotenv, gTTS,
  pydub, pypdf, SpeechRecognition, PyYAML, requests, fastapi, uvicorn, python-multipart,
  huggingface-hub, Pillow).

### 2. Análisis de imports reales del código (65 archivos `.py`, ~370 imports)
- Barrido exhaustivo de `import X` / `from X import ...`, excluyendo stdlib, imports
  internos del proyecto y falsos positivos (imports Kotlin/Java embebidos en f-strings,
  `.py` vendidos dentro de `node_modules`).
- Detectados **22 paquetes de terceros**, de los cuales 21 estaban instalados.
- **Faltante:** `docker`, importado por:
  - `execution/build_sandbox.py:2` — import directo sin try/except (fallaría con
    `ModuleNotFoundError`).
  - `execution/run_sandbox.py:8` — import protegido, pero hace `sys.exit(1)` si falta.
- Dependencias de sistema verificadas: `ffmpeg` ✅ (requerido por pydub), `arecord` ✅;
  `SpeechRecognition` trae su propio binario flac, no hace falta a nivel sistema.

### 3. Corrección de la brecha detectada
- Añadido `docker` a `requirements.txt` (quedó entre `python-multipart` y
  `huggingface-hub`).
- Instalación en `agro_env`: `docker==7.2.0` (dependencias ya cubiertas: requests,
  urllib3, etc.).

### 4. Diagnóstico del demonio Docker caído
- `journalctl -u docker`: fallo repetido al arrancar con
  *"cannot create network ... (docker0): conflicts with network ... networks have same
  bridge name"* — base de datos local de redes obsoleta/corrupta (`local-kv.db`),
  issue conocido de Docker.
- Sin sudo sin contraseña desde el agente → el arreglo se entregó al usuario para que lo
  ejecutara con su contraseña.

### 5. Arreglo aplicado por el usuario (comandos proporcionados por el agente)
```bash
sudo systemctl stop docker.socket docker.service
sudo rm /var/lib/docker/network/files/local-kv.db
sudo systemctl start docker
docker ps
```

## Verificaciones
- Test de imports en `agro_env`: **22/22 OK**, faltantes: ninguno.
- `docker.from_env()` desde `agro_env`: **OK** — server v29.1.3, API 1.52.
- `docker ps` del usuario respondió correctamente (lista vacía, daemon vivo).
- Imagen **`agent-sandbox:latest` ya existe** → `execution/run_sandbox.py` listo para
  usarse sin reconstruir.

## Decisiones
- Corregir la causa raíz (requirements.txt incompleto) además del síntoma (paquete
  ausente): así cualquier recreación futura del entorno instala todo.
- Documentar advertencias sin actuar sobre ellas todavía (ver Pendientes).

## Advertencias registradas (no bloquean hoy)
1. **Python 3.10 EOL para google.api_core: octubre 2026** → conviene recrear `agro_env`
   con Python ≥ 3.11 antes de esa fecha.
2. **`google-generativeai` oficialmente deprecado** (sin parches) → migrar eventualmente
   a `google-genai`; afecta `execution/chat_with_llm.py`, `generate_chat_title.py`,
   `execution/test_gemini_connection.py`.

## Documentación generada
- Nueva sección **«8. Auditoría de dependencias y advertencias»** en
  `docs/entorno_conda.md`, con la tabla del faltante corregido, las advertencias vigentes,
  el arreglo del demonio Docker y los comandos para re-auditar en el futuro.

## Pendientes (mañana)
- [ ] Recrear `agro_env` con Python ≥ 3.11 antes de oct-2026 (EOL soporte google.api_core).
- [ ] Evaluar migración de `google-generativeai` → `google-genai` (3 scripts afectados).
- [ ] Opcional: smoke test end-to-end del sandbox (`execution/run_sandbox.py`) con código trivial ahora que el demonio está arriba.

---

# Sesión (tarde): Revisión del HF Space y rotación completa de tokens HuggingFace

**Fecha:** 2026-08-23 (tarde)
**Agente:** opencode

## Tema tratado
Revisión de la página web del agente en HuggingFace
(`https://huggingface.co/spaces/cero2k6/agente-agro-inteligent`, SDK docker) que derivó en
una auditoría de seguridad: el token HF estaba embebido en la URL del remoto git y resultó
ser un token de amplio uso compartido por varios proyectos de la máquina.

## Hallazgos de la revisión del Space

| Aspecto | Resultado |
|---|---|
| Estado | RUNNING, cpu-basic, HTTP 200 en ~0.7s |
| Último despliegue | commit `04039da` (2026-04-19) — 3 commits detrás del HEAD local |
| Contenido de esos 3 commits | Solo artefactos Hardhat/Ethereum (~11k líneas: AgroIAToken, package-lock) + LaTeX — **sin impacto en la web**, no urgente redesplegar |
| Dockerfile del Space | Correcto: python:3.10-slim + portaudio19-dev + ffmpeg, uvicorn puerto 7860 |

## Vulnerabilidad encontrada y radio de impacto

El remoto `hf` tenía el token (`despliegue-agente-ia`, `hf_...wAiI`) incrustado en la URL
de `.git/config`. Al rastrearlo apareció en **4 lugares**:
1. `.git/config` (remoto hf) — limpiado con `git remote set-url`.
2. `CYBERSEGURIDAD/.env:37` (`HF_TOKEN=`).
3. `ELECTRONICA/.env:40` (`HF_TOKEN=` — usado por `execution/publicar_hf.py`: crea repos
   de datasets y sube carpetas → requiere escritura).
4. `~/.cache/huggingface/token` — login global de `huggingface_hub` para TODOS los
   proyectos Python de la máquina.

Además se confirmó vía API que HF **no permite crear ni revocar tokens programáticamente**
(endpoints internos 404; `huggingface_hub` solo expone `auth_check`): todo el ciclo se hizo
por la interfaz web guiada + automatización local de la parte de archivos.

## Arquitectura de reemplazo: 2 tokens por función

| Token | Alcance fine-grained | Consumidores |
|---|---|---|
| `despliegue-agro-space-v2` | SOLO el Space `agente-agro-inteligente`: repo.access.read, repo.content.read, repo.write | `~/.git-credentials` (push del despliegue) |
| `hf-inferencia-datasets` | User cero2k6: repo.content.read, repo.access.read, repo.write, inference.serverless.write | `HF_TOKEN` en CYBERSEGURIDAD/.env, ELECTRONICA/.env y `~/.cache/huggingface/token` |

## Actividades realizadas
1. Limpieza del remoto (`git remote set-url hf …` sin credencial) y configuración de
   `credential.helper store`.
2. Creación guiada (UI web) de ambos tokens fine-grained; el usuario los guardó en el
   `.env` raíz como `HuggingFace_TOKEN_A/B`.
3. Script efímero `migrar_tokens_hf.sh` (borrado al final): backups con timestamp +
   actualización de `~/.git-credentials`, los dos `.env`, y la caché global.
4. Auditorías sucesivas del scope real vía `whoami-v2`:
   - Token A v1 quedó sobre-privilegiado ("full access": endpoints, webhooks, billing,
     jobs, notificaciones…).
   - v2 intermedia: sin extras pero aún a nivel usuario completo.
   - **v2 final (correcta):** permisos acotados exclusivamente a
     `space:cero2k6/agente-agro-inteligent`, `scoped[user]` vacío, `global: []`.
5. Revocación del token viejo por el usuario → verificado **HTTP 401**.
6. Eliminación de todos los backups que contenían el token viejo.

## Verificaciones finales
- `git push --dry-run hf main`: autenticación OK con Token A mínimo (x3 durante el proceso).
- Inferencia real con Token B vía `router.huggingface.co/v1/chat/completions`
  (`google/gemma-4-26B-A4B-it` → `'OK'`). Nota: los modelos del catálogo actual son
  reasoning y requieren `max_tokens` holgado (mismo fenómeno documentado el 19-08); y
  modelos antiguos pueden ya no estar hospedados por ningún proveedor (400
  *model_not_supported*).
- Cero restos del token viejo en archivos clave; `.gitignore` cubre `.env`/backups en los
  3 proyectos afectados.

## Decisiones
- Separar tokens por función (deploy vs inferencia/datasets) en vez de uno multiuso.
- `credential.helper store` (~/.git-credentials, chmod 600) en lugar de tokens en URLs de
  remotos o pegados en chats.
- No redesplegar el Space todavía: los commits pendientes solo añaden bloat de Ethereum/LaTeX.

## Pendientes (tarde)
- [ ] Opcional: recrear Token B si algún día se quiere acotar también a repos específicos (hoy es razonable: solo user-level read/write + inferencia).
- [ ] Los 3 commits locales sin desplegar al Space (decidir si se excluyen los artefactos Ethereum antes de subir).
- [ ] Recordatorio: rotar `hf-inferencia-datasets` a su expiración (12 meses desde 2026-08-23).
