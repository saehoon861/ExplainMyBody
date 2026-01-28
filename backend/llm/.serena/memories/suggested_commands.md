# Suggested Commands

## Running the Pipeline

### Ollama (Local LLM)
```bash
# Run with specific profile ID (0-9)
python3 run_pipeline.py --profile-id 0

# Run all profiles
python3 run_pipeline.py --all
```

### Claude API
```bash
# Run with specific profile ID
python3 run_pipeline_claude.py --profile-id 6

# Run all profiles
python3 run_pipeline_claude.py --all
```

### GPT API
```bash
python3 run_pipeline_gpt.py --profile-id 0
```

## Package Management (uv)
```bash
# Install dependencies
uv sync

# Add a package
uv add package_name

# Run with uv
uv run python3 run_pipeline.py --profile-id 0
```

## Ollama (Local LLM Server)
```bash
# Start Ollama server (must be running before pipeline)
ollama serve

# List available models
ollama list

# Pull a model
ollama pull qwen3:8b
```

## Environment Variables
Create `.env` file with:
```
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## WSL Commands (Windows)
Since this project runs in WSL Ubuntu-22.04:
```powershell
# From Windows, run WSL command
wsl.exe -d Ubuntu-22.04 bash -c "cd /home/user/projects/ExplainMyBody/experiments/llm && python3 run_pipeline.py --profile-id 0"
```
