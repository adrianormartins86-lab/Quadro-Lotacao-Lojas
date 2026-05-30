import streamlit as st
import pandas as pd
import requests
import json

# 1. CONFIGURAÇÃO DA PÁGINA (Estilo Dashboard em tela cheia)
st.set_page_config(page_title="Molicenter - Quadro de Lotação", layout="wide")

# URL DA SUA API DO GOOGLE APPS SCRIPT
URL_API_SHEETS = "https://script.google.com/macros/s/AKfycbz_OA0O8zS-rMuuZEYu5rUeZow3lEZt-GcGYUWUbX4kiaRwDoQ9vZeoknsF5K-zFZvn/exec"

# Estilo global das tabelas em HTML (Cores e Rolagem Horizontal)
st.markdown("""
    <style>
    .tabela-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 25px;
    }
    .ql-table {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 14px;
        color: #ffffff;
    }
    .ql-table th, .ql-table td {
        border: 1px solid #444444;
        padding: 8px;
        text-align: left;
    }
    .ql-table tr:nth-child(even) {
        background-color: #1e1e1e;
    }
    .ql-table tr:nth-child(odd) {
        background-color: #121212;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Quadro de Lotação (QL) // Requisição")
st.markdown("---")

# 2. FUNÇÃO HÍBRIDA PARA CARREGAR OS DADOS
@st.cache_data(ttl="0d")  #ttl="0d" força a atualização em tempo real a cada clique/F5
def carregar_dados_completos():
    # A. Carrega os funcionários fixos do Excel oficial do seu GitHub
    df = pd.read_excel("Banco QL.xlsx", sheet_name="Banco")
    df['Loja'] = df['Loja'].fillna(0).astype(int)
    
    # Tratamento do Horário do Sistema (Coluna L - 'Descrição (Escala)')
    nome_coluna_horario = 'Descrição (Escala)'
    if nome_coluna_horario in df.columns:
        df['Horario_Sistema_Real'] = df[nome_coluna_horario].astype(str).str.replace('.0', '', regex=False).str.strip()
        df['Horario_Sistema_Real'] = df['Horario_Sistema_Real'].apply(lambda x: '-' if x in ['nan', 'None', ''] else x)
    else:
        df['Horario_Sistema_Real'] = "-"

    # B. Inicializa as 9 colunas operacionais vazias com o traço "-"
    colunas_digitacao = ['Observação', 'Data Abertura', 'Responsável', 'Horário Contrato', 'Sexo', 'Motivo', 'Status RH', 'Candidato', 'Data Admissão']
    for col in colunas_digitacao:
        df[col] = "-"

    # C. Busca o que os usuários já digitaram e salvaram no Google Sheets
    try:
        response = requests.get(URL_API_SHEETS, timeout=10)
        if response.status_code == 200:
            dados_sheets = response.json()
            for registro in dados_sheets:
                nome_func = registro.get('Nome')
                # Força a leitura correta da loja vinda do Sheets para cruzar
                try:
                    loja_reg = int(float(str(registro.get('Loja', 0))))
                except:
                    loja_reg = 0
                
                # Cruza as informações: Só joga na tabela se bater Nome E Loja simultaneamente
                idx_list = df[(df['Nome'] == nome_func) & (df['Loja'] == loja_reg)].index
                if len(idx_list) > 0:
                    idx = idx_list[0]
                    df.at[idx, 'Observação'] = registro.get('Observação', '-')
                    df.at[idx, 'Data Abertura'] = registro.get('Data Abertura', '-')
                    df.at[idx, 'Responsável'] = registro.get('Responsável', '-')
                    df.at[idx, 'Horário Contrato'] = registro.get('Horário Contrato', '-')
                    df.at[idx, 'Sexo'] = registro.get('Sexo', '-')
                    df.at[idx, 'Motivo'] = registro.get('Motivo', '-')
                    df.at[idx, 'Status RH'] = registro.get('Status RH', '-')
                    df.at[idx, 'Candidato'] = registro.get('Candidato', '-')
                    df.at[idx, 'Data Admissão'] = registro.get('Data Admissão', '-')
    except Exception as e:
        pass # Se o Sheets estiver totalmente zerado no primeiro acesso, segue com traços

    return df

try:
    df_bruto = carregar_dados_completos()

    # 3. FILTRO DE LOJA
    lojas_disponiveis = sorted([int(l) for l in df_bruto['Loja'].unique() if int(l) > 0])
    loja_selecionada = st.selectbox("Selecione a Loja para Análise:", lojas_disponiveis, format_func=lambda x: f"Loja {int(x):02d}")

    df_loja = df_bruto[df_bruto['Loja'] == loja_selecionada].copy()

    # =========================================================
    # 🛠️ BARRA LATERAL (SIDEBAR) - FORMULÁRIO DE DIGITAÇÃO
    # =========================================================
    st.sidebar.header("📝 Alimentar Informações")
    funcionarios_loja = sorted(df_loja['Nome'].dropna().unique())
    colaborador_selecionado = st.sidebar.selectbox("Selecione o Colaborador:", funcionarios_loja)
    
    if colaborador_selecionado:
        dados_func = df_loja[df_loja['Nome'] == colaborador_selecionado].iloc[0]
        st.sidebar.markdown("---")
        
        # 🔸 INPUTS DO SUPERVISOR
        st.sidebar.subheader("🔸 Supervisor")
        nova_obs = st.sidebar.text_area("Observação:", value=str(dados_func['Observação']) if str(dados_func['Observação']) != "-" else "")
        
        # 🔹 INPUTS DO GERENTE
        st.sidebar.subheader("🔹 Gerente")
        nova_data_abertura = st.sidebar.text_input("Data Abertura:", value=str(dados_func['Data Abertura']) if str(dados_func['Data Abertura']) != "-" else "")
        novo_responsavel = st.sidebar.text_input("Responsável:", value=str(dados_func['Responsável']) if str(dados_func['Responsável']) != "-" else "")
        novo_horario_contrato = st.sidebar.text_input("Horário Contrato:", value=str(dados_func['Horário Contrato']) if str(dados_func['Horário Contrato']) != "-" else "")
        
        sexo_atual = str(dados_func['Sexo']).strip().upper()
        sexo_index = 0
        if sexo_atual == "M": sexo_index = 1
        elif sexo_atual == "F": sexo_index = 2
        novo_sexo = st.sidebar.selectbox("Sexo:", ["-", "M", "F"], index=sexo_index)
        novo_motivo = st.sidebar.text_input("Motivo:", value=str(dados_func['Motivo']) if str(dados_func['Motivo']) != "-" else "")
        
        # 🔺 INPUTS DO RH
        st.sidebar.subheader("🔺 Recursos Humanos (RH)")
        novo_status_rh = st.sidebar.text_input("Status RH:", value=str(dados_func['Status RH']) if str(dados_func['Status RH']) != "-" else "")
        novo_candidato = st.sidebar.text_input("Candidato:", value=str(dados_func['Candidato']) if str(dados_func['Candidato']) != "-" else "")
        nova_data_admissao = st.sidebar.text_input("Data Admissão:", value=str(dados_func['Data Admissão']) if str(dados_func['Data Admissão']) != "-" else "")
        
        # BOTÃO INTERATIVO QUE DISPARA A GRAVAÇÃO NO GOOGLE SHEETS
        if st.sidebar.button("💾 Salvar Alterações", use_container_width=True):
            payload = {
                "Loja": int(loja_selecionada),
                "Nome": colaborador_selecionado,
                "Observacao": nova_obs if nova_obs.strip() != "" else "-",
                "DataAbertura": nova_data_abertura if nova_data_abertura.strip() != "" else "-",
                "Responsavel": novo_responsavel if novo_responsavel.strip() != "" else "-",
                "HorarioContrato": novo_horario_contrato if novo_horario_contrato.strip() != "" else "-",
                "Sexo": novo_sexo,
                "Motivo": novo_motivo if novo_motivo.strip() != "" else "-",
                "StatusRH": novo_status_rh if novo_status_rh.strip() != "" else "-",
                "Candidato": novo_candidato if novo_candidato.strip() != "" else "-",
                "DataAdmissao": nova_data_admissao if nova_data_admissao.strip() != "" else "-"
            }
            
            try:
                headers = {'Content-Type': 'application/json'}
                res = requests.post(URL_API_SHEETS, data=json.dumps(payload), headers=headers, timeout=10)
                if res.status_code == 200:
                    st.sidebar.success("Dados consolidados com sucesso!")
                    st.cache_data.clear() # Limpa o cache para forçar a leitura do dado novo
                    st.rerun() # Atualiza a tela
                else:
                    st.sidebar.error("Erro interno ao enviar dados para a API do Google.")
            except Exception as e:
                st.sidebar.error(f"Erro de comunicação com o Sheets: {e}")

    # =========================================================
    # 🏪 INDICADORES E PAINEL VISUAL (TELA PRINCIPAL)
    # =========================================================
    st.markdown(f"### 🏪 Quadro de Funcionários - Loja {int(loja_selecionada):02d}")

    df_loja['Situação_Upper'] = df_loja['Situação'].astype(str).str.upper()
    ativos_qtd = len(df_loja[df_loja['Situação_Upper'].str.contains('ATIVO')])
    demitidos_qtd = len(df_loja[df_loja['Situação_Upper'].str.contains('DEMITIDO')])
    ferias_afastados = len(df_loja[df_loja['Situação_Upper'].str.contains('FÉRIAS|AFASTAMENTO|AFASTADO')])

    col1, col2, col3 = st.columns(3)
    col1.metric("Funcionários Ativos", ativos_qtd)
    col2.metric("Demitidos", demitidos_qtd)
    col3.metric("Férias / Afastamentos", ferias_afastados)

    st.markdown("---")

    st.subheader("📋 Distribuição por Setor e Cargo")
    departamentos = sorted(df_loja['Dept'].dropna().unique())

    for dept in departamentos:
        with st.expander(f"🏢 DEPARTAMENTO: {dept}", expanded=True):
            df_dept = df_loja[df_loja['Dept'] == dept]
            funcoes = sorted(df_dept['Função'].dropna().unique())
            
            for funcao in funcoes:
                st.markdown(f"**🔹 Cargo: {funcao}**")
                df_funcao = df_dept[df_dept['Função'] == funcao]
                
                df_filtrado = df_funcao[[
                    'Situação', 'Nome', 'Horario_Sistema_Real',
                    'Observação',
                    'Data Abertura', 'Responsável', 'Horário Contrato', 'Sexo', 'Motivo',
                    'Status RH', 'Candidato', 'Data Admissão'
                ]]
                
                html_tabela = f"""
                <div class="tabela-container">
                    <table class="ql-table">
                        <thead>
                            <tr>
                                <th colspan="3" style="background-color: #1c3d5a; color: white; text-align: center; font-weight: bold;">DONO: ANALISTA</th>
                                <th colspan="1" style="background-color: #d97706; color: white; text-align: center; font-weight: bold;">DONO: SUPERVISOR</th>
                                <th colspan="5" style="background-color: #15803d; color: white; text-align: center; font-weight: bold;">DONO: GERENTE</th>
                                <th colspan="3" style="background-color: #b91c1c; color: white; text-align: center; font-weight: bold;">DONO: RH</th>
                            </tr>
                            <tr style="background-color: #262626; color: #dddddd;">
                                <th>Status</th><th>Nome do Colaborador</th><th>Horário Sistema</th>
                                <th>Observação</th>
                                <th>Data Abertura</th><th>Responsável</th><th>Horário Contrato</th><th>Sexo</th><th>Motivo</th>
                                <th>Status RH</th><th>Candidato</th><th>Data Admissão</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for _, row in df_filtrado.iterrows():
                    html_tabela += "<tr>"
                    for val in row:
                        html_tabela += f"<td>{val}</td>"
                    html_tabela += "</tr>"
                    
                html_tabela += """
                        </tbody>
                    </table>
                </div>
                """
                st.markdown(html_tabela, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro no processamento cruzado de dados. Detalhes: {e}")
