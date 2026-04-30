import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Load dataset
df = pd.read_csv("student_performance_dataset.csv")

# Features and target
X = df[["attendance", "assignment_score", "internal_marks"]]
y = df["final_marks"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Predict
pred = model.predict(X_test)

# R² (0.90+ means good model)
print("R2 Score:", r2_score(y_test, pred))

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model Saved: model.pkl")
