import json
import base64
import os
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import filedialog, messagebox

def extract_images_from_har(har_file_path, output_folder="extracted_stickers"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"[+] Cartella creata: {output_folder}")

    try:
        with open(har_file_path, "r", encoding="utf-8") as f:
            har_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile leggere il file HAR:\n{e}")
        return 0

    entries = har_data.get("log", {}).get("entries", [])
    print(f"[i] Analisi di {len(entries)} richieste HTTP...")

    extracted_count = 0

    for i, entry in enumerate(entries):
        req_url = entry.get("request", {}).get("url", "")
        response = entry.get("response", {})
        content = response.get("content", {})

        mime_type = content.get("mimeType", "").lower()
        text_data = content.get("text", "")
        encoding = content.get("encoding", "")

        is_image_mime = "image" in mime_type
        is_image_url = any(ext in req_url.lower() for ext in [".webp", ".png", ".jpg", ".jpeg", ".avif", "tplv-"])

        if is_image_mime or is_image_url:
            ext = "webp"
            if "png" in mime_type or ".png" in req_url.lower():
                ext = "png"
            elif "jpg" in mime_type or "jpeg" in mime_type or ".jpg" in req_url.lower():
                ext = "jpg"
            elif "avif" in mime_type or ".avif" in req_url.lower():
                ext = "avif"
            elif "webp" in mime_type or ".webp" in req_url.lower():
                ext = "webp"

            filename = f"sticker_{extracted_count + 1:03d}.{ext}"
            filepath = os.path.join(output_folder, filename)

            saved = False

            if text_data:
                try:
                    if encoding == "base64":
                        img_data = base64.b64decode(text_data)
                        with open(filepath, "wb") as img_file:
                            img_file.write(img_data)
                        saved = True
                    elif text_data.startswith("data:image"):
                        header, encoded = text_data.split(",", 1)
                        img_data = base64.b64decode(encoded)
                        with open(filepath, "wb") as img_file:
                            img_file.write(img_data)
                        saved = True
                except Exception:
                    pass

            if not saved and req_url.startswith("http"):
                try:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    req = urllib.request.Request(req_url, headers=headers)
                    with urllib.request.urlopen(req) as response_stream, open(filepath, 'wb') as out_file:
                        out_file.write(response_stream.read())
                    saved = True
                except Exception:
                    pass

            if saved:
                print(f"[✓] Salvato: {filename}")
                extracted_count += 1

    return extracted_count

def main():
    # Nasconde la finestra principale di Tkinter
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo("Seleziona HAR", "Seleziona il file .har esportato da TikTok.")

    # Apre la finestra di dialogo per la scelta del file
    har_path = filedialog.askopenfilename(
        title="Seleziona il file HAR di TikTok",
        filetypes=[("File HAR", "*.har"), ("Tutti i file", "*.*")]
    )

    if not har_path:
        print("[-] Operazione annullata.")
        return

    print(f"[i] File selezionato: {har_path}")
    count = extract_images_from_har(har_path)

    if count > 0:
        messagebox.showinfo("Successo", f"Estrazione completata!\n\nEstratte {count} immagini.\nCartella: 'extracted_stickers'")
    else:
        messagebox.showwarning("Attenzione", "Nessuna immagine trovata nel file HAR selezionato.")

if __name__ == "__main__":
    main()