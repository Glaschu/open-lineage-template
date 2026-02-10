import { useState } from 'react';
import type { Dataset, ColumnMapping } from '../types';
import './forms.css';

interface ColumnLineageEditorProps {
    outputDataset: Dataset;
    inputDatasets: Dataset[];
    existingLineage: Record<string, ColumnMapping[]>;
    onSave: (lineage: Record<string, ColumnMapping[]>) => void;
    onCancel: () => void;
}

export function ColumnLineageEditor({
    outputDataset,
    inputDatasets,
    existingLineage,
    onSave,
    onCancel
}: ColumnLineageEditorProps) {
    const [lineage, setLineage] = useState<Record<string, ColumnMapping[]>>(existingLineage);

    const outputFields = outputDataset.schema?.fields || [];
    const allInputFields = inputDatasets.flatMap(ds =>
        (ds.schema?.fields || []).map(f => ({
            dataset: ds.id,
            field: f.name,
            type: f.type
        }))
    );

    const addMapping = (outputField: string) => {
        if (allInputFields.length === 0) return;

        const firstInput = allInputFields[0];
        const newMapping: ColumnMapping = {
            inputField: firstInput.field,
            inputDataset: firstInput.dataset,
            transformation: 'IDENTITY'
        };

        setLineage(prev => ({
            ...prev,
            [outputField]: [...(prev[outputField] || []), newMapping]
        }));
    };

    const updateMapping = (outputField: string, index: number, updates: Partial<ColumnMapping>) => {
        setLineage(prev => ({
            ...prev,
            [outputField]: (prev[outputField] || []).map((m, i) =>
                i === index ? { ...m, ...updates } : m
            )
        }));
    };

    const removeMapping = (outputField: string, index: number) => {
        setLineage(prev => ({
            ...prev,
            [outputField]: (prev[outputField] || []).filter((_, i) => i !== index)
        }));
    };

    const handleSave = () => {
        // Remove empty mappings
        const cleaned = Object.fromEntries(
            Object.entries(lineage).filter(([_, mappings]) => mappings.length > 0)
        );
        onSave(cleaned);
    };

    return (
        <div className="form column-lineage-form">
            <h2>Column Lineage</h2>
            <p className="subtitle">
                Map input fields to output fields for <strong>{outputDataset.id}</strong>
            </p>

            {inputDatasets.length === 0 && (
                <div className="warning-message">
                    No input datasets selected. Add input datasets to the job first.
                </div>
            )}

            <div className="lineage-grid">
                {outputFields.map(outputField => (
                    <div key={outputField.name} className="lineage-row">
                        <div className="output-field">
                            <strong>{outputField.name}</strong>
                            <span className="field-type">{outputField.type}</span>
                        </div>
                        <div className="arrow">←</div>
                        <div className="input-mappings">
                            {(lineage[outputField.name] || []).map((mapping, i) => (
                                <div key={i} className="mapping-item">
                                    <select
                                        value={`${mapping.inputDataset}.${mapping.inputField}`}
                                        onChange={e => {
                                            const [dataset, ...fieldParts] = e.target.value.split('.');
                                            updateMapping(outputField.name, i, {
                                                inputDataset: dataset,
                                                inputField: fieldParts.join('.')
                                            });
                                        }}
                                    >
                                        {allInputFields.map(f => (
                                            <option key={`${f.dataset}.${f.field}`} value={`${f.dataset}.${f.field}`}>
                                                {f.dataset}.{f.field}
                                            </option>
                                        ))}
                                    </select>
                                    <select
                                        value={mapping.transformation}
                                        onChange={e => updateMapping(outputField.name, i, {
                                            transformation: e.target.value as ColumnMapping['transformation']
                                        })}
                                        className="transform-select"
                                    >
                                        <option value="IDENTITY">IDENTITY</option>
                                        <option value="TRANSFORM">TRANSFORM</option>
                                        <option value="AGGREGATE">AGGREGATE</option>
                                        <option value="FILTER">FILTER</option>
                                    </select>
                                    <input
                                        type="text"
                                        value={mapping.description || ''}
                                        onChange={e => updateMapping(outputField.name, i, { description: e.target.value })}
                                        placeholder="Description (optional)"
                                        className="description-input"
                                    />
                                    <label className="masking-label">
                                        <input
                                            type="checkbox"
                                            checked={mapping.masking || false}
                                            onChange={e => updateMapping(outputField.name, i, { masking: e.target.checked })}
                                        />
                                        Masked
                                    </label>
                                    <button
                                        type="button"
                                        className="btn-small danger"
                                        onClick={() => removeMapping(outputField.name, i)}
                                    >
                                        ×
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                className="btn-small"
                                onClick={() => addMapping(outputField.name)}
                                disabled={allInputFields.length === 0}
                            >
                                + Add Source
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {outputFields.length === 0 && (
                <p className="hint">
                    The output dataset has no schema fields. Add fields to the dataset first.
                </p>
            )}

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
                <button type="button" className="btn-primary" onClick={handleSave}>Save Column Lineage</button>
            </div>
        </div>
    );
}
