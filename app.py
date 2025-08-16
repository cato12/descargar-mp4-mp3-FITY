from flask import Flask, render_template, request, send_file, redirect, url_for, flash, Response
import os, uuid, yt_dlp, time, json

app = Flask(__name__)
app.secret_key = "descargador123"

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

progreso_data = {}

def progreso_terminal(d):
    if d['status'] == 'downloading':
        porcentaje = d.get('_percent_str', '').strip()
        descargado = d.get('_downloaded_bytes_str', '').strip()
        total = d.get('_total_bytes_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        progreso_data['porcentaje'] = porcentaje
        progreso_data['descargado'] = descargado
        progreso_data['total'] = total
        progreso_data['eta'] = eta
    elif d['status'] == 'finished':
        progreso_data['porcentaje'] = '100%'
        progreso_data['descargado'] = progreso_data.get('total', '')
        progreso_data['eta'] = '0'

def descargar_video(url, formato):
    filename = str(uuid.uuid4())
    plantilla = os.path.join(DOWNLOAD_FOLDER, filename + ".%(ext)s")
    ydl_opts = {
        'outtmpl': plantilla,
        'noplaylist': True,
        'progress_hooks': [progreso_terminal],  # <-- Agrega el hook
    }
    if formato == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif formato == "mp4":
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'postprocessor_args': [
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental'
            ],
        })
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
            flash("Debes ingresar una URL y elegir el formato.", "error")
            return redirect(url_for("index"))
        try:
            file_path, title = descargar_video(url, formato)
            flash(f"¡Descarga completada! Se descargó '{title}' como {formato}.", "success")
            return send_file(file_path, as_attachment=True, download_name=f"{title}.{formato}")
        except Exception as e:
            flash(f"Error: {e}", "error")
            return redirect(url_for("index"))
    return render_template("index.html")

@app.route('/progreso')
def progreso():
    def event_stream():
        while True:
            time.sleep(1)
            yield f"data: {json.dumps(progreso_data if progreso_data else {})}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)