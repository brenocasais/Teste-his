# app_malhas.py  — versão com layout 2-colunas e sem artefato “[0:NULL …]”
import io, textwrap
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns, streamlit as st

st.set_page_config(page_title="Análise de Malhas", layout="wide")
sns.set_theme(context="talk", style="whitegrid")

DIAG_ORDER = [
    "Bom",
    "Muitos ajustes de SP revisar estratégia",
    "Verificar sintonia ou problemas na válvula",
    "Verificar variabilidade do PV",
    "Investigar erro elevado",
    "Válvula saturada",
    "Malha fora do modo correto",
]
PAL     = sns.color_palette("Set2", n_colors=len(DIAG_ORDER))
PAL_MAP = {d: c for d, c in zip(DIAG_ORDER, PAL)}
GRANS   = [("ts_10m", "10 min"), ("ts_1h", "1 h"), ("ts_1d", "1 dia")]

# ---------- utilidades ----------
def coerce_float(s):
    if pd.api.types.is_numeric_dtype(s): return s.astype(float)
    return (s.astype(str).str.replace(",",".").replace(["","nan","None","NaN"],np.nan).astype(float))
def is_number(x):
    try: float(str(x).replace(",", ".")); return True
    except Exception: return False
def mode_equals(series,val):
    return pd.to_numeric(series,errors="coerce")==float(val) if is_number(val) else series.astype(str).str.strip().str.upper()==str(val).strip().upper()
def cv(s): m=s.mean(); return 0. if pd.isna(m) or m==0 else float(s.std()/m)
def classify(r):
    if r["Average Service Factor"]>0.9:
        if pd.isna(r["Average Absolute Error / SP"]) or r["Average Absolute Error / SP"]<0.1:
            if r["Coefficient of Variation (PV)"]<0.1:
                if r["Coefficient of Variation (OP)"]<0.1: return "Bom"
                return "Verificar sintonia ou problemas na válvula"
            denom=r["Coefficient of Variation (PV)"]
            if denom and 0.9<=r["Coefficient of Variation (SP)"]/denom<=1.1:
                return "Muitos ajustes de SP revisar estratégia"
            return "Verificar variabilidade do PV"
        return "Investigar erro elevado"
    return "Malha fora do modo correto" if r["Mode"]>r["OP"] else "Válvula saturada"

def plot_diag(counts, titulo, h=5):
    data = counts.reindex(DIAG_ORDER, fill_value=0).reset_index()
    data.columns = ["Diagnóstico", "Percentual"]
    fig, ax = plt.subplots(figsize=(12, h), dpi=120)
    sns.barplot(data=data, x="Diagnóstico", y="Percentual",
                order=DIAG_ORDER, palette=[PAL_MAP[d] for d in DIAG_ORDER], ax=ax)
    ax.set_ylim(0,100); ax.set_ylabel("%"); ax.set_xlabel("")
    ax.set_title(titulo, fontsize=16, pad=8); ax.grid(axis="y", ls="--", alpha=.3)
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    for p in ax.patches:
        ax.text(p.get_x()+p.get_width()/2, p.get_height()+1, f"{p.get_height():.1f}%",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticklabels([textwrap.fill(l, 22) for l in DIAG_ORDER],
                       rotation=0, ha="center", fontsize=9)
    fig.tight_layout(); return fig  # devolve só fig → evita “[0:NULL …]”

# ---------- Upload ----------
st.sidebar.header("📂 Arquivos")
mode   = st.sidebar.radio("Tipo de entrada", ("Planilhas XLSX","Arquivos CSV"))
spec_up= st.sidebar.file_uploader("Especificações", type="xlsx" if mode=="Planilhas XLSX" else ["csv","txt"])
pids_up= st.sidebar.file_uploader("Dados de Processo", type="xlsx" if mode=="Planilhas XLSX" else ["csv","txt"])
run    = st.sidebar.button("⚙️ Executar análise")

# ---------- Processa só se clicar em Executar ----------
if run:
    if not (spec_up and pids_up): st.error("Envie os dois arquivos."); st.stop()

    specs = pd.read_excel(spec_up) if mode=="Planilhas XLSX" else pd.read_csv(spec_up, sep=None, engine="python")
    pids  = pd.read_excel(pids_up ) if mode=="Planilhas XLSX" else pd.read_csv(pids_up , sep=None, engine="python")
    if "timestamp" not in pids.columns: st.error("timestamp ausente."); st.stop()
    pids["timestamp"]=pd.to_datetime(pids["timestamp"], errors="coerce")
    pids=pids.dropna(subset=["timestamp"]).sort_values("timestamp")

    res={}
    for spec in specs.itertuples(index=False):
        g=str(spec.grupo).strip()
        tags=dict(PV=spec.PV_tag, SP=spec.SP_tag, OP=spec.OP_tag, Mode=spec.Mode_tag)
        if any(t not in pids.columns for t in tags.values()):
            st.warning(f"Tags ausentes para {g}."); continue
        df=pids[["timestamp",*tags.values()]].copy().rename(columns={v:k for k,v in tags.items()})
        df["PV"],df["SP"],df["OP"]=map(coerce_float,[df["PV"],df["SP"],df["OP"]])
        df["ts_10m"]=df["timestamp"].dt.floor("10min"); df["ts_1h"]=df["timestamp"].dt.floor("H"); df["ts_1d"]=df["timestamp"].dt.floor("D")
        dados={}
        for ts_col,label in GRANS:
            rows=[]
            for ts,sub in df.dropna(subset=["PV","SP","OP"]).groupby(ts_col):
                sf=(sub["PV"].between(spec.PV_Lo,spec.PV_Hi)&
                    sub["OP"].between(spec.OP_Lo,spec.OP_Hi)&
                    mode_equals(sub["Mode"],spec.Mode_Normal)).mean()
                abs_rel=np.where(sub["SP"]!=0,(sub["SP"]-sub["PV"]).abs()/sub["SP"],np.nan)
                rows.append({ts_col:ts, "Average Service Factor":sf,
                             "Average Absolute Error / SP":np.nanmean(abs_rel),
                             "Coefficient of Variation (PV)":cv(sub["PV"]),
                             "Coefficient of Variation (SP)":cv(sub["SP"]),
                             "Coefficient of Variation (OP)":cv(sub["OP"]),
                             "Mode":pd.to_numeric(sub["Mode"],errors="coerce").mean(),
                             "OP":sub["OP"].mean()})
            met=pd.DataFrame(rows); met["diagnóstico"]=met.apply(classify,axis=1)
            dados[label]=met
        res[g]=dados
    st.session_state["res"]=res; st.session_state["malhas"]=list(res.keys()); st.session_state["ready"]=False
    st.success("✅ Análise concluída – configure a visualização e clique *Gerar visualização*.")

if "res" not in st.session_state: st.info("Carregue arquivos e clique em *Executar análise*."); st.stop()

# ---------- Seletores ----------
vis = st.selectbox("Visão", ["Uma malha / um tempo","Uma malha / todos os tempos","Todas as malhas / todos os tempos"], key="sel_vis")
if vis.startswith("Uma malha"):
    st.selectbox("Malha", st.session_state["malhas"], key="sel_malha")
    if vis=="Uma malha / um tempo": st.selectbox("Granularidade", [l for _,l in GRANS], key="sel_gran")
if st.button("📊 Gerar visualização"): st.session_state["ready"]=True
if not st.session_state.get("ready"): st.stop()

# ---------- Renderização ----------
res = st.session_state["res"]
if vis=="Uma malha / um tempo":
    g = st.session_state["sel_malha"]; gran = st.session_state["sel_gran"]
    df = res[g][gran]; st.dataframe(df, use_container_width=True)
    st.pyplot(plot_diag(df["diagnóstico"].value_counts(normalize=True)*100, f"{g} — {gran}"))

elif vis=="Uma malha / todos os tempos":
    g = st.session_state["sel_malha"]; graphs=[]
    for _,label in GRANS:
        df=res[g][label]; counts=df["diagnóstico"].value_counts(normalize=True)*100
        graphs.append(plot_diag(counts,f"{g} — {label}",h=4.5))
    # até 2 por linha
    for i,fig in enumerate(graphs):
        if i%2==0: cols=st.columns(2)
        cols[i%2].pyplot(fig)

else:  # todas malhas
    for g in st.session_state["malhas"]:
        st.subheader(f"🔹 {g}")
        figs=[]
        for _,label in GRANS:
            df=res[g][label]; counts=df["diagnóstico"].value_counts(normalize=True)*100
            figs.append(plot_diag(counts,f"{g} — {label}",h=4))
        # 2 por linha
        for i,fig in enumerate(figs):
            if i%2==0: cols=st.columns(2)
            cols[i%2].pyplot(fig)
