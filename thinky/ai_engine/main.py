import numpy as np
import joblib
import step1
import step2
import step3

# 1. تحميل الداتا من Step 1[cite: 9]
df = step1.df

# 2. تحويل الداتا لميزات عبر Step 2[cite: 9, 11]
features_list = []
for i in range(0, len(df), 5): # نأخذ كل 5 محاولات كبروفايل طالب
    chunk = df.iloc[i:i+5]
    attempts = []
    for _, row in chunk.iterrows():
        attempts.append({
            'is_correct': row['is_correct'],
            'time_taken': row['time_taken'],
            'hints': row['hints_used'],
            'allowed_time': row['allowed_time']
        })
    f, _, _ = step2.extract_behavior_features(attempts)
    features_list.append(f)

X_train = np.array(features_list)

# 3. تدريب الموديل وحفظه[cite: 9, 12]
print("🧠 Training Hakeem AI...")
step3.model.fit(X_train, X_train, epochs=200, verbose=0)
step3.model.save('autoencoder_hakeem.h5')

# 4. حفظ المجموعات[cite: 9]
groups = ["MASTER", "RECKLESS", "HESITANT", "DEPENDENT", "STRUGGLER"]
joblib.dump(groups, 'student_groups.pkl')

print("✅ Success! Model & Groups saved.")