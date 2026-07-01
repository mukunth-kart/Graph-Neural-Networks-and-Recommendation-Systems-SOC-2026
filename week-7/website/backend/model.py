import torch
import torch.nn as nn
import torch.nn.functional as F

def aggregate_neighbors(neighbor_feats, index, num_nodes):
    """
    Mean aggregation helper using PyTorch scatter operations.
    - neighbor_feats: [E, D] - features of neighbor nodes
    - index: [E] - index of target destination nodes for each edge
    - num_nodes: int - number of destination nodes
    """
    device = neighbor_feats.device
    D = neighbor_feats.size(1)
    
    # Sum aggregate
    out = torch.zeros(num_nodes, D, device=device)
    expanded_index = index.unsqueeze(1).expand(-1, D)
    out.scatter_add_(0, expanded_index, neighbor_feats)
    
    # Count aggregate for mean
    counts = torch.zeros(num_nodes, 1, device=device)
    ones = torch.ones(index.size(0), 1, device=device)
    counts.scatter_add_(0, index.unsqueeze(1), ones)
    
    # Normalize (clamp count min to 1 to avoid division by zero)
    counts = torch.clamp(counts, min=1.0)
    return out / counts

class BipartiteSAGEConv(nn.Module):
    """
    GraphSAGE Conv layer for bipartite graph.
    Updates representation of destination nodes by aggregating source neighbors.
    """
    def __init__(self, src_dim, dst_dim, out_dim):
        super(BipartiteSAGEConv, self).__init__()
        self.src_dim = src_dim
        self.dst_dim = dst_dim
        self.out_dim = out_dim
        
        self.fc_self = nn.Linear(dst_dim, out_dim)
        self.fc_neigh = nn.Linear(src_dim, out_dim)
        self.act = nn.ReLU()
        
    def forward(self, src_feats, dst_feats, edge_index, num_dst_nodes):
        """
        - src_feats: [N_src, src_dim]
        - dst_feats: [N_dst, dst_dim]
        - edge_index: [2, E] - edge_index[0] represents source indices, edge_index[1] represents target indices
        - num_dst_nodes: int - N_dst
        """
        src_indices = edge_index[0]
        dst_indices = edge_index[1]
        
        # 1. Gather source features for each edge
        edge_src_feats = src_feats[src_indices]
        
        # 2. Aggregate to destination nodes
        neigh_agg = aggregate_neighbors(edge_src_feats, dst_indices, num_dst_nodes)
        
        # 3. Combine self and aggregated neighbor representations
        out_self = self.fc_self(dst_feats)
        out_neigh = self.fc_neigh(neigh_agg)
        
        # GraphSAGE combination: Concatenation or Sum.
        # We use a weighted sum (represented by self.fc_self + self.fc_neigh) and apply ReLU.
        out = self.act(out_self + out_neigh)
        return F.normalize(out, p=2, dim=-1) # L2 normalization

class GraphSAGEModel(nn.Module):
    def __init__(self, num_users, num_movies, num_genres, embedding_dim=64):
        super(GraphSAGEModel, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Trainable node embeddings
        self.user_emb = nn.Embedding(num_users, embedding_dim)
        self.movie_emb = nn.Embedding(num_movies, embedding_dim)
        
        # Movie content feature projection (genres multi-hot)
        self.genre_proj = nn.Linear(num_genres, embedding_dim)
        
        # Bipartite GraphSAGE Layer 1
        self.user_conv1 = BipartiteSAGEConv(embedding_dim, embedding_dim, embedding_dim)
        self.movie_conv1 = BipartiteSAGEConv(embedding_dim, embedding_dim, embedding_dim)
        
        # Bipartite GraphSAGE Layer 2
        self.user_conv2 = BipartiteSAGEConv(embedding_dim, embedding_dim, embedding_dim)
        self.movie_conv2 = BipartiteSAGEConv(embedding_dim, embedding_dim, embedding_dim)
        
        # Rating Prediction Head
        # Predicts continuous score [1, 5]
        self.pred_mlp = nn.Sequential(
            nn.Linear(embedding_dim * 3, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def get_movie_features(self, movie_genres):
        """
        Calculates initial movie representations combining ID embedding and genre features.
        - movie_genres: [N_movies, num_genres] - multi-hot genre matrix
        """
        # [N_movies, D]
        base_emb = self.movie_emb.weight
        # Project genres to embedding dimension
        genres_proj = self.genre_proj(movie_genres)
        # Sum representations
        return F.normalize(base_emb + genres_proj, p=2, dim=-1)
        
    def forward(self, user_ids, movie_ids, movie_genres, user_to_movie_edges, movie_to_user_edges):
        """
        Runs the GNN layers and returns predicted ratings for specified edge inputs.
        - user_ids: [BatchSize]
        - movie_ids: [BatchSize]
        - movie_genres: [N_movies, num_genres] - full movies genre matrix
        - user_to_movie_edges: [2, E] - [0] is user index, [1] is movie index
        - movie_to_user_edges: [2, E] - [0] is movie index, [1] is user index
        """
        num_users = self.user_emb.weight.size(0)
        num_movies = self.movie_emb.weight.size(0)
        
        # Initial representations
        h_u = self.user_emb.weight
        h_m = self.get_movie_features(movie_genres)
        
        # Layer 1
        h_m_1 = self.movie_conv1(h_u, h_m, user_to_movie_edges, num_movies)
        h_u_1 = self.user_conv1(h_m, h_u, movie_to_user_edges, num_users)
        
        # Layer 2
        h_m_2 = self.movie_conv2(h_u_1, h_m_1, user_to_movie_edges, num_movies)
        h_u_2 = self.user_conv2(h_m_1, h_u_1, movie_to_user_edges, num_users)
        
        # Extract features for prediction batch
        u_feat = h_u_2[user_ids]
        m_feat = h_m_2[movie_ids]
        
        # Concatenate features and interaction term
        combined = torch.cat([u_feat, m_feat, u_feat * m_feat], dim=-1)
        
        # Predict rating
        pred = self.pred_mlp(combined).squeeze(-1)
        # Clamp between 1.0 and 5.0
        pred = 1.0 + 4.0 * torch.sigmoid(pred)
        
        return pred, h_u_2, h_m_2
        
    def encode(self, movie_genres, user_to_movie_edges, movie_to_user_edges):
        """
        Helper to run GNN encoding and return final node embeddings.
        """
        num_users = self.user_emb.weight.size(0)
        num_movies = self.movie_emb.weight.size(0)
        
        h_u = self.user_emb.weight
        h_m = self.get_movie_features(movie_genres)
        
        h_m_1 = self.movie_conv1(h_u, h_m, user_to_movie_edges, num_movies)
        h_u_1 = self.user_conv1(h_m, h_u, movie_to_user_edges, num_users)
        
        h_m_2 = self.movie_conv2(h_u_1, h_m_1, user_to_movie_edges, num_movies)
        h_u_2 = self.user_conv2(h_m_1, h_u_1, movie_to_user_edges, num_users)
        
        return h_u_2, h_m_2
