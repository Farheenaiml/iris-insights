import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import type { QueryResponse } from "@/lib/mockApi";

interface Props {
  graph: QueryResponse["graphrag"]["graph"];
}

interface Pos {
  x: number;
  y: number;
}

export default function GraphVisualization({ graph }: Props) {
  const [hover, setHover] = useState<string | null>(null);

  const positions = useMemo<Record<string, Pos>>(() => {
    // Layout nodes in concentric layers based on group
    const W = 720;
    const H = 360;
    const groups: Record<number, string[]> = {};
    graph.nodes.forEach((n) => {
      groups[n.group] = groups[n.group] || [];
      groups[n.group].push(n.id);
    });
    const groupKeys = Object.keys(groups).map(Number).sort();
    const pos: Record<string, Pos> = {};
    const colW = W / (groupKeys.length + 1);
    groupKeys.forEach((g, gi) => {
      const arr = groups[g];
      const x = colW * (gi + 1);
      arr.forEach((id, i) => {
        const y = (H / (arr.length + 1)) * (i + 1);
        pos[id] = { x, y };
      });
    });
    return pos;
  }, [graph]);

  const isConnected = (id: string) => {
    if (!hover) return false;
    return graph.edges.some(
      (e) => (e.source === hover && e.target === id) || (e.target === hover && e.source === id)
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-strong rounded-2xl p-6 shadow-card"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Reasoning Graph</h3>
          <p className="text-xs text-muted-foreground">Entities and relationships used in retrieval</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-primary" /> Path
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-muted-foreground" /> Entity
          </span>
        </div>
      </div>

      <div className="relative w-full overflow-hidden rounded-xl bg-background/40 border border-border">
        <svg viewBox="0 0 720 360" className="w-full h-[360px]">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="hsl(var(--primary) / 0.6)" />
            </marker>
          </defs>

          {graph.edges.map((e, i) => {
            const s = positions[e.source];
            const t = positions[e.target];
            if (!s || !t) return null;
            const active = e.highlight;
            const dim = hover && hover !== e.source && hover !== e.target;
            return (
              <line
                key={i}
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={active ? "hsl(var(--primary))" : "hsl(var(--border))"}
                strokeWidth={active ? 1.5 : 1}
                strokeOpacity={dim ? 0.15 : active ? 0.7 : 0.4}
                markerEnd="url(#arrow)"
                style={{ transition: "all 0.3s" }}
              />
            );
          })}

          {graph.nodes.map((n) => {
            const p = positions[n.id];
            if (!p) return null;
            const active = hover === n.id || isConnected(n.id);
            const dim = hover && !active;
            return (
              <g
                key={n.id}
                transform={`translate(${p.x}, ${p.y})`}
                onMouseEnter={() => setHover(n.id)}
                onMouseLeave={() => setHover(null)}
                style={{ cursor: "pointer", transition: "opacity 0.3s", opacity: dim ? 0.35 : 1 }}
              >
                <circle
                  r={active ? 26 : 22}
                  fill="hsl(var(--card))"
                  stroke={active ? "hsl(var(--primary))" : "hsl(var(--border))"}
                  strokeWidth={active ? 2 : 1}
                  style={{ transition: "all 0.3s" }}
                />
                <text
                  textAnchor="middle"
                  dy="0.35em"
                  fontSize="10"
                  fontWeight="500"
                  fill="hsl(var(--foreground))"
                >
                  {n.id.length > 10 ? n.id.slice(0, 9) + "…" : n.id}
                </text>
              </g>
            );
          })}
        </svg>
        {hover && (
          <div className="absolute top-3 left-3 glass px-3 py-1.5 rounded-lg text-xs">
            <span className="text-muted-foreground">Entity:</span>{" "}
            <span className="font-medium">{hover}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
