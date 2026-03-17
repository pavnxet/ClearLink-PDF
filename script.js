const { PDFDocument } = PDFLib;

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const fileActionsContainer = document.getElementById('file-actions');
const clearAllBtn = document.getElementById('clear-all-btn');
const processBtn = document.getElementById('process-btn');
const progressContainer = document.getElementById('overall-progress');
const progressBar = document.querySelector('.progress-bar');
const downloadAllBtn = document.getElementById('download-all-btn');
const statsPanel = document.getElementById('stats-panel');

let currentFiles = [];
let processedFiles = []; // { name, url }

// Settings persistence via localStorage
const SETTING_IDS = ['remove-annots', 'scrub-metadata', 'remove-bookmarks', 'auto-download'];

function loadSettings() {
    SETTING_IDS.forEach(id => {
        const saved = localStorage.getItem(`clearlink-${id}`);
        if (saved !== null) {
            document.getElementById(id).checked = saved === 'true';
        }
    });
}

function bindSettingsPersistence() {
    SETTING_IDS.forEach(id => {
        document.getElementById(id).addEventListener('change', (e) => {
            localStorage.setItem(`clearlink-${id}`, e.target.checked);
        });
    });
}

loadSettings();
bindSettingsPersistence();

// Utility: human-readable file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Event Listeners
dropZone.onclick = () => fileInput.click();
fileInput.onchange = (e) => addFiles([...e.target.files]);

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('active');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('active'));

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('active');
    addFiles([...e.dataTransfer.files]);
});

function addFiles(files) {
    const pdfs = files.filter(f => f.type === 'application/pdf');
    if (pdfs.length === 0) return;

    currentFiles.push(...pdfs);
    renderFileList();
}

function renderFileList() {
    dropZone.style.display = 'none';
    fileList.style.display = 'grid';
    fileActionsContainer.style.display = 'flex';
    downloadAllBtn.style.display = 'none';
    statsPanel.style.display = 'none';

    fileList.innerHTML = '';
    currentFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-meta">${formatFileSize(file.size)}</span>
                <span class="file-status" id="status-${index}" style="margin-left: 10px; font-size: 11px; opacity: 0.6;">Ready</span>
            </div>
            <div class="file-actions" id="actions-${index}">
                <button class="btn-item" onclick="removeFileFromList(${index})">✕</button>
            </div>
        `;
        fileList.appendChild(item);
    });
}

function removeFileFromList(index) {
    currentFiles.splice(index, 1);
    if (currentFiles.length === 0) {
        dropZone.style.display = 'flex';
        fileList.style.display = 'none';
        fileActionsContainer.style.display = 'none';
        downloadAllBtn.style.display = 'none';
        statsPanel.style.display = 'none';
        progressContainer.style.display = 'none';
        progressBar.style.width = '0%';
    } else {
        renderFileList();
    }
}

clearAllBtn.onclick = () => {
    revokeProcessedUrls();
    currentFiles = [];
    processedFiles = [];
    dropZone.style.display = 'flex';
    fileList.style.display = 'none';
    fileActionsContainer.style.display = 'none';
    downloadAllBtn.style.display = 'none';
    statsPanel.style.display = 'none';
    progressContainer.style.display = 'none';
    progressBar.style.width = '0%';
};

processBtn.onclick = async () => {
    processBtn.disabled = true;
    clearAllBtn.disabled = true;
    processBtn.innerText = "Processing...";
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    downloadAllBtn.style.display = 'none';
    statsPanel.style.display = 'none';
    revokeProcessedUrls();
    processedFiles = [];

    const removeAnnots = document.getElementById('remove-annots').checked;
    const scrubMetadata = document.getElementById('scrub-metadata').checked;
    const removeBookmarks = document.getElementById('remove-bookmarks').checked;
    const autoDownload = document.getElementById('auto-download').checked;

    let successCount = 0;
    let errorCount = 0;
    let totalOriginalSize = 0;
    let totalCleanedSize = 0;

    for (let i = 0; i < currentFiles.length; i++) {
        const file = currentFiles[i];
        const statusLabel = document.getElementById(`status-${i}`);
        const actionsContainer = document.getElementById(`actions-${i}`);

        totalOriginalSize += file.size;

        try {
            statusLabel.innerText = "Cleaning...";
            console.log(`Processing file: ${file.name}`);
            const arrayBuffer = await file.arrayBuffer();
            const pdfDoc = await PDFDocument.load(arrayBuffer);
            
            // 1. Precise Link Removal Logic
            console.log('1. Processing Annotations/Links...');
            const pages = pdfDoc.getPages();
            pages.forEach(page => {
                const annotations = page.node.Annots();
                if (annotations) {
                    // Iterate backwards as we are deleting items
                    for (let j = annotations.size() - 1; j >= 0; j--) {
                        const annot = annotations.lookup(j);
                        if (!annot || !annot.get) continue;
                        const subtype = annot.get(PDFLib.PDFName.of('Subtype'));
                        
                        // Type /Link or any annotation if user requested all
                        if (subtype === PDFLib.PDFName.of('Link') || removeAnnots) {
                            annotations.remove(j);
                        }
                    }
                }
            });

            // 2. Remove Bookmarks (Table of Contents / Outlines)
            if (removeBookmarks) {
                console.log('2. Removing Bookmarks...');
                const catalog = pdfDoc.catalog;
                catalog.delete(PDFLib.PDFName.of('Outlines'));
            }

            // 3. Scrub Metadata
            if (scrubMetadata) {
                console.log('3. Scrubbing Metadata...');
                pdfDoc.setTitle('');
                pdfDoc.setAuthor('');
                pdfDoc.setSubject('');
                pdfDoc.setKeywords([]);
                pdfDoc.setProducer('');
                pdfDoc.setCreator('');
            }

            console.log('Saving processed PDF...');
            const pdfBytes = await pdfDoc.save();
            totalCleanedSize += pdfBytes.length;

            const blob = new Blob([pdfBytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);

            console.log(`Successfully processed: ${file.name}`);
            statusLabel.innerText = "✓ Done";
            statusLabel.style.color = "#4ade80";

            processedFiles.push({ name: file.name, url });

            // Allow dragging out or downloading
            actionsContainer.innerHTML = `<button class="btn-item download" onclick="downloadFile('${file.name}', '${url}')">Download</button>`;

            if (autoDownload) downloadFile(file.name, url);

            successCount++;
        } catch (err) {
            console.error(`Error processing ${file.name}:`, err);
            statusLabel.innerText = "Error";
            statusLabel.style.color = "#f87171";
            errorCount++;
        }

        progressBar.style.width = `${((i + 1) / currentFiles.length) * 100}%`;
    }

    // Update and show stats
    document.getElementById('stat-processed').innerText = successCount;
    document.getElementById('stat-errors').innerText = errorCount;
    document.getElementById('stat-size-orig').innerText = formatFileSize(totalOriginalSize);
    document.getElementById('stat-size-clean').innerText = formatFileSize(totalCleanedSize);
    statsPanel.style.display = 'flex';

    // Show Download All when more than one file was processed successfully
    if (processedFiles.length > 1) {
        downloadAllBtn.style.display = 'block';
    }

    processBtn.innerText = "Process Again";
    processBtn.disabled = false;
    clearAllBtn.disabled = false;
};

function downloadFile(name, url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = `clean_${name}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function downloadAll() {
    processedFiles.forEach(({ name, url }, i) => {
        setTimeout(() => downloadFile(name, url), i * 150);
    });
}

function revokeProcessedUrls() {
    processedFiles.forEach(({ url }) => URL.revokeObjectURL(url));
}
