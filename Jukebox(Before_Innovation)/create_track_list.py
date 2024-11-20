import tkinter as tk
import tkinter.scrolledtext as tkst
from tkinter import messagebox
import track_library as lib
import font_manager as fonts

# Utility function to set text in a text area
def set_text(text_area, content):
    text_area.delete("1.0", tk.END)
    text_area.insert(1.0, content)

class CreateTrackList:
    def __init__(self, window):
        self.window = window
        window.geometry("800x400")
        window.title("Create Track List")
        
        # Frame for Track Input
        input_frame = tk.Frame(window)
        input_frame.pack(pady=10)

        enter_lbl = tk.Label(input_frame, text="Enter Track Number")
        enter_lbl.grid(row=0, column=0, padx=10)
        self.track_input = tk.Entry(input_frame, width=5)
        self.track_input.grid(row=0, column=1, padx=10)
        add_track_btn = tk.Button(input_frame, text="Add Track", command=self.add_track_clicked)
        add_track_btn.grid(row=0, column=2, padx=10)

        # Frame for Playlist Display
        playlist_frame = tk.Frame(window)
        playlist_frame.pack(pady=10)

        self.playlist_txt = tkst.ScrolledText(playlist_frame, width=60, height=10, wrap="none")
        self.playlist_txt.pack()

        # Frame for Control Buttons
        control_frame = tk.Frame(window)
        control_frame.pack(pady=10)

        play_playlist_btn = tk.Button(control_frame, text="Play Playlist", command=self.play_playlist_clicked)
        play_playlist_btn.grid(row=0, column=0, padx=10)
        reset_playlist_btn = tk.Button(control_frame, text="Reset Playlist", command=self.reset_playlist_clicked)
        reset_playlist_btn.grid(row=0, column=1, padx=10)
        
        # Additional buttons for removing tracks and saving/loading
        remove_track_btn = tk.Button(control_frame, text="Remove Track", command=self.remove_track_clicked)
        remove_track_btn.grid(row=0, column=2, padx=10)
        save_playlist_btn = tk.Button(control_frame, text="Save Playlist", command=self.save_playlist_clicked)
        save_playlist_btn.grid(row=0, column=3, padx=10)
        load_playlist_btn = tk.Button(control_frame, text="Load Playlist", command=self.load_playlist_clicked)
        load_playlist_btn.grid(row=0, column=4, padx=10)
        
        # Status label
        self.status_lbl = tk.Label(window, text="", font=("Helvetica", 10))
        self.status_lbl.pack(pady=10)

        # Initialize playlist as an empty list
        self.playlist = []
        
    def add_track_clicked(self):
        track_number = self.track_input.get()
        if not track_number.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid track number.")
            return

        if not lib.get_name(track_number):
            messagebox.showerror("Invalid Track", "Track number does not exist.")
            return

        if track_number in self.playlist:
            messagebox.showwarning("Track Exists", "This track is already in the playlist.")
            return

        self.playlist.append(track_number)
        # Show track name in playlist
        track_name = lib.get_name(track_number)
        playlist_display = "\n".join([f"{num} - {lib.get_name(num)}" for num in self.playlist])
        set_text(self.playlist_txt, playlist_display)
        self.track_input.delete(0, tk.END)
        self.status_lbl.config(text=f"Track {track_name} added to the playlist.")

    def play_playlist_clicked(self):
        if not self.playlist:
            messagebox.showwarning("Empty Playlist", "No tracks to play.")
            return

        # Increment play count for each track
        for track_number in self.playlist:
            lib.increment_play_count(track_number)
            
        self.status_lbl.config(text="Playing playlist... Play counts incremented.")

    def reset_playlist_clicked(self):
        self.playlist.clear()  # Clear the playlist
        set_text(self.playlist_txt, "")  # Clear the text area
        self.status_lbl.config(text="Playlist reset.")  # Update the status label

    def remove_track_clicked(self):
        track_number = self.track_input.get()
        if track_number in self.playlist:
            track_name = lib.get_name(track_number)
            self.playlist.remove(track_number)
            playlist_display = "\n".join([f"{num} - {lib.get_name(num)}" for num in self.playlist])
            set_text(self.playlist_txt, playlist_display)
            self.status_lbl.config(text=f"Track {track_name} removed from the playlist.")
        else:
            messagebox.showwarning("Track Not Found", "This track is not in the playlist.")

    def save_playlist_clicked(self):
        try:
            with open("playlist.txt", "w") as f:
                for track in self.playlist:
                    f.write(f"{track}\n")
            self.status_lbl.config(text="Playlist saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save playlist: {str(e)}")

    def load_playlist_clicked(self):
        try:
            with open("playlist.txt", "r") as f:
                self.playlist = [line.strip() for line in f.readlines()]
                playlist_display = "\n".join([f"{num} - {lib.get_name(num)}" for num in self.playlist])
                set_text(self.playlist_txt, playlist_display)
            self.status_lbl.config(text="Playlist loaded successfully.")
        except FileNotFoundError:
            messagebox.showwarning("Warning", "No saved playlist found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load playlist: {str(e)}")

    
    

    
    

if __name__ == "__main__":
    window = tk.Tk()
    fonts.configure()
    CreateTrackList(window)
    window.mainloop()