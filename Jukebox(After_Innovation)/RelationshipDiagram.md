# Class Relationships Diagram

```mermaid

classDiagram
    %% Abstract Base Classes
    class PlayerObserver {
        <<abstract>>
        +on_track_change(track_info)
        +on_playback_state_change(is_playing)
    }
    class LibraryObserver {
        <<abstract>>
        +on_library_change()
    }
    class PlaybackStrategy {
        <<abstract>>
        +get_next_track(playlist, current_index)
        +get_initial_track(playlist)
    }
    class MediaItem {
        <<abstract>>
        +name: str
        +artist: str
        +rating: int
        +play_count: int
        +get_name()
        +get_artist()
        +get_rating()
        +set_rating()
        +increment_play_count()
    }

    %% Concrete Classes
    class JukeboxApp {
        -player: MusicPlayer
        -library: MusicLibrary
        -playlist_manager: PlaylistManager
        -youtube_api: YouTubeAPI
        +initialize()
        +handle_track_selection()
        +update_display()
    }
    class MusicPlayer {
        -current_track
        -volume: float
        -is_playing: bool
        -strategy: PlaybackStrategy
        +play()
        +pause()
        +stop()
        +set_volume()
    }
    class Track {
        -file_path: str
        -duration: float
        +load()
        +get_duration()
    }
    class MusicLibrary {
        -tracks: Dict
        -observers: List
        +add_track()
        +remove_track()
        +get_track()
        +search_tracks()
    }
    class YouTubeAPI {
        +search_tracks()
        +download_track()
    }
    class PlaylistManager {
        -playlists: Dict
        +create_playlist()
        +load_playlist()
        +save_playlist()
    }
    class SequentialPlaybackStrategy {
        +get_next_track()
        +get_initial_track()
    }
    class RandomPlaybackStrategy {
        +get_next_track()
        +get_initial_track()
    }

    %% Relationships
    JukeboxApp ..|> PlayerObserver
    JukeboxApp ..|> LibraryObserver
    Track --|> MediaItem
    SequentialPlaybackStrategy --|> PlaybackStrategy
    RandomPlaybackStrategy --|> PlaybackStrategy
    JukeboxApp *-- MusicPlayer
    JukeboxApp *-- MusicLibrary
    JukeboxApp *-- PlaylistManager
    JukeboxApp *-- YouTubeAPI
    MusicLibrary "1" *-- "many" Track
    MusicPlayer --> PlaybackStrategy