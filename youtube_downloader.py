import os
import io
import urllib.request
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import imageio_ffmpeg
import yt_dlp

# Set the appearance mode and default color theme
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup main window
        self.title("Descargador de YouTube")
        self.geometry("680x520")
        self.resizable(False, False)

        # Variables
        self.download_folder = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.video_info = None
        self.is_downloading = False

        # --- UI Components ---
        
        # Title Label
        self.title_label = ctk.CTkLabel(self, text="Descargador de Videos - YouTube", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # URL Frame
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=20, pady=10)

        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="Ingresa la URL del video de YouTube...", width=400)
        self.url_entry.pack(side="left", padx=(0, 10))

        self.search_btn = ctk.CTkButton(self.url_frame, text="Buscar", width=100, command=self.search_video)
        self.search_btn.pack(side="left")

        # Info Frame
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.thumbnail_label = ctk.CTkLabel(self.info_frame, text="")
        self.thumbnail_label.pack(side="left", padx=10, pady=10)

        self.video_title_label = ctk.CTkLabel(self.info_frame, text="Título: (Esperando búsqueda...)", wraplength=450, justify="left")
        self.video_title_label.pack(side="left", pady=10, padx=10, anchor="w")

        # Options Frame
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=20, pady=10)

        # Format Selection
        self.format_label = ctk.CTkLabel(self.options_frame, text="Formato:")
        self.format_label.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")

        self.format_var = tk.StringVar(value="mp4")
        self.rb_mp4 = ctk.CTkRadioButton(self.options_frame, text="MP4 (Video)", variable=self.format_var, value="mp4")
        self.rb_mp4.grid(row=0, column=1, padx=10, pady=10)

        self.rb_mp3 = ctk.CTkRadioButton(self.options_frame, text="MP3 (Audio)", variable=self.format_var, value="mp3")
        self.rb_mp3.grid(row=0, column=2, padx=10, pady=10)

        # Folder Selection
        self.folder_label = ctk.CTkLabel(self.options_frame, text="Destino:")
        self.folder_label.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")

        self.folder_entry = ctk.CTkEntry(self.options_frame, textvariable=self.download_folder, width=250, state="disabled")
        self.folder_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="we")

        self.folder_btn = ctk.CTkButton(self.options_frame, text="Examinar...", width=100, command=self.select_folder)
        self.folder_btn.grid(row=1, column=3, padx=10, pady=10)

        # Progress Frame
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=10)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Esperando...")
        self.progress_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=560)
        self.progress_bar.pack(pady=(5, 0))
        self.progress_bar.set(0)

        # Action Buttons Frame
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=10)

        self.reset_btn = ctk.CTkButton(self.action_frame, text="Nuevo / Reiniciar", width=150, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.reset_ui)
        self.reset_btn.pack(side="left", padx=(0, 10))

        self.download_btn = ctk.CTkButton(self.action_frame, text="Descargar", width=150, command=self.start_download, state="disabled")
        self.download_btn.pack(side="right")

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder.get(), title="Seleccionar carpeta de destino")
        if folder:
            self.download_folder.set(folder)

    def search_video(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor ingresa una URL válida.")
            return

        self.search_btn.configure(state="disabled", text="Buscando...")
        self.video_title_label.configure(text="Buscando información del video...")
        self.download_btn.configure(state="disabled")

        # Run fetch in a separate thread to avoid freezing UI
        threading.Thread(target=self._fetch_video_info, args=(url,), daemon=True).start()

    def _fetch_video_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True, # Only extract info, don't download
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title', 'Título desconocido')
                uploader = info.get('uploader', 'Desconocido')
                thumbnail_url = info.get('thumbnail', None)
                
                # Verify if it's a playlist
                if 'entries' in info:
                    self.video_info = info['entries'][0] # Take first video for simplicity, or handle playlist
                    title = self.video_info.get('title', title) + " (Lista de reproducción)"
                    thumbnail_url = self.video_info.get('thumbnail', thumbnail_url)
                else:
                    self.video_info = info

                self.after(0, self._update_gui_after_fetch, f"Título: {title}\nCanal: {uploader}", True, thumbnail_url)
        except Exception as e:
            self.after(0, self._update_gui_after_fetch, f"Error al obtener el video:\n{str(e)}", False, None)

    def _update_gui_after_fetch(self, message, success, thumbnail_url=None):
        self.video_title_label.configure(text=message)
        self.search_btn.configure(state="normal", text="Buscar")
        
        if success:
            self.download_btn.configure(state="normal")
            self.progress_label.configure(text="Listo para descargar.")
            if thumbnail_url:
                try:
                    req = urllib.request.Request(thumbnail_url, headers={'User-Agent': 'Mozilla/5.0'})
                    raw_data = urllib.request.urlopen(req).read()
                    image = Image.open(io.BytesIO(raw_data))
                    
                    # Resize while keeping aspect ratio
                    image.thumbnail((120, 90))
                    
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    self.thumbnail_label.configure(image=ctk_image, text="")
                    self.thumbnail_label.image = ctk_image
                except Exception as e:
                    self.thumbnail_label.configure(image="", text="(Sin miniatura)")
            else:
                self.thumbnail_label.configure(image="", text="(Sin miniatura)")
        else:
            self.video_info = None
            self.download_btn.configure(state="disabled")
            self.thumbnail_label.configure(image="", text="")

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.download_folder.get()

        if not os.path.isdir(folder):
            messagebox.showerror("Error", "La carpeta de destino seleccionada no es válida.")
            return

        if self.is_downloading:
            messagebox.showwarning("Aviso", "Ya hay una descarga en progreso.")
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="Descargando...")
        self.search_btn.configure(state="disabled")
        self.reset_btn.configure(state="disabled")
        self.folder_btn.configure(state="disabled")
        for btn in [self.rb_mp4, self.rb_mp3]:
            btn.configure(state="disabled")

        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando descarga...")

        format_choice = self.format_var.get()
        threading.Thread(target=self._download_process, args=(url, folder, format_choice), daemon=True).start()

    def yt_dlp_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Calculate progress
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes:
                    percent = downloaded_bytes / total_bytes
                    speed = d.get('speed', 0)
                    if speed:
                        speed_mb = speed / 1024 / 1024
                        speed_str = f"{speed_mb:.2f} MB/s"
                    else:
                        speed_str = "Calculando..."

                    eta = d.get('eta', 0)
                    
                    self.progress_bar.set(percent)
                    percent_str = f"{percent*100:.1f}%"
                    self.progress_label.configure(text=f"Descargando... {percent_str} - {speed_str} - ETA: {eta}s")
            except Exception as e:
                pass
        elif d['status'] == 'finished':
            self.progress_label.configure(text="Procesando archivo final (puede tardar unos segundos)...")

    def _download_process(self, url, folder, format_choice):
        # yt-dlp Options
        outtmpl = os.path.join(folder, '%(title)s.%(ext)s')
        
        ydl_opts = {
            'outtmpl': outtmpl,
            'progress_hooks': [self.yt_dlp_hook],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        except Exception:
            pass

        if format_choice == "mp4":
            # Best single file video+audio or fallback
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            # If ffmpeg is not installed, the first option might fail or fallback to 'best'
        elif format_choice == "mp3":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            # Note: For MP3 conversion, FFmpeg is required on the system.
            # If not present, this will raise an error.

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._download_complete, True, "¡Descarga completada con éxito!")
        except Exception as e:
            error_msg = str(e)
            if "ffprobe" in error_msg.lower() or "ffmpeg" in error_msg.lower():
                error_msg = "Error: FFmpeg no está instalado.\nSe requiere FFmpeg para convertir a MP3 o unir HQ Video+Audio."
            self.after(0, self._download_complete, False, error_msg)

    def _download_complete(self, success, message):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="Descargar")
        self.search_btn.configure(state="normal")
        self.reset_btn.configure(state="normal")
        self.folder_btn.configure(state="normal")
        for btn in [self.rb_mp4, self.rb_mp3]:
            btn.configure(state="normal")

        if success:
            self.progress_bar.set(1)
            self.progress_label.configure(text=message)
            messagebox.showinfo("Éxito", message)
            self.reset_ui()
        else:
            self.progress_label.configure(text="Error en la descarga.")
            messagebox.showerror("Error", f"Ocurrió un error en la descarga:\n{message}")

    def reset_ui(self):
        if self.is_downloading:
            return
        self.url_entry.delete(0, 'end')
        self.video_info = None
        self.video_title_label.configure(text="Título: (Esperando búsqueda...)")
        self.thumbnail_label.configure(image="", text="")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Esperando...")
        self.download_btn.configure(state="disabled")
        self.format_var.set("mp4")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
