import fitz  # PyMuPDF
import os

def remove_hyperlinks(input_path, output_path, remove_all_annots=False, scrub_metadata=True, compress=True, remove_bookmarks=False):
    """
    Removes hyperlinks from a PDF file with perfect logic.
    """
    try:
        doc = fitz.open(input_path)
        
        for page in doc:
            # 1. Safely remove annotations (including links) without skipping
            # PyMuPDF annotations are a linked list. Deleting while iterating via a standard for-loop skips items!
            annot = page.first_annot
            while annot:
                next_annot = annot.next  # Save reference to next before deleting!
                
                # Type 1 is a Link annotation. We also catch any annotation with a URI action.
                is_link = (annot.type[0] == 1)
                
                if remove_all_annots or is_link:
                    page.delete_annot(annot)
                
                annot = next_annot
            
            # 2. Also clear links using get_links() just in case they are defined differently
            links = list(page.get_links())
            for link in links:
                try:
                    page.delete_link(link)
                except:
                    pass
            
            # 3. Widgets (forms) which might act as links
            if remove_all_annots:
                widget = page.first_widget
                while widget:
                    next_widget = widget.next
                    try:
                        page.delete_widget(widget)
                    except:
                        pass
                    widget = next_widget

        # 4. Optional: Remove Bookmarks (Table of Contents) that might act as links
        if remove_bookmarks:
            doc.set_toc([])

        # 5. Optional: Scrub Metadata
        if scrub_metadata:
            doc.set_metadata({})
            
        # 6. Save with optimizations
        # garbage=4: removes unused objects, duplicate objects, and compacts xrefs
        garbage_level = 4 if compress else 3
        doc.save(output_path, garbage=garbage_level, deflate=True, clean=True)
        doc.close()
        
        return True, "Processing successful"
    except Exception as e:
        return False, str(e)

def compress_pdf(input_path, output_path):
    try:
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return True, "Compressed successfully"
    except Exception as e:
        return False, str(e)

def extract_text(input_path):
    try:
        doc = fitz.open(input_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return True, text
    except Exception as e:
        return False, str(e)

def extract_images(input_path, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        doc = fitz.open(input_path)
        count = 0
        for i in range(len(doc)):
            page = doc[i]
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                with open(os.path.join(output_dir, f"page{i+1}_img{count}.{ext}"), "wb") as f:
                    f.write(image_bytes)
                count += 1
        doc.close()
        return True, f"Extracted {count} images"
    except Exception as e:
        return False, str(e)

def merge_pdfs(input_paths, output_path):
    try:
        merged = fitz.open()
        for path in input_paths:
            doc = fitz.open(path)
            merged.insert_pdf(doc)
            doc.close()
        merged.save(output_path, garbage=3, deflate=True)
        merged.close()
        return True, "Merged successfully"
    except Exception as e:
        return False, str(e)

def split_pdf(input_path, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        doc = fitz.open(input_path)
        base = os.path.basename(input_path).replace('.pdf', '')
        for i in range(len(doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            new_doc.save(os.path.join(output_dir, f"{base}_page_{i+1}.pdf"))
            new_doc.close()
        doc.close()
        return True, f"Split into {len(doc)} pages"
    except Exception as e:
        return False, str(e)

def rotate_pdf(input_path, output_path, angle):
    try:
        doc = fitz.open(input_path)
        for page in doc:
            page.set_rotation(angle)
        doc.save(output_path, garbage=3, deflate=True)
        doc.close()
        return True, "Rotated successfully"
    except Exception as e:
        return False, str(e)

def encrypt_pdf(input_path, output_path, password):
    try:
        doc = fitz.open(input_path)
        perm = fitz.PDF_PERM_ACCESSIBILITY | fitz.PDF_PERM_PRINT
        encrypt_meth = fitz.PDF_ENCRYPT_AES_256
        doc.save(output_path, encryption=encrypt_meth, owner_pw=password, user_pw=password, permissions=perm)
        doc.close()
        return True, "Encrypted successfully"
    except Exception as e:
        return False, str(e)

def decrypt_pdf(input_path, output_path, password):
    try:
        doc = fitz.open(input_path)
        if doc.is_encrypted:
            if not doc.authenticate(password):
                return False, "Incorrect password"
        doc.save(output_path, garbage=3, deflate=True)
        doc.close()
        return True, "Decrypted successfully"
    except Exception as e:
        return False, str(e)

def add_watermark(input_path, output_path, watermark_text):
    try:
        doc = fitz.open(input_path)
        for page in doc:
            rect = page.rect
            page.insert_text((rect.width/4, rect.height/2), watermark_text, fontsize=48, color=(0.7,0.7,0.7), rotate=45, overlay=True)
        doc.save(output_path, garbage=3, deflate=True)
        doc.close()
        return True, "Watermarked successfully"
    except Exception as e:
        return False, str(e)

def pdf_to_images(input_path, output_dir):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        doc = fitz.open(input_path)
        base = os.path.basename(input_path).replace('.pdf', '')
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            pix.save(os.path.join(output_dir, f"{base}_page_{i+1}.png"))
        doc.close()
        return True, f"Converted {len(doc)} pages to images"
    except Exception as e:
        return False, str(e)
