"""Plot helpers for Thuir match performance analysis."""

import matplotlib.pyplot as plt
import numpy as np


def plot_player_participations_by_phase(df):
    """Plot grouped bar chart of Thuir player participation counts by phase."""

    # Count participations by player and phase
    counts = df.groupby(["player_thuir", "idx_phase"]).size().unstack(fill_value=0)

    # Sort by total participation count
    counts = counts.loc[counts.sum(axis=1).sort_values(ascending=False).index]

    # Plot
    ax = counts.plot(kind="bar", figsize=(12, 6), width=0.8)

    ax.set_title("Participations par joueur et par phase")
    ax.set_xlabel("Joueur")
    ax.set_ylabel("Nombre de participations")
    ax.legend(title="Phase")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


# plot_player_participations_by_phase(simples_df)


def plot_home_away_performance(df_result, top_n=None):
    """Plot home vs away win rates for Thuir players.

    df_result should be the DataFrame returned by analyze_home_away_performance.
    """

    data = df_result.copy()

    # Option: limit to the top N players by difference
    if top_n is not None:
        data = data.head(top_n)

    players = data.index.tolist()
    home = data["home_win_rate"].values
    away = data["away_win_rate"].values

    x = np.arange(len(players))
    width = 0.4

    plt.figure(figsize=(max(10, len(players) * 0.6), 6))

    plt.bar(x - width / 2, home, width, label="Domicile")
    plt.bar(x + width / 2, away, width, label="Extérieur")

    plt.xticks(x, players, rotation=45, ha="right")
    plt.ylabel("Win rate")
    plt.title("Performance domicile vs extérieur par joueur")
    plt.ylim(0, 1)
    plt.legend()

    plt.tight_layout()
    plt.show()


# plot_home_away_performance(analyze_home_away_performance(simples_df))


def plot_thuir_series(df):
    """Plot Thuir team ranking progression across phases and matches."""
    df = df.copy()

    def get_result(row):
        if row["score_thuir"] > row["score_adv"]:
            return "win"
        elif row["score_thuir"] == row["score_adv"]:
            return "draw"
        else:
            return "loss"

    df["result"] = df.apply(get_result, axis=1)

    teams = sorted(df["num_equipe_thuir"].unique())

    nrows = len(teams)
    ncols = 2  # phase 1 / phase 2

    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=(18, 4 * nrows), sharex=False, sharey=False
    )
    fig.suptitle("Évolution des classements Thuir", fontsize=16)

    # If there is only one team, ensure axes remains iterable
    if nrows == 1:
        axes = [axes]

    for row_idx, team in enumerate(teams):
        dft = df[df["num_equipe_thuir"] == team].sort_values(["idx_phase", "idx_match"])

        for col_idx, phase in enumerate([1, 2]):
            ax = axes[row_idx][col_idx] if nrows > 1 else axes[col_idx]

            dfp = dft[dft["idx_phase"] == phase]

            ax.set_title(f"Équipe {team} - Phase {phase}")

            if dfp.empty:
                ax.text(0.5, 0.5, "Aucun match", ha="center")
                ax.axis("off")
                continue

            x = list(range(len(dfp)))

            labels = [
                f"{opp} ({'D' if home else 'E'})"
                for opp, home in zip(dfp["nom_eq_adv"], dfp["at_home"])
            ]

            # Plot lines
            ax.plot(x, dfp["classement_total_thuir"], color="green", label="Thuir")
            ax.plot(x, dfp["classement_total_adv"], color="red", label="Opponent")

            # Thuir markers
            for i, row in enumerate(dfp.itertuples()):
                if row.score_thuir > row.score_adv:
                    marker = "*"
                    size = 240
                elif row.score_thuir == row.score_adv:
                    marker = "s"
                    size = 90
                else:
                    marker = "o"
                    size = 90

                ax.scatter(
                    i,
                    row.classement_total_thuir,
                    marker=marker,
                    color="green",
                    s=size,
                    zorder=3,
                )

            # Opponent markers (discrete circles)
            ax.scatter(
                x,
                dfp["classement_total_adv"],
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
    plt.show()


# plot_thuir_series(matches_df)


def plot_thuir_match_matrix(df):
    """Plot a Thuir match matrix showing results and opponent names per match."""
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

    teams = sorted(df["num_equipe_thuir"].unique())
    n_teams = len(teams)

    fig, ax = plt.subplots(figsize=(max(12, n_matches), 1.2 * n_teams))

    ax.set_xlim(-0.5, n_matches - 0.5)
    ax.set_ylim(-0.5, n_teams - 0.5)

    ax.invert_yaxis()

    ax.set_yticks(range(n_teams))
    ax.set_yticklabels([f"Équipe {t}" for t in teams])

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
        dft = df[df["num_equipe_thuir"] == team]

        for row in dft.itertuples():
            if row.match_key not in match_to_col:
                continue

            col = match_to_col[row.match_key]

            # result color
            if row.score_thuir > row.score_adv:
                color = "#68876e"
            elif row.score_thuir == row.score_adv:
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
            sign = "+" if row.classement_total_thuir > row.classement_total_adv else "—"

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
            home_flag = "D" if row.at_home else "E"

            ax.text(
                col,
                i,
                f"{row.nom_eq_adv} ({home_flag})",
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

    ax.set_title("Matrice des confrontations Thuir")
    plt.tight_layout()
    plt.show()


# plot_thuir_match_matrix(matches_df)
