import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yagmail
import os
from datetime import datetime

# ================= CONFIGURACIÓN =================
USUARIO_MAIL = "jobandosue@gmail.com"
PASSWORD_MAIL = "osqqdpnuixkguctr" 
DESTINATARIO = "jobando@envasescomeca.com"
DB_FILE = "money_data.csv"
CAT_FILE = "categorias_personalizadas.csv"

# --- Funciones de Datos ---
def cargar_datos():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Fecha", "Tipo", "Categoría", "Monto"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

def cargar_categorias():
    if os.path.exists(CAT_FILE):
        return pd.read_csv(CAT_FILE)["Nombre"].tolist()
    return ["Comida", "Transporte", "Hogar", "Salud", "Ocio", "Compras", "Facturas"]

def guardar_lista_categorias(lista):
    pd.DataFrame({"Nombre": lista}).to_csv(CAT_FILE, index=False)

# ================= INTERFAZ MÓVIL (UI) =================
st.set_page_config(page_title="Control de Gastos e Ingresos", layout="centered")

# CSS para que se vea bien en celulares (fuentes y botones grandes)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 55px; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# Estado de sesión para limpiar el monto
if 'monto_widget' not in st.session_state:
    st.session_state.monto_widget = 0.0

df = cargar_datos()
lista_cats = cargar_categorias()

# --- RESUMEN Y GRÁFICO (VISTA CELULAR) ---
st.title("₡ Control de Gastos e Ingresos")

ingresos_totales = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
gastos_totales = df[df["Tipo"] == "Gasto"]["Monto"].sum()
balance = ingresos_totales - gastos_totales

# Gráfico ajustado para pantalla angosta
fig = go.Figure(data=[
    go.Bar(name='Ingresos', x=['Resumen'], y=[ingresos_totales], marker_color='#2ecc71', text=f"₡{ingresos_totales:,.0f}"),
    go.Bar(name='Gastos', x=['Resumen'], y=[gastos_totales], marker_color='#e74c3c', text=f"₡{gastos_totales:,.0f}")
])
fig.update_layout(barmode='group', height=250, margin=dict(t=5, b=5, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

# Métricas en columnas que se apilan en móvil
c1, c2 = st.columns(2)
c1.metric("INGRESOS", f"₡{ingresos_totales:,.0f}")
c2.metric("GASTOS", f"₡{gastos_totales:,.0f}")
st.subheader(f"Balance: ₡{balance:,.2f}")

st.divider()

# --- REGISTRO TÁCTIL ---
st.subheader("Registrar Movimiento")
tipo = st.radio("Seleccione:", ["Gasto", "Ingreso"], horizontal=True)

# El monto ahora se limpia automáticamente
monto_input = st.number_input("Monto en Colones:", min_value=0.0, step=500.0, format="%.2f", key="monto_widget")

def registrar_y_limpiar(tipo_mov, cat_mov, monto_mov):
    global df
    if monto_mov > 0:
        nuevo = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), 
            "Tipo": tipo_mov, 
            "Categoría": cat_mov, 
            "Monto": monto_mov
        }])
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_datos(df)
        st.session_state.monto_widget = 0.0  # Limpia el campo
        st.rerun()
    else:
        st.error("Por favor, ingrese un monto")

if tipo == "Gasto":
    # Cuadrícula de 2 columnas para que los botones sean grandes en el dedo
    cols = st.columns(2)
    for i, cat in enumerate(lista_cats):
        with cols[i % 2]:
            if st.button(f"{cat}"):
                registrar_y_limpiar("Gasto", cat, monto_input)
else:
    if st.button("✅ GUARDAR INGRESO"):
        registrar_y_limpiar("Ingreso", "Ingreso General", monto_input)

# --- SIDEBAR: CONFIGURACIÓN Y REPORTE ---
with st.sidebar:
    st.header("⚙️ Opciones")
    
    with st.expander("📂 Gestionar Categorías"):
        nueva_cat = st.text_input("Nueva:")
        if st.button("Añadir"):
            if nueva_cat and nueva_cat not in lista_cats:
                lista_cats.append(nueva_cat)
                guardar_lista_categorias(lista_cats)
                st.rerun()
        
        st.write("---")
        for c in lista_cats:
            col_c, col_b = st.columns([3, 1])
            col_c.write(c)
            if col_b.button("🗑️", key=f"del_{c}"):
                lista_cats.remove(c)
                guardar_lista_categorias(lista_cats)
                st.rerun()

    st.divider()

    if st.button("📧 Enviar Reporte a Manuel"):
        try:
            yag = yagmail.SMTP(USUARIO_MAIL, PASSWORD_MAIL)
            resumen_df = df.groupby(['Tipo', 'Categoría'])['Monto'].sum().reset_index()
            resumen_df['Monto'] = resumen_df['Monto'].apply(lambda x: f"₡{x:,.2f}")
            
            tabla_html = resumen_df.to_html(index=False)
            tabla_html = tabla_html.replace('table', 'table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px;"')
            tabla_html = tabla_html.replace('<th>', '<th style="background-color: #2F75B5; color: white; padding: 8px; border: 1px solid #ddd;">')
            tabla_html = tabla_html.replace('<td>', '<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">')

            cuerpo_html = f"""
            <div style="max-width: 400px; font-family: sans-serif; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2F75B5;">Resumen de Gastos</h2>
                <div style="background: #eef7ff; padding: 15px; border-radius: 5px; text-align: center;">
                    <span style="font-size: 14px;">Balance Neto</span><br>
                    <b style="font-size: 24px; color: {'#27ae60' if balance >= 0 else '#e74c3c'};">₡{balance:,.2f}</b>
                </div>
                <br>
                {tabla_html}
            </div>
            """
            yag.send(to=DESTINATARIO, subject="📊 Reporte de Gastos e Ingresos", contents=cuerpo_html, attachments=DB_FILE)
            st.success("¡Reporte enviado!")
        except Exception as e:
            st.error(f"Error: {e}")

# --- HISTORIAL ---
st.divider()
st.subheader("🗑️ Últimos movimientos")
if not df.empty:
    for i in reversed(df.index[-5:]):
        col_txt, col_del = st.columns([4, 1])
        row = df.iloc[i]
        simbolo = "🟢" if row['Tipo'] == "Ingreso" else "🔴"
        col_txt.write(f"{simbolo} **{row['Categoría']}**: ₡{row['Monto']:,.2f}")
        if col_del.button("❌", key=f"del_row_{i}"):
            df = df.drop(i)
            guardar_datos(df)
            st.rerun()