# 🚀 ClearLink-PDF: Advanced Link Remover

A premium, high-performance utility designed to strip hyperlinks and sensitive data from PDF files. Built with a modern glassmorphic interface and a focus on privacy and efficiency.

![Application Preview](https://via.placeholder.com/800x450.png?text=ClearLink+PDF+Interface) *Placeholder: Create a screenshot and replace this link!*

---

## ✨ Key Features

### 💎 Premium UI/UX
- **Glassmorphic Design**: A sleek, dark-mode aesthetic with translucent elements and smooth rounded corners.
- **Interactive Drag-and-Drop In**: Simply drag your PDFs from Windows Explorer directly into the application.
- **Seamless Drag-and-Drop Out**: Once processed, drag the resulting "Success" items directly out of the app to any folder or your desktop.
- **Batch Processing**: Handle dozens of files simultaneously with real-time progress tracking.
- **Instant Preview & Open**: Open your cleaned PDF directly from the app with a single click after processing.

### 🧠 "Perfect Logic" PDF Engine
- **Linked-List Traversal**: Unlike standard tools that skip links during deletion, our engine safely traverses the internal PDF linked-list to ensure **100% link removal**.
- **Triple-Sweep Cleaning**:
    1. **Visible Links**: Standard annotations and URI links.
    2. **Invisible Clickables**: Internal PDF link objects and URI Action events.
    3. **Embedded Widgets**: Forms and interactive elements that function as links.
- **State-of-the-Art Compression**: Uses `PyMuPDF` garbage collection level 4 and `zlib` deflation to significantly reduce file sizes without losing quality.
- **Privacy Focus**: Built-in metadata scrubbing to remove Author, Creator, and Producer information.

---

## 🛠️ Advanced Options Explained

| Feature | Description |
| :--- | :--- |
| **Remove All Annotations** | Strips everything: highlights, notes, sticky notes, and drawing markups. |
| **Scrub Metadata** | Resets the PDF "Properties" to blank (removes timestamps and author info). |
| **Compress Size** | Applies deep object optimization to shrink the file size. |
| **Remove Bookmarks** | Deletes the Table of Contents (often used for internal/external tracking). |

---

## 🚀 Installation & Setup

This application is designed to run in a lightweight virtual environment to keep your system clean.

### 1. Requirements
- Python 3.8+
- Windows OS (Optimized for DirectWrite fonts)

### 2. Setup (Manual Instructions)
If you are setting this up for the first time:

```powershell
# Create the virtual environment
python -m venv venv

# Install the high-performance dependencies
.\venv\Scripts\python -m pip install PySide6 pymupdf
```

### 3. Running the App
```powershell
.\venv\Scripts\python main.py
```

---

## 🌐 Web Version (GitHub Pages)

The web-based version of this tool is located in the `web/` directory. It uses `pdf-lib` to process files directly in the browser.

### **How to Deploy to GitHub Pages:**
1.  **Push your files** (including the `web/` folder) to a GitHub repository.
2.  Go to **Settings > Pages** in your repo.
3.  Under "Build and deployment", select the **main** branch.
4.  Specify the folder as **`web/`** (or if pushing only the contents of `web` to a `gh-pages` branch, use root).
5.  Click **Save**, and your link remover will be live!

---

## 📂 Automatic Cleanup
The application is built with **Privacy First** in mind:
- **Zero Residue**: When you close the GUI, the application automatically scans and deletes all processed temporary files and removes the `processed_pdfs` folder if empty.
- **Local Processing**: All processing happens on your machine. No data is ever uploaded to a server.

---

## 📝 Technical Deep Dive: The Iteration Bug
Standard PDF libraries often fail when deleting links because they use a standard `for-loop`. When an annotation is deleted, the internal list shifts, causing the loop to skip the next item. 

**ClearLink-PDF** solves this by using a pointer-based `while` loop:
```python
annot = page.first_annot
while annot:
    next_annot = annot.next # Store next pointer BEFORE deletion
    page.delete_annot(annot)
    annot = next_annot      # Move to stored pointer
```
This ensures that even in complex PDFs with hundreds of overlapping links, **not a single one is missed.**

---

*Developed with ❤️ by [Pavneet](https://github.com/pavnxet/ClearLink-PDF)*
