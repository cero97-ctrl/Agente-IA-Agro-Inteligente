# Sesión: Integración de OpenRouter y política de modelos LLM en Agente-IA-Agro-Inteligente

**Fecha:** 2026-08-19
**Agente:** opencode

## Tema tratado
El usuario compró créditos en OpenRouter y quería que el Agente IA de este workspace los usara como proveedor LLM principal (acceso a Gemini, Claude, etc. sin depender de Groq/OpenAI, que están geo-bloqueados desde VE). Se pidió replicar la política de ELECTRONICA: **modelo barato por defecto (Gemini Flash) y Claude Opus 5 solo para tareas complejas**.

## Estado inicial del workspace
- `.env` raíz solo tenía `PRIVATE_KEY` y `SEPOLIA_URL` (Ethereum/Hardhat) — **ninguna clave de LLM configurada**.
- `execution/chat_with_llm.py` solo soportaba proveedores `openai`, `anthropic`, `groq`, `gemini` con orden de fallback Groq → Gemini → OpenAI → Anthropic. Sin OpenRouter.
- Los scripts de generación secundarios (README, resumen, refactor, tests, traducción, auto-doc, explicar código, benchmark) replicaban su propia selección de proveedor, sin OpenRouter.

## Actividades realizadas

### 1. Diagnóstico de impacto
- Confirmado que no había ninguna referencia a `openrouter` en el repositorio (código, directivas o `.env`).
- Verificado que ELECTRONICA sí tenía la integración (commit `8f5250c` en adelante) con `OPENROUTER_API_KEY`, `OPENROUTER_MAX_TOKENS`, `base_url="https://openrouter.ai/api/v1"` y modelos `openai/gpt-oss-20b` / `qwen/qwen3.6-27b` / `google/gemini-2.5-flash`.

### 2. Integración de OpenRouter en el núcleo (`execution/chat_with_llm.py`)
- Nueva función `chat_openrouter()`: cliente compatible con OpenAI contra `https://openrouter.ai/api/v1/chat/completions`, con `max_tokens` configurable vía `OPENROUTER_MAX_TOKENS` (default 2048).
- Añadido `openrouter` a las opciones de `--provider` y como primer proveedor en el orden de fallback: **OpenRouter → Groq → Gemini → OpenAI → Anthropic**.
- Nueva opción `--model` para forzar un modelo específico (ej. `anthropic/claude-opus-5`).

### 3. Scripts secundarios actualizados para preferir OpenRouter
- `benchmark_models.py`, `summarize_project.py`, `refactor_code.py`, `generate_tests.py`, `translate_text.py`, `auto_document.py`, `explain_code.py`, `generate_readme.py` — importan `chat_openrouter` y lo priorizan sobre los demás proveedores.

### 4. `.env`
- Portada `OPENROUTER_API_KEY` y añadido `OPENROUTER_MAX_TOKENS=2048` (misma clave que ELECTRONICA; misma cuenta/créditos).
- Portadas además `GROQ_API_KEY`, `GOOGLE_API_KEY` y `OPENAI_API_KEY` desde ELECTRONICA para respaldo (Anthropic no existe en origen, se omite). Documentadas en `.env.example`.

### 5. Monitor de saldo OpenRouter
- Portado `execution/monitor_saldo_openrouter.py` desde ELECTRONICA (OpenRouter no expone saldo por API; se estima como `créditos_totales − usage`).
- Añadida directiva `directives/monitor_saldo_openrouter.yaml`.
- `CREDITS_TOTAL_REF` recalibrada con el saldo visto en la página (2026-08-19: $9.80 + usage $0.03705 → **9.83704702**). El monitor reporta el saldo estimado correcto.

### 6. Política de modelos (default barato + Opus para tareas complejas)
- Default de OpenRouter: **`google/gemini-3.7-flash`** (barato, ~$0.375/M in / $1.875/M out).
- Opus 5 (`anthropic/claude-opus-5`) explícito solo en tareas complejas: `refactor_code.py` y `generate_tests.py`, o vía CLI `--model anthropic/claude-opus-5`. (El alias `anthropic/claude-opus-latest` no es válido en la API de chat; se usa el ID explícito `anthropic/claude-opus-5`.)
- Benchmark actualizado a Gemini Flash; directivas `chat_with_llm.yaml` y `benchmark_models.yaml` documentan la nueva opción `model`.

### 7. Mismo ajuste aplicado en ELECTRONICA (2026-08-19)
- **Opus 5 (tareas complejas):** `agent_eda.py` (primario), `execution/elaborar_examen.py`, `execution/elaborar_ejercicios.py`, `execution/generar_kicad_llm.py` (default + backend openrouter), `flujo_elaborar_examen.py`/`flujo_elaborar_ejercicios.py` (default y fallback), `flujo_evaluar_examen.py` (`DEFAULT_MODELO["openrouter"]`), `mcp_elaborar_server.py` (default).
- **Gemini Flash (rutinarias):** `rag_system.py`, `data_capture.py` (metadatos RAG), `flujo_analizar_imagen.py` (fallback OpenRouter), `Proyectos/SOLANA/x402_service/app/config.py` (default `LLM_MODEL`).
- Directivas YAML actualizadas (elaborar/evaluar → Opus; analizar imagen → Gemini Flash).

## Verificaciones
- `python3 -m py_compile` OK en todos los archivos modificados (Agente-IA-Agro-Inteligente y ELECTRONICA).
- YAML válido en las directivas editadas.
- Pruebas reales vía OpenRouter:
  - `chat_with_llm.py --provider openrouter` → OK (Gemini Flash default y Opus 5 explícito).
  - Respaldos: Groq/OpenAI devuelven 403 Forbidden (geo-bloqueo VE, esperado); Gemini directo OK.
  - Monitor de saldo: saldo estimado $9.80 (coincide con la página).

## Decisiones
- Modelo OpenRouter por defecto = Gemini Flash para no consumir rápido los créditos.
- Opus 5 reservado para refactorización, generación de tests y tareas complejas de ELECTRONICA (EDA, exámenes, kicad).
- Los modelos de razonamiento (Gemini 3.7 Flash y Opus 5) gastan tokens en "thinking" antes del `content`; fijar `max_tokens` holgado (2048+) para evitar `content: null` (verificado en ELECTRONICA).

## Estado de créditos y monitor (2026-08-19, tarde)
- Consumo acumulado según API: **$0.0406** (usage ≈ 4 céntimos; usage_monthly = usage, tier pago, sin tope).
- Saldo estimado: **$9.80**, consistente con la página.
- Proyección: ~$0.0005–$0.01 por consulta típica con Gemini Flash → cientos de consultas antes del primer auto-top-up (disparado al bajar de $5).
- **Monitor en segundo plano ARRANCADO ✔:** `execution/monitor_saldo_openrouter.py --watch --interval 300`, lanzado con `setsid` (PID 44769, sesión propia `Ss`, sobrevive al cierre de terminal; el primer intento con `nohup` murió por el timeout del shell). Log en `.tmp/saldo_openrouter.log`. Primer chequeo: saldo $9.80, usage $0.0406.
- Para detenerlo: `kill 44769`.

## Pendientes
- [ ] Si cambia el saldo visto en la página (compra/top-up), recalibrar `CREDITS_TOTAL_REF` en `execution/monitor_saldo_openrouter.py` (Agente-IA-Agro-Inteligente).
- [ ] Vigilar saldo vía el monitor (PID 44769); al sonar la alerta (< $5.10), depositar fondos en la tarjeta para el auto top-up de $10 y luego recalibrar la constante.
- [x] Centralizar el cliente OpenRouter en un helper compartido — hecho en ELECTRONICA (`execution/llm_client.py`, commit 8f7b67b). Pendiente opcional: replicar el mismo helper aquí si se quiere compartir lógica entre workspaces.
- [ ] Opcional: llevar un registro automático de sesiones en `Sessions/` al cerrar cada tarea.