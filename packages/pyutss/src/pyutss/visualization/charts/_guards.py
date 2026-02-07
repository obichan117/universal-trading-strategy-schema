"""Dependency guard checks for optional visualization libraries."""


def _check_matplotlib() -> None:
    """Check if matplotlib is available."""
    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install matplotlib"
        )


def _check_seaborn() -> None:
    """Check if seaborn is available."""
    try:
        import seaborn as sns  # noqa: F401
    except ImportError:
        raise ImportError(
            "seaborn is required for heatmaps. "
            "Install it with: pip install seaborn"
        )
