from typing import Optional, Dict, List, Set  # Import necessary types for type hinting
from library_item import Track  # Import the Track class from library_item module
from abc import ABC, abstractmethod  # Import abstract base class and abstract method decorators
import csv  # Import CSV module for handling CSV file operations
import os  # Import OS module for interacting with the operating system
import time  # Import time module for time-related functions
from watchdog.observers import Observer  # Import Observer class from watchdog for file monitoring
from watchdog.events import FileSystemEventHandler  # Import event handler for file system events

class LibraryObserver(ABC):
    """Observer interface for library updates"""
    @abstractmethod
    def on_library_change(self) -> None:
        pass

class CSVHandler(FileSystemEventHandler):
    """Handler for CSV file changes"""
    def __init__(self, library):
        self.library = library  # Store reference to the music library

    def on_modified(self, event):
        """Handle modified events for the CSV file"""
        if not event.is_directory and event.src_path.endswith('tracks.csv'):
            self.library.reload_library()  # Reload library if the tracks.csv file is modified

class MusicLibrary:
    """Enhanced music library with observer pattern and CSV storage"""
    def __init__(self):
        self._library: Dict[str, Track] = {}  # Initialize an empty dictionary for the library
        self._observers: List[LibraryObserver] = []  # List to hold observers
        self._library_file = "tracks.csv"  # Define the CSV file name for the library
        self._last_modified = 0  # Initialize last modified timestamp
        self._initialize_library()  # Load the library from CSV
        self._setup_file_watcher()  # Set up file watcher for monitoring changes

    def add_track(self, track_id: str, name: str, artist: str, rating: int = 0, play_count: int = 0) -> bool:
        """Add a new track to the library with proper UTF-8 handling"""
        try:
            # Ensure track_id is properly padded
            track_id = str(track_id).zfill(2)
            
            if track_id in self._library:
                print(f"Track {track_id} already exists")
                return False
                
            if not 0 <= rating <= 5:
                print("Rating must be between 0 and 5")
                return False
                
            # Add track to memory first
            track = Track(name, artist, rating)
            for _ in range(play_count):
                track.increment_play_count()
            self._library[track_id] = track
            
            # Save to CSV with UTF-8 encoding
            self._save_library_to_csv()
            self.notify_observers()
            return True
            
        except Exception as e:
            print(f"Error adding track: {str(e)}")
            return False

    def remove_track(self, track_id: str) -> bool:
        """
        Remove a track from the library and its audio file
        
        Args:
            track_id: The track ID to remove (will be padded to 2 digits)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Pad track_id to 2 digits
            track_id = str(track_id).zfill(2)
            
            # Check if track exists
            if track_id not in self._library:
                print(f"Track {track_id} not found")  # Notify if the track is not found
                return False  # Return failure
                
            # Get track info before removal (for confirmation message)
            track_name = self._library[track_id].name  # Get the track name
            track_artist = self._library[track_id].artist  # Get the track artist
                
            # Remove audio file if it exists
            tracks_dir = "tracks"  # Define the directory for tracks
            audio_removed = False  # Flag to check if audio file was removed
            for ext in ['.mp3', '.wav']:  # Check for both MP3 and WAV formats
                file_path = os.path.join(tracks_dir, f"track_{track_id}{ext}")  # Define the file path
                if os.path.exists(file_path):
                    os.remove(file_path)  # Remove the audio file
                    audio_removed = True  # Set flag to true if audio was removed
                    
            # Remove from CSV while preserving header and structure
            rows = []  # Initialize a list to hold CSV rows
            with open(self._library_file, 'r', newline='') as file:
                reader = csv.reader(file)  # Create a CSV reader
                header = next(reader)  # Save header
                rows.append(header)  # Add header to rows
                # Keep all rows except the one we want to remove
                rows.extend([row for row in reader if row[0] != track_id])  # Filter out the track to be removed
                        
            # Write back to CSV
            with open(self._library_file, 'w', newline='') as file:
                writer = csv.writer(file)  # Create a CSV writer
                writer.writerows(rows)  # Write all rows back to the CSV file
                
            # Update memory
            self.reload_library()  # Reload the library to reflect changes
            
            # Print success message
            print(f"Successfully removed track: {track_id} - {track_name} by {track_artist}")  # Notify success
            if audio_removed:
                print("Audio file was also removed")  # Notify if audio file was removed
            else:
                print("No audio file was found")  # Notify if no audio file was found
                
            return True  # Return success
            
        except Exception as e:
            print(f"Error removing track: {e}")  # Print error message if an exception occurs
            return False  # Return failure

    def _setup_file_watcher(self):
        """Setup watchdog observer for CSV file changes"""
        self.event_handler = CSVHandler(self)  # Create an instance of CSVHandler
        self.observer = Observer()  # Create an observer instance
        self.observer.schedule(self.event_handler, path='.', recursive=False)  # Schedule the event handler
        self.observer.start()  # Start the observer

    def add_observer(self, observer: LibraryObserver) -> None:
        """Add an observer to the library"""
        self._observers.append(observer)  # Append the observer to the list

    def remove_observer(self, observer: LibraryObserver) -> None:
        """Remove an observer from the library"""
        if observer in self._observers:
            self._observers.remove(observer)  # Remove the observer if it exists

    def notify_observers(self) -> None:
        """Notify all observers about library changes"""
        for observer in self._observers:
            observer.on_library_change()  # Call the on_library_change method for each observer

    def reload_library(self) -> None:
        """Reload library from CSV file"""
        try:
            current_modified = os.path.getmtime(self._library_file)  # Get the last modified time of the library file
            if current_modified > self._last_modified:  # Check if the file has been modified
                self._load_library_from_csv()  # Load the library from the CSV file
                self._last_modified = current_modified  # Update the last modified time
                self.notify_observers()  # Notify observers about the change
        except Exception as e:
            print(f"Error reloading library: {e}")  # Print error message if an exception occurs

    def _load_library_from_csv(self) -> None:
        """Load track data from CSV file with improved error handling"""
        if not os.path.exists(self._library_file):
            self._create_default_csv()
            return
            
        backup_created = False
        try:
            # Create backup if doesn't exist
            if not os.path.exists(self._library_file + '.bak'):
                import shutil
                shutil.copy2(self._library_file, self._library_file + '.bak')
                backup_created = True

            with open(self._library_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self._library.clear()
                for row in reader:
                    try:
                        track = Track(
                            name=row['name'],
                            artist=row['artist'],
                            rating=int(row['rating'])
                        )
                        for _ in range(int(row['play_count'])):
                            track.increment_play_count()
                        self._library[row['track_id']] = track
                    except Exception as row_error:
                        print(f"Error loading track {row.get('track_id', 'unknown')}: {str(row_error)}")
                        continue

        except Exception as e:
            print(f"Error loading library file: {str(e)}")
            # Try to restore from backup
            if not backup_created and os.path.exists(self._library_file + '.bak'):
                try:
                    import shutil
                    shutil.copy2(self._library_file + '.bak', self._library_file)
                    # Retry loading with backup
                    self._load_library_from_csv()
                except Exception as restore_error:
                    print(f"Error restoring from backup: {str(restore_error)}")
                    self._library.clear()

    def _save_library_to_csv(self) -> None:
        """Save current library state to CSV file with UTF-8 encoding and backup"""
        try:
            # Make backup before any changes
            if os.path.exists(self._library_file):
                backup_file = self._library_file + '.bak'
                import shutil
                shutil.copy2(self._library_file, backup_file)
            
            # Write to temporary file first
            temp_file = self._library_file + '.tmp'
            with open(temp_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['track_id', 'name', 'artist', 'rating', 'play_count'])
                
                track_ids = sorted(self._library.keys(), key=lambda x: int(x))
                for track_id in track_ids:
                    track = self._library[track_id]
                    writer.writerow([
                        str(track_id).zfill(2),
                        track.name,
                        track.artist,
                        track.rating,
                        track.play_count
                    ])

            # Only replace original file after successful write
            if os.path.exists(temp_file):
                os.replace(temp_file, self._library_file)
                
        except Exception as e:
            print(f"Error saving library file: {str(e)}")
            # Restore from backup if save failed
            try:
                if os.path.exists(self._library_file + '.bak'):
                    import shutil
                    shutil.copy2(self._library_file + '.bak', self._library_file)
                    self._load_library_from_csv()  # Reload library from backup
            except Exception as restore_error:
                print(f"Error restoring from backup: {str(restore_error)}")

    def _create_default_csv(self) -> None:
        """Create a new CSV file with UTF-8 encoding"""
        try:
            with open(self._library_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['track_id', 'name', 'artist', 'rating', 'play_count'])
        except Exception as e:
            print(f"Error creating default CSV: {str(e)}")

    def _initialize_library(self) -> None:
        """Initialize the library from CSV storage"""
        if not os.path.exists(self._library_file):  # Check if the library file exists
            self._create_default_csv()  # Create a default CSV file if it doesn't exist
        
        self._load_library_from_csv()  # Load the library from the CSV file
        self._last_modified = os.path.getmtime(self._library_file)  # Update the last modified time
        self.notify_observers()  # Notify observers about the initial load

    def set_rating(self, key: str, rating: int) -> None:
        """Set the rating for a specific track"""
        track = self._library.get(key)  # Get the track by key
        if track:  # Check if the track exists
            track.rating = rating  # Set the new rating
            self._save_library_to_csv()  # Save changes to the CSV
            self.notify_observers()  # Notify observers about the change

    def increment_play_count(self, key: str) -> None:
        """Increment the play count for a specific track"""
        track = self._library.get(key)  # Get the track by key
        if track:  # Check if the track exists
            track.increment_play_count()  # Increment the play count
            self._save_library_to_csv()  # Save changes to the CSV
            self.notify_observers()  # Notify observers about the change

    def list_all(self) -> str:
        """List all tracks in the library"""
        return "\n".join(item.info() for item in self._library.values())  # Return a string of all track info

    def get_name(self, key: str) -> Optional[str]:
        """Get the name of a track by its key"""
        track = self._library.get(key)  # Get the track by key
        return track.name if track else None  # Return the track name or None if not found

    def get_artist(self, key: str) -> Optional[str]:
        """Get the artist of a track by its key"""
        track = self._library.get(key)  # Get the track by key
        return track.artist if track else None  # Return the artist name or None if not found

    def get_rating(self, key: str) -> int:
        """Get the rating of a track by its key"""
        track = self._library.get(key)  # Get the track by key
        return track.rating if track else -1  # Return the rating or -1 if not found

    def get_play_count(self, key: str) -> int:
        """Get the play count of a track by its key"""
        track = self._library.get(key)  # Get the track by key
        return track.play_count if track else -1  # Return the play count or -1 if not found

    def search_tracks(self, query: str, search_type: str) -> List[Track]:
        """Search for tracks based on a query and search type"""
        query = query.lower()  # Convert query to lowercase for case-insensitive search
        results = []  # Initialize a list to hold search results
        
        for track in self._library.values():  # Iterate through all tracks in the library
            if search_type == "Track Name" and query in track.name.lower():
                results.append(track)  # Add track if name matches the query
            elif search_type == "Artist" and query in track.artist.lower():
                results.append(track)  # Add track if artist matches the query
            elif search_type == "Both" and (
                query in track.name.lower() or 
                query in track.artist.lower()
            ):
                results.append(track)  # Add track if either name or artist matches the query
        
        return results  # Return the list of matching tracks

    @property
    def library(self) -> Dict[str, Track]:
        """Get a copy of the current library"""
        return self._library.copy()  # Return a copy of the library dictionary

    def get_unique_artists(self) -> Set[str]:
        """Get list of unique artists in library"""
        return {track.artist for track in self._library.values()}  # Return a set of unique artist names

    def __del__(self):
        """Clean up the file observer when the library is destroyed"""
        if hasattr(self, 'observer'):
            self.observer.stop()  # Stop the observer if it exists
            self.observer.join()  # Wait for the observer thread to finish

# Create a single instance of the library
library = MusicLibrary()  # Instantiate the MusicLibrary class to create a library object