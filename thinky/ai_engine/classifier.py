import numpy as np
import os
import joblib
import requests

class AIDecisionEngine:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        groups_path = os.path.join(base_path, 'student_groups.pkl')

        # 🎯 أوزان ومراكز المجموعات الـ 5 (تم ضبطها لتتوافق مع الميزات الصافية من 0 إلى 1)
        # الترتيب: [Accuracy, Speed, Independence, Stability]
        self.centroids = {
            "MASTER":    np.array([1.0, 0.8, 1.0, 0.9]),
            "RECKLESS":  np.array([0.25, 1.0, 1.0, 0.8]),
            "HESITANT":  np.array([1.0, 0.2, 1.0, 0.9]),
            "DEPENDENT": np.array([0.75, 0.5, 0.0, 0.7]),
            "STRUGGLER": np.array([0.25, 0.2, 0.5, 0.4]),
        }
        
        try:
            self.ai_groups = joblib.load(groups_path)
        except Exception:
            self.ai_groups = ["MASTER", "RECKLESS", "HESITANT", "DEPENDENT", "STRUGGLER"]

    def get_decision(self, avg_features, weak_skill, common_mistake, user, wrong_details=None):
        # 1. حساب المسافة الإقليدية مباشرة وبشكل نقي[cite: 1]
        distances = {g: np.linalg.norm(avg_features - c) for g, c in self.centroids.items()}
        group = min(distances, key=distances.get)

        # 🚨 قاعدة ضبط تصنيف الاعتمادية (Dependent Override)[cite: 1]
        if wrong_details:
            hints_count = sum([1 for d in wrong_details if d.get('hints_used')])
            if hints_count >= 2 or avg_features[2] <= 0.4:
                group = "DEPENDENT"

        user_gender = getattr(user, 'gender', 'M') 
        gender_syntax = "المذكر" if user_gender == 'M' else "المؤنث"

        target_error = wrong_details[0] if wrong_details else None
        error_info = ""
        if target_error:
            error_info = f"اللغز: {target_error['question']} | الصح: {target_error['correct_answer']} | إجابة الطفل: {target_error['student_answer']}"

        strategies = {
            "RECKLESS": "أقنعه أن الدقة هي توقيع الأذكياء؛ السرعة بلا تركيز تضيع العبقرية.",
            "HESITANT": "ابنِ ثقته الحديدية؛ أخبره أن عقله المبدع يعطيه الحل الصحيح فوراً.",
            "STRUGGLER": "بسط له المفهوم كأنه رحلة استكشاف؛ أخبره أن الخطأ هو مجرد تدريب لعضلة العقل.",
            "DEPENDENT": "حفزه على الاستقلال الكامل؛ أخبره أن التلميحات هي عكاز وهو بطل قوي يستطيع الحل بمفرده.",
            "MASTER": "هذا بطل حقيقي ومستواه ماستر؛ أخبره أن الأخطاء البسيطة هي كبوة جواد وأن مستواه ينافس العباقرة."
        }

        gemini_prompt = f"""
أنت 'Thinky' مدرب الرياضيات الصديق للأبطال. تخاطب المستخدم ({user.username}) بصيغة {gender_syntax}.
سياق الطفل السلوكي للإقناع: {strategies.get(group, "شجعه بذكاء.")}
بيانات السؤال الخاطئ: {error_info}
الخطأ الشائع: {common_mistake}

المطلوب كتابة فقرة واحدة مشجعة وسهلة جداً للأطفال (بدون عناوين أو ترقيم، أقصى حد 90 كلمة):
1. نصيحة سلوكية مقنعة بناءً على سياقه.
2. قل له: 'تعال أعلمك سر الحل السهل:' ثم اشرح السؤال باستخدام مفهوم 'الجمع المتكرر' للوصول لـ {target_error['correct_answer'] if target_error else ''}.
3. التزم بصيغة {gender_syntax}.
"""
        return {
            "group": group,
            "gemini_prompt": gemini_prompt,
            "suggested_difficulties": ["EASY", "MEDIUM"] if group != "MASTER" else ["MEDIUM", "HARD"]
        }

    def get_ai_response(self, prompt):
        """
        توصيل برومبت Thinky بـ OpenRouter باستخدام نموذج Gemini المستقر والمتاح في حسابك لتفادي زحام الـ Rate Limit.
        """
        # النص الاحتياطي الافتراضي في حال انقطاع الشبكة أو رجوع رد فارغ
        final_msg = "واصل التقدم يا بطل! محاولتك رائعة جداً وعقلك ذكي ولماح."
        
        try:
            api_key = "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"
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://thinky-game.edu",
                "X-Title": "Thinky Educational App"
            }
            
            # 🌟 استخدام المعرف الرسمي المباشر لـ Gemini من قائمة حسابك لتخطي اختناق السيرفرات المشتركة
            data = {
                "model": "google/gemini-3.1-flash-lite", 
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 200
            }
            
            print(f"\n🚀 [AI ENGINE] Sending Prompt to OpenRouter using Gemini 3.1 Flash Lite...")
            response = requests.post(url, headers=headers, json=data, timeout=12)
            
            print(f"📡 [AI ENGINE] HTTP Status Code: {response.status_code}")
            res_json = response.json()
            
            if 'choices' in res_json and len(res_json['choices']) > 0:
                message_obj = res_json['choices'][0].get('message', {})
                if message_obj:
                    raw_content = message_obj.get('content') or message_obj.get('text')
                    if raw_content:
                        final_msg = str(raw_content).strip()
                        print("✅ [AI ENGINE] Success: Response fetched beautifully from Gemini!")
                    else:
                        print("⚠️ [AI ENGINE] Warning: Content field is empty.")
                else:
                    print("⚠️ [AI ENGINE] Warning: Message object is empty.")
            elif 'error' in res_json:
                print(f"❌ [AI ENGINE] OpenRouter Error: {res_json['error']}")
                
        except Exception as e:
            print(f"💥 [AI ENGINE] Fallback Activated due to: {str(e)}")
            
        return final_msg