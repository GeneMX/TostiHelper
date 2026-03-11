import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tostadas Siberia - Asistente", page_icon="🌮", layout="wide")

# --- INICIALIZACIÓN DE VARIABLES ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- CONFIGURACIÓN DE API KEY ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configura la GOOGLE_API_KEY en los Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1SWaypb3Fq1rR_S1van5P8OYcJhO9m_lxYBAoLRgDjCk/edit?usp=sharing"

@st.cache_data(ttl=300)
def cargar_menu(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame({"Producto": ["Tostada"], "Precio": [85], "Descripcion": ["Tradicional"]})

df_menu = cargar_menu(SHEET_URL)

# --- INTERFAZ ---
st.title("🌮 Tostadas Tipo Siberia")
col_chat, col_pedido = st.columns([2, 1])

with col_chat:
    pregunta = st.text_input("¿Tienes dudas sobre el menú?")
    if pregunta:
        menu_txt = df_menu.to_string(index=False)
        prompt = f"Eres un mesero de Tostadas Siberia. Menú: {menu_txt}. Ayuda al cliente."
        response = model.generate_content([prompt, pregunta])
        st.info(response.text)

    st.subheader("Selecciona para añadir al pedido:")
    grid = st.columns(2)
    for i, row in df_menu.iterrows():
        with grid[i % 2]:
            if st.button(f"➕ {row['Producto']} (${row['Precio']})"):
                st.session_state.carrito.append({"nombre": row['Producto'], "precio": row['Precio']})
                st.rerun()

with col_pedido:
    st.subheader("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("Vacío")
    else:
        total = sum(item['precio'] for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.write(f"- {item['nombre']} (${item['precio']})")
        
        st.markdown(f"### Total: **${total}**")
        
        if st.button("🗑️ Vaciar"):
            st.session_state.carrito = []
            st.rerun()

        st.divider()
        
        # --- SECCIÓN DE PAGO ---
        st.subheader("💰 Método de Pago")
        metodo_pago = st.radio("¿Cómo vas a pagar?", ["Efectivo (Necesito cambio)", "Pago exacto / Tarjeta"])
        
        monto_pago = total
        cambio = 0
        detalles_pago = ""

        if metodo_pago == "Efectivo (Necesito cambio)":
            monto_pago = st.number_input("¿Con cuánto vas a pagar?", min_value=float(total), step=10.0, value=float(total))
            if monto_pago > total:
                cambio = monto_pago - total
                st.success(f"Te enviaremos **${cambio:.2f}** de cambio.")
                detalles_pago = f"%0A• Paga con: ${monto_pago}%0A• Cambio requerido: ${cambio:.2f}"
            else:
                detalles_pago = "%0A• Pago exacto en efectivo."
        else:
            detalles_pago = "%0A• Pago exacto / Tarjeta al recibir."

        # --- BOTÓN DE WHATSAPP ---
        if st.session_state.carrito:
            items_texto = "%0A".join([f"• {x['nombre']} (${x['precio']})" for x in st.session_state.carrito])
            tel_negocio = "528130447383" # PON EL TELÉFONO AQUÍ
            
            # Construcción del mensaje final
            msg = (
                f"¡Hola! Nuevo pedido:%0A"
                f"--------------------------%0A"
                f"{items_texto}%0A"
                f"--------------------------%0A"
                f"*TOTAL A PAGAR: ${total}*"
                f"{detalles_pago}%0A"
                f"--------------------------%0A"
                f"Favor de confirmar el pedido."
            )
            
            st.link_button("🚀 CONFIRMAR Y PEDIR CAMBIO", f"https://wa.me/{tel_negocio}?text={msg}")
