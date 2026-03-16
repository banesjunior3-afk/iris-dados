import streamlit as st
import pandas as pd
import anthropic
import os
import unicodedata

st.set_page_config(page_title="Íris — Estrategista Eleitoral", page_icon="🗳️", layout="centered")

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
)

@st.cache_data
def carregar_dados():
    base = "https://raw.githubusercontent.com/banesjunior3-afk/iris-dados/main/"
    merged    = pd.read_csv(base + "votacao_2022.csv")
    merged_18 = pd.read_csv(base + "votacao_2018.csv")
    indice    = pd.read_csv(base + "indice_candidatos.csv")
    merged_16 = pd.read_csv(base + "votacao_2016.csv")
    merged_20 = pd.read_csv(base + "votacao_2020.csv")
    return merged, merged_18, merged_16, merged_20, indice

@st.cache_data
def carregar_perfil():
    base = "https://raw.githubusercontent.com/banesjunior3-afk/iris-dados/main/"
    return pd.read_csv(base + "perfil_municipio.csv")

@st.cache_data
def carregar_eleitos():
    base = "https://raw.githubusercontent.com/banesjunior3-afk/iris-dados/main/"
    est     = pd.read_csv(base + "eleitos_estadual_2022_mg.csv")
    fed     = pd.read_csv(base + "eleitos_federal_2022_mg.csv")
    ver_16  = pd.read_csv(base + "eleitos_vereador_2016_mg.csv")
    pref_16 = pd.read_csv(base + "eleitos_prefeito_2016_mg.csv")
    ver_20  = pd.read_csv(base + "eleitos_vereador_2020_mg.csv")
    pref_20 = pd.read_csv(base + "eleitos_prefeito_2020_mg.csv")
    return est, fed, ver_16, pref_16, ver_20, pref_20

merged, merged_2018, merged_2016, merged_20, indice_candidatos = carregar_dados()
eleitos_estadual, eleitos_federal, eleitos_vereador_16, eleitos_prefeito_16, eleitos_vereador_20, eleitos_prefeito_20 = carregar_eleitos()

def normalizar(texto):
    return unicodedata.normalize("NFKD", str(texto)).encode("ASCII","ignore").decode("ASCII").upper().strip()

@st.cache_data
def lista_municipios():
    return set(merged["NM_MUNICIPIO"].apply(normalizar).unique())

MUNICIPIOS = lista_municipios()

PALAVRAS_IGNORAR = {
    "BOM","DIA","BOA","TARDE","NOITE","OI","OLA","IRIS","TUDO","BEM",
    "OBRIGADO","OBRIGADA","SIM","NAO","OK","CERTO","PODE","VAMOS","LA","AI",
    "EU","TU","ELE","ELA","NOS","VOS","ELES","ELAS","MEU","MINHA","SEU","SUA",
    "NOVO","NOVA","QUERO","SABER","SOBRE","COMO","QUAL","QUANDO","ONDE","POR",
    "CANDIDATO","CANDIDATA","ESTRATEGIA","CONFUSO","AINDA","MEIO","AJUDA",
    "MONTAR","PRIMEIRA","CANDIDATURA","CIDADE","ESTADO","PARTIDO",
    "DEPUTADO","FEDERAL","ESTADUAL","SENADOR","GOVERNADOR","PREFEITO","VEREADOR",
    "VOTOS","ELEICAO","CAMPANHA","DADOS","ANALISE","PERFIL","ELEITOR","MUNICIPIO",
    "REGIAO","TERRITORIO","SCORE","PRIORIDADE","INVESTIR","DIGITAL","TOP","PIOR",
    "MELHOR","RANKING","LISTA","QUAIS","ONDE","FOI","BEM","MAL","PIORES","MELHORES",
    "CRIOU","QUEM","DESENVOLVEU","CONSTRUIU"
}

def foi_eleito(nome, cargo):
    nome_norm = normalizar(nome)
    cargo_norm = normalizar(cargo)

    if "ESTADUAL" in cargo_norm:
        df = eleitos_estadual.copy()
        df["NM_NORM"] = df["NM_VOTAVEL"].apply(normalizar)
        return True if len(df[df["NM_NORM"].str.contains(nome_norm, na=False, regex=False)]) > 0 else False

    if "FEDERAL" in cargo_norm:
        df = eleitos_federal.copy()
        df["NM_NORM"] = df["NM_VOTAVEL"].apply(normalizar)
        return True if len(df[df["NM_NORM"].str.contains(nome_norm, na=False, regex=False)]) > 0 else False

    if "VEREADOR" in cargo_norm:
        for df_ver in [eleitos_vereador_20, eleitos_vereador_16]:
            df_ver = df_ver.copy()
            df_ver["NM_NORM"] = df_ver["NM_VOTAVEL"].apply(normalizar)
            if len(df_ver[df_ver["NM_NORM"].str.contains(nome_norm, na=False, regex=False)]) > 0:
                return True
        return False

    if "PREFEITO" in cargo_norm:
        for df_pref in [eleitos_prefeito_20, eleitos_prefeito_16]:
            df_pref = df_pref.copy()
            df_pref["NM_NORM"] = df_pref["NM_VOTAVEL"].apply(normalizar)
            if len(df_pref[df_pref["NM_NORM"].str.contains(nome_norm, na=False, regex=False)]) > 0:
                return True
        return False

    return None

def contem_municipio(texto):
    texto_norm = normalizar(texto)
    palavras = texto_norm.split()
    for tamanho in range(4, 0, -1):
        for i in range(len(palavras) - tamanho + 1):
            trecho = " ".join(palavras[i:i+tamanho])
            if trecho in MUNICIPIOS:
                return trecho
    return None

def buscar_candidato(texto):
    texto_upper = normalizar(texto)
    palavras = [p for p in texto_upper.split() if p not in PALAVRAS_IGNORAR and len(p) >= 2]
    if not palavras:
        return pd.DataFrame()
    indice_norm = indice_candidatos.copy()
    indice_norm["NM_NORM"] = indice_norm["NM_VOTAVEL"].apply(normalizar)
    for tamanho in range(len(palavras), 1, -1):
        for i in range(len(palavras) - tamanho + 1):
            trecho = " ".join(palavras[i:i+tamanho])
            r = indice_norm[indice_norm["NM_NORM"].str.contains(trecho, na=False, regex=False)][["NM_VOTAVEL","DS_CARGO","ANO"]].drop_duplicates()
            if 0 < len(r) <= 15:
                return r
    for palavra in palavras:
        if len(palavra) >= 4:
            r = indice_norm[indice_norm["NM_NORM"].str.contains(palavra, na=False, regex=False)][["NM_VOTAVEL","DS_CARGO","ANO"]].drop_duplicates()
            if 0 < len(r) <= 20:
                return r
    if len(palavras) >= 2:
        mask = pd.Series([True] * len(indice_norm), index=indice_norm.index)
        for palavra in palavras:
            if len(palavra) >= 4:
                mask = mask & indice_norm["NM_NORM"].str.contains(palavra, na=False, regex=False)
        r = indice_norm[mask][["NM_VOTAVEL","DS_CARGO","ANO"]].drop_duplicates()
        if 0 < len(r) <= 15:
            return r
    return pd.DataFrame()

def normalizar_cargo(cargo):
    cargo_norm = cargo.upper().replace("_"," ").strip()
    for ano in ["2022","2018","2020","2016","2014"]:
        cargo_norm = cargo_norm.replace(ano,"").strip()
    return cargo_norm.strip()

def analisar_candidato(nome, cargo):
    nome_norm = normalizar(nome)
    cargo_norm = normalizar_cargo(cargo)
    eh_municipal = any(c in cargo_norm for c in ["VEREADOR","PREFEITO"])

    if eh_municipal:
        resultados = []
        for df_ano, ano_label in [(merged_20, "2020"), (merged_2016, "2016")]:
            df_norm = df_ano.copy()
            df_norm["NM_NORM"] = df_norm["NM_VOTAVEL"].apply(normalizar)
            df_norm["CARGO_NORM"] = df_norm["DS_CARGO"].apply(normalizar)
            df_filtrado = df_norm[
                (df_norm["NM_NORM"].str.contains(nome_norm, na=False, regex=False)) &
                (df_norm["CARGO_NORM"].str.contains(cargo_norm, na=False, regex=False))
            ][["NM_MUNICIPIO","QT_VOTOS","PCT_VOTOS"]].copy()
            if len(df_filtrado) > 0:
                resultados.append((ano_label, df_filtrado))

        if not resultados:
            return None

        ano_label, df_principal = resultados[0]
        total = df_principal["QT_VOTOS"].sum()
        municipios = len(df_principal)
        top10_votos  = df_principal.sort_values("QT_VOTOS", ascending=False).head(10)
        top10_pct    = df_principal.sort_values("PCT_VOTOS", ascending=False).head(10)
        bottom10_pct = df_principal.sort_values("PCT_VOTOS", ascending=True).head(10)

        eleicao_status = foi_eleito(nome, cargo)
        status_str = "RESULTADO: ELEITO" if eleicao_status else "RESULTADO: NAO ELEITO"

        comp_str = ""
        if len(resultados) == 2:
            _, df_anterior = resultados[1]
            comp = df_principal.merge(
                df_anterior[["NM_MUNICIPIO","PCT_VOTOS"]].rename(columns={"PCT_VOTOS":"PCT_ANT"}),
                on="NM_MUNICIPIO", how="left"
            )
            comp["PCT_ANT"] = comp["PCT_ANT"].fillna(0)
            comp["TENDENCIA"] = (comp["PCT_VOTOS"] - comp["PCT_ANT"]).round(2)
            top_cresc = comp.nlargest(5,"TENDENCIA")[["NM_MUNICIPIO","PCT_VOTOS","PCT_ANT","TENDENCIA"]]
            top_queda = comp.nsmallest(5,"TENDENCIA")[["NM_MUNICIPIO","PCT_VOTOS","PCT_ANT","TENDENCIA"]]
            comp_str = f"""
EVOLUCAO 2016-2020 — TOP 5 CRESCIMENTO:
{top_cresc.to_string(index=False)}
EVOLUCAO 2016-2020 — TOP 5 QUEDA:
{top_queda.to_string(index=False)}"""

        return f"""DADOS REAIS TSE — {nome.upper()} — {cargo_norm} — MG {ano_label}
{status_str}
Total de votos: {total:,.0f} | Municipios: {municipios}
TOP 10 POR VOLUME: {top10_votos.to_string(index=False)}
TOP 10 POR %: {top10_pct.to_string(index=False)}
MENOR PENETRACAO: {bottom10_pct.to_string(index=False)}
{comp_str}"""

    else:
        merged_norm = merged.copy()
        merged_norm["NM_NORM"] = merged_norm["NM_VOTAVEL"].apply(normalizar)
        merged_norm["CARGO_NORM"] = merged_norm["DS_CARGO"].apply(normalizar)
        df22 = merged_norm[
            (merged_norm["NM_NORM"].str.contains(nome_norm, na=False, regex=False)) &
            (merged_norm["CARGO_NORM"].str.contains(cargo_norm, na=False, regex=False))
        ][["NM_MUNICIPIO","QT_VOTOS","PCT_VOTOS"]].copy()
        if len(df22) == 0:
            df22 = merged_norm[merged_norm["NM_NORM"].str.contains(nome_norm, na=False, regex=False)][["NM_MUNICIPIO","QT_VOTOS","PCT_VOTOS"]].copy()
        if len(df22) == 0:
            return None

        merged_18_norm = merged_2018.copy()
        merged_18_norm["NM_NORM"] = merged_2018["NM_VOTAVEL"].apply(normalizar)
        df18 = merged_18_norm[merged_18_norm["NM_NORM"].str.contains(nome_norm, na=False, regex=False)][["NM_MUNICIPIO","PCT_2018"]].copy()

        total = df22["QT_VOTOS"].sum()
        municipios = len(df22)
        top10_votos  = df22.sort_values("QT_VOTOS", ascending=False).head(10)
        top10_pct    = df22.sort_values("PCT_VOTOS", ascending=False).head(10)
        bottom10_pct = df22.sort_values("PCT_VOTOS", ascending=True).head(10)

        eleicao_status = foi_eleito(nome, cargo)
        status_str = "RESULTADO 2022: ELEITO" if eleicao_status else "RESULTADO 2022: NAO ELEITO"

        comp_str = "Sem dados de 2018."
        score_str = ""
        if len(df18) > 0:
            comp = df22.merge(df18, on="NM_MUNICIPIO", how="left")
            comp["PCT_2018"] = comp["PCT_2018"].fillna(0)
            comp["TENDENCIA"] = (comp["PCT_VOTOS"] - comp["PCT_2018"]).round(2)
            comp["SCORE"] = (comp["PCT_VOTOS"] * 0.6 + comp["TENDENCIA"] * 0.4).round(2)
            comp["PRIORIDADE"] = pd.cut(comp["SCORE"],bins=[-999,15,30,45,999],labels=["EVITAR","ATIVAR","INVESTIR","PRIORIDADE MAXIMA"])
            top_cresc = comp.nlargest(5,"TENDENCIA")[["NM_MUNICIPIO","PCT_VOTOS","PCT_2018","TENDENCIA"]]
            top_queda = comp.nsmallest(5,"TENDENCIA")[["NM_MUNICIPIO","PCT_VOTOS","PCT_2018","TENDENCIA"]]
            p_max = len(comp[comp["PRIORIDADE"]=="PRIORIDADE MAXIMA"])
            p_inv = len(comp[comp["PRIORIDADE"]=="INVESTIR"])
            p_ati = len(comp[comp["PRIORIDADE"]=="ATIVAR"])
            p_evi = len(comp[comp["PRIORIDADE"]=="EVITAR"])
            top_prior = comp[comp["PRIORIDADE"]=="PRIORIDADE MAXIMA"].nlargest(10,"SCORE")[["NM_MUNICIPIO","SCORE","PCT_VOTOS","PCT_2018"]]
            comp_str = f"""EVOLUCAO 2018-2022:
TOP 5 CRESCIMENTO: {top_cresc.to_string(index=False)}
TOP 5 QUEDA: {top_queda.to_string(index=False)}"""
            score_str = f"""SCORE: Prioridade Maxima: {p_max} | Investir: {p_inv} | Ativar: {p_ati} | Evitar: {p_evi}
TOP 10 PRIORIDADE MAXIMA: {top_prior.to_string(index=False)}"""

        return f"""DADOS REAIS TSE — {nome.upper()} — {cargo_norm} — MG 2022
{status_str}
Total: {total:,.0f} votos | Municipios: {municipios}
TOP 10 VOLUME: {top10_votos.to_string(index=False)}
TOP 10 %: {top10_pct.to_string(index=False)}
MENOR PENETRACAO: {bottom10_pct.to_string(index=False)}
{comp_str}
{score_str}"""

def perfil_municipio(municipio):
    try:
        perfil = carregar_perfil()
        mun_norm = normalizar(municipio)
        perfil["MUN_NORM"] = perfil["NM_MUNICIPIO"].apply(normalizar)
        mun = perfil[perfil["MUN_NORM"] == mun_norm]
        if len(mun) == 0:
            mun = perfil[perfil["MUN_NORM"].str.contains(mun_norm, na=False, regex=False)]
        if len(mun) == 0:
            return None
        nome_mun = mun["NM_MUNICIPIO"].iloc[0]
        genero       = mun.groupby("DS_GENERO")["QT_ELEITORES_PERFIL"].sum().reset_index().sort_values("QT_ELEITORES_PERFIL",ascending=False)
        faixa        = mun.groupby("DS_FAIXA_ETARIA")["QT_ELEITORES_PERFIL"].sum().reset_index().sort_values("QT_ELEITORES_PERFIL",ascending=False).head(8)
        escolaridade = mun.groupby("DS_GRAU_ESCOLARIDADE")["QT_ELEITORES_PERFIL"].sum().reset_index().sort_values("QT_ELEITORES_PERFIL",ascending=False)
        raca         = mun.groupby("DS_RACA_COR")["QT_ELEITORES_PERFIL"].sum().reset_index().sort_values("QT_ELEITORES_PERFIL",ascending=False)
        total        = mun["QT_ELEITORES_PERFIL"].sum()
        return f"""PERFIL — {nome_mun}
Total eleitores: {total:,.0f}
GENERO: {genero.to_string(index=False)}
FAIXA ETARIA: {faixa.to_string(index=False)}
ESCOLARIDADE: {escolaridade.to_string(index=False)}
RACA/COR: {raca.to_string(index=False)}"""
    except:
        return None

def concorrentes_municipio(municipio, cargo="DEPUTADO ESTADUAL"):
    try:
        mun_norm   = normalizar(municipio)
        cargo_norm = normalizar(cargo)
        eh_municipal = any(c in cargo_norm for c in ["VEREADOR","PREFEITO"])
        df_base = merged_20.copy() if eh_municipal else merged.copy()
        df_base["MUN_NORM"]   = df_base["NM_MUNICIPIO"].apply(normalizar)
        df_base["CARGO_NORM"] = df_base["DS_CARGO"].apply(normalizar)
        df = df_base[
            (df_base["MUN_NORM"] == mun_norm) &
            (df_base["CARGO_NORM"].str.contains(cargo_norm, na=False, regex=False))
        ][["NM_VOTAVEL","QT_VOTOS","PCT_VOTOS"]].sort_values("QT_VOTOS",ascending=False).head(20)
        if len(df) == 0:
            return None
        total_mun = df["QT_VOTOS"].sum()
        df = df.copy()
        df["STATUS"] = df["NM_VOTAVEL"].apply(lambda x: "ELEITO" if foi_eleito(x, cargo) else "")
        ano_ref = "2020" if eh_municipal else "2022"
        return f"""CENARIO — {municipio.upper()} — {cargo.upper()} {ano_ref}
Total votos no cargo: {total_mun:,.0f}
TOP 20: {df.to_string(index=False)}"""
    except:
        return None

st.title("🗳️ Íris")
st.caption("Estrategista eleitoral digital — dados reais do TSE/MG")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "historico_display" not in st.session_state:
    st.session_state.historico_display = []
if "candidato_ativo" not in st.session_state:
    st.session_state.candidato_ativo = None

sistema = """Voce e Iris, uma inteligencia artificial eleitoral criada por Banes Junior para o ciclo eleitoral 2026.

CONTEXTO ELEITORAL 2026:
- 2026 e ano de ELEICOES GERAIS: governador, senador, deputado federal e deputado estadual.
- NAO ha eleicoes municipais em 2026.
- Dados municipais (2016 e 2020) existem para candidatos com historico como vereador ou prefeito que agora disputam cargo estadual ou federal — use esses dados para mapear a base territorial deles.

REGRA DE OURO — ENTREVISTA PRIMEIRO:
Antes de qualquer analise, voce DEVE entender quem e o candidato. Faca UMA pergunta por vez, de forma natural, ate ter:
1. Cargo pretendido em 2026
2. Municipio ou regiao base
3. Partido ou campo politico
4. Principais pautas e bandeiras
5. Historico — ja teve mandato? Foi vereador, prefeito?
6. Publico natural — quem ja te conhece?

SO DEPOIS de ter essas informacoes, busque dados e gere analise.

NIVEL DE ANALISE — PADRAO SENIOR:
- Diagnostico territorial preciso com numeros reais
- Identificacao de oportunidades nao obvias
- Leitura de riscos e armadilhas
- Recomendacoes concretas e priorizadas
- Contexto politico que explica os numeros
- NUNCA de perfil demografico generico sem dados reais que o comprovem
- NUNCA diga "seu eleitorado e mulheres" sem dados que provem isso
- Se nao tiver dados suficientes, diga claramente e sugira o que buscar

FORMATO VISUAL:
- Emojis nos titulos (📊 🎯 ⚠️ 💡 🏆 📍 🗺️ 👤 📣 🚀)
- **Negrito** para dados criticos
- Secoes claras
- Respostas objetivas — sem enrolacao

APRESENTACAO INICIAL:
Curta, impactante, no maximo 3 linhas. Personalidade forte. Sem listar funcionalidades.

QUANDO GERAR RELATORIO COMPLETO:
1. 🎯 Diagnostico Geral
2. 🗺️ Mapeamento Territorial
3. 👤 Perfil do Eleitorado
4. ⚔️ Analise da Concorrencia
5. 💡 Oportunidades Nao Obvias
6. ⚠️ Riscos e Armadilhas
7. 🚀 Proximas Etapas

SE PERGUNTAREM QUEM TE CRIOU: Banes Junior — estrategista digital que quis democratizar inteligencia territorial que antes so grandes campanhas podiam pagar.

REGRAS ABSOLUTAS:
1. NUNCA invente dados. Use APENAS dados fornecidos pelo sistema.
2. NUNCA exiba blocos tecnicos na resposta.
3. Faca a entrevista estrategica antes de qualquer analise.
4. Comandos de busca — SEMPRE em linha isolada:
   BUSCAR_DADOS::NOME_EXATO::CARGO
   BUSCAR_PERFIL::NOME_MUNICIPIO
   BUSCAR_CONCORRENTES::NOME_MUNICIPIO::CARGO
5. Para candidato novo — busque PERFIL e CONCORRENTES do municipio APOS entrevista.
6. Linguagem sempre profissional e respeitosa.
7. Uma pergunta por vez."""

for msg in st.session_state.historico_display:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not st.session_state.historico:
    with st.chat_message("assistant"):
        msg_inicial = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=sistema,
            messages=[{"role":"user","content":"Apresente-se. Seja direta e impactante — maximo 3 linhas. Personalidade forte. Sem listar funcionalidades. Ano atual: 2026, eleicoes gerais."}]
        ).content[0].text
        st.write(msg_inicial)
        st.session_state.historico.append({"role":"assistant","content":msg_inicial})
        st.session_state.historico_display.append({"role":"assistant","content":msg_inicial})

user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    municipio_detectado = contem_municipio(user_input)
    eh_candidato_novo = any(p in normalizar(user_input) for p in [
        "PRIMEIRA CANDIDATURA","CANDIDATO NOVO","CANDIDATURA NOVA","PRIMEIRA VEZ",
        "ESTREANTE","NAO CONCORRI","NUNCA CONCORRI","QUERO SER CANDIDATO","PRIMEIRA ELEICAO"
    ])

    resultado_busca = pd.DataFrame()
    if not eh_candidato_novo:
        resultado_busca = buscar_candidato(user_input)

    contexto = ""
    if len(resultado_busca) > 0:
        contexto += f"\n\n[SISTEMA] CANDIDATOS_ENCONTRADOS (nao exibir):\n{resultado_busca.to_string(index=False)}"
    if municipio_detectado:
        contexto += f"\n\n[SISTEMA] MUNICIPIO_DETECTADO: {municipio_detectado}"
    if st.session_state.candidato_ativo:
        ca = st.session_state.candidato_ativo
        contexto += f"\n\n[SISTEMA] DADOS_CANDIDATO_ATIVO — {ca['nome']} — {ca['cargo']}:\n{ca['dados']}"

    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.historico_display.append({"role":"user","content":user_input})
    st.session_state.historico.append({"role":"user","content":user_input+contexto})

    if len(st.session_state.historico) > 24:
        st.session_state.historico = st.session_state.historico[-24:]

    def limpar(texto):
        BLOCOS = [
            "BUSCAR_DADOS::","BUSCAR_PERFIL::","BUSCAR_CONCORRENTES::",
            "[SISTEMA]","CANDIDATOS_ENCONTRADOS","DADOS_TSE:","PERFIL_ELEITORADO:",
            "CONCORRENTES:","DADOS_CANDIDATO_ATIVO","NM_VOTAVEL","NR_VOTAVEL",
            "SG_PARTIDO","QT_VOTOS_NOMINAIS","VOTO EM BRANCO","VOTO EM LEGENDA",
            "NM_MUNICIPIO","QT_VOTOS","Analise e entregue","Analise concorr"
        ]
        linhas = texto.split("\n")
        limpas = [l for l in linhas if not any(b in l for b in BLOCOS)]
        return "\n".join(limpas).strip()

    with st.chat_message("assistant"):
        with st.spinner("Analisando..."):
            resposta = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=sistema,
                messages=st.session_state.historico
            ).content[0].text

        resposta_final = None

        if "BUSCAR_DADOS::" in resposta:
            try:
                linha = [l for l in resposta.split("\n") if "BUSCAR_DADOS::" in l][0]
                partes = linha.split("::")
                nome_cand  = partes[1].strip()
                cargo_cand = partes[2].strip() if len(partes) > 2 else "DEPUTADO FEDERAL"
                with st.spinner(f"Buscando dados de {nome_cand}..."):
                    dados = analisar_candidato(nome_cand, cargo_cand)
                if dados:
                    st.session_state.candidato_ativo = {"nome":nome_cand,"cargo":cargo_cand,"dados":dados}
                    st.session_state.historico.append({"role":"assistant","content":resposta})
                    st.session_state.historico.append({"role":"user","content":f"[SISTEMA] DADOS_TSE:\n{dados}\n\nGere analise estrategica senior com formatacao visual rica."})
                    with st.spinner("Gerando analise..."):
                        resposta_final = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=3000,
                            system=sistema,
                            messages=st.session_state.historico
                        ).content[0].text
                else:
                    resposta_final = f"Nao encontrei dados para **{nome_cand}**. Pode confirmar o nome exato como aparece na urna?"
            except:
                resposta_final = "Erro ao buscar dados. Pode repetir o nome?"

        elif "BUSCAR_PERFIL::" in resposta:
            try:
                linha = [l for l in resposta.split("\n") if "BUSCAR_PERFIL::" in l][0]
                municipio = linha.split("::")[1].strip()
                with st.spinner(f"Buscando perfil de {municipio}..."):
                    perfil = perfil_municipio(municipio)
                if perfil:
                    st.session_state.historico.append({"role":"assistant","content":resposta})
                    st.session_state.historico.append({"role":"user","content":f"[SISTEMA] PERFIL_ELEITORADO:\n{perfil}\n\nGere leitura estrategica senior com formatacao visual rica."})
                    with st.spinner("Analisando perfil..."):
                        resposta_final = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=3000,
                            system=sistema,
                            messages=st.session_state.historico
                        ).content[0].text
                else:
                    resposta_final = f"Nao encontrei perfil para **{municipio}**."
            except:
                resposta_final = "Erro ao buscar perfil. Tente novamente."

        elif "BUSCAR_CONCORRENTES::" in resposta:
            try:
                linha = [l for l in resposta.split("\n") if "BUSCAR_CONCORRENTES::" in l][0]
                partes    = linha.split("::")
                municipio = partes[1].strip()
                cargo     = partes[2].strip() if len(partes) > 2 else "DEPUTADO ESTADUAL"
                with st.spinner(f"Mapeando cenario em {municipio}..."):
                    conc = concorrentes_municipio(municipio, cargo)
                if conc:
                    st.session_state.historico.append({"role":"assistant","content":resposta})
                    st.session_state.historico.append({"role":"user","content":f"[SISTEMA] CONCORRENTES:\n{conc}\n\nGere analise estrategica senior do cenario. Use os dados reais para identificar nichos, oportunidades e riscos especificos. Nunca generalize o perfil do eleitorado sem dados que comprovem."})
                    with st.spinner("Analisando cenario..."):
                        resposta_final = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=3000,
                            system=sistema,
                            messages=st.session_state.historico
                        ).content[0].text
                else:
                    resposta_final = f"Nao encontrei dados para **{municipio}**."
            except:
                resposta_final = "Erro ao buscar concorrentes. Tente novamente."

        if resposta_final:
            texto_exibir = limpar(resposta_final)
            st.write(texto_exibir)
            st.session_state.historico.append({"role":"assistant","content":resposta_final})
            st.session_state.historico_display.append({"role":"assistant","content":texto_exibir})
        else:
            texto_exibir = limpar(resposta)
            st.write(texto_exibir)
            st.session_state.historico.append({"role":"assistant","content":resposta})
            st.session_state.historico_display.append({"role":"assistant","content":texto_exibir})

# v4 — municipio exato, eleitos 2016/2020, contexto 2026, entrevista estrategica, analise senior
