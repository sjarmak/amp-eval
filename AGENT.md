# Amp Model-Efficacy Evaluation Agent
Make sure you activate the relevant environment before running code!

## 📜 Purpose
Benchmark three conversational models—**Sonnet-4**, **GPT-5**, and **o3 ("oracle")**—on
tool-calling accuracy, code-fix success, and knowledge-retrieval scenarios common to coding-agent workflows.

## 🛠️ Registered Tools
| Tool name           | Description                               | When to use                          |
|---------------------|-------------------------------------------|--------------------------------------|
| `git_branch`        | Create / switch git branches              | Always before modifying code         |
| `git_commit`        | Stage & commit changes                    | After tests pass                     |
| `file_edit`         | Insert / replace code blocks              | All code modifications               |
| `run_tests`         | Execute repo's test suite                 | To verify fixes/refactors            |

*(Keep schemas minimal; see `/evals/tool_schemas/`)*

## 🧠 Model Selection Rules
1. **Oracle trigger** (highest priority): prompt starts with `"consult the oracle:"`
2. **CLI flag override**: `--try-gpt5` forces GPT-5 usage
3. **Environment variable**: `AMP_MODEL={sonnet-4,gpt-5,o3}`
4. **Rules engine**: auto-upgrade to GPT-5 when:
   - `diff_lines > 40` (large code changes)
   - `touched_files > 2` (multi-file modifications)
5. **Default fallback**: Sonnet-4

## ✅ Success Criteria
* **Tool call correctness**: first call has right name & args (≥70% accuracy)
* **Task completion**: unit tests green or output matches reference  
* **Efficiency**: ≤ 2 retries; within token budget thresholds
* **Oracle discipline**: at most one o3 invocation per task

## 🏗️ Repository Layout

```
amp-eval/
├─ config/
│  └─ agent_settings.yaml      # Model selection rules and thresholds
├─ adapters/
│  └─ amp_runner.py           # OpenAI-Evals compatible wrapper
├─ evals/
│  ├─ tool_calling_micro.yaml # 10 function-calling prompts  
│  ├─ single_file_fix.yaml    # 5 bug-fix tasks graded by pytest
│  └─ oracle_knowledge.yaml   # 3 prompts requiring oracle (o3) call
├─ tasks/repos/               # Mini git repos w/ failing tests
│  ├─ calc/                   # Calculator with syntax errors
│  ├─ string_utils/           # Text processor with logic bugs
│  └─ algorithms/             # Fibonacci with infinite loop
├─ scripts/
│  └─ aggregate_results.ipynb # Jupyter notebook for metrics analysis
└─ .vscode/
   └─ tasks.json             # VS Code task to launch GPT-5
```

## 📊 Evaluation Suites

### 1. Tool Calling Micro (`tool_calling_micro.yaml`)
- **Purpose**: Test function-calling accuracy on first attempt
- **Tasks**: 10 micro-prompts covering common tools (glob, Grep, Read, etc.)
- **Grading**: Tool name (40%) + args present (30%) + args correct (30%)
- **Pass threshold**: 70%

### 2. Single File Fix (`single_file_fix.yaml`)  
- **Purpose**: Test bug-fixing ability on isolated Python files
- **Tasks**: 5 scenarios (syntax errors, logic bugs, infinite loops, etc.)
- **Grading**: Tests pass (70%) + correct files modified (20%) + efficiency (10%)
- **Pass threshold**: 70%

### 3. Oracle Knowledge (`oracle_knowledge.yaml`)
- **Purpose**: Test oracle triggering and deep reasoning
- **Tasks**: 3 expert-level prompts requiring o3 capabilities
- **Grading**: Oracle triggered (25%) + reasoning depth (30%) + technical accuracy (25%) + insights (20%)
- **Pass threshold**: 75%

## 🎯 Model Performance Targets

| Model | Tool Calling | Bug Fixing | Oracle Knowledge | Token Efficiency |
|-------|-------------|------------|------------------|------------------|
| **Sonnet-4** | ≥70% | ≥65% | N/A | ≤8K tokens |
| **GPT-5** | ≥85% | ≥80% | N/A | ≤16K tokens |
| **o3** | ≥90% | ≥85% | ≥75% | ≤32K tokens |

## 🚀 Quick Commands

```bash
# Install dependencies
pip install openai-evals json5 pyyaml pandas matplotlib jupyter

# Default evaluation (Sonnet-4)
openai tools evaluate amp-eval/evals/tool_calling_micro.yaml --registry amp-eval/adapters

# Force GPT-5 for all tasks
AMP_MODEL=gpt-5 openai tools evaluate amp-eval/evals/single_file_fix.yaml --registry amp-eval/adapters

# Oracle-only evaluation
AMP_MODEL=o3 openai tools evaluate amp-eval/evals/oracle_knowledge.yaml --registry amp-eval/adapters

# Analyze results
jupyter notebook scripts/aggregate_results.ipynb
```

## 🔧 Configuration

Edit [`config/agent_settings.yaml`](config/agent_settings.yaml) to customize:

- **Model selection precedence**: Oracle trigger → CLI flag → env var → rules → default
- **Upgrade rules**: Thresholds for diff lines and touched files  
- **Token budgets**: Per-model efficiency targets
- **Oracle trigger phrase**: Default `"consult the oracle:"`

## 📈 Success Metrics

### Primary KPIs
- **First-attempt accuracy**: % of tasks completed correctly on first try
- **Token efficiency**: Average tokens used per successful completion
- **Latency**: Average response time per model
- **Oracle discipline**: % of oracle tasks that actually used o3

### Secondary Metrics  
- **Retry rate**: % of tasks requiring multiple attempts
- **Test pass rate**: % of bug fixes that pass all tests
- **False oracle triggers**: Cases where oracle was invoked unnecessarily

## 🎮 VS Code Integration

Use the provided VS Code task for quick GPT-5 testing:

1. `Cmd+Shift+P` → "Tasks: Run Task"
2. Select "Launch Amp with GPT-5" 
3. Opens new terminal with `AMP_MODEL=gpt-5 amp` ready

## 🧪 Adding New Evaluations

1. **Create evaluation YAML**: Follow OpenAI-Evals format in `evals/`
2. **Add test repos**: Place failing test scenarios in `tasks/repos/`
3. **Define grading criteria**: Specify scoring method and thresholds
4. **Register with adapter**: Ensure `amp_runner.py` can handle the new eval type
5. **Update documentation**: Add to this README and evaluation matrix

## 🐛 Troubleshooting

### Common Issues

**"No module named 'amp_runner'"**
- Ensure you're running from the `amp-eval/` directory
- Check that `adapters/amp_runner.py` is executable

**"Oracle not triggered"**  
- Verify prompt starts with exact phrase: `"consult the oracle:"`
- Check `AMP_MODEL` environment variable isn't overriding

**"Tests failing immediately"**
- Ensure test repositories in `tasks/repos/` have correct structure
- Verify Python path includes repo directories

**"Token budget exceeded"**
- Review token thresholds in `config/agent_settings.yaml`
- Consider upgrading to higher-capacity model

## 🛣️ Roadmap

### Phase 1: Core Framework ✅
- [x] Model selection logic
- [x] OpenAI-Evals integration  
- [x] Basic evaluation suites
- [x] Results aggregation

### Phase 2: Advanced Evaluations 🚧
- [ ] Multi-file refactoring tasks
- [ ] Performance optimization challenges
- [ ] Security vulnerability detection
- [ ] API integration scenarios

### Phase 3: Production Features 📋
- [ ] Continuous evaluation pipeline
- [ ] Model performance tracking  
- [ ] Automated regression detection
- [ ] Integration with Amp CLI analytics

## 📞 Support

For questions or issues:
1. Check this documentation first
2. Review evaluation YAML files for examples
3. Examine `amp_runner.py` for implementation details
4. Create issue with reproduction steps and logs
