import { useState } from 'react';
import type { Dataset, SchemaField, Owner, CdeLink } from '../types';
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

    const addCdeLink = () => {
        setData(prev => ({
            ...prev,
            cdeLinks: [...(prev.cdeLinks || []), { cdeId: '', cdeName: '', cdeUrl: '', mappingType: 'Direct' }]
        }));
    };

    const updateCdeLink = (index: number, link: Partial<CdeLink>) => {
        setData(prev => {
            const newLinks = [...(prev.cdeLinks || [])];
            newLinks[index] = { ...newLinks[index], ...link };
            return { ...prev, cdeLinks: newLinks };
        });
    };

    const removeCdeLink = (index: number) => {
        setData(prev => ({
            ...prev,
            cdeLinks: (prev.cdeLinks || []).filter((_, i) => i !== index)
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
                            onChange={e => setData(prev => ({ ...prev, id: e.target.value.replace(/[^a-zA-Z0-9_.-]/g, '_') }))}
                            placeholder="e.g., crm.customer_master"
                        />
                    </label>
                    <label>
                        Environment
                        <input
                            type="text"
                            value={data.environment || ''}
                            onChange={e => setData(prev => ({ ...prev, environment: e.target.value }))}
                            placeholder="e.g., PROD"
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
                            placeholder="e.g., Customer Master"
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
                <h3>System & Structure</h3>
                <div className="form-row">
                    <label>
                        System Name
                        <input
                            type="text"
                            value={data.system?.name || ''}
                            onChange={e => setData(prev => ({ ...prev, system: { ...prev.system, name: e.target.value } as any }))}
                            placeholder="e.g., Snowflake"
                        />
                    </label>
                    <label>
                        System Type
                        <input
                            type="text"
                            value={data.system?.type || ''}
                            onChange={e => setData(prev => ({ ...prev, system: { ...prev.system, type: e.target.value } as any }))}
                            placeholder="e.g., DataWarehouse"
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Database
                        <input
                            type="text"
                            value={data.structure?.database || ''}
                            onChange={e => setData(prev => ({ ...prev, structure: { ...prev.structure, database: e.target.value } as any }))}
                        />
                    </label>
                    <label>
                        Schema
                        <input
                            type="text"
                            value={data.structure?.schema || ''}
                            onChange={e => setData(prev => ({ ...prev, structure: { ...prev.structure, schema: e.target.value } as any }))}
                        />
                    </label>
                    <label>
                        Table
                        <input
                            type="text"
                            value={data.structure?.table || ''}
                            onChange={e => setData(prev => ({ ...prev, structure: { ...prev.structure, table: e.target.value } as any }))}
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Catalogue & CDE</h3>
                <div className="form-row">
                    <label>
                        Alation ID
                        <input
                            type="text"
                            value={data.catalogueReference?.alationId || ''}
                            onChange={e => setData(prev => ({ ...prev, catalogueReference: { ...prev.catalogueReference, alationId: e.target.value } }))}
                        />
                    </label>
                    <label>
                        Alation URL
                        <input
                            type="text"
                            value={data.catalogueReference?.catalogueUrl || ''}
                            onChange={e => setData(prev => ({ ...prev, catalogueReference: { ...prev.catalogueReference, catalogueUrl: e.target.value } }))}
                        />
                    </label>
                </div>

                <h4>CDE Links</h4>
                {(data.cdeLinks || []).map((link, i) => (
                    <div key={i} className="form-row inline">
                        <input
                            type="text"
                            value={link.cdeId}
                            onChange={e => updateCdeLink(i, { cdeId: e.target.value })}
                            placeholder="CDE ID"
                        />
                        <input
                            type="text"
                            value={link.cdeName}
                            onChange={e => updateCdeLink(i, { cdeName: e.target.value })}
                            placeholder="CDE Name"
                        />
                        <select
                            value={link.mappingType}
                            onChange={e => updateCdeLink(i, { mappingType: e.target.value })}
                        >
                            <option value="Direct">Direct</option>
                            <option value="Derived">Derived</option>
                        </select>
                        <button type="button" className="btn-small danger" onClick={() => removeCdeLink(i)}>×</button>
                    </div>
                ))}
                <button type="button" className="btn-secondary" onClick={addCdeLink}>+ Add CDE Link</button>
            </div>

            <div className="form-section">
                <h3>Data Quality & Freshness</h3>
                <div className="form-row">
                    <label>
                        Completeness %
                        <input
                            type="number"
                            value={data.dataQuality?.completeness || ''}
                            onChange={e => setData(prev => ({ ...prev, dataQuality: { ...prev.dataQuality, completeness: Number(e.target.value) } }))}
                        />
                    </label>
                    <label>
                        Accuracy %
                        <input
                            type="number"
                            value={data.dataQuality?.accuracy || ''}
                            onChange={e => setData(prev => ({ ...prev, dataQuality: { ...prev.dataQuality, accuracy: Number(e.target.value) } }))}
                        />
                    </label>
                    <label>
                        Last Checked
                        <input
                            type="date"
                            value={data.dataQuality?.lastChecked ? new Date(data.dataQuality.lastChecked).toISOString().split('T')[0] : ''}
                            onChange={e => setData(prev => ({ ...prev, dataQuality: { ...prev.dataQuality, lastChecked: new Date(e.target.value).toISOString() } }))}
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Last Updated
                        <input
                            type="date"
                            value={data.freshness?.lastUpdated ? new Date(data.freshness.lastUpdated).toISOString().split('T')[0] : ''}
                            onChange={e => setData(prev => ({ ...prev, freshness: { ...prev.freshness, lastUpdated: new Date(e.target.value).toISOString() } }))}
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
                <button type="submit" className="btn-primary">Save Dataset</button>
            </div>
        </form>
    );
}
