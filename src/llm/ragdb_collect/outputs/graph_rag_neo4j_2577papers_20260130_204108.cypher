// Concept Nodes (by type)

// Biomarker Concepts (2개)
CREATE (cskeletal_muscle_mass:Concept:Biomarker {id: 'skeletal_muscle_mass', name_ko: '골격근량', name_en: 'skeletal muscle mass', importance: 0.95});
CREATE (cbody_fat_percentage:Concept:Biomarker {id: 'body_fat_percentage', name_ko: '체지방률', name_en: 'body fat percentage', importance: 0.95});

// Unknown Concepts (15개)
CREATE (cvisceral_fat_level:Concept:Unknown {id: 'visceral_fat_level', name_ko: '내장지방 레벨', name_en: 'visceral fat level', importance: 0.9});
CREATE (cbasal_metabolic_rate:Concept:Unknown {id: 'basal_metabolic_rate', name_ko: '기초대사량', name_en: 'basal metabolic rate', importance: 0.85});
CREATE (csmi:Concept:Unknown {id: 'smi', name_ko: '골격근량지수', name_en: 'skeletal muscle index', importance: 0.9});
CREATE (cfat_loss:Concept:Unknown {id: 'fat_loss', name_ko: '지방 감소', name_en: 'fat loss', importance: 0.95});
CREATE (cbody_recomposition:Concept:Unknown {id: 'body_recomposition', name_ko: '체형 개선', name_en: 'body recomposition', importance: 0.85});
CREATE (cstrength_gain:Concept:Unknown {id: 'strength_gain', name_ko: '근력 향상', name_en: 'strength gain', importance: 0.8});
CREATE (ccardio:Concept:Unknown {id: 'cardio', name_ko: '유산소 운동', name_en: 'cardio', importance: 0.85});
CREATE (chiit:Concept:Unknown {id: 'hiit', name_ko: '고강도 인터벌 트레이닝', name_en: 'high intensity interval training', importance: 0.8});
CREATE (ccarbohydrate:Concept:Unknown {id: 'carbohydrate', name_ko: '탄수화물', name_en: 'carbohydrate', importance: 0.8});
CREATE (csarcopenia:Concept:Unknown {id: 'sarcopenia', name_ko: '근감소증', name_en: 'sarcopenia', importance: 0.9});
CREATE (cmetabolic_syndrome:Concept:Unknown {id: 'metabolic_syndrome', name_ko: '대사증후군', name_en: 'metabolic syndrome', importance: 0.85});
CREATE (csarcopenic_obesity:Concept:Unknown {id: 'sarcopenic_obesity', name_ko: '근감소성 비만', name_en: 'sarcopenic obesity', importance: 0.85});
CREATE (cbia:Concept:Unknown {id: 'bia', name_ko: '생체전기저항분석', name_en: 'bioelectrical impedance analysis', importance: 0.9});
CREATE (cinbody:Concept:Unknown {id: 'inbody', name_ko: '인바디', name_en: 'InBody', importance: 0.95});
CREATE (cdxa:Concept:Unknown {id: 'dxa', name_ko: '이중에너지 X선 흡수계측법', name_en: 'dual-energy X-ray absorptiometry', importance: 0.85});

// Outcome Concepts (1개)
CREATE (cmuscle_hypertrophy:Concept:Outcome {id: 'muscle_hypertrophy', name_ko: '근비대', name_en: 'muscle hypertrophy', importance: 0.95});

// Intervention Concepts (3개)
CREATE (cresistance_training:Concept:Intervention {id: 'resistance_training', name_ko: '저항성 운동', name_en: 'resistance training', importance: 0.9});
CREATE (cprotein_intake:Concept:Intervention {id: 'protein_intake', name_ko: '단백질 섭취', name_en: 'protein intake', importance: 0.95});
CREATE (ccalorie_deficit:Concept:Intervention {id: 'calorie_deficit', name_ko: '칼로리 결핍', name_en: 'calorie deficit', importance: 0.9});

// Paper Nodes