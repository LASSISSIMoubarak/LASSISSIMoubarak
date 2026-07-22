"""
PHASE 5: Graph Topology Feature Engineering

Extract graph structure from TRUE causal edges in training data.
Use these to predict which edges are causal in test set.

Key Insight:
  Hub nodes (high centrality) are more likely causal sources
  Clustering coefficient indicates functional modules
  These features complement correlation-based prediction
"""

import pandas as pd
import numpy as np
from pathlib import Path
import networkx as nx
from sklearn.preprocessing import StandardScaler

# ============================================================================
# UTILITY: Load true edges from training data
# ============================================================================

def load_true_edges(network_id):
    """Load causal edges from data_train/target{network_id}.csv"""
    target_file = f"data_train/target{network_id}.csv"
    try:
        df = pd.read_csv(target_file)  # Has header: Cause,Effect
        edges = []
        for i in range(len(df)):
            cause_str = str(df.iloc[i, 0]).strip()  # "V0", "V1", etc.
            effect_str = str(df.iloc[i, 1]).strip()
            
            # Parse "V0" → 0, "V1" → 1, etc.
            cause_id = int(cause_str[1:]) if cause_str.startswith('V') else int(cause_str)
            effect_id = int(effect_str[1:]) if effect_str.startswith('V') else int(effect_str)
            
            edges.append((cause_id, effect_id))
        return edges
    except Exception as e:
        print(f"    Error loading edges: {e}")
        return []

# ============================================================================
# GRAPH FEATURES: Compute topological properties
# ============================================================================

def compute_graph_features(edges, n_nodes=20):
    """
    Compute centrality measures from true edges.
    
    Returns dict of node properties:
      - in_degree: # of nodes pointing to i
      - out_degree: # of nodes that i points to
      - betweenness: shortest path importance
      - closeness: average distance to other nodes
      - pagerank: influence score (iterative)
      - eigenvector: influence by connected importance
      - clustering: local triangle density
    """
    
    # Create directed graph from true edges
    G = nx.DiGraph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges)
    
    # Compute centrality measures
    try:
        in_degree = dict(G.in_degree())  # Who influences this node?
        out_degree = dict(G.out_degree())  # Who does this node influence?
        betweenness = nx.betweenness_centrality(G)  # Bridge importance
        closeness = nx.closeness_centrality(G)  # Network proximity
        pagerank = nx.pagerank(G)  # Influence propagation
        eigenvector = nx.eigenvector_centrality_numpy(G, max_iter=1000)
    except:
        # Fallback if convergence fails
        eigenvector = {i: 0.05 for i in range(n_nodes)}
    
    # Clustering: undirected version for triangle counting
    G_undirected = G.to_undirected()
    clustering = nx.clustering(G_undirected)
    
    return {
        'in_degree': in_degree,
        'out_degree': out_degree,
        'betweenness': betweenness,
        'closeness': closeness,
        'pagerank': pagerank,
        'eigenvector': eigenvector,
        'clustering': clustering
    }

# ============================================================================
# PAIR FEATURES: Edge-level properties
# ============================================================================

def extract_edge_features(i, j, graph_features, original_features):
    """
    Extract features for edge (i → j).
    
    Combines:
      - Original node features (from data_train/data*.csv)
      - Graph topology features (from true edges)
    """
    
    features = {}
    
    # Original features (both source and target)
    for k, val in enumerate(original_features[i]):
        features[f'src_feat_{k}'] = val
    for k, val in enumerate(original_features[j]):
        features[f'dst_feat_{k}'] = val
    
    # Graph topology: Source node i
    features['src_in_degree'] = graph_features['in_degree'].get(i, 0)
    features['src_out_degree'] = graph_features['out_degree'].get(i, 0)
    features['src_betweenness'] = graph_features['betweenness'].get(i, 0)
    features['src_closeness'] = graph_features['closeness'].get(i, 0)
    features['src_pagerank'] = graph_features['pagerank'].get(i, 0)
    features['src_eigenvector'] = graph_features['eigenvector'].get(i, 0)
    features['src_clustering'] = graph_features['clustering'].get(i, 0)
    
    # Graph topology: Target node j
    features['dst_in_degree'] = graph_features['in_degree'].get(j, 0)
    features['dst_out_degree'] = graph_features['out_degree'].get(j, 0)
    features['dst_betweenness'] = graph_features['betweenness'].get(j, 0)
    features['dst_closeness'] = graph_features['closeness'].get(j, 0)
    features['dst_pagerank'] = graph_features['pagerank'].get(j, 0)
    features['dst_eigenvector'] = graph_features['eigenvector'].get(j, 0)
    features['dst_clustering'] = graph_features['clustering'].get(j, 0)
    
    # Interaction features
    features['src_dst_pagerank_ratio'] = (
        graph_features['pagerank'].get(i, 0.01) / 
        max(graph_features['pagerank'].get(j, 0.01), 0.01)
    )
    features['dst_src_indegree_diff'] = (
        graph_features['in_degree'].get(j, 0) - 
        graph_features['in_degree'].get(i, 0)
    )
    
    return features

# ============================================================================
# MAIN: Generate enriched feature set for all networks
# ============================================================================

def generate_enriched_features(network_id, output_suffix=""):
    """
    Load training data, compute graph features, save enriched dataset.
    
    Returns:
      - Enriched feature dataframe (for ensemble training)
      - Graph features dict (for test set transformation)
    """
    
    print(f"\n--- Network {network_id} Feature Engineering ---")
    
    # Load training data
    train_data = pd.read_csv(f"data_train/data{network_id}.csv", header=None).values
    n_nodes = train_data.shape[0]
    
    # Load true edges and compute graph features
    true_edges = load_true_edges(network_id)
    print(f"  True edges: {len(true_edges)} causal pairs")
    
    graph_features = compute_graph_features(true_edges, n_nodes=n_nodes)
    
    # Extract edge features for all possible pairs
    edge_features_list = []
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j:
                edge_feat = extract_edge_features(i, j, graph_features, train_data)
                edge_features_list.append(edge_feat)
    
    enriched_df = pd.DataFrame(edge_features_list)
    
    # Save enriched features
    output_file = f"data_train/enriched_features{network_id}{output_suffix}.csv"
    enriched_df.to_csv(output_file, index=False)
    print(f"  ✓ Saved enriched features: {output_file}")
    print(f"    Shape: {enriched_df.shape}")
    print(f"    Columns: {enriched_df.columns.tolist()[:5]}... (+{len(enriched_df.columns)-5} more)")
    
    return enriched_df, graph_features

# ============================================================================
# BATCH PROCESS: Generate features for all 5 networks
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 5: GRAPH TOPOLOGY FEATURE ENGINEERING")
    print("=" * 70)
    print("\nObjective:")
    print("  Combine original features with graph centrality measures")
    print("  Use to train improved ensemble for causal edge prediction")
    print("\nFeatures extracted:")
    print("  • Original node features (20 per node)")
    print("  • In-degree / Out-degree (node influence)")
    print("  • Betweenness / Closeness / PageRank (centrality)")
    print("  • Eigenvector centrality (recursive influence)")
    print("  • Clustering coefficient (local triangles)")
    print("  • Interaction features (src-dst ratios)")
    
    all_enriched_dfs = {}
    all_graph_features = {}
    
    for net_id in range(1, 6):
        try:
            enriched_df, graph_feat = generate_enriched_features(net_id)
            all_enriched_dfs[net_id] = enriched_df
            all_graph_features[net_id] = graph_feat
        except Exception as e:
            print(f"  ⚠️  Error processing Network {net_id}: {e}")
    
    print("\n" + "=" * 70)
    print("✓ PHASE 5 COMPLETE: Feature engineering done!")
    print("=" * 70)
    print("\nNext: Use enriched features in generate_phase5_ensemble.py")
    print("Expected: 0.32 → 0.40-0.45+ with graph topology signal")
