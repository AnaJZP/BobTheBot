import pandas as pd
import pandas_ta as ta # pip install pandas_ta

def analyze_parabolic_sar(df_stock_data: pd.DataFrame) -> tuple[str, str]:
    """
    Analiza la señal del Parabolic SAR.

    Args:
        df_stock_data (pd.DataFrame): DataFrame con columnas 'High', 'Low', 'Close'.

    Returns:
        tuple[str, str]: (Señal: "Compra", "Venta" o "Mantener", Justificación)
    """
    if df_stock_data is None or df_stock_data.empty or len(df_stock_data) < 2:
        return "Mantener", "Datos insuficientes para Parabolic SAR."

    # Calcular PSAR
    df_stock_data.ta.psar(append=True) # Añade columnas PSARl (long), PSARs (short), PSARaf, PSARr

    # La columna relevante es PSARs para señales de venta y PSARl para señales de compra
    # pandas_ta puede devolver una columna 'PSAR' o 'PSAR_0.02_0.2' dependiendo de la versión.
    # Buscamos una columna que contenga 'PSAR' pero no 'PSARaf' o 'PSARr'.
    psar_col_name = None
    for col in df_stock_data.columns:
        if "PSAR" in col and "PSARaf" not in col and "PSARr" not in col:
            psar_col_name = col
            break
    
    if psar_col_name is None or psar_col_name not in df_stock_data.columns:
         return "Mantener", "No se pudo calcular la columna PSAR principal."

    last_close = df_stock_data['Close'].iloc[-1]
    prev_close = df_stock_data['Close'].iloc[-2]
    
    last_psar = df_stock_data[psar_col_name].iloc[-1]
    prev_psar = df_stock_data[psar_col_name].iloc[-2]

    signal = "Mantener"
    justification = f"Precio ({last_close:.2f}), PSAR ({last_psar:.2f}). "

    # Señal de Compra: Precio cruza POR ENCIMA del PSAR
    # (PSAR estaba arriba y ahora está abajo O el precio cierra encima del PSAR que está abajo)
    if prev_close < prev_psar and last_close > last_psar: # Cruce alcista
        signal = "Compra"
        justification += "El precio ha cruzado por encima del Parabolic SAR."
    # Señal de Venta: Precio cruza POR DEBAJO del PSAR
    # (PSAR estaba abajo y ahora está arriba O el precio cierra debajo del PSAR que está arriba)
    elif prev_close > prev_psar and last_close < last_psar: # Cruce bajista
        signal = "Venta"
        justification += "El precio ha cruzado por debajo del Parabolic SAR."
    elif last_close > last_psar:
        justification += "El precio se mantiene por encima del Parabolic SAR (tendencia alcista)."
        signal = "Mantener (Posición Larga)" # O simplemente Mantener si no hay posición.
    elif last_close < last_psar:
        justification += "El precio se mantiene por debajo del Parabolic SAR (tendencia bajista)."
        signal = "Mantener (Posición Corta)" # O simplemente Mantener.
    else:
        justification += "El precio y el Parabolic SAR están muy juntos o no hay señal clara."

    return signal, justification

def analyze_stochastic_oscillator(df_stock_data: pd.DataFrame, k: int = 14, d: int = 3, smooth_k: int = 3) -> tuple[str, str]:
    """
    Analiza la señal del Oscilador Estocástico.

    Args:
        df_stock_data (pd.DataFrame): DataFrame con columnas 'High', 'Low', 'Close'.
        k (int): Periodo para %K.
        d (int): Periodo para %D (media móvil de %K).
        smooth_k (int): Suavizado para %K.

    Returns:
        tuple[str, str]: (Señal: "Compra", "Venta" o "Mantener", Justificación)
    """
    if df_stock_data is None or df_stock_data.empty or len(df_stock_data) < k + d: # Necesita suficientes datos
        return "Mantener", "Datos insuficientes para Oscilador Estocástico."

    # Calcular Estocástico
    df_stock_data.ta.stoch(k=k, d=d, smooth_k=smooth_k, append=True)
    # Columnas añadidas: STOCHk_14_3_3 (%K), STOCHd_14_3_3 (%D)

    k_col = f'STOCHk_{k}_{d}_{smooth_k}'
    d_col = f'STOCHd_{k}_{d}_{smooth_k}'

    if k_col not in df_stock_data.columns or d_col not in df_stock_data.columns:
        return "Mantener", "No se pudieron calcular las columnas del Oscilador Estocástico."

    last_k = df_stock_data[k_col].iloc[-1]
    last_d = df_stock_data[d_col].iloc[-1]
    prev_k = df_stock_data[k_col].iloc[-2]
    prev_d = df_stock_data[d_col].iloc[-2]

    oversold_level = 20
    overbought_level = 80
    signal = "Mantener"
    justification = f"%K ({last_k:.2f}), %D ({last_d:.2f}). "

    # Señal de Compra: %K cruza %D desde abajo, en zona de sobreventa
    if prev_k < prev_d and last_k > last_d and last_k < oversold_level:
        signal = "Compra"
        justification += f"%K cruzó por encima de %D en la zona de sobreventa (<{oversold_level})."
    # Señal de Venta: %K cruza %D desde arriba, en zona de sobrecompra
    elif prev_k > prev_d and last_k < last_d and last_k > overbought_level:
        signal = "Venta"
        justification += f"%K cruzó por debajo de %D en la zona de sobrecompra (>{overbought_level})."
    # Otras condiciones para mantener o salir de zonas extremas
    elif last_k < oversold_level or last_d < oversold_level:
        justification += f"Indicador en zona de sobreventa (<{oversold_level}). Atender a cruces alcistas."
    elif last_k > overbought_level or last_d > overbought_level:
        justification += f"Indicador en zona de sobrecompra (>{overbought_level}). Atender a cruces bajistas."
    else:
        justification += "Indicador en zona neutral."
        
    return signal, justification

def generate_combined_recommendation(df_stock_data: pd.DataFrame, ticker_symbol: str) -> tuple[str, str, str, str, str]:
    """
    Genera una recomendación combinada o elige una estrategia.
    Para este ejemplo, se mostrarán ambas y se intentará una recomendación consolidada.
    """
    if df_stock_data is None:
        return "Error", "No se pudieron obtener datos del activo.", "", "", ""

    sar_signal, sar_justification = analyze_parabolic_sar(df_stock_data.copy()) # Usar copia para no alterar el df original
    stoch_signal, stoch_justification = analyze_stochastic_oscillator(df_stock_data.copy())

    # Lógica de recomendación consolidada (simplificada):
    # Si ambas señales coinciden (y no son "Mantener")
    if sar_signal == stoch_signal and sar_signal != "Mantener":
        final_signal = sar_signal
        final_justification = f"Ambos indicadores coinciden: {sar_justification} Y {stoch_justification}"
    # Si una es fuerte y la otra es mantener
    elif sar_signal != "Mantener" and stoch_signal == "Mantener":
        final_signal = sar_signal
        final_justification = f"PSAR: {sar_justification} (Estocástico en {stoch_signal})"
    elif stoch_signal != "Mantener" and sar_signal == "Mantener":
        final_signal = stoch_signal
        final_justification = f"Estocástico: {stoch_justification} (PSAR en {sar_signal})"
    # Si hay conflicto o ambas son mantener
    else:
        final_signal = "Mantener"
        final_justification = (f"Señales mixtas o neutrales. "
                               f"PSAR: {sar_signal} ({sar_justification.split('. ')[1] if '. ' in sar_justification else sar_justification}). "
                               f"Estocástico: {stoch_signal} ({stoch_justification.split('. ')[1] if '. ' in stoch_justification else stoch_justification})")


    # Para un reporte más educativo, podrías devolver ambas individualmente
    # En este caso, priorizamos una única señal como pide el requerimiento
    return final_signal, final_justification, sar_signal, sar_justification, stoch_signal, stoch_justification


if __name__ == '__main__':
    # Pruebas
    from data_provider import get_stock_data # Para prueba local
    datos_test = get_stock_data("MSFT", period="1y", interval="1d")
    if datos_test is not None:
        print(f"\n--- Análisis para MSFT (Precio Cierre: {datos_test['Close'].iloc[-1]:.2f}) ---")
        
        sig_sar, just_sar = analyze_parabolic_sar(datos_test.copy())
        print(f"PSAR: Señal '{sig_sar}', Justificación: {just_sar}")

        sig_stoch, just_stoch = analyze_stochastic_oscillator(datos_test.copy())
        print(f"Estocástico: Señal '{sig_stoch}', Justificación: {just_stoch}")

        print("\n--- Recomendación Consolidada ---")
        final_sig, final_just, _, _, _, _ = generate_combined_recommendation(datos_test, "MSFT")
        print(f"Señal Final: {final_sig}\nJustificación: {final_just}")
