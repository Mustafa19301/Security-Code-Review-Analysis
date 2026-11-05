from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent


DATA_FILES = {
    "github_final": (
        "data/processed/final_security.csv"
    ),

    "github_model_comparison": (
        "data/processed/model_comparison/"
        "complete_model_comparison.csv"
    ),

    "github_model_summary": (
        "data/processed/interpretation_outputs/"
        "final_model_summary.csv"
    ),

    "gerrit_final": (
        "data/gerrit/couchbase_java_client/processed/"
        "finalized_gerrit.csv"
    ),

    "gerrit_features": (
        "data/gerrit/couchbase_java_client/features/"
        "gerrit_structured_features.csv"
    ),

    "gerrit_model_comparison": (
        "data/gerrit/couchbase_java_client/features/"
        "final_model_comparison_summary.csv"
    ),

    "gerrit_predictions": (
        "data/gerrit/couchbase_java_client/features/"
        "gerrit_oof_predictions.csv"
    ),

    "gerrit_false_positives": (
        "data/gerrit/couchbase_java_client/features/"
        "gerrit_false_positives.csv"
    ),

    "gerrit_false_negatives": (
        "data/gerrit/couchbase_java_client/features/"
        "gerrit_false_negatives.csv"
    ),

    "gerrit_expanded_final": (
        "data/gerrit/couchbase_java_client/processed/"
        "finalized_gerrit_intermediate_expansion.csv"
    ),

    "gerrit_expanded_modeling": (
        "data/gerrit/couchbase_java_client/processed/"
        "gerrit_modeling_intermediate_expansion.csv"
    ),

    "gerrit_expanded_predictions": (
        "results/machine_learning/gerrit_expanded/"
        "predictions/expanded_gerrit_oof_predictions.csv"
    ),

    "gerrit_expanded_false_positives": (
        "results/machine_learning/gerrit_expanded/"
        "predictions/expanded_gerrit_false_positives.csv"
    ),

    "gerrit_expanded_false_negatives": (
        "results/machine_learning/gerrit_expanded/"
        "predictions/expanded_gerrit_false_negatives.csv"
    ),
}

MODEL_FILES = {

    "gerrit_code_diff": (
        "results/machine_learning/models/"
        "gerrit_tfidf_logistic_regression.joblib"
    ),

    "gerrit_expanded_code_diff": (
        "results/machine_learning/gerrit_expanded/models/"
        "gerrit_expanded_tfidf_logistic_regression.joblib"
    ),
}

def get_data_path(file_key):
    """
    Return the absolute path for a research dataset.

    Parameters
    ----------
    file_key : str
        Dataset identifier from DATA_FILES.

    Returns
    -------
    Path
        Absolute dataset path.

    Raises
    ------
    ValueError
        If the dataset key is not registered.
    """

    if file_key not in DATA_FILES:
        raise ValueError(
            f"Unknown dataset key: {file_key}"
        )

    return PROJECT_ROOT / DATA_FILES[file_key]


@st.cache_data(show_spinner="Loading research data...")
def load_csv(file_key):
    """
    Load and cache a research CSV dataset.

    Parameters
    ----------
    file_key : str
        Dataset identifier from DATA_FILES.

    Returns
    -------
    pandas.DataFrame or None
        Loaded dataset, or None if the file does not exist.
    """

    path = get_data_path(file_key)

    if not path.exists():
        return None

    return pd.read_csv(
        path,
        low_memory=False,
    )

def get_file_information(file_key):
    """
    Return information about a research dataset.

    Parameters
    ----------
    file_key : str
        Dataset identifier from DATA_FILES.

    Returns
    -------
    dict
        File existence, relative path, and file size.
    """

    path = get_data_path(file_key)

    if not path.exists():
        return {
            "exists": False,
            "path": str(path.relative_to(PROJECT_ROOT)),
            "size_mb": None,
        }

    return {
        "exists": True,
        "path": str(path.relative_to(PROJECT_ROOT)),
        "size_mb": round(
            path.stat().st_size / (1024 * 1024),
            2,
        ),
    }


def get_model_path(model_key):
    """
    Return the absolute path for a trained machine learning model.

    Parameters
    ----------
    model_key : str
        Model identifier from MODEL_FILES.

    Returns
    -------
    Path
        Absolute model path.

    Raises
    ------
    ValueError
        If the model key is not registered.
    """

    if model_key not in MODEL_FILES:
        raise ValueError(
            f"Unknown model key: {model_key}"
        )

    return PROJECT_ROOT / MODEL_FILES[model_key]


@st.cache_resource(show_spinner="Loading machine learning model...")
def load_model(model_key):
    """
    Load and cache a trained machine learning model bundle.

    Parameters
    ----------
    model_key : str
        Model identifier from MODEL_FILES.

    Returns
    -------
    object or None
        Loaded model bundle, or None if the model file
        does not exist.
    """

    model_path = get_model_path(model_key)

    if not model_path.exists():
        return None

    return joblib.load(model_path)