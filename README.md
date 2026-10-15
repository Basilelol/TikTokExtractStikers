# TikTok to WhatsApp Sticker Exporter 🚀

Uno strumento semplice e una guida passo-passo per estrarre gli sticker preferiti salvati o inviati su TikTok e importarli su WhatsApp, utilizzando un file di log di rete (`.har`) del browser e uno script Python con interfaccia grafica integrata.

Poiché TikTok carica messaggi, immagini e contenuti delle chat in modo incrementale (*lazy loading*), questa guida spiega come caricare la cronologia desiderata prima di esportare i dati.

## 📑 Indice

- [Prerequisiti](#-1-prerequisiti)
- [Passo 1: Caricare gli sticker su TikTok Web](#-2-passo-1-caricare-gli-sticker-su-tiktok-web)
- [Passo 2: Esportare il file HAR](#-3-passo-2-esportare-il-file-har)
- [Passo 3: Estrarre le immagini con Python](#-4-passo-3-estrarre-le-immagini-con-python)
- [Passo 4: Trasferire gli sticker su smartphone e importarli in WhatsApp](#-5-passo-4-trasferire-gli-sticker-su-smartphone-e-importarli-in-whatsapp)
- [Risoluzione dei problemi](#-6-risoluzione-dei-problemi)
- [Privacy e sicurezza](#-7-privacy-e-sicurezza)
- [Licenza](#-8-licenza)

---

## 🛠️ 1. Prerequisiti

Prima di iniziare, assicurati di avere a disposizione:

- Un computer con **Python 3.x** installato.
- Un browser desktop, ad esempio Google Chrome, Microsoft Edge o Brave.
- Un account TikTok con accesso ai messaggi e agli sticker che desideri recuperare.
- Uno smartphone con WhatsApp installato.
- Facoltativamente, un servizio cloud come Google Drive o OneDrive per trasferire le immagini.

Lo script utilizza esclusivamente moduli della libreria standard di Python, tra cui `json`, `base64`, `os`, `urllib` e `tkinter`. Non è necessario installare librerie esterne.

> **Nota:** il recupero dipende dai dati effettivamente disponibili nel browser e dalle modalità con cui TikTok carica e distribuisce gli sticker. Non è garantito che ogni sticker venga recuperato dal file HAR.

---

## 🌐 2. Passo 1: Caricare gli sticker su TikTok Web

TikTok non carica necessariamente tutta la cronologia di una chat in una sola volta. Per ridurre il consumo di risorse, può caricare i messaggi man mano che vengono visualizzati.

Per aumentare le possibilità di recuperare gli sticker desiderati:

1. Apri [TikTok Web](https://www.tiktok.com/) dal browser del computer.
2. Accedi al tuo account.
3. Entra nella sezione **Messaggi**.
4. Apri la conversazione che contiene gli sticker da recuperare.
5. Scorri lentamente verso l'alto nella cronologia della chat, fino a raggiungere il periodo che ti interessa.
6. Attendi il caricamento dei messaggi prima di continuare a scorrere.
7. Ripeti l'operazione fino a raggiungere l'inizio del periodo desiderato.

### 💡 Il trucco del caricamento incrementale

Non basta aprire la chat: è necessario permettere al browser di caricare i messaggi e le risorse associate.

Scorrere gradualmente la cronologia può indurre TikTok a richiedere ulteriori dati al server. Tuttavia, non garantisce che tutte le immagini siano memorizzate nel browser o incluse nel successivo file HAR.

**Consiglio:** se devi recuperare sticker di un periodo specifico, concentrati su quel periodo invece di caricare inutilmente tutta la cronologia.

---

## 📡 3. Passo 2: Esportare il file HAR

Il file `.har` (*HTTP Archive*) registra le richieste di rete effettuate dal browser e, quando disponibili, alcuni dati delle risposte. Può contenere URL, intestazioni, metadati e corpi delle risposte.

Segui questi passaggi:

1. Mantieni aperta la chat di TikTok.
2. Premi `F12` oppure fai clic con il tasto destro sulla pagina e seleziona **Ispeziona**.
3. Apri la scheda **Network** (Rete).
4. Verifica che la registrazione delle richieste sia attiva.
5. Se disponibile, abilita **Preserve log** per conservare le richieste durante eventuali navigazioni o aggiornamenti della pagina.
6. Esegui un piccolo movimento di scroll nella chat oppure apri uno sticker, così da generare nuove richieste.
7. Nel pannello Network, cerca l'opzione per esportare o salvare le richieste in formato HAR. In Chrome e nei browser basati su Chromium, può essere disponibile tramite il menu contestuale del pannello.
8. Salva il file sul computer, ad esempio con il nome `tiktok.har`.

Il file esportato potrebbe includere anche richieste estranee agli sticker, come avatar, miniature e altre risorse della pagina.

> **Importante:** il formato HAR può contenere informazioni sensibili della sessione, URL privati e dati delle conversazioni. Non pubblicarlo su GitHub e non condividerlo senza aver verificato e rimosso le informazioni riservate.

---

## 🐍 4. Passo 3: Estrarre le immagini con Python

In questa fase utilizzeremo uno script Python con una finestra di dialogo per selezionare il file HAR.

### 4.1 Creare il file Python

Crea un file chiamato `extract_stickers.py` e incolla il codice seguente.

```python
import json
import base64
import os
import re
import urllib.request
import tkinter as tk

from urllib.parse import urlparse
from tkinter import filedialog, messagebox


OUTPUT_FOLDER = "extracted_stickers"


def get_image_extension(mime_type, url):
    """Determina l'estensione dell'immagine dal MIME type o dall'URL."""
    mime_type = mime_type.lower().split(";")[0].strip()
    path = urlparse(url).path.lower()

    extensions = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "image/avif": "avif",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/x-icon": "ico",
    }

    if mime_type in extensions:
        return extensions[mime_type]

    match = re.search(
        r"\.(png|jpe?g|webp|avif|gif|bmp|ico)$",
        path,
    )

    if match:
        ext = match.group(1)
        return "jpg" if ext == "jpeg" else ext

    return "img"


def extract_images_from_har(
    har_file_path,
    output_folder=OUTPUT_FOLDER,
):
    """Estrae le immagini disponibili nelle risposte del file HAR."""
    os.makedirs(output_folder, exist_ok=True)

    try:
        with open(har_file_path, "r", encoding="utf-8-sig") as file:
            har_data = json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        messagebox.showerror(
            "Errore",
            f"Impossibile leggere il file HAR:\n{error}",
        )
        return 0

    entries = har_data.get("log", {}).get("entries", [])
    extracted_count = 0
    seen_urls = set()

    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        content = response.get("content", {})

        req_url = request.get("url", "")
        mime_type = content.get("mimeType", "").lower()
        text_data = content.get("text", "")
        encoding = content.get("encoding", "")

        if not req_url:
            continue

        is_image = (
            mime_type.startswith("image/")
            or bool(
                re.search(
                    r"\.(png|jpe?g|webp|avif|gif|bmp|ico)(?:$|[?#])",
                    req_url,
                    re.IGNORECASE,
                )
            )
        )

        if not is_image:
            continue

        # Evita di salvare più volte la stessa URL.
        if req_url in seen_urls:
            continue

        seen_urls.add(req_url)

        # Ignora le risposte HTTP non riuscite.
        if response.get("status", 0) >= 400:
            continue

        extension = get_image_extension(mime_type, req_url)

        filename = (
            f"sticker_{extracted_count + 1:03d}.{extension}"
        )
        filepath = os.path.join(output_folder, filename)

        saved = False

        # Primo tentativo: recupera il corpo della risposta dal HAR.
        if text_data:
            try:
                if encoding == "base64":
                    image_data = base64.b64decode(
                        text_data,
                        validate=True,
                    )

                    with open(filepath, "wb") as image_file:
                        image_file.write(image_data)

                    saved = True

                elif text_data.startswith("data:image"):
                    _, encoded = text_data.split(",", 1)
                    image_data = base64.b64decode(
                        encoded,
                        validate=True,
                    )

                    with open(filepath, "wb") as image_file:
                        image_file.write(image_data)

                    saved = True

            except (ValueError, OSError):
                saved = False

        # Secondo tentativo: richiede nuovamente l'URL pubblico.
        # Potrebbe non funzionare con URL scaduti o autenticati.
        if not saved and req_url.startswith("https://"):
            try:
                request_obj = urllib.request.Request(
                    req_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Windows NT 10.0; Win64; x64)"
                        )
                    },
                )

                with urllib.request.urlopen(
                    request_obj,
                    timeout=10,
                ) as response_stream:
                    image_data = response_stream.read()

                # Controlla che la risposta sia effettivamente
                # un'immagine prima di salvarla.
                if image_data.startswith(
                    (
                        b"\x89PNG\r\n\x1a\n",
                        b"\xff\xd8\xff",
                        b"GIF87a",
                        b"GIF89a",
                        b"RIFF",
                        b"BM",
                    )
                ):
                    with open(filepath, "wb") as image_file:
                        image_file.write(image_data)

                    saved = True

            except Exception:
                # Alcune risorse richiedono autenticazione
                # o non sono più disponibili.
                pass

        if saved:
            extracted_count += 1

        else:
            # Non lasciare file vuoti o incompleti.
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except OSError:
                pass

    return extracted_count


def main():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo(
        "Seleziona HAR",
        "Seleziona il file .har esportato dal browser.",
    )

    har_path = filedialog.askopenfilename(
        title="Seleziona il file HAR di TikTok",
        filetypes=[
            ("File HAR", "*.har"),
            ("Tutti i file", "*.*"),
        ],
    )

    if not har_path:
        root.destroy()
        return

    count = extract_images_from_har(har_path)

    if count > 0:
        messagebox.showinfo(
            "Estrazione completata",
            f"Immagini estratte: {count}\n\n"
            f"Cartella: {os.path.abspath(OUTPUT_FOLDER)}",
        )

    else:
        messagebox.showwarning(
            "Nessuna immagine trovata",
            "Non è stato possibile estrarre immagini dal file HAR.\n\n"
            "Verifica che il file contenga le risposte delle "
            "immagini e riprova.",
        )

    root.destroy()


if __name__ == "__main__":
    main()
```

### 4.2 Eseguire lo script

Apri il terminale nella cartella contenente `extract_stickers.py`.

Esegui:

```bash
python extract_stickers.py
```

Su alcuni sistemi potrebbe essere necessario utilizzare:

```bash
python3 extract_stickers.py
```

Su Windows, se il comando `python` non è disponibile, puoi provare:

```powershell
py extract_stickers.py
```

Si aprirà una finestra di dialogo:

1. Seleziona il file `.har`.
2. Attendi il completamento dell'estrazione.
3. Leggi il messaggio che indica il numero di immagini recuperate.
4. Apri la cartella `extracted_stickers`, creata nella cartella di lavoro dello script.

Le immagini estratte saranno organizzate con nomi progressivi, ad esempio:

```text
extracted_stickers/
├── sticker_001.webp
├── sticker_002.png
├── sticker_003.jpg
└── sticker_004.webp
```

**Attenzione:** il codice è un estrattore generico di immagini, non un parser specifico degli sticker TikTok. Può recuperare anche avatar, miniature e immagini non pertinenti. Inoltre, alcune risposte HAR non includono i dati binari delle immagini: in quei casi, lo script potrebbe non riuscire a recuperarle.

---

## 📱 5. Passo 4: Trasferire gli sticker su smartphone e importarli in WhatsApp

Dopo aver estratto le immagini sul computer, puoi trasferirle sul telefono e convertirle in un pacchetto di sticker.

### 5.1 Trasferire le immagini

Scegli uno dei seguenti metodi:

- **Google Drive:** carica la cartella o i file e scaricali sullo smartphone.
- **OneDrive:** sincronizza la cartella e scarica le immagini sul telefono.
- **Cavo USB:** copia le immagini direttamente nella memoria del dispositivo.
- **Chat personale:** inviati le immagini tramite un servizio di messaggistica che consenta di conservarle come file.

Se trasferisci molte immagini, può essere utile comprimere la cartella in un archivio ZIP.

### 5.2 Importare gli sticker su WhatsApp

Per creare un pacchetto personalizzato:

1. Installa un'applicazione per creare sticker compatibile con WhatsApp, ad esempio [Sticker Maker](https://play.google.com/store/search?q=sticker%20maker&c=apps) su Android, oppure cerca un'app equivalente nell'App Store su iPhone.
2. Apri l'applicazione e crea un nuovo pacchetto.
3. Importa le immagini estratte dalla cartella `extracted_stickers`.
4. Se necessario, ritaglia le immagini e rimuovi lo sfondo.
5. Aggiungi il numero minimo di sticker richiesto dall'applicazione.
6. Usa la funzione di esportazione o aggiunta a WhatsApp, se disponibile.
7. Apri WhatsApp e verifica che il pacchetto sia presente nella sezione degli sticker.

Le procedure possono variare a seconda dell'applicazione, della versione di WhatsApp e del sistema operativo.

### 5.3 Consigli per ottenere un risultato migliore

- Controlla ogni immagine prima di importarla.
- Elimina duplicati, avatar e miniature non pertinenti.
- Preferisci immagini con sfondo trasparente quando disponibili.
- Se un'immagine è troppo grande, ridimensionala con un editor compatibile.
- Se lo sticker contiene animazioni, verifica che il file originale sia effettivamente animato: il semplice salvataggio di un'immagine statica non conserva l'animazione.

---

## 🔧 6. Risoluzione dei problemi

### Lo script non trova immagini

Possibili cause:

- Il file HAR contiene solo gli URL delle immagini, senza i corpi delle risposte.
- Le immagini sono state caricate prima dell'inizio della registrazione.
- La cronologia della chat non è stata caricata completamente.
- TikTok utilizza risorse che richiedono autenticazione o URL temporanei.

**Soluzione:** ripeti la registrazione con la chat aperta, carica il periodo desiderato e verifica che nel file HAR siano presenti richieste di tipo `image`.

### Alcune immagini non si aprono

Il tipo di file potrebbe essere stato identificato in modo errato oppure il contenuto potrebbe non essere un'immagine valida.

**Soluzione:** verifica il MIME type della risposta e prova ad aprire il file con un visualizzatore compatibile.

### Le immagini estratte non sono sticker

Il file HAR registra anche immagini di profilo, miniature, elementi dell'interfaccia e altre risorse.

**Soluzione:** controlla le immagini e seleziona manualmente quelle desiderate. Per un filtraggio più preciso, servirebbe un parser specifico delle richieste e dei formati utilizzati da TikTok.

### Il comando Python non funziona

Verifica che Python 3 sia installato:

```bash
python --version
```

Oppure:

```bash
python3 --version
```

Su Windows puoi provare:

```powershell
py --version
```

Se Python è installato ma `tkinter` non è disponibile, potrebbe essere necessario installare il componente relativo al tuo sistema operativo.

### L'importazione in WhatsApp non funziona

Verifica che:

- L'app per creare sticker supporti il tuo sistema operativo.
- Le immagini siano in un formato supportato.
- Il pacchetto rispetti i requisiti dell'app.
- WhatsApp sia aggiornato e installato sul dispositivo.

---

## 🔐 7. Privacy e sicurezza

Il file HAR può contenere informazioni sensibili, tra cui URL privati, intestazioni HTTP, identificativi e dati di sessione.

Per proteggere il tuo account:

- Non caricare file HAR su repository pubblici.
- Non condividere file HAR non verificati con altre persone.
- Non pubblicare cookie, token o intestazioni di autenticazione.
- Conserva i file localmente e cancellali quando non sono più necessari.
- Evita di eseguire script ricevuti da fonti non attendibili senza averne verificato il codice.

Utilizza questo strumento esclusivamente per contenuti a cui hai legittimamente accesso e rispetta i termini di servizio di TikTok, le condizioni di WhatsApp e i diritti dei rispettivi autori.

---

## 📄 8. Licenza

Questo progetto può essere pubblicato su GitHub come strumento personale e didattico.

Se desideri permettere ad altre persone di riutilizzare, modificare e distribuire il codice, puoi aggiungere una licenza open source, ad esempio la **MIT License**. In tal caso, inserisci un file `LICENSE` con il testo ufficiale della licenza e specifica il titolare del copyright.

Se non hai ancora scelto una licenza, evita di dichiarare che il progetto è distribuito sotto MIT o un'altra licenza specifica.

---

## 🚀 Conclusione

Con questa procedura puoi tentare di recuperare le immagini caricate durante l'utilizzo di TikTok Web, organizzarle sul computer e trasferire quelle desiderate su WhatsApp.

Il flusso di lavoro è semplice:

1. Carica la cronologia desiderata su TikTok Web.
2. Esporta il file HAR dal browser.
3. Esegui lo script Python per estrarre le immagini disponibili.
4. Trasferisci le immagini sullo smartphone.
5. Crea un pacchetto di sticker compatibile con WhatsApp.

**Buon divertimento con i tuoi sticker! 🎉**
