# bot.py
# Telegram Bot (Python) - Auro Ashly Flex Master
# Flujo principal: Servicios -> Amazon Flex -> (Cuenta nueva / Reactivación)
# Sin IA. Sin inventar disponibilidad. Con cierre formal y sugerencia de Estados de WhatsApp.

import os
import re
import time
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
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")

# Tu WhatsApp (formato USA)
WHATSAPP_NUMBER = "+1 512 679 0599"

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
    "Veo que necesita una cuenta nueva.\n\n"
    "Por favor, indíquenos en qué ciudad desea crear la cuenta."
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
    "Escriba por favor: \"Hola, vengo del bot y cumplo con los requisitos\"."
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
    "Escriba por favor:\n"
    "\"Hola, vengo del bot, elegí Instacart y quiero avanzar\".\n\n"
    "📌 Le recomendamos revisar con frecuencia nuestros Estados de WhatsApp."
)
# =========================
# DISPONIBILIDAD REAL (EDITA AQUÍ SI CAMBIA)
# base_price = precio base de ciudad (antes de sumas)
# =========================
AVAILABLE_CITIES = {
    # Pennsylvania (PA)
    "bellefonte": {
        "display": "Bellefonte, PA",
        "state": "PA",
        "region": "northeast",
        "price": 150,
        "note": "Close to NY and Philadelphia",
    },
    "pittsburgh": {
        "display": "Pittsburgh, PA",
        "state": "PA",
        "region": "northeast",
        "price": 190,
        "note": "",
    },

    # Minnesota (MN)
    "mankato": {
        "display": "Mankato, MN",
        "state": "MN",
        "region": "midwest",
        "price": 150,
        "note": "80 miles to Minneapolis",
    },

    # West Virginia (WV)
    "parkersburg": {
        "display": "Parkersburg, WV",
        "state": "WV",
        "region": "south",
        "price": 150,
        "note": "3 Hours to Cincinnati",
    },
    "beaver": {
        "display": "Beaver, WV",
        "state": "WV",
        "region": "south",
        "price": 150,
        "note": "3 hours to Charlotte",
    },

    # Georgia (GA)
    "brunswick": {
        "display": "Brunswick, GA",
        "state": "GA",
        "region": "south",
        "price": 300,
        "note": "1 hour to Jacksonville",
    },

    # New York (NY)
    "buffalo": {
        "display": "Buffalo, NY",
        "state": "NY",
        "region": "northeast",
        "price": 170,
        "note": "Large city",
    },
}

# =========================
# HELPERS
# =========================
_recent = {}
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
    "salir", "cancelar",
    "no cumplo", "nocumplo",
    "no me sirve", "no sirve",
    "ninguna", "ninguna opcion", "ninguna opción",
    "no quiero", "ya no", "no gracias",
    "gracias",
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
        "PENSILVANIA":"PA",
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
    for key in AVAILABLE_CITIES.keys():
        if re.search(rf"\b{re.escape(key)}\b", t):
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

    # fallback ordenado por regiones
    ordered = []
    for pref in ["northeast", "south", "midwest", "west"]:
        ordered.extend([meta["display"] for _, meta in items if meta.get("region") == pref])

    seen = set()
    out = []
    for c in ordered:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:limit]

def calculate_final_price(base_price: int, account_type: str) -> int:
    # account_type: "new" o "reactivation"
    if account_type == "reactivation":
        return base_price + 500
    return base_price + 150

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
        [
            InlineKeyboardButton("✅ SI", callback_data="instacart:yes"),
            InlineKeyboardButton("❌ NO", callback_data="instacart:no"),
        ]
    ])

def advance_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➡️ AVANZAR", callback_data="instacart:advance"),
            InlineKeyboardButton("❌ NO", callback_data="instacart:cancel"),
        ]
    ])
# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME)
    await update.message.reply_text(CHOOSE_SERVICE, reply_markup=services_menu())

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

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
            await q.edit_message_text(
                INSTACART_INTRO_TEXT,
                reply_markup=yes_no_menu()
            )
            return
        await q.edit_message_text(COMING_SOON_TEXT, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Volver a servicios", callback_data="nav:services")]
        ]))
        return
    # =========================
    # INSTACART - BOTONES
    # =========================
    if data == "instacart:yes":
        context.user_data["service"] = "instacart"
        context.user_data["mode"] = "instacart_decide_advance"
        await q.edit_message_text(
            INSTACART_WAITLIST_YES_TEXT,
            reply_markup=advance_menu()
        )
        return

    if data == "instacart:no":
        context.user_data["service"] = "instacart"
        context.user_data["mode"] = "instacart_decide_advance"
        await q.edit_message_text(
            INSTACART_WAITLIST_NO_TEXT,
            reply_markup=advance_menu()
        )
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
            context.user_data["mode"] = "amazon_new_account_city"
            await q.edit_message_text(AMAZON_NEW_ACCOUNT_TEXT)
            return

        if choice == "reactivacion":
            context.user_data["mode"] = "amazon_reactivation_requirements"
            await q.edit_message_text(AMAZON_REACT_REQUIREMENTS_TEXT)
            return

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if is_duplicate(update.message.chat_id, update.message.message_id):
        return

    text_raw = update.message.text or ""
    text_norm = normalize(text_raw)

    # Salida formal en cualquier momento
    if wants_to_exit(text_norm):
        context.user_data.clear()
        await update.message.reply_text(GOODBYE_TEXT)
        return

    service = context.user_data.get("service", "")
    mode = context.user_data.get("mode", "")

    # =========================
    # AMAZON FLEX - CUENTA NUEVA
    # =========================
    if service == "amazon_flex" and mode == "amazon_new_account_city":
        city_raw = text_raw.strip()
        if not city_raw:
            await update.message.reply_text("📍 Por favor, indíquenos la ciudad.")
            return

        reply = availability_message(city_raw, account_type="new")
        await update.message.reply_text(reply)

        # Si hay disponibilidad, esperamos "CONTINUAR"
        if find_city_key(city_raw):
            context.user_data["mode"] = "amazon_new_wait_continue"
            context.user_data["last_city"] = city_raw
        # Si no hay, se queda en el mismo modo para que escriba otra ciudad
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

    # =========================
    # AMAZON FLEX - REACTIVACIÓN
    # =========================
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

    # Si el usuario escribe sin estar en flujo
    await update.message.reply_text(
        "Para comenzar, por favor escriba /start.",
        reply_markup=services_menu()
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN o BOT_TOKEN en variables de entorno")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # Polling (si usas Render, evita tener 2 instancias corriendo a la vez)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
