import pandas as pd
from datetime import datetime, timezone

def limpar_csv_arquivo(caminho_original, caminho_corrigido):
    linhas_validas = []
    num_colunas_esperado = None

    with open(caminho_original, "r", encoding="utf-8") as origem:
        for i, linha in enumerate(origem):
            campos = linha.strip().split(',')

            if i == 0:
                num_colunas_esperado = len(campos)
                linhas_validas.append(','.join(campos) + '\n')
                continue

            if len(campos) != num_colunas_esperado:
                continue

            try:
                timestamp = campos[0]
                # Keep as float, do not round!
                ts_float = float(timestamp)
                data = datetime.fromtimestamp(ts_float, timezone.utc)
                if data.year != 2025:
                    continue  # Mantém só pacotes do ano 2025

                campos[0] = str(ts_float)
                linhas_validas.append(','.join(campos) + '\n')

            except (ValueError, IndexError, OverflowError, OSError):
                continue

    with open(caminho_corrigido, "w", encoding="utf-8") as destino:
        destino.writelines(linhas_validas)

    print(f"[OK] Arquivo filtrado e corrigido salvo em: {caminho_corrigido}")

def pegar_primeiras_linhas(caminho_entrada, caminho_saida, n_linhas=200_000):
    """
    Lê as primeiras `n_linhas` do CSV e salva em novo arquivo,
    preservando o cabeçalho.
    """
    df = pd.read_csv(caminho_entrada, nrows=n_linhas, low_memory=False)

    cabecalho_padrao = ",".join(df.columns.tolist()) + "\n"

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(cabecalho_padrao)
        df.to_csv(f, index=False, header=False, lineterminator='\n')

    print(f"[OK] {n_linhas} linhas salvas em: {caminho_saida}")

# === Execução ===
if __name__ == "__main__":
    caminho_entrada = "data.csv"
    caminho_filtrado = "data_filtrado.csv"
    caminho_saida = "data_200k.csv"

    limpar_csv_arquivo(caminho_entrada, caminho_filtrado)
    pegar_primeiras_linhas(caminho_filtrado, caminho_saida)


