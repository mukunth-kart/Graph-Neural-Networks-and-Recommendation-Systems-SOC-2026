# GNN-Based Recommendation System

Welcome to the pre-finale week of our Graph Neural Network (GNN) journey! This week's focus is on building and optimizing a recommendation system using GNN architectures.

The repository contains a full-stack setup featuring a web interface connected to a machine learning backend.

---

## 🚀 Project Structure & Key Files

The core machine learning logic is located in the `backend/` directory. As a data scientist, your primary focus should be on optimizing the pipeline:

* `backend/model.py`: Defines the GNN architecture (currently a basic placeholder).
* `backend/train.py`: Handles the training, evaluation, and logging loop.
* `frontend/`: Contains the front-end interface and its respective installation guidelines.

---

## 🎯 Core Objectives & Expectations

Your main task is to replace the placeholder implementation with a robust graph-based recommendation model. Try out different models and report your observations.

### 1. Implement a Robust GNN Model

Modify `model.py` and `train.py` to build an optimized link prediction or node recommendation pipeline. While we covered specific architectures in class, you are encouraged to explore any modern GNN variant suitable for collaborative filtering.

### 2. Alternative Path: Standalone MovieLens Implementation

If you prefer to focus purely on the machine learning components without interacting with the web framework, you can fulfill this week's requirements by:

* Developing a standalone **GraphSAGE** link prediction model.
* Training and evaluating it directly on the **MovieLens** dataset.
* Documenting and reporting the relevant performance metrics (e.g., RMSE, Recall@K, Precision@K).

> 💡 **Recommendation:** Prioritize model architecture and evaluation metrics over front-end tweaks. The web UI is functional, but your primary objective is the graph data science component.

---

## 🛠️ Setup & Configuration

### Web Interface & Backend

To spin up the web application local server, please follow the dedicated instructions in the website directory:

```bash
cd website
# Refer to the README.md inside this folder for specific setup steps

```

### Admin Credentials

The web portal includes an administrative dashboard with options to trigger model retraining manually. Use the following credentials to access the admin panel:

| Field | Value |
| --- | --- |
| **Username** | `admin` |
| **Password** | `admin123` |

*Note: You can also register new standard user accounts directly through the interface sign-up flow.*

---

## 🤝 Contributing & Feedback

This project template is actively being improved. If you encounter bugs in the interface or have suggestions for structural enhancements, feel free to open an issue or share feedback. Contributing to the codebase infrastructure is entirely voluntary.