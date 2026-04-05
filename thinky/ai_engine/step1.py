import numpy as np
import pandas as pd

num_samples = 500
# np.random.seed(42) # يمكنكِ تفعيله إذا أردتِ نتائج ثابتة في كل مرة

data = []

# ai_engine/step1.py
for _ in range(num_samples):
    # 1. تحديد مستوى الصعوبة
    difficulty = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
    
    # 2. تحديد الوقت المسموح بناءً على مهارة عشوائية وصعوبة السؤال
    base_skill_time = np.random.randint(15, 45) 
    allowed_time = base_skill_time * (1 + (difficulty - 1) * 0.5)
    
    # --- التعديل الجوهري هنا لجعل البيانات واقعية ---
    # نحدد "معامل سرعة" عشوائي لكل طفل (من 0.4 أي سريع جداً إلى 1.6 أي بطيء جداً)
    speed_factor = np.random.uniform(0.4, 1.6) 
    
    # الوقت الفعلي يعتمد على سرعة الطفل بالنسبة للوقت المسموح
    time_taken = allowed_time * speed_factor
    
    # إضافة تذبذب بسيط (ضوضاء إحصائية) لجعل الأرقام غير متكررة
    time_taken = np.random.normal(loc=time_taken, scale=3)
    time_taken = max(4, time_taken) # التأكد من أن الوقت لا يقل عن 4 ثوانٍ
    # -----------------------------------------------

    # 3. التلميحات المستخدمة
    hints_used = np.random.choice([0, 1, 2], p=[0.6, 0.25, 0.15])
    
    # 4. حساب احتمالية الإجابة الصحيحة
    # المبدأ: الإجابة الصحيحة تقل مع الصعوبة، زيادة التلميحات، والبطء الشديد
    prob_correct = 0.9
    prob_correct -= 0.15 * (difficulty - 1)
    prob_correct -= 0.2 * hints_used
    
    # إذا كان الطفل بطيئاً جداً (تجاوز الوقت المسموح)، تقل احتمالية صحة إجابته قليلاً
    if time_taken > allowed_time:
        prob_correct -= 0.1
        
    prob_correct = np.clip(prob_correct, 0.05, 0.95)
    
    # تحديد النتيجة النهائية
    is_correct = np.random.choice([1, 0], p=[prob_correct, 1 - prob_correct])
    
    # إضافة البيانات للقائمة
    data.append([is_correct, time_taken, hints_used, difficulty, allowed_time])

# إنشاء الـ DataFrame النهائي
df = pd.DataFrame(data, columns=["is_correct", "time_taken", "hints_used", "difficulty", "allowed_time"])

# (اختياري) للتأكد من وجود حالات بطيئة، يمكنكِ فحص أول 5 صفوف
# print(df.head())