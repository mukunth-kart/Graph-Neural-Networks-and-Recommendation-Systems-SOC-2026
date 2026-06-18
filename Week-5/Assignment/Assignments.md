# 📚 Week 4 Assignments: GCNs & Spectral Graph Theory


## 📝 Q1. Normalizing the Adjacency Matrix 

Consider a 3-node path graph: Node 1 — Node 2 — Node 3 (Node 2 connects to both others).

1. Write the adjacency matrix $A$ and degree matrix $D$.
2. Add self-loops to get $\tilde{A} = A + I_N$ and $\tilde{D}$.
3. Compute the symmetric normalized matrix $\hat{A} = \tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$ by hand.
4. **🧠 Conceptual:** How is the message from a high-degree neighbor weighted compared to a low-degree neighbor? Why might this be a sensible design choice?


---

## 💻 Q2. Implementing One GCN Layer 

1. Using only `numpy`, write a function implementing one GCN layer:
$$H = \text{ReLU}\left(\hat{A}\, X\, W\right), \quad \hat{A} = \tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$$
   Test it on the graph from Q1 with a random feature matrix $X$ and weight matrix $W$.
2. **⚡ Quick check:** If $N$ is the number of nodes and $F$ is the feature dimension, would you compute $(\hat{A} X) W$ or $\hat{A} (X W)$ first when $N \gg F$? Why?

---

## 🔍 Q3. Why Do We Need Self-Loops? 

The paper replaces $(I_N + D^{-1/2}AD^{-1/2})$ with the renormalized $\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$ (self-loops added *before* normalizing).

1. **📐 Short proof:** Show that the eigenvalues of $D^{-1/2}AD^{-1/2}$ lie in $[-1, 1]$. (Hint: relate it to the normalized Laplacian $L = I_N - D^{-1/2}AD^{-1/2}$, known to have eigenvalues in $[0,2]$.)
2. **🔢 Numerical check (code):** Pick any small graph (e.g. `networkx.karate_club_graph()`). Using `numpy.linalg.eigvalsh`, compute the eigenvalues of $I_N + D^{-1/2}AD^{-1/2}$ vs. the renormalized $\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2}$. Confirm the renormalized version stays tightly within $[0,1]$.
3. **🧠 Conceptual:** From a message-passing point of view, what would a node lose during aggregation if we never added the self-loop $I_N$ to $A$?

---

## 📉 Q4. Over-Smoothing in Deep GCNs 

Using PyTorch Geometric on the Cora dataset:

1. Build a GCN with $K$ stacked layers.
2. Train and record test accuracy for $K = 2, 4, 8, 16$.
3. Plot **📊 test accuracy vs. K**. You should see accuracy *drop* as the network gets deeper — this is **over-smoothing**.
4. **🧠 Conceptual:** Each GCN layer averages a node's features with its neighbors'. Explain in your own words why stacking many such layers makes all node embeddings start to look alike, and why this hurts classification performance.

 ## 📥 How to Submit Your Assignment

* **For Q1 & Q3 (The Math Proofs):** You have three options. Choose the one you are most comfortable with:
  1. **Markdown/LaTeX:** Type your proofs directly into a `Answers.md` file using `$` for inline math and `$$` for block equations.
  2. **Scanned PDF:** Write it neatly on paper, scan it, and upload it to the repo as `Math_Proofs.pdf`.(my recommendation)

* **For Q2, Q3 (Numerical Check), & Q4 (Coding):**
  * put all your code into a single Jupyter Notebook (`Week4_GCNs.ipynb`). 
  * Make sure to **run all cells** before committing and pushing to GitHub so the graders can see your printed eigenvalues and your over-smoothing plot for Q4 without having to run the code locally.(if you dont understand dont mind we would run it / show all your results in the readme file in the form of ss)
  * share a public Google Colab link at the top of your `README.md`, but make sure the permissions are set to "Anyone with the link can view".
