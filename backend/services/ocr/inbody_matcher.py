"""
인바디 결과지 초정밀 매칭 - 원근 변환 추가
- 4개 꼭지점 검출 및 원근 변환으로 기울어진 문서 정렬
"""

import os
# DEBUG_START
import random
# DEBUG_END
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import contextmanager
import tempfile

# 환경 변수 설정
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_executor_v2'] = '0'
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import cv2
import json
import re
import numpy as np
import difflib
from paddleocr import PaddleOCR


@dataclass
class MatchConfig:
    """매칭 설정 데이터 클래스"""
    regex: str
    y_range: Tuple[int, int]
    direction: str
    x_tolerance: int = 800
    y_tolerance: int = 50
    allow_zero: bool = False


class Scaler:
    """해상도 스케일링 담당 클래스"""
    def __init__(self, target_height: int, base_height: int = 2400):
        self.target_height = target_height
        self.base_height = base_height
        self.scale_factor = target_height / base_height
        
    def scale(self, value: float) -> int:
        """단일 값 스케일링"""
        return int(value * self.scale_factor)
        
    def scale_range(self, value_range: Tuple[int, int]) -> Tuple[int, int]:
        """범위 튜플 스케일링"""
        return (self.scale(value_range[0]), self.scale(value_range[1]))
    
    def scale_config(self, config: MatchConfig) -> MatchConfig:
        """MatchConfig 객체 전체 스케일링"""
        return MatchConfig(
            regex=config.regex,
            y_range=self.scale_range(config.y_range),
            direction=config.direction,
            x_tolerance=self.scale(config.x_tolerance),
            y_tolerance=self.scale(config.y_tolerance),
            allow_zero=config.allow_zero
        )


class ConfigManager:
    """설정 관리 클래스"""
    
    @staticmethod
    def get_default_targets() -> Dict[str, MatchConfig]:
        """기본 타겟 설정 반환 (2400px 기준 좌표)"""
        return {
            "신장": MatchConfig(r"(\d{3})", (130, 220), "down"),
            "연령": MatchConfig(r"(\d{2})", (130, 220), "down"),
            "성별": MatchConfig(r"(남성|여성|남|여)$", (130, 220), "down"),
            "체수분": MatchConfig(r"(\d+\.\d+)", (300, 380), "right"),
            "단백질": MatchConfig(r"(\d+\.\d+)", (370, 440), "right"),
            "무기질": MatchConfig(r"(\d+\.\d+)", (430, 490), "right"),
            "체지방": MatchConfig(r"(\d+\.\d+)", (480, 550), "right", x_tolerance=2000),
            "체중": MatchConfig(r"(\d+\.\d+)", (740, 830), "right", x_tolerance=2000),
            "골격근량": MatchConfig(r"(\d+\.\d+)", (830, 910), "right", x_tolerance=2000),
            "체지방량": MatchConfig(r"(\d+\.\d+)", (910, 980), "right", x_tolerance=2000),
            "적정체중": MatchConfig(r"(\d+\.\d+)", (550, 650), "right"),
            "체중조절": MatchConfig(r"([-+]?\d+\.\d+)", (550, 750), "right", allow_zero=True, x_tolerance=1000),
            "지방조절": MatchConfig(r"([-+]?\d+\.\d+)", (600, 800), "right", allow_zero=True, x_tolerance=1000),
            "근육조절": MatchConfig(r"([-+]?\d+\.\d+)", (650, 850), "right", allow_zero=True, x_tolerance=1000),
            "복부지방률": MatchConfig(r"(\d\.\d{2})", (850, 1050), "down"),
            "내장지방레벨": MatchConfig(r"(\d+)", (950, 1150), "down"),
            "BMI": MatchConfig(r"(\d+\.\d+)", (1120, 1180), "right", x_tolerance=2000),
            "체지방률": MatchConfig(r"(\d+\.\d+)", (1200, 1260), "right", x_tolerance=2000),
            "제지방량": MatchConfig(r"(\d+\.?\d*)", (1140, 1210), "right"),
            "기초대사량": MatchConfig(r"(\d{4})", (1210, 1260), "right"),
            "비만도": MatchConfig(r"(\d+)", (1250, 1300), "right"),
            "권장섭취열량": MatchConfig(r"(\d{4})", (1290, 1350), "right"),
        }
    
    @staticmethod
    def get_correction_map() -> Dict[str, str]:
        """오타 교정 맵 반환"""
        return {
            "척정체중": "적정체중", "정체중": "적정체중",
            "체지방륨": "체지방률", "체지방율": "체지방률",
            "골격극량": "골격근량", "극근량": "골격근량",
            "무기실": "무기질", "보부지방률": "복부지방률",
            "부지방률": "복부지방률", "내장지방레빌": "내장지방레벨",
            "제지방륨": "제지방량", "제지방률": "제지방량",
            "율근론": "골격근량", "율근량": "골격근량", "율근륜": "골격근량",
            "근육량": "골격근량", "Skeletal": "골격근량",
            "MuscleMass": "골격근량", "SkeletalMtiscleMass": "골격근량",
            "단백칠": "단백질", "무기칠": "무기질", 
            "단백절": "단백질", "골격근": "골격근량"
        }


@contextmanager
def temporary_file(suffix='.jpg'):
    """임시 파일 컨텍스트 매니저"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        yield temp_path
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass


class DocumentRectifier:
    """문서 4점 원근 변환 클래스"""
    
    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """4개의 점을 [좌상, 우상, 우하, 좌하] 순서로 정렬"""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
    
    @staticmethod
    def calculate_skew_score(corners: np.ndarray, img_shape: tuple) -> float:
        """
        기울기 점수 계산 (0~100, 높을수록 기울어짐)
        
        Returns:
            0-20: 거의 정면 (원근 변환 불필요)
            20-50: 약간 기울어짐 (선택적)
            50+: 심하게 기울어짐 (원근 변환 필요)
        """
        rect = DocumentRectifier.order_points(corners)
        (tl, tr, br, bl) = rect
        h, w = img_shape[:2]
        
        # 1. 면적 비율
        detected_area = cv2.contourArea(corners)
        image_area = h * w
        area_ratio = detected_area / image_area
        area_score = (1 - area_ratio) * 100
        
        # 2. 각도 왜곡
        def angle_between(p1, p2, p3):
            v1 = p1 - p2
            v2 = p3 - p2
            angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            return np.degrees(angle)
        
        angles = [
            angle_between(tl, tr, br),
            angle_between(tr, br, bl),
            angle_between(br, bl, tl),
            angle_between(bl, tl, tr)
        ]
        
        angle_deviation = np.mean([abs(angle - 90) for angle in angles])
        angle_score = angle_deviation * 2
        
        # 3. 변 길이 비율
        top_width = np.linalg.norm(tr - tl)
        bottom_width = np.linalg.norm(br - bl)
        left_height = np.linalg.norm(bl - tl)
        right_height = np.linalg.norm(br - tr)
        
        width_ratio = abs(top_width - bottom_width) / max(top_width, bottom_width)
        height_ratio = abs(left_height - right_height) / max(left_height, right_height)
        ratio_score = (width_ratio + height_ratio) * 50
        
        total_score = (area_score * 0.3 + angle_score * 0.5 + ratio_score * 0.2)
        
        return min(100, total_score)
    
    @staticmethod
    def find_document_corners(img: np.ndarray) -> Optional[np.ndarray]:
        """윤곽선 검출로 문서 4개 꼭지점 찾기"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            
            for contour in contours:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                if len(approx) == 4:
                    return approx.reshape(4, 2)
            return None
        except:
            return None
    
    @staticmethod
    def apply_perspective_transform(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """원근 변환으로 문서를 정면으로 펼치기"""
        rect = DocumentRectifier.order_points(corners)
        (tl, tr, br, bl) = rect
        
        widthA = np.sqrt((br[0] - bl[0]) ** 2 + (br[1] - bl[1]) ** 2)
        widthB = np.sqrt((tr[0] - tl[0]) ** 2 + (tr[1] - tl[1]) ** 2)
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt((tr[0] - br[0]) ** 2 + (tr[1] - br[1]) ** 2)
        heightB = np.sqrt((tl[0] - bl[0]) ** 2 + (tl[1] - bl[1]) ** 2)
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        return warped
    
    @staticmethod
    def rectify_auto(img: np.ndarray, threshold: float = 15.0) -> Tuple[np.ndarray, bool, float]:
        """
        자동으로 기울기를 판단하여 원근 변환 적용
        
        Args:
            img: 입력 이미지
            threshold: 기울기 임계값 (이 값 이상이면 변환 적용)
        
        Returns:
            (변환된 이미지, 변환 적용 여부, 기울기 점수)
        """
        try:
            corners = DocumentRectifier.find_document_corners(img)
            
            if corners is None:
                return img, False, 0.0
            
            h, w = img.shape[:2]
            detected_area = cv2.contourArea(corners)
            image_area = h * w
            area_ratio = detected_area / image_area
            
            if area_ratio < 0.3:
                return img, False, 0.0
            
            skew_score = DocumentRectifier.calculate_skew_score(corners, img.shape)
            
            if skew_score >= threshold:
                warped = DocumentRectifier.apply_perspective_transform(img, corners)
                # DEBUG_START
                if True: # 디버깅 강제
                    debug_img = img.copy()
                    cv2.drawContours(debug_img, [corners.astype(int)], -1, (0, 0, 255), 3)
                    cv2.putText(debug_img, f"Skew: {skew_score:.1f} (Threshold: {threshold}) - WARPED", 
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imwrite("debug_rectification.jpg", debug_img)
                # DEBUG_END
                return warped, True, skew_score
            else:
                # DEBUG_START
                if True:
                    debug_img = img.copy()
                    cv2.drawContours(debug_img, [corners.astype(int)], -1, (0, 255, 0), 3)
                    cv2.putText(debug_img, f"Skew: {skew_score:.1f} (Threshold: {threshold}) - SKIPPED", 
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imwrite("debug_rectification.jpg", debug_img)
                # DEBUG_END
                return img, False, skew_score
                
        except:
            return img, False, 0.0


class InBodyMatcher:
    """인바디 결과지 매칭 클래스"""
    
    # 해상도 설정 (성능 최적화)
    TARGET_HEIGHT = 1200 # 1200 → 960 (사용자 요청, 처리 속도 향상)
    
    def __init__(self, config_path: Optional[str] = None, 
                 auto_perspective: bool = True,
                 skew_threshold: float = 15.0):
        """
        Args:
            config_path: 설정 파일 경로 (JSON)
            auto_perspective: 자동 원근 변환 활성화 (기본: True)
            skew_threshold: 기울기 임계값 (0-100, 기본: 15.0)
        """
        try:
            import logging
            logging.getLogger('ppocr').setLevel(logging.ERROR)
            
            self.ocr = PaddleOCR(
                lang='korean',
                ocr_version='PP-OCRv5',
                text_det_limit_side_len=960,      # 960 
                text_det_unclip_ratio=1.5,        # 2.0 → 1.6 (속도 향상)
                use_textline_orientation=False,   # 인바디는 수평 문서
                det_db_thresh=0.3,                # 검출 임계값 낮춤 (더 많은 텍스트)
                det_db_box_thresh=0.5             # 박스 임계값 낮춤
            )
        except Exception as e:
            raise Exception(f"PaddleOCR 초기화 실패: {e}")
        
        self.correction_map = ConfigManager.get_correction_map()
        
        # 스케일러 초기화
        self.scaler = Scaler(self.TARGET_HEIGHT)
        
        # 타겟 좌표 스케일링 (2400px 기준 → TARGET_HEIGHT 기준)
        base_targets = ConfigManager.get_default_targets()
        self.targets = {
            k: self.scaler.scale_config(v) for k, v in base_targets.items()
        }
        
        self.auto_perspective = auto_perspective
        self.skew_threshold = skew_threshold
        
        print(f"✅ OCR 설정: 해상도={self.TARGET_HEIGHT}px, 스케일={self.scaler.scale_factor:.3f}")
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

        # DEBUG_START
        self.debug_info = {}
        # DEBUG_END

    
    def _load_config(self, config_path: str):
        """외부 설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            pass
    
    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """Hough Transform을 이용한 미세 기울기 보정"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 해상도에 맞춰 파라미터 스케일링
            min_line_len = self.scaler.scale(100)
            max_line_gap = self.scaler.scale(10)
            
            # accumulator threshold도 스케일링 (2400px 기준 100 -> 960px 기준 약 40)
            hough_thresh = self.scaler.scale(100)
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, hough_thresh, minLineLength=min_line_len, maxLineGap=max_line_gap)
            
            if lines is not None:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    if -10 < angle < 10:
                        angles.append(angle)
                
                if angles:
                    median_angle = np.median(angles)
                    (h, w) = img.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return img
        except:
            return img
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """이미지 전처리"""
        try:
            img = self._deskew(img)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            enhanced = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
            return enhanced
        except:
            return img
    
    def _extract_nodes(self, image_path: str) -> List[Dict[str, Any]]:
        """OCR을 통해 텍스트 노드 추출"""
        try:
            result = self.ocr.predict(input=image_path)
            all_nodes = []
            
            if result:
                for res in result:
                    dt_polys = res.get('dt_polys', [])
                    rec_texts = res.get('rec_texts', [])
                    rec_scores = res.get('rec_scores', [])
                    
                    for poly, text, conf in zip(dt_polys, rec_texts, rec_scores):
                        pts = np.array(poly)
                        x_min, y_min = pts.min(axis=0)
                        x_max, y_max = pts.max(axis=0)
                        
                        node = {
                            'text': text.strip().replace(" ", "").replace("|", ""),
                            'bbox': [int(x_min), int(y_min), int(x_max), int(y_max)],
                            'h': int(y_max - y_min),
                            'center': [(x_min + x_max) / 2, (y_min + y_max) / 2],
                            'conf': float(conf),
                            'poly': pts.astype(int).tolist() # 다각형 좌표 저장
                        }
                        all_nodes.append(node)
            
            return all_nodes
        except:
            return []
    
    def _correct_text(self, text: str) -> str:
        """텍스트 오타 교정"""
        return self.correction_map.get(text, text)
    
    def _find_key_node(self, key: str, nodes: List[Dict], y_range: Tuple[int, int]) -> Optional[Dict]:
        """키워드에 해당하는 노드 찾기"""
        yr_min, yr_max = y_range
        
        candidates = []
        for node in nodes:
            # 상하 여백 스케일링 (50px -> 25px at 0.5 scale)
            y_buffer = self.scaler.scale(50)
            if not (yr_min - y_buffer <= node['center'][1] <= yr_max + y_buffer):
                continue
            
            text_without_parens = re.sub(r'\([^)]*\)', '', node['text'])
            corrected_text = self._correct_text(text_without_parens)
            original_corrected = self._correct_text(node['text'])
            
            if key in corrected_text or key in original_corrected:
                candidates.append(node)
            else:
                ratio1 = difflib.SequenceMatcher(None, key, corrected_text).ratio()
                ratio2 = difflib.SequenceMatcher(None, key, original_corrected).ratio()
                max_ratio = max(ratio1, ratio2)
                
                if max_ratio > 0.5:
                    candidates.append(node)
        
        if not candidates:
            return None
            
        # 우선순위 정렬: 
        # 1. 완전 일치 (체중 == 체중)
        # 2. 시작 일치 (체중... == 체중) -> 접두어
        # 3. 포함 (저체중 contains 체중) -> 이건 최하위여야 함
        # 4. Fuzzy 점수
        
        def sort_key(node):
            text = self._correct_text(re.sub(r'\([^)]*\)', '', node['text']))
            
            # 1순위: 완전 일치
            if text == key:
                return (0, -node['conf']) # 점수 낮을수록 우선 (0 < 1 < 2)
            
            # 2순위: 원래 텍스트 완전 일치
            if node['text'] == key:
                return (1, -node['conf'])
                
            # 3순위: 접두어로 시작 (예: "체중 :" vs "저체중")
            if text.startswith(key):
                return (2, -node['conf'])
                
            # 4순위: 포함 (Fuzzy 포함)
            return (3, -node['conf'])

        candidates.sort(key=sort_key)
        
        # 디버그: 키워드 후보가 여러 개일 때 선택된 것 출력
        # if len(candidates) > 1:
        #    print(f"[Key Select] '{key}' -> '{candidates[0]['text']}' (from {len(candidates)})")
            
        return candidates[0]
    
    def _match_value(self, key: str, key_node: Dict, config: MatchConfig, 
                     nodes: List[Dict], used_node_ids: Optional[set] = None) -> Optional[str]:
        """값 노드 매칭 (동적 허용오차 적용)"""
        yr_min, yr_max = config.y_range
        candidates = []
        
        # 디버그 모드
        debug = key in ["체중조절", "지방조절", "근육조절", "체중", "적정체중", "비만도", 
                       "BMI", "체지방률", "골격근량", "체지방량"]
        
        # 기준 높이
        ref_h = key_node.get('h', self.scaler.scale(30))
        if ref_h < 1: ref_h = self.scaler.scale(30)

        # 동적 허용오차 (텍스트 높이 기반)
        base_dy = self.scaler.scale(40)
        dynamic_dy = int(ref_h * 1.7)
        dy_max_limit = max(base_dy, dynamic_dy) 
        
        roi_buffer = max(self.scaler.scale(100), int(ref_h * 3.0))

        if debug:
            y_buffer_debug = self.scaler.scale(50)
            print(f"\n{'='*60}")
            print(f"[{key}] 매칭 시작 (Dynamic Tolerance)")
            print(f"  키워드: '{key_node['text']}' (h={ref_h})")
            print(f"  위치: y={key_node['center'][1]:.0f}, bbox={key_node['bbox']}")
            print(f"  허용오차 dy_max: {dy_max_limit} (Base: {base_dy}, Dynamic: {dynamic_dy})")
            print(f"  ROI Y범위: {yr_min} ~ {yr_max} (Buffer: {roi_buffer})")
            print(f"{'='*60}")
        
        for node in nodes:
            if node == key_node:
                continue
            
            # 이미 사용된 노드는 제외 (중복 매칭 방지)
            if used_node_ids is not None and id(node) in used_node_ids:
                if debug:
                    pass
                    # print(f"      [SKIP] 이미 사용된 노드: '{node['text']}'")
                continue
            
            # 텍스트 정규화
            clean_text = re.sub(r'\(.*?\)', '', node['text'])
            clean_text = clean_text.replace('I', '1').replace('l', '1').replace(',', '.').strip()
            
            # 디버그: Y 범위 내의 모든 노드 출력
            y_buffer_debug_wide = self.scaler.scale(100)
            if debug and (yr_min - y_buffer_debug_wide <= node['center'][1] <= yr_max + y_buffer_debug_wide):
                 # print(f"  노드: '{node['text']}' (정규화: '{clean_text}') at y={node['center'][1]:.0f}")
                 pass

            # 정규식 매칭
            match = re.search(config.regex, clean_text)
            if not match:
                continue
            
            val = match.group(1)
            
            # 1. ROI 체크
            in_roi = (yr_min - roi_buffer <= node['center'][1] <= yr_max + roi_buffer)
            
            if not in_roi:
                # ROI 밖이면 과감히 제외 (사용자 요청: Relaxed ROI 제거)
                # if debug: print(f"      [SKIP] ROI 밖: '{val}' at y={node['center'][1]:.0f}")
                continue
            
            # 2. 위치 관계 및 방향 체크
            is_dir_match = False
            fail_reason = ""

            if config.direction == "right":
                key_right = key_node['bbox'][2]
                node_center_x = node['center'][0]
                
                # dx: 키워드 우측 끝 ~ 값 중심 (양수여야 오른쪽)
                dx = node_center_x - key_right
                
                # dy 계산: Center-to-Center와 Top-to-Top 중 더 작은 값 사용
                # 이유: 폰트 크기 차이가 클 때 Center는 안 맞아도 Top은 맞는 경우가 있음 (또는 그 반대)
                dy_center = abs(node['center'][1] - key_node['center'][1])
                dy_top = abs(node['bbox'][1] - key_node['bbox'][1])
                dy = min(dy_center, dy_top)
                
                max_dist_x = config.x_tolerance
                # 겹침 허용: 키워드 안쪽으로 조금 들어온 것도 허용 (기존 -0.5 -> 0으로 수정)
                # 사용자 피드백: "적정체중" 등이 왼쪽 노드를 잡는 문제 발생 -> 엄격하게 Right만 허용
                min_dx = 0 # -int(ref_h * 0.5) 
                
                # 상세 조건 체크
                cond_dx = (min_dx < dx < max_dist_x)
                cond_vertical = (dy < dy_max_limit)
                
                is_dir_match = cond_dx and cond_vertical
                
                if not is_dir_match:
                    if not cond_dx: fail_reason += f"DX_FAIL({dx:.1f} not in {min_dx}~{max_dist_x}) "
                    if not cond_vertical: fail_reason += f"DY_FAIL({dy:.1f} >= {dy_max_limit}) "
                
            elif config.direction == "down":
                dx = abs(node['center'][0] - key_node['center'][0])
                dy = node['center'][1] - key_node['bbox'][3]
                
                max_dist_x = int(ref_h * 5.0)
                max_dist_y = self.scaler.scale(300)
                
                cond_dx = (dx < max_dist_x)
                cond_dy = (0 < dy < max_dist_y)
                
                is_dir_match = cond_dx and cond_dy
                
                if not is_dir_match:
                     if not cond_dx: fail_reason += f"DX_FAIL({dx:.1f}) "
                     if not cond_dy: fail_reason += f"DY_FAIL({dy:.1f}) "
            
            if debug:
                status = "PASS" if is_dir_match else "FAIL"
                print(f"      [{status}] 값: '{val}', dx={dx:.1f}, dy={dy:.1f} (Limit: {dy_max_limit}) {fail_reason}")

            if not is_dir_match:
                continue
            
            # 3. 0값 필터링
            if not config.allow_zero:
                try:
                    if abs(float(val)) < 0.01:
                        continue
                except:
                    pass
            
            # 4. 눈금선(매우 작은 텍스트) 필터링
            # 해상도가 낮아지면 OCR 박스 크기가 비선형적으로 변할 수 있으므로, 
            # 기준 높이의 85% 미만은 과감하게 필터링 (기존 0.7 -> 0.8 상향)
            if node.get('h', 999) < (ref_h * 0.8):
                if debug: print(f"      [SKIP] 작은 텍스트: '{val}' h={node['h']} (ref_h={ref_h})")
                continue

            # 5. 점수 계산
            # dy 점수 스케일링 (2400px 기준 500점 -> 현재 해상도 기준 조정)
            # 기존: norm_dy = dy / self.SCALE_FACTOR
            # Scaler 사용시: dy는 이미 스케일링된 좌표계임. 
            # 점수 가중치는 해상도에 무관하게 '픽셀 차이'에 비례해야 함.
            # 하지만 원본 로직이 '2400px 기준 거리'로 환산해서 점수를 매겼었음.
            # self.scaler.scale_factor로 나누면 원본 2400px 기준 거리가 됨.
            
            # dy 점수 스케일링 (2400px 기준 500점 -> 현재 해상도 기준 조정)
            # 기존: norm_dy = dy / self.SCALE_FACTOR
            # Scaler 사용시: dy는 이미 스케일링된 좌표계임. 
            # 점수 가중치는 해상도에 무관하게 '픽셀 차이'에 비례해야 함.
            # 하지만 원본 로직이 '2400px 기준 거리'로 환산해서 점수를 매겼었음.
            # self.scaler.scale_factor로 나누면 원본 2400px 기준 거리가 됨.
            
            norm_dy = dy / self.scaler.scale_factor
            norm_dx = abs(dx) / self.scaler.scale_factor
            
            # dy 가중치를 10.0으로 복구 (행 바뀜 방지)
            # 이유: x_tolerance를 2000 등으로 넓혔으므로, 
            # 다른 행에 있지만 x좌표가 더 가까운 엉뚱한 값을 잡지 않도록 수직(dy) 패널티를 강화해야 함.
            score = (norm_dy * 10.0) + norm_dx
            candidates.append((score, val, node))

        # DEBUG_START
        self.debug_info["matches"].append({
            "key": key,
            "key_node": key_node,
            "config": config,
            "candidates": [c[2] for c in candidates],
            "selected": candidates[0][2] if candidates else None,
            "roi": (yr_min, yr_max)
        })
        # DEBUG_END

        if candidates:
            candidates.sort(key=lambda x: x[0])
            best_node = candidates[0][2]
            best_val = candidates[0][1]
            
            # 선택된 노드 ID 등록
            if used_node_ids is not None:
                used_node_ids.add(id(best_node))
            
            if debug:
                print(f"    => 최종 선택: '{best_val}' (Score={candidates[0][0]:.1f})")
            return best_val
            
        return None
    

    def _extract_segment_evaluations(self, nodes: List[Dict]) -> Dict[str, str]:
        """부위별 평가 추출 (Clustering 방식)"""
        # 해상도 스케일링된 ROI
        seg_y_min = self.scaler.scale(1400)
        seg_y_max = self.scaler.scale(1900)
        
        eval_keywords = ["표준이하", "표준이상", "표준"]
        
        # 1. 평가 키워드 노드만 수집 (ROI 내부만)
        eval_nodes = []
        for node in nodes:
            # ROI 필터링
            if not (seg_y_min <= node['center'][1] <= seg_y_max):
                continue
                
            for k in eval_keywords:
                if k in node['text']:
                    eval_nodes.append(node)
                    break
        
        if not eval_nodes:
            return {}

        # 2. Y좌표 기준으로 정렬
        eval_nodes.sort(key=lambda x: x['center'][1])
        
        # 3. 행 구분 (Clustering)
        rows = []
        if eval_nodes:
            current_row = [eval_nodes[0]]
            avg_h = eval_nodes[0]['h']
            
            for i in range(1, len(eval_nodes)):
                node = eval_nodes[i]
                prev_node = current_row[-1]
                
                # Y 차이가 높이의 0.6배 이상이면 새로운 행
                if abs(node['center'][1] - prev_node['center'][1]) > (avg_h * 0.6):
                    current_row.sort(key=lambda x: x['center'][0])
                    rows.append(current_row)
                    current_row = []
                
                current_row.append(node)
                avg_h = (avg_h + node['h']) / 2
                
            if current_row:
                current_row.sort(key=lambda x: x['center'][0])
                rows.append(current_row)
            
        results = {}
        
        # 행 위치 기반 매핑 (상단, 중단, 하단)
        row_top = []
        row_mid = []
        row_bot = []
        
        for row in rows:
            avg_y = sum(n['center'][1] for n in row) / len(row)
            rel_y = avg_y / self.TARGET_HEIGHT
            
            if 0.55 <= rel_y < 0.68:
                row_top = row
            elif 0.68 <= rel_y < 0.75:
                row_mid = row
            elif 0.75 <= rel_y < 0.90:
                row_bot = row

        def _get_val(n):
            for k in eval_keywords:
                if k in n['text']: return k
            return "미검출"

        if len(row_top) >= 4:
            results["왼쪽팔 근육"] = _get_val(row_top[0])
            results["오른쪽팔 근육"] = _get_val(row_top[1])
            if len(row_top) > 2: results["왼쪽팔 체지방"] = _get_val(row_top[2])
            if len(row_top) > 3: results["오른쪽팔 체지방"] = _get_val(row_top[3])
                
        if len(row_mid) >= 2:
             results["복부 근육"] = _get_val(row_mid[0])
             results["복부 체지방"] = _get_val(row_mid[1])
             
        if len(row_bot) >= 4:
            results["왼쪽하체 근육"] = _get_val(row_bot[0])
            results["오른쪽하체 근육"] = _get_val(row_bot[1])
            if len(row_bot) > 2: results["왼쪽하체 체지방"] = _get_val(row_bot[2])
            if len(row_bot) > 3: results["오른쪽하체 체지방"] = _get_val(row_bot[3])
            
        return results
    
    def extract_and_match(self, image_path: str) -> Dict[str, Optional[str]]:
        """이미지에서 인바디 데이터 추출 및 매칭"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        try:
            # ⏱️ 전체 처리 시간 측정
            total_start = time.time()
            
            # DEBUG_START
            self.debug_info = {
                "nodes": [],
                "matches": []
            }
            # DEBUG_END

            
            # ⏱️ 1. 이미지 로드
            load_start = time.time()
            src_img = cv2.imread(image_path)
            if src_img is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
            load_time = time.time() - load_start
            
            print(f"📸 원본 이미지 크기: {src_img.shape[:2]} (⏱️ {load_time:.3f}초)")
            
            # ⏱️ 2. 원근 변환 (Perspective Transform)
            perspective_time = 0.0
            if self.auto_perspective:
                perspective_start = time.time()
                src_img, applied, skew_score = DocumentRectifier.rectify_auto(
                    src_img, threshold=self.skew_threshold
                )
                perspective_time = time.time() - perspective_start
                if applied:
                    print(f"🔄 원근 변환 적용 (기울기 점수: {skew_score:.1f}, ⏱️ {perspective_time:.3f}초)")
                else:
                    if skew_score > 0:
                        print(f"✓ 정면 문서 (기울기 점수: {skew_score:.1f}, 임계값: {self.skew_threshold}, ⏱️ {perspective_time:.3f}초)")
            
            # ⏱️ 3. 해상도 정규화
            resize_start = time.time()
            target_h = self.TARGET_HEIGHT  # 1600px (최적화)
            ratio = target_h / src_img.shape[0]
            img = cv2.resize(
                src_img,
                (int(src_img.shape[1] * ratio), target_h),
                interpolation=cv2.INTER_LANCZOS4
            )
            resize_time = time.time() - resize_start
            
            print(f"📏 정규화된 크기: {img.shape[:2]} (⏱️ {resize_time:.3f}초)")
            
            # ⏱️ 4. 전처리 (Preprocessing)
            preprocess_start = time.time()
            with temporary_file() as temp_path:
                processed_img = self._preprocess_image(img)
                cv2.imwrite(temp_path, processed_img)
                preprocess_time = time.time() - preprocess_start
                print(f"🎨 전처리 완료 (Deskew + CLAHE, ⏱️ {preprocess_time:.3f}초)")
                
                # ⏱️ 5. OCR 텍스트 추출 (가장 느린 단계)
                ocr_start = time.time()
                all_nodes = self._extract_nodes(temp_path)
                
                # DEBUG_START
                self.debug_info["nodes"] = all_nodes
                # DEBUG_END
                
                ocr_time = time.time() - ocr_start
            
            print(f"📝 추출된 텍스트 노드: {len(all_nodes)}개 (⏱️ {ocr_time:.3f}초)")
            
            if not all_nodes:
                print("⚠️ 텍스트를 추출할 수 없습니다")
                return {}
            
            # ⏱️ 6. 매칭 수행 (Postprocessing)
            match_start = time.time()
            matched_data = {}
            used_node_ids = set() # 중복 매칭 방지용
            
            for key, config in self.targets.items():
                key_node = self._find_key_node(key, all_nodes, config.y_range)
                
                if not key_node:
                    matched_data[key] = None
                    continue
                
                value = self._match_value(key, key_node, config, all_nodes, used_node_ids)
                matched_data[key] = value
            
            # 부위별 평가 추출
            segment_results = self._extract_segment_evaluations(all_nodes)
            matched_data.update(segment_results)
            match_time = time.time() - match_start
            
            # 매칭 통계
            detected = sum(1 for v in matched_data.values() if v is not None)
            total = len(matched_data)
            print(f"✅ 매칭 완료: {detected}/{total} 항목 ({detected/total*100:.1f}%, ⏱️ {match_time:.3f}초)")
            
            # ⏱️ 전체 처리 시간 요약
            total_time = time.time() - total_start
            print(f"\n⏱️ === OCR 처리 시간 상세 분석 ===")
            print(f"   1. 이미지 로드:      {load_time:.3f}초 ({load_time/total_time*100:5.1f}%)")
            print(f"   2. 원근 변환:        {perspective_time:.3f}초 ({perspective_time/total_time*100:5.1f}%)")
            print(f"   3. 해상도 정규화:    {resize_time:.3f}초 ({resize_time/total_time*100:5.1f}%)")
            print(f"   4. 전처리 (CLAHE):   {preprocess_time:.3f}초 ({preprocess_time/total_time*100:5.1f}%)")
            print(f"   5. OCR 텍스트 추출:  {ocr_time:.3f}초 ({ocr_time/total_time*100:5.1f}%) ⚠️ 병목")
            print(f"   6. 매칭 (후처리):    {match_time:.3f}초 ({match_time/total_time*100:5.1f}%)")
            print(f"   " + "="*40)
            print(f"   총 처리 시간:        {total_time:.3f}초")
            print(f"   " + "="*40 + "\n")
            
            return matched_data
        
        except Exception as e:
            print(f"❌ 오류: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"처리 중 오류 발생: {e}")
        finally:
            # DEBUG_START
            if 'processed_img' in locals():
                self.save_visualized_result(processed_img, "debug_ocr_result.jpg")
            # DEBUG_END

    
    def save_results(self, results: Dict, output_path: str, format: str = 'json'):
        """결과를 파일로 저장"""
        try:
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"💾 JSON 결과 저장 완료: {output_path}")
            
            elif format in ['dict', 'python']:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("# InBody 측정 결과\n")
                    f.write("inbody_data = ")
                    f.write(json.dumps(results, ensure_ascii=False, indent=4))
                print(f"💾 Python 형식 결과 저장 완료: {output_path}")
        except Exception as e:
            print(f"⚠️ 결과 저장 중 오류 발생 ({output_path}): {e}")
    
    def get_structured_results(self, results: Dict) -> Dict:
        """결과를 구조화된 딕셔너리로 반환"""
        structured = {
            "기본정보": {
                "신장": results.get("신장"),
                "연령": results.get("연령"),
                "성별": results.get("성별"),
            },
            "체성분": {
                "체수분": results.get("체수분"),
                "단백질": results.get("단백질"),
                "무기질": results.get("무기질"),
                "체지방": results.get("체지방"),
            },
            "체중관리": {
                "체중": results.get("체중"),
                "골격근량": results.get("골격근량"),
                "체지방량": results.get("체지방량"),
                "적정체중": results.get("적정체중"),
                "체중조절": results.get("체중조절"),
                "지방조절": results.get("지방조절"),
                "근육조절": results.get("근육조절"),
            },
            "비만분석": {
                "BMI": results.get("BMI"),
                "체지방률": results.get("체지방률"),
                "복부지방률": results.get("복부지방률"),
                "내장지방레벨": results.get("내장지방레벨"),
                "비만도": results.get("비만도"),
            },
            "연구항목": {
                "제지방량": results.get("제지방량"),
                "기초대사량": results.get("기초대사량"),
                "권장섭취열량": results.get("권장섭취열량"),
            },
            "부위별근육분석": {
                "왼쪽팔": results.get("왼쪽팔 근육"),
                "오른쪽팔": results.get("오른쪽팔 근육"),
                "복부": results.get("복부 근육"),
                "왼쪽하체": results.get("왼쪽하체 근육"),
                "오른쪽하체": results.get("오른쪽하체 근육"),
            },
            "부위별체지방분석": {
                "왼쪽팔": results.get("왼쪽팔 체지방"),
                "오른쪽팔": results.get("오른쪽팔 체지방"),
                "복부": results.get("복부 체지방"),
                "왼쪽하체": results.get("왼쪽하체 체지방"),
                "오른쪽하체": results.get("오른쪽하체 체지방"),
            }
        }
        
        return structured

    # DEBUG_START
    def save_visualized_result(self, img: np.ndarray, output_path: str):
        """디버깅용 시각화 이미지 저장"""
        try:
            vis_img = img.copy()
            
            # 1. 모든 텍스트 노드 그리기 (회색)
            for node in self.debug_info.get("nodes", []):
                if 'poly' in node:
                    pts = np.array(node['poly'], np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis_img, [pts], True, (200, 200, 200), 1)
                else:
                    bbox = node['bbox']
                    cv2.rectangle(vis_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (200, 200, 200), 1)
            
            # 2. 매칭 정보 그리기
            for match in self.debug_info.get("matches", []):
                key = match['key']
                key_node = match['key_node']
                selected = match['selected']
                candidates = match['candidates']
                config = match['config']
                
                # 색상 생성 (키마다 다르게)
                color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                
                # C. 후보군 (노란색) 및 점수 표시
                for idx, cand in enumerate(candidates):
                    # cand 구조: (dist_score, val, node, dx, dy, dy_score, dx_score)
                    score, val, cand_node, dx, dy, dy_s, dx_s = cand
                    
                    c_bbox = cand_node['bbox']
                    color_cand = (0, 255, 255)
                    
                    # 1순위는 조금 더 진하게
                    if idx == 0:
                        cv2.rectangle(vis_img, (c_bbox[0], c_bbox[1]), (c_bbox[2], c_bbox[3]), (0, 0, 255), 2)
                    else:
                        cv2.rectangle(vis_img, (c_bbox[0], c_bbox[1]), (c_bbox[2], c_bbox[3]), color_cand, 1)
                    
                    # 점수 상세 정보 텍스트 표시
                    info_text = f"S:{int(score)} (Y:{int(dy_s)} X:{int(dx_s)})"
                    cv2.putText(vis_img, info_text, (c_bbox[2]+5, c_bbox[1]+10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2) # 그림자
                    cv2.putText(vis_img, info_text, (c_bbox[2]+5, c_bbox[1]+10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

                
                # D. 최종 선택 (빨간색 + 연결선)
                if selected:
                    s_bbox = selected['bbox']
                    # 키 -> 값 연결 선
                    cv2.line(vis_img, 
                            (int(key_node['center'][0]), int(key_node['center'][1])),
                            (int(selected['center'][0]), int(selected['center'][1])),
                            (0, 0, 255), 2)

            cv2.imwrite(output_path, vis_img)
            print(f"🐛 디버그 이미지 저장 완료: {output_path}")
        except Exception as e:
            print(f"⚠️ 디버그 이미지 저장 실패: {e}")
    # DEBUG_END



def main():
    """메인 실행 함수"""
    img_path = sys.argv[1] if len(sys.argv) > 1 else "444.jpg"
    
    try:
        print("=" * 60)
        print("InBody OCR 처리 시작")
        print("=" * 60)
        
        if not os.path.exists(img_path):
            print(f"❌ 파일을 찾을 수 없습니다: {img_path}")
            sys.exit(1)
        
        print(f"✓ 파일 확인: {img_path}")
        
        matcher = InBodyMatcher(
            auto_perspective=True,
            skew_threshold=15.0
        )
        
        print("✓ InBodyMatcher 초기화 완료")
        print()
        
        result = matcher.extract_and_match(img_path)
        
        if not result:
            print("\n❌ OCR 결과가 비어있습니다!")
            sys.exit(1)
        
        # 결과 출력
        print("\n" + "=" * 50)
        print(f"{'항목':<15} | {'결과'}")
        print("-" * 50)
        
        has_data = False
        for key, val in result.items():
            if val and val != "미검출":
                has_data = True
            print(f"{key:<15} | {val if val else '미검출'}")
        
        print("=" * 50)
        
        if not has_data:
            print("\n⚠️ 모든 항목이 미검출입니다!")
        else:
            # 파일로 저장하지 않고 데이터 구조만 반환합니다.
            # matcher.save_results(result, "inbody_result.json", format='json')
            
            structured = matcher.get_structured_results(result)
            # matcher.save_results(structured, "inbody_result_structured.json", format='json')
            
            print("\n" + "=" * 50)
            print("📦 추출된 데이터 딕셔너리")
            print("=" * 50)
            print(json.dumps(structured, ensure_ascii=False, indent=2))
            print("=" * 50)
            
            print("\n✅ 완료")
        
    except FileNotFoundError as e:
        print(f"\n❌ 파일 오류: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        print("\n상세 오류:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()