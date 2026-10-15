# 📑 PDF Toolkit

A Streamlit-based web application for managing PDF documents. It provides tools to organize, compress, convert, edit, extract text from, and secure PDFs through a simple interface.

## Features

### 📘 Organize PDFs
- Merge multiple PDFs and arrange their order.
- Extract selected pages or save each page as a separate PDF.
- Reorder pages or remove unwanted pages.
- Rotate all pages or selected pages.

### ⚡ Optimize PDFs
- Compress a PDF using different quality presets.
- Batch-compress multiple PDFs.
- Compare uploaded PDF file sizes.

### 🖼️ Convert Files
- Convert images (PNG, JPG/JPEG, WebP, BMP) into a PDF.
- Convert PDF pages into PNG images at selectable resolutions.
- Convert Word documents to PDF.
- Convert PDFs to Word documents.

### 📝 Edit and Read
- Add page numbers.
- Add a text watermark with adjustable opacity.
- Extract selectable text from PDFs and download it as a text file.
- Edit PDF title, author, subject, and keywords metadata.

### 🛡️ Security
- Password-protect PDFs.
- Unlock PDFs when you know the password and are authorized to access the document.

## Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux
- Ghostscript for PDF compression
- Microsoft Word is recommended/required by `docx2pdf` for Word-to-PDF conversion on supported desktop systems

## Installation

1. Clone or download this project and open a terminal in the project folder.
2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate it.

   **Windows PowerShell:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   **Windows Command Prompt:**
   ```bat
   .venv\Scripts\activate.bat
   ```

   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

If you do not have a `requirements.txt` file yet, install the core and optional packages with:

```bash
pip install streamlit pypdf streamlit-sortables Pillow pymupdf python-docx docx2pdf pdf2docx reportlab
```

Some conversion features need optional packages. If a package is missing, install the package named in the app's warning message.

## Run the Application

Start the app from the project folder:

```bash
streamlit run app.py
```

Then open the local URL printed in the terminal, usually:

```text
http://localhost:8501
```

### Windows `run.bat`

You can create a `run.bat` file in the project root:

```bat
@echo off
.venv\Scripts\streamlit.exe run app.py
pause
```

Double-click `run.bat` to launch the app.

## PDF Compression Setup

PDF compression uses Ghostscript. Install Ghostscript and ensure its command-line executable (`gswin64c` on most 64-bit Windows installations, or `gs` on many Unix-like systems) is available on your system `PATH`. Restart the terminal after changing `PATH`.

Available compression presets:
- **High quality (larger file)** — `/printer`
- **Recommended (balanced)** — `/ebook`
- **Smallest file (lower quality)** — `/screen`

Compression may not reduce every file's size; keep the original if the compressed output is larger or quality is insufficient.

## Privacy

The app is designed for local processing when run on your own computer. Uploaded documents are handled by the running Streamlit app; avoid exposing the app to untrusted networks when working with sensitive files.

## Notes and Limitations

- Text extraction works on selectable PDF text. Scanned PDFs may require OCR, which is not built into this app.
- PDF-to-Word conversion may not preserve the original layout perfectly.
- Word-to-PDF conversion depends on `docx2pdf` and a supported Microsoft Word installation.
- PDF compression requires Ghostscript to be installed separately.
- Only unlock PDFs you own or are authorized to access.

## Project Structure

```text
project/
├── app.py
├── requirements.txt
├── run.bat                 # optional Windows launcher
└── .venv/                  # local virtual environment; do not commit
```

## License

Add your preferred license here before distributing the project.
