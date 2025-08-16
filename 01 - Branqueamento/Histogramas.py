"""
Streamlit app — KPIs de Branqueamento
Histogramas, Capabilidade e Filtros Dinâmicos
Rev. 13-Aug-2025 — legenda PT-BR configurável + Nome(Tag) + figuras Nome_Tag
  • Cp/Cpk com desvio-padrão GLOBAL (Std).
  • Pp/Ppk com σ within (MR/D2) apenas como referência.
  • Limites teóricos (±3·σ_within) opcionais (visual/uso comparativo).
  • Legenda configurável (Seção 3.1), tudo marcado por padrão, em português.
  • Filtros/seleção mostram "Nome (Tag)". Figuras salvas como "Nome_Tag.png".
  • Produção = filtro GLOBAL. Demais variáveis = filtros LOCAIS por gráfico.
  • Remoção de outliers por variável (IQR ou Z-score).
  • Regra adicional: após Produção, cada variável do histograma é forçada a > 0.
"""

import io
import re
import zipfile
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
