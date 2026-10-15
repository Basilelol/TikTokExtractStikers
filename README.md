# TikTok to WhatsApp Sticker Exporter 🚀

A simple tool and step-by-step guide to extracting your favorite stickers from TikTok and importing them into WhatsApp using a browser network log (`.har` file) and a Python script with a built-in graphical interface.

Since TikTok loads messages, images, and chat content incrementally through *lazy loading*, this guide explains how to load the relevant chat history before attempting to export the available images.

## 📑 Table of Contents

- [Prerequisites](#-1-prerequisites)
- [Step 1: Load Stickers on TikTok Web](#-2-step-1-load-stickers-on-tiktok-web)
- [Step 2: Export the HAR File](#-3-step-2-export-the-har-file)
- [Step 3: Extract Images Using Python](#-4-step-3-extract-images-using-python)
- [Step 4: Transfer Stickers to Your Smartphone and Import Them into WhatsApp](#-5-step-4-transfer-stickers-to-your-smartphone-and-import-them-into-whatsapp)
- [Troubleshooting](#-6-troubleshooting)
- [Privacy and Security](#-7-privacy-and-security)
- [License](#-8-license)

---

## 🛠️ 1. Prerequisites

Before getting started, make sure you have:

- A computer with **Python 3.x** installed.
- A desktop browser, such as Google Chrome, Microsoft Edge, or Brave.
- A TikTok account with access to the messages and stickers you want to retrieve.
- A smartphone with WhatsApp installed.
- Optionally, a cloud storage service such as Google Drive or OneDrive to transfer the images.

The script uses only Python's standard library, including `json`, `base64`, `os`, `urllib`, and `tkinter`. No third-party Python packages are required.

> **Note:** Successful extraction depends on which data is available in the browser and how TikTok loads and delivers sticker images. There is no guarantee that every sticker will be recovered from the HAR file.

---

## 🌐 2. Step 1: Load Stickers on TikTok Web

TikTok does not necessarily load an entire chat history at once. To reduce resource usage, it may load messages as they become visible.

To improve your chances of retrieving the stickers you want:

1. Open [TikTok Web](https://www.tiktok.com/) in your desktop browser.
2. Sign in to your account.
3. Open the **Messages** section.
4. Select the conversation containing the stickers you want to retrieve.
5. Slowly scroll upward through the chat history until you reach the period you are interested in.
6. Wait for older messages to load before continuing to scroll.
7. Repeat until you reach the beginning of the relevant period.

### 💡 The Lazy-Loading Trick

Simply opening a chat is not enough. You need to give the browser an opportunity to load the messages and their associated resources.

Gradually scrolling through the conversation may cause TikTok to request additional data from its servers. However, this does not guarantee that every image will be stored in the browser or included in the HAR file.

**Tip:** If you only need stickers from a particular period, focus on loading that period instead of unnecessarily loading the entire conversation.

---

## 📡 3. Step 2: Export the HAR File

A `.har` (*HTTP Archive*) file records network requests made by the browser and, when available, some of the corresponding response data. It may contain URLs, headers, metadata, and response bodies.

Follow these steps:

1. Keep the TikTok chat open.
2. Press `F12`, or right-click the page and select **Inspect**.
3. Open the **Network** tab.
4. Make sure network recording is enabled.
5. If available, enable **Preserve log** to retain requests during navigation or page reloads.
6. Scroll slightly through the chat or open a sticker to generate additional network requests.
7. In the Network panel, look for the option to export or save requests as a HAR file. In Chrome and Chromium-based browsers, this may be available through the panel's context menu.
8. Save the file to your computer, for example as `tiktok.har`.

The exported file may contain unrelated requests, such as profile pictures, thumbnails, and other page resources.

> **Important:** HAR files can contain sensitive session information, private URLs, request headers, and conversation data. Do not publish them on GitHub or share them without checking for and removing sensitive information.

---

## 🐍 4. Step 3: Extract Images Using Python

In this step, we will use a Python script with a file-selection dialog to choose the HAR file.

### 4.1 Create the Python File

Create a file named `extract_stickers.py` and paste the following code into it.

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
    """Determine the image extension from its MIME type or URL."""
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
    """Extract available images from HAR response data."""
    os.makedirs(output_folder, exist_ok=True)

    try:
        with open(har_file_path, "r", encoding="utf-8-sig") as file:
            har_data = json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        messagebox.showerror(
            "Error",
            f"Unable to read the HAR file:\n{error}",
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

        # Avoid downloading the same URL more than once.
        if req_url in seen_urls:
            continue

        seen_urls.add(req_url)

        # Ignore unsuccessful HTTP responses.
        if response.get("status", 0) >= 400:
            continue

        extension = get_image_extension(mime_type, req_url)

        filename = (
            f"sticker_{extracted_count + 1:03d}.{extension}"
        )
        filepath = os.path.join(output_folder, filename)

        saved = False

        # First attempt: extract the response body from the HAR file.
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

        # Second attempt: request the public HTTPS URL again.
        # This may fail for expired or authenticated URLs.
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

                # Check that the response resembles an image
                # before saving it.
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
                # Some resources require authentication
                # or are no longer available.
                pass

        if saved:
            extracted_count += 1

        else:
            # Remove empty or incomplete files.
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
        "Select HAR File",
        "Select the .har file exported from your browser.",
    )

    har_path = filedialog.askopenfilename(
        title="Select TikTok HAR File",
        filetypes=[
            ("HAR Files", "*.har"),
            ("All Files", "*.*"),
        ],
    )

    if not har_path:
        root.destroy()
        return

    count = extract_images_from_har(har_path)

    if count > 0:
        messagebox.showinfo(
            "Extraction Complete",
            f"Images extracted: {count}\n\n"
            f"Folder: {os.path.abspath(OUTPUT_FOLDER)}",
        )

    else:
        messagebox.showwarning(
            "No Images Found",
            "No images could be extracted from the selected HAR file.\n\n"
            "Check whether the file contains image responses and try again.",
        )

    root.destroy()


if __name__ == "__main__":
    main()
```

### 4.2 Run the Script

Open a terminal in the folder containing `extract_stickers.py`.

Run:

```bash
python extract_stickers.py
```

On some systems, you may need to use:

```bash
python3 extract_stickers.py
```

On Windows, if the `python` command is unavailable, try:

```powershell
py extract_stickers.py
```

A file-selection dialog will open:

1. Select your `.har` file.
2. Wait for the extraction to finish.
3. Read the message showing how many images were recovered.
4. Open the `extracted_stickers` folder, created in the script's working directory.

The extracted images will be saved with sequential filenames, for example:

```text
extracted_stickers/
├── sticker_001.webp
├── sticker_002.png
├── sticker_003.jpg
└── sticker_004.webp
```

**Important:** This is a general-purpose image extractor, not a TikTok-specific sticker parser. It may also recover profile pictures, thumbnails, and unrelated images. Some HAR responses do not include the binary image data, so the script may be unable to recover those images.

---

## 📱 5. Step 4: Transfer Stickers to Your Smartphone and Import Them into WhatsApp

Once the images have been extracted on your computer, you can transfer them to your phone and turn them into a sticker pack.

### 5.1 Transfer the Images

Choose one of the following methods:

- **Google Drive:** Upload the folder or files and download them to your smartphone.
- **OneDrive:** Sync the folder and download the images to your phone.
- **USB cable:** Copy the images directly to your device's storage.
- **Personal chat:** Send the images to yourself through a messaging service that allows you to keep them as files.

If you are transferring many images, you may find it convenient to compress the folder into a ZIP archive.

### 5.2 Import Stickers into WhatsApp

To create a custom sticker pack:

1. Install a sticker-creation app compatible with WhatsApp, such as [Sticker Maker](https://play.google.com/store/search?q=sticker%20maker&c=apps) on Android, or find an equivalent app in the Apple App Store on iPhone.
2. Open the app and create a new sticker pack.
3. Import the extracted images from the `extracted_stickers` folder.
4. Crop the images or remove their backgrounds if needed.
5. Add the minimum number of stickers required by the app.
6. Use the app's export or **Add to WhatsApp** feature, if available.
7. Open WhatsApp and check that the sticker pack appears in the sticker section.

The exact process may vary depending on the app, WhatsApp version, and operating system.

### 5.3 Tips for Better Results

- Review every image before importing it.
- Remove duplicates, profile pictures, and irrelevant thumbnails.
- Prefer images with transparent backgrounds when available.
- Resize oversized images using a compatible image editor.
- If you want animated stickers, check whether the original file actually contains animation. Saving a static image will not preserve animation.

---

## 🔧 6. Troubleshooting

### The Script Cannot Find Any Images

Possible causes:

- The HAR file contains image URLs but not the response bodies.
- The images were loaded before network recording started.
- The relevant chat history was not fully loaded.
- TikTok uses resources that require authentication or temporary URLs.

**Solution:** Repeat the recording with the chat open, load the relevant period, and check whether the HAR file contains requests with an `image` content type.

### Some Images Will Not Open

The file extension may have been identified incorrectly, or the response may not contain a valid image.

**Solution:** Check the response MIME type and try opening the file with a compatible image viewer.

### The Extracted Images Are Not Stickers

HAR files can include profile pictures, thumbnails, interface elements, and other resources.

**Solution:** Review the extracted files and manually select the images you want. More precise filtering would require a parser tailored to TikTok's specific requests and data formats.

### The Python Command Does Not Work

Check whether Python 3 is installed:

```bash
python --version
```

Alternatively:

```bash
python3 --version
```

On Windows, try:

```powershell
py --version
```

If Python is installed but `tkinter` is unavailable, you may need to install the corresponding component for your operating system.

### Importing into WhatsApp Does Not Work

Check that:

- The sticker-making app supports your operating system.
- The images use a supported format.
- The sticker pack meets the app's requirements.
- WhatsApp is up to date and installed on your device.

---

## 🔐 7. Privacy and Security

HAR files may contain sensitive information, including private URLs, HTTP headers, identifiers, and session data.

To protect your account:

- Do not upload HAR files to public repositories.
- Do not share unreviewed HAR files with other people.
- Never publish cookies, authentication tokens, or authorization headers.
- Keep the files locally and delete them when they are no longer needed.
- Avoid running scripts from untrusted sources without reviewing the code.

Use this tool only for content you are legally entitled to access, and respect TikTok's terms of service, WhatsApp's terms, and the rights of the original content creators.

---

## 📄 8. License

This project can be published on GitHub as a personal or educational tool.

If you want others to reuse, modify, and distribute the code, you can add an open-source license such as the **MIT License**. Create a `LICENSE` file containing the official license text and specify the copyright holder.

If you have not chosen a license yet, do not claim that the project is distributed under the MIT License or any other specific license.

---

## 🚀 Conclusion

This workflow lets you attempt to recover images loaded while using TikTok Web, organize them on your computer, and transfer the images you want to WhatsApp.

The process is straightforward:

1. Load the relevant chat history on TikTok Web.
2. Export the browser's HAR file.
3. Run the Python script to extract available images.
4. Transfer the images to your smartphone.
5. Create a sticker pack compatible with WhatsApp.

**Enjoy your stickers! 🎉**
