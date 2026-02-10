const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface MedicationInfo {
  name: string;
  url?: string;
  medex_data?: string;
  schedule: string;
}

export interface UserInput {
  meds: string[];
  schedule: string[];
  age: number;
  gender: 'M' | 'F';
  conditions?: string[];
}

export interface DrugSearchResult {
  query: string;
  results: string[];
}

export interface ContextSource {
  title: string;
  source: string;
  url: string;
  section_type: string;
  publication_year: string;
}

export interface MedicationDetail {
  name: string;
  schedule: string;
  found_in_database: boolean;
  has_detailed_info: boolean;
}

export interface AdviceResponse {
  advice: string;
  medications_processed: number;
  medications_found: number;
  successful_scrapes: number;
  pubmed_articles: number;
  context_sources: ContextSource[];
  drug_interactions_found: number;
  interaction_warnings: number;
  processing_time: string;
  patient_age: number;
  patient_gender: string;
  medications_detail: MedicationDetail[];
  advice_format: string;
}

export interface HealthResponse {
  status: string;
  services: string;
  timestamp: string;
  services_detail: Record<string, boolean>;
}

export interface DrugInfo {
  drug_name: string;
  url: string;
  found: boolean;
}

export interface SystemStats {
  timestamp: string;
  api_version: string;
  services: Record<string, unknown>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async searchDrugs(query: string, limit: number = 10): Promise<DrugSearchResult> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
    });
    return this.get<DrugSearchResult>(`/search_drugs?${params}`);
  }

  async getMedicationAdvice(userInput: UserInput): Promise<AdviceResponse> {
    return this.post<AdviceResponse>('/advise', userInput);
  }

  async getMedicationAdviceHtml(userInput: UserInput): Promise<string> {
    const response = await fetch(`${this.baseUrl}/advise/html`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userInput),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.text();
  }

  async getDrugInfo(drugName: string): Promise<DrugInfo> {
    return this.get<DrugInfo>(`/drug_info/${encodeURIComponent(drugName)}`);
  }

  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  async getStats(): Promise<SystemStats> {
    return this.get<SystemStats>('/stats');
  }
}

export const apiClient = new ApiClient();
