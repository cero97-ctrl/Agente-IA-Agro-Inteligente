# Entorno Conda del Proyecto (`agro_env`)

> **Fecha:** agosto 2026 · **Estado:** solución vigente y verificada

Este documento registra la lección aprendida sobre la activación del entorno conda del proyecto, para evitar repetir los errores cometidos al intentar activarlo mediante métodos clásicos dentro de sesiones de agentes de IA (opencode).

---

## 1. Objetivo

El entorno oficial de este workspace es el entorno de conda **`agro_env`**, ubicado en:

```
/home/cero/anaconda3/envs/agro_env
```

Toda ejecución de Python en este proyecto debe usar ese intérprete:

```
/home/cero/anaconda3/envs/agro_env/bin/python
```

## 2. Contexto técnico clave

La shell interna que usa opencode para ejecutar comandos es **no interactiva y no login**:

- Al ser **no login**, no lee `~/.profile` ni `~/.bash_profile`.
- Al ser **no interactiva**, **no lee `~/.bashrc`**.

Consecuencia directa: todo lo configurado en `~/.bashrc` (bloque `# >>> conda initialize >>>`, hook de `direnv`) **nunca se ejecuta** en las sesiones del agente. Esto invalida varios métodos de activación que sí funcionan en terminales manuales.

## 3. Por qué fallan los métodos clásicos

| Método | Por qué falla en la shell de opencode |
|---|---|
| `conda activate agro_env` directo | `conda activate` no es un binario autónomo: es una **función de shell** definida por el bloque `conda init` de `~/.bashrc`. En shells no interactivas esa función no existe → error *"Your shell has not been properly configured to use 'conda activate'"* o sin efecto persistente. El binario `/home/cero/anaconda3/bin/conda` existe, pero invocarlo como subproceso no modifica el PATH del proceso actual. |
| `direnv` + `.envrc` | El `.envrc` del proyecto está bien escrito (`source conda.sh` + `conda activate agro_env`), pero direnv funciona vía hook ligado a `PROMPT_COMMAND`, que solo se dispara al pintar el prompt en shells **interactivas**. Dentro de opencode el hook jamás se ejecuta → `.envrc` se ignora por completo. *Sí funciona en terminales manuales tras `direnv allow`.* |
| Extensión Python de VS Code | Solo activa el entorno en terminales que la propia extensión crea; no afecta la shell interna de opencode ni otras herramientas externas. |

## 4. Solución vigente

El plugin de opencode [`.opencode/plugins/conda-env.js`](../.opencode/plugins/conda-env.js) usa el hook `shell.env`, que **inyecta las variables directamente antes de cada sesión de shell**:

- Antepone `/home/cero/anaconda3/envs/agro_env/bin` al `PATH`.
- Define `CONDA_PREFIX=/home/cero/anaconda3/envs/agro_env`
- Define `CONDA_DEFAULT_ENV=agro_env`
- Define `VIRTUAL_ENV=/home/cero/anaconda3/envs/agro_env`

Esto replica exactamente lo que hace `conda activate` (PATH + variables) **sin depender de funciones de shell ni de la interactividad**. Además, el plugin es robusto: si el prefijo del env no existe (reinstalación o mudanza de anaconda), no inyecta nada y avisa una vez por arranque.

> ⚠️ **Importante:** los plugins de opencode solo se cargan al arrancar. Tras cualquier cambio en `conda-env.js` hay que **reiniciar opencode**.

Métodos complementarios según contexto:

| Contexto | Método válido |
|---|---|
| Sesiones del agente (opencode) | Plugin `shell.env` — automático, no hacer nada |
| Terminal manual interactivo (con direnv) | Entrar al directorio del proyecto (requiere `direnv allow` la primera vez) |
| Script puntual / subshell cualquiera | `source ~/anaconda3/etc/profile.d/conda.sh && conda activate agro_env` |

## 5. Cómo verificar que el entorno está activo

```bash
echo $CONDA_DEFAULT_ENV                    # esperado: agro_env
which python                               # esperado: /home/cero/anaconda3/envs/agro_env/bin/python
python -c "import sys; print(sys.prefix)"  # esperado: /home/cero/anaconda3/envs/agro_env
```

Listado general de entornos: `conda env list` (el asterisco marca el activo).

## 6. Troubleshooting

### El `python` apunta a base o al sistema

1. Verificar que exista `.opencode/plugins/conda-env.js`.
2. Verificar que el env exista: `ls /home/cero/anaconda3/envs/agro_env/bin/python`.
3. **Reiniciar opencode** (los plugins solo cargan al arrancar).

### Anaconda se movió o reinstaló

Actualizar la constante `prefix` al inicio de `.opencode/plugins/conda-env.js` con la nueva ruta y reiniciar opencode. Si la ruta ya no existe, el plugin queda inactivo por diseño (la shell hereda el PATH del sistema en lugar de romperse) y mostrará una advertencia al arrancar.

### Reglas para no repetir el error

1. **NO ejecutar `conda activate` directamente** en sesiones del agente: fallará.
2. **NO asumir que direnv está activo**: dentro de opencode el `.envrc` se ignora.
3. Si un comando necesita el env puntualmente sin el plugin, usar:
   ```bash
   source ~/anaconda3/etc/profile.d/conda.sh && conda activate agro_env
   ```
   o invocar el intérprete por su ruta absoluta: `/home/cero/anaconda3/envs/agro_env/bin/python`.

## 7. Archivos involucrados

| Archivo | Rol |
|---|---|
| `.opencode/plugins/conda-env.js` | Solución vigente: inyecta las variables del env antes de cada sesión de shell |
| `.envrc` | Activación automática vía direnv — solo útil en terminales interactivos del usuario |
| `~/.bashrc` | Contiene el bloque `conda init` y el hook de direnv — nunca se carga en sesiones del agente |
| `AGENTS.md` | Nota breve en la raíz para futuras sesiones de agentes IA, enlaza a este documento |

## 8. Auditoría de dependencias y advertencias (agosto 2026)

Auditoría que compara los imports reales del código contra lo instalado en `agro_env`
y contra `requirements.txt`. Resultado: todos los paquetes de `requirements.txt` están
instalados, pero se detectó un paquete **usado por el código sin estar declarado**:

| Paquete faltante | Usado por | Estado |
|---|---|---|
| `docker` (Docker SDK) | `execution/build_sandbox.py:2`, `execution/run_sandbox.py:8` | ✅ Añadido a `requirements.txt` e instalado (`docker==7.2.0`) |

### Advertencias vigentes (no bloquean, pero conviene planificar)

1. **Python 3.10.19** es la versión de `agro_env`. `google.api_core` advierte que
   termina su soporte para Python 3.10 en **octubre 2026**. Antes de esa fecha conviene
   recrear el entorno con Python ≥ 3.11 (exportar `requirements.txt`, crear env nuevo,
   reinstalar y verificar con los scripts de diagnóstico).
2. **`google-generativeai` está oficialmente deprecado**: ya no recibe parches. El
   sustituto recomendado por Google es el paquete `google-genai`. La migración implica
   cambios de API en `execution/chat_with_llm.py`, `generate_chat_title.py` y
   `execution/test_gemini_connection.py`.
3. **Demonio de Docker caído** (problema de sistema, no de `agro_env`): `docker.service`
   falla al arrancar con *"cannot create network ... (docker0): conflicts with network
   ... networks have same bridge name"*, causado por una base de datos de redes
   obsoleta (`local-kv.db`). Arreglo estándar (requiere sudo):
   ```bash
   sudo systemctl stop docker.socket docker.service
   sudo rm /var/lib/docker/network/files/local-kv.db
   sudo systemctl start docker
   docker ps   # debe listar contenedores sin error
   ```

### Cómo re-auditar en el futuro

```bash
# 1. Comparar requirements.txt vs instalados
/home/cero/anaconda3/envs/agro_env/bin/pip install -r requirements.txt --dry-run

# 2. Verificar que cada import del código resuelve en el entorno
/home/cero/anaconda3/envs/agro_env/bin/python -c "
import importlib.util as u
mods = ['requests','dotenv','google.generativeai','chromadb','PIL','fastapi',
        'uvicorn','pydantic','docker','gtts','pydub','speech_recognition',
        'huggingface_hub','duckduckgo_search','yaml','pypdf','bs4','psutil',
        'autopep8','pytest']
falta = [m for m in mods if u.find_spec(m) is None]
print('FALTANTES:', falta or 'ninguno')
"
```

> Nota: `pydub` necesita `ffmpeg` a nivel sistema (presente: `/usr/bin/ffmpeg`) y
> `SpeechRecognition`+`PyAudio` dependen de PortAudio; ambos verificados en esta auditoría.
