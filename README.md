# T2_Redes
Trabalho 2 da disciplina de Redes de Computadores.
 • Filtrar apenas pacotes TCP das capturas (.pcap)

Métricas Extraídas:

 • Duração da conexão v
 • RTT estimado (por timestamp dos ACKs) V
 • Número de retransmissões V
 • Throughput médio por conexão VF
 • Evolução da janela de congestionamento V
 • Tempo de handshake V
 • Distribuição dos tamanhos dos segmentos
 • Identificiar o MSS por conexão
 • Identificar fluxos elefantes e microbursts F
 • Top 10 aplicações mais acessadas (observar números das portas) V

Gráficos Gerados:

 • Curva da janela de congestionamento ao longo do tempo. F
 • Gráfico de dispersão do RTT por conexão.  F
 • CDF do tempo de estabelecimento das conexões.  F
 • Histograma da taxa de retransmissões.  V
 • Comparação entre conexões curtas e longas.  F


EXPLICAÇÃO DOS ARQUIVOS:

dataProcessing.py --> processa os dados e salva nos jsons

extrator.c --> realiza a extração dos pacotes, salvando-os em data.csv

filtro_tcp.c --> arquivo auxiliar usado para filtrar um arquivo .pcap, 
    gerando um novo arquivo .pcap apenas com pacotes TCP

graficos.py --> gera os gráficos obrigatórios (utiliza stats_completo.json)

metricas.py --> gera as métricas obrigatórias (utiliza stats_metricas.json)

explanation.txt --> descreve os métodos de obtenção das estatísticas 


ESTRUTURA GERAL DOS ARQUIVOS JSON


Explicação atualizada dos arquivos JSON gerados
1. stats_completo.json
Este arquivo contém o conjunto completo de estatísticas extraídas e analisadas a partir do CSV de pacotes TCP. Ele inclui tanto dados brutos quanto algumas métricas e séries temporais.

Estrutura e conteúdo:
janela_congestionamento
Dicionário onde a chave é o ID da conexão (string normalizada) e o valor é uma lista de pares [timestamp, valor_estimado].
Cada par representa um instante de tempo e a estimativa da janela de congestionamento naquele momento.

rtt_por_conexao
Lista de pares [conexao_id, rtt_em_segundos].
RTT estimado (tempo entre SYN e SYN-ACK) para cada conexão onde foi possível calcular.

tempos_estabelecimento
Lista de tempos em segundos (float) representando o intervalo entre SYN e ACK final, para várias conexões.

taxa_retransmissoes
Dicionário com chave IP de origem e valor a taxa de retransmissão (float entre 0 e 1).

duracao_conexoes
Dicionário com chave conexão e valor duração da conexão em segundos (float).

throughput_por_conexao
Dicionário chave conexão e valor throughput em bytes por segundo (float).

tamanhos_segmentos
Lista de inteiros com os tamanhos (em bytes) dos segmentos TCP observados.

mss_por_conexao
Dicionário com chave conexão e valor MSS real observado (float), onde disponível (filtrado mss != -1).

fluxos_elefantes
Dicionário das 10 conexões com maior volume total de bytes enviados (bytes totais por conexão).

microbursts
Dicionário com timestamp (arredondado para segundo) e número total de pacotes nesse segundo (os 10 maiores).

top_aplicacoes_portas
Dicionário das 10 portas de destino mais frequentes e quantidade de pacotes para cada.

top_ips_destino
Dicionário dos 10 IPs de destino mais frequentes e quantidade de pacotes para cada.

pacotes_por_tempo
Lista de registros com chaves "timestamp" (string ISO) e "count" (inteiro), representando pacotes contados por segundo.

trafego_por_minuto
Dicionário com chave tempo arredondado para minuto e valor total de bytes transferidos naquele minuto.

heatmap_ips_tempo
Objeto que contém:

"matriz": dicionário aninhado ip_origem -> { tempo_minuto -> contagem_pacotes }

"ips": lista dos IPs origem considerados (top 10)

"tempos": lista dos tempos (minutos) considerados (strings ISO)

2. stats_metricas.json
Este arquivo contém um subconjunto compacto e focado em métricas para facilitar análises, comparações e visualizações rápidas. Muitas das séries temporais e listas detalhadas são convertidas em dicionários simples, ou são omitidas para manter o arquivo leve.

Estrutura e conteúdo:
janela_congestionamento
Dicionário conexao_id -> lista de valores estimados da janela de congestionamento (sem timestamps, só os valores).

rtt_por_conexao
Dicionário conexao_id -> rtt_em_segundos (float).

tempos_estabelecimento
Lista de tempos em segundos (float).

taxa_retransmissoes
Dicionário ip_origem -> taxa_float de retransmissões.

duracao_conexoes
Dicionário conexao_id -> duracao_em_segundos (float).

throughput_por_conexao
Dicionário conexao_id -> throughput_bytes_por_segundo (float).

fluxos_elefantes
Dicionário conexao_id -> volume_total_bytes (top 10 conexões com maior volume).

microbursts
Dicionário timestamp_segundo -> total_pacotes (top 10).

top_aplicacoes_portas
Dicionário porta_destino -> quantidade_pacotes (top 10).

top_ips_destino
Dicionário ip_destino -> quantidade_pacotes (top 10).