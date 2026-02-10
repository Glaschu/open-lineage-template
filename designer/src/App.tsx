import { useState, useCallback } from 'react';
import type { Dataset, Job } from './types';
import { datasetToYaml, jobToYaml } from './types';
import { DatasetForm } from './components/DatasetForm';
import { JobForm } from './components/JobForm';
import { LineagePreview } from './components/LineagePreview';
import { ExportPanel } from './components/ExportPanel';
import { ImportPanel } from './components/ImportPanel';
import './App.css';

function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState<'datasets' | 'jobs' | 'preview' | 'export' | 'import'>('datasets');
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  const handleSaveDataset = useCallback((dataset: Dataset) => {
    setDatasets(prev => {
      const existing = prev.findIndex(d => d.id === dataset.id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = dataset;
        return updated;
      }
      return [...prev, dataset];
    });
    setEditingDataset(null);
  }, []);

  const handleSaveJob = useCallback((job: Job) => {
    setJobs(prev => {
      const existing = prev.findIndex(j => j.id === job.id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = job;
        return updated;
      }
      return [...prev, job];
    });
    setEditingJob(null);
  }, []);

  const handleDeleteDataset = useCallback((id: string) => {
    setDatasets(prev => prev.filter(d => d.id !== id));
  }, []);

  const handleDeleteJob = useCallback((id: string) => {
    setJobs(prev => prev.filter(j => j.id !== id));
  }, []);

  const handleExport = useCallback(() => {
    const files: { name: string; content: string }[] = [];

    for (const dataset of datasets) {
      files.push({
        name: `datasets/${dataset.id}.yaml`,
        content: datasetToYaml(dataset)
      });
    }

    for (const job of jobs) {
      files.push({
        name: `jobs/${job.id}.yaml`,
        content: jobToYaml(job)
      });
    }

    return files;
  }, [datasets, jobs]);

  const handleImport = useCallback((newDatasets: Dataset[], newJobs: Job[]) => {
    setDatasets(prev => [...prev, ...newDatasets]);
    setJobs(prev => [...prev, ...newJobs]);
    setActiveTab('datasets');
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔗 Lineage Designer</h1>
        <p>Design OpenLineage YAML definitions visually</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'datasets' ? 'active' : ''}
          onClick={() => setActiveTab('datasets')}
        >
          📦 Datasets ({datasets.length})
        </button>
        <button
          className={activeTab === 'jobs' ? 'active' : ''}
          onClick={() => setActiveTab('jobs')}
        >
          ⚙️ Jobs ({jobs.length})
        </button>
        <button
          className={activeTab === 'preview' ? 'active' : ''}
          onClick={() => setActiveTab('preview')}
        >
          👁️ Preview
        </button>
        <button
          className={activeTab === 'export' ? 'active' : ''}
          onClick={() => setActiveTab('export')}
        >
          📤 Export
        </button>
        <button
          className={activeTab === 'import' ? 'active' : ''}
          onClick={() => setActiveTab('import')}
        >
          📥 Import
        </button>
      </nav>

      <main className="content">
        {activeTab === 'datasets' && (
          <div className="panel">
            {editingDataset ? (
              <DatasetForm
                dataset={editingDataset}
                onSave={handleSaveDataset}
                onCancel={() => setEditingDataset(null)}
              />
            ) : (
              <>
                <button
                  className="btn-primary"
                  onClick={() => setEditingDataset({
                    id: '',
                    namespace: '',
                    name: '',
                    schema: { fields: [] }
                  })}
                >
                  + New Dataset
                </button>
                <div className="item-list">
                  {datasets.map(d => (
                    <div key={d.id} className="item-card">
                      <div className="item-info">
                        <strong>{d.id}</strong>
                        <span className="namespace">{d.namespace}</span>
                        <span className="name">{d.name}</span>
                        <span className="field-count">{d.schema.fields.length} fields</span>
                      </div>
                      <div className="item-actions">
                        <button onClick={() => setEditingDataset(d)}>Edit</button>
                        <button className="danger" onClick={() => handleDeleteDataset(d.id)}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {datasets.length === 0 && (
                    <p className="empty-state">No datasets yet. Click "New Dataset" to create one.</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="panel">
            {editingJob ? (
              <JobForm
                job={editingJob}
                datasets={datasets}
                onSave={handleSaveJob}
                onCancel={() => setEditingJob(null)}
              />
            ) : (
              <>
                <button
                  className="btn-primary"
                  onClick={() => setEditingJob({
                    id: '',
                    namespace: '',
                    name: '',
                    inputs: [],
                    outputs: []
                  })}
                >
                  + New Job
                </button>
                <div className="item-list">
                  {jobs.map(j => (
                    <div key={j.id} className="item-card">
                      <div className="item-info">
                        <strong>{j.id}</strong>
                        <span className="namespace">{j.namespace}</span>
                        <span className="name">{j.name}</span>
                        <span className="io-count">{j.inputs.length} in → {j.outputs.length} out</span>
                      </div>
                      <div className="item-actions">
                        <button onClick={() => setEditingJob(j)}>Edit</button>
                        <button className="danger" onClick={() => handleDeleteJob(j.id)}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {jobs.length === 0 && (
                    <p className="empty-state">No jobs yet. Create datasets first, then add jobs.</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'preview' && (
          <LineagePreview datasets={datasets} jobs={jobs} />
        )}

        {activeTab === 'export' && (
          <ExportPanel files={handleExport()} />
        )}

        {activeTab === 'import' && (
          <ImportPanel
            onImport={handleImport}
            existingDatasetIds={datasets.map(d => d.id)}
            existingJobIds={jobs.map(j => j.id)}
          />
        )}
      </main>
    </div>
  );
}

export default App;
