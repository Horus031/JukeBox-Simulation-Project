import tkinter as tk  # Importing the tkinter library for GUI creation
import tkinter.scrolledtext as tkst  # Importing the scrolled text widget for displaying text
import track_library as lib  # Importing a custom library for track management
import font_manager as fonts  # Importing a custom font manager

def set_text(text_area, content):
    """Function to set text in the specified text area."""
    text_area.delete("1.0", tk.END)  # Clear all existing text in the text area
    text_area.insert(1.0, content)  # Insert the new content into the text area
    


class TrackViewer():
    """Class to create the Track Viewer GUI."""
    
    def view_tracks_clicked(self):
        """Handler for the 'View Track' button click event."""
        key = self.input_txt.get()  # Get the track number from the input field
        name = lib.get_name(key)  # Retrieve the track name using the track number
        if name is not None:  # Check if the track exists
            artist = lib.get_artist(key)  # Get the artist name
            rating = lib.get_rating(key)  # Get the track rating
            play_count = lib.get_play_count(key)  # Get the play count
            # Format the track details for display
            track_details = f"{name}\n{artist}\nrating: {rating}\nplays: {play_count}"
            set_text(self.track_txt, track_details)  # Set the formatted details in the text area
        else:
            set_text(self.track_txt, f"Track {key} not found")  # Display a not found message if track does not exist
        self.status_lbl.configure(text="View Track button was clicked!")  # Update status label

    def list_tracks_clicked(self):
        """Handler for the 'List All Tracks' button click event."""
        track_list = lib.list_all()  # Retrieve the list of all tracks
        set_text(self.list_txt, track_list)  # Set the list of tracks in the text area
        self.status_lbl.configure(text="List Tracks button was clicked!")  # Update status label    
    
    def __init__(self, window):
        """Initialize the TrackViewer with a window."""
        window.geometry("750x350")  # Set the window size
        window.title("View Tracks")  # Set the window title
        # Button to list all tracks
        list_tracks_btn = tk.Button(window, text="List All Tracks", command=self.list_tracks_clicked)
        list_tracks_btn.grid(row=0, column=0, padx=10, pady=10)  # Place the button on the grid
        # Label for track number input
        enter_lbl = tk.Label(window, text="Enter Track Number")
        enter_lbl.grid(row=0, column=1, padx=10, pady=10)  # Place the label on the grid
        # Entry field for user to input track number
        self.input_txt = tk.Entry(window, width=3)
        self.input_txt.grid(row=0, column=2, padx=10, pady=10)  # Place the entry on the grid
        # Button to view details of a specific track
        check_track_btn = tk.Button(window, text="View Track", command=self.view_tracks_clicked)
        check_track_btn.grid(row=0, column=3, padx=10, pady=10)  # Place the button on the grid
        # Scrolled text area to list all tracks
        self.list_txt = tkst.ScrolledText(window, width=48, height=12, wrap="none")
        self.list_txt.grid(row=1, column=0, columnspan=3, sticky="W", padx=10, pady=10)  # Place the text area on the grid
        # Text area to display details of a specific track
        self.track_txt = tk.Text(window, width=24, height=4, wrap="none")
        self.track_txt.grid(row=1, column=3, sticky="NW", padx=10, pady=10)  # Place the text area on the grid
        # Label to display status messages
        self.status_lbl = tk.Label(window, text="", font=("Helvetica", 10))
        self.status_lbl.grid(row=2, column=0, columnspan=4, sticky="W", padx=10, pady=10)  # Place the status label on the grid

        self.list_tracks_clicked()  # Automatically list all tracks on initialization

if __name__ == "__main__":  # This block runs only when this file is executed directly
    window = tk.Tk()  # Create a new Tkinter window
    fonts.configure()  # Configure the fonts using the custom font manager
    TrackViewer(window)  # Create an instance of the TrackViewer class with the window
    window.mainloop()  # Start the Tkinter event loop to run the application