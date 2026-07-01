import os
import zipfile
import urllib.request
import sqlite3
import json
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from database import get_db_connection, init_db, add_training_log, hash_password
from model import GraphSAGEModel

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ML_ZIP_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
ZIP_PATH = os.path.join(DATA_DIR, "ml-100k.zip")
EXTRACT_PATH = os.path.join(DATA_DIR, "ml-100k")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pth")
MAPPINGS_PATH = os.path.join(os.path.dirname(__file__), "mappings.json")

def download_and_extract_movielens():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    u_data_path = os.path.join(EXTRACT_PATH, "u.data")
    u_item_path = os.path.join(EXTRACT_PATH, "u.item")
    
    if os.path.exists(u_data_path) and os.path.exists(u_item_path):
        print("MovieLens 100k dataset already exists.")
        return u_data_path, u_item_path

    print(f"Downloading MovieLens 100K from {ML_ZIP_URL}...")
    try:
        urllib.request.urlretrieve(ML_ZIP_URL, ZIP_PATH)
        print("Extracting dataset...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            # ml-100k zip extracts into a folder named ml-100k
            zip_ref.extractall(DATA_DIR)
        print("MovieLens 100k downloaded and extracted successfully.")
    except Exception as e:
        print(f"Failed to download/extract MovieLens dataset: {e}")
        print("Generating mock/synthetic dataset to ensure database initializes correctly...")
        generate_mock_dataset(u_data_path, u_item_path)
        
    return u_data_path, u_item_path

def generate_mock_dataset(u_data_path, u_item_path):
    # Generates a basic mock dataset in case the user has no internet connection
    os.makedirs(EXTRACT_PATH, exist_ok=True)
    
    # 1. Mock Movies
    genres_list = ["Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", "Documentary", 
                   "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", "Romance", 
                   "Sci-Fi", "Thriller", "War", "Western"]
    
    movies = []
    titles = [
        "Toy Story (1995)", "GoldenEye (1995)", "Four Rooms (1995)", "Get Shorty (1995)", 
        "Copycat (1995)", "Shanghai Triad (1995)", "Twelve Monkeys (1995)", "Babe (1995)", 
        "Dead Man Walking (1995)", "Richard III (1995)", "Seven (1995)", "Usual Suspects, The (1995)",
        "Mighty Aphrodite (1995)", "Postino, Il (1994)", "Mr. Holland's Opus (1995)", "French Twist (1995)",
        "From Dusk Till Dawn (1996)", "White Balloon, The (1995)", "Antonia's Line (1995)", "Angels and Insects (1995)"
    ]
    
    with open(u_item_path, "w", encoding="latin-1") as f:
        for idx, title in enumerate(titles):
            m_id = idx + 1
            # Assign random genres
            genre_bits = [0] * 19
            # Ensure at least one genre is active
            active_genre_idx = idx % 19
            genre_bits[active_genre_idx] = 1
            if idx % 2 == 0:
                genre_bits[(active_genre_idx + 2) % 19] = 1
            genre_str = "|".join(map(str, genre_bits))
            # Format: id | title | release_date | video_release_date | IMDb | genre_bits
            f.write(f"{m_id}|{title}|01-Jan-1995||http://mockurl|0|{genre_str}\n")
            
    # 2. Mock Ratings
    with open(u_data_path, "w") as f:
        # Generate ratings for 20 users and 20 movies
        for user_id in range(1, 21):
            for movie_id in range(1, 21):
                # User rates movies with some noise
                if (user_id + movie_id) % 3 != 0:
                    rating = 3.0 + float((user_id * 2 + movie_id) % 3)
                    timestamp = 874724800 + (user_id * 100) + movie_id
                    f.write(f"{user_id}\t{movie_id}\t{int(rating)}\t{timestamp}\n")
    print("Mock dataset generated successfully.")

def populate_database_from_movielens(u_data_path, u_item_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check if movies table is already populated
    cursor.execute("SELECT COUNT(*) FROM movies")
    if cursor.fetchone()[0] > 0:
        print("Database already populated.")
        conn.close()
        return

    print("Populating database with MovieLens data...")
    # Load Movies
    genres_list = ["unknown", "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", 
                   "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", 
                   "Romance", "Sci-Fi", "Thriller", "War", "Western"]
                   
    movies_data = []
    with open(u_item_path, "r", encoding="latin-1") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) < 6:
                continue
            movie_id = int(parts[0])
            title = parts[1]
            
            # Extract year from title, e.g. "Toy Story (1995)"
            year = 1995
            try:
                if "(" in title:
                    year_str = title.split("(")[-1].split(")")[0]
                    if year_str.isdigit():
                        year = int(year_str)
            except:
                pass
                
            # Genre list mapping
            movie_genres = []
            for i, genre_val in enumerate(parts[5:24]):
                if i < len(genres_list) and genre_val == "1":
                    movie_genres.append(genres_list[i])
                    
            genres_str = ",".join(movie_genres)
            movies_data.append((movie_id, title, genres_str, year))
            
    cursor.executemany("INSERT OR IGNORE INTO movies (id, title, genres, release_year) VALUES (?, ?, ?, ?)", movies_data)
    print(f"Inserted {len(movies_data)} movies.")
    
    # Load Ratings
    ratings_data = []
    users_to_create = set()
    with open(u_data_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 4:
                continue
            user_id = int(parts[0])
            movie_id = int(parts[1])
            rating = float(parts[2])
            timestamp = int(parts[3])
            
            users_to_create.add(user_id)
            # Default loaded ratings are marked as trained (is_new_feedback = 0)
            ratings_data.append((user_id, movie_id, rating, timestamp, 0))
            
    # Insert users
    user_pass_hash = hash_password("password")
    users_batch = []
    for u_id in sorted(users_to_create):
        # We match user table primary key with MovieLens user IDs
        users_batch.append((u_id, f"user{u_id}", f"user{u_id}@movielens.com", f"+1555000{u_id:04d}", user_pass_hash, "user", "active"))
        
    cursor.executemany("INSERT OR IGNORE INTO users (id, username, email, phone, password_hash, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)", users_batch)
    print(f"Created {len(users_batch)} users.")
    
    cursor.executemany("INSERT OR IGNORE INTO ratings (user_id, movie_id, rating, timestamp, is_new_feedback) VALUES (?, ?, ?, ?, ?)", ratings_data)
    print(f"Inserted {len(ratings_data)} ratings.")
    
    conn.commit()
    conn.close()

def build_mappings_and_features():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get active users
    cursor.execute("SELECT id FROM users WHERE status = 'active' ORDER BY id ASC")
    user_rows = cursor.fetchall()
    user_ids = [row["id"] for row in user_rows]
    user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    
    # Get movies
    cursor.execute("SELECT id, genres FROM movies ORDER BY id ASC")
    movie_rows = cursor.fetchall()
    movie_ids = [row["id"] for row in movie_rows]
    movie_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
    
    # Build genres multi-hot
    genres_list = ["unknown", "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", 
                   "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", 
                   "Romance", "Sci-Fi", "Thriller", "War", "Western"]
    genre_to_idx = {g: idx for idx, g in enumerate(genres_list)}
    
    movie_genres_matrix = np.zeros((len(movie_ids), len(genres_list)), dtype=np.float32)
    for row in movie_rows:
        m_id = row["id"]
        m_idx = movie_to_idx[m_id]
        genres_str = row["genres"]
        if genres_str:
            for g in genres_str.split(","):
                if g in genre_to_idx:
                    movie_genres_matrix[m_idx, genre_to_idx[g]] = 1.0
                    
    conn.close()
    
    return {
        "user_to_idx": user_to_idx,
        "idx_to_user": {v: k for k, v in user_to_idx.items()},
        "movie_to_idx": movie_to_idx,
        "idx_to_movie": {v: k for k, v in movie_to_idx.items()},
        "num_genres": len(genres_list)
    }, movie_genres_matrix

def train_model(epochs=15, batch_size=512, lr=0.01, embedding_dim=64):
    start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    add_training_log(start_time, "running", loss=None, metrics="Training started...")
    
    try:
        # Ensure data is populated
        u_data, u_item = download_and_extract_movielens()
        populate_database_from_movielens(u_data, u_item)
        
        # Load mappings
        mappings, movie_genres_np = build_mappings_and_features()
        user_to_idx = mappings["user_to_idx"]
        movie_to_idx = mappings["movie_to_idx"]
        
        # Load ratings
        conn = get_db_connection()
        cursor = conn.cursor()
        # Exclude ratings from banned users
        cursor.execute(
            """
            SELECT r.user_id, r.movie_id, r.rating 
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            WHERE u.status = 'active'
            """
        )
        ratings_rows = cursor.fetchall()
        conn.close()
        
        if len(ratings_rows) == 0:
            raise Exception("No active user ratings found in database. Cannot train.")
            
        print(f"Training on {len(ratings_rows)} active ratings.")
        
        # Build rating tensors
        train_users = []
        train_movies = []
        train_ratings = []
        
        for r in ratings_rows:
            uid = r["user_id"]
            mid = r["movie_id"]
            if uid in user_to_idx and mid in movie_to_idx:
                train_users.append(user_to_idx[uid])
                train_movies.append(movie_to_idx[mid])
                train_ratings.append(r["rating"])
                
        user_tensor = torch.tensor(train_users, dtype=torch.long)
        movie_tensor = torch.tensor(train_movies, dtype=torch.long)
        rating_tensor = torch.tensor(train_ratings, dtype=torch.float32)
        
        # Build GNN Edges (all rating interactions)
        user_to_movie_edges = torch.stack([user_tensor, movie_tensor], dim=0) # [2, E]
        movie_to_user_edges = torch.stack([movie_tensor, user_tensor], dim=0) # [2, E]
        
        # Device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Training on device: {device}")
        
        # Transfer data to device
        movie_genres_tensor = torch.tensor(movie_genres_np, dtype=torch.float32).to(device)
        user_to_movie_edges = user_to_movie_edges.to(device)
        movie_to_user_edges = movie_to_user_edges.to(device)
        user_tensor = user_tensor.to(device)
        movie_tensor = movie_tensor.to(device)
        rating_tensor = rating_tensor.to(device)
        
        # Initialize model
        model = GraphSAGEModel(
            num_users=len(user_to_idx),
            num_movies=len(movie_to_idx),
            num_genres=mappings["num_genres"],
            embedding_dim=embedding_dim
        ).to(device)
        
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
        criterion = nn.MSELoss()
        
        dataset_size = len(train_users)
        
        # Training loop
        model.train()
        epoch_losses = []
        for epoch in range(epochs):
            permutation = torch.randperm(dataset_size)
            epoch_loss = 0.0
            num_batches = 0
            
            for i in range(0, dataset_size, batch_size):
                indices = permutation[i:i + batch_size]
                batch_users = user_tensor[indices]
                batch_movies = movie_tensor[indices]
                batch_ratings = rating_tensor[indices]
                
                optimizer.zero_grad()
                pred, _, _ = model(
                    batch_users, 
                    batch_movies, 
                    movie_genres_tensor, 
                    user_to_movie_edges, 
                    movie_to_user_edges
                )
                
                loss = criterion(pred, batch_ratings)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
                
            mean_loss = epoch_loss / num_batches
            epoch_losses.append(mean_loss)
            print(f"Epoch {epoch+1}/{epochs} | Loss: {mean_loss:.4f}")
            
        # Get final embeddings and save
        model.eval()
        with torch.no_grad():
            _, final_user_emb, final_movie_emb = model(
                user_tensor[:10], # dummy batch to trigger forward
                movie_tensor[:10],
                movie_genres_tensor,
                user_to_movie_edges,
                movie_to_user_edges
            )
            
        # Save checkpoints
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "user_embeddings": final_user_emb.cpu().numpy().tolist(),
            "movie_embeddings": final_movie_emb.cpu().numpy().tolist(),
        }
        torch.save(model.state_dict(), MODEL_PATH)
        
        # Write embeddings and metadata to mappings
        mappings["user_embeddings"] = checkpoint["user_embeddings"]
        mappings["movie_embeddings"] = checkpoint["movie_embeddings"]
        with open(MAPPINGS_PATH, "w") as f:
            json.dump(mappings, f)
            
        # Record training metrics
        metrics = {
            "final_epoch_loss": float(epoch_losses[-1]),
            "num_epochs": epochs,
            "total_ratings": len(ratings_rows),
            "num_users": len(user_to_idx),
            "num_movies": len(movie_to_idx),
            "device": str(device)
        }
        
        # Mark all ratings in database as trained
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE ratings SET is_new_feedback = 0 WHERE is_new_feedback = 1")
        conn.commit()
        conn.close()
        
        add_training_log(start_time, "completed", loss=float(epoch_losses[-1]), metrics=json.dumps(metrics))
        print("Training completed and model saved successfully.")
        return True, metrics
        
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"Error during training: {err_msg}")
        add_training_log(start_time, "failed", loss=None, metrics=str(e))
        return False, str(e)

# Dynamic Outlier Detection
def calculate_user_outliers():
    """
    Computes outlier metrics for each user dynamically from current SQL database state.
    Calculates:
    - Rating count
    - Average rating
    - Rating variance (extremely low/high is flagged)
    - Rating speed (duplicate timestamp ratio)
    - Genre contradiction score
    Returns list of users with their anomaly scores and flagged reasons.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch ratings along with movie genres
    cursor.execute("""
        SELECT r.user_id, u.username, u.email, u.phone, u.status, r.movie_id, r.rating, r.timestamp, m.genres
        FROM ratings r
        JOIN users u ON r.user_id = u.id
        JOIN movies m ON r.movie_id = m.id
        WHERE u.role != 'admin'
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
        
    df = pd.DataFrame([dict(r) for r in rows])
    
    outlier_list = []
    
    # Group by user to calculate metrics
    for user_id, group in df.groupby("user_id"):
        username = group["username"].iloc[0]
        email = group["email"].iloc[0]
        phone = group["phone"].iloc[0]
        status = group["status"].iloc[0]
        
        ratings = group["rating"].values
        timestamps = group["timestamp"].values
        
        count = len(ratings)
        mean_rating = float(np.mean(ratings))
        variance = float(np.var(ratings)) if count > 1 else 0.0
        
        # 1. Rating Speed / Velocity (duplicate timestamps)
        # Ratio of ratings submitted at exact same second
        unique_timestamps = len(np.unique(timestamps))
        speed_anomaly_ratio = (count - unique_timestamps) / count if count > 0 else 0.0
        
        # 2. Rating Variance Anomaly
        # Flat lining: user rates everything exactly 5.0 (variance = 0)
        is_flatliner = (variance < 0.1) and (count >= 5)
        # Random noise: user rates items extremely randomly (high variance)
        is_hyper_variable = (variance > 2.2) and (count >= 5)
        
        # 3. Genre Contradiction
        # Explode genres to calculate genre preference
        genres_expanded = []
        for index, row in group.iterrows():
            if row["genres"]:
                for g in row["genres"].split(","):
                    genres_expanded.append({"genre": g, "rating": row["rating"]})
                    
        contradiction_score = 0.0
        flagged_genres = []
        if genres_expanded:
            df_g = pd.DataFrame(genres_expanded)
            genre_stats = df_g.groupby("genre")["rating"].agg(["mean", "var", "count"])
            # Contradiction: high variance inside the same genre.
            # Example: user rates Romance movie as 5 and another Romance movie as 1, across many romance movies.
            for g, r_stat in genre_stats.iterrows():
                if r_stat["count"] >= 3 and r_stat["var"] > 2.0:
                    contradiction_score += 1.0
                    flagged_genres.append(g)
                    
        # Compute dynamic anomaly score (0 to 100)
        anomaly_score = 0.0
        reasons = []
        
        # Rules for anomaly score
        if speed_anomaly_ratio > 0.4:
            anomaly_score += 40.0
            reasons.append(f"High Speed: {speed_anomaly_ratio:.1%} ratings submitted in identical seconds (bot activity).")
        if is_flatliner:
            anomaly_score += 30.0
            reasons.append(f"Flatline: Gave identical rating ({mean_rating:.1f}) to all {count} movies (low effort).")
        if is_hyper_variable:
            anomaly_score += 25.0
            reasons.append(f"Hyper-Variable: Extreme variance ({variance:.2f}) in rating behaviors (random spam).")
        if contradiction_score > 0:
            anomaly_score += min(30.0, contradiction_score * 15.0)
            reasons.append(f"Genre Contradictions: Highly inconsistent ratings in specific genres: {', '.join(flagged_genres)}.")
        if count > 200:
            anomaly_score += 10.0
            reasons.append(f"Hyper-Active: Rated {count} movies (potential bot).")
            
        anomaly_score = min(100.0, anomaly_score)
        
        outlier_list.append({
            "user_id": int(user_id),
            "username": username,
            "email": email,
            "phone": phone,
            "status": status,
            "rating_count": int(count),
            "avg_rating": round(mean_rating, 2),
            "rating_variance": round(variance, 2),
            "duplicate_timestamp_ratio": round(speed_anomaly_ratio, 2),
            "anomaly_score": round(anomaly_score, 1),
            "reasons": reasons
        })
        
    # Sort by anomaly score descending
    outlier_list.sort(key=lambda x: x["anomaly_score"], reverse=True)
    return outlier_list

if __name__ == "__main__":
    init_db()
    train_model(epochs=5)
