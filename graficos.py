import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import dates as mdates

plt.style.use('seaborn-v0_8-darkgrid')

PASTA_GRAFICOS = "graficos_opcionais"

def salvar_figura(nome_arquivo):
    caminho = os.path.join(PASTA_GRAFICOS, nome_arquivo)
    try:
        plt.tight_layout()
        plt.savefig(caminho)
    except Exception as e:
        print(f"Erro ao salvar o gráfico em {caminho}: {e}")
    finally:
        plt.close()

def gerar_graficos(stats):
    os.makedirs(PASTA_GRAFICOS, exist_ok=True)

    # Scatter tamanho x ipg
    df = pd.DataFrame(stats.get("relacao_tamanho_frequencia", []), columns=["tamanho", "ipg"])
    gerar_scatter_tamanho_frequencia(df, "tamanho_frequencia.png")

    # Barra top IPs destino
    gerar_barra(stats.get("top_ips_destino", {}), "Top IPs de Destino", "ip_destino.png")
    
    # Top IPs de destino
    if "top_ips_destino" in stats and stats["top_ips_destino"]:
        plt.figure(figsize=(10, 4))
        ips = list(stats["top_ips_destino"].keys())
        contagens = list(stats["top_ips_destino"].values())
        plt.barh(ips, contagens, color='crimson')
        plt.title("Top 10 IPs de Destino")
        plt.xlabel("Nº de Pacotes")
        plt.tight_layout()
        salvar_figura("top_ips_destino.png")

    # Pacotes por tempo
    pacotes_por_tempo = stats.get("pacotes_por_tempo", None)
    if pacotes_por_tempo is not None:
        if not isinstance(pacotes_por_tempo, pd.DataFrame):
            if isinstance(pacotes_por_tempo, dict):
                pacotes_por_tempo = pd.DataFrame(list(pacotes_por_tempo.items()), columns=["timestamp", "count"])
            elif isinstance(pacotes_por_tempo, list):
                pacotes_por_tempo = pd.DataFrame(pacotes_por_tempo, columns=["timestamp", "count"])
        pacotes_por_tempo['timestamp'] = pd.to_datetime(pacotes_por_tempo['timestamp'], errors='coerce')
        pacotes_por_tempo.set_index('timestamp', inplace=True)
        gerar_tempo(pacotes_por_tempo, "Pacotes ao Longo do Tempo", "pacotes_tempo.png")

    # Heatmap IPs ativos
    heatmap = stats.get("heatmap_ips_tempo", {})
    matriz = heatmap.get("matriz", None)
    ips = heatmap.get("ips", [])
    tempos = heatmap.get("tempos", [])
    gerar_heatmap_ips_ativos(matriz, ips, tempos, "Mapa de Calor dos IPs mais Ativos", "ips_ativos_tempo.png")

    # Tráfego agregado por minuto
    trafego = stats.get("trafego_por_minuto", {})
    gerar_trafego_agrupado_tempo(trafego, "Tráfego Agregado ao Longo do Tempo", "trafego_agregado_tempo.png")

    # Gráficos obrigatórios TCP
    conexoes_tcp = stats.get("conexoes_tcp", {})
    if conexoes_tcp:
        gerar_janela_congestionamento(conexoes_tcp)
        gerar_scatter_rtt(conexoes_tcp)
        gerar_cdf_estabelecimento(conexoes_tcp)
        gerar_histograma_retransmissoes(conexoes_tcp)
        comparar_conexoes(conexoes_tcp)

def gerar_scatter_tamanho_frequencia(df, nome_arquivo):
    if df.empty or "tamanho" not in df.columns or "ipg" not in df.columns:
        return
    plt.figure(figsize=(10, 6))
    plt.scatter(df['ipg'], df['tamanho'], alpha=0.5, s=10, c='blue')
    plt.xlabel("Inter-Packet Gap (segundos)")
    plt.ylabel("Tamanho do Pacote (bytes)")
    plt.title("Relação entre IPG e Tamanho de Pacote")
    plt.grid(True)
    salvar_figura(nome_arquivo)

def gerar_barra(dados_dict, titulo, nome_arquivo):
    if not dados_dict:
        return
    nomes = list(dados_dict.keys())
    valores = list(dados_dict.values())
    plt.figure(figsize=(10, 6))
    plt.bar(nomes, valores, color='skyblue')
    plt.title(titulo)
    plt.xticks(rotation=45, ha='right')
    salvar_figura(nome_arquivo)

def gerar_tempo(stats, titulo, nome_arquivo):
    if stats.empty:
        return
    stats.index = pd.to_datetime(stats.index, errors='coerce')
    stats = stats.dropna()
    stats = stats[stats.index.year >= 2024]
    if stats.empty:
        return
    try:
        start_time = pd.Timestamp(stats.index.date[0]) + pd.Timedelta(hours=5)
        end_time = start_time + pd.Timedelta(minutes=15)
        stats_intervalo = stats[(stats.index >= start_time) & (stats.index <= end_time)]
        if stats_intervalo.empty:
            stats_intervalo = stats
    except IndexError:
        stats_intervalo = stats
    if stats_intervalo.empty:
        return
    stats_aggregated = stats_intervalo.resample('min').sum()
    plt.figure(figsize=(10, 6))
    plt.plot(stats_aggregated.index, stats_aggregated.values, label=titulo)
    plt.title(titulo)
    plt.xlabel('Tempo')
    plt.ylabel('Quantidade de Pacotes')
    plt.xticks(rotation=45)
    salvar_figura(nome_arquivo)

def gerar_heatmap_ips_ativos(matrix, ips, tempos, titulo, nome_arquivo):
    if matrix is None or not ips or not tempos:
        return
    tempos_2025 = [tempo for tempo in tempos if pd.to_datetime(tempo, errors='coerce').year == 2025]
    tempos_2025 = sorted(tempos_2025, key=lambda x: pd.to_datetime(x))
    matrix_df = pd.DataFrame.from_dict(matrix, orient='index').fillna(0)
    matrix_df.index = matrix_df.index.astype(str)
    tempos_2025 = [str(t).strip() for t in tempos_2025]
    tempos_validos = [t for t in tempos_2025 if t in matrix_df.index]
    ips = [str(ip).strip() for ip in ips]
    matrix_df.columns = matrix_df.columns.astype(str)
    ips_validos = [ip for ip in ips if ip in matrix_df.columns]
    if not ips_validos or not tempos_validos:
        return
    matriz_filtrada = matrix_df.loc[tempos_validos, ips_validos]
    plt.figure(figsize=(12, 8))
    sns.heatmap(matriz_filtrada, xticklabels=ips_validos, yticklabels=tempos_validos, cmap='YlGnBu')
    plt.xlabel("IPs")
    plt.ylabel("Tempo")
    plt.title(titulo)
    salvar_figura(nome_arquivo)

def gerar_trafego_agrupado_tempo(trafego_dict, titulo, nome_arquivo):
    if not trafego_dict:
        return
    df = pd.DataFrame(list(trafego_dict.items()), columns=["timestamp", "bytes"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(inplace=True)
    df = df[df['timestamp'].dt.year == 2025]
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    if df.empty:
        return
    df_resampled = df.resample('1min').sum()
    df_resampled['bytes_acumulado'] = df_resampled['bytes'].cumsum()
    plt.figure(figsize=(12, 6))
    plt.plot(df_resampled.index, df_resampled['bytes_acumulado'], color='royalblue', linewidth=2, label='Tráfego Acumulado (Bytes)')
    plt.title(titulo)
    plt.xlabel("Tempo (minutos)")
    plt.ylabel("Volume de Tráfego Acumulado (Bytes)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 1)))
    plt.xlim(pd.Timestamp('2025-01-01 05:00:00'), pd.Timestamp('2025-01-01 05:15:00'))
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    salvar_figura(nome_arquivo)

def gerar_janela_congestionamento(conexoes):
    plt.figure(figsize=(12, 6))
    for id_conexao, df in conexoes.items():
        if 'timestamp' in df and 'congestion_window' in df:
            plt.plot(pd.to_datetime(df['timestamp']), df['congestion_window'], label=id_conexao)
    plt.xlabel("Tempo")
    plt.ylabel("Janela de Congestionamento (bytes)")
    plt.title("Curva da Janela de Congestionamento ao Longo do Tempo")
    plt.legend(loc='best', fontsize='small')
    salvar_figura("janela_congestionamento.png")

def gerar_scatter_rtt(conexoes):
    dados = []
    for id_conexao, df in conexoes.items():
        if 'rtt' in df.columns:
            for rtt in df['rtt'].dropna():
                dados.append({'conexao': id_conexao, 'rtt': rtt})
    if not dados:
        return
    df_rtt = pd.DataFrame(dados)
    plt.figure(figsize=(12, 6))
    sns.stripplot(x='conexao', y='rtt', data=df_rtt, jitter=True)
    plt.xticks(rotation=45)
    plt.xlabel("Conexão")
    plt.ylabel("RTT (s)")
    plt.title("Dispersão do RTT por Conexão")
    salvar_figura("rtt_por_conexao.png")

def gerar_cdf_estabelecimento(conexoes):
    tempos = []
    for conn in conexoes.values():
        if 'tempo_estabelecimento' in conn.columns:
            tempos.extend(conn['tempo_estabelecimento'].dropna().tolist())
    if not tempos:
        return
    tempos = np.array(sorted(tempos))
    cdf = np.arange(len(tempos)) / len(tempos)
    plt.figure(figsize=(10, 6))
    plt.plot(tempos, cdf, marker='.', linestyle='none')
    plt.xlabel("Tempo de Estabelecimento (s)")
    plt.ylabel("CDF")
    plt.title("CDF do Tempo de Estabelecimento das Conexões")
    salvar_figura("cdf_estabelecimento.png")

def gerar_histograma_retransmissoes(conexoes):
    taxas = []
    for conn in conexoes.values():
        total = len(conn)
        if total == 0:
            continue
        if 'retransmissoes' in conn.columns:
            retransmissoes = conn['retransmissoes'].sum()
            taxas.append(retransmissoes / total)
    if not taxas:
        return
    plt.figure(figsize=(10, 6))
    plt.hist(taxas, bins=20, color='orange', edgecolor='black')
    plt.xlabel("Taxa de Retransmissões")
    plt.ylabel("Número de Conexões")
    plt.title("Histograma da Taxa de Retransmissões por Conexão")
    salvar_figura("retransmissoes.png")

def comparar_conexoes(stats_conexoes):
    duracoes = []
    for conn in stats_conexoes.values():
        if 'timestamp' in conn.columns and not conn.empty:
            inicio = pd.to_datetime(conn['timestamp'].min())
            fim = pd.to_datetime(conn['timestamp'].max())
            duracao = (fim - inicio).total_seconds()
            duracoes.append(duracao)
    if not duracoes:
        return
    df = pd.DataFrame(duracoes, columns=["duracao"])
    categorias = df['duracao'].apply(lambda x: 'Curta' if x < 10 else 'Longa')
    contagem = categorias.value_counts()
    plt.figure(figsize=(8, 5))
    contagem.plot(kind='bar', color=['green', 'red'])
    plt.xlabel("Tipo de Conexão")
    plt.ylabel("Número de Conexões")
    plt.title("Comparação entre Conexões Curtas e Longas")
    salvar_figura("conexoes_curta_longa.png")

if __name__ == "__main__":
    caminho_stats = "stats_completo.json"
    if not os.path.exists(caminho_stats):
        print(f"Arquivo {caminho_stats} não encontrado. Gere os dados completos primeiro.")
        exit(1)

    with open(caminho_stats, "r") as f:
        stats = json.load(f)

    # Converter conexoes_tcp em dict de DataFrames
    if "conexoes_tcp" in stats:
        conexoes_tcp = {}
        for k, v in stats["conexoes_tcp"].items():
            try:
                conexoes_tcp[k] = pd.DataFrame(v)
            except Exception as e:
                print(f"Erro ao converter conexão {k} para DataFrame: {e}")
        stats["conexoes_tcp"] = conexoes_tcp

    gerar_graficos(stats)
    print("Gráficos gerados com sucesso.")
