import pandas as pd
import numpy as np
import json
from collections import defaultdict

def parse_timestamp(ts):
    try:
        return pd.to_datetime(float(ts), unit='s')
    except Exception:
        return pd.NaT

def analisar_estatisticas(arquivo_csv):
    col_types = {
        'timestamp': float,
        'src_ip': str,
        'src_port': str,
        'dst_ip': str,
        'dst_port': str,
        'protocol': str,
        'length': float,
        'flags': str,
        'seq': float,
        'ack': float,
        'window': float
    }

    df = pd.read_csv(arquivo_csv, dtype=col_types, low_memory=False)

    # Parse timestamps com robustez
    df['timestamp'] = df['timestamp'].apply(parse_timestamp)
    df.dropna(subset=['timestamp'], inplace=True)

    df = df[df['protocol'] == 'TCP']

    df['connection_id'] = df['src_ip'] + ':' + df['src_port'] + ' -> ' + df['dst_ip'] + ':' + df['dst_port']

    stats = {}

    # 1. Janela de Congestionamento (estimada)
    janela_congestionamento = defaultdict(list)
    for conn_id, group in df.groupby('connection_id'):
        group_sorted = group.sort_values('timestamp')
        group_sorted['delta'] = group_sorted['timestamp'].diff().dt.total_seconds().fillna(0)
        janela_estimada = group_sorted['delta'].rolling(window=10).mean().fillna(0)
        janela_congestionamento[conn_id] = list(zip(group_sorted['timestamp'].astype(str), janela_estimada))
    stats['janela_congestionamento'] = janela_congestionamento

    # 2. RTT estimado (SYN -> SYN-ACK)
    rtt_por_conexao = []
    conexoes = df[df['flags'].str.contains('S', na=False)]
    for conn_id, group in conexoes.groupby('connection_id'):
        group = group.sort_values('timestamp')
        if len(group) >= 2:
            rtt = (group.iloc[1]['timestamp'] - group.iloc[0]['timestamp']).total_seconds()
            rtt_por_conexao.append((conn_id, rtt))
    stats['rtt_por_conexao'] = rtt_por_conexao

    # 3. Tempo de estabelecimento
    tempos_estabelecimento = []
    for conn_id, group in df.groupby('connection_id'):
        group = group.sort_values('timestamp')
        syn_time = group[group['flags'].str.contains('S', na=False)]['timestamp'].min()
        ack_time = group[group['flags'].str.contains('A', na=False)]['timestamp'].min()
        if pd.notna(syn_time) and pd.notna(ack_time):
            tempo = (ack_time - syn_time).total_seconds()
            if tempo >= 0:
                tempos_estabelecimento.append(tempo)
    stats['tempos_estabelecimento'] = tempos_estabelecimento

    # 4. Número de retransmissões (pode não existir -> será ignorado)
    if 'retransmission' in df.columns:
        retransmissoes = df[df['retransmission'] == True]
        total_por_ip = df['src_ip'].value_counts()
        retrans_por_ip = retransmissoes['src_ip'].value_counts()
        taxa_retransmissoes = (retrans_por_ip / total_por_ip).fillna(0)
        stats['taxa_retransmissoes'] = taxa_retransmissoes.to_dict()
    else:
        stats['taxa_retransmissoes'] = {}

    # 5. Duração da conexão
    duracoes = {}
    for conn_id, group in df.groupby('connection_id'):
        dur = (group['timestamp'].max() - group['timestamp'].min()).total_seconds()
        duracoes[conn_id] = dur
    stats['duracao_conexoes'] = duracoes

    # 6. Throughput médio
    throughputs = {}
    for conn_id, group in df.groupby('connection_id'):
        dur = (group['timestamp'].max() - group['timestamp'].min()).total_seconds()
        total_bytes = group['length'].sum()
        if dur > 0:
            throughputs[conn_id] = total_bytes / dur
    stats['throughput_por_conexao'] = throughputs

    # 7. Tamanhos dos segmentos
    stats['tamanhos_segmentos'] = df['length'].dropna().tolist()

    # 8. MSS por conexão (maior segmento observado)
    mss_por_conexao = df.groupby('connection_id')['length'].max().dropna().to_dict()
    stats['mss_por_conexao'] = mss_por_conexao

    # 9. Fluxos elefantes e microbursts
    volume_por_conexao = df.groupby('connection_id')['length'].sum()
    elefantes = volume_por_conexao.sort_values(ascending=False).head(10).to_dict()
    stats['fluxos_elefantes'] = elefantes

    df['timestamp_rounded'] = df['timestamp'].dt.floor('s')
    pacotes_por_tempo = df.groupby('timestamp_rounded').size()
    microbursts = pacotes_por_tempo.sort_values(ascending=False).head(10).to_dict()
    stats['microbursts'] = microbursts

    # 10. Portas destino mais usadas
    ports = df['dst_port'].value_counts().head(10).to_dict()
    stats['top_aplicacoes_portas'] = ports

    # Dados auxiliares para gráficos
    stats['top_ips_destino'] = dict(df['dst_ip'].value_counts().head(10))
    contagem_tempo = df.groupby(df['timestamp'].dt.floor('s')).size()
    stats['pacotes_por_tempo'] = contagem_tempo.reset_index(name='count').to_dict(orient='records')
    stats['trafego_por_minuto'] = df.groupby(df['timestamp'].dt.floor('min'))['length'].sum().to_dict()

    # Mapa de calor (sem iterrows)
    df['minuto'] = df['timestamp'].dt.floor('min')
    top_ips = df['src_ip'].value_counts().head(10).index.tolist()
    heatmap_df = df[df['src_ip'].isin(top_ips)]
    heatmap_data = heatmap_df.groupby(['src_ip', 'minuto']).size().unstack(fill_value=0)
    stats['heatmap_ips_tempo'] = {
        'matriz': heatmap_data.to_dict(),
        'ips': heatmap_data.index.tolist(),
        'tempos': heatmap_data.columns.astype(str).tolist()
    }

    # Resumo
    resumo_metricas = {
        "janela_congestionamento": {k: [v[1] for v in vals] for k, vals in stats['janela_congestionamento'].items()},
        "rtt_por_conexao": dict(stats['rtt_por_conexao']),
        "tempos_estabelecimento": stats['tempos_estabelecimento'],
        "taxa_retransmissoes": stats['taxa_retransmissoes'],
        "duracao_conexoes": stats['duracao_conexoes'],
        "throughput_por_conexao": stats['throughput_por_conexao'],
        "fluxos_elefantes": stats['fluxos_elefantes'],
        "microbursts": stats['microbursts'],
        "top_aplicacoes_portas": stats['top_aplicacoes_portas'],
        "top_ips_destino": stats['top_ips_destino']
    }

    return stats, resumo_metricas

def salvar_estatisticas(stats, caminho="estatisticas.json"):
    def tornar_json_friendly(obj):
        if isinstance(obj, defaultdict) or isinstance(obj, dict):
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


if __name__ == "__main__":
    stats, resumo = analisar_estatisticas("data_300k.csv")
    salvar_estatisticas(stats, "stats_completo.json")
    salvar_estatisticas(resumo, "stats_metricas.json")
