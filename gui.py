import os
import sys
import shutil
import tempfile
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QFileDialog, 
                             QProgressBar, QScrollArea, QCheckBox, QStackedWidget)
from PySide6.QtCore import Qt, QMimeData, QSize, Signal, QPropertyAnimation, QEasingCurve, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap, QColor, QDrag, QDesktopServices
import fitz  # PyMuPDF
from pdf_processor import remove_hyperlinks

class Style:
    MAIN_BG = "#0f172a"
    CARD_BG = "rgba(30, 41, 59, 0.7)"
    ACCENT = "#38bdf8"
    ACCENT_HOVER = "#7dd3fc"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    SUCCESS = "#4ade80"
    ERROR = "#f87171"
    
    SHEET = f"""
    QMainWindow {{
        background-color: {MAIN_BG};
    }}
    QWidget#MainContainer {{
        background-color: {MAIN_BG};
    }}
    QFrame#DropZone {{
        background-color: {CARD_BG};
        border: 2px dashed {ACCENT};
        border-radius: 20px;
    }}
    QFrame#DropZone[dragged="true"] {{
        background-color: rgba(56, 189, 248, 0.1);
        border: 2px solid {ACCENT_HOVER};
    }}
    QLabel#Title {{
        color: {TEXT_PRIMARY};
        font-size: 24px;
        font-weight: bold;
    }}
    QLabel#Subtitle {{
        color: {TEXT_SECONDARY};
        font-size: 14px;
    }}
    QPushButton#ActionButton {{
        background-color: {ACCENT};
        color: {MAIN_BG};
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 14px;
    }}
    QPushButton#ActionButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QProgressBar {{
        border: none;
        border-radius: 5px;
        background-color: #1e293b;
        text-align: center;
        color: white;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 5px;
    }}
    QCheckBox {{
        color: {TEXT_SECONDARY};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {ACCENT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
    }}
    """

class FileItem(QFrame):
    removed = Signal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.output_path = None
        self.drag_start_pos = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        layout = QHBoxLayout(self)
        
        name = os.path.basename(self.file_path)
        self.label = QLabel(name)
        self.label.setStyleSheet(f"color: {Style.TEXT_PRIMARY}; font-weight: 500;")
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {Style.TEXT_SECONDARY}; font-size: 11px;")
        
        self.open_btn = QPushButton("Open")
        self.open_btn.setVisible(False)
        self.open_btn.setFixedSize(60, 24)
        self.open_btn.setStyleSheet(f"background: {Style.CARD_BG}; color: {Style.ACCENT}; border-radius: 5px; font-size: 11px;")
        self.open_btn.clicked.connect(self.open_file)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setStyleSheet("color: #f87171; background: transparent; font-weight: bold;")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self.file_path))
        
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.remove_btn)

    def open_file(self):
        if self.output_path and os.path.exists(self.output_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_pos or (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            return
            
        if self.output_path and os.path.exists(self.output_path):
            drag = QDrag(self)
            mime = QMimeData()
            # Important: Wrap path in QUrl
            url = QUrl.fromLocalFile(os.path.abspath(self.output_path))
            mime.setUrls([url])
            # For some systems, also add plain text path
            mime.setText(self.output_path)
            
            drag.setMimeData(mime)
            
            # Start the drag action
            drag.exec(Qt.CopyAction | Qt.MoveAction)

class DropZone(QFrame):
    files_dropped = Signal(list)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setProperty("dragged", "false")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Using standard text instead of icon to avoid font crashes
        self.icon_label = QLabel("PDF")
        self.icon_label.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {Style.ACCENT};")
        
        self.text_label = QLabel("Drop PDF files here")
        self.text_label.setObjectName("Subtitle")
        self.text_label.setStyleSheet("font-size: 18px;")
        
        self.subtext = QLabel("or click to browse")
        self.subtext.setObjectName("Subtitle")
        
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self.text_label, 0, Qt.AlignCenter)
        layout.addWidget(self.subtext, 0, Qt.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setProperty("dragged", "true")
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragged", "false")
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragged", "false")
        self.style().polish(self)
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
        if files:
            self.files_dropped.emit(files)

    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if files:
            self.files_dropped.emit(files)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing MainWindow...")
        self.setWindowTitle("ClearLink-PDF")
        self.resize(800, 600)
        self.setStyleSheet(Style.SHEET)
        
        self.files = {} # path: widget
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("MainContainer")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title_vbox = QVBoxLayout()
        self.title = QLabel("ClearLink-PDF")
        self.title.setObjectName("Title")
        self.subtitle = QLabel("Fast, Private & Secure PDF Link Removal")
        self.subtitle.setObjectName("Subtitle")
        title_vbox.addWidget(self.title)
        title_vbox.addWidget(self.subtitle)
        header.addLayout(title_vbox)
        header.addStretch()
        main_layout.addLayout(header)
        
        # Settings Bar
        settings_layout = QHBoxLayout()
        self.check_all_annots = QCheckBox("Remove All Annotations")
        self.check_all_annots.setToolTip("Removes all highlights, notes, and links")
        
        self.check_metadata = QCheckBox("Scrub Metadata")
        self.check_metadata.setChecked(True)
        
        self.check_compress = QCheckBox("Compress Size")
        self.check_compress.setChecked(True)
        
        self.check_bookmarks = QCheckBox("Remove Bookmarks")
        self.check_bookmarks.setChecked(True)
        self.check_bookmarks.setToolTip("Sometimes table of contents act as links")

        settings_layout.addWidget(self.check_all_annots)
        settings_layout.addWidget(self.check_metadata)
        settings_layout.addWidget(self.check_compress)
        settings_layout.addWidget(self.check_bookmarks)
        settings_layout.addStretch()
        main_layout.addLayout(settings_layout)
        
        # Drop Zone / List Area
        self.stack = QStackedWidget()
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.add_files)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_container)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.stack.addWidget(self.drop_zone)
        self.stack.addWidget(scroll)
        main_layout.addWidget(self.stack)
        
        # Footer / Actions
        self.footer = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.footer.addWidget(self.progress)
        
        self.process_btn = QPushButton("Process Files")
        self.process_btn.setObjectName("ActionButton")
        self.process_btn.setVisible(False)
        self.process_btn.clicked.connect(self.start_processing)
        self.footer.addWidget(self.process_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(f"color: {Style.TEXT_SECONDARY}; text-decoration: underline; background: transparent;")
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self.clear_all)
        self.footer.addWidget(self.clear_btn)
        
        main_layout.addLayout(self.footer)

    def add_files(self, paths):
        for path in paths:
            if path not in self.files:
                item = FileItem(path)
                item.removed.connect(self.remove_file)
                self.list_layout.addWidget(item)
                self.files[path] = item
        
        self.update_ui_state()

    def remove_file(self, path):
        if path in self.files:
            widget = self.files.pop(path)
            widget.deleteLater()
        self.update_ui_state()

    def clear_all(self):
        for path in list(self.files.keys()):
            self.remove_file(path)

    def update_ui_state(self):
        has_files = len(self.files) > 0
        self.stack.setCurrentIndex(1 if has_files else 0)
        self.process_btn.setVisible(has_files)
        self.clear_btn.setVisible(has_files)

    def start_processing(self):
        self.process_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.files))
        self.progress.setValue(0)
        
        remove_all = self.check_all_annots.isChecked()
        scrub = self.check_metadata.isChecked()
        compress = self.check_compress.isChecked()
        rm_bookmarks = self.check_bookmarks.isChecked()
        
        # In a real app, use QThread. For now, we process sequentially.
        processed_count = 0
        for path, widget in self.files.items():
            out_dir = os.path.join(os.path.dirname(path), "processed_pdfs")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            
            out_path = os.path.join(out_dir, "clean_" + os.path.basename(path))
            success, msg = remove_hyperlinks(path, out_path, remove_all, scrub, compress, rm_bookmarks)
            
            if success:
                widget.output_path = out_path
                widget.status_label.setText("Success")
                widget.status_label.setStyleSheet(f"color: {Style.SUCCESS}; font-weight: bold;")
                widget.open_btn.setVisible(True)
            else:
                widget.status_label.setText(f"Error: {msg}")
                widget.status_label.setStyleSheet(f"color: {Style.ERROR};")
            
            processed_count += 1
            self.progress.setValue(processed_count)
            
        self.process_btn.setText("Process Again")
        self.process_btn.setEnabled(True)

    def closeEvent(self, event):
        """Cleanup temporary files on exit"""
        print("Cleaning up temporal file results...")
        for widget in self.files.values():
            if widget.output_path and os.path.exists(widget.output_path):
                try:
                    # Only delete if it's in a temporary directory we managed
                    # But per current logic we save to 'processed_pdfs'
                    # Let's just track all outputs and delete them if they exist
                    os.remove(widget.output_path)
                except Exception as e:
                    print(f"Failed to delete {widget.output_path}: {e}")
        
        # Also try to remove empty 'processed_pdfs' folders
        processed_dirs = set()
        for widget in self.files.values():
            if widget.output_path:
                processed_dirs.add(os.path.dirname(widget.output_path))
        
        for d in processed_dirs:
            if os.path.exists(d) and not os.listdir(d):
                try:
                    os.rmdir(d)
                except: pass
                
        event.accept()
