import numpy as np
import os
import joblib
from tensorflow.keras.models import load_model, Model

class AIDecisionEngine:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        model_path = os.path.join(base_path, 'autoencoder_hakeem.h5')
        groups_path = os.path.join(base_path, 'student_groups.pkl')

        try:
            # 1. تحميل الموديل والـ Encoder
            full_model = load_model(model_path)
            self.encoder = Model(
                inputs=full_model.input,
                outputs=full_model.get_layer("embedding_layer").output
            )
            self.ai_groups = joblib.load(groups_path)
            self.model_loaded = True
        except Exception as e:
            print(f"Warning: AI Model fallback active. Error: {e}")
            self.model_loaded = False
            # المراكز الاحتياطية بـ 4 ميزات: [Accuracy, Speed, Independence, Stability]
            self.centroids = {
                "MASTER":    np.array([20.0, 8.0, 10.0, 9.0]),
                "RECKLESS":  np.array([5.0, 10.0, 10.0, 8.0]),
                "HESITANT":  np.array([20.0, 2.0, 10.0, 9.0]),
                "DEPENDENT": np.array([15.0, 5.0, 0.0, 7.0]),
                "STRUGGLER": np.array([5.0, 2.0, 5.0, 4.0]),
            }

    def get_decision(self, avg_features, weak_skill, common_mistake, user, wrong_details=None):
        # 1. المجموعات السلوكية (داخلياً)
        if self.model_loaded:
            import numpy as np
            input_data = np.array([avg_features])
            latent = self.encoder.predict(input_data, verbose=0)[0]
            group = self.ai_groups[np.argmax(latent) % len(self.ai_groups)]
        else:
            import numpy as np
            distances = {g: np.linalg.norm(avg_features - c) for g, c in self.centroids.items()}
            group = min(distances, key=distances.get)

        # 2. جلب جنس المستخدم بدقة من الموديل (M/F)
        user_gender = getattr(user, 'gender', 'M') 
        gender_syntax = "المذكر" if user_gender == 'M' else "المؤنث"

        # 3. اختيار لغز واحد لتحويله لدرس تعليمي
        target_error = wrong_details[0] if wrong_details else None
        error_info = ""
        if target_error:
            error_info = f"اللغز: {target_error['question']} | الصح: {target_error['correct_answer']} | إجابة الطفل: {target_error['student_answer']}"

        # 4. استراتيجيات الإقناع العميقة (شاملة الـ MASTER)
        strategies = {
            "RECKLESS": "أقنعه أن الدقة هي توقيع الأذكياء؛ السرعة بلا تركيز تضيع العبقرية، والابطال يراجعون خطواتهم دوماً لضمان الفوز الساحق.",
            "HESITANT": "ابنِ ثقته الحديدية؛ أخبره أن عقله المبدع يعطيه الحل الصحيح فوراً، والشك هو مجرد ضجيج يحاول تعطيله. شجعه ليثق بحدسه.",
            "STRUGGLER": "بسط له المفهوم كأنه رحلة استكشاف؛ أخبره أن الخطأ هو مجرد تدريب لعضلة العقل، وبالصبر سيحل أصعب الألغاز.",
            "DEPENDENT": "حفزه على الاستقلال الكامل؛ أخبره أن التلميحات هي عكاز للضعفاء، وهو بطل قوي يستطيع الجري بعقله منفرداً.",
            "MASTER": "هذا بطل حقيقي؛ أخبره أن الأخطاء البسيطة هي 'كبوة جواد'، وأن مستواه يتطلب منه دقة متناهية لأنه ينافس العباقرة. حفزه للبحث عن طرق حل أسرع وأذكى."
        }

        # 5. البرومبت المطور: التركيز على "كيفية الحل" خطوة بخطوة
        # 5. البرومبت المطور: التركيز على "الجمع المتكرر" وتبسيط الحل للأطفال
        gemini_prompt = f"""
أنت 'Thinky' مدرب الرياضيات الصديق للأبطال. تخاطب المستخدم ({user.username}) بصيغة {gender_syntax}.

سياق الطفل السلوكي للإقناع: {strategies.get(group, "شجعه بذكاء.")}
بيانات السؤال الخاطئ: {error_info}
الخطأ الشائع: {common_mistake}

المطلوب منك كتابة فقرة واحدة مشجعة وسهلة جداً (بدون عناوين):
1. ابدأ بنصيحة سلوكية مقنعة بناءً على سياقه (أقنعه بالهدوء أو الثقة أو الاستقلال).
2. انتقل لقول: 'تعال أعلمك سر الحل السهل:' ثم اشرح السؤال المذكور باستخدام مفهوم "الجمع المتكرر".
3. بسط الفكرة للأطفال؛ مثلاً إذا كان السؤال 3x4، اشرح له أننا نكرر الرقم 3 أربع مرات (3+3+3+3) لتسهيل الحساب، واستخدم الأرقام والعمليات بوضوح للوصول للناتج الصحيح {target_error['correct_answer'] if target_error else ''}.
4. إذا كان الخطأ الشائع ({common_mistake}) ليس 'None'، علمه بلمحة بسيطة كيف يتجنب هذا الفخ.
5. التزم بصيغة {gender_syntax} (أنتَ بطل) طوال الوقت.

القواعد:
- لغة عربية بسيطة جداً (مستوى طفل)، فقرة واحدة متصلة.
- ممنوع الترقيم أو "المهمة 1/2".
- الحد الأقصى 90 كلمة.
"""

        return {
            "group": group,
            "gemini_prompt": gemini_prompt,
            "suggested_difficulties": ["EASY", "MEDIUM"] if group != "MASTER" else ["MEDIUM", "HARD"]
        }