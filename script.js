const { PDFDocument } = PDFLib;

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const processBtn = document.getElementById('process-btn');
const progressContainer = document.getElementById('overall-progress');
const progressBar = document.querySelector('.progress-bar');

let currentFiles = [];

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
    processBtn.style.display = 'block';

    fileList.innerHTML = '';
    currentFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
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
        processBtn.style.display = 'none';
    } else {
        renderFileList();
    }
}

processBtn.onclick = async () => {
    processBtn.disabled = true;
    processBtn.innerText = "Processing...";
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';

    const removeAnnots = document.getElementById('remove-annots').checked;
    const scrubMetadata = document.getElementById('scrub-metadata').checked;
    const removeBookmarks = document.getElementById('remove-bookmarks').checked;

    for (let i = 0; i < currentFiles.length; i++) {
        const file = currentFiles[i];
        const statusLabel = document.getElementById(`status-${i}`);
        const actionsContainer = document.getElementById(`actions-${i}`);
        
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
            const blob = new Blob([pdfBytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);

            console.log(`Successfully processed: ${file.name}`);
            statusLabel.innerText = "Success";
            statusLabel.style.color = "#4ade80";
            
            // Allow dragging out or downloading
            actionsContainer.innerHTML = `<button class="btn-item download" onclick="downloadFile('${file.name}', '${url}')">Download</button>`;

        } catch (err) {
            console.error(`Error processing ${file.name}:`, err);
            statusLabel.innerText = "Error";
            statusLabel.style.color = "#f87171";
        }

        progressBar.style.width = `${((i + 1) / currentFiles.length) * 100}%`;
    }

    processBtn.innerText = "Process Again";
    processBtn.disabled = false;
};

function downloadFile(name, url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = `clean_${name}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
