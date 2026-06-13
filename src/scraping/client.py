"""FFTT scraping utilities for Thuir team data.

This module provides a client for fetching FFTT match pages, parsing the
match structure, and converting scraped HTML into pandas DataFrames.
"""

import json
import os
import time
import re
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from loguru import logger


def _load_lid(config_path=None):
    """Load the FFTT login identifier from local configuration.

    If no config_path is provided, this function looks for a file named
    .fftt_config in the repository root.
    """
    if config_path is None:
        config_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", ".fftt_config")
        )

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Missing FFTT client config file: {config_path}")

    with open(config_path, "r", encoding="utf-8") as handle:
        try:
            config = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in FFTT client config file: {config_path}"
            ) from exc

    lid = config.get("lid")
    if not lid:
        raise ValueError(
            f"FFTT client config file must contain a 'lid' value: {config_path}"
        )

    return lid


class FFTTClient:
    """Client for scraping FFTT match pages and parsing Thuir team results.

    The client can read authentication cookies from a local config file when a
    cookie set is not provided explicitly.
    """

    def __init__(self, cookies=None, sleep=None, matches=None, config_path=None):
        """Create a new FFTTClient.

        cookies: Optional cookie mapping to use for requests.
        sleep: Optional delay between HTTP requests in seconds.
        matches: Optional prebuilt match list to skip initial phase scraping.
        config_path: Optional path to the local FFTT config file.
        """
        if cookies is None:
            lid = _load_lid(config_path)
            self.cookies = {"lid": lid}
        else:
            self.cookies = cookies

        self.sleep = sleep

        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.matches = matches

    # =========================================================
    # FETCH
    # =========================================================
    def _fetch(self, url):
        """Fetch a URL and return a parsed BeautifulSoup document."""
        if self.sleep:
            time.sleep(self.sleep)

        r = self.session.get(url, cookies=self.cookies)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    # =========================================================
    # BUILD MATCH INDEX (per phase)
    # =========================================================
    def _build_matches(self, soup):
        """Build a map of Thuir teams to their match page URLs for one phase."""
        matches = {}

        for pool in soup.select("ul.rounded.pool-ranking"):
            team_link = pool.select_one("a.item-container p")
            if not team_link:
                continue

            team_name = team_link.get_text(strip=True)

            if not team_name.startswith("THUIR TT"):
                continue

            matches[team_name] = [
                self._fetch("http://pingpocket.fr" + a["href"])
                for a in pool.select("li.score.arrow > a[href]")
            ]

        return matches

    # =========================================================
    # PARSE MATCH → THUIR-CENTRIC ROWS
    # =========================================================
    def _parse_match(self, soup, team_name, idx_match, idx_phase):
        """Parse one match page into Thuir-centric match, singles, and doubles rows."""
        title = soup.select_one("div.toolbar h1").get_text(strip=True)
        team_left, team_right = map(str.strip, title.split(" vs "))

        scores = soup.select_one("ul.divisionIndividualRoundMatchesPanel > li").select(
            "p.rich-button"
        )

        def safe_int(x):
            txt = x.get_text(strip=True)
            if txt == "":
                return np.nan
            try:
                return int(txt)
            except ValueError:
                return np.nan

        if len(scores) >= 2:
            score_left = safe_int(scores[0])
            score_right = safe_int(scores[1])
        elif len(scores) == 1:
            score_left = safe_int(scores[0])
            score_right = np.nan
        else:
            score_left = np.nan
            score_right = np.nan

        thuir_is_left = team_left == team_name

        score_thuir = score_left if thuir_is_left else score_right
        score_adv = score_right if thuir_is_left else score_left
        nom_eq_adv = team_right if thuir_is_left else team_left

        num_eq = re.search(r"THUIR\s*TT\s*\(?\s*(\d+)\s*\)?", team_name)
        num_eq = int(num_eq.group(1)) if num_eq else None

        # ==========================================================
        # Team composition
        # ==========================================================

        team_blocks = soup.select("div.division-grid > ul.rounded")

        if len(team_blocks) >= 2:
            left_team = team_blocks[0]
            right_team = team_blocks[1]

            def build_player_map(team_block, positions):
                players = {}

                rows = team_block.select("li.arrow")

                if not rows:
                    return players, np.nan

                try:
                    team_ranking = int(
                        rows[0].select_one("p.rich-button").get_text(strip=True)
                    )
                except Exception:
                    team_ranking = np.nan

                player_rows = rows[1:-1]

                for pos, row in zip(positions, player_rows):
                    try:
                        name = row.select_one("div.labels p").get_text(strip=True)

                        ranking = int(
                            row.select_one("p.rich-button").get_text(strip=True)
                        )

                        players[name] = {
                            "position": pos,
                            "ranking": ranking,
                        }

                    except Exception:
                        continue

                return players, team_ranking

            left_players, left_team_ranking = build_player_map(
                left_team, ["A", "B", "C", "D"]
            )

            right_players, right_team_ranking = build_player_map(
                right_team, ["W", "X", "Y", "Z"]
            )

        else:
            left_players = {}
            right_players = {}
            left_team_ranking = np.nan
            right_team_ranking = np.nan

        if thuir_is_left:
            thuir_players = left_players
            adv_players = right_players

            classement_total_thuir = left_team_ranking
            classement_total_adv = right_team_ranking

        else:
            thuir_players = right_players
            adv_players = left_players

            classement_total_thuir = right_team_ranking
            classement_total_adv = left_team_ranking

        # ==========================================================
        # Match sheet
        # ==========================================================

        panel = soup.select("ul.divisionIndividualRoundMatchesPanel")[1]

        simples = []
        doubles = []

        for li in panel.find_all("li", recursive=False):
            left = li.select_one("a.labels-fragment.left, p.labels-fragment.left")

            right = li.select_one("a.labels-fragment.right, p.labels-fragment.right")

            if not left or not right:
                continue

            left_name = left.get_text(" ", strip=True)
            right_name = right.get_text(" ", strip=True)

            left_win = bool(
                li.select_one("span.pos.left, a.labels-fragment.left span.pos")
            )

            right_win = bool(
                li.select_one("span.pos.right, a.labels-fragment.right span.pos")
            )

            is_double = " et " in left_name and " et " in right_name

            if is_double:
                winner_side = None

                if li.select_one("p.labels-fragment.left span.pos"):
                    winner_side = "left"

                elif li.select_one("p.labels-fragment.right span.pos"):
                    winner_side = "right"

                left_win = winner_side == "left"
                right_win = winner_side == "right"

            # ======================================================
            # SIMPLES
            # ======================================================

            if not is_double:
                if not thuir_is_left:
                    player_thuir = left_name
                    player_adv = right_name
                    wins = left_win
                else:
                    player_thuir = right_name
                    player_adv = left_name
                    wins = right_win

                thuir_info = thuir_players.get(
                    player_thuir, {"position": None, "ranking": np.nan}
                )

                adv_info = adv_players.get(
                    player_adv, {"position": None, "ranking": np.nan}
                )

                simples.append(
                    {
                        "player_thuir": player_thuir,
                        "position_thuir": thuir_info["position"],
                        "ranking_thuir": thuir_info["ranking"],
                        "player_adv": player_adv,
                        "position_adv": adv_info["position"],
                        "ranking_adv": adv_info["ranking"],
                        "wins": wins,
                        "num_eq_thuir": num_eq,
                        "idx_match": idx_match,
                        "idx_phase": idx_phase,
                        "at_home": thuir_is_left,
                    }
                )

            # ======================================================
            # DOUBLES
            # ======================================================

            else:
                left_split = [x.strip() for x in left_name.split(" et ")]
                right_split = [x.strip() for x in right_name.split(" et ")]

                if not thuir_is_left:
                    jt1, jt2 = left_split
                    ja1, ja2 = right_split
                    wins = left_win
                else:
                    jt1, jt2 = right_split
                    ja1, ja2 = left_split
                    wins = right_win

                doubles.append(
                    {
                        "joueur_thuir_1": jt1,
                        "joueur_thuir_2": jt2,
                        "joueur_adv_1": ja1,
                        "joueur_adv_2": ja2,
                        "wins": wins,
                        "num_eq_thuir": num_eq,
                        "idx_match": idx_match,
                        "idx_phase": idx_phase,
                        "at_home": thuir_is_left,
                    }
                )

        match = {
            "num_equipe_thuir": num_eq,
            "nom_eq_adv": nom_eq_adv,
            "score_thuir": score_thuir,
            "score_adv": score_adv,
            "classement_total_thuir": classement_total_thuir,
            "classement_total_adv": classement_total_adv,
            "idx_match": idx_match,
            "idx_phase": idx_phase,
            "at_home": thuir_is_left,
        }

        return match, simples, doubles

    # =========================================================
    # PUBLIC API (MULTI-PHASE)
    # =========================================================
    def scrape_thuir(self, base_url, phases=(1, 2)):
        """Scrape the Thuir team pages for the given phase URLs.

        Returns three DataFrames: matches, singles, and doubles.
        """
        all_matches = []
        all_simples = []
        all_doubles = []

        if self.matches is None:
            self.matches = []
            for idx_phase in phases:
                url = f"{base_url}{idx_phase}"
                logger.info(f"Scraping phase {idx_phase}: {url}")

                soup = self._fetch(url)
                self.matches.append(self._build_matches(soup))

        for idx_phase in phases:
            for team_name, team_matches in self.matches[idx_phase - 1].items():
                for idx_match, html in enumerate(team_matches, start=1):
                    match, simples, doubles = self._parse_match(
                        html, team_name, idx_match, idx_phase
                    )
                    all_matches.append(match)
                    all_simples.extend(simples)
                    all_doubles.extend(doubles)

        return (
            pd.DataFrame(all_matches),
            pd.DataFrame(all_simples),
            pd.DataFrame(all_doubles),
        )
