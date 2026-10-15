import os
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st
from pypdf import PdfReader, PdfWriter
from streamlit_sortables import sort_items

# Optional libraries: the app remains usable if these are not installed.
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

st.set_page_config(
    page_title="PDF Toolkit",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- STYLE --------------------
st.markdown("""
<style>
.stApp { background:#080808; color:#f5f5f5; }
[data-testid="stSidebar"] { background:#111111; border-right:1px solid #292929; }
.block-container { max-width:1100px; padding-top:2rem; padding-bottom:3rem; }
h1,h2,h3,p,label { color:#f5f5f5; }
.muted { color:#a3a3a3; }
div[data-testid="stFileUploader"] { background:#111; border:1px solid #303030; border-radius:12px; padding:12px; }
div[data-testid="stMetric"] { background:#141414; border:1px solid #303030; padding:16px; border-radius:12px; }
.stButton > button, .stDownloadButton > button { border-radius:9px; min-height:42px; }
.tool-card { background:#0c0c0c; border:1px solid #303030; border-radius:16px; padding:20px; margin:10px 0; }
.tool-row { display:flex; align-items:center; gap:15px; }
.tool-icon { width:54px;height:54px;border-radius:12px;display:flex;justify-content:center;align-items:center;font-size:27px;flex-shrink:0; }
.tool-title { color:#f5f5f5;font-size:19px;font-weight:650;margin-bottom:5px; }
.tool-desc { color:#bdbdbd;font-size:14px; }
</style>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
def get_bytes(uploaded):
    return uploaded.getvalue()

def pdf_reader(data):
    return PdfReader(io.BytesIO(data), strict=False)

def make_pdf_bytes(writer):
    out = io.BytesIO()
    writer.write(out)
    writer.close()
    return out.getvalue()

def format_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024**2):.2f} MB"

def gs_executable():
    # First, check whether Ghostscript is available on PATH.
    candidates = [
        shutil.which("gswin64c"),
        shutil.which("gswin32c"),
        shutil.which("gs"),
        shutil.which("ghostscript"),
        r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe",
    ]

    for path in candidates:
        if path and os.path.isfile(path):
            return path

    return None

def compress_pdf(data, preset):
    gs = gs_executable()
    if not gs:
        raise RuntimeError(
            "Ghostscript was not found. Install Ghostscript and add its command-line "
            "executable to PATH, then restart the terminal."
        )
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "input.pdf")
        dst = os.path.join(tmp, "compressed.pdf")
        with open(src, "wb") as f:
            f.write(data)
        cmd = [
            gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={preset}", "-dNOPAUSE", "-dBATCH", "-dQUIET",
            f"-sOutputFile={dst}", src
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if result.returncode != 0 or not os.path.exists(dst):
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError("Ghostscript could not compress this PDF. " + details[-700:])
        with open(dst, "rb") as f:
            return f.read()

def parse_page_ranges(text, total_pages):
    """Parse ranges like 1-3,5,8-10 using 1-based page numbers."""
    pages = []
    if not text.strip():
        raise ValueError("Enter at least one page number or range.")
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bits = part.split("-", 1)
            if not bits[0].strip() or not bits[1].strip():
                raise ValueError(f"Invalid range: {part}")
            start, end = int(bits[0]), int(bits[1])
            if start > end:
                raise ValueError(f"Range start must not exceed end: {part}")
            nums = range(start, end + 1)
        else:
            nums = [int(part)]
        for num in nums:
            if num < 1 or num > total_pages:
                raise ValueError(f"Page {num} is outside 1–{total_pages}.")
            if num not in pages:
                pages.append(num)
    return pages

def add_download(label, data, filename, mime="application/pdf", key=None):
    st.download_button(label, data=data, file_name=filename, mime=mime, key=key)

def show_error_if_missing(package, install_command):
    st.warning(f"This feature needs an optional dependency. Install it with: `{install_command}`")

# -------------------- NAVIGATION --------------------
categories = ["Dashboard", "Organize PDFs", "Optimize PDFs", "Convert Files", "Edit and Read", "Security"]
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def navigate(destination):
    st.session_state.page = destination

with st.sidebar:
    st.markdown("# 📑 PDF Toolkit")
    st.caption("Your document workspace")
    st.divider()
    for item in categories:
        if st.button(
            item, key=f"nav_{item}", use_container_width=True,
            type="primary" if st.session_state.page == item else "secondary"
        ):
            navigate(item)
            st.rerun()
    st.divider()
    st.caption("🔒 Local processing")
    st.caption("Works offline after setup")

page = st.session_state.page

# -------------------- DASHBOARD --------------------
if page == "Dashboard":
    st.title("PDF Toolkit")
    st.markdown('<p class="muted">Everything you need to manage your documents.</p>', unsafe_allow_html=True)
    cards = [
        ("Organize PDFs", "Merge · Split · Reorder · Delete · Rotate", "#DCEAFE", "📘"),
        ("Optimize PDFs", "Compress · Batch compress · Compare file sizes", "#DCFCE7", "⚡"),
        ("Convert Files", "Images to PDF · PDF to images · Word conversion", "#F3E8FF", "🖼️"),
        ("Edit and Read", "Page numbers · Watermarks · Text · Metadata", "#FEF3C7", "📝"),
        ("Security", "Password protection · Authorized decryption", "#FEE2E2", "🛡️"),
    ]
    for title, desc, color, icon in cards:
        st.markdown(
            f'<div class="tool-card"><div class="tool-row">'
            f'<div class="tool-icon" style="background:{color}">{icon}</div>'
            f'<div><div class="tool-title">{title}</div><div class="tool-desc">{desc}</div></div>'
            f'</div></div>', unsafe_allow_html=True
        )
        if st.button(f"Open {title} →", key=f"open_{title}"):
            navigate(title)
            st.rerun()
    st.caption("Tip: use the sidebar to switch between tool categories.")

# -------------------- ORGANIZE --------------------
elif page == "Organize PDFs":
    st.title("📘 Organize PDFs")
    tool = st.radio(
        "Choose a tool",
        ["Merge PDFs", "Split PDF", "Reorder / Delete Pages", "Rotate PDF"],
        horizontal=True,
    )

    if tool == "Merge PDFs":
        files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True, key="merge_files")
        if files:
            labels = [f"{i+1}. {f.name} [{i}]" for i, f in enumerate(files)]
            file_map = dict(zip(labels, files))
            st.caption("Drag the rows to set the merge order.")
            sorted_labels = sort_items(labels, key="merge_sort")
            if st.button("Merge PDFs", type="primary"):
                try:
                    writer = PdfWriter()
                    for label in sorted_labels:
                        writer.append(io.BytesIO(file_map[label].getvalue()))
                    merged = make_pdf_bytes(writer)
                    st.session_state.merge_result = merged
                    st.success(f"Merged {len(files)} PDF files.")
                except Exception as e:
                    st.error(f"Merge failed: {e}")
            if "merge_result" in st.session_state:
                add_download("⬇️ Download Merged PDF", st.session_state.merge_result, "merged_document.pdf", key="merge_download")

    elif tool == "Split PDF":
        uploaded = st.file_uploader("Choose a PDF to split", type=["pdf"], key="split_pdf")
        if uploaded:
            data = get_bytes(uploaded)
            try:
                total = len(pdf_reader(data).pages)
                st.info(f"This PDF contains {total} pages.")
                mode = st.radio("Split method", ["Extract selected pages into one PDF", "Save every page as a separate PDF"], horizontal=False)
                if mode == "Extract selected pages into one PDF":
                    ranges = st.text_input("Pages to extract", placeholder="Example: 1-3,5,8-10")
                    if st.button("Create PDF from selected pages", type="primary"):
                        pages = parse_page_ranges(ranges, total)
                        reader = pdf_reader(data)
                        writer = PdfWriter()
                        for n in pages:
                            writer.add_page(reader.pages[n - 1])
                        st.session_state.split_result = make_pdf_bytes(writer)
                        st.session_state.split_filename = Path(uploaded.name).stem + "_split.pdf"
                else:
                    if st.button("Prepare individual pages", type="primary"):
                        reader = pdf_reader(data)
                        st.session_state.split_pages = []
                        for idx, pg in enumerate(reader.pages, start=1):
                            writer = PdfWriter()
                            writer.add_page(pg)
                            st.session_state.split_pages.append((f"page_{idx}.pdf", make_pdf_bytes(writer)))
                if "split_result" in st.session_state:
                    add_download("Download extracted pages", st.session_state.split_result, st.session_state.split_filename, key="split_download")
                if "split_pages" in st.session_state:
                    st.write("Download each page:")
                    for filename, content in st.session_state.split_pages:
                        add_download(f"⬇️ {filename}", content, filename, key=f"dl_{filename}")
            except Exception as e:
                st.error(f"Could not read/split this PDF: {e}")

    elif tool == "Reorder / Delete Pages":
        uploaded = st.file_uploader("Choose a PDF", type=["pdf"], key="page_edit_pdf")
        if uploaded:
            data = get_bytes(uploaded)
            try:
                reader = pdf_reader(data)
                total = len(reader.pages)
                st.info(f"PDF has {total} pages. Drag the labels to reorder; uncheck pages you want to remove.")
                labels = [f"Page {i+1}" for i in range(total)]
                sorted_labels = sort_items(labels, key="page_order_sort")
                keep = st.multiselect("Pages to keep", sorted_labels, default=sorted_labels)
                if st.button("Save reordered PDF", type="primary"):
                    writer = PdfWriter()
                    for label in sorted_labels:
                        if label in keep:
                            page_num = int(label.split()[1]) - 1
                            writer.add_page(reader.pages[page_num])
                    st.session_state.page_edit_result = make_pdf_bytes(writer)
                if "page_edit_result" in st.session_state:
                    add_download("Download edited PDF", st.session_state.page_edit_result, "reordered_pages.pdf", key="page_edit_download")
            except Exception as e:
                st.error(f"Could not edit pages: {e}")

    elif tool == "Rotate PDF":
        uploaded = st.file_uploader("Choose a PDF", type=["pdf"], key="rotate_pdf")
        if uploaded:
            data = get_bytes(uploaded)
            try:
                reader = pdf_reader(data)
                total = len(reader.pages)
                page_choice = st.radio("Apply rotation to", ["All pages", "Selected pages"], horizontal=True)
                angle = st.selectbox("Rotation", [90, 180, 270], format_func=lambda a: f"{a}° clockwise")
                selected = list(range(1, total + 1))
                if page_choice == "Selected pages":
                    page_text = st.text_input("Page numbers/ranges", placeholder="Example: 1-3,5")
                    if page_text:
                        selected = parse_page_ranges(page_text, total)
                    else:
                        selected = []
                if st.button("Rotate and save PDF", type="primary"):
                    writer = PdfWriter()
                    for i, pg in enumerate(reader.pages, start=1):
                        if i in selected:
                            pg.rotate(angle)
                        writer.add_page(pg)
                    st.session_state.rotate_result = make_pdf_bytes(writer)
                if "rotate_result" in st.session_state:
                    add_download("Download rotated PDF", st.session_state.rotate_result, "rotated.pdf", key="rotate_download")
            except Exception as e:
                st.error(f"Rotation failed: {e}")

# -------------------- OPTIMIZE --------------------
elif page == "Optimize PDFs":
    st.title("⚡ Optimize PDFs")
    tool = st.radio("Choose a tool", ["Compress PDF", "Batch Compress", "Compare File Sizes"], horizontal=True)
    presets = {
        "High quality (larger file)": "/printer",
        "Recommended (balanced)": "/ebook",
        "Smallest file (lower quality)": "/screen",
    }

    if tool == "Compress PDF":
        pdf = st.file_uploader("Upload PDF to compress", type=["pdf"], key="compress_file")
        quality = st.selectbox("Compression quality", list(presets), index=1)
        if pdf:
            original = get_bytes(pdf)
            st.write(f"Original size: **{format_size(len(original))}**")
            if st.button("Compress PDF", type="primary"):
                try:
                    compressed = compress_pdf(original, presets[quality])
                    st.session_state.compress_result = compressed
                    st.session_state.compress_original_size = len(original)
                    st.session_state.compress_filename = Path(pdf.name).stem + "_compressed.pdf"
                    st.success("Compression finished.")
                except Exception as e:
                    st.error(str(e))
        if "compress_result" in st.session_state:
            compressed = st.session_state.compress_result
            old = st.session_state.compress_original_size
            new = len(compressed)
            c1, c2, c3 = st.columns(3)
            c1.metric("Original", format_size(old))
            c2.metric("Compressed", format_size(new))
            c3.metric("Size change", f"{(old-new)/old*100:.1f}%" if old else "N/A")
            if new >= old:
                st.warning("The output is not smaller. Consider keeping the original.")
            add_download("⬇️ Download Compressed PDF", compressed, st.session_state.compress_filename, key="compress_download")

    elif tool == "Batch Compress":
        files = st.file_uploader("Upload multiple PDFs", type=["pdf"], accept_multiple_files=True, key="batch_compress")
        quality = st.selectbox("Compression quality", list(presets), index=1, key="batch_quality")
        if files and st.button("Compress all PDFs", type="primary"):
            results = []
            progress = st.progress(0)
            for i, f in enumerate(files):
                try:
                    results.append((Path(f.name).stem + "_compressed.pdf", compress_pdf(get_bytes(f), presets[quality]), None))
                except Exception as e:
                    results.append((f.name, None, str(e)))
                progress.progress((i + 1) / len(files))
            st.session_state.batch_results = results
        if "batch_results" in st.session_state:
            for name, data, error in st.session_state.batch_results:
                if error:
                    st.error(f"{name}: {error}")
                else:
                    add_download(f"Download {name}", data, name, key=f"batch_{name}")

    elif tool == "Compare File Sizes":
        files = st.file_uploader("Upload PDFs to compare", type=["pdf"], accept_multiple_files=True, key="compare_files")
        if files:
            st.subheader("File sizes")
            for f in files:
                st.write(f"**{f.name}** — {format_size(len(f.getvalue()))}")
            total = sum(len(f.getvalue()) for f in files)
            st.metric("Combined size", format_size(total))

# -------------------- CONVERT --------------------
elif page == "Convert Files":
    st.title("🖼️ Convert Files")
    tool = st.radio("Choose a tool", ["Images to PDF", "PDF to Images", "Word to PDF", "PDF to Word"], horizontal=True)

    if tool == "Images to PDF":
        if Image is None:
            show_error_if_missing("Pillow", "pip install Pillow")
        else:
            imgs = st.file_uploader("Upload images", type=["png", "jpg", "jpeg", "webp", "bmp"], accept_multiple_files=True, key="images_to_pdf")
            if imgs:
                st.caption("Images are added in the order uploaded.")
                if st.button("Convert images to PDF", type="primary"):
                    try:
                        converted = []
                        for img in imgs:
                            im = Image.open(io.BytesIO(img.getvalue()))
                            if im.mode != "RGB":
                                if im.mode in ("RGBA", "LA"):
                                    bg = Image.new("RGB", im.size, "white")
                                    bg.paste(im, mask=im.getchannel("A"))
                                    im = bg
                                else:
                                    im = im.convert("RGB")
                            converted.append(im.copy())
                        output = io.BytesIO()
                        converted[0].save(output, format="PDF", save_all=True, append_images=converted[1:])
                        st.session_state.images_pdf_result = output.getvalue()
                    except Exception as e:
                        st.error(f"Conversion failed: {e}")
            if "images_pdf_result" in st.session_state:
                add_download("Download PDF", st.session_state.images_pdf_result, "images.pdf", key="images_pdf_download")

    elif tool == "PDF to Images":
        if fitz is None:
            show_error_if_missing("PyMuPDF", "pip install pymupdf")
        else:
            pdf = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_to_images")
            scale = st.selectbox("Image resolution", ["Standard (150 DPI)", "High (200 DPI)", "Very high (300 DPI)"], index=0)
            dpi = {"Standard (150 DPI)": 150, "High (200 DPI)": 200, "Very high (300 DPI)": 300}[scale]
            if pdf and st.button("Convert pages to PNG", type="primary"):
                try:
                    doc = fitz.open(stream=pdf.getvalue(), filetype="pdf")
                    results = []
                    zoom = dpi / 72
                    for i, pg in enumerate(doc, start=1):
                        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                        results.append((f"page_{i}.png", pix.tobytes("png")))
                    st.session_state.pdf_images_result = results
                    doc.close()
                except Exception as e:
                    st.error(f"Conversion failed: {e}")
            if "pdf_images_result" in st.session_state:
                st.caption("Download each rendered page as a PNG.")
                for name, content in st.session_state.pdf_images_result:
                    add_download(f"Download {name}", content, name, "image/png", key=f"png_{name}")

    elif tool == "Word to PDF":
        st.write("Uses Microsoft Word via docx2pdf. Best supported on Windows/macOS with Word installed.")
        show_error_if_missing("docx2pdf", "pip install docx2pdf")
        docx = st.file_uploader("Upload DOCX", type=["docx"], key="word_to_pdf")
        if docx and st.button("Convert Word to PDF", type="primary"):
            try:
                from docx2pdf import convert
                with tempfile.TemporaryDirectory() as tmp:
                    src = os.path.join(tmp, "input.docx")
                    dst = os.path.join(tmp, "input.pdf")
                    with open(src, "wb") as f:
                        f.write(docx.getvalue())
                    convert(src, dst)
                    with open(dst, "rb") as f:
                        st.session_state.word_pdf_result = f.read()
            except Exception as e:
                st.error(f"Conversion failed: {e}. Ensure Microsoft Word is installed.")

        if "word_pdf_result" in st.session_state:
            add_download("Download PDF", st.session_state.word_pdf_result, "converted.pdf", key="word_pdf_download")

    elif tool == "PDF to Word":
        st.write("Uses pdf2docx. Layout fidelity varies, especially for scanned PDFs.")
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_to_word")
        if pdf and st.button("Convert PDF to Word", type="primary"):
            try:
                from pdf2docx import Converter
                with tempfile.TemporaryDirectory() as tmp:
                    src = os.path.join(tmp, "input.pdf")
                    dst = os.path.join(tmp, "output.docx")
                    with open(src, "wb") as f:
                        f.write(pdf.getvalue())
                    cv = Converter(src)
                    cv.convert(dst)
                    cv.close()
                    with open(dst, "rb") as f:
                        st.session_state.pdf_word_result = f.read()
            except ImportError:
                st.error("Install the optional dependency with: pip install pdf2docx")
            except Exception as e:
                st.error(f"Conversion failed: {e}")
        if "pdf_word_result" in st.session_state:
            add_download("Download Word document", st.session_state.pdf_word_result, "converted.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="pdf_word_download")

# -------------------- EDIT AND READ --------------------
elif page == "Edit and Read":
    st.title("📝 Edit and Read")
    tool = st.radio("Choose a tool", ["Add Page Numbers", "Add Watermark", "Extract Text", "Edit Metadata"], horizontal=True)

    if tool == "Add Page Numbers":
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="number_pdf")
        position = st.selectbox("Position", ["Bottom center", "Bottom right", "Bottom left", "Top center"])
        start = st.number_input("Starting page number", min_value=1, value=1, step=1)
        if pdf and st.button("Add page numbers", type="primary"):
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from pypdf import Transformation
                reader = pdf_reader(pdf.getvalue())
                writer = PdfWriter()
                for i, pg in enumerate(reader.pages):
                    w = float(pg.mediabox.width)
                    h = float(pg.mediabox.height)
                    layer = io.BytesIO()
                    c = canvas.Canvas(layer, pagesize=(w, h))
                    n = int(start) + i
                    if position == "Bottom center":
                        x, y, align = w / 2, 20, "center"
                    elif position == "Bottom right":
                        x, y, align = w - 30, 20, "right"
                    elif position == "Bottom left":
                        x, y, align = 30, 20, "left"
                    else:
                        x, y, align = w / 2, h - 25, "center"
                    c.setFont("Helvetica", 10)
                    if align == "center":
                        c.drawCentredString(x, y, str(n))
                    elif align == "right":
                        c.drawRightString(x, y, str(n))
                    else:
                        c.drawString(x, y, str(n))
                    c.save()
                    layer.seek(0)
                    overlay = PdfReader(layer).pages[0]
                    pg.merge_page(overlay)
                    writer.add_page(pg)
                st.session_state.number_result = make_pdf_bytes(writer)
            except ImportError:
                st.error("Install reportlab with: pip install reportlab")
            except Exception as e:
                st.error(f"Could not number pages: {e}")
        if "number_result" in st.session_state:
            add_download("Download numbered PDF", st.session_state.number_result, "numbered.pdf", key="number_download")

    elif tool == "Add Watermark":
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="watermark_pdf")
        text = st.text_input("Watermark text", value="CONFIDENTIAL")
        opacity = st.slider("Opacity", 0.1, 1.0, 0.25, 0.05)
        if pdf and st.button("Apply watermark", type="primary"):
            try:
                from reportlab.pdfgen import canvas
                reader = pdf_reader(pdf.getvalue())
                writer = PdfWriter()
                for pg in reader.pages:
                    w, h = float(pg.mediabox.width), float(pg.mediabox.height)
                    layer = io.BytesIO()
                    c = canvas.Canvas(layer, pagesize=(w, h))
                    c.saveState()
                    c.setFillAlpha(opacity)
                    c.setFillColorRGB(0.45, 0.45, 0.45)
                    c.setFont("Helvetica-Bold", max(20, min(w, h) / 12))
                    c.translate(w / 2, h / 2)
                    c.rotate(35)
                    c.drawCentredString(0, 0, text[:100])
                    c.restoreState()
                    c.save()
                    layer.seek(0)
                    pg.merge_page(PdfReader(layer).pages[0])
                    writer.add_page(pg)
                st.session_state.watermark_result = make_pdf_bytes(writer)
            except ImportError:
                st.error("Install reportlab with: pip install reportlab")
            except Exception as e:
                st.error(f"Could not apply watermark: {e}")
        if "watermark_result" in st.session_state:
            add_download("Download watermarked PDF", st.session_state.watermark_result, "watermarked.pdf", key="watermark_download")

    elif tool == "Extract Text":
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="extract_text_pdf")
        if pdf:
            try:
                reader = pdf_reader(pdf.getvalue())
                text = "\n\n".join((pg.extract_text() or "") for pg in reader.pages)
                if not text.strip():
                    st.warning("No selectable text found. This may be a scanned PDF; OCR is needed.")
                st.text_area("Extracted text", text, height=350)
                st.download_button("Download text file", text, file_name=Path(pdf.name).stem + ".txt", mime="text/plain")
            except Exception as e:
                st.error(f"Text extraction failed: {e}")

    elif tool == "Edit Metadata":
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="metadata_pdf")
        if pdf:
            try:
                reader = pdf_reader(pdf.getvalue())
                metadata = reader.metadata or {}
                title = st.text_input("Title", value=str(metadata.get("/Title") or ""))
                author = st.text_input("Author", value=str(metadata.get("/Author") or ""))
                subject = st.text_input("Subject", value=str(metadata.get("/Subject") or ""))
                keywords = st.text_input("Keywords", value=str(metadata.get("/Keywords") or ""))
                if st.button("Save metadata", type="primary"):
                    writer = PdfWriter()
                    writer.append(io.BytesIO(pdf.getvalue()))
                    writer.add_metadata({
                        "/Title": title, "/Author": author,
                        "/Subject": subject, "/Keywords": keywords
                    })
                    st.session_state.metadata_result = make_pdf_bytes(writer)
                if "metadata_result" in st.session_state:
                    add_download("Download updated PDF", st.session_state.metadata_result, "metadata_updated.pdf", key="metadata_download")
            except Exception as e:
                st.error(f"Metadata update failed: {e}")

# -------------------- SECURITY --------------------
elif page == "Security":
    st.title("🛡️ Security")
    tool = st.radio("Choose a tool", ["Password Protect PDF", "Unlock PDF"], horizontal=True)

    if tool == "Password Protect PDF":
        pdf = st.file_uploader("Upload PDF", type=["pdf"], key="protect_pdf")
        password = st.text_input("Set password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        if pdf and st.button("Encrypt PDF", type="primary"):
            if not password:
                st.error("Enter a password.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    writer = PdfWriter()
                    writer.append(io.BytesIO(pdf.getvalue()))
                    writer.encrypt(password)
                    st.session_state.protected_result = make_pdf_bytes(writer)
                    st.success("PDF encrypted.")
                except Exception as e:
                    st.error(f"Encryption failed: {e}")
        if "protected_result" in st.session_state:
            add_download("Download password-protected PDF", st.session_state.protected_result, "protected.pdf", key="protected_download")

    elif tool == "Unlock PDF":
        pdf = st.file_uploader("Upload password-protected PDF", type=["pdf"], key="unlock_pdf")
        password = st.text_input("Current PDF password", type="password")
        if pdf and st.button("Unlock PDF", type="primary"):
            try:
                reader = pdf_reader(pdf.getvalue())
                if reader.is_encrypted and not reader.decrypt(password):
                    st.error("Incorrect password or unsupported encryption.")
                else:
                    writer = PdfWriter()
                    for pg in reader.pages:
                        writer.add_page(pg)
                    st.session_state.unlocked_result = make_pdf_bytes(writer)
                    st.success("PDF decrypted. Only unlock documents you are authorized to access.")
            except Exception as e:
                st.error(f"Could not unlock PDF: {e}")
        if "unlocked_result" in st.session_state:
            add_download("Download unlocked PDF", st.session_state.unlocked_result, "unlocked.pdf", key="unlocked_download")

st.sidebar.divider()
st.sidebar.caption("PDF Toolkit · Local-first")
