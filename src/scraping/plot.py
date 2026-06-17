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
    """Grouped horizontal bar chart of player participation counts by phase."""

    counts = df.groupby(["player_home", "idx_phase"]).size().unstack(fill_value=0)

    # sort by total participation
    counts = counts.loc[counts.sum(axis=1).sort_values(ascending=True).index]

    fig, ax = plt.subplots(figsize=(12, max(6, len(counts) * 0.4)))

    counts.plot(kind="barh", width=0.8, ax=ax)

    ax.set_title("Participations par joueur et par phase")
    ax.set_xlabel("Nombre de participations")
    ax.set_ylabel("Joueur")

    ax.legend(title="Phase")

    plt.tight_layout()

    _save_or_show(fig, save_path)


def plot_home_away_performance(df_result, top_n=None, save_path=None):
    """Horizontal bar chart: home vs away win rates per player."""

    data = df_result.copy()

    if top_n is not None:
        data = data.head(top_n)

    # sort for better readability
    data = data.sort_values("home_win_rate")

    players = data.index.tolist()
    home = data["home_win_rate"].values
    away = data["away_win_rate"].values

    y = np.arange(len(players))
    height = 0.4

    fig, ax = plt.subplots(figsize=(10, max(6, len(players) * 0.5)))

    ax.barh(y - height / 2, home, height, label="Domicile")
    ax.barh(y + height / 2, away, height, label="Extérieur")

    ax.set_yticks(y)
    ax.set_yticklabels(players)

    ax.set_xlabel("Win rate")
    ax.set_title("Performance domicile vs extérieur par joueur")
    ax.set_xlim(0, 1)

    ax.legend()

    plt.tight_layout()

    _save_or_show(fig, save_path)


def plot_team_series(df, save_path=None):
    """Plot team ranking progression across phases and matches.

    Args:
        df: Match DataFrame.
        save_path: Optional path to save the figure as JPG (e.g. "output/chart.jpg").
                   If None, the figure is displayed interactively.
    """
    df = df.copy()

    team_div = (
        df.groupby("team_id")["division"]
        .agg(lambda x: x.dropna().iloc[0] if not x.dropna().empty else "")
        .to_dict()
    )

    def get_result(row):
        if row["score_home"] > row["score_opponent"]:
            return "win"
        elif row["score_home"] == row["score_opponent"]:
            return "draw"
        return "loss"

    df["result"] = df.apply(get_result, axis=1)

    teams = sorted(df["team_id"].unique())
    phases = [1, 2]

    ncols = 1
    nrows = len(teams) * len(phases)

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(10, 4 * nrows),
        sharex=False,
        sharey=False,
        squeeze=False,
    )

    fig.suptitle("Team ranking evolution", fontsize=16)

    row_plot = 0

    for team in teams:
        dft = df[df["team_id"] == team].sort_values(["idx_phase", "idx_match"])

        for phase in phases:
            ax = axes[row_plot, 0]
            row_plot += 1

            dfp = dft[dft["idx_phase"] == phase]

            ax.set_title(f"{format_label(team, team_div)} — Phase {phase}")

            if dfp.empty:
                ax.text(
                    0.5,
                    0.5,
                    "No matches",
                    ha="center",
                    va="center",
                )
                ax.axis("off")
                continue

            x = dfp["idx_match"].tolist()

            labels = [
                f"{opp} ({'H' if home else 'A'})"
                for opp, home in zip(
                    dfp["opponent_name"],
                    dfp["at_home"],
                )
            ]

            # Plot lines
            ax.plot(
                x,
                dfp["ranking_home"],
                color="green",
                label="Home Team",
            )
            ax.plot(
                x,
                dfp["ranking_opponent"],
                color="red",
                label="Opponent",
            )

            # Home team markers
            for i, row in zip(x, dfp.itertuples()):
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

            # Opponent markers
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

            if row_plot == 1:
                ax.legend()

            ymin, ymax = ax.get_ylim()

            for i, label in zip(x, labels):
                ax.text(
                    i,
                    ymin + (ymax - ymin) * 0.02,
                    label,
                    rotation=90,
                    ha="center",
                    va="bottom",
                    fontsize=12,
                    alpha=0.8,
                    color="gray",
                )

            max_match = dfp["idx_match"].max()
            all_ticks = list(range(1, max_match + 1))

            ax.set_xticks(all_ticks)
            ax.set_xticklabels([f"P{phase}-J{j}" for j in all_ticks])

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    _save_or_show(fig, save_path)


def format_label(t, team_div):
    div = team_div.get(t)
    return f"Team {t}" if not div else f"Team {t} — {div}"


def plot_team_match_matrix(df, save_path=None):
    """Team match matrix with Phase 1 and Phase 2 in separate subplots."""

    df = df.copy()

    team_div = (
        df.groupby("team_id")["division"]
        .agg(lambda x: x.dropna().iloc[0] if not x.dropna().empty else "")
        .to_dict()
    )

    df["match_key"] = (
        "P" + df["idx_phase"].astype(str) + "-J" + df["idx_match"].astype(str)
    )

    teams = sorted(df["team_id"].unique())
    phases = [1, 2]

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(max(12, 10), 1.2 * len(teams) * 2),
        sharey=True,
    )

    for ax_idx, phase in enumerate(phases):
        ax = axes[ax_idx]

        dfp = df[df["idx_phase"] == phase]

        # match order
        match_keys = (
            dfp[["idx_match", "match_key"]]
            .drop_duplicates()
            .sort_values("idx_match")["match_key"]
            .tolist()
        )

        col_map = {k: i for i, k in enumerate(match_keys)}

        ax.set_xlim(-0.5, len(match_keys) - 0.5)
        ax.set_ylim(-0.5, len(teams) - 0.5)
        ax.invert_yaxis()

        ax.set_yticks(range(len(teams)))
        ax.set_yticklabels([format_label(t, team_div) for t in teams])

        ax.set_xticks(range(len(match_keys)))
        ax.set_xticklabels([f"J{i + 1}" for i in range(len(match_keys))], rotation=90)

        ax.set_title(f"Phase {phase}")

        for i, team in enumerate(teams):
            dft = dfp[dfp["team_id"] == team]

            for row in dft.itertuples():
                if row.match_key not in col_map:
                    continue

                col = col_map[row.match_key]

                if row.score_home > row.score_opponent:
                    color = "#68876e"
                elif row.score_home == row.score_opponent:
                    color = "white"
                else:
                    color = "#ff876e"

                ax.add_patch(
                    plt.Rectangle(
                        (col - 0.5, i - 0.5),
                        1,
                        1,
                        facecolor=color,
                        edgecolor="black",
                    )
                )

                sign = "+" if row.ranking_home > row.ranking_opponent else "—"

                ax.text(
                    col,
                    i,
                    sign,
                    ha="center",
                    va="center",
                    fontsize=18,
                    fontweight="bold",
                )

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
                )

    axes[0].set_title("Phase 1")
    axes[1].set_title("Phase 2")

    plt.tight_layout()
    _save_or_show(fig, save_path)
