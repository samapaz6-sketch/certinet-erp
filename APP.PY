import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración de la App
st.set_page_config(page_title="Certinet ERP", layout="wide")

# ======== BASE DE DATOS ========
def conectar_db():
    return sqlite3.connect("certinet_erp.db", check_same_thread=False)

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trabajadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT UNIQUE, nombre TEXT, nacionalidad TEXT, 
            fecha_contrato DATE, tipo_contrato TEXT, cargo TEXT, 
            sueldo_base REAL, afp TEXT, salud TEXT, email TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE, producto TEXT, entrada INTEGER DEFAULT 0, 
            salida INTEGER DEFAULT 0, costo_total REAL, valor_venta REAL
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

# ======== MENÚ LATERAL IZQUIERDO ========
st.sidebar.title("KAME / ERP - CERTINET")
menu = st.sidebar.radio(
    "Navegación:",
    ["Inventario", "Trabajadores", "Liquidaciones", "Libro de Ventas", "Libro de Compras", "Libro Diario"]
)

# ======== 1. SECCIÓN INVENTARIO (CON VNR Y ELIMINAR) ========
if menu == "Inventario":
    st.header("📦 Control de Inventario")
    
    with st.expander("➕ Formulario de ingreso de Producto", expanded=False):
        with st.form("ingreso_inv"):
            c1, c2, c3 = st.columns(3)
            f = c1.date_input("Fecha")
            p = c2.text_input("Producto")
            ent = c3.number_input("Entrada", min_value=0)
            c4, c5, c6 = st.columns(3)
            sal = c4.number_input("Salida", min_value=0)
            ct = c5.number_input("Costo Total ($)", min_value=0.0)
            vv = c6.number_input("Valor de Venta ($)", min_value=0.0)
            if st.form_submit_button("Guardar Registro"):
                conn = conectar_db()
                conn.execute("INSERT INTO inventario (fecha, producto, entrada, salida, costo_total, valor_venta) VALUES (?,?,?,?,?,?)", (f, p, ent, sal, ct, vv))
                conn.commit()
                st.success("Guardado correctamente.")
                st.rerun()

    conn = conectar_db()
    df_inv = pd.read_sql("SELECT * FROM inventario", conn)
    
    if not df_inv.empty:
        df_inv['Stock'] = df_inv['entrada'] - df_inv['salida']
        df_inv['Costo Unitario'] = df_inv['costo_total'] / df_inv['entrada'].replace(0, 1)
        
        st.subheader("📊 Tabla de Existencias")
        st.dataframe(df_inv, use_container_width=True)

        # ELIMINAR PRODUCTO POR ID
        with st.expander("🗑️ Eliminar Fila (Error de ingreso)"):
            id_borrar = st.number_input("Ingrese el número de ID de la fila a borrar", min_value=1, step=1)
            if st.button("Eliminar permanentemente", type="primary"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventario WHERE id = ?", (id_borrar,))
                conn.commit()
                st.success("Producto eliminado.")
                st.rerun()

        # CÁLCULO VNR (Basado en tu ejemplo de Excel)
        st.markdown("---")
        st.subheader("⚖️ Cálculo de VNR")
        cv1, cv2 = st.columns(2)
        p_est = cv1.number_input("Precio estimado de venta ($)", min_value=0.0)
        c_term = cv2.number_input("Costos de terminación ($)", min_value=0.0)
        g_vta = cv2.number_input("Gastos de venta ($)", min_value=0.0)
        
        vnr_res = p_est - c_term - g_vta
        st.metric("VNR Calculado", f"$ {vnr_res:,.0f}")

# ======== 2. SECCIÓN LIQUIDACIONES (ESTILO CERTINET) ========
elif menu == "Liquidaciones":
    st.header("📄 Liquidación de Sueldo")
    conn = conectar_db()
    df_t = pd.read_sql("SELECT * FROM trabajadores", conn)
    
    if not df_t.empty:
        busc = st.text_input("🔍 Buscar trabajador por RUT o Nombre")
        if busc:
    df_f = df_t[
        df_t['rut'].astype(str).str.contains(busc, na=False) |
        df_t['nombre'].astype(str).str.contains(busc, case=False, na=False)
    ]
else:
    df_f = df_t
        
        if not df_f.empty:
            sel_r = st.selectbox("Seleccione el RUT:", df_f['rut'])
            r = df_t[df_t['rut'] == sel_r].iloc[0]
            
            st.markdown(f"""
            <div style="border:2px solid black; padding:25px; background-color:white; color:black">
                <h2 style="text-align:center">CERTINET S.A.</h2>
                <p style="text-align:center">RUT: 99.532.830-5 | HUERFANOS 1052 PISO 12</p>
                <hr>
                <p><b>Nombre:</b> {r['nombre']} | <b>RUT:</b> {r['rut']}</p>
                <p><b>AFP:</b> {r['afp']} | <b>Salud:</b> {r['salud']} | <b>Cargo:</b> {r['cargo']}</p>
                <h3 style="text-align:right">LÍQUIDO A PAGAR: ${r['sueldo_base']*0.8:,.0f}*</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay trabajadores. Regístralos en la pestaña 'Trabajadores'.")
        
