import { motion } from "framer-motion";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (q: string) => void;
  loading: boolean;
}

const SUGGESTIONS = [
  "Why are floods frequent in Mumbai?",
  "How does photosynthesis affect climate?",
  "What caused the 2008 financial crisis?",
];

export default function QueryInput({ onSubmit, loading }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="w-full max-w-3xl mx-auto text-center"
    >
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass text-xs text-muted-foreground mb-6">
        <Sparkles className="w-3 h-3 text-primary" />
        <span>GraphRAG vs Baseline LLM</span>
      </div>

      <h1 className="text-4xl md:text-6xl font-semibold tracking-tight mb-4">
        Ask anything. <span className="text-gradient">See the difference.</span>
      </h1>
      <p className="text-muted-foreground mb-10 max-w-xl mx-auto">
        Compare responses, latency, and cost between a baseline LLM and a graph-augmented retrieval system.
      </p>

      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-px bg-gradient-primary rounded-2xl opacity-0 group-focus-within:opacity-60 blur-md transition-opacity duration-500" />
        <div className="relative glass-strong rounded-2xl p-2 flex items-center gap-2 shadow-card">
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ask a question…"
            disabled={loading}
            className="flex-1 bg-transparent px-4 py-4 text-base outline-none placeholder:text-muted-foreground/70"
          />
          <button
            type="submit"
            disabled={loading || !value.trim()}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-primary text-primary-foreground font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-glow transition-all duration-300"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running…
              </>
            ) : (
              <>
                Run Comparison
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
        <span className="text-xs text-muted-foreground">Try:</span>
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => !loading && setValue(s)}
            className="text-xs px-3 py-1.5 rounded-full glass hover:border-primary/40 transition-colors text-muted-foreground hover:text-foreground"
          >
            {s}
          </button>
        ))}
      </div>
    </motion.section>
  );
}
