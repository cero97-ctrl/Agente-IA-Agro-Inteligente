#!/usr/bin/env python3
import datetime
import json
import random
import os
import subprocess
import sys
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_users.txt")
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_reminders.json")
PERSONA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_persona.txt")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_config.json")
APPOINTMENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_appointments.json")
ROLES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_roles.json")
CROPS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_crops.json")
ALERTS_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_alerts.log")
SURVEILLANCE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_surveillance.json")

PERSONAS = {
    "default": "Eres un Asistente Agrónomo de IA experto en agricultura de precisión. Tu propósito es monitorear cultivos, detectar plagas y optimizar el riego. Respondes de forma técnica pero accesible para agricultores.",
    "serio": "Eres un asistente corporativo, extremadamente formal y serio. No usas emojis ni coloquialismos. Vas directo al grano.",
    "sarcastico": "Eres un asistente con humor negro y sarcasmo. Te burlas sutilmente de las preguntas obvias, pero das la respuesta correcta al final.",
    "profesor": "Eres un profesor universitario paciente y didáctico. Explicas todo con ejemplos, analogías y un tono educativo.",
    "pirata": "¡Arrr! Eres un pirata informático de los siete mares. Usas jerga marinera y pirata en todas tus respuestas.",
    "frances": "Tu es un assistant IA créé par le Prof. César Rodríguez. Tu résides sur un PC GNU/Linux. Réponds toujours en français, de manière gentille, claire et concise."
}

def get_current_persona():
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE, 'r') as f:
            return f.read().strip()
    return PERSONAS["default"]

def set_persona(persona_key):
    with open(PERSONA_FILE, 'w') as f:
        f.write(PERSONAS.get(persona_key, PERSONAS["default"]))

def save_user(chat_id):
    """Registra el ID del usuario para futuros broadcasts."""
    if not chat_id: return
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = set(f.read().splitlines())
    if str(chat_id) not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{chat_id}\n")

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def load_appointments():
    if os.path.exists(APPOINTMENTS_FILE):
        try:
            with open(APPOINTMENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_appointments(appts):
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(appts, f, indent=2)

def get_role(chat_id):
    if os.path.exists(ROLES_FILE):
        try:
            with open(ROLES_FILE, 'r') as f:
                roles = json.load(f)
                return roles.get(str(chat_id), "productor") # Por defecto todos son productores
        except:
            return "productor"
    return "productor"

def set_role(chat_id, role):
    roles = {}
    if os.path.exists(ROLES_FILE):
        try:
            with open(ROLES_FILE, 'r') as f:
                roles = json.load(f)
        except:
            pass
    roles[str(chat_id)] = role
    with open(ROLES_FILE, 'w') as f:
        json.dump(roles, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f)

def check_reminders():
    reminders = load_reminders()
    if not reminders: return

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    updated = False

    for r in reminders:
        # Si coincide la hora y NO se ha enviado hoy
        if r.get('time') == current_time and r.get('last_sent') != today_str:
            print(f"   ⏰ Enviando recordatorio a {r['chat_id']}: {r['message']}")
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏰ *RECORDATORIO:*\n\n{r['message']}", "--chat-id", r['chat_id']])
            r['last_sent'] = today_str
            updated = True
    
    if updated:
        save_reminders(reminders)

def check_appointments():
    appts = load_appointments()
    if not appts: return

    now = datetime.datetime.now()
    current_date = now.strftime("%d/%m")
    current_time = now.strftime("%H:%M")
    updated = False

    for appt in appts:
        # Si coincide fecha y hora, y NO ha sido notificado aún
        if appt.get('date') == current_date and appt.get('time') == current_time and not appt.get('notified'):
            print(f"   📅 Recordando cita a {appt['chat_id']}: {appt['reason']}")
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"📅 *RECORDATORIO DE CITA:*\n\nEs hora de tu cita: {appt['reason']}", "--chat-id", appt['chat_id']])
            appt['notified'] = True
            updated = True
    
    if updated:
        save_appointments(appts)

def load_crops():
    # Datos iniciales con múltiples cultivos
    default_crops = {}

    if os.path.exists(CROPS_FILE):
        try:
            with open(CROPS_FILE, 'r') as f:
                data = json.load(f)
                # Migración simple si cambia formato
                if "heart_rate" in str(data): # Limpieza de datos viejos de telemedicina
                    return {}
                
                return data
        except:
            pass
    return default_crops

def save_crops(data):
    with open(CROPS_FILE, 'w') as f:
        json.dump(data, f)

def simulate_and_monitor_crops():
    crops = load_crops()
    updated = False
    
    for cid, stats in crops.items():
        # 1. Simulación (Solo si NO es modo 'real')
        if stats.get("mode") != "real" and time.time() - stats.get("last_update", 0) > 5:
            # Objetivos ideales (Tomate/Pimiento)
            target_humidity, target_temp, target_ph = 60, 25.0, 6.5
            
            # Simulación de secado progresivo del suelo
            current_hum = stats.get("humidity", 60)
            if current_hum > 10:
                stats["humidity"] = current_hum - random.uniform(0.05, 0.2) # Se seca poco a poco
            
            # Fluctuación de temperatura ambiental
            stats["temperature"] = stats.get("temperature", 25.0) + random.uniform(-0.5, 0.5)
            
            # Fluctuación leve de pH
            stats["ph"] = stats.get("ph", 6.5) + random.uniform(-0.01, 0.01)

            # Redondear
            stats["humidity"] = round(stats["humidity"], 1)
            stats["temperature"] = round(stats["temperature"], 1)
            stats["ph"] = round(stats["ph"], 2)
            
            # Límites fisiológicos
            stats["humidity"] = max(0, min(100, stats["humidity"]))
            stats["temperature"] = max(-5.0, min(50.0, stats["temperature"]))
            
            stats["last_update"] = time.time()
            updated = True

        # 2. Monitoreo y Alertas
        if time.time() - stats.get("last_alert", 0) > 60: # Alertas cada minuto si persiste
            alerts = []
            if stats["humidity"] < 30: alerts.append(f"💧 Estrés Hídrico (Sequía): {stats['humidity']}%")
            if stats["humidity"] > 90: alerts.append(f"🌊 Exceso de Riego: {stats['humidity']}%")
            if stats["temperature"] > 35: alerts.append(f"🔥 Calor Extremo: {stats['temperature']}°C")
            if stats["temperature"] < 5: alerts.append(f"❄️ Riesgo de Helada: {stats['temperature']}°C")
            if stats.get("pest_detected"): alerts.append(f"🐛 PLAGA DETECTADA: {stats['pest_detected']}")

            if alerts:
                msg = f"🚨 *ALERTA AGRONÓMICA*\nCultivo: {stats.get('name', 'Desconocido')} ({cid})\n\n" + "\n".join(alerts) + "\n\n_Se requiere intervención en campo._"
                
                # Guardar en Log Histórico
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(ALERTS_LOG_FILE, 'a') as f:
                    for alert in alerts:
                        f.write(f"[{timestamp}] [{cid}] {alert}\n")

                # Enviar a todos los agrónomos registrados
                if os.path.exists(ROLES_FILE):
                    with open(ROLES_FILE, 'r') as f:
                        roles = json.load(f)
                    for chat_id, role in roles.items():
                        if role == "agronomo":
                            print(f"   🚨 Enviando alerta de cultivo a {chat_id}...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", msg, "--chat-id", chat_id])
                
                stats["last_alert"] = time.time()
                updated = True

    if updated:
        save_crops(crops)

def run_tool(script, args):
    """Ejecuta una herramienta del framework, maneja errores y devuelve su salida JSON."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    cmd = [sys.executable, script_path] + args
    try:
        # Aumentar el timeout para operaciones largas como la ingesta de PDFs
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Mostrar stderr para depuración (RAG, errores, etc.)
        if result.stderr:
            print(f"   🛠️  [LOG {script}]: {result.stderr.strip()}")
            
        # Si el script falló (exit code != 0) Y stdout está vacío,
        # es muy probable que el error JSON esté en stderr.
        if result.returncode != 0 and not result.stdout.strip():
            try:
                # Devolvemos el JSON de error para que el llamador lo maneje
                return json.loads(result.stderr)
            except json.JSONDecodeError:
                # Si stderr tampoco es JSON, devolvemos un error genérico con el contenido de stderr
                return {"status": "error", "error_message": "Error de ejecución no JSON", "details": result.stderr.strip()}

        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Error crítico: {script} falló y no devolvió JSON válido.")
        err_details = "Sin detalles."
        # 'result' puede no existir si el error fue antes de la asignación
        if 'result' in locals():
            if result.stdout: print(f"   Salida (stdout): {result.stdout.strip()}")
            if result.stderr: 
                print(f"   Logs de error (stderr): {result.stderr.strip()}")
                err_details = result.stderr.strip()
        return {"status": "error", "error_message": "Respuesta inválida (no JSON)", "details": err_details}
    except subprocess.TimeoutExpired:
        print(f"❌ Error crítico: {script} tardó demasiado en ejecutarse (timeout).")
        return {"status": "error", "error_message": "Timeout", "details": f"El script {script} superó el límite de 120 segundos."}
    except Exception as e:
        print(f"Error ejecutando {script}: {e}")
        return {"status": "error", "error_message": "Excepción en run_tool", "details": str(e)}

def load_surveillance():
    if os.path.exists(SURVEILLANCE_FILE):
        try:
            with open(SURVEILLANCE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_surveillance(data):
    with open(SURVEILLANCE_FILE, 'w') as f:
        json.dump(data, f)

def check_surveillance():
    data = load_surveillance()
    if not data.get("active"): return

    # Intervalo: 5 minutos (300 segundos)
    if time.time() - data.get("last_check", 0) > 300:
        chat_id = data.get("chat_id")
        print(f"   🛡️ [Vigilancia] Revisando cámara...")
        
        cam_ip = os.getenv("ESP32_CAM_IP")
        if not cam_ip:
            return

        # 1. Capturar
        local_path = os.path.join(".tmp", f"surveillance_{int(time.time())}.jpg")
        res = run_tool("capture_image.py", ["--ip", cam_ip, "--output-file", local_path])
        
        if res and res.get("status") == "success":
            # 2. Analizar
            prompt = "Actúa como un guardia de seguridad. Analiza esta imagen. Si ves a una persona, alguien en el suelo, o algo peligroso, responde comenzando con 'ALERTA: ' seguido de la descripción. Si la habitación está vacía y tranquila, responde solo 'Normal'."
            
            analysis = run_tool("analyze_image.py", ["--image", local_path, "--prompt", prompt])
            
            if analysis and analysis.get("status") == "success":
                desc = analysis.get("description", "")
                if "ALERTA" in desc.upper():
                    msg = f"🚨 *ALERTA DE VIGILANCIA*\n\n{desc}"
                    run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", local_path, "--chat-id", chat_id, "--caption", msg])
            
            try: os.remove(local_path)
            except: pass
        
        data["last_check"] = time.time()
        save_surveillance(data)

def main():
    # Asegurar que el directorio temporal existe para evitar errores
    os.makedirs(os.path.dirname(SURVEILLANCE_FILE), exist_ok=True)

    # Asegurar que el archivo de cultivos exista, aunque esté vacío, para la UI web.
    if not os.path.exists(CROPS_FILE):
        with open(CROPS_FILE, 'w') as f:
            json.dump({}, f)
        print("   🌱 Archivo de cultivos inicializado para la web.")

    print("📡 Escuchando Telegram... (Presiona Ctrl+C para detener)")
    print("   El agente responderá a cualquier mensaje que le envíes.")
    
    # Verificación de configuración al inicio
    admin_id = os.getenv("TELEGRAM_CHAT_ID")
    if admin_id:
        print(f"   ✅ Configurado para responder al Admin ID: {admin_id}")
        
        # Enviar mensaje de bienvenida al iniciar
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🌱 *Sistema Agro-Inteligente Iniciado*\n\nEstoy monitoreando los cultivos.\nUsa /ayuda para ver las herramientas disponibles.", "--chat-id", admin_id])
    else:
        print("   ⚠️  ADVERTENCIA: TELEGRAM_CHAT_ID no detectado en .env. El bot podría ignorar tus mensajes.")
    
    # Resetear estado de vigilancia al iniciar para evitar activaciones accidentales
    save_surveillance({"active": False, "last_check": 0, "chat_id": ""})
    print("   🛡️  Vigilancia: Estado reiniciado a OFF.")

    # Configurar menú de comandos visual en Telegram
    print("   🔘 Activando menú de comandos en Telegram...")
    run_tool("telegram_tool.py", ["--action", "set-commands"])

    last_health_check = time.time()
    HEALTH_CHECK_INTERVAL = 300  # Verificar cada 5 minutos

    try:
        while True:
            # 1. Consultar nuevos mensajes
            response = run_tool("telegram_tool.py", ["--action", "check"])
            
            if response and response.get("status") == "error":
                print(f"⚠️ Error en Telegram: {response.get('message')}")
                time.sleep(5) # Esperar un poco más si hubo error para no saturar

            if response and response.get("status") == "success":
                messages = response.get("messages", [])
                for msg in messages:
                    try:
                        # Parsear formato "CHAT_ID|MENSAJE"
                        if "|" in msg:
                            sender_id, content = msg.split("|", 1)
                        else:
                            sender_id = None
                            content = msg

                        save_user(sender_id)
                        print(f"\n📩 Mensaje recibido de {sender_id}: '{content}'")
                        
                        reply_text = ""
                        msg_logic = content # Usamos el contenido limpio para la lógica
                        is_voice_interaction = False # Bandera para saber si responder con audio
                        voice_lang_short = "es" # Default language for TTS
                        
                        # --- COMANDOS ESPECIALES (Capa 3: Ejecución) ---
                        
                        # 1. DETECCIÓN DE FOTOS
                        if msg_logic.startswith("__PHOTO__:"):
                            parts = content.replace("__PHOTO__:", "").split("|||")
                            file_id = parts[0]
                            user_caption = parts[1] if len(parts) > 1 else ""
                            
                            # Prompt agronómico por defecto si el usuario no especifica nada
                            if not user_caption.strip():
                                caption = "Actúa como un Ingeniero Agrónomo experto. Analiza esta imagen detalladamente. Busca signos de plagas, enfermedades, deficiencias nutricionales o estrés hídrico. Si detectas algo, da un diagnóstico y una recomendación de tratamiento. Si es una planta sana, indícalo."
                            else:
                                caption = f"Actúa como un Ingeniero Agrónomo. El usuario pregunta: '{user_caption}'. Analiza la imagen en base a esto."
                            
                            print(f"   📸 Foto recibida. Descargando ID: {file_id}...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "👀 Analizando imagen...", "--chat-id", sender_id])
                            
                            # Descargar
                            local_path = os.path.join(".tmp", f"photo_{int(time.time())}.jpg")
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # Analizar
                            res = run_tool("analyze_image.py", ["--image", local_path, "--prompt", caption])
                            if res and res.get("status") == "success":
                                reply_text = f"👁️ *Análisis Visual:*\n{res.get('description')}"
                            else:
                                reply_text = f"❌ Error analizando imagen: {res.get('message')}"

                        # 1.2 DETECCIÓN DE DOCUMENTOS (PDF)
                        elif msg_logic.startswith("__DOCUMENT__:"):

                            parts = content.replace("__DOCUMENT__:", "").split("|||")
                            file_id = parts[0]
                            file_name = parts[1]
                            caption = parts[2] if len(parts) > 2 else ""
                            
                            print(f"   📄 Documento recibido: {file_name}. Descargando...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"📂 Recibí `{file_name}`. Leyendo contenido...", "--chat-id", sender_id])
                            
                            # Descargar a .tmp (que se monta en /mnt/out en el sandbox)
                            local_path = os.path.join(".tmp", file_name)
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # Extraer texto usando el Sandbox (ya tiene pypdf)
                            # Nota: .tmp está montado en /mnt/out dentro del contenedor
                            path_in_sandbox = f"/mnt/out/{file_name}"
                            
                            read_code = (
                                f"from pypdf import PdfReader; "
                                f"reader = PdfReader('{path_in_sandbox}'); "
                                f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                            )
                            
                            res_sandbox = run_tool("run_sandbox.py", ["--code", read_code])
                            
                            if res_sandbox and res_sandbox.get("status") == "success":
                                content = res_sandbox.get("stdout", "")
                                if len(content) > 15000:
                                    content = content[:15000] + "... (truncado)"
                                
                                if not content.strip():
                                    reply_text = "⚠️ El documento parece estar vacío o es una imagen escaneada sin texto (OCR no disponible en sandbox)."
                                else:
                                    # Analizar con LLM
                                    analysis_prompt = f"""Actúa como un Ingeniero Agrónomo experto. Analiza el siguiente documento PDF proporcionado por el usuario.
                                    
CONTEXTO DEL USUARIO (si lo hay): {caption}

CONTENIDO DEL DOCUMENTO:
---
{content}
---

TAREA:
1.  **Identifica el tipo de documento** (ej: análisis de suelo, ficha técnica de fertilizante, paper de investigación, guía de plagas).
2.  **Si es un análisis técnico:**
    - Resume los valores clave (pH, nutrientes, etc.).
    - Da recomendaciones prácticas para el agricultor.
    - **IMPORTANTE:** Termina tu respuesta con el disclaimer: "Nota: Soy una IA. Este análisis es informativo y no sustituye la opinión de un ingeniero agrónomo en campo."
3.  **Si es cualquier otro tipo de documento:**
    - Simplemente resume su contenido y propósito principal de forma clara.
"""
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando informe médico...", "--chat-id", sender_id])
                                    
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", analysis_prompt])
                                    
                                    if llm_res and "content" in llm_res:
                                        reply_text = llm_res["content"]
                                    else:
                                        reply_text = "❌ Error al analizar el documento con la IA."
                            else:
                                err = res_sandbox.get("stderr") or res_sandbox.get("message")
                                reply_text = f"❌ Error leyendo el PDF: {err}"

                        # 1.5 DETECCIÓN DE VOZ
                        elif msg_logic.startswith("__VOICE__:"):

                            is_voice_interaction = True
                            file_id = content.replace("__VOICE__:", "")
                            print(f"   🎤 Nota de voz recibida. Descargando ID: {file_id}...")

                            run_tool("telegram_tool.py", ["--action", "send", "--message", "👂 Escuchando...", "--chat-id", sender_id])
                            
                            local_path = os.path.join(".tmp", f"voice_{int(time.time())}.ogg")
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # Transcribir
                            # Cargar idioma configurado (default es-ES)
                            config = load_config()
                            lang_code = config.get("voice_lang", "es-ES")
                            voice_lang_short = lang_code.split('-')[0] # 'es-ES' -> 'es'
                            
                            res = run_tool("transcribe_audio.py", ["--file", local_path, "--lang", lang_code])
                            if res and res.get("status") == "success":
                                text = res.get("text")
                                print(f"   📝 Transcripción: '{text}'")
                                # ¡Truco! Reemplazamos el mensaje de voz por su texto y dejamos que el flujo continúe
                                msg_logic = text
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"🗣️ Dijiste: \"{text}\"", "--chat-id", sender_id])
                            else:
                                err_msg = res.get("message", "Error desconocido") if res else "Falló el script de transcripción"
                                reply_text = f"❌ No pude entender el audio. Detalle: {err_msg}"

                        # 2. COMANDOS DE TEXTO
                        # (Nota: usamos 'if' aquí en lugar de 'elif' para que el texto transcrito de voz pueda entrar)
                        if msg_logic.startswith("/investigar") or msg_logic.startswith("/research"):
                            topic = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not topic:
                                reply_text = "⚠️ Uso: /investigar [tema]"
                            else:
                                print(f"   🔍 Ejecutando investigación sobre: {topic}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"🕵️‍♂️ Investigando sobre '{topic}'... dame unos segundos.", "--chat-id", sender_id])
                                
                                # Ejecutar herramienta de research
                                res = run_tool("research_topic.py", ["--query", topic, "--output-file", ".tmp/tg_research.txt"])
                                
                                if res and res.get("status") == "success":
                                    # Leer y resumir resultados
                                    try:
                                        with open(".tmp/tg_research.txt", "r", encoding="utf-8") as f:
                                            data = f.read()
                                        print("   🧠 Resumiendo resultados...")
                                        
                                        # Prompt mejorado: pide al LLM que use su memoria (RAG) y los resultados de la búsqueda.
                                        summarization_prompt = f"""Considerando lo que ya sabes en tu memoria y los siguientes resultados de búsqueda sobre '{topic}', crea un resumen conciso para Telegram.

Resultados de Búsqueda:
---
{data}"""
                                        llm_res = run_tool("chat_with_llm.py", ["--prompt", summarization_prompt, "--memory-query", topic])
                                        
                                        if llm_res and "content" in llm_res:
                                            reply_text = llm_res["content"]
                                        elif llm_res and "error" in llm_res:
                                            reply_text = f"⚠️ Error del modelo: {llm_res['error']}"
                                        else:
                                            reply_text = "❌ No se pudo generar el resumen (Respuesta vacía o inválida)."
                                    except Exception as e:
                                        reply_text = f"Error procesando resultados: {e}"
                                else:
                                    reply_text = "❌ Error al ejecutar la herramienta de investigación."
                    
                        elif msg_logic.startswith("/reporte") or msg_logic.startswith("/report"):
                            topic = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not topic:
                                reply_text = "⚠️ Uso: /reporte [tema agronómico o de investigación]"
                            else:
                                print(f"   🚜 Generando reporte agronómico sobre: {topic}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"👩‍🌾 Iniciando investigación profunda sobre '{topic}'... Esto tomará unos segundos.", "--chat-id", sender_id])
                            
                                # 1. Investigar (Search)
                                # Buscamos específicamente tratamientos y terapias
                                query = f"manejo agronómico control plagas y fertilización para {topic}"
                                res_search = run_tool("research_topic.py", ["--query", query, "--output-file", ".tmp/agro_research.txt"])
                            
                                if res_search and res_search.get("status") == "success":
                                    try:
                                        with open(".tmp/agro_research.txt", "r", encoding="utf-8") as f:
                                            search_data = f.read()
                                    
                                        # 2. Generar Reporte (LLM)
                                        report_prompt = f"""Actúa como un Ingeniero Agrónomo Investigador.
    Basado en los siguientes resultados de búsqueda, genera un REPORTE DETALLADO en formato Markdown sobre '{topic}'.

    Estructura sugerida:
    1. 📋 Resumen Ejecutivo
    2. 🐛 Plagas y Enfermedades Comunes
    3. 💊 Estrategias de Control (Biológico y Químico)
    4. 💧 Requerimientos de Riego y Nutrición
    5. 🚜 Recomendaciones de Manejo

    RESULTADOS DE BÚSQUEDA:
    {search_data}

    IMPORTANTE:
    - Usa un tono profesional pero claro y esperanzador.
    - INCLUYE UN DISCLAIMER AL INICIO: "Nota: Soy una IA. Este reporte es informativo y no sustituye el consejo técnico en campo."
    """
                                        run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando datos y redactando informe...", "--chat-id", sender_id])
                                    
                                        # Usamos --memory-query para que busque en memoria solo el tema, no el prompt entero
                                        llm_res = run_tool("chat_with_llm.py", ["--prompt", report_prompt, "--memory-query", topic])
                                    
                                        if llm_res and "content" in llm_res:
                                            report_content = llm_res["content"]
                                        
                                            # 3. Guardar en docs/
                                            safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:30]
                                            filename = f"Reporte_Agro_{safe_topic}.md"
                                            # Construir ruta absoluta a docs/
                                            docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", filename)
                                        
                                            with open(docs_path, "w", encoding="utf-8") as f:
                                                f.write(report_content)
                                            
                                            reply_text = f"✅ *Reporte Generado Exitosamente*\n\nHe guardado el informe detallado en:\n`docs/{filename}`\n\nAquí tienes un resumen:\n\n" + report_content[:400] + "...\n\n_(Lee el archivo completo en tu carpeta docs)_"
                                        else:
                                            reply_text = "❌ Error al redactar el reporte con el modelo."
                                        
                                    except Exception as e:
                                        reply_text = f"❌ Error procesando el reporte: {e}"
                                else:
                                    reply_text = "❌ Error en la fase de investigación (Búsqueda)."

                        elif msg_logic.startswith("/recordatorio") or msg_logic.startswith("/remind"):
                            try:
                                parts = msg_logic.split(" ", 2)
                                if len(parts) < 3:
                                    reply_text = "⚠️ Uso: /recordatorio HH:MM Mensaje\nEj: /recordatorio 08:00 Revisar riego"
                                else:
                                    time_str = parts[1]
                                    note = parts[2]
                                    # Validar formato de hora
                                    datetime.datetime.strptime(time_str, "%H:%M")
                                
                                    reminders = load_reminders()
                                    reminders.append({
                                        "chat_id": str(sender_id),
                                        "time": time_str,
                                        "message": note,
                                        "last_sent": ""
                                    })
                                    save_reminders(reminders)
                                    reply_text = f"✅ Recordatorio configurado.\nTe avisaré todos los días a las {time_str}: '{note}'."
                            except ValueError:
                                reply_text = "❌ Hora inválida. Usa formato 24h (HH:MM), ej: 14:30."

                        elif msg_logic.startswith("/borrar_recordatorios") or msg_logic.startswith("/clear_reminders"):
                            reminders = load_reminders()
                            # Filtrar, manteniendo solo los recordatorios de OTROS usuarios
                            reminders_to_keep = [r for r in reminders if r.get('chat_id') != str(sender_id)]
                            if len(reminders) == len(reminders_to_keep):
                                reply_text = "🤔 No tienes recordatorios configurados para borrar."
                            else:
                                save_reminders(reminders_to_keep)
                                reply_text = "✅ Todos tus recordatorios han sido eliminados."

                        elif msg_logic.startswith("/cita") or msg_logic.startswith("/appointment"):
                            try:
                                # Formato esperado: /cita DD/MM HH:MM Motivo
                                parts = msg_logic.split(" ", 3)
                                if len(parts) < 4:
                                    reply_text = "⚠️ Uso: /cita DD/MM HH:MM Motivo\nEj: /cita 25/10 15:30 Visita técnica"
                                else:
                                    date_str = parts[1]
                                    time_str = parts[2]
                                    reason = parts[3]
                                    
                                    # Validación simple de formato de fecha/hora
                                    datetime.datetime.strptime(f"{date_str} {time_str}", "%d/%m %H:%M")
                                    
                                    # Guardar en un archivo JSON dedicado a citas
                                    existing_appts = []
                                    if os.path.exists(APPOINTMENTS_FILE):
                                        with open(APPOINTMENTS_FILE, 'r') as f:
                                            try: existing_appts = json.load(f)
                                            except: pass
                                    
                                    existing_appts.append({"chat_id": str(sender_id), "date": date_str, "time": time_str, "reason": reason, "created_at": str(datetime.datetime.now())})
                                    
                                    with open(APPOINTMENTS_FILE, 'w') as f:
                                        json.dump(existing_appts, f, indent=2)
                                        
                                    reply_text = f"✅ *Cita Agendada*\n\n📅 Fecha: {date_str}\n⏰ Hora: {time_str}\n📝 Motivo: {reason}\n\nHe registrado esta cita en el sistema."
                            except ValueError:
                                reply_text = "❌ Formato de fecha u hora inválido. Usa DD/MM HH:MM (ej: 25/10 14:00)."

                        elif msg_logic.startswith("/mis_citas") or msg_logic.startswith("/my_appointments"):
                            appts = load_appointments()
                            user_appts = [a for a in appts if a.get('chat_id') == str(sender_id)]
                            
                            if not user_appts:
                                reply_text = "🗓️ No tienes ninguna cita agendada."
                            else:
                                future_appts = []
                                now = datetime.datetime.now()
                                
                                for appt in user_appts:
                                    try:
                                        # Asume el año actual. Para una cita de enero hecha en diciembre, podría fallar.
                                        # Para este caso de uso, es una simplificación aceptable.
                                        appt_dt = datetime.datetime.strptime(f"{now.year}/{appt['date']} {appt['time']}", "%Y/%d/%m %H:%M")
                                        if appt_dt >= now:
                                            future_appts.append(appt)
                                    except ValueError:
                                        continue # Ignorar citas con formato de fecha/hora corrupto
                                
                                if not future_appts:
                                    reply_text = "🗓️ No tienes citas pendientes. (Todas tus citas agendadas ya pasaron)."
                                else:
                                    future_appts.sort(key=lambda x: datetime.datetime.strptime(f"{now.year}/{x['date']} {x['time']}", "%Y/%d/%m %H:%M"))
                                    reply_text = "🗓️ *Tus Próximas Citas:*\n\n"
                                    for appt in future_appts:
                                        reply_text += f"▫️ *{appt['date']}* a las *{appt['time']}* - {appt['reason']}\n"

                        elif msg_logic.startswith("/traducir") or msg_logic.startswith("/translate"):
                            content = msg_logic.split(" ", 1)[1].strip() if " " in msg_logic else ""
                            if not content:
                                reply_text = "⚠️ Uso: /traducir [texto | nombre_archivo]"
                            else:
                                # Verificar si es un archivo local (docs o .tmp)
                                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                docs_file = os.path.join(base_dir, "docs", content)
                                tmp_file = os.path.join(base_dir, ".tmp", content)
                            
                                target_file = None
                                if os.path.exists(docs_file): target_file = docs_file
                                elif os.path.exists(tmp_file): target_file = tmp_file
                            
                                if target_file:
                                    print(f"   📄 Traduciendo archivo: {content}")
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Traduciendo `{content}` al español...", "--chat-id", sender_id])
                                
                                    res = run_tool("translate_text.py", ["--file", target_file, "--lang", "Español"])
                                
                                    if res and res.get("status") == "success":
                                        out_path = res.get("file_path")
                                        run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", out_path, "--chat-id", sender_id, "--caption", "📄 Traducción al Español"])
                                        reply_text = "✅ Archivo traducido enviado."
                                    else:
                                        err = res.get("message", "Error desconocido") if res else "Error en script"
                                        reply_text = f"❌ Error al traducir archivo: {err}"
                                else:
                                    # Traducir texto plano
                                    print(f"   🔤 Traduciendo texto...")
                                    prompt = f"Traduce el siguiente texto al Español. Devuelve solo la traducción:\n\n{content}"
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
                                    if llm_res and "content" in llm_res:
                                        reply_text = f"🇪🇸 *Traducción:*\n\n{llm_res['content']}"
                                    else:
                                        reply_text = "❌ Error al traducir texto."

                        elif msg_logic.startswith("/idioma") or msg_logic.startswith("/lang"):
                            parts = msg_logic.split(" ")
                            if len(parts) < 2:
                                reply_text = "⚠️ Uso: /idioma [es/en]\nEj: /idioma en (para inglés)"
                            else:
                                lang_map = {"es": "es-ES", "en": "en-US", "fr": "fr-FR", "pt": "pt-BR"}
                                selection = parts[1].lower()
                                code = lang_map.get(selection, "es-ES")
                                config = load_config()
                                config["voice_lang"] = code
                                save_config(config)
                                reply_text = f"✅ Idioma de voz cambiado a: `{code}`.\nAhora te escucharé en ese idioma."

                        elif msg_logic.startswith("/ayuda_agro"):
                            manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "manual_agronomo.pdf")
                            if os.path.exists(manual_path):
                                print(f"   🚜 Enviando manual agronómico a {sender_id}...")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "📘 Aquí tienes la guía de uso del sistema.", "--chat-id", sender_id])
                                run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", manual_path, "--chat-id", sender_id, "--caption", "Manual de Agro-Inteligencia (IA)"])
                            else:
                                reply_text = "⚠️ El manual PDF no ha sido generado aún. Pide al administrador que ejecute `pdflatex`."

                        elif msg_logic.startswith("/ingestar") or msg_logic.startswith("/ingest"):
                            filename = msg_logic.split(" ", 1)[1].strip() if " " in msg_logic else ""
                            if not filename:
                                reply_text = "⚠️ Uso: /ingestar [nombre_archivo.pdf] (debe estar en la carpeta docs/)"
                            else:
                                print(f"   📚 Ingestando archivo: {filename}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Procesando `{filename}` para memoria a largo plazo...", "--chat-id", sender_id])
                                
                                # Ejecutar script de ingesta
                                res = run_tool("ingest_pdf.py", ["--filename", filename])
                                
                                if res and res.get("status") == "success":
                                    chunks = res.get("chunks_ingested", 0)
                                    reply_text = f"✅ *Ingesta Completada*\n\nArchivo: `{filename}`\nFragmentos guardados: {chunks}\n\nAhora puedo recordar el contenido de este documento."
                                else:
                                    err = res.get("error_message") if res else "Falló la ejecución."
                                    details = res.get("details") if res else "Revisa los logs del servidor."
                                    reply_text = f"❌ Error al ingestar: {err}\n_{details}_"

                        elif msg_logic.startswith("/biblioteca") or msg_logic.startswith("/library"):
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "📚 Consultando índice de documentos...", "--chat-id", sender_id])
                            res = run_tool("list_documents.py", [])
                            
                            if res and res.get("status") == "success":
                                docs = res.get("documents", [])
                                if docs:
                                    reply_text = "📚 *Documentos en Memoria:*\n\n" + "\n".join([f"📄 `{d['name']}`" for d in docs])
                                else:
                                    reply_text = "📭 No hay documentos PDF ingestados aún."
                            else:
                                reply_text = f"❌ Error consultando biblioteca: {res.get('message')}"

                        elif msg_logic.startswith("/resumir_archivo") or msg_logic.startswith("/summarize_file"):
                            filename = msg_logic.split(" ", 1)[1].strip() if " " in msg_logic else ""
                            if not filename:
                                reply_text = "⚠️ Uso: /resumir_archivo [nombre_del_archivo_en_docs]"
                            else:
                                print(f"   📄 Resumiendo archivo local: {filename}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo y resumiendo `{filename}`...", "--chat-id", sender_id])

                                # 1. Leer el archivo desde el Sandbox
                                path_in_container = f"/mnt/docs/{filename}"
                            
                                if filename.lower().endswith(".pdf"):
                                    # Código para extraer texto de PDF usando pypdf
                                    read_code = (
                                        f"from pypdf import PdfReader; "
                                        f"reader = PdfReader('{path_in_container}'); "
                                        f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                                    )
                                else:
                                    read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"
                            
                                read_res = run_tool("run_sandbox.py", ["--code", read_code])

                                if read_res and read_res.get("status") == "success" and read_res.get("stdout"):
                                    content = read_res.get("stdout")
                                
                                    if len(content) > 10000:
                                        content = content[:10000] + "... (truncado)"
                                
                                    # 2. Enviar a LLM para resumir
                                    prompt = f"Resume el siguiente documento llamado '{filename}':\n\n{content}"
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])

                                    if llm_res and "content" in llm_res:
                                        reply_text = llm_res["content"]
                                    else:
                                        reply_text = "❌ Error generando el resumen."
                                else:
                                    error_details = read_res.get("stderr") or read_res.get("message", "No se pudo leer el archivo.")
                                    reply_text = f"❌ Error al leer el archivo `{filename}` desde el Sandbox:\n`{error_details}`"

                        elif msg_logic.startswith("/resumir") or msg_logic.startswith("/summarize"):
                            url = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not url:
                                reply_text = "⚠️ Uso: /resumir [url]"
                            else:
                                print(f"   🌐 Resumiendo URL: {url}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo {url}...", "--chat-id", sender_id])
                            
                                # 1. Scrape
                                scrape_res = run_tool("scrape_single_site.py", ["--url", url, "--output-file", ".tmp/web_content.txt"])
                            
                                if scrape_res and scrape_res.get("status") == "success":
                                    # 2. Summarize
                                    try:
                                        with open(".tmp/web_content.txt", "r", encoding="utf-8") as f:
                                            content = f.read()
                                    
                                        # Truncar si es muy largo (ej. 10k caracteres) para no saturar CLI args
                                        if len(content) > 10000:
                                            content = content[:10000] + "... (truncado)"
                                        
                                        prompt = f"Resume el siguiente contenido web para Telegram:\n\n{content}"
                                        llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
                                    
                                        if llm_res and "content" in llm_res:
                                            reply_text = llm_res["content"]
                                        elif llm_res and "error" in llm_res:
                                            reply_text = f"⚠️ Error del modelo: {llm_res['error']}"
                                        else:
                                            reply_text = "❌ Error generando resumen."
                                        
                                    except Exception as e:
                                        reply_text = f"❌ Error leyendo contenido: {e}"
                                else:
                                    err = scrape_res.get("message") if scrape_res else "Error desconocido"
                                    # Ayuda contextual si el usuario intenta usar /resumir con un archivo local
                                    if "No scheme supplied" in str(err):
                                        filename = url.split('/')[-1]
                                        reply_text = f"🤔 El comando /resumir es para URLs (ej: `https://...`).\n\nSi querías resumir el archivo local `{filename}`, el comando correcto es:\n/resumir_archivo {filename}"
                                    else:
                                        reply_text = f"❌ Error leyendo la web: {err}"

                        elif msg_logic.startswith("/recordar") or msg_logic.startswith("/remember"):
                            memory_text = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not memory_text:
                                reply_text = "⚠️ Uso: /recordar [dato a guardar]"
                            else:
                                print(f"   💾 Guardando en memoria: {memory_text}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "💾 Guardando nota...", "--chat-id", sender_id])
                            
                                # Ejecutar herramienta de memoria (save_memory.py)
                                res = run_tool("save_memory.py", ["--text", memory_text, "--category", "telegram_note"])
                            
                                if res and res.get("status") == "success":
                                    reply_text = "✅ Nota guardada en memoria a largo plazo."
                                else:
                                    reply_text = "❌ Error al guardar. (Verifica que save_memory.py exista y funcione)."

                        elif msg_logic.startswith("/memorias") or msg_logic.startswith("/memories"):
                            print("   🧠 Consultando lista de recuerdos...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Consultando base de datos...", "--chat-id", sender_id])
                        
                            res = run_tool("list_memories.py", ["--limit", "5"])
                            if res and res.get("status") == "success":
                                memories = res.get("memories", [])
                                if not memories:
                                    reply_text = "📭 No tengo recuerdos guardados aún."
                                else:
                                    reply_text = "🧠 *Últimos recuerdos:*\n"
                                    for m in memories:
                                        date = m.get("timestamp", "").replace("T", " ").split(".")[0]
                                        content = m.get("content", "")
                                        mem_id = m.get("id", "N/A")
                                        reply_text += f"🆔 `{mem_id}`\n📅 {date}: {content}\n\n"
                            else:
                                reply_text = "❌ Error al consultar la memoria."

                        elif msg_logic.startswith("/olvidar") or msg_logic.startswith("/forget"):
                            mem_id = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not mem_id:
                                reply_text = "⚠️ Uso: /olvidar [ID]"
                            else:
                                print(f"   🗑️ Eliminando recuerdo: {mem_id}")
                                res = run_tool("delete_memory.py", ["--id", mem_id])
                                if res and res.get("status") == "success":
                                    reply_text = "✅ Recuerdo eliminado."
                                else:
                                    reply_text = f"❌ Error al eliminar: {res.get('message', 'Desconocido')}"

                        elif msg_logic.startswith("/olvidar_archivo") or msg_logic.startswith("/forget_file"):
                            filename = msg_logic.split(" ", 1)[1].strip() if " " in msg_logic else ""
                            if not filename:
                                reply_text = "⚠️ Uso: /olvidar_archivo [nombre_archivo.pdf]"
                            else:
                                print(f"   🗑️ Eliminando documento de memoria: {filename}")
                                res = run_tool("delete_memory.py", ["--filename", filename])
                                if res and res.get("status") == "success":
                                    reply_text = f"✅ Documento '{filename}' eliminado de la memoria."
                                else:
                                    reply_text = f"❌ Error al eliminar: {res.get('message', 'Desconocido')}"

                        elif msg_logic.startswith("/broadcast") or msg_logic.startswith("/anuncio"):
                            announcement = msg_logic.split(" ", 1)[1] if " " in msg_logic else ""
                            if not announcement:
                                reply_text = "⚠️ Uso: /broadcast [mensaje para todos]"
                            else:
                                if os.path.exists(USERS_FILE):
                                    with open(USERS_FILE, 'r') as f:
                                        users = f.read().splitlines()
                                    count = 0
                                    for uid in users:
                                        if uid.strip():
                                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"📢 *ANUNCIO:*\n{announcement}", "--chat-id", uid])
                                            count += 1
                                    reply_text = f"✅ Mensaje enviado a {count} usuarios."
                                else:
                                    reply_text = "⚠️ No tengo usuarios registrados aún."

                        elif msg_logic.startswith("/status"):
                            print("   📊 Verificando estado del sistema...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "🔍 Escaneando sistema...", "--chat-id", sender_id])
                        
                            res = run_tool("monitor_resources.py", [])
                            # monitor_resources devuelve JSON incluso si hay alertas (exit code 1)
                            if res:
                                metrics = res.get("metrics", {})
                                alerts = res.get("alerts", [])
                                
                                cam_ip = os.getenv("ESP32_CAM_IP", "No configurada")
                            
                                status_emoji = "✅" if not alerts else "⚠️"
                                reply_text = (
                                    f"{status_emoji} *Estado del Servidor:*\n\n"
                                    f"💻 *CPU:* {metrics.get('cpu_percent', 0)}%\n"
                                    f"🧠 *RAM:* {metrics.get('memory_percent', 0)}% ({metrics.get('memory_used_gb', 0)}GB / {metrics.get('memory_total_gb', 0)}GB)\n"
                                    f"💾 *Disco:* {metrics.get('disk_percent', 0)}% (Libre: {metrics.get('disk_free_gb', 0)}GB)\n"
                                    f"📷 *Cámara IP:* `{cam_ip}`\n"
                                )
                                if alerts:
                                    reply_text += "\n🚨 *Alertas:*\n" + "\n".join([f"- {a}" for a in alerts])
                            else:
                                reply_text = "❌ Error al obtener métricas."

                        elif msg_logic.startswith("/debug_env"):
                            import platform
                            reply_text = (
                                f"🛠️ *Entorno de Ejecución:*\n\n"
                                f"🐍 *Python:* `{sys.executable}`\n"
                                f"💻 *OS:* {platform.system()} {platform.release()}\n"
                                f"📂 *CWD:* `{os.getcwd()}`\n"
                                f"📦 *Virtual Env:* {'✅ Sí' if sys.prefix != sys.base_prefix else '⚠️ No detectado'}"
                            )

                        elif msg_logic.startswith("/usuarios") or msg_logic.startswith("/users"):
                            if os.path.exists(USERS_FILE):
                                with open(USERS_FILE, 'r') as f:
                                    users = [line.strip() for line in f if line.strip()]
                                last_users = users[-5:]
                                if last_users:
                                    reply_text = f"👥 *Últimos {len(last_users)} usuarios registrados:*\n" + "\n".join([f"- `{u}`" for u in last_users])
                                else:
                                    reply_text = "📭 No hay usuarios registrados."
                            else:
                                reply_text = "📭 No hay archivo de usuarios aún."

                        elif msg_logic.startswith("/modo"):
                            mode = msg_logic.split(" ", 1)[1].lower().strip() if " " in msg_logic else ""
                            if mode in PERSONAS:
                                set_persona(mode)
                                reply_text = f"🎭 *Modo cambiado a:* {mode.capitalize()}\n\n_{PERSONAS[mode]}_"
                            else:
                                opts = ", ".join([f"`{k}`" for k in PERSONAS.keys()])
                                reply_text = (
                                    "⚠️ Modo no reconocido.\n"
                                    f"Opciones disponibles: {opts}\n"
                                    "Uso: /modo [opcion]"
                                )

                        elif msg_logic.startswith("/reiniciar") or msg_logic.startswith("/reset"):
                            print("   🔄 Reiniciando sesión...")
                            # 1. Borrar historial de chat
                            run_tool("chat_with_llm.py", ["--prompt", "/clear"])
                        
                            # 2. Resetear personalidad
                            set_persona("default")
                        
                            reply_text = "🔄 *Sistema reiniciado.*\n\n- Historial de conversación borrado.\n- Personalidad restablecida a 'Default'."

                        elif msg_logic.startswith("/rol") or msg_logic.startswith("/role"):
                            parts = msg_logic.split(" ", 1)
                            if len(parts) < 2:
                                current_role = get_role(sender_id)
                                reply_text = f"👤 Tu rol actual es: *{current_role.upper()}*.\n\nPara cambiarlo, usa:\n/rol agronomo\n/rol productor"
                            else:
                                new_role = parts[1].lower().strip()
                                if new_role in ["medico", "médico", "doctor", "agronomo", "agrónomo"]:
                                    set_role(sender_id, "agronomo")
                                    reply_text = "👨‍🌾 *Rol actualizado a AGRÓNOMO.*\nAhora tienes acceso a sensores, cámaras y gestión de cultivos."
                                elif new_role in ["paciente", "usuario", "productor", "agricultor"]:
                                    set_role(sender_id, "productor")
                                    reply_text = "👤 *Rol actualizado a PRODUCTOR.*\nRecibirás alertas y reportes de tus cultivos."
                                else:
                                    reply_text = "⚠️ Rol no reconocido. Usa `agronomo` o `productor`."

                        elif msg_logic.startswith("/foto") or msg_logic.startswith("/camara") or msg_logic.startswith("/photo"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ *Acceso Denegado:* Solo personal técnico puede acceder a la cámara."
                            else:
                                # Detectar si se pide flash automático (ej: /foto flash)
                                use_flash = "flash" in msg_logic.lower()
                                
                                cam_ip = os.getenv("ESP32_CAM_IP")
                                if not cam_ip:
                                    reply_text = "⚠️ Error de Configuración: La variable `ESP32_CAM_IP` no está definida en el archivo `.env`."
                                else:
                                    # 1. Encender Flash si se solicitó
                                    if use_flash:
                                        print(f"   💡 Encendiendo flash para la captura...")
                                        try:
                                            subprocess.run(["curl", f"http://{cam_ip}/flash?state=1", "--max-time", "1"], capture_output=True)
                                            time.sleep(1.0) # Esperar a que el sensor ajuste la exposición
                                        except: pass

                                    print(f"   📸 Solicitando foto a {cam_ip}...")
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", "📸 Capturando...", "--chat-id", sender_id])
                                    
                                    filename = f"cam_{int(time.time())}.jpg"
                                    local_path = os.path.join(".tmp", filename)
                                    
                                    # 2. Capturar
                                    res = run_tool("capture_image.py", ["--ip", cam_ip, "--output-file", local_path])
                                    
                                    # 3. Apagar Flash inmediatamente
                                    if use_flash:
                                        try:
                                            subprocess.run(["curl", f"http://{cam_ip}/flash?state=0", "--max-time", "1"], capture_output=True)
                                        except: pass

                                    if res and res.get("status") == "success":
                                        # Enviar foto
                                        caption = "Vista con Flash ⚡" if use_flash else "Vista en tiempo real"
                                        run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", local_path, "--chat-id", sender_id, "--caption", caption])
                                        
                                        # Analizar la imagen capturada automáticamente
                                        run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando la imagen capturada...", "--chat-id", sender_id])
                                        
                                        analysis_prompt = "Actúa como un Ingeniero Agrónomo. Analiza esta imagen del cultivo. Busca signos de plagas (insectos, manchas), enfermedades (hongos, necrosis) o deficiencias nutricionales (hojas amarillas). Si todo se ve bien, indícalo."
                                        
                                        analysis_res = run_tool("analyze_image.py", ["--image", local_path, "--prompt", analysis_prompt])
                                        
                                        if analysis_res and analysis_res.get("status") == "success":
                                            analysis_text = f"👁️ *Análisis Visual:*\n{analysis_res.get('description')}"
                                            run_tool("telegram_tool.py", ["--action", "send", "--message", analysis_text, "--chat-id", sender_id])
                                        else:
                                            err = analysis_res.get("message", "Error desconocido") if analysis_res else "Falló el script de análisis."
                                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"❌ No se pudo analizar la imagen: {err}", "--chat-id", sender_id])

                                        reply_text = "" # Ya se enviaron las respuestas, no se necesita una final.
                                    else:
                                        err = res.get("message", "Error desconocido") if res else "No se pudo conectar con la cámara."
                                        reply_text = f"❌ Error al capturar imagen: {err}\n\nVerifique que la ESP32-CAM esté encendida y conectada al WiFi."

                        elif msg_logic.startswith("/captura"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ *Acceso Denegado:* Solo personal técnico puede acceder a la cámara."
                            else:
                                use_flash = "flash" in msg_logic.lower()
                                
                                cam_ip = os.getenv("ESP32_CAM_IP")
                                if not cam_ip:
                                    reply_text = "⚠️ Error de Configuración: La variable `ESP32_CAM_IP` no está definida en el archivo `.env`."
                                else:
                                    # 1. Encender Flash si se solicitó
                                    if use_flash:
                                        print(f"   💡 Encendiendo flash para la captura...")
                                        try:
                                            subprocess.run(["curl", f"http://{cam_ip}/flash?state=1", "--max-time", "1"], capture_output=True)
                                            time.sleep(1.0) # Esperar a que el sensor ajuste la exposición
                                        except: pass

                                    print(f"   📸 Solicitando captura simple a {cam_ip}...")
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", "📷 Capturando (sin análisis)...", "--chat-id", sender_id])
                                    
                                    filename = f"capture_{int(time.time())}.jpg"
                                    local_path = os.path.join(".tmp", filename)
                                    
                                    res = run_tool("capture_image.py", ["--ip", cam_ip, "--output-file", local_path])
                                    
                                    if use_flash:
                                        try:
                                            subprocess.run(["curl", f"http://{cam_ip}/flash?state=0", "--max-time", "1"], capture_output=True)
                                        except: pass

                                    if res and res.get("status") == "success":
                                        caption = "Captura Rápida (con Flash) ⚡" if use_flash else "Captura Rápida"
                                        run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", local_path, "--chat-id", sender_id, "--caption", caption])
                                        reply_text = "" # No más mensajes
                                    else:
                                        err = res.get("message", "Error desconocido") if res else "No se pudo conectar con la cámara."
                                        reply_text = f"❌ Error al capturar imagen: {err}"

                        elif msg_logic.startswith("/flash") or msg_logic.startswith("/luz"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ *Acceso Denegado:* Solo personal técnico puede controlar la iluminación."
                            else:
                                # Normalizar para soportar /flash_on y /flash on
                                normalized_msg = msg_logic.lower().replace("_", " ")
                                parts = normalized_msg.split(" ")
                                # Detectar si se pide encender (on, 1) o apagar (cualquier otra cosa)
                                state = "1" if len(parts) > 1 and parts[1] in ["on", "encender", "1"] else "0"
                                
                                cam_ip = os.getenv("ESP32_CAM_IP")
                                if not cam_ip:
                                    reply_text = "⚠️ Error: La IP de la cámara no está configurada en .env"
                                else:
                                    print(f"   💡 Cambiando estado del flash a {state}...")
                                    try:
                                        subprocess.run(["curl", f"http://{cam_ip}/flash?state={state}", "--max-time", "3"], capture_output=True)
                                        status_text = "ENCENDIDO" if state == "1" else "APAGADO"
                                        reply_text = f"💡 *Flash {status_text}*"
                                    except Exception as e:
                                        reply_text = f"❌ Error al controlar el flash: {e}"

                        elif msg_logic.startswith("/vigilancia"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Solo agrónomos pueden activar la vigilancia."
                            else:
                                parts = msg_logic.split(" ")
                                state = parts[1].lower() if len(parts) > 1 else ""
                                if state == "on":
                                    save_surveillance({"active": True, "last_check": 0, "chat_id": str(sender_id)})
                                    reply_text = "🛡️ *Modo Vigilancia ACTIVADO*\n\nRevisaré la cámara cada 5 minutos y te avisaré si detecto algo inusual."
                                elif state == "off":
                                    save_surveillance({"active": False, "last_check": 0, "chat_id": ""})
                                    reply_text = "🛡️ *Modo Vigilancia DESACTIVADO*."
                                else:
                                    reply_text = "⚠️ Uso: /vigilancia on o /vigilancia off"

                        elif msg_logic.startswith("/cultivos") or msg_logic.startswith("/monitorear"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ *Acceso Denegado:* Comando exclusivo para agrónomos."
                            else:
                                crops = load_crops()
                                parts = msg_logic.split(" ", 1)
                                
                                if len(parts) < 2:
                                    # Mostrar resumen de todos
                                    if not crops:
                                        reply_text = "🌱 No hay cultivos registrados en el sistema."
                                    else:
                                        reply_text = "📡 *Cultivos Activos:*\n\n"
                                        for cid, c in crops.items():
                                            status = "🟢 Estable"
                                            if c['humidity'] < 30 or c.get('pest_detected'): status = "🔴 Alerta"
                                            reply_text += f"🌿 *{c.get('name')}* (`{cid}`)\n   Estado: {status} | Humedad: {c['humidity']}% | Temp: {c['temperature']}°C\n\n"
                                        reply_text += "Usa /monitorear [ID] para ver detalles."
                                else:
                                    # Mostrar detalle de uno
                                    cid = parts[1].strip()
                                    if cid in crops:
                                        stats = crops[cid]
                                        reply_text = (
                                            f"📡 *Telemetría: {stats.get('name')} ({cid})*\n\n"
                                            f"💧 *Humedad Suelo:* {stats.get('humidity')}% (Ideal: 60%)\n"
                                            f"🌡️ *Temperatura:* {stats.get('temperature')}°C\n"
                                            f"🧪 *pH Suelo:* {stats.get('ph')}\n"
                                            f"🐛 *Plagas:* {'DETECTADA ⚠️' if stats.get('pest_detected') else 'Ninguna'}\n"
                                            f"_Última actualización: Hace {int(time.time() - stats.get('last_update', 0))}s_"
                                        )
                                    else:
                                        reply_text = f"❌ Cultivo `{cid}` no encontrado."

                        elif msg_logic.startswith("/simular_plaga"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Solo agrónomos pueden ejecutar simulaciones."
                            else:
                                crops = load_crops()
                                parts = msg_logic.split(" ", 1)
                                cid = parts[1].strip() if len(parts) > 1 else "CULT-001"
                                
                                if cid in crops:
                                    crops[cid]["pest_detected"] = "Pulgón (Simulado)"
                                    crops[cid]["humidity"] = 25.0 # Simular sequía también
                                    crops[cid]["last_alert"] = 0
                                    save_crops(crops)
                                    reply_text = f"⚠️ *Simulación Iniciada para {crops[cid]['name']}*: Plaga detectada y estrés hídrico."
                                else:
                                    reply_text = f"❌ Cultivo `{cid}` no encontrado. Usa /cultivos para ver IDs."

                        elif msg_logic.startswith("/tratamiento") or msg_logic.startswith("/regar"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Solo agrónomos pueden aplicar tratamientos."
                            else:
                                crops = load_crops()
                                parts = msg_logic.split(" ", 1)
                                cid = parts[1].strip() if len(parts) > 1 else "CULT-001"
                                
                                if cid in crops:
                                    crops[cid]["humidity"] = 60.0
                                    crops[cid]["temperature"] = 25.0
                                    crops[cid]["ph"] = 6.5
                                    crops[cid]["pest_detected"] = None
                                    save_crops(crops)
                                    reply_text = f"✅ *{crops[cid]['name']} Tratado*: Riego aplicado y plagas controladas."
                                else:
                                    reply_text = f"❌ Cultivo `{cid}` no encontrado."

                        elif msg_logic.startswith("/cultivo_reset"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Solo agrónomos pueden resetear sensores."
                            else:
                                crops = load_crops()
                                parts = msg_logic.split(" ", 1)
                                cid = parts[1].strip() if len(parts) > 1 else "CULT-001"
                                
                                if cid in crops:
                                    crops[cid]["humidity"] = 60.0
                                    crops[cid]["last_alert"] = 0
                                    save_crops(crops)
                                    reply_text = f"🔄 *Sensores de {crops[cid]['name']} Reseteados*."
                                else:
                                    reply_text = f"❌ Cultivo `{cid}` no encontrado."

                        elif msg_logic.startswith("/historial_alertas") or msg_logic.startswith("/alert_history"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Acceso denegado."
                            else:
                                if os.path.exists(ALERTS_LOG_FILE):
                                    with open(ALERTS_LOG_FILE, 'r') as f:
                                        lines = f.readlines()
                                    # Mostrar las últimas 10 alertas
                                    last_alerts = lines[-10:]
                                    if last_alerts:
                                        reply_text = "📋 *Historial de Alertas Recientes:*\n\n" + "".join(last_alerts)
                                    else:
                                        reply_text = "📋 El historial de alertas está vacío."
                                else:
                                    reply_text = "📋 No hay alertas registradas aún."

                        elif msg_logic.startswith("/nuevo_cultivo"):
                            if get_role(sender_id) != "agronomo":
                                reply_text = "⛔ Solo agrónomos pueden registrar cultivos."
                            else:
                                crops = load_crops()
                                args = msg_logic.split(" ", 1)
                                
                                if len(args) < 2:
                                    reply_text = "⚠️ Uso: /nuevo_cultivo [Nombre/Variedad]"
                                else:
                                    content = args[1].strip()
                                    
                                    # Detectar si el primer término es un ID manual (ej: SIM-005)
                                    first_word = content.split(" ")[0]
                                    if first_word.upper().startswith("CULT-") and " " in content:
                                        new_id = first_word.upper()
                                        new_name = content.split(" ", 1)[1].strip()
                                    else:
                                        # Generar ID automático (CULT-XXX)
                                        max_n = 0
                                        for cid in crops:
                                            if cid.startswith("CULT-"):
                                                try:
                                                    n = int(cid.split("-")[1])
                                                    if n > max_n: max_n = n
                                                except: pass
                                        new_id = f"CULT-{max_n + 1:03d}"
                                        new_name = content

                                    if new_id in crops:
                                        reply_text = f"⚠️ El cultivo con ID `{new_id}` ya existe."
                                    else:
                                        # Crear cultivo con valores por defecto
                                        crops[new_id] = { 
                                            "name": new_name, 
                                            "humidity": 60.0, 
                                            "temperature": 25.0, 
                                            "ph": 6.5, 
                                            "pest_detected": None,
                                            "last_update": time.time(), 
                                            "last_alert": 0 
                                        }
                                        save_crops(crops)
                                        reply_text = f"✅ *Cultivo Registrado*\n\n🌿 Nombre: {new_name}\n🆔 ID: `{new_id}`\n\nSensores activos."

                        elif msg_logic.startswith("/ayuda") or msg_logic.startswith("/help"):
                            role = get_role(sender_id)
                            
                            if role == "agronomo":
                                reply_text = (
                                    "👨‍🌾 *Panel de Control Agronómico:*\n\n"
                                    "*Monitoreo y Vigilancia:*\n"
                                    "📡 /monitorear [ID]: Ver estado de sensores del cultivo.\n"
                                    "📸 /foto [flash]: Captura y *analiza* la imagen con IA.\n"
                                    "📷 /captura [flash]: Toma una foto rápida (sin análisis).\n"
                                    "💡 /flash [on/off]: Controlar la luz de la cámara.\n"
                                    "🛡️ /vigilancia [on/off]: Activar/desactivar monitoreo automático.\n"
                                    "📋 /historial_alertas: Ver registro de crisis pasadas.\n\n"
                                    "*Gestión de Cultivos:*\n"
                                    "➕ /nuevo_cultivo [Nombre]: Registrar nueva parcela.\n"
                                    "🌱 /cultivos: Lista de cultivos activos.\n"
                                    "⚠️ /simular_plaga [ID]: Test de alertas.\n"
                                    "💉 /tratamiento [ID]: Aplicar riego/corrección.\n\n"
                                    "*Análisis y Reportes:*\n"
                                    " /reporte [tema]: Generar informe agronómico.\n"
                                    "🔍 /investigar [tema]: Búsqueda técnica avanzada.\n"
                                    "📄 /resumir_archivo [pdf]: Analizar ficha técnica.\n\n"
                                    "*Sistema:*\n"
                                    "⚙️ /status: Estado del servidor.\n"
                                    "👤 /rol productor: Cambiar a vista de productor.\n"
                                )
                            else:
                                reply_text = (
                                    "🤖 *Asistente de Productor:*\n\n"
                                    "📅 /cita [fecha]: Agendar visita técnica.\n"
                                    "🗓️ /mis_citas: Ver visitas agendadas.\n"
                                    "⏰ /recordatorio: Configurar recordatorio de tareas.\n"
                                    "📘 /ayuda_agro: Ver manual de uso.\n"
                                    "️ *Notas de voz*: Puedes hablarme para consultas.\n"
                                    "👨‍🌾 /rol agronomo: (Solo personal autorizado).\n"
                                )
                    
                        elif msg_logic.startswith("/py "):
                            code_to_run = msg_logic.split(" ", 1)[1].strip()
                            print(f"   🐍 Ejecutando en Sandbox: {code_to_run}")

                            res = run_tool("run_sandbox.py", ["--code", code_to_run])

                            reply_text = "" # Resetear
                            if res and res.get("status") == "success":
                                stdout = res.get("stdout", "")
                                stderr = res.get("stderr", "")
                            
                                # --- Manejo de Salida de Archivos ---
                                sent_file = False
                                clean_stdout_lines = []
                                if stdout:
                                    for line in stdout.splitlines():
                                        potential_path_in_container = line.strip()
                                        if potential_path_in_container.startswith('/mnt/out/'):
                                            filename = os.path.basename(potential_path_in_container)
                                            local_path = os.path.join(".tmp", filename)
                                            if os.path.exists(local_path):
                                                print(f"   🖼️  Detectado archivo de salida: {local_path}. Enviando...")
                                                run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", local_path, "--chat-id", sender_id, "--caption", "Archivo generado por el Sandbox."])
                                                sent_file = True
                                                continue # No añadir esta línea a la respuesta de texto
                                        clean_stdout_lines.append(line)
                            
                                clean_stdout = "\n".join(clean_stdout_lines)

                                # --- Manejo de Salida de Texto ---
                                text_output_exists = clean_stdout or stderr
                                if text_output_exists:
                                    reply_text = "📦 *Resultado del Sandbox:*\n\n"
                                    if clean_stdout:
                                        reply_text += f"*Salida:*\n```\n{clean_stdout}\n```\n"
                                    if stderr:
                                        reply_text += f"*Errores:*\n```\n{stderr}\n```\n"
                                elif not sent_file: # No hay salida de texto Y no se envió archivo
                                    reply_text = "📦 *Resultado del Sandbox:*\n\n_El código se ejecutó sin producir salida._"
                            else:
                                reply_text = f"❌ *Error en Sandbox:*\n{res.get('message', 'Error desconocido.')}"

                        elif msg_logic.lower().strip() in ["hola", "hola!", "hi", "hello", "/start"]:
                            role = get_role(sender_id)
                            if role == "agronomo":
                                reply_text = "👨‍🌾 *Bienvenido, Ingeniero.*\n\nEl sistema de Agro-Inteligencia está activo. Use `/monitorear` para ver el estado de los cultivos o `/ayuda` para ver las herramientas profesionales."
                            else:
                                reply_text = """👋 ¡Hola! Soy tu Asistente de Agro-Inteligencia.

    Estoy aquí para ayudarte a gestionar tus cultivos y responder tus consultas técnicas.

    Puedes interactuar conmigo de varias formas:
    - Envíame un análisis de suelo en PDF para que lo revise.
    - Pídeme un reporte sobre un cultivo o plaga con /reporte [tema].
    - Usa /ayuda para ver todos los comandos disponibles."""

                        elif msg_logic.lower().strip() in ["gracias", "gracias!", "thanks", "thank you"]:
                            reply_text = "¡De nada! Estoy aquí para ayudar. 🤖"

                        # --- CHAT GENERAL (Capa 2: Orquestación) ---
                        elif not reply_text: # Solo si no se ha generado respuesta por un comando anterior
                            # Estrategia Directa con RAG:
                            # Enviamos el mensaje al LLM. El script chat_with_llm.py se encarga de
                            # buscar en la memoria e inyectar el contexto si es relevante.
                            print("   🤔 Consultando al Agente (con memoria)...")
                            current_sys = get_current_persona()
                        
                            # Inyectar fecha y hora actual para que el LLM lo sepa
                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            current_sys += f"\n[Contexto Temporal: Fecha y Hora actual del servidor: {now_str}]"

                            # Si la interacción fue por voz, instruir al LLM que responda en ese idioma
                            if is_voice_interaction and voice_lang_short != "es":
                                current_sys += f"\nIMPORTANT: The user is speaking in '{voice_lang_short}'. You MUST respond in '{voice_lang_short}', regardless of your default instructions."

                            llm_response = run_tool("chat_with_llm.py", ["--prompt", msg_logic, "--system", current_sys])
                        
                            if llm_response and "content" in llm_response:
                                reply_text = llm_response["content"]
                            else:
                                error_msg = llm_response.get('error', 'Respuesta vacía') if llm_response else "Error desconocido"
                                reply_text = f"⚠️ Error del Modelo: {error_msg}"
                    
                        # 3. Enviar respuesta a Telegram
                        if reply_text:
                            print(f"   📤 Enviando respuesta: '{reply_text[:60]}...'")
                            res = run_tool("telegram_tool.py", ["--action", "send", "--message", reply_text, "--chat-id", sender_id])
                            if res and res.get("status") == "error":
                                print(f"   ❌ Error al enviar mensaje: {res.get('message')}")
                        
                            # 4. Si fue interacción por voz, enviar también audio
                            if is_voice_interaction and reply_text:
                                print("   🗣️ Generando respuesta de voz...")
                                audio_path = os.path.join(".tmp", f"reply_{int(time.time())}.ogg")
                                # Generar audio
                                tts_res = run_tool("text_to_speech.py", ["--text", reply_text[:500], "--output", audio_path, "--lang", voice_lang_short]) # Limitamos a 500 chars para no hacerlo eterno
                                if tts_res and tts_res.get("status") == "success":
                                    run_tool("telegram_tool.py", ["--action", "send-voice", "--file-path", audio_path, "--chat-id", sender_id])
                    
                    except Exception as e:
                        print(f"❌❌❌ ERROR CRÍTICO PROCESANDO MENSAJE: {msg} ❌❌❌")
                        print(f"   Error: {e}")
                        traceback.print_exc()
                        try:
                            # Intentar notificar al usuario del error
                            error_reply = "🤖 ¡Ups! Ocurrió un error inesperado al procesar tu último mensaje. El administrador ha sido notificado."
                            run_tool("telegram_tool.py", ["--action", "send", "--message", error_reply, "--chat-id", sender_id])
                        except:
                            pass # Si incluso el envío de error falla, no hacer nada para no entrar en un bucle de errores.
            
            # --- TAREA DE FONDO: RECORDATORIOS ---
            check_reminders()
            check_appointments()
            check_surveillance()
            simulate_and_monitor_crops()

            # --- TAREA DE FONDO: MONITOREO PROACTIVO ---
            if time.time() - last_health_check > HEALTH_CHECK_INTERVAL:
                last_health_check = time.time()
                # Solo el admin (CHAT_ID del .env) recibe alertas técnicas
                admin_id = os.getenv("TELEGRAM_CHAT_ID")
                if admin_id:
                    res = run_tool("monitor_resources.py", [])
                    if res and res.get("alerts"):
                        alerts = res.get("alerts", [])
                        alert_msg = "🚨 *ALERTA DEL SISTEMA:*\n\n" + "\n".join([f"- {a}" for a in alerts])
                        print(f"   ⚠️ Detectada alerta de sistema. Notificando a {admin_id}...")
                        run_tool("telegram_tool.py", ["--action", "send", "--message", alert_msg, "--chat-id", admin_id])
            
            # Esperar un poco antes del siguiente chequeo para no saturar la CPU/API
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Desconectando servicio de Telegram.")

if __name__ == "__main__":
    main()