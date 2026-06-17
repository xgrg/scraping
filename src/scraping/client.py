"""FFTT scraping utilities for club team data.

This module provides a client for fetching FFTT match pages from the pingpocket
service, parsing the match structure, and converting scraped HTML into pandas
DataFrames.
"""

import json
import os
import time
import re
from datetime import datetime, timedelta

import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from loguru import logger

_CACHE_FILENAME = ".fftt_cache.json"
_CACHE_TTL = timedelta(days=30)


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
    """Client for scraping FFTT match pages and parsing team results.

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
            if config_path is None:
                config_path = os.path.normpath(
                    os.path.join(os.path.dirname(__file__), "..", "..", ".fftt_config")
                )

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
        self.cache_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", _CACHE_FILENAME)
        )
        self.cache = self._load_cache()

    def _load_cache(self):
        """Load the on-disk cache file if available."""
        if not os.path.exists(self.cache_path):
            return {}

        try:
            with open(self.cache_path, "r", encoding="utf-8") as handle:
                cache = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {}

        return cache

    def _save_cache(self):
        """Persist the cache to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as handle:
                json.dump(self.cache, handle, indent=2, ensure_ascii=False)
        except OSError:
            logger.warning("Unable to write FFTT cache file: %s", self.cache_path)

    def _cache_url(self, club_id, url, html_text):
        """Store a fetched HTML page into the cache for the given club."""
        club_cache = self.cache.setdefault(str(club_id), {})
        club_cache[url] = {
            "fetched_at": datetime.utcnow().isoformat(),
            "content": html_text,
        }
        self._save_cache()

    def _cached_html(self, club_id, url):
        """Return cached HTML for the given club and URL if fresh, otherwise None."""
        if club_id is None:
            return None

        club_cache = self.cache.get(str(club_id), {})
        entry = club_cache.get(url)
        if not entry:
            return None

        try:
            fetched_at = datetime.fromisoformat(entry["fetched_at"])
        except (TypeError, ValueError):
            return None

        if datetime.utcnow() - fetched_at > _CACHE_TTL:
            del club_cache[url]
            self._save_cache()
            return None

        return entry.get("content")

    def _fetch(self, url):
        """Fetch a URL and return a parsed BeautifulSoup document."""
        if self.sleep:
            time.sleep(self.sleep)

        r = self.session.get(url, cookies=self.cookies)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    def _fetch_cached(self, url, club_id=None):
        """Fetch a URL with caching enabled for a club-specific key."""
        html_text = self._cached_html(club_id, url)
        if html_text is not None:
            logger.debug(f"Using cached HTML for club {club_id}: {url}")
            return BeautifulSoup(html_text, "html.parser")

        if self.sleep:
            time.sleep(self.sleep)

        r = self.session.get(url, cookies=self.cookies)
        r.raise_for_status()
        html_text = r.text
        if club_id is not None:
            self._cache_url(club_id, url, html_text)

        return BeautifulSoup(html_text, "html.parser")

    # =========================================================
    # BUILD MATCH INDEX (per phase)
    # =========================================================
    def _build_matches(self, soup, club_id):
        """Build a map of all teams to their match page URLs for one phase.

        soup is the BeautifulSoup document of the phase page.
        """
        matches = {}

        for pool in soup.select("ul.rounded.pool-ranking"):
            if not pool.select_one("i.fa.fa-male"):
                logger.warning(f"Skipping pool without fa-male icon: {pool}")
                continue

            team_label = pool.select_one("div.labels p")
            if not team_label:
                logger.warning(f"Skipping pool without team label: {pool}")
                continue

            team_name = team_label.get_text(strip=True)

            matches[team_name] = []
            for li in pool.select("li.score"):
                a = li.select_one("a[href]") if "arrow" in li.get("class", []) else None
                if a is not None:
                    matches[team_name].append(
                        self._fetch_cached("http://pingpocket.fr" + a["href"], club_id)
                    )
                else:
                    matches[team_name].append(None)

        return matches

    # =========================================================
    # PARSE MATCH → HOME TEAM-CENTRIC ROWS
    # =========================================================
    def _parse_match(self, soup, team_name, idx_match, idx_phase):
        """Parse one match page into home team-centric match, singles, and doubles rows."""
        title = soup.select_one("div.toolbar h1").get_text(strip=True)
        team_left, team_right = map(str.strip, title.split(" vs "))

        scores = soup.select_one("ul.divisionIndividualRoundMatchesPanel > li").select(
            "p.rich-button"
        )

        def _extract_team_id(team_name: str) -> int:
            """
            Extract numeric team id from team names
            """
            match = re.search(r"(\d+)\s*$|\((\d+)\)\s*$", team_name)
            if match:
                return int(match.group(1) or match.group(2))
            raise ValueError(f"Cannot extract team_id from team_name: {team_name}")

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

        home_is_left = team_left == team_name

        score_home = score_left if home_is_left else score_right
        score_opponent = score_right if home_is_left else score_left
        opponent_name = team_right if home_is_left else team_left

        team_id = _extract_team_id(team_name)

        data_title = soup.select_one("div.daymatchdetails").get("data-title", "")
        parts = [p.strip() for p in data_title.split(",")]
        division = None

        if len(parts) > 3:
            division = parts[3]

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

        if home_is_left:
            home_players = left_players
            opponent_players = right_players

            ranking_home = left_team_ranking
            ranking_opponent = right_team_ranking

        else:
            home_players = right_players
            opponent_players = left_players

            ranking_home = right_team_ranking
            ranking_opponent = left_team_ranking

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

            if left_name == "Joueur absent" or right_name == "Joueur absent":
                logger.warning(
                    f"Skipping match with absent player: {left_name} vs {right_name}"
                )
                continue
            if left_name == " " or right_name == " ":
                logger.warning(
                    f"Skipping match with absent player: {left_name} vs {right_name}"
                )
                continue
            is_double = " et " in left_name or " et " in right_name

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
                if not home_is_left:
                    player_home = left_name
                    player_opponent = right_name
                    wins = left_win
                else:
                    player_home = right_name
                    player_opponent = left_name
                    wins = right_win

                home_info = home_players.get(
                    player_home, {"position": None, "ranking": np.nan}
                )

                opponent_info = opponent_players.get(
                    player_opponent, {"position": None, "ranking": np.nan}
                )
                simples.append(
                    {
                        "player_home": player_home,
                        "position_home": home_info["position"],
                        "ranking_home": home_info["ranking"],
                        "player_opponent": player_opponent,
                        "position_opponent": opponent_info["position"],
                        "ranking_opponent": opponent_info["ranking"],
                        "wins": wins,
                        "team_id": team_id,
                        "idx_match": idx_match,
                        "idx_phase": idx_phase,
                        "at_home": home_is_left,
                    }
                )

            # ======================================================
            # DOUBLES
            # ======================================================

            else:
                left_split = [x.strip() for x in left_name.split(" et ")]
                right_split = [x.strip() for x in right_name.split(" et ")]

                if not home_is_left:
                    player_home_1, player_home_2 = left_split
                    player_opponent_1, player_opponent_2 = right_split
                    wins = left_win
                else:
                    player_home_1, player_home_2 = right_split
                    player_opponent_1, player_opponent_2 = left_split
                    wins = right_win

                doubles.append(
                    {
                        "player_home_1": player_home_1,
                        "player_home_2": player_home_2,
                        "player_opponent_1": player_opponent_1,
                        "player_opponent_2": player_opponent_2,
                        "wins": wins,
                        "team_id": team_id,
                        "idx_match": idx_match,
                        "idx_phase": idx_phase,
                        "at_home": home_is_left,
                    }
                )

        match = {
            "team_id": team_id,
            "team_name": team_name,
            "opponent_name": opponent_name,
            "score_home": score_home,
            "score_opponent": score_opponent,
            "ranking_home": ranking_home,
            "ranking_opponent": ranking_opponent,
            "idx_match": idx_match,
            "idx_phase": idx_phase,
            "at_home": home_is_left,
            "division": division,
        }

        return match, simples, doubles

    def get_clubs(self, department) -> dict[str, str]:
        """
        Parse club HTML and return a dict of {club_name: club_id}.
        Extracts club ID from the href URL and club name from the <p> tag.
        """
        url = f"https://www.pingpocket.fr/app/fftt/comites/{department}/clubs"

        soup = self._fetch(url)

        clubs = {}

        for a_tag in soup.find_all("a", class_="item-container"):
            href = a_tag.get("href", "")
            # Extract the numeric ID from the URL path, e.g. /app/fftt/clubs/01010069
            match = re.search(r"/clubs/(\w+)", href)
            if not match:
                continue

            club_id = match.group(1)

            # The club name is in the first <p> tag inside .labels
            labels_div = a_tag.find("div", class_="labels")
            if not labels_div:
                continue

            name_tag = labels_div.find("p")
            if not name_tag:
                continue

            club_name = name_tag.get_text(strip=True)
            if club_name:
                clubs[club_name] = club_id

        return clubs

    # =========================================================
    # PUBLIC API (MULTI-PHASE)
    # =========================================================
    def scrape_club(self, club_id, phases=(1, 2)):
        """Scrape club team pages for the given phase URLs.

        Returns three DataFrames: matches, singles, and doubles.
        """
        base_url = f"https://www.pingpocket.fr/app/fftt/clubs/{club_id}/equipes/calendriers?phase="

        all_matches = []
        all_simples = []
        all_doubles = []

        if self.matches is None:
            self.matches = []
            for idx_phase in phases:
                url = f"{base_url}{idx_phase}"
                logger.info(f"Scraping phase {idx_phase}: {url}")

                soup = self._fetch_cached(url, club_id)
                self.matches.append(self._build_matches(soup, club_id))

        for idx_phase in phases:
            for team_name, team_matches in self.matches[idx_phase - 1].items():
                for idx_match, html in enumerate(team_matches, start=1):
                    if html is None:
                        logger.info(
                            f"Skipping match {idx_match} for team {team_name} (no link)."
                        )
                        continue
                    try:
                        match, simples, doubles = self._parse_match(
                            html, team_name, idx_match, idx_phase
                        )
                        all_matches.append(match)
                        all_simples.extend(simples)
                        all_doubles.extend(doubles)
                    except Exception:
                        logger.error(
                            f"Parsing match {idx_match} for team {team_name} in phase {idx_phase} resulted in error."
                        )

        return (
            pd.DataFrame(all_matches),
            pd.DataFrame(all_simples),
            pd.DataFrame(all_doubles),
        )
