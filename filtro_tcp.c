
// Arquivo usado para gerar um novo PCAP filtrado, removendo todos pacotes que não sejam TCP

// compila: gcc filtro_tcp.c -lpcap -o filtro_tcp
// executa: ./filtro_tcp entrada.pcap saida_tcp.pcap

#include <stdio.h>
#include <stdlib.h>
#include <pcap.h>
#include <netinet/ip.h>

int main(int argc, char *argv[]) 
{
    if (argc != 3) 
    {
        fprintf(stderr, "Uso: %s entrada.pcap saida_tcp.pcap\n", argv[0]);
        return 1;
    }

    char errbuf[PCAP_ERRBUF_SIZE];
    
    pcap_t *input_handle = pcap_open_offline(argv[1], errbuf);
    if (!input_handle) 
    {
        fprintf(stderr, "Erro ao abrir arquivo de entrada: %s\n", errbuf);
        return 1;
    }

    pcap_dumper_t *output_dumper = NULL;
    output_dumper = pcap_dump_open(input_handle, argv[2]);
    if (!output_dumper) 
    {
        fprintf(stderr, "Erro ao criar arquivo de saída: %s\n", pcap_geterr(input_handle));
        pcap_close(input_handle);
        return 1;
    }

    struct pcap_pkthdr *header;
    const unsigned char *packet;
    int datalink = pcap_datalink(input_handle);
    int ethernet_header_len = (datalink == DLT_EN10MB) ? 14 : 0;

    while (pcap_next_ex(input_handle, &header, &packet) == 1) 
    {
        if (header->caplen < ethernet_header_len + sizeof(struct iphdr))
            continue;

        const struct iphdr *ip_header = (struct iphdr *)(packet + ethernet_header_len);

        if (ip_header->version != 4)
            continue;

        if (ip_header->protocol == IPPROTO_TCP) 
        {
            pcap_dump((u_char *)output_dumper, header, packet);
        }
    }

    pcap_dump_close(output_dumper);
    pcap_close(input_handle);

    printf("Pacotes TCP salvos em: %s\n", argv[2]);
    return 0;
}
