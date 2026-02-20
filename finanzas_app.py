import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yagmail
import os
import random
from datetime import datetime

# ================= CONFIGURACIÓN =================
USUARIO_MAIL = "jobandosue@gmail.com"
PASSWORD_MAIL = "osqqdpnuixkguctr" 
DESTINATARIO = "jobando@envasescomeca.com"
DB_FILE = "money_data.csv"
CAT_FILE = "categorias_personalizadas.csv"

# --- Contenido Proactivo ---
FRASES_DIA = [
    "“Cuida de los pequeños gastos; un pequeño agujero hunde un gran barco.” – Benjamin Franklin",
    "“No ahorres lo que te queda después de gastar, gasta lo que te queda después de ahorrar.” – Warren Buffett"
]
TIPS_FINANCIEROS = [
    "**Regla 50/30/20:** 50% necesidades, 30% deseos, 20% ahorro.",
    "**Regla de las 24 Horas:** Antes de una compra impulsiva, espera un día completo."
]

# --- Funciones de Datos (Preservadas) ---
def cargar_datos():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Fecha", "Tipo", "Categoría", "Monto", "Observaciones"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)
    return df

def cargar_categorias():
    if os.path.exists(CAT_FILE): return pd.read_csv(CAT_FILE)["Nombre"].tolist()
    return ["Comida", "Transporte", "Hogar", "Salud", "Ocio", "Compras", "Facturas"]

def guardar_lista_categorias(lista):
    pd.DataFrame({"Nombre": lista}).to_csv(CAT_FILE, index=False)

# --- Generador de Diseño de Estado de Cuenta (Preservado) ---
def generar_html_diseno(df):
    df_sorted = df.sort_values(by="Fecha", ascending=False)
    total_ing = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
    total_gas = df[df["Tipo"] == "Gasto"]["Monto"].sum()
    saldo = total_ing - total_gas
    
    html = f"""
    <div style="font-family: Calibri, sans-serif; border: 1px solid #004d40; max-width: 600px; margin: auto;">
        <div style="background-color: #004d40; color: white; padding: 10px; text-align: center;">
            <h2>ESTADO DE CUENTA PROFESIONAL</h2>
        </div>
        <div style="padding: 15px;">
            <p><b>Balance Neto:</b> ${saldo:,.2f}</p>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <thead>
                    <tr style="background-color: #dce6f1;">
                        <th style="border: 1px solid #ccc; padding: 4px;">FECHA</th>
                        <th style="border: 1px solid #ccc; padding: 4px;">CATEGORÍA</th>
                        <th style="border: 1px solid #ccc; padding: 4px;">MONTO</th>
                    </tr>
                </thead>
                <tbody>
    """
    for _, row in df_sorted.head(20).iterrows():
        bg = "#e2efda" if row['Tipo'] == "Ingreso" else "#ffffff"
        html += f"<tr style='background-color: {bg};'><td style='border: 1px solid #ccc; padding: 2px; text-align: center;'>{row['Fecha']}</td><td style='border: 1px solid #ccc; padding: 2px;'>{row['Categoría']}</td><td style='border: 1px solid #ccc; padding: 2px; text-align: right;'>{row['Monto']:,.2f}</td></tr>"
    html += "</tbody></table></div></div>"
    return html

# ================= INTERFAZ STREAMLIT =================
st.set_page_config(page_title="Control Financiero", layout="wide")
df = cargar_datos()
lista_cats = cargar_categorias()
if "f_key" not in st.session_state: st.session_state.f_key = 0

st.title("📊 Control de Gastos e Ingresos")

# --- REGISTRO ---
with st.container(border=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: tipo = st.selectbox("Tipo:", ["Gasto", "Ingreso"], key=f"t_{st.session_state.f_key}")
    with c2: monto = st.number_input("Monto:", min_value=0.0, format="%.2f", key=f"m_{st.session_state.f_key}")
    with c3: obs = st.text_input("Observaciones:", key=f"o_{st.session_state.f_key}")
    
    if tipo == "Gasto":
        cols = st.columns(len(lista_cats))
        for i, cat in enumerate(lista_cats):
            if cols[i].button(cat, use_container_width=True):
                nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "Tipo": "Gasto", "Categoría": cat, "Monto": monto, "Observaciones": obs}])
                df = pd.concat([df, nv], ignore_index=True); guardar_datos(df)
                st.session_state.f_key += 1; st.rerun()
    else:
        if st.button("📥 REGISTRAR INGRESO", use_container_width=True):
            nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "Tipo": "Ingreso", "Categoría": "Ingreso General", "Monto": monto, "Observaciones": obs}])
            df = pd.concat([df, nv], ignore_index=True); guardar_datos(df)
            st.session_state.f_key += 1; st.rerun()

st.divider()

# --- TABLA DE EDICIÓN ---
st.subheader("⚙️ Historial y Edición")
df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
if st.button("💾 Guardar Cambios"):
    guardar_datos(df_edit); st.success("Guardado"); st.rerun()

# --- SIDEBAR (DASHBOARD + BOTONES DE ENVÍO) ---
with st.sidebar:
    st.header("📈 Dashboard")
    if not df.empty:
        total_ing = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
        total_gas = df[df['Tipo'] == 'Gasto']['Monto'].sum()
        st.metric("BALANCE NETO", f"${total_ing - total_gas:,.2f}")
        
        df_chart = df.groupby(['Categoría', 'Tipo'])['Monto'].sum().unstack(fill_value=0).reset_index()
        fig = go.Figure()
        if 'Ingreso' in df_chart.columns: fig.add_trace(go.Bar(x=df_chart['Categoría'], y=df_chart['Ingreso'], name='Ing.', marker_color='#27ae60'))
        if 'Gasto' in df_chart.columns: fig.add_trace(go.Bar(x=df_chart['Categoría'], y=df_chart['Gasto'], name='Gas.', marker_color='#e74c3c'))
        fig.update_layout(barmode='group', height=230, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # --- BOTÓN 1: ESTADO EN EL CUERPO ---
    if st.button("📧 Enviar Estado en Cuerpo", use_container_width=True):
        yag = yagmail.SMTP(USUARIO_MAIL, PASSWORD_MAIL)
        yag.send(to=DESTINATARIO, subject="Estado de Cuenta (Vista Directa)", contents=generar_html_diseno(df))
        st.success("Enviado al cuerpo")

    # --- BOTÓN 2: TODO COMO ADJUNTO ---
    if st.button("📎 Enviar Todo como Adjunto", use_container_width=True):
        # Generar archivo temporal del reporte
        with open("Estado_Cuenta.html", "w", encoding="utf-8") as f: f.write(generar_html_diseno(df))
        
        frase = random.choice(FRASES_DIA)
        tip = random.choice(TIPS_FINANCIEROS)
        cuerpo_bonito = f"<h3>¡Hola!</h3><p>{frase}</p><p><b>Tip:</b> {tip}</p><p>Te adjunto tu data y el reporte visual.</p>"
        
        yag = yagmail.SMTP(USUARIO_MAIL, PASSWORD_MAIL)
        yag.send(to=DESTINATARIO, subject="Data + Reporte Adjuntos", contents=cuerpo_bonito, attachments=[DB_FILE, "Estado_Cuenta.html"])
        st.success("Archivos adjuntados con éxito")

    with st.expander("Categorías"):
        nc = st.text_input("Nueva:")
        if st.button("Añadir"):
            l = cargar_categorias(); l.append(nc); guardar_lista_categorias(l); st.rerun()