# =========================
# MAIN.PY — AI Classifier Edition
# =========================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.models import Model
import joblib

import step1
import step2
import step3

# =========================
# STEP 1 — Load Generated Data
# =========================
df = step1.df

# =========================
# STEP 2 — Extract Behavior Features
# =========================
features = []
for _, row in df.iterrows():
    f = step2.extract_behavior_features(
        correct=row["is_correct"],
        time_taken=row["time_taken"],
        hints=row["hints_used"],
        allowed_time=row["allowed_time"]
    )
    features.append(f)

features = np.array(features)

# =========================
# STEP 3 — Train Autoencoder
# =========================
print("Training AI Brain (Autoencoder)...")
step3.model.fit(features, features, epochs=300, verbose=0) # verbose=0 لهدوء الشاشة

embedding_model = Model(
    inputs=step3.model.input,
    outputs=step3.model.get_layer("embedding_layer").output
)

embeddings = embedding_model.predict(features)

# =========================
# STEP 4 — AI CLASSIFIER (The Intelligent Grouping)
# =========================
# سنقوم بتعريف المصنف هنا مباشرة لسهولة النسخ
class StudentClassifier:
    def __init__(self):
        # النقاط المركزية بناءً على أوزان step2: [Accuracy(15), Speed(15), Independence(10)]
        self.centroids = {
            "MASTER":    np.array([15.0, 12.0, 10.0]), # متفوق
            "RECKLESS":  np.array([0.0,  14.0, 10.0]), # متهور (سريع جداً وخاطئ)
            "HESITANT":  np.array([15.0, 2.0,  10.0]), # متردد (دقيق جداً وبطيء)
            "DEPENDENT": np.array([12.0, 8.0,  0.0]),  # معتمد (يستخدم كل التلميحات)
            "STRUGGLER": np.array([0.0,  2.0,  5.0]),  # متعثر (بطيء وخاطئ)
        }

    def predict(self, feature_vector):
        distances = {group: np.linalg.norm(feature_vector - center) 
                     for group, center in self.centroids.items()}
        return min(distances, key=distances.get)

clf = StudentClassifier()

# تصنيف كل الطلاب في الـ DataFrame
df["ai_group"] = [clf.predict(f) for f in features]
df["embed_x"] = embeddings[:, 0]
df["embed_y"] = embeddings[:, 1]

# =========================
# STEP 5 — AI Group Summary Table
# =========================
group_summary = []

for g in df["ai_group"].unique():
    group_data = df[df["ai_group"] == g]
    summary = {
        "group": g,
        "count": len(group_data),
        "avg_correct": group_data["is_correct"].mean(),
        "avg_time": group_data["time_taken"].mean(),
        "avg_hints": group_data["hints_used"].mean()
    }
    group_summary.append(summary)

summary_df = pd.DataFrame(group_summary)
print("\n===== AI GROUP SUMMARY =====\n")
print(summary_df)

# =========================
# STEP 6 — Visualization (Heatmap)
# =========================
plt.figure(figsize=(10, 6))
sns.heatmap(summary_df.set_index("group").select_dtypes(include=[np.number]), annot=True, cmap="YlGnBu")
plt.title("Student Groups Behavioral Analysis")
plt.show()

# =========================
# STEP 7 — Embedding Visualization
# =========================
plt.figure(figsize=(10, 7))
unique_groups = df["ai_group"].unique()
for g in unique_groups:
    mask = df["ai_group"] == g
    plt.scatter(df.loc[mask, "embed_x"], df.loc[mask, "embed_y"], label=g, alpha=0.6)

plt.title("AI Student Grouping (Latent Space)")
plt.legend()
plt.grid(True)
plt.show()

# =========================
# STEP 8 — Save Models
# =========================
step3.model.save('autoencoder_hakeem.h5')
# حفظ قائمة المجموعات كمرجع
joblib.dump(list(unique_groups), 'student_groups.pkl')

print("\nSuccess! AI Classifier is ready and groups are identified. 🧠🎉")
# ==========================================
# STEP 9 — PRINT STUDENTS BY AI GROUP (WITH DIFFICULTY & TIME)
# ==========================================
print("\n" + "="*60)
print("     DETAILED STUDENTS PERFORMANCE BY AI GROUP")
print("="*60)

for group_name in sorted(df["ai_group"].unique()):
    print(f"\n>>> GROUP: {group_name} <<<")
    print("-" * 50)
    
    current_group = df[df["ai_group"] == group_name].copy()
    
    # حساب "كفاءة الوقت": هل حل أسرع من الوقت المسموح؟
    # إذا كانت النتيجة > 100% يعني أنه أبطأ من المسموح
    current_group["time_efficiency"] = (current_group["time_taken"] / current_group["allowed_time"]) * 100
    
    # اختيار الأعمدة التي تهمكِ لرؤية العلاقة بين الصعوبة والوقت
    display_columns = [
        "difficulty", 
        "allowed_time", 
        "time_taken", 
        "time_efficiency", 
        "is_correct", 
        "hints_used"
    ]
    
    # عرض أول 10 طلاب لرؤية البيانات
    print(current_group[display_columns].head(10).to_string(index=False))
    
    print(f"\nTotal students in {group_name}: {len(current_group)}")