import pandas as pd
from PIL import ImageFont
import svgwrite
from loguru import logger

import re


def normalize_cat(x):
    if pd.isna(x):
        return x

    s = str(x).upper()
    s = s.split("_")[-1]
    s = s.split("-")[-1]

    # Remove accents and non-alphanumeric characters
    s = (
        s.replace("É", "E")
        .replace("È", "E")
        .replace("Ê", "E")
        .replace("À", "A")
        .replace("Ç", "C")
    )
    s = re.sub(r"[^A-Z0-9]", "", s)

    # Special categories
    if "PR" in s or "PREREGION" in s or "PREEGION" in s:
        return "PR"

    if "PN" in s or "PRENATION" in s:
        return "PN"

    # Canonical forms already present
    m = re.search(r"\b([NRD])([1-9])\b", s)
    if m:
        return f"{m.group(1)}{m.group(2)}"

    # Verbose forms
    patterns = {
        "N": r"NAT",
        "R": r"REG",
        "D": r"DEP",
    }

    # last resort: check tail only
    tail = s[-2:]  # enough for PR / PN / N1 / R9 / D3

    if re.fullmatch(r"(PR|PN)", tail):
        return tail

    m = re.fullmatch(r"([NRD][1-9])", tail)
    if m:
        return m.group(1)

    for letter, pattern in patterns.items():
        m = re.search(pattern + r".*?([1-9])", s)
        if m:
            return f"{letter}{m.group(1)}"

        # structured match anywhere in string
    m = re.search(r"([NRD])([1-9])", s)
    if m:
        return f"{m.group(1)}{m.group(2)}"

    return ""


def filter_by_match_day(df, match_index, phase_index):
    """
    Select match data for poster generation.

    Invalid or missing scores are converted to <NA>.
    """

    df = df.query("idx_match == @match_index & idx_phase == @phase_index").copy()

    output_df = df.rename(
        columns={
            "team_name": "Equipe",
            "opponent_name": "Adversaire",
            "score_home": "Score_Equipe",
            "score_opponent": "Score_Adv",
            "division": "cat",
            "at_home": "at_home",
        }
    )[["Equipe", "Adversaire", "Score_Equipe", "Score_Adv", "cat", "at_home"]].copy()

    # Safely convert scores to nullable integers
    for col in ["Score_Equipe", "Score_Adv"]:
        output_df[col] = (
            pd.to_numeric(output_df[col], errors="coerce").round().astype("Int64")
        )

    # Normalize category strings
    output_df["cat"] = output_df["cat"].apply(normalize_cat)

    return output_df


def fit_text(draw, text, max_width, font_path="arial.ttf", max_size=40):
    """
    Returns a font that allows drawing `text` within max_width.
    """
    font_size = max_size
    while font_size > 5:  # stop if too small
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            return font
        font_size -= 1
    return ImageFont.truetype(font_path, 5)


def generate_poster(
    matchs, match_index, phase_index, output="resultats.svg", export_png=False
):
    """
    Generates an SVG poster with all matches involving THUIR for the provided index.
    - Scores displayed in neutral color
    - Thuir team highlighted: green if victory, red if defeat
    """
    # Dimensions
    largeur, hauteur = 1000, 300 + len(matchs) * 120
    rect_width, rect_height = 300, 60
    marge = 10

    # Colors
    fond_color = "#0A2846"
    vert, rouge, orange = "#00C800", "#C80000", "#e4e8ed"
    blanc = "#F0F0F0"
    texte_color = "#000000"
    neutre = "#E0E0E0"

    # creating SVG
    dwg = svgwrite.Drawing(output, size=(f"{largeur}px", f"{hauteur}px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=fond_color))

    # Background image with opacity 0.17
    dwg.add(
        dwg.image(
            href="/home/goperto/downloads/background.png",
            insert=(0, 0),
            size=(largeur, hauteur),
            opacity=0.17,
        )
    )

    # Logo club
    dwg.add(
        dwg.image(
            href="/home/goperto/downloads/logo.png", insert=(50, 20), size=(250, 245)
        )
    )

    # Title and subtitle
    dwg.add(
        dwg.text(
            f"Phase {phase_index}",
            insert=(largeur / 2, 140),
            text_anchor="middle",
            fill=orange,
            font_size="50px",
            font_family="Anton",
            font_weight="bold",
        )
    )
    dwg.add(
        dwg.text(
            f"Journée n° {match_index}",
            insert=(largeur / 2, 200),
            text_anchor="middle",
            fill=orange,
            font_size="50px",
            font_family="Anton",
            font_weight="bold",
        )
    )

    # Utility function for adapting font size
    def fit_font_size(text, max_width, max_font=40, min_font=5):
        font_size = max_font
        while font_size >= min_font:
            if 0.45 * font_size * len(text) <= max_width:
                return font_size
            font_size -= 1
        return min_font

    # Boucle sur les matchs
    y_offset = 300
    for _, row in matchs.iterrows():
        at_home = bool(row.get("at_home", True))

        # Team scores from team's perspective
        if pd.notna(row.get("Score_Equipe")):
            score_thuir = int(row.get("Score_Equipe"))
            score_adv = int(row.get("Score_Adv"))
        else:
            score_thuir = None
            score_adv = None

        # Display order: home team on the left
        if at_home:
            equipe_g = str(row["Equipe"])
            equipe_d = str(row["Adversaire"])

            score_g = score_thuir
            score_d = score_adv

            thuir_gauche = True
            thuir_droite = False
        else:
            equipe_g = str(row["Adversaire"])
            equipe_d = str(row["Equipe"])

            score_g = score_adv
            score_d = score_thuir

            thuir_gauche = False
            thuir_droite = True

        color_g = color_d = neutre
        if thuir_gauche:
            if score_g > score_d:
                color_g = vert
            elif score_g < score_d:
                color_g = rouge
        if thuir_droite:
            if score_g < score_d:
                color_d = vert
            elif score_g > score_d:
                color_d = rouge

        x_left, x_right = 100, largeur - 100

        # Left team block
        dwg.add(
            dwg.rect(
                insert=(x_left - marge, y_offset - marge),
                size=(rect_width, rect_height),
                fill=color_g,
            )
        )
        # Right team block
        dwg.add(
            dwg.rect(
                insert=(x_right - rect_width, y_offset - marge),
                size=(rect_width, rect_height),
                fill=color_d,
            )
        )

        # Font sizes adapted to team names
        font_size_g = fit_font_size(equipe_g, rect_width - 2 * marge)
        font_size_d = fit_font_size(equipe_d, rect_width - 2 * marge)
        score_font_size = 60

        # Team names text
        dwg.add(
            dwg.text(
                equipe_g,
                insert=(
                    x_left + marge,
                    y_offset + rect_height / 2 + font_size_g / 2 - 15,
                ),
                fill=blanc if thuir_gauche and color_g != neutre else texte_color,
                font_size=f"{font_size_g}px",
                font_family="Oswald",
            )
        )
        dwg.add(
            dwg.text(
                equipe_d,
                insert=(
                    x_right - marge,
                    y_offset + rect_height / 2 + font_size_d / 2 - 15,
                ),
                fill=blanc if thuir_droite and color_d != neutre else texte_color,
                font_size=f"{font_size_d}px",
                font_family="Oswald",
                text_anchor="end",
            )
        )

        # Scores (always in neutral color)
        if score_g is None and score_d is None:
            score_g = "VS"
        dwg.add(
            dwg.text(
                f"{score_g:02}",
                insert=(
                    largeur / 2 - 30,
                    y_offset + rect_height / 2 + score_font_size / 2 - 20,
                ),
                fill=neutre,
                font_size=f"{score_font_size}px",
                font_family="Bebas Neue",
                text_anchor="end",
            )
        )
        if score_d is not None:
            dwg.add(
                dwg.text(
                    f"{score_d:02}",
                    insert=(
                        largeur / 2 + 30,
                        y_offset + rect_height / 2 + score_font_size / 2 - 20,
                    ),
                    fill=neutre,
                    font_size=f"{score_font_size}px",
                    font_family="Bebas Neue",
                    text_anchor="start",
                )
            )

        categorie = str(row.get("cat", ""))  # avoid error if the key does not exist
        dwg.add(
            dwg.text(
                categorie,
                insert=(
                    x_right + 20,
                    y_offset + rect_height / 2 + score_font_size / 2 - 25,
                ),
                fill=blanc,
                font_size="40px",
                font_family="Oswald",
                text_anchor="start",
            )
        )

        y_offset += 120

    dwg.save()
    logger.success(f"✅ SVG successfully created: {output}")

    if export_png:
        import cairosvg

        png_output = str(output).replace(".svg", ".png")
        cairosvg.svg2png(url=str(output), write_to=png_output)
        logger.success(f"✅ PNG successfully created: {png_output}")
