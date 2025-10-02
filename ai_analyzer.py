import os
import streamlit as st
import google.generativeai as genai

AI_ENABLED = True

PROMPT_IA = """
Você é um advogado especialista em contratos de locação comercial. Analise o contrato abaixo protegendo o LOCATÁRIO.

**TEXTO DO CONTRATO:**
{texto}

**ESTRUTURA DA ANÁLISE (SEJA CONCISO E DIRETO):**

## 📊 RESUMO EXECUTIVO
- Avaliação geral do contrato em 2-3 linhas
- **Nível de risco:** CRÍTICO / ALTO / MÉDIO / BAIXO
- **Recomendação principal:** [ação objetiva]

## ✅ PONTOS POSITIVOS (máx. 5 itens)
Liste apenas os principais benefícios ao locatário, com página.

## ⚠️ RISCOS CRÍTICOS (máx. 5 itens)
Para cada risco:
- **[NÍVEL]** Título do Risco (Página X)
  - **Impacto:** [breve explicação em 1-2 linhas]
  - **Solução:** [ação específica em 1 linha]

## 🔍 PONTOS DE ATENÇÃO (máx. 3 itens)
Ambiguidades ou cláusulas que precisam esclarecimento.

## 📋 DOCUMENTOS FALTANTES (máx. 5 itens)
Liste apenas os essenciais.

## ⚖️ CONFORMIDADE LEGAL
Identifique até 3 violações principais da Lei 8.245/91.

## 🎯 AÇÕES RECOMENDADAS
Liste 3-5 ações prioritárias antes da assinatura.

**IMPORTANTE:** Seja direto, use **negrito** em palavras-chave, máximo 800 palavras.
"""

def configurar_api_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False
        genai.configure(api_key=api_key)
        return True
    except:
        return False

@st.cache_data
def analisar_contrato_com_ia(texto: str) -> str:
    if not configurar_api_gemini():
        return "❌ **Erro:** GEMINI_API_KEY não configurada."
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        resposta = model.generate_content(PROMPT_IA.format(texto=texto))
        return resposta.text
    except Exception as e:
        return f"❌ **Erro:** {e}"