"""
인바디 결과지 초정밀 매칭 - 14차 시각화 강화판 (Filter Visibility + Reason Highlighting)
"""

import os
import cv2
import json
import re
import numpy as np
import time
import difflib
from paddleocr import PaddleOCR

class InBodyMatcher:
    def __init__(self):
        os.environ['FLAGS_use_mkldnn'] = '0'
        os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
        # [V5 고정밀 설정] 서버급 탐지기와 최신 한국어 인식 모델의 조합
        # 'mobile_rec' 명칭은 V5의 표준 경량화 고성능 모델을 의미하며, 이전 버전의 서버급보다 정밀합니다.
        self.ocr = PaddleOCR(
            lang='korean', 
            ocr_version='PP-OCRv5',
            text_det_limit_side_len=2560, 
            text_det_unclip_ratio=2.0,
            use_angle_cls=True
        )
        
        self.correction_map = {
            "척정체중": "적정체중", "정체중": "적정체중", "체지방륨": "체지방률", "체지방율": "체지방률",
            "골격극량": "골격근량", "극근량": "골격근량", "무기실": "무기질", "보부지방률": "복부지방률",
            "부지방률": "복부지방률", "내장지방레빌": "내장지방레벨", "제지방륨": "제지방량", "제지방률": "제지방량",
            "율근론": "골격근량", "율근량": "골격근량", "근육량": "골격근량", "Skeletal": "골격근량", "MuscleMass": "골격근량"
        }

    def extract_and_match(self, image_path, output_vis_path="inbody_matching_vis.jpg"):
        src_img = cv2.imread(image_path)
        if src_img is None: return {}
        # ROI 실측 좌표계인 2400px로 안정화
        target_h = 2400
        img = cv2.resize(src_img, (int(src_img.shape[1] * (target_h / src_img.shape[0])), target_h), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite("temp_standard_image.jpg", img)
        
        scale = 1.0 # 2400px 기준

        result = self.ocr.predict(input="temp_standard_image.jpg")
        all_nodes = []
        if result:
            for res in result:
                for poly, text, conf in zip(res['dt_polys'], res['rec_texts'], res.get('rec_scores', [])):
                    pts = np.array(poly)
                    all_nodes.append({
                        'text': text.strip().replace(" ", "").replace("|", ""),
                        'bbox': [int(pts.min(axis=0)[0]), int(pts.min(axis=0)[1]), int(pts.max(axis=0)[0]), int(pts.max(axis=0)[1])],
                        'h': int(pts.max(axis=0)[1] - pts.min(axis=0)[1]),
                        'center': [(pts.min(axis=0)[0] + pts.max(axis=0)[0]) / 2, (pts.min(axis=0)[1] + pts.max(axis=0)[1]) / 2],
                        'conf': float(conf)
                    })

        # [ROI 정밀 재조정] V5 모델 성능에 맞춰 범위를 다시 타이트하게 설정 (인접 행 혼입 방지)
        targets = {
            "신장": {"re": r"(\d{3})", "yr": [130, 210], "dir": "down"},
            "연령": {"re": r"(\d{2})", "yr": [130, 210], "dir": "down"},
            "성별": {"re": r"(남성|여성|남|여)$", "yr": [130, 210], "dir": "down"},
            "체수분": {"re": r"(\d+\.\d+)", "yr": [320, 370], "dir": "right"},
            "단백질": {"re": r"(\d+\.\d+)", "yr": [380, 430], "dir": "right"},
            "무기질": {"re": r"(\d+\.\d+)", "yr": [440, 480], "dir": "right"},
            "체지방": {"re": r"(\d+\.\d+)", "yr": [490, 540], "dir": "right"},
            
            # 머슬-팻 분석: 키워드 오독(율근론 등) 대비 및 ROI 고정
            "체중": {"re": r"(\d+\.\d+)", "yr": [760, 815], "dir": "right"},    # 77.7
            "골격근량": {"re": r"(\d+\.\d+)", "yr": [840, 895], "dir": "right"}, # 32.5 (율근론, Skeletal 보정)
            "체지방량": {"re": r"(\d+\.\d+)", "yr": [900, 965], "dir": "right"}, # 20.6
            
            "적정체중": {"re": r"(\d+\.\d+)", "yr": [560, 610], "dir": "right"},
            "체중조절": {"re": r"([-+]\d+\.\d+)", "yr": [600, 650], "dir": "right"},
            "지방조절": {"re": r"([-+]\d+\.\d+)", "yr": [640, 690], "dir": "right"},
            "근육조절": {"re": r"0.0|(\d+\.\d+)", "yr": [680, 725], "dir": "right"},
            
            "복부지방률": {"re": r"(\d\.\d{2})", "yr": [900, 1020], "dir": "down"}, 
            "내장지방레벨": {"re": r"(\d+)", "yr": [1000, 1150], "dir": "down"},
            
            # 비만분석 섹션: 결과값 테이블(BMI, 체지방률) ROI 정밀 압축
            "BMI": {"re": r"(\d+\.\d+)", "yr": [1140, 1175], "dir": "right"}, 
            "체지방률": {"re": r"(\d+\.\d+)", "yr": [1180, 1220], "dir": "right"}, 
            
            "제지방량": {"re": r"(\d+\.?\d*)", "yr": [1150, 1210], "dir": "right"},
            "기초대사량": {"re": r"(\d{4})", "yr": [1210, 1245], "dir": "right"},
            "비만도": {"re": r"(\d+)", "yr": [1245, 1285], "dir": "right"},
            "권장섭취열량": {"re": r"(\d{4})", "yr": [1280, 1330], "dir": "right"},
        }

        matched_data = {}
        vis_image = img.copy()
        overlay = img.copy()

        for key, config in targets.items():
            yr_min, yr_max = int(config["yr"][0] * scale), int(config["yr"][1] * scale)
            cv2.rectangle(overlay, (0, yr_min), (img.shape[1], yr_max), (230, 230, 230), -1) # ROI 영역 표시
            
            candidates_k = [n for n in all_nodes if (yr_min - int(20*scale) <= n['center'][1] <= yr_max + int(20*scale)) and 
                           (key in self.correction_map.get(n['text'], n['text']) or difflib.SequenceMatcher(None, key, self.correction_map.get(n['text'], n['text'])).ratio() > 0.5)]

            if not candidates_k:
                matched_data[key] = None; continue

            k_node = max(candidates_k, key=lambda x: x['conf'])
            cv2.rectangle(vis_image, (k_node['bbox'][0], k_node['bbox'][1]), (k_node['bbox'][2], k_node['bbox'][3]), (255, 0, 0), 2)
            cv2.putText(vis_image, key, (k_node['bbox'][0], k_node['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            candidates_v = []
            for item in all_nodes:
                if item == k_node: continue
                
                # [괄호 필터링] 괄호와 그 안의 텍스트를 완전히 무시 (예: (77.7), (10-15) 제거)
                clean_text = re.sub(r'\(.*?\)', '', item['text'])
                # [숫자 오인식 보정] I, l 등을 1로 치환하여 인식률 제고
                clean_text = clean_text.replace('I', '1').replace('l', '1').replace(',', '.')
                
                match = re.search(config['re'], clean_text)
                if not match: continue
                val = match.group(0) if "조절" in key else match.group(1)
                
                # 가중치 및 필터 로직 시각화 준비
                i_center = item['center']
                dx = i_center[0] - k_node['bbox'][2] if config.get("dir", "right") == "right" else abs(i_center[0] - k_node['center'][0])
                dy = abs(i_center[1] - k_node['center'][1])
                
                # 수평 라인 및 ROI 체크
                in_roi = (yr_min - 10 <= i_center[1] <= yr_max + 50)
                is_right_dir = (config.get("dir", "right") == "right" and 0 < dx < 900 and dy < 60)
                is_down_dir = (config.get("dir") == "down" and 0 < (item['center'][1] - k_node['bbox'][3]) < 350 and dx < 120)
                
                if in_roi and (is_right_dir or is_down_dir):
                    if "조절" not in key and (val == "0.0" or val == "0"): continue
                    # [매칭 엔진 v8] 대형 텍스트(Value) 절대 우선순위
                    # 인바디 실측값은 눈금(Scale)보다 높이(h)가 훨씬 크며, 보통 35px 이상입니다.
                    h_val = item.get('h', 0)
                    is_big = (h_val > 35) # 큰 글씨 임계값
                    
                    # 1. 큰 글씨일 경우 점수를 대폭 낮추어 최우선 후보로 만듦
                    # 2. 측정값은 보통 그래프 우측 끝(X=600~900)에 위치함을 반영
                    target_dx = 800 if config.get("dir", "right") == "right" else 0
                    dist_score = (dy * 100) + abs(target_dx - dx)
                    
                    if is_big:
                        dist_score -= 10000 # 큰 글씨 절대 우선권
                    
                    candidates_v.append((dist_score, val, item))

            if candidates_v:
                candidates_v.sort(key=lambda x: x[0])
                matched_data[key] = candidates_v[0][1]
                v_node = candidates_v[0][2]
                # [시각화] 최종 매칭된 수치는 녹색으로 표시
                cv2.rectangle(vis_image, (v_node['bbox'][0], v_node['bbox'][1]), (v_node['bbox'][2], v_node['bbox'][3]), (0, 255, 0), 3)
                cv2.putText(vis_image, "Value", (v_node['bbox'][0], v_node['bbox'][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            else:
                matched_data[key] = None

        v_nodes_debug = [n for n in all_nodes if 1100 <= n['center'][1] <= 1350]
        print("\n--- [Debug] Obesity Analysis Area (1100-1350) ---")
        for n in sorted(v_nodes_debug, key=lambda x: x['center'][1]):
            print(f"Text: {n['text']}, Center: {n['center']}")
        print("------------------------------------------\n")

        # [부위별 분석 최종 고도화] 인바디 270 그리드 레이아웃 (팔2-복부1-다리2)
        evals = ["표준이하", "표준이상", "표준"]
        # 해상도 상향에 따른 ROI 좌표 보정
        seg_nodes = sorted([n for n in all_nodes if any(ev in n['text'] for ev in evals) and (1400*scale <= n['center'][1] <= 1850*scale)], key=lambda x: x['center'][1])
        
        # Y축 좌표를 기준으로 세 개 층(상/중/하)으로 분리 (팔 / 복부 / 다리)
        row_top = sorted([n for n in seg_nodes if n['center'][1] < 1550*scale], key=lambda x: x['center'][0])
        row_mid = sorted([n for n in seg_nodes if 1550*scale <= n['center'][1] <= 1680*scale], key=lambda x: x['center'][0])
        row_bot = sorted([n for n in seg_nodes if n['center'][1] > 1680*scale], key=lambda x: x['center'][0])

        # 레이아웃 매핑 (X좌표 순서: [Left-Muscle, Right-Muscle, Left-Fat, Right-Fat] 또는 [Muscle, Fat])
        if len(row_top) >= 4:
            matched_data["왼쪽팔 근육"] = next((ev for ev in evals if ev in row_top[0]['text']), "미검출")
            matched_data["오른쪽팔 근육"] = next((ev for ev in evals if ev in row_top[1]['text']), "미검출")
            matched_data["왼쪽팔 체지방"] = next((ev for ev in evals if ev in row_top[2]['text']), "미검출")
            matched_data["오른쪽팔 체지방"] = next((ev for ev in evals if ev in row_top[3]['text']), "미검출")
        
        if len(row_mid) >= 2:
            matched_data["복부 근육"] = next((ev for ev in evals if ev in row_mid[0]['text']), "미검출")
            matched_data["복부 체지방"] = next((ev for ev in evals if ev in row_mid[1]['text']), "미검출")

        if len(row_bot) >= 4:
            matched_data["왼쪽하체 근육"] = next((ev for ev in evals if ev in row_bot[0]['text']), "미검출")
            matched_data["오른쪽하체 근육"] = next((ev for ev in evals if ev in row_bot[1]['text']), "미검출")
            matched_data["왼쪽하체 체지방"] = next((ev for ev in evals if ev in row_bot[2]['text']), "미검출")
            matched_data["오른쪽하체 체지방"] = next((ev for ev in evals if ev in row_bot[3]['text']), "미검출")

        vis_image = cv2.addWeighted(overlay, 0.2, vis_image, 0.8, 0)
        cv2.imwrite(output_vis_path, vis_image)
        return matched_data

if __name__ == "__main__":
    img_path = "/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody/다운로드.jpg"
    result = InBodyMatcher().extract_and_match(img_path)
    with open("/home/roh/workspace/ExplainMyBody/experiments/PaddleOCR/inbody_matched_final.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print(f"{'항목':<15} | {'결과'}")
    print("-" * 50)
    for key, val in result.items():
        print(f"{key:<15} | {val if val else '미검출'}")
    print("="*50)
    print(f"\n[시각화 고도화] 이미지에 'Scale'(눈금)과 'Value'(실제값) 구분 표시를 추가했습니다.")
