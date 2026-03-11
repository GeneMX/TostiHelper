import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Tostitellez Suc. Juarez - Asistente para Servicio a Domicilio", 
    page_icon="🌮", 
    layout="wide"
)

# --- 2. ESTILOS CSS PERSONALIZADOS (IDENTIDAD DE MARCA) ---
st.markdown("""
    <style>
    /* Estilo para los botones de añadir al carrito */
    div.stButton > button:first-child {
        background-color: #2e7d32; /* Verde bosque */
        color: white;
        border-radius: 12px;
        border: none;
        height: 3em;
        width: 100%;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1b5e20;
        transform: scale(1.03);
        border: none;
    }
    /* Estilo para el botón de confirmar WhatsApp */
    a[href^="https://wa.me"] button {
        background-color: #25d366 !important;
        color: white !important;
        font-weight: bold !important;
    }
    /* Títulos en rojo tradicional */
    h1, h2, h3 {
        color: #d32f2f;
    }
    /* Contenedor del carrito */
    [data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
        background-color: #fcfcfc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ESTADO DE LA SESIÓN ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "mostrar_menu" not in st.session_state:
    st.session_state.mostrar_menu = False

# --- 4. CONFIGURACIÓN DE API IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')
else:
    st.error("⚠️ Falta la configuración de GOOGLE_API_KEY en Secrets.")
    st.stop()

# --- 5. CARGA DE DATOS (GOOGLE SHEETS) ---
# Reemplaza con tu link publicado como CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD6Xflh5DacQ4ZOgPROgXFv1JocZb_0TO8z85CihhgNUGspywHpJhjPWyvslaH63SYv4W3lAa0cgfo/pub?output=csv"

@st.cache_data(ttl=300)
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        # Normalización de columnas
        df.columns = [str(c).strip().lower() for c in df.columns]
        mapa_nombres = {}
        for c in df.columns:
            if any(x in c for x in ['prod', 'nom']): mapa_nombres[c] = 'producto'
            elif any(x in c for x in ['prec', 'cost']): mapa_nombres[c] = 'precio'
            elif any(x in c for x in ['desc', 'det', 'promo']): mapa_nombres[c] = 'descripcion'
        df = df.rename(columns=mapa_nombres)

        # Limpieza de precios (quitar $$ y comas)
        if 'precio' in df.columns:
            df['precio'] = df['precio'].astype(str).str.replace('$', '', regex=False)
            df['precio'] = df['precio'].str.replace(',', '.', regex=False).str.strip()
            df['precio'] = pd.to_numeric(df['precio'], errors='coerce').fillna(0)
            
        return df.dropna(subset=['producto'])
    except:
        # Menú de emergencia si falla la conexión
        return pd.DataFrame({
            'producto': ['Tostada Especial', 'Tostada Sencilla', 'Consomé'],
            'precio': [90.0, 75.0, 40.0],
            'descripcion': ['Pollo, crema y guacamole', 'La clásica', 'Caliente']
        })

df_menu = cargar_datos(SHEET_URL)

# --- 6. DISEÑO DE LA APLICACIÓN ---
st.title("🌮 Tostitellez Suc. Juarez - Asistente para Servicio a Domicilio")

col_chat, col_pedido = st.columns([2, 1], gap="large")

with col_chat:
    st.subheader("🤖 Consulta al Asistente")
    pregunta = st.text_input("¿Qué deseas saber o pedir hoy?", placeholder="Ej: ¿Qué promociones hay? / Quiero pedir...")
    
    if pregunta:
        preg = pregunta.lower()
        
        # A. INTENCIÓN: UBICACIÓN
        if any(x in preg for x in ["donde", "ubicacion", "mapa", "llegar"]):
            st.success("📍 **Nuestra Ubicación:** Av. Elizama S/N, Frente al kínder, Mirador de San Antonio, Juárez, NL.")
            mapa_df = pd.DataFrame({'lat': [25.644955073270065],'lon': [-100.05841009550268]})
            st.map(mapa_df)

        # B. INTENCIÓN: MENÚ O PEDIDO
        elif any(x in preg for x in ["menu", "lista", "pedir", "ordenar", "quiero"]):
            st.session_state.mostrar_menu = True
            st.info("📜 **Menú habilitado:** Puedes ver los productos abajo para añadirlos.")
            df_view = df_menu.dropna(subset=['producto'])
            for _, r in df_view.iterrows():
                st.write(f"• **{r['producto']}** - ${r['precio']} ({r['descripcion']})")

        # C. RESPUESTA DE IA GENERAL
        else:
            try:
                contexto = f"Menú: {df_menu.to_string(index=False)}. Ubicación: Juárez NL. Responde amablemente."
                response = model.generate_content([contexto, pregunta])
                st.info(response.text)
            except:
                st.warning("Sera transferido a chat de whatsapp para una mejor atención...")
		# WHATSAPP
                tel_negocio = "528130447383" # <-- REEMPLAZA CON EL CELULAR REAL
                msg_wa = f"Mensaje:%0A{preg}"
                st.link_button("🚀 CONTACTAR POR WHATSAPP", f"https://wa.me/{tel_negocio}?text={msg_wa}")

    # --- SECCIÓN DINÁMICA DE PRODUCTOS ---
    if st.session_state.mostrar_menu:
        st.write("---")
        st.subheader("📋 Selecciona tus productos")
        grid = st.columns(2)
        for i, row in df_menu.iterrows():
            with grid[i % 2]:
                p_nom = str(row['producto'])
                p_pre = float(row['precio'])
                if st.button(f"➕ {p_nom} (${p_pre})", key=f"btn_{i}"):
                    st.session_state.carrito.append({"nombre": p_nom, "precio": p_pre})
                    st.toast(f"✅ {p_nom} añadido")
                    st.rerun()
        
        if st.button("⬅️ Ocultar Menú"):
            st.session_state.mostrar_menu = False
            st.rerun()

with col_pedido:
    st.subheader("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("Selecciona algo del menú para comenzar.")
    else:
        # Suma total protegida contra errores de tipo
        total = sum(float(item['precio']) for item in st.session_state.carrito)
        
        for i, item in enumerate(st.session_state.carrito):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{item['nombre']} (${item['precio']})")
            if c2.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
        
        st.divider()
        st.write(f"## Total: ${total:.2f}")

        # PAGO
        metodo = st.radio("Método de pago:", ["Efectivo (Cambio)", "Tarjeta / Exacto"])
        msg_pago = ""
        if "Efectivo" in metodo:
            paga_con = st.number_input("¿Con cuánto pagas?", min_value=float(total), step=10.0, value=float(total))
            if paga_con > total:
                cambio = paga_con - total
                st.success(f"Cambio: ${cambio:.2f}")
                msg_pago = f"%0A• Paga con: ${paga_con}%0A• Cambio: ${cambio:.2f}"
            else: msg_pago = "%0A• Pago exacto."
        else: msg_pago = "%0A• Pago con tarjeta/exacto."

        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        # WHATSAPP
        tel = "528130447383" # <-- REEMPLAZAR AQUÍ
        lista_final = "%0A".join([f"• {x['nombre']} (${x['precio']})" for x in st.session_state.carrito])
        msg_wa = f"¡Hola! Pedido Siberia:%0A{lista_final}%0A%0A*TOTAL: ${total:.2f}*{msg_pago}"
        
        st.link_button("🚀 ENVIAR POR WHATSAPP", f"https://wa.me/{tel}?text={msg_wa}")
