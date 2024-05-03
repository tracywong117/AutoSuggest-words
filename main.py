import tkinter as tk
import tkinter.ttk as ttk
import sqlite3
import time
from Levenshtein import distance
import inflect

# Define the Levenshtein distance function
def levenshtein_distance(s1, s2):
    try:
        return distance(s1, s2)
    except Exception as e:
        return 99999
    

# Define the custom function to find the minimum distance
def find_min_distance(*distances):
    try:
        valid_distances = [d for d in distances if d is not None]
        if valid_distances:
            min_distance = min(valid_distances)
            return min_distance
        return None
    except Exception as e:
        return None
    
def find_min_index(*distances):
    try:
        valid_distances = [d for d in distances if d is not None]
        if valid_distances:
            min_distance = min(valid_distances)
            min_distance_index = distances.index(min_distance)
            return min_distance_index
        return None
    except Exception as e:
        return None
    
conn = sqlite3.connect('taxonomy_names.db')

conn.create_function('LEVENSHTEIN', 2, levenshtein_distance)

conn.create_function('FIND_MIN_DISTANCE', 4, find_min_distance)
conn.create_function('FIND_MIN_INDEX', 4, find_min_index)

cursor = conn.cursor()

# Sample list of autocomplete suggestions
autocomplete_list = []

def load_autocomplete_list():
    cursor.execute("SELECT scientific_name FROM organism_names_fts LIMIT 10;")
    results = cursor.fetchall()
    for row in results:
        # print(row)
        autocomplete_list.append(row[0])
    print(autocomplete_list)


def on_key_press(event):
    # Get the current text in the entry widget
    current_text = entry.get()

    # Clear any previous autocomplete suggestions
    autocomplete_box.delete(0, tk.END)

    # Filter and display matching suggestions
    autocomplete_list = search_organisms()
    # matching_suggestions = [suggestion for suggestion in autocomplete_list if suggestion.startswith(current_text)]
    for suggestion in autocomplete_list:
        autocomplete_box.insert(tk.END, suggestion)

def on_suggestion_select(event):
    # Get the selected suggestion from the autocomplete box
    selected_suggestion = autocomplete_box.get(autocomplete_box.curselection())

    # Set the selected suggestion as the text in the entry widget
    entry.delete(0, tk.END)
    entry.insert(tk.END, selected_suggestion)

def search_organisms():
    user_input = entry.get()
    print(user_input)

    engine = inflect.engine()
    singular_noun = engine.singular_noun(user_input)
    if not singular_noun:
        singular_noun = user_input

    start = time.time()

    cursor.execute(f'''
        SELECT *,
        FIND_MIN_DISTANCE(LEVENSHTEIN(scientific_name, '{user_input}'), LEVENSHTEIN(common_name, '{user_input}'),
                            LEVENSHTEIN(genbank_common_name, '{user_input}'), LEVENSHTEIN(synonym, '{user_input}')) AS min_distance,
        FIND_MIN_INDEX(LEVENSHTEIN(scientific_name, '{user_input}'), LEVENSHTEIN(common_name, '{user_input}'),
                            LEVENSHTEIN(genbank_common_name, '{user_input}'), LEVENSHTEIN(synonym, '{user_input}')) AS min_index
        FROM organism_names_fts
        WHERE common_name MATCH '"{singular_noun}"*'
        OR genbank_common_name MATCH '"{singular_noun}"*'
        OR synonym MATCH '"{singular_noun}"*'
        OR scientific_name MATCH '"{singular_noun}"*'
        ORDER BY min_distance
        LIMIT 10;
    ''')

    results = cursor.fetchall()
    end = time.time()
    print(f'Result: returned in {(end-start)*1000:.4f}ms')
    autocomplete_list = []
    for row in results:
        print(row)
        autocomplete_list.append(row[row[-1]])

    return autocomplete_list

load_autocomplete_list()

# Create the main window
window = tk.Tk()
window.title("Autocomplete Demo")

# Create an entry widget for user input
entry = tk.Entry(window)
entry.pack()

# Create a listbox widget for autocomplete suggestions
autocomplete_box = tk.Listbox(window)
autocomplete_box.pack()

# Bind keypress event to the entry widget
entry.bind("<KeyRelease>", on_key_press)

# Bind selection event to the autocomplete box
autocomplete_box.bind("<<ListboxSelect>>", on_suggestion_select)

# # Create a button to search for organisms
search_button = tk.Button(window, text="Search")
search_button.pack()

window.mainloop()