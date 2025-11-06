from __future__ import annotations

import pandas as pd


def get_sugar_or_carb_column(df: pd.DataFrame) -> str | None:
    """Get sugar_g column if available, otherwise carbs_g, or None if neither exists."""
    if "sugar_g" in df.columns:
        return "sugar_g"
    if "carbs_g" in df.columns:
        return "carbs_g"
    return None


def get_item_column(df: pd.DataFrame) -> str | None:
    """Get item_name column if available, otherwise item, or None if neither exists."""
    if "item_name" in df.columns:
        return "item_name"
    if "item" in df.columns:
        return "item"
    return None


def get_sodium_column(df: pd.DataFrame) -> str | None:
    """Get sodium column if available, otherwise sodium_mg, or None if neither exists."""
    if "sodium" in df.columns:
        return "sodium"
    if "sodium_mg" in df.columns:
        return "sodium_mg"
    return None


def by_calories_under(df: pd.DataFrame, max_calories: float) -> pd.DataFrame:
    if "calories" not in df.columns:
        return df.iloc[0:0]
    return df[df["calories"] <= max_calories]


def with_column_threshold(df: pd.DataFrame, column: str, max_value: float) -> pd.DataFrame:
    if column not in df.columns:
        return df.iloc[0:0]
    return df[df[column] <= max_value]


def apply_filters(
    df: pd.DataFrame,
    *,
    calories_le: float | None = None,
    sugar_g_le: float | None = None,
    fat_g_le: float | None = None,
    protein_g_ge: float | None = None,
    sodium_mg_le: float | None = None,
    caffeine_mg_gt: float | None = None,
    name_contains: str | None = None,
) -> pd.DataFrame:
    mask = pd.Series([True] * len(df), index=df.index)
    if calories_le is not None and "calories" in df.columns:
        mask &= df["calories"] <= calories_le
    if sugar_g_le is not None:
        col = get_sugar_or_carb_column(df)
        if col is not None:
            mask &= df[col] <= sugar_g_le
    if fat_g_le is not None and "fat_g" in df.columns:
        mask &= df["fat_g"] <= fat_g_le
    if protein_g_ge is not None and "protein_g" in df.columns:
        mask &= df["protein_g"] >= protein_g_ge
    if sodium_mg_le is not None:
        col = get_sodium_column(df)
        if col is not None:
            mask &= df[col] <= sodium_mg_le
    if caffeine_mg_gt is not None and "caffeine_mg" in df.columns:
        mask &= df["caffeine_mg"] > caffeine_mg_gt
    if name_contains:
        col = get_item_column(df)
        if col is not None:
            mask &= df[col].astype(str).str.contains(name_contains, case=False, na=False)
    return df[mask]
