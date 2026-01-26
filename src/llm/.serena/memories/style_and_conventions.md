# Style and Conventions

## Language
- **Code**: English variable names, function names
- **Comments/Docstrings**: Korean (한국어)
- **Data values**: Korean enum values (e.g., `"남자"`, `"여자"`, `"정상"`, `"비만"`)

## Code Style
- **Type Hints**: Required for all function signatures
- **Docstrings**: Korean docstrings with Args/Returns sections
- **Naming**: 
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

## Pydantic Conventions
- Use `Field()` for constraints (ge, le, min_length, max_length)
- Use `Union[int, str]` for LLM output flexibility (handles "30초", "8-12" ranges)
- Use `Optional[T] = None` for optional fields
- Use `@field_validator` with `mode="before"` for input parsing

## Example Pydantic Model
```python
class Exercise(BaseModel):
    """운동 정보"""
    name: str
    sets: Union[int, str] = Field(default=3, description="세트 수 또는 시간")
    reps: Union[int, str] = Field(default=12, description="횟수(12) 또는 시간(30초)")
    rest_seconds: Union[int, str] = Field(default=60, description="휴식 시간")
    note: Optional[str] = None
    
    @field_validator("reps", mode="before")
    @classmethod
    def parse_reps(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
```

## File Organization
- Enums at top of `models.py`
- Input models, then output models
- Related classes grouped with section comments (`# === Section ===`)

## Print Statements
- Use `print()` with string concatenation (not f-strings in some files)
- Prefix status with `[1/2]`, `[Warning]`, etc.
