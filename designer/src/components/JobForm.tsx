import { useState } from 'react';
import type { Job, Dataset, ColumnMapping } from '../types';
import { ColumnLineageEditor } from './ColumnLineageEditor';
import './forms.css';

interface JobFormProps {
    job: Job;
    datasets: Dataset[];
    onSave: (job: Job) => void;
    onCancel: () => void;
}

export function JobForm({ job, datasets, onSave, onCancel }: JobFormProps) {
    const [data, setData] = useState<Job>(job);
    const [error, setError] = useState<string | null>(null);
    const [editingColumnLineage, setEditingColumnLineage] = useState<{
        outputIndex: number;
        outputDataset: Dataset;
    } | null>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!data.id.trim()) {
            setError('Job ID is required');
            return;
        }
        if (!data.namespace.trim()) {
            setError('Namespace is required');
            return;
        }
        if (!data.name.trim()) {
            setError('Name is required');
            return;
        }
        if (data.inputs.length === 0) {
            setError('At least one input dataset is required');
            return;
        }
        if (data.outputs.length === 0) {
            setError('At least one output dataset is required');
            return;
        }

        onSave(data);
    };

    const toggleInput = (datasetId: string) => {
        setData(prev => {
            const existing = prev.inputs.find(i => i.ref === datasetId);
            if (existing) {
                return { ...prev, inputs: prev.inputs.filter(i => i.ref !== datasetId) };
            }
            return { ...prev, inputs: [...prev.inputs, { ref: datasetId }] };
        });
    };

    const toggleOutput = (datasetId: string) => {
        setData(prev => {
            const existing = prev.outputs.find(o => o.ref === datasetId);
            if (existing) {
                return { ...prev, outputs: prev.outputs.filter(o => o.ref !== datasetId) };
            }
            return { ...prev, outputs: [...prev.outputs, { ref: datasetId }] };
        });
    };

    const handleColumnLineageSave = (outputIndex: number, columnLineage: Record<string, ColumnMapping[]>) => {
        setData(prev => ({
            ...prev,
            outputs: prev.outputs.map((o, i) =>
                i === outputIndex ? { ...o, columnLineage } : o
            )
        }));
        setEditingColumnLineage(null);
    };

    const getDatasetById = (id: string) => datasets.find(d => d.id === id);
    const inputDatasets = data.inputs.map(i => getDatasetById(i.ref)).filter(Boolean) as Dataset[];

    if (editingColumnLineage) {
        return (
            <ColumnLineageEditor
                outputDataset={editingColumnLineage.outputDataset}
                inputDatasets={inputDatasets}
                existingLineage={data.outputs[editingColumnLineage.outputIndex].columnLineage || {}}
                onSave={(lineage) => handleColumnLineageSave(editingColumnLineage.outputIndex, lineage)}
                onCancel={() => setEditingColumnLineage(null)}
            />
        );
    }

    return (
        <form className="form" onSubmit={handleSubmit}>
            <h2>{job.id ? 'Edit Job' : 'New Job'}</h2>

            {error && <div className="error-message">{error}</div>}

            <div className="form-section">
                <h3>Basic Info</h3>
                <div className="form-row">
                    <label>
                        ID *
                        <input
                            type="text"
                            value={data.id}
                            onChange={e => setData(prev => ({ ...prev, id: e.target.value.replace(/[^a-zA-Z0-9_-]/g, '_') }))}
                            placeholder="e.g., users_etl"
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Namespace *
                        <input
                            type="text"
                            value={data.namespace}
                            onChange={e => setData(prev => ({ ...prev, namespace: e.target.value }))}
                            placeholder='e.g., data-platform'
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Name *
                        <input
                            type="text"
                            value={data.name}
                            onChange={e => setData(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="e.g., users-etl-job"
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Description
                        <textarea
                            value={data.documentation?.description || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                documentation: { description: e.target.value }
                            }))}
                            placeholder="What does this job do?"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Job Type</h3>
                <div className="form-row inline">
                    <label>
                        Processing Type
                        <select
                            value={data.jobType?.processingType || 'BATCH'}
                            onChange={e => setData(prev => ({
                                ...prev,
                                jobType: { ...prev.jobType, processingType: e.target.value as 'BATCH' | 'STREAMING' | 'SERVICE' }
                            }))}
                        >
                            <option value="BATCH">Batch</option>
                            <option value="STREAMING">Streaming</option>
                            <option value="SERVICE">Service</option>
                        </select>
                    </label>
                    <label>
                        Job Type
                        <input
                            type="text"
                            value={data.jobType?.jobType || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                jobType: { ...prev.jobType, processingType: prev.jobType?.processingType || 'BATCH', jobType: e.target.value }
                            }))}
                            placeholder="e.g., ETL, MODEL"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Input Datasets</h3>
                {datasets.length === 0 ? (
                    <p className="hint">Create datasets first before adding them as inputs.</p>
                ) : (
                    <div className="dataset-selector">
                        {datasets.map(d => (
                            <label key={d.id} className="checkbox-item">
                                <input
                                    type="checkbox"
                                    checked={data.inputs.some(i => i.ref === d.id)}
                                    onChange={() => toggleInput(d.id)}
                                />
                                <span>{d.id}</span>
                                <span className="secondary">{d.name}</span>
                            </label>
                        ))}
                    </div>
                )}
            </div>

            <div className="form-section">
                <h3>Output Datasets</h3>
                {datasets.length === 0 ? (
                    <p className="hint">Create datasets first before adding them as outputs.</p>
                ) : (
                    <div className="dataset-selector">
                        {datasets.map(d => {
                            const outputIndex = data.outputs.findIndex(o => o.ref === d.id);
                            const isOutput = outputIndex >= 0;
                            const hasColumnLineage = isOutput && data.outputs[outputIndex].columnLineage &&
                                Object.keys(data.outputs[outputIndex].columnLineage!).length > 0;

                            return (
                                <div key={d.id} className="output-item">
                                    <label className="checkbox-item">
                                        <input
                                            type="checkbox"
                                            checked={isOutput}
                                            onChange={() => toggleOutput(d.id)}
                                        />
                                        <span>{d.id}</span>
                                        <span className="secondary">{d.name}</span>
                                    </label>
                                    {isOutput && (
                                        <button
                                            type="button"
                                            className={`btn-small ${hasColumnLineage ? 'success' : ''}`}
                                            onClick={() => setEditingColumnLineage({ outputIndex, outputDataset: d })}
                                        >
                                            {hasColumnLineage ? '✓ Column Lineage' : '+ Column Lineage'}
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
                <button type="submit" className="btn-primary">Save Job</button>
            </div>
        </form>
    );
}
