import { useState, useCallback } from 'react';
import type { Dataset, Job, Application } from './types';
import { entityToYaml } from './types';
import { DatasetForm } from './components/DatasetForm';
import { JobForm } from './components/JobForm';
import { ApplicationForm } from './components/ApplicationForm';
import { LineagePreview } from './components/LineagePreview';
import { ExportPanel } from './components/ExportPanel';
import { ImportPanel } from './components/ImportPanel';
import './App.css';

function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);

  const [activeTab, setActiveTab] = useState<'applications' | 'datasets' | 'jobs' | 'preview' | 'export' | 'import'>('applications');

  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);

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

  const handleSaveApplication = useCallback((application: Application) => {
    setApplications(prev => {
      const existing = prev.findIndex(a => a.id === application.id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = application;
        return updated;
      }
      return [...prev, application];
    });
    setEditingApplication(null);
  }, []);

  const handleDeleteDataset = useCallback((id: string) => {
    setDatasets(prev => prev.filter(d => d.id !== id));
  }, []);

  const handleDeleteJob = useCallback((id: string) => {
    setJobs(prev => prev.filter(j => j.id !== id));
  }, []);

  const handleDeleteApplication = useCallback((id: string) => {
    setApplications(prev => prev.filter(a => a.id !== id));
  }, []);

  const handleExport = useCallback(() => {
    const files: { name: string; content: string }[] = [];

    for (const app of applications) {
      files.push({
        name: `application/${app.id.split('.').join('/')}.yaml`,
        content: entityToYaml(app)
      });
    }

    for (const dataset of datasets) {
      files.push({
        name: `dataset/${dataset.id.split('.').join('/')}.yaml`,
        content: entityToYaml(dataset)
      });
    }

    for (const job of jobs) {
      files.push({
        name: `jobs/${job.id.split('.').join('/')}.yaml`,
        content: entityToYaml(job)
      });
    }

    return files;
  }, [datasets, jobs, applications]);

  const handleImport = useCallback((newDatasets: Dataset[], newJobs: Job[], newApplications: Application[]) => {
    setDatasets(prev => {
      // Merge and avoid duplicates based on ID
      const existingIds = new Set(prev.map(d => d.id));
      const filteredNew = newDatasets.filter(d => !existingIds.has(d.id));
      return [...prev, ...filteredNew];
    });
    setJobs(prev => {
      const existingIds = new Set(prev.map(j => j.id));
      const filteredNew = newJobs.filter(j => !existingIds.has(j.id));
      return [...prev, ...filteredNew];
    });
    setApplications(prev => {
      const existingIds = new Set(prev.map(a => a.id));
      const filteredNew = newApplications.filter(a => !existingIds.has(a.id));
      return [...prev, ...filteredNew];
    });
    setActiveTab('applications');
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔗 Lineage Designer</h1>
        <p>Design OpenLineage YAML definitions visually</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'applications' ? 'active' : ''}
          onClick={() => setActiveTab('applications')}
        >
          📱 Applications ({applications.length})
        </button>
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
        {activeTab === 'applications' && (
          <div className="panel">
            {editingApplication ? (
              <ApplicationForm
                application={editingApplication}
                onSave={handleSaveApplication}
                onCancel={() => setEditingApplication(null)}
              />
            ) : (
              <>
                <button
                  className="btn-primary"
                  onClick={() => setEditingApplication({
                    id: '',
                    version: 1,
                    kind: 'application',
                    name: '',
                    tags: []
                  })}
                >
                  + New Application
                </button>
                <div className="item-list">
                  {applications.map(a => (
                    <div key={a.id} className="item-card">
                      <div className="item-info">
                        <strong>{a.id}</strong>
                        <span className="namespace">v{a.version}</span>
                        <span className="name">{a.name}</span>
                        <span className="field-count">{(a.jobs || []).length} jobs</span>
                      </div>
                      <div className="item-actions">
                        <button onClick={() => setEditingApplication(a)}>Edit</button>
                        <button className="danger" onClick={() => handleDeleteApplication(a.id)}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {applications.length === 0 && (
                    <p className="empty-state">No applications yet. Click "New Application" to create one.</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}

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
                    version: 1,
                    kind: 'dataset',
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
                        <span className="namespace">{d.structure?.schema || 'no-schema'}</span>
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
                    version: 1,
                    kind: 'job',
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
                        <span className="namespace">{j.applicationId || 'no-app'}</span>
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
            existingApplicationIds={applications.map(a => a.id)}
          />
        )}
      </main>
    </div>
  );
}

export default App;
