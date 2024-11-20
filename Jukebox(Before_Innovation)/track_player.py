import tkinter as tk
import tkinter.scrolledtext as tkst
import font_manager as fonts
import track_library as lib
from create_track_list import CreateTrackList
from view_track import TrackViewer
from update_track import UpdateTracks

# Utility function to set text in a text area
def set_text(text_area, content):
    text_area.delete("1.0", tk.END)
    text_area.insert(1.0, content)

# View Tracks handler
def view_tracks_clicked():
    # Update the status label to show the button was clicked
    status_lbl.configure(text="View Tracks button was clicked!")
    TrackViewer(tk.Toplevel(window))  # Open the TrackViewer GUI in a new window

# Create Track List handler
def create_track_list_clicked():
    # Update the status label to show the button was clicked
    status_lbl.configure(text="Create Track List button was clicked!")
    CreateTrackList(tk.Toplevel(window))  # Open the CreateTrackList GUI in a new window

# Update Tracks handler
def update_tracks_clicked():
    # Update the status label to show the button was clicked
    status_lbl.configure(text="Update Tracks button was clicked!")
    UpdateTracks(tk.Toplevel(window))  # Open the UpdateTracks GUI in a new window

# Main Jukebox Application
window = tk.Tk()
window.geometry("520x150")
window.title("JukeBox")
window.configure(bg="gray")

fonts.configure()  # Configure fonts from the font_manager module

# Header label
header_lbl = tk.Label(window, text="Select an option by clicking one of the buttons below")
header_lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

# View Tracks button
view_tracks_btn = tk.Button(window, text="View Tracks", command=view_tracks_clicked)
view_tracks_btn.grid(row=1, column=0, padx=10, pady=10)

# Create Track List button
create_track_list_btn = tk.Button(window, text="Create Track List", command=create_track_list_clicked)
create_track_list_btn.grid(row=1, column=1, padx=10, pady=10)

# Update Tracks button
update_tracks_btn = tk.Button(window, text="Update Tracks", command=update_tracks_clicked)
update_tracks_btn.grid(row=1, column=2, padx=10, pady=10)

# Status label
status_lbl = tk.Label(window, bg='gray', text="", font=("Helvetica", 10))
status_lbl.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

# Main loop to run the window
window.mainloop()