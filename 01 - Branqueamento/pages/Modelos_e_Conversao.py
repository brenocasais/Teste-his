# pages/Modelos e Conversão.py
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Modelos de Planilhas", layout="wide")
st.title("Modelos e Conversão de Planilhas")

# === Geração de modelos em XLSX ===
st.subheader("Modelos para preenchimento")
col1, col2 = st.columns(2)

def gerar_xlsx_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

with col1:
    if st.button("Gerar modelo: Limites (.xlsx)"):
        modelo_limites = pd.DataFrame({
            "Nome": ["Ex: Alvura Branqueada"],
            "Tag": ["Ex: 3205QI021.PNT"],
            "LO": [85.0],
            "HI": [90.0],
        })
        xlsx_data = gerar_xlsx_bytes(modelo_limites, "Limites")
        st.download_button(
            "Baixar modelo de Limites (XLSX)",
            data=xlsx_data,
            file_name="modelo_limites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with col2:
    if st.button("Gerar modelo: Qualidade (.xlsx)"):
        modelo_qualidade = pd.DataFrame({
            "timestamp": ["2025-08-07 08:00:00"],
            "3205QI021.PNT": [88.2],
            "3205QI022.PNT": [43.1],
        })
        xlsx_data = gerar_xlsx_bytes(modelo_qualidade, "Qualidade")
        st.download_button(
            "Baixar modelo de Qualidade (XLSX)",
            data=xlsx_data,
            file_name="modelo_qualidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# === Upload genérico para conversão de abas em CSV ===
st.subheader("Conversão de Excel para CSVs (qualquer aba)")
st.caption("Envie qualquer arquivo Excel para converter uma ou mais abas em arquivos CSV.")

uploaded_excel = st.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"], key="generic_excel")

if uploaded_excel:
    try:
        with io.BytesIO(uploaded_excel.read()) as bio:
            xl = pd.ExcelFile(bio, engine="openpyxl")
            sheet_names = xl.sheet_names
            st.success(f"Abas encontradas: {', '.join(sheet_names)}")
            for sheet in sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet)
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Baixar aba '{sheet}' como CSV",
                    data=csv_bytes,
                    file_name=f"{sheet}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"Erro ao ler o Excel: {e}")