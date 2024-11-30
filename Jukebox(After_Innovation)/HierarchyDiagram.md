# Class Hierarchy Diagram

```mermaid
classDiagram
    %% Abstract Classes
    class ABC {
        <<Abstract>>
    }
    class LibraryObserver {
        <<Abstract>>
        +on_library_change()*
    }
    class PlayerObserver {
        <<Abstract>>
        +on_track_change(track_info)*
        +on_playback_state_change(is_playing)*
    }
    class PlaybackStrategy {
        <<Abstract>>
        +get_next_track(playlist, current_index)*
        +get_initial_track(playlist)*
    }
    class MediaItem {
        <<Abstract>>
        -name: str
        -artist: str
        -rating: int
        -play_count: int
        +get_name()
        +get_artist()
        +set_rating()
        +increment_play_count()
    }

    %% Concrete Classes
    class Track {
        +name: str
        +artist: str
        +rating: int
    }

    class MusicLibrary {
        -library: Dict
        -observers: List
        +add_track()
        +remove_track()
        +set_rating()
        +get_name()
        +get_artist()
    }

    class MusicPlayer {
        -is_playing: bool
        -current_track: str
        -strategy: PlaybackStrategy
        +play_single_track()
        +play_playlist()
        +toggle_playback()
        +seek_to_position()
    }

    class JukeboxApp {
        -player: MusicPlayer
        -library: MusicLibrary
        -youtube_api: YouTubeAPI
        +play_playlist()
        +add_track()
        +search_tracks()
    }

    class YouTubeAPI {
        -api_key: str
        +search_tracks()
        +download_track()
    }

    class SearchResultsFrame {
        -youtube_api: YouTubeAPI
        +display_results()
        +handle_download()
    }

    class PlaylistManager {
        -playlists_dir: str
        +get_all_playlists()
        +save_playlist()
        +load_playlist()
    }

    class SequentialPlaybackStrategy {
        +get_next_track()
        +get_initial_track()
    }

    class RandomPlaybackStrategy {
        +get_next_track()
        +get_initial_track()
    }

    %% Inheritance Relationships
    ABC <|-- LibraryObserver
    ABC <|-- PlayerObserver
    ABC <|-- PlaybackStrategy
    ABC <|-- MediaItem
    MediaItem <|-- Track
    LibraryObserver <|-- JukeboxApp
    PlayerObserver <|-- JukeboxApp
    PlaybackStrategy <|-- SequentialPlaybackStrategy
    PlaybackStrategy <|-- RandomPlaybackStrategy

    %% Composition/Association Relationships
    JukeboxApp *-- MusicPlayer : has
    JukeboxApp *-- MusicLibrary : uses
    JukeboxApp *-- YouTubeAPI : uses
    JukeboxApp *-- PlaylistManager : uses
    MusicPlayer o-- PlaybackStrategy : uses
    SearchResultsFrame o-- YouTubeAPI : uses
    MusicLibrary o-- Track : contains