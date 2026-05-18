# Week 1 Assignment: Mathematical Foundations, Data Exploration, and Predictive Modeling

Welcome to your Week 1 assignment! Here, you will apply all that you have learnt in the right places.

---

## Part 1: NumPy & Linear Algebra – Gram-Schmidt Orthonormalization

Gram-Schmidt Orthonormalization should be familiar from MA110, and even otherwise is a basic algorithm. To give you some PTSD we shall implement this in numpy(honestly just implementing since you are already familiar with it).

### Your Task

Write a Python function `gram_schmidt(A)` that takes a linearly independent set of vectors (stored as columns in a 2D NumPy array $A$) and returns an orthonormal basis matrix $Q$ using the classical Gram-Schmidt process. **You are forbidden from using `np.linalg.qr` or external optimization libraries.**

Recall that for a set of vectors $v_1, v_2, \dots, v_n$, the orthogonal vectors $u_i$ are computed as:

$$u_k = v_k - \sum_{j=1}^{k-1} \frac{\langle v_k, u_j \rangle}{\langle u_j, u_j \rangle} u_j$$

To transform these into an *orthonormal* basis, normalize each vector:

$$e_k = \frac{u_k}{\|u_k\|}$$

### Requirements

* Your code must utilize vectorized NumPy operations where possible (e.g., `np.dot`, the `@` operator, or `np.linalg.norm`).
* Include a verification step in your script proving that $Q^T Q = I$ (the identity matrix) within a reasonable floating-point tolerance using `np.allclose`.

---

## Part 2: Pandas & Visualization – The Submission Delay Dataset

We have provided a course assignment submission dataset containing roughly 100 anonymous features(named x_*). To simulate real data engineering workflows (and to force you to use your scripting tools instead of opening it in Microsoft Excel), the file is packaged as a Python binary format: [`submission_data.pkl`](submission_data.pkl).

### Phase 1: Data Preparation & Exploration

1. **Load the Data:** Read `submission_data.pkl` into a Pandas DataFrame. Programmatically inspect its shape, column data types, and check for missing values.
2. **Target Labeling:** Create a binary classification target column named `target`. If the `Submission_Delay` column is $> 0$, assign it a value of **1** (Late). If it is $\le 0$, assign it a value of **0** (On Time/Early). Drop the original continuous `submission_delay` column to avoid data leakage.
3. **Feature Normalization:** Because the 100 features may exist on drastically different scales(you can check this with pandas), normalize the continuous feature columns using a Standard Scaler approach (shifting the mean to 0 and variance to 1). *Do not normalize your binary target column.*

### Phase 2: Feature Correlation & Heatmaps

1. Calculate the Pearson correlation coefficient between all 100 features and your new binary `target` variable.
2. Identify the **top 15 features** that display the strongest absolute correlation with the target.
3. Using **Seaborn**, plot a localized correlation heatmap of *only* these top 15 features.
4. **Written Summary:** Analyze the heatmap. Explain what the correlations mean, and look closely for multi-collinearity (high correlation between independent features). Explain why multi-collinearity can introduce redundancy into a model.

### Phase 3: Dimensionality Reduction (UMAP vs. t-SNE)

You will treat the 100 features as high-dimensional embeddings and project them down to 2D space to see if late and on-time submissions possess distinct geometric signatures also make a similar seperate umap of the top-15 features you found in Phase 2. *(Note: You will need to install `umap-learn` via pip/conda if you haven't already).*

1. Run **t-SNE** (`sklearn.manifold.TSNE`) on your normalized features and plot the 2D scatter plot, color-coding the points by your binary target labels.
2. Run **UMAP** on the same dataset and generate a matching 2D scatter plot.
3. **Written Summary:** Compare the two plots. Which algorithm preserved the global structure of the data better? Do the late and on-time points form clean clusters, or are they deeply intermingled? Compare the plots of 100 features with 15 features, which looks to have better clustering?

---

## Part 3: Predictive Modeling & Evaluation

Now that you have explored the dataset's geometry and correlations, you will train machine learning models to predict whether a submission will be delayed based on your top selected features.

Since your target variable is binary (0 or 1), you will use classification variants of standard models: **Logistic Regression** (the classification framework built on linear foundations), **Support Vector Classifiers (SVC)**, and **Random Forest Classifiers**.

### Your Task

1. Split your dataset into an **80% training set** and a **20% testing set** using `sklearn.model_selection.train_test_split`. Restrict your training features ($X$) to the top features identified during your correlation analysis.
2. Train all three models on the training data and evaluate their performance on the testing data.
3. Use Scikit-Learn’s `classification_report` to extract evaluation data and organize your results into a clean markdown table inside your final submission report.

### Evaluation Metrics Table

Your final report must include a populated table tracking the performance of each model on the test split:

| Model | Accuracy | Precision (Class 1) | Recall (Class 1) | F1-Score (Class 1) | AUC_ROC |
| --- | --- | --- | --- | --- |---|
| **Logistic Regression** | *Value* | *Value* | *Value* | *Value* | *Value* |
| **Support Vector Machine (SVC)** | *Value* | *Value* | *Value* | *Value* | *Value* |
| **Random Forest Classifier** | *Value* | *Value* | *Value* | *Value* | *Value* |

### Written Analysis Requirements

In your final summary, provide a clear, unambiguous response to the following:

* **Deconstruct the Metrics:** Based on the output of Scikit-Learn's `classification_report`, explain exactly what **Accuracy**, **Precision**, **Recall**, **F1-Score** and the **AUC-ROC** represent in the context of this specific problem. (e.g., What does a low recall score for Class 1 practically mean for tracking late submissions?)
* **Model Selection:** Which model performed the best overall? Why do you think that specific architecture succeeded over the others on this dataset?
* **Practical Application:** Imagine this model is deployed by an operations team at an organization or educational institution. Explain what practical purpose this model serves. 
* **More Features?:** As a test try implementing the models with all features and see if it gives you something better.

---

## Part 4: NumPy in Physics – Simulating Quantum Wavefunctions

To wrap up this assignment, you will step away from data science dataframes and use NumPy to visualize one of the foundational equations of classical quantum mechanics and semiconductor physics: the **1D Time-Independent Schrödinger Equation (TISE)**.(Basically, MA110 PTSD done let's do Ph110 now, on a side note my hands were trembling from my own PTSD while writing this up)

The TISE is expressed as:

$$-\frac{\hbar^2}{2m} \frac{d^2\psi(x)}{dx^2} + V(x)\psi(x) = E\psi(x)$$

Where $\psi(x)$ is the wavefunction, $V(x)$ is the potential energy, $E$ is the total energy of the particle, $m$ is the mass, and $\hbar$ is the reduced Planck constant. 

### Your Task
Assume a simplified system where the potential $V(x) = V$ and total energy $E$ are **completely constant** across a spatial domain of $x \in [0, 5]$. To make implementation simple, we will use atomic units where $\hbar = 1$ and $m = 1$. 

Depending on the relative values of $E$ and $V$, the solution to this differential equation changes drastically. Assuming standard physical boundary conditions at $x = 0$, the spatial evolution of the wavefunction behaves as follows:

1. **Scattering Case ($E > V$):** The particle has enough energy to move freely. The solution is oscillatory:
   $$\psi(x) = \cos(k x) \quad \text{where} \quad k = \sqrt{2(E - V)}$$

2. **Bound Case ($E < V$):** The particle encounters a barrier higher than its energy. In quantum mechanics, it doesn't instantly bounce back; its probability density decays exponentially (quantum tunneling):
   $$\psi(x) = e^{-\kappa x} \quad \text{where} \quad \kappa = \sqrt{2(V - E)}$$

3. **Critical Threshold ($E = V$):** The kinetic energy is exactly zero, resulting in a linear flat-state:
   $$\psi(x) = 1$$

### Implementation Requirements
1. Define a continuous spatial spatial grid array `x` from $0$ to $5$ with at least 500 points using `np.linspace`.
2. Write a single vectorized NumPy function `simulate_wavefunction(x, E, V)` that evaluates the correct mathematical regime based on the scalar inputs of $E$ and $V$. Use array operations to compute $\psi(x)$.
3. Using **Matplotlib**, generate a single, clear plot displaying the wavefunction $\psi(x)$ for the following three distinct scenarios:
   * **Case A (Oscillatory):** $E = 12$, $V = 2$
   * **Case B (Decaying):** $E = 2$, $V = 7$
   * **Case C (Threshold):** $E = 5$, $V = 5$
4. Ensure your plot includes appropriate axis labels, a title, distinct line styles/colors for each case, and a prominent legend.

### Written Summary Requirements
In your `summary.md` file, briefly comment on the plot:
* Explain how the frequency of oscillation in Case A would change if you significantly increased the total energy $E$ further away from $V$.
* What physical meaning does a rapidly decaying wavefunction (Case B) have regarding the probability of finding an electron inside a highly resistive potential barrier?

___

## 🌟 Bonus Part: Numerical Quantum Mechanics – The Finite Difference Method

In real-world quantum mechanics and device physics, potential functions $V(x)$ are rarely perfectly flat constants. When dealing with complex geometries—like semiconductor heterostructure quantum wells or molecular bonds—analytical solutions do not exist. We must solve the Schrödinger equation numerically.

In this bonus section, you will use the **Finite Difference Method (FDM)** to convert the continuous 1D Time-Independent Schrödinger Equation into a matrix eigenvalue problem ($H\psi = E\psi$) and solve it using NumPy. This is for those who want to go the extra mile and also sheds some light on how numpy used to be used.

### The Math: Discretizing the Hamiltonian
To solve the equation numerically on a spatial grid of $N$ points with spacing $\Delta x$, we approximate the second spatial derivative of the wavefunction at point $x_i$ using the central difference formula:

$$\frac{d^2\psi(x_i)}{dx^2} \approx \frac{\psi_{i+1} - 2\psi_i + \psi_{i-1}}{\Delta x^2}$$

Substituting this back into the TISE (assuming $\hbar = 1$ and $m = 1$) yields the discrete equation for each point $i$:

$$-\frac{1}{2\Delta x^2}\psi_{i-1} + \left(\frac{1}{\Delta x^2} + V(x_i)\right)\psi_i - \frac{1}{2\Delta x^2}\psi_{i+1} = E\psi_i$$

This can be beautifully rewritten as a symmetric, tridiagonal matrix equation, where the Hamiltonian matrix $H$ acts on the vector of wavefunction values $\Psi = [\psi_1, \psi_2, \dots, \psi_N]^T$:

*   **Main Diagonal elements ($H_{i,i}$):** $\frac{1}{\Delta x^2} + V(x_i)$
*   **Off-Diagonal elements ($H_{i,i+1}$ and $H_{i,i-1}$):** $-\frac{1}{2\Delta x^2}$

### Your Task: The Quantum Harmonic Oscillator
You will simulate a particle trapped inside a non-constant **Parabolic Potential Well** (a Quantum Harmonic Oscillator), defined by the potential function:

$$V(x) = \frac{1}{2} k x^2$$

Use a spatial domain of $x \in [-5, 5]$ with $N = 500$ points, and set the spring constant $k = 10$.

1. **Construct the Potential Vector:** Compute the array $V$ for your spatial grid.
2. **Build the Hamiltonian Matrix ($H$):** Create an $N \times N$ matrix. Use `np.diag` or matrix slicing to efficiently populate the main diagonal and the immediate upper/lower off-diagonals. 
3. **Solve the Eigenvalue Problem:** Use NumPy’s specialized solver for symmetric/Hermitian matrices, `np.linalg.eigh(H)`. This function returns sorted eigenvalues (energy levels $E$) and their corresponding eigenvectors (wavefunctions $\psi$).
4. **Normalize the Wavefunctions:** Ensure that the total probability integrates to 1 for your discrete states. For a discrete grid, ensure that for each chosen eigenvector:
   $$\sum_{i=1}^{N} |\psi_i|^2 \Delta x = 1$$

### Visualization Requirements
Using **Matplotlib**, create a comprehensive visualization of the quantum well:
*   Plot the potential well curve $V(x)$ vs $x$ as a background reference line.
*   Find the lowest three energy levels ($E_0$, $E_1$, $E_2$) and their corresponding wavefunctions ($\psi_0$, $\psi_1$, $\psi_2$).
*   To make the plot readable, scale the wavefunctions by a visible factor and **shift them vertically** by adding their corresponding energy level value (i.e., plot $E_n+\alpha\psi_n(x)$). Draw a dashed horizontal line at each energy level $E_n$ to serve as a baseline.

### Written Summary Requirements (Bonus)
In your `summary.md` file, provide a brief physical interpretation of your numerical results:
*   Look at the analytical ground state energy for a quantum harmonic oscillator, which is theoretically $E_n = \left(n + \frac{1}{2}\right)\hbar\omega$. Given $\hbar=1, m=1,$ and $\omega = \sqrt{k/m} = \sqrt{10}$, check how close your numerically computed ground state energy ($E_0$) matches the theoretical prediction.
*   Observe the number of times each wavefunction crosses its baseline axis (the number of zero-crossing nodes). What is the exact mathematical relationship between the quantum state index $n$ ($n=0, 1, 2\dots$) and the number of nodes in its wavefunction?

___

## Submission Deliverables

* `gram_schmidt.py`: Your functional script containing your custom matrix operations and identity verification checks.
* `TISE.py`: Your script for solving 1D-TISE.
* `data_exploration_and_modeling.ipynb`: A clean, fully documented Jupyter Notebook containing your Pandas pipelines, Seaborn heatmaps, UMAP/t-SNE comparisons, and Scikit-Learn modeling pipelines.
* `summary.md`: A concise markdown file answering all written prompts across Parts 2,3,4 and bonus if done.
* `BONUS.py`: If done, then please do submit.

___

## How to Submit?
* Push all your submissions into your repo.
* Mentors will clone at deadline time and explore it.
* Keep them all under the assignment folder.

Happy Learning!!!