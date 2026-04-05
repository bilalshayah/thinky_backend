# ai_engine/step2.py
import numpy as np

def extract_behavior_features(attempts_list):
    """
    تحليل أداء الطفل في مرحلة كاملة (5 أسئلة).
    attempts_list: قائمة تحتوي على بيانات كل سؤال
    مثال: [{'is_correct': True, 'time_taken': 10, 'hints': 0, 'allowed_time': 20, 'skill': 'addition_1'}, ...]
    """
    if not attempts_list:
        return [0, 0, 0], None

    total_acc = 0
    total_speed = 0
    total_indep = 0
    skill_stats = {}

    for a in attempts_list:
        # 1. حساب الميزات العامة للموديل (الدقة، السرعة، الاستقلالية)
        total_acc += (15 if a['is_correct'] else 0)
        
        # السرعة: نقارن الوقت المستغرق بالوقت المسموح لكل سؤال
        speed_ratio = max(0, 1 - (a['time_taken'] / a['allowed_time']))
        total_speed += (speed_ratio * 15)
        
        # الاستقلالية: الاعتماد على التلميحات
        indep_ratio = max(0, 1 - (a['hints'] / 2))
        total_indep += (indep_ratio * 10)
        
        # 2. مراقبة المهارات (Skill Tracking)
        skill = a['skill']
        if skill not in skill_stats:
            skill_stats[skill] = {'correct': 0, 'total': 0}
        skill_stats[skill]['total'] += 1
        if a['is_correct']:
            skill_stats[skill]['correct'] += 1

    # حساب المتوسط للـ 5 أسئلة
    count = len(attempts_list)
    avg_features = [total_acc / count, total_speed / count, total_indep / count]
    
    # 3. تحديد المهارة الأضعف
    weakest_skill = None
    min_accuracy = 1.1 # قيمة افتراضية للبحث عن الأقل
    
    for s, stats in skill_stats.items():
        acc = stats['correct'] / stats['total']
        if acc < min_accuracy:
            min_accuracy = acc
            weakest_skill = s
            
# إذا كانت دقة الطفل أقل من 90% (بدل 80) نعتبره يحتاج مساعدة
    if min_accuracy >= 0.9: 
        weakest_skill = "General" # أو أي مهارة عشوائية ليتعلمها

    return avg_features, weakest_skill