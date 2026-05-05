import { motion } from "framer-motion";
import { Clock, Coins, Cpu, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { QueryResponse } from "@/lib/mockApi";

interface Props {
  data: QueryResponse | null;
  loading: boolean;
}

function Metric({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
        <Icon className="w-4 h-4 text-muted-foreground" />
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="text-sm font-mono font-medium">{value}</div>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-3">
      <div className="h-3 rounded shimmer" />
      <div className="h-3 rounded shimmer w-[90%]" />
      <div className="h-3 rounded shimmer w-[75%]" />
      <div className="h-3 rounded shimmer w-[85%]" />
    </div>
  );
}

function Card({
  title,
  loading,
  loadingLabel,
  answer,
  tokens,
  time,
  cost,
  highlighted,
}: {
  title: string;
  loading: boolean;
  loadingLabel: string;
  answer?: string;
  tokens?: number;
  time?: number;
  cost?: number;
  highlighted?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`relative rounded-2xl p-6 glass shadow-card ${
        highlighted ? "border-primary/40 pulse-glow" : ""
      }`}
    >
      {highlighted && (
        <div className="absolute -top-3 right-6 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-gradient-primary text-primary-foreground text-[10px] font-semibold uppercase tracking-wider">
          <Sparkles className="w-3 h-3" />
          Optimized
        </div>
      )}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        {loading && (
          <span className="text-xs text-muted-foreground flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            {loadingLabel}
          </span>
        )}
      </div>

      <div className="h-48 overflow-y-auto pr-2 mb-5 text-sm leading-relaxed text-foreground/90 prose prose-sm dark:prose-invert">
        {loading ? (
          <Skeleton />
        ) : (
          <ReactMarkdown
            components={{
              a: ({ node, ...props }) => (
                <a target="_blank" rel="noopener noreferrer" {...props} />
              ),
            }}
          >
            {answer || ""}
          </ReactMarkdown>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 pt-4 border-t border-border">
        <Metric icon={Cpu} label="Tokens" value={loading || tokens === undefined ? "—" : tokens.toLocaleString()} />
        <Metric icon={Clock} label="Time" value={loading || time === undefined ? "—" : `${(time / 1000).toFixed(2)}s`} />
        <Metric icon={Coins} label="Cost" value={loading || cost === undefined ? "—" : `$${cost.toFixed(4)}`} />
      </div>
    </motion.div>
  );
}

export default function ComparisonCards({ data, loading }: Props) {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card
        title="Baseline LLM"
        loading={loading}
        loadingLabel="Running Baseline…"
        answer={data?.baseline.answer}
        tokens={data?.baseline.tokens}
        time={data?.baseline.responseTime}
        cost={data?.baseline.cost}
      />
      <Card
        title="GraphRAG"
        highlighted
        loading={loading}
        loadingLabel="Running GraphRAG…"
        answer={data?.graphrag.answer}
        tokens={data?.graphrag.tokens}
        time={data?.graphrag.responseTime}
        cost={data?.graphrag.cost}
      />
    </div>
  );
}
