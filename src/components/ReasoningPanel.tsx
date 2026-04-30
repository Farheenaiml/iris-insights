import { motion } from "framer-motion";
import { GitBranch } from "lucide-react";

interface Props {
  paths: string[];
}

export default function ReasoningPanel({ paths }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.25 }}
      className="glass rounded-2xl p-6 shadow-card"
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
          <GitBranch className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Reasoning Path</h3>
          <p className="text-xs text-muted-foreground">How GraphRAG arrived at the answer</p>
        </div>
      </div>

      <ol className="space-y-2">
        {paths.map((p, i) => {
          const parts = p.split("→").map((s) => s.trim());
          return (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.08 }}
              className="flex items-center gap-2 flex-wrap text-sm font-mono"
            >
              <span className="text-muted-foreground text-xs">{String(i + 1).padStart(2, "0")}</span>
              {parts.map((part, idx) => (
                <span key={idx} className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-lg bg-secondary border border-border">{part}</span>
                  {idx < parts.length - 1 && <span className="text-primary">→</span>}
                </span>
              ))}
            </motion.li>
          );
        })}
      </ol>
    </motion.div>
  );
}
