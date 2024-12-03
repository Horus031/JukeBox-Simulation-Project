import os  # Import the os module for operating system dependent functionality
import asyncio  # Import asyncio for asynchronous programming
from googleapiclient.discovery import build  # Import build function to create a Google API client
from googleapiclient.errors import HttpError  # Import HttpError to handle API errors
from dotenv import load_dotenv
import yt_dlp  # Import yt-dlp for downloading videos from YouTube
import aiohttp  # Import aiohttp for making asynchronous HTTP requests
import subprocess  # Import subprocess to run external commands
import tkinter as tk  # Import tkinter for creating GUI applications
import customtkinter as ctk  # Import customtkinter for enhanced tkinter widgets
from customtkinter import CTkImage
import pygame  # Import pygame for multimedia applications (not used in this snippet)
import font_manager as fonts  # Import font manager for handling fonts
from threading import Thread  # Import Thread for running tasks in separate threads
from tkinter import messagebox  # Import messagebox for displaying message boxes in tkinter
from PIL import Image, ImageTk  # Import Image and ImageTk for image processing
from datetime import timedelta  # Import timedelta for handling time durations
from abc import ABC, abstractmethod  # Import ABC for creating abstract base classes
from typing import List, Tuple, Optional, Dict  # Import typing constructs for type hinting
from track_library import library, LibraryObserver  # Import library and observer classes for track management
from library_item import MusicPlayer, PlayerObserver, SequentialPlaybackStrategy, RandomPlaybackStrategy  # Import music player and playback strategies

# Your existing imports remain at the top
import os
import asyncio
# ... other imports ...

def initialize_application():
    """Initialize required directories and files"""
    # Get the directory containing the script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths for required directories
    required_dirs = {
        'tracks': os.path.join(current_dir, 'tracks'),
        'track_images': os.path.join(current_dir, 'track_images'),
        'playlists': os.path.join(current_dir, 'playlists')
    }
    
    # Create directories if they don't exist
    for directory in required_dirs.values():
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    # Return the paths dictionary for use in the application
    return required_dirs

class YouTubeAPI:  # Define YouTubeAPI class for interacting with YouTube API
    def __init__(self):
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            # Get API key from environment variable
            self.api_key = os.getenv('YOUTUBE_API_KEY')
            
            if not self.api_key:
                print("Warning: YouTube API key not found in environment variables")
                self.youtube = None
                return

            self.youtube = build('youtube', 'v3', developerKey=self.api_key)

            # Configure yt-dlp options
            self.ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'outtmpl': '%(title)s.%(ext)s',
                'default_search': 'auto',
                'ignoreerrors': True,
            }

        except Exception as e:
            print(f"Error initializing YouTube API: {e}")
            self.youtube = None

    async def search_tracks(self, query: str, max_results: int = 10) -> List[Dict]:  # Asynchronous method to search for tracks
        """ 
        Search for tracks on YouTube with improved Vietnamese language support 
        """ 
        if not self.youtube:  # Check if YouTube API client is initialized
            print("YouTube API not initialized")  # Print warning if not initialized
            return []  # Return empty list

        try:  # Try block to handle exceptions
            import sys  # Import sys for system-specific parameters
            if sys.platform == 'win32':  # Check if the platform is Windows
                sys.stdout.reconfigure(encoding='utf-8')  # Reconfigure stdout for UTF-8 encoding

            print(f"Searching YouTube for: {query}")  # Print search query

            # Perform search request to YouTube API
            search_response = self.youtube.search().list( 
                q=query,  # Set query parameter
                part='snippet',  # Specify the part of the response
                maxResults=max_results,  # Set maximum number of results
                type='video',  # Set the type to video
                videoCategoryId='10',  # Filter by music category
                fields='items(id/videoId,snippet(title,channelTitle,thumbnails/default/url))',  # Specify fields to return
                safeSearch='none',  # Disable safe search
                relevanceLanguage='vi',  # Set relevance language to Vietnamese
                regionCode='VN'  # Set region code to Vietnam
            ).execute()  # Execute the search request

            print(f"Search response received with {len(search_response.get('items', []))} results")  # Print number of results received

            tracks = []  # Initialize list to store track information
            for item in search_response.get('items', []):  # Iterate over each item in the search response
                try:  # Try block to handle exceptions
                    video_id = item['id']['videoId']  # Extract video ID from the item
                    
                    # Ensure proper encoding for title and channel name
                    title = item['snippet']['title'].encode('utf-8').decode('utf-8')  # Encode and decode title
                    channel = item['snippet']['channelTitle'].encode('utf-8').decode('utf-8')  # Encode and decode channel title
                    
                    # Request video details from YouTube API
                    video_response = self.youtube.videos().list(
                        part='contentDetails,statistics',  # Specify parts to return
                        id=video_id,  # Set video ID
                        fields='items(contentDetails/duration,statistics/viewCount)'  # Specify fields to return
                    ).execute()  # Execute the request
                    
                    if video_response['items']:  # Check if video details are available
                        video_details = video_response['items'][0]  # Get the first item
                        duration = video_details['contentDetails']['duration']  # Extract duration
                        view_count = int(video_details['statistics']['viewCount'])  # Extract view count

                        # Append track information to the list
                        tracks.append({
                            'track_id': video_id,  # Store video ID
                            'name': title,  # Store track title
                            'artist': channel,  # Store artist name
                            'thumbnail': item['snippet']['thumbnails']['default']['url'],  # Store thumbnail URL
                            'duration': self._parse_duration(duration),  # Parse and store duration
                            'views': view_count,  # Store view count
                            'url': f'https://www.youtube.com/watch?v={video_id}'  # Construct and store video URL
                        })
                except Exception as e:  # Catch any exceptions during processing
                    print(f"Error processing video {video_id}: {e}")  # Print error message
                    continue  # Continue to the next item

            print(f"Successfully processed {len(tracks)} tracks")  # Print number of successfully processed tracks
            return tracks  # Return the list of tracks

        except HttpError as e:  # Catch HTTP errors
            if e.resp.status == 403:  # Check for quota exceeded or invalid API key
                print("API quota exceeded or invalid API key")  # Print error message
            else:
                print(f"HTTP error occurred: {e}")  # Print other HTTP error messages
            return []  # Return empty list on error
        except Exception as e:  # Catch any other exceptions
            print(f"An error occurred during search: {str(e)}")  # Print error message
            return []  # Return empty list

    async def download_track(self, track_info: Dict):
        try:
            # Get the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Define complete paths for tracks and images directories
            tracks_dir = os.path.join(current_dir, 'tracks')
            images_dir = os.path.join(current_dir, 'track_images')
            
            # Create directories if they don't exist
            for directory in [tracks_dir, images_dir]:
                if not os.path.exists(directory):
                    os.makedirs(directory)

            # Get next available track ID
            existing_ids = [int(track_id) for track_id in library.library.keys()]
            next_id = str(max(existing_ids + [0]) + 1).zfill(2)
            
            # Define complete file paths
            audio_path = os.path.join(tracks_dir, f'track_{next_id}.mp3')
            image_path = os.path.join(images_dir, f'track_{next_id}.jpg')

            # Download thumbnail
            async with aiohttp.ClientSession() as session:
                async with session.get(track_info['thumbnail']) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        with open(image_path, 'wb') as f:
                            f.write(image_data)

            # Configure yt-dlp options with correct output path
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(tracks_dir, f'track_{next_id}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'writethumbnail': False,
                'default_search': 'auto',
                'ignoreerrors': True,
                'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe'  # Make sure this path is correct
            }

            try:
                # Check if FFmpeg is available
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)

                # Download and convert the audio
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(track_info['url'], download=True)
                    
                    # Wait briefly for file to be completely written
                    await asyncio.sleep(1)
                    
                    if info and os.path.exists(audio_path):
                        # Store observers and clear temporarily
                        observers = library._observers.copy()
                        library._observers.clear()
                        
                        # Add track to library with normalized fields
                        success = library.add_track(
                            track_id=next_id,
                            name=track_info['name'].strip(),
                            artist=track_info['artist'].strip(),
                            rating=0,
                            play_count=0
                        )
                        
                        # Restore observers
                        library._observers = observers
                        
                        if success:
                            messagebox.showinfo(
                                "Success",
                                f"Track '{track_info['name']}' downloaded successfully!"
                            )
                            library.notify_observers()
                        else:
                            for file_path in [audio_path, image_path]:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                            messagebox.showerror("Error", "Failed to add track to library")
                    else:
                        raise Exception("Download completed but audio file not found")

            except Exception as e:
                for file_path in [audio_path, image_path]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                messagebox.showerror("Download Error", f"Error during download: {str(e)}")

        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    def _parse_duration(self, duration: str) -> str:  # Method to parse YouTube duration format
        """Convert YouTube duration format to readable format"""
        import re  # Import regular expressions for parsing
        import datetime  # Import datetime for handling time

        # Remove 'PT' from start of duration
        duration = duration[2:]  # Remove 'PT' prefix
        
        # Initialize hours, minutes, seconds
        hours = 0  # Initialize hours
        minutes = 0  # Initialize minutes
        seconds = 0  # Initialize seconds
        
        # Find hours, minutes, seconds using regex
        hour_match = re.search(r'(\d+)H', duration)  # Search ```python
        hour_match = re.search(r'(\d+)H', duration)  # Search for hours in the duration string
        minute_match = re.search(r'(\d+)M', duration)  # Search for minutes in the duration string
        second_match = re.search(r'(\d+)S', duration)  # Search for seconds in the duration string
        
        if hour_match:  # Check if hours were found
            hours = int(hour_match.group(1))  # Convert hours to integer
        if minute_match:  # Check if minutes were found
            minutes = int(minute_match.group(1))  # Convert minutes to integer
        if second_match:  # Check if seconds were found
            seconds = int(second_match.group(1))  # Convert seconds to integer
            
        # Format duration string
        if hours > 0:  # If there are hours
            return f"{hours}:{minutes:02d}:{seconds:02d}"  # Return formatted string with hours
        else:  # If there are no hours
            return f"{minutes}:{seconds:02d}"  # Return formatted string without hours

class SearchResultsFrame(ctk.CTkFrame):  # Define SearchResultsFrame class for displaying search results
    """Enhanced frame for displaying YouTube search results"""
    def __init__(self, master, youtube_api):  # Constructor for SearchResultsFrame
        super().__init__(master)  # Call parent constructor
        self.youtube_api = youtube_api  # Store reference to YouTube API
        self.setup_ui()  # Setup UI components
        
    def setup_ui(self):  # Method to setup UI components
        ''' Add header frame for loading indicator and close button '''
        self.header_frame = ctk.CTkFrame(self)  # Create header frame
        self.header_frame.pack(fill="x", padx=5, pady=2)  # Pack header frame
        
        # Add a loading indicator
        self.loading_label = ctk.CTkLabel(  # Create loading label
            self,
            text="Searching...",  # Set label text
            font=("Helvetica", 14)  # Set font style and size
        )
        
        # Add close button
        self.close_btn = ctk.CTkButton(  # Create close button
            self.header_frame,
            text="✖",  # Set button text
            width=30,  # Set button width
            height=30,  # Set button height
            command=self.hide_results,  # Set command to hide results
            fg_color="red",  # Set foreground color
            hover_color="darkred"  # Set hover color
        )
        self.close_btn.pack(side="right", padx=5, pady=5)  # Pack close button to the right
        
        # Results scrollable frame
        self.results_frame = ctk.CTkScrollableFrame(  # Create scrollable frame for results
            self,
            width=600,  # Set width
            height=400  # Set height
        )
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)  # Pack results frame
        
    def show_loading(self, show: bool = True):  # Method to show or hide loading indicator
        """Show or hide loading indicator"""
        if show:  # If showing loading
            self.loading_label.pack(side="left", pady=5, padx=5)  # Pack loading label
            self.results_frame.pack_forget()  # Hide results frame
        else:  # If not showing loading
            self.loading_label.pack_forget()  # Hide loading label
            self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)  # Show results frame
    
    def hide_results(self):  # Method to hide search results frame
        """Hide the search results frame"""
        self.pack_forget()  # Hide the frame
        library.reload_library()  # Reload the library directly
        
    def show_results(self):  # Method to show search results frame
        """Show the search results frame"""
        self.pack(fill="both", expand=True, padx=10, pady=5)  # Pack the frame
    
    def display_results(self, results: List[Dict]):  # Method to display search results
        # Clear previous results
        for widget in self.results_frame.winfo_children():  # Iterate over existing widgets
            widget.destroy()  # Destroy each widget
            
        # Display each result
        for track in results:  # Iterate over each track in results
            try:  # Try block to handle exceptions
                # Create result frame
                result_frame = ctk.CTkFrame(self.results_frame)
                result_frame.pack(fill="x", padx=5, pady=5)  # Pack result frame
                
                # Track info with proper encoding
                info_text = (  # Prepare track information text
                    f"{track['name']}\n"  # Track name
                    f"By: {track['artist']}\n"  # Artist name
                    f"Duration: {track['duration']} • Views: {self._format_views(track['views'])}"  # Duration and views
                ).encode('utf-8').decode('utf-8')  # Ensure proper encoding
                
                info_label = ctk.CTkLabel(  # Create label for track info
                    result_frame,
                    text=info_text,  # Set label text
                    justify="left",  # Left justify text
                    anchor="w",  # Anchor to the west (left)
                    wraplength=500  # Set wrap length for long titles
                )
                info_label.pack(side="left", padx=10, fill="x", expand=True)  # Pack info label
                
                download_btn = ctk.CTkButton(  # Create download button
                    result_frame,
                    text="⬇ Download",  # Set button text
                    command=lambda t=track: self.handle_download(t),  # Set command to handle download
                    width=100  # Set button width
                )
                download_btn.pack(side="right", padx=10)  # Pack download button to the right
            except Exception as e:  # Catch any exceptions during display
                print(f"Error displaying track: {str(e)}")  # Print error message
            
    def handle_download(self, track_info: Dict) -> None:  # Method to handle track download
        """Wrapper to handle async download"""
        def run_async():  # Define inner function to run async download
            loop = asyncio.new_event_loop()  # Create new event loop
            asyncio.set_event_loop(loop)  # Set the new event loop
            try:  # Try block to handle exceptions
                # Show download progress
                progress_window = self._create_progress_window(track_info['name'])  # Create progress window
                
                try:  # Try block to handle download
                    # Run the download
                    loop.run_until_complete(self.youtube_api.download_track(track_info))  # Await download completion
                    
                except Exception as e:  # Catch any exceptions during download
                    messagebox.showerror("Download Error", f"Error during download: {str(e)}")  # Show error message
                finally:  # Finally block to ensure cleanup
                    # Always close progress window
                    progress_window.destroy()  # Destroy progress window
                    
            finally:  # Finally block to ensure event loop closure
                loop.close()  # Close the event loop
        
        # Run in a separate thread
        download_thread = Thread(target=run_async)  # Create a thread for async download
        download_thread.daemon = True  # Set thread as daemon
        download_thread.start()  # Start the download thread
            
    def _format_views(self, views: int) -> str:  # Method to format view count
        """Format view count to readable format"""
        if views >= 1_000_000_000:  # Check for billions
            return f"{views/1_000_000_000:.1f}B"  # Format as billions
        elif views >= 1_000_000:  # Check for millions
            return f"{views/1_000_000:.1f}M"  # Format as millions
        elif views >= 1_000:  # Check for thousands
            return f"{views/1_000:.1f}K"  # Format as thousands
        return str(views)  # Return as string if less than a thousand
            
    def _create_progress_window(self, track_name: str) -> tk.Toplevel:  # Method to create a progress window
        """Create a progress window for download"""
        progress_window = tk.Toplevel()  # Create a new top-level window
        progress_window.title("Downloading...")  # Set window title
        progress_window.geometry("300x100")  # Set window size
        
        # Center the window
        progress_window.geometry("+%d+%d" % (  # Center the window on the screen
            progress_window.winfo_screenwidth()/2 - 150,  # Calculate x position
            progress_window.winfo_screenheight()/2 - 50  # Calculate y position
        ))
        
        # Add progress message
        message = ctk.CTkLabel(  # Create label for download message
            progress_window,
            text=f"Downloading:\n{track_name}..."
        )  # Set label text
        message.pack(pady=20)  # Pack the message label with padding
        
        # Add progress bar
        progress = ctk.CTkProgressBar(progress_window)  # Create a progress bar
        progress.pack(pady=10)  # Pack the progress bar with padding
        progress.start()  # Start the progress animation
        
        return progress_window  # Return the created progress window

class UIComponent(ABC):  # Define abstract base class for UI components
    """Base class for UI components"""
    def __init__(self, master: tk.Widget):  # Constructor for UIComponent
        self._master = master  # Store reference to master widget
        self._widget: Optional[tk.Widget] = None  # Initialize widget as None

    @abstractmethod
    def create(self) -> None:  # Abstract method to create UI component
        pass

    @property
    def widget(self) -> tk.Widget:  # Property to get the widget
        return self._widget  # Return the widget

class PlayerControls(UIComponent):  # Define PlayerControls class for player controls
    """UI component for player controls"""
    def __init__(self, master: tk.Widget, player: MusicPlayer):  # Constructor for PlayerControls
        super().__init__(master)  # Call parent constructor
        self._player = player  # Store reference to MusicPlayer
        self.create()  # Create UI components

    def create(self) -> None:  # Method to create UI components
        self._widget = ctk.CTkFrame(self._master)  # Create frame for controls
        
        # Create other control buttons
        for symbol, command in [  # List of control symbols and their commands
            ("⏮", lambda: self._player.play_previous()),  # Previous track button
            ("⏸", lambda: self._player.toggle_playback()),  # Play/Pause button
            ("⏹", self._player.stop),  # Stop button
            ("⏭", lambda: self._player.play_next())  # Next track button
        ]:
            btn = ctk.CTkButton(  # Create button for each control
                self._widget,
                text=symbol,  # Set button text
                command=command,  # Set button command
                width=40,  # Set button width
                height=40  # Set button height
            )
            btn.pack(side="left", padx=5)  # Pack button to the left with padding

class PlaylistManager:  # Define PlaylistManager class for managing playlists
    """Manages multiple playlist files and their operations"""
    def __init__(self):
        # Get the directory containing the script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Set the playlists directory path relative to the script location
        self.playlists_dir = os.path.join(current_dir, "playlists")
        
        # Only create directory if it doesn't exist at this specific path
        if not os.path.exists(self.playlists_dir):
            os.makedirs(self.playlists_dir)

    def get_all_playlists(self):  # Method to get all playlists
        """Get list of all playlist files"""
        try:  # Try block to handle exceptions
            return [f for f in os.listdir(self.playlists_dir)  # List all files in playlists directory
                   if f.endswith('.txt')]  # Filter for .txt files
        except Exception as e:  # Catch any exceptions
            print(f"Error listing playlists: {e}")  # Print error message
            return []  # Return empty list

    def load_playlist(self, playlist_name):
        """Load a specific playlist file with UTF-8 encoding"""
        try:
            playlist = []
            file_path = os.path.join(self.playlists_dir, playlist_name)
            with open(file_path, "r", encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(" - ", 1)
                    if len(parts) == 2:
                        playlist.append((parts[0], parts[1]))
            return playlist
        except Exception as e:
            print(f"Error loading playlist {playlist_name}: {e}")
            return []

    def save_playlist(self, playlist_name, tracks):
        """Save playlist to a specific file with UTF-8 encoding"""
        try:
            # Ensure .txt extension
            if not playlist_name.endswith('.txt'):
                playlist_name += '.txt'
            
            file_path = os.path.join(self.playlists_dir, playlist_name)
            
            # First write to a temporary file
            temp_file = file_path + '.tmp'
            try:
                with open(temp_file, "w", encoding='utf-8', newline='') as f:
                    for track_id, track_name in tracks:
                        f.write(f"{track_id} - {track_name}\n")
                
                # If temporary file was written successfully, replace the original file
                os.replace(temp_file, file_path)
                return True
            except Exception as e:
                # Clean up temporary file if it exists
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e
                
        except Exception as e:
            print(f"Error saving playlist {playlist_name}: {e}")
            return False

    def delete_playlist(self, playlist_name):  # Method to delete a playlist file
        """Delete a playlist file"""
        try:  # Try block to handle exceptions
            file_path = os.path.join(self.playlists_dir, playlist_name)  # Construct file path
            if os.path.exists(file_path):  # Check if file exists
                os.remove(file_path)  # Remove the file
                return True  # Return success
        except Exception as e:  # Catch any exceptions
            print(f"Error deleting playlist {playlist_name}: {e}")  # Print error message
        return False  # Return failure

class PlaylistDialog:  # Define PlaylistDialog class for managing playlists
    """Dialog for managing playlists"""
    def __init__(self, master, playlist_manager, app):  # Constructor for PlaylistDialog
        self.dialog = ctk.CTkToplevel(master)  # Create a new top-level dialog
        self.dialog.title("Playlist Manager")  # Set dialog title
        self.dialog.geometry("600x400")  # Set dialog size
        self.dialog.transient(master)  # Set dialog as transient to master
        self.dialog.grab_set()  # Grab focus for the dialog
        
        self.playlist_manager = playlist_manager  # Store reference to PlaylistManager
        self.app = app  # Store reference to main application
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (  # Center the dialog on the screen
            master.winfo_rootx() + master.winfo_width()//2 - 300,  # Calculate x position
            master.winfo_rooty() + master.winfo_height()//2 - 200  # Calculate y position
        ))
        
        self._setup_ui()  # Setup UI components
        self._load_playlists()  # Load available playlists

    def _setup_ui(self):  # Method to setup UI components
        # Left side - Playlist list
        list_frame = ctk.CTkFrame(self.dialog)  # Create frame for playlist list
        list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)  # Pack list frame
        
        # Playlist list label
        ctk.CTkLabel(  # Create label for available playlists
            list_frame,
            text="Available Playlists",  # Set label text
            font=("Helvetica", 14, "bold")  # Set font style and size
        ).pack(pady=5)  # Pack label with padding
        
        # Playlist listbox
        self.playlist_list = ctk.CTkTextbox(list_frame, width=200, height=300)  # Create textbox for playlist list
        self.playlist_list.pack(fill="both", expand=True, pady=5)  # Pack textbox
        
        # Right side - Actions
        action_frame = ctk.CTkFrame(self.dialog)  # Create frame for action buttons
        action_frame.pack(side="right", fill="both", padx=10, pady=10)  # Pack action frame
        
        # Action buttons
        buttons = [  # List of action buttons and their commands
            ("Load", self._load_selected_playlist),  # Load button
            ("Save Current", self._save_current_playlist),  # Save current button
            ("Save As...", self._save_as_playlist),  # Save as button
            ("Delete", self._delete_selected_playlist),  # Delete button
            ("Close", self.dialog.destroy)  # Close button
        ]
        
        for text, command in buttons:  # Iterate over buttons
            ctk.CTkButton(  # Create button
                action_frame,
                text=text,  # Set button text
                command=command,  # Set button command
                width=150  # Set button width
            ).pack(pady=5)  # Pack button with padding

    def _load_playlists(self):  # Method to load and display available playlists
        """Load and display available playlists"""
        playlists = self.playlist_manager.get_all_playlists()  # Get all playlists
        self.playlist_list.delete("0.0", "end")  # Clear existing playlist list
        for playlist in playlists:  # Iterate over playlists
            self.playlist_list.insert("end", f"{playlist}\n")  # Insert each playlist into the list

    def _get_selected_playlist(self):  # Method to get the currently selected playlist name
        """Get the currently selected playlist name"""
        try:  # Try block to handle exceptions
            cursor_pos = self.playlist_list.index("insert")  # Get cursor position
            line = self.playlist_list.get(f"{cursor_pos} linestart", f"{cursor_pos} lineend")  # Get the line at cursor
            return line.strip()  # Return the selected playlist name
        except:  # Catch any exceptions
            return None  # Return None if no selection

    def _load_selected_playlist(self):  # Method to load the selected playlist into the main application
        """Load the selected playlist into the main application"""
        selected = self._get_selected_playlist()  # Get selected playlist
        if not selected:  # Check if no selection
            messagebox.showwarning("No Selection", "Please select a playlist to load")  # Show warning
            return  # Exit method
            
        tracks = self.playlist_manager.load_playlist(selected)  # Load the selected playlist
        if tracks:  # Check if tracks were loaded
            self.app.playlist = tracks  # Update app's playlist
            self.app.current_playlist_name = selected  # Store the current playlist name
            self.app._set_text(  # Update playlist display
                self.app.playlist_txt,
                "\n".join(name for _, name in tracks)  # Join track names for display
            )
            self.app.status_lbl.configure(text=f"Loaded playlist: {selected}")  # Update status label
            self.dialog.destroy()  # Close the dialog
        else:  # If loading failed
            messagebox.showerror("Error", f"Failed to load playlist: {selected}")  # Show error message

    def _save_current_playlist(self):  # Method to save to currently loaded playlist
        """Save to currently loaded playlist"""
        if not self.app.playlist:  # Check if playlist is empty
            messagebox.showwarning("Empty Playlist", "Cannot save an empty playlist")  # Show warning
            return  # Exit method
            
        if not hasattr(self.app, 'current_playlist_name') or not self.app.current_playlist_name:  # Check if no playlist is loaded
            self._save_as_playlist()  # Redirect to Save As
            return  # Exit method
            
        if messagebox.askyesno(  # Confirm overwrite
            "Confirm Save",
            f"Save changes to playlist '{self.app.current_playlist_name}'?"
        ):
            if self.playlist_manager.save_playlist(self.app.current_playlist_name, self.app.playlist):  # Save playlist
                messagebox.showinfo("Success", f"Playlist saved as {self.app.current_playlist_name}")  # Show success message
                self._load_playlists()  # Refresh the list
            else:  # If saving failed
                messagebox.showerror("Error", f"Failed to save playlist {self.app.current_playlist_name}")  # Show error message

    def _save_as_playlist(self):  # Method to save current playlist with a new name
        """Save current playlist with a new name"""
        if not self.app.playlist:  # Check if playlist is empty
            messagebox.showwarning("Empty Playlist", "Cannot save an empty playlist")  # Show warning
            return  # Exit method
            
        save_dialog = ctk.CTkInputDialog(  # Create save dialog
            text="Enter playlist name:",  # Set dialog text
            title="Save Playlist As"  # Set dialog title
        )
        playlist_name = save_dialog.get_input()  # Get input from dialog
        
        if playlist_name:  # Check if input is provided
            if not playlist_name.endswith('.txt'):  # Ensure .txt extension
                playlist_name += '.txt'  # Add .txt extension
                
            if os.path.exists(os.path.join(self.playlist_manager.playlists_dir, playlist_name)):  # Check if file exists
                if not messagebox.askyesno(  # Confirm overwrite
                    "Confirm Overwrite",
                    f"Playlist {playlist_name} already exists. Overwrite?"
                ):
                    return  # Exit method
                    
            # Save playlist
            if self.playlist_manager.save_playlist(playlist_name, self.app.playlist):  # Save playlist with new name
                self.app.current_playlist_name = playlist_name  # Update current playlist name
                messagebox.showinfo("Success", f"Playlist saved as {playlist_name}")  # Show success message
                self._load_playlists()  # Refresh the playlist list
            else:  # If saving failed
                messagebox.showerror("Error", f"Failed to save playlist {playlist_name}")  # Show error message

    def _delete_selected_playlist(self):  # Method to delete the selected playlist
        """Delete the selected playlist"""
        selected = self._get_selected_playlist()  # Get selected playlist
        if not selected:  # Check if no selection
            messagebox.showwarning("No Selection", "Please select a playlist to delete")  # Show warning
            return  # Exit method
            
        if messagebox.askyesno("Confirm Delete", f"Delete playlist {selected}?"):  # Confirm deletion
            if self.playlist_manager.delete_playlist(selected):  # Delete the playlist
                self._load_playlists()  # Refresh the playlist list
                messagebox.showinfo("Success", f"Deleted playlist: {selected}")  # Show success message
            else:  # If deletion failed
                messagebox.showerror("Error", f"Failed to delete playlist: {selected}")  # Show error message

class JukeboxApp(PlayerObserver, LibraryObserver):  # Define JukeboxApp class for the main application
    """Main application class implementing observer patterns"""
    def __init__(self):  # Constructor for JukeboxApp
        pygame.mixer.init()
        self.window = ctk.CTk()  # Create main application window
        self.window.geometry("1920x1080")  # Set window size
        self.window.attributes('-fullscreen', True)  # Make window fullscreen
        self.playlist_manager = PlaylistManager()  # Initialize PlaylistManager
        self.window.bind('<Escape>', lambda e: self.window.attributes('-fullscreen', False))  # Bind escape key to exit fullscreen
        self._updating_rating = False
        self.app_dirs = initialize_application()

        # Set the default color theme
        ctk.set_appearance_mode("dark")  # Set appearance mode to dark
        ctk.set_default_color_theme("blue")  # Set default color theme to blue

        # Create main container frame
        self.main_frame = ctk.CTkFrame(self.window)  # Create main frame
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)  # Pack main frame
        
        # Initialize core components
        self.player = MusicPlayer(SequentialPlaybackStrategy())  # Initialize music player with sequential strategy
        self.player.add_observer(self)  # Add observer to player
        self.playlist: List[Tuple[str, str]] = []  # Initialize playlist
        self.current_playlist_name: Optional[str] = None  # Initialize current playlist name
        
        # Add as library observer
        library.add_observer(self)  # Add observer to library
        
        # Configure fonts
        fonts.configure()  # Configure fonts
        
        # Initialize YouTube API
        self.youtube_api = YouTubeAPI()  # Create YouTube API instance
        
        # Setup UI
        self._setup_ui()  # Setup user interface
        
    async def global_search_tracks(self):  # Asynchronous method to perform global search using YouTube API
        """Perform global search using YouTube API"""
        try:  # Try block to handle exceptions
            search_term = self.youtube_search_entry.get().strip()  # Get search term from entry
            
            if not search_term:  # Check if search term is empty
                messagebox.showwarning("Empty Search", "Please enter a search term")  # Show warning
                return  # Exit method
                
            # Show loading state
            self.search_results.show_loading(True)  # Show loading indicator
            self.search_results.show_results()  # Show results frame
            
            # Ensure proper encoding for search term
            encoded_search = search_term.encode('utf-8').decode('utf-8')  # Encode search term
            
            # Perform search
            results = await self.youtube_api.search_tracks(encoded_search)  # Await search results
            
            # Hide loading state
            self.search_results.show_loading(False)  # Hide loading indicator
            
            if results:  # Check if results were found
                self.search_results.display_results(results)  # Display search results
                self.status_lbl.configure(text=f"Found {len(results)} tracks on YouTube")  # Update status label
            else:  # If no results found
                self.status_lbl.configure(text="No tracks found on YouTube")  # Update status label
                self.search_results.display_results([])  # Display empty results
            
        except Exception as e:  # Catch any exceptions during search
            print(f"Search error details: {str(e)}")  # Print error details
            messagebox.showerror("Search Error", f"Error searching YouTube: {str(e)}")  # Show error message
            self.search_results.show_loading(False)  # Hide loading indicator

    def on_track_change(self, track_info: str) -> None:  # Method to handle track change updates
        """Handle track change updates"""
        if hasattr(self, 'track_info'):  # Check if track_info attribute exists
            self.track_info.configure(text=track_info)  # Update track info label

    def on_playback_state_change(self, is_playing: bool) -> None:  # Method to handle playback state changes
        """Handle playback state changes"""
        if not is_playing:  # If playback is not playing
            # Reset progress bar and time label when playback stops
            self.progress_scale.set(0)  # Reset progress scale
            self.time_label.configure(text="0:00 / 0:00")  # Reset time label

    def on_library_change(self) -> None:
        """Handle library updates"""
        # Get current status text
        current_status = self.status_lbl.cget("text")
        
        # If it's a rating update, don't change the status or refresh
        if "Updated rating for" in current_status:
            return
            
        # Only refresh track list if not playing a playlist
        if not self.player.is_playing:
            if "Showing" in current_status:
                self.apply_filter()  # Maintain the current filter
            else:
                self.list_tracks_clicked()  # Refresh the entire list

    def _set_text(self, text_area: ctk.CTkTextbox, content: str) -> None:  # Helper method to set text in a text area
        """Helper method to set text in a text area"""
        text_area.delete("0.0", tk.END)  # Clear existing text
        text_area.insert("0.0", content)  # Insert new content

    def _load_track_image(self, track_number: str) -> Optional[ctk.CTkImage]:
        """Load image for a given track number using CTkImage"""
        try:
            image_path = None
            current_dir = os.path.dirname(os.path.abspath(__file__))
            track_images_dir = os.path.join(current_dir, 'track_images')
            
            for ext in ['.png', '.jpg', '.jpeg']:
                potential_path = os.path.join(track_images_dir, f'track_{track_number}{ext}')
                if os.path.exists(potential_path):
                    image_path = potential_path
                    break
            
            if image_path:
                pil_image = Image.open(image_path)
                return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
            else:
                default_path = os.path.join(track_images_dir, 'default.png')
                if os.path.exists(default_path):
                    default_image = Image.open(default_path)
                    return ctk.CTkImage(light_image=default_image, dark_image=default_image, size=(100, 100))
                return None
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    def _load_default_image(self) -> None:
        """Load default image for track display using CTkImage"""
        default_image = self._load_track_image('default')
        if default_image:
            self.image_label.configure(image=default_image)
            # No need to keep a reference as CTkImage handles this internally

    def list_tracks_clicked(self) -> None:
        """Handler for List All Tracks button with improved error handling"""
        try:
            self.status_lbl.configure(text="Displaying Track List")
            self.list_txt.delete("0.0", tk.END)
            
            # Get all tracks and sort by track ID
            sorted_tracks = []
            for key in sorted(library.library.keys(), key=lambda x: int(x)):
                track = library.library[key]
                if track and track.name and track.artist:  # Ensure valid track data
                    sorted_tracks.append(track.info())
            
            if sorted_tracks:
                self._set_text(self.list_txt, "\n".join(sorted_tracks))
                
                # Store the mapping for track selection
                self._filtered_tracks = {
                    f"{library.get_name(key)} - {library.get_artist(key)}": key
                    for key in library.library.keys()
                    if library.get_name(key) and library.get_artist(key)
                }
            else:
                self._set_text(self.list_txt, "No tracks available")
                self._filtered_tracks = {}
                
        except Exception as e:
            print(f"Error listing tracks: {e}")
            self._set_text(self.list_txt, "Error listing tracks")
            self._filtered_tracks = {}

    def search_tracks(self) -> None:  # Method to search tracks based on criteria
        """Search tracks based on criteria"""
        search_term = self.search_entry.get().lower().strip()  # Get search term
        search_type = self.search_var.get()  # Get selected search type
        
        if not search_term:  # Check if search term is empty
            self.list_tracks_clicked()  # If empty, display all tracks
            return  # Exit method

        results = []  # Initialize list to store search results
        for key in library.library.keys():  # Iterate over all track keys in the library
            track_name = library.get_name(key)  # Get track name
            artist_name = library.get_artist(key)  # Get artist name
            
            if track_name and artist_name:  # Check if both track and artist names are available
                track_info = f"{track_name} - {artist_name}"  # Format track info
                
                if search_type == "Track Name" and search_term in track_name.lower():  # Search by track name
                    results.append(track_info)  # Add to results
                elif search_type == "Artist" and search_term in artist_name.lower():  # Search by artist
                    results.append(track_info)  # Add to results
                elif search_type == "Both" and (  # Search by both
                    search_term in track_name.lower() or 
                    search_term in artist_name.lower()
                ):
                    results.append(track_info)  # Add to results
        
        if results:  # Check if any results were found
            self._set_text(self.list_txt, "\n".join(results))  # Display results
            self.status_lbl.configure(text=f"Found {len(results)} matches")  # Update status label
        else:  # If no matches found
            self.status_lbl.configure(text="No matches found")  # Update status label
            self._set_text(self.list_txt, "No matches found")  # Display no matches message

    def clear_search(self) -> None:  # Method to clear search results
        """Clear search results"""
        self.search_entry.delete(0, tk.END)  # Clear search entry
        self.list_tracks_clicked()  # Display all tracks
        self.status_lbl.configure(text="Search cleared")  # Update status label

    def apply_filter(self, *args) -> None:
        """Apply selected filter to track list while preserving original track information"""
        filter_type = self.filter_var.get()
        results = []

        try:
            if filter_type == "No Filter":
                for key in sorted(library.library.keys(), key=lambda x: int(x)):
                    name = library.get_name(key)
                    artist = library.get_artist(key)
                    if name and artist:  # Only include tracks with valid info
                        track_info = f"{name} - {artist}"
                        results.append((track_info, key, name, artist))
            
            elif filter_type == "Most Played" or filter_type == "Least Played":
                tracks = [(key, library.get_name(key), library.get_artist(key), library.get_play_count(key)) 
                        for key in library.library.keys()]
                # Only include tracks with valid info
                tracks = [t for t in tracks if all(x is not None for x in t[1:3])]
                tracks.sort(key=lambda x: x[3], reverse=(filter_type == "Most Played"))
                for track_id, name, artist, count in tracks:
                    track_info = f"{name} - {artist} (Plays: {count})"
                    results.append((track_info, track_id, name, artist))
                    
            elif filter_type in ["Highest Rated", "Lowest Rated"]:
                tracks = [(key, library.get_name(key), library.get_artist(key), library.get_rating(key)) 
                        for key in library.library.keys()]
                # Only include tracks with valid info
                tracks = [t for t in tracks if all(x is not None for x in t[1:3])]
                tracks.sort(key=lambda x: x[3], reverse=(filter_type == "Highest Rated"))
                for track_id, name, artist, rating in tracks:
                    track_info = f"{name} - {artist} (Rating: {rating})"
                    results.append((track_info, track_id, name, artist))

            # Clear and update display
            self.list_txt.delete("0.0", tk.END)
            for display_text, _, _, _ in results:
                self.list_txt.insert(tk.END, f"{display_text}\n")
            
            # Store the mapping for later use when adding tracks
            self._filtered_tracks = {
                f"{name} - {artist}": track_id 
                for _, track_id, name, artist in results
            }
            
            self.status_lbl.configure(
                text=f"Showing {len(results)} tracks" + 
                    (f" for filter: {filter_type}" if filter_type != "No Filter" else "")
            )
        except Exception as e:
            print(f"Error applying filter: {e}")
            self.list_txt.delete("0.0", tk.END)
            self.list_txt.insert(tk.END, "Error displaying tracks")
            self._filtered_tracks = {}

    def _get_filter_options(self) -> List[str]:  # Method to get list of filter options
        """Get list of filter options"""
        options = ["No Filter"]  # Initialize options list
        
        # Add play count and rating sort options
        options.extend([  # Extend options list with additional filters
            "Most Played",  # Most played filter
            "Least Played",  # Least played filter
            "Highest Rated",  # Highest rated filter
            "Lowest Rated"  # Lowest rated filter
        ])
        
        return options  # Return the list of filter options

    def view_tracks_clicked(self) -> None:  # Method to view selected track details
        """View selected track details"""
        try:  # Try block to handle exceptions
            # Get selected line
            selection = self.list_txt.selection_get() if self.list_txt.tag_ranges("sel") else ""  # Get selected text
            if not selection:  # If no selection, get the line at cursor
                cursor_pos = self.list_txt.index("insert")  # Get cursor position
                selection = self.list_txt.get(f"{cursor_pos} linestart", f"{cursor_pos} lineend")  # Get the line at cursor
            
            if not selection.strip():  # Check if selection is empty
                messagebox.showwarning("No Selection", "Please select a track first")  # Show warning
                return  # Exit method
                
            # Remove any trailing stars (ratings) from the selection
            base_selection = selection.rstrip("* ")  # Strip trailing stars
            
            # Find matching track in library
            for track_id, track in library.library.items():  # Iterate over library tracks
                track_text = f"{track.name} - {track.artist}"  # Format track text
                if track_text == base_selection:  # Check if track matches selection
                    rating = library.get_rating(track_id)  # Get track rating
                    play_count = library.get_play_count(track_id)  # Get play count
                    track_details = f"{track.name}\n{track.artist}\nrating: {rating}\nplays: {play_count}"  # Format track details
                    self._set_text(self.track_txt, track_details)  # Set text in track details textbox
                    
                    track_image = self._load_track_image(track_id)  # Load track image
                    if track_image:  # If image is loaded
                        self.image_label.configure(image=track_image)  # Set image label to track image
                        self.image_label.image = track_image  # Keep reference to avoid garbage collection
                    
                    self.status_lbl.configure(text="Track details displayed")  # Update status label ```python
                    self.status_lbl.configure(text="Track details displayed")  # Update status label to indicate track details are displayed
                    return  # Exit method after displaying track details
                    
            messagebox.showerror("Error", "Could not find track in library")  # Show error if track not found
            
        except Exception as e:  # Catch any exceptions
            messagebox.showerror("Error", f"An error occurred: {str(e)}")  # Show error message
            self._set_text(self.track_txt, "Track not found")  # Set track details textbox to indicate track not found
            self._load_default_image()  # Load default image if track not found

    def view_playlists_clicked(self):  # Method to view playlists
        """Handler for View Playlists button"""
        PlaylistDialog(self.window, self.playlist_manager, self)  # Open PlaylistDialog

    def update_rating_clicked(self) -> None:  # Method to update track rating
        """Update track rating"""
        try:
            self._updating_rating = True
            track_number = self.track_id_entry.get().strip()  # Get track number from entry
            new_rating = self.rating_input_entry.get().strip()  # Get new rating from entry

            if track_number.isdigit() and len(track_number) == 1:  # Check if track number is a single digit
                track_number = track_number.zfill(2)  # Pad track number with leading zero
            
            if not new_rating.isdigit() or not 1 <= int(new_rating) <= 5:  # Validate new rating
                self.status_lbl.configure(text="Error: Please enter a valid rating (1-5).")  # Show error message
                return  # Exit method

            if not track_number.isdigit() or not library.get_name(track_number):  # Validate track number
                self.status_lbl.configure(text="Error: Track number not found. Please enter a valid track number.")  # Show error message
                return  # Exit method

            library.set_rating(track_number, int(new_rating))  # Set new rating in library
            track_name = library.get_name(track_number)  # Get track name

            self.status_lbl.configure(text=f"Successfully updated: Track: {track_name} - New Rating: {new_rating}")  # Update status label
            
            self.track_id_entry.delete(0, "end")  # Clear track ID entry
            self.rating_input_entry.delete(0, "end")  # Clear rating input entry
            
        except Exception as e:
            print(f"Error updating rating: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._updating_rating = False  # Reset flag after update

    def update_rating_from_selection(self):
        """Update rating for selected track with improved error handling"""
        try:
            self._updating_rating = True
            # Get current cursor position
            cursor_pos = self.list_txt.index("insert")
            # Get the line at cursor position
            selection = self.list_txt.get(f"{cursor_pos} linestart", f"{cursor_pos} lineend").strip()

            if not selection:
                messagebox.showwarning("No Selection", "Please select a track first")
                return

            # Create rating dialog with safety checks
            rating_dialog = ctk.CTkToplevel(self.window)
            rating_dialog.title("Update Rating")
            rating_dialog.geometry("300x150")
            rating_dialog.transient(self.window)
            rating_dialog.grab_set()

            # Center dialog
            rating_dialog.geometry(f"+{self.window.winfo_x() + 150}+{self.window.winfo_y() + 150}")

            # Clean up selection - remove ratings and parenthetical info
            base_selection = selection.split(' (')[0].strip()
            base_selection = base_selection.rstrip('* ')

            # Track display
            track_label = ctk.CTkLabel(rating_dialog, text=base_selection)
            track_label.pack(pady=10)

            # Rating buttons
            rating_var = ctk.IntVar(value=1)
            rating_frame = ctk.CTkFrame(rating_dialog)
            rating_frame.pack(pady=10)
            rating_btns = []

            def update_button_colors(selected_value):
                rating_var.set(selected_value)
                for btn, value in zip(rating_btns, range(1, 6)):
                    if value <= selected_value:
                        btn.configure(fg_color="green", hover_color="darkgreen")
                    else:
                        btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])

            for i in range(1, 6):
                btn = ctk.CTkButton(
                    rating_frame,
                    text="★",
                    width=40,
                    command=lambda v=i: update_button_colors(v)
                )
                btn.pack(side="left", padx=5)
                rating_btns.append(btn)

            def update_rating():
                try:
                    new_rating = rating_var.get()
                    if not 1 <= new_rating <= 5:
                        messagebox.showerror("Invalid Rating", "Rating must be between 1 and 5")
                        return

                    found = False
                    # Search through library for matching track
                    library_snapshot = library.library.copy()  # Work with a copy
                    for track_id in sorted(library_snapshot.keys(), key=lambda x: int(x)):
                        track = library_snapshot[track_id]
                        track_text = f"{track.name} - {track.artist}"

                        if track_text == base_selection:
                            found = True
                            # Update rating with error handling
                            try:
                                library.set_rating(track_id, new_rating)
                                self.status_lbl.configure(text=f"Updated rating for {track.name} to {new_rating} stars")
                                
                                # Update track details if they're being viewed
                                rating = library.get_rating(track_id)
                                play_count = library.get_play_count(track_id)
                                track_details = f"{track.name}\n{track.artist}\nrating: {rating}\nplays: {play_count}"
                                self._set_text(self.track_txt, track_details)

                                # Refresh the track listing without modifying the CSV directly
                                if "Showing" in self.status_lbl.cget("text"):
                                    self.apply_filter()
                                else:
                                    self.list_tracks_clicked()
                                break
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to update rating: {str(e)}")
                                return

                    if not found:
                        messagebox.showerror("Error", "Could not find track in library")
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")
                finally:
                    rating_dialog.destroy()

            # Update button
            update_btn = ctk.CTkButton(
                rating_dialog,
                text="Update",
                command=update_rating,
                width=100
            )
            update_btn.pack(pady=10)

        except Exception as e:
            print(f"Error updating rating: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._updating_rating = False  # Reset flag after update

    def _update_rating_inline(self):
        """Safely update rating for currently viewed track"""
        try:
            cursor_pos = self.list_txt.index("insert")
            current_line = self.list_txt.get(f"{cursor_pos} linestart", f"{cursor_pos} lineend").strip()
            
            if not current_line:
                messagebox.showerror("Error", "Please select a track first")
                return

            def reset_stars():
                # Reset all stars to default color
                self.rating_var.set(1)  # Reset to default value
                for btn in self.rating_btns:
                    btn.configure(
                        fg_color=["#3B8ED0", "#1F6AA5"],
                        hover_color=["#36719F", "#144870"]
                    )

            # Get base selection (song name + artist)
            base_selection = current_line
            # Remove any parenthetical info (plays, rating)
            if " (Plays:" in base_selection:
                base_selection = base_selection.split(" (Plays:")[0].strip()
            elif " (Rating:" in base_selection:
                base_selection = base_selection.split(" (Rating:")[0].strip()
            # Remove any trailing stars
            base_selection = base_selection.rstrip('*').strip()

            new_rating = self.rating_var.get()
            if not 1 <= new_rating <= 5:
                messagebox.showerror("Invalid Rating", "Rating must be between 1 and 5")
                return

            update_successful = False
            # Search through library
            for track_id in sorted(library.library.keys(), key=lambda x: int(x)):
                track = library.library[track_id]
                track_text = f"{track.name} - {track.artist}"
                
                if track_text == base_selection:
                    # Store cursor position and selected track info
                    current_pos = cursor_pos
                    
                    # Update rating
                    library.set_rating(track_id, new_rating)
                    
                    # Set the status text
                    status_text = f"Succesfully updated rating for {track.name} to {new_rating} stars"
                    
                    # Update the display without triggering list_tracks_clicked
                    current_view = "Showing" in self.status_lbl.cget("text")
                    if current_view:
                        self.apply_filter()
                    else:
                        # Update the track list while preserving the status
                        self.list_txt.delete("0.0", tk.END)
                        sorted_tracks = []
                        for key in sorted(library.library.keys(), key=lambda x: int(x)):
                            track = library.library[key]
                            if track and track.name and track.artist:
                                sorted_tracks.append(track.info())
                        if sorted_tracks:
                            self._set_text(self.list_txt, "\n".join(sorted_tracks))
                            
                    # Restore cursor position
                    self.list_txt.mark_set("insert", current_pos)
                    self.list_txt.see("insert")
                    
                    # Set the status text AFTER all updates
                    self.status_lbl.configure(text=status_text)
                    
                    # Reset stars to default state after successful update
                    self.window.after(500, reset_stars)  # Reset after a short delay for better visual feedback
                    
                    update_successful = True
                    break

            if not update_successful:
                messagebox.showerror("Error", "Could not find track in library")
                reset_stars()  # Also reset stars if update failed

        except Exception as e:
            print(f"Error updating rating: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            reset_stars()  # Reset stars in case of error
                                                      
    def _update_cursor_position(self, event):
        """Update the cursor position when clicking in the track list"""
        self.list_txt.focus_set()
        # Get the index under the mouse
        index = self.list_txt.index(f"@{event.x},{event.y}")
        # Move cursor to clicked line
        self.list_txt.mark_set("insert", index)

    def add_track_clicked(self) -> None:  # Method to add a track to the playlist
        """Add a track to the playlist"""
        track_number = self.track_input.get().strip()  # Get track number from input
        
        if track_number.isdigit() and len(track_number) == 1:  # Check if track number is a single digit
            track_number = track_number.zfill(2)  # Pad track number with leading zero
            
        if not track_number.isdigit():  # Validate track number
            messagebox.showerror("Invalid Input", "Please enter a valid track number.")  # Show error message
            return  # Exit method

        if any(track[0] == track_number for track in self.playlist):  # Check if track is already in the playlist
            messagebox.showinfo("Duplicate Track", "Track is already in the playlist!")  # Show info message
            return  # Exit method

        track_name = library.get_name(track_number)  # Get track name from library
        track_artist = library.get_artist(track_number)  # Get artist name from library
        
        if track_name and track_artist:  # Check if track and artist names are available
            self.playlist.append((track_number, track_name))  # Add track to playlist
            
            # Update playlist display with track numbers and names
            playlist_display = "\n".join(f"{num} - {name}" for num, name in self.playlist)  # Format playlist display
            self._set_text(self.playlist_txt, playlist_display)  # Set text in playlist textbox
            
            self.status_lbl.configure(text=f"Added track: {track_name} - {track_artist}")  # Update status label
            
            self.track_input.delete(0, tk.END)  # Clear input field
        else:  # If no track found
            messagebox.showerror("Track Not Found", "No track found for the given number.")  # Show error message

    def add_selected_track(self) -> None:
        try:
            # Get selected line from text widget
            selection = self.list_txt.selection_get() if self.list_txt.tag_ranges("sel") else ""
            if not selection:
                cursor_pos = self.list_txt.index("insert")
                selection = self.list_txt.get(f"{cursor_pos} linestart", f"{cursor_pos} lineend")
            
            if not selection.strip():
                messagebox.showwarning("No Selection", "Please select a track first")
                return
            
            # Clean up the selection - remove any info in parentheses and trailing stars
            base_selection = selection.split(" (")[0].strip().rstrip("*").strip()
            
            # Try to find track_id using the filtered_tracks mapping
            track_id = None
            if hasattr(self, '_filtered_tracks'):
                # Loop through filtered tracks to find a match
                for track_text, tid in self._filtered_tracks.items():
                    cleaned_track_text = track_text.split(" (")[0].strip().rstrip("*").strip()
                    if cleaned_track_text == base_selection:
                        track_id = tid
                        break
            
            # If not found in filtered tracks, search through library
            if not track_id:
                for key, track in library.library.items():
                    track_text = f"{track.name} - {track.artist}"
                    if track_text == base_selection:
                        track_id = key
                        break
            
            if track_id:
                track = library.library[track_id]
                
                # Check for duplicate
                if any(track_id == t[0] for t in self.playlist):
                    messagebox.showinfo("Duplicate Track", "Track is already in the playlist!")
                    return
                
                # Add to playlist
                self.playlist.append((track_id, track.name))
                self._set_text(self.playlist_txt, "\n".join(name for _, name in self.playlist))
                self.status_lbl.configure(text=f"Added track: {track.name} - {track.artist}")
                
                # Show track details
                rating = library.get_rating(track_id)
                play_count = library.get_play_count(track_id)
                track_details = f"{track.name}\n{track.artist}\nrating: {rating}\nplays: {play_count}"
                self._set_text(self.track_txt, track_details)
                
                # Load and display track image
                track_image = self._load_track_image(track_id)
                if track_image:
                    self.image_label.configure(image=track_image)
                    self.image_label.image = track_image
            else:
                print(f"Debug - Base selection: '{base_selection}'")
                print("Debug - Available tracks:", {k: f"{v.name} - {v.artist}" for k,v in library.library.items()})
                messagebox.showerror("Error", "Could not find track in library")
                    
        except Exception as e:
            print(f"Error adding track: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self._set_text(self.track_txt, "Track not found")
            self._load_default_image()

    def play_playlist_clicked(self) -> None:
        """Start playlist playback"""
        if not self.playlist:  # Check if playlist is empty
            messagebox.showwarning("Empty Playlist", "Please add tracks to the playlist before playing.")
            return

        # Configure player before starting playback
        self.player.set_track_info_callback(self.update_track_info)

        # Temporarily store observers and clear them to prevent list_tracks_clicked from being called
        observers = self.player._observers.copy()
        self.player._observers.clear()
        
        try:
            # Start playlist playback
            self.player.play_playlist(self.playlist.copy())
            self.status_lbl.configure(text="Playing playlist...")
            
            if self.playlist:
                first_track = self.playlist[0][0]
                track_name = library.get_name(first_track)
                artist_name = library.get_artist(first_track)
                self.track_info.configure(text=f"Now Playing: {track_name} - {artist_name}")
                
                # Reset progress indicators
                self.progress_scale.set(0)
                self.time_label.configure(text="0:00 / 0:00")
        finally:
            # Restore observers
            self.player._observers = observers

    def reset_playlist_clicked(self) -> None:  # Method to reset playlist
        """Reset playlist and clear current playlist name"""
        self.playlist.clear()  # Clear all tracks from playlist
        self.current_playlist_name = None  # Clear current playlist name
        self._set_text(self.playlist_txt, "")  # Clear playlist display
        self.status_lbl.configure(text="Playlist reset.")  # Update status label

    def remove_track_clicked(self) -> None:  # Method to remove track from playlist
        try:  # Try block to handle potential errors
            # Get cursor position
            current_pos = self.playlist_txt.index("insert")  # Get current cursor position
            # Get line at cursor
            line = self.playlist_txt.get(f"{current_pos} linestart", f"{current_pos} lineend")  # Get entire line at cursor
            if not line.strip():  # If line is empty or only whitespace
                messagebox.showwarning("No Selection", "Please select a track to remove.")  # Show warning dialog
                return  # Exit the method

            # Find and remove track from playlist
            for track_id, name in self.playlist:  # Iterate through playlist
                if name == line.strip():  # If track name matches selected line
                    # Remove track and keep all others
                    self.playlist = [track for track in self.playlist if track[0] != track_id]  # Filter out the selected track
                    self._set_text(self.playlist_txt, "\n".join(name for _, name in self.playlist))  # Update playlist display
                    self.status_lbl.configure(text=f"Removed track: {line}")  # Update status label
                    return  # Exit the method

            messagebox.showerror("Error", "Could not find track to remove")  # Show error if track not found
                
        except Exception as e:  # Catch any exceptions that occur
            messagebox.showerror("Error", f"An error occurred: {str(e)}")  # Show error dialog with details

    def save_playlist_clicked(self) -> None:  # Method to save playlist to file
        """Save playlist to file"""
        with open("playlist.txt", "w") as f:  # Open file for writing
            for track in self.playlist:  # Iterate through playlist
                f.write(f"{track[0]} - {track[1]}\n")  # Write each track to file
        self.status_lbl.configure(text="Playlist saved.")  # Update status label

    def load_playlist_clicked(self) -> None:  # Method to load playlist from file
        """Load playlist from file"""
        try:  # Try block to handle potential errors
            with open("playlist.txt", "r") as f:  # Open file for reading
                # Parse each line into tuple of (track_id, name) and store in playlist
                self.playlist = [tuple(line.strip().split(" - ")) for line in f]  # Load playlist from file
            self._set_text(self.playlist_txt, "\n".join(f"{num} - {name}" for num, name in self.playlist))  # Update playlist display
            self.status_lbl.configure(text="Playlist loaded.")  # Update status label
        except FileNotFoundError:  # If playlist file doesn't exist
            messagebox.showerror("File Not Found", "No saved playlist found.")  # Show error dialog

    def format_time(self, seconds):  # Method to format time in seconds to MM:SS
        """Convert seconds to MM:SS format"""
        return str(timedelta(seconds=int(seconds)))[2:7]  # Convert seconds to timedelta and format as MM:SS

    def _start_progress_update(self):  # Method to start progress update loop
        """Start the progress update loop"""
        def update():  # Inner function for continuous updates
            if self.player.is_playing or pygame.mixer.music.get_busy():  # If music is playing
                try:  # Try block to handle potential errors
                    # Calculate current position
                    current_pos = pygame.mixer.music.get_pos() / 1000.0  # Get current position in seconds
                    current_pos += self.player._current_position  # Add stored position for accurate tracking
                    track_length = self.player._track_length  # Get total track length
                    
                    if track_length > 0 and current_pos >= 0:  # If valid position and length
                        # Update progress bar
                        progress = (current_pos / track_length) * 100  # Calculate progress percentage
                        self.progress_scale.set(progress)  # Update progress bar
                        
                        # Update time display
                        self.time_label.configure(  # Update time label with current and total time
                            text=f"{self.format_time(current_pos)} / {self.format_time(track_length)}"
                        )
                        
                        # Handle track end
                        if current_pos >= track_length:  # If track has ended
                            self.progress_scale.set(0)  # Reset progress bar
                            self.time_label.configure(text="0:00 / 0:00")  # Reset time display
                except Exception as e:  # Catch any exceptions during update
                    print(f"Error updating progress: {e}")  # Print error message
            
            # Schedule next update
            self.window.after(100, update)  # Schedule next update in 100ms
        
        update()  # Start the update loop

    def on_progress_click(self, event) -> None:  # Method to handle progress bar clicks
        """Handle click on progress bar"""
        if self.player.is_playing and self.player._track_length > 0:  # If music is playing
            widget_width = self.progress_scale.winfo_width()  # Get progress bar width
            relative_pos = event.x / widget_width  # Calculate relative position of click
            target_pos = relative_pos * self.player._track_length  # Calculate target position in seconds
            self.player.seek_to_position(target_pos)  # Seek to target position
            
    def on_progress_drag(self, event) -> None:  # Method to handle progress bar dragging
        """Handle dragging the progress slider"""
        if self.player.is_playing and self.player._track_length > 0:  # If music is playing
            widget_width = self.progress_scale.winfo_width()  # Get progress bar width
            relative_pos = max(0, min(1, event.x / widget_width))  # Calculate and clamp relative position
            target_pos = relative_pos * self.player._track_length  # Calculate target position in seconds
            self.progress_scale.set(relative_pos * 100)  # Update progress bar position
            self.player.seek_to_position(target_pos)  # Seek to target position

    def update_volume(self, value) -> None:  # Method to update player volume
        """Update player volume"""
        volume = float(value) / 100  # Convert percentage to decimal
        self.player.set_volume(volume)  # Set player volume
    
    # Creating UI
    def _setup_ui(self):
        # Create left and right container frames
        left_frame = ctk.CTkFrame(self.main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        
        right_frame = ctk.CTkFrame(self.main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10)
        
        # Configure grid weights
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # Create header frame to contain both title and close button
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=20, sticky="ew")
        
        # Header label
        self.header_lbl = ctk.CTkLabel(
            header_frame,
            text="Jukebox Application",
            font=("Helvetica", 24, "bold")
        )
        self.header_lbl.pack(side="left", padx=20)
        
        # Close button
        close_btn = ctk.CTkButton(
            header_frame,
            text="✖",
            width=40,
            height=40,
            command=self.window.destroy,
            fg_color="red",
            hover_color="darkred"
        )
        close_btn.pack(side="right", padx=20)

        # Left frame components
        self._create_search_filter_frame(left_frame)
        self._create_track_listing_frame(left_frame)
        self._create_track_viewer(left_frame)

        # Right frame components
        self._create_playlist_frame(right_frame)
        self._create_player_frame(right_frame)
        
        # Status label at bottom
        self._create_status_label()
        
        # Start progress update
        self._start_progress_update()
        
        # Initialize search results frame with proper error handling
        try:
            if not self.youtube_api.youtube:
                messagebox.showwarning(
                    "YouTube API Not Available",
                    "YouTube search functionality is not available. Please check your API key."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error initializing YouTube API: {str(e)}")

    def run_async(self, coro):
        """Run an async operation in the Tkinter event loop"""
        async def wrapper():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                await coro
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                loop.close()
        
        # Run in separate thread to not block GUI
        Thread(target=lambda: asyncio.run(wrapper())).start()

    def on_global_search(self):
        """Handle global search button click"""
        if not self.youtube_api.youtube:
            messagebox.showwarning(
                "YouTube API Not Available",
                "YouTube search functionality is not available. Please check your API key."
            )
            return
            
        search_term = self.youtube_search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Empty Search", "Please enter a search term")
            return
            
        self.search_results.show_loading(True)
        self.search_results.show_results()  # Use new method
        self.run_async(self.global_search_tracks())

    def _create_search_filter_frame(self, parent):
        search_filter_frame = ctk.CTkFrame(parent)
        search_filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Add YouTube search section
        youtube_frame = ctk.CTkFrame(search_filter_frame)
        youtube_frame.pack(fill="x", padx=10, pady=5)
        
        youtube_label = ctk.CTkLabel(youtube_frame, text="YouTube Search:", anchor="w")
        youtube_label.pack(side="left", padx=5)
        
        self.youtube_search_entry = ctk.CTkEntry(youtube_frame, width=200)
        self.youtube_search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            youtube_frame,
            text="🔍 Search YouTube",
            command=self.on_global_search,
            width=120
        ).pack(side="left", padx=5)
        
        # Create search results frame
        self.search_results = SearchResultsFrame(search_filter_frame, self.youtube_api)
        
        # Search controls
        search_frame = ctk.CTkFrame(search_filter_frame)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        # Search type
        search_label = ctk.CTkLabel(search_frame, text="Search in:", anchor="w")
        search_label.pack(side="left", padx=5)
        
        self.search_var = ctk.StringVar(value="Both")
        self.search_type = ctk.CTkOptionMenu(
            search_frame,
            variable=self.search_var,
            values=["Track Name", "Artist", "Both"],
            width=120
        )
        self.search_type.pack(side="left", padx=5)
        
        # Search entry
        search_term_label = ctk.CTkLabel(search_frame, text="Search term:", anchor="w")
        search_term_label.pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, width=200)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_tracks())
        
        # Search buttons
        ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            command=self.search_tracks,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            search_frame,
            text="❌ Clear",
            command=self.clear_search,
            width=100
        ).pack(side="left", padx=5)
        
        # Filter controls
        filter_frame = ctk.CTkFrame(search_filter_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        filter_label = ctk.CTkLabel(filter_frame, text="Filter by:", anchor="w")
        filter_label.pack(side="left", padx=5)
        
        self.filter_var = ctk.StringVar(value="No Filter")
        self.filter_type = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.filter_var,
            values=self._get_filter_options(),
            width=200
        )
        self.filter_type.configure(command=lambda choice: self.apply_filter())  # Changed this line
        self.filter_type.pack(side="left", padx=5)

    def _create_track_listing_frame(self, parent):
        track_frame = ctk.CTkFrame(parent)
        track_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Track controls frame
        controls_frame = ctk.CTkFrame(track_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            controls_frame,
            text="View Track",
            command=self.view_tracks_clicked,
            width=100
        ).pack(side="left", padx=5)

        # Add to Playlist button
        ctk.CTkButton(
            controls_frame,
            text="Add Selected to Playlist",
            command=self.add_selected_track,
            width=150
        ).pack(side="left", padx=5)
        
        # List tracks button
        self.view_tracks_btn = ctk.CTkButton(
            track_frame,
            text="List All Tracks",
            command=self.list_tracks_clicked,
            width=200
        )
        self.view_tracks_btn.pack(pady=10)
        
        # Track list
        self.list_txt = ctk.CTkTextbox(
            track_frame,
            width=400,
            height=150
        )
        self.list_txt.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bind click events to update selection and handle double-clicks
        self.list_txt.bind('<Button-1>', self._update_cursor_position)
        self.list_txt.bind('<Double-Button-1>', lambda e: self.add_selected_track())  # Fix here - properly bind double-click

    def _create_track_viewer(self, parent):
        viewer_frame = ctk.CTkFrame(parent)
        viewer_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side: Track info and image
        info_frame = ctk.CTkFrame(viewer_frame)
        info_frame.pack(side="left", fill="x",expand=True, padx=5, pady=5)
        
        self.track_txt = ctk.CTkTextbox(
            info_frame,
            width=200,
            height=100,
            wrap="none"
        )
        self.track_txt.pack(side="left", padx=5)
        
        self.image_label = ctk.CTkLabel(info_frame, text="")
        self.image_label.pack(side="left", padx=5)
        
        # Right side: Rating controls
        rating_frame = ctk.CTkFrame(viewer_frame)
        rating_frame.pack(side="right", fill="y",padx=5, pady=5)
        
        rating_label = ctk.CTkLabel(rating_frame, text="Update Rating")
        rating_label.pack(pady=5)
        
        # Rating buttons frame
        buttons_frame = ctk.CTkFrame(rating_frame)
        buttons_frame.pack(pady=5)
        
        self.rating_var = ctk.IntVar(value=1)
        self.rating_btns = []
        
        def update_button_colors(selected_value):
            self.rating_var.set(selected_value)
            for btn, value in zip(self.rating_btns, range(1, 6)):
                if value <= selected_value:
                    btn.configure(fg_color="green", hover_color="darkgreen")
                else:
                    btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
        
        # Create rating buttons
        for i in range(1, 6):
            btn = ctk.CTkButton(
                buttons_frame,
                text="★",
                width=30,
                command=lambda v=i: update_button_colors(v)
            )
            btn.pack(side="left", padx=10)
            self.rating_btns.append(btn)
        
        # Update button
        update_btn = ctk.CTkButton(
            rating_frame,
            text="Update Rating",
            command=self._update_rating_inline,
            width=120
        )
        update_btn.pack(pady=10)
        
    def _create_playlist_frame(self, parent):
        """Modified _create_playlist_frame method for JukeboxApp"""
        playlist_frame = ctk.CTkFrame(parent)
        playlist_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Playlist controls
        controls_frame = ctk.CTkFrame(playlist_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Initialize playlist manager
        self.playlist_manager = PlaylistManager()
        
        button_configs = [
            ("▶ Play", self.play_playlist_clicked, "green"),
            ("⏹ Reset", self.reset_playlist_clicked, "red"),
            ("❌ Remove", self.remove_track_clicked, None),
            ("📂 View Playlists", self.view_playlists_clicked, None)
        ]
        
        for text, command, color in button_configs:
            kwargs = {"fg_color": color} if color else {}
            ctk.CTkButton(
                controls_frame,
                text=text,
                command=command,
                width=120 if text == "View Playlists" else 100,
                **kwargs
            ).pack(side="left", padx=5)
        
        # Playlist display
        self.playlist_txt = ctk.CTkTextbox(
            playlist_frame,
            width=480,
            height=300,
            wrap="none"
        )
        self.playlist_txt.pack(fill="both", expand=True, padx=10, pady=5)

    def _create_player_frame(self, parent):
        player_frame = ctk.CTkFrame(parent)
        player_frame.pack(fill="x", padx=10, pady=5)
        
        # Now Playing section
        self.track_info = ctk.CTkLabel(
            player_frame,
            text="No track playing",
            font=("Helvetica", 14))
        self.track_info.pack(fill="x", padx=10, pady=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(player_frame)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_scale = ctk.CTkSlider(
            progress_frame,
            from_=0,
            to=100,
            orientation="horizontal"
        )
        self.progress_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_scale.set(0)
        self.progress_scale.bind("<Button-1>", self.on_progress_click)
        self.progress_scale.bind("<B1-Motion>", self.on_progress_drag)
        
        self.time_label = ctk.CTkLabel(
            progress_frame,
            text="0:00 / 0:00",
            width=100
        )
        self.time_label.pack(side="right", padx=5)
        
        # Use PlayerControls class
        controls = PlayerControls(player_frame, self.player)
        
        # Volume control
        volume_frame = ctk.CTkFrame(controls.widget)
        volume_frame.pack(side="right", padx=20)
        
        ctk.CTkLabel(
            volume_frame,
            text="🔊",
            font=("Helvetica", 14)
        ).pack(side="left", padx=5)
        
        volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=100,
            command=self.update_volume,
            width=120
        )
        volume_slider.pack(side="left", padx=5)
        volume_slider.set(70)
        
        controls.widget.pack(fill="x", padx=10, pady=5)
        
        # Add strategy selection
        strategy_frame = ctk.CTkFrame(player_frame)
        strategy_frame.pack(fill="x", padx=10, pady=5)

        # Create strategy instances once and reuse them
        self.strategies = {
            "Sequential": SequentialPlaybackStrategy(),
            "Random": RandomPlaybackStrategy(),
        }

        def change_strategy(*args):
            selected = strategy_var.get()
            self.player._strategy = self.strategies[selected]
            # If currently playing, restart with new strategy
            if self.player._is_playing:
                self.player.play_playlist(self.playlist.copy())

        strategy_var = ctk.StringVar(value="Sequential")
        strategy_menu = ctk.CTkOptionMenu(
            strategy_frame,
            variable=strategy_var,
            values=list(self.strategies.keys()),
            command=change_strategy
        )
        strategy_menu.pack(side="right", padx=5)

        ctk.CTkLabel(
            strategy_frame,
            text="Playback Mode:"
        ).pack(side="right", padx=5)

    def _create_status_label(self):
        self.status_lbl = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Helvetica", 12))
        self.status_lbl.grid(row=2, column=0, columnspan=2, pady=10)

    def update_track_info(self, text: str) -> None:  # Method to update track info display
        """Update track info display"""
        if self.track_info:  # If track info label exists
            self.track_info.configure(text=text)  # Update display text


# Initialize and run the application
if __name__ == "__main__":
    app = JukeboxApp()
    app.window.mainloop()