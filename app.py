import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tostadas Siberia - Pedidos", page_icon="🌮", layout="wide")

# --- INICIALIZACIÓN DEL CARRITO ---
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- CONFIGURACIÓN DE API IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Falta la API Key en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- FUNCIÓN PARA CARGAR DATOS (CON LIMPIEZA DE COLUMNAS) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1SWaypb3Fq1rR_S1van5P8OYcJhO9m_lxYBAoLRgDjCk/edit?usp=sharing"

@st.cache_data(ttl=300)
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        # Limpiar nombres de columnas: quitar espacios y convertir a minúsculas para comparar
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapear nombres comunes a los que usa el código
        columnas_esperadas = {
            'producto': 'producto', 'nombre': 'producto', 'platillo': 'producto',
            'precio': 'precio', 'costo': 'precio', 'valor': 'precio',
            'descripcion': 'descripcion', 'detalle': 'descripcion', 'ingredientes': 'descripcion'
        }
        
        # Renombrar basándose en el mapeo
        nuevas_columnas = {}
        for col in df.columns:
            if col in columnas_esperadas:
                nuevas_columnas[col] = columnas_esperadas[col]
        
        df = df.rename(columns=nuevas_columnas)
        return df
    except Exception as e:
        st.error(f"Error conectando con el menú: {e}")
        return pd.DataFrame(columns=['producto', 'precio', 'descripcion'])

df_menu = cargar_datos(SHEET_URL)

# --- DISEÑO DE LA APLICACIÓN ---
st.title("🌮 Tostadas Tipo Siberia: Pedido en Línea")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    # 1. Chat con IA para dudas o sugerencias
    st.subheader("🤖 Consulta al Asistente")
    pregunta = st.text_input("¿Qué deseas saber hoy?", placeholder="Ej: ¿Qué incluye la tostada siberia?")
    
    if pregunta:
        contexto_menu = df_menu.to_string(index=False)
        prompt_sistema = f"""
        Eres el mesero virtual de 'Tostadas Siberia'. 
        Usa este menú: {contexto_menu}.
        REGLAS:
        - Si piden algo fuera del menú, sugiere lo más parecido.
        - Sé muy amable y describe los ingredientes (guacamole, crema, pollo) de forma antojable.
        - Si piden sugerencias, recomienda el combo con consomé.
        """
        with st.spinner("Escribiendo..."):
            response = model.generate_content([prompt_sistema, pregunta])
            st.info(response.text)

    # 2. Selección de Productos (Botones dinámicos)
    st.write("---")
    st.subheader("📋 Menú del Día")
    if df_menu.empty:
        st.warning("No se pudo cargar el menú. Revisa el link de Google Sheets.")
    else:
        grid = st.columns(2)
        for i, row in df_menu.iterrows():
            with grid[i % 2]:
                # Usamos .get() por si acaso falta una columna
                nombre = row.get('producto', 'Sin nombre')
                precio = row.get('precio', 0)
                desc = row.get('descripcion', '')
                
                with st.expander(f"**{nombre}** - ${precio}"):
                    st.write(desc)
                    if st.button(f"Añadir {nombre}", key=f"btn_{i}"):
                        st.session_state.carrito.append({"nombre": nombre, "precio": precio})
                        st.toast(f"✅ {nombre} añadido")
                        st.rerun()

with col_der:
    # 3. Carrito de Compras
    st.subheader("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("Aún no has seleccionado nada.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.carrito):
            cols_cart = st.columns([3, 1])
            cols_cart[0].write(f"{item['nombre']} (${item['precio']})")
            if cols_cart[1].button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
            total += item['precio']
        
        st.divider()
        st.write(f"### Total: ${total}")

        # 4. Gestión de Pago y Cambio
        st.subheader("💰 Método de Pago")
        metodo = st.radio("¿Cómo pagarás?", ["Efectivo (Necesito cambio)", "Pago exacto / Tarjeta"])
        
        detalles_pago = ""
        if metodo == "Efectivo (Necesito cambio)":
            paga_con = st.number_input("¿Con cuánto pagarás?", min_value=float(total), step=10.0, value=float(total))
            if paga_con > total:
                cambio = paga_con - total
                st.success(f"Te enviaremos **${cambio:.2f}** de cambio.")
                detalles_pago = f"%0A• Paga con: ${paga_con}%0A• Cambio requerido: ${cambio:.2f}"
            else:
                detalles_pago = "%0A• Pago exacto en efectivo."
        else:
            detalles_pago = "%0A• Pago exacto / Tarjeta."

        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        # 5. Envío a WhatsApp
        st.divider()
        tel_negocio = "521XXXXXXXXXX" # <-- COLOCA EL TELÉFONO AQUÍ
        lista_final = "%0A".join([f"• {x['nombre']} (${x['precio']})" for x in st.session_state.carrito])
        
        texto_wa = (
            f"¡Hola! Nuevo pedido de Tostadas Siberia%0A"
            f"--------------------------%0A"
            f"{lista_final}%0A"
            f"--------------------------%0A"
            f"*TOTAL: ${total}*"
            f"{detalles_pago}%0A"
            f"--------------------------"
        )
        
        st.link_button("🚀 ENVIAR PEDIDO POR WHATSAPP", f"https://wa.me/{tel_negocio}?text={texto_wa}")

