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
        self.error_log_path = "error_log.txt"
        self.max_threads = os.cpu_count()

        self.setup_ui()

    def setup_ui(self):
        self.root.configure(bg="black")
        self.log_text = tk.Text(self.root, wrap=tk.WORD, bg="black", fg="white", font=("Consolas", 12))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.select_btn = tk.Button(self.root, text="Selecionar Pasta", command=self.select_folder, bg="gray", fg="white")
        self.select_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.run_btn = tk.Button(self.root, text="Executar", state=tk.DISABLED, command=self.start_processing, bg="gray", fg="white")
        self.run_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta da Steam Workshop")
        if folder:
            self.base_folder = folder
            self.log_text.insert(tk.END, f"Pasta selecionada: {folder}\n")
            self.run_btn.config(state=tk.NORMAL)

    def start_processing(self):
        self.run_btn.config(state=tk.DISABLED, text="Processando...")
        self.log_text.insert(tk.END, "Iniciando processamento...\n")
        self.progress_bar['value'] = 0

        thread_pool = ThreadPoolExecutor(max_workers=self.max_threads)
        thread_pool.submit(self.process_files)

    def process_files(self):
        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.base_folder) for file in files if file.endswith(".zip")]
        self.progress_bar['maximum'] = len(all_files)

        with open(self.error_log_path, "w", encoding="utf-8") as error_log:
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = {executor.submit(self.process_zip, file, error_log): file for file in all_files}

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

    def process_zip(self, file_path, error_log):
        """Extrai, modifica e reinsere o manifest.sii sem recriar todo o ZIP"""
        file_path = Path(file_path)  # Converte string para Path
        temp_zip_path = file_path.with_name(f"{file_path.stem}_temp.zip")

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if "manifest.sii" not in zip_ref.namelist():
                    return f"Sem manifest.sii na raiz: {file_path}"
                manifest_data = zip_ref.read("manifest.sii").decode("utf-8")

            lines = manifest_data.splitlines()
            if "mp_mod_optional: true" in manifest_data:
                return f"Já está correto: {file_path}"

            corrected_lines = []
            inside_package = False
            for line in lines:
                corrected_lines.append(line)
                if line.strip().startswith("mod_package"):
                    inside_package = True
                if inside_package and line.strip() == "}":
                    corrected_lines.insert(-1, "    mp_mod_optional: true")
                    inside_package = False

            new_manifest_data = "\n".join(corrected_lines).encode("utf-8")

            with zipfile.ZipFile(temp_zip_path, 'w') as new_zip:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    for item in zip_ref.infolist():
                        if item.filename != "manifest.sii":
                            new_zip.writestr(item.filename, zip_ref.read(item.filename))
                    new_zip.writestr("manifest.sii", new_manifest_data)

            os.replace(temp_zip_path, file_path)
            return f"Modificado: {file_path}"

        except Exception as e:
            error_log.write(f"Erro ao processar ZIP {file_path}: {e}\n")
            return f"Erro ao processar ZIP: {file_path}"

if __name__ == "__main__":
    root = tk.Tk()
    app = ModProcessorApp(root)
    root.mainloop()
