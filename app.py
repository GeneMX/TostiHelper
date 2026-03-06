import streamlit as st
import google.generativeai as genai
import pandas as pd

# Configuración visual
st.set_page_config(page_title="Tostadas Siberia - Asesor", page_icon="🌮")
st.title("🌮 Tostadas Tipo Siberia: Asistente de Pedidos")

# 1. Conexión a tus datos (Link del CSV de Google Sheets)
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1SWaypb3Fq1rR_S1van5P8OYcJhO9m_lxYBAoLRgDjCk/edit?usp=sharing"

def obtener_menu():
    try:
        df = pd.read_csv(SHEET_CSV)
        return df.to_string(index=False)
    except:
        return "Tostada Especial: $90 (Pechuga de pollo desmenuzada, guacamole, crema)."

# 2. Configurar la IA
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. Interfaz de usuario
pregunta = st.text_input("¿Qué se te antoja hoy?", placeholder="Ej: ¿Qué trae la tostada?")

if pregunta:
    menu = obtener_menu()
    
    prompt_sistema = f"""
    Eres el asistente de 'TostiTellez'. 
    Tu especialidad son las Tostadas tipo Siberia (descripción: {menu}).
    Sé amable, usa modismos locales en Nuevo Leon,Mexico si es adecuado y antoja al cliente.
    Si preguntan por el envío, diles que el costo es de 30 pesos.
    Al final de cada respuesta, invita a darle al botón de abajo para pedir por WhatsApp.
    """
    
    response = model.generate_content([prompt_sistema, pregunta])
    st.info(response.text)

    # Botón de cierre de venta

    st.link_button("✅ ¡Hacer mi pedido ahora!", "https://wa.me/8130447383?text=Hola! Quiero hacer un pedido.")



