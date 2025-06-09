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
    if ignorar_zeros:
        valores_sem_zeros = valores[valores > 0]
    else:
        valores_sem_zeros = valores

    # Se não houver valores > 0, retorna tudo (incluindo zeros)
    if valores_sem_zeros.size == 0:
        return valores

    # Calcula quartis só com valores > 0
    q1 = np.percentile(valores_sem_zeros, 25)
    q3 = np.percentile(valores_sem_zeros, 75)
    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    # Filtra valores dentro do limite (incluindo zeros se ignorar_zeros=False)
    if ignorar_zeros:
        filtrados = valores[(valores >= limite_inferior) & (valores <= limite_superior)]
    else:
        # Mantém zeros mesmo se estão fora dos limites
        filtrados = valores[((valores >= limite_inferior) & (valores <= limite_superior)) | (valores == 0)]

    return filtrados


def plotar_distribuicao_tamanhos_segmentos(distribuicao):
    if not distribuicao or 'media' not in distribuicao:
        print("Distribuição de tamanhos de segmentos não disponível.")
        return
    # Exemplo de visualização dos percentis
    percentis = ['percentil_25', 'percentil_75', 'percentil_90', 'percentil_95', 'percentil_99']
    valores = [distribuicao[p] for p in percentis]
    plt.figure(figsize=(8, 4))
    plt.bar(percentis, valores, color='cornflowerblue')
    plt.title("Percentis dos Tamanhos dos Segmentos")
    plt.ylabel("Tamanho (bytes)")
    plt.tight_layout()
    salvar_figura("distribuicao_tamanhos_segmentos.png")
    print("Gráfico salvo: distribuicao_tamanhos_segmentos.png")


def plotar_mss_por_conexao(mss_por_conexao, top_n=20):
    if not mss_por_conexao:
        print("MSS por conexão não disponível.")
        return

    itens = sorted(mss_por_conexao.items(), key=lambda x: x[1], reverse=True)[:top_n]

    if len(itens) == 0:
        print("Nenhuma conexão com MSS disponível para plotar.")
        return

    labels_raw, valores = zip(*itens)

    labels = []
    for lbl in labels_raw:
        s = str(lbl)
        if len(s) > 15:
            s = s[:12] + "..."
        labels.append(s)

    plt.figure(figsize=(12, max(6, top_n * 0.5)))
    plt.barh(range(len(valores)), valores, color='slateblue')
    plt.gca().invert_yaxis()  # maior em cima
    plt.yticks(range(len(labels)), labels, fontsize=8)  # <-- força mostrar todos os labels
    plt.title(f"Top {top_n} MSS por Conexão", fontsize=12)
    plt.xlabel("MSS (bytes)", fontsize=10)
    plt.xticks(fontsize=8)
    plt.tight_layout()
    salvar_figura("mss_por_conexao.png")
    print("Gráfico salvo: mss_por_conexao.png")


def plotar_distribuicao_mss(mss_por_conexao, bins=30):
    if not mss_por_conexao:
        print("MSS por conexão não disponível.")
        return

    # Pega só os valores de MSS
    valores_mss = list(mss_por_conexao.values())
    
    plt.figure(figsize=(10, 6))
    plt.hist(valores_mss, bins=bins, color='slateblue', edgecolor='black')
    plt.title("Distribuição do MSS")
    plt.xlabel("MSS (bytes)")
    plt.ylabel("Frequência")
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()
    salvar_figura("distribuicao_mss.png")
    print("Gráfico salvo: distribuicao_mss.png")




def plotar_microbursts_temporais_top_10(microbursts, df=None):
    """
    Cria 10 gráficos temporais individuais dos microbursts com maior número de pacotes
    e salva no diretório graficos_top_10
    """
    if not microbursts:
        print("Nenhum dado de microburst encontrado")
        return
    
    # Criar diretório para os gráficos
    os.makedirs("graficos_top_10", exist_ok=True)
    
    # Selecionar os top 10 microbursts
    top_10 = sorted(microbursts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if not top_10:
        print("Nenhum microburst para plotar")
        return
    
    # Se temos acesso ao DataFrame original, podemos criar gráficos mais detalhados
    if df is not None:
        # Tentar criar gráficos com dados do DataFrame
        for i, (timestamp, count) in enumerate(top_10, 1):
            try:
                # Filtrar dados próximos ao timestamp do microburst
                df_temp = df.copy()
                
                # Converter timestamp se necessário
                if isinstance(timestamp, str):
                    try:
                        timestamp_dt = pd.to_datetime(timestamp)
                    except:
                        timestamp_dt = timestamp
                else:
                    timestamp_dt = timestamp
                
                # Definir janela de tempo (por exemplo, ±5 segundos ao redor do microburst)
                if isinstance(timestamp_dt, (pd.Timestamp, pd.DatetimeIndex)):
                    inicio = timestamp_dt - pd.Timedelta(seconds=5)
                    fim = timestamp_dt + pd.Timedelta(seconds=5)
                    
                    # Filtrar dados na janela de tempo
                    if 'timestamp' in df_temp.columns:
                        df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
                        df_janela = df_temp[(df_temp['timestamp'] >= inicio) & 
                                          (df_temp['timestamp'] <= fim)]
                    else:
                        # Se não temos coluna timestamp, usar índice
                        df_janela = df_temp.head(100)  # Pegar amostra
            except Exception as e:
                print(f"Erro ao processar microburst {timestamp}: {e}")
                

def plotar_janela_congestionamento_analise(janela_congestionamento):
    """
    Função para analisar os dados da janela de congestionamento e criar visualizações específicas
    """
    print("\n=== ANÁLISE DOS DADOS DA JANELA DE CONGESTIONAMENTO ===")
    
    # Análise estatística dos dados
    estatisticas = {}
    dados_todos = []
    
    for conn_id, valores in janela_congestionamento.items():
        if not valores:
            continue
            
        tamanhos = []
        for v in valores:
            if isinstance(v, (list, tuple)) and len(v) > 1:
                try:
                    tamanho = float(v[1])
                    tamanhos.append(tamanho)
                    dados_todos.append(tamanho)
                except (ValueError, TypeError):
                    continue
        
        if tamanhos:
            tamanhos_array = np.array(tamanhos)
            estatisticas[conn_id] = {
                'count': len(tamanhos),
                'zeros': np.sum(tamanhos_array == 0),
                'mean': np.mean(tamanhos_array),
                'std': np.std(tamanhos_array),
                'min': np.min(tamanhos_array),
                'max': np.max(tamanhos_array),
                'non_zero_mean': np.mean(tamanhos_array[tamanhos_array > 0]) if np.any(tamanhos_array > 0) else 0
            }
    
    # Estatísticas gerais
    dados_todos = np.array(dados_todos)
    print(f"Total de pontos de dados: {len(dados_todos)}")
    print(f"Valores zero: {np.sum(dados_todos == 0)} ({100*np.sum(dados_todos == 0)/len(dados_todos):.1f}%)")
    print(f"Valores não-zero: {np.sum(dados_todos > 0)} ({100*np.sum(dados_todos > 0)/len(dados_todos):.1f}%)")
    print(f"Média geral: {np.mean(dados_todos):.6f}")
    print(f"Média (apenas não-zero): {np.mean(dados_todos[dados_todos > 0]):.6f}")
    print(f"Desvio padrão: {np.std(dados_todos):.6f}")
    print(f"Mín: {np.min(dados_todos):.6f}, Máx: {np.max(dados_todos):.6f}")
    
    # Top 10 conexões por número de pontos
    print(f"\nTop 10 conexões por número de pontos:")
    top_por_count = sorted(estatisticas.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
    for conn_id, stats in top_por_count:
        print(f"  {conn_id}: {stats['count']} pontos, {stats['zeros']} zeros ({100*stats['zeros']/stats['count']:.1f}%)")
    
    # Criar histograma dos valores
    plt.figure(figsize=(15, 5))
    
    # Subplot 1: Todos os valores
    plt.subplot(1, 3, 1)
    plt.hist(dados_todos, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('Distribuição de Todos os Valores')
    plt.xlabel('Tamanho da Janela')
    plt.ylabel('Frequência')
    plt.yscale('log')
    
    # Subplot 2: Apenas valores não-zero
    plt.subplot(1, 3, 2)
    dados_nao_zero = dados_todos[dados_todos > 0]
    if len(dados_nao_zero) > 0:
        plt.hist(dados_nao_zero, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        plt.title('Distribuição de Valores Não-Zero')
        plt.xlabel('Tamanho da Janela')
        plt.ylabel('Frequência')
        plt.yscale('log')
    
    # Subplot 3: Box plot das top 5 conexões
    plt.subplot(1, 3, 3)
    top_5_dados = []
    top_5_labels = []
    for conn_id, stats in top_por_count[:5]:
        valores_conn = []
        for v in janela_congestionamento[conn_id]:
            if isinstance(v, (list, tuple)) and len(v) > 1:
                try:
                    tamanho = float(v[1])
                    valores_conn.append(tamanho)
                except (ValueError, TypeError):
                    continue
        if valores_conn:
            top_5_dados.append(valores_conn)
            top_5_labels.append(conn_id.split(' <-> ')[0][-15:])  # Pega só o final do primeiro IP
    
    if top_5_dados:
        plt.boxplot(top_5_dados, tick_labels=top_5_labels)
        plt.title('Box Plot - Top 5 Conexões')
        plt.xlabel('Conexão')
        plt.ylabel('Tamanho da Janela')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig("graficos_metricas/janela_congestionamento_analise.png", bbox_inches='tight', dpi=150)
    plt.close()
    print("Análise salva: janela_congestionamento_analise.png")


def plotar_janela_congestionamento_agrupada(janela_congestionamento, top_n=5, remover_zeros=True):
    plt.figure(figsize=(12, 6))
    # conexoes_ordenadas = sorted(janela_congestionamento.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
    conexoes_ordenadas = sorted(
        [(k, v) for k, v in janela_congestionamento.items() if any(float(x[1]) > 0 for x in v if len(x) > 1)],
        key=lambda x: np.mean([float(xi[1]) for xi in x[1] if len(xi) > 1]),
        reverse=True
    )[:top_n]

    series = []
    comprimentos = []

    for conn_id, valores in conexoes_ordenadas:
        if not valores:
            continue
        tamanhos = [v[1] if isinstance(v, (list, tuple)) else v for v in valores]
        tamanhos = np.array(tamanhos)
        if remover_zeros:
            tamanhos = tamanhos[tamanhos != 0]
        tamanhos_filtrados = remover_outliers(tamanhos)
        if tamanhos_filtrados.size == 0:
            continue
        series.append((conn_id, tamanhos_filtrados))
        comprimentos.append(len(tamanhos_filtrados))

    if not series:
        return

    min_len = min(comprimentos)
    plot_len = min(min_len, 20)

    for conn_id, valores in series:
        plt.plot(np.arange(plot_len), valores[:plot_len], label=conn_id, linewidth=1)

    # plt.title(f"Janela de Congestionamento - Top {top_n} Conexões (Zerados Removidos)")
    plt.title("Janela de Congestionamento - Top 10 Conexões (Zerados Removidos)")
    plt.xlabel("Pacotes (ordem temporal ajustada)")
    plt.ylabel("Tamanho Estimado")
    plt.xlim(0, 20)
    plt.legend(fontsize='small')
    plt.tight_layout()
    salvar_figura("janela_congestionamento_top.png")


def plotar_janela_congestionamento_movel(janela_congestionamento, top_n=5, window=5):
    plt.figure(figsize=(12, 6))
    # conexoes_ordenadas = sorted(janela_congestionamento.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]
    conexoes_ordenadas = sorted(
        [(k, v) for k, v in janela_congestionamento.items() if any(float(x[1]) > 0 for x in v if len(x) > 1)],
        key=lambda x: np.mean([float(xi[1]) for xi in x[1] if len(xi) > 1]),
        reverse=True
    )[:top_n]

    movel_series = []
    comprimentos = []

    for conn_id, valores in conexoes_ordenadas:
        if not valores:
            continue
        tamanhos = [v[1] if isinstance(v, (list, tuple)) else v for v in valores]
        tamanhos = np.array(tamanhos)
        tamanhos = tamanhos[tamanhos != 0]
        valores_filtrados = remover_outliers(tamanhos, ignorar_zeros=False)
        if valores_filtrados.size == 0 or np.all(valores_filtrados == 0):
            continue
        movel = np.convolve(valores_filtrados, np.ones(window)/window, mode='valid')
        movel_series.append((conn_id, movel))
        comprimentos.append(len(movel))

    if not movel_series:
        return

    min_len = min(comprimentos)
    plot_len = min(min_len, 20)

    for conn_id, movel in movel_series:
        plt.plot(np.arange(plot_len), movel[:plot_len], label=conn_id, linewidth=1)

    plt.title(f"Janela de Congestionamento (Média Móvel {window}) - Top {top_n} Conexões")
    plt.xlabel("Pacotes (ordem temporal ajustada)")
    plt.ylabel("Tamanho Estimado (média móvel)")
    plt.xlim(0, 20)
    plt.legend(fontsize='small')
    plt.tight_layout()
    salvar_figura("janela_congestionamento_movel.png")

def plotar_microbursts_top(microbursts, top_n=20):
    """
    Plota os top N microbursts por contagem de pacotes
    """
    if not microbursts:
        print("Nenhum dado de microburst encontrado")
        return
    
    # Converter timestamps para string se necessário e ordenar por contagem
    top = sorted(microbursts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    if not top:
        print("Nenhum microburst para plotar")
        return
    
    tempos, counts = zip(*top)
    
    plt.figure(figsize=(14, 6))
    bars = plt.bar(range(len(tempos)), counts, color='crimson', alpha=0.7, edgecolor='black')
    
    # Configurar labels do eixo x
    plt.xticks(range(len(tempos)), [str(t) for t in tempos], rotation=45, ha='right')
    
    # Adicionar valores nas barras
    for i, (bar, count) in enumerate(zip(bars, counts)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01, 
                str(count), ha='center', va='bottom', fontsize=8)
    
    # plt.title(f"Top {top_n} Microbursts por Número de Pacotes")
    plt.title("Top 10 Microbursts por Número de Pacotes")
    plt.xlabel("Timestamp")
    plt.ylabel("Número de Pacotes")
    plt.tight_layout()
    salvar_figura("microbursts_top.png")
    print(f"Gráfico salvo: microbursts_top.png")

def plotar_microbursts_linha_annotated(microbursts, threshold=None):
    """
    Plota microbursts em linha temporal com anotações nos picos
    """
    if not microbursts:
        print("Nenhum dado de microburst encontrado")
        return
    
    # Converter timestamps para datetime se possível
    dados_processados = []
    for timestamp, count in microbursts.items():
        try:
            # Tentar converter para datetime
            if isinstance(timestamp, str):
                tempo = pd.to_datetime(timestamp)
            else:
                tempo = timestamp
            dados_processados.append((tempo, count))
        except:
            # Se falhar, usar como string
            dados_processados.append((str(timestamp), count))
    
    # Ordenar por tempo
    dados_processados.sort(key=lambda x: x[0])
    tempos, counts = zip(*dados_processados)
    counts = np.array(counts)
    
    plt.figure(figsize=(14, 6))
    
    # Verificar se tempos são datetime
    if isinstance(tempos[0], (pd.Timestamp, pd.DatetimeIndex)):
        plt.plot(tempos, counts, label='Microbursts', marker='o', linestyle='-', 
                 alpha=0.7, markersize=4, linewidth=1.5, color='darkblue')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        # Usar AutoDateLocator para limitar ticks
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45)
    else:
        # Se não forem datetime, usar índices
        indices = range(len(tempos))
        plt.plot(indices, counts, label='Microbursts', marker='o', linestyle='-', 
                alpha=0.7, markersize=4, linewidth=1.5, color='darkblue')
        # Mostrar apenas alguns labels para evitar sobreposição
        step = max(1, len(tempos) // 10)
        plt.xticks(indices[::step], [str(t) for t in tempos[::step]], rotation=45)
    
    # Definir threshold automaticamente se não fornecido
    if threshold is None:
        threshold = np.percentile(counts, 90)
    
    plt.axhline(threshold, color='red', linestyle='--', alpha=0.8, 
               label=f'Threshold (90º percentil): {threshold:.0f}')
    
    # Anotar pontos acima do threshold
    pontos_anotados = 0
    max_anotacoes = 15  # Limitar anotações para evitar poluição visual
    
    for i, (t, c) in enumerate(zip(tempos, counts)):
        if c > threshold and pontos_anotados < max_anotacoes:
            if isinstance(t, (pd.Timestamp, pd.DatetimeIndex)):
                plt.annotate(f"{c}", (t, c), textcoords="offset points", 
                           xytext=(0, 10), ha='center', fontsize=8, 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            else:
                plt.annotate(f"{c}", (i, c), textcoords="offset points", 
                           xytext=(0, 10), ha='center', fontsize=8,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            pontos_anotados += 1
    
    plt.title("Microbursts ao Longo do Tempo (com Anotações nos Picos)")
    plt.xlabel("Tempo")
    plt.ylabel("Número de Pacotes")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    salvar_figura("microbursts_linha_annotated.png")
    print(f"Gráfico salvo: microbursts_linha_annotated.png")


def plotar_microbursts_heatmap(df, time_col='timestamp_rounded', ip_col='src_ip', top_n=10):
    """
    Plota heatmap de microbursts por IP ao longo do tempo
    """
    try:
        # Verificar se as colunas existem
        if time_col not in df.columns or ip_col not in df.columns:
            print(f"Colunas necessárias não encontradas: {time_col}, {ip_col}")
            return
        
        # Selecionar top IPs
        top_ips = df[ip_col].value_counts().head(top_n).index
        df_top = df[df[ip_col].isin(top_ips)]
        
        if df_top.empty:
            print("Nenhum dado encontrado para o heatmap")
            return
        
        # Criar pivot table
        pivot = pd.pivot_table(df_top, index=time_col, columns=ip_col, 
                              aggfunc='size', fill_value=0)
        
        if pivot.empty:
            print("Pivot table vazia")
            return
        
        plt.figure(figsize=(16, 8))
        im = plt.imshow(pivot.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        plt.colorbar(im, label='Número de Pacotes')
        
        # Configurar eixos
        plt.yticks(range(len(pivot.columns)), [str(ip) for ip in pivot.columns])
        
        # Configurar eixo x (tempo)
        n_ticks = min(10, len(pivot.index))
        step = max(1, len(pivot.index) // n_ticks)
        tick_positions = range(0, len(pivot.index), step)
        tick_labels = [str(pivot.index[i]) for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=45, ha='right')
        
        plt.xlabel('Tempo')
        plt.ylabel('IP de Origem')
        plt.title(f'Heatmap de Microbursts - Top {top_n} IPs ao longo do tempo')
        plt.tight_layout()
        salvar_figura("microbursts_heatmap.png")
        print(f"Gráfico salvo: microbursts_heatmap.png")
        
    except Exception as e:
        print(f"Erro ao gerar heatmap: {e}")
        

def plotar_microbursts_estatisticas(microbursts):
    """
    Plota estatísticas dos microbursts (histograma e box plot)
    """
    if not microbursts:
        print("Nenhum dado de microburst encontrado")
        return
    
    counts = np.array(list(microbursts.values()))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Histograma
    ax1.hist(counts, bins=30, color='skyblue', alpha=0.7, edgecolor='black')
    ax1.set_title('Distribuição do Número de Pacotes por Microburst')
    ax1.set_xlabel('Número de Pacotes')
    ax1.set_ylabel('Frequência')
    ax1.grid(True, alpha=0.3)
    
    # Adicionar estatísticas no histograma
    media = np.mean(counts)
    mediana = np.median(counts)
    ax1.axvline(media, color='red', linestyle='--', alpha=0.8, label=f'Média: {media:.1f}')
    ax1.axvline(mediana, color='green', linestyle='--', alpha=0.8, label=f'Mediana: {mediana:.1f}')
    ax1.legend()
    
    # Box plot
    ax2.boxplot(counts, patch_artist=True, 
                boxprops=dict(facecolor='lightgreen', alpha=0.7))
    ax2.set_title('Box Plot - Distribuição de Pacotes por Microburst')
    ax2.set_ylabel('Número de Pacotes')
    ax2.grid(True, alpha=0.3)
    
    # Adicionar estatísticas textuais
    q1, q3 = np.percentile(counts, [25, 75])
    ax2.text(1.1, np.max(counts), f'Estatísticas:\n'
                                  f'Min: {np.min(counts)}\n'
                                  f'Q1: {q1:.1f}\n'
                                  f'Mediana: {mediana:.1f}\n'
                                  f'Q3: {q3:.1f}\n'
                                  f'Max: {np.max(counts)}\n'
                                  f'Média: {media:.1f}\n'
                                  f'Std: {np.std(counts):.1f}',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8))
    
    plt.tight_layout()
    salvar_figura("microbursts_estatisticas.png")
    print(f"Gráfico salvo: microbursts_estatisticas.png")



def plotar_graficos(dados):
    # # RTT por conexão
    # if "rtt_por_conexao" in dados and dados["rtt_por_conexao"]:
    #     rtt = np.array(list(dados["rtt_por_conexao"].values()), dtype=float)
    #     # Remove NaN, inf, zero, and negative values
    #     rtt = rtt[np.isfinite(rtt) & (rtt > 0)]
    #     if rtt.size > 0:
    #         plt.figure(figsize=(10, 4))
    #         plt.hist(rtt, bins=30, color='skyblue', edgecolor='black')
    #         plt.title("Distribuição de RTT por Conexão")
    #         plt.xlabel("RTT (s)")
    #         plt.ylabel("Frequência")
    #         salvar_figura("rtt_por_conexao.png")

    # se tiver bugado usa o codigo de cima
    if "rtt_por_conexao" in dados and dados["rtt_por_conexao"]:
        rtt = np.array(list(dados["rtt_por_conexao"].values()), dtype=float)
        # Remove NaN, inf, zero, and negative values
        rtt = rtt[np.isfinite(rtt) & (rtt > 0)]

        limite_maximo = 1.0  # limite máximo de RTT em segundos para o histograma

        # Filtra valores para limitar o crescimento dos grandes valores
        rtt_filtrado = rtt[rtt <= limite_maximo]

        if rtt_filtrado.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(rtt_filtrado, bins=30, color='skyblue', edgecolor='black')
            plt.title(f"Distribuição de RTT por Conexão (≤ {limite_maximo} s)")
            plt.xlabel("RTT (s)")
            plt.ylabel("Frequência")
            salvar_figura("rtt_por_conexao.png")



    # Throughput por conexão
    # if "throughput_por_conexao" in dados and dados["throughput_por_conexao"]:
    #     throughputs = np.array(list(dados["throughput_por_conexao"].values()))
    #     throughputs = throughputs[throughputs > 0]  # Remove valores zero ou negativos

    #     if throughputs.size > 0:
    #         plt.figure(figsize=(10, 4))
    #         limite_superior = 240
    #         throughputs_filtrados = throughputs[throughputs <= limite_superior]

    #         bins = np.arange(0, limite_superior + 40, 40)  
    #         plt.hist(throughputs_filtrados, bins=bins, color='mediumseagreen', edgecolor='black')
    #         plt.xlabel("Throughput (bytes/s)")
    #         plt.ylabel("Número de conexões")
    #         plt.title("Distribuição de Throughput por Conexão")
    #         plt.tight_layout()
    #         plt.savefig("graficos_metricas/throughput_medio.png")
    #         plt.close()


    # se ficar bugado utilize o codigo acima
    if "throughput_por_conexao" in dados and dados["throughput_por_conexao"]:
        throughputs = np.array(list(dados["throughput_por_conexao"].values()))
        throughputs = throughputs[(throughputs > 0) & (throughputs <= 30000)]  # filtra positivos e ≤ 30k

        if throughputs.size > 0:
            plt.figure(figsize=(10, 4))

            bins = np.arange(0, 30000 + 3000, 3000)  # bins de 3k até 30k

            plt.hist(throughputs, bins=bins, color='mediumseagreen', edgecolor='black')

            plt.xlabel("Throughput (bytes/s)")
            plt.ylabel("Número de conexões")
            plt.title("Distribuição de Throughput por Conexão (≤ 30.000 bytes/s)")
            plt.tight_layout()
            plt.savefig("graficos_metricas/throughput_medio.png")
            plt.close()



    # Taxa de retransmissões (histograma)
    if "taxa_retransmissoes" in dados and dados["taxa_retransmissoes"]:
        taxas = remover_outliers(list(dados["taxa_retransmissoes"].values()), ignorar_zeros=True)
        if taxas.size > 0:
            media = np.mean(taxas)
            mediana = np.median(taxas)

            plt.figure(figsize=(10, 4))
            plt.hist(taxas, bins=30, color='orange', edgecolor='black', alpha=0.7)
            plt.axvline(media, color='blue', linestyle='dashed', linewidth=1.5, label=f'Média: {media:.4f}')
            plt.axvline(mediana, color='red', linestyle='dotted', linewidth=1.5, label=f'Mediana: {mediana:.4f}')
            plt.title("Taxa de Retransmissões por IP de Origem")
            plt.xlabel("Taxa de Retransmissão")
            plt.ylabel("Frequência")
            plt.legend()
            plt.tight_layout()
            salvar_figura("taxa_retransmissoes.png")

    # Gráfico: Top 10 IPs com maior número de retransmissões (absoluto)
    if "taxa_retransmissoes" in dados:
        # df = pd.read_csv("data_200k.csv")
        df = pd.read_csv("data.csv")
        df_retrans = df[['src_ip', 'dst_ip', 'seq', 'length']].dropna()
        is_retrans = df_retrans.duplicated(keep=False)
        df['retransmissao'] = False
        df.loc[df_retrans.index, 'retransmissao'] = is_retrans.values

        retrans_por_ip = df[df['retransmissao'] == True]['src_ip'].value_counts().head(10)

        plt.figure(figsize=(10, 5))
        retrans_por_ip.sort_values().plot(kind='barh', color='teal', edgecolor='black')
        plt.xlabel("Número de Retransmissões")
        plt.ylabel("IP de Origem")
        plt.title("Top 10 IPs com Mais Retransmissões")
        plt.tight_layout()
        salvar_figura("top_10_retransmissoes.png")

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

    # Tempo de estabelecimento (limpando zeros e negativos)
    if "tempos_estabelecimento" in dados and dados["tempos_estabelecimento"]:
        tempos = np.array(dados["tempos_estabelecimento"])
        tempos = tempos[(tempos > 0)]
        tempos = remover_outliers(tempos, ignorar_zeros=True)
        if tempos.size > 0:
            plt.figure(figsize=(10, 4))
            plt.hist(tempos, bins=30, color='salmon', edgecolor='black')
            plt.title("Tempo de Estabelecimento das Conexões")
            plt.xlabel("Tempo (s)")
            plt.ylabel("Frequência")
            plt.yscale('log')
            salvar_figura("tempo_estabelecimento.png")

    # Distribuição dos tamanhos dos segmentos
    if "distribuicao_tamanhos_segmentos" in dados:
        plotar_distribuicao_tamanhos_segmentos(dados["distribuicao_tamanhos_segmentos"])

    # MSS por conexão
    if "mss_por_conexao" in dados:
        plotar_mss_por_conexao(dados["mss_por_conexao"], top_n=10)
        plotar_distribuicao_mss(dados["mss_por_conexao"], bins=30)

    # Gráficos janela de congestionamento
    if "janela_congestionamento" in dados:
        print("\n=== GERANDO GRÁFICOS DA JANELA DE CONGESTIONAMENTO ===")
        
        # Primeiro fazer análise dos dados
        plotar_janela_congestionamento_analise(dados["janela_congestionamento"])

        plotar_janela_congestionamento_agrupada(dados["janela_congestionamento"], top_n=5, remover_zeros=True)
        plotar_janela_congestionamento_movel(dados["janela_congestionamento"], top_n=5, window=5)
        

    # Gráficos microbursts
    if "microbursts" in dados and dados["microbursts"]:
        microbursts = dados["microbursts"]
        if len(microbursts) > 0:
            # Top-N microbursts (bar)
            plotar_microbursts_top(microbursts, top_n=20)
            # Annotated line plot with threshold (auto threshold: 90th percentile)
            counts = np.array(list(microbursts.values()))
            if len(counts) > 0:
                threshold = np.percentile(counts, 90)
                plotar_microbursts_linha_annotated(microbursts, threshold=threshold)



    # Duração das conexões
    if "duracao_conexoes" in dados and dados["duracao_conexoes"]:
        duracoes = np.array(list(dados["duracao_conexoes"].values()))
        duracoes = duracoes[(duracoes > 0)]
        duracoes = remover_outliers(duracoes, ignorar_zeros=True)
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