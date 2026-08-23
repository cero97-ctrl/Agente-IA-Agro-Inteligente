# AGENTS.md — Notas para agentes de IA

## Entorno conda obligatorio: `agro_env`

- Este workspace usa el entorno conda **`agro_env`** (`/home/cero/anaconda3/envs/agro_env`).
- La activación es **automática** en las sesiones de opencode gracias al plugin
  `.opencode/plugins/conda-env.js` (hook `shell.env`).

### Reglas

1. **NO ejecutar `conda activate agro_env` directamente** en sesiones del agente:
   la shell interna de opencode es no interactiva, la función `conda` no existe y el comando falla.
2. **NO asumir que direnv está activo**: `.envrc` se ignora dentro de opencode.
3. Si necesitas el intérprete puntualmente, invócalo por ruta absoluta:
   `/home/cero/anaconda3/envs/agro_env/bin/python`
4. Tras modificar `conda-env.js`, **reiniciar opencode** (los plugins solo cargan al arrancar).

Verificación rápida:

```bash
echo $CONDA_DEFAULT_ENV   # → agro_env
which python              # → /home/cero/anaconda3/envs/agro_env/bin/python
```

Documentación completa (causas del fallo, troubleshooting): [docs/entorno_conda.md](docs/entorno_conda.md)
