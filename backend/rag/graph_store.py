import os
import json
import networkx as nx
from typing import Dict, List, Tuple, Any, Set

class MedicalGraphStore:
    def __init__(self, filepath: str = "rag_index/medical_graph.json"):
        self.filepath = filepath
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_node(self, node_id: str, label: str = "Entity", properties: Dict[str, Any] = None):
        """Adds a node with type/label and optional properties."""
        node_id = str(node_id).strip()
        if not node_id:
            return
        
        props = properties or {}
        # Default group based on label type
        groups = {
            "treatment": 1,
            "drug": 1,
            "subject": 1,
            "condition": 2,
            "disease": 2,
            "action": 2,
            "metric": 3,
            "value": 3,
            "entity": 0
        }
        group = groups.get(label.lower(), 0)
        
        self.graph.add_node(
            node_id, 
            label=label, 
            group=group,
            **props
        )

    def add_edge(self, source: str, target: str, relation_type: str, weight: float = 1.0, properties: Dict[str, Any] = None):
        """Adds a directed relation edge between source and target."""
        source = str(source).strip()
        target = str(target).strip()
        relation_type = str(relation_type).strip()
        
        if not source or not target or not relation_type:
            return
            
        props = properties or {}
        self.graph.add_edge(
            source, 
            target, 
            key=relation_type,
            relation=relation_type, 
            weight=weight,
            **props
        )

    def get_subgraph_for_entities(self, query_entities: List[str], max_depth: int = 1) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """
        Retrieves matching nodes, their neighbors, and the relationships (triples)
        to form the context and visualization data.
        """
        retrieved_nodes = set()
        retrieved_edges = []
        triples = []
        
        # Normalize and find nodes in graph that match or contain the query entities
        matched_roots = []
        for entity in query_entities:
            entity_norm = entity.lower().strip()
            for node in self.graph.nodes:
                if entity_norm in node.lower() or node.lower() in entity_norm:
                    matched_roots.append(node)
                    
        matched_roots = list(set(matched_roots))
        if not matched_roots:
            return [], [], []

        # Find BFS subgraph starting from matched root nodes up to max_depth
        current_layer = set(matched_roots)
        visited = set(matched_roots)
        retrieved_nodes.update(matched_roots)
        
        for _ in range(max_depth):
            next_layer = set()
            for u in current_layer:
                # Outgoing edges
                if u in self.graph:
                    for v in self.graph[u]:
                        for key in self.graph[u][v]:
                            edge_data = self.graph[u][v][key]
                            retrieved_nodes.add(v)
                            next_layer.add(v)
                            
                            # Add to output edges
                            retrieved_edges.append({
                                "source": u,
                                "target": v,
                                "relation": edge_data.get("relation", "related_to"),
                                "highlight": True
                            })
                            
                            # Format triple for prompt context
                            triples.append(f"({u}) -[{edge_data.get('relation', 'related_to')}]-> ({v})")
                            
                # Incoming edges
                # To capture bidirectional relevance, we look at predecessors too
                for pred in self.graph.predecessors(u):
                    if pred not in visited:
                        for key in self.graph[pred][u]:
                            edge_data = self.graph[pred][u][key]
                            retrieved_nodes.add(pred)
                            next_layer.add(pred)
                            
                            retrieved_edges.append({
                                "source": pred,
                                "target": u,
                                "relation": edge_data.get("relation", "related_to"),
                                "highlight": True
                            })
                            
                            triples.append(f"({pred}) -[{edge_data.get('relation', 'related_to')}]-> ({u})")
                            
            current_layer = next_layer - visited
            visited.update(current_layer)

        # Build list of node dicts for the frontend
        nodes_list = []
        for node in retrieved_nodes:
            node_data = self.graph.nodes[node]
            nodes_list.append({
                "id": node,
                "group": node_data.get("group", 0)
            })

        # Deduplicate edges based on source, target, relation
        unique_edges = []
        seen_edges = set()
        for edge in retrieved_edges:
            edge_key = (edge["source"], edge["target"], edge["relation"])
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)

        return nodes_list, unique_edges, list(set(triples))

    def save(self):
        """Saves the graph state to a JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        nodes_data = []
        for node, attrs in self.graph.nodes(data=True):
            nodes_data.append({"id": node, "attributes": attrs})
            
        edges_data = []
        for u, v, key, attrs in self.graph.edges(keys=True, data=True):
            edges_data.append({"source": u, "target": v, "key": key, "attributes": attrs})
            
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump({"nodes": nodes_data, "edges": edges_data}, f, indent=2)

    def load(self):
        """Loads the graph state from a JSON file if it exists."""
        if not os.path.exists(self.filepath):
            return
            
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.graph.clear()
            
            for node_info in data.get("nodes", []):
                attrs = node_info.get("attributes", {})
                self.graph.add_node(node_info["id"], **attrs)
                
            for edge_info in data.get("edges", []):
                self.graph.add_edge(
                    edge_info["source"],
                    edge_info["target"],
                    key=edge_info["key"],
                    **edge_info.get("attributes", {})
                )
        except Exception as e:
            print(f"Error loading graph store: {e}")
            self.graph = nx.MultiDiGraph()
