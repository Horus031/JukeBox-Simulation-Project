import pytest
from library_item import MediaItem, Track, PlaybackStrategy, SequentialPlaybackStrategy, RandomPlaybackStrategy, MusicPlayer

def test_track_creation():
    """Test track creation and basic properties"""
    track = Track("Test Song", "Test Artist", 4)
    assert track.name == "Test Song"
    assert track.artist == "Test Artist"
    assert track.rating == 4
    assert track.play_count == 0

def test_track_rating_validation():
    """Test rating validation"""
    track = Track("Test Song", "Test Artist")
    
    # Test valid ratings
    track.rating = 5
    assert track.rating == 5
    
    track.rating = 0
    assert track.rating == 0
    
    # Test invalid ratings (should not change)
    track.rating = 6
    assert track.rating == 0
    
    track.rating = -1
    assert track.rating == 0

def test_play_count_increment():
    """Test play count increment"""
    track = Track("Test Song", "Test Artist")
    assert track.play_count == 0
    
    track.increment_play_count()
    assert track.play_count == 1
    
    track.increment_play_count()
    assert track.play_count == 2

def test_track_info_format():
    """Test track info string format"""
    track = Track("Test Song", "Test Artist", 3)
    expected_info = "Test Song - Test Artist ***"
    assert track.info() == expected_info

def test_stars_display():
    """Test star rating display"""
    track = Track("Test Song", "Test Artist", 4)
    assert track.stars() == "****"
    
    track.rating = 0
    assert track.stars() == ""

def test_file_path_handling():
    """Test file path handling"""
    track = Track("Test Song", "Test Artist")
    
    test_path = "/path/to/file.mp3"
    track.set_file_path(test_path)
    assert track.get_file_path() == test_path

def test_sequential_strategy():
    """Test sequential playback strategy"""
    strategy = SequentialPlaybackStrategy()
    playlist = [("01", "Track 1"), ("02", "Track 2"), ("03", "Track 3")]
    
    # Test initial track
    assert strategy.get_initial_track(playlist) == 0
    
    # Test next track selection
    assert strategy.get_next_track(playlist, 0) == 1
    assert strategy.get_next_track(playlist, 1) == 2
    assert strategy.get_next_track(playlist, 2) == 0  # Should loop back

def test_random_strategy():
    """Test random playback strategy"""
    strategy = RandomPlaybackStrategy()
    playlist = [("01", "Track 1"), ("02", "Track 2"), ("03", "Track 3")]
    
    # Test multiple times to ensure randomness
    initial_positions = set()
    for _ in range(10):
        initial_positions.add(strategy.get_initial_track(playlist))
    
    # Should get different positions (though not guaranteed)
    assert len(initial_positions) > 1

class MockPlayerObserver:
    def __init__(self):
        self.track_changes = []
        self.state_changes = []
    
    def on_track_change(self, track_info):
        self.track_changes.append(track_info)
    
    def on_playback_state_change(self, is_playing):
        self.state_changes.append(is_playing)

def test_music_player_observers():
    """Test music player observer pattern"""
    player = MusicPlayer()
    observer = MockPlayerObserver()
    
    player.add_observer(observer)
    player.notify_observers("Test Track")
    
    assert len(observer.track_changes) == 1
    assert len(observer.state_changes) == 1