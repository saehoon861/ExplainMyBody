# Task Completion Checklist

## Before Completing a Task

### 1. Code Validation
- [ ] Ensure Pydantic models are updated if data structures change
- [ ] Test with at least one profile: `python3 run_pipeline.py --profile-id 0`
- [ ] Check that JSON output is valid and saved to `outputs/`

### 2. LLM Output Handling
When modifying prompt or models:
- [ ] LLM output fields should be flexible (`Union[int, str]`, `Optional`)
- [ ] `ollama_client.py` has `_fix_json()` for common LLM JSON quirks
- [ ] Test with multiple profiles (body types vary significantly)

### 3. File Integrity
- [ ] Do NOT modify original `rulebase.py` - use `rulebase_wrapper.py` instead
- [ ] Keep Korean enum values consistent with existing data

## Testing Commands
```bash
# Quick test with one profile
python3 run_pipeline.py --profile-id 0

# Full test with all 10 profiles
python3 run_pipeline.py --all

# Claude API version
python3 run_pipeline_claude.py --profile-id 6
```

## Common Issues
1. **JSON parse error**: LLM returns invalid JSON (e.g., `8-12` without quotes)
   - Fix in `ollama_client.py` `_fix_json()` method
   
2. **Pydantic validation error**: Missing required field
   - Make field `Optional` with default value in `models.py`

3. **Prompt too long**: qwen3:8b has token limits
   - Simplify prompt in `prompt_generator*.py`
