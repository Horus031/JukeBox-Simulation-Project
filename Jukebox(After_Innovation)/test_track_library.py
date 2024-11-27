import pytest
import os
import csv
from track_library import MusicLibrary, CSVHandler
from library_item import Track

@pytest.fixture
def temp_library(tmp_path):
    """Create a temporary library for testing"""
    # Create test directory if it doesn't exist
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    
    # Initialize library with test file path
    library = MusicLibrary()
    library._library_file = str(tmp_path / "test_tracks.csv")
    
    # Create initial CSV file with headers
    with open(library._library_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['track_id', 'name', 'artist', 'rating', 'play_count'])
    
    # Clear any existing data
    library._library = {}
    library._observers = []
    
    return library

def test_add_track(temp_library):
    """Test adding a track to the library"""
    # First clear any existing tracks
    temp_library._library.clear()
    
    # Add test track
    success = temp_library.add_track(
        "01", "Test Track", "Test Artist", 4, 0
    )
    assert success, "Failed to add track"
    
    # Verify track was added
    track = temp_library._library.get("01")
    assert track is not None, "Track not found in library"
    assert track.name == "Test Track", f"Expected 'Test Track', got {track.name}"
    assert track.artist == "Test Artist", f"Expected 'Test Artist', got {track.artist}"
    assert track.rating == 4, f"Expected rating 4, got {track.rating}"

def test_duplicate_track(temp_library):
    """Test adding duplicate track"""
    temp_library.add_track("01", "Track 1", "Artist 1")
    success = temp_library.add_track("01", "Track 2", "Artist 2")
    assert not success

def test_invalid_rating(temp_library):
    """Test adding track with invalid rating"""
    success = temp_library.add_track("01", "Test Track", "Test Artist", 6)
    assert not success

def test_remove_track(temp_library):
    """Test removing a track"""
    temp_library.add_track("01", "Test Track", "Test Artist")
    success = temp_library.remove_track("01")
    assert success
    assert "01" not in temp_library._library

def test_remove_nonexistent_track(temp_library):
    """Test removing track that doesn't exist"""
    success = temp_library.remove_track("99")
    assert not success

class MockLibraryObserver:
    def __init__(self):
        self.changes = 0
    
    def on_library_change(self):
        self.changes += 1

def test_library_observers(temp_library):
    """Test library observer pattern"""
    # Clear existing observers
    temp_library._observers = []
    
    # Create and add new observer
    observer = MockLibraryObserver()
    temp_library.add_observer(observer)
    
    # Verify observer is added
    assert observer in temp_library._observers, "Observer not added to library"
    
    # Test track addition notification
    observer.changes = 0  # Reset counter
    temp_library.add_track("01", "Test Track", "Test Artist")
    assert observer.changes == 1, f"Expected 1 change, got {observer.changes}"

def test_search_tracks(temp_library):
    """Test track search functionality"""
    # Clear existing tracks
    temp_library._library.clear()
    
    # Add test tracks
    temp_library.add_track("01", "Love Song", "Artist One")
    temp_library.add_track("02", "Happy Song", "Artist Two")
    temp_library.add_track("03", "Love Story", "Artist One")
    
    # Test name search
    results = temp_library.search_tracks("Love", "Track Name")
    assert len(results) == 2, f"Expected 2 tracks with 'Love', got {len(results)}"
    
    # Verify search results
    track_names = [track.name for track in results]
    assert "Love Song" in track_names, "Love Song not found in results"
    assert "Love Story" in track_names, "Love Story not found in results"

def test_rating_operations(temp_library):
    """Test rating operations"""
    temp_library.add_track("01", "Test Track", "Test Artist", 3)
    
    temp_library.set_rating("01", 5)
    assert temp_library.get_rating("01") == 5
    
    temp_library.set_rating("01", 0)
    assert temp_library.get_rating("01") == 0

def test_play_count(temp_library):
    """Test play count operations"""
    # Clear existing tracks
    temp_library._library.clear()
    
    # Add new track
    temp_library.add_track("01", "Test Track", "Test Artist")
    
    # Verify initial play count
    initial_count = temp_library.get_play_count("01")
    assert initial_count == 0, f"Expected initial play count 0, got {initial_count}"
    
    # Increment and verify
    temp_library.increment_play_count("01")
    new_count = temp_library.get_play_count("01")
    assert new_count == 1, f"Expected play count 1, got {new_count}"
    
def test_library_initialization(temp_library):
    """Test library initialization"""
    assert os.path.exists(temp_library._library_file), "CSV file not created"
    assert isinstance(temp_library._library, dict), "Library not initialized as dictionary"
    assert len(temp_library._observers) == 0, "Observers not empty on initialization"

def test_csv_file_structure(temp_library):
    """Test CSV file structure"""
    with open(temp_library._library_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_header = ['track_id', 'name', 'artist', 'rating', 'play_count']
        assert header == expected_header, f"Expected header {expected_header}, got {header}"