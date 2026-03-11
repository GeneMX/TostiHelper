import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tostitellez Suc. Juarez - Asistente para Servicio a Domicilio", page_icon="🌮", layout="wide")

if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- CONFIGURACIÓN DE API IA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configura la API Key en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- FUNCIÓN DE CARGA INDESTRUCTIBLE ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD6Xflh5DacQ4ZOgPROgXFv1JocZb_0TO8z85CihhgNUGspywHpJhjPWyvslaH63SYv4W3lAa0cgfo/pub?output=csv"

@st.cache_data(ttl=300)
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        # Limpieza inicial de nombres de columnas
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Diccionario para renombrar columnas por aproximación
        nuevos_nombres = {}
        for col in df.columns:
            if any(x in col for x in ['prod', 'nom', 'item', 'platillo']):
                nuevos_nombres[col] = 'producto'
            elif any(x in col for x in ['prec', 'cost', 'val', 'monto']):
                nuevos_nombres[col] = 'precio'
            elif any(x in col for x in ['desc', 'det', 'promo', 'info']):
                nuevos_nombres[col] = 'descripcion'
        
        df = df.rename(columns=nuevos_nombres)
        
        # Si después del mapeo faltan columnas, las creamos para evitar el KeyError
        columnas_necesarias = ['producto', 'precio', 'descripcion']
        for col in columnas_necesarias:
            if col not in df.columns:
                df[col] = "N/A" if col != 'precio' else 0
        
        return df[columnas_necesarias] # Retornamos solo lo que necesitamos
    except Exception as e:
        st.error(f"Error de conexión con datos: {e}")
        return pd.DataFrame(columns=['producto', 'precio', 'descripcion'])

df_menu = cargar_datos(SHEET_URL)

# --- INTERFAZ ---
st.title("🌮 Tostitellez Sucursal Juarez: Asistente para Servicio a Domicilio")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("🤖 Consulta al Asistente")
    pregunta = st.text_input("¿En qué puedo ayudarte?", placeholder="Pide el menú o pregunta por promociones o pregunta por el costo de servicio a domicilio o dudas ")
    
    if pregunta:
        preg = pregunta.lower()
        
        # 1. Filtro Menú Corregido
        if any(x in preg for x in ["servicio", "domicilio", "envio", "servicio a domicilio"]):
            st.info(" El costo de envio es de 30 pesos ")
        elif any(x in preg for x in ["menu", "menú", "carta", "lista"]):
            st.info("📜 **Nuestro Menú:**")
            # Eliminamos filas que estén totalmente vacías en el Excel
            df_limpio = df_menu.dropna(subset=['producto']) 
            
            for _, row in df_limpio.iterrows():
                # Extraemos los datos asegurando que no sean NaN
                nombre = str(row['producto']) if pd.notna(row['producto']) else "Producto"
                precio = row['precio'] if pd.notna(row['precio']) else 0
                desc = str(row['descripcion']) if pd.notna(row['descripcion']) else ""
                
                # Limpiamos el texto para que no aparezca "NaN" visualmente
                desc_texto = f"({desc})" if desc != "nan" and desc != "N/A" else ""
                
                # Imprimimos de forma limpia
                st.write(f"• **{nombre}**: ${precio} {desc_texto}")
        
        # 2. Filtro Promociones
        elif any(x in preg for x in ["promo", "descuento", "especial", "oferta"]):
            promos = df_menu[df_menu['descripcion'].astype(str).str.contains("promo|especial|descuento", case=False, na=False)]
            if not promos.empty:
                st.success("🎉 **Promociones encontradas:**")
                for _, row in promos.iterrows():
                    st.write(f"✅ **{row['producto']}**: {row['descripcion']} - **${row['precio']}**")
            else:
                st.warning("No hay promociones marcadas en el menú por ahora.")
        
        # 3. Inteligencia Artificial
        else:
            try:
                contexto = df_menu.to_string(index=False)
                prompt_sistema = f"""
            		Eres el asistente de 'TostiTellez'. 
            		Tu especialidad son las Tostadas tipo Siberia.            Usa este menú: {contexto_menu}.
            		REGLAS:
            		- Sé amable, usa modismos locales en Nuevo Leon,Mexico si es adecuado y antoja al cliente.
            		- Si preguntan por el envío, diles que el costo es de 30 pesos.
            		- Si preguntan por promociones, diles el menu buscando solamente los productos que sean tipo Promo.
            		- Solo ofrece opciones dentro del menu.
            		- Al final de cada respuesta, invita a darle al botón de abajo para pedir por WhatsApp.
            		- Si piden algo fuera del menú, sugiere lo más parecido.
            		- Sé muy amable y describe los ingredientes (guacamole, crema, pollo) de forma antojable.
            		- Si piden sugerencias, recomienda el combo con consomé.
                    - Si pregunta sobre servicio a domicilio, responde que el costo es de 30 pesos 
                    - Pregunta sobre que colonia es el servicio para saber si esta dentro de la cobertura.
        		"""
                with st.spinner("Analizando..."):
                    response = model.generate_content([prompt, pregunta])
                    st.info(response.text)
            except Exception as e:
                st.error("Asistente temporalmente ocupado. - Se contactara con un agente por whatsapp")
                 # WHATSAPP
                tel_negocio = "528130447383" # <-- REEMPLAZA CON EL CELULAR REAL
                msg_wa = f"Mensaje:%0A{preg}"
                st.link_button("🚀 CONTACTAR POR WHATSAPP", f"https://wa.me/{tel_negocio}?text={msg_wa}")


    # --- BOTONES DE PRODUCTOS ---
    st.write("---")
    st.subheader("📋 Añade a tu pedido")
    grid = st.columns(2)
    for i, row in df_menu.iterrows():
        with grid[i % 2]:
            # Acceso seguro a los datos
            p_nom = row['producto']
            p_pre = row['precio']
            if st.button(f"➕ {p_nom} (${p_pre})", key=f"btn_{i}"):
                st.session_state.carrito.append({"nombre": p_nom, "precio": p_pre})
                st.toast(f"✅ {p_nom} añadido")
                st.rerun()

with col_der:
    st.subheader("🛒 Tu Pedido")
    if not st.session_state.carrito:
        st.write("Selecciona productos del menú.")
    else:
        # Versión segura que ignora errores de texto en los precios
        total = sum(float(item['precio']) if str(item['precio']).replace('.','',1).isdigit() else 0.0 for item in st.session_state.carrito)
        total = total + 25
        for i, item in enumerate(st.session_state.carrito):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{item['nombre']} (${item['precio']})")
            if c2.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
        
        st.divider()
        st.write(f"### Total con envio: ${total}")

        # GESTIÓN DE PAGO
        metodo = st.radio("Pago:", ["Efectivo (Necesito cambio)", "Exacto / Transferencia"])
        detalles_pago = ""
        
        if "Efectivo" in metodo:
            paga_con = st.number_input("¿Con cuánto pagas?", min_value=float(total), value=float(total), step=10.0)
            if paga_con > total:
                cambio = paga_con - total
                st.success(f"Cambio: ${cambio:.2f}")
                detalles_pago = f"%0A• Paga con: ${paga_con}%0A• Cambio: ${cambio:.2f}"
            else:
                detalles_pago = "%0A• Pago exacto."
        else:
            detalles_pago = "%0A• Pago exacto / Transferencia."

        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        # WHATSAPP
        tel_negocio = "528130447383" # <-- REEMPLAZA CON EL CELULAR REAL
        lista_final = "%0A".join([f"• {x['nombre']} (${x['precio']})" for x in st.session_state.carrito])
        msg_wa = f"¡Hola! Pedido:%0A{lista_final}%0A%0A*TOTAL: ${total}*{detalles_pago}"
        st.link_button("🚀 CONFIRMAR POR WHATSAPP", f"https://wa.me/{tel_negocio}?text={msg_wa}")
















