import { useState } from 'react';
import JSZip from 'jszip';
import './export.css';

interface ExportFile {
    name: string;
    content: string;
}

interface ExportPanelProps {
    files: ExportFile[];
}

export function ExportPanel({ files }: ExportPanelProps) {
    const [selectedFile, setSelectedFile] = useState<ExportFile | null>(files[0] || null);
    const [downloading, setDownloading] = useState(false);

    const downloadFile = (file: ExportFile) => {
        const blob = new Blob([file.content], { type: 'text/yaml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name.split('/').pop() || file.name;
        a.click();
        URL.revokeObjectURL(url);
    };

    const downloadAllAsZip = async () => {
        setDownloading(true);

        try {
            const zip = new JSZip();

            // Add each file to the ZIP with proper folder structure
            for (const file of files) {
                // file.name is like "datasets/my_dataset.yaml" or "jobs/my_job.yaml"
                zip.file(file.name, file.content);
            }

            // Generate the ZIP file
            const blob = await zip.generateAsync({
                type: 'blob',
                compression: 'DEFLATE',
                compressionOptions: { level: 6 }
            });

            // Download the ZIP
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'lineage-definitions.zip';
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error creating ZIP:', error);
        } finally {
            setDownloading(false);
        }
    };

    const copyToClipboard = (content: string) => {
        navigator.clipboard.writeText(content);
    };

    if (files.length === 0) {
        return (
            <div className="export-panel">
                <h2>📤 Export YAML</h2>
                <p className="empty-state">
                    No datasets or jobs to export. Create some definitions first.
                </p>
            </div>
        );
    }

    return (
        <div className="export-panel">
            <h2>📤 Export YAML</h2>

            <div className="export-actions">
                <button
                    className="btn-primary"
                    onClick={downloadAllAsZip}
                    disabled={downloading}
                >
                    {downloading ? '⏳ Creating ZIP...' : `📦 Download All as ZIP (${files.length} files)`}
                </button>
                <p className="export-hint">
                    ZIP contains datasets/ and jobs/ folders with YAML files ready to use
                </p>
            </div>

            <div className="export-layout">
                <div className="file-list">
                    <h3>Files</h3>
                    {files.map(file => (
                        <div
                            key={file.name}
                            className={`file-item ${selectedFile?.name === file.name ? 'selected' : ''}`}
                            onClick={() => setSelectedFile(file)}
                        >
                            <span className="file-icon">📄</span>
                            <span className="file-name">{file.name}</span>
                        </div>
                    ))}
                </div>

                <div className="file-preview">
                    {selectedFile && (
                        <>
                            <div className="preview-header">
                                <h3>{selectedFile.name}</h3>
                                <div className="preview-actions">
                                    <button onClick={() => copyToClipboard(selectedFile.content)}>
                                        📋 Copy
                                    </button>
                                    <button onClick={() => downloadFile(selectedFile)}>
                                        ⬇️ Download
                                    </button>
                                </div>
                            </div>
                            <pre className="yaml-content">{selectedFile.content}</pre>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
