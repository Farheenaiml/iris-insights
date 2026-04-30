import { motion } from "framer-motion";
import { TrendingDown } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { QueryResponse } from "@/lib/mockApi";

interface Props {
  data: QueryResponse;
}

const tooltipStyle = {
  background: "hsl(225 15% 11%)",
  border: "1px solid hsl(225 12% 16%)",
  borderRadius: "12px",
  fontSize: "12px",
  padding: "8px 12px",
};

function Chart({ title, unit, data }: { title: string; unit: string; data: { name: string; value: number }[] }) {
  return (
    <div className="glass rounded-2xl p-5 shadow-card">
      <h4 className="text-sm font-medium text-muted-foreground mb-4">{title}</h4>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} barCategoryGap="35%">
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
            formatter={(v: number) => [`${v.toLocaleString()} ${unit}`, ""]}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={i === 0 ? "hsl(var(--muted-foreground))" : "hsl(var(--primary))"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function MetricsDashboard({ data }: Props) {
  const tokens = [
    { name: "Baseline", value: data.baseline.tokens },
    { name: "GraphRAG", value: data.graphrag.tokens },
  ];
  const time = [
    { name: "Baseline", value: +(data.baseline.responseTime / 1000).toFixed(2) },
    { name: "GraphRAG", value: +(data.graphrag.responseTime / 1000).toFixed(2) },
  ];
  const cost = [
    { name: "Baseline", value: +(data.baseline.cost * 1000).toFixed(2) },
    { name: "GraphRAG", value: +(data.graphrag.cost * 1000).toFixed(2) },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="space-y-5"
    >
      <div className="glass-strong rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4 shadow-elegant">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
            <TrendingDown className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Efficiency Gain</div>
            <div className="text-2xl font-semibold">
              You saved <span className="text-gradient">{data.comparison.tokensSavedPct}% tokens</span> using GraphRAG
            </div>
          </div>
        </div>
        <div className="flex gap-6 text-sm">
          <div>
            <div className="text-muted-foreground text-xs">Faster</div>
            <div className="font-mono font-semibold text-success">{data.comparison.timeSavedPct}%</div>
          </div>
          <div>
            <div className="text-muted-foreground text-xs">Cheaper</div>
            <div className="font-mono font-semibold text-success">{data.comparison.costSavedPct}%</div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        <Chart title="Token Usage" unit="tokens" data={tokens} />
        <Chart title="Response Time" unit="s" data={time} />
        <Chart title="Cost (×1000)" unit="$" data={cost} />
      </div>
    </motion.section>
  );
}
