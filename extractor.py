import fitz
import re

def extrair_texto_local(caminho_pdf):
    try:
        doc = fitz.open(caminho_pdf)
        texto = [f"--- PÁGINA {p.number + 1} ---\n{p.get_text('text')}\n\n" for p in doc]
        doc.close()
        return "".join(texto), None
    except Exception as e:
        return None, f"Erro ao ler PDF: {e}"

def extrair_clausulas_chave(texto: str) -> dict:
    alertas_criticos, alertas_graves, alertas_moderados = [], [], []
    pontos_positivos, dados_essenciais = [], []
    
    # Dados essenciais - Extração por padrões
    padroes_dados = {
        "Valor do Aluguel": r"(?:valor|aluguel|aluguer).*?R\$\s*([\d\.,]+)",
        "Prazo do Contrato": r"(?:prazo|período|vigência).*?(\d+)\s*(?:meses|anos)",
        "Índice de Reajuste": r"(?:reajust|corrigi).*?(?:IGP-M|IPCA|INPC|[\w\-]+)",
        "Dia de Vencimento": r"(?:vencimento|pagamento).*?dia\s*(\d+)",
        "Multa por Rescisão": r"(?:multa|penalidade).*?(?:rescis|quebra).*?(\d+)\s*(?:%|meses)",
        "Caução/Depósito": r"(?:caução|depósito|garantia).*?R\$\s*([\d\.,]+)",
    }
    for tipo_dado, padrao in padroes_dados.items():
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            valor_extraido = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else match.group(0).strip()
            dados_essenciais.append({"tipo": tipo_dado, "valor": valor_extraido})

    # Padrões de risco - análise detalhada
    todos_padroes_risco = {
        "Venda Durante Locação": {"padroes": [r"(?:venda|alienação).*?(?:durante|vigência)", r"(?:caso|se).*?(?:vend|aliene).*?(?:locatário|inquilino).*?(?:desocup|sair)"], "nivel": "CRÍTICO", "impacto": "Risco de despejo forçado se o imóvel for vendido durante a locação."},
        "Obrigação de Desfazer Reformas": {"padroes": [r"(?:desfazer|reverter|retornar|restaurar).*?(?:estado\s+original|condições\s+originais)", r"(?:remover|retirar).*?(?:benfeitorias|melhorias|alterações)"], "nivel": "CRÍTICO", "impacto": "Você perde todo o investimento em melhorias e ainda tem o custo de remover tudo."},
        "Benfeitorias sem Indenização": {"padroes": [r"(?:renuncia|abdica).*?(?:indenização|reembolso).*?(?:benfeitorias|melhorias)", r"sem.*?(?:direito|indenização).*?benfeitorias"], "nivel": "CRÍTICO", "impacto": "Qualquer melhoria feita no imóvel (mesmo necessária) não será reembolsada."},
        "Multa Proporcional Mal Calculada": {"padroes": [r"multa.*?(?:integral|total).*?(?:independente|não\s+proporcional)", r"multa.*?equivalente.*?(?:totalidade|todos\s+os\s+meses)"], "nivel": "CRÍTICO", "impacto": "A multa por quebra de contrato pode ser cobrada integralmente, mesmo se você já tiver cumprido parte do contrato."},
        "Despejo Imotivado": {"padroes": [r"(?:retomar|reaver|recuperar).*?(?:sem\s+motivo|sem\s+justificativa)", r"(?:locador|proprietário).*?poderá.*?(?:rescindir|denunciar).*?(?:imotivadamente|sem\s+causa)"], "nivel": "CRÍTICO", "impacto": "Permite ao locador pedir o imóvel de volta a qualquer momento, sem justificativa legal."},
        "Visitação Abusiva": {"padroes": [r"(?:visitar|inspecionar|vistoriar).*?(?:a\s+qualquer|quando\s+quiser|sem\s+aviso)", r"(?:acesso|entrada).*?(?:livre|irrestrito).*?(?:locador|proprietário)"], "nivel": "CRÍTICO", "impacto": "Violação da sua privacidade com visitas sem aviso prévio ou a qualquer hora."},
        "Direito de Preferência Negado": {"padroes": [r"(?:renuncia|abdica|dispensa).*?(?:preferência|prioridade)", r"sem.*?direito.*?(?:preferência|compra)"], "nivel": "GRAVE", "impacto": "Você perde o direito legal de comprar o imóvel se o proprietário decidir vender."},
        "Responsabilidade por Jardim/Piscina": {"padroes": [r"(?:locatário|inquilino).*?(?:responsável|responsabilidade).*?(?:jardim|piscina|área\s+externa)", r"(?:manutenção|conservação).*?(?:jardim|piscina).*?(?:locatário|inquilino)"], "nivel": "GRAVE", "impacto": "Custos adicionais significativos com manutenção de áreas externas."},
        "Proibição Total de Alterações": {"padroes": [r"(?:proibid|vedad|impedi).*?(?:qualquer|toda|nenhuma).*?(?:alteração|modificação|reforma)", r"nenhuma.*?(?:alteração|modificação).*?(?:permit|autoriz)"], "nivel": "GRAVE", "impacto": "Impede até mesmo pequenas melhorias básicas."},
        "Prazo de Desocupação Curto": {"padroes": [r"(?:desocupar|entregar|devolver).*?(?:em|no\s+prazo\s+de)\s*(\d+)\s*dias", r"(?:rescisão|término).*?desocup.*?(\d+)\s*dias"], "nivel": "GRAVE", "impacto": "Prazo muito curto (menos de 30 dias) para desocupar o imóvel."},
        "Chaves com Terceiros": {"padroes": [r"(?:chaves|cópias).*?(?:porteiro|síndico|imobiliária|administradora)", r"(?:acesso|entrada).*?(?:porteiro|síndico).*?(?:emergência|inspeção)"], "nivel": "GRAVE", "impacto": "Terceiros podem ter acesso ao seu imóvel, comprometendo a segurança."},
        "Multa por Atraso Excessiva": {"padroes": [r"(?:multa|penalidade).*?(?:atraso|inadimpl).*?(\d+)\s*%", r"(?:mora|atraso).*?(\d+)\s*(?:por\s+cento|%)"], "nivel": "MODERADO", "impacto": "Multa por atraso superior a 10% é considerada abusiva."},
        "Juros Abusivos": {"padroes": [r"juros.*?(\d+)\s*%.*?(?:mês|mensal|ao\s+mês)", r"correção.*?juros.*?(\d+)\s*%"], "nivel": "MODERADO", "impacto": "Juros acima de 1% ao mês podem ser considerados abusivos."},
    }
    
    # Análise de riscos
    for categoria, config in todos_padroes_risco.items():
        for padrao in config["padroes"]:
            for match in re.finditer(padrao, texto, re.IGNORECASE | re.MULTILINE):
                contexto_texto = match.group(0)
                alerta = {"categoria": categoria, "detalhe": config["impacto"], "contexto": contexto_texto[:200]}
                if categoria == "Multa por Atraso Excessiva":
                    percentual = re.search(r'(\d+)', contexto_texto)
                    if percentual and int(percentual.group(1)) <= 10: continue
                if categoria == "Juros Abusivos":
                    percentual = re.search(r'(\d+)', contexto_texto)
                    if percentual and int(percentual.group(1)) <= 1: continue
                if categoria == "Prazo de Desocupação Curto":
                    dias = re.search(r'(\d+)', contexto_texto)
                    if dias and int(dias.group(1)) >= 30: continue
                if config["nivel"] == "CRÍTICO" and not any(a['contexto'] == alerta['contexto'] for a in alertas_criticos):
                    alertas_criticos.append(alerta)
                elif config["nivel"] == "GRAVE" and not any(a['contexto'] == alerta['contexto'] for a in alertas_graves):
                    alertas_graves.append(alerta)
                elif config["nivel"] == "MODERADO" and not any(a['contexto'] == alerta['contexto'] for a in alertas_moderados):
                    alertas_moderados.append(alerta)

    # Pontos positivos - análise de proteções
    padroes_positivos = {
        "Multa Proporcional": r"multa.*?proporcional.*?(?:período|tempo).*?(?:cumprido|decorrido)",
        "Direito de Preferência": r"(?:locatário|inquilino).*?(?:direito|preferência).*?(?:compra|aquisição)",
        "Indenização por Benfeitorias": r"(?:indenizaç|reembols).*?benfeitorias.*?(?:necessárias|úteis)",
        "Aviso Prévio para Visitas": r"(?:aviso|comunicação).*?(?:prévio|antecedência).*?(?:visita|inspeção)",
        "Prazo de Carência": r"(?:carência|isenção).*?(?:primeiros|inicial).*?(?:meses|período)",
    }
    for tipo_positivo, padrao in padroes_positivos.items():
        if re.search(padrao, texto, re.IGNORECASE):
            pontos_positivos.append(tipo_positivo)

    # Cálculo de score e recomendação
    score = min(100, (len(alertas_criticos) * 15) + (len(alertas_graves) * 8) + (len(alertas_moderados) * 3))
    
    if score >= 30: recomendacao_geral = "❌ NÃO ASSINAR"
    elif score >= 15: recomendacao_geral = "⚠️ NEGOCIAR OBRIGATÓRIO"
    elif score > 0: recomendacao_geral = "⚡ REVISAR COM CUIDADO"
    else: recomendacao_geral = "✅ APARENTEMENTE SEGURO"
    
    return {
        "dados_essenciais": dados_essenciais,
        "alertas_criticos": alertas_criticos,
        "alertas_graves": alertas_graves,
        "alertas_moderados": alertas_moderados,
        "pontos_positivos": pontos_positivos,
        "resumo_riscos": {
            "score_risco": score,
            "total_criticos": len(alertas_criticos),
            "total_graves": len(alertas_graves),
            "total_moderados": len(alertas_moderados),
            "recomendacao_geral": recomendacao_geral
        }
    }