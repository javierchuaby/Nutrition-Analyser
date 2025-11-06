"""Data loader for Starbucks nutrition CSVs with reliable normalization.

This module provides functions to load and normalize Starbucks drinks and food
CSVs according to a strict specification, ensuring accurate item-level nutrition
data for filters, stats, and lookups.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Normalized column mappings from spec
COLUMN_RENAME_MAP = {
    "Calories": "calories",
    "Fat (g)": "fat_g",
    "Carb. (g)": "carbs_g",
    "Fiber (g)": "fiber_g",
    "Protein": "protein_g",
    "Protein (g)": "protein_g",
    "Sodium": "sodium",
}

# Expected columns per dataset
DRINKS_COLUMNS = ["item_name", "calories", "fat_g", "carbs_g", "fiber_g", "protein_g", "sodium"]
FOOD_COLUMNS = ["item_name", "calories", "fat_g", "carbs_g", "fiber_g", "protein_g"]

# Numeric columns to coerce
NUMERIC_COLUMNS = ["calories", "fat_g", "carbs_g", "fiber_g", "protein_g", "sodium"]


def _strip_whitespace(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Strip leading/trailing whitespace from specified column."""
    if column in df.columns:
        df = df.copy()
        df[column] = df[column].astype(str).str.strip()
    return df


def _collapse_internal_spaces(text: str) -> str:
    """Collapse multiple internal spaces to single space."""
    return re.sub(r"\s+", " ", text).strip()


def _normalize_item_name(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize item_name: strip whitespace and collapse internal spaces."""
    df = df.copy()
    if "item_name" in df.columns:
        df["item_name"] = df["item_name"].astype(str).str.strip()
        df["item_name"] = df["item_name"].apply(_collapse_internal_spaces)
    return df


def _dedupe_by_item_name(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate rows by item_name using first_non_null_per_column strategy.
    
    Strategy: For duplicate item_name rows, keep the first non-null value
    per column, then keep the first row overall as tie-breaker.
    """
    if "item_name" not in df.columns:
        return df
    
    df = df.copy()
    
    # Group by item_name (case-insensitive for matching)
    df["_item_name_lower"] = df["item_name"].astype(str).str.lower()
    
    # Find duplicates (case-insensitive)
    duplicate_mask = df.duplicated(subset=["_item_name_lower"], keep=False)
    
    if not duplicate_mask.any():
        df = df.drop(columns=["_item_name_lower"])
        return df
    
    logger.info("Found %d rows with duplicate item_name (case-insensitive)", duplicate_mask.sum())
    
    # For each group of duplicates, merge non-null values
    deduplicated_rows = []
    seen_names = set()
    
    for idx, row in df.iterrows():
        name_lower = row["_item_name_lower"]
        
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            # If this is a duplicate, we need to merge with others
            if duplicate_mask.loc[idx]:
                # Get all rows with same name (case-insensitive)
                same_name_mask = df["_item_name_lower"] == name_lower
                same_name_rows = df[same_name_mask]
                
                # Merge: first non-null per column
                merged_row = row.copy()
                for col in df.columns:
                    if col in ["_item_name_lower"]:
                        continue
                    if pd.isna(merged_row[col]) or merged_row[col] == "":
                        # Find first non-null value in same_name_rows
                        for _, other_row in same_name_rows.iterrows():
                            if not pd.isna(other_row[col]) and other_row[col] != "":
                                merged_row[col] = other_row[col]
                                break
                
                deduplicated_rows.append(merged_row)
            else:
                deduplicated_rows.append(row)
    
    result_df = pd.DataFrame(deduplicated_rows)
    result_df = result_df.drop(columns=["_item_name_lower"])
    
    logger.info("Deduplicated to %d unique item_name rows", len(result_df))
    return result_df


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns according to spec."""
    df = df.copy()
    df = df.rename(columns=COLUMN_RENAME_MAP)
    return df


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce specified columns to numeric with error handling.
    
    Handles commas and ensures NaN (not zero) for missing values.
    Always produces float64 dtype to match spec requirements.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            # Convert to string first, then strip commas and convert to numeric
            df[col] = df[col].astype(str).str.replace(",", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Ensure float64 dtype (not Int64 or other nullable integer types)
            if not pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].astype("float64")
    return df


def _validate_dataset(df: pd.DataFrame, dataset_type: str) -> None:
    """Validate dataset according to spec requirements."""
    # Assert item_name is non-empty after trimming
    if "item_name" in df.columns:
        empty_names = df["item_name"].astype(str).str.strip().eq("")
        if empty_names.any():
            logger.warning("Found %d rows with empty item_name after trimming", empty_names.sum())
    
    # Report counts of rows with any missing numeric fields
    numeric_cols = [c for c in NUMERIC_COLUMNS if c in df.columns]
    if numeric_cols:
        rows_with_missing = df[numeric_cols].isna().any(axis=1).sum()
        logger.info("Rows with any missing numeric fields: %d", rows_with_missing)
        
        # Count rows with all nutrient fields missing (sparse data)
        all_missing = df[numeric_cols].isna().all(axis=1).sum()
        if all_missing > 0:
            logger.info("Rows with all nutrient fields missing (sparse): %d", all_missing)
    
    # Ensure all numeric columns are float dtype after coercion
    # (This is a verification step; _coerce_numeric should already ensure float64)
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_float_dtype(df[col]):
                logger.warning("Column %s is not float dtype, converting", col)
                df[col] = df[col].astype("float64")
    
    # Verify no leading/trailing spaces remain in item_name
    if "item_name" in df.columns:
        has_leading_trailing = (
            df["item_name"].astype(str).str.startswith(" ") |
            df["item_name"].astype(str).str.endswith(" ")
        ).any()
        if has_leading_trailing:
            logger.warning("Found item_name values with leading/trailing spaces")
    
    # Verify duplicate item_name rows have been resolved
    if "item_name" in df.columns:
        # Case-insensitive check
        duplicates = df["item_name"].astype(str).str.lower().duplicated()
        if duplicates.any():
            logger.warning("Found %d duplicate item_name rows (case-insensitive)", duplicates.sum())


def load_drinks(path: str) -> pd.DataFrame:
    """Load and normalize drinks CSV according to spec.
    
    Handles common CSV formatting issues:
    - Missing data (handled via na_values)
    - Inconsistent entries (normalized during processing)
    - Malformed rows (skipped with warnings)
    - Extra columns (ignored)
    - Missing columns (handled gracefully)
    - Empty files (raises informative error)
    
    Args:
        path: Path to drinks CSV file
        
    Returns:
        Normalized DataFrame with columns: item_name, calories, fat_g, carbs_g,
        fiber_g, protein_g, sodium
        
    Raises:
        FileNotFoundError: If file doesn't exist
        pd.errors.EmptyDataError: If file is empty
        ValueError: If file cannot be parsed
    """
    import os
    
    logger.info("Loading drinks CSV from %s", path)
    
    # Check if file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Drinks CSV file not found: {path}")
    
    # Check if file is empty
    if os.path.getsize(path) == 0:
        raise pd.errors.EmptyDataError(f"Drinks CSV file is empty: {path}")
    
    # Read CSV with robust error handling for common issues
    expected_cols = ["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein", "Sodium"]
    
    try:
        # Try reading with expected column names first
        df = pd.read_csv(
            path,
            encoding="utf-8",
            header=0,
            names=expected_cols,
            na_values=["-", "", "NA", "N/A", "n/a", "null", "NULL", "None"],
            keep_default_na=True,
            dtype=None,
            skipinitialspace=False,
            on_bad_lines="warn",
            engine="python",
            sep=",",
            quotechar='"',
            skip_blank_lines=True,
        )
    except (ValueError, pd.errors.ParserError) as e:
        # If column count mismatch, read without names and map columns
        if "Number of passed names" in str(e) or "did not match" in str(e):
            logger.info("CSV column structure doesn't match expected. Attempting flexible parsing...")
            try:
                # Read without specifying names to detect actual structure
                df = pd.read_csv(
                    path,
                    encoding="utf-8",
                    header=0,
                    na_values=["-", "", "NA", "N/A", "n/a", "null", "NULL", "None"],
                    keep_default_na=True,
                    dtype=str,  # Read as string first for flexibility
                    skipinitialspace=False,
                    on_bad_lines="warn",
                    engine="python",
                    sep=",",
                    quotechar='"',
                    skip_blank_lines=True,
                )
                
                # Map detected columns to expected names (case-insensitive, partial matching)
                actual_cols_lower = {col.strip().lower(): col for col in df.columns}
                col_mapping = {}
                
                for exp_col in expected_cols:
                    exp_col_lower = exp_col.lower()
                    # Try exact match first
                    if exp_col_lower in actual_cols_lower:
                        col_mapping[actual_cols_lower[exp_col_lower]] = exp_col
                    else:
                        # Try partial match
                        for act_col_lower, act_col in actual_cols_lower.items():
                            if exp_col_lower in act_col_lower or act_col_lower in exp_col_lower:
                                col_mapping[act_col] = exp_col
                                break
                
                # Rename columns
                df = df.rename(columns=col_mapping)
                
                # Add missing columns with NaN
                for exp_col in expected_cols:
                    if exp_col not in df.columns:
                        df[exp_col] = pd.NA
                        logger.warning("Missing expected column '%s', filled with NaN", exp_col)
                
                # Keep only expected columns (drop extras)
                df = df[expected_cols]
                logger.info("Successfully mapped columns to expected structure")
            except Exception as e2:
                logger.error("Failed to parse CSV with flexible column mapping: %s", e2)
                raise ValueError(f"Could not parse drinks CSV file: {e2}") from e2
        else:
            # Other parser errors, try recovery
            logger.warning("CSV parsing encountered issues: %s. Attempting recovery...", e)
            try:
                df = pd.read_csv(
                    path,
                    encoding="utf-8",
                    header=0,
                    names=expected_cols,
                    na_values=["-", "", "NA", "N/A", "n/a", "null", "NULL", "None"],
                    keep_default_na=True,
                    dtype=str,
                    skipinitialspace=False,
                    on_bad_lines="skip",
                    engine="python",
                    sep=",",
                    skip_blank_lines=True,
                )
                logger.info("Successfully recovered CSV with lenient parsing")
            except Exception as e2:
                logger.error("Failed to parse drinks CSV: %s", e2)
                raise ValueError(f"Could not parse drinks CSV file: {e2}") from e2
    except pd.errors.EmptyDataError:
        logger.error("Drinks CSV file is empty or contains no data")
        raise
    except UnicodeDecodeError as e:
        logger.warning("UTF-8 decoding failed, trying alternative encodings: %s", e)
        # Try alternative encodings
        for encoding in ["latin-1", "iso-8859-1", "cp1252"]:
            try:
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    header=0,
                    names=["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein", "Sodium"],
                    na_values=["-", "", "NA", "N/A", "n/a", "null", "NULL", "None"],
                    keep_default_na=True,
                    dtype=None,
                    skipinitialspace=False,
                    on_bad_lines="warn",
                    engine="python",
                    sep=",",
                    skip_blank_lines=True,
                )
                logger.info("Successfully loaded with %s encoding", encoding)
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        else:
            raise ValueError(f"Could not decode drinks CSV file with any encoding: {e}") from e
    
    # Handle case where DataFrame is empty
    if len(df) == 0:
        logger.warning("Drinks CSV parsed but contains no data rows")
        # Return empty DataFrame with correct columns
        df = pd.DataFrame(columns=["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein", "Sodium"])
    
    # Ensure we have all expected columns (already handled above, but double-check)
    expected_cols = ["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein", "Sodium"]
    if len(df.columns) != len(expected_cols) or set(df.columns) != set(expected_cols):
        # Final check: ensure all expected columns exist
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            logger.warning("Missing expected columns: %s. Filling with NaN", missing_cols)
            for col in missing_cols:
                df[col] = pd.NA
        
        # Keep only expected columns (drop extras)
        df = df[expected_cols]
    
    logger.info("Parsed %d rows from drinks CSV", len(df))
    
    # Normalize item_name
    df = _normalize_item_name(df)
    
    # Rename columns
    df = _rename_columns(df)
    
    # Coerce numeric columns
    df = _coerce_numeric(df, NUMERIC_COLUMNS)
    
    # Deduplicate
    df = _dedupe_by_item_name(df)
    
    # Validate
    _validate_dataset(df, "drinks")
    
    logger.info("Schema validated for drinks dataset")
    
    return df


def load_food(path: str) -> pd.DataFrame:
    """Load and normalize food CSV according to spec.
    
    Handles common CSV formatting issues:
    - Missing data (handled via na_values)
    - Inconsistent entries (normalized during processing)
    - Malformed rows (skipped with warnings)
    - Extra columns (ignored)
    - Missing columns (handled gracefully)
    - Empty files (raises informative error)
    - Encoding issues (tries multiple encodings)
    
    Args:
        path: Path to food CSV file
        
    Returns:
        Normalized DataFrame with columns: item_name, calories, fat_g, carbs_g,
        fiber_g, protein_g
        
    Raises:
        FileNotFoundError: If file doesn't exist
        pd.errors.EmptyDataError: If file is empty
        ValueError: If file cannot be parsed
    """
    import os
    
    logger.info("Loading food CSV from %s", path)
    
    # Check if file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Food CSV file not found: {path}")
    
    # Check if file is empty
    if os.path.getsize(path) == 0:
        raise pd.errors.EmptyDataError(f"Food CSV file is empty: {path}")
    
    # Read CSV with robust error handling
    # Try utf-8-sig first (per spec), then fall back to other encodings
    encodings_to_try = ["utf-8-sig", "utf-16le", "utf-8", "latin-1", "iso-8859-1", "cp1252"]
    df = None
    last_error = None
    
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                header=0,
                names=["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein (g)"],
                na_values=["", "-", "NA", "N/A", "n/a", "null", "NULL", "None"],
                keep_default_na=True,
                dtype=None,
                skipinitialspace=True,
                on_bad_lines="warn",  # Skip malformed rows with warning
                engine="python",  # More forgiving parser
                sep=",",  # Explicitly set separator
                quotechar='"',
                skip_blank_lines=True,  # Skip empty lines
            )
            if encoding != "utf-8-sig":
                logger.info("Successfully loaded food CSV with %s encoding", encoding)
            break
        except UnicodeDecodeError as e:
            last_error = e
            logger.debug("Failed to load with %s encoding: %s", encoding, e)
            continue
        except pd.errors.EmptyDataError:
            logger.error("Food CSV file is empty or contains no data")
            raise
        except pd.errors.ParserError as e:
            logger.warning("CSV parsing encountered issues with %s encoding: %s. Trying recovery...", encoding, e)
            # Try with more lenient settings
            try:
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    header=0,
                    names=["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein (g)"],
                    na_values=["", "-", "NA", "N/A", "n/a", "null", "NULL", "None"],
                    keep_default_na=True,
                    dtype=str,  # Read everything as string first
                    skipinitialspace=True,
                    on_bad_lines="skip",  # Skip problematic rows
                    engine="python",
                    sep=",",
                    skip_blank_lines=True,
                )
                logger.info("Successfully recovered CSV with lenient parsing (%s encoding)", encoding)
                break
            except Exception:
                continue
    
    if df is None:
        raise ValueError(f"Could not parse food CSV file with any encoding. Last error: {last_error}") from last_error
    
    # Handle case where DataFrame is empty
    if len(df) == 0:
        logger.warning("Food CSV parsed but contains no data rows")
        # Return empty DataFrame with correct columns
        df = pd.DataFrame(columns=["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein (g)"])
    
    # Handle extra columns (keep only what we need)
    expected_cols = ["item_name", "Calories", "Fat (g)", "Carb. (g)", "Fiber (g)", "Protein (g)"]
    if len(df.columns) > len(expected_cols):
        extra_cols = [c for c in df.columns if c not in expected_cols]
        logger.info("Found %d extra columns (will be ignored): %s", len(extra_cols), extra_cols)
        # Keep only expected columns
        df = df[expected_cols]
    elif len(df.columns) < len(expected_cols):
        missing_cols = [c for c in expected_cols if c not in df.columns]
        logger.warning("Missing expected columns: %s. Filling with NaN", missing_cols)
        for col in missing_cols:
            df[col] = pd.NA
    
    logger.info("Parsed %d rows from food CSV", len(df))
    
    # Normalize item_name
    df = _normalize_item_name(df)
    
    # Rename columns
    df = _rename_columns(df)
    
    # Coerce numeric columns (food doesn't have sodium)
    food_numeric = [c for c in NUMERIC_COLUMNS if c != "sodium"]
    df = _coerce_numeric(df, food_numeric)
    
    # Deduplicate
    df = _dedupe_by_item_name(df)
    
    # Validate
    _validate_dataset(df, "food")
    
    logger.info("Schema validated for food dataset")
    
    return df


def get_item(dataset: pd.DataFrame, item_name: str) -> dict[str, Any] | None:
    """Get a single item by exact, case-insensitive match on item_name.
    
    Args:
        dataset: Normalized DataFrame (drinks or food)
        item_name: Item name to lookup (case-insensitive)
        
    Returns:
        Dictionary of normalized record, or None if not found
    """
    if "item_name" not in dataset.columns:
        return None
    
    # Case-insensitive match
    mask = dataset["item_name"].astype(str).str.lower() == item_name.lower()
    matches = dataset[mask]
    
    if len(matches) == 0:
        return None
    
    # Return first match as dict
    record = matches.iloc[0].to_dict()
    
    # Convert numpy types to native Python types for JSON serialization
    for key, value in record.items():
        if pd.isna(value):
            record[key] = None
        elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
            record[key] = float(value) if pd.notna(value) else None
        elif hasattr(value, "item"):  # numpy scalar
            record[key] = value.item()
    
    return record


def filter_items(dataset: pd.DataFrame, criteria: dict[str, Any]) -> pd.DataFrame:
    """Filter items based on criteria.
    
    Args:
        dataset: Normalized DataFrame (drinks or food)
        criteria: Dictionary with filter criteria:
            - max_calories: Maximum calories
            - max_sugar_g: Maximum sugar (not in spec, but may be in future)
            - max_fat_g: Maximum fat
            - min_protein_g: Minimum protein
            - max_sodium: Maximum sodium
            - name_substring: Substring to match in item_name (case-insensitive)
            
    Returns:
        Filtered DataFrame
    """
    df = dataset.copy()
    mask = pd.Series([True] * len(df), index=df.index)
    
    if "max_calories" in criteria and criteria["max_calories"] is not None:
        if "calories" in df.columns:
            mask &= df["calories"] <= criteria["max_calories"]
    
    if "max_fat_g" in criteria and criteria["max_fat_g"] is not None:
        if "fat_g" in df.columns:
            mask &= df["fat_g"] <= criteria["max_fat_g"]
    
    if "min_protein_g" in criteria and criteria["min_protein_g"] is not None:
        if "protein_g" in df.columns:
            mask &= df["protein_g"] >= criteria["min_protein_g"]
    
    if "max_sodium" in criteria and criteria["max_sodium"] is not None:
        if "sodium" in df.columns:
            mask &= df["sodium"] <= criteria["max_sodium"]
    
    if "name_substring" in criteria and criteria["name_substring"]:
        if "item_name" in df.columns:
            mask &= df["item_name"].astype(str).str.contains(
                criteria["name_substring"], case=False, na=False
            )
    
    return df[mask]


def get_columns(dataset: pd.DataFrame) -> list[str]:
    """Get list of available normalized columns for dataset.
    
    Args:
        dataset: Normalized DataFrame (drinks or food)
        
    Returns:
        List of column names
    """
    return list(dataset.columns)
