import pytest
import os
import csv
import pygame
import tkinter as tk
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock
from library_item import Track, MusicPlayer, SequentialPlaybackStrategy, RandomPlaybackStrategy
from track_library import MusicLibrary, library
from jukebox import YouTubeAPI, SearchResultsFrame, JukeboxApp

@pytest.fixture
def setup_library():
    # Create a temporary library file
    with open("tracks1.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["track_id", "name", "artist", "rating", "play_count"])
    
    test_lib = MusicLibrary()
    yield test_lib

@pytest.fixture
def mock_player():
    pygame.mixer.init()
    return MusicPlayer(SequentialPlaybackStrategy())

def test_track_rating_bounds():
    track = Track("Test Song", "Test Artist")
    track.rating = 5
    assert track.rating == 5
    track.rating = 6
    assert track.rating == 5
    track.rating = -1
    assert track.rating == 5

def test_track_play_count():
    track = Track("Test Song", "Test Artist")
    assert track.play_count == 0
    track.increment_play_count()
    assert track.play_count == 1

# Library Tests
def test_library_add_track(setup_library):
    result = setup_library.add_track("03", "New Track", "New Artist", 5)
    assert result == True
    assert setup_library.get_name("03") == "New Track"
    assert setup_library.get_artist("03") == "New Artist"

def test_library_search(setup_library):
    # First add some tracks to search
    setup_library.add_track("01", "Test Track 1", "Test Artist", 4)
    setup_library.add_track("02", "Test Track 2", "Test Artist", 3)
    
    results = setup_library.search_tracks("Test", "Both")
    assert len(results) > 0
    assert all("Test" in track.name or "Test" in track.artist for track in results)

def test_library_rating_update(setup_library):
    setup_library.add_track("01", "Test Track", "Test Artist", 3)
    setup_library.set_rating("01", 5)
    assert setup_library.get_rating("01") == 5

# Player Tests
def test_player_initialization(mock_player):
    assert mock_player.is_playing == False
    assert mock_player.current_track == None

def test_player_volume_control(mock_player):
    mock_player.set_volume(0.5)
    assert abs(mock_player._volume - 0.5) < 0.01

def test_sequential_strategy():
    strategy = SequentialPlaybackStrategy()
    playlist = [("01", "Track 1"), ("02", "Track 2")]
    next_index = strategy.get_next_track(playlist, 0)
    assert next_index == 1

def test_random_strategy():
    strategy = RandomPlaybackStrategy()
    playlist = [("01", "Track 1"), ("02", "Track 2")]
    initial_index = strategy.get_initial_track(playlist)
    assert 0 <= initial_index < len(playlist)

# YouTubeAPI Tests
@pytest.mark.asyncio
async def test_youtube_api_search():
    api = YouTubeAPI()
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_search = MagicMock()
        mock_response = {
            'items': [{
                'id': {'videoId': 'test123'},
                'snippet': {
                    'title': 'Test Video',
                    'channelTitle': 'Test Channel',
                    'thumbnails': {'default': {'url': 'http://test.com'}}
                }
            }]
        }
        mock_search.execute.return_value = mock_response
        mock_build.return_value.search.return_value.list.return_value = mock_search
        mock_build.return_value.videos.return_value.list.return_value.execute.return_value = {
            'items': [{
                'contentDetails': {'duration': 'PT4M20S'},
                'statistics': {'viewCount': '1000'}
            }]
        }
        
        results = await api.search_tracks("test query")
        assert len(results) > 0
        assert 'track_id' in results[0]

# Integration Tests
def test_app_initialization():
    root = tk.Tk()  # Create root window first
    with patch('tkinter.Tk', return_value=root), \
         patch('customtkinter.CTk'), \
         patch('customtkinter.CTkFrame'), \
         patch.object(JukeboxApp, '_setup_ui'):
        app = JukeboxApp()
        assert hasattr(app, 'player')
        assert hasattr(app, 'playlist')
        assert isinstance(app.player._strategy, (SequentialPlaybackStrategy, RandomPlaybackStrategy))
    root.destroy()  # Clean up


if __name__ == "__main__":
    pytest.main(["-v"])