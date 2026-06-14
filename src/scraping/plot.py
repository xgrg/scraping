"""Plot helpers for team match performance analysis."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def _save_or_show(fig, save_path=None):
    """Save figure to JPG if save_path is provided, otherwise display it."""
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format="jpg", dpi=150, bbox_inches="tight")
        print(f"Figure saved to {path}")
        plt.close(fig)
    else:
        plt.show()


def plot_player_participations_by_phase(df, save_path=None):
    """Plot grouped bar chart of player participation counts by phase.

    Args:
        df: Match DataFrame.
        save_path: Optional path to save the figure as JPG (e.g. "output/chart.jpg").
                   If None, the figure is displayed interactively.
    """
    # Count participations by player and phase
    counts = df.groupby(["player_home", "idx_phase"]).size().unstack(fill_value=0)

    # Sort by total participation count
    counts = counts.loc[counts.sum(axis=1).sort_values(ascending=False).index]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    counts.plot(kind="bar", width=0.8, ax=ax)

    ax.set_title("Participations par joueur et par phase")
    ax.set_xlabel("Joueur")
    ax.set_ylabel("Nombre de participations")
    ax.legend(title="Phase")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    _save_or_show(fig, save_path)


# plot_player_participations_by_phase(simples_df, save_path="output/participations.jpg")


def plot_home_away_performance(df_result, top_n=None, save_path=None):
    """Plot home vs away win rates for players.

    Args:
        df_result: DataFrame returned by analyze_home_away_performance.
        top_n: Optional — limit to the top N players by difference.
        save_path: Optional path to save the figure as JPG (e.g. "output/chart.jpg").
                   If None, the figure is displayed interactively.
    """
    data = df_result.copy()

    if top_n is not None:
        data = data.head(top_n)

    players = data.index.tolist()
    home = data["home_win_rate"].values
    away = data["away_win_rate"].values

    x = np.arange(len(players))
    width = 0.4

    fig, ax = plt.subplots(figsize=(max(10, len(players) * 0.6), 6))

    ax.bar(x - width / 2, home, width, label="Domicile")
    ax.bar(x + width / 2, away, width, label="Extérieur")

    ax.set_xticks(x)
    ax.set_xticklabels(players, rotation=45, ha="right")
    ax.set_ylabel("Win rate")
    ax.set_title("Performance domicile vs extérieur par joueur")
    ax.set_ylim(0, 1)
    ax.legend()

    plt.tight_layout()

    _save_or_show(fig, save_path)


# plot_home_away_performance(analyze_home_away_performance(simples_df), save_path="output/home_away.jpg")


def plot_team_series(df, save_path=None):
    """Plot team ranking progression across phases and matches.

    Args:
        df: Match DataFrame.
        save_path: Optional path to save the figure as JPG (e.g. "output/chart.jpg").
                   If None, the figure is displayed interactively.
    """
    df = df.copy()

    def get_result(row):
        if row["score_home"] > row["score_opponent"]:
            return "win"
        elif row["score_home"] == row["score_opponent"]:
            return "draw"
        else:
            return "loss"

    df["result"] = df.apply(get_result, axis=1)

    teams = sorted(df["team_id"].unique())

    nrows = len(teams)
    ncols = 2  # phase 1 / phase 2

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=(18, 4 * nrows), sharex=False, sharey=False
    )
    fig.suptitle("Team ranking evolution", fontsize=16)

    # If there is only one team, ensure axes remains iterable
    if nrows == 1:
        axes = [axes]

    for row_idx, team in enumerate(teams):
        dft = df[df["team_id"] == team].sort_values(["idx_phase", "idx_match"])

        for col_idx, phase in enumerate([1, 2]):
            ax = axes[row_idx][col_idx] if nrows > 1 else axes[col_idx]

            dfp = dft[dft["idx_phase"] == phase]

            ax.set_title(f"Team {team} - Phase {phase}")

            if dfp.empty:
                ax.text(0.5, 0.5, "No matches", ha="center")
                ax.axis("off")
                continue

            x = list(range(len(dfp)))

            labels = [
                f"{opp} ({'H' if home else 'A'})"
                for opp, home in zip(dfp["opponent_name"], dfp["at_home"])
            ]

            # Plot lines
            ax.plot(x, dfp["ranking_home"], color="green", label="Home Team")
            ax.plot(x, dfp["ranking_opponent"], color="red", label="Opponent")

            # Home team markers
            for i, row in enumerate(dfp.itertuples()):
                if row.score_home > row.score_opponent:
                    marker = "*"
                    size = 240
                elif row.score_home == row.score_opponent:
                    marker = "s"
                    size = 90
                else:
                    marker = "o"
                    size = 90

                ax.scatter(
                    i,
                    row.ranking_home,
                    marker=marker,
                    color="green",
                    s=size,
                    zorder=3,
                )

            # Opponent markers (discrete circles)
            ax.scatter(
                x,
                dfp["ranking_opponent"],
                marker="o",
                color="lightcoral",
                alpha=0.4,
                s=60,
                zorder=2,
            )

            ax.grid(alpha=0.3)

            if row_idx == 0 and col_idx == 0:
                ax.legend()

            for i, label in enumerate(labels):
                ax.text(
                    i,
                    ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02,
                    label,
                    rotation=90,
                    ha="center",
                    va="bottom",
                    fontsize=12,
                    alpha=0.8,
                    color="gray",
                )
            labels = [f"P{phase}-J{idx + 1}" for idx, _ in enumerate(dfp.itertuples())]
            ax.set_xticks(range(len(dfp)))
            ax.set_xticklabels(labels)

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    _save_or_show(fig, save_path)


# plot_team_series(matches_df, save_path="output/series.jpg")


def plot_team_match_matrix(df, save_path=None):
    """Plot a team match matrix showing results and opponent names per match.

    Args:
        df: Match DataFrame.
        save_path: Optional path to save the figure as JPG (e.g. "output/chart.jpg").
                   If None, the figure is displayed interactively.
    """
    df = df.copy()

    # match key
    df["match_key"] = (
        "P" + df["idx_phase"].astype(str) + "-J" + df["idx_match"].astype(str)
    )

    # global match order
    match_order = (
        df[["idx_phase", "idx_match", "match_key"]]
        .drop_duplicates()
        .sort_values(["idx_phase", "idx_match"])
        .reset_index(drop=True)
    )

    match_keys = match_order["match_key"].tolist()

    # Split phase 1 / phase 2
    phase1 = [k for k, p in zip(match_keys, match_order["idx_phase"]) if p == 1]
    phase2 = [k for k, p in zip(match_keys, match_order["idx_phase"]) if p == 2]

    # small horizontal gap between phases
    gap = [" "]  # empty column

    match_keys = phase1 + gap + phase2

    n_matches = len(match_keys)

    teams = sorted(df["team_id"].unique())
    n_teams = len(teams)

    fig, ax = plt.subplots(figsize=(max(12, n_matches), 1.2 * n_teams))

    ax.set_xlim(-0.5, n_matches - 0.5)
    ax.set_ylim(-0.5, n_teams - 0.5)

    ax.invert_yaxis()

    ax.set_yticks(range(n_teams))
    ax.set_yticklabels([f"Team {t}" for t in teams])

    ax.set_xticks(range(n_matches))
    ax.set_xticklabels(match_keys, rotation=90)

    # mapping match to column (ignoring the gap)
    match_to_col = {}
    col = 0
    for k in match_keys:
        if k == " ":
            col += 1
            continue
        match_to_col[k] = col
        col += 1

    for i, team in enumerate(teams):
        dft = df[df["team_id"] == team]

        for row in dft.itertuples():
            if row.match_key not in match_to_col:
                continue

            col = match_to_col[row.match_key]

            # result color
            if row.score_home > row.score_opponent:
                color = "#68876e"
            elif row.score_home == row.score_opponent:
                color = "white"
            else:
                color = "#ff876e"

            edge = "black"

            ax.add_patch(
                plt.Rectangle(
                    (col - 0.5, i - 0.5), 1, 1, facecolor=color, edgecolor=edge
                )
            )

            # + / -
            sign = "+" if row.ranking_home > row.ranking_opponent else "—"

            ax.text(
                col,
                i,
                f"{sign}",
                ha="center",
                va="center",
                fontsize=20,
                fontweight="bold",
                zorder=3,
            )

            # opponent name diagonally
            home_flag = "H" if row.at_home else "A"

            ax.text(
                col,
                i,
                f"{row.opponent_name} ({home_flag})",
                ha="center",
                va="center",
                rotation=45,
                fontsize=7,
                alpha=0.6,
                color="black",
                zorder=2,
            )

    # separation line between phases
    if len(phase1) > 0:
        sep = len(phase1)
        ax.axvline(sep - 0.5, color="black", linewidth=1.5, alpha=0.4)

    ax.set_title("Match Results Matrix")
    plt.tight_layout()

    _save_or_show(fig, save_path)


# plot_team_match_matrix(matches_df, save_path="output/match_matrix.jpg")
