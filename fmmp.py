#!/usr/bin/env python3
"""
Interface Graphique FFmpeg NVENC - Version Corrigée
Python 3 requis - Interface pour l'encodage vidéo avec NVIDIA NVENC
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
from pathlib import Path

class FFmpegNVENCGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg NVENC GUI - Encodeur Vidéo NVIDIA")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        # Variables
        self.input_files = []
        self.output_folder = ""
        self.is_processing = False
        self.current_process = None
        
        # Vérifier FFmpeg
        self.check_ffmpeg()
        
        self.setup_ui()
        
    def check_ffmpeg(self):
        """Vérifier si FFmpeg est disponible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if 'ffmpeg version' in result.stdout:
                self.ffmpeg_available = True
                # Détecter NVENC
                result = subprocess.run(['ffmpeg', '-encoders'], 
                                      capture_output=True, text=True)
                self.nvenc_available = 'nvenc' in result.stdout.lower()
            else:
                self.ffmpeg_available = False
                self.nvenc_available = False
        except:
            self.ffmpeg_available = False
            self.nvenc_available = False
            
        if not self.ffmpeg_available:
            messagebox.showwarning(
                "FFmpeg non trouvé",
                "FFmpeg n'est pas installé ou n'est pas dans le PATH.\n\n"
                "Veuillez installer FFmpeg pour utiliser cette application."
            )
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            title_frame,
            text="🎬 FFmpeg NVENC GUI",
            font=('Arial', 18, 'bold'),
            foreground='#2c3e50'
        ).pack(side=tk.LEFT)
        
        # Status FFmpeg
        status_color = '#27ae60' if self.ffmpeg_available else '#e74c3c'
        nvenc_status = "✓ NVENC disponible" if self.nvenc_available else "✗ NVENC non disponible"
        status_text = f"FFmpeg: {'✓' if self.ffmpeg_available else '✗'} | {nvenc_status}"
        
        ttk.Label(
            title_frame,
            text=status_text,
            foreground=status_color,
            font=('Arial', 10, 'bold')
        ).pack(side=tk.RIGHT)
        
        # Notebook (onglets)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Conversion
        self.setup_conversion_tab(notebook)
        
        # Onglet Paramètres
        self.setup_settings_tab(notebook)
        
        # Onglet Logs
        self.setup_logs_tab(notebook)
        
    def setup_conversion_tab(self, notebook):
        # Onglet Conversion
        conv_frame = ttk.Frame(notebook, padding="15")
        notebook.add(conv_frame, text="🔄 Conversion")
        
        # Section fichiers d'entrée
        input_frame = ttk.LabelFrame(conv_frame, text="📁 Fichiers d'entrée", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Boutons de sélection
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            btn_frame,
            text="📄 Ajouter des fichiers vidéo",
            command=self.add_video_files
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="📁 Ajouter un dossier",
            command=self.add_video_folder
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="🗑️ Tout effacer",
            command=self.clear_files
        ).pack(side=tk.LEFT)
        
        # Liste des fichiers
        list_frame = ttk.Frame(input_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ('filename', 'path', 'size')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        self.file_tree.heading('filename', text='Nom du fichier')
        self.file_tree.heading('path', text='Chemin')
        self.file_tree.heading('size', text='Taille')
        
        self.file_tree.column('filename', width=250)
        self.file_tree.column('path', width=400)
        self.file_tree.column('size', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Menu contextuel
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🗑️ Supprimer", command=self.remove_selected_file)
        self.file_tree.bind("<Button-3>", self.show_context_menu)
        
        # Section sortie
        output_frame = ttk.LabelFrame(conv_frame, text="📂 Dossier de sortie", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        output_btn_frame = ttk.Frame(output_frame)
        output_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            output_btn_frame,
            text="📁 Choisir le dossier de sortie",
            command=self.select_output_folder
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_label = ttk.Label(
            output_btn_frame,
            text="Aucun dossier sélectionné",
            foreground='#7f8c8d'
        )
        self.output_label.pack(side=tk.LEFT)
        
        # Section paramètres de conversion
        self.setup_conversion_settings(conv_frame)
        
        # Boutons d'action
        action_frame = ttk.Frame(conv_frame)
        action_frame.pack(fill=tk.X, pady=15)
        
        self.convert_btn = ttk.Button(
            action_frame,
            text="🚀 Démarrer la conversion",
            command=self.start_conversion
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            action_frame,
            text="⏹️ Arrêter",
            command=self.stop_conversion
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress = ttk.Progressbar(action_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(action_frame, text="Prêt")
        self.progress_label.pack(side=tk.LEFT)
        
    def setup_conversion_settings(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="⚙️ Paramètres de conversion", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Notebook pour les paramètres
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.X)
        
        # Onglet Codec
        codec_frame = ttk.Frame(settings_notebook, padding="10")
        settings_notebook.add(codec_frame, text="Codec")
        
        # Encodeur vidéo
        ttk.Label(codec_frame, text="Encodeur vidéo:").grid(row=0, column=0, sticky='w', pady=5)
        self.video_encoder = tk.StringVar(value="h264_nvenc")
        encoder_combo = ttk.Combobox(codec_frame, textvariable=self.video_encoder)
        encoder_combo['values'] = ('h264_nvenc', 'hevc_nvenc', 'av1_nvenc')
        encoder_combo.grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Qualité
        ttk.Label(codec_frame, text="Qualité (CRF):").grid(row=1, column=0, sticky='w', pady=5)
        quality_frame = ttk.Frame(codec_frame)
        quality_frame.grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        self.crf = tk.IntVar(value=23)
        ttk.Scale(quality_frame, from_=0, to=51, variable=self.crf, orient=tk.HORIZONTAL).pack(side=tk.LEFT)
        self.crf_label = ttk.Label(quality_frame, text="23")
        self.crf_label.pack(side=tk.LEFT, padx=(10, 0))
        self.crf.trace('w', self.update_crf_label)
        
        # Débit max
        ttk.Label(codec_frame, text="Débit max (kbps):").grid(row=2, column=0, sticky='w', pady=5)
        self.max_bitrate = tk.StringVar(value="0")
        ttk.Entry(codec_frame, textvariable=self.max_bitrate).grid(row=2, column=1, sticky='w', pady=5, padx=(10, 0))
        ttk.Label(codec_frame, text="0 = illimité").grid(row=2, column=2, sticky='w', pady=5, padx=(5, 0))
        
        # Présets
        ttk.Label(codec_frame, text="Préset NVENC:").grid(row=3, column=0, sticky='w', pady=5)
        self.preset = tk.StringVar(value="medium")
        preset_combo = ttk.Combobox(codec_frame, textvariable=self.preset)
        preset_combo['values'] = ('p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7')
        preset_combo.grid(row=3, column=1, sticky='w', pady=5, padx=(10, 0))
        ttk.Label(codec_frame, text="(p1=rapide, p7=meilleure qualité)").grid(row=3, column=2, sticky='w', pady=5, padx=(5, 0))
        
        # Onglet Audio
        audio_frame = ttk.Frame(settings_notebook, padding="10")
        settings_notebook.add(audio_frame, text="Audio")
        
        ttk.Label(audio_frame, text="Codec audio:").grid(row=0, column=0, sticky='w', pady=5)
        self.audio_codec = tk.StringVar(value="aac")
        audio_combo = ttk.Combobox(audio_frame, textvariable=self.audio_codec)
        audio_combo['values'] = ('aac', 'ac3', 'mp3', 'copy')
        audio_combo.grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
        
        ttk.Label(audio_frame, text="Débit audio (kbps):").grid(row=1, column=0, sticky='w', pady=5)
        self.audio_bitrate = tk.StringVar(value="128")
        ttk.Entry(audio_frame, textvariable=self.audio_bitrate).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Onglet Filtres
        filters_frame = ttk.Frame(settings_notebook, padding="10")
        settings_notebook.add(filters_frame, text="Filtres")
        
        ttk.Label(filters_frame, text="Échelle (width:height):").grid(row=0, column=0, sticky='w', pady=5)
        self.scale = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.scale).grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
        ttk.Label(filters_frame, text="ex: 1920:1080, 1280:720").grid(row=0, column=2, sticky='w', pady=5, padx=(5, 0))
        
        ttk.Label(filters_frame, text="FPS:").grid(row=1, column=0, sticky='w', pady=5)
        self.fps = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.fps).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        ttk.Label(filters_frame, text="Filtres supplémentaires:").grid(row=2, column=0, sticky='w', pady=5)
        self.extra_filters = tk.StringVar()
        ttk.Entry(filters_frame, textvariable=self.extra_filters).grid(row=2, column=1, columnspan=2, sticky='w', pady=5, padx=(10, 0))
        
    def setup_settings_tab(self, notebook):
        settings_frame = ttk.Frame(notebook, padding="15")
        notebook.add(settings_frame, text="🔧 Paramètres")
        
        # Paramètres généraux
        general_frame = ttk.LabelFrame(settings_frame, text="Paramètres généraux", padding="10")
        general_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(general_frame, text="Chemin FFmpeg:").grid(row=0, column=0, sticky='w', pady=5)
        self.ffmpeg_path = tk.StringVar(value="ffmpeg")
        ttk.Entry(general_frame, textvariable=self.ffmpeg_path).grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
        
        ttk.Label(general_frame, text="Suffixe des fichiers de sortie:").grid(row=1, column=0, sticky='w', pady=5)
        self.output_suffix = tk.StringVar(value="_encoded")
        ttk.Entry(general_frame, textvariable=self.output_suffix).grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))
        
        # Paramètres avancés
        advanced_frame = ttk.LabelFrame(settings_frame, text="Paramètres avancés", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.overwrite = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Écraser les fichiers existants", variable=self.overwrite).pack(anchor='w', pady=2)
        
        self.keep_structure = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Conserver la structure des dossiers", variable=self.keep_structure).pack(anchor='w', pady=2)
        
        self.two_pass = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Encodage en deux passes", variable=self.two_pass).pack(anchor='w', pady=2)
        
    def setup_logs_tab(self, notebook):
        logs_frame = ttk.Frame(notebook, padding="15")
        notebook.add(logs_frame, text="📋 Logs")
        
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            height=20,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons logs
        log_btn_frame = ttk.Frame(logs_frame)
        log_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            log_btn_frame,
            text="📄 Effacer les logs",
            command=self.clear_logs
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            log_btn_frame,
            text="💾 Sauvegarder les logs",
            command=self.save_logs
        ).pack(side=tk.LEFT)
        
    def update_crf_label(self, *args):
        self.crf_label.config(text=str(self.crf.get()))
    
    def add_video_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers vidéo",
            filetypes=[
                ("Vidéos", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if files:
            self.input_files.extend(files)
            self.update_file_list()
    
    def add_video_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier contenant des vidéos")
        if folder:
            video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v')
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(video_extensions):
                        self.input_files.append(os.path.join(root, file))
            self.update_file_list()
    
    def update_file_list(self):
        # Vider la liste
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Ajouter les fichiers
        for file_path in self.input_files:
            filename = os.path.basename(file_path)
            try:
                size = os.path.getsize(file_path)
                size_str = self.format_file_size(size)
            except:
                size_str = "N/A"
            
            self.file_tree.insert('', tk.END, values=(filename, file_path, size_str))
        
        # Mettre à jour le bouton de conversion
        self.update_convert_button()
    
    def format_file_size(self, size):
        """Formater la taille du fichier"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def show_context_menu(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def remove_selected_file(self):
        selected = self.file_tree.selection()
        if selected:
            item = selected[0]
            values = self.file_tree.item(item, 'values')
            file_path = values[1]  # Le chemin est dans la deuxième colonne
            self.input_files.remove(file_path)
            self.file_tree.delete(item)
            self.update_convert_button()
    
    def clear_files(self):
        if self.input_files:
            result = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer tous les fichiers?")
            if result:
                self.input_files.clear()
                self.update_file_list()
    
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=folder)
            self.update_convert_button()
    
    def update_convert_button(self):
        """Activer/désactiver le bouton de conversion"""
        if self.input_files and self.output_folder and self.ffmpeg_available:
            self.convert_btn.config(state='normal')
        else:
            self.convert_btn.config(state='disabled')
    
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder les logs",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Logs sauvegardés: {filename}")
    
    def log_message(self, message):
        """Ajouter un message aux logs"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def build_ffmpeg_command(self, input_file, output_file):
        """Construire la commande FFmpeg"""
        cmd = [self.ffmpeg_path.get(), '-i', input_file]
        
        # Options vidéo
        video_filters = []
        
        # Échelle
        if self.scale.get():
            video_filters.append(f"scale={self.scale.get()}")
        
        # FPS
        if self.fps.get():
            video_filters.append(f"fps={self.fps.get()}")
        
        # Filtres supplémentaires
        if self.extra_filters.get():
            video_filters.append(self.extra_filters.get())
        
        # Ajouter les filtres vidéo
        if video_filters:
            cmd.extend(['-vf', ','.join(video_filters)])
        
        # Codec vidéo
        cmd.extend([
            '-c:v', self.video_encoder.get(),
            '-preset', self.preset.get(),
            '-crf', str(self.crf.get())
        ])
        
        # Débit max
        if self.max_bitrate.get() and self.max_bitrate.get() != "0":
            cmd.extend(['-maxrate', f"{self.max_bitrate.get()}k"])
        
        # Codec audio
        if self.audio_codec.get() == 'copy':
            cmd.extend(['-c:a', 'copy'])
        else:
            cmd.extend([
                '-c:a', self.audio_codec.get(),
                '-b:a', f"{self.audio_bitrate.get()}k"
            ])
        
        # Overwrite
        if self.overwrite.get():
            cmd.append('-y')
        else:
            cmd.append('-n')
        
        # Fichier de sortie
        cmd.append(output_file)
        
        return cmd
    
    def get_output_filename(self, input_file):
        """Générer le nom de fichier de sortie"""
        input_path = Path(input_file)
        suffix = self.output_suffix.get()
        output_filename = f"{input_path.stem}{suffix}{input_path.suffix}"
        
        if self.keep_structure.get():
            # Conserver la structure des dossiers
            relative_path = input_path.relative_to(input_path.anchor)
            output_path = Path(self.output_folder) / relative_path.parent / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Juste dans le dossier de sortie
            output_path = Path(self.output_folder) / output_filename
        
        return str(output_path)
    
    def start_conversion(self):
        """Démarrer la conversion"""
        if not self.input_files:
            messagebox.showwarning("Aucun fichier", "Veuillez sélectionner des fichiers à convertir.")
            return
        
        if not self.output_folder:
            messagebox.showwarning("Aucun dossier de sortie", "Veuillez sélectionner un dossier de sortie.")
            return
        
        self.is_processing = True
        self.convert_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.start()
        
        # Démarrer le thread de conversion
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def stop_conversion(self):
        """Arrêter la conversion"""
        self.is_processing = False
        if self.current_process:
            self.current_process.terminate()
        self.convert_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.progress_label.config(text="Conversion arrêtée")
        self.log_message("=== CONVERSION ARRÊTÉE PAR L'UTILISATEUR ===")
    
    def process_files(self):
        """Traiter tous les fichiers"""
        total_files = len(self.input_files)
        processed_files = 0
        
        self.log_message(f"=== DÉBUT DE LA CONVERSION ===")
        self.log_message(f"Fichiers à traiter: {total_files}")
        self.log_message(f"Dossier de sortie: {self.output_folder}")
        self.log_message("")
        
        for input_file in self.input_files:
            if not self.is_processing:
                break
            
            output_file = self.get_output_filename(input_file)
            
            self.progress_label.config(text=f"Traitement: {os.path.basename(input_file)}")
            self.log_message(f"Conversion: {os.path.basename(input_file)}")
            self.log_message(f"Vers: {os.path.basename(output_file)}")
            
            cmd = self.build_ffmpeg_command(input_file, output_file)
            self.log_message(f"Commande: {' '.join(cmd)}")
            
            try:
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Lire la sortie en temps réel
                for line in self.current_process.stdout:
                    if not self.is_processing:
                        break
                    self.log_message(line.strip())
                
                self.current_process.wait()
                
                if self.current_process.returncode == 0:
                    self.log_message(f"✓ Succès: {os.path.basename(input_file)}")
                else:
                    self.log_message(f"✗ Échec: {os.path.basename(input_file)} (code: {self.current_process.returncode})")
                
            except Exception as e:
                self.log_message(f"✗ Erreur: {str(e)}")
            
            self.log_message("")
            processed_files += 1
        
        # Fin de la conversion
        self.is_processing = False
        self.current_process = None
        
        self.root.after(0, self.conversion_finished, processed_files, total_files)
    
    def conversion_finished(self, processed, total):
        """Appelé quand la conversion est terminée"""
        self.convert_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        self.progress_label.config(text="Conversion terminée")
        
        self.log_message(f"=== CONVERSION TERMINÉE ===")
        self.log_message(f"Fichiers traités: {processed}/{total}")
        
        if processed == total:
            messagebox.showinfo("Conversion terminée", f"Tous les {total} fichiers ont été convertis avec succès!")
        else:
            messagebox.showwarning("Conversion partielle", f"{processed}/{total} fichiers ont été convertis.")

def main():
    root = tk.Tk()
    app = FFmpegNVENCGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()