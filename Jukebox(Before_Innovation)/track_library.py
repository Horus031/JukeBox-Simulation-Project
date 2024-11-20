# Import the LibraryItem class from the library_item module
from library_item import LibraryItem 

#  Create an empty dictionary to store library items
library = {} 

# Add a library item to the dictionary
library["01"] = LibraryItem("Another Brick in the Wall", "Pink Floyd", 4)
library["02"] = LibraryItem("Stayin' Alive", "Bee Gees", 5)
library["03"] = LibraryItem("Highway to Hell ", "AC/DC", 2)
library["04"] = LibraryItem("Shape of You", "Ed Sheeran", 1)
library["05"] = LibraryItem("Someone Like You", "Adele", 3)


def list_all(): # Function to list all library items
    output = ""
    for key in library:
        item = library[key]
        output += f"{key} {item.info()}\n"
    return output


def get_name(key): # Function to get the name of a library item
    try:
        item = library[key]
        return item.name
    except KeyError:
        return None


def get_artist(key): # Function to get the artist of a library item
    try:
        item = library[key]
        return item.artist
    except KeyError:
        return None


def get_rating(key): # Function to get the rating of a library item
    try:
        item = library[key]
        return item.rating
    except KeyError:
        return -1


def set_rating(key, rating): # Function to set the rating of a library item
    try:
        item = library[key]
        item.rating = rating
    except KeyError:
        return


def get_play_count(key): # Function to get the play count of a library item
    try:
        item = library[key]
        return item.play_count
    except KeyError:
        return -1


def increment_play_count(key): # Function to increment the play count of a library item
    try:
        item = library[key]
        item.play_count += 1
    except KeyError:
        return