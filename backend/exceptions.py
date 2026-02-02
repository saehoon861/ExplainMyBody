"""
커스텀 예외 클래스
Service 레이어에서 사용하는 비즈니스 로직 예외 정의
Router 레이어에서 이 예외들을 HTTPException으로 변환
"""


# ============================================
# OCR Service 예외
# ============================================

class OCRServiceError(Exception):
    """OCR 서비스 기본 예외"""
    pass


class OCREngineNotInitializedError(OCRServiceError):
    """OCR 엔진이 초기화되지 않음"""
    pass


class OCRExtractionFailedError(OCRServiceError):
    """OCR 결과 추출 실패"""
    pass


class OCRProcessingError(OCRServiceError):
    """OCR 처리 중 오류 발생"""
    pass


# ============================================
# Auth Service 예외
# ============================================

class AuthServiceError(Exception):
    """인증 서비스 기본 예외"""
    pass


class EmailAlreadyExistsError(AuthServiceError):
    """이메일 중복"""
    pass


class InvalidCredentialsError(AuthServiceError):
    """잘못된 인증 정보 (이메일 또는 비밀번호 오류)"""
    pass


class UserNotFoundError(AuthServiceError):
    """사용자를 찾을 수 없음"""
    pass


# ============================================
# Health/Analysis Service 예외
# ============================================

class HealthServiceError(Exception):
    """건강 서비스 기본 예외"""
    pass


class HealthRecordNotFoundError(HealthServiceError):
    """건강 기록을 찾을 수 없음"""
    pass


class AnalysisReportNotFoundError(HealthServiceError):
    """분석 리포트를 찾을 수 없음"""
    pass


# ============================================
# Weekly Plan Service 예외
# ============================================

class WeeklyPlanServiceError(Exception):
    """주간 계획 서비스 기본 예외"""
    pass


class WeeklyPlanNotFoundError(WeeklyPlanServiceError):
    """주간 계획을 찾을 수 없음"""
    pass


class WeeklyPlanGenerationError(WeeklyPlanServiceError):
    """주간 계획 생성 실패"""
    pass


# ============================================
# Goal/UserDetail Service 예외
# ============================================

class GoalServiceError(Exception):
    """목표 서비스 기본 예외"""
    pass


class GoalNotFoundError(GoalServiceError):
    """목표를 찾을 수 없음"""
    pass

