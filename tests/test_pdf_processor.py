from pathlib import Path

import fitz

from pdf_processor import (
    add_watermark,
    compress_pdf,
    decrypt_pdf,
    encrypt_pdf,
    extract_text,
    merge_pdfs,
    remove_hyperlinks,
    rotate_pdf,
    split_pdf,
)


def make_pdf(path: Path, pages=2):
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1}")
    doc.save(path)
    doc.close()


def test_remove_links_and_metadata(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "clean.pdf"
    make_pdf(src)
    with fitz.open(src) as doc:
        doc.set_metadata({"author": "test", "title": "example"})
        page = doc[0]
        page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(10, 10, 100, 30), "uri": "https://example.com"})
        doc.save(tmp_path / "with-link.pdf")
    src = tmp_path / "with-link.pdf"

    ok, message = remove_hyperlinks(src, out, remove_all_annots=True)
    assert ok, message
    with fitz.open(out) as doc:
        assert all(not page.get_links() for page in doc)
        metadata = doc.metadata
        user_metadata_fields = (
            "title",
            "author",
            "subject",
            "keywords",
            "creator",
            "producer",
        )
        assert not any(metadata.get(field) for field in user_metadata_fields)


def test_split_and_merge(tmp_path):
    src = tmp_path / "source.pdf"
    make_pdf(src, pages=3)
    split_dir = tmp_path / "split"
    ok, message = split_pdf(src, split_dir)
    assert ok, message
    parts = sorted(split_dir.glob("*.pdf"))
    assert len(parts) == 3

    merged = tmp_path / "merged.pdf"
    ok, message = merge_pdfs(parts, merged)
    assert ok, message
    with fitz.open(merged) as doc:
        assert len(doc) == 3


def test_rotate_compress_and_watermark(tmp_path):
    src = tmp_path / "source.pdf"
    make_pdf(src)
    rotated = tmp_path / "rotated.pdf"
    compressed = tmp_path / "compressed.pdf"
    watermarked = tmp_path / "watermarked.pdf"

    ok, message = rotate_pdf(src, rotated, 90)
    assert ok, message
    with fitz.open(rotated) as doc:
        assert doc[0].rotation == 90

    ok, message = compress_pdf(src, compressed)
    assert ok, message
    assert compressed.stat().st_size > 0

    ok, message = add_watermark(src, watermarked, "CONFIDENTIAL")
    assert ok, message
    assert watermarked.stat().st_size > 0


def test_encrypt_decrypt(tmp_path):
    src = tmp_path / "source.pdf"
    encrypted = tmp_path / "encrypted.pdf"
    decrypted = tmp_path / "decrypted.pdf"
    make_pdf(src)

    ok, message = encrypt_pdf(src, encrypted, "secret")
    assert ok, message
    with fitz.open(encrypted) as doc:
        assert doc.is_encrypted

    ok, message = decrypt_pdf(encrypted, decrypted, "secret")
    assert ok, message
    with fitz.open(decrypted) as doc:
        assert not doc.is_encrypted


def test_extract_text(tmp_path):
    src = tmp_path / "source.pdf"
    make_pdf(src)
    ok, text = extract_text(src)
    assert ok
    assert "Page 1" in text
