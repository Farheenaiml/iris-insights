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

export async function runComparison(query: string): Promise<QueryResponse> {
  // Simulated backend. Replace with: fetch('/query', { method:'POST', body: JSON.stringify({query}) })
  await new Promise((r) => setTimeout(r, 1800));

  const baselineTokens = 1850;
  const grTokens = 720;
  const baselineTime = 4200;
  const grTime = 1450;
  const baselineCost = 0.0421;
  const grCost = 0.0162;

  return {
    query,
    baseline: {
      answer:
        "Mumbai experiences frequent flooding due to a combination of intense monsoon rainfall, poor drainage infrastructure, rapid urbanization, encroachment on natural water bodies, rising sea levels, and the city's low-lying topography. The British-era stormwater drains were designed for 25mm/hour rainfall but the city often receives 50–100mm/hour during monsoons. Climate change has exacerbated extreme weather events, while construction over wetlands and the Mithi river floodplain has reduced natural water absorption.",
      tokens: baselineTokens,
      responseTime: baselineTime,
      cost: baselineCost,
    },
    graphrag: {
      answer:
        "Mumbai floods frequently because heavy monsoon rainfall overwhelms an outdated colonial drainage system, while urbanization over wetlands and the Mithi river has eliminated natural absorption pathways. Three causal chains dominate: rainfall→drainage capacity, urbanization→wetland loss, and topography→sea-level coupling.",
      tokens: grTokens,
      responseTime: grTime,
      cost: grCost,
      reasoningPath: [
        "Mumbai → Rainfall → Flood",
        "Mumbai → Drainage System → Flood",
        "Mumbai → Urbanization → Wetland Loss → Flood",
        "Mumbai → Topography → Sea Level → Flood",
      ],
      graph: {
        nodes: [
          { id: "Mumbai", group: 0 },
          { id: "Rainfall", group: 1 },
          { id: "Drainage", group: 1 },
          { id: "Urbanization", group: 1 },
          { id: "Topography", group: 1 },
          { id: "Wetland Loss", group: 2 },
          { id: "Sea Level", group: 2 },
          { id: "Flood", group: 3 },
        ],
        edges: [
          { source: "Mumbai", target: "Rainfall", highlight: true },
          { source: "Mumbai", target: "Drainage", highlight: true },
          { source: "Mumbai", target: "Urbanization", highlight: true },
          { source: "Mumbai", target: "Topography", highlight: true },
          { source: "Rainfall", target: "Flood", highlight: true },
          { source: "Drainage", target: "Flood", highlight: true },
          { source: "Urbanization", target: "Wetland Loss", highlight: true },
          { source: "Wetland Loss", target: "Flood", highlight: true },
          { source: "Topography", target: "Sea Level", highlight: true },
          { source: "Sea Level", target: "Flood", highlight: true },
        ],
      },
    },
    comparison: {
      tokensSavedPct: Math.round(((baselineTokens - grTokens) / baselineTokens) * 100),
      timeSavedPct: Math.round(((baselineTime - grTime) / baselineTime) * 100),
      costSavedPct: Math.round(((baselineCost - grCost) / baselineCost) * 100),
    },
  };
}
