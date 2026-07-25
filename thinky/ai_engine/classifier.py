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
# 🧠 التوجيهات النفسية والتربوية بالعامية السورية المخصصة لكل نمط (عمر 10 سنوات)
        strategies = {
            "RECKLESS": (
                "الولد كتير مستعجل وعم يركض ركض بالحل! قنعو يهدّي السرعة شوي، ويمشي على مهلو "
                "خطوة خطوة مشان ما يوقع بفخ الأخطاء السريعة، وقلو إنو التمهل هو يلي بيصنع الأبطال."
            ),
            "HESITANT": (
                "الولد خايف ومتردد كتير يختار الجواب. ابنِ ثقتو بحالو وقلو يوثق بعقلو الذكي "
                "وبأول جواب بيخطر ببالو، لأنو شاطر كتير وما في داعي يخاف من الغلط أبداً."
            ),
            "STRUGGLER": (
                "الولد عم يعاني وحاسس بصعوبة بالرياضيات؛ بسطلو اللغز كأنو لعبة مسلية وخفف عنو، "
                "وقلو إنو الغلط عادي كتير وهو يلي بيمرّن عقلنا ليصير بطل وأقوى."
            ),
            "DEPENDENT": (
                "الولد كل شوي بياخد تلميحات ومعتمد عالمساعدة؛ شجعو بقوة إنو يعتمد على حالو بالكامل "
                "هالمرة، وقلو أنت بطل قوي وبتئدر تحلها لحالك بدون ما تحتاج مساعدة حدا."
            ),
            "MASTER": (
                "الولد عبقري ومستواه ممتاز بس هالمرة وقع بغلطة صغيرة؛ قلو أنت ملك الرياضيات "
                "وهاد الغلط البسيط بيمرق مع كل الشاطرين، ركز المرة الجاية لتضل بالصدارة."
            )
        }

        gemini_prompt = f"""
أنت المساعد الذكي 'Thinky' بلعبة الرياضيات. خاطب الطفل ({user.username}) بعمر 10 سنوات بلهجة سورية عامية بيضاء ومبسطة، والتزم بجنس الطفل: {gender_syntax}.

📌 السياق السلوكي للطفل (أعطه نصيحة سريعة ومباشرة جداً لتعديل سلوكه بدون مبالغة بالكلام العاطفي وبدون كلمات زائدة):
- {strategies.get(group, "شجعو يا بطل.")}

📌 بيانات اللغز الرياضي الفعلي الذي أخطأ به الطفل (اشرح أرقام هذه المسألة المعطاة هنا حصراً):
- المسألة الفعيلة: {target_error['question'] if target_error else ''}
- الجواب الصحيح للغز: {target_error['correct_answer'] if target_error else ''}
- جواب الطفل الذي أرسله خطأ: {target_error['student_answer'] if target_error else ''}
- نوع الخطأ الشائع: {common_mistake}

⚠️ شروط الصياغة الصارمة (نص متصل وقصير، بدون أي عناوين، وبدون ترقيم خطوات):
1. ممنوع تماماً اختراع أرقام أو مسائل من عندك (مثل 20 أو 30 أو تفاح)، بل التزم كلياً بالأرقام المذكورة في "المسألة الفعلية" أعلاه واشرحها هي بالذات.
2. قلل الكلمات العاطفية والتجميلية إلى الحد الأدنى؛ نريد كلاماً مفيداً وفعالاً يركز على طريقة التفكير الرياضي الصحيحة.
3. اشرح طريقة الحل بالتدرج وببساطة (Little by little) ومن الصفر: فكك أرقام المسألة الفعلية المعطاة بأسلوب منطقي ملموس ومناسب لنوع العملية (جمع، طرح، ضرب، قسمة) واجمعهم أو اطرحهم خطوة وراء خطوة ليصل الطفل للمبدأ الرياضي نفسه، فيعرف كيف يحل أي سؤال مشابه بمفرده لاحقاً.
4. التزم تماماً بصيغة {gender_syntax}. استخدم إيموجيز معتدلة 🎈 لتبسيط القراءة بلمحة سريعة.
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
                "temperature": 0.6,
                "max_tokens": 600  # 🌟 رفعنا القيمة هنا ليعطيه مساحة كاملة للشرح السوري الممتع دون انقطاع
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