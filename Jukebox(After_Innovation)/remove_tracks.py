import argparse
from track_library import library

def main():
    parser = argparse.ArgumentParser(description='Remove a track from the jukebox library')
    parser.add_argument('track_id', help='Track ID to remove')
    
    args = parser.parse_args()
    
    # Ask for confirmation
    track_id = str(args.track_id).zfill(2)
    track = library.get_name(track_id)
    if track:
        artist = library.get_artist(track_id)
        print(f"Are you sure you want to remove track {track_id}?")
        print(f"Title: {track}")
        print(f"Artist: {artist}")
        confirm = input("Type 'yes' to confirm: ")
        
        if confirm.lower() == 'yes':
            success = library.remove_track(track_id)
            if success:
                print("Track removed successfully!")
            else:
                print("Failed to remove track")
        else:
            print("Operation cancelled")
    else:
        print(f"Track {track_id} not found")

if __name__ == '__main__':
    main()