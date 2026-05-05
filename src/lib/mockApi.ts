export interface QueryResponse {
  query: string;
  baseline: {
    answer: string;
    tokens: number;
    responseTime: number; // ms
    cost: number; // USD
  };
  graphrag: {
    answer: string;
    tokens: number;
    responseTime: number;
    cost: number;
    reasoningPath: string[];
    graph: {
      nodes: { id: string; group: number }[];
      edges: { source: string; target: string; highlight?: boolean }[];
    };
  };
  comparison: {
    tokensSavedPct: number;
    timeSavedPct: number;
    costSavedPct: number;
  };
}

export async function runComparison(query: string, file?: File): Promise<QueryResponse> {
  try {
    const formData = new FormData();
    formData.append('query', query);
    if (file) {
      formData.append('file', file);
    }

    const response = await fetch('http://localhost:8000/api/query', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (e) {
        // Ignore json parse error
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Failed to fetch comparison data:", error);
    throw error;
  }
}
