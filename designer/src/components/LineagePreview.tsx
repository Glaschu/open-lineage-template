import type { Dataset, Job } from '../types';
import './preview.css';

interface LineagePreviewProps {
    datasets: Dataset[];
    jobs: Job[];
}

export function LineagePreview({ datasets, jobs }: LineagePreviewProps) {
    const getDatasetById = (id: string) => datasets.find(d => d.id === id);

    return (
        <div className="preview-panel">
            <h2>Lineage Overview</h2>

            {datasets.length === 0 && jobs.length === 0 ? (
                <p className="empty-state">No lineage defined yet. Create datasets and jobs to see the preview.</p>
            ) : (
                <div className="lineage-diagram">
                    {jobs.map(job => {
                        const inputs = job.inputs.map(i => getDatasetById(i.ref)).filter(Boolean) as Dataset[];
                        const outputs = job.outputs.map(o => getDatasetById(o.ref)).filter(Boolean) as Dataset[];

                        return (
                            <div key={job.id} className="job-flow">
                                <div className="flow-column inputs">
                                    <h4>Inputs</h4>
                                    {inputs.map(ds => (
                                        <div key={ds.id} className="dataset-node">
                                            <div className="node-header">{ds.id}</div>
                                            <div className="node-body">
                                                {ds.schema.fields.slice(0, 5).map(f => (
                                                    <div key={f.name} className="field-item">{f.name}</div>
                                                ))}
                                                {ds.schema.fields.length > 5 && (
                                                    <div className="more-fields">+{ds.schema.fields.length - 5} more</div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="flow-column job">
                                    <div className="job-node">
                                        <div className="node-header">{job.name}</div>
                                        <div className="node-body">
                                            <span className="job-type">{job.jobType?.processingType || 'BATCH'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flow-column outputs">
                                    <h4>Outputs</h4>
                                    {outputs.map(ds => {
                                        const outputDef = job.outputs.find(o => o.ref === ds.id);
                                        const hasLineage = outputDef?.columnLineage && Object.keys(outputDef.columnLineage).length > 0;

                                        return (
                                            <div key={ds.id} className={`dataset-node ${hasLineage ? 'has-lineage' : ''}`}>
                                                <div className="node-header">
                                                    {ds.id}
                                                    {hasLineage && <span className="lineage-badge">📊</span>}
                                                </div>
                                                <div className="node-body">
                                                    {ds.schema.fields.slice(0, 5).map(f => (
                                                        <div key={f.name} className="field-item">{f.name}</div>
                                                    ))}
                                                    {ds.schema.fields.length > 5 && (
                                                        <div className="more-fields">+{ds.schema.fields.length - 5} more</div>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}

                    {/* Unused datasets */}
                    {(() => {
                        const usedIds = new Set([
                            ...jobs.flatMap(j => [...j.inputs.map(i => i.ref), ...j.outputs.map(o => o.ref)])
                        ]);
                        const unused = datasets.filter(d => !usedIds.has(d.id));

                        if (unused.length === 0) return null;

                        return (
                            <div className="unused-datasets">
                                <h4>Unlinked Datasets</h4>
                                <div className="unused-list">
                                    {unused.map(ds => (
                                        <div key={ds.id} className="dataset-node unused">
                                            <div className="node-header">{ds.id}</div>
                                            <div className="node-subtitle">{ds.name}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })()}
                </div>
            )}
        </div>
    );
}
