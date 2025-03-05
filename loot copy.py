import mysql.connector
import tkinter as tk
from tkinter import ttk
import sqlite3
from PIL import Image, ImageTk
import theme
import os

try:  # Connect to MariaDB
    conn = mysql.connector.connect(  
        host="192.168.1.105",
        user="eqemu",
        password="eqemu",
        database="peq"
    )
    cursor = conn.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit(1)

def clear_results():
    # Clear the zone entry box
    zone_entry.delete(0, tk.END)
    
    # Clear the NPC name entry box
    npc_name_entry.delete(0, tk.END)
    
    # Clear the loottable ID entry box
    loottable_id_entry.delete(0, tk.END)

    # Clear NPC results
    for item in npc_tree.get_children():
        npc_tree.delete(item)
    
    # Clear loot results
    for item in loot_tree.get_children():
        loot_tree.delete(item)

    # Clear loot2 results
    for item in loot_tree2.get_children():
        loot_tree2.delete(item)

    # Reset info labels
    loot_id_var.set("Loot Table ID: ")
    
    # Clear mincash and maxcash entries
    loottable_name_entry.delete(0, tk.END)
    mincash_entry.delete(0, tk.END)
    maxcash_entry.delete(0, tk.END)
    avgcoin_entry.delete(0, tk.END)
    minexpac_entry.delete(0, tk.END)
    maxexpac_entry.delete(0, tk.END)
    item_id_entry.delete(0, tk.END)
    
    # Reset status message
    status_var.set("Cleared and Ready")

def clear_search_results():
    # Clear the zone entry box
    zone_entry.delete(0, tk.END)
    
    # Clear the NPC name entry box
    npc_name_entry.delete(0, tk.END)
    
    # Clear the loottable ID entry box
    loottable_id_entry.delete(0, tk.END)

    # Reset status message
    status_var.set("Cleared and Ready")

def sort_treeview(tree, col, reverse=False):
    """
    Universal sorting function for any treeview
    tree: the treeview widget
    col: the column header text to sort by
    reverse: boolean to determine sort order
    """
    # Get all column IDs
    columns = tree["columns"]
    
    # Find the index of the column we're sorting by
    col_index = columns.index(col)
    
    def convert_value(value):
        """Convert string values to appropriate types for sorting"""
        try:
            # Try to convert to float first (handles both integers and decimals)
            return float(value)
        except ValueError:
            # If not a number, return lowercase string for case-insensitive sorting
            return str(value).lower()
    
    # Get all items along with their values
    items = [(tuple(convert_value(tree.set(item, column)) for column in columns), item) 
             for item in tree.get_children("")]
    
    # Sort based on the specified column
    items.sort(key=lambda x: x[0][col_index], reverse=reverse)
    
    # Rearrange items in sorted order
    for index, (_, item) in enumerate(items):
        tree.move(item, "", index)
    
    # Reverse sort next time if clicked again
    tree.heading(col, command=lambda: sort_treeview(tree, col, not reverse))

def setup_treeview_sorting(tree):
    #Apply sorting to all columns of a treeview
    for col in tree["columns"]:
        tree.heading(col, text=col, command=lambda c=col: sort_treeview(tree, c))

def create_db():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_note(name, note_type, content):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (name, type, content) VALUES (?, ?, ?)",
              (name, note_type, content))
    conn.commit()
    conn.close()

def load_notes(tree):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes")
    rows = c.fetchall()
    for row in rows:
        tree.insert("", "end", values=row)
    conn.close()

def open_notes_window():
    notes_window = tk.Toplevel()
    notes_window.title("Notes")

    # Top section
    top_frame = ttk.Frame(notes_window)
    top_frame.pack(pady=10)

    ttk.Label(top_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
    name_entry = ttk.Entry(top_frame, width=30)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(top_frame, text="Type:").grid(row=1, column=0, padx=5, pady=5)
    type_combobox = ttk.Combobox(top_frame, values=["Loot Table", "Loot Drop", "Item ID", "NPC ID"])
    type_combobox.grid(row=1, column=1, padx=5, pady=5)

    def clear_fields():
        name_entry.delete(0, tk.END)
        type_combobox.set("")

    def save_note_to_db():
        name = name_entry.get()
        note_type = type_combobox.get()
        content = "Sample content"  # Replace with actual content input if needed
        save_note(name, note_type, content)
        clear_fields()
        refresh_treeview()

    ttk.Button(top_frame, text="Clear", command=clear_fields).grid(row=2, column=0, padx=5, pady=5)
    ttk.Button(top_frame, text="Save", command=save_note_to_db).grid(row=2, column=1, padx=5, pady=5)

    # Bottom section
    bottom_frame = ttk.Frame(notes_window)
    bottom_frame.pack(pady=10)

    columns = ("ID", "Name", "Type", "Content")
    tree = ttk.Treeview(bottom_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack()

    def refresh_treeview():
        for row in tree.get_children():
            tree.delete(row)
        load_notes(tree)

    refresh_treeview()

def find_unused_ids():
    loottable_query = """
        WITH RECURSIVE number_sequence AS (
            SELECT 1 AS id
            UNION ALL
            SELECT id + 1
            FROM number_sequence
            WHERE id < 500000
        )
        SELECT ns.id
        FROM number_sequence ns
        LEFT JOIN loottable lt ON ns.id = lt.id
        WHERE lt.id IS NULL
        ORDER BY ns.id
        LIMIT 10
    """
    
    lootdrop_query = """
        WITH RECURSIVE number_sequence AS (
            SELECT 1 AS id
            UNION ALL
            SELECT id + 1
            FROM number_sequence
            WHERE id < 500000
        )
        SELECT ns.id
        FROM number_sequence ns
        LEFT JOIN lootdrop ld ON ns.id = ld.id
        WHERE ld.id IS NULL
        ORDER BY ns.id
        LIMIT 10
    """
    
    try:
        # Execute the loottable query
        cursor.execute(loottable_query)
        unused_loottable_ids = cursor.fetchall()
        unused_loottable_ids = [str(row[0]) for row in unused_loottable_ids]

        # Execute the lootdrop query
        cursor.execute(lootdrop_query)
        unused_lootdrop_ids = cursor.fetchall()
        unused_lootdrop_ids = [str(row[0]) for row in unused_lootdrop_ids]

        # Define the maximum number of IDs to display before adding "..."
        max_display_ids = 9

        # Truncate the loottable IDs and add "..." if necessary
        if len(unused_loottable_ids) > max_display_ids:
            unused_loottable_ids = unused_loottable_ids[:max_display_ids] + ["..."]

        # Truncate the lootdrop IDs and add "..." if necessary
        if len(unused_lootdrop_ids) > max_display_ids:
            unused_lootdrop_ids = unused_lootdrop_ids[:max_display_ids] + ["..."]

        # Update the labels with the truncated lists
        unused_loottable_label.config(text=", ".join(unused_loottable_ids))
        unused_lootdrop_label.config(text=", ".join(unused_lootdrop_ids))

        # Extract the first unused loottable and lootdrop IDs
        first_unused_loottable_id = unused_loottable_ids[0]
        first_unused_lootdrop_id = unused_lootdrop_ids[0]

        # Update the label text with the first unused IDs
        ttk.Label(find_unused_frame, text=f"new loot table ID: {first_unused_loottable_id} with lootdrop ID: {first_unused_lootdrop_id}").grid(row=6, column=1, sticky=tk.W)

    except mysql.connector.Error as err:
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def find_next_available_id(table_name, id_column):
    """Find the next available ID in a table by checking for gaps."""
    try:
        cursor.execute(f"""
            WITH RECURSIVE number_sequence AS (
                SELECT 1 AS id
                UNION ALL
                SELECT id + 1
                FROM number_sequence
                WHERE id < (SELECT MAX({id_column}) FROM {table_name}) + 1
            )
            SELECT MIN(ns.id)
            FROM number_sequence ns
            LEFT JOIN {table_name} t ON ns.id = t.{id_column}
            WHERE t.{id_column} IS NULL
        """)
        next_id = cursor.fetchone()[0]
        if next_id is None:
            # If no gaps, use the next ID after the maximum
            cursor.execute(f"SELECT MAX({id_column}) + 1 FROM {table_name}")
            next_id = cursor.fetchone()[0]
            if next_id is None:
                next_id = 1  # Default to 1 if the table is empty
        return next_id
    except mysql.connector.Error as err:
        tk.messagebox.showerror("Database Error", f"Error finding next available ID: {err}")
        return None

def search_zone():
    global status_var  # Declare status_var as global
    zone = zone_entry.get().strip()
    if not zone:
        return

    status_var.set("Searching...")
    root.update_idletasks()

    query = """
        SELECT DISTINCT npc_types.id, npc_types.name, npc_types.level,
        npc_types.race, npc_types.class, npc_types.bodytype, npc_types.hp, npc_types.mana,
        npc_types.gender, npc_types.texture, npc_types.helmtexture, npc_types.size,
        npc_types.loottable_id, npc_types.npc_spells_id, npc_types.npc_faction_id,
        npc_types.mindmg, npc_types.maxdmg, npc_types.npcspecialattks, npc_types.special_abilities, 
        npc_types.MR, npc_types.CR, npc_types.DR, npc_types.FR, npc_types.PR, npc_types.AC,
        npc_types.attack_delay, npc_types.STR, npc_types.STA, npc_types.DEX,
        npc_types.AGI, npc_types._INT, npc_types.WIS, npc_types.maxlevel, npc_types.skip_global_loot, npc_types.exp_mod

        FROM spawn2
        JOIN spawnentry ON spawn2.spawngroupID = spawnentry.spawngroupID
        JOIN npc_types ON spawnentry.npcID = npc_types.id
        WHERE spawn2.zone = %s
    """
    
    try:
        cursor.execute(query, (zone,))
        rows = cursor.fetchall()
    except mysql.connector.Error as err:
        tk.messagebox.showerror("Database Error", f"Error: {err}")
        return

    # Clear old results
    for item in npc_tree.get_children():
        npc_tree.delete(item)

    # Insert new results
    for row in rows:
        npc_tree.insert("", "end", values=row)

    status_var.set(f"Found {len(rows)} results.")

def search_npc_name():
    global status_var
    npc_name = npc_name_entry.get().strip()
    if not npc_name:
        return

    status_var.set("Searching...")
    root.update_idletasks()

    query = """
        SELECT DISTINCT 
                id, name, level, race, class, bodytype, hp, mana,
                gender, texture, helmtexture, size, loottable_id, npc_spells_id, npc_faction_id,
                mindmg, maxdmg, npcspecialattks, special_abilities, MR, CR, DR, FR, PR, AC,
                attack_delay, STR, STA, DEX, AGI, _INT, WIS, maxlevel, skip_global_loot, exp_mod
        FROM 
            npc_types
        WHERE 
            name LIKE %s
    """
    
    try:
        cursor.execute(query, (f"%{npc_name}%",))
        rows = cursor.fetchall()
    except mysql.connector.Error as err:
        tk.messagebox.showerror("Database Error", f"Error: {err}")
        return

    # Clear old results
    for item in npc_tree.get_children():
        npc_tree.delete(item)

    # Insert new results
    for row in rows:
        npc_tree.insert("", "end", values=row)

    status_var.set(f"Found {len(rows)} results.")

def lookup_item_by_id():
    # Create a new window
    item_lookup_window = tk.Toplevel(root)
    item_lookup_window.title("Lookup Item by ID")
    item_lookup_window.geometry("900x600")

    # Entry field for Item ID
    ttk.Label(item_lookup_window, text="Enter Item ID:").pack(pady=10)
    item_id_entry = ttk.Entry(item_lookup_window, width=20)
    item_id_entry.pack(pady=5)

    # Lookup button
    lookup_button = ttk.Button(item_lookup_window, text="Lookup", command=lambda: fetch_item_data(item_id_entry.get(), item_tree))
    lookup_button.pack(pady=10)

    # Updated Treeview with NPC Name
    item_tree = ttk.Treeview(
        item_lookup_window,
        columns=("Loot Table ID", "Loot Table Name", "Loot Drop ID", "Loot Drop Name", "NPC Name"),
        show="headings"
    )
    item_tree.heading("Loot Table ID", text="Loot Table ID")
    item_tree.heading("Loot Table Name", text="Loot Table Name")
    item_tree.heading("Loot Drop ID", text="Loot Drop ID")
    item_tree.heading("Loot Drop Name", text="Loot Drop Name")
    item_tree.heading("NPC Name", text="NPC Name")

    item_tree.column("Loot Table ID", width=100, stretch=False)
    item_tree.column("Loot Table Name", width=200, stretch=True)
    item_tree.column("Loot Drop ID", width=100, stretch=False)
    item_tree.column("Loot Drop Name", width=200, stretch=True)
    item_tree.column("NPC Name", width=200, stretch=True)

    item_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Function to fetch and display item data
    def fetch_item_data(item_id, tree):
        # Clear previous results
        tree.delete(*tree.get_children())

        try:
            # Fetch lootdrops that contain the item
            cursor.execute("""
                SELECT lde.lootdrop_id, ld.name
                FROM lootdrop_entries lde
                JOIN lootdrop ld ON lde.lootdrop_id = ld.id
                WHERE lde.item_id = %s
            """, (item_id,))
            lootdrops = cursor.fetchall()

            if not lootdrops:
                status_var.set(f"No lootdrops found for item ID {item_id}.")
                return

            # Fetch loottables and associated NPCs for each lootdrop
            for lootdrop_id, lootdrop_name in lootdrops:
                cursor.execute("""
                    SELECT lt.id, lt.name, COALESCE(GROUP_CONCAT(npc.name SEPARATOR ', '), 'None')
                    FROM loottable_entries lte
                    JOIN loottable lt ON lte.loottable_id = lt.id
                    LEFT JOIN npc_types npc ON lt.id = npc.loottable_id
                    WHERE lte.lootdrop_id = %s
                    GROUP BY lt.id, lt.name
                """, (lootdrop_id,))
                loottables = cursor.fetchall()

                # Insert data correctly into the tree
                for loottable_id, loottable_name, npc_name in loottables:
                    tree.insert(
                        "", "end",
                        values=(loottable_id, loottable_name, lootdrop_id, lootdrop_name, npc_name)
                    )

            status_var.set(f"Found {len(lootdrops)} lootdrops for item ID {item_id}.")
        except mysql.connector.Error as err:
            status_var.set(f"Error fetching data: {err}")

def search_loottable_id():
    loottable_id = loottable_id_entry.get().strip()
    if not loottable_id:
        return

    status_var.set("Searching...")
    root.update_idletasks()

    # Clear previous results
    for item in loot_tree.get_children():
        loot_tree.delete(item)
    for item in loot_tree2.get_children():
        loot_tree2.delete(item)
    for item in npc_tree.get_children():
        npc_tree.delete(item)

    try:
        # Fetch loottable details
        query = """
            SELECT name, mincash, maxcash, avgcoin, min_expansion, max_expansion
            FROM loottable
            WHERE id = %s
        """
        cursor.execute(query, (loottable_id,))
        loottable_data = cursor.fetchone()

        if loottable_data:
            loot_id_var.set(f"Loot Table ID: {loottable_id}")
            loottable_name_entry.delete(0, tk.END)
            loottable_name_entry.insert(0, loottable_data[0])
            mincash_entry.delete(0, tk.END)
            mincash_entry.insert(0, loottable_data[1])
            maxcash_entry.delete(0, tk.END)
            maxcash_entry.insert(0, loottable_data[2])
            avgcoin_entry.delete(0, tk.END)
            avgcoin_entry.insert(0, loottable_data[3])
            minexpac_entry.delete(0, tk.END)
            minexpac_entry.insert(0, loottable_data[4])
            maxexpac_entry.delete(0, tk.END)
            maxexpac_entry.insert(0, loottable_data[5])
        else:
            loot_id_var.set("Loot Table ID: ")
            loottable_name_entry.delete(0, tk.END)
            avgcoin_entry.delete(0, tk.END)
            minexpac_entry.delete(0, tk.END)
            maxexpac_entry.delete(0, tk.END)
            mincash_entry.delete(0, tk.END)
            maxcash_entry.delete(0, tk.END)

        # Fetch loottable entries
        query = """
            SELECT loottable_entries.lootdrop_id, lootdrop.name, loottable_entries.multiplier,
               loottable_entries.mindrop, loottable_entries.droplimit, loottable_entries.probability
            FROM loottable_entries
            JOIN lootdrop ON loottable_entries.lootdrop_id = lootdrop.id
            WHERE loottable_entries.loottable_id = %s
        """
        cursor.execute(query, (loottable_id,))
        rows = cursor.fetchall()

        # Insert loottable details into loot_tree
        for row in rows:
            loot_tree.insert("", "end", values=row)

        # Automatically select the first loot drop in the loot_tree
        if loot_tree.get_children():
            first_lootdrop = loot_tree.get_children()[0]
            loot_tree.selection_set(first_lootdrop)
            loot_tree.focus(first_lootdrop)
            on_lootdrop_select(None)  # Trigger the lootdrop selection event

        # Fetch NPCs with this loottable_id
        query = """
            SELECT id, name, level, race, class, bodytype, hp, mana,
                   gender, texture, helmtexture, size, loottable_id, npc_spells_id, npc_faction_id,
                   mindmg, maxdmg, npcspecialattks, special_abilities, MR, CR, DR, FR, PR, AC,
                   attack_delay, STR, STA, DEX, AGI, _INT, WIS,
                   maxlevel, skip_global_loot, exp_mod
            FROM npc_types
            WHERE loottable_id = %s
        """
        cursor.execute(query, (loottable_id,))
        npc_rows = cursor.fetchall()

        # Insert NPCs into npc_tree
        for row in npc_rows:
            npc_tree.insert("", "end", values=row)

        status_var.set(f"Found {len(rows)} loot drops and {len(npc_rows)} NPCs.")
    except mysql.connector.Error as err:
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def on_npc_select(event):
    selected_item = npc_tree.selection()
    if not selected_item:
        return
    
    npc_data = npc_tree.item(selected_item[0], "values")
    loottable_id = npc_data[12]  # 12th column is loottable_id
    
    # Clear previous results in both trees
    for item in loot_tree.get_children():
        loot_tree.delete(item)
    for item in loot_tree2.get_children():
        loot_tree2.delete(item)
    for widget in image_frame.winfo_children():
        widget.destroy()

    if not loottable_id:
        # Clear loot_mod_frame if no loottable_id
        loot_id_var.set("Loot Table ID: ")
        loottable_name_entry.delete(0, tk.END)
        mincash_entry.delete(0, tk.END)
        maxcash_entry.delete(0, tk.END)
        avgcoin_entry.delete(0, tk.END)
        minexpac_entry.delete(0, tk.END)
        maxexpac_entry.delete(0, tk.END)
        return

    # Fetch loottable details
    query = """
        SELECT name, mincash, maxcash, avgcoin, min_expansion, max_expansion
        FROM loottable
        WHERE id = %s
    """
    cursor.execute(query, (loottable_id,))
    loottable_data = cursor.fetchone()

    if loottable_data:
        loot_id_var.set(f"Loot Table ID: {loottable_id}")
        loottable_name_entry.delete(0, tk.END)
        loottable_name_entry.insert(0, loottable_data[0])
        mincash_entry.delete(0, tk.END)
        mincash_entry.insert(0, loottable_data[1])
        maxcash_entry.delete(0, tk.END)
        maxcash_entry.insert(0, loottable_data[2])
        avgcoin_entry.delete(0, tk.END)
        avgcoin_entry.insert(0, loottable_data[3])
        minexpac_entry.delete(0, tk.END)
        minexpac_entry.insert(0, loottable_data[4])
        maxexpac_entry.delete(0, tk.END)
        maxexpac_entry.insert(0, loottable_data[5])
        
    else:
        loot_id_var.set("Loot Table ID: ")
        mincash_entry.delete(0, tk.END)
        maxcash_entry.delete(0, tk.END)
        avgcoin_entry.delete(0, tk.END)
        minexpac_entry.delete(0, tk.END)
        maxexpac_entry.delete(0, tk.END)
        loottable_name_entry.delete(0, tk.END)

    # Fetch loottable entries
    query = """
        SELECT loottable_entries.lootdrop_id, lootdrop.name, loottable_entries.multiplier,
               loottable_entries.mindrop, loottable_entries.droplimit, loottable_entries.probability
        FROM loottable_entries
        JOIN lootdrop ON loottable_entries.lootdrop_id = lootdrop.id
        WHERE loottable_entries.loottable_id = %s
    """
    cursor.execute(query, (loottable_id,))
    rows = cursor.fetchall()

    # Insert loottable details into loot_tree
    for row in rows:
        loot_tree.insert("", "end", values=row)

    # Automatically select the first loot drop in the loot_tree
    if loot_tree.get_children():
        first_lootdrop = loot_tree.get_children()[0]
        loot_tree.selection_set(first_lootdrop)
        loot_tree.focus(first_lootdrop)
        on_lootdrop_select(None)  # Trigger the lootdrop selection event

    # Default image path
    default_image_path = "images/other/default.jpg"  # Ensure this file exists

    # Create the image frame
    image_frame2 = ttk.Frame(image_frame)  # Replace with your actual frame for the image
    image_frame2.grid()

    # Construct the image filename based on npc_data[3], [8], [9], and [10]
    image_filename = f"images/raceimages/{npc_data[3]}_{npc_data[8]}_{npc_data[9]}_{npc_data[10]}.jpg"

    # Try to load the NPC image, fallback to default if not found
    if not os.path.exists(image_filename):
        image_filename = default_image_path

    try:
        # Load and display the image
        img = Image.open(image_filename)
        img = img.resize((95, 125), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        image_label = ttk.Label(image_frame2, image=img_tk)
        image_label.image = img_tk  # Keep reference
        image_label.grid()
    except Exception as e:
        print(f"Error loading image: {e}")

def on_item_select(event):
    selected_loot_item = loot_tree2.selection()
    if not selected_loot_item:
        return
   
    item_id = loot_tree2.item(selected_loot_item, "values")[0]
   
    # Clear previous item image and stats
    for item in canvas.find_all():
        canvas.delete(item)
    
    # Redraw the background image
    canvas.create_image(0, 0, anchor="nw", image=bg_image)
   
    query = """
        SELECT DISTINCT Name, aagi, ac, accuracy, acha, adex, aint, asta, astr, attack, augrestrict,  
               augtype, avoidance, awis, bagsize, bagslots, bagtype, bagwr, banedmgamt, banedmgraceamt, 
               banedmgbody, banedmgrace, classes, color, combateffects, extradmgskill, extradmgamt, cr, damage, 
               damageshield, deity, delay, dotshielding, dr, elemdmgtype, elemdmgamt, endur, fr, fvnodrop, 
               haste, hp, regen, icon, itemclass, itemtype, lore, loregroup, magic, mana, manaregen, enduranceregen, mr, nodrop, norent, pr, races, 
               `range`, reclevel, recskill, reqlevel, shielding, size, skillmodtype, skillmodvalue, 
               slots, clickeffect, spellshield, strikethrough, stunresist, weight, attuneable, svcorruption, skillmodmax,
               heroic_str, heroic_int, heroic_wis, heroic_agi, heroic_dex, 
               heroic_sta, heroic_cha, heroic_pr, heroic_dr, heroic_fr, 
               heroic_cr, heroic_mr, heroic_svcorrup, healamt, spelldmg, clairvoyance, backstabdmg
        FROM items
        WHERE id = %s
    """
    cursor.execute(query, (item_id,))
    item_data = cursor.fetchone()
    
    if item_data:
        columns = [
            "Name", "aagi", "ac", "accuracy", "acha", "adex", "aint", "asta", "astr", "attack", "augrestrict",  
            "augtype", "avoidance", "awis", "bagsize", "bagslots", "bagtype", "bagwr", "banedmgamt", "banedmgraceamt", 
            "banedmgbody", "banedmgrace", "classes", "color", "combateffects", "extradmgskill", "extradmgamt", "cr", "damage", 
            "damageshield", "deity", "delay", "dotshielding", "dr", "elemdmgtype", "elemdmgamt", "endur", "fr", "fvnodrop", 
            "haste", "hp", "regen", "icon", "itemclass", "itemtype", "lore", "loregroup", "magic", "mana", "manaregen", "enduranceregen", "mr", "nodrop", "norent", "pr", "races", 
            "range", "reclevel", "recskill", "reqlevel", "shielding", "size", "skillmodtype", "skillmodvalue", 
            "slots", "clickeffect", "spellshield", "strikethrough", "stunresist", "weight", "attuneable", "svcorruption", "skillmodmax",
            "heroic_str", "heroic_int", "heroic_wis", "heroic_agi", "heroic_dex", 
            "heroic_sta", "heroic_cha", "heroic_pr", "heroic_dr", "heroic_fr", 
            "heroic_cr", "heroic_mr", "heroic_svcorrup", "healamt", "spelldmg", "clairvoyance", "backstabdmg"
        ]
       
        item_stats = dict(zip(columns, item_data))
        
        # Process special fields
        
        # Handle icon - display item image
        icon_id = item_stats.get("icon")
        if icon_id:
            try:
                # Load icon image based on icon_id
                icon_path = f"images/icons/item_{icon_id}.gif"  # Adjust path format as needed
                item_icon = Image.open(icon_path)
                item_photo = ImageTk.PhotoImage(item_icon)
                
                # Save reference to prevent garbage collection
                # You need to keep this reference alive
                canvas.item_photo = item_photo  
                
                # Display icon at specific pixel location
                canvas.create_image(28, 50, image=item_photo)
            except Exception as e:
                print(f"Could not load icon: {e}")
        
        # Handle classes bitmask
        classes_bitmask = item_stats.get("classes")
        if classes_bitmask is not None:
            # Define class mapping - adjust to match your game's classes
            class_map = {
                1: "WAR", 2: "CLR", 4: "PAL", 8: "RNG",
                16: "SK", 32: "DRU", 64: "MON", 128: "BRD",
                256: "ROG", 512: "SHM", 1024: "NEC",
                2048: "WIZ", 4096: "MAG", 8192: "ENC", 65535: "ALL"
            }
        
            # Check if the bitmask matches the ALL value
            if classes_bitmask == 65535:
                item_stats["classes"] = "ALL"
            else:
                # Convert bitmask to list of class names
                class_names = []
                for bit_value, class_name in class_map.items():
                    if bit_value != 65535 and classes_bitmask & bit_value:
                        class_names.append(class_name)
                
                # Replace the bitmask value with readable class names
                item_stats["classes"] = ", ".join(class_names)
        
        # Handle races bitmask similarly
        races_bitmask = item_stats.get("races")
        if races_bitmask is not None:
            # Define race mapping - adjust to match your game's races
            race_map = {
                1: "HUM", 2: "BAR", 4: "ERU", 8: "WEF",
                16: "HIE", 32: "DRK", 64: "HEL", 128: "DWF",
                256: "TRL", 512: "OGR", 1024: "HLF", 2048: "GME", 65535: "ALL"
            }
        
            # Check if the bitmask matches the ALL value
            if races_bitmask == 65535:
                item_stats["races"] = "ALL"
            else:
                # Convert bitmask to list of race names
                race_names = []
                for bit_value, race_name in race_map.items():
                    if bit_value != 65535 and races_bitmask & bit_value:
                        race_names.append(race_name)
                
                # Replace the bitmask value with readable race names
                item_stats["races"] = ", ".join(race_names)
        
        # Define exact pixel positions and custom formatting for each individual stat
        # Format: {
        #   stat_name: {
        #     "x": x_position, 
        #     "y": y_position, 
        #     "color": color, 
        #     "font": font,
        #     "label": custom_label,  # Optional custom label
        #     "format": format_function  # Optional function to format the value
        #   }
        # }
        stat_positions = {
            "Name": {
                "x": 150, "y": 3, 
                "color": "white", 
                "font": ("Arial", 10),
                "label": None  # No label for Name
            },
            "classes": {
                "x": 55, "y": 44, 
                "color": "skyblue", 
                "font": ("Arial", 9),
                "label": "Class"  # Singular form
            },
            "races": {
                "x": 55, "y": 60, 
                "color": "skyblue", 
                "font": ("Arial", 9),
                "label": "Race"  # Singular form
            },
            
            # Add more stats with custom formatting as needed
        }
        
        # Process the standard stats first
        for stat_name, config in stat_positions.items():
            # Skip the special properties we'll handle separately
            if stat_name in ["magic", "loregroup", "nodrop", "fvnodrop", "norent", "attunable"]:
                continue

            if stat_name in item_stats and item_stats[stat_name] is not None:
                value = item_stats[stat_name]

                # Apply custom formatting if provided
                if "format" in config:
                    formatted_value = config["format"](value)
                    if not formatted_value:
                        continue
                    value = formatted_value
                elif value == "":
                    continue
                
                # Determine display text based on label configuration
                if config.get("label") is None:
                    stat_text = f"{value}"
                elif config.get("label") == "":
                    continue
                else:
                    stat_text = f"{config['label']}: {value}"

                # Create text at the exact position
                canvas.create_text(
                    config["x"], 
                    config["y"], 
                    text=stat_text, 
                    fill=config["color"], 
                    anchor="nw", 
                    font=config["font"]
                )

        # Now handle the special property row (magic, lore, nodrop)
        # Set the row position
        row_y = 28
        base_x = 55
        spacing = 40

        # Define property details for the special row
        property_row_details = {
            "magic": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: "Magic" if value == 1 else ""
            },
            "loregroup": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: " Lore" if value == -1 else ""
            },
            "nodrop": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: "No Drop" if value == 0 else ""
            },
            "fvnodrop": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: "FV No Drop" if value == 1 else ""
            },
            "norent": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: "No Rent" if value == 0 else ""
            },
            "attuneable": {
                "color": "white", 
                "font": ("Arial", 10),
                "format": lambda value: "Attune" if value == 1 else ""
            }
        }

        items_placed = 0
        # Process special properties in order
        for prop_name in ["magic", "loregroup", "nodrop", "fvnodrop", "norent", "attuneable"]:
            config = property_row_details[prop_name]

            if prop_name in item_stats and item_stats[prop_name] is not None:
                value = item_stats[prop_name]

                # Apply custom formatting
                if "format" in config:
                    formatted_value = config["format"](value)
                    # Skip empty formatted values
                    if not formatted_value:
                        continue
                    value = formatted_value
                # Skip empty values
                elif value == "":
                    continue

                current_x = base_x + (items_placed * spacing)

                # Create text at the current position
                canvas.create_text(
                    current_x, 
                    row_y, 
                    text=value,  # Just show the formatted value
                    fill=config["color"], 
                    anchor="nw", 
                    font=config["font"]
                )

                # Move x position for next item
                items_placed += 1




def on_npc_edit(event):
    # Get the clicked item and column
    tree = event.widget
    region = tree.identify_region(event.x, event.y)
    if region != "cell":
        return
        
    column = tree.identify_column(event.x)
    item = tree.identify_row(event.y)
    
    if not item or not column:
        return
    
    # Get column index (1-based to 0-based)
    column_index = int(column[1:]) - 1
    
    # Get the column name from the treeview
    column_name = tree["columns"][column_index]
    
    # Get current values
    item_values = list(tree.item(item, "values"))
    current_value = item_values[column_index]
    
    # Get cell bbox relative to tree
    bbox = tree.bbox(item, column)
    if not bbox:
        return
        
    # Create entry widget
    entry = tk.Entry(tree)
    entry.insert(0, current_value)
    entry.select_range(0, tk.END)
    
    # Position entry widget
    entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
    entry.focus_set()
    
    def save_edit(event=None):
        new_value = entry.get()
        
        # Get the NPC ID from the first column
        npc_id = item_values[0]  # NPC ID is in the first column
        
        try:
            # Map column names to database fields
            column_to_field = {
                "NPC ID": "id",
                "Name": "name",
                "Lvl": "level",
                "Race": "race",
                "Class": "class",
                "Body": "bodytype",
                "HP": "hp",
                "Mana": "mana",
                "Gender": "gender",
                "Texture": "texture",
                "Helmtexture": "helmtexture",
                "Size": "size",
                "Loottable ID": "loottable_id",
                "Spells ID": "npc_spells_id",
                "Faction ID": "npc_faction_id",
                "Mindmg": "mindmg",
                "Maxdmg": "maxdmg",
                "Npcspecialattks": "npcspecialattks",
                "Special Abilities": "special_abilities",
                "MR": "MR",
                "CR": "CR",
                "DR": "DR",
                "FR": "FR",
                "PR": "PR",
                "AC": "AC",
                "Attack Delay": "attack_delay",
                "STR": "STR",
                "STA": "STA",
                "DEX": "DEX",
                "AGI": "AGI",
                "_INT": "_INT",
                "WIS": "WIS",
                "Maxlevel": "maxlevel",
                "Skip Global Loot": "skip_global_loot",
                "Exp Mod": "exp_mod"
            }
            
            # Only allow editing if column is in our mapping
            if column_name not in column_to_field:
                status_var.set(f"Column {column_name} is not editable")
                entry.destroy()
                return
                
            # Validate numeric fields
            numeric_fields = [
                "id", "level", "race", "class", "hp", "mana", "gender", "size", 
                "hp_regen_rate", "mana_regen_rate", "loottable_id", "npc_spells_id", 
                "npc_faction_id", "mindmg", "maxdmg", "runspeed", "MR", "CR", "DR", "FR", 
                "PR", "AC", "attack_speed", "attack_delay", "STR", "STA", "DEX", "AGI",
                "_INT", "WIS", "CHA", "ATK", "accuracy", "avoidance", "slow_mitigation", "maxlevel", "exp_mod"
            ]
            
            field_name = column_to_field[column_name]
            if field_name in numeric_fields:
                try:
                    float(new_value)
                except ValueError:
                    status_var.set(f"Invalid numeric value for {column_name}")
                    entry.destroy()
                    return
            
            # Construct and execute the update query
            query = f"""
                UPDATE npc_types
                SET {column_to_field[column_name]} = %s
                WHERE id = %s
            """
            cursor.execute(query, (new_value, npc_id))
            conn.commit()
            
            # Update the display
            item_values[column_index] = new_value
            tree.item(item, values=item_values)
            
            status_var.set("Update successful")
        except mysql.connector.Error as err:
            status_var.set(f"Error updating: {err}")
        finally:
            entry.destroy()
    
    def on_escape(event):
        entry.destroy()
    
    entry.bind("<Return>", save_edit)
    entry.bind("<Escape>", on_escape)
    entry.bind("<FocusOut>", lambda e: entry.destroy())

def update_loottable():
    try:
        # Get the currently selected loottable_id from loot_id_var
        loottable_id = loot_id_var.get().split(": ")[1]  # Extract the ID from the label
        if not loottable_id:
            status_var.set("No loottable selected.")
            return

        # Get the new mincash and maxcash values
        loottablename = loottable_name_entry.get().strip()
        mincash = mincash_entry.get().strip()
        maxcash = maxcash_entry.get().strip()
        avgcoin = avgcoin_entry.get().strip()
        minexpac = minexpac_entry.get().strip()
        maxexpac = maxexpac_entry.get().strip()

        # Validate the inputs
        try:
            loottablename = loottablename[:64]  # Truncate to 64 characters
            mincash = int(mincash)
            maxcash = int(maxcash)
            avgcoin = int(avgcoin)
            minexpac = int(minexpac)
            maxexpac = int(maxexpac)
        except ValueError:
            status_var.set("Invalid cash values. Please enter integers.")
            return

        # Update the loottable with the new cash range
        cursor.execute("""
            UPDATE loottable
            SET name = %s, mincash = %s, maxcash = %s, avgcoin = %s, min_expansion = %s, max_expansion = %s
            WHERE id = %s
        """, (loottablename, mincash, maxcash, avgcoin, minexpac, maxexpac, loottable_id))
        conn.commit()

        # Refresh the loot_mod_frame to show the updated cash range
        loot_id = loot_id_var.get().split(": ")[1]
        query = """
            SELECT name, mincash, maxcash, avgcoin, min_expansion, max_expansion
            FROM loottable
            WHERE id = %s
        """
        cursor.execute(query, (loot_id,))
        loottable_data = cursor.fetchone()

        if loottable_data:
            loot_id_var.set(f"Loot Table ID: {loot_id}")

        status_var.set("Cash range updated successfully.")
    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def on_lootdrop_select(event):
    selected_item = loot_tree.selection()
    if not selected_item:
        return
    
    lootdrop_data = loot_tree.item(selected_item[0], "values")
    lootdrop_id = lootdrop_data[0]  # LootDrop_ID is the first value

    # Clear previous results in loot_tree2
    for item in loot_tree2.get_children():
        loot_tree2.delete(item)

    if not lootdrop_id:
        return

    # Fetch lootdrop details
    # Fetch lootdrop details with item name
    query = """
        SELECT lootdrop_entries.item_id, items.name AS item_name, lootdrop_entries.item_charges, lootdrop_entries.equip_item,
               lootdrop_entries.chance, lootdrop_entries.trivial_min_level, lootdrop_entries.trivial_max_level,
               lootdrop_entries.multiplier, lootdrop_entries.npc_min_level, lootdrop_entries.npc_max_level,
               lootdrop_entries.min_expansion, lootdrop_entries.max_expansion
        FROM lootdrop_entries
        JOIN items ON lootdrop_entries.item_id = items.id
        WHERE lootdrop_entries.lootdrop_id = %s
    """

    cursor.execute(query, (lootdrop_id,))
    rows = cursor.fetchall()

    # Insert lootdrop details into loot_tree2
    for row in rows:
        loot_tree2.insert("", "end", values=row)

def on_lootdrop_edit(event):
    # Get the clicked item and column
    tree = event.widget
    region = tree.identify_region(event.x, event.y)
    if region != "cell":
        return
        
    column = tree.identify_column(event.x)
    item = tree.identify_row(event.y)
    
    if not item or not column:
        return
    
    # Get column index (1-based to 0-based)
    column_index = int(column[1:]) - 1
    
    # Get the column name from the treeview
    column_name = tree["columns"][column_index]
    
    # Get current values
    item_values = list(tree.item(item, "values"))
    current_value = item_values[column_index]
    
    # Get cell bbox relative to tree
    bbox = tree.bbox(item, column)
    if not bbox:
        return
        
    # Create entry widget
    entry = tk.Entry(tree)
    entry.insert(0, current_value)
    entry.select_range(0, tk.END)
    
    # Position entry widget
    entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
    entry.focus_set()
    
    def save_edit(event=None):
        new_value = entry.get()
        
        # Get the necessary values
        old_item_id = item_values[0]  # Item ID is in the first column
        
        # Get the lootdrop_id from the currently selected row in loot_tree
        selected_lootdrop = loot_tree.selection()
        if not selected_lootdrop:
            entry.destroy()
            return
            
        lootdrop_id = loot_tree.item(selected_lootdrop[0], "values")[0]
    
        try:
            # Map column names to database fields
            column_to_field = {
                "Item ID": "item_id",
                "Charges": "item_charges",
                "Equip": "equip_item",
                "Chance": "chance",
                "Triv Min Lvl": "trivial_min_level",
                "Triv Max Lvl": "trivial_max_level",
                "Multiplier": "multiplier",
                "NPC Min Lvl": "npc_min_level",
                "NPC Max Lvl": "npc_max_level",
                "Min Xpac": "min_expansion",
                "Max Xpac": "max_expansion"
            }
            
            # Only allow editing if column is in our mapping
            if column_name not in column_to_field:
                status_var.set(f"Column {column_name} is not editable")
                entry.destroy()
                return
                
            # Special handling for Item ID changes
            if column_name == "Item ID":
                # First verify the new item ID exists
                cursor.execute("SELECT name FROM items WHERE id = %s", (new_value,))
                item_result = cursor.fetchone()
                if not item_result:
                    status_var.set(f"Item ID {new_value} does not exist")
                    entry.destroy()
                    return
                # Get the item name for display update
                new_item_name = item_result[0]
                # Update the item_values for display
                item_values[1] = new_item_name  # Update the Item Name column
            
            # Validate numeric fields
            numeric_fields = ["item_id", "charges", "chance", "trivial_min_level", "trivial_max_level", 
                            "multiplier", "npc_min_level", "npc_max_level", 
                            "min_expansion", "max_expansion"]
            
            field_name = column_to_field[column_name]
            if field_name in numeric_fields:
                try:
                    float(new_value)
                except ValueError:
                    status_var.set(f"Invalid numeric value for {column_name}")
                    entry.destroy()
                    return
            
            # Construct and execute the update query
            query = f"""
                UPDATE lootdrop_entries
                SET {column_to_field[column_name]} = %s
                WHERE lootdrop_id = %s AND item_id = %s
            """
            cursor.execute(query, (new_value, lootdrop_id, old_item_id))
            conn.commit()
            
            # Update the display
            item_values[column_index] = new_value
            tree.item(item, values=item_values)
            
            status_var.set("Update successful")
        except mysql.connector.Error as err:
            status_var.set(f"Error updating: {err}")
        finally:
            entry.destroy()
    
    def on_escape(event):
        entry.destroy()
    
    entry.bind("<Return>", save_edit)
    entry.bind("<Escape>", on_escape)
    entry.bind("<FocusOut>", lambda e: entry.destroy())

def on_loottable_edit(event):
    # Get the clicked item and column
    tree = event.widget
    region = tree.identify_region(event.x, event.y)
    if region != "cell":
        return
        
    column = tree.identify_column(event.x)
    item = tree.identify_row(event.y)
    
    if not item or not column:
        return
    
    # Get column index (1-based to 0-based)
    column_index = int(column[1:]) - 1
    
    # Get the column name from the treeview
    column_name = tree["columns"][column_index]
    
    # Get current values
    item_values = list(tree.item(item, "values"))
    current_value = item_values[column_index]
    
    # Get cell bbox relative to tree
    bbox = tree.bbox(item, column)
    if not bbox:
        return
        
    # Create entry widget
    entry = tk.Entry(tree)
    entry.insert(0, current_value)
    entry.select_range(0, tk.END)
    
    # Position entry widget
    entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
    entry.focus_set()
    
    def save_edit(event=None):
        new_value = entry.get()

        # Get the lootdrop_id from the first column
        lootdrop_id = item_values[0]  # LootDrop ID is in the first column

        # Get the loottable_id from loot_id_var
        loottable_id = loot_id_var.get().split(": ")[1]  # Extract the ID from the label

        try:
            # Map column names to database fields
            column_to_field = {
                "LootDrop ID": "lootdrop_id",  # Not editable, but included for completeness
                "LootDrop Name": "name",       # Comes from lootdrop table
                "Multiplier": "multiplier",   # Comes from loottable_entries
                "MinDrop": "mindrop",          # Comes from loottable_entries
                "DropLimit": "droplimit",      # Comes from loottable_entries
                "Probability": "probability"  # Comes from loottable_entries
            }

            # Only allow editing if column is in our mapping
            if column_name not in column_to_field:
                status_var.set(f"Column {column_name} is not editable")
                entry.destroy()
                return

            # Validate numeric fields
            numeric_fields = ["lootdrop_id", "multiplier", "mindrop", "droplimit", "probability"]

            field_name = column_to_field[column_name]
            if field_name in numeric_fields:
                try:
                    float(new_value)
                except ValueError:
                    status_var.set(f"Invalid numeric value for {column_name}")
                    entry.destroy()
                    return

            # Determine which table to update
            if column_name == "LootDrop Name":
                # Update the lootdrop table
                query = f"""
                    UPDATE lootdrop
                    SET {column_to_field[column_name]} = %s
                    WHERE id = %s
                """
                cursor.execute(query, (new_value, lootdrop_id))
            else:
                # Update the loottable_entries table
                query = f"""
                    UPDATE loottable_entries
                    SET {column_to_field[column_name]} = %s
                    WHERE loottable_id = %s AND lootdrop_id = %s
                """
                cursor.execute(query, (new_value, loottable_id, lootdrop_id))

            conn.commit()

            # Update the display
            item_values[column_index] = new_value
            tree.item(item, values=item_values)

            status_var.set("Update successful")
        except mysql.connector.Error as err:
            status_var.set(f"Error updating: {err}")
        finally:
            entry.destroy()
    
    def on_escape(event):
        entry.destroy()
    
    entry.bind("<Return>", save_edit)
    entry.bind("<Escape>", on_escape)
    entry.bind("<FocusOut>", lambda e: entry.destroy())

def add_item_to_lootdrop():
    try:
        # Step 1: Get the currently selected lootdrop_id
        selected_item = loot_tree.selection()
        if not selected_item:
            status_var.set("No lootdrop selected. Please select a lootdrop.")
            return

        lootdrop_id = loot_tree.item(selected_item, "values")[0]  # Assuming the first column is the lootdrop_id

        # Step 2: Fetch a random item_id from the items table
        cursor.execute("SELECT id FROM items ORDER BY RAND() LIMIT 1")
        random_item_id = cursor.fetchone()[0]  # Use a random item_id from the items table

        # Step 3: Insert into lootdrop_entries table
        cursor.execute("""
            INSERT INTO lootdrop_entries (
                lootdrop_id, item_id, item_charges, equip_item, chance, disabled_chance,
                trivial_min_level, trivial_max_level, multiplier, npc_min_level, npc_max_level,
                min_expansion, max_expansion, content_flags, content_flags_disabled
            ) VALUES (%s, %s, 1, 0, 5, 0, 0, 0, 1, 0, 127, -1, -1, NULL, NULL)
        """, (lootdrop_id, random_item_id))

        # Commit the transaction
        conn.commit()

        # Step 4: Refresh the lootdrop entries in the UI
        on_lootdrop_select(selected_item)

        # Update the status bar
        status_var.set(f"Added random item {random_item_id} to lootdrop {lootdrop_id}.")

    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        status_var.set(f"Error: {err}")
 
def add_specific_item_to_lootdrop():
    try:
        # Step 1: Get the currently selected lootdrop_id
        selected_item = loot_tree.selection()
        if not selected_item:
            status_var.set("No lootdrop selected. Please select a lootdrop.")
            return

        lootdrop_id = loot_tree.item(selected_item, "values")[0]  # Assuming the first column is the lootdrop_id

        # Step 2: Get the item ID from the text entry box
        item_id = item_id_entry.get().strip()
        if not item_id:
            status_var.set("No item ID entered. Please enter an item ID.")
            return

        # Validate that the item ID exists in the items table
        cursor.execute("SELECT id FROM items WHERE id = %s", (item_id,))
        if not cursor.fetchone():
            status_var.set(f"Item ID {item_id} does not exist in the items table.")
            return

        # Step 3: Insert into lootdrop_entries table
        cursor.execute("""
            INSERT INTO lootdrop_entries (
                lootdrop_id, item_id, item_charges, equip_item, chance, disabled_chance,
                trivial_min_level, trivial_max_level, multiplier, npc_min_level, npc_max_level,
                min_expansion, max_expansion, content_flags, content_flags_disabled
            ) VALUES (%s, %s, 1, 0, 5, 0, 0, 0, 1, 0, 127, -1, -1, NULL, NULL)
        """, (lootdrop_id, item_id))

        # Commit the transaction
        conn.commit()

        # Step 4: Refresh the lootdrop entries in the UI
        on_lootdrop_select(selected_item)

        # Update the status bar
        status_var.set(f"Added item {item_id} to lootdrop {lootdrop_id}.")

    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        status_var.set(f"Error: {err}")

def remove_item_from_lootdrop():
    try:
        # Step 1: Get the currently selected lootdrop_id
        selected_lootdrop = loot_tree.selection()
        if not selected_lootdrop:
            status_var.set("No lootdrop selected. Please select a lootdrop.")
            return

        lootdrop_id = loot_tree.item(selected_lootdrop[0], "values")[0]  # Lootdrop ID is in the first column

        # Step 2: Get the selected item from the lootdrop entries treeview
        selected_item = loot_tree2.selection()
        if not selected_item:
            status_var.set("No item selected. Please select an item to remove.")
            return

        item_id = loot_tree2.item(selected_item, "values")[0]  # Item ID is in the first column

        # Step 3: Delete the item from the lootdrop_entries table
        cursor.execute("""
            DELETE FROM lootdrop_entries
            WHERE lootdrop_id = %s AND item_id = %s
        """, (lootdrop_id, item_id))

        # Commit the transaction
        conn.commit()

        # Step 4: Refresh the lootdrop entries in the UI
        on_lootdrop_select(selected_lootdrop)

        # Update the status bar
        status_var.set(f"Removed item {item_id} from lootdrop {lootdrop_id}.")

    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        status_var.set(f"Error: {err}")

def fetch_item_data(item_id, loot_table_tree, loot_drop_tree):
    try:
        # Clear existing data in the Treeviews
        for row in loot_table_tree.get_children():
            loot_table_tree.delete(row)
        for row in loot_drop_tree.get_children():
            loot_drop_tree.delete(row)

        # Step 1: Fetch lootdrops containing the item
        cursor.execute("""
            SELECT lootdrop_id
            FROM lootdrop_entries
            WHERE item_id = %s
        """, (item_id,))
        lootdrop_ids = [row[0] for row in cursor.fetchall()]

        if not lootdrop_ids:
            tk.messagebox.showinfo("No Results", f"No lootdrops found for item ID {item_id}.")
            return

        # Step 2: Fetch loottables referencing the lootdrops
        cursor.execute("""
            SELECT DISTINCT loottable_id
            FROM loottable_entries
            WHERE lootdrop_id IN (%s)
        """ % ",".join(["%s"] * len(lootdrop_ids)), lootdrop_ids)
        loottable_ids = [row[0] for row in cursor.fetchall()]

        if not loottable_ids:
            tk.messagebox.showinfo("No Results", f"No loottables found for item ID {item_id}.")
            return

        # Step 3: Fetch details for the loottables
        cursor.execute("""
            SELECT id, name, mincash, maxcash, avgcoin
            FROM loottable
            WHERE id IN (%s)
        """ % ",".join(["%s"] * len(loottable_ids)), loottable_ids)

        for row in cursor.fetchall():
            loot_table_tree.insert("", "end", values=row)

        # Step 4: Fetch details for the lootdrops
        cursor.execute("""
            SELECT ld.id, ld.name, lde.item_id, lde.chance
            FROM lootdrop ld
            JOIN lootdrop_entries lde ON ld.id = lde.lootdrop_id
            WHERE ld.id IN (%s)
        """ % ",".join(["%s"] * len(lootdrop_ids)), lootdrop_ids)

        for row in cursor.fetchall():
            loot_drop_tree.insert("", "end", values=row)

    except mysql.connector.Error as err:
        tk.messagebox.showerror("Error", f"Database error: {err}")

def add_lootdrop_to_loottable():
    try:
        # Step 1: Find the next available lootdrop_id
        next_lootdrop_id = find_next_available_id("lootdrop", "id")
        if next_lootdrop_id is None:
            return

        # Step 2: Insert into lootdrop table
        lootdrop_name = f"generated_lootdrop_{next_lootdrop_id}"
        cursor.execute("""
            INSERT INTO lootdrop (id, name, min_expansion, max_expansion, content_flags, content_flags_disabled)
            VALUES (%s, %s, -1, -1, NULL, NULL)
        """, (next_lootdrop_id, lootdrop_name))

        # Step 3: Insert into lootdrop_entries table with a placeholder item_id
        cursor.execute("SELECT id FROM items LIMIT 1")
        placeholder_item_id = cursor.fetchone()[0]  # Use the first item_id from the items table

        cursor.execute("""
            INSERT INTO lootdrop_entries (
                lootdrop_id, item_id, item_charges, equip_item, chance, disabled_chance,
                trivial_min_level, trivial_max_level, multiplier, npc_min_level, npc_max_level,
                min_expansion, max_expansion, content_flags, content_flags_disabled
            ) VALUES (%s, %s, 1, 0, 5, 0, 0, 0, 1, 0, 127, -1, -1, NULL, NULL)
        """, (next_lootdrop_id, placeholder_item_id))

        # Step 4: Find the next available loottable_id
        next_loottable_id = find_next_available_id("loottable", "id")
        if next_loottable_id is None:
            return

        # Step 5: Insert into loottable table
        loottable_name = f"generated_loottable_{next_loottable_id}"
        cursor.execute("""
            INSERT INTO loottable (id, name, mincash, maxcash, avgcoin, done, min_expansion, max_expansion, content_flags, content_flags_disabled)
            VALUES (%s, %s, 500, 5000, 0, 0, -1, -1, NULL, NULL)
        """, (next_loottable_id, loottable_name))

        # Step 6: Insert into loottable_entries table
        cursor.execute("""
            INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
            VALUES (%s, %s, 1, 0, 1, 100)
        """, (next_loottable_id, next_lootdrop_id))

        # Commit the transaction
        conn.commit()

        # Update the status bar
        status_var.set(f"Added lootdrop {next_lootdrop_id} and loottable {next_loottable_id}.")

    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        tk

def add_new_lootdrop():
    try:
        # Get the currently selected loottable_id from loot_id_var
        loottable_id = loot_id_var.get().split(": ")[1]  # Extract the ID from the label
        if not loottable_id:
            status_var.set("No loottable selected.")
            return

        # Step 1: Find the next available lootdrop_id
        cursor.execute("SELECT MIN(id) + 1 FROM lootdrop WHERE (id + 1) NOT IN (SELECT id FROM lootdrop)")
        next_lootdrop_id = cursor.fetchone()[0]
        if next_lootdrop_id is None:
            next_lootdrop_id = 1  # Default to 1 if no gaps are found

        # Step 2: Insert into lootdrop table
        lootdrop_name = f"generated_lootdrop_{next_lootdrop_id}"
        cursor.execute("""
            INSERT INTO lootdrop (id, name, min_expansion, max_expansion, content_flags, content_flags_disabled)
            VALUES (%s, %s, -1, -1, NULL, NULL)
        """, (next_lootdrop_id, lootdrop_name))

        # Step 3: Insert into lootdrop_entries table with a placeholder item_id
        cursor.execute("SELECT id FROM items LIMIT 1")
        placeholder_item_id = cursor.fetchone()[0]  # Use the first item_id from the items table

        cursor.execute("""
            INSERT INTO lootdrop_entries (
                lootdrop_id, item_id, item_charges, equip_item, chance, disabled_chance,
                trivial_min_level, trivial_max_level, multiplier, npc_min_level, npc_max_level,
                min_expansion, max_expansion, content_flags, content_flags_disabled
            ) VALUES (%s, %s, 1, 0, 5, 0, 0, 0, 1, 0, 127, -1, -1, NULL, NULL)
        """, (next_lootdrop_id, placeholder_item_id))

        # Step 4: Insert into loottable_entries table
        cursor.execute("""
            INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
            VALUES (%s, %s, 1, 0, 1, 100)
        """, (loottable_id, next_lootdrop_id))

        # Commit the transaction
        conn.commit()

        # Refresh the loot_tree to show the new lootdrop
        on_npc_select(None)  # Re-trigger the NPC selection to refresh the loot table

        status_var.set(f"Added new lootdrop {next_lootdrop_id} to loottable {loottable_id}.")
    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def remove_selected_lootdrop():
    try:
        # Get the selected item from the treeview
        selected_item = loot_tree.selection()
        if not selected_item:
            status_var.set("No lootdrop selected.")
            return

        # Get the lootdrop_id from the selected item
        item_values = loot_tree.item(selected_item, "values")
        lootdrop_id = item_values[0]  # LootDrop ID is in the first column

        # Get the loottable_id from loot_id_var
        loottable_id = loot_id_var.get().split(": ")[1]  # Extract the ID from the label

        # Step 1: Delete from loottable_entries table
        cursor.execute("""
            DELETE FROM loottable_entries
            WHERE loottable_id = %s AND lootdrop_id = %s
        """, (loottable_id, lootdrop_id))

        # Commit the transaction
        conn.commit()

        # Refresh the loot_tree to reflect the changes
        on_npc_select(None)  # Re-trigger the NPC selection to refresh the loot table

        status_var.set(f"Removed lootdrop {lootdrop_id} from loottable {loottable_id}.")
    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def add_existing_lootdrop_to_loottable():
    try:
        # Get the currently selected loottable_id from loot_id_var
        loottable_id = loot_id_var.get().split(": ")[1]  # Extract the ID from the label
        if not loottable_id:
            status_var.set("No loottable selected.")
            return

        # Get the lootdrop_id from the text entry widget
        lootdrop_id = lootdrop_id_entry.get()
        if not lootdrop_id:
            status_var.set("No lootdrop ID entered.")
            return

        # Convert the lootdrop_id to an integer
        lootdrop_id = int(lootdrop_id)

        # Check if the lootdrop_id exists in the lootdrop table
        cursor.execute("SELECT id FROM lootdrop WHERE id = %s", (lootdrop_id,))
        if not cursor.fetchone():
            status_var.set(f"Lootdrop ID {lootdrop_id} does not exist.")
            return

        # Check if the lootdrop is already linked to the loottable
        cursor.execute("""
            SELECT lootdrop_id FROM loottable_entries 
            WHERE loottable_id = %s AND lootdrop_id = %s
        """, (loottable_id, lootdrop_id))
        if cursor.fetchone():
            status_var.set(f"Lootdrop ID {lootdrop_id} is already linked to this loottable.")
            return

        # Step 2: Insert into loottable_entries table
        cursor.execute("""
            INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
            VALUES (%s, %s, 1, 0, 1, 100)
        """, (loottable_id, lootdrop_id))

        # Commit the transaction
        conn.commit()

        # Refresh the loot_tree to show the updated loottable
        on_npc_select(None)  # Re-trigger the NPC selection to refresh the loot table

        status_var.set(f"Added existing lootdrop {lootdrop_id} to loottable {loottable_id}.")
    except ValueError:
        status_var.set("Invalid lootdrop ID. Please enter a valid integer.")
    except mysql.connector.Error as err:
        conn.rollback()  # Rollback in case of error
        tk.messagebox.showerror("Database Error", f"Error: {err}")

def refresh_lootdrop_entries(lootdrop_id):
    # Clear the current entries in the lootdrop treeview
    for row in loot_tree2.get_children():
        loot_tree2.delete(row)

    # Fetch the updated lootdrop entries from the database
    cursor.execute("""
        SELECT item_id, item_name, item_charges, equip_item, chance, trivial_min_level, trivial_max_level,
               multiplier, npc_min_level, npc_max_level, min_expansion, max_expansion
        FROM lootdrop_entries
        WHERE lootdrop_id = %s
    """, (lootdrop_id,))

    # Insert the new entries into the treeview
    for row in cursor.fetchall():
        loot_tree2.insert("", "end", values=row)

# Define the root window
root = tk.Tk()
root.title("NPC Loot Tool")
root.geometry("1400x850")
style = theme.set_dark_theme(root)

## BEGIN TOP FRAME ## Search and Info Frame
##      Three Sub-Frames -> Search Boxes (search_frame), Unused IDs (find_unused_frame), Utilities (utilities_frame)

top_root = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
top_root.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Search Frame
search_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
search_frame.grid(row=0, column=0, padx=5, pady=5)

# Zone Search
ttk.Label(search_frame, text="Enter Zone Shortname:").grid(row=0, column=0, sticky=tk.W)
zone_entry = ttk.Entry(search_frame, width=20)
zone_entry.grid(row=0, column=1, padx=5, pady=5)
search_zone_button = ttk.Button(search_frame, text="Search Zone", command=search_zone)
search_zone_button.grid(row=0, column=2, padx=5, pady=5)

# NPC Name Search
ttk.Label(search_frame, text="Enter NPC Name:").grid(row=1, column=0, sticky=tk.W)
npc_name_entry = ttk.Entry(search_frame, width=20)
npc_name_entry.grid(row=1, column=1, padx=5, pady=5)
search_npc_name_button = ttk.Button(search_frame, text="Search NPC Name", command=search_npc_name)
search_npc_name_button.grid(row=1, column=2, padx=5, pady=5)

# Loottable ID Search
ttk.Label(search_frame, text="Enter Loottable ID:").grid(row=2, column=0, sticky=tk.W)
loottable_id_entry = ttk.Entry(search_frame, width=20)
loottable_id_entry.grid(row=2, column=1, padx=5, pady=5)
search_loottable_button = ttk.Button(search_frame, text="Search Loottable", command=search_loottable_id)
search_loottable_button.grid(row=2, column=2, padx=5, pady=5)

# Clear Button

clear_button = ttk.Button(search_frame, text="Clear All Windows", command=clear_results)
clear_button.grid(row=3, column=0, columnspan=2, pady=5,padx=20)

clear_button = ttk.Button(search_frame, text="Clear Search Windows", command=clear_search_results)
clear_button.grid(row=3, column=2, pady=5, padx=5)

#
###END SEARCH FRAME###

###BEGIN UNUSED IDS LOOKUP###
#

find_unused_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
find_unused_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

ttk.Label(find_unused_frame, text="Unused IDs").grid(row=0, column=0, columnspan=2)
find_unused_button = ttk.Button(find_unused_frame, text="Refresh", command=find_unused_ids)
find_unused_button.grid(row=0, column=1, pady=5)

ttk.Label(find_unused_frame, text="Unused Loot Table IDs:").grid(row=1, column=0, sticky=tk.E)
unused_loottable_label = ttk.Label(find_unused_frame, text="...")
unused_loottable_label.grid(row=1, column=1, columnspan=2, pady=5, padx=5, sticky=tk.W)

ttk.Label(find_unused_frame, text="Unused Lootdrop IDs:").grid(row=2, column=0, sticky=tk.E)
unused_lootdrop_label = ttk.Label(find_unused_frame, text="...")
unused_lootdrop_label.grid(row=2, column=1, columnspan=2, pady=5, padx=5, sticky=tk.W)

# Create New Loottable AND Lootdrop with first available unused values.
add_lootdrop_to_loottable_button = ttk.Button(find_unused_frame, text="Create", command=add_lootdrop_to_loottable)
add_lootdrop_to_loottable_button.grid(row=6, column=0, pady=5, padx=5, sticky=tk.E)

#
###END UNUSED IDS LOOKUP FRAME###


###BEGIN IMAGES FRAME###
#
image_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
image_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

backingimage2 = Image.open("images/other/default.jpg")  # Replace with your image path
bg2_image = ImageTk.PhotoImage(backingimage2)

canvas = tk.Canvas(image_frame, width=bg2_image.width(), height=bg2_image.height(), highlightthickness=0)
canvas.grid(row=0, column=0, sticky="nsew")
canvas.create_image(0, 0, anchor="nw", image=bg2_image)



backingimage = Image.open("images/other/itemback.png")  # Replace with your image path
bg_image = ImageTk.PhotoImage(backingimage)

item_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
item_frame.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)

canvas = tk.Canvas(item_frame, width=bg_image.width(), height=bg_image.height(), highlightthickness=0)
canvas.grid(row=0, column=0, sticky="nsew")
canvas.create_image(0, 0, anchor="nw", image=bg_image)

#
###END IMAGES FRAME###
#
###END TOP ROOT FRAME###
#

#
###BEGIN MIDDLE ROOT FRAME###
## Middle Root Frame: Three Sub-Frames -> Loot Table (loot_tree_frame), Loot Mod (loot_mod_frame) , and Loot Drop (loot_tree2_frame)
#

middle_root_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
middle_root_frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")

###BEGIN LOOT TABLE FRAME###
#

# Define the variables
loot_id_var = tk.StringVar(value="Loot Table ID: ")

loottable_frame = ttk.Frame(middle_root_frame)
loottable_frame.grid(row=0, column=0, padx=5, pady=5)

loottable_mod_frame = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
loottable_mod_frame.grid(row=0, column=0, sticky="w", pady=5)

ttk.Label(loottable_mod_frame,textvariable=loot_id_var, font=("Arial", 12, "bold")).grid(row=0, sticky="n", pady=5, columnspan=2)

ttk.Label(loottable_mod_frame, text="Loot Table Name:").grid(row=1, column=0, sticky="w")
loottable_name_entry = ttk.Entry(loottable_mod_frame, width=20)
loottable_name_entry.grid(row=1, column=1, padx=5)
ttk.Label(loottable_mod_frame, text="Avg Coin:").grid(row=1, column=2, sticky="w")
avgcoin_entry = ttk.Entry(loottable_mod_frame, width=8)
avgcoin_entry.grid(row=1, column=3, padx=5, pady=3, sticky="w")

ttk.Label(loottable_mod_frame, text="Min Cash:").grid(row=2, column=0, sticky="w")
mincash_entry = ttk.Entry(loottable_mod_frame, width=5)
mincash_entry.grid(row=2, column=1, padx=5, sticky="w")

ttk.Label(loottable_mod_frame, text="Max Cash:").grid(row=2, column=2, sticky="w")
maxcash_entry = ttk.Entry(loottable_mod_frame, width=8)
maxcash_entry.grid(row=2, column=3, padx=5, pady=3, sticky="w")

ttk.Label(loottable_mod_frame, text="Min Xpac:").grid(row=3, column=0, sticky="w")
minexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
minexpac_entry.grid(row=3, column=1, padx=5, sticky="w")

ttk.Label(loottable_mod_frame, text="Max Xpac:").grid(row=3, column=2, sticky="w")
maxexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
maxexpac_entry.grid(row=3, column=3, padx=5, pady=3, sticky="w")

ttk.Label(loottable_mod_frame, text="Update Changes").grid(row=1, column=4, padx=17, sticky="nsew")

update_cash_button = ttk.Button(loottable_mod_frame, text="Update", command=update_loottable)
update_cash_button.grid(row=2, column=4, padx=25, pady=3, sticky="n",rowspan=2)

loottable_mod_frame2 = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
loottable_mod_frame2.grid(row=1, column=0, sticky="w", pady=5)

add_new_lootdrop_button = ttk.Button(loottable_mod_frame2, text="Create Lootdrop & Add", command=add_new_lootdrop)
add_new_lootdrop_button.grid(row=0, column=0, padx=3)

remove_button = ttk.Button(loottable_mod_frame2, text="Remove Selected Lootdrop", command=remove_selected_lootdrop)
remove_button.grid(row=0, column=2, padx=3)

add_existing_lootdrop_button = ttk.Button(loottable_mod_frame2, text="Add Existing Lootdrop ID:", command=add_existing_lootdrop_to_loottable)
add_existing_lootdrop_button.grid(row=0, column=3, pady=5, padx=3)

lootdrop_id_entry = ttk.Entry(loottable_mod_frame2, width=10)
lootdrop_id_entry.grid(row=0, column=4, pady=5, padx=2)

# LOOT TABLE TREE SECTION

loottable_tree_frame = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
loottable_tree_frame.grid(row=2, column=0, sticky="w", pady=5)
ttk.Label(loottable_tree_frame, text="Loot Table Entries", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")

loot_tree = ttk.Treeview(loottable_tree_frame, height=6, columns=("LootDrop ID", "LootDrop Name", "Multiplier", "MinDrop", "DropLimit", "Probability"), show="headings")
for col in loot_tree["columns"]:
    loot_tree.heading(col, text=col)
    loot_tree.column(col, width=100, stretch=True)
loot_tree.grid(row=1, column=0, sticky="w", pady=5)

# Set column widths and stretch behavior
loot_tree.column("LootDrop ID", width=80, stretch=False)
loot_tree.column("LootDrop Name", width=160, stretch=False)
loot_tree.column("Multiplier", width=65, stretch=False)
loot_tree.column("MinDrop", width=65, stretch=False)
loot_tree.column("DropLimit", width=65, stretch=False)
loot_tree.column("Probability", width=69, stretch=False)

#
###END LOOT TABLE FRAME###

###BEGIN LOOTDROP FRAME###
#

# LOOT DROP TREE SECTION

lootdrop_frame = ttk.Frame(middle_root_frame)
lootdrop_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

loot_tree2_frame = ttk.Frame(lootdrop_frame, relief=tk.SUNKEN, borderwidth=2)
loot_tree2_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)

ttk.Label(loot_tree2_frame, text="Loot Drop Entries", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
loot_tree2 = ttk.Treeview(loot_tree2_frame, columns=("Item ID", "Item Name", "Charges", "Equip", "Chance", 
                                                     "Triv Min Lvl", "Triv Max Lvl", "Multiplier", 
                                                     "NPC Min Lvl", "NPC Max Lvl", "Min Xpac", "Max Xpac"), show="headings")
for col in loot_tree2["columns"]:
    loot_tree2.heading(col, text=col)
    loot_tree2.column(col, width=100, stretch=True)
loot_tree2.grid(row=1, column=0, sticky="nsew", columnspan=2)

# Set column widths and stretch behavior
loot_tree2.column("Item ID", width=55, stretch=False)
loot_tree2.column("Item Name", width=130, stretch=False)
loot_tree2.column("Charges", width=40, stretch=False)
loot_tree2.column("Equip", width=40, stretch=False)
loot_tree2.column("Chance", width=40, stretch=False)
loot_tree2.column("Triv Min Lvl", width=75, stretch=False)
loot_tree2.column("Triv Max Lvl", width=75, stretch=False)
loot_tree2.column("Multiplier", width=65, stretch=False)
loot_tree2.column("NPC Min Lvl", width=75, stretch=False)
loot_tree2.column("NPC Max Lvl", width=75, stretch=False)
loot_tree2.column("Min Xpac", width=65, stretch=False)
loot_tree2.column("Max Xpac", width=65, stretch=False)

# LOOT DROP MOD SECTION

lootdrop_mod_frame = ttk.Frame(lootdrop_frame, relief=tk.SUNKEN, borderwidth=2)
lootdrop_mod_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

remove_item_button = ttk.Button(lootdrop_mod_frame, text="Remove Selected Item from Lootdrop", command=remove_item_from_lootdrop)
remove_item_button.grid(row=0, column=1, pady=5, columnspan=2, padx=10)

# Add Item to Lootdrop Button
add_item_to_lootdrop_button = ttk.Button(lootdrop_mod_frame, text="Add Random Item ID to selected Lootdrop", command=add_item_to_lootdrop)
add_item_to_lootdrop_button.grid(row=0, column=0, pady=5, padx=5)

# Lookup Item by ID Button
lookup_item_button = ttk.Button(lootdrop_mod_frame, text="Lookup Item by ID", command=lookup_item_by_id)
lookup_item_button.grid(row=0, column=3, pady=5, padx=3)


# Add a label for the text entry
ttk.Label(lootdrop_mod_frame, text="------------> Item ID:").grid(row=1, column=0, padx=5, pady=5, sticky="e")

# Add a text entry box
item_id_entry = ttk.Entry(lootdrop_mod_frame)
item_id_entry.grid(row=1, column=1, padx=2, pady=5, sticky="w")

# Add a button to add the specific item
add_specific_item_button = ttk.Button(lootdrop_mod_frame,text="Add Specific Item",command=add_specific_item_to_lootdrop)
add_specific_item_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")

notes_button = ttk.Button(lootdrop_mod_frame, text="Notes", command=open_notes_window)
notes_button.grid(row=1, column=2,pady=5)

#
###END Loot Drop FRAME###
#
###END MIDDLE ROOT FRAME###
#

#
## START BOTTOM SECTION: NPC Tree ##
#

bottom_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=2)
bottom_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

npc_tree_frame = ttk.Frame(bottom_frame)
npc_tree_frame.grid(row=0, column=0, sticky="nsew")

ttk.Label(npc_tree_frame, text="  NPC List and Editor", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
npc_tree = ttk.Treeview(npc_tree_frame, columns=("ID", "Name", "Lvl", "Race", "Class", "Body", "HP", "Mana",
                                               "Gender", "Texture", "Helmtexture", "Size", "Loottable ID", "Spells ID", "Faction ID",
                                               "Mindmg", "Maxdmg", "Npcspecialattks", "Special Abilities", "MR", "CR", "DR", "FR", "PR", "AC",
                                               "Attack Delay", "STR", "STA", "DEX", "AGI", "_INT", "WIS", "Maxlevel",
                                               "Skip Global Loot", "Exp Mod"), show="headings")

# Define column widths in a dictionary
column_widths = {
    "ID": 50,
    "Name": 125,
    "Lvl": 25,
    "Race": 35,
    "Class": 39,
    "Body": 36,
    "HP": 25,
    "Mana": 35,
    "Gender": 45,
    "Texture": 45,
    "Helmtexture": 45,
    "Size": 45,
    "Loottable ID": 65,
    "Spells ID": 65,
    "Faction ID": 65,
    "Mindmg": 45,
    "Maxdmg": 45,
    "Npcspecialattks": 35,
    "Special Abilities": 35,
    "MR": 25,
    "CR": 25,
    "DR": 25,
    "FR": 25,
    "PR": 25,
    "AC": 25,
    "Attack Delay": 45,
    "STR": 30,
    "STA": 30,
    "DEX": 30,
    "AGI": 30,
    "_INT": 30,
    "WIS": 30,
    "Maxlevel": 15,
    "Skip Global Loot": 15,
    "Exp Mod": 15
}

# Configure columns and set headings in a single loop
for col, width in column_widths.items():
    npc_tree.column(col, width=width, stretch=False)
    npc_tree.heading(col, text=col)

npc_tree.grid(row=1, column=0, sticky="nsew")

# Add and Define status_var
status_var = tk.StringVar(value="Ready")
status_bar = ttk.Label(root, textvariable=status_var)
status_bar.grid(row=4, column=0, columnspan=3)  # Use grid for status_bar

## END BOTTOM SECTION ##

# Setup sorting for all treeviews after they're created
setup_treeview_sorting(npc_tree)
setup_treeview_sorting(loot_tree)
setup_treeview_sorting(loot_tree2)

# Bind the selection events
npc_tree.bind("<<TreeviewSelect>>", on_npc_select)
npc_tree.bind("<Double-1>", on_npc_edit)
loot_tree.bind("<<TreeviewSelect>>", on_lootdrop_select)
loot_tree.bind("<Double-1>", on_loottable_edit)
loot_tree2.bind("<Double-1>", on_lootdrop_edit)
loot_tree2.bind('<<TreeviewSelect>>', on_item_select)

create_db()
find_unused_ids()
root.mainloop()
