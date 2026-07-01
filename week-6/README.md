#  Week -6 (Another week another paper🥲)

> **Paper:** *Inductive Representation Learning on Large Graphs*
> Hamilton, Ying & Leskovec — NeurIPS 2017
> [`arxiv.org/abs/1706.02216`](https://arxiv.org/abs/1706.02216)

Don't panic. This repo has everything you need to go from zero to understanding GraphSAGE — paper, blogs, code, videos, anything you need. 🧠


---

## 🤔 What even is GraphSAGE?


- Old methods (GCN, DeepWalk) are **transductive** — they can only make predictions for nodes they've already seen. Add a new node? Retrain from scratch. Not great.
- **GraphSAGE** fixes this. It learns *how* to aggregate neighborhood info rather than memorizing fixed embeddings. So it generalizes to **unseen nodes** without retraining.
- The name stands for **Graph SA**mple and a**GG**r**E**gate — it samples a fixed number of neighbors, aggregates their features, and produces a node embedding.
- Real-world users: **Pinterest** (18B edges, PinSAGE), **UberEats** (600k+ restaurants), **Reddit**, citation networks.

### The core idea in one diagram

```
        [Node v's neighbors]
               ↓
         SAMPLE a few
               ↓
         AGGREGATE their features  ──→  h_neighbors
               ↓
         CONCAT(h_v_prev, h_neighbors)
               ↓
         Linear layer + activation
               ↓
         New embedding h_v
```

Repeat this for K layers (hops). That's literally the whole algorithm.

---


## 📄 The Paper

| Resource | Link |
|----------|------|
| 📑 Original Paper (NeurIPS 2017) | [arxiv.org/abs/1706.02216](https://arxiv.org/abs/1706.02216) |
| 🌐 Official Stanford Page | [snap.stanford.edu/graphsage](https://snap.stanford.edu/graphsage/) |

**Sections to focus on (first read):**
- Abstract + Intro — understand the motivation
- Section 3 — the actual algorithm (Algorithm 1 is the key thing)
- Section 3.3 — the aggregator variants (mean, LSTM, pooling)
- Results — just skim, see what datasets they test on

**Sections you can skip on first read:**
- Section 4 (theoretical analysis) — come back to this later
- Appendix — if you wish to goo deeep 

---

## 🎥 Video Lectures

Watch these **before** reading the paper. Makes everything click way faster.

| Title | Source | When to Watch |
|-------|--------|---------------|
| [Graph Neural Networks — Stanford CS224W Lecture 8](https://www.youtube.com/watch?v=LLUxwHc7O4A) | Jure Leskovec (the author!) | Before reading |
| [Large-scale Graph Representation Learning](https://www.youtube.com/watch?v=oQL4E1gK3VU) | Jure Leskovec @ ICLR | After first read |



---

## 📖 Blogs & Tutorials 

### 1. Big Picture 
- [**GraphSAGE: Scaling up GNNs** — Towards Data Science](https://towardsdatascience.com/introduction-to-graphsage-in-python-a9e7f9ecf9d7/)
  Great intro, covers Pinterest/UberEats use cases, explains mini-batching and aggregators clearly.

- [**Graph SAGE — IIT Roorkee DSG Blog**](https://dsgiitr.in/blogs/graph_sage/)
  Solid conceptual breakdown, nice diagrams, explains parameter sharing well.

### 2.Deep Dive
- [**GraphSAGE Sampling & Aggregation** — apxml.com](https://apxml.com/courses/introduction-to-graph-neural-networks/chapter-3-foundational-gnn-architectures/graphsage-model)
  Best breakdown of the two-step sample → aggregate process with the math.

- [**Introduction to GraphSAGE** — Weights & Biases](https://wandb.ai/graph-neural-networks/GraphSAGE/reports/An-Introduction-to-GraphSAGE--Vmlldzo1MTEwNzQ1)
  Code examples in PyTorch Geometric + interactive visualizations.

### 3. Hands-on Coding
- [**Coding GraphSAGE from Scratch** — Syed Rizvi (June 2024)](https://syedarizvi.com/blog/2024/graphsage-from-scratch/)
  Builds the full thing from scratch in PyTorch — no PyG, no abstractions. Best for understanding.

- [**Comprehensive Case Study with PyTorch Geometric** — TDS (2024)](https://towardsdatascience.com/a-comprehensive-case-study-of-graphsage-algorithm-with-hands-on-experience-using-pytorchgeometric-6fc631ab1067/)
  Uses the OGB products dataset (Amazon co-purchase graph). Real-world scale.

---

## 💻 GitHub Repos for Practice 

These are ordered from "easiest to get started" to "closest to the original paper."

**[`dsgiitr/graph_nets`](https://github.com/dsgiitr/graph_nets)**
- Covers DeepWalk → GCN → **GraphSAGE** → GAT in one repo
- Has a Jupyter notebook with code + explanations side by side
- Great if you want to see GraphSAGE in context of other GNN papers

```bash
git clone https://github.com/dsgiitr/graph_nets
cd graph_nets/GraphSAGE
jupyter notebook GraphSAGE_Code+Blog.ipynb
```


---

## 📚 Further Reading (When You're Ready to Go Deeper)

| Resource | What it covers |
|----------|---------------|
| [PinSAGE (Ying et al., 2018)](https://arxiv.org/abs/1806.01973) | GraphSAGE at Pinterest scale |
| [Graph Representation Learning Book](https://www.cs.mcgill.ca/~wlh/grl_book/) | Free book by Hamilton (GraphSAGE author) |
| [PyTorch Geometric Docs](https://pytorch-geometric.readthedocs.io/) | SAGEConv implementation reference |

## Good news for you This week no assignment submission required 😉 ,As This much material should be sufficient to keep you busy.
