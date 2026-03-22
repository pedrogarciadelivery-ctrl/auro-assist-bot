# bot.py
# Telegram Bot (Python) - Auro Ashly Flex Master
# Mejorado para:
# - recibir texto
# - recibir audios / notas de voz
# - transcribir audios con OpenAI
# - procesar la transcripción igual que si fuera texto
# - guardar leads en archivo JSONL
# - seguir notificando al admin

import os
import re
import json
import time
import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logging.info("🤖 Bot iniciado (cargando código)")

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "+1 512 679 0599")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
AUDIO_TRANSCRIBE_MODEL = os.environ.get("AUDIO_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
LEADS_FILE = os.environ.get("LEADS_FILE", "leads.jsonl")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =========================
# TEXTOS
# =========================
WELCOME = (
    "Bienvenido(a).\n\n"
    "Soy el Asistente Virtual de la empresa Auro Ashly Flex Master.\n\n"
    "Estoy aquí para brindarle apoyo y orientación en nuestros servicios, "
    "así como para ayudarle a resolver sus consultas de manera clara y eficiente."
)

CHOOSE_SERVICE = "¿Con cuál servicio le podemos ayudar el día de hoy?"

AMAZON_CHOOSE_TYPE = (
    "Ha seleccionado el servicio Amazon Flex.\n\n"
    "Por favor, seleccione una opción:"
)

AMAZON_NEW_ACCOUNT_TEXT = (
    "Veo que ha seleccionado Cuenta Nueva ✅\n\n"
    "Aquí tiene todas las ciudades que tenemos disponibles.\n\n"
    "👉 Si alguna le interesa, puede tocarla y así nos lo hará saber."
)

AMAZON_REACT_REQUIREMENTS_TEXT = (
    "♻️ Reactivación – Amazon Flex\n\n"
    "Antes de continuar, confirme si cuenta con TODOS los requisitos:\n\n"
    "1) Licencia nueva (diferente a la que tenía cuando lo desactivaron en Amazon Flex).\n"
    "   • Aplica número de licencia diferente o licencia de otro estado.\n"
    "2) Licencia que tenía registrada en la cuenta desactivada.\n"
    "3) Correo de la cuenta desactivada.\n\n"
    "📍 Importante: También debo contar con disponibilidad en la ciudad donde desea la nueva cuenta.\n\n"
    "Si cumple con todo, escriba: CUMPLO\n"
    "Si NO cumple, escriba: NO CUMPLO"
)

AMAZON_REQUIREMENTS_TEXT = (
    "Para que el proceso sea viable, es indispensable cumplir con TODOS los requisitos siguientes:\n\n"
    "1) No puede tener ni haber tenido multas.\n"
    "2) No puede tener ni haber tenido antecedentes.\n"
    "3) No puede haber trabajado en almacenes de Amazon.\n"
    "4) No puede haber tenido accidentes.\n"
    "5) Debe ser mayor de 21 años.\n"
    "6) La licencia debe ser válida (no restringida).\n"
    "7) No puede haber tenido una aplicación/cuenta de Amazon activa en el pasado.\n\n"
    "📌 Importante: El pago se realiza por adelantado.\n"
    "Si cumple con todos los requisitos, le garantizo mi trabajo.\n"
    "Si NO los cumple, recomiendo NO iniciar el proceso.\n\n"
    "Si está de acuerdo y cumple con todo, por favor escriba: CUMPLO"
)

OWNER_CONTACT_TEXT = (
    "Perfecto ✅\n\n"
    "Si cumple con todos los requisitos y desea continuar con la aplicación, "
    "por favor comuníquese conmigo directamente por WhatsApp:\n\n"
    f"📞 WhatsApp: {WHATSAPP_NUMBER}\n\n"
    'Escriba por favor: "Hola, vengo del bot y cumplo con los requisitos".'
)

WHATSAPP_STATUS_TEXT = (
    "📌 Le recomendamos revisar con frecuencia nuestros Estados de WhatsApp, "
    "ya que ahí publicamos las ciudades disponibles en tiempo real.\n\n"
    f"📞 WhatsApp: {WHATSAPP_NUMBER}"
)

GOODBYE_TEXT = (
    "Entendido.\n\n"
    "Gracias por su tiempo y por haberse comunicado con nosotros.\n"
    "En este momento no continuaremos con el proceso, pero será un gusto atenderle en otra ocasión.\n\n"
    "Si en el futuro desea consultar nuevamente, puede comunicarse con nosotros cuando lo desee.\n\n"
    f"{WHATSAPP_STATUS_TEXT}\n\n"
    "Le deseamos un excelente día."
)

COMING_SOON_TEXT = (
    "✅ Servicio seleccionado.\n\n"
    "Este servicio se habilitará próximamente. Por ahora, por favor seleccione Amazon Flex."
)

INSTACART_INTRO_TEXT = (
    "✅ Veo que escogiste la opción de Instacart.\n\n"
    "Y ahí vamos con las preguntas importantes para poder saber qué hacer con este cliente.\n\n"
    "📌 Lo primero:\n"
    "¿Alguna vez aplicó y tiene una cuenta en lista de espera?\n\n"
)

INSTACART_WAITLIST_YES_TEXT = (
    "Entendido ✅\n\n"
    "Si ya aplicó y está en lista de espera, vamos a necesitar:\n"
    "• Otro correo electrónico\n"
    "• Otro número de teléfono (puede ser online)\n\n"
    "💰 Costo: $150\n\n"
    "¿Desea avanzar con la aplicación?"
)

INSTACART_WAITLIST_NO_TEXT = (
    "Perfecto ✅\n\n"
    "Si NO ha aplicado nunca, vamos a necesitar:\n"
    "• Número de teléfono\n"
    "• Correo electrónico NUNCA usado en Instacart\n\n"
    "💰 Costo: $150\n\n"
    "¿Desea avanzar con la aplicación?"
)

INSTACART_OWNER_CONTACT_TEXT = (
    "Perfecto ✅\n\n"
    "Para avanzar con el proceso, por favor comuníquese conmigo directamente por WhatsApp:\n\n"
    f"📞 WhatsApp: {WHATSAPP_NUMBER}\n\n"
    "\"Hola, vengo del bot, elegí Instacart y quiero avanzar\".\n\n"
    "📌 Le recomendamos revisar con frecuencia nuestros Estados de WhatsApp."
)

AUDIO_RECEIVED_TEXT = "🎤 Recibí su audio. Un momento mientras lo proceso..."
AUDIO_ERROR_TEXT = (
    "⚠️ En este momento no pude procesar el audio.\n\n"
    "Por favor, intente de nuevo o envíe su mensaje en texto."
)

AUDIO_NOT_CONFIGURED_TEXT = (
    "⚠️ El sistema de audio todavía no está configurado.\n\n"
    "Por favor, envíe su mensaje en texto por ahora."
)

# =========================
# DISPONIBILIDAD REAL
# =========================
AVAILABLE_CITIES = {
    "prescott": {"display": "Prescott, AZ", "state": "AZ", "region": "west", "price": 450, "note": ""},
    "show low": {"display": "Show Low, AZ", "state": "AZ", "region": "west", "price": 440, "note": ""},
    "fayetteville springdale": {"display": "Fayetteville–Springdale, AR", "state": "AR", "region": "south", "price": 370, "note": ""},
    "yellville": {"display": "Yellville, AR", "state": "AR", "region": "south", "price": 290, "note": ""},
    "jonesboro": {"display": "Jonesboro, AR", "state": "AR", "region": "south", "price": 290, "note": ""},
    "montrose": {"display": "Montrose, CO", "state": "CO", "region": "west", "price": 390, "note": ""},
    "tallahassee": {"display": "Tallahassee, FL", "state": "FL", "region": "south", "price": 400, "note": ""},
    "brunswick": {"display": "Brunswick, GA", "state": "GA", "region": "south", "price": 290, "note": ""},
    "valdosta": {"display": "Valdosta, GA", "state": "GA", "region": "south", "price": 390, "note": ""},
    "savannah": {"display": "Savannah, GA", "state": "GA", "region": "south", "price": 640, "note": ""},
    "columbus": {"display": "Columbus, GA", "state": "GA", "region": "south", "price": 450, "note": ""},
    "sandpoint": {"display": "Sandpoint, ID", "state": "ID", "region": "west", "price": 390, "note": ""},
    "boise": {"display": "Boise, ID", "state": "ID", "region": "west", "price": 690, "note": ""},
    "idaho falls": {"display": "Idaho Falls, ID", "state": "ID", "region": "west", "price": 440, "note": ""},
    "jerome": {"display": "Jerome, ID", "state": "ID", "region": "west", "price": 340, "note": ""},
    "evansville": {"display": "Evansville, IN", "state": "IN", "region": "midwest", "price": 330, "note": ""},
    "lafayette": {"display": "Lafayette, IN", "state": "IN", "region": "midwest", "price": 490, "note": ""},
    "eagle grove": {"display": "Eagle Grove, IA", "state": "IA", "region": "midwest", "price": 340, "note": ""},
    "dubuque": {"display": "Dubuque, IA", "state": "IA", "region": "midwest", "price": 440, "note": ""},
    "fort scott": {"display": "Fort Scott, KS", "state": "KS", "region": "midwest", "price": 440, "note": ""},
    "wichita": {"display": "Wichita, KS", "state": "KS", "region": "midwest", "price": 440, "note": ""},
    "paducah": {"display": "Paducah, KY", "state": "KY", "region": "south", "price": 340, "note": ""},
    "caribou": {"display": "Caribou, ME", "state": "ME", "region": "northeast", "price": 310, "note": ""},
    "fergus falls alexandria": {"display": "Fergus Falls–Alexandria, MN", "state": "MN", "region": "midwest", "price": 290, "note": ""},
    "mankato": {"display": "Mankato, MN", "state": "MN", "region": "midwest", "price": 310, "note": ""},
    "st cloud": {"display": "St. Cloud, MN", "state": "MN", "region": "midwest", "price": 340, "note": ""},
    "grand rapids": {"display": "Grand Rapids, MN", "state": "MN", "region": "midwest", "price": 370, "note": ""},
    "springfield": {"display": "Springfield, MO", "state": "MO", "region": "midwest", "price": 390, "note": ""},
    "butte": {"display": "Butte, MT", "state": "MT", "region": "west", "price": 290, "note": ""},
    "belgrade": {"display": "Belgrade, MT", "state": "MT", "region": "west", "price": 370, "note": ""},
    "wells": {"display": "Wells, NV", "state": "NV", "region": "west", "price": 290, "note": ""},
    "roswell": {"display": "Roswell, NM", "state": "NM", "region": "west", "price": 370, "note": ""},
    "hobbs": {"display": "Hobbs, NM", "state": "NM", "region": "west", "price": 340, "note": ""},
    "glens falls granville": {"display": "Glens Falls–Granville, NY", "state": "NY", "region": "northeast", "price": 310, "note": ""},
    "buffalo": {"display": "Buffalo, NY", "state": "NY", "region": "northeast", "price": 440, "note": ""},
    "southern pines": {"display": "Southern Pines, NC", "state": "NC", "region": "south", "price": 340, "note": ""},
    "minot stanley": {"display": "Minot–Stanley, ND", "state": "ND", "region": "midwest", "price": 370, "note": ""},
    "hillsboro": {"display": "Hillsboro, OH", "state": "OH", "region": "midwest", "price": 340, "note": ""},
    "akron": {"display": "Akron, OH", "state": "OH", "region": "midwest", "price": 540, "note": ""},
    "lima findlay": {"display": "Lima–Findlay, OH", "state": "OH", "region": "midwest", "price": 490, "note": ""},
    "la grande": {"display": "La Grande, OR", "state": "OR", "region": "west", "price": 410, "note": ""},
    "erie": {"display": "Erie, PA", "state": "PA", "region": "northeast", "price": 340, "note": ""},
    "bellefonte": {"display": "Bellefonte, PA", "state": "PA", "region": "northeast", "price": 340, "note": ""},
    "lancaster": {"display": "Lancaster, PA", "state": "PA", "region": "northeast", "price": 540, "note": ""},
    "pittsburgh": {"display": "Pittsburgh, PA", "state": "PA", "region": "northeast", "price": 440, "note": ""},
    "allentown": {"display": "Allentown, PA", "state": "PA", "region": "northeast", "price": 540, "note": ""},
    "sioux falls": {"display": "Sioux Falls, SD", "state": "SD", "region": "midwest", "price": 290, "note": ""},
    "brownsville": {"display": "Brownsville, TX", "state": "TX", "region": "south", "price": 290, "note": ""},
    "nacogdoches": {"display": "Nacogdoches, TX", "state": "TX", "region": "south", "price": 340, "note": ""},
    "bryan": {"display": "Bryan, TX", "state": "TX", "region": "south", "price": 490, "note": ""},
    "roanoke": {"display": "Roanoke, VA", "state": "VA", "region": "south", "price": 540, "note": ""},
    "pasco": {"display": "Pasco, WA", "state": "WA", "region": "west", "price": 340, "note": ""},
    "kennewick richland": {"display": "Kennewick–Richland, WA", "state": "WA", "region": "west", "price": 370, "note": ""},
    "union gap yakima": {"display": "Union Gap–Yakima, WA", "state": "WA", "region": "west", "price": 390, "note": ""},
    "pullman": {"display": "Pullman, WA", "state": "WA", "region": "west", "price": 390, "note": ""},
    "wenatchee": {"display": "Wenatchee, WA", "state": "WA", "region": "west", "price": 300, "note": ""},
    "kitsap": {"display": "Kitsap, WA", "state": "WA", "region": "west", "price": 540, "note": ""},
    "beaver": {"display": "Beaver, WV", "state": "WV", "region": "south", "price": 340, "note": ""},
    "davisville": {"display": "Davisville, WV", "state": "WV", "region": "south", "price": 390, "note": ""},
    "wausau weston": {"display": "Wausau–Weston, WI", "state": "WI", "region": "midwest", "price": 290, "note": ""},
    "cody": {"display": "Cody, WY", "state": "WY", "region": "west", "price": 290, "note": ""},
    "riverton": {"display": "Riverton, WY", "state": "WY", "region": "west", "price": 370, "note": ""},
}

# =========================
# HELPERS
# =========================
_recent = {}
_seen_users = {}

def is_duplicate(chat_id: int, message_id: int, ttl: int = 30) -> bool:
    now = time.time()
    for k, ts in list(_recent.items()):
        if now - ts > ttl:
            _recent.pop(k, None)
    key = (chat_id, message_id)
    if key in _recent:
        return True
    _recent[key] = now
    return False

def normalize(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

EXIT_KEYWORDS = {
    "salir", "cancelar", "no cumplo", "nocumplo", "no me sirve", "no sirve",
    "ninguna", "ninguna opcion", "ninguna opción", "no quiero", "ya no", "no gracias", "gracias",
}

def wants_to_exit(text_norm: str) -> bool:
    return any(k in text_norm for k in EXIT_KEYWORDS)

US_REGIONS_BY_STATE = {
    "CT":"northeast","ME":"northeast","MA":"northeast","NH":"northeast","NJ":"northeast",
    "NY":"northeast","PA":"northeast","RI":"northeast","VT":"northeast",
    "IL":"midwest","IN":"midwest","IA":"midwest","KS":"midwest","MI":"midwest","MN":"midwest",
    "MO":"midwest","NE":"midwest","ND":"midwest","OH":"midwest","SD":"midwest","WI":"midwest",
    "TX":"south","OK":"south","LA":"south","AR":"south","MS":"south","AL":"south","GA":"south",
    "FL":"south","SC":"south","NC":"south","TN":"south","KY":"south","VA":"south","WV":"south",
    "MD":"south","DE":"south","DC":"south",
    "AK":"west","AZ":"west","CA":"west","CO":"west","HI":"west","ID":"west","MT":"west",
    "NV":"west","NM":"west","OR":"west","UT":"west","WA":"west","WY":"west",
}

def extract_state_code(raw: str):
    text = (raw or "").upper()
    m = re.search(r"\b([A-Z]{2})\b", text)
    if m and m.group(1) in US_REGIONS_BY_STATE:
        return m.group(1)
    names = {
        "PENNSYLVANIA":"PA",
        "MINNESOTA":"MN",
        "WEST VIRGINIA":"WV",
        "GEORGIA":"GA",
        "NEW YORK":"NY",
        "PENSILVANIA":"PA"
    }
    up = re.sub(r"[^A-Z\s]", " ", text)
    up = re.sub(r"\s+", " ", up).strip()
    for k, v in names.items():
        if k in up:
            return v
    return None

def find_city_key(user_text: str):
    t = normalize(user_text)
    if t in AVAILABLE_CITIES:
        return t
    t_pad = f" {t} "
    for key in AVAILABLE_CITIES.keys():
        if f" {key} " in t_pad:
            return key
    return None

def suggest_alternatives(user_text: str, limit: int = 3):
    state = extract_state_code(user_text)
    items = list(AVAILABLE_CITIES.items())

    if state:
        same_state = [meta["display"] for _, meta in items if meta.get("state") == state]
        if same_state:
            return same_state[:limit]
        region = US_REGIONS_BY_STATE.get(state)
        if region:
            same_region = [meta["display"] for _, meta in items if meta.get("region") == region]
            if same_region:
                return same_region[:limit]

    ordered = []
    for pref in ["northeast", "south", "midwest", "west"]:
        ordered.extend([meta["display"] for _, meta in items if meta.get("region") == pref])

    out, seen = [], set()
    for c in ordered:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:limit]

def calculate_final_price(base_price: int, account_type: str) -> int:
    if account_type == "reactivation":
        return base_price + 500
    return base_price

def availability_message(city_raw: str, account_type: str) -> str:
    key = find_city_key(city_raw)

    if key and key in AVAILABLE_CITIES:
        meta = AVAILABLE_CITIES[key]
        base_price = int(meta.get("price", 0))
        final_price = calculate_final_price(base_price, account_type)
        note = (meta.get("note") or "").strip()

        msg = (
            f"✅ Sí contamos con disponibilidad en {meta['display']}.\n"
            f"💰 Precio: ${final_price}\n"
        )
        if note:
            msg += f"📌 {note}\n"
        msg += "\nPara continuar con el proceso, por favor escriba: CONTINUAR"
        return msg

    suggestions = suggest_alternatives(city_raw, limit=3)
    sug_txt = "\n".join([f"• {s}" for s in suggestions]) if suggestions else "• (Sin sugerencias disponibles por el momento)"

    return (
        f"❌ Por el momento NO contamos con disponibilidad en {city_raw.strip()}.\n\n"
        "📍 Opciones disponibles cercanas:\n"
        f"{sug_txt}\n\n"
        "Si desea, indíquenos otra ciudad y con gusto le confirmamos.\n\n"
        f"{WHATSAPP_STATUS_TEXT}"
    )

def _user_label(u) -> str:
    if not u:
        return "N/A"
    name = (u.full_name or "").strip() or "Sin nombre"
    uname = f"@{u.username}" if getattr(u, "username", None) else "(sin @)"
    return f"{name} {uname} | user_id={u.id}"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_lead(update: Update, text: str, source: str):
    try:
        payload = {
            "timestamp": _now_iso(),
            "source": source,
            "text": text,
            "chat_id": update.effective_chat.id if update.effective_chat else None,
            "user_id": update.effective_user.id if update.effective_user else None,
            "username": update.effective_user.username if update.effective_user else None,
            "full_name": update.effective_user.full_name if update.effective_user else None,
            "service": update._effective_user and None,  # placeholder seguro
        }

        Path(LEADS_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(LEADS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.warning("No pude guardar lead: %s", e)

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not ADMIN_CHAT_ID:
        return
    try:
        await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=text)
    except Exception as e:
        logging.warning("No pude notificar al admin: %s", e)

async def track_user_and_notify_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if u:
        _seen_users[str(u.id)] = _now_iso()

async def cmd_admin_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Admin test OK")
    await notify_admin(context, "✅ Admin test: el bot puede enviarte mensajes.")

async def cmd_who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _seen_users:
        await update.message.reply_text("Aún no hay usuarios registrados en memoria.")
        return
    items = sorted(_seen_users.items(), key=lambda x: x[1], reverse=True)[:20]
    lines = ["👥 Últimos usuarios (máx 20):"]
    for user_id, ts in items:
        lines.append(f"• user_id={user_id} | last_seen={ts}")
    await update.message.reply_text("\n".join(lines))

# =========================
# AUDIO
# =========================
def _transcribe_file_sync(file_path: str) -> str:
    if not openai_client:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    with open(file_path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model=AUDIO_TRANSCRIBE_MODEL,
            file=audio_file,
        )
    text = getattr(transcript, "text", "") or ""
    return text.strip()

async def transcribe_telegram_audio(telegram_file, suffix: str = ".ogg") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name

    try:
        await telegram_file.download_to_drive(custom_path=tmp_path)
        text = await asyncio.to_thread(_transcribe_file_sync, tmp_path)
        return text
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

# =========================
# MENÚS
# =========================
def services_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Amazon Flex", callback_data="svc:amazon_flex")],
        [InlineKeyboardButton("Instacart", callback_data="svc:instacart")],
        [InlineKeyboardButton("Shipt", callback_data="svc:shipt")],
        [InlineKeyboardButton("Veho", callback_data="svc:veho")],
        [InlineKeyboardButton("Spark Driver", callback_data="svc:spark_driver")],
        [InlineKeyboardButton("Uber", callback_data="svc:uber")],
        [InlineKeyboardButton("Door Dash", callback_data="svc:doordash")],
    ])

def amazon_type_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Cuenta nueva", callback_data="amz:type:nueva")],
        [InlineKeyboardButton("♻️ Reactivación", callback_data="amz:type:reactivacion")],
        [InlineKeyboardButton("⬅️ Volver a servicios", callback_data="nav:services")],
    ])

def yes_no_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ SI", callback_data="instacart:yes"),
         InlineKeyboardButton("❌ NO", callback_data="instacart:no")]
    ])

def advance_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ AVANZAR", callback_data="instacart:advance"),
         InlineKeyboardButton("❌ NO", callback_data="instacart:cancel")]
    ])

def amazon_new_cities_menu():
    items = list(AVAILABLE_CITIES.items())
    items.sort(key=lambda kv: kv[1].get("display", ""))

    keyboard = []
    for key, meta in items:
        keyboard.append([InlineKeyboardButton(meta["display"], callback_data=f"amz:new:city:{key}")])

    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data="amz:back:type")])
    return InlineKeyboardMarkup(keyboard)

# =========================
# LÓGICA CENTRAL DE TEXTO
# =========================
async def process_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text_raw: str,
    source: str = "text",
):
    if not text_raw:
        await update.message.reply_text("No pude entender su mensaje. Intente nuevamente.")
        return

    text_norm = normalize(text_raw)
    save_lead(update, text_raw, source)

    u = update.effective_user
    await notify_admin(
        context,
        "📩 MENSAJE\n"
        f"👤 {_user_label(u)}\n"
        f"💬 chat_id={update.effective_chat.id if update.effective_chat else 'N/A'}\n"
        f"🧾 origen={source}\n"
        f"✍️ texto:\n{text_raw}"
    )

    if wants_to_exit(text_norm):
        context.user_data.clear()
        await update.message.reply_text(GOODBYE_TEXT)
        return

    service = context.user_data.get("service", "")
    mode = context.user_data.get("mode", "")

    if service == "amazon_flex" and mode == "amazon_new_pick_city":
        await update.message.reply_text("📌 Por favor seleccione una ciudad usando los botones.")
        return

    if service == "amazon_flex" and mode == "amazon_new_wait_continue":
        if "continuar" in text_norm:
            context.user_data["mode"] = "amazon_new_requirements"
            await update.message.reply_text(AMAZON_REQUIREMENTS_TEXT)
            return
        await update.message.reply_text("Para continuar, por favor escriba: CONTINUAR")
        return

    if service == "amazon_flex" and mode == "amazon_new_requirements":
        if "cumplo" in text_norm:
            context.user_data["mode"] = "amazon_done"
            await update.message.reply_text(OWNER_CONTACT_TEXT)
            return
        await update.message.reply_text("Si cumple con todos los requisitos, por favor escriba: CUMPLO")
        return

    if service == "amazon_flex" and mode == "amazon_reactivation_requirements":
        if "cumplo" in text_norm:
            context.user_data["mode"] = "amazon_reactivation_city"
            await update.message.reply_text("Perfecto. Ahora indíqueme en qué ciudad desea la nueva cuenta.")
            return
        if "no cumplo" in text_norm or "nocumplo" in text_norm:
            context.user_data.clear()
            await update.message.reply_text(GOODBYE_TEXT)
            return
        await update.message.reply_text("Por favor responda escribiendo: CUMPLO o NO CUMPLO")
        return

    if service == "amazon_flex" and mode == "amazon_reactivation_city":
        city_raw = text_raw.strip()
        if not city_raw:
            await update.message.reply_text("📍 Por favor, indíqueme la ciudad.")
            return

        reply = availability_message(city_raw, account_type="reactivation")
        await update.message.reply_text(reply)

        if find_city_key(city_raw):
            context.user_data["mode"] = "amazon_reactivation_wait_continue"
            context.user_data["last_city"] = city_raw
        return

    if service == "amazon_flex" and mode == "amazon_reactivation_wait_continue":
        if "continuar" in text_norm:
            context.user_data["mode"] = "amazon_done"
            await update.message.reply_text(OWNER_CONTACT_TEXT)
            return
        await update.message.reply_text("Para continuar, por favor escriba: CONTINUAR")
        return

    await update.message.reply_text("Para comenzar, por favor escriba /start.", reply_markup=services_menu())

# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await track_user_and_notify_start(update, context)

    logging.info(
        "START | %s | chat_id=%s",
        _user_label(update.effective_user),
        update.effective_chat.id if update.effective_chat else "N/A"
    )

    await notify_admin(
        context,
        "🟢 /start\n"
        f"👤 {_user_label(update.effective_user)}\n"
        f"💬 chat_id={update.effective_chat.id if update.effective_chat else 'N/A'}"
    )

    await update.message.reply_text(WELCOME)
    await update.message.reply_text(CHOOSE_SERVICE, reply_markup=services_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await track_user_and_notify_start(update, context)

    data = (q.data or "")
    logging.info("CALLBACK | %s | data=%s", _user_label(q.from_user), data)

    await notify_admin(
        context,
        "🔘 BOTÓN (callback)\n"
        f"👤 {_user_label(q.from_user)}\n"
        f"💬 chat_id={q.message.chat_id if q.message else 'N/A'}\n"
        f"📦 data={data}"
    )

    await q.answer()

    if data == "nav:services":
        context.user_data.clear()
        await q.edit_message_text(CHOOSE_SERVICE, reply_markup=services_menu())
        return

    if data.startswith("svc:"):
        service_key = data.split(":", 1)[1]
        context.user_data.clear()
        context.user_data["service"] = service_key

        if service_key == "amazon_flex":
            context.user_data["mode"] = "amazon_choose_type"
            await q.edit_message_text(AMAZON_CHOOSE_TYPE, reply_markup=amazon_type_menu())
            return

        if service_key == "instacart":
            context.user_data["service"] = "instacart"
            context.user_data["mode"] = "instacart_waitlist_question"
            await q.edit_message_text(INSTACART_INTRO_TEXT, reply_markup=yes_no_menu())
            return

        await q.edit_message_text(
            COMING_SOON_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Volver a servicios", callback_data="nav:services")]]
            )
        )
        return

    if data == "instacart:yes":
        context.user_data["service"] = "instacart"
        context.user_data["mode"] = "instacart_decide_advance"
        await q.edit_message_text(INSTACART_WAITLIST_YES_TEXT, reply_markup=advance_menu())
        return

    if data == "instacart:no":
        context.user_data["service"] = "instacart"
        context.user_data["mode"] = "instacart_decide_advance"
        await q.edit_message_text(INSTACART_WAITLIST_NO_TEXT, reply_markup=advance_menu())
        return

    if data == "instacart:advance":
        context.user_data.clear()
        await q.edit_message_text(INSTACART_OWNER_CONTACT_TEXT)
        return

    if data == "instacart:cancel":
        context.user_data.clear()
        await q.edit_message_text(GOODBYE_TEXT)
        return

    if data.startswith("amz:type:"):
        choice = data.split(":", 2)[2]
        context.user_data["service"] = "amazon_flex"

        if choice == "nueva":
            context.user_data["mode"] = "amazon_new_pick_city"
            await q.edit_message_text(AMAZON_NEW_ACCOUNT_TEXT, reply_markup=amazon_new_cities_menu())
            return

        if choice == "reactivacion":
            context.user_data["mode"] = "amazon_reactivation_requirements"
            await q.edit_message_text(AMAZON_REACT_REQUIREMENTS_TEXT)
            return

    if data == "amz:back:type":
        context.user_data["mode"] = "amazon_choose_type"
        await q.edit_message_text(AMAZON_CHOOSE_TYPE, reply_markup=amazon_type_menu())
        return

    if data.startswith("amz:new:city:"):
        city_key = data.split(":", 3)[3]
        meta = AVAILABLE_CITIES.get(city_key)

        if not meta:
            context.user_data["mode"] = "amazon_new_pick_city"
            await q.edit_message_text(
                "❌ Esta ciudad ya no está disponible. Seleccione otra:",
                reply_markup=amazon_new_cities_menu()
            )
            return

        context.user_data["service"] = "amazon_flex"
        context.user_data["mode"] = "amazon_new_wait_continue"
        context.user_data["last_city"] = meta["display"]

        final_price = calculate_final_price(int(meta.get("price", 0)), account_type="new")
        note = (meta.get("note") or "").strip()

        msg = (
            f"✅ Sí contamos con disponibilidad en {meta['display']}.\n"
            f"💰 Precio: ${final_price}\n"
        )
        if note:
            msg += f"📌 {note}\n"
        msg += "\nPara continuar con el proceso, por favor escriba: CONTINUAR"

        await q.edit_message_text(msg)
        return

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if is_duplicate(update.message.chat_id, update.message.message_id):
        return

    await track_user_and_notify_start(update, context)
    await process_text_message(update, context, update.message.text or "", source="text")

async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return
    if is_duplicate(update.message.chat_id, update.message.message_id):
        return

    await track_user_and_notify_start(update, context)

    await notify_admin(
        context,
        "🎤 AUDIO RECIBIDO\n"
        f"👤 {_user_label(update.effective_user)}\n"
        f"💬 chat_id={update.effective_chat.id if update.effective_chat else 'N/A'}\n"
        f"⏱ duración={update.message.voice.duration}s"
    )

    if not openai_client:
        await update.message.reply_text(AUDIO_NOT_CONFIGURED_TEXT)
        return

    waiting_msg = await update.message.reply_text(AUDIO_RECEIVED_TEXT)

    try:
        telegram_file = await update.message.voice.get_file()
        transcript = await transcribe_telegram_audio(telegram_file, suffix=".ogg")

        if not transcript:
            await waiting_msg.edit_text(AUDIO_ERROR_TEXT)
            return

        await waiting_msg.edit_text(f"📝 Transcripción:\n{transcript}")
        await process_text_message(update, context, transcript, source="voice")

    except Exception as e:
        logging.exception("Error procesando nota de voz: %s", e)
        await waiting_msg.edit_text(AUDIO_ERROR_TEXT)
        await notify_admin(context, f"🚨 ERROR procesando nota de voz:\n{e}")

async def on_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.audio:
        return
    if is_duplicate(update.message.chat_id, update.message.message_id):
        return

    await track_user_and_notify_start(update, context)

    await notify_admin(
        context,
        "🎵 AUDIO RECIBIDO\n"
        f"👤 {_user_label(update.effective_user)}\n"
        f"💬 chat_id={update.effective_chat.id if update.effective_chat else 'N/A'}\n"
        f"🎼 archivo={update.message.audio.file_name or 'sin nombre'}"
    )

    if not openai_client:
        await update.message.reply_text(AUDIO_NOT_CONFIGURED_TEXT)
        return

    waiting_msg = await update.message.reply_text(AUDIO_RECEIVED_TEXT)

    try:
        telegram_file = await update.message.audio.get_file()
        transcript = await transcribe_telegram_audio(telegram_file, suffix=".mp3")

        if not transcript:
            await waiting_msg.edit_text(AUDIO_ERROR_TEXT)
            return

        await waiting_msg.edit_text(f"📝 Transcripción:\n{transcript}")
        await process_text_message(update, context, transcript, source="audio")

    except Exception as e:
        logging.exception("Error procesando audio: %s", e)
        await waiting_msg.edit_text(AUDIO_ERROR_TEXT)
        await notify_admin(context, f"🚨 ERROR procesando audio:\n{e}")

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.exception("ERROR del bot: %s", context.error)
    try:
        await notify_admin(context, f"🚨 ERROR en el bot:\n{context.error}")
    except Exception:
        pass

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN o BOT_TOKEN en variables de entorno")

    if not ADMIN_CHAT_ID:
        logging.warning("⚠️ Falta ADMIN_CHAT_ID (no se enviarán mensajes al admin).")

    if not OPENAI_API_KEY:
        logging.warning("⚠️ Falta OPENAI_API_KEY (los audios no funcionarán).")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_test", cmd_admin_test))
    app.add_handler(CommandHandler("who", cmd_who))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.AUDIO, on_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.add_error_handler(on_error)

    logging.info("✅ Bot listo. Iniciando polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
