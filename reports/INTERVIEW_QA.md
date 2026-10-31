Q: Why did you choose tree-based models instead of deep learning?
A: The data is structured/tabular where tree-based models like Random Forest and XGBoost handle heterogeneous features, missing values, and provide feature importance. They are faster to train and easier to interpret for this domain.

Q: How did you handle high-cardinality categorical features like Make and Model?
A: I used frequency encoding and, where helpful, target-encoding via cross-validated schemes. For models requiring one-hot I limited to top-K categories and grouped rare ones as 'other'.

Q: How is the parts recommendation implemented?
A: Hybrid approach: an ML classifier predicts probable diagnosis and a rule-based mapping (extracted from the diagnostic dataset) recommends repair steps and parts — this ensures explainability and safety.
