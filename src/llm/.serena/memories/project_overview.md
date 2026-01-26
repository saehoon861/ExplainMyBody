# ExplainMyBody LLM Experiments

## Project Purpose
This project analyzes InBody body composition measurements and generates personalized diet and exercise recommendations using LLMs.

## Pipeline Flow
1. **Input**: InBody profile data (height, weight, BMI, body fat %, skeletal muscle mass, segment measurements)
2. **Rule-based Analysis** (`rulebase.py`): Classifies body type through 3 stages
   - Stage 1: BMI + body fat classification (저체중, 정상, 마른비만, 과체중, etc.)
   - Stage 2: Muscle level adjustment (근육형, 탄탄형, etc.)
   - Stage 3: Body part distribution analysis (상체발달형, 하체발달형, etc.)
3. **LLM Recommendation**: Generates personalized 1-week exercise plan, diet plan, and tips
4. **Output**: JSON result validated with Pydantic models

## Tech Stack
- **Language**: Python 3.11+
- **Package Manager**: uv
- **Validation**: Pydantic v2
- **LLM Clients**: 
  - Ollama (local, qwen3:8b)
  - Anthropic Claude API
- **Dependencies**: anthropic, numpy, pydantic, pydantic-settings, python-dotenv

## Key Files
| File | Purpose |
|------|---------|
| `rulebase.py` | Rule-based body type classification |
| `models.py` | Pydantic models for all data structures |
| `ollama_client.py` | Ollama API wrapper with JSON fixing |
| `prompt_generator.py` | Prompt template for Ollama |
| `prompt_generator_claude.py` | Simplified prompt for Claude |
| `run_pipeline.py` | Main pipeline (Ollama) |
| `run_pipeline_claude.py` | Pipeline using Claude API |
| `sample_profiles.json` | 10 test profiles with varied body types |
| `rulebase_wrapper.py` | Safe import wrapper for rulebase.py |

## Output
Results are saved to `outputs/` directory as JSON files.
