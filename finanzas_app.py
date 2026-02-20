import streamlit as st
import pandas as pd
import plotly.express as px
import yagmail
import os
from datetime import datetime

# ================= CONFIGURACIÓN =================
USUARIO_MAIL = "jobandosue@gmail.com"
PASSWORD_MAIL = "osqqdpnuixkguctr" 
DESTINATARIO = "jobando@envasescomeca.com"
DB_FILE = "money_data.csv"

# Funciones de Datos
def cargar_datos():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Fecha", "Tipo", "Categoría", "Monto"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# ================= INTERFAZ (UI) =================
st.set_page_config(page_title="Money Flow", layout="centered")

# Estilos personalizados para parecer una App móvil
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 70px;
        font-size: 20px;
    }
    .main {
        background-color: #f5f7f9;
    }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- RESUMEN DE BALANCE ---
st.title("💰 Money Flow")
ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
gastos = df[df["Tipo"] == "Gasto"]["Monto"].sum()
balance = ingresos - gastos

c1, c2, c3 = st.columns(3)
c1.metric("INGRESOS", f"${ingresos:,.0f}")
c2.subheader(f"Balance\n${balance:,.0f}")
c3.metric("GASTOS", f"${gastos:,.0f}", delta=f"-{gastos:,.0f}", delta_color="inverse")

# --- GRÁFICO DE DONA CENTRAL ---
# 
if not df[df["Tipo"] == "Gasto"].empty:
    fig = px.pie(df[df["Tipo"] == "Gasto"], values='Monto', names='Categoría', 
                 hole=.7, color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Toca una categoría para empezar a registrar.")

# --- ENTRADA DE MONTO ---
monto_input = st.number_input("Introducir Monto:", min_value=0.0, step=1.0, format="%.2f")

# --- TECLADO DE CATEGORÍAS (CUADRÍCULA) ---
categorias_gastos = {
    "Comida": "🍕", "Transporte": "🚌", "Hogar": "🏠",
    "Salud": "🚑", "Ocio": "🍿", "Compras": "🛒",
    "Facturas": "🧾", "Regalos": "🎁", "Ahorro": "💰"
}

st.write("### ¿En qué gastaste?")
cols = st.columns(3)
for i, (nombre, icono) in enumerate(categorias_gastos.items()):
    with cols[i % 3]:
        if st.button(f"{icono}\n{nombre}"):
            if monto_input > 0:
                nuevo = pd.DataFrame([{"Fecha": datetime.now(), "Tipo": "Gasto", "Categoría": nombre, "Monto": monto_input}])
                df = pd.concat([df, nuevo], ignore_index=True)
                guardar_datos(df)
                st.rerun()
            else:
                st.error("Escribe un monto")

# --- BOTÓN DE INGRESOS ---
st.divider()
if st.button("➕ REGISTRAR INGRESO (SUELDO/OTROS)"):
    if monto_input > 0:
        nuevo = pd.DataFrame([{"Fecha": datetime.now(), "Tipo": "Ingreso", "Categoría": "Ingreso General", "Monto": monto_input}])
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_datos(df)
        st.rerun()

# --- CONSOLIDACIÓN Y ENVÍO ---
with st.sidebar:
    st.header("Ajustes y Reporte")
    if st.button("📧 Enviar Reporte al Correo"):
        try:
            yag = yagmail.SMTP(USUARIO_MAIL, PASSWORD_MAIL)
            resumen = df.groupby(['Tipo', 'Categoría'])['Monto'].sum().to_frame().to_html()
            
            yag.send(
                to=DESTINATARIO,
                subject=f"Consolidado Money Flow - {datetime.now().strftime('%d/%m/%Y')}",
                contents=[
                    "<h2>Tu resumen financiero</h2>",
                    f"<p>Balance Total: <b>${balance:,.2f}</b></p>",
                    resumen
                ]
            )
            st.success("Enviado!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    if st.checkbox("Ver tabla de datos"):
        st.dataframe(df)