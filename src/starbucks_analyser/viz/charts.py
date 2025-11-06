from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def bar_top_items(df: pd.DataFrame, column: str, top_n: int, out_path: str) -> str:
    """Create a bar chart of top N items by a given column. Used by CLI."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cols = [column]
    # Support both new "item_name" and legacy "item" column names
    if "item_name" in df.columns:
        cols = ["item_name", column]
    elif "item" in df.columns:
        cols = ["item", column]
    sub = df[cols].dropna(subset=[column]).sort_values(by=column, ascending=False).head(top_n)
    index_col = "item_name" if "item_name" in sub.columns else ("item" if "item" in sub.columns else sub.index)
    ax = sub.set_index(index_col).plot(
        kind="bar", legend=False, title=f"Top {top_n} by {column}"
    )
    ax.set_ylabel(column)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path


def grouped_means_bar(
    drinks: pd.DataFrame,
    food: pd.DataFrame,
    nutrients: list[str],
    out_path: str,
) -> str:
    """Create a grouped bar chart comparing means between drinks and food. Used by CLI."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    data = []
    labels = []
    for label, df in ("drinks", drinks), ("food", food):
        labels.append(label)
        means = []
        for n in nutrients:
            col = n
            if n == "sugar_g" and n not in df.columns and "carbs_g" in df.columns:
                col = "carbs_g"
            # Support both new "sodium" and legacy "sodium_mg" column names
            elif n == "sodium" and n not in df.columns and "sodium_mg" in df.columns:
                col = "sodium_mg"
            elif n == "sodium_mg" and n not in df.columns and "sodium" in df.columns:
                col = "sodium"
            means.append(float(df[col].mean()) if col in df.columns else 0.0)
        data.append(means)
    # Plot grouped bars
    x = np.arange(len(nutrients))
    width = 0.35
    fig, ax = plt.subplots()
    ax.bar(x - width / 2, data[0], width, label="drinks")
    ax.bar(x + width / 2, data[1], width, label="food")
    ax.set_xticks(x)
    ax.set_xticklabels(nutrients)
    ax.set_ylabel("mean")
    ax.set_title("Mean nutrients: drinks vs food")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path


def overall_average_comparisons(
    drinks_desc: dict[str, Any],
    food_desc: dict[str, Any],
    out_path: str,
) -> str:
    """Create a bar chart showing overall average comparisons (matching summary structure)."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    metrics = ["calories", "fat_g", "carbs_g", "protein_g", "fiber_g"]
    drinks_means = drinks_desc.get("means", {})
    food_means = food_desc.get("means", {})
    
    drinks_values = []
    food_values = []
    differences = []
    metric_labels = []
    
    for metric in metrics:
        if metric in drinks_means and metric in food_means:
            drinks_val = drinks_means[metric]
            food_val = food_means[metric]
            diff = drinks_val - food_val
            
            drinks_values.append(drinks_val)
            food_values.append(food_val)
            differences.append(abs(diff))
            metric_labels.append(metric.replace("_", " ").title())
    
    # Add fat-to-protein ratio if available
    if "fat_to_protein_ratio" in drinks_means and "fat_to_protein_ratio" in food_means:
        drinks_values.append(drinks_means["fat_to_protein_ratio"])
        food_values.append(food_means["fat_to_protein_ratio"])
        differences.append(abs(drinks_means["fat_to_protein_ratio"] - food_means["fat_to_protein_ratio"]))
        metric_labels.append("Fat/Protein Ratio")
    
    if not metric_labels:
        # Create empty chart if no data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title("Overall Average Comparisons")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path
    
    x = np.arange(len(metric_labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width / 2, drinks_values, width, label="Drinks", color="#2E86AB", edgecolor="white", linewidth=1.5)
    bars2 = ax.bar(x + width / 2, food_values, width, label="Food", color="#F18F01", edgecolor="white", linewidth=1.5)
    
    # Add value labels on bars with appropriate formatting
    max_val = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    label_offset = max_val * 0.02  # 2% of max value for label offset
    
    for i, (drinks_val, food_val) in enumerate(zip(drinks_values, food_values)):
        # Format based on value size
        if drinks_val >= 100:
            drinks_label = f"{drinks_val:.0f}"
        elif drinks_val >= 10:
            drinks_label = f"{drinks_val:.1f}"
        else:
            drinks_label = f"{drinks_val:.2f}"
        
        if food_val >= 100:
            food_label = f"{food_val:.0f}"
        elif food_val >= 10:
            food_label = f"{food_val:.1f}"
        else:
            food_label = f"{food_val:.2f}"
        
        # Position labels above bars
        ax.text(i - width / 2, drinks_val + label_offset, drinks_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#2E86AB")
        ax.text(i + width / 2, food_val + label_offset, food_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#F18F01")
    
    ax.set_xlabel("Metric", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Value", fontsize=12, fontweight="bold")
    ax.set_title("Overall Average Comparisons", fontsize=14, fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, rotation=45, ha="right", fontsize=10)
    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    
    # Ensure y-axis starts from 0 and shows smaller values clearly
    y_max = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    ax.set_ylim(bottom=0, top=y_max * 1.15)  # Add 15% padding at top for labels
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    return out_path


def direct_comparisons(
    drinks_desc: dict[str, Any],
    food_desc: dict[str, Any],
    comparisons: dict[str, Any],
    out_path: str,
) -> str:
    """Create a chart showing direct comparisons between drinks and food (matching summary structure)."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Extract comparison data
    comparison_labels = []
    drinks_values = []
    food_values = []
    differences = []
    
    # Map of comparison keys to display labels
    comparison_map = {
        "avg_calories_drinks_vs_food": "Average Calories",
        "avg_sugar_drinks_vs_food": "Average Sugar",
        "avg_fat_g_drinks_vs_food": "Average Fat (g)",
        "avg_protein_g_drinks_vs_food": "Average Protein (g)",
        "avg_carbs_g_drinks_vs_food": "Average Carbs (g)",
        "avg_sodium_drinks_vs_food": "Average Sodium",
        "fat_to_protein_ratio_drinks_vs_food": "Fat-to-Protein Ratio",
    }
    
    for key, label in comparison_map.items():
        if key in comparisons:
            comp_data = comparisons[key]
            if isinstance(comp_data, dict):
                drinks_val = comp_data.get("drinks")
                food_val = comp_data.get("food")
                diff = comp_data.get("difference", 0)
                
                if drinks_val is not None and food_val is not None:
                    comparison_labels.append(label)
                    drinks_values.append(drinks_val)
                    food_values.append(food_val)
                    differences.append(abs(diff))
    
    if not comparison_labels:
        # Fallback: use direct means if comparisons not available
        drinks_means = drinks_desc.get("means", {})
        food_means = food_desc.get("means", {})
        
        metrics = ["calories", "fat_g", "carbs_g", "protein_g"]
        for metric in metrics:
            if metric in drinks_means and metric in food_means:
                comparison_labels.append(metric.replace("_", " ").title())
                drinks_values.append(drinks_means[metric])
                food_values.append(food_means[metric])
                differences.append(abs(drinks_means[metric] - food_means[metric]))
    
    if not comparison_labels:
        # Create empty chart if no data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title("Direct Comparisons")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path
    
    x = np.arange(len(comparison_labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width / 2, drinks_values, width, label="Drinks", color="#2E86AB", edgecolor="white", linewidth=1.5)
    bars2 = ax.bar(x + width / 2, food_values, width, label="Food", color="#F18F01", edgecolor="white", linewidth=1.5)
    
    # Add value labels on bars with appropriate formatting
    max_val = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    label_offset = max_val * 0.02  # 2% of max value for label offset
    
    for i, (drinks_val, food_val) in enumerate(zip(drinks_values, food_values)):
        # Format based on value size
        if drinks_val >= 100:
            drinks_label = f"{drinks_val:.0f}"
        elif drinks_val >= 10:
            drinks_label = f"{drinks_val:.1f}"
        else:
            drinks_label = f"{drinks_val:.2f}"
        
        if food_val >= 100:
            food_label = f"{food_val:.0f}"
        elif food_val >= 10:
            food_label = f"{food_val:.1f}"
        else:
            food_label = f"{food_val:.2f}"
        
        # Position labels above bars
        ax.text(i - width / 2, drinks_val + label_offset, drinks_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#2E86AB")
        ax.text(i + width / 2, food_val + label_offset, food_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#F18F01")
    
    ax.set_xlabel("Comparison", fontsize=12, fontweight="bold")
    ax.set_ylabel("Value", fontsize=12, fontweight="bold")
    ax.set_title("Direct Comparisons", fontsize=14, fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_labels, rotation=45, ha="right", fontsize=10)
    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    
    # Ensure y-axis starts from 0 and shows smaller values clearly
    y_max = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    ax.set_ylim(bottom=0, top=y_max * 1.15)  # Add 15% padding at top for labels
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    return out_path


def extremes_comparison(
    drinks: pd.DataFrame,
    food: pd.DataFrame,
    out_path: str,
) -> str:
    """Create a chart showing extreme values (highest/lowest) for drinks and food."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Determine item_name column (check drinks first, then food)
    item_name_col = "item_name"
    if len(drinks) > 0:
        if "item_name" in drinks.columns:
            item_name_col = "item_name"
        elif "item" in drinks.columns:
            item_name_col = "item"
    elif len(food) > 0:
        if "item_name" in food.columns:
            item_name_col = "item_name"
        elif "item" in food.columns:
            item_name_col = "item"
    
    # Helper function to safely get max value
    def safe_max_idx(df: pd.DataFrame, col: str) -> pd.Series | None:
        """Safely get the row with maximum value in a column, handling empty/NaN cases."""
        if len(df) == 0 or col not in df.columns:
            return None
        # Drop NaN values and check if any remain
        non_null = df[col].dropna()
        if len(non_null) == 0:
            return None
        try:
            return df.loc[non_null.idxmax()]
        except (ValueError, KeyError):
            return None
    
    # Find extremes
    extremes_data = []
    
    # Highest calories
    if len(drinks) > 0 and "calories" in drinks.columns:
        drinks_max_cal = safe_max_idx(drinks, "calories")
        if drinks_max_cal is not None:
            extremes_data.append(("Highest Calories", drinks_max_cal[item_name_col], drinks_max_cal["calories"], "Drinks"))
    if len(food) > 0 and "calories" in food.columns:
        food_max_cal = safe_max_idx(food, "calories")
        if food_max_cal is not None:
            extremes_data.append(("Highest Calories", food_max_cal[item_name_col], food_max_cal["calories"], "Food"))
    
    # Highest fat
    if len(drinks) > 0 and "fat_g" in drinks.columns:
        drinks_max_fat = safe_max_idx(drinks, "fat_g")
        if drinks_max_fat is not None:
            extremes_data.append(("Highest Fat", drinks_max_fat[item_name_col], drinks_max_fat["fat_g"], "Drinks"))
    if len(food) > 0 and "fat_g" in food.columns:
        food_max_fat = safe_max_idx(food, "fat_g")
        if food_max_fat is not None:
            extremes_data.append(("Highest Fat", food_max_fat[item_name_col], food_max_fat["fat_g"], "Food"))
    
    # Highest carbs
    if len(drinks) > 0 and "carbs_g" in drinks.columns:
        drinks_max_carb = safe_max_idx(drinks, "carbs_g")
        if drinks_max_carb is not None:
            extremes_data.append(("Highest Carbs", drinks_max_carb[item_name_col], drinks_max_carb["carbs_g"], "Drinks"))
    if len(food) > 0 and "carbs_g" in food.columns:
        food_max_carb = safe_max_idx(food, "carbs_g")
        if food_max_carb is not None:
            extremes_data.append(("Highest Carbs", food_max_carb[item_name_col], food_max_carb["carbs_g"], "Food"))
    
    # Handle empty extremes_data - create an empty chart
    if not extremes_data:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data available for extremes comparison", 
                ha="center", va="center", fontsize=14)
        ax.set_title("Extremes (Drink and Food Comparisons)", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        return out_path
    
    # Create grouped bar chart
    categories = sorted(set([e[0] for e in extremes_data]))
    drinks_values = []
    food_values = []
    
    for cat in categories:
        drinks_val = next((e[2] for e in extremes_data if e[0] == cat and e[3] == "Drinks"), 0)
        food_val = next((e[2] for e in extremes_data if e[0] == cat and e[3] == "Food"), 0)
        drinks_values.append(drinks_val)
        food_values.append(food_val)
    
    x = np.arange(len(categories))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width / 2, drinks_values, width, label="Drinks", color="#2E86AB", edgecolor="white", linewidth=1.5)
    bars2 = ax.bar(x + width / 2, food_values, width, label="Food", color="#F18F01", edgecolor="white", linewidth=1.5)
    
    # Add value labels on bars with appropriate formatting
    max_val = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    label_offset = max_val * 0.02  # 2% of max value for label offset
    
    for i, (drinks_val, food_val) in enumerate(zip(drinks_values, food_values)):
        # Format based on value size
        if drinks_val >= 100:
            drinks_label = f"{drinks_val:.0f}"
        elif drinks_val >= 10:
            drinks_label = f"{drinks_val:.1f}"
        else:
            drinks_label = f"{drinks_val:.2f}"
        
        if food_val >= 100:
            food_label = f"{food_val:.0f}"
        elif food_val >= 10:
            food_label = f"{food_val:.1f}"
        else:
            food_label = f"{food_val:.2f}"
        
        # Position labels above bars
        ax.text(i - width / 2, drinks_val + label_offset, drinks_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#2E86AB")
        ax.text(i + width / 2, food_val + label_offset, food_label,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#F18F01")
    
    ax.set_xlabel("Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Value", fontsize=12, fontweight="bold")
    ax.set_title("Extremes Comparisons", fontsize=14, fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=10)
    ax.legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    
    # Ensure y-axis starts from 0 and shows smaller values clearly
    y_max = max(max(drinks_values) if drinks_values else [0], max(food_values) if food_values else [0])
    if y_max > 0:
        ax.set_ylim(bottom=0, top=y_max * 1.15)  # Add 15% padding at top for labels
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    return out_path
