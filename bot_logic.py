import re
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib.pyplot as plt # pip install matplotlib
import io # Para enviar imagen sin guardar en disco

# Módulos del proyecto
from config import TELEGRAM_BOT_TOKEN
from data_provider import get_stock_data, get_current_price
from technical_analysis import generate_combined_recommendation
from query_logger import log_query # Opcional

# --- Comandos Básicos ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"¡Hola {user_name}! 👋 Soy tu asistente de análisis bursátil.\n"
        "Puedes preguntarme sobre un activo, por ejemplo: '¿Compro o vendo AMZN?' o '¿Qué opinas de TSLA hoy?'.\n"
        "También puedes usar /ayuda para ver más comandos."
    )

async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Comandos disponibles:\n"
        "/start - Iniciar conversación\n"
        "/ayuda - Mostrar esta ayuda\n"
        "/analizar <TICKER> - Obtener análisis de un activo (ej: /analizar AAPL)\n\n"
        "También puedes enviar consultas en lenguaje natural como:\n"
        "  '¿Compro o vendo MSFT?'\n"
        "  'Análisis de GOOG'\n"
        "  '¿Qué tal NFLX hoy?'\n\n"
        "Las recomendaciones se basan en Parabolic SAR y Oscilador Estocástico."
    )

# --- Procesamiento de Consultas Libres y Comando /analizar ---
def extract_ticker(text: str) -> str | None:
    """Extrae un ticker de un texto. Asume tickers en mayúsculas de 1 a 5 letras."""
    # Intenta encontrar tickers comunes como AMZN, TSLA. Puede mejorarse.
    # Primero busca tickers explícitos como $AAPL
    match_dollar = re.search(r'\$([A-Z]{1,5}\.?[A-Z]{0,2})', text.upper())
    if match_dollar:
        return match_dollar.group(1)

    # Luego busca palabras en mayúsculas que puedan ser tickers
    # Prioriza palabras que son solo letras y terminan oración o están solas.
    potential_tickers = re.findall(r'\b([A-Z]{1,5}\.?[A-Z]{0,2})\b', text.upper())
    if potential_tickers:
        # Heurística: si hay varias, tomar la última o la que parece más un ticker.
        # Por simplicidad, tomamos la primera que no sea una palabra común como "HOY", "COMPRO".
        # Esta parte puede necesitar un NLP más sofisticado para robustez.
        common_words_to_ignore = ["HOY", "COMPRO", "VENDO", "OPINAS", "ANALISIS"]
        for pt in reversed(potential_tickers): # Dar prioridad a las últimas encontradas
             if pt not in common_words_to_ignore and len(pt)>1 : #Evitar letras sueltas si no es un ticker conocido de 1 letra
                 # Podríamos tener una lista de tickers válidos si fuera necesario
                return pt
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto que no son comandos."""
    message_text = update.message.text
    print(f"Recibido mensaje: {message_text}") # Log para debug

    ticker = extract_ticker(message_text)

    if not ticker:
        await update.message.reply_text("No pude identificar un símbolo de activo en tu consulta. Intenta con algo como '¿Análisis de AAPL?' o usando el comando /analizar <TICKER>.")
        return

    await perform_analysis(update, context, ticker, message_text)


async def analizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /analizar <TICKER>."""
    if not context.args:
        await update.message.reply_text("Por favor, especifica un ticker. Ejemplo: /analizar AAPL")
        return
    
    ticker = context.args[0].upper()
    query_text = f"/analizar {ticker}"
    await perform_analysis(update, context, ticker, query_text)


async def perform_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: str, query_text: str):
    """Realiza el análisis y responde al usuario."""
    user = update.message.from_user
    await update.message.reply_text(f"🔍 Analizando {ticker}, por favor espera un momento...")

    # 1. Obtener datos del activo
    # Para análisis diario, se suelen usar datos con periodos de 6 meses a 1 año.
    df_stock_data = get_stock_data(ticker, period="1y", interval="1d")
    current_price = get_current_price(ticker)

    if df_stock_data is None or current_price is None:
        await update.message.reply_text(f"Lo siento, no pude obtener los datos para {ticker}. Verifica que el símbolo sea correcto.")
        log_query(user.id, user.first_name, ticker, query_text, "Error", "No se pudieron obtener datos")
        return

    # 2. Generar recomendación
    signal, justification, sar_sig, sar_just, stoch_sig, stoch_just = generate_combined_recommendation(df_stock_data, ticker)

    # 3. Formatear y enviar respuesta
    response_message = (
        f"🔔 **Análisis para {ticker}** 🔔\n\n"
        f"**Precio Actual:** ${current_price:.2f}\n"
        f"**Señal Sugerida:** **{signal.upper()}**\n\n"
        f"**Justificación Principal:**\n{justification}\n\n"
        f"--- Detalles de Indicadores ---\n"
        f"📊 **Parabolic SAR:**\n"
        f"   - Señal: {sar_sig}\n"
        f"   - Nota: {sar_just}\n"
        f"📉 **Oscilador Estocástico (14,3,3):**\n"
        f"   - Señal: {stoch_sig}\n"
        f"   - Nota: {stoch_just}\n\n"
        f"🎓 _Recuerda: Esta es una recomendación automatizada basada en indicadores técnicos y no constituye asesoramiento financiero. Considera siempre múltiples factores._"
    )
    await update.message.reply_text(response_message, parse_mode='Markdown')
    
    # 4. Registrar consulta (Extra)
    log_query(user.id, user.first_name, ticker, query_text, signal, justification)

    # 5. Graficar y enviar imagen (Extra - Opcional)
    try:
        send_graph = True # Poner en False para deshabilitar gráficos temporalmente
        if send_graph and df_stock_data is not None and len(df_stock_data) > 30: # Necesita suficientes datos para graficar bien
            # Usar una copia para añadir indicadores sin afectar otros usos del df
            plot_df = df_stock_data.copy() 
            
            # Recalcular indicadores en la copia si no están ya (generate_combined_recommendation los calcula pero en su propia copia)
            # Parabolic SAR
            psar_col_name = None
            plot_df.ta.psar(append=True)
            for col in plot_df.columns:
                if "PSAR" in col and "PSARaf" not in col and "PSARr" not in col:
                    psar_col_name = col; break
            
            # Stochastic
            k, d, smooth_k = 14, 3, 3
            plot_df.ta.stoch(k=k, d=d, smooth_k=smooth_k, append=True)
            k_col = f'STOCHk_{k}_{d}_{smooth_k}'
            d_col = f'STOCHd_{k}_{d}_{smooth_k}'

            # Tomar los últimos N datos para que el gráfico sea legible (ej. últimos 100 días)
            plot_df_subset = plot_df.tail(100)

            fig, axs = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
            
            # Gráfico de Precio y PSAR
            axs[0].plot(plot_df_subset.index, plot_df_subset['Close'], label='Precio de Cierre', color='blue')
            if psar_col_name and psar_col_name in plot_df_subset.columns:
                 axs[0].scatter(plot_df_subset.index, plot_df_subset[psar_col_name], label='Parabolic SAR', color='red', s=10)
            axs[0].set_title(f'Precio de {ticker} y Parabolic SAR')
            axs[0].set_ylabel('Precio')
            axs[0].legend()
            axs[0].grid(True)

            # Gráfico del Oscilador Estocástico
            if k_col in plot_df_subset.columns and d_col in plot_df_subset.columns:
                axs[1].plot(plot_df_subset.index, plot_df_subset[k_col], label='%K', color='green')
                axs[1].plot(plot_df_subset.index, plot_df_subset[d_col], label='%D', color='orange')
                axs[1].axhline(80, color='red', linestyle='--', alpha=0.5, label='Sobrecompra (80)')
                axs[1].axhline(20, color='green', linestyle='--', alpha=0.5, label='Sobreventa (20)')
                axs[1].set_title('Oscilador Estocástico')
                axs[1].set_ylabel('Valor')
                axs[1].set_ylim(0, 100)
                axs[1].legend()
                axs[1].grid(True)
            
            plt.xlabel('Fecha')
            plt.tight_layout() # Ajusta el layout para que no se solapen los títulos
            
            # Guardar gráfico en un buffer de memoria
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            await update.message.reply_photo(photo=InputFile(buf, filename=f'{ticker}_analisis.png'), caption=f"Gráfico de {ticker} con indicadores.")
            plt.close(fig) # Cerrar la figura para liberar memoria
            buf.close()

    except Exception as e:
        print(f"Error al generar o enviar el gráfico: {e}")
        # await update.message.reply_text("No se pudo generar el gráfico en este momento.")


# --- Función Principal del Bot ---
def run_bot():
    """Inicializa y corre el bot de Telegram."""
    print("Iniciando bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Registrar handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ayuda", ayuda_command))
    app.add_handler(CommandHandler("analizar", analizar_command))
    
    # Handler para mensajes de texto generales (debe ir después de los CommandHandlers)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    app.run_polling()
