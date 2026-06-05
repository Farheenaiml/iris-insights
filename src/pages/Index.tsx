import { motion } from "framer-motion";
import { Network } from "lucide-react";
import { useState } from "react";
import ComparisonCards from "@/components/ComparisonCards";
import GraphVisualization from "@/components/GraphVisualization";
import MetricsDashboard from "@/components/MetricsDashboard";
import QueryInput from "@/components/QueryInput";
import ReasoningPanel from "@/components/ReasoningPanel";
import { runComparison, type QueryResponse } from "@/lib/mockApi";
import { toast } from "sonner";

const Index = () => {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (q: string, file?: File) => {
    setLoading(true);
    setSubmitted(true);
    setData(null);
    try {
      const res = await runComparison(q, file);
      setData(res);
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Failed to fetch response. Please check your backend.");
      setSubmitted(false); // Reset submitted state on error so UI doesn't hang on skeletons
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-border/50">
        <div className="container mx-auto flex items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow">
              <Network className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold tracking-tight text-lg">IRIS</span>
            <span className="text-xs text-muted-foreground hidden sm:inline ml-2">
              GraphRAG Comparison
            </span>
          </div>
          <nav className="text-xs text-muted-foreground hidden sm:flex gap-6">
            <a href="#" className="hover:text-foreground transition-colors">Docs</a>
            <a href="#" className="hover:text-foreground transition-colors">API</a>
            <a href="#" className="hover:text-foreground transition-colors">GitHub</a>
          </nav>
        </div>
      </header>

      <main className="container mx-auto py-12 md:py-20 space-y-12">
        <QueryInput onSubmit={handleSubmit} loading={loading} />

        <ComparisonCards data={data} loading={loading} />

        {submitted && data && !loading && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="space-y-8"
          >
            <MetricsDashboard data={data} />
            <div className="grid lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3">
                <GraphVisualization graph={data.graphrag.graph} />
              </div>
              <div className="lg:col-span-2">
                <ReasoningPanel paths={data.graphrag.reasoningPath} />
              </div>
            </div>
          </motion.section>
        )}
      </main>

      <footer className="border-t border-border/50 mt-20">
        <div className="container mx-auto py-6 text-center text-xs text-muted-foreground">
          IRIS · Built for GraphRAG evaluation
        </div>
      </footer>
    </div>
  );
};

export default Index;
