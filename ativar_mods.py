import os

def process_manifest(file_path):
    """
    Processa o arquivo manifest.sii para adicionar a linha mp_mod_optional: true
    """
    try:
        # Lê o conteúdo do arquivo
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Verifica se a linha já existe
        if any("mp_mod_optional: true" in line for line in lines):
            print(f"A linha 'mp_mod_optional: true' já existe no arquivo: {file_path}")
            return

        # Insere a linha antes da última chave "}"
        modified_lines = []
        for line in lines:
            modified_lines.append(line)
            if "{" in line:  # Adiciona após a primeira abertura de chave
                modified_lines.append("    mp_mod_optional: true\n")

        # Escreve de volta no arquivo
        with open(file_path, 'w') as file:
            file.writelines(modified_lines)

        print(f"Modificação concluída no arquivo: {file_path}")

    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")


def main():
    """
    Função principal: verifica diretórios e processa todos os arquivos manifest.sii
    """
    # Caminho base da pasta 227300
    base_dir = r"F:\SteamLibrary\steamapps\workshop\content\227300"

    if not os.path.exists(base_dir):
        print(f"Erro: O diretório {base_dir} não existe.")
        return

    print(f"Verificando arquivos em: {base_dir}")

    # Percorre a estrutura de diretórios procurando por manifest.sii
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "manifest.sii":
                file_path = os.path.join(root, file)
                print(f"Encontrado: {file_path}")
                process_manifest(file_path)

    print("Processamento concluído!")


if __name__ == "__main__":
    main()
