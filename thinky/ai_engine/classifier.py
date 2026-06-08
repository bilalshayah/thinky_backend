import numpy as np
import os
import joblib

class AIDecisionEngine:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        groups_path = os.path.join(base_path, 'student_groups.pkl')

        # 🎯 المراكز السلوكية الرياضية المطورة بدقة لحساب المسافات لـ ريري
        # الميزات مرتبة كالتالي: [Accuracy, Speed, Independence, Stability]
        self.centroids = {
            "MASTER":    np.array([20.0, 8.0, 10.0, 9.0]),
            "RECKLESS":  np.array([5.0, 10.0, 10.0, 8.0]),
            "HESITANT":  np.array([20.0, 2.0, 10.0, 9.0]),
            "DEPENDENT": np.array([15.0, 5.0, 0.0, 7.0]),
            "STRUGGLER": np.array([5.0, 2.0, 5.0, 4.0]),
        }
        
        # تعطيل تحميل موديل Keras لمنع تعارض الإصدارات وعمل كراش في البيئة الحالية
        self.model_loaded = False
        print("🛡️ Keras mismatch bypassed. Active Strategy: High-Performance Centroid Classifier.")

        # تحميل ملف المجموعات السلوكية الاحتياطي
        try:
            self.ai_groups = joblib.load(groups_path)
        except Exception:
            self.ai_groups = ["MASTER", "RECKLESS", "HESITANT", "DEPENDENT", "STRUGGLER"]

    def get_decision(self, avg_features, weak_skill, common_mistake, user, wrong_details=None):
        # 1. حساب المسافة الإقليدية (Euclidean Distance) بين أداء الطفل ومراكز المجموعات
        # هذا يضمن تصنيفاً سلوكياً ذكياً وسريعاً جداً بدون أي حمل زائد على المعالج
        distances = {g: np.linalg.norm(avg_features - c) for g, c in self.centroids.items()}
        group = min(distances, key=distances.get)

        # 🚨 قاعدة ريري الصارمة لضبط تصنيف الاعتمادية (Dependent Override):
        # إذا تبين سلوكياً أن الطفل طلب تلميحين أو أكثر خلال الـ Phase الحالي، يُصنف فوراً كـ DEPENDENT
        if wrong_details:
            hints_count = sum([1 for d in wrong_details if d.get('hints_used')])
            if hints_count >= 2 or (len(avg_features) > 2 and avg_features[2] <= 4.0):
                group = "DEPENDENT"

        # 2. تحديد جنس المستخدم لتعديل الصياغة اللغوية (M/F)
        user_gender = getattr(user, 'gender', 'M') 
        gender_syntax = "المذكر" if user_gender == 'M' else "المؤنث"

        # 3. جلب بيانات اللغز الذي تعثر فيه الطفل لتحليله
        target_error = wrong_details[0] if wrong_details else None
        error_info = ""
        if target_error:
            error_info = f"اللغز: {target_error['question']} | الصح: {target_error['correct_answer']} | إجابة الطفل: {target_error['student_answer']}"

        # 4. استراتيجيات الإقناع والدعم النفسي المخصصة لكل نمط
        strategies = {
            "RECKLESS": "أقنعه أن الدقة هي توقيع الأذكياء؛ السرعة بلا تركيز تضيع العبقرية، والأبطال يراجعون خطواتهم دوماً لضمان الفوز الساحق.",
            "HESITANT": "ابنِ ثقته الحديدية؛ أخبره أن عقله المبدع يعطيه الحل الصحيح فوراً، والشك هو مجرد ضجيج يحاول تعطيله. شجعه ليثق بحدسه.",
            "STRUGGLER": "بسط له المفهوم كأنه رحلة استكشاف؛ أخبره أن الخطأ هو مجرد تدريب لعضلة العقل، وبالصبر سيحل أصعب الألغاز.",
            "DEPENDENT": "حفزه على الاستقلال الكامل؛ أخبره أن التلميحات هي عكاز للضعفاء، وهو بطل قوي يستطيع الجري بعقله منفرداً للقمة دون مساعدة الحكيم.",
            "MASTER": "هذا بطل حقيقي ومستواه ماستر؛ أخبره أن الأخطاء البسيطة هي 'كبوة جواد'، وأن مستواه يتطلب منه دقة متناهية لأنه ينافس العباقرة والشرير بانتظاره."
        }

        # 5. بناء البرومبت النهائي الموجه لـ Gemini لتبسيط الرياضيات بالجمع المتكرر لسن الأطفال
        gemini_prompt = f"""
أنت 'Thinky' مدرب الرياضيات الصديق للأبطال. تخاطب المستخدم ({user.username}) بصيغة {gender_syntax}.

سياق الطفل السلوكي للإقناع: {strategies.get(group, "شجعه بذكاء.")}
بيانات السؤال الخاطئ: {error_info}
الخطأ الشائع: {common_mistake}

المطلوب منك كتابة فقرة واحدة مشجعة وسهلة جداً (بدون عناوين):
1. ابدأ بنصيحة سلوكية مقنعة بناءً على سياقه (أقنعه بالهدوء أو الثقة أو الاستقلال التام).
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