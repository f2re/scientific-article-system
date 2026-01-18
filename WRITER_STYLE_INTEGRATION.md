# Writer Agents Style Integration Guide

**Purpose**: This document defines mandatory style rules for all writer agents (intro, methods, results, discussion, editor) based on the author's stylistic profile (AUTOR_STYLE.md).

**Status**: MANDATORY for all article generation
**Language**: Russian academic text following GOST standards
**Updated**: 2026-01-18

---

## Core Style Requirements (Apply to ALL Writers)

### 1. Tone and Formality

**MANDATORY**:
- ✅ Строго официальный научный стиль (strictly formal scientific style)
- ✅ Нейтрально-объективный тон (neutral-objective tone)
- ✅ Авторитарно-экспертная дистанция (authoritative-expert distance)
- ❌ NO emotional coloring or evaluations
- ❌ NO exclamation marks or interjections
- ❌ NO colloquial language

**Characteristic phrases**:
- "Рассмотрим..." (Let us consider...)
- "Обозначим..." (Let us denote...)
- "Пусть..." (Let...)
- "Тогда..." (Then...)
- "Следовательно..." (Consequently...)
- "В то же время..." (At the same time...)
- "Отметим, что..." (Note that...)

### 2. Sentence Structure

**Requirements**:
- Average length: 20-35 words
- Predominant type: Сложноподчиненные предложения (complex subordinate sentences)
- Use of participial and gerund clauses
- Causal, conditional, and defining relationships

**Pattern examples**:
- "Для обеспечения наибольшей производительности необходимо спроектировать систему таким образом, чтобы обеспечить наименее затратное по времени получение необходимых данных..."
- "Тип и количество необходимых для обработки данных определяются, исходя из решаемых задач..."

**AVOID**:
- ❌ Short simple sentences in sequence (< 10 words)
- ❌ Question structures (use declarative only)
- ❌ First person singular ("я")

### 3. Lexical Profile

**Abbreviations** (MANDATORY pattern):
- Define on first use: "гидрометеорологические данные (ГМД)"
- Use consistently after introduction
- Common abbreviations: БД (database), СУБД (DBMS), ИНС (ANN), МВ (meteorological variables), ОЯП (dangerous weather phenomena)

**Mathematical formalization**:
- Use formal variable introduction: "Пусть T – множество сроков наблюдений..."
- Define all variables: "где n – количество сроков, m – количество изобарических поверхностей"
- Use ellipsis for continuation: "x₁, x₂, ..., xₙ"

**Technical terms**:
- Keep English terms in Latin: LSTM, RNN, AutoML, Transformer
- Translate on first mention: "рекуррентная нейронная сеть (RNN)"
- Use Russian mathematical notation

### 4. Voice and Grammar

**Voice distribution**:
- Passive constructions: 40-50% ("данные сохраняются в БД...")
- Impersonal constructions: 30-40% ("необходимо спроектировать...")
- Inclusive first person plural: 20-30% ("Рассмотрим модель...")
- ❌ NEVER first person singular ("я сделал...")

**Verb forms**:
- Imperative plural for joint action: "рассмотрим", "обозначим", "представим"
- Modal constructions: "необходимо", "следует", "требуется"

### 5. Formatting Standards

**Section headers**:
- ПРОПИСНЫЕ БУКВЫ (UPPERCASE) for major sections
- Example: "РАСПРЕДЕЛЕННАЯ ОБРАБОТКА МЕТЕОРОЛОГИЧЕСКОЙ ИНФОРМАЦИИ"

**Lists**:
- Numbered lists with parentheses: 1) Типизация; 2) Нормализация; 3) Упорядочивание
- Bulleted lists with dashes: "- точности; - логичности; - объективности"

**Formulas**:
- Separate lines with numbered labels in parentheses
- Example:
  ```
  L = L_MSE + λL_physics                    (1)
  ```
- Define all variables: "где L – общая функция потерь, λ – весовой коэффициент"

**Visual references**:
- "На рисунке 2 представлен..." (Figure 2 shows...)
- "Структура представлена на рисунке 3" (Structure is shown in Figure 3)

### 6. Transitions and Connectors

**Essential connectors** (use frequently):
- Causal: "Следовательно", "Таким образом", "Поэтому"
- Contrastive: "В то же время", "Однако", "Тем не менее"
- Sequential: "Затем", "Далее", "После этого"
- Additive: "Кроме того", "Помимо этого"

**Structural phrases**:
- Introduction: "Цель статьи – обзор...", "Рассмотрим модель..."
- Definition: "примет вид", "выглядит следующим образом", "будет иметь вид"
- Attribution: "где ... – это...", "здесь ... – производительность системы"

### 7. Numerical Data and Precision

**MANDATORY for all numbers**:
- Always include units and context
- Use percentage improvements
- Provide concrete values
- Example: "точность составила 93%", "объем увеличится на ~15 Терабайт"

**Avoid**:
- ❌ "хорошие результаты" → ✅ "RMSE = 2.1°C, улучшение на 23%"
- ❌ "значительное улучшение" → ✅ "снижение ошибки на 15%"

---

## Agent-Specific Integration Rules

### Writer-Intro Agent

**Add to existing structure**:

**Section 1: Context & Relevance**
- Use formal introduction: "Цель данной работы – рассмотрение..."
- Mathematical formalization if relevant: "Пусть S – множество задач прогнозирования..."
- Define key abbreviations early

**Section 3: Literature Review**
- Group works methodologically
- Use formal transitions: "В то же время, работа [Автор, Год] рассматривает..."
- Introduce formal notation for approaches: "Пусть M₁, M₂, ..., Mₙ – множество рассмотренных моделей..."

**Section 4: Goal & Contributions**
- Formal statement: "Цель работы – разработка метода..."
- Numbered contributions with full stops: "Вклад работы состоит в следующем: 1) разработка архитектуры...; 2) создание датасета...; 3) экспериментальная валидация..."

**Style additions**:
```markdown
## Style Requirements (Intro-specific)

- Start with broad formal context using passive constructions
- Use mathematical notation where applicable
- Define all abbreviations in first paragraph
- Complex sentences (25-35 words average)
- Formal transitions between literature groups
- Numbered contribution list with semicolons
```

### Writer-Methods Agent

**CRITICAL**: This agent already has strong Russian requirements. Enhance with:

**Mathematical formalization** (expand existing):
- Always introduce variables formally: "Пусть D = {(xᵢ, yᵢ)}ᵢ₌₁ᴺ – обучающая выборка..."
- Define dimensions explicitly: "где xᵢ ∈ ℝᵈ – входной вектор, d – размерность"
- Use Russian mathematical terminology: "множество", "отображение", "функция"

**Algorithm descriptions**:
```markdown
Алгоритм обучения состоит из следующих этапов:
1) Инициализация весовых коэффициентов θ₀;
2) Для каждой эпохи t = 1, ..., T:
   a) вычисление функции потерь L(θₜ);
   b) обновление параметров: θₜ₊₁ = θₜ - η∇L(θₜ);
3) Выбор модели с минимальной ошибкой на валидационной выборке.
```

**Justification pattern**:
- "Выбор данного подхода обусловлен..." (Choice justified by...)
- "Такое решение позволяет обеспечить..." (This solution ensures...)
- "Применение данного метода вызвано необходимостью..." (Application necessitated by...)

**Enhanced style checklist**:
```markdown
## Methods-Specific Style Rules

- [ ] All mathematical objects formally introduced with "Пусть..."
- [ ] All variables defined: "где x – входные данные, y – целевая переменная"
- [ ] Complex algorithm descriptions use numbered hierarchical lists
- [ ] Each design choice has justification clause
- [ ] Hyperparameters presented in Russian table format
- [ ] Passive constructions for processes: "данные были нормализованы..."
- [ ] Formal citations: "оптимизатор Adam [Kingma & Ba, 2015]"
```

### Writer-Results Agent

**Enhancement needed**: Current agent lacks author style. Add:

**Objective presentation with formalization**:
```markdown
Результаты эксперимента представлены в таблице 1. Обозначим через E_model –
среднеквадратичную ошибку предложенной модели, E_baseline – ошибку базовой модели.
Тогда относительное улучшение составляет:

Δ = (E_baseline - E_model) / E_baseline × 100%        (1)

Для рассмотренных моделей M₁, M₂, ..., M₅ получены следующие значения
RMSE (°C): 2.1, 2.7, 3.1, 2.9, 3.4 соответственно.
```

**Table formatting**:
```markdown
**Таблица 1.** Результаты сравнительного анализа моделей. Приведены средние
значения и стандартные отклонения по 5 запускам. Жирным выделены лучшие результаты.

| Модель | RMSE (°C) ↓ | MAE (°C) ↓ | R² ↑ |
|--------|-------------|------------|------|
| **Предложенная** | **2.1±0.3** | **1.7±0.2** | **0.94** |
| GraphCast | 2.7±0.4 | 2.1±0.3 | 0.89 |
```

**Pattern for breakdowns**:
```markdown
Рассмотрим зависимость ошибки от временного горизонта прогноза. Пусть h –
горизонт прогноза в часах, E(h) – RMSE для данного горизонта. Тогда наблюдается
линейный рост ошибки: E(h) ≈ 0.4h + 1.2 (R² = 0.97) для h ∈ [24, 240].
```

**Style additions**:
```markdown
## Results-Specific Style Rules

- [ ] Formal variable introduction for key metrics
- [ ] Mathematical expressions for relationships
- [ ] Tables with Russian captions and arrows (↑↓)
- [ ] Passive voice dominance (80%): "получены следующие значения..."
- [ ] Numerical precision with units and uncertainties
- [ ] Formal references to visualizations: "На рисунке 2 представлена..."
- [ ] Structured breakdown using "Пусть... Тогда..." pattern
```

### Writer-Discussion Agent

**Major enhancement needed**. Add:

**Formal interpretation structure**:
```markdown
Полученные результаты позволяют сделать следующие выводы. Пусть M – множество
рассмотренных моделей, E_M – соответствующие им ошибки. Тогда предложенный
подход показывает улучшение Δ = 23% относительно лучшего baseline.

Рассмотрим возможные причины данного улучшения:
1) Использование физически обоснованной функции потерь обеспечивает выполнение
   законов сохранения, что критично для долгосрочных прогнозов [Автор, Год];
2) Архитектура трансформера позволяет учитывать дальние корреляции в
   пространственно-временных данных [Автор, Год];
3) Предварительное обучение на реанализе улучшает обобщающую способность
   модели на ограниченных данных наблюдений.
```

**Limitations (formal tone)**:
```markdown
Необходимо отметить следующие ограничения предложенного подхода:
1) Производительность в полярных регионах остается субоптимальной вследствие
   недостаточного покрытия обучающими данными;
2) Локальное сохранение массы обеспечивается приближенно (погрешность ~1%),
   что может быть критично для приложений, требующих строгого баланса;
3) Вычислительная сложность составляет O(N²) от числа точек сетки, что
   ограничивает применимость для сверхвысоких разрешений.
```

**Future directions (actionable formalism)**:
```markdown
Направления дальнейших исследований включают:
1) Интеграцию модели морского льда для улучшения прогнозов в полярных регионах
   [Автор, Год];
2) Применение дифференцируемых физических движков для строгого выполнения
   законов сохранения [Автор, Год];
3) Использование методов эффективной адаптации параметров для снижения
   вычислительных затрат при дообучении [Автор, Год].
```

**Style additions**:
```markdown
## Discussion-Specific Style Rules

- [ ] Formal conclusion structure: "Полученные результаты позволяют..."
- [ ] Numbered explanations with causal connections
- [ ] Formal limitation list with specific quantification
- [ ] Mathematical quantification where possible
- [ ] Passive constructions for objective statements
- [ ] Conditional modality: "может быть вызвано...", "вероятно, обусловлено..."
- [ ] Future work as numbered actionable items with citations
- [ ] Formal connectors: "В то же время", "Следовательно", "Тем не менее"
```

### Editor Agent

**Add final style enforcement**:

**Phase 2B: Style Unification Pass**
```markdown
### Style Consistency Check

1. **Abbreviation consistency**:
   ```bash
   # Extract all abbreviations
   grep -oE '[А-ЯЁ]{2,}' FINAL_ARTICLE.md | sort | uniq > abbreviations.txt

   # Verify all defined on first use
   for abbr in $(cat abbreviations.txt); do
     first_use=$(grep -n "$abbr" FINAL_ARTICLE.md | head -1)
     # Check if pattern "term ($abbr)" exists before first use
   done
   ```

2. **Mathematical formalization**:
   - Verify all formulas numbered: (1), (2), (3)...
   - Check variable definitions: "где x – ..., y – ..."
   - Ensure Russian notation in formulas

3. **Sentence complexity**:
   ```bash
   # Check average sentence length
   python check_sentence_length.py FINAL_ARTICLE.md
   # Target: 20-35 words average
   ```

4. **Voice distribution**:
   - Passive: 40-50%
   - Impersonal: 30-40%
   - Inclusive plural: 20-30%

5. **Formal markers**:
   ```bash
   # Check presence of characteristic phrases
   grep -c "Рассмотрим" FINAL_ARTICLE.md  # Should appear 5-10 times
   grep -c "Пусть" FINAL_ARTICLE.md       # Should appear 10-20 times
   grep -c "Тогда" FINAL_ARTICLE.md       # Should appear 8-15 times
   ```

6. **Section headers**:
   - Verify UPPERCASE for major sections
   - Numbered structure: 1., 2., 3., ...
```

**Add to completion checklist**:
```markdown
## Style Compliance Checklist

- [ ] All abbreviations defined on first use
- [ ] Mathematical variables introduced with "Пусть..."
- [ ] Formulas numbered and variables defined
- [ ] Section headers in UPPERCASE
- [ ] Average sentence length 20-35 words
- [ ] Voice distribution appropriate (passive 40-50%)
- [ ] Formal transitions present ("Следовательно", "Тогда", etc.)
- [ ] Numerical data includes units and precision
- [ ] Tables have Russian captions with arrows
- [ ] No emotional language or exclamations
- [ ] No first person singular
- [ ] Complex sentence structures predominate
```

---

## Master Style Checklist (For All Agents)

Use this checklist before finalizing ANY section:

### Tone & Register
- [ ] Строго официальный научный стиль (formal scientific)
- [ ] Нейтрально-объективный тон (neutral-objective)
- [ ] No emotional coloring
- [ ] No rhetorical questions

### Sentence Structure
- [ ] Average length 20-35 words
- [ ] Complex subordinate sentences predominate
- [ ] Participial and gerund clauses used
- [ ] Logical connectors present

### Lexicon
- [ ] All abbreviations defined on first use
- [ ] Mathematical formalization where applicable
- [ ] Russian terminology with English terms in Latin
- [ ] Technical precision maintained

### Grammar & Voice
- [ ] Passive constructions: 40-50%
- [ ] Impersonal constructions: 30-40%
- [ ] Inclusive first plural: 20-30%
- [ ] No first person singular ("я")

### Mathematical Notation
- [ ] Variables introduced: "Пусть X – ..."
- [ ] All symbols defined: "где x – входные данные"
- [ ] Formulas numbered: (1), (2), (3)
- [ ] Dimensions specified

### Formatting
- [ ] Section headers in UPPERCASE
- [ ] Numbered lists: 1) ...; 2) ...; 3) ...
- [ ] Bulleted lists: - ...; - ...; - ...
- [ ] Table captions in Russian with arrows (↑↓)
- [ ] Visual references: "На рисунке X..."

### Characteristic Phrases
- [ ] "Рассмотрим..." (appears 5-10 times)
- [ ] "Пусть..." (appears 10-20 times)
- [ ] "Тогда..." (appears 8-15 times)
- [ ] "Следовательно..." (appears 5-8 times)
- [ ] "Обозначим..." (appears 5-10 times)

### Numerical Data
- [ ] All numbers have units
- [ ] Percentages for improvements
- [ ] Concrete values, not qualitative assessments
- [ ] Uncertainties included (±)

### Citations
- [ ] First mentions cited
- [ ] Format: [Author et al., Year] or [Author, Year]
- [ ] Russian sources in Cyrillic
- [ ] International sources in Latin

---

## Implementation Instructions

### For Agent Developers

1. **Read AUTOR_STYLE.md** completely before modifying agents
2. **Add style section** to each agent's prompt with specific rules
3. **Update verification checklists** with style requirements
4. **Add automated checks** for:
   - Sentence length
   - Abbreviation definitions
   - Formula numbering
   - Voice distribution
5. **Test with examples** from AUTOR_STYLE.md

### For Agent Execution

1. **Load AUTOR_STYLE.md** at agent initialization
2. **Apply style rules** during writing, not as post-processing
3. **Self-verify** against checklist before saving
4. **Flag style violations** in quality score
5. **Auto-revise** if style score < 8/10

### For Quality Assurance

```bash
# Run style validator
python validate_style.py sections/section_name.md

# Check specific requirements
bash check_abbreviations.sh sections/section_name.md
bash check_formulas.sh sections/section_name.md
bash check_voice_distribution.sh sections/section_name.md

# Generate style report
python generate_style_report.py FINAL_ARTICLE.md > style_report.txt
```

---

## Common Violations and Fixes

### Violation 1: Informal tone
❌ **Bad**: "В этой работе мы попытались улучшить модель."
✅ **Good**: "Целью данной работы является разработка усовершенствованного метода..."

### Violation 2: Missing variable definitions
❌ **Bad**: "Модель обучалась на датасете D."
✅ **Good**: "Пусть D = {(xᵢ, yᵢ)}ᵢ₌₁ᴺ – обучающая выборка, где xᵢ ∈ ℝᵈ – входной вектор признаков, yᵢ ∈ ℝᵐ – целевая переменная. Модель обучалась на данном датасете."

### Violation 3: Vague results
❌ **Bad**: "Модель показала хорошие результаты."
✅ **Good**: "Модель достигла RMSE = 2.1±0.3°C, что соответствует улучшению на 23% относительно baseline (RMSE = 2.7±0.4°C, p < 0.001)."

### Violation 4: Short simple sentences
❌ **Bad**: "Мы использовали Adam. Скорость обучения 1e-4. Batch size 32."
✅ **Good**: "Обучение проводилось с использованием оптимизатора Adam [Kingma & Ba, 2015] с начальной скоростью обучения 1e-4 и размером батча 32, что обеспечило стабильную сходимость на протяжении 100 эпох."

### Violation 5: Missing abbreviation definitions
❌ **Bad**: "ГМД обрабатывались с использованием СУБД."
✅ **Good**: "Гидрометеорологические данные (ГМД) обрабатывались с использованием системы управления базами данных (СУБД)."

### Violation 6: Unnumbered formulas
❌ **Bad**:
```
L = L_MSE + λL_physics
```
✅ **Good**:
```
L = L_MSE + λL_physics                    (1)

где L – общая функция потерь, L_MSE – среднеквадратичная ошибка,
L_physics – физически обоснованный член регуляризации, λ – весовой коэффициент.
```

---

## Testing and Validation

### Automated Tests

Create validation scripts:

```python
# validate_style.py
def check_author_style(text):
    """Validate text against AUTOR_STYLE.md requirements."""

    issues = []

    # Check 1: Sentence length
    sentences = split_sentences(text)
    avg_length = mean([len(s.split()) for s in sentences])
    if not (20 <= avg_length <= 35):
        issues.append(f"Average sentence length {avg_length} outside 20-35 range")

    # Check 2: Characteristic phrases frequency
    markers = {
        "Рассмотрим": (5, 10),
        "Пусть": (10, 20),
        "Тогда": (8, 15),
        "Следовательно": (5, 8)
    }

    for marker, (min_count, max_count) in markers.items():
        count = text.count(marker)
        if not (min_count <= count <= max_count):
            issues.append(f"'{marker}' appears {count} times, expected {min_count}-{max_count}")

    # Check 3: Abbreviations defined
    abbrevs = re.findall(r'\b[А-ЯЁ]{2,}\b', text)
    for abbrev in set(abbrevs):
        pattern = rf'[а-яё\s]+\({abbrev}\)'
        if not re.search(pattern, text):
            issues.append(f"Abbreviation '{abbrev}' not defined on first use")

    # Check 4: Formula numbering
    formulas = re.findall(r'\\\[[\s\S]*?\\\]', text)
    for i, formula in enumerate(formulas, 1):
        if f'({i})' not in formula:
            issues.append(f"Formula {i} not numbered")

    return issues

# Usage
issues = check_author_style(open('sections/introduction.md').read())
if issues:
    print("Style violations found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ Style validation passed")
```

### Manual Review Checklist

Use this for final human review:

```markdown
## AUTOR_STYLE Compliance Review

**Reviewer**: _________
**Date**: _________
**Section**: _________

### 1. Tone and Register (Weight: 25%)
- [ ] Formal academic language throughout
- [ ] No emotional language or exclamations
- [ ] Authoritative expert distance maintained
- [ ] No rhetorical questions
**Score**: ___/10

### 2. Sentence Structure (Weight: 20%)
- [ ] Average length 20-35 words
- [ ] Complex subordinate sentences predominate
- [ ] Logical connectors used appropriately
- [ ] No excessive simple sentence sequences
**Score**: ___/10

### 3. Mathematical Formalization (Weight: 20%)
- [ ] Variables introduced formally ("Пусть...")
- [ ] All symbols defined ("где x – ...")
- [ ] Formulas numbered sequentially
- [ ] Dimensions and units specified
**Score**: ___/10

### 4. Lexical Profile (Weight: 15%)
- [ ] Abbreviations defined on first use
- [ ] Technical terminology consistent
- [ ] English terms in Latin properly
- [ ] Russian mathematical notation used
**Score**: ___/10

### 5. Voice Distribution (Weight: 10%)
- [ ] Passive constructions 40-50%
- [ ] Impersonal constructions 30-40%
- [ ] Inclusive plural 20-30%
- [ ] No first person singular
**Score**: ___/10

### 6. Formatting (Weight: 10%)
- [ ] Section headers in UPPERCASE
- [ ] Lists properly formatted
- [ ] Tables with Russian captions and arrows
- [ ] Visual references present
**Score**: ___/10

**Total Score**: ___/60 → ___/10
**Pass Threshold**: 8/10
**Status**: [ ] PASS  [ ] REVISE REQUIRED
```

---

## Revision Protocol

If style score < 8/10:

1. **Identify violations** using automated validator
2. **Prioritize fixes** by weight (Tone > Structure > Math > Lexicon)
3. **Apply corrections** section by section
4. **Re-validate** after each fix
5. **Human review** if automated score still < 8/10

**Maximum revisions**: 2 automatic + 1 human-assisted

---

## Summary

This integration ensures all writer agents produce text consistent with the author's established style profile. Key enforcement points:

1. **Formal academic Russian** following GOST standards
2. **Mathematical formalization** with proper variable introduction
3. **Complex sentence structures** averaging 20-35 words
4. **Consistent abbreviations** defined on first use
5. **Passive and impersonal** voice dominance
6. **Numbered formulas** with complete definitions
7. **Characteristic phrases** appearing at expected frequencies
8. **Numerical precision** with units and uncertainties

All agents must pass style validation (score ≥ 8/10) before section completion.

---

**Document Owner**: System Architect
**Last Updated**: 2026-01-18
**Version**: 1.0
**Status**: ACTIVE - MANDATORY COMPLIANCE
