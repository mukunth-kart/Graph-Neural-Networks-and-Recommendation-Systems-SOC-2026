import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt

import database as db
from train import train_model, calculate_user_outliers, MODEL_PATH, MAPPINGS_PATH

# Auth constants
SECRET_KEY = "movielens_gnn_secret_key_extremely_secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

app = FastAPI(title="MovieLens GraphSAGE Recommender API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
@app.on_event("startup")
def startup_db():
    db.init_db()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Pydantic schemas
class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    user_id: int

class RatingSubmit(BaseModel):
    movie_id: int
    rating: float

class RecommendationRequest(BaseModel):
    seed_movie_ids: List[int]

class UserStatusUpdate(BaseModel):
    status: str

# Helper functions for Auth
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    if user["status"] == "banned":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is banned."
        )
    return user

def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required."
        )
    return current_user

# ----------------- AUTH ROUTES -----------------

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password required.")
    success, msg = db.create_user(req.username, req.email, req.phone, req.password, "user")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

@app.post("/api/auth/token", response_model=Token)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user_by_username(form_data.username)
    if not user or not db.verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user["status"] == "banned":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned due to anomalous rating activity."
        )
        
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
        "user_id": user["id"]
    }

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "phone": current_user["phone"],
        "role": current_user["role"],
        "status": current_user["status"]
    }

# ----------------- MOVIE ROUTES -----------------

@app.get("/api/movies")
def list_movies(
    q: Optional[str] = None, 
    genre: Optional[str] = None, 
    limit: int = 30, 
    offset: int = 0
):
    movies = db.search_movies(query_str=q, genre=genre, limit=limit, offset=offset)
    return movies

# ----------------- RATINGS ROUTES -----------------

@app.post("/api/ratings")
def submit_rating(rating_data: RatingSubmit, current_user: dict = Depends(get_current_user)):
    success, msg = db.add_user_rating(
        user_id=current_user["id"],
        movie_id=rating_data.movie_id,
        rating=rating_data.rating,
        timestamp=int(time.time())
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": "Feedback saved."}

@app.get("/api/ratings/my-ratings")
def my_ratings(current_user: dict = Depends(get_current_user)):
    return db.get_user_ratings(current_user["id"])

# ----------------- RECOMMENDATION ENGINE -----------------

@app.post("/api/movies/recommend")
def get_recommendations(req: RecommendationRequest, current_user: dict = Depends(get_current_user)):
    """
    Computes movie recommendations dynamically:
    1. Read user's explicit seed movie interests from onboarding/selection.
    2. Read user's rating history from SQLite DB.
    3. Merge seed movies and user-liked movies (ratings >= 4.0) to create their preference set.
    4. If the GNN model is trained, use embedding cosine similarities between preference set and candidates.
    5. If model is not trained, fallback to recommending high-average-rating movies of matching genres.
    """
    db_ratings = db.get_user_ratings(current_user["id"])
    
    # Positive feedback movies from DB (rating >= 3.5)
    liked_db_movies = [r["movie_id"] for r in db_ratings if r["rating"] >= 3.5]
    
    # Combine with seed movies chosen in UI
    user_liked_ids = list(set(req.seed_movie_ids + liked_db_movies))
    
    # Exclude movies the user has already rated (we don't recommend what they already rated)
    already_rated_ids = set([r["movie_id"] for r in db_ratings])
    
    # Load GNN mapping and embeddings
    if os.path.exists(MAPPINGS_PATH) and os.path.exists(MODEL_PATH):
        try:
            with open(MAPPINGS_PATH, "r") as f:
                mappings = json.load(f)
                
            movie_to_idx = mappings["movie_to_idx"]
            movie_embeddings = mappings["movie_embeddings"]
            
            # Map liked movies to their indexes and gather embeddings
            liked_indices = [movie_to_idx[str(mid)] for mid in user_liked_ids if str(mid) in movie_to_idx]
            
            if not liked_indices:
                # Fallback if user hasn't liked anything or no valid indices
                return get_fallback_recommendations(already_rated_ids, limit=12)
                
            # Compute average embedding profile for the user
            movie_emb_arr = np.array(movie_embeddings) # [N_movies, D]
            user_profile = np.mean(movie_emb_arr[liked_indices], axis=0)
            
            # Compute similarity with all movies
            # Since embeddings are L2 normalized, cosine similarity is just dot product
            # Normalize user profile first
            user_profile_norm = user_profile / np.linalg.norm(user_profile)
            similarities = np.dot(movie_emb_arr, user_profile_norm) # [N_movies]
            
            # Sort candidate movies
            recommended_list = []
            idx_to_movie = mappings["idx_to_movie"]
            
            # Sort indices by similarity descending
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Get details of candidate movies
            all_movie_ids = [int(idx_to_movie[str(idx)]) for idx in sorted_indices]
            
            # Filter out already rated movies and liked seed movies
            candidates = [mid for mid in all_movie_ids if mid not in already_rated_ids and mid not in user_liked_ids]
            
            # Get metadata from DB for top 12
            top_candidates = candidates[:12]
            movies_meta = db.get_movies_by_ids(top_candidates)
            
            # Format output
            for mid in top_candidates:
                if mid in movies_meta:
                    movie_idx = movie_to_idx[str(mid)]
                    recommended_list.append({
                        **movies_meta[mid],
                        "similarity_score": float(similarities[movie_idx])
                    })
            return recommended_list
            
        except Exception as e:
            print(f"Error computing GNN recommendations: {e}")
            
    # Fallback recommendations (popularity + genre match)
    return get_fallback_recommendations(already_rated_ids, user_liked_ids, limit=12)

def get_fallback_recommendations(exclude_ids, seed_ids=None, limit=12):
    # Generates recommendations based on movie genres and global average ratings
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Find favorite genres from seed movies
    genres = []
    if seed_ids:
        placeholders = ",".join(["?"] * len(seed_ids))
        cursor.execute(f"SELECT genres FROM movies WHERE id IN ({placeholders})", list(seed_ids))
        for row in cursor.fetchall():
            if row["genres"]:
                genres.extend(row["genres"].split(","))
                
    genre_clause = ""
    params = []
    
    if genres:
        # Find the most frequent genre in user's liked movies
        fav_genre = max(set(genres), key=genres.count)
        genre_clause = "AND m.genres LIKE ?"
        params.append(f"%{fav_genre}%")
        
    sql = f"""
        SELECT m.id, m.title, m.genres, m.release_year, AVG(r.rating) as avg_rating, COUNT(r.rating) as num_ratings
        FROM movies m
        LEFT JOIN ratings r ON m.id = r.movie_id
        WHERE 1=1 {genre_clause}
        GROUP BY m.id
        HAVING num_ratings >= 5
        ORDER BY avg_rating DESC, num_ratings DESC
        LIMIT 100
    """
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    recs = []
    for r in rows:
        m_id = r["id"]
        if m_id not in exclude_ids and (not seed_ids or m_id not in seed_ids):
            recs.append({
                "id": m_id,
                "title": r["title"],
                "genres": r["genres"],
                "release_year": r["release_year"],
                "similarity_score": float(r["avg_rating"]) / 5.0 # normalized mock similarity
            })
            if len(recs) >= limit:
                break
    return recs

# ----------------- ADMIN DASHBOARD ROUTES -----------------

@app.get("/api/admin/outliers")
def get_outliers(current_admin: dict = Depends(get_current_admin)):
    """
    Dynamically computes outlier metrics for all active non-admin users.
    Calculates speed of ratings, rating variance, and genre contradictions.
    """
    return calculate_user_outliers()

@app.post("/api/admin/users/{user_id}/status")
def update_user_status(
    user_id: int, 
    update: UserStatusUpdate, 
    current_admin: dict = Depends(get_current_admin)
):
    if update.status not in ["active", "banned"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be active or banned.")
        
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Cannot change status of an admin.")
        
    db.set_user_status(user_id, update.status)
    return {"message": f"User status updated to {update.status}."}

@app.get("/api/admin/users")
def get_users_list(current_admin: dict = Depends(get_current_admin)):
    return db.list_all_users()

# Background task training wrapper
def bg_training_job():
    print("Background training job started...")
    # Train for 15 epochs, using GPU if available
    train_model(epochs=12, batch_size=512, lr=0.01)

@app.post("/api/admin/train")
def trigger_training(
    background_tasks: BackgroundTasks, 
    current_admin: dict = Depends(get_current_admin)
):
    # Check if there's already a training run in progress
    logs = db.get_latest_training_logs(limit=1)
    if logs and logs[0]["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Training is already running. Please wait for the current run to finish."
        )
        
    # Queue training in background
    background_tasks.add_task(bg_training_job)
    return {"message": "Model training triggered in background."}

@app.get("/api/admin/training-status")
def get_training_status(current_admin: dict = Depends(get_current_admin)):
    return db.get_latest_training_logs(limit=15)
