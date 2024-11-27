import argparse
from track_library import library

def main():
    parser = argparse.ArgumentParser(description='Add a track to the jukebox library')
    parser.add_argument('track_id', help='Track ID (will be padded to 2 digits)')
    parser.add_argument('name', help='Track name')
    parser.add_argument('artist', help='Artist name')
    parser.add_argument('--rating', type=int, default=0, help='Initial rating (0-5)')
    parser.add_argument('--play-count', type=int, default=0, help='Initial play count')
    parser.add_argument('--file', help='Path to audio file (MP3 or WAV)', default=None)
    
    args = parser.parse_args()
    
    success = library.add_track(
        track_id=args.track_id,
        name=args.name,
        artist=args.artist,
        rating=args.rating,
        play_count=args.play_count,
        audio_file_path=args.file
    )
    
    if success:
        print("Track added successfully!")
    else:
        print("Failed to add track")

if __name__ == '__main__':
    main()