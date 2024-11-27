from abc import ABC, abstractmethod  # Importing ABC and abstractmethod for creating abstract base classes
import pygame  # Importing pygame for multimedia handling
from threading import Thread  # Importing Thread for running tasks in parallel
import os.path  # Importing os.path for file path manipulations
import time  # Importing time for handling time-related functions
from typing import Optional, Callable, List, Tuple  # Importing types for type hints

class MediaItem(ABC):
    """Abstract base class for media items"""
    def __init__(self, name: str, artist: str, rating: int = 0):
        self._name = name  # Initialize the name of the media item
        self._artist = artist  # Initialize the artist of the media item
        self._rating = rating  # Initialize the rating (default is 0)
        self._play_count = 0  # Initialize the play count to 0
        self._file_path: Optional[str] = None  # Initialize file path as None

    @property
    def name(self) -> str:
        return self._name  # Return the name of the media item

    @property
    def artist(self) -> str:
        return self._artist  # Return the artist of the media item

    @property
    def rating(self) -> int:
        return self._rating  # Return the rating of the media item

    @rating.setter
    def rating(self, value: int) -> None:
        if 0 <= value <= 5:  # Ensure the rating is between 0 and 5
            self._rating = value  # Set the rating

    @property
    def play_count(self) -> int:
        return self._play_count  # Return the play count

    def increment_play_count(self) -> None:
        self._play_count += 1  # Increment the play count by 1

    def info(self) -> str:
        return f"{self._name} - {self._artist} {self.stars()}"  # Return a string with media item info

    def stars(self) -> str:
        return "*" * self._rating  # Return a string of stars based on the rating

    def set_file_path(self, path: str) -> None:
        self._file_path = path  # Set the file path for the media item

    def get_file_path(self) -> Optional[str]:
        return self._file_path  # Return the file path of the media item

class Track(MediaItem):
    """Implementation of audio track"""
    def __init__(self, name: str, artist: str, rating: int = 0):
        super().__init__(name, artist, rating)  # Call the parent constructor

class PlayerObserver(ABC):
    """Observer interface for player updates"""
    @abstractmethod
    def on_track_change(self, track_info: str) -> None:
        pass  # Abstract method to notify about track changes

    @abstractmethod
    def on_playback_state_change(self, is_playing: bool) -> None:
        pass  # Abstract method to notify about playback state changes

class PlaybackStrategy(ABC):
    """Abstract base class for playback strategies"""
    @abstractmethod
    def get_next_track(self, playlist: List[Tuple[str, str]], current_index: int) -> int:
        pass  # Abstract method to get the next track index

    @abstractmethod
    def get_initial_track(self, playlist: List[Tuple[str, str]]) -> int:
        pass  # Abstract method to get the initial track index

class SequentialPlaybackStrategy(PlaybackStrategy):
    """Plays tracks in sequential order"""
    def get_next_track(self, playlist: List[Tuple[str, str]], current_index: int) -> int:
        return (current_index + 1) % len(playlist)  # Return the next track index in a circular manner

    def get_initial_track(self, playlist: List[Tuple[str, str]]) -> int:
        return 0  # Return the first track index

class RandomPlaybackStrategy(PlaybackStrategy):
    """Plays tracks in random order"""
    def get_next_track(self, playlist: List[Tuple[str, str]], current_index: int) -> int:
        import random  # Import random for generating random numbers
        return random.randint(0, len(playlist) - 1)  # Return a random track index

    def get_initial_track(self, playlist: List[Tuple[str, str]]) -> int:
        import random  # Import random for generating random numbers
        return random.randint(0, len(playlist) - 1)  # Return a random initial track index

class MusicPlayer:
    """Handles music playback functionality with improved OOP structure"""
    def __init__(self, strategy: PlaybackStrategy = None):
        pygame.mixer.init()
        self._current_track: Optional[str] = None
        self._is_playing: bool = False
        self._current_playlist: list = []
        self._playlist_thread: Optional[Thread] = None
        self._current_position: float = 0
        self._track_length: float = 0
        self._track_index: int = 0
        self._played_duration: float = 0
        self._last_position_check: float = 0
        self._track_info_callback: Optional[Callable] = None
        self._paused: bool = False
        self._volume: float = 0.7
        self._observers: List[PlayerObserver] = []
        self._strategy = strategy or SequentialPlaybackStrategy()
        self._changing_track: bool = False

    def add_observer(self, observer: PlayerObserver) -> None:
        self._observers.append(observer)  # Add an observer to the list

    def remove_observer(self, observer: PlayerObserver) -> None:
        if observer in self._observers:  # Check if the observer is in the list
            self._observers.remove(observer)  # Remove the observer from the list

    def notify_observers(self, track_info: str = None) -> None:
        """Notify observers about state changes"""
        for observer in self._observers:
            try:
                if track_info:
                    observer.on_track_change(track_info)
                observer.on_playback_state_change(self._is_playing)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def set_track_info_callback(self, callback: Callable[[str], None]) -> None:
        self._track_info_callback = callback  # Set the callback for track info updates

    def load_track(self, track_number: str) -> Optional[str]:
        try:
            track_number = str(track_number).zfill(2)  # Format track number to two digits
            for ext in ['.mp3', '.wav']:  # Check for both .mp3 and .wav formats
                track_path = os.path.join('tracks', f'track_{track_number}{ext}')  # Construct the track path
                if os.path.exists(track_path):  # Check if the track file exists
                    return track_path  # Return the valid track path
            return None  # Return None if no track is found
        except Exception as e:
            print(f"Error loading track: {e}")  # Print error message if an exception occurs
            return None  # Return None in case of an error

    def play_single_track(self, track_number: str) -> bool:
        """Play a single track and handle the audio setup"""
        track_path = self.load_track(track_number)
        if not track_path:
            return False

        try:
            # Load track for length calculation
            self._sound = pygame.mixer.Sound(track_path)
            self._track_length = self._sound.get_length()
            
            # Load and play track
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(self._volume)
            
            # Update state
            self._current_track = track_number
            self._current_position = 0.0
            self._played_duration = 0.0
            self._last_position_check = time.time()
            self._is_playing = True
            
            # Start monitoring play duration for play count updates
            self._monitor_play_duration()
            
            return True
            
        except Exception as e:
            print(f"Error playing track: {e}")
            self._track_length = 0.0
            self._sound = None
            return False
    
    def _get_current_track_info(self) -> str:
        """Get formatted track info for current track with improved synchronization"""
        try:
            import track_library as lib
            if self._current_track:
                track_id = str(self._current_track).zfill(2)
                track_name = lib.library.get_name(track_id)
                artist_name = lib.library.get_artist(track_id)
                
                if track_name and artist_name:
                    return f"Now Playing: {track_name} - {artist_name}"
                else:
                    # If track info not found in library, get it from current playlist
                    for i, (tid, name) in enumerate(self._current_playlist):
                        if tid == self._current_track:
                            return f"Now Playing: {name}"
            return "No track playing"
        except Exception as e:
            print(f"Error getting track info: {e}")
            return "Error getting track info"

    def play_playlist(self, playlist: list) -> None:
        if not playlist:
            return
            
        self._current_playlist = playlist.copy()
        self._track_index = self._strategy.get_initial_track(self._current_playlist)
        self._paused = False
        self._is_playing = True
        self._current_position = 0.0
        self._changing_track = False

        def playlist_worker():
            while self._is_playing and self._current_playlist:
                try:
                    if self._changing_track:
                        time.sleep(0.1)
                        continue

                    current_track = self._current_playlist[self._track_index]
                    track_id = current_track[0]
                    self._current_track = track_id  # Update current track ID
                    
                    if self.play_single_track(track_id):
                        # Update track info after successful play
                        track_info = self._get_current_track_info()
                        if self._track_info_callback:
                            self._track_info_callback(track_info)
                        self.notify_observers(track_info)
                        
                        while pygame.mixer.music.get_busy() or self._paused:
                            if not self._is_playing or self._changing_track:
                                pygame.mixer.music.stop()
                                break
                                
                            if self._paused:
                                time.sleep(0.1)
                                continue
                                
                            time.sleep(0.1)
                        
                        # Only advance if we're still playing and not paused
                        if self._is_playing and not self._changing_track:
                            next_index = self._strategy.get_next_track(
                                self._current_playlist,
                                self._track_index
                            )
                            self._track_index = next_index
                            # Reset positions for next track
                            self._current_position = 0.0
                            self._played_duration = 0.0
                            continue
                                
                except Exception as e:
                    print(f"Error in playlist worker: {e}")
                    time.sleep(0.1)

        # Stop existing playback
        if self._playlist_thread and self._playlist_thread.is_alive():
            self.stop()
            time.sleep(0.1)

        # Start new playlist thread
        self._playlist_thread = Thread(target=playlist_worker)
        self._playlist_thread.daemon = True
        self._playlist_thread.start()

    def _monitor_play_duration(self) -> None:
        """Monitor track play duration for play count updates"""
        def monitor():
            while self._is_playing and (pygame.mixer.music.get_busy() or self._paused):  # Loop while playing or paused
                if not self._paused:  # Check if not paused
                    current_time = time.time()  # Get the current time
                    elapsed = current_time - self._last_position_check  # Calculate elapsed time
                    self._played_duration += elapsed  # Update played duration
                    self._last_position_check = current_time  # Update last position check time
                    
                    if self._played_duration >= 1 and self._current_track:  # Check if at least 1 second has played
                        import track_library as lib  # Import track library for updating play count
                        lib.library.increment_play_count(str(self._current_track).zfill(2))  # Increment play count
                        break  # Exit the monitor loop
                time.sleep(0.1)  # Sleep briefly to avoid busy waiting
        Thread(target=monitor, daemon=True).start()  # Start the monitor thread

    def _update_track_info(self) -> None:
        """Update track info display"""
        if self._track_info_callback:
            track_info = self._get_current_track_info()
            try:
                # Use configure instead of config for CTk widgets
                self._track_info_callback(track_info)
            except Exception as e:
                print(f"Error updating track info display: {e}")

    def play_previous(self) -> None:
        """Play the previous track in the playlist"""
        if not self._current_playlist or self._changing_track:
            return
        
        # Prevent multiple track changes    
        self._changing_track = True
        
        try:
            # Stop current playback
            pygame.mixer.music.stop()
            
            # Calculate previous index BEFORE playing
            prev_index = (self._track_index - 1) if self._track_index > 0 else len(self._current_playlist) - 1
            self._track_index = prev_index
            
            # Get track info
            track_id = self._current_playlist[self._track_index][0]
            
            # Reset states
            self._current_position = 0.0
            self._played_duration = 0.0
            self._is_playing = True
            self._paused = False
            self._current_track = track_id
            
            # Load and play track
            track_path = self.load_track(track_id)
            if track_path:
                # Load track for length calculation
                self._sound = pygame.mixer.Sound(track_path)
                self._track_length = self._sound.get_length()
                
                # Load and play track
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                pygame.mixer.music.set_volume(self._volume)
                
                # Update track info and notify observers
                track_info = self._get_current_track_info()
                if self._track_info_callback:
                    self._track_info_callback(track_info)
                self.notify_observers(track_info)
                
        except Exception as e:
            print(f"Error playing previous track: {e}")
            self._is_playing = False
            self._paused = False
        finally:
            self._changing_track = False

    def play_next(self) -> None:
        """Play the next track in the playlist"""
        if not self._current_playlist or self._changing_track:
            return

        # Prevent multiple track changes
        self._changing_track = True
        
        try:
            # Stop current playback
            pygame.mixer.music.stop()
            
            # Calculate next index BEFORE playing
            next_index = self._strategy.get_next_track(
                self._current_playlist, 
                self._track_index
            )
            self._track_index = next_index
            
            # Get track info
            track_id = self._current_playlist[self._track_index][0]
            
            # Reset states
            self._current_position = 0.0
            self._played_duration = 0.0
            self._is_playing = True
            self._paused = False
            self._current_track = track_id
            
            # Load and play track
            track_path = self.load_track(track_id)
            if track_path:
                # Load track for length calculation
                self._sound = pygame.mixer.Sound(track_path)
                self._track_length = self._sound.get_length()
                
                # Load and play track
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                pygame.mixer.music.set_volume(self._volume)
                
                # Update track info and notify observers
                track_info = self._get_current_track_info()
                if self._track_info_callback:
                    self._track_info_callback(track_info)
                self.notify_observers(track_info)
                
        except Exception as e:
            print(f"Error playing next track: {e}")
            self._is_playing = False
            self._paused = False
        finally:
            self._changing_track = False

    @property
    def is_playing(self) -> bool:
        return self._is_playing  # Return the current playing state

    @property
    def current_track(self) -> Optional[str]:
        return self._current_track  # Return the current track number

    def toggle_playback(self) -> None:
        """Toggle between play and pause"""
        if self._is_playing:  # Check if currently playing
            self.pause()  # Call pause method
        else:
            self.unpause()  # Call unpause method

    def stop_playback(self) -> None:
        """Stop playback"""
        self.stop()  # Call stop method
        self.progress_scale.set(0)  # Reset progress scale to 0
        self.time_label.configure(text="0:00 / 0:00")  # Reset time label display
        self.track_info.configure(text="No track playing")  # Update track info display
        # Reset track index to start of playlist
        self.player._track_index = 0  # Reset track index to 0

    def pause(self) -> None:
        """Pause playback with improved state handling"""
        if self._is_playing and not self._paused:  # Check if currently playing and not already paused
            pygame.mixer.music.pause()  # Pause the music playback
            self._paused = True  # Set paused state to True
            self._is_playing = False  # Set playing state to False
            # Store current position when pausing
            pos = pygame.mixer.music.get_pos() / 1000.0  # Get the current position in seconds
            self._current_position += pos  # Update current position with paused position

    def unpause(self) -> None:
        """Resume playback with improved state handling"""
        if self._paused:  # Reload and seek to the stored position
            if self._current_track:  # Check if there is a current track
                track_path = self.load_track(self._current_track)  # Load the current track
                if track_path:  # If the track path is valid
                    pygame.mixer.music.load(track_path)  # Load the track into the mixer
                    pygame.mixer.music.play(start=self._current_position)  # Start playing from the stored position
                    pygame.mixer.music.set_volume(self._volume)  # Set the volume level
            
            self._paused = False  # Set paused state to False
            self._is_playing = True  # Set playing state to True
            self._last_position_check = time.time()  # Record the last position check time
            self.notify_observers()  # Notify observers of state change

    def stop(self) -> None:
        """Stop playback"""
        pygame.mixer.music.stop()  # Stop the music playback
        self._is_playing = False  # Set playing state to False
        self._paused = False  # Set paused state to False
        self._current_playlist = []  # Clear the current playlist
        self._played_duration = 0  # Reset played duration
        self._current_position = 0  # Reset current position
        self._track_length = 0  # Reset track length
        if self._track_info_callback:  # Check if track info callback is set
            self._track_info_callback("No track playing")  # Update track info display
            
        # Notify observers about the state change
        self.notify_observers()  # Notify observers of playback stop

    def set_volume(self, volume: float) -> None:
        """Set playback volume"""
        self._volume = max(0.0, min(1.0, volume))  # Ensure volume is between 0.0 and 1.0
        pygame.mixer.music.set_volume(self._volume)  # Set the volume level in the mixer

    def seek_to_position(self, position: float) -> None:
        """Seek to a specific position in the current track"""
        if self._is_playing and self._current_track:  # Check if currently playing and there is a current track
            try:
                # Store the target position
                self._current_position = position  # Update current position to the target position
                
                # Reload and play the track from the new position
                track_path = self.load_track(self._current_track)  # Load the current track
                if track_path:  # If the track path is valid
                    pygame.mixer.music.load(track_path)  # Load the track into the mixer
                    pygame.mixer.music.play(start=position)  # Start playing from the new position
                    pygame.mixer.music.set_volume(self._volume)  # Set the volume level
                    
            except Exception as e:
                print(f"Error seeking position: {e}")  # Print error message if an exception occurs