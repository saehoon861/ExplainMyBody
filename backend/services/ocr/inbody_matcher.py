"""
인바디 결과지 초정밀 매칭 - 원근 변환 추가
- 4개 꼭지점 검출 및 원근 변환으로 기울어진 문서 정렬
"""

import os
import sys
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


class ScaleManager:
    """해상도 스케일링 관리 클래스"""
    
    def __init__(self, target_height: int, base_height: int = 2400):
        """
        Args:
            target_height: 현재 이미지의 높이
            base_height: 기준 높이 (기본값: 2400 - 원본 하드코딩 기준)
        """
        # Scaling Policy:
        # scale_ratio = current_image_height / BASE_HEIGHT (2400)
        self.scale_ratio = target_height / base_height
    
    def scale_y(self, y: int) -> int:
        """Y 좌표/거리 스케일링"""
        return int(y * self.scale_ratio)
    
    def scale_x(self, x: int) -> int:
        """X 좌표/거리 스케일링 (높이 비율 기반)"""
        # X-related distances also scale by height ratio to maintain aspect ratio logic
        return int(x * self.scale_ratio)
    
    def scale_range(self, y_range: Tuple[int, int]) -> Tuple[int, int]:
        """Y 범위 스케일링"""
        return (int(y_range[0] * self.scale_ratio), int(y_range[1] * self.scale_ratio))


@dataclass
class ScaledMatchingParameters:
    """스케일링된 매칭 파라미터 (Read-only)"""
    # A. Position Values
    segment_y_min: int
    segment_y_max: int
    segment_row_top_max: int
    segment_row_mid_min: int
    segment_row_mid_max: int
    segment_row_bot_min: int
    body_fat_percent_y_min: int

    # B. Distance/Tolerance Values
    keyword_search_y_margin: int
    roi_y_margin: int
    right_dir_x_min: int
    right_dir_y_max: int
    right_dir_x_tolerance_default: int
    down_dir_y_max: int
    down_dir_x_tolerance: int
    scale_mark_height_max: int
    large_node_height_min: int
    distance_y_weight: int # Scaled per policy

    # C. Ratio/Weight Values (No Scale)
    similarity_threshold: float
    large_node_bonus: int
    scale_mark_penalty: int
    
    # Hough Transform (Scaled)
    hough_min_line_length: int
    hough_max_line_gap: int


@dataclass
class MatchingParameters:
    """
    매칭 로직에 사용되는 파라미터 및 허용 오차 정의 (Base: 2400px)
    """
    # ==========================================
    # Category A: Position Values (SCALE)
    # ==========================================
    
    # 의미: 부위별 평가(근육, 체지방) 섹션이 시작되는 최소 Y 좌표
    # 근거: 인바디 결과지 레이아웃 상 상단 테이블 이후에 위치함
    # 스케일링: 필요 (Y 좌표 위치)
    segment_y_min: int = 1400
    
    # 의미: 부위별 평가 섹션이 끝나는 최대 Y 좌표
    # 근거: 하단 로고나 기타 정보 직전까지
    # 스케일링: 필요 (Y 좌표 위치)
    segment_y_max: int = 1900
    
    # 의미: 부위별 평가 상단 행(팔)의 최대 Y 좌표
    # 근거: 팔 데이터와 복부 데이터 사이의 경계
    # 스케일링: 필요 (Y 좌표 위치)
    segment_row_top_max: int = 1580
    
    # 의미: 부위별 평가 중간 행(복부)의 최소 Y 좌표
    # 근거: 상단 행(팔) 직후 시작
    # 스케일링: 필요 (Y 좌표 위치)
    segment_row_mid_min: int = 1580
    
    # 의미: 부위별 평가 중간 행(복부)의 최대 Y 좌표
    # 근거: 복부 데이터와 하체 데이터 사이의 경계
    # 스케일링: 필요 (Y 좌표 위치)
    segment_row_mid_max: int = 1700
    
    # 의미: 부위별 평가 하단 행(하체)의 최소 Y 좌표
    # 근거: 중간 행(복부) 직후 시작
    # 스케일링: 필요 (Y 좌표 위치)
    segment_row_bot_min: int = 1700
    
    # 의미: '체지방률' 항목 필터링을 위한 최소 Y 위치
    # 근거: 비만 분석 섹션 내의 체지방률만 찾기 위해 상단의 다른 체지방률 텍스트 무시
    # 스케일링: 필요 (Y 좌표 위치)
    body_fat_percent_y_min: int = 1210

    # ==========================================
    # Category B: Distance/Tolerance Values (SCALE)
    # ==========================================

    # 의미: 키워드 노드(예: '신장')를 찾을 때 예상 범위 앞뒤로 주는 여유 마진
    # 근거: 문서의 미세한 이동이나 OCR 박스 크기 변화 대응
    # 스케일링: 필요 (픽셀 거리)
    keyword_search_y_margin: int = 50
    
    # 의미: 값 노드를 매칭할 때 키워드 기준 Y축 탐색 범위(위아래)
    # 근거: 키워드와 값의 중심 Y좌표가 정확히 일치하지 않을 수 있음
    # 스케일링: 필요 (픽셀 거리)
    roi_y_margin: int = 50
    
    # 의미: Right 방향 매칭 시, 키워드보다 약간 왼쪽(-X)에 있는 값도 허용하는 범위
    # 근거: 정렬 오차로 인해 값이 키워드 왼쪽 끝보다 살짝 앞으로 튀어나올 수 있음
    # 스케일링: 필요 (픽셀 거리)
    right_dir_x_min: int = -50
    
    # 의미: Right 방향 매칭 시, 같은 행으로 간주하는 최대 Y 차이
    # 근거: 키워드와 값이 같은 라인에 있다고 판단하는 기준
    # 스케일링: 필요 (픽셀 거리)
    right_dir_y_max: int = 80
    
    # 의미: Right 방향 매칭 시 값 탐색 최대 거리
    # 근거: 키워드로부터 너무 멀리 떨어진 값은 오매칭 방지
    # 스케일링: 필요 (픽셀 거리)
    right_dir_x_tolerance_default: int = 800
    
    # 의미: Down 방향 매칭 시 값 탐색 최대 Y 거리
    # 근거: 키워드 바로 아래에 있는 값을 찾기 위함
    # 스케일링: 필요 (픽셀 거리)
    down_dir_y_max: int = 300
    
    # 의미: Down 방향 매칭 시 좌우 X축 허용 오차
    # 근거: 키워드와 값이 수직으로 잘 정렬되어 있는지 확인
    # 스케일링: 필요 (픽셀 거리)
    down_dir_x_tolerance: int = 150
    
    # 의미: 눈금선으로 판단하여 제외할 최대 높이
    # 근거: 그래프나 테이블의 작은 눈금선들이 OCR로 잡히는 것 방지
    # 스케일링: 필요 (노드 크기 픽셀)
    scale_mark_height_max: int = 30
    
    # 의미: 중요 텍스트(큰 글자)로 판단할 최소 높이
    # 근거: 결과값은 보통 텍스트보다 크게 인쇄됨
    # 스케일링: 필요 (노드 크기 픽셀)
    large_node_height_min: int = 35
    
    # 의미: 거리 점수 계산 시 Y 차이에 부여하는 가중치 (score = dy * weight + dx)
    # 근거: 같은 행(Y차이가 적음)에 있는 것이 X 거리가 가까운 것보다 훨씬 중요함
    # 스케일링: 필요 (픽셀 단위 가중치이므로 해상도에 따라 의미가 달라질 수 있어 스케일링 결정)
    distance_y_weight: int = 300

    # ==========================================
    # Category C: Ratio/Weight Values (NO SCALE)
    # ==========================================
    
    # 의미: 문자열 유사도 매칭 임계값 (0.0 ~ 1.0)
    # 근거: difflib.SequenceMatcher 기준
    # 스케일링: 불필요 (비율값)
    similarity_threshold: float = 0.5
    
    # 의미: 큰 노드(중요 값)에 부여하는 점수 보너스 (낮을수록 좋음)
    # 근거: 우선순위 조정을 위한 상대적 점수
    # 스케일링: 불필요 (상대적 가중치)
    large_node_bonus: int = 20000
    
    # 의미: 눈금선(노이즈)에 부여하는 점수 페널티 (높을수록 나쁨)
    # 근거: 우선순위 조정을 위한 상대적 점수
    # 스케일링: 불필요 (상대적 가중치)
    scale_mark_penalty: int = 50000
    
    # ==========================================
    # Hough Transform (Scale needed)
    # ==========================================
    # 의미: 선으로 인식할 최소 길이
    # 근거: 너무 짧은 선은 노이즈로 처리
    # 스케일링: 필요
    hough_min_line_length: int = 100
    
    # 의미: 하나의 선으로 간주할 최대 끊김 거리
    # 근거: 점선이나 약간 끊긴 선 연결
    # 스케일링: 필요
    hough_max_line_gap: int = 10

    def scale(self, manager: ScaleManager) -> ScaledMatchingParameters:
        """현재 해상도에 맞춰 파라미터 스케일링"""
        return ScaledMatchingParameters(
            # A. Position Values
            segment_y_min=manager.scale_y(self.segment_y_min),
            segment_y_max=manager.scale_y(self.segment_y_max),
            segment_row_top_max=manager.scale_y(self.segment_row_top_max),
            segment_row_mid_min=manager.scale_y(self.segment_row_mid_min),
            segment_row_mid_max=manager.scale_y(self.segment_row_mid_max),
            segment_row_bot_min=manager.scale_y(self.segment_row_bot_min),
            body_fat_percent_y_min=manager.scale_y(self.body_fat_percent_y_min),

            # B. Distance/Tolerance Values
            keyword_search_y_margin=manager.scale_y(self.keyword_search_y_margin),
            roi_y_margin=manager.scale_y(self.roi_y_margin),
            right_dir_x_min=manager.scale_x(self.right_dir_x_min),
            right_dir_y_max=manager.scale_y(self.right_dir_y_max),
            right_dir_x_tolerance_default=manager.scale_x(self.right_dir_x_tolerance_default),
            down_dir_y_max=manager.scale_y(self.down_dir_y_max),
            down_dir_x_tolerance=manager.scale_x(self.down_dir_x_tolerance),
            scale_mark_height_max=manager.scale_y(self.scale_mark_height_max),
            large_node_height_min=manager.scale_y(self.large_node_height_min),
            distance_y_weight=manager.scale_y(self.distance_y_weight),

            # C. Ratio/Weight Values
            similarity_threshold=self.similarity_threshold,
            large_node_bonus=self.large_node_bonus,
            scale_mark_penalty=self.scale_mark_penalty,
            
            # Hough Transform (Lower bound applied)
            # 최소값 보장: 길이 40px, 간격 5px
            hough_min_line_length=max(40, manager.scale_x(self.hough_min_line_length)),
            hough_max_line_gap=max(5, manager.scale_x(self.hough_max_line_gap))
        )


@dataclass
class MatchConfig:
    """매칭 설정 데이터 클래스"""
    regex: str
    y_range: Tuple[int, int]
    direction: str
    x_tolerance: int = 800
    y_tolerance: int = 50
    allow_zero: bool = False


class ConfigManager:
    """설정 관리 클래스"""
    
    @staticmethod
    def get_default_targets() -> Dict[str, MatchConfig]:
        """기본 타겟 설정 반환 (Based on 2400px)"""
        return {
            "신장": MatchConfig(r"(\d{3})", (130, 220), "down"),
            "연령": MatchConfig(r"(\d{2})", (130, 220), "down"),
            "성별": MatchConfig(r"(남성|여성|남|여)$", (130, 220), "down"),
            "체수분": MatchConfig(r"(\d+\.\d+)", (300, 380), "right"),
            "단백질": MatchConfig(r"(\d+\.\d+)", (370, 440), "right"),
            "무기질": MatchConfig(r"(\d+\.\d+)", (430, 490), "right"),
            "체지방": MatchConfig(r"(\d+\.\d+)", (480, 550), "right"),
            "체중": MatchConfig(r"(\d+\.\d+)", (740, 830), "right"),
            "골격근량": MatchConfig(r"(\d+\.\d+)", (830, 910), "right"),
            "체지방량": MatchConfig(r"(\d+\.\d+)", (910, 980), "right"),
            "적정체중": MatchConfig(r"(\d+\.\d+)", (550, 650), "right"),
            "체중조절": MatchConfig(r"([-+]?\d+\.\d+)", (550, 750), "right", allow_zero=True, x_tolerance=1000),
            "지방조절": MatchConfig(r"([-+]?\d+\.\d+)", (600, 800), "right", allow_zero=True, x_tolerance=1000),
            "근육조절": MatchConfig(r"([-+]?\d+\.\d+)", (650, 850), "right", allow_zero=True, x_tolerance=1000),
            "복부지방률": MatchConfig(r"(\d\.\d{2})", (850, 1050), "down"),
            "내장지방레벨": MatchConfig(r"(\d+)", (950, 1150), "down"),
            "BMI": MatchConfig(r"(\d+\.\d+)", (1120, 1180), "right"),
            "체지방률": MatchConfig(r"(\d+\.\d+)", (1200, 1260), "right"),
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
                return warped, True, skew_score
            else:
                return img, False, skew_score
                
        except:
            return img, False, 0.0


class InBodyMatcher:
    """인바디 결과지 매칭 클래스"""
    
    def __init__(self, config_path: Optional[str] = None, 
                 auto_perspective: bool = True,
                 skew_threshold: float = 15.0,
                 target_height: int = 960):   # 해상도 변경하기  #fixme
        """
        Args:
            config_path: 설정 파일 경로 (JSON)
            auto_perspective: 자동 원근 변환 활성화 (기본: True)
            skew_threshold: 기울기 임계값 (0-100, 기본: 15.0)
            target_height: OCR 수행 시 정규화할 높이 (기본: 2400)
        """
        self.target_height = target_height
        
        # 해상도에 따른 PaddleOCR 파라미터 미세 조정 (비례적용)
        # 2400px 기준 2560 사용. 960px이면 약 1000이 적당함.
        det_limit = max(960, int(2560 * (target_height / 2400)))
        
        try:
            import logging
            logging.getLogger('ppocr').setLevel(logging.ERROR)
            
            self.ocr = PaddleOCR(
                lang='korean',
                ocr_version='PP-OCRv5',
                text_det_limit_side_len=det_limit,
                text_det_unclip_ratio=2.0,
                use_textline_orientation=True
            )
        except Exception as e:
            raise Exception(f"PaddleOCR 초기화 실패: {e}")
        
        self.correction_map = ConfigManager.get_correction_map()
        
        # Base Configuration (2400px)
        self.base_targets = ConfigManager.get_default_targets() 
        self.base_params = MatchingParameters()
        
        # Scaled (Initialized in extract_and_match)
        self.scale_manager: Optional[ScaleManager] = None
        self.params: Optional[ScaledMatchingParameters] = None
        self.targets: Optional[Dict[str, MatchConfig]] = None
        
        self.auto_perspective = auto_perspective
        self.skew_threshold = skew_threshold
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

    def _initialize_scaling(self, img_height: int):
        """현재 이미지 높이에 맞춰 스케일링 초기화 (Method B)"""
        self.scale_manager = ScaleManager(target_height=img_height)
        
        # 1. MatchingParameters 스케일링
        self.params = self.base_params.scale(self.scale_manager)
        
        # 2. MatchConfig 타겟 스케일링
        self.targets = {}
        for key, cfg in self.base_targets.items():
            self.targets[key] = MatchConfig(
                regex=cfg.regex,
                y_range=self.scale_manager.scale_range(cfg.y_range),
                direction=cfg.direction,
                x_tolerance=self.scale_manager.scale_x(cfg.x_tolerance),
                y_tolerance=self.scale_manager.scale_y(cfg.y_tolerance),
                allow_zero=cfg.allow_zero
            )
            
        print(f"⚖️ Scaling Initialized: ratio={self.scale_manager.scale_ratio:.3f} (h={img_height})")
    
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
            
            # Use scaled Hough parameters if available, else default
            min_len = self.params.hough_min_line_length if self.params else 100
            max_gap = self.params.hough_max_line_gap if self.params else 10
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=min_len, maxLineGap=max_gap)
            
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
                            'conf': float(conf)
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
        # Use scaled margin
        y_buffer = self.params.keyword_search_y_margin if self.params else 50
        
        candidates = []
        for node in nodes:
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
                
                # Similarity threshold (No Scale)
                threshold = self.params.similarity_threshold if self.params else 0.5
                if max_ratio > threshold:
                    candidates.append(node)
        
        if candidates:
            best = max(candidates, key=lambda x: x['conf'])
            return best
        
        return None
    
    def _match_value(self, key: str, key_node: Dict, config: MatchConfig, 
                     nodes: List[Dict]) -> Optional[str]:
        """값 노드 매칭"""
        # Ensure params are loaded
        if not self.params:
            raise RuntimeError("MatchingParameters not initialized. Call extract_and_match first.")

        p = self.params
        yr_min, yr_max = config.y_range
        candidates = []
        
        # 디버그 모드
        debug = key in ["체중조절", "지방조절", "근육조절"]
        
        # Check buffer for debug printing (Scaled)
        y_chk_buffer = p.roi_y_margin * 2
        
        for node in nodes:
            if node == key_node:
                continue
            
            # 텍스트 정규화
            clean_text = re.sub(r'\(.*?\)', '', node['text'])
            clean_text = clean_text.replace('I', '1').replace('l', '1').replace(',', '.')
            
            # 디버그: Y 범위 내의 모든 노드 출력
            if debug and (yr_min - y_chk_buffer <= node['center'][1] <= yr_max + y_chk_buffer):
                print(f"  노드: '{node['text']}' (정규화: '{clean_text}') at y={node['center'][1]:.0f}")
            
            # 정규식 매칭
            match = re.search(config.regex, clean_text)
            if not match:
                continue
            
            # 값 추출
            val = match.group(1)
            
            # 위치 계산
            dx = node['center'][0] - key_node['bbox'][2] if config.direction == "right" else abs(node['center'][0] - key_node['center'][0])
            dy = abs(node['center'][1] - key_node['center'][1])
            
            # ROI 체크 (체지방률 특수 처리)
            if key == "체지방률" and node['center'][1] < p.body_fat_percent_y_min:
                continue
            
            in_roi = (yr_min - p.roi_y_margin <= node['center'][1] <= yr_max + p.roi_y_margin)
            
            # Direction checks using scaled parameters
            # config.x_tolerance is already scaled in _initialize_scaling
            is_right_dir = (
                config.direction == "right" and 
                p.right_dir_x_min < dx < config.x_tolerance and 
                dy < p.right_dir_y_max
            )
            is_down_dir = (
                config.direction == "down" and 
                0 < (node['center'][1] - key_node['bbox'][3]) < p.down_dir_y_max and 
                abs(node['center'][0] - key_node['center'][0]) < p.down_dir_x_tolerance
            )
            
            if not in_roi or not (is_right_dir or is_down_dir):
                continue
            
            # 0값 필터링
            if not config.allow_zero:
                if val in ["0.0", "0", "+0.0"]:
                    continue
            
            # 눈금선 값 필터링
            is_scale_mark = node.get('h', 0) < p.scale_mark_height_max
            
            # 거리 점수 계산 (Scaled weight)
            dist_score = (dy * p.distance_y_weight) + abs(dx)
            
            # Large node bonus (No Scale)
            if node.get('h', 0) > p.large_node_height_min:
                dist_score -= p.large_node_bonus
            
            # Scale mark penalty (No Scale)
            if is_scale_mark:
                dist_score += p.scale_mark_penalty
            
            candidates.append((dist_score, val, node, dx, dy))
        
        if candidates:
            candidates.sort(key=lambda x: x[0])
            best_match = candidates[0]
            if debug:
                print(f"  [{key}] Selected: {best_match[1]} (score={best_match[0]:.0f})")
            return best_match[1]
        
        return None
    
    def _extract_segment_evaluations(self, nodes: List[Dict]) -> Dict[str, str]:
        """부위별 평가 추출"""
        if not self.params:
             return {}

        p = self.params
        evals = ["표준이하", "표준이상", "표준"]
        
        seg_nodes = sorted(
            [n for n in nodes if any(ev in n['text'] for ev in evals) and (p.segment_y_min <= n['center'][1] <= p.segment_y_max)],
            key=lambda x: x['center'][1]
        )
        
        row_top = sorted([n for n in seg_nodes if n['center'][1] < p.segment_row_top_max], key=lambda x: x['center'][0])
        row_mid = sorted([n for n in seg_nodes if p.segment_row_mid_min <= n['center'][1] <= p.segment_row_mid_max], key=lambda x: x['center'][0])
        row_bot = sorted([n for n in seg_nodes if n['center'][1] > p.segment_row_bot_min], key=lambda x: x['center'][0])
        
        results = {}
        
        try:
            if len(row_top) >= 4:
                results["왼쪽팔 근육"] = next((ev for ev in evals if ev in row_top[0]['text']), "미검출")
                results["오른쪽팔 근육"] = next((ev for ev in evals if ev in row_top[1]['text']), "미검출")
                results["왼쪽팔 체지방"] = next((ev for ev in evals if ev in row_top[2]['text']), "미검출")
                results["오른쪽팔 체지방"] = next((ev for ev in evals if ev in row_top[3]['text']), "미검출")
            
            if len(row_mid) >= 2:
                results["복부 근육"] = next((ev for ev in evals if ev in row_mid[0]['text']), "미검출")
                results["복부 체지방"] = next((ev for ev in evals if ev in row_mid[1]['text']), "미검출")
            
            if len(row_bot) >= 4:
                results["왼쪽하체 근육"] = next((ev for ev in evals if ev in row_bot[0]['text']), "미검출")
                results["오른쪽하체 근육"] = next((ev for ev in evals if ev in row_bot[1]['text']), "미검출")
                results["왼쪽하체 체지방"] = next((ev for ev in evals if ev in row_bot[2]['text']), "미검출")
                results["오른쪽하체 체지방"] = next((ev for ev in evals if ev in row_bot[3]['text']), "미검출")
        except:
            pass
        
        return results
    
    def extract_and_match(self, image_path: str) -> Dict[str, Optional[str]]:
        """이미지에서 인바디 데이터 추출 및 매칭"""
        import time
        start_time = time.time()
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        try:
            # 1. 이미지 로드 및 원근 변환
            step_start = time.time()
            src_img = cv2.imread(image_path)
            if src_img is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
            
            print(f"📸 원본 이미지 크기: {src_img.shape[:2]}")
            
            if self.auto_perspective:
                src_img, applied, skew_score = DocumentRectifier.rectify_auto(
                    src_img, threshold=self.skew_threshold
                )
                if applied:
                    print(f"🔄 원근 변환 적용 (기울기 점수: {skew_score:.1f})")
                else:
                    if skew_score > 0:
                        print(f"✓ 정면 문서 (기울기 점수: {skew_score:.1f}, 임계값: {self.skew_threshold})")
            print(f"⏱️ [1/4] 이미지 로드 및 보정: {time.time() - step_start:.4f}초")
            
            # 2. 해상도 정규화 및 스케일링 초기화
            step_start = time.time()
            target_h = self.target_height
            ratio = target_h / src_img.shape[0]
            img = cv2.resize(
                src_img,
                (int(src_img.shape[1] * ratio), target_h),
                interpolation=cv2.INTER_LANCZOS4
            )
            
            print(f"📏 정규화된 크기: {img.shape[:2]}")
            
            # 스케일링 초기화 (Method B)
            self._initialize_scaling(img.shape[0])
            print(f"⏱️ [2/4] 리사이징 및 스케일링 초기화: {time.time() - step_start:.4f}초")
            
            # 3. 전처리 및 OCR 수행
            step_start = time.time()
            with temporary_file() as temp_path:
                processed_img = self._preprocess_image(img)
                cv2.imwrite(temp_path, processed_img)
                all_nodes = self._extract_nodes(temp_path)
            
            print(f"📝 추출된 텍스트 노드: {len(all_nodes)}개")
            print(f"⏱️ [3/4] 전처리 및 OCR 추론: {time.time() - step_start:.4f}초")
            
            if not all_nodes:
                print("⚠️ 텍스트를 추출할 수 없습니다")
                return {}
            
            # 4. 매칭 수행
            step_start = time.time()
            matched_data = {}
            
            for key, config in self.targets.items():
                key_node = self._find_key_node(key, all_nodes, config.y_range)
                
                if not key_node:
                    matched_data[key] = None
                    continue
                
                value = self._match_value(key, key_node, config, all_nodes)
                matched_data[key] = value
            
            # 부위별 평가 추출
            segment_results = self._extract_segment_evaluations(all_nodes)
            matched_data.update(segment_results)
            
            # 매칭 통계
            detected = sum(1 for v in matched_data.values() if v is not None)
            total = len(matched_data)
            print(f"✅ 매칭 완료: {detected}/{total} 항목 ({detected/total*100:.1f}%)")
            print(f"⏱️ [4/4] 데이터 매칭: {time.time() - step_start:.4f}초")
            
            print(f"✨ 전체 소요 시간: {time.time() - start_time:.4f}초")
            
            return matched_data
        
        except Exception as e:
            print(f"❌ 오류: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"처리 중 오류 발생: {e}")
    
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
            structured = matcher.get_structured_results(result)
            
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