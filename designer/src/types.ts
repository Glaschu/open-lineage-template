// Lineage Designer Types
// Shared types for datasets, jobs, and column lineage

export interface SchemaField {
    name: string;
    type: string;
    description?: string;
}

export interface Owner {
    name: string;
    type: 'PERSON' | 'TEAM' | 'SERVICE';
}

export interface Dataset {
    id: string;
    namespace: string;
    name: string;
    schema: {
        fields: SchemaField[];
    };
    ownership?: {
        owners: Owner[];
    };
    dataSource?: {
        name: string;
        uri: string;
    };
    description?: string;
    tags?: string[];
}

export interface ColumnMapping {
    inputField: string;
    inputDataset: string;
    transformation: 'IDENTITY' | 'TRANSFORM' | 'AGGREGATE' | 'FILTER';
    description?: string;
    masking?: boolean;
}

export interface ColumnLineage {
    [outputField: string]: ColumnMapping[];
}

export interface JobOutput {
    ref: string;
    columnLineage?: ColumnLineage;
}

export interface JobInput {
    ref: string;
}

export interface Job {
    id: string;
    namespace: string;
    name: string;
    jobType?: {
        processingType: 'BATCH' | 'STREAMING' | 'SERVICE';
        integration?: string;
        jobType?: string;
    };
    documentation?: {
        description: string;
        contentType?: string;
    };
    inputs: JobInput[];
    outputs: JobOutput[];
}

export interface LineageProject {
    datasets: Dataset[];
    jobs: Job[];
}

// YAML export format
export function datasetToYaml(dataset: Dataset): string {
    const lines: string[] = [
        `version: 1`,
        `kind: dataset`,
        `id: ${dataset.id}`,
        ``,
        `namespace: "${dataset.namespace}"`,
        `name: "${dataset.name}"`,
    ];

    if (dataset.schema?.fields?.length) {
        lines.push(``);
        lines.push(`schema:`);
        lines.push(`  fields:`);
        for (const field of dataset.schema.fields) {
            lines.push(`    - name: ${field.name}`);
            lines.push(`      type: ${field.type}`);
            if (field.description) {
                lines.push(`      description: "${field.description}"`);
            }
        }
    }

    if (dataset.ownership?.owners?.length) {
        lines.push(``);
        lines.push(`ownership:`);
        lines.push(`  owners:`);
        for (const owner of dataset.ownership.owners) {
            lines.push(`    - name: ${owner.name}`);
            lines.push(`      type: ${owner.type}`);
        }
    }

    if (dataset.description) {
        lines.push(``);
        lines.push(`description: "${dataset.description}"`);
    }

    if (dataset.tags?.length) {
        lines.push(``);
        lines.push(`tags:`);
        for (const tag of dataset.tags) {
            lines.push(`  - ${tag}`);
        }
    }

    return lines.join('\n');
}

export function jobToYaml(job: Job): string {
    const lines: string[] = [
        `version: 1`,
        `kind: job`,
        `id: ${job.id}`,
        ``,
        `namespace: ${job.namespace}`,
        `name: ${job.name}`,
    ];

    if (job.jobType) {
        lines.push(``);
        lines.push(`jobType:`);
        lines.push(`  processingType: ${job.jobType.processingType}`);
        if (job.jobType.integration) {
            lines.push(`  integration: ${job.jobType.integration}`);
        }
        if (job.jobType.jobType) {
            lines.push(`  jobType: ${job.jobType.jobType}`);
        }
    }

    if (job.documentation?.description) {
        lines.push(``);
        lines.push(`documentation:`);
        lines.push(`  description: "${job.documentation.description}"`);
    }

    if (job.inputs?.length) {
        lines.push(``);
        lines.push(`inputs:`);
        for (const input of job.inputs) {
            lines.push(`  - ref: ${input.ref}`);
        }
    }

    if (job.outputs?.length) {
        lines.push(``);
        lines.push(`outputs:`);
        for (const output of job.outputs) {
            lines.push(`  - ref: ${output.ref}`);
            if (output.columnLineage && Object.keys(output.columnLineage).length > 0) {
                lines.push(`    columnLineage:`);
                for (const [outputField, mappings] of Object.entries(output.columnLineage)) {
                    lines.push(`      ${outputField}:`);
                    for (const mapping of mappings) {
                        lines.push(`        - inputField: ${mapping.inputField}`);
                        lines.push(`          inputDataset: ${mapping.inputDataset}`);
                        lines.push(`          transformation: ${mapping.transformation}`);
                        if (mapping.description) {
                            lines.push(`          description: "${mapping.description}"`);
                        }
                        if (mapping.masking) {
                            lines.push(`          masking: true`);
                        }
                    }
                }
            }
        }
    }

    return lines.join('\n');
}

// YAML import functions
import yaml from 'js-yaml';

export interface ImportResult {
    datasets: Dataset[];
    jobs: Job[];
    errors: string[];
}

export function parseYamlContent(content: string, filename: string): ImportResult {
    const result: ImportResult = { datasets: [], jobs: [], errors: [] };

    try {
        const parsed = yaml.load(content) as Record<string, unknown>;

        if (!parsed || typeof parsed !== 'object') {
            result.errors.push(`${filename}: Invalid YAML content`);
            return result;
        }

        const kind = parsed.kind as string;

        if (kind === 'dataset') {
            const dataset = parseDatasetYaml(parsed, filename);
            if (dataset) {
                result.datasets.push(dataset);
            } else {
                result.errors.push(`${filename}: Failed to parse dataset`);
            }
        } else if (kind === 'job') {
            const job = parseJobYaml(parsed, filename);
            if (job) {
                result.jobs.push(job);
            } else {
                result.errors.push(`${filename}: Failed to parse job`);
            }
        } else {
            result.errors.push(`${filename}: Unknown kind "${kind}". Expected "dataset" or "job"`);
        }
    } catch (e) {
        result.errors.push(`${filename}: ${(e as Error).message}`);
    }

    return result;
}

function parseDatasetYaml(data: Record<string, unknown>, filename: string): Dataset | null {
    const id = (data.id as string) || filename.replace(/\.ya?ml$/i, '');
    const namespace = data.namespace as string;
    const name = data.name as string;

    if (!namespace || !name) {
        return null;
    }

    const dataset: Dataset = {
        id,
        namespace,
        name,
        schema: { fields: [] }
    };

    // Parse schema
    const schema = data.schema as { fields?: Array<{ name: string; type: string; description?: string }> };
    if (schema?.fields) {
        dataset.schema.fields = schema.fields.map(f => ({
            name: f.name,
            type: f.type,
            description: f.description
        }));
    }

    // Parse ownership
    const ownership = data.ownership as { owners?: Array<{ name: string; type: string }> };
    if (ownership?.owners) {
        dataset.ownership = {
            owners: ownership.owners.map(o => ({
                name: o.name,
                type: o.type as 'PERSON' | 'TEAM' | 'SERVICE'
            }))
        };
    }

    // Parse description
    if (data.description) {
        dataset.description = data.description as string;
    }

    // Parse tags
    if (data.tags && Array.isArray(data.tags)) {
        dataset.tags = data.tags as string[];
    }

    return dataset;
}

function parseJobYaml(data: Record<string, unknown>, filename: string): Job | null {
    const id = (data.id as string) || filename.replace(/\.ya?ml$/i, '');
    const namespace = data.namespace as string;
    const name = data.name as string;

    if (!namespace || !name) {
        return null;
    }

    const job: Job = {
        id,
        namespace,
        name,
        inputs: [],
        outputs: []
    };

    // Parse jobType
    const jobType = data.jobType as { processingType?: string; integration?: string; jobType?: string };
    if (jobType) {
        job.jobType = {
            processingType: (jobType.processingType as 'BATCH' | 'STREAMING' | 'SERVICE') || 'BATCH',
            integration: jobType.integration,
            jobType: jobType.jobType
        };
    }

    // Parse documentation
    const documentation = data.documentation as { description?: string };
    if (documentation?.description) {
        job.documentation = { description: documentation.description };
    }

    // Parse inputs
    const inputs = data.inputs as Array<{ ref: string }>;
    if (inputs && Array.isArray(inputs)) {
        job.inputs = inputs.map(i => ({ ref: i.ref }));
    }

    // Parse outputs with column lineage
    const outputs = data.outputs as Array<{ ref: string; columnLineage?: Record<string, unknown[]> }>;
    if (outputs && Array.isArray(outputs)) {
        job.outputs = outputs.map(o => {
            const output: JobOutput = { ref: o.ref };

            if (o.columnLineage) {
                output.columnLineage = {};
                for (const [field, mappings] of Object.entries(o.columnLineage)) {
                    output.columnLineage[field] = (mappings as Array<{
                        inputField: string;
                        inputDataset: string;
                        transformation?: string;
                        description?: string;
                        masking?: boolean;
                    }>).map(m => ({
                        inputField: m.inputField,
                        inputDataset: m.inputDataset,
                        transformation: (m.transformation as 'IDENTITY' | 'TRANSFORM' | 'AGGREGATE' | 'FILTER') || 'IDENTITY',
                        description: m.description,
                        masking: m.masking
                    }));
                }
            }

            return output;
        });
    }

    return job;
}

export function parseMultipleYamlFiles(files: Array<{ name: string; content: string }>): ImportResult {
    const combined: ImportResult = { datasets: [], jobs: [], errors: [] };

    for (const file of files) {
        const result = parseYamlContent(file.content, file.name);
        combined.datasets.push(...result.datasets);
        combined.jobs.push(...result.jobs);
        combined.errors.push(...result.errors);
    }

    return combined;
}
