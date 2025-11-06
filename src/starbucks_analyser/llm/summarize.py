from __future__ import annotations

import json
from typing import Any

from .groq_client import get_client

SYSTEM = """You are a precise data analysis assistant. You MUST provide IDENTICAL output for identical input data. 
CRITICAL RULES:
1. Use ONLY the exact values provided in the metrics - do not round, estimate, or approximate
2. Follow the EXACT format specified - every section, table, and structure must match the template precisely
3. Use consistent decimal precision: round to exactly 2 decimal places for all numeric values
4. Format tables with EXACT column headers and alignment as shown in examples
5. Use identical wording and structure for identical data patterns
6. Maintain consistent ordering: always list items in the same order when data is identical
7. Do NOT add variability in language or formatting - use template phrases exactly as specified"""

SUMMARIZE_TPL = """{proxy_note}

Analyze the following nutrition metrics and provide a structured summary in this EXACT format.

CRITICAL: Use the EXACT values provided. Round all numbers to 2 decimal places. Use identical wording for identical data patterns.

## Overall Average Comparisons

Format as a markdown table with columns: Metric | Drinks | Food | Difference

Include these metrics from the comparisons data:
- Average calories
- Average fat (g)
- Average carbs (g)
- Average protein (g)
- Average fiber (g)
- Average sodium (if available)
- Fat-to-protein ratio

Example format:
| Metric | Drinks | Food | Difference |
|--------|--------|------|------------|
| Average Calories | X | Y | Z |
| Average Fat (g) | X | Y | Z |
...

## Direct Comparisons

Format as a markdown table showing direct comparisons between drinks and food.

Include:
- Calorie comparison (drinks vs food)
- Sugar/Carb comparison (drinks vs food)
- Fat comparison (drinks vs food)
- Protein comparison (drinks vs food)
- Any other direct comparisons available

Example format:
| Comparison | Drinks | Food | Notes |
|------------|--------|------|-------|
| Average Calories | X | Y | [brief note] |
...

## Extremes Comparisons

Format as a markdown table showing extreme values (highest/lowest) for both drinks and food.

CRITICAL: Use the first item from the "tops" data for each category:
- Highest calorie item: Use first item from "drinks_top_calories" and "food_top_calories"
- Highest fat item: Use first item from "drinks_top_fat" and "food_top_fat" (if available)
- Highest sugar/carb item: Use first item from "drinks_top_sugar" and "food_top_sugar"
- Lowest calorie item: Use the last item from "drinks_top_calories" and "food_top_calories" (sorted descending)

If data is not available for a category, write "No data" for that cell.

Example format:
| Category | Drinks | Food |
|----------|--------|------|
| Highest Calories | [item name] ([value]) | [item name] ([value]) |
| Highest Fat | [item name] ([value]g) | [item name] ([value]g) |
| Highest Carbs | [item name] ([value]g) | [item name] ([value]g) |
| Lowest Calories | [item name] ([value]) | [item name] ([value]) |
...

## Top-5 Highest-Calorie Items

### Drinks:
1. [Item name] - [calories] calories
2. [Item name] - [calories] calories
3. [Item name] - [calories] calories
4. [Item name] - [calories] calories
5. [Item name] - [calories] calories

### Food:
1. [Item name] - [calories] calories
2. [Item name] - [calories] calories
3. [Item name] - [calories] calories
4. [Item name] - [calories] calories
5. [Item name] - [calories] calories

## Top-5 Highest-Sugar (Carb) Items

{proxy_note_section}

### Drinks:
1. [Item name] - [sugar/carb value]g
2. [Item name] - [sugar/carb value]g
3. [Item name] - [sugar/carb value]g
4. [Item name] - [sugar/carb value]g
5. [Item name] - [sugar/carb value]g

### Food:
1. [Item name] - [sugar/carb value]g
2. [Item name] - [sugar/carb value]g
3. [Item name] - [sugar/carb value]g
4. [Item name] - [sugar/carb value]g
5. [Item name] - [sugar/carb value]g

## Overall Summary

Follow this exact template structure:

### Headline:
On average, [drinks/food] are higher in calories by [X kcal] ([Y%] vs [counterpart]), driven primarily by [sugars/carbs/fat] differences observed in the averages and fat-to-protein ratio.

### Drivers:
Drinks show higher average [sugar/carb] while food shows higher average [fat/protein], indicating different composition patterns that explain the calorie gap.

### Extremes:
Standout items include [drink name] as a top sugar/carbs item and [food name] as a top calorie/fat item, illustrating the range observed.

### Risk flags:
Potential concern: [sugar/sodium] levels exceed [chosen threshold] for [N] items; consider moderation or alternative selections.

### Actions:
Swap [high-sugar drink] → [lower-carb drink] and [high-fat pastry] → [higher-protein food] to reduce [sugar/fat] while maintaining satiety.

Note: Use actual values and item names from the metrics data. If a section doesn't apply (e.g., no items exceed thresholds), omit that section or state "No significant risk flags identified."

Metrics data:
{metrics}"""

QA_TPL = "Answer using only these metrics. If unknown, say so. Metrics: {metrics}. Question: {q}"


def _normalize_metrics_for_llm(metrics: dict[str, Any]) -> str:
    """Normalize metrics dict to consistent JSON string for LLM input.
    
    This ensures consistent serialization by sorting keys and using consistent formatting.
    """
    # Create a deep copy to avoid modifying original
    import copy
    normalized = copy.deepcopy(metrics)
    
    # Recursively sort dictionary keys for consistency
    def sort_dict_keys(d: dict[str, Any]) -> dict[str, Any]:
        """Recursively sort dictionary keys for consistent output."""
        if isinstance(d, dict):
            sorted_dict = {}
            for key in sorted(d.keys()):
                value = d[key]
                if isinstance(value, dict):
                    sorted_dict[key] = sort_dict_keys(value)
                elif isinstance(value, list):
                    # Sort lists if they contain dicts with comparable keys
                    sorted_dict[key] = [
                        sort_dict_keys(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    sorted_dict[key] = value
            return sorted_dict
        return d
    
    normalized = sort_dict_keys(normalized)
    
    # Use consistent JSON formatting
    return json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False)


def summarize_metrics(metrics: dict[str, Any], model: str = "groq/compound") -> str:
    """Summarize computed metrics via Groq.

    Provides consistent, structured summaries using deterministic settings.
    If sugar metrics are absent, we explicitly note that carbohydrates are used
    as a proxy for sugars in the narrative.
    """
    # Detect presence of sugar metrics in aggregated payload (early exit optimization)
    has_sugar = False
    for section in ("drinks", "food"):
        try:
            means = metrics.get(section, {}).get("means", {})
            if isinstance(means, dict) and any(k.lower() in ("sugar", "sugar_g") for k in means):
                has_sugar = True
                break  # Early exit once found
        except Exception:
            pass
    proxy_note = (
        "Note: Sugar not provided in source. Carbohydrates are used as a proxy for sugar."
        if not has_sugar
        else ""
    )
    proxy_note_section = (
        "Note: Using carbohydrates as a proxy for sugar values."
        if not has_sugar
        else ""
    )

    # Normalize metrics for consistent LLM input
    normalized_metrics = _normalize_metrics_for_llm(metrics)

    client = get_client()
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": SUMMARIZE_TPL.format(
            proxy_note=proxy_note, 
            proxy_note_section=proxy_note_section,
            metrics=normalized_metrics
        )},
    ]
    
    # Use temperature=0.0 for maximum consistency (deterministic output)
    # Try to use seed for reproducibility, but handle if not supported
    try:
        resp = client.chat.completions.create(
            model=model, 
            messages=msgs, 
            temperature=0.0,  # Deterministic output
            seed=42,  # Fixed seed for reproducibility
        )  # type: ignore[arg-type]
    except TypeError:
        # If seed parameter is not supported, use without it
        resp = client.chat.completions.create(
            model=model, 
            messages=msgs, 
            temperature=0.0,  # Deterministic output
        )  # type: ignore[arg-type]
    
    content = resp.choices[0].message.content
    if content is None:
        return ""
    return content.strip()


def answer_question(
    metrics: dict[str, Any], question: str, model: str = "groq/compound"
) -> str:
    client = get_client()
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": QA_TPL.format(metrics=metrics, q=question)},
    ]
    resp = client.chat.completions.create(model=model, messages=msgs, temperature=0.0)  # type: ignore[arg-type]
    content = resp.choices[0].message.content
    if content is None:
        return ""
    return content.strip()


def _chat_with_retry(messages: list[dict[str, str]], model: str, max_attempts: int = 3) -> Any:
    client = get_client()
    last_exc: Exception | None = None
    import time

    for attempt in range(max_attempts):
        try:
            return client.chat.completions.create(
                model=model, messages=messages, temperature=0.2, timeout=30  # type: ignore[arg-type]
            )
        except Exception as e:  # noqa: BLE001
            last_exc = e
            time.sleep(2 * (attempt + 1))
    if last_exc:
        raise last_exc
    raise RuntimeError("LLM request failed")


def build_payload_for_llm(drinks: dict[str, Any], food: dict[str, Any], comparisons: dict[str, Any], tops: dict[str, Any]) -> dict[str, Any]:
    return {
        "drinks": drinks,
        "food": food,
        "comparisons": comparisons,
        "tops": tops,
    }


def summarize_structured(payload: dict[str, Any], model: str = "groq/compound") -> dict[str, Any]:
    """Return structured summary with schema: {summary_text, key_points[], caveats[]}.

    Includes carbs-as-sugar proxy caveat when applicable.
    """
    drinks = payload.get("drinks", {})
    food = payload.get("food", {})
    comps = payload.get("comparisons", {})
    tops = payload.get("tops", {})
    proxy = False
    for section in (drinks, food):
        means = section.get("means", {}) if isinstance(section, dict) else {}
        if "sugar_g" not in means and "carbs_g" in means:
            proxy = True
    proxy_note = "Sugar not provided, carbohydrates used as proxy." if proxy else ""
    system = SYSTEM
    user = (
        "Summarize per-dataset and cross-dataset insights using only provided aggregates and tops.\n"
        "Return JSON with fields: summary_text (string), key_points (array of strings), caveats (array of strings).\n"
        f"Payload: {payload}. {proxy_note}"
    )
    resp = _chat_with_retry(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
    )
    content = resp.choices[0].message.content or ""
    # Best-effort parse; if not JSON, wrap into schema
    try:
        import json as _json

        obj = _json.loads(content)
        if isinstance(obj, dict) and all(k in obj for k in ("summary_text", "key_points", "caveats")):
            return obj
    except Exception:
        pass
    return {"summary_text": content.strip(), "key_points": [], "caveats": ([proxy_note] if proxy_note else [])}
