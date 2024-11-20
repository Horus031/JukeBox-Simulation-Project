class LibraryItem: # Class Constructors to create music tracks

    def __init__(self, name, artist, rating=0): # Initialize the arguments as the information
        self.name = name # Name of the music track
        self.artist = artist  # Artist of the music track
        self.rating = rating   # Rating of the music track
        self.play_count = 0   # Play count of the music track

    def info(self): # Function to display the information of the music track
        return f"{self.name} - {self.artist} {self.stars()}"
        # Return the name, artist and rating of the music track

    def stars(self): # Function to display the rating of the music track
        stars = "" # Initialize the variable to store the rating
        for i in range(self.rating): #  Loop through the rating
            stars += "*" # Add a star for each rating
        return stars # Return the rating as a string of stars