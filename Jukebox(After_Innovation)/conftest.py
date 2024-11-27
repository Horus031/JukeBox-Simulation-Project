# conftest.py
import pytest
import pygame
import os
import shutil
import patch

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    
    # Create test directories and files
    test_dir = tmp_path_factory.mktemp("test_files")
    tracks_dir = test_dir / "tracks"
    tracks_dir.mkdir()
    
    # Create dummy audio file
    dummy_audio = tracks_dir / "track_01.mp3"
    shutil.copy("path/to/test/audio.mp3", dummy_audio) if os.path.exists("path/to/test/audio.mp3") else dummy_audio.touch()
    
    yield
    
    # Cleanup
    pygame.mixer.quit()
    pygame.quit()
    shutil.rmtree(test_dir)

@pytest.fixture(autouse=True)
def setup_pygame():
    pygame.init()
    pygame.mixer.init()
    yield
    pygame.mixer.quit()
    pygame.quit()

@pytest.fixture(scope="session")
def test_audio_file(tmp_path_factory):
    test_dir = tmp_path_factory.mktemp("tracks")
    test_file = test_dir / "track_01.mp3"
    test_file.touch()  # Creates empty file
    return test_file

def mock_pygame_mixer():
    with patch('pygame.mixer.music') as mock_music:
        mock_music.get_busy.return_value = False
        mock_music.get_pos.return_value = 0
        yield mock_music