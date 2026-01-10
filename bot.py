import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
Eres AURO ASSIST, un bot de atención al cliente para Amazon Flex.

REGLAS OBLIGATORIAS:
- Responde SOLO sobre Amazon Flex
- Sé claro, directo y profesional
- NO inventes información
- Si no sabes algo, di: "Un asesor humano te contactará"

INFORMACIÓN DEL NEGOCIO:
- Servicios: activación, reactivación y cupos Amazon Flex
- Idioma: español
- Tono: respetuoso y confiable

SI EL CLIENTE PREGUNTA:
- precios → explica y pide ciudad
- requisitos → lista clara
- humano → pide nombre y ciudad
"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    user_text = update.message.text

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=user_text
    )

    await update.message.reply_text(response.output_text)

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
