import pytest
import tkinter as tk
import customtkinter as ctk
from jukebox import JukeboxApp, SearchResultsFrame, PlaylistManager

@pytest.fixture
def app():
    """Create test application instance"""
    return JukeboxApp()

def test_playlist_manager():
    """Test playlist manager functionality"""
    manager = PlaylistManager()
    
    # Test saving playlist
    tracks = [("01", "Track 1"), ("02", "Track 2")]
    success = manager.save_playlist("test_playlist.txt", tracks)
    assert success
    
    # Test loading playlist
    loaded_tracks = manager.load_playlist("test_playlist.txt")
    assert loaded_tracks == tracks
    
    # Test getting all playlists
    playlists = manager.get_all_playlists()
    assert "test_playlist.txt" in playlists
    
    # Test deleting playlist
    success = manager.delete_playlist("test_playlist.txt")
    assert success
    assert "test_playlist.txt" not in manager.get_all_playlists()

def test_search_functionality(app):
    """Test search functionality"""
    app.search_entry.insert(0, "test")
    app.search_var.set("Track Name")
    
    # Trigger search
    app.search_tracks()
    
    # Clear search
    app.clear_search()
    assert app.search_entry.get() == ""

def test_filter_functionality(app):
    """Test filter functionality"""
    # Test different filter types
    app.filter_var.set("No Filter")
    app.apply_filter()
    
    app.filter_var.set("Most Played")
    app.apply_filter()
    
    app.filter_var.set("Highest Rated")
    app.apply_filter()

def test_playlist_operations(app):
    """Test playlist operations"""
    # Add track to playlist
    app.track_input.insert(0, "01")
    app.add_track_clicked()
    
    # Reset playlist
    app.reset_playlist_clicked()
    assert len(app.playlist) == 0

def test_volume_control(app):
    """Test volume control"""
    app.update_volume(50)
    assert app.player._volume == 0.5
    
    app.update_volume(100)
    assert app.player._volume == 1.0
    
    app.update_volume(0)
    assert app.player._volume == 0.0
