# Week 1 Assignment Summary

## Part 2: Data Exploration & Dimensionality Reduction

**Heatmap Analysis**
Looking at the heatmap,`Total_Words` and `Total_Characters` are correlated. They have a correlation of 0.99. Features `x_05` and `x_02` also have a high positive correlation (0.78), while `x_54` and `x_74` are basically opposites with a -0.79 correlation. 

When features are this highly correlated, it’s called multi-collinearity. It basically means we are feeding the model the exact same information twice. This is bad because it adds unnecessary data to process, and it confuses simple models since they can't figure out which specific feature is actually responsible for the result.

**UMAP vs. t-SNE**
UMAP definitely did a better job keeping the overall structure of the data intact. t-SNE kind of stretched everything out, but UMAP grouped the data into nice, tight little islands with lots of space between them. However, inside those islands, the late points (1) and on-time points (0) are completely mixed together. There are no clean, separate clusters for late students.

**100 Features vs. 15 Features**
When I plotted the UMAP for just the top 15 features, the overall shape of the islands looked almost exactly the same as the 100-feature version. This tells me that the other 85 features were basically just random noise. Even with the noise gone, the orange and blue dots were still pretty mixed up, which shows that figuring out who will submit late isn't a simple straight-line problem.

---

## Part 3: Predictive Modeling & Evaluation

### Evaluation Metrics Table

| Model | Accuracy | Precision (Class 1) | Recall (Class 1) | F1-Score (Class 1) 
| --- | --- | --- | --- | --- |
| **Logistic Regression** | 0.88 | 0.00 | 0.00 | 0.00 
| **Support Vector Machine (SVC)** | 0.88 | 0.00 | 0.00 | 0.00 
| **Random Forest Classifier** | 0.93 | 0.94 | 0.42 | 0.59 


### Written Analysis

**Deconstructing the Metrics**
When I first evaluated the models, I encountered an `UndefinedMetricWarning` for dividing by zero in both the Logistic Regression and SVC outputs. Looking at the support metrics, the reason became clear: the dataset is heavily imbalanced, with 284 on-time assignments and only 40 late ones. 

Understanding this imbalance is key to reading the metrics correctly:
* **Accuracy:** This metric proved to be misleading. Logistic Regression achieved an 88% accuracy score, but it did so simply by defaulting to "on-time" (Class 0) for every single student, completely failing to identify any late submissions.
* **Precision:** For the Random Forest, precision for Class 1 is 94%. This means that when the model actually flags an assignment as late, it is correct 94% of the time. It is very reliable when it makes a positive prediction.
* **Recall:** The recall for Random Forest is much lower at 42%. This indicates that out of all the actual late submissions, the model only successfully caught 42% of them, missing more than half.
* **F1-Score:** Because the recall is so low, it pulls the harmonic balance of the F1-score down to 0.59.

**Model Selection**
Random Forest was the most successful model for this task. Logistic Regression and SVC struggled to find a clear mathematical boundary due to the imbalanced data and defaulted to predicting Class 0. Because Random Forest uses decision trees, it was much better equipped to handle the complex, non-linear patterns without requiring perfectly scaled or balanced data.

**Practical Application**
If an educational institution deployed this Random Forest model, it would serve as a highly precise, though conservative, early warning tool. Thanks to the 94% precision, administrators could confidently set up automated reminder emails for flagged students, knowing the model rarely makes false accusations. However, because of the low recall, they would need to understand that the system will not catch every student who submits late, meaning human oversight is still necessary.

**Testing with All 100 Features**
The assignment asked what would happen if the models were trained on all 100 features instead of the top 15. Initially, I assumed more data would improve the model, but the Random Forest's performance actually dropped significantly. The recall fell from 42% down to just 10% (catching only 4 out of 40 late submissions). This demonstrated the "Curse of Dimensionality"—the extra 85 features introduced unnecessary noise that confused the decision trees. Selecting only the top correlated features was a necessary step to help the model find the actual predictive signals.

## Part 4: 1D Time-Independent Schrödinger Equation

**Case A (Oscillatory):**
If we increase the total energy $E$ so it's much higher than $V$, the particle's kinetic energy goes up. In physics, more kinetic energy means higher momentum, which makes the wavelength shorter. So, the wave would start oscillating much faster in the plot.

**Case B (Decaying):**
The wave dropping off super fast represents quantum tunneling. Even though the particle hit a wall that has more potential energy than the particle has total energy (which should be impossible to pass), there is still a tiny, non-zero chance of finding the electron inside that barrier. The exponential drop just means the further you look into the wall, the lower that chance gets.