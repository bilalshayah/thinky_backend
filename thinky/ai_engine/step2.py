import numpy as np

def extract_behavior_features(attempts_list):
    # إذا كانت القائمة فارغة، نرجع قيم افتراضية لضمان عدم توقف النظام
    if not attempts_list:
        return [0, 0, 0, 0], "General", "None"

    total_acc = 0       # لتجميع نقاط الدقة
    speed_ratios = []   # لحفظ نسب السرعة لكل سؤال
    total_indep = 0     # لتجميع نقاط الاستقلالية
    skill_stats = {}    # قاموس لتتبع أداء كل مهارة (جمع، طرح.. إلخ)
    mistake_counts = {} # قاموس لتتبع أنواع الأخطاء (نسيان الصفر، استلاف..)

    for a in attempts_list:
        # 1. الدقة (الوزن: 20)
        # إذا كانت الإجابة صحيحة، يحصل الطفل على 20 نقطة
        total_acc += (20 if a['is_correct'] else 0)
        
        # 2. السرعة (Speed Ratio)
        # المعادلة تحسب النسبة المئوية للوقت المتبقي: (الوقت المسموح - الوقت المستغرق) / المسموح
        # إذا حل بسرعة البرق، النتيجة تقترب من 1. إذا استنفد الوقت، النتيجة 0
        ratio = max(0, 1 - (a['time_taken'] / a['allowed_time']))
        speed_ratios.append(ratio)
        
        # 3. الاستقلالية (الوزن: 10)
        # قسمنا على 3 لأنكِ طلبتِ أن يكون الحد الأقصى 3 تلميحات
        # (1 - نسبة التلميحات المستخدمة) يعطينا درجة استقلالية الطفل
        indep_ratio = max(0, 1 - (a['hints'] / 3)) 
        total_indep += (indep_ratio * 10) # نضرب في 10 ليكون الحد الأقصى للميزة هو 10[cite: 9]
        
        # 4. تجميع بيانات المهارات والأخطاء
        skill = a.get('skill', 'General') # إذا لم يجد المهارة سيسميها General ولن ينهار الكود
        skill_stats.setdefault(skill, {'correct': 0, 'total': 0})
        skill_stats[skill]['total'] += 1
        if a['is_correct']:
            skill_stats[skill]['correct'] += 1
        else:
            # نأخذ نوع الخطأ، والافتراضي هو None كما طلبتِ[cite: 9]
            m_type = a.get('mistake_type', 'None')
            if m_type != 'None':
                mistake_counts[m_type] = mistake_counts.get(m_type, 0) + 1

    count = len(attempts_list) # عدد الأسئلة (غالباً 5)
    
    # الإجابة على سؤالكِ: لماذا لم نضرب السرعة في وزن؟
    # في الكود السابق، كنا نحسب المتوسط فقط، لكن الصحيح هو ضربه في وزن (مثلاً 10)[cite: 8, 9]
    # لكي تتساوى الأحجام داخل الـ AI، قمت بتعديلها الآن لتضرب في 10[cite: 9]
    
    avg_features = [
        total_acc / count,                  # متوسط الدقة (أقصى قيمة 20)[cite: 9]
        (sum(speed_ratios) / count) * 10,     # متوسط السرعة (أقصى قيمة 10)[cite: 9]
        total_indep / count,                # متوسط الاستقلالية (أقصى قيمة 10)[cite: 9]
        (1 - np.std(speed_ratios)) * 10       # الاستقرار (أقصى قيمة 10)[cite: 9]
    ]
    
    # تحديد المهارة الأضعف والخطأ الشائع[cite: 9]
    weakest_skill = min(skill_stats, key=lambda s: skill_stats[s]['correct'] / skill_stats[s]['total'])
    common_mistake = max(mistake_counts, key=mistake_counts.get) if mistake_counts else "None"

    return avg_features, weakest_skill, common_mistake