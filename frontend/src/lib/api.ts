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
}

export interface DrugSearchResult {
  query: string;
  results: string[];
}

export interface AdviceResponse {
  advice: string;
  medications_processed: number;
  medications_found: number;
  successful_scrapes: number;
  pubmed_articles: number;
  context_sources: Array<{
    title: string;
    source: string;
    url: string;
    section_type: string;
    publication_year: string;
  }>;
  drug_interactions_found: number;
  interaction_warnings: number;
  processing_time: string;
  patient_age: number;
  patient_gender: string;
  medications_detail: Array<{
    name: string;
    schedule: string;
    found_in_database: boolean;
    has_detailed_info: boolean;
  }>;
  advice_format: string;
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

  async post<T>(endpoint: string, data: any): Promise<T> {
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

  async getDrugInfo(drugName: string): Promise<{ drug_name: string; url: string; found: boolean }> {
    return this.get<{ drug_name: string; url: string; found: boolean }>(`/drug_info/${encodeURIComponent(drugName)}`);
  }

  async getHealth(): Promise<any> {
    return this.get('/health');
  }

  async getStats(): Promise<any> {
    return this.get('/stats');
  }
}

export const apiClient = new ApiClient();
