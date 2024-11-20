import pytest
from tkinter import Tk
import track_library as lib  # Importing the library that contains track-related functions and classes
from view_track import TrackViewer  # Importing the TrackViewer class for viewing tracks
from create_track_list import CreateTrackList  # Importing the CreateTrackList class for managing playlists
from update_track import UpdateTracks  # Importing the UpdateTracks class for updating track ratings

# Fixture to create a Tkinter root window for testing
@pytest.fixture
def root():
    import os
    os.environ['TCL_LIBRARY'] = r"C:/Python3x/tcl/tcl8.6"  # Set the TCL_LIBRARY environment variable
    root = Tk()  # Create a new Tkinter root window
    root.update_idletasks()  # Process any pending events
    yield root  # Provide the root window to the test
    root.destroy()  # Destroy the root window after the test is done

# Alternative approach if the first method doesn't work:
@pytest.fixture
def root():
    import tkinter as tk
    root = tk.Tk()  # Create a new Tkinter root window
    root.withdraw()  # Hide the root window
    root.update()  # Process any pending events
    yield root  # Provide the hidden root window to the test
    root.destroy()  # Destroy the root window after the test is done

# Test class for TrackViewer functionality
class TestTrackViewer:
    @pytest.fixture
    def viewer(self, root):
        return TrackViewer(root)  # Create an instance of TrackViewer with the Tkinter root

    # Test case for viewing a valid track
    def test_view_valid_track(self, viewer):
        viewer.input_txt.insert(0, "01")  # Insert a valid track ID
        viewer.view_tracks_clicked()  # Simulate the button click to view the track
        result = viewer.track_txt.get("1.0", "end-1c")  # Get the displayed track information
        assert "Another Brick in the Wall" in result  # Check if the track title is present
        assert "Pink Floyd" in result  # Check if the artist name is present

    # Test case for viewing an invalid track
    def test_view_invalid_track(self, viewer):
        viewer.input_txt.insert(0, "99")  # Insert an invalid track ID
        viewer.view_tracks_clicked()  # Simulate the button click to view the track
        result = viewer.track_txt.get("1.0", "end-1c")  # Get the displayed track information
        assert "Track 99 not found" in result  # Verify the error message for invalid track

    # Test case for listing all tracks
    def test_list_tracks(self, viewer):
        viewer.list_tracks_clicked()  # Simulate the button click to list all tracks
        result = viewer.list_txt.get("1.0", "end-1c")  # Get the displayed list of tracks
        assert "Pink Floyd" in result  # Check if a known artist is present
        assert "Bee Gees" in result  # Check if another known artist is present

# Test class for CreateTrackList functionality
class TestCreateTrackList:
    @pytest.fixture
    def playlist(self, root):
        return CreateTrackList(root)  # Create an instance of CreateTrackList with the Tkinter root

    # Test case for adding a valid track to the playlist
    def test_add_valid_track(self, playlist):
        playlist.track_input.insert(0, "01")  # Insert a valid track ID
        playlist.add_track_clicked()  # Simulate the button click to add the track
        assert "01" in playlist.playlist  # Verify the track ID is in the playlist
        assert "Another Brick in the Wall" in playlist.playlist_txt.get("1.0", "end-1c")  # Check if the track title is displayed

    # Test case for adding an invalid track to the playlist
    def test_add_invalid_track(self, playlist):
        playlist.track_input.insert(0, "99")  # Insert an invalid track ID
        playlist.add_track_clicked()  # Simulate the button click to add the track
        assert len(playlist.playlist) == 0  # Verify the playlist is still empty

    # Test case for adding a duplicate track to the playlist
    def test_add_duplicate_track(self, playlist):
        playlist.track_input.insert(0, "01")  # Insert a valid track ID
        playlist.add_track_clicked()  # Add the track to the playlist
        playlist.track_input.insert(0, "01")  # Insert the same track ID again
        playlist.add_track_clicked()  # Attempt to add the duplicate track
        assert playlist.playlist.count("01") == 1  # Verify that the duplicate track is not added again

    # Test case for playing the playlist
    def test_play_playlist(self, playlist):
        playlist.playlist = ["01"]  # Set the playlist with a valid track ID
        initial_count = lib.get_play_count("01")  # Get the initial play count for the track
        playlist.play_playlist_clicked()  # Simulate the button click to play the playlist
        assert lib.get_play_count("01") == initial_count + 1  # Verify the play count has increased

    # Test case for resetting the playlist
    def test_reset_playlist(self, playlist):
        playlist.playlist = ["01", "02"]  # Set the playlist with multiple tracks
        playlist.reset_playlist_clicked()  # Simulate the button click to reset the playlist
        assert len(playlist.playlist) == 0  # Verify the playlist is empty after reset
        assert playlist.playlist_txt.get("1.0", "end-1c") == ""  # Verify the display is also empty

# Test class for UpdateTracks functionality
class TestUpdateTracks:
    @pytest.fixture
    def updater(self, root):
        return UpdateTracks(root)  # Create an instance of UpdateTracks with the Tkinter root

    # Test case for updating a valid track rating
    def test_update_valid_rating(self, updater):
        updater.track_input.insert(0, "01")  # Insert a valid track ID
        updater.rating_input.insert(0, "5")  # Insert a new rating
        updater.update_rating_clicked()  # Simulate the button click to update the rating
        assert lib.get_rating("01") == 5  # Verify the rating has been updated

    # Test case for attempting to update with an invalid rating
    def test_update_invalid_rating(self, updater):
        updater.track_input.insert(0, "01")  # Insert a valid track ID
        updater.rating_input.insert(0, "6")  # Insert an invalid rating (assuming max is 5)
        original_rating = lib.get_rating("01")  # Get the original rating
        updater.update_rating_clicked()  # Simulate the button click to update the rating
        assert lib.get_rating("01") == original_rating  # Verify the rating remains unchanged

    # Test case for updating a rating for an invalid track
    def test_update_invalid_track(self, updater):
        updater.track_input.insert(0, "99")  # Insert an invalid track ID
        updater.rating_input.insert(0, "5")  # Insert a new rating
        updater.update_rating_clicked()  # Simulate the button click to update the rating
        assert "not found" in updater.status_lbl.cget("text")  # Verify the error message is displayed

# Test case for LibraryItem class creation
def test_library_item_creation():
    item = lib.LibraryItem("Test Track", "Test Artist", 3)  # Create a new LibraryItem instance
    assert item.name == "Test Track"  # Verify the track name
    assert item.artist == "Test Artist"  # Verify the artist name
    assert item.rating == 3  # Verify the rating
    assert item.play_count == 0  # Verify the initial play count is zero

# Test case for getting LibraryItem information
def test_library_item_info():
    item = lib.LibraryItem("Test Track", "Test Artist", 3)  # Create a new LibraryItem instance
    assert item.info() == "Test Track - Test Artist ***"  # Verify the formatted info string

# Test case for various library functions
def test_library_functions():
    assert lib.get_name("01") == "Another Brick in the Wall"  # Verify the track name retrieval
    assert lib.get_artist("01") == "Pink Floyd"  # Verify the artist name retrieval
    assert isinstance(lib.get_rating("01"), int)  # Verify the rating is an integer
    assert isinstance(lib.get_play_count("01"), int)  # Verify the play count is an integer