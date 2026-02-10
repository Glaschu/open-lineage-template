import { useRef, useState } from 'react';
import type { Dataset, Job, ImportResult } from '../types';
import { parseMultipleYamlFiles } from '../types';
import './import.css';

interface ImportPanelProps {
    onImport: (datasets: Dataset[], jobs: Job[]) => void;
    existingDatasetIds: string[];
    existingJobIds: string[];
}

export function ImportPanel({ onImport, existingDatasetIds, existingJobIds }: ImportPanelProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [result, setResult] = useState<ImportResult | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [importing, setImporting] = useState(false);

    const handleFiles = async (files: FileList) => {
        setImporting(true);
        const fileContents: Array<{ name: string; content: string }> = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
                const content = await file.text();
                fileContents.push({ name: file.name, content });
            }
        }

        if (fileContents.length === 0) {
            setResult({ datasets: [], jobs: [], errors: ['No YAML files found'] });
            setImporting(false);
            return;
        }

        const parsed = parseMultipleYamlFiles(fileContents);

        // Check for duplicates
        const duplicateDatasets = parsed.datasets.filter(d => existingDatasetIds.includes(d.id));
        const duplicateJobs = parsed.jobs.filter(j => existingJobIds.includes(j.id));

        if (duplicateDatasets.length > 0) {
            parsed.errors.push(`Duplicate dataset IDs: ${duplicateDatasets.map(d => d.id).join(', ')}`);
        }
        if (duplicateJobs.length > 0) {
            parsed.errors.push(`Duplicate job IDs: ${duplicateJobs.map(j => j.id).join(', ')}`);
        }

        setResult(parsed);
        setImporting(false);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            handleFiles(e.target.files);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = () => {
        setDragOver(false);
    };

    const confirmImport = () => {
        if (result) {
            // Filter out duplicates before importing
            const newDatasets = result.datasets.filter(d => !existingDatasetIds.includes(d.id));
            const newJobs = result.jobs.filter(j => !existingJobIds.includes(j.id));
            onImport(newDatasets, newJobs);
            setResult(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const clearResult = () => {
        setResult(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="import-panel">
            <h2>📥 Import YAML Files</h2>
            <p className="import-hint">
                Upload your saved dataset and job YAML files to continue editing them.
            </p>

            <div
                className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".yaml,.yml"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
                <div className="drop-icon">📁</div>
                <p>Drop YAML files here or click to browse</p>
                <span className="drop-hint">Supports multiple .yaml and .yml files</span>
            </div>

            {importing && (
                <div className="import-status">
                    <span className="spinner">⏳</span> Parsing files...
                </div>
            )}

            {result && (
                <div className="import-result">
                    <h3>Import Preview</h3>

                    {result.errors.length > 0 && (
                        <div className="import-errors">
                            <h4>⚠️ Warnings/Errors</h4>
                            <ul>
                                {result.errors.map((err, i) => (
                                    <li key={i}>{err}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="import-summary">
                        <div className="summary-item">
                            <span className="summary-count">{result.datasets.length}</span>
                            <span className="summary-label">Datasets</span>
                            {result.datasets.length > 0 && (
                                <ul className="summary-list">
                                    {result.datasets.map(d => (
                                        <li key={d.id} className={existingDatasetIds.includes(d.id) ? 'duplicate' : ''}>
                                            {d.id}
                                            {existingDatasetIds.includes(d.id) && <span className="dup-badge">exists</span>}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <div className="summary-item">
                            <span className="summary-count">{result.jobs.length}</span>
                            <span className="summary-label">Jobs</span>
                            {result.jobs.length > 0 && (
                                <ul className="summary-list">
                                    {result.jobs.map(j => (
                                        <li key={j.id} className={existingJobIds.includes(j.id) ? 'duplicate' : ''}>
                                            {j.id}
                                            {existingJobIds.includes(j.id) && <span className="dup-badge">exists</span>}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </div>

                    <div className="import-actions">
                        <button className="btn-secondary" onClick={clearResult}>Cancel</button>
                        <button
                            className="btn-primary"
                            onClick={confirmImport}
                            disabled={result.datasets.length === 0 && result.jobs.length === 0}
                        >
                            Import {result.datasets.filter(d => !existingDatasetIds.includes(d.id)).length +
                                result.jobs.filter(j => !existingJobIds.includes(j.id)).length} Items
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
