/**
 * Document Viewer - In-browser PDF and image preview
 * Uses PDF.js for PDF rendering
 */

// PDF.js worker location (from CDN)
if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

class DocumentViewer {
    constructor() {
        this.modal = null;
        this.currentPdf = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.scale = 1.0;
        this.minScale = 0.5;
        this.maxScale = 3.0;
        this.init();
    }

    init() {
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // Check if modal already exists
        if (document.getElementById('documentViewerModal')) {
            this.modal = document.getElementById('documentViewerModal');
            return;
        }

        const modalHTML = `
            <div id="documentViewerModal" class="doc-viewer-modal" style="display: none;">
                <div class="doc-viewer-overlay"></div>
                <div class="doc-viewer-container">
                    <div class="doc-viewer-header">
                        <div class="doc-viewer-title">
                            <span class="doc-viewer-filename"></span>
                        </div>
                        <div class="doc-viewer-controls">
                            <div class="doc-viewer-pagination" style="display: none;">
                                <button class="doc-viewer-btn" id="docPrevPage" title="Previous Page">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="15 18 9 12 15 6"></polyline>
                                    </svg>
                                </button>
                                <span class="doc-viewer-page-info">
                                    <span id="docCurrentPage">1</span> / <span id="docTotalPages">1</span>
                                </span>
                                <button class="doc-viewer-btn" id="docNextPage" title="Next Page">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="9 18 15 12 9 6"></polyline>
                                    </svg>
                                </button>
                            </div>
                            <div class="doc-viewer-zoom">
                                <button class="doc-viewer-btn" id="docZoomOut" title="Zoom Out">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"></circle>
                                        <line x1="8" y1="11" x2="14" y2="11"></line>
                                    </svg>
                                </button>
                                <span class="doc-viewer-zoom-level" id="docZoomLevel">100%</span>
                                <button class="doc-viewer-btn" id="docZoomIn" title="Zoom In">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"></circle>
                                        <line x1="11" y1="8" x2="11" y2="14"></line>
                                        <line x1="8" y1="11" x2="14" y2="11"></line>
                                    </svg>
                                </button>
                                <button class="doc-viewer-btn" id="docZoomFit" title="Fit to Width">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="9" y1="3" x2="9" y2="21"></line>
                                        <line x1="15" y1="3" x2="15" y2="21"></line>
                                    </svg>
                                </button>
                            </div>
                            <a class="doc-viewer-btn doc-viewer-download" id="docDownload" title="Download" download>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7 10 12 15 17 10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                            </a>
                            <button class="doc-viewer-btn doc-viewer-close" id="docClose" title="Close">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="doc-viewer-content">
                        <div class="doc-viewer-loading" style="display: none;">
                            <div class="doc-viewer-spinner"></div>
                            <span>Loading document...</span>
                        </div>
                        <div class="doc-viewer-error" style="display: none;">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                            <span class="doc-viewer-error-msg">Unable to load document</span>
                        </div>
                        <canvas id="docViewerCanvas" class="doc-viewer-canvas"></canvas>
                        <img id="docViewerImage" class="doc-viewer-image" style="display: none;" alt="Document preview">
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('documentViewerModal');
        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('docViewerStyles')) return;

        const styles = `
            <style id="docViewerStyles">
                .doc-viewer-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .doc-viewer-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.85);
                    backdrop-filter: blur(4px);
                }
                .doc-viewer-container {
                    position: relative;
                    width: 95%;
                    max-width: 1200px;
                    height: 90vh;
                    background: var(--theme-bg, #ffffff);
                    border-radius: 16px;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                }
                .doc-viewer-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 20px;
                    background: var(--theme-bg-secondary, #f9fafb);
                    border-bottom: 1px solid var(--theme-border, #e5e7eb);
                    flex-shrink: 0;
                }
                .doc-viewer-title {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .doc-viewer-filename {
                    font-size: 16px;
                    font-weight: 600;
                    color: var(--theme-text, #1e3a5f);
                    max-width: 300px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .doc-viewer-controls {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .doc-viewer-pagination,
                .doc-viewer-zoom {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    padding: 4px 8px;
                    background: var(--theme-bg, #ffffff);
                    border-radius: 8px;
                    border: 1px solid var(--theme-border, #e5e7eb);
                }
                .doc-viewer-page-info,
                .doc-viewer-zoom-level {
                    font-size: 13px;
                    font-weight: 500;
                    color: var(--theme-text-secondary, #6b7280);
                    min-width: 60px;
                    text-align: center;
                }
                .doc-viewer-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 36px;
                    height: 36px;
                    border: none;
                    background: transparent;
                    color: var(--theme-text-secondary, #6b7280);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                }
                .doc-viewer-btn:hover {
                    background: var(--theme-bg-hover, #f3f4f6);
                    color: var(--theme-text, #1e3a5f);
                }
                .doc-viewer-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .doc-viewer-close {
                    background: var(--theme-danger-bg, #fee2e2);
                    color: var(--theme-danger, #dc2626);
                }
                .doc-viewer-close:hover {
                    background: var(--theme-danger, #dc2626);
                    color: white;
                }
                .doc-viewer-download {
                    background: var(--theme-success-bg, #dcfce7);
                    color: var(--theme-success, #16a34a);
                }
                .doc-viewer-download:hover {
                    background: var(--theme-success, #16a34a);
                    color: white;
                }
                .doc-viewer-content {
                    flex: 1;
                    overflow: auto;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--theme-bg-tertiary, #f0f2f5);
                    position: relative;
                }
                .doc-viewer-canvas,
                .doc-viewer-image {
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    transition: transform 0.2s ease;
                }
                .doc-viewer-loading,
                .doc-viewer-error {
                    position: absolute;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    color: var(--theme-text-secondary, #6b7280);
                }
                .doc-viewer-spinner {
                    width: 48px;
                    height: 48px;
                    border: 4px solid var(--theme-border, #e5e7eb);
                    border-top-color: var(--theme-accent, #0d9488);
                    border-radius: 50%;
                    animation: docViewerSpin 1s linear infinite;
                }
                @keyframes docViewerSpin {
                    to { transform: rotate(360deg); }
                }
                .doc-viewer-error {
                    color: var(--theme-danger, #dc2626);
                }
                .doc-viewer-error-msg {
                    font-size: 16px;
                    font-weight: 500;
                }

                /* Dark mode support */
                [data-theme="dark"] .doc-viewer-container {
                    background: #1a1a2e;
                }
                [data-theme="dark"] .doc-viewer-header {
                    background: #0f0f1a;
                    border-color: #2d2d44;
                }
                [data-theme="dark"] .doc-viewer-content {
                    background: #0a0a14;
                }
                [data-theme="dark"] .doc-viewer-pagination,
                [data-theme="dark"] .doc-viewer-zoom {
                    background: #1a1a2e;
                    border-color: #2d2d44;
                }

                /* Mobile responsive */
                @media (max-width: 768px) {
                    .doc-viewer-container {
                        width: 100%;
                        height: 100%;
                        border-radius: 0;
                    }
                    .doc-viewer-header {
                        flex-wrap: wrap;
                        gap: 8px;
                        padding: 10px 12px;
                    }
                    .doc-viewer-filename {
                        max-width: 200px;
                        font-size: 14px;
                    }
                    .doc-viewer-controls {
                        flex-wrap: wrap;
                    }
                    .doc-viewer-btn {
                        width: 32px;
                        height: 32px;
                    }
                }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }

    bindEvents() {
        // Close button
        document.getElementById('docClose')?.addEventListener('click', () => this.close());

        // Overlay click to close
        this.modal?.querySelector('.doc-viewer-overlay')?.addEventListener('click', () => this.close());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.modal?.style.display === 'none') return;

            switch(e.key) {
                case 'Escape':
                    this.close();
                    break;
                case 'ArrowLeft':
                    this.prevPage();
                    break;
                case 'ArrowRight':
                    this.nextPage();
                    break;
                case '+':
                case '=':
                    e.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    this.zoomOut();
                    break;
            }
        });

        // Pagination
        document.getElementById('docPrevPage')?.addEventListener('click', () => this.prevPage());
        document.getElementById('docNextPage')?.addEventListener('click', () => this.nextPage());

        // Zoom
        document.getElementById('docZoomIn')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('docZoomOut')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('docZoomFit')?.addEventListener('click', () => this.fitToWidth());
    }

    async open(url, filename, downloadUrl) {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Set filename
        this.modal.querySelector('.doc-viewer-filename').textContent = filename || 'Document';

        // Set download link
        const downloadBtn = document.getElementById('docDownload');
        downloadBtn.href = downloadUrl || url;
        downloadBtn.download = filename || 'document';

        // Show loading
        this.showLoading();

        // Determine file type
        const ext = (filename || url).toLowerCase().split('.').pop();
        const isPdf = ext === 'pdf';
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext);

        try {
            if (isPdf) {
                await this.loadPdf(url);
            } else if (isImage) {
                await this.loadImage(url);
            } else {
                // Unsupported format - offer download
                this.showError('This file type cannot be previewed. Click download to view.');
            }
        } catch (error) {
            console.error('Document viewer error:', error);
            this.showError('Unable to load document');
        }
    }

    async loadPdf(url) {
        const canvas = document.getElementById('docViewerCanvas');
        const image = document.getElementById('docViewerImage');

        canvas.style.display = 'block';
        image.style.display = 'none';

        // Show pagination controls
        this.modal.querySelector('.doc-viewer-pagination').style.display = 'flex';

        try {
            // Check if PDF.js is loaded
            if (typeof pdfjsLib === 'undefined') {
                throw new Error('PDF.js not loaded');
            }

            this.currentPdf = await pdfjsLib.getDocument(url).promise;
            this.totalPages = this.currentPdf.numPages;
            this.currentPage = 1;

            document.getElementById('docTotalPages').textContent = this.totalPages;

            await this.renderPage(this.currentPage);
            this.hideLoading();
        } catch (error) {
            console.error('PDF load error:', error);
            this.showError('Unable to load PDF. The file may be corrupted or protected.');
        }
    }

    async renderPage(pageNum) {
        if (!this.currentPdf) return;

        const page = await this.currentPdf.getPage(pageNum);
        const canvas = document.getElementById('docViewerCanvas');
        const ctx = canvas.getContext('2d');

        // Calculate scale to fit width
        const container = this.modal.querySelector('.doc-viewer-content');
        const containerWidth = container.clientWidth - 40;
        const viewport = page.getViewport({ scale: 1 });
        const fitScale = containerWidth / viewport.width;

        // Use minimum of fit scale or current scale
        const actualScale = Math.min(fitScale, this.scale) * window.devicePixelRatio;
        const scaledViewport = page.getViewport({ scale: actualScale });

        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        canvas.style.width = (scaledViewport.width / window.devicePixelRatio) + 'px';
        canvas.style.height = (scaledViewport.height / window.devicePixelRatio) + 'px';

        await page.render({
            canvasContext: ctx,
            viewport: scaledViewport
        }).promise;

        document.getElementById('docCurrentPage').textContent = pageNum;
        this.updateZoomLevel();
    }

    async loadImage(url) {
        const canvas = document.getElementById('docViewerCanvas');
        const image = document.getElementById('docViewerImage');

        canvas.style.display = 'none';
        image.style.display = 'block';

        // Hide pagination controls for images
        this.modal.querySelector('.doc-viewer-pagination').style.display = 'none';

        return new Promise((resolve, reject) => {
            image.onload = () => {
                this.hideLoading();
                resolve();
            };
            image.onerror = () => {
                this.showError('Unable to load image');
                reject(new Error('Image load failed'));
            };
            image.src = url;
        });
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderPage(this.currentPage);
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.renderPage(this.currentPage);
        }
    }

    zoomIn() {
        if (this.scale < this.maxScale) {
            this.scale += 0.25;
            if (this.currentPdf) {
                this.renderPage(this.currentPage);
            } else {
                this.applyImageZoom();
            }
        }
    }

    zoomOut() {
        if (this.scale > this.minScale) {
            this.scale -= 0.25;
            if (this.currentPdf) {
                this.renderPage(this.currentPage);
            } else {
                this.applyImageZoom();
            }
        }
    }

    fitToWidth() {
        this.scale = 1.0;
        if (this.currentPdf) {
            this.renderPage(this.currentPage);
        } else {
            this.applyImageZoom();
        }
    }

    applyImageZoom() {
        const image = document.getElementById('docViewerImage');
        image.style.transform = `scale(${this.scale})`;
        this.updateZoomLevel();
    }

    updateZoomLevel() {
        document.getElementById('docZoomLevel').textContent = Math.round(this.scale * 100) + '%';
    }

    showLoading() {
        this.modal.querySelector('.doc-viewer-loading').style.display = 'flex';
        this.modal.querySelector('.doc-viewer-error').style.display = 'none';
        document.getElementById('docViewerCanvas').style.display = 'none';
        document.getElementById('docViewerImage').style.display = 'none';
    }

    hideLoading() {
        this.modal.querySelector('.doc-viewer-loading').style.display = 'none';
    }

    showError(message) {
        this.modal.querySelector('.doc-viewer-loading').style.display = 'none';
        this.modal.querySelector('.doc-viewer-error').style.display = 'flex';
        this.modal.querySelector('.doc-viewer-error-msg').textContent = message;
    }

    close() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';

        // Clean up
        this.currentPdf = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.scale = 1.0;

        // Clear canvas and image
        const canvas = document.getElementById('docViewerCanvas');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        document.getElementById('docViewerImage').src = '';
    }
}

// Global instance
let documentViewer = null;

// Initialize on DOM ready
function initDocumentViewer() {
    if (!documentViewer) {
        documentViewer = new DocumentViewer();
    }
    return documentViewer;
}

// Helper function to preview a document
function previewDocument(url, filename, downloadUrl) {
    const viewer = initDocumentViewer();
    viewer.open(url, filename, downloadUrl);
}

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDocumentViewer);
} else {
    initDocumentViewer();
}
