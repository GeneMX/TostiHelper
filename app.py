import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tostadas Siberia - Pedidos", page_icon="🌮", layout="wide")

# --- INICIALIZACIÓN DEL CARRITO ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- CONFIGURACIÓN DE API IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configura la API Key en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- FUNCIÓN PARA CARGAR DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1SWaypb3Fq1rR_S1van5P8OYcJhO9m_lxYBAoLRgDjCk/edit?usp=sharing"

@st.cache_data(ttl=300)
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        mapping = {'producto': 'producto', 'nombre': 'producto', 'precio': 'precio', 'costo': 'precio', 'descripcion': 'descripcion', 'promo': 'descripcion'}
        df = df.rename(columns={c: mapping[c] for c in df.columns if c in mapping})
        return df
    except:
        return pd.DataFrame(columns=['producto', 'precio', 'descripcion'])

df_menu = cargar_datos(SHEET_URL)

# --- DISEÑO ---
st.title("🌮 Tostadas Tipo Siberia: Pedido Inteligente")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("🤖 Consulta al Asistente")
    pregunta = st.text_input("¿En qué puedo ayudarte?", placeholder="Pide el menú o pregunta por promociones...")
    
    if pregunta:
        pregunta_min = pregunta.lower()
        
        # 1. LÓGICA DE PALABRAS CLAVE (Filtros Directos)
        if "menu" in pregunta_min or "menú" in pregunta_min:
            st.info("📜 **Nuestro Menú Actual:**")
            for i, row in df_menu.iterrows():
                st.write(f"- **{row['producto']}**: ${row['precio']} ({row['descripcion']})")
        
        elif "promocion" in pregunta_min or "promociones" in pregunta_min or "promo" in pregunta_min:
            # Filtramos el dataframe buscando la palabra 'promo' en la descripción
            promos = df_menu[df_menu['descripcion'].str.contains("promo|especial|descuento", case=False, na=False)]
            if not promos.empty:
                st.success("🎉 **¡Tenemos estas promociones para ti!**")
                for i, row in promos.iterrows():
                    st.write(f"✅ **{row['producto']}**: {row['descripcion']} a solo **${row['precio']}**")
            else:
                st.warning("Por el momento no tenemos promociones marcadas, ¡pero nuestras Tostadas Siberia tienen el mejor precio de la ciudad!")
        
        # 2. LÓGICA DE INTELIGENCIA ARTIFICIAL (Para todo lo demás)
        else:
            try:
                contexto_menu = df_menu.to_string(index=False)
                prompt_sistema = f"Eres el mesero de Tostadas Siberia. Usa este menú: {contexto_menu}. Sé breve y antojable."
                with st.spinner("Escribiendo..."):
                    response = model.generate_content([prompt_sistema, pregunta])
                    st.info(response.text)
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.warning("⚠️ Sistema ocupado. Reintenta en 10 segundos.")
                    time.sleep(2)
                else:
                    st.error(f"Error técnico: {e}")

    # --- BOTONERA DE PRODUCTOS ---
    st.write("---")
    st.subheader("📋 Haz clic para añadir")
    grid = st.columns(2)
    for i, row in df_menu.iterrows():
        with grid[i % 2]:
            nombre = row.get('producto', 'Producto')
            precio = row.get('precio', 0)
            if st.button(f"➕ {nombre} (${precio})", key=f"btn_{i}"):
                st.session_state.carrito.append({"nombre": nombre, "precio": precio})
                st.rerun()

with col_der:
    st.subheader("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("Carrito vacío.")
    else:
        total = sum(item['precio'] for item in st.session_state.carrito)
        for i, item in enumerate(st.session_state.carrito):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{item['nombre']} (${item['precio']})")
            if c2.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
        
        st.divider()
        st.write(f"### Total: ${total}")

        # --- SECCIÓN DE PAGO ---
        metodo = st.radio("Método de pago:", ["Efectivo (Necesito cambio)", "Pago exacto / Tarjeta"])
        detalles_pago = ""
        
        if "Efectivo" in metodo:
            paga_con = st.number_input("¿Con cuánto pagas?", min_value=float(total), step=10.0, value=float(total))
            if paga_con > total:
                cambio = paga_con - total
                st.success(f"Cambio: ${cambio:.2f}")
                detalles_pago = f"%0A• Paga con: ${paga_con}%0A• Cambio: ${cambio:.2f}"
            else:
                detalles_pago = "%0A• Pago exacto en efectivo."
        else:
            detalles_pago = "%0A• Pago exacto / Tarjeta."

        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        # --- BOTÓN WHATSAPP ---
        tel_negocio = "528130447383" # <-- REEMPLAZA ESTO
        lista_pedido = "%0A".join([f"• {x['nombre']} (${x['precio']})" for x in st.session_state.carrito])
        msg = f"¡Hola! Pedido Siberia:%0A{lista_pedido}%0A%0A*TOTAL: ${total}*{detalles_pago}"
        st.link_button("🚀 ENVIAR POR WHATSAPP", f"https://wa.me/{tel_negocio}?text={msg}")

