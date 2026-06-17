"""Statistics helpers for club match and player performance data."""

import pandas as pd
import numpy as np


def compute_home_away_record(
    singles_df: pd.DataFrame,
    doubles_df: pd.DataFrame,
    by_phase: bool = True,
) -> tuple[dict, pd.DataFrame]:
    """
    Compute home/away performance records for the club.

    Singles and doubles are combined together. Each row in the input
    DataFrames is considered as one match.

    Parameters
    ----------
    singles_df : pd.DataFrame
        Singles matches. Must contain:
        - wins (bool)
        - at_home (bool)
        - team_id
        - idx_phase (if by_phase=True)

    doubles_df : pd.DataFrame
        Doubles matches. Must contain:
        - wins (bool)
        - at_home (bool)
        - team_id
        - idx_phase (if by_phase=True)

    by_phase : bool, default=True
        If True, statistics are stratified by (team_id, idx_phase).
        Otherwise, they are computed only by team_id.

    Returns
    -------
    tuple
        (
            global_stats: dict,
            team_stats: pd.DataFrame,
        )

    global_stats : dict
        {
            "home": {
                "wins": int,
                "losses": int,
                "total": int,
                "win_rate": float,
            },
            "away": {
                "wins": int,
                "losses": int,
                "total": int,
                "win_rate": float,
            },
        }

    team_stats : pd.DataFrame
        Index:
            - (team_id,) if by_phase=False
            - (team_id, idx_phase) if by_phase=True

        Columns:
            home_wins
            home_losses
            home_total
            home_win_rate
            away_wins
            away_losses
            away_total
            away_win_rate
    """
    # Keep only the required columns and combine singles + doubles
    required_cols = ["wins", "at_home", "team_id", "idx_phase"]

    matches = pd.concat(
        [
            singles_df[required_cols],
            doubles_df[required_cols],
        ],
        ignore_index=True,
    )

    #
    # Global statistics
    #
    global_stats = {}

    for location, label in [(True, "home"), (False, "away")]:
        subset = matches[matches["at_home"] == location]

        wins = int(subset["wins"].sum())
        total = len(subset)
        losses = total - wins

        global_stats[label] = {
            "wins": wins,
            "losses": losses,
            "total": total,
            "win_rate": wins / total if total > 0 else 0.0,
        }

    #
    # Team statistics
    #
    group_cols = ["team_id"]
    if by_phase:
        group_cols.append("idx_phase")

    team_stats = (
        matches.groupby(group_cols + ["at_home"])["wins"]
        .agg(
            wins="sum",
            total="count",
        )
        .assign(
            losses=lambda x: x["total"] - x["wins"],
            win_rate=lambda x: x["wins"] / x["total"],
        )
        .reset_index()
    )

    # Pivot home / away into columns
    team_stats = team_stats.pivot(
        index=group_cols,
        columns="at_home",
        values=["wins", "losses", "total", "win_rate"],
    ).fillna(0)

    # Rename columns
    team_stats.columns = [
        f"{'home' if at_home else 'away'}_{metric}"
        for metric, at_home in team_stats.columns
    ]

    # Ensure consistent column order
    expected_columns = [
        "home_wins",
        "home_losses",
        "home_total",
        "home_win_rate",
        "away_wins",
        "away_losses",
        "away_total",
        "away_win_rate",
    ]

    for col in expected_columns:
        if col not in team_stats.columns:
            team_stats[col] = 0

    team_stats = team_stats[expected_columns]

    # Convert counts to integers
    count_columns = [
        "home_wins",
        "home_losses",
        "home_total",
        "away_wins",
        "away_losses",
        "away_total",
    ]

    team_stats[count_columns] = team_stats[count_columns].astype(int)

    team_stats = team_stats.sort_index()

    return global_stats, team_stats


def compute_doubles_record(
    df: pd.DataFrame, by_phase: bool = False
) -> tuple[dict, pd.DataFrame]:
    """
    Compute the doubles record for the club.

    Parameters
    ----------
    df : pd.DataFrame
        - wins (bool)
        - team_id

    Returns
    -------
    tuple
        (
            global_stats: dict,
            team_stats: pd.DataFrame
        )

    global_stats :
        {
            "wins": int,
            "losses": int,
            "total": int,
            "win_rate": float,
        }

    team_stats :
        DataFrame indexed by team_id with columns:
        wins, losses, total, win_rate
    """
    n_wins = int(df["wins"].sum())
    n_total = len(df)
    n_losses = n_total - n_wins

    global_stats = {
        "wins": n_wins,
        "losses": n_losses,
        "total": n_total,
        "win_rate": n_wins / n_total if n_total > 0 else 0.0,
    }

    group_cols = ["team_id"]
    if by_phase:
        group_cols.append("idx_phase")

    team_stats = (
        df.groupby(group_cols)["wins"]
        .agg(
            wins="sum",
            total="count",
        )
        .assign(
            losses=lambda x: x["total"] - x["wins"],
            win_rate=lambda x: x["wins"] / x["total"],
        )[["wins", "losses", "total", "win_rate"]]
        .astype({"wins": int, "losses": int, "total": int})
        .sort_index()
    )

    return global_stats, team_stats


def build_pair_stats(df):
    """Build statistics for home team doubles pairs.

    Returns a DataFrame with unordered pairs, match counts, wins, losses, and win rate.
    """
    tmp = df.copy()

    # unordered pair key
    tmp["pair"] = tmp.apply(
        lambda r: tuple(sorted([r["player_home_1"], r["player_home_2"]])), axis=1
    )

    # played
    played = tmp.groupby("pair").size().rename("n_played_matches")

    # wins / losses
    wins = tmp[tmp["wins"]].groupby("pair").size().rename("n_won")
    losses = tmp[~tmp["wins"]].groupby("pair").size().rename("n_lost")

    # merge
    out = pd.concat([played, wins, losses], axis=1).fillna(0)

    # proper integer types
    out = out.astype(int)

    # win percentage
    out["win_pct"] = (out["n_won"] / out["n_played_matches"] * 100).round(1)

    return out.reset_index()


def build_individual_stats(df):
    """Build individual player statistics from home team match rows."""
    stats = df.groupby("player_home").agg(
        n_played=("wins", "count"), n_won=("wins", "sum")
    )

    stats["n_lost"] = stats["n_played"] - stats["n_won"]
    stats["win_pct"] = (stats["n_won"] / stats["n_played"] * 100).round(1)

    return stats.reset_index()


def compute_perfs(df: pd.DataFrame):
    """Compute performance scores and top/bottom results based on ranking gaps."""
    df = df.copy()

    # safe numeric conversions
    df["ranking_home"] = pd.to_numeric(df["ranking_home"], errors="coerce")
    df["ranking_opponent"] = pd.to_numeric(df["ranking_opponent"], errors="coerce")
    df["wins"] = df["wins"].astype(str).str.upper().map({"TRUE": True, "FALSE": False})

    # ranking gap (positive = opponent is higher ranked)
    df["rank_gap"] = df["ranking_opponent"] - df["ranking_home"]

    # performance score:
    # - win against a better-ranked opponent => positive strong performance
    # - loss against a lower-ranked opponent => negative strong underperformance
    df["perf_score"] = np.where(
        df["wins"],
        df["rank_gap"],  # win against better-ranked = positive
        -df["rank_gap"],  # lose against lower-ranked = negative
    )

    # top performances
    best_perfs = df.sort_values("perf_score", ascending=False).head(10)

    # top underperformances
    worst_perfs = df.sort_values("perf_score", ascending=True).head(10)

    return best_perfs, worst_perfs


def analyze_home_away_performance(df):
    """Analyze home/away win rates for individual home team players."""
    df = df.copy()

    df["wins"] = df["wins"].astype(bool)
    df["at_home"] = df["at_home"].astype(bool)

    # aggregation
    agg = (
        df.groupby(["player_home", "at_home"])
        .agg(matches=("wins", "size"), wins_count=("wins", "sum"))
        .reset_index()
    )

    agg["win_rate"] = agg["wins_count"] / agg["matches"]

    # explicit pivot with controlled column names
    pivot = agg.pivot(index="player_home", columns="at_home", values="win_rate")

    # IMPORTANT: enforce both columns exist
    pivot = pivot.reindex(columns=[False, True])

    pivot.columns = ["away_win_rate", "home_win_rate"]

    # additional statistics (kept separate)
    counts = agg.pivot(index="player_home", columns="at_home", values="matches")
    counts = counts.reindex(columns=[False, True])
    counts.columns = ["matches_away", "matches_home"]

    result = pivot.join(counts).fillna(0)

    result["diff_home_away"] = result["home_win_rate"] - result["away_win_rate"]

    return result.sort_values("diff_home_away", ascending=False)
