Part-1 NumPy & Linear Algebra – Gram-Schmidt Orthonormalization

Part-2 Pandas & Visualization - The Submission Delay Dataset

Phase-2 : Feature Correlations & Heatmaps
Summary :
The heatmap represents the correlation matrix among the top 15 features and the target variable. Correlation values range from -1 to +1, where positive values indicate direct linear relationships between features and negative values indicate inverse relationships between features. 
Multicollinearity is that the two or more independent features are highly correlated and essentially represent similar information or the same underlying idea.
The problem with multi-collinearity is that the two features are almost similar and depicting one idea but if we don’t remove one, that leads to the weightage of that one idea contributing unrealistically to the target leading to unstable coefficients and fake representation of feature importance. Now since, this one feature represented as two due to multi-collinearity has a lot of weightage to the predictions, increasing variance- the model becoming highly sensitive to changes in this one feature and this also affects the training performance leading to overfitting as model reacts strongly to these duplicate features, starts fitting noise, training accuracy becomes high but generalization performance worsens.
Phase-3 : Dimensionality Reduction (UMAP vs. t-SNE)
UMAP preserves global structure better because 
•	t-SNE mainly focuses on local neighbourhoods. It does not preserve the overall geometry. Hence, in the figure too, clusters appear isolated like floating islands, spacing between them is inconsistent.
•	While in the UMAP plot, the The manifold structure looks more organized. Relative positions between groups are more stable. Similar groups remain closer globally. As UMAP attempts to preserve both the local structure and global topology.
In both the plots, I notice that the the late and on-time points do not form clean clusters.
I believe the UMAP plot with 100 features looks to have better and clean clustering.
Since, more features directly imply more information, hence the embedding algorithms had more information to organize the data, the clusters look more detailed, more meaningful geometrically and more naturally separated. 

Part 3: Predictive Modeling & Evaluation

