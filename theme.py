import tkinter as tk
from tkinter import ttk

def set_dark_theme(root):

    style = ttk.Style(root)
    
    # Configure colors
    bg_color = "#2d2d2d"  # Dark background
    fg_color = "#ffffff"  # White foreground
    accent_color = "#3c3c3c"  # Slightly lighter background for buttons, etc.
    
    # Apply the dark theme to root
    root.configure(bg='black')
    
    # Create the dark theme
    style.theme_create("dark", parent="alt", settings={
        "TFrame": {"configure": {"background": bg_color}},
        "TLabel": {"configure": {"background": bg_color, "foreground": fg_color}},
        "TButton": {
            "configure": {
                "background": accent_color,
                "foreground": fg_color,
                "borderwidth": 1,
                "relief": "raised",
            },
            "map": {
                "background": [("active", "#4c4c4c")],  # Slightly lighter when hovered
                "foreground": [("active", fg_color)],
            },
        },
        "TEntry": {
            "configure": {
                "fieldbackground": accent_color,
                "foreground": fg_color,
                "insertcolor": fg_color,
            },
        },
        "TCombobox": {
            "configure": {
                "fieldbackground": accent_color,
                "foreground": fg_color,
                "background": bg_color,
            },
        },
        "TNotebook": {
            "configure": {
                "background": bg_color,
                "foreground": fg_color,
            },
        },
        "TNotebook.Tab": {
            "configure": {
                "background": accent_color,
                "foreground": fg_color,
                "padding": [10, 5],
            },
            "map": {
                "background": [("selected", bg_color)],
                "foreground": [("selected", fg_color)],
            },
        },
    })
    
    # Set the custom dark theme
    style.theme_use("dark")
    
    # Configure Treeview
    style.configure("Treeview", 
                   background="#d3d3d3", 
                   fieldbackground="#d3d3d3", 
                   foreground="black")
    
    # Make the column separators more visible
    style.configure("Treeview.Heading",
                   background="#808080",
                   foreground="white",
                   font=("Arial", 10),
                   borderwidth=1,          # Add a border width
                   relief="raised",
                   padding=(1,1,1,15))       # Use raised relief to make it stand out
    
    # Configure heading separator
    style.configure("Treeview.Heading.Separator", background="black")

    
    
    # Change selected row color
    style.map("Treeview", background=[("selected", "#a6a6a6")])
    
    # Add specific style for when the user is resizing columns
    style.map("Treeview.Heading",
             relief=[("active", "sunken")]) # Changes appearance when mouse interacts with separator
    
    # Fix for empty Treeview background
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    
    return style