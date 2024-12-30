import os
import zipfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def process_manifest(file_path):
    """Corrige e adiciona a linha no arquivo manifest.sii"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        inside_package = False
        corrected_lines = []
        mp_mod_optional_found = False

        for line in lines:
            stripped_line = line.strip()

            # Detecta o início do bloco mod_package
            if stripped_line.startswith("mod_package"):
                inside_package = True

            # Remove linhas duplicadas de "mp_mod_optional: true"
            if stripped_line == "mp_mod_optional: true":
                if mp_mod_optional_found:
                    continue
                mp_mod_optional_found = True

            # Detecta o fechamento do bloco e insere a linha, se necessário
            if stripped_line == "}" and inside_package:
                if not mp_mod_optional_found:
                    corrected_lines.append("    mp_mod_optional: true\n")
                    mp_mod_optional_found = True
                inside_package = False

            corrected_lines.append(line)

        # Reescreve o arquivo somente se houver alterações
        if lines != corrected_lines:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(corrected_lines)
            return f"Modificado: {file_path}"

        return f"Já está correto: {file_path}"

    except Exception as e:
        return f"Erro ao processar {file_path}: {e}"


def process_zip(file_path, error_log):
    """Processa arquivos ZIP"""
    temp_dir = Path(file_path).parent / "temp_zip"
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if "manifest.sii" not in zip_ref.namelist():
                return f"Sem manifest.sii: {file_path}"
            zip_ref.extractall(temp_dir)

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file == "manifest.sii":
                    process_manifest(os.path.join(root, file))

        with zipfile.ZipFile(file_path, 'w') as zip_ref:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, temp_dir)
                    zip_ref.write(full_path, arcname)

        return f"Processado ZIP: {file_path}"
    except Exception as e:
        error_log.write(f"Erro ao processar ZIP {file_path}: {e}\n")
        return f"Erro ao processar ZIP: {file_path}"
    finally:
        remove_temp_dir(temp_dir, error_log)


def remove_temp_dir(temp_dir, error_log):
    """Remove a pasta temporária com mais controle"""
    try:
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except Exception as e:
                    error_log.write(f"Erro ao remover arquivo {file}: {e}\n")
            for dir in dirs:
                try:
                    os.rmdir(os.path.join(root, dir))
                except Exception as e:
                    error_log.write(f"Erro ao remover diretório {dir}: {e}\n")
        temp_dir.rmdir()
    except Exception as e:
        error_log.write(f"Erro ao remover pasta temporária {temp_dir}: {e}\n")


class ModProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ativar Mods Opcionais")
        self.root.geometry("900x600")
        self.theme = "dark"
        self.error_log_path = "error_log.txt"

        self.setup_ui()

    def setup_ui(self):
        """Configura a interface gráfica"""
        self.root.configure(bg="black")
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(self.frame, wrap=tk.WORD, bg="black", fg="white", insertbackground="white", font=("Consolas", 12))
        self.log_text.insert(tk.END, "Selecione a pasta da Steam Workshop para iniciar.\n", "title")
        self.log_text.insert(tk.END, "Caminho sugerido: C:/Program Files (x86)/Steam/steamapps/workshop/content/227300\n")
        self.log_text.tag_config("title", font=("Helvetica", 14, "bold"))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.btn_frame = tk.Frame(self.root, bg="black")
        self.btn_frame.pack(fill=tk.X)

        self.select_btn = tk.Button(self.btn_frame, text="Selecionar Pasta", command=self.select_folder, bg="gray", fg="white", font=("Helvetica", 12))
        self.select_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.run_btn = tk.Button(self.btn_frame, text="Executar", state=tk.DISABLED, command=self.start_processing, bg="gray", fg="white", font=("Helvetica", 12))
        self.run_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.theme_btn = tk.Button(self.btn_frame, text="Alternar Tema", command=self.toggle_theme, bg="gray", fg="white", font=("Helvetica", 12))
        self.theme_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        if self.theme == "dark":
            self.root.configure(bg="white")
            self.frame.configure(bg="white")
            self.log_text.configure(bg="white", fg="black", insertbackground="black")
            self.theme = "light"
        else:
            self.root.configure(bg="black")
            self.frame.configure(bg="black")
            self.log_text.configure(bg="black", fg="white", insertbackground="white")
            self.theme = "dark"

    def select_folder(self):
        """Permite ao usuário selecionar a pasta da Steam"""
        folder = filedialog.askdirectory(title="Selecione a pasta da Steam Workshop (ex.: .../workshop/content/227300)")
        if folder:
            self.base_folder = folder
            self.log_text.insert(tk.END, f"Pasta selecionada: {folder}\n")
            self.run_btn.config(state=tk.NORMAL)

    def start_processing(self):
        """Inicia o processamento"""
        self.run_btn.config(state=tk.DISABLED, text="Processando...")
        self.log_text.insert(tk.END, "Iniciando processamento...\n")
        self.progress_bar['value'] = 0

        thread = threading.Thread(target=self.process_files)
        thread.start()

    def process_files(self):
        """Processa os arquivos"""
        all_files = []
        for root, dirs, files in os.walk(self.base_folder):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        sii_files = [f for f in all_files if f.endswith("manifest.sii")]
        zip_files = [f for f in all_files if f.endswith(".zip")]

        total_files = len(sii_files) + len(zip_files)
        self.progress_bar['maximum'] = total_files

        with open(self.error_log_path, "w", encoding="utf-8") as error_log:
            for i, file in enumerate(sii_files + zip_files):
                if file.endswith("manifest.sii"):
                    result = process_manifest(file)
                elif file.endswith(".zip"):
                    result = process_zip(file, error_log)
                else:
                    result = f"Ignorado: {file}"

                self.log_text.insert(tk.END, f"{result}\n")
                self.progress_bar['value'] = i + 1

        self.run_btn.config(state=tk.NORMAL, text="Executar")
        self.log_text.insert(tk.END, "Processamento concluído!\n")
        messagebox.showinfo("Concluído", "Processamento finalizado com sucesso! Verifique error_log.txt para detalhes de erros.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModProcessorApp(root)
    root.mainloop()
