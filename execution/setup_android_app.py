#!/usr/bin/env python3
import os
import stat
import sys
import shutil
import json

try:
    from PIL import Image
except ImportError:
    print("❌ Error: La librería 'Pillow' es necesaria para procesar imágenes.")
    print("   Por favor, instálala ejecutando: pip install Pillow")
    sys.exit(1)

# --- CONFIGURACIÓN ---
APP_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "APP-ANDROID", "mi-primera-app")
HF_URL = "https://cero2k6-agente-agro-inteligente.hf.space"
# ---------------------

def find_file(name, search_path):
    for root, dirs, files in os.walk(search_path):
        if name in files:
            return os.path.join(root, name)
    return None

def ensure_project_structure(root_path):
    """Verifica y crea los archivos de Gradle necesarios si no existen."""
    print("🔎 Verificando estructura del proyecto Android...")
    gradlew_path = os.path.join(root_path, "gradlew")
    
    if os.path.exists(gradlew_path):
        print("   ✅ Estructura del proyecto parece completa.")
        return

    print("   ⚠️ Estructura incompleta. Creando archivos de Gradle faltantes...")

    # --- Contenido de los archivos estándar de Gradle ---
    
    # settings.gradle
    settings_gradle_content = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "MiPrimeraApp"
include ':app'
"""

    # build.gradle (nivel raíz)
    build_gradle_content = """// Top-level build file
plugins {
    id 'com.android.application' version '8.0.0' apply false
    id 'com.android.library' version '8.0.0' apply false
    id 'org.jetbrains.kotlin.android' version '1.8.20' apply false
}
"""

    # gradle/wrapper/gradle-wrapper.properties
    wrapper_properties_content = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.0-bin.zip
"""

    # gradlew (script para Linux/macOS)
    # Es un script largo, lo incluimos como un string multi-línea.
    gradlew_content = r'''#!/usr/bin/env sh

set -e

warn () {
    echo "$*"
}

die () {
    echo
    echo "$*"
    echo
    exit 1
}

DEFAULT_JVM_OPTS='"-Xmx64m" "-Xms64m"'

APP_NAME="Gradle"
APP_BASE_NAME=`basename "$0"`

APP_HOME=`cd \`dirname "$0"\` && pwd`

if [ -z "$JAVA_HOME" ] && [ -d /usr/lib/jvm/default-java ]; then
    export JAVA_HOME=/usr/lib/jvm/default-java
fi

if [ -z "$JAVA_HOME" ] ; then
    JAVA_EXE_PATH=`which java`
    if [ "x$JAVA_EXE_PATH" != "x" ] ; then
        export JAVA_HOME=`dirname \`dirname \`readlink -f "$JAVA_EXE_PATH"\`\``
    fi
fi

if [ -z "$JAVA_HOME" ] ; then
    die "ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH."
fi

JAVACMD="$JAVA_HOME/bin/java"

if [ ! -x "$JAVACMD" ] ; then
    die "ERROR: JAVA_HOME is not defined correctly. We cannot execute $JAVACMD"
fi

CLASSPATH="$APP_HOME/gradle/wrapper/gradle-wrapper.jar"

eval exec "\"$JAVACMD\"" $DEFAULT_JVM_OPTS $JVM_OPTS -classpath "\"$CLASSPATH\"" org.gradle.wrapper.GradleWrapperMain "$@"
'''

    # --- Creación de archivos y directorios ---
    try:
        # Crear gradlew y darle permisos de ejecución
        with open(gradlew_path, 'w') as f: f.write(gradlew_content)
        os.chmod(gradlew_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        print("      -> Creado 'gradlew' (script de compilación)")

        # Crear settings.gradle
        with open(os.path.join(root_path, 'settings.gradle'), 'w') as f: f.write(settings_gradle_content)
        print("      -> Creado 'settings.gradle'")

        # Crear build.gradle
        with open(os.path.join(root_path, 'build.gradle'), 'w') as f: f.write(build_gradle_content)
        print("      -> Creado 'build.gradle'")

        # Crear directorio y archivo de propiedades del wrapper
        wrapper_dir = os.path.join(root_path, 'gradle', 'wrapper')
        os.makedirs(wrapper_dir, exist_ok=True)
        with open(os.path.join(wrapper_dir, 'gradle-wrapper.properties'), 'w') as f: f.write(wrapper_properties_content)
        print("      -> Creado 'gradle/wrapper/gradle-wrapper.properties'")
        
        print("   ✅ Estructura de proyecto reparada.")

    except Exception as e:
        print(f"   ❌ Error fatal creando la estructura del proyecto: {e}")
        sys.exit(1)

def ensure_app_build_gradle(app_path):
    """Crea un build.gradle para el módulo app si no existe."""
    build_gradle_path = os.path.join(app_path, "build.gradle")
    if os.path.exists(build_gradle_path):
        return

    print("   ⚠️ No se encontró app/build.gradle. Creando uno básico...")
    
    # Intentar adivinar el namespace del AndroidManifest si existe
    namespace = "com.example.agroapp"
    manifest = find_file("AndroidManifest.xml", app_path)
    if manifest:
        try:
            with open(manifest, 'r') as f:
                for line in f:
                    if 'package="' in line:
                        namespace = line.split('package="')[1].split('"')[0]
                        break
        except: pass

    content = f"""plugins {{
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}}

android {{
    namespace '{namespace}'
    compileSdk 33

    defaultConfig {{
        applicationId "{namespace}"
        minSdk 24
        targetSdk 33
        versionCode 1
        versionName "1.0"
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
    kotlinOptions {{
        jvmTarget = '1.8'
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.8.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.5.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}}
"""
    with open(build_gradle_path, 'w') as f:
        f.write(content)
    print("      -> Creado 'app/build.gradle'")

def patch_gradle(gradle_path):
    print(f"🔧 Parcheando dependencias en: {gradle_path}")
    with open(gradle_path, 'r') as f:
        content = f.read()
    
    # Dependencias necesarias
    deps = [
        "implementation 'com.squareup.retrofit2:retrofit:2.9.0'",
        "implementation 'com.squareup.retrofit2:converter-gson:2.9.0'",
        "implementation 'com.squareup.okhttp3:logging-interceptor:4.9.0'",
        "implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.6.4'",
        "implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.6.1'"
    ]
    
    if "retrofit2" in content:
        print("   ✅ Las dependencias ya parecen estar instaladas.")
        return

    # Insertar dependencias
    if "dependencies {" in content:
        new_deps_str = "\n    ".join(deps)
        new_content = content.replace("dependencies {", f"dependencies {{\n    {new_deps_str}")
        with open(gradle_path, 'w') as f:
            f.write(new_content)
        print("   ✅ Dependencias agregadas correctamente.")
    else:
        print("   ❌ Error: No se encontró el bloque 'dependencies {' en build.gradle.")

def patch_manifest(manifest_path):
    print(f"🔧 Verificando permisos en: {manifest_path}")
    with open(manifest_path, 'r') as f:
        content = f.read()
    
    perm = '<uses-permission android:name="android.permission.INTERNET" />'
    
    if "android.permission.INTERNET" in content:
        print("   ✅ Permiso de Internet ya existe.")
        return
        
    if "<application" in content:
        new_content = content.replace("<application", f"{perm}\n    <application")
        with open(manifest_path, 'w') as f:
            f.write(new_content)
        print("   ✅ Permiso de Internet agregado.")
    else:
        print("   ❌ Error: No se encontró el tag <application> en el Manifiesto.")

def rewrite_main_activity(activity_path):
    print(f"🔧 Reescribiendo lógica en: {activity_path}")
    with open(activity_path, 'r') as f:
        lines = f.readlines()
    
    # Preservar el nombre del paquete original
    package_line = next((line.strip() for line in lines if line.strip().startswith("package ")), None)
    
    if not package_line:
        print("   ❌ Error: No se encontró la declaración de 'package' en MainActivity.kt.")
        return

    # Código completo de la App Cliente
    new_code = f"""{package_line}

import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import okhttp3.RequestBody
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

// --- Definición de la API ---
interface ApiService {{
    @Multipart
    @POST("/chat")
    suspend fun chat(@Part("message") message: RequestBody): ChatResponse
}}

data class ChatResponse(val reply: String)

object RetrofitClient {{
    private const val BASE_URL = "{HF_URL}/"
    
    val api: ApiService by lazy {{
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }}
}}

// --- Interfaz de Usuario y Lógica ---
class MainActivity : AppCompatActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        
        // Construcción de UI Programática (Sin XML para evitar errores de recursos)
        val root = LinearLayout(this).apply {{ orientation = LinearLayout.VERTICAL; setPadding(32, 32, 32, 32) }}
        val chatLog = TextView(this).apply {{ text = "🤖 Agente Agro-Inteligente\\n\\n"; textSize = 16f }}
        val scroll = ScrollView(this).apply {{ layoutParams = LinearLayout.LayoutParams(-1, 0, 1f); addView(chatLog) }}
        val inputLayout = LinearLayout(this).apply {{ orientation = LinearLayout.HORIZONTAL; setPadding(0, 16, 0, 0) }}
        val input = EditText(this).apply {{ hint = "Consulta..."; layoutParams = LinearLayout.LayoutParams(0, -2, 1f) }}
        val btn = Button(this).apply {{ text = "Enviar" }}

        inputLayout.addView(input); inputLayout.addView(btn)
        root.addView(scroll); root.addView(inputLayout)
        setContentView(root)

        btn.setOnClickListener {{
            val msg = input.text.toString()
            if (msg.isNotBlank()) {{
                chatLog.append("🧑‍🌾 Tú: $msg\\n")
                input.text.clear()
                lifecycleScope.launch {{
                    try {{
                        chatLog.append("⏳ ...\\n")
                        val req = RequestBody.create("text/plain".toMediaTypeOrNull(), msg)
                        val res = RetrofitClient.api.chat(req)
                        chatLog.append("🤖: ${{res.reply}}\\n\\n")
                    }} catch (e: Exception) {{ chatLog.append("❌ Error: ${{e.message}}\\n") }}
                }}
            }}
        }}
    }}
}}
"""
    with open(activity_path, 'w') as f:
        f.write(new_code)
    print("   ✅ MainActivity actualizada con éxito.")

def fix_expo_config(project_path):
    print(f"🔧 Reparando configuración de Expo (app.json y eas.json) en: {project_path}")
    
    # 1. eas.json para generar APK
    eas_json_path = os.path.join(project_path, "eas.json")
    eas_content = """{
  "cli": {
    "version": ">= 7.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {}
  }
}"""
    with open(eas_json_path, 'w') as f:
        f.write(eas_content)
    print("   ✅ eas.json configurado para generar APK (preview) y AAB (production).")

    # 2. app.json con package name y logo
    app_json_path = os.path.join(project_path, "app.json")

    # --- Lógica para el logo ---
    # La ruta del script es .../execution/setup_android_app.py
    # La ruta del logo es .../docs/AGROBOT.png
    agent_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_src_path = os.path.join(agent_root, "docs", "AGROBOT.png")
    
    assets_dir = os.path.join(project_path, "assets")
    logo_dest_path = os.path.join(assets_dir, "icon.png")
    
    if os.path.exists(logo_src_path):
        os.makedirs(assets_dir, exist_ok=True)
        
        # --- Lógica para asegurar que el icono sea cuadrado ---
        with Image.open(logo_src_path) as img:
            width, height = img.size
            if width == height:
                # La imagen ya es cuadrada, solo copiar
                shutil.copy(logo_src_path, logo_dest_path)
                print(f"   🖼️  Logo cuadrado copiado a: {os.path.relpath(logo_dest_path)}")
            else:
                # La imagen no es cuadrada, crear un fondo cuadrado y centrarla
                print(f"   ⚠️  El logo no es cuadrado ({width}x{height}). Creando una versión cuadrada...")
                side_length = max(width, height)
                
                # Crear un nuevo lienzo cuadrado con fondo transparente
                new_img = Image.new('RGBA', (side_length, side_length), (0, 0, 0, 0))
                
                # Calcular la posición para centrar la imagen original
                paste_x = (side_length - width) // 2
                paste_y = (side_length - height) // 2
                
                # Pegar la imagen original en el lienzo (usando la imagen como máscara si tiene transparencia)
                new_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
                
                # Guardar la nueva imagen cuadrada
                new_img.save(logo_dest_path, 'PNG')
                print(f"   🖼️  Versión cuadrada del logo guardada en: {os.path.relpath(logo_dest_path)}")
        # --- Fin de la lógica del icono ---
    else:
        print(f"   ⚠️  No se encontró el logo en: {logo_src_path}")
    # --- Fin lógica del logo ---
    
    base_config = {}
    if os.path.exists(app_json_path):
        try:
            with open(app_json_path, 'r') as f:
                base_config = json.load(f)
        except: pass
    
    if "expo" not in base_config:
        base_config["expo"] = {}
    
    # Asegurar campos críticos
    base_config["expo"]["name"] = base_config["expo"].get("name", "Agro-Inteligente")
    base_config["expo"]["slug"] = base_config["expo"].get("slug", "mi-primera-app")
    base_config["expo"]["icon"] = "./assets/icon.png" # Referencia al icono
    
    if "android" not in base_config["expo"]:
        base_config["expo"]["android"] = {}
        
    # Establecer package name si no existe o es genérico
    current_pkg = base_config["expo"]["android"].get("package", "")
    if not current_pkg or "example" in current_pkg:
        base_config["expo"]["android"]["package"] = "com.agro.inteligente"

    with open(app_json_path, 'w') as f:
        json.dump(base_config, f, indent=2)
    print(f"   ✅ app.json actualizado (Package: {base_config['expo']['android'].get('package')}, Icono: {base_config['expo'].get('icon')})")

def cleanup_native_artifacts(root_path):
    """Elimina archivos de scaffolding de Android Nativo que pueden confundir a EAS Build."""
    print(f"🧹 Limpiando artefactos nativos en: {root_path}")
    files_to_delete = ["gradlew", "gradlew.bat", "settings.gradle", "build.gradle", "local.properties"]
    dirs_to_delete = ["gradle"]
    
    cleaned = False
    for filename in files_to_delete:
        path = os.path.join(root_path, filename)
        if os.path.exists(path):
            os.remove(path)
            print(f"   - Eliminado: {filename}")
            cleaned = True
            
    for dirname in dirs_to_delete:
        path = os.path.join(root_path, dirname)
        if os.path.exists(path) and os.path.isdir(path):
            shutil.rmtree(path)
            print(f"   - Eliminado directorio: {dirname}/")
            cleaned = True
    
    if not cleaned:
        print("   ✅ No se encontraron artefactos nativos para limpiar.")

def setup_react_native_app(project_path):
    # Limpiar artefactos de Android Nativo que pueden haber sido creados por error en ejecuciones anteriores
    # y que confunden a EAS Build. El path del proyecto es .../app, los artefactos están en el padre.
    parent_dir = os.path.dirname(project_path)
    cleanup_native_artifacts(parent_dir)

    print(f"🔧 Configurando App React Native en: {project_path}")
    
    # Detectar si es TypeScript
    is_ts = os.path.exists(os.path.join(project_path, "tsconfig.json"))
    
    # Identificar archivos objetivo (Expo Router vs Clásico)
    targets = []
    
    # 1. Expo Router (app/index.tsx o app/index.js) - Prioridad Alta
    expo_router_dir = os.path.join(project_path, "app")
    if os.path.exists(expo_router_dir) and os.path.isdir(expo_router_dir):
        targets.append(os.path.join(expo_router_dir, "index.tsx"))
        targets.append(os.path.join(expo_router_dir, "index.js"))
    
    # 2. Clásico (App.tsx o App.js en raíz)
    root_filename = "App.tsx" if is_ts else "App.js"
    targets.append(os.path.join(project_path, root_filename))
    
    # URL de la API
    api_url = "https://cero2k6-agente-agro-inteligente.hf.space/chat"
    
    # Contenido del App.js/tsx
    content = f"""import React, {{ useState, useRef }} from 'react';
import {{ StyleSheet, Text, View, TextInput, Button, ScrollView, KeyboardAvoidingView, Platform, ActivityIndicator, SafeAreaView }} from 'react-native';

// URL de tu Agente en Hugging Face
const HF_API_URL = "{api_url}";

export default function App() {{
  const [messages, setMessages] = useState([
    {{ sender: 'bot', text: '¡Hola! Soy tu asistente agrónomo. ¿En qué puedo ayudarte?' }}
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef(null);

  const handleSend = async () => {{
    if (input.trim() === '') return;

    const userMessage = {{ sender: 'user', text: input }};
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {{
      const formData = new FormData();
      formData.append('message', input);

      const response = await fetch(HF_API_URL, {{
        method: 'POST',
        body: formData,
      }});

      if (!response.ok) {{
        throw new Error(`Error del servidor: ${{response.status}}`);
      }}

      const data = await response.json();
      const botMessage = {{ sender: 'bot', text: data.reply || 'No he recibido respuesta.' }};
      setMessages(prev => [...prev, botMessage]);

    }} catch (error) {{
      const errorMessage = {{ sender: 'bot', text: `❌ Error: ${{error.message}}` }};
      setMessages(prev => [...prev, errorMessage]);
    }} finally {{
      setIsLoading(false);
    }}
  }};

  return (
    <SafeAreaView style={{styles.container}}>
      <View style={{styles.header}}>
        <Text style={{styles.title}}>Agro-Inteligente</Text>
      </View>
      <KeyboardAvoidingView 
        style={{styles.keyboardView}}
        behavior={{Platform.OS === "ios" ? "padding" : "height"}}
      >
        <ScrollView 
          style={{styles.chatBox}}
          ref={{scrollViewRef}}
          onContentSizeChange={{() => scrollViewRef.current?.scrollToEnd({{ animated: true }})}}
        >
          {{messages.map((msg, index) => (
            <View key={{index}} style={{[styles.messageBubble, msg.sender === 'user' ? styles.userBubble : styles.botBubble]}}>
              <Text style={{msg.sender === 'user' ? styles.userText : styles.botText}}>{{msg.text}}</Text>
            </View>
          ))}}
          {{isLoading && <ActivityIndicator style={{styles.loadingIndicator}} size="small" color="#666" />}}
        </ScrollView>
        <View style={{styles.inputArea}}>
          <TextInput style={{styles.input}} value={{input}} onChangeText={{setInput}} placeholder="Consulta..." editable={{!isLoading}} />
          <Button title="Enviar" onPress={{handleSend}} disabled={{isLoading}} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{ container: {{ flex: 1, backgroundColor: '#f5f5f5' }}, header: {{ padding: 20, backgroundColor: 'white', alignItems: 'center', marginTop: 25 }}, title: {{ fontSize: 20, fontWeight: 'bold' }}, keyboardView: {{ flex: 1 }}, chatBox: {{ flex: 1, padding: 10 }}, messageBubble: {{ padding: 10, borderRadius: 10, marginBottom: 10, maxWidth: '80%' }}, userBubble: {{ backgroundColor: '#007bff', alignSelf: 'flex-end' }}, botBubble: {{ backgroundColor: 'white', alignSelf: 'flex-start' }}, userText: {{ color: 'white' }}, botText: {{ color: 'black' }}, inputArea: {{ flexDirection: 'row', padding: 10, backgroundColor: 'white' }}, input: {{ flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 20, paddingHorizontal: 15, marginRight: 10, height: 40 }}, loadingIndicator: {{ margin: 10 }} }});
"""
    
    written = False
    for target in targets:
        # Sobrescribir si existe, o si es el archivo raíz por defecto
        if os.path.exists(target) or target.endswith(root_filename):
            with open(target, 'w') as f:
                f.write(content)
            print(f"   ✅ Archivo actualizado: {target}")
            written = True
            
    print("   🚀 ¡Tu App ahora está conectada al Agente!")
    
    # Reparar configuración de build
    fix_expo_config(project_path)

def main():
    if not os.path.exists(APP_ROOT):
        print(f"❌ No encuentro la carpeta: {{APP_ROOT}}")
        print("Asegúrate de haber copiado la carpeta 'mi-primera-app' dentro de '.tmp/APP-ANDROID/'")
        return

    # --- NUEVA VALIDACIÓN DE TIPO DE PROYECTO ---
    # Verificar si es React Native (en raíz o en subcarpeta app/)
    if os.path.exists(os.path.join(APP_ROOT, "package.json")):
        setup_react_native_app(APP_ROOT)
        return
    elif os.path.exists(os.path.join(APP_ROOT, "app", "package.json")):
        setup_react_native_app(os.path.join(APP_ROOT, "app"))
        return
    # --- FIN DE LA VALIDACIÓN ---

    # --- Reestructuración Automática ---
    app_module_path = os.path.join(APP_ROOT, "app")
    
    # Buscar AndroidManifest.xml para determinar dónde está el código realmente
    manifest_candidate = find_file("AndroidManifest.xml", APP_ROOT)
    
    # Si encontramos un manifiesto y NO está dentro de la carpeta 'app' (o 'app' no existe aún)
    if manifest_candidate and (not os.path.exists(app_module_path) or not manifest_candidate.startswith(app_module_path)):
        print("   ℹ️ Estructura plana detectada (Manifest en raíz). Reorganizando...")
        
        temp_dir = os.path.join(APP_ROOT, "__temp_app_module__")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Mover todo excepto archivos de sistema/gradle root
        ignore_list = [".git", ".gradle", "gradle", "build", "gradlew", "gradlew.bat", "settings.gradle", "local.properties", "__temp_app_module__", "app"]
        moved_items = []
        for item_name in os.listdir(APP_ROOT):
            if item_name in ignore_list:
                continue
            shutil.move(os.path.join(APP_ROOT, item_name), os.path.join(temp_dir, item_name))
            moved_items.append(item_name)
        
        # Renombrar la carpeta temporal a 'app'
        if os.path.exists(app_module_path): shutil.rmtree(app_module_path)
        os.rename(temp_dir, app_module_path)
        print(f"   ✅ Contenido del módulo ({', '.join(moved_items)}) movido a la subcarpeta 'app/'.")

    print(f"📂 Configurando proyecto en: {APP_ROOT}")
    
    # 0. Crear/Reparar la estructura de Gradle en la raíz del proyecto
    ensure_project_structure(APP_ROOT)

    # 0.1 Asegurar que exista app/build.gradle
    if not os.path.exists(app_module_path): os.makedirs(app_module_path, exist_ok=True)
    ensure_app_build_gradle(app_module_path)

    # 1. Buscar build.gradle del módulo app
    app_gradle = find_file("build.gradle", app_module_path)
    if app_gradle: patch_gradle(app_gradle)
    else: print("❌ No se encontró 'app/build.gradle'")

    # 2. Buscar y parchear AndroidManifest.xml
    manifest = find_file("AndroidManifest.xml", app_module_path)
    if manifest: patch_manifest(manifest)
    else: print("❌ No se encontró AndroidManifest.xml")

    # 3. Buscar y reescribir MainActivity.kt
    main_activity = find_file("MainActivity.kt", app_module_path)
    if main_activity: rewrite_main_activity(main_activity)
    else: print("❌ No se encontró MainActivity.kt")

    print("\n✨ Proceso finalizado. Ahora compila tu app.")

if __name__ == "__main__":
    main()