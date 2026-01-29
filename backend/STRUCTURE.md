# Backend Structure - Feature-Based Organization

## 📁 Directory Structure

```
backend/
├── routers/
│   ├── common/          # 공통 기능 (인증, 사용자)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── users.py
│   ├── ocr/             # OCR 팀 전담
│   │   ├── __init__.py
│   │   └── health_records.py
│   └── llm/             # LLM 팀 전담
│       ├── __init__.py
│       ├── analysis.py
│       └── goals.py
│
├── services/
│   ├── common/          # 공통 서비스
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── health_service.py
│   ├── ocr/             # OCR 팀 전담
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   ├── body_type_service.py
│   │   └── inbody_matcher.py
│   └── llm/             # LLM 팀 전담
│       ├── __init__.py
│       └── llm_service.py
│
└── repositories/
    ├── common/          # 공통 레포지토리
    │   ├── __init__.py
    │   ├── user_repository.py
    │   └── health_record_repository.py
    └── llm/             # LLM 팀 전담
        ├── __init__.py
        ├── analysis_report_repository.py
        └── user_goal_repository.py
```

## 🎯 Design Principles

### Feature-Based Organization
- **OCR Team**: Works in `*/ocr/` directories
- **LLM Team**: Works in `*/llm/` directories  
- **Common**: Shared code (minimal changes, requires coordination)

### Benefits
1. **Reduced Merge Conflicts**: Teams work in separate directories
2. **Clear Ownership**: Easy to identify who owns what code
3. **Matches Schema Organization**: Consistent with `schemas/` structure
4. **Easier Navigation**: Find code by feature domain

## 📦 Import Examples

### Routers
```python
# In main.py
from routers.common import auth_router, users_router
from routers.ocr import health_records_router
from routers.llm import analysis_router, goals_router
```

### Services
```python
# OCR team
from services.ocr.ocr_service import OCRService
from services.ocr.body_type_service import BodyTypeService

# LLM team
from services.llm.llm_service import LLMService

# Common
from services.common.health_service import HealthService
from services.common.auth_service import AuthService
```

### Repositories
```python
# Common
from repositories.common.user_repository import UserRepository
from repositories.common.health_record_repository import HealthRecordRepository

# LLM team
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from repositories.llm.user_goal_repository import UserGoalRepository
```

## 🤝 Team Collaboration Guide

### OCR Team
**Your directories:**
- `routers/ocr/`
- `services/ocr/`

**Your files:**
- `health_records.py` - OCR upload, validation, body type analysis
- `ocr_service.py` - OCR extraction logic
- `body_type_service.py` - Body type classification
- `inbody_matcher.py` - OCR engine (팀원 코드)

### LLM Team
**Your directories:**
- `routers/llm/`
- `services/llm/`
- `repositories/llm/`

**Your files:**
- `analysis.py` - Health analysis endpoints
- `goals.py` - Goal management + weekly plans
- `llm_service.py` - LLM API calls
- `analysis_report_repository.py`
- `user_goal_repository.py`

### Common Files (Coordinate Changes)
- `routers/common/` - Auth, users
- `services/common/` - Auth service, health CRUD
- `repositories/common/` - User, health record repos

## 🔄 Migration Complete

All files have been reorganized into feature-based directories. The server automatically reloads with the new structure.

**Verification:**
- ✅ All files moved using `git mv` (history preserved)
- ✅ All import paths updated
- ✅ `__init__.py` files created for module exports
- ✅ `main.py` updated with new router imports
- ✅ Server running successfully
