import tkinter as tk  # Import the tkinter module for creating GUI applications
import track_library as lib  # Import a custom library for track management
import font_manager as fonts  # Import a custom font manager for font configurations


        
        
class UpdateTracks:  # Define a class for the UpdateTracks application
    def update_rating_clicked(self):  # Method to handle the button click event
        track_number = self.track_input.get().strip()  # Get the track number input and remove whitespace
        new_rating = self.rating_input.get().strip()  # Get the new rating input and remove whitespace

        # Validate if the new rating is a number and between 1 and 5
        if not new_rating.isdigit() or not 1 <= int(new_rating) <= 5:  # Check if the rating is valid
            self.status_lbl.config(text="Error: Please enter a valid rating (1-5).", fg="red")  # Show error message
            return  # Exit the method

        if not track_number.isdigit() or not lib.get_name(track_number):  # Check if track number is valid and exists
            self.status_lbl.config(text="Error: Track number not found. Please enter a valid track number.", fg="red")  # Show error message
            return  # Exit the method

        # Update the track rating
        lib.set_rating(track_number, int(new_rating))  # Call the library function to set the new rating
        play_count = lib.get_play_count(track_number)  # Get the play count of the track
        track_name = lib.get_name(track_number)  # Get the name of the track

        # Display success message
        self.status_lbl.config(  # Update the status label with success information
            text=f"Successfully updated:\nTrack: {track_name}\nNew Rating: {new_rating}\nPlay Count: {play_count}",
            fg="green"  # Set the text color to green for success
        )

        # Clear the input fields after successful update
        self.track_input.delete(0, tk.END)  # Clear the track number input field
        self.rating_input.delete(0, tk.END)  # Clear the new rating input field
    
    def __init__(self, window):  # Initialize the class with the main window as a parameter
        self.window = window  # Store the window reference
        window.geometry("500x300")  # Set the window size to 500x300 pixels
        window.title("Update Track Rating")  # Set the title of the window

        # Create a frame for organizing input fields and labels
        input_frame = tk.Frame(window)  # Create a frame widget
        input_frame.pack(pady=20)  # Pack the frame into the window with padding

        # Track Number Entry
        tk.Label(input_frame, text="Enter Track Number").grid(row=0, column=0, padx=10, pady=5, sticky="e")  # Label for track number
        self.track_input = tk.Entry(input_frame, width=10)  # Entry field for track number
        self.track_input.grid(row=0, column=1, padx=10, pady=5)  # Position the entry field in the grid

        # New Rating Entry
        tk.Label(input_frame, text="Enter New Rating (1-5)").grid(row=1, column=0, padx=10, pady=5, sticky="e")  # Label for new rating
        self.rating_input = tk.Entry(input_frame, width=10)  # Entry field for new rating
        self.rating_input.grid(row=1, column=1, padx=10, pady=5)  # Position the entry field in the grid

        # Update Button
        update_btn = tk.Button(input_frame, text="Update Rating", command=self.update_rating_clicked)  # Button to update rating
        update_btn.grid(row=2, column=0, columnspan=2, pady=10)  # Position the button in the grid

        # Status Label for feedback messages
        self.status_lbl = tk.Label(window, text="", font=("Helvetica", 10), fg="blue", wraplength=450, justify="left")  # Label for status messages
        self.status_lbl.pack(pady=20)  # Pack the status label into the window

if __name__ == "__main__":  # Check if the script is being run directly
    window = tk.Tk()  # Create the main application window
    fonts.configure()  # Configure fonts using the custom font manager
    app = UpdateTracks(window)  # Create an instance of the UpdateTracks application
    window.mainloop()  # Start the Tkinter event loop to listen for events