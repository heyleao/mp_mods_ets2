import os
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor

class ModProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ativar Mods Opcionais")
        self.root.geometry("900x600")
        self.theme = "dark"
        self.error_log_path = "error_log.txt"
        self.max_threads = os.cpu_count()  # Define a quantidade de threads igual aos núcleos lógicos do sistema

        self.setup_ui()

    def setup_ui(self):
        """Configura a interface gráfica"""
        self.root.configure(bg="black")
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(self.frame, wrap=tk.WORD, bg="black", fg="white", insertbackground="white", font=("Consolas", 12))
        self.log_text.insert(tk.END, f"Selecione a pasta da Steam Workshop para iniciar. Usando {self.max_threads} threads.\n", "title")
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
        """Inicia o processamento em uma thread separada"""
        self.run_btn.config(state=tk.DISABLED, text="Processando...")
        self.log_text.insert(tk.END, "Iniciando processamento...\n")
        self.progress_bar['value'] = 0

        thread_pool = ThreadPoolExecutor(max_workers=self.max_threads)
        thread_pool.submit(self.process_files)

    def process_files(self):
        """Processa os arquivos usando múltiplas threads"""
        all_files = [os.path.join(root, file) for root, dirs, files in os.walk(self.base_folder) for file in files if file.lower() == "manifest.sii" or file.endswith(".zip")]
        total_files = len(all_files)
        self.progress_bar['maximum'] = total_files

        with open(self.error_log_path, "w", encoding="utf-8") as error_log:
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = {executor.submit(self.process_single_file, file, error_log): file for file in all_files}

                for i, future in enumerate(futures):
                    try:
                        result = future.result()
                        self.log_text.insert(tk.END, f"{result}\n")
                    except Exception as e:
                        self.log_text.insert(tk.END, f"Erro: {e}\n")
                    self.progress_bar['value'] = i + 1

        self.run_btn.config(state=tk.NORMAL, text="Executar")
        self.log_text.insert(tk.END, "Processamento concluído!\n")
        messagebox.showinfo("Concluído", "Processamento finalizado com sucesso!")

    def process_single_file(self, file_path, error_log):
        """Processa um único arquivo, seja ZIP ou manifest.sii"""
        if file_path.lower().endswith("manifest.sii"):
            return self.process_manifest(file_path)
        elif file_path.endswith(".zip"):
            return self.process_zip(file_path, error_log)
        return f"Ignorado: {file_path}"

    def process_manifest(self, file_path):
        """Corrige e adiciona a linha no arquivo manifest.sii se necessário"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            if any("mp_mod_optional: true" in line for line in lines):
                return f"Já está correto: {file_path}"

            corrected_lines = []
            inside_package = False

            for line in lines:
                corrected_lines.append(line)
                if line.strip().startswith("mod_package"):
                    inside_package = True
                if inside_package and line.strip() == "}":
                    corrected_lines.insert(-1, "    mp_mod_optional: true\n")
                    inside_package = False

            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(corrected_lines)

            return f"Modificado: {file_path}"

        except Exception as e:
            return f"Erro ao processar {file_path}: {e}"

    def process_zip(self, file_path, error_log):
        """Processa apenas o arquivo manifest.sii na raiz do ZIP sem alterar a estrutura"""
        temp_dir = Path(file_path).parent / "temp_zip"
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if "manifest.sii" not in zip_ref.namelist():
                    return f"Sem manifest.sii na raiz: {file_path}"
                zip_ref.extract("manifest.sii", temp_dir)

            manifest_path = temp_dir / "manifest.sii"
            result = self.process_manifest(manifest_path)

            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zip_ref.write(full_path, arcname)

            return result
        except Exception as e:
            error_log.write(f"Erro ao processar ZIP {file_path}: {e}\n")
            return f"Erro ao processar ZIP: {file_path}"
        finally:
            self.remove_temp_dir(temp_dir, error_log)

    def remove_temp_dir(self, temp_dir, error_log):
        """Remove a pasta temporária com mais controle"""
        try:
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            temp_dir.rmdir()
        except Exception as e:
            error_log.write(f"Erro ao remover pasta temporária {temp_dir}: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModProcessorApp(root)
    root.mainloop()
