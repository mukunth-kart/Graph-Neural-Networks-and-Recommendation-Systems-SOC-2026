# MovieLens GraphSAGE Recommendation System

A hybrid GraphSAGE Graph Neural Network (GNN) recommendation system featuring a **FastAPI backend** (PyTorch) and a **Vite + React frontend**.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Cloning the Repository](#cloning-the-repository)
3. [Backend Setup (FastAPI + PyTorch)](#backend-setup-fastapi--pytorch)
4. [Frontend Setup (Vite + React)](#frontend-setup-vite--react)
5. [Running the Application](#running-the-application)
6. [System Verification](#system-verification)

---

## Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.8 to 3.11** (PyTorch compatible)
- **Node.js** (v18 or higher recommended) and **npm**
- **Git**

---

## Cloning the Repository

To clone the repository and navigate into the project root directory:

```bash
git clone <repository-url>
cd Recommendation
```

---

## Backend Setup (FastAPI + PyTorch)

The backend is built using FastAPI and PyTorch for running/training the GraphSAGE model.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (Command Prompt):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     source venv/bin/activate
     ```

4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Verify the backend environment and model initialization:
   ```bash
   python verify_setup.py
   ```

---

## Frontend Setup (Vite + React)

The frontend is a fast modern React application built with Vite.

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install the project dependencies:
   ```bash
   npm install
   ```

---

## Running the Application

To run the entire stack, you will need to start both the backend server and frontend development server in separate terminal windows.

### 1. Run the FastAPI Backend
With your virtual environment activated in the `backend/` folder, run:
```bash
uvicorn main:app --reload --port 8000
```
- The backend API will be available at: `http://127.0.0.1:8000`
- You can access the interactive API docs at: `http://127.0.0.1:8000/docs`

### 2. Run the React Frontend
In the `frontend/` folder, run:
```bash
npm run dev
```
- The frontend will be available at: `http://localhost:5173` (or the port specified in your terminal output).
