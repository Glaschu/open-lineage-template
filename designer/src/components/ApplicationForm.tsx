import { useState } from 'react';
import type { Application, ApplicationVersion, ApplicationEnvironment } from '../types';
import './forms.css';

interface ApplicationFormProps {
    application: Application;
    onSave: (application: Application) => void;
    onCancel: () => void;
}

export function ApplicationForm({ application, onSave, onCancel }: ApplicationFormProps) {
    const [data, setData] = useState<Application>(application);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!data.id.trim()) {
            setError('Application ID is required');
            return;
        }
        if (!data.name.trim()) {
            setError('Name is required');
            return;
        }

        onSave(data);
    };

    const addVersion = () => {
        setData(prev => ({
            ...prev,
            versions: [...(prev.versions || []), { version: '', releaseDate: '', changeLog: '' }]
        }));
    };

    const updateVersion = (index: number, version: Partial<ApplicationVersion>) => {
        setData(prev => {
            const newVersions = [...(prev.versions || [])];
            newVersions[index] = { ...newVersions[index], ...version };
            return { ...prev, versions: newVersions };
        });
    };

    const removeVersion = (index: number) => {
        setData(prev => ({
            ...prev,
            versions: (prev.versions || []).filter((_, i) => i !== index)
        }));
    };

    const addEnvironment = () => {
        setData(prev => ({
            ...prev,
            environments: [...(prev.environments || []), { name: '', url: '', description: '' }]
        }));
    };

    const updateEnvironment = (index: number, env: Partial<ApplicationEnvironment>) => {
        setData(prev => {
            const newEnvs = [...(prev.environments || [])];
            newEnvs[index] = { ...newEnvs[index], ...env };
            return { ...prev, environments: newEnvs };
        });
    };

    const removeEnvironment = (index: number) => {
        setData(prev => ({
            ...prev,
            environments: (prev.environments || []).filter((_, i) => i !== index)
        }));
    };

    return (
        <form className="form" onSubmit={handleSubmit}>
            <h2>{application.id ? 'Edit Application' : 'New Application'}</h2>

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
                            placeholder="e.g., Customer Portal"
                        />
                    </label>
                </div>
                <div className="form-row">
                    <label>
                        Description
                        <textarea
                            value={data.description || ''}
                            onChange={e => setData(prev => ({ ...prev, description: e.target.value }))}
                            placeholder="Application description"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Ownership</h3>
                <div className="form-row">
                    <label>
                        Owner Team
                        <input
                            type="text"
                            value={data.owner?.team || ''}
                            onChange={e => setData(prev => ({ ...prev, owner: { ...prev.owner, team: e.target.value } }))}
                            placeholder="e.g., CRM Team"
                        />
                    </label>
                    <label>
                        Owner BRID
                        <input
                            type="text"
                            value={data.owner?.brid || ''}
                            onChange={e => setData(prev => ({ ...prev, owner: { ...prev.owner, brid: e.target.value } }))}
                            placeholder="e.g., 123456"
                        />
                    </label>
                    <label>
                        Owner Email
                        <input
                            type="text"
                            value={data.owner?.email || ''}
                            onChange={e => setData(prev => ({ ...prev, owner: { ...prev.owner, email: e.target.value } }))}
                            placeholder="e.g., team@barclays.com"
                        />
                    </label>
                </div>
            </div>

            <div className="form-section">
                <h3>Versions</h3>
                {(data.versions || []).map((ver, i) => (
                    <div key={i} className="form-row inline">
                        <input
                            type="text"
                            value={ver.version}
                            onChange={e => updateVersion(i, { version: e.target.value })}
                            placeholder="Version e.g. 1.0.0"
                            style={{ width: '100px' }}
                        />
                        <input
                            type="date"
                            value={ver.releaseDate || ''}
                            onChange={e => updateVersion(i, { releaseDate: e.target.value })}
                        />
                        <input
                            type="text"
                            value={ver.changeLog || ''}
                            onChange={e => updateVersion(i, { changeLog: e.target.value })}
                            placeholder="Changelog URL or summary"
                        />
                        <button type="button" className="btn-small danger" onClick={() => removeVersion(i)}>×</button>
                    </div>
                ))}
                <button type="button" className="btn-secondary" onClick={addVersion}>+ Add Version</button>
            </div>

            <div className="form-section">
                <h3>Environments</h3>
                {(data.environments || []).map((env, i) => (
                    <div key={i} className="form-row inline">
                        <input
                            type="text"
                            value={env.name}
                            onChange={e => updateEnvironment(i, { name: e.target.value })}
                            placeholder="Env Name e.g. PROD"
                            style={{ width: '100px' }}
                        />
                        <input
                            type="text"
                            value={env.url || ''}
                            onChange={e => updateEnvironment(i, { url: e.target.value })}
                            placeholder="URL"
                        />
                        <input
                            type="text"
                            value={env.description || ''}
                            onChange={e => updateEnvironment(i, { description: e.target.value })}
                            placeholder="Description"
                        />
                        <button type="button" className="btn-small danger" onClick={() => removeEnvironment(i)}>×</button>
                    </div>
                ))}
                <button type="button" className="btn-secondary" onClick={addEnvironment}>+ Add Environment</button>
            </div>

            <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
                <button type="submit" className="btn-primary">Save Application</button>
            </div>
        </form>
    );
}
