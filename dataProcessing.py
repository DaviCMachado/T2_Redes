import pandas as pd
import numpy as np
import json
from collections import defaultdict

def calcular_janela_congestionamento(group):
    group_sorted = group.sort_values('timestamp')
    group_sorted['delta'] = group_sorted['timestamp'].diff().dt.total_seconds().fillna(0)
    janela_estimada = group_sorted['delta'].rolling(window=10, min_periods=1).mean().fillna(0)
    return list(zip(group_sorted['timestamp'].astype(str), janela_estimada))


def calcular_janela_congestionamento(group):
    group_sorted = group.sort_values('timestamp')
    group_sorted['delta'] = group_sorted['timestamp'].diff().dt.total_seconds().fillna(0)
    janela_estimada = group_sorted['delta'].rolling(window=10, min_periods=1).mean().fillna(0)
    return list(zip(group_sorted['timestamp'].astype(str), janela_estimada))


def normalize_conn(row):
    # Converte IPs para string e trata NaNs
    src_ip = str(row['src_ip']) if pd.notna(row['src_ip']) else ''
    dst_ip = str(row['dst_ip']) if pd.notna(row['dst_ip']) else ''
    
    if src_ip == '' or dst_ip == '':
        return 'incomplete_connection'

    # Converte portas para inteiro (ou zero se inválido)
    try:
        src_port = int(float(row['src_port']))
    except:
        src_port = 0
    try:
        dst_port = int(float(row['dst_port']))
    except:
        dst_port = 0

    ips = sorted([src_ip, dst_ip])
    ports = sorted([str(src_port), str(dst_port)])

    return f"{ips[0]}:{ports[0]} <-> {ips[1]}:{ports[1]}"

def calcular_distribuicao_tamanhos(tamanhos_lista):
    """Calcula estatísticas descritivas da distribuição de tamanhos"""
    if not tamanhos_lista:
        return {}
    
    tamanhos_array = np.array(tamanhos_lista)
    return {
        'min': float(np.min(tamanhos_array)),
        'max': float(np.max(tamanhos_array)),
        'media': float(np.mean(tamanhos_array)),
        'mediana': float(np.median(tamanhos_array)),
        'desvio_padrao': float(np.std(tamanhos_array)),
        'percentil_25': float(np.percentile(tamanhos_array, 25)),
        'percentil_75': float(np.percentile(tamanhos_array, 75)),
        'percentil_90': float(np.percentile(tamanhos_array, 90)),
        'percentil_95': float(np.percentile(tamanhos_array, 95)),
        'percentil_99': float(np.percentile(tamanhos_array, 99)),
        'total_segmentos': len(tamanhos_lista)
    }

def analisar_estatisticas(arquivo_csv):
    col_types = {
        'timestamp': float,
        'src_ip': str,
        'src_port': float,
        'dst_ip': str,
        'dst_port': float,
        'protocol': str,
        'length': float,
        'flags': str,
        'seq': float,
        'ack': float,
        'window': float,
        'segmento_tcp_len': float,  
        'mss': float                # <-- aqui está o MSS real
    }


    df = pd.read_csv(arquivo_csv, dtype=col_types, low_memory=False)

    # Converter portas para int
    df['src_port'] = df['src_port'].astype('Int64')
    df['dst_port'] = df['dst_port'].astype('Int64')

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    df = df[df['protocol'] == 'TCP']

    # Normalizar conexões bidirecionais
    df['connection_id'] = df.apply(normalize_conn, axis=1)

    # Flags detalhadas
    df['flag_S'] = df['flags'].str.contains('S', na=False)
    df['flag_A'] = df['flags'].str.contains('A', na=False)
    df['flag_SYN_only'] = df['flag_S'] & ~df['flag_A']
    df['flag_SYN_ACK'] = df['flag_S'] & df['flag_A']
    df['flag_ACK_only'] = ~df['flag_S'] & df['flag_A']

    # Grupos de conexões
    grupos_conexoes = dict(tuple(df.groupby('connection_id')))

    # Janela de congestionamento
    stats = {}
    stats['janela_congestionamento'] = {k: calcular_janela_congestionamento(g) for k, g in grupos_conexoes.items()}

    # Duracao e throughput (vetorizados)
    grouped = df.groupby('connection_id')
    min_time = grouped['timestamp'].min()
    max_time = grouped['timestamp'].max()
    duration = (max_time - min_time).dt.total_seconds()
    stats['duracao_conexoes'] = duration.to_dict()

    throughput = grouped['length'].sum() / duration.replace(0, np.nan)
    throughput = throughput.fillna(0)
    stats['throughput_por_conexao'] = throughput.to_dict()

    # RTT estimado (entre SYN e SYN-ACK)
    rtt_por_conexao = {}
    for conn_id, group in grupos_conexoes.items():
        syn_pkt = group[group['flag_SYN_only']]
        syn_ack_pkt = group[group['flag_SYN_ACK']]
        if not syn_pkt.empty and not syn_ack_pkt.empty:
            syn_time = syn_pkt['timestamp'].min()
            syn_ack_time = syn_ack_pkt['timestamp'].min()
            if syn_ack_time >= syn_time:
                rtt_por_conexao[conn_id] = (syn_ack_time - syn_time).total_seconds()
    stats['rtt_por_conexao'] = rtt_por_conexao

    # Tempo de estabelecimento: entre SYN e ACK final
    tempos_estabelecimento = []
    for conn_id, group in grupos_conexoes.items():
        syn_time = group[group['flag_SYN_only']]['timestamp'].min()
        ack_time = group[group['flag_ACK_only']]['timestamp'].min()
        if pd.notna(syn_time) and pd.notna(ack_time):
            delta = (ack_time - syn_time).total_seconds()
            if delta >= 0:
                tempos_estabelecimento.append(delta)
    stats['tempos_estabelecimento'] = tempos_estabelecimento

    # Detectar retransmissões (duplicados em src_ip, dst_ip, seq, length)
    df['retransmissao'] = df.duplicated(subset=['src_ip', 'dst_ip', 'seq'], keep=False)

    # Taxa de retransmissões por src_ip
    total_por_ip = df['src_ip'].value_counts()
    retrans_por_ip = df[df['retransmissao']]['src_ip'].value_counts()
    taxa_retransmissoes = (retrans_por_ip / total_por_ip).fillna(0)
    stats['taxa_retransmissoes'] = taxa_retransmissoes.to_dict()

    # Tamanhos dos segmentos e distribuição
    stats['tamanhos_segmentos'] = df['length'].dropna().tolist()
    stats['distribuicao_tamanhos_segmentos'] = calcular_distribuicao_tamanhos(stats['tamanhos_segmentos'])
    
    # MSS real por conexão (onde mss != -1)
    df['conexao_normalizada'] = df.apply(normalize_conn, axis=1)
    df_valid_mss = df[df['mss'] != -1]

    mss_por_conexao = df_valid_mss.groupby('conexao_normalizada')['mss'].min()
    stats['mss_por_conexao'] = mss_por_conexao.to_dict()

    volume_por_conexao = grouped['length'].sum()
    stats['fluxos_elefantes'] = volume_por_conexao.sort_values(ascending=False).head(10).to_dict()

    df['timestamp_rounded'] = df['timestamp'].dt.floor('s')
    pacotes_por_tempo = df.groupby('timestamp_rounded').size()
    stats['microbursts'] = pacotes_por_tempo.sort_values(ascending=False).head(10).to_dict()
    stats['top_aplicacoes_portas'] = df['dst_port'].value_counts().head(10).to_dict()
    stats['top_ips_destino'] = dict(df['dst_ip'].value_counts().head(10))

    contagem_tempo = df.groupby(df['timestamp'].dt.floor('s')).size()
    stats['pacotes_por_tempo'] = contagem_tempo.reset_index(name='count').to_dict(orient='records')
    stats['trafego_por_minuto'] = df.groupby(df['timestamp'].dt.floor('min'))['length'].sum().to_dict()

    df['minuto'] = df['timestamp'].dt.floor('min')
    top_ips = df['src_ip'].value_counts().head(10).index.tolist()
    heatmap_df = df[df['src_ip'].isin(top_ips)]
    heatmap_data = heatmap_df.groupby(['src_ip', 'minuto']).size().unstack(fill_value=0)
    stats['heatmap_ips_tempo'] = {
        'matriz': heatmap_data.to_dict(),
        'ips': heatmap_data.index.tolist(),
        'tempos': heatmap_data.columns.astype(str).tolist()
    }

    resumo_metricas = {
        "janela_congestionamento": stats['janela_congestionamento'],
        "rtt_por_conexao": stats['rtt_por_conexao'],
        "tempos_estabelecimento": stats['tempos_estabelecimento'],
        "taxa_retransmissoes": stats['taxa_retransmissoes'],
        "duracao_conexoes": stats['duracao_conexoes'],
        "throughput_por_conexao": stats['throughput_por_conexao'],
        "distribuicao_tamanhos_segmentos": stats['distribuicao_tamanhos_segmentos'],
        "mss_por_conexao": stats['mss_por_conexao'],
        "fluxos_elefantes": stats['fluxos_elefantes'],
        "microbursts": stats['microbursts'],
        "top_aplicacoes_portas": stats['top_aplicacoes_portas'],
        "top_ips_destino": stats['top_ips_destino']
    }

    return stats, resumo_metricas

def salvar_estatisticas(stats, caminho="estatisticas.json"):
    def tornar_json_friendly(obj):
        if isinstance(obj, (defaultdict, dict)):
            return {str(k): tornar_json_friendly(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [tornar_json_friendly(i) for i in obj]
        elif isinstance(obj, (pd.Timestamp, np.datetime64)):
            return str(obj)
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        else:
            return obj

    stats_friendly = tornar_json_friendly(stats)
    with open(caminho, 'w') as f:
        json.dump(stats_friendly, f, indent=4)


import time

if __name__ == "__main__":
    inicio = time.time()
    # stats, resumo = analisar_estatisticas("data_200k.csv")
    stats, resumo = analisar_estatisticas("data.csv")
    salvar_estatisticas(stats, "stats_completo.json")
    salvar_estatisticas(resumo, "stats_metricas.json")
    
    fim = time.time()
    duracao = fim - inicio
    print(f"Tempo total de execução: {duracao:.2f} segundos")