# T2_Redes
Trabalho 2 da disciplina de Redes de Computadores.
 • Filtrar apenas pacotes TCP das capturas (.pcap)

Métricas Extraídas:

 • Duração da conexão
 • RTT estimado (por timestamp dos ACKs)
 • Número de retransmissões
 • Throughput médio por conexão
 • Evolução da janela de congestionamento
 • Tempo de handshake 
 • Distribuição dos tamanhos dos segmentos
 • Identificiar o MSS por conexão
 • Identificar fluxos elefantes e microbursts
 • Top 10 aplicações mais acessadas (observar números das portas)

Gráficos Gerados:

 • Curva da janela de congestionamento ao longo do tempo.
 • Gráfico de dispersão do RTT por conexão.
 • CDF do tempo de estabelecimento das conexões.
 • Histograma da taxa de retransmissões.
 • Comparação entre conexões curtas e longas.


EXPLICAÇÃO DOS ARQUIVOS:

dataProcessing.py --> processa os dados e salva nos jsons

extrator.c --> realiza a extração dos pacotes, salvando-os em data.csv

filtro_tcp.c --> arquivo auxiliar usado para filtrar um arquivo .pcap, 
    gerando um novo arquivo .pcap apenas com pacotes TCP

graficos.py --> gera os gráficos obrigatórios (utiliza stats_completo.json)

metricas.py --> gera as métricas obrigatórias (utiliza stats_metricas.json)

explanation.txt --> descreve os métodos de obtenção das estatísticas 


ESTRUTURA GERAL DOS ARQUIVOS JSON

stats_completo.json:

{
  "janela_congestionamento": {
    "conexao_id": [ [ "timestamp", valor_estimado ], ... ],
    ...
  },
  "rtt_por_conexao": [ ["conexao_id", rtt_segundos], ... ],
  "tempos_estabelecimento": [ tempo_em_segundos, ... ],
  "taxa_retransmissoes": {
    "ip_origem": taxa_float,
    ...
  },
  "duracao_conexoes": {
    "conexao_id": duracao_em_segundos,
    ...
  },
  "throughput_por_conexao": {
    "conexao_id": bytes_por_segundo,
    ...
  },
  "tamanhos_segmentos": [ tamanho_bytes, ... ],
  "mss_por_conexao": {
    "conexao_id": maior_segmento_bytes,
    ...
  },
  "fluxos_elefantes": {
    "conexao_id": volume_total_bytes,
    ...
  },
  "microbursts": {
    "timestamp_segundo": total_pacotes,
    ...
  },
  "top_aplicacoes_portas": {
    "porta_destino": quantidade_pacotes,
    ...
  },
  "top_ips_destino": {
    "ip": quantidade_pacotes,
    ...
  },
  "pacotes_por_tempo": [
    {
      "timestamp": "YYYY-MM-DDTHH:MM:SS",
      "count": total_pacotes
    },
    ...
  ],
  "trafego_por_minuto": {
    "YYYY-MM-DDTHH:MM:00": soma_bytes,
    ...
  },
  "heatmap_ips_tempo": {
    "matriz": {
      "ip_origem": {
        "YYYY-MM-DDTHH:MM:00": total_pacotes,
        ...
      },
      ...
    },
    "ips": [ "ip_origem1", "ip_origem2", ... ],
    "tempos": [ "YYYY-MM-DDTHH:MM:00", ... ]
  }
}


stats_metricas.json:

{
  "janela_congestionamento": {
    "conexao_id": [ valor_estimado_1, valor_estimado_2, ... ],
    ...
  },
  "rtt_por_conexao": {
    "conexao_id": rtt_segundos,
    ...
  },
  "tempos_estabelecimento": [ tempo_em_segundos, ... ],
  "taxa_retransmissoes": {
    "ip_origem": taxa_float,
    ...
  },
  "duracao_conexoes": {
    "conexao_id": duracao_em_segundos,
    ...
  },
  "throughput_por_conexao": {
    "conexao_id": bytes_por_segundo,
    ...
  },
  "fluxos_elefantes": {
    "conexao_id": volume_total_bytes,
    ...
  },
  "microbursts": {
    "timestamp_segundo": total_pacotes,
    ...
  },
  "top_aplicacoes_portas": {
    "porta_destino": quantidade_pacotes,
    ...
  },
  "top_ips_destino": {
    "ip": quantidade_pacotes,
    ...
  }
}
