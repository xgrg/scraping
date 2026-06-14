"""Statistics helpers for club match and player performance data."""

import pandas as pd
import numpy as np


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


# stats = build_pair_stats(doubles_df).sort_values(['n_played_matches','win_pct'], ascending=[False, False])


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


# compute_perfs(simples_df)[0].sort_values("rank_gap")


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


# analyze_home_away_performance(simples_df)
