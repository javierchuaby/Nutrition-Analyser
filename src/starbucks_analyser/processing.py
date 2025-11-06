from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

NUM_COLS = ["calories", "fat_g", "carbs_g", "fiber_g", "protein_g", "sodium"]


def describe(df: pd.DataFrame) -> dict[str, Any]:
    sub = df[[c for c in NUM_COLS if c in df.columns]]
    desc: dict[str, Any] = {
        "count": int(sub.shape[0]),
        "means": {c: float(sub[c].mean()) for c in sub.columns},
        "medians": {c: float(sub[c].median()) for c in sub.columns},
        "mins": {c: float(sub[c].min()) for c in sub.columns},
        "maxs": {c: float(sub[c].max()) for c in sub.columns},
        "totals": {c: float(sub[c].sum()) for c in sub.columns},
        "assumptions": {},
    }
    # Populate sugar mean using carbs as proxy when sugar column is absent
    if "sugar_g" not in sub.columns and "carbs_g" in sub.columns:
        means_mut: dict[str, float] = desc["means"]  # type: ignore[assignment]
        means_mut["sugar_g"] = float(sub["carbs_g"].mean())
        assumptions_mut: dict[str, Any] = desc["assumptions"]  # type: ignore[assignment]
        assumptions_mut["sugar_proxy"] = "carbs_g"
    if "fat_g" in sub.columns and "protein_g" in sub.columns:
        ratio = (sub["fat_g"] / sub["protein_g"]).replace([float("inf")], pd.NA)
        mean_ratio = ratio.mean(skipna=True)
        if pd.notna(mean_ratio):
            means_dict: dict[str, float] = desc["means"]  # type: ignore[assignment]
            means_dict["fat_to_protein_ratio"] = float(mean_ratio)
    return desc


def compare(drinks: pd.DataFrame, food: pd.DataFrame) -> dict[str, Any]:
    """Compare drinks and food datasets, including fat-to-protein ratio comparison.
    
    Args:
        drinks: Normalized drinks DataFrame
        food: Normalized food DataFrame
        
    Returns:
        Dictionary with descriptive stats for each dataset and comparisons
    """
    d = describe(drinks)
    f = describe(food)
    out = {"drinks": d, "food": f, "comparisons": {}}
    
    # Compare calories
    if "calories" in d["means"] and "calories" in f["means"]:
        out["comparisons"]["avg_calories_drinks_vs_food"] = {
            "drinks": d["means"]["calories"],
            "food": f["means"]["calories"],
            "difference": d["means"]["calories"] - f["means"]["calories"],
        }
    
    # Compare average sugars (carbs proxy populated into sugar_g if absent)
    if "sugar_g" in d["means"] and "sugar_g" in f["means"]:
        out["comparisons"]["avg_sugar_drinks_vs_food"] = {
            "drinks": d["means"]["sugar_g"],
            "food": f["means"]["sugar_g"],
            "difference": d["means"]["sugar_g"] - f["means"]["sugar_g"],
            "note": "sugar may be proxied by carbs_g if absent",
        }
    
    # Compare fat-to-protein ratio across datasets
    drinks_ratio = d["means"].get("fat_to_protein_ratio")
    food_ratio = f["means"].get("fat_to_protein_ratio")
    
    if drinks_ratio is not None and food_ratio is not None:
        out["comparisons"]["fat_to_protein_ratio_drinks_vs_food"] = {
            "drinks": drinks_ratio,
            "food": food_ratio,
            "difference": drinks_ratio - food_ratio,
            "ratio_difference_pct": ((drinks_ratio - food_ratio) / food_ratio * 100) if food_ratio != 0 else None,
            "note": "Higher ratio indicates more fat relative to protein",
        }
    elif drinks_ratio is not None:
        out["comparisons"]["fat_to_protein_ratio_drinks"] = {
            "drinks": drinks_ratio,
            "note": "Food dataset missing fat or protein data for comparison",
        }
    elif food_ratio is not None:
        out["comparisons"]["fat_to_protein_ratio_food"] = {
            "food": food_ratio,
            "note": "Drinks dataset missing fat or protein data for comparison",
        }
    
    # Additional nutrient mean comparisons
    # Support both new "sodium" and legacy "sodium_mg" column names
    nutrients = ["fat_g", "protein_g", "sodium", "sodium_mg"]
    for nutrient in nutrients:
        if nutrient in d["means"] and nutrient in f["means"]:
            out["comparisons"][f"avg_{nutrient}_drinks_vs_food"] = {
                "drinks": d["means"][nutrient],
                "food": f["means"][nutrient],
                "difference": d["means"][nutrient] - f["means"][nutrient],
            }
    
    # Largest absolute difference among comparisons
    if out["comparisons"]:
        diffs = {k: abs(v.get("difference", 0.0)) for k, v in out["comparisons"].items() if isinstance(v, dict) and "difference" in v}
        if diffs:
            key_max = max(diffs, key=diffs.get)
            out["comparisons"]["largest_difference"] = {"metric": key_max, "abs_diff": diffs[key_max]}
    
    return out


def save_metrics(payload: dict[str, Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def load_metrics(path: str | Path) -> dict[str, Any] | None:
    """Load metrics from a JSON file. Returns None if file doesn't exist or can't be read."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def top_n_by(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    if column not in df.columns:
        return df.iloc[0:0]
    cols: list[str] = [column]
    # Support both new "item_name" and legacy "item" column names
    if "item_name" in df.columns:
        cols = ["item_name", column]
    elif "item" in df.columns:
        cols = ["item", column]
    sub = df[cols].copy()
    sub = sub.dropna(subset=[column])
    sub = sub.sort_values(by=column, ascending=False).head(n)
    return sub
