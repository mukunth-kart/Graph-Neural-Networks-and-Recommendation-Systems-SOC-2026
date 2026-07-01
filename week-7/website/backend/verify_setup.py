import sys
import os

print("=" * 50)
print("VERIFYING MOVIELENS GNN RECOMMENDATION SYSTEM SETUP")
print("=" * 50)

# 1. Check Python version
print(f"Python Version: {sys.version}")

# 2. Check Package Imports
required_packages = {
    "fastapi": "FastAPI (web framework)",
    "uvicorn": "Uvicorn (web server)",
    "torch": "PyTorch (deep learning backend)",
    "pandas": "Pandas (data manipulation)",
    "numpy": "NumPy (linear algebra)",
    "sklearn": "Scikit-Learn (metrics)",
    "passlib": "Passlib (password hashing)",
    "jose": "Jose (JWT tokens)",
    "requests": "Requests (http requests)"
}

print("\nChecking packages:")
all_passed = True
for pkg, desc in required_packages.items():
    try:
        __import__(pkg)
        print(f"  [✓] {pkg:<12} - Installed")
    except ImportError:
        print(f"  [✗] {pkg:<12} - NOT INSTALLED ({desc})")
        all_passed = False

if not all_passed:
    print("\n[!] Please run: pip install -r requirements.txt")
    print("=" * 50)
    sys.exit(1)

# 3. Check CUDA & PyTorch
import torch
print("\nPyTorch Details:")
print(f"  PyTorch Version: {torch.__version__}")
print(f"  CUDA Available:  {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  CUDA Device:     {torch.cuda.get_device_name(0)}")
    print(f"  CUDA VRAM:       {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("  [!] Running on CPU. Recommend checking CUDA installation to train on GPU.")

# 4. Check SQLite
print("\nChecking SQLite database...")
try:
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "recommender.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sqlite_version()")
    ver = cursor.fetchone()[0]
    print(f"  [✓] SQLite Version: {ver}")
    conn.close()
except Exception as e:
    print(f"  [✗] Database connection failed: {e}")

# 5. Check GraphSAGE initialization
print("\nChecking GraphSAGE GNN Model initialization...")
try:
    from model import GraphSAGEModel
    # Initialize a dummy model
    model = GraphSAGEModel(num_users=10, num_movies=10, num_genres=19, embedding_dim=16)
    
    # Run a mock forward pass
    user_ids = torch.tensor([0, 1, 2], dtype=torch.long)
    movie_ids = torch.tensor([0, 1, 2], dtype=torch.long)
    movie_genres = torch.zeros((10, 19), dtype=torch.float32)
    movie_genres[0, 1] = 1.0
    movie_genres[1, 2] = 1.0
    
    user_to_movie = torch.tensor([[0, 1, 2], [0, 1, 2]], dtype=torch.long)
    movie_to_user = torch.tensor([[0, 1, 2], [0, 1, 2]], dtype=torch.long)
    
    pred, _, _ = model(user_ids, movie_ids, movie_genres, user_to_movie, movie_to_user)
    print(f"  [✓] Model successfully initialized and output shape: {pred.shape}")
    print("=" * 50)
    print("VERIFICATION COMPLETED: Setup is correct!")
    print("=" * 50)
except Exception as e:
    import traceback
    print(f"  [✗] GraphSAGE verification failed: {e}")
    traceback.print_exc()
    print("=" * 50)
