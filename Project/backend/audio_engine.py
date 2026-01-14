# audio_engine.py
"""
AudioEngine: shared playback + track selection for LumiTune.

- Organizes music by decade (year group) and genre.
- Provides methods to set year/genre, play/pause/next/previous, and volume.
- Uses pygame.mixer for audio output.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

import pygame

# Decades and genres used across the system
YEAR_GROUPS = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
GENRES = ["chill", "energetic", "warm", "party"]
NUM_SONGS_PER_GENRE = 3  # expects files like 1950_chill_01.mp3, ..., _03.mp3


class AudioEngine:
    def __init__(
        self,
        music_dir: Optional[Path] = None,
        year_groups=None,
        genres=None,
        num_songs_per_genre: int = NUM_SONGS_PER_GENRE,
    ) -> None:
        # Resolve music directory; default: ../music relative to this file
        if music_dir is None:
            self.music_dir = Path(__file__).resolve().parent.parent / "music"
        else:
            self.music_dir = Path(music_dir)

        self.year_groups = year_groups or YEAR_GROUPS
        self.genres = genres or GENRES
        self.num_songs_per_genre = num_songs_per_genre

        # Initialize pygame mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print(f"[AUDIO] Initialized pygame mixer (dir={self.music_dir})")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to initialize pygame mixer: {e}")

        # Build song map
        self.song_map: Dict[int, Dict[str, List[Path]]] = self._build_song_map()

        # Playback state
        self.current_year: int = self.year_groups[0]
        self.current_genre: str = self.genres[0]
        self.current_index: int = 0
        self.current_song: Optional[Path] = None
        self.volume: float = 0.7  # 0.0–1.0
        self.is_playing: bool = False
        self.is_paused: bool = False

    # ---------- Internal helpers ----------

    def _build_song_map(self) -> Dict[int, Dict[str, List[Path]]]:
        song_map: Dict[int, Dict[str, List[Path]]] = {}
        if not self.music_dir.exists():
            print(f"[AUDIO WARNING] music_dir does not exist: {self.music_dir}")
            return song_map

        for year in self.year_groups:
            song_map[year] = {}
            for g in self.genres:
                files: List[Path] = []
                for i in range(1, self.num_songs_per_genre + 1):
                    filename = f"{year}_{g}_{i:02d}.mp3"
                    path = self.music_dir / filename
                    if path.exists():
                        files.append(path)
                if not files:
                    print(f"[AUDIO WARNING] No files for {year}/{g} in {self.music_dir}")
                song_map[year][g] = files
        return song_map

    def _get_playlist(self, year: Optional[int] = None, genre: Optional[str] = None) -> List[Path]:
        """Return list of Path objects for the given year+genre, with fallback."""
        year = year if year is not None else self.current_year
        genre = (genre or self.current_genre).lower()

        # Validate year
        if year not in self.song_map:
            print(f"[AUDIO WARNING] Year {year} not found, using {self.year_groups[0]}")
            year = self.year_groups[0]
            self.current_year = year

        # Validate genre
        if genre not in self.genres:
            print(f"[AUDIO WARNING] Genre '{genre}' not known, using '{self.genres[0]}'")
            genre = self.genres[0]
            self.current_genre = genre

        playlist = self.song_map.get(year, {}).get(genre, [])
        if playlist:
            return playlist

        # Fallback: try same genre across all years
        for y in self.year_groups:
            pl = self.song_map.get(y, {}).get(genre, [])
            if pl:
                print(f"[AUDIO] Falling back to {y}/{genre}")
                self.current_year = y
                return pl

        # Final fallback: any song at all
        print("[AUDIO WARNING] No songs found for requested year/genre; using any available track.")
        all_tracks: List[Path] = []
        for y in self.year_groups:
            for g in self.genres:
                all_tracks.extend(self.song_map.get(y, {}).get(g, []))
        return all_tracks

    def _load_and_play(self, track: Path) -> None:
        """Load and play a specific track immediately."""
        try:
            pygame.mixer.music.load(str(track))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            self.current_song = track
            self.is_playing = True
            self.is_paused = False
            print(f"[PLAY] {self.current_year}/{self.current_genre} - {track.name} (vol={self.volume:.2f})")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to play {track}: {e}")
            self.is_playing = False
            self.current_song = None

    # ---------- Public API ----------
    def get_year(self) -> int:
        return self.current_year

    def set_year(self, year: int) -> None:
        if year not in self.year_groups:
            print(f"[AUDIO WARNING] Year {year} not in YEAR_GROUPS; keeping {self.current_year}")
            return
        else:
            self.current_year = year
        print(f"[AUDIO] Current year set to {self.current_year}")

    def set_genre(self, genre: str) -> None:
        genre = (genre or "").lower()
        if genre not in self.genres:
            print(f"[AUDIO WARNING] Genre '{genre}' not in GENRES; keeping '{self.current_genre}'")
            return
        self.current_genre = genre
        print(f"[AUDIO] Current genre set to {self.current_genre}")

    def set_mode(self, year: Optional[int] = None, genre: Optional[str] = None) -> None:
        """Convenience: update year and/or genre together."""
        if year is not None:
            self.set_year(year)
        if genre is not None:
            self.set_genre(genre)

    def set_volume(self, volume: float) -> None:
        """Set volume 0.0–1.0."""
        volume = max(0.0, min(1.0, volume))
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume)
        print(f"[AUDIO] Volume set to {self.volume:.2f}")

    def change_volume(self, delta: float) -> None:
        """Change volume by delta (e.g., +0.1 or -0.1)."""
        self.set_volume(self.volume + delta)

    def play_current(self) -> None:
        """Play the current index within the current playlist."""
        playlist = self._get_playlist()
        if not playlist:
            print("[AUDIO ERROR] No tracks available to play.")
            return
        if self.current_index >= len(playlist):
            self.current_index = 0
        track = playlist[self.current_index]
        self._load_and_play(track)

    def play_random(self) -> None:
        """Play a random track from the current year/genre."""
        playlist = self._get_playlist()
        if not playlist:
            print("[AUDIO ERROR] No tracks available to play.")
            return
        self.current_index = random.randrange(len(playlist))
        self._load_and_play(playlist[self.current_index])

    def next_track(self) -> None:
        playlist = self._get_playlist()
        if not playlist:
            return
        self.current_index = (self.current_index + 1) % len(playlist)
        self._load_and_play(playlist[self.current_index])

    def previous_track(self) -> None:
        playlist = self._get_playlist()
        if not playlist:
            return
        self.current_index = (self.current_index - 1) % len(playlist)
        self._load_and_play(playlist[self.current_index])

    def pause(self) -> None:
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            print("[AUDIO] Paused")

    def resume(self) -> None:
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            print("[AUDIO] Resumed")

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        print("[AUDIO] Stopped")

    def is_track_playing(self) -> bool:
        """Return True if a track is currently playing at the mixer level."""
        return pygame.mixer.music.get_busy()

    def get_status(self) -> dict:
        """Return a simple status dict for MQTT or debugging."""
        return {
            "year": self.current_year,
            "genre": self.current_genre,
            "song": self.current_song.name if self.current_song else None,
            "volume": self.volume,
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
        }
