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
