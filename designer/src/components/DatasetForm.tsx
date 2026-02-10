import { useState } from 'react';
import type { Dataset, SchemaField, Owner } from '../types';
import './forms.css';

interface DatasetFormProps {
    dataset: Dataset;
    onSave: (dataset: Dataset) => void;
    onCancel: () => void;
}

export function DatasetForm({ dataset, onSave, onCancel }: DatasetFormProps) {
    const [data, setData] = useState<Dataset>(dataset);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!data.id.trim()) {
            setError('Dataset ID is required');
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

        onSave(data);
    };

    const addField = () => {
        setData(prev => ({
            ...prev,
            schema: {
                ...prev.schema,
                fields: [...prev.schema.fields, { name: '', type: 'string' }]
            }
        }));
    };

    const updateField = (index: number, field: Partial<SchemaField>) => {
        setData(prev => ({
            ...prev,
            schema: {
                ...prev.schema,
                fields: prev.schema.fields.map((f, i) =>
                    i === index ? { ...f, ...field } : f
                )
            }
        }));
    };

    const removeField = (index: number) => {
        setData(prev => ({
            ...prev,
            schema: {
                ...prev.schema,
                fields: prev.schema.fields.filter((_, i) => i !== index)
            }
        }));
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

    return (
        <form className="form" onSubmit={handleSubmit}>
            <h2>{dataset.id ? 'Edit Dataset' : 'New Dataset'}</h2>

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
                            placeholder="e.g., raw_users"
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
                            placeholder='e.g., postgres://host:5432'
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
                            placeholder="e.g., public.users"
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Description
                        <textarea
                            value={data.description || ''}
                            onChange={e => setData(prev => ({ ...prev, description: e.target.value }))}
                            placeholder="Human-readable description"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Schema Fields</h3>
                <table className="fields-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Description</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.schema.fields.map((field, i) => (
                            <tr key={i}>
                                <td>
                                    <input
                                        type="text"
                                        value={field.name}
                                        onChange={e => updateField(i, { name: e.target.value })}
                                        placeholder="field_name"
                                    />
                                </td>
                                <td>
                                    <select
                                        value={field.type}
                                        onChange={e => updateField(i, { type: e.target.value })}
                                    >
                                        <option value="string">string</option>
                                        <option value="integer">integer</option>
                                        <option value="boolean">boolean</option>
                                        <option value="timestamp">timestamp</option>
                                        <option value="date">date</option>
                                        <option value="decimal(10,2)">decimal</option>
                                        <option value="varchar(255)">varchar</option>
                                    </select>
                                </td>
                                <td>
                                    <input
                                        type="text"
                                        value={field.description || ''}
                                        onChange={e => updateField(i, { description: e.target.value })}
                                        placeholder="optional"
                                    />
                                </td>
                                <td>
                                    <button type="button" className="btn-small danger" onClick={() => removeField(i)}>×</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <button type="button" className="btn-secondary" onClick={addField}>+ Add Field</button>
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
                        <button type="button" className="btn-small danger" onClick={() => removeOwner(i)}>×</button>
                    </div>
                ))}
                <button type="button" className="btn-secondary" onClick={addOwner}>+ Add Owner</button>
            </div>

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
                <button type="submit" className="btn-primary">Save Dataset</button>
            </div>
        </form>
    );
}
