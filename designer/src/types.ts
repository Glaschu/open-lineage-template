// Lineage Designer Types
// Shared types for applications, datasets, jobs, and column lineage

export interface SchemaField {
    name: string;
    type: string;
    description?: string;
}

export interface Owner {
    name: string;
    type: 'PERSON' | 'TEAM' | 'SERVICE';
    brid?: string;
    email?: string;
}

export interface CdeLink {
    cdeId: string;
    cdeName: string;
    cdeUrl: string;
    mappingType: string;
}

export interface DataQuality {
    completeness?: number;
    accuracy?: number;
    lastChecked?: string;
    reportUrl?: string;
}

export interface Dataset {
    id: string; // e.g., crm.customer_master
    version: number;
    kind: 'dataset';

    name: string;
    description?: string;
    environment?: string;

    system?: {
        name: string;
        type: string;
    };

    structure?: {
        database?: string;
        schema?: string;
        table?: string;
        namespace?: string;
    };

    schema: {
        fields: SchemaField[];
    };

    catalogueReference?: {
        alationId?: string;
        catalogueUrl?: string;
        certificationType?: string;
    };

    cdeLinks?: CdeLink[];

    ownership?: {
        owners: Owner[];
    };

    freshness?: {
        lastUpdated?: string;
        updateFrequency?: string;
    };

    dataQuality?: DataQuality;

    tags?: string[];
}

export interface ApplicationVersion {
    version: string;
    releaseDate?: string;
    changeLog?: string;
}

export interface ApplicationEnvironment {
    name: string;
    url?: string;
    description?: string;
}

export interface Application {
    id: string; // e.g., crm.customer_portal
    version: number;
    kind: 'application';

    name: string;
    description?: string;

    owner?: {
        team?: string;
        brid?: string;
        email?: string;
    };

    versions?: ApplicationVersion[];
    environments?: ApplicationEnvironment[];

    jobs?: { ref: string }[]; // List of job IDs

    tags?: string[];
}

export interface ColumnMapping {
    inputField: string;
    inputDataset: string;
    transformation: string;
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

export interface ExtractorMetadata {
    type: 'MANUAL' | '3RD_PARTY_TOOL' | 'GEN_AI' | string;
    confidence?: number;
    toolName?: string;
    toolVersion?: string;
}

export interface ReviewMetadata {
    lastReviewDate?: string;
    lastReviewedByBrid?: string;
    reviewStatus?: string;
}

export interface Job {
    id: string; // e.g., etl.customer_consolidation
    version: number;
    kind: 'job';

    name: string;
    description?: string;
    jobPath?: string;
    enabled?: boolean;

    applicationId?: string; // Reference to Application ID

    execution?: {
        type: 'BATCH' | 'STREAMING' | string;
        schedule?: string;
    };

    inputs: JobInput[];
    outputs: JobOutput[];

    extractorMetadata?: ExtractorMetadata;
    reviewMetadata?: ReviewMetadata;

    ownership?: {
        owners: Owner[];
    };

    tags?: string[];
}

export type LineageEntity = Dataset | Job | Application;

export interface LineageProject {
    applications: Application[];
    datasets: Dataset[];
    jobs: Job[];
}

import yaml from 'js-yaml';
import { dump } from 'js-yaml';

export interface ImportResult {
    applications: Application[];
    datasets: Dataset[];
    jobs: Job[];
    errors: string[];
}

export function parseYamlContent(content: string, filename: string): ImportResult {
    const result: ImportResult = { applications: [], datasets: [], jobs: [], errors: [] };

    try {
        const parsed = yaml.load(content) as Record<string, unknown>;

        if (!parsed || typeof parsed !== 'object') {
            result.errors.push(`${filename}: Invalid YAML content`);
            return result;
        }

        const kind = parsed.kind as string;

        if (kind === 'dataset') {
            // We cast because manual validation would be verbose, but in prod we should validate
            const dataset = parsed as unknown as Dataset;
            // Ensure ID exists
            if (!dataset.id) dataset.id = filename.replace(/\.ya?ml$/i, '');
            result.datasets.push(dataset);
        } else if (kind === 'job') {
            const job = parsed as unknown as Job;
            if (!job.id) job.id = filename.replace(/\.ya?ml$/i, '');
            result.jobs.push(job);
        } else if (kind === 'application') {
            const app = parsed as unknown as Application;
            if (!app.id) app.id = filename.replace(/\.ya?ml$/i, '');
            result.applications.push(app);
        } else {
            result.errors.push(`${filename}: Unknown kind "${kind}". Expected "dataset", "job", or "application"`);
        }
    } catch (e) {
        result.errors.push(`${filename}: ${(e as Error).message}`);
    }

    return result;
}

export function parseMultipleYamlFiles(files: Array<{ name: string; content: string }>): ImportResult {
    const combined: ImportResult = { applications: [], datasets: [], jobs: [], errors: [] };

    for (const file of files) {
        const result = parseYamlContent(file.content, file.name);
        combined.applications.push(...result.applications);
        combined.datasets.push(...result.datasets);
        combined.jobs.push(...result.jobs);
        combined.errors.push(...result.errors);
    }

    return combined;
}

export function entityToYaml(entity: LineageEntity): string {
    return dump(entity, {
        indent: 2,
        lineWidth: -1,
        noRefs: true,
        sortKeys: false
    });
}
