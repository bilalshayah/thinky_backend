import numpy as np

def extract_behavior_features(attempts_list):
    if not attempts_list:
        return [0.0, 0.0, 0.0, 0.0], "General", "None"

    total_acc = 0       
    speed_ratios = []   
    total_indep = 0     
    skill_stats = {}    
    mistake_counts = {} 

    for a in attempts_list:
        # 1. الدقة (الإجابة الصحيحة تعطي 1)
        total_acc += (1 if a['is_correct'] else 0)
        
        # 2. السرعة (نسبة الوقت المتبقي من 0 إلى 1)
        ratio = max(0, 1 - (a['time_taken'] / a['allowed_time']))
        speed_ratios.append(ratio)
        
        # 3. الاستقلالية (نسبة عدم استخدام التلميحات من 0 إلى 1)
        indep_ratio = max(0, 1 - (a['hints'] / 3)) 
        total_indep += indep_ratio
        
        # 4. تجميع المهارات والأخطاء
        skill = a.get('skill', 'General')
        skill_stats.setdefault(skill, {'correct': 0, 'total': 0})
        skill_stats[skill]['total'] += 1
        if a['is_correct']:
            skill_stats[skill]['correct'] += 1
        else:
            m_type = a.get('mistake_type', 'None')
            if m_type != 'None':
                mistake_counts[m_type] = mistake_counts.get(m_type, 0) + 1

    count = len(attempts_list)
    
    # هنا نخرج ميزات صافية (Normalized من 0 إلى 1) دون أي تكرار للأوزان!
    avg_features = [
        total_acc / count,                  # متوسط الدقة (0 إلى 1)
        sum(speed_ratios) / count,          # متوسط السرعة (0 إلى 1)
        total_indep / count,                # متوسط الاستقلالية (0 إلى 1)
        (1 - np.std(speed_ratios))          # استقرار السرعة (0 إلى 1)
    ]
    
    weakest_skill = min(skill_stats, key=lambda s: skill_stats[s]['correct'] / skill_stats[s]['total'])
    common_mistake = max(mistake_counts, key=mistake_counts.get) if mistake_counts else "None"

    return avg_features, weakest_skill, common_mistake