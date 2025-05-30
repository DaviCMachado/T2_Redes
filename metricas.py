import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import matplotlib.dates as mdates

plt.rcParams.update({'axes.grid': True})
os.makedirs("graficos_metricas", exist_ok=True)

def salvar_figura(nome):
    plt.savefig(f"graficos_metricas/{nome}", bbox_inches='tight')
    plt.close()

def remover_outliers(valores, ignorar_zeros=True):
    valores = np.array(valores)
    if valores.size == 0:
        return valores
    if ignorar_zeros:
        valores = valores[valores > 0]  # Remove zeros antes de calcular IQR
    if valores.size == 0:
        return valores
    q1 = np.percentile(valores, 25)
    q3 = np.percentile(valores, 75)
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr
    filtrados = valores[(valores >= limite_inferior) & (valores <= limite_superior)]
    return filtrados


def plotar_janela_congestionamento_agrupada(janela_congestionamento, top_n=5):
    plt.figure(figsize=(12, 6))
    conexoes_ordenadas = sorted(janela_congestionamento.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]

    for conn_id, valores in conexoes_ordenadas:
        if not valores:
            continue
        tamanhos = [v[1] if isinstance(v, (list, tuple)) else v for v in valores]
        tamanhos = np.array(tamanhos)
        tamanhos_filtrados = remover_outliers(tamanhos)
        if tamanhos_filtrados.size == 0:
            continue
        x = np.arange(len(tamanhos_filtrados))
        plt.plot(x, tamanhos_filtrados, label=conn_id, linewidth=1)

    plt.title(f"Janela de Congestionamento - Top {top_n} Conexões")
    plt.xlabel("Pacotes (ordem temporal)")
    plt.ylabel("Tamanho Estimado")
    plt.legend(fontsize='small')
    plt.tight_layout()
    salvar_figura("janela_congestionamento_top.png")

def plotar_microbursts_agregado(microbursts, freq='1T'):
    try:
        df = pd.Series(microbursts)
        df.index = pd.to_datetime(df.index)
    except Exception:
        print("Não foi possível converter timestamps para datetime, pulando agregação.")
        return

    df_agg = df.resample(freq).sum()
    plt.figure(figsize=(12, 5))
    plt.bar(df_agg.index, df_agg.values, color='indigo')
    plt.title(f"Microbursts agregados por {freq}")
    plt.xlabel("Timestamp")
    plt.ylabel("Nº de Pacotes")
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    salvar_figura(f"microbursts_agregado_{freq}.png")

def plotar_microbursts_linha(microbursts):
    try:
        tempos = pd.to_datetime(list(microbursts.keys()))
    except Exception:
        tempos = list(microbursts.keys())
    counts = list(microbursts.values())

    ordenado = sorted(zip(tempos, counts), key=lambda x: x[0])
    tempos, counts = zip(*ordenado)

    plt.figure(figsize=(12, 5))
    plt.plot(tempos, counts, marker='o', linestyle='-', color='indigo')
    plt.title("Microbursts ao longo do tempo")
    plt.xlabel("Timestamp")
    plt.ylabel("Nº de Pacotes")
    plt.xticks(rotation=45)
    if isinstance(tempos[0], pd.Timestamp):
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.gcf().autofmt_xdate()
    plt.tight_layout()
    salvar_figura("microbursts_linha.png")

def plotar_boxplot_janela_congestionamento(janela_congestionamento, top_n=5):
    conexoes_ordenadas = sorted(janela_congestionamento.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
    dados_filtrados = []
    labels = []
    for conn_id, valores in conexoes_ordenadas:
        if not valores:
            continue
        tamanhos = [v[1] if isinstance(v, (list, tuple)) else v for v in valores]
        tamanhos = remover_outliers(np.array(tamanhos))
        if len(tamanhos) == 0:
            continue
        dados_filtrados.append(tamanhos)
        labels.append(conn_id)

    if dados_filtrados:
        plt.figure(figsize=(12, 6))
        plt.boxplot(dados_filtrados, labels=labels, patch_artist=True)
        plt.xticks(rotation=45, ha='right')
        plt.title("Boxplot da Janela de Congestionamento - Top Conexões")
        plt.ylabel("Tamanho Estimado")
        plt.tight_layout()
        salvar_figura("janela_congestionamento_boxplot.png")

def plotar_janela_congestionamento_movel(janela_congestionamento, top_n=5, window=5):
    plt.figure(figsize=(12, 6))
    conexoes_ordenadas = sorted(janela_congestionamento.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]

    for conn_id, valores in conexoes_ordenadas:
        if not valores:
            continue
        tamanhos = [v[1] if isinstance(v, (list, tuple)) else v for v in valores]
        tamanhos = np.array(tamanhos)
        valores_filtrados = remover_outliers(tamanhos)
        if valores_filtrados.size == 0:
            continue
        movel = np.convolve(valores_filtrados, np.ones(window)/window, mode='valid')
        x = np.arange(len(movel))
        plt.plot(x, movel, label=conn_id, linewidth=1)

    plt.title(f"Janela de Congestionamento (Média Móvel {window}) - Top {top_n} Conexões")
    plt.xlabel("Pacotes (ordem temporal)")
    plt.ylabel("Tamanho Estimado (média móvel)")
    plt.legend(fontsize='small')
    plt.tight_layout()
    salvar_figura("janela_congestionamento_movel.png")

def plotar_graficos(dados):
    # RTT por conexão
    if "rtt_por_conexao" in dados and dados["rtt_por_conexao"]:
        rtt = remover_outliers(list(dados["rtt_por_conexao"].values()))
        if rtt.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(rtt, bins=30, color='skyblue', edgecolor='black')
            plt.title("Distribuição de RTT por Conexão")
            plt.xlabel("RTT (s)")
            plt.ylabel("Frequência")
            salvar_figura("rtt_por_conexao.png")

    # Throughput por conexão
    if "throughput_por_conexao" in dados and dados["throughput_por_conexao"]:
        throughputs = remover_outliers(list(dados["throughput_por_conexao"].values()))
        if throughputs.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(throughputs, bins=30, color='mediumseagreen', edgecolor='black')
            plt.title("Distribuição de Throughput por Conexão")
            plt.xlabel("Throughput (bytes/s)")
            plt.ylabel("Frequência")
            salvar_figura("throughput_por_conexao.png")

    # Taxa de retransmissões
    if "taxa_retransmissoes" in dados and dados["taxa_retransmissoes"]:
        taxas = remover_outliers(list(dados["taxa_retransmissoes"].values()))
        if taxas.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(taxas, bins=30, color='orange', edgecolor='black')
            plt.title("Taxa de Retransmissões por IP de Origem")
            plt.xlabel("Taxa")
            plt.ylabel("Frequência")
            salvar_figura("taxa_retransmissoes.png")

    # Fluxos elefantes
    if "fluxos_elefantes" in dados and dados["fluxos_elefantes"]:
        plt.figure(figsize=(10, 4))
        itens = sorted(dados["fluxos_elefantes"].items(), key=lambda x: x[1], reverse=True)[:10]
        labels, valores = zip(*itens)
        plt.barh(labels, valores, color='teal')
        plt.title("Top 10 Fluxos Elefantes (volume de dados)")
        plt.xlabel("Bytes Transferidos")
        plt.tight_layout()
        salvar_figura("fluxos_elefantes.png")

    # Top portas destino
    if "top_aplicacoes_portas" in dados and dados["top_aplicacoes_portas"]:
        plt.figure(figsize=(10, 4))
        portas = list(map(str, dados["top_aplicacoes_portas"].keys()))
        counts = list(dados["top_aplicacoes_portas"].values())
        plt.bar(portas, counts, color='darkcyan')
        plt.title("Top 10 Portas de Destino Mais Usadas")
        plt.xlabel("Porta")
        plt.ylabel("Número de Pacotes")
        plt.tight_layout()
        salvar_figura("top_aplicacoes.png")

    # Top IPs de destino
    if "top_ips_destino" in dados and dados["top_ips_destino"]:
        plt.figure(figsize=(10, 4))
        ips = list(dados["top_ips_destino"].keys())
        contagens = list(dados["top_ips_destino"].values())
        plt.barh(ips, contagens, color='crimson')
        plt.title("Top 10 IPs de Destino")
        plt.xlabel("Nº de Pacotes")
        plt.tight_layout()
        salvar_figura("top_ips_destino.png")

    # Tempo de estabelecimento (limpando zeros e negativos)
    if "tempos_estabelecimento" in dados and dados["tempos_estabelecimento"]:
        tempos = np.array(dados["tempos_estabelecimento"])
        tempos = tempos[(tempos > 0)]
        tempos = remover_outliers(tempos)
        if tempos.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(tempos, bins=30, color='salmon', edgecolor='black')
            plt.title("Tempo de Estabelecimento das Conexões")
            plt.xlabel("Tempo (s)")
            plt.ylabel("Frequência")
            plt.yscale('log')
            salvar_figura("tempo_estabelecimento.png")

    # Gráficos janela de congestionamento
    if "janela_congestionamento" in dados:
        plotar_janela_congestionamento_agrupada(dados["janela_congestionamento"], top_n=5)
        plotar_janela_congestionamento_movel(dados["janela_congestionamento"], top_n=5)
        plotar_boxplot_janela_congestionamento(dados["janela_congestionamento"], top_n=5)

    # Gráficos microbursts
    if "microbursts" in dados and dados["microbursts"]:
        plotar_microbursts_linha(dados["microbursts"])
        plotar_microbursts_agregado(dados["microbursts"], freq='1T')

    # Duração das conexões
    if "duracao_conexoes" in dados and dados["duracao_conexoes"]:
        duracoes = np.array(list(dados["duracao_conexoes"].values()))
        duracoes = duracoes[(duracoes > 0)]
        duracoes = remover_outliers(duracoes)
        if duracoes.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(duracoes, bins=30, color='plum', edgecolor='black')
            plt.title("Duração das Conexões")
            plt.xlabel("Duração (s)")
            plt.ylabel("Frequência")
            plt.yscale('log')
            plt.tight_layout()
            salvar_figura("duracao_conexoes.png")

if __name__ == "__main__":
    with open("stats_metricas.json", "r") as f:
        dados = json.load(f)
    plotar_graficos(dados)
    print("Gráficos de métricas gerados com sucesso.")
