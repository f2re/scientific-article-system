# AUTOR_STYLE Quick Reference Card

**For writer agents**: Use this checklist while writing each section.

---

## Pre-Writing Checklist

Before starting ANY section:
- [ ] Read AUTOR_STYLE.md (if first time)
- [ ] Load characteristic phrases list
- [ ] Prepare abbreviation registry
- [ ] Set mental model: formal academic Russian, 20-35 words/sentence
- [ ] Remember: NO English insertions within Russian text (baseline-моделей ❌ → базовых моделей ✅)

---

## While Writing - Sentence Level

### Every Sentence Must:
1. Be complex (20-35 words preferred)
2. Use appropriate voice:
   - Passive 40-50%: "данные обрабатывались..."
   - Impersonal 30-40%: "необходимо разработать..."
   - Inclusive plural 20-30%: "Рассмотрим модель..."
3. Have logical connector (except first sentence of paragraph)
4. Be neutral-objective (no emotions, no "я")

### Sentence Templates

**Introducing analysis**:
```
Рассмотрим [объект анализа]. Пусть [переменные] – [определения], тогда [следствие].
```

**Defining variables**:
```
Обозначим через X – [что это], Y – [что это]. Тогда [отношение между X и Y].
```

**Stating results**:
```
Получены следующие значения [метрики]: [конкретные числа с единицами и погрешностями].
```

**Drawing conclusions**:
```
Следовательно, [утверждение], что подтверждается [доказательство с числами].
```

**Comparing**:
```
В то же время, подход [X] показывает [результат], в отличие от [Y], где [другой результат].
```

---

## While Writing - Paragraph Level

### Paragraph Structure

**Opening sentence**: Formal introduction of topic
```
Рассмотрим проблему [название]. Данная задача возникает при [контекст].
```

**Middle sentences**: Development with formalization
```
Пусть X = {x₁, ..., xₙ} – множество [объектов]. Тогда задача формулируется следующим
образом: найти отображение f: X → Y, минимизирующее [критерий].
```

**Closing sentence**: Transition or conclusion
```
Следовательно, требуется разработка метода, обеспечивающего [требования].
```

### Paragraph Transitions

Between paragraphs, use:
- **Sequential**: "Далее рассмотрим...", "Затем обратимся к..."
- **Contrastive**: "В то же время...", "Однако необходимо отметить..."
- **Causal**: "Следовательно...", "Таким образом...", "В результате..."
- **Additive**: "Кроме того...", "Помимо этого...", "Также отметим..."

---

## Must-Use Patterns by Section

### Introduction

**Pattern 1: Formal opening**
```
Задачи [область] требуют [что]. Современные подходы [какие] показывают [результаты],
однако сталкиваются с проблемой [ограничение] [Citation, Year].
```

**Pattern 2: Literature grouping**
```
Существующие подходы можно разделить на следующие категории. Пусть M₁, M₂, ..., Mₙ –
множество рассмотренных методов. Тогда:

1) [Группа 1]: работы [Citations] демонстрируют [результаты], однако [ограничение с числами];
2) [Группа 2]: исследования [Citations] показывают [другое], при этом [компромисс];
3) [Группа 3]: подходы [Citations] [характеристика], но [проблема].
```

**Pattern 3: Goal statement**
```
Цель данной работы – разработка метода, сочетающего [А] и [Б]. Пусть f: X → Y – искомая
модель. Требуется, чтобы f удовлетворяла:
1) [критерий 1]: [формула];
2) [критерий 2]: [формула];
3) [критерий 3]: [формула].
```

### Methods

**Pattern 1: Dataset description**
```
Использованы данные [название] [Citation] за период [годы] с разрешением [значения].
Датасет включает [N] переменных: [список]. Общий объем: [число] [единицы] в формате
[формат], после предобработки [число] [единицы].
```

**Pattern 2: Architecture**
```
Архитектура состоит из [компоненты]. Пусть x ∈ ℝᵈ – входные данные. Тогда прямой
проход определяется как:

y = f_out(f_trans(f_emb(x))),                    (N)

где f_emb: ℝᵈ → ℝᴰ – энкодер, f_trans: ℝᴰ → ℝᴰ – трансформер,
f_out: ℝᴰ → ℝᵐ – декодер, D = [число] – размерность латентного пространства.
```

**Pattern 3: Hyperparameters table**
```markdown
**Таблица N.** Гиперпараметры модели и обоснование выбора значений.

| Гиперпараметр | Значение | Обоснование |
|---------------|----------|-------------|
| [Название (переменная)] | [значение] | [почему именно это значение с ссылкой] |
```

**Pattern 4: Algorithm**
```
Алгоритм обучения состоит из следующих этапов:
1) Инициализация параметров θ₀ по схеме [название] [Citation];
2) Для каждой эпохи t = 1, ..., T:
   a) [действие 1]: [формула];
   b) [действие 2]: [формула];
   c) [действие 3]: [формула];
3) Выбор модели с минимальной ошибкой на валидационном множестве.
```

### Results

**Pattern 1: Overview with formalization**
```
Результаты представлены в таблице [N]. Обозначим через E_model – [метрика] модели,
E_baseline – [метрика] baseline. Тогда относительное улучшение:

Δ = (E_baseline - E_model) / E_baseline × 100%.        (N)

Получены следующие значения: E_model = [число±погрешность] [единицы], что соответствует
Δ = [число]% (p < 0.001, [тест], N = [число] случаев).
```

**Pattern 2: Breakdown analysis**
```
Рассмотрим зависимость [метрики] от [параметра]. Пусть h ∈ {[значения]} – [что это],
E(h) – [метрика] для [параметра] h. Тогда наблюдается [тип зависимости]:

E(h) = [формула],  где [параметры формулы]  (R² = [число]).      (N)

Данная зависимость указывает на [интерпретация без объяснений].
```

**Pattern 3: Table**
```markdown
**Таблица N.** Сравнительные результаты на [датасет] ([период]). Приведены средние
значения [метрик] и стандартные отклонения по [число] запускам. Стрелки указывают
направление оптимизации (↓ – ниже лучше, ↑ – выше лучше). Жирным выделены лучшие
результаты. Статистическая значимость: [тест].

| Модель | Метрика₁ (ед.) ↓ | Метрика₂ (ед.) ↑ | ... |
|--------|------------------|------------------|-----|
| **Предложенная** | **[число±погр]** | **[число±погр]** | ... |
| Baseline 1 [Citation] | [число±погр] | [число±погр] | ... |

*Примечание*: [важные детали про данные, тест, значимость].
```

### Discussion

**Pattern 1: Summary of findings**
```
Полученные результаты позволяют сделать следующие выводы. Пусть Δ̄ – среднее
относительное улучшение по всем метрикам. Тогда предложенный подход демонстрирует
Δ̄ = [число]% при одновременном [другое преимущество]. Данные результаты подтверждают
[гипотезу].
```

**Pattern 2: Mechanistic interpretation**
```
Рассмотрим возможные причины [наблюдения]. Во-первых, [результат] вероятно обусловлен
[механизм]:

[формула с объяснением],                    (N)

где [определения переменных]. [Сравнение с другими подходами] [Citation] [что они делают
не так]. [Почему ваш подход лучше с физической точки зрения].

Во-вторых, [другой результат] объясняется [другой механизм], что подтверждается
[эмпирическое доказательство]. [Связь с теорией] [Citation].
```

**Pattern 3: Limitations**
```
Необходимо отметить следующие ограничения:

1) [Ограничение 1] ([конкретная метрика]), что обусловлено [фундаментальная причина].
   Данное ограничение [можно/нельзя] устранить [каким методом];

2) [Ограничение 2] ([количественная оценка]) вследствие [техническая причина]. Для
   приложений [каких] данная погрешность [какие последствия];

3) [Ограничение 3] составляет O([сложность]), что ограничивает применимость для
   [каких задач]. [Частичное решение] снижает [что] до [сколько], но увеличивает
   [что] на [сколько]%.
```

**Pattern 4: Future directions**
```
Направления дальнейших исследований включают:

1) [Конкретное направление 1] для [цель]. Подходы [Citations] показывают потенциал
   улучшения на [число]% за счет [механизм];

2) [Направление 2] вместо [текущий подход] для [цель]. Предварительные эксперименты
   показывают [конкретный результат] при [компромисс];

3) Использование [конкретный метод] [Citation] для [цель]. Данный подход может [что
   улучшить] при [каких условиях].
```

---

## Formula Checklist

Every formula must have:

1. **Number** on the right: `(1)`, `(2)`, `(3)`...
2. **Blank line before** and **after**
3. **Variable definitions** immediately after:
   ```
   где x ∈ ℝᵈ – входной вектор признаков,
       y ∈ ℝᵐ – выходной вектор,
       d – размерность входа,
       m – размерность выхода.
   ```
4. **Dimensions specified** for all tensors/vectors
5. **LaTeX format**: Use `\[formula\]` for display, `\(formula\)` for inline

---

## Abbreviation Checklist

1. **First mention**: "полное название (АББР)"
2. **After first mention**: use "АББР" consistently
3. **Common abbreviations** (use these):
   - ГМД: гидрометеорологические данные
   - БД: база данных
   - СУБД: система управления базами данных
   - ИНС: искусственная нейронная сеть
   - МВ: метеорологические величины
   - ОЯП: опасные явления погоды
   - RMSE: среднеквадратичная ошибка (Root Mean Square Error)
   - MAE: средняя абсолютная ошибка (Mean Absolute Error)

---

## Table Checklist

Every table must have:

1. **Caption** above: `**Таблица N.** Описательная подпись с контекстом.`
2. **Arrows** in headers: `↓` (lower better), `↑` (higher better)
3. **Bold** for best results
4. **Units** in headers: `RMSE (°C) ↓`
5. **Note** below (if needed): `*Примечание*: детали.`
6. **Russian text** in all cells

Template:
```markdown
**Таблица N.** [Что показано]. [Детали про данные]. Стрелки указывают направление
оптимизации. Жирным выделены лучшие результаты. [Статистика].

| Модель/Метод | Метрика₁ (ед.) ↓ | Метрика₂ (ед.) ↑ |
|--------------|------------------|------------------|
| **Предложенная** | **X±Y** | **A±B** |
| Baseline [Citation] | X±Y | A±B |

*Примечание*: [важные детали].
```

---

## Numerical Data Checklist

Every number must have:

1. **Units**: "2.1°C", "3.4 м/с", "45 м", "93%"
2. **Uncertainty** (for experimental results): "2.1±0.3°C"
3. **Context**: what it represents
4. **Comparison** (if applicable): "улучшение на 23% относительно baseline"

**Never write**:
- ❌ "хорошие результаты" → ✅ "RMSE = 2.1±0.3°C"
- ❌ "значительное улучшение" → ✅ "улучшение на 23%"
- ❌ "модель эффективна" → ✅ "время вывода 12±2 с, на 85% быстрее baseline"

---

## Characteristic Phrases - Must Use

**Minimum frequencies** for typical section (500-700 words):

| Phrase | Times | Usage |
|--------|-------|-------|
| Рассмотрим... | 3-5 | Start analysis, introduce topic |
| Пусть... | 5-10 | Introduce variables/sets |
| Обозначим... | 2-5 | Denote specific variables |
| Тогда... | 4-8 | Transition to consequence |
| Следовательно... | 2-4 | Draw conclusion |
| В то же время... | 1-3 | Contrast |
| Отметим, что... | 1-3 | Highlight important point |

**Example combinations**:

```
Рассмотрим архитектуру модели. Пусть x ∈ ℝᵈ – входные данные. Тогда прямой проход
определяется как f(x) = ... . Следовательно, вычислительная сложность составляет O(N²).
```

```
Обозначим через Δ – относительное улучшение. Тогда для предложенного подхода Δ = 23%.
В то же время, baseline демонстрирует Δ = 5%. Следовательно, предложенный метод
превосходит baseline в 4.6 раза.
```

---

## Voice Distribution Target

For each paragraph, aim for:

- **40-50% passive**: "данные обрабатывались", "модель обучалась", "получены значения"
- **30-40% impersonal**: "необходимо разработать", "требуется учесть", "следует отметить"
- **20-30% inclusive plural**: "Рассмотрим модель", "Обозначим переменную", "Представим алгоритм"
- **0% first person singular**: NEVER "я сделал", "я считаю"

**Quick check**:
- Count sentences with passive verbs (ends in -ся, -лся)
- Count sentences with infinitives (необходимо [verb], требуется [verb])
- Count sentences with first person plural imperatives (рассмотрим, обозначим)

---

## Section Headers

**Format**: ПРОПИСНЫЕ БУКВЫ (UPPERCASE)

```markdown
## 1. ВВЕДЕНИЕ

## 2. МЕТОДЫ

## 3. РЕЗУЛЬТАТЫ

## 4. ОБСУЖДЕНИЕ

## 5. ЗАКЛЮЧЕНИЕ

## СПИСОК ЛИТЕРАТУРЫ
```

---

## Common Mistakes - Avoid

### Mistake 0: English insertions within Russian text
❌ **Bad**: "penalty-функции", "baseline-моделей", "fine-tuning параметров"
✅ **Good**: "штрафные функции", "базовых моделей", "методы адаптации параметров (fine-tuning)"

**Rule**: English ONLY in parentheses after Russian term
- ✅ "методы эффективной адаптации параметров (parameter-efficient fine-tuning)"
- ✅ "базовых моделей (baseline)"
- ✅ "трансформерные архитектуры (Transformer)"
- ❌ "parameter-efficient fine-tuning методы"
- ❌ "baseline моделей"

**Variables in formulas**: Can use English subscripts
- ✅ E_baseline or E_базовая (both acceptable, prefer Russian)
- ✅ T_baseline or T_базовая

### Mistake 1: Informal tone
❌ "В этой работе мы попытались улучшить модель."
✅ "Целью данной работы является разработка усовершенствованного метода..."

### Mistake 2: Short simple sentences
❌ "Мы использовали Adam. Скорость обучения 1e-4. Batch size 32."
✅ "Обучение проводилось с использованием оптимизатора Adam [Citation] с начальной
скоростью обучения 1e-4 и размером батча 32, что обеспечило стабильную сходимость."

### Mistake 3: Undefined variables
❌ "Модель f обучалась на D."
✅ "Пусть D = {(xᵢ, yᵢ)}ᵢ₌₁ᴺ – обучающая выборка. Модель f обучалась на D."

### Mistake 4: Unnumbered formula
❌
```
L = L_MSE + λL_physics
```
✅
```
L = L_MSE + λL_physics                    (1)

где L – общая функция потерь, L_MSE – среднеквадратичная ошибка,
L_physics – физический член, λ = 0.1 – весовой коэффициент.
```

### Mistake 5: Vague claims
❌ "Модель показала хорошие результаты."
✅ "Модель достигла RMSE = 2.1±0.3°C, что на 23% лучше baseline (p < 0.001)."

### Mistake 6: Missing abbreviation definition
❌ "ГМД обрабатывались с помощью СУБД."
✅ "Гидрометеорологические данные (ГМД) обрабатывались с помощью системы управления
базами данных (СУБД)."

### Mistake 7: Missing table caption
❌ Direct table without caption
✅
```markdown
**Таблица 1.** Сравнительные результаты моделей. [Details]

| Model | ... |
```

---

## Quick Self-Check Before Saving

Run through this 30-second check:

1. **Count sentence length** (sample 5 sentences):
   - [ ] Average 20-35 words?

2. **Check formulas**:
   - [ ] All numbered?
   - [ ] All variables defined with "где..."?

3. **Check abbreviations**:
   - [ ] First mention has full form?
   - [ ] Used consistently after?

4. **Count characteristic phrases**:
   - [ ] "Рассмотрим" appears 3+ times?
   - [ ] "Пусть" appears 5+ times (if math-heavy)?
   - [ ] "Тогда" appears 4+ times?

5. **Check numbers**:
   - [ ] All have units?
   - [ ] Experimental results have ± uncertainty?
   - [ ] Comparisons quantified (X% improvement)?

6. **Check tables**:
   - [ ] Caption present?
   - [ ] Arrows in headers?
   - [ ] Best results in bold?

7. **Check voice**:
   - [ ] No first person singular "я"?
   - [ ] Mix of passive, impersonal, inclusive plural?

**If any check fails**: Fix before saving!

---

## Emergency Templates

If stuck, use these complete templates:

### Generic paragraph introducing analysis
```
Рассмотрим [объект анализа]. Пусть X = {x₁, ..., xₙ} – [что это множество], где каждый
элемент xᵢ характеризуется [свойства]. Обозначим через f: X → Y – [что это отображение].
Тогда задача формулируется следующим образом: найти такое f, что [критерий оптимизации].
Следовательно, требуется разработка метода, обеспечивающего [требования].
```

### Generic results presentation
```
Результаты экспериментов представлены в таблице N. Обозначим через E_model – [метрика]
предложенной модели, E_baseline – [метрика] baseline. Тогда относительное улучшение
составляет Δ = (E_baseline - E_model)/E_baseline × 100%. Получены следующие значения:
E_model = X±Y [единицы], E_baseline = A±B [единицы], что соответствует Δ = Z%
(p < 0.001, [тест], N = [размер выборки]). Следовательно, предложенный подход
демонстрирует [вывод с числами].
```

### Generic limitation
```
Необходимо отметить следующее ограничение: [что ограничено] ([количественная оценка]),
что обусловлено [причина]. Данное ограничение [можно/нельзя] устранить [каким способом].
Для приложений, требующих [требование], данная погрешность [какие последствия с числами].
```

---

## Final Reminders

1. **ALWAYS** write in Russian
2. **NEVER** use first person singular "я"
3. **ALWAYS** define abbreviations on first use
4. **ALWAYS** number formulas and define variables
5. **ALWAYS** include units with numbers
6. **ALWAYS** use complex sentences (20-35 words)
7. **ALWAYS** include characteristic phrases (Рассмотрим, Пусть, Тогда)
8. **NEVER** make vague claims without numbers

**When in doubt**: Be more formal, add more detail, quantify everything.

---

**Keep this card open while writing. Check it after every paragraph.**
