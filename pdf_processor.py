import os
from pathlib import Path

import fitz  # PyMuPDF


_METADATA_FIELDS = (
    "format",
    "title",
    "author",
    "subject",
    "keywords",
    "creator",
    "producer",
    "creationDate",
    "modDate",
    "trapped",
    "encryption",
)


def _ensure_parent(output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)


def _save_and_verify(doc, output_path, **kwargs):
    _ensure_parent(output_path)
    doc.save(output_path, **kwargs)
    if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
        raise IOError(f"Output file was not created correctly: {output_path}")


def _metadata_is_scrubbed(metadata):
    """Return True when user-visible PDF metadata fields are empty.

    PyMuPDF always reports structural fields such as ``format`` for an opened
    PDF, so checking ``any(metadata.values())`` incorrectly treats a clean PDF
    as containing metadata.
    """
    user_fields = (
        "title",
        "author",
        "subject",
        "keywords",
        "creator",
        "producer",
        "creationDate",
        "modDate",
        "trapped",
    )
    return not any(metadata.get(field) for field in user_fields)


def remove_hyperlinks(input_path, output_path, remove_all_annots=False, scrub_metadata=True, compress=True, remove_bookmarks=False):
    """Remove PDF links and optionally annotations, bookmarks, and metadata."""
    try:
        with fitz.open(input_path) as doc:
            for page in doc:
                annot = page.first_annot
                while annot:
                    next_annot = annot.next
                    is_link = annot.type[0] == fitz.PDF_ANNOT_LINK
                    if remove_all_annots or is_link:
                        page.delete_annot(annot)
                    annot = next_annot

                for link in list(page.get_links()):
                    page.delete_link(link)

                if remove_all_annots:
                    widget = page.first_widget
                    while widget:
                        next_widget = widget.next
                        page.delete_widget(widget)
                        widget = next_widget

            if remove_bookmarks:
                doc.set_toc([])
            if scrub_metadata:
                doc.set_metadata({})

            garbage_level = 4 if compress else 3
            _save_and_verify(doc, output_path, garbage=garbage_level, deflate=True, clean=True)

        with fitz.open(output_path) as check:
            remaining_links = sum(len(page.get_links()) for page in check)
            if remaining_links:
                return False, f"Verification failed: {remaining_links} links remain"
            if remove_all_annots:
                remaining_annots = sum(1 for page in check for _ in iter_annots(page))
                if remaining_annots:
                    return False, f"Verification failed: {remaining_annots} annotations remain"
            if scrub_metadata and not _metadata_is_scrubbed(check.metadata):
                return False, "Verification failed: metadata remains"

        return True, "Processing successful"
    except Exception as e:
        return False, str(e)


def iter_annots(page):
    annot = page.first_annot
    while annot:
        yield annot
        annot = annot.next


def compress_pdf(input_path, output_path):
    try:
        with fitz.open(input_path) as doc:
            _save_and_verify(doc, output_path, garbage=4, deflate=True, clean=True)
        return True, "Compressed successfully"
    except Exception as e:
        return False, str(e)


def extract_text(input_path):
    try:
        with fitz.open(input_path) as doc:
            text = "\n".join(page.get_text() for page in doc)
        return True, text
    except Exception as e:
        return False, str(e)


def extract_images(input_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        with fitz.open(input_path) as doc:
            count = 0
            for page_index, page in enumerate(doc):
                for img in page.get_images(full=True):
                    base_image = doc.extract_image(img[0])
                    ext = base_image["ext"]
                    output = os.path.join(output_dir, f"page{page_index + 1}_img{count}.{ext}")
                    with open(output, "wb") as f:
                        f.write(base_image["image"])
                    count += 1
        return True, f"Extracted {count} images"
    except Exception as e:
        return False, str(e)


def merge_pdfs(input_paths, output_path):
    try:
        with fitz.open() as merged:
            for path in input_paths:
                with fitz.open(path) as doc:
                    merged.insert_pdf(doc)
            _save_and_verify(merged, output_path, garbage=3, deflate=True)
        return True, "Merged successfully"
    except Exception as e:
        return False, str(e)


def split_pdf(input_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        with fitz.open(input_path) as doc:
            page_count = len(doc)
            base = Path(input_path).stem
            for i in range(page_count):
                with fitz.open() as new_doc:
                    new_doc.insert_pdf(doc, from_page=i, to_page=i)
                    new_doc.save(os.path.join(output_dir, f"{base}_page_{i + 1}.pdf"), garbage=3, deflate=True)
        return True, f"Split into {page_count} pages"
    except Exception as e:
        return False, str(e)


def rotate_pdf(input_path, output_path, angle):
    try:
        angle = int(angle)
        normalized_angle = angle % 360
        if normalized_angle not in (0, 90, 180, 270):
            return False, "Angle must be a multiple of 90 degrees"
        with fitz.open(input_path) as doc:
            for page in doc:
                page.set_rotation(normalized_angle)
            _save_and_verify(doc, output_path, garbage=3, deflate=True)
        return True, "Rotated successfully"
    except Exception as e:
        return False, str(e)


def encrypt_pdf(input_path, output_path, password):
    try:
        if not password:
            return False, "Password must not be empty"
        with fitz.open(input_path) as doc:
            permissions = fitz.PDF_PERM_ACCESSIBILITY | fitz.PDF_PERM_PRINT
            _save_and_verify(
                doc,
                output_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw=password,
                user_pw=password,
                permissions=permissions,
            )
        with fitz.open(output_path) as check:
            if not check.is_encrypted:
                return False, "Verification failed: output is not encrypted"
        return True, "Encrypted successfully"
    except Exception as e:
        return False, str(e)


def decrypt_pdf(input_path, output_path, password):
    try:
        with fitz.open(input_path) as doc:
            if doc.is_encrypted and not doc.authenticate(password):
                return False, "Incorrect password"
            _save_and_verify(doc, output_path, garbage=3, deflate=True)
        with fitz.open(output_path) as check:
            if check.is_encrypted:
                return False, "Verification failed: output is still encrypted"
        return True, "Decrypted successfully"
    except Exception as e:
        return False, str(e)


def add_watermark(input_path, output_path, watermark_text):
    try:
        if not watermark_text:
            return False, "Watermark text must not be empty"
        with fitz.open(input_path) as doc:
            for page in doc:
                rect = page.rect
                # PyMuPDF's insert_text() accepts only 0/90/180/270 degree
                # rotations. Keep the watermark API deterministic and portable.
                page.insert_text(
                    (rect.width / 4, rect.height / 2),
                    watermark_text,
                    fontsize=48,
                    color=(0.7, 0.7, 0.7),
                    rotate=0,
                    overlay=True,
                )
            _save_and_verify(doc, output_path, garbage=3, deflate=True)
        return True, "Watermarked successfully"
    except Exception as e:
        return False, str(e)


def pdf_to_images(input_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        with fitz.open(input_path) as doc:
            page_count = len(doc)
            base = Path(input_path).stem
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=150)
                pix.save(os.path.join(output_dir, f"{base}_page_{i + 1}.png"))
        return True, f"Converted {page_count} pages to images"
    except Exception as e:
        return False, str(e)
