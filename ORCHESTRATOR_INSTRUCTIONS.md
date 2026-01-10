# Multi-Agent System Orchestration Instructions

**Topic**: Применение трансформеров в метеорологическом прогнозировании  
**Mode**: Full Verification (with experiment reproduction)  
**Target**: Scientific article in Russian with verified results

---

## System Overview

This multi-agent system writes scientific articles with **experimentally verified results**. Unlike traditional literature reviews that rely on paper claims, this system:

1. ✅ Analyzes papers
2. ✅ **Reproduces key experiments** (NEW!)
3. ✅ **Verifies claimed results** (NEW!)
4. ✅ Writes article with TRUE numbers
5. ✅ Provides reproducible code

---

## Quick Start

### Option 1: Automated Execution (Recommended)

```bash
# Full verification mode (2-6 hours)
python orchestrator.py \
  --mode=full-verified \
  --topic="Применение трансформеров в метеорологическом прогнозировании" \
  --papers-dir=papers/ \
  --config=input/research_config.md

# Fast mode without reproduction (65-90 minutes)
python orchestrator.py \
  --mode=fast \
  --topic="Применение трансформеров в метеорологическом прогнозировании"

# Partial verification (top 3 papers only, 1.5-3 hours)
python orchestrator.py \
  --mode=partial-verified \
  --reproduce-top=3
```

### Option 2: Manual Step-by-Step (Full Control)

Follow the detailed instructions below for manual orchestration.

---

## Manual Orchestration Guide

### Phase 0: Preparation (5 minutes)

1. **Create project structure**:
```bash
mkdir -p project/{input,papers,analysis,experiments,sections,review,references}
cd project
```

2. **Create research configuration**:
```bash
cat > input/research_config.md << 'EOF'
# Research Configuration

## Topic
Применение трансформеров в метеорологическом прогнозировании

## Keywords
- Transformers
- Weather forecasting
- Attention mechanisms
- Numerical weather prediction
- Deep learning
- ERA5
- WeatherBench

## Scope
- Time range: 2020-2026 (focus on recent advances)
- Geographic: Global weather prediction
- Forecast horizon: 1-10 days (medium-range)

## Target Venue
- IEEE Transactions on Geoscience and Remote Sensing
- OR Nature Communications
- OR Weather and Forecasting (AMS)

## Requirements
- Length: 6000-8000 words
- Language: Russian (academic style)
- Format: IMRAD structure
- Citations: IEEE numerical style
EOF
```

3. **Add papers** (10-50 PDFs):
```bash
# Place PDFs in papers/ directory
# Recommended papers for this topic:
# - GraphCast (Lam et al., 2023)
# - Pangu-Weather (Bi et al., 2023)
# - FourCastNet (Pathak et al., 2022)
# - ClimaX (Nguyen et al., 2023)
# - GenCast (Price et al., 2024)
# + 10-45 more related papers
```

---

### Phase 1: Literature Analysis (8-10 minutes)

**Agent**: @analyzer

```bash
# Invoke analyzer agent
@analyzer

# Provide instruction:
"""
Проанализируй все статьи в papers/ по теме "Применение трансформеров 
в метеорологическом прогнозировании".

Для каждой статьи:
1. Оцени релевантность (1-10)
2. Извлеки методологию (модели, датасеты, метрики)
3. Извлеки ключевые результаты
4. Определи возможность воспроизведения (reproducible: true/false)
5. Найди ссылки на код (GitHub, если доступен)

Сохрани результаты в analysis/papers_analyzed.json
"""
```

**Expected output**:
- `analysis/papers_analyzed.json` (~10-50 entries)
- Papers scored by relevance
- Methodology extracted
- **Reproducibility flags set** (NEW!)

**Verification**:
```bash
# Check output exists
ls -lh analysis/papers_analyzed.json

# Count papers
jq 'length' analysis/papers_analyzed.json

# Check top papers
jq '[.[] | select(.relevance_score >= 8) | {title, score: .relevance_score, reproducible}]' analysis/papers_analyzed.json
```

---

### Phase 1.5: Experiment Reproduction (1-4 hours) ◄─ NEW!

**Agent**: @experiment-reproducer

**IMPORTANT**: This phase can be skipped for speed, but reduces scientific rigor.

```bash
# Invoke experiment reproducer
@experiment-reproducer

# Provide instruction:
"""
На основе analysis/papers_analyzed.json:

1. Выбери 5-8 статей с наиболее значимыми результатами, где:
   - reproducible: true
   - code_available или публичные датасеты
   - relevance_score >= 8

2. Для каждой статьи:
   - Скачай/подготовь данные (ERA5, WeatherBench, синтетические)
   - Реализуй модель на Python (PyTorch/TensorFlow)
   - Воспроизведи обучение и тестирование
   - Сравни полученные метрики с заявленными в статье
   - Классифицируй:
     * VERIFIED (расхождение <10%)
     * PARTIAL (расхождение 10-20%)
     * DISCREPANCY (расхождение >20%)

3. Сохрани результаты:
   - experiments/reproduced_results_summary.json
   - experiments/{paper_id}/model_implementation.py
   - experiments/{paper_id}/reproduction_results.json

Приоритет: GraphCast, Pangu-Weather, FourCastNet (ключевые работы).
"""
```

**Configuration options**:

```python
# For quick verification (subset of data)
reproduction_config = {
    "mode": "fast",
    "data_subset": "2020-2023",  # Instead of full 1979-2023
    "spatial_resolution": "1.0deg",  # Instead of 0.25deg
    "epochs": 20,  # Instead of 100
    "estimate_full_scale": True
}

# For thorough verification (slow but accurate)
reproduction_config = {
    "mode": "thorough",
    "data_subset": None,  # Full dataset
    "spatial_resolution": "0.25deg",
    "epochs": 100,
    "statistical_tests": True
}
```

**Expected output**:
- `experiments/reproduction_candidates.json` (prioritized list)
- `experiments/reproduced_results_summary.json` (**KEY FILE**)
- `experiments/{paper_id}/` (code + results for each paper)

**Verification**:
```bash
# Check summary
cat experiments/reproduced_results_summary.json | jq '.reproduction_metadata'

# List verified papers
jq '.verified_results[] | {paper: .paper_title, status: .key_metrics[].confidence}' \
   experiments/reproduced_results_summary.json

# Check experiment code
ls experiments/*/model_implementation.py
```

**Expected time**:
- With fast config: 1-2 hours
- With thorough config: 3-6 hours
- Can run overnight if needed

---

### Phase 2: Section Writing (30-40 minutes)

#### Phase 2a: Parallel Writing (10-12 minutes)

**Agents**: @writer-intro, @writer-methods (run in parallel)

**Terminal 1** (or parallel execution):
```bash
@writer-intro

"""
Напиши секцию Introduction на русском языке.

Используй:
- analysis/papers_analyzed.json (топ-15 статей)
- Тема: применение трансформеров в метеорологическом прогнозировании

Структура:
1. Контекст и актуальность (100 слов)
2. Проблематика (140 слов)
3. Обзор литературы (240 слов, группировка по подходам):
   - Классические NWP (IFS, GFS)
   - CNN-based методы (2018-2020)
   - Transformer-based методы (2022-2026)
4. Цель и вклад работы (120 слов)

Требования:
- 500-700 слов
- 15-20 цитат
- Русский академический язык
- Сохрани в sections/introduction.md
"""
```

**Terminal 2** (or parallel):
```bash
@writer-methods

"""
Напиши секцию Methods на русском языке.

Используй:
- analysis/papers_analyzed.json (методология из топ статей)
- experiments/reproduced_results_summary.json (данные о датасетах, архитектурах)

Структура (400-600 слов):
1. Обзор подхода (80-120 слов)
2. Данные и датасеты (150-250 слов):
   - ERA5 (описание, переменные, разрешение, период)
   - Предобработка
   - Train/val/test split
3. Архитектура моделей (200-350 слов):
   - Transformer (описание с формулами LaTeX)
   - GraphCast/Pangu-Weather (если релевантны)
   - Гиперпараметры (таблица)
4. Обучение (100-150 слов)
5. Метрики оценки (100-150 слов):
   - RMSE, MAE, ACC (формулы LaTeX)
6. Бейзлайны (60-100 слов)

Используй ВОСПРОИЗВЕДЕННЫЕ параметры из experiments/, не только заявленные!

Сохрани в sections/methods.md
"""
```

**Wait for both to complete**, then verify:
```bash
wc -w sections/introduction.md sections/methods.md
grep -o '\[[^]]*[0-9]\{4\}\]' sections/introduction.md | wc -l  # Citations
```

#### Phase 2b: Sequential - Results (8-12 minutes)

**Agent**: @writer-results (depends on methods.md)

```bash
@writer-results

"""
Напиши секцию Results на русском языке.

КРИТИЧЕСКИ ВАЖНО: Используй ВОСПРОИЗВЕДЕННЫЕ метрики из 
experiments/reproduced_results_summary.json, НЕ заявленные в статьях!

Читай:
- sections/methods.md (определения метрик)
- experiments/reproduced_results_summary.json (ГЛАВНЫЙ ИСТОЧНИК ДАННЫХ!)
- analysis/papers_analyzed.json (контекст)

Структура (400-600 слов):
1. Основные результаты (таблица):
   - Модели: GraphCast, Pangu-Weather, FourCastNet, etc.
   - Метрики: RMSE, MAE, ACC для разных горизонтов (3-day, 7-day)
   - Используй reproduced values + confidence intervals!
   - Отметь verified/partial/claimed статус

2. Сравнение с бейзлайнами:
   - IFS HRES (baseline)
   - Persistence
   - Улучшение в %

3. Абляционные исследования (если доступны)

4. Заметки о воспроизведении:
   - "Мы успешно воспроизвели X из Y методов"
   - "Результаты GraphCast: заявлено 180м, воспроизведено 182.3±4.2м (подтверждено)"

Формат таблиц:
| Модель | 3-day RMSE (Z500) | 7-day RMSE (Z500) | Статус |
|--------|-------------------|-------------------|--------|
| **GraphCast** | **182.3±4.2** м | **315.8±8.1** м | ✓ Verified |

Сохрани в sections/results.md
"""
```

#### Phase 2c: Sequential - Discussion (10-15 minutes)

**Agent**: @writer-discussion (depends on intro/methods/results)

```bash
@writer-discussion

"""
Напиши секцию Discussion на русском языке.

Читай:
- sections/introduction.md (research questions)
- sections/methods.md  
- sections/results.md (verified results!)
- experiments/reproduced_results_summary.json (confidence, notes)

Структура (500-700 слов):
1. Интерпретация результатов (200 слов):
   - Ответы на research questions из Introduction
   - Почему трансформеры работают лучше?
   - Анализ attention mechanisms

2. Сравнение с литературой (150 слов):
   - Как наши воспроизведенные результаты соотносятся с SOTA
   - Подтвержденные vs неподтвержденные claims

3. Ограничения (150 слов):
   - Честно обсуди ограничения воспроизведения
   - Что не удалось воспроизвести и почему
   - Вычислительные ограничения

4. Практические применения (100 слов)

5. Будущие направления (100 слов):
   - Улучшение архитектур
   - Новые датасеты
   - Долгосрочные прогнозы (>10 дней)

Сохрани в sections/discussion.md
"""
```

**Verify all sections**:
```bash
for section in introduction methods results discussion; do
    echo "=== $section ==="
    wc -w sections/${section}.md
    echo ""
done

# Check total
cat sections/*.md | wc -w  # Should be ~2000-2800 words (core sections)
```

---

### Phase 3: Peer Review (15-20 minutes)

**Agent**: @reviewer

**CRITICAL**: Reviewer now checks reproducibility!

```bash
@reviewer

"""
Проведи критическую рецензию статьи.

Читай все файлы:
- sections/introduction.md
- sections/methods.md
- sections/results.md
- sections/discussion.md
- experiments/reproduced_results_summary.json (НОВОЕ!)

Оцени по критериям (взвешенные баллы):
1. Логика и связность (25%)
2. Научная корректность (30%)
3. Релевантность теме (20%)
4. Качество изложения (15%)
5. Структура (10%)

ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА (НОВОЕ):
6. Воспроизводимость результатов:
   - Использованы ли verified metrics?
   - Раскрыты ли discrepancies?
   - Указана ли доступность кода?
   - Прозрачность методологии?

Сформируй:
- Общий балл (0-100)
- critical_issues (список блокирующих проблем)
- minor_improvements (список улучшений)
- section_scores (оценки по секциям)
- reproducibility_assessment (НОВОЕ!)
- accept_status: accept / minor_revisions / major_revisions / reject

Сохрани в review/feedback.json
"""
```

**Expected**: Higher scores due to verified results (~82-92 instead of ~75-85)

**Check review**:
```bash
cat review/feedback.json | jq '{
  score: .overall_assessment.overall_score,
  status: .overall_assessment.accept_status,
  reproducibility: .reproducibility_assessment.reproducibility_score,
  critical_issues: .critical_issues | length
}'
```

**Decision point**:
- **accept / minor_revisions**: Proceed to Phase 4
- **major_revisions**: Fix critical issues, re-run affected writers
- **reject**: Reassess topic or methodology

---

### Phase 4: Final Editing (12-18 minutes)

**Agent**: @editor

```bash
@editor

"""
Финализируй статью для публикации.

Читай:
- sections/*.md (все секции)
- review/feedback.json (фидбек рецензента)
- experiments/reproduced_results_summary.json (для reproducibility statement)

Задачи:
1. Примени правки из review/feedback.json:
   - 100% critical issues
   - 90%+ minor improvements
   - Документируй все изменения в CHANGES.md

2. Форматируй список литературы (IEEE numerical):
   - [1], [2], [3]... по порядку появления
   - Сохрани в references/formatted_references.md

3. Сгенерируй Abstract (150-250 слов, IMRAD):
   - Background (20%)
   - Objective (10%)
   - Methods (30%)
   - Results (30%) - используй КОНКРЕТНЫЕ ЧИСЛА из reproduced_results!
   - Conclusions (10%)
   - БЕЗ цитат!
   - Сохрани в abstract.md

4. ДОБАВЬ Reproducibility Statement (НОВОЕ!):
   ```
   ## Code and Data Availability

   Код для воспроизведения всех экспериментов доступен по адресу 
   [GitHub URL]. Мы успешно воспроизвели X из Y ключевых методов 
   со средней относительной погрешностью <Y%. Датасеты: ERA5 
   (https://cds.climate.copernicus.eu), WeatherBench 
   (https://github.com/pangeo-data/WeatherBench).
   ```

5. Собери финальный документ:
   - FINAL_ARTICLE.md (полная статья)
   - metadata.json (метаданные)

Формат FINAL_ARTICLE.md:
```
***
title: "Применение трансформеров..."
date: "2026-01-09"
word_count: XXXX
***

# Применение трансформеров в метеорологическом прогнозировании

**Автор И.О.**
Организация

## Abstract
[150-250 слов]

## 1. Introduction
[из sections/introduction.md с правками]

## 2. Methods
[из sections/methods.md с правками]

## 3. Results  
[из sections/results.md с правками]

## 4. Discussion
[из sections/discussion.md с правками]

## 5. Conclusion
[краткое резюме, 200-300 слов]

## References
[из references/formatted_references.md]

## Code and Data Availability
[reproducibility statement]
```

Сохрани все выходные файлы.
"""
```

**Verify final outputs**:
```bash
ls -lh FINAL_ARTICLE.md abstract.md CHANGES.md metadata.json

# Check word count
wc -w FINAL_ARTICLE.md  # Target: 6000-8000 words

# Check abstract
wc -w abstract.md  # Should be 150-250

# Check reproducibility statement present
grep -A 5 "Code and Data" FINAL_ARTICLE.md
```

---

## Verification Checklist

### ✅ Quality Assurance

```bash
# 1. All required files exist
required_files=(
    "analysis/papers_analyzed.json"
    "experiments/reproduced_results_summary.json"  # NEW!
    "sections/introduction.md"
    "sections/methods.md"
    "sections/results.md"
    "sections/discussion.md"
    "review/feedback.json"
    "FINAL_ARTICLE.md"
    "abstract.md"
    "references/formatted_references.md"
    "CHANGES.md"
    "metadata.json"
)

for file in "${required_files[@]}"; do
    [ -f "$file" ] && echo "✓ $file" || echo "✗ MISSING: $file"
done

# 2. Check reproducibility integration
echo "\n=== Reproducibility Check ==="
jq '.reproduction_metadata.successful' experiments/reproduced_results_summary.json
grep -q "Code and Data Availability" FINAL_ARTICLE.md && echo "✓ Reproducibility statement" || echo "✗ Missing"
grep -q "воспроизвели\|reproduced" sections/results.md && echo "✓ Reproduction mentioned" || echo "✗ Not mentioned"

# 3. Check metrics usage
echo "\n=== Verified Metrics Usage ==="
echo "Verified results available:"
jq '.verified_results | length' experiments/reproduced_results_summary.json
echo "Used in Results section:"
grep -c "reproduced\|verified\|±" sections/results.md

# 4. Check review score
echo "\n=== Review Score ==="
jq '.overall_assessment | {score, status, reproducibility}' review/feedback.json

# 5. Word counts
echo "\n=== Word Counts ==="
echo "Introduction: $(wc -w < sections/introduction.md)"
echo "Methods: $(wc -w < sections/methods.md)"
echo "Results: $(wc -w < sections/results.md)"
echo "Discussion: $(wc -w < sections/discussion.md)"
echo "Abstract: $(wc -w < abstract.md)"
echo "Total article: $(wc -w < FINAL_ARTICLE.md)"
```

---

## Troubleshooting

### Problem: Experiment reproduction too slow

**Solution 1**: Use fast config
```bash
# In experiment-reproducer instructions, specify:
"reproduction_config": {
    "mode": "fast",
    "data_years": "2020-2023",
    "spatial_resolution": "1.0deg",
    "epochs": 20
}
```

**Solution 2**: Skip reproduction for this run
```bash
# Use fast mode
python orchestrator.py --mode=fast --skip-reproduction
```

**Solution 3**: Reproduce only top papers
```bash
python orchestrator.py --mode=partial-verified --reproduce-top=3
```

### Problem: Reproduction fails for a paper

**Expected behavior**: Reproducer should:
1. Log the failure clearly
2. Mark as "not_reproduced" in summary.json
3. Document reason (e.g., "proprietary data")
4. Continue with other papers

**Fallback**: Use paper-claimed results with caveat
```python
# In reproduced_results_summary.json:
{
  "not_reproduced": [
    {
      "paper_id": "author2024work",
      "reason": "Proprietary dataset unavailable",
      "fallback_action": "Use paper-claimed results with disclaimer"
    }
  ]
}
```

### Problem: Low reviewer score despite verification

**Check**:
1. Are verified results actually used in Results section?
2. Is reproducibility statement present?
3. Are discrepancies (if any) disclosed honestly?
4. Is code availability mentioned?

**Fix**: Re-run editor with explicit instructions to emphasize reproducibility.

### Problem: Writer-results uses paper claims instead of verified metrics

**Cause**: Writer didn't read reproduced_results_summary.json

**Fix**: Explicitly instruct writer-results:
```
КРИТИЧЕСКИ ВАЖНО: Используй ТОЛЬКО метрики из 
experiments/reproduced_results_summary.json -> verified_results[].key_metrics.
НЕ используй analysis/papers_analyzed.json -> key_findings!
```

---

## Expected Timeline

| Phase | Agent | Time (Fast) | Time (Thorough) |
|-------|-------|-------------|-----------------|
| 0. Preparation | User | 5 min | 5 min |
| 1. Analysis | analyzer | 8-10 min | 8-10 min |
| **1.5. Reproduction** | **experiment-reproducer** | **1-2 hr** | **3-6 hr** |
| 2a. Intro+Methods | writer-intro, writer-methods | 10-12 min | 10-12 min |
| 2b. Results | writer-results | 8-12 min | 8-12 min |
| 2c. Discussion | writer-discussion | 10-15 min | 10-15 min |
| 3. Review | reviewer | 15-20 min | 15-20 min |
| 4. Editing | editor | 12-18 min | 12-18 min |
| **TOTAL** | | **~2 hours** | **~4-7 hours** |

**Without reproduction** (skip Phase 1.5): 65-90 minutes

---

## Output Files Summary

### Core Article Files
- `FINAL_ARTICLE.md` - Complete article (6000-8000 words, Russian)
- `abstract.md` - Standalone abstract (150-250 words)
- `references/formatted_references.md` - IEEE format
- `CHANGES.md` - Editorial change log
- `metadata.json` - Submission metadata

### Reproducibility Files (NEW!)
- `experiments/reproduced_results_summary.json` - Verified metrics
- `experiments/{paper_id}/model_implementation.py` - Executable code
- `experiments/{paper_id}/reproduction_results.json` - Individual results
- `experiments/{paper_id}/requirements.txt` - Environment specs
- `experiments/REPRODUCTION_REPORT.md` - Human-readable summary

### Internal Files
- `analysis/papers_analyzed.json` - Literature analysis
- `sections/*.md` - Individual sections (draft + final)
- `review/feedback.json` - Peer review report

---

## Success Criteria

### Minimum Requirements
- ✅ All core article files present
- ✅ Word count: 6000-8000 (FINAL_ARTICLE.md)
- ✅ Abstract: 150-250 words
- ✅ Reviewer score: ≥75
- ✅ Review status: accept or minor_revisions
- ✅ No placeholder text ([TODO], [TBD])
- ✅ References formatted (IEEE)

### Enhanced Requirements (with reproduction)
- ✅ At least 50% of key papers reproduced
- ✅ Reproducibility statement present
- ✅ Verified metrics used in Results
- ✅ Reproduction code available
- ✅ Discrepancies documented
- ✅ Reviewer reproducibility score: ≥8.0
- ✅ Total reviewer score: ≥82 (higher due to verification)

---

## Post-Completion Steps

1. **Review FINAL_ARTICLE.md manually**
2. **Test reproduction code**:
   ```bash
   cd experiments/graphcast2023/
   python model_implementation.py
   # Should produce same results as in reproduction_results.json
   ```
3. **Package for submission**:
   ```bash
   mkdir submission/
   cp FINAL_ARTICLE.md submission/manuscript.md
   cp abstract.md submission/
   cp references/formatted_references.md submission/
   cp -r experiments/ submission/code/
   tar -czf submission.tar.gz submission/
   ```

4. **Share code publicly** (after acceptance):
   ```bash
   git init
   git add experiments/ sections/ FINAL_ARTICLE.md
   git commit -m "Reproducible research: Transformers in weather forecasting"
   git remote add origin <your-repo>
   git push
   ```

---

## Contact & Support

For issues with:
- **Orchestration**: Check this file
- **Individual agents**: See `.claude/agents/*.md`
- **Reproduction**: See `.claude/agents/experiment-reproducer.md`
- **Workflow**: See `WORKFLOW_DIAGRAM_UPDATED.md`

---

**Prepared for**: Применение трансформеров в метеорологическом прогнозировании  
**System version**: 2.0 (with experimental verification)  
**Date**: 2026-01-09
