from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp
import os
import uuid

app = Flask(__name__)
app.secret_key = "descargador123"

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def descargar_video(url, formato):
    filename = str(uuid.uuid4())
    plantilla = os.path.join(DOWNLOAD_FOLDER, filename + ".%(ext)s")
    if formato == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': plantilla,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif formato == "mp4":
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': plantilla,
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental'
            ],
        }
    else:
        return None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = "mp3" if formato == "mp3" else "mp4"
        file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.{ext}")
        return file_path, info.get('title', 'descarga')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        formato = request.form.get("formato")
        if not url or not formato:
            flash("Debes ingresar una URL y elegir el formato.")
            return redirect(url_for("index"))
        try:
            file_path, title = descargar_video(url, formato)
            return send_file(file_path, as_attachment=True, download_name=f"{title}.{formato}")
        except Exception as e:
            flash(f"Error: {e}")
            return redirect(url_for("index"))
    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)