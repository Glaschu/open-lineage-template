import { useState } from 'react';
import type { Job, Dataset, ColumnMapping, Owner } from '../types';
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

    const addOwner = () => {
        setData(prev => ({
            ...prev,
            ownership: {
                owners: [...(prev.ownership?.owners || []), { name: '', type: 'TEAM' as const }]
            }
        }));
    };

    const updateOwner = (index: number, owner: Partial<Owner>) => {
        setData(prev => ({
            ...prev,
            ownership: {
                owners: (prev.ownership?.owners || []).map((o, i) =>
                    i === index ? { ...o, ...owner } : o
                )
            }
        }));
    };

    const removeOwner = (index: number) => {
        setData(prev => ({
            ...prev,
            ownership: {
                owners: (prev.ownership?.owners || []).filter((_, i) => i !== index)
            }
        }));
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
                            onChange={e => setData(prev => ({ ...prev, id: e.target.value.replace(/[^a-zA-Z0-9_.-]/g, '_') }))}
                            placeholder="e.g., users_etl"
                        />
                    </label>
                    <label>
                        Application ID
                        <input
                            type="text"
                            value={data.applicationId || ''}
                            onChange={e => setData(prev => ({ ...prev, applicationId: e.target.value }))}
                            placeholder="e.g., crm.customer_portal"
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
                            value={data.description || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                description: e.target.value
                            }))}
                            placeholder="What does this job do?"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Job Execution</h3>
                <div className="form-row inline">
                    <label>
                        Execution Type
                        <select
                            value={data.execution?.type || 'BATCH'}
                            onChange={e => setData(prev => ({
                                ...prev,
                                execution: {
                                    schedule: prev.execution?.schedule,
                                    type: e.target.value
                                }
                            }))}
                        >
                            <option value="BATCH">Batch</option>
                            <option value="STREAMING">Streaming</option>
                            <option value="SERVICE">Service</option>
                        </select>
                    </label>
                    <label>
                        Schedule
                        <input
                            type="text"
                            value={data.execution?.schedule || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                execution: {
                                    type: prev.execution?.type || 'BATCH',
                                    schedule: e.target.value
                                }
                            }))}
                            placeholder="e.g., 0 0 * * *"
                        />
                    </label>
                </div>
                <label>
                    <input
                        type="checkbox"
                        checked={data.enabled !== false}
                        onChange={e => setData(prev => ({ ...prev, enabled: e.target.checked }))}
                    />
                    Enabled
                </label>
            </div>

            <div className="form-section">
                <h3>Extractor Metadata</h3>
                <div className="form-row">
                    <label>
                        Type
                        <select
                            value={data.extractorMetadata?.type || 'MANUAL'}
                            onChange={e => setData(prev => ({
                                ...prev,
                                extractorMetadata: {
                                    ...prev.extractorMetadata,
                                    type: e.target.value
                                }
                            }))}
                        >
                            <option value="MANUAL">Manual</option>
                            <option value="3RD_PARTY_TOOL">3rd Party</option>
                            <option value="GEN_AI">GenAI</option>
                        </select>
                    </label>
                    <label>
                        Tool Name
                        <input
                            type="text"
                            value={data.extractorMetadata?.toolName || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                extractorMetadata: {
                                    ...prev.extractorMetadata,
                                    type: prev.extractorMetadata?.type || 'MANUAL',
                                    toolName: e.target.value
                                }
                            }))}
                            placeholder="e.g., dbt"
                        />
                    </label>
                    <label>
                        Tool Version
                        <input
                            type="text"
                            value={data.extractorMetadata?.toolVersion || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                extractorMetadata: {
                                    ...prev.extractorMetadata,
                                    type: prev.extractorMetadata?.type || 'MANUAL',
                                    toolVersion: e.target.value
                                }
                            }))}
                            placeholder="e.g., 1.0.0"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Review Metadata</h3>
                <div className="form-row">
                    <label>
                        Last Review Date
                        <input
                            type="date"
                            value={data.reviewMetadata?.lastReviewDate ? new Date(data.reviewMetadata.lastReviewDate).toISOString().split('T')[0] : ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                reviewMetadata: { ...prev.reviewMetadata, lastReviewDate: new Date(e.target.value).toISOString() }
                            }))}
                        />
                    </label>
                    <label>
                        Reviewer BRID
                        <input
                            type="text"
                            value={data.reviewMetadata?.lastReviewedByBrid || ''}
                            onChange={e => setData(prev => ({
                                ...prev,
                                reviewMetadata: { ...prev.reviewMetadata, lastReviewedByBrid: e.target.value }
                            }))}
                        />
                    </label>
                    <label>
                        Status
                        <select
                            value={data.reviewMetadata?.reviewStatus || 'PENDING'}
                            onChange={e => setData(prev => ({
                                ...prev,
                                reviewMetadata: { ...prev.reviewMetadata, reviewStatus: e.target.value as any }
                            }))}
                        >
                            <option value="PENDING">Pending</option>
                            <option value="APPROVED">Approved</option>
                            <option value="REJECTED">Rejected</option>
                        </select>
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

            <div className="form-section">
                <h3>Ownership</h3>
                {(data.ownership?.owners || []).map((owner, i) => (
                    <div key={i} className="form-row inline">
                        <input
                            type="text"
                            value={owner.name}
                            onChange={e => updateOwner(i, { name: e.target.value })}
                            placeholder="Owner name"
                        />
                        <select
                            value={owner.type}
                            onChange={e => updateOwner(i, { type: e.target.value as Owner['type'] })}
                        >
                            <option value="TEAM">Team</option>
                            <option value="PERSON">Person</option>
                            <option value="SERVICE">Service</option>
                        </select>
                        <input
                            type="text"
                            value={owner.brid || ''}
                            onChange={e => updateOwner(i, { brid: e.target.value })}
                            placeholder="BRID"
                            style={{ width: '80px' }}
                        />
                        <input
                            type="text"
                            value={owner.email || ''}
                            onChange={e => updateOwner(i, { email: e.target.value })}
                            placeholder="Email"
                        />
                        <button type="button" className="btn-small danger" onClick={() => removeOwner(i)}>×</button>
                    </div>
                ))}
                <button type="button" className="btn-secondary" onClick={addOwner}>+ Add Owner</button>
            </div>

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
                <button type="submit" className="btn-primary">Save Job</button>
            </div>
        </form>
    );
}
