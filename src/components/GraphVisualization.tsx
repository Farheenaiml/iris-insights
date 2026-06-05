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
    const W = 720;
    const H = 360;
    const nodes = graph.nodes;
    const edges = graph.edges;

    if (nodes.length === 0) return {};

    // Check how many unique groups we have
    const uniqueGroups = new Set(nodes.map(n => n.group));

    if (uniqueGroups.size > 1) {
      // Use original Column-Based Grid Flow Layout
      const groups: Record<number, string[]> = {};
      nodes.forEach((n) => {
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
    } else {
      // Use Force-Directed Layout to spread single-group nodes out dynamically
      const pos: Record<string, Pos> = {};
      nodes.forEach((n, i) => {
        const angle = (i / nodes.length) * 2 * Math.PI;
        const radius = 80 + Math.random() * 30;
        pos[n.id] = {
          x: W / 2 + radius * Math.cos(angle),
          y: H / 2 + radius * Math.sin(angle),
        };
      });

      const iterations = 120;
      const k = Math.sqrt((W * H) / (nodes.length || 1)) * 0.8;

      for (let iter = 0; iter < iterations; iter++) {
        const disp: Record<string, { x: number; y: number }> = {};
        nodes.forEach((n) => {
          disp[n.id] = { x: 0, y: 0 };
        });

        for (let i = 0; i < nodes.length; i++) {
          const u = nodes[i];
          for (let j = i + 1; j < nodes.length; j++) {
            const v = nodes[j];
            const dx = pos[u.id].x - pos[v.id].x;
            const dy = pos[u.id].y - pos[v.id].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
            if (dist < 150) {
              const force = (k * k) / dist;
              disp[u.id].x += (dx / dist) * force;
              disp[u.id].y += (dy / dist) * force;
              disp[v.id].x -= (dx / dist) * force;
              disp[v.id].y -= (dy / dist) * force;
            }
          }
        }

        edges.forEach((e) => {
          const u = e.source;
          const v = e.target;
          if (!pos[u] || !pos[v]) return;
          const dx = pos[u].x - pos[v].x;
          const dy = pos[u].y - pos[v].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          const force = (dist * dist) / k;
          disp[u].x -= (dx / dist) * force * 0.5;
          disp[u].y -= (dy / dist) * force * 0.5;
          disp[v].x += (dx / dist) * force * 0.5;
          disp[v].y += (dy / dist) * force * 0.5;
        });

        nodes.forEach((n) => {
          const dx = pos[n.id].x - W / 2;
          const dy = pos[n.id].y - H / 2;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1.0;
          disp[n.id].x -= (dx / dist) * 0.05 * dist;
          disp[n.id].y -= (dy / dist) * 0.05 * dist;
        });

        const maxDisplacement = 15;
        nodes.forEach((n) => {
          const d = disp[n.id];
          const dist = Math.sqrt(d.x * d.x + d.y * d.y) || 1.0;
          const cappedDist = Math.min(maxDisplacement, dist);
          pos[n.id].x += (d.x / dist) * cappedDist;
          pos[n.id].y += (d.y / dist) * cappedDist;

          pos[n.id].x = Math.max(35, Math.min(W - 35, pos[n.id].x));
          pos[n.id].y = Math.max(35, Math.min(H - 35, pos[n.id].y));
        });
      }
      return pos;
    }
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
