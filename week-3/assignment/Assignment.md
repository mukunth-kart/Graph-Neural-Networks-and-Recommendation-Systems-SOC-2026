# 🚀 Time to Get Working!

### 1. MLP from Scratch (NumPy)

* **Task:** Code a Multi-Layer Perceptron (MLP) entirely from scratch using only **NumPy** (no PyTorch/TensorFlow).
* **Details:** You must manually implement:
* The forward pass
* The backpropagation algorithm
* Weight initialization and updates


* **Dataset:** Train and evaluate it on the **MNIST** dataset.
* **Note:** *If you have already done this for prior coursework, you may submit that code. However, ensure you thoroughly review it to solidify your understanding of the underlying math.*

---

### 2. PyTorch Practice (MLP vs. CNN)

* **Task:** Implement both an **MLP** and a **CNN** classifier using **PyTorch**.
* **Dataset:** Train both models on the **MNIST** dataset.
* **Evaluation:** Compare their performance (accuracy, training speed, parameter count) and analyze the results.

---

### 3. Theoretical & Practical Proof: $y = x$

* **Theory:** Prove the existence of an MLP (including its weights) that can perfectly learn the identity function $y = x$.
* **Critical Questions to Answer:**
* Is an activation function needed here? Why or why not?
* What do you expect the exact weights and biases to be?
* *Defend your design—simpler architectures with fewer layers are strongly preferred.*


* **Code Implementation:** Build this specific network, train/run it, and inspect the final weights.
* *Are the weights exactly what you expected? If not, explain why.*



---

### 4. Theoretical & Practical Proof: $y = x^2$

* **Task:** Repeat all the steps from **Task 3**, but this time for the non-linear function $y = x^2$.
* **Key Focus:** Pay close attention to how the need for an activation function changes when moving from a linear to a non-linear target function.

---

### 5. A few combos

When training a neural network for classification tasks, which loss function typically performs better: **Mean Squared Error (MSE) with tanh** or **Cross-Entropy with Softmax**?