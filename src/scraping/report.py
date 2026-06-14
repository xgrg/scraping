"""Excel report builder for TT club stats."""

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ── Palette ────────────────────────────────────────────────────────────────
HDR_FILL = PatternFill("solid", start_color="1E2130")
HDR_FONT = Font(name="Arial", bold=True, color="B5F542", size=10)
TITLE_FONT = Font(name="Arial", bold=True, color="1E2130", size=11)
BODY_FONT = Font(name="Arial", size=10)
WIN_FILL = PatternFill("solid", start_color="C6EFCE")
LOSS_FILL = PatternFill("solid", start_color="FFC7CE")
DRAW_FILL = PatternFill("solid", start_color="FFEB9C")
ALT_FILL = PatternFill("solid", start_color="F5F5F5")
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center")
LEFT_AL = Alignment(horizontal="left", vertical="center")


def _header_row(ws, cols, row=1):
    for col_idx, label in enumerate(cols, 1):
        cell = ws.cell(row=row, column=col_idx, value=label)
        cell.font = HDR_FONT
        cell.fill = HDR_FILL
        cell.border = BORDER
        cell.alignment = CENTER
    ws.row_dimensions[row].height = 20


def _style_cell(cell, font=None, fill=None, alignment=None):
    cell.font = font or BODY_FONT
    cell.border = BORDER
    cell.alignment = alignment or CENTER
    if fill:
        cell.fill = fill


def _autofit(ws, min_w=8, max_w=40):
    for col in ws.columns:
        length = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(
            max(length + 2, min_w), max_w
        )


def _result_fill(score_home, score_opponent):
    if score_home > score_opponent:
        return WIN_FILL
    if score_home < score_opponent:
        return LOSS_FILL
    return DRAW_FILL


def _sheet_matches(wb, df):
    ws = wb.create_sheet("Matches")
    ws.sheet_view.showGridLines = False

    cols = [
        "Team",
        "Phase",
        "Match",
        "Home/Away",
        "Opponent",
        "Score",
        "Opponent Score",
        "Ranking",
        "Opponent Ranking",
    ]
    _header_row(ws, cols)

    for i, row in enumerate(df.itertuples(), 2):
        alt = ALT_FILL if i % 2 == 0 else None
        fill = _result_fill(row.score_home, row.score_opponent)

        values = [
            f"Team {row.team_id}",
            row.idx_phase,
            row.idx_match,
            "Home" if row.at_home else "Away",
            row.opponent_name,
            row.score_home,
            row.score_opponent,
            row.ranking_home,
            row.ranking_opponent,
        ]

        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=i, column=col_idx, value=val)
            # Score columns get result color, others get alternating
            if col_idx in (6, 7):
                _style_cell(cell, fill=fill)
            else:
                _style_cell(
                    cell, fill=alt, alignment=LEFT_AL if col_idx == 5 else CENTER
                )

    ws.freeze_panes = "A2"
    _autofit(ws)

    # Summary stats
    last = len(df) + 1
    ws.cell(row=last + 2, column=1, value="Wins").font = TITLE_FONT
    ws.cell(row=last + 2, column=2, value=f'=COUNTIF(F2:F{last},">"&G2:G{last})')
    ws.cell(row=last + 3, column=1, value="Losses").font = TITLE_FONT
    ws.cell(row=last + 3, column=2, value=f'=COUNTIF(F2:F{last},"<"&G2:G{last})')
    ws.cell(row=last + 4, column=1, value="Draws").font = TITLE_FONT
    ws.cell(row=last + 4, column=2, value=f'=COUNTIF(F2:F{last},"="&G2:G{last})')


def _sheet_simples(wb, df):
    ws = wb.create_sheet("Singles")
    ws.sheet_view.showGridLines = False

    cols = [
        "Phase",
        "Match",
        "Team",
        "Player",
        "Pos.",
        "Ranking",
        "Opponent Player",
        "Opp. Pos.",
        "Opp. Ranking",
        "Result",
        "Home/Away",
    ]
    _header_row(ws, cols)

    for i, row in enumerate(df.itertuples(), 2):
        alt = ALT_FILL if i % 2 == 0 else None
        fill = WIN_FILL if row.wins else LOSS_FILL

        values = [
            row.idx_phase,
            row.idx_match,
            f"Team {row.team_id}" if row.team_id else "",
            row.player_home,
            row.position_home,
            row.ranking_home,
            row.player_opponent,
            row.position_opponent,
            row.ranking_opponent,
            "Win" if row.wins else "Loss",
            "Home" if row.at_home else "Away",
        ]

        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=i, column=col_idx, value=val)
            if col_idx == 10:
                _style_cell(cell, fill=fill)
            else:
                _style_cell(
                    cell, fill=alt, alignment=LEFT_AL if col_idx in (4, 7) else CENTER
                )

    ws.freeze_panes = "A2"
    _autofit(ws)

    # Player statistics
    last = len(df) + 1
    ws.cell(row=last + 2, column=1, value="Player Stats").font = Font(
        name="Arial", bold=True, size=11, color="1E2130"
    )

    stat_cols = ["Player", "Matches Played", "Wins", "Losses", "Win Rate"]
    for col_idx, label in enumerate(stat_cols, 1):
        cell = ws.cell(row=last + 3, column=col_idx, value=label)
        cell.font = HDR_FONT
        cell.fill = HDR_FILL
        cell.border = BORDER
        cell.alignment = CENTER

    players = df.groupby("player_home")
    stat_start = last + 4
    for s_row, (player, grp) in enumerate(players, stat_start):
        played = len(grp)
        wins = int(grp["wins"].sum())
        losses = played - wins
        ws.cell(row=s_row, column=1, value=player).font = BODY_FONT
        ws.cell(row=s_row, column=2, value=played).font = BODY_FONT
        ws.cell(row=s_row, column=3, value=wins).font = BODY_FONT
        ws.cell(row=s_row, column=4, value=losses).font = BODY_FONT
        wr_cell = ws.cell(
            row=s_row, column=5, value=f"=C{s_row}/B{s_row}" if played else 0
        )
        wr_cell.number_format = "0.0%"
        wr_cell.font = BODY_FONT
        for col_idx in range(1, 6):
            ws.cell(row=s_row, column=col_idx).border = BORDER
            ws.cell(row=s_row, column=col_idx).alignment = (
                LEFT_AL if col_idx == 1 else CENTER
            )


def _sheet_doubles(wb, df):
    ws = wb.create_sheet("Doubles")
    ws.sheet_view.showGridLines = False

    cols = [
        "Phase",
        "Match",
        "Team",
        "Player 1",
        "Player 2",
        "Opponent 1",
        "Opponent 2",
        "Result",
        "Home/Away",
    ]
    _header_row(ws, cols)

    for i, row in enumerate(df.itertuples(), 2):
        alt = ALT_FILL if i % 2 == 0 else None
        fill = WIN_FILL if row.wins else LOSS_FILL

        values = [
            row.idx_phase,
            row.idx_match,
            f"Team {row.team_id}" if row.team_id else "",
            row.player_home_1,
            row.player_home_2,
            row.player_opponent_1,
            row.player_opponent_2,
            "Win" if row.wins else "Loss",
            "Home" if row.at_home else "Away",
        ]

        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=i, column=col_idx, value=val)
            if col_idx == 8:
                _style_cell(cell, fill=fill)
            else:
                _style_cell(
                    cell,
                    fill=alt,
                    alignment=LEFT_AL if col_idx in (4, 5, 6, 7) else CENTER,
                )

    ws.freeze_panes = "A2"
    _autofit(ws)


def _sheet_summary(wb, matches_df, simples_df, doubles_df):
    ws = wb.create_sheet("Summary", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 18

    def section(row, label):
        cell = ws.cell(row=row, column=1, value=label)
        cell.font = Font(name="Arial", bold=True, size=11, color="FFFFFF")
        cell.fill = HDR_FILL
        cell.alignment = LEFT_AL
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        ws.row_dimensions[row].height = 18
        return row + 1

    def kv(row, key, value):
        k = ws.cell(row=row, column=1, value=key)
        k.font = BODY_FONT
        k.border = BORDER
        k.alignment = LEFT_AL
        v = ws.cell(row=row, column=2, value=value)
        v.font = Font(name="Arial", bold=True, size=10)
        v.border = BORDER
        v.alignment = CENTER
        return row + 1

    r = 1
    r = section(r, "Overview")

    n_teams = matches_df["team_id"].nunique()
    n_phases = matches_df["idx_phase"].nunique()
    r = kv(r, "Number of Teams", n_teams)
    r = kv(r, "Phases Played", n_phases)
    r = kv(r, "Total Matches per Team", len(matches_df))

    r += 1
    r = section(r, "Match Results by Team")
    for team in sorted(matches_df["team_id"].unique()):
        grp = matches_df[matches_df["team_id"] == team]
        wins = int((grp["score_home"] > grp["score_opponent"]).sum())
        draws = int((grp["score_home"] == grp["score_opponent"]).sum())
        lost = int((grp["score_home"] < grp["score_opponent"]).sum())
        r = kv(r, f"Team {team} (W/D/L)", f"{wins} / {draws} / {lost}")

    r += 1
    r = section(r, "Singles")
    total_s = len(simples_df)
    wins_s = int(simples_df["wins"].sum())
    r = kv(r, "Singles Matches Played", total_s)
    r = kv(r, "Wins", wins_s)
    r = kv(r, "Losses", total_s - wins_s)
    r = kv(r, "Win Rate", f"{wins_s / total_s:.1%}" if total_s else "–")

    r += 1
    r = section(r, "Doubles")
    total_d = len(doubles_df)
    wins_d = int(doubles_df["wins"].sum())
    r = kv(r, "Doubles Matches Played", total_d)
    r = kv(r, "Wins", wins_d)
    r = kv(r, "Losses", total_d - wins_d)
    r = kv(r, "Win Rate", f"{wins_d / total_d:.1%}" if total_d else "–")


def build_excel_report(matches_df, simples_df, doubles_df, output_path="report.xlsx"):
    wb = Workbook()
    wb.remove(wb.active)

    _sheet_summary(wb, matches_df, simples_df, doubles_df)
    _sheet_matches(wb, matches_df)
    _sheet_simples(wb, simples_df)
    _sheet_doubles(wb, doubles_df)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
