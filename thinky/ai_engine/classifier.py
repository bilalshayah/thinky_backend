# ai_engine/classifier.py
import numpy as np

class AIDecisionEngine:
    def __init__(self):
        self.centroids = {
            "MASTER":    np.array([15.0, 12.0, 10.0]),
            "RECKLESS":  np.array([0.0,  14.0, 10.0]),
            "HESITANT":  np.array([15.0, 2.0,  10.0]),
            "DEPENDENT": np.array([12.0, 8.0,  0.0]),
            "STRUGGLER": np.array([0.0,  2.0,  5.0]),
        }

    def get_decision(self, avg_features, weak_skill, user):
        distances = {g: np.linalg.norm(avg_features - c) for g, c in self.centroids.items()}
        group = min(distances, key=distances.get)

        # تحديد صيغة المنادى والنوع بناءً على بيانات المستخدم
        gender = getattr(user, 'gender', 'male') # نفترض وجود حقل gender في موديل User
        gender_context = "خاطبه بصيغة الأنثى (أنتِ، يا بطلة، اسمعي)" if gender == 'female' else "خاطبه بصيغة الذكر (أنتَ، يا بطل، اسمع)"

        is_master = (group == "MASTER")
        
        if is_master:
            # برومبت الوحش (تحدي فقط - مخصص حسب النوع)
            gemini_prompt = f"""
أنت الآن 'الوحش المظلم'. الطفل ({user.username}) عبقري في مجموعة (MASTER).
{gender_context}.
مهمتك: تحدّاه بأسلوب شرير ومغرور. قل له أن مهارة ({weak_skill}) ستكون نهايته في التحدي القادم.
القواعد: ابدأ الكلام مباشرة، لا تستخدم عناوين، لا تشرح أي شيء تعليمي.
"""
        else:
            # برومبت الحكيم (معلم حقيقي - مخصص حسب النوع والمجموعة)
            gemini_prompt = f"""
أنت 'المعلم الحكيم'. الطفل ({user.username}) في مجموعة ({group}). {gender_context}.
مهمتك تقديم نصيحة سلوكية ذكية ثم شرح مهارة ({weak_skill}) بتبسيط شديد.

المطلوب (ابدأ النص مباشرة بدون عناوين):
1. النصيحة السلوكية (حسب المجموعة):
   - إذا كان RECKLESS: علمه 'كيف' يهدأ (مثلاً: خذ نفساً عميقاً، اقرأ السؤال مرتين، وضع إصبعك تحت كل رقم).
   - إذا كان HESITANT: علمه 'كيف' يثق بنفسه (مثلاً: عقلك أعطاك الإجابة فوراً، لا تغير رأيك، أنت دائماً تصيب!).
   - إذا كان DEPENDENT: شجعه على محاولة الحل منفرداً 'كالبطل الذي يعتمد على سيفه وحده'.
   - إذا كان STRUGGLER: طمئنه بأن الخطأ هو 'درجة سلم' للصعود للقوة.
   
2. الشرح التعليمي (قاعدة الـ 5 سنوات):
   - اشرح ({weak_skill}) في 3 خطوات بسيطة جداً.
   - استخدم أشياء ملموسة (أصابع، حلوى، تفاح).
   - اجعل الشرح عملياً: "أولاً افعل كذا.. ثانياً افعل كذا.. ثالثاً ستجد الحل".

القواعد الصارمة:
- ممنوع الكلمات العاطفية الزائدة (حبيبي/قلبي).
- الرد يجب أن يكون موجهاً لـ {gender} (ذكر/أنثى) بشكل دقيق.
- لا تضع أي كلمات إضافية مثل 'النصيحة السلوكية' أو 'الشرح'. ابدأ بالكلام للطفل فوراً.
"""

        return {
            "group": group,
            "weakest_skill": weak_skill,
            "gemini_prompt": gemini_prompt,
            "character_type": "villain" if is_master else "hakeem"
        }