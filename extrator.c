// Arquivo utilizado para extrair os arquivos TCP e escrevê-los em um csv

// passo a passo:

// editcap -c 1000000 original.pcap batches/parte.pcap  --> divide o arquivo original em partes de 1.000.000 pacotes e salva na pasta batches

// gcc extrator.c -lpcap -lpthread -o extrator  -> compilar

// ./extrator batches/parte_00*.pcap  --> rodar para todas as partes

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <pcap.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

void tcp_flags_to_str(uint8_t flags, char *out) 
{
    int idx = 0;
    if (flags & TH_FIN)  out[idx++] = 'F';
    if (flags & TH_SYN)  out[idx++] = 'S';
    if (flags & TH_RST)  out[idx++] = 'R';
    if (flags & TH_PUSH) out[idx++] = 'P';
    if (flags & TH_ACK)  out[idx++] = 'A';
    if (flags & TH_URG)  out[idx++] = 'U';
    out[idx] = '\0';
}

void manipular_pacote(unsigned char *args, const struct pcap_pkthdr *cabecalho, const unsigned char *pacote) 
{
    FILE *data = (FILE *)args;

    // Assumindo Ethernet + IPv4 + TCP
    const struct iphdr *ip_header = (struct iphdr *)(pacote + 14);
    size_t ip_header_len = ip_header->ihl * 4;

    const struct tcphdr *tcp_header = (struct tcphdr *)(pacote + 14 + ip_header_len);
    size_t tcp_header_len = tcp_header->doff * 4;

    // Calcula tamanho do segmento TCP (payload)
    size_t segmento_tcp_len = 0;
    if (cabecalho->len >= 14 + ip_header_len + tcp_header_len)
        segmento_tcp_len = cabecalho->len - 14 - ip_header_len - tcp_header_len;

    char src_ip[INET_ADDRSTRLEN], dst_ip[INET_ADDRSTRLEN];
    struct in_addr src_addr = {.s_addr = ip_header->saddr};
    struct in_addr dst_addr = {.s_addr = ip_header->daddr};

    inet_ntop(AF_INET, &src_addr, src_ip, INET_ADDRSTRLEN);
    inet_ntop(AF_INET, &dst_addr, dst_ip, INET_ADDRSTRLEN);

    uint16_t src_port = ntohs(tcp_header->source);
    uint16_t dst_port = ntohs(tcp_header->dest);
    uint32_t seq = ntohl(tcp_header->seq);
    uint32_t ack = ntohl(tcp_header->ack_seq);
    uint16_t window = ntohs(tcp_header->window);

    double timestamp = cabecalho->ts.tv_sec + cabecalho->ts.tv_usec / 1000000.0;

    char flags_str[8];
    tcp_flags_to_str(tcp_header->th_flags, flags_str);

    // Parse das opções TCP para extrair MSS se houver
    int mss_value = -1;
    if (tcp_header->th_flags & TH_SYN) {
        const unsigned char *options = (const unsigned char *)(tcp_header + 1);
        int optlen = tcp_header_len - sizeof(struct tcphdr);
        int i = 0;
        while (i < optlen) {
            uint8_t kind = options[i];

            if (kind == 0) break;              // End of options list
            if (kind == 1) { i++; continue; }  // No-Op (1 byte)

            if (i + 1 >= optlen) break;
            uint8_t len = options[i + 1];
            if (len < 2 || i + len > optlen) break;

            if (kind == 2 && len == 4) {
                mss_value = (options[i + 2] << 8) | options[i + 3];
                break;
            }

            i += len;
        }
    }

    pthread_mutex_lock(&lock);
    fprintf(data, "%.6f,%s,%d,%s,%d,TCP,%u,%s,%u,%u,%u,%zu,%d\n",
        timestamp,
        src_ip, src_port,
        dst_ip, dst_port,
        cabecalho->len,
        flags_str,
        seq,
        ack,
        window,
        segmento_tcp_len,
        mss_value
    );
    pthread_mutex_unlock(&lock);
}

void *processar_pcap(void *arg) 
{
    char *nome_arquivo = (char *)arg;

    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t *handle = pcap_open_offline(nome_arquivo, errbuf);
    if (!handle) 
    {
        fprintf(stderr, "Erro ao abrir %s: %s\n", nome_arquivo, errbuf);
        return NULL;
    }

    FILE *data = fopen("data.csv", "a");
    if (!data) 
    {
        perror("Erro ao abrir data.csv");
        pcap_close(handle);
        return NULL;
    }

    pcap_loop(handle, 0, manipular_pacote, (unsigned char *)data);
    fclose(data);
    pcap_close(handle);

    printf("Thread finalizou: %s\n", nome_arquivo);
    return NULL;
}

int main(int argc, char *argv[]) 
{
    if (argc < 2) 
    {
        printf("Uso: %s arquivo1.pcap arquivo2.pcap ...\n", argv[0]);
        return 1;
    }

    FILE *data = fopen("data.csv", "w");
    fprintf(data, "timestamp,src_ip,src_port,dst_ip,dst_port,protocol,length,flags,seq,ack,window,segmento_tcp_len,mss\n");
    fclose(data);

    int num_arquivos = argc - 1;
    pthread_t threads[num_arquivos];

    for (int i = 0; i < num_arquivos; i++) 
    {
        pthread_create(&threads[i], NULL, processar_pcap, argv[i + 1]);
    }

    for (int i = 0; i < num_arquivos; i++) 
    {
        pthread_join(threads[i], NULL);
    }

    printf("Processamento finalizado.\n");
    return 0;
}
