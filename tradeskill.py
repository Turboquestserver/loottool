import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import theme
from dictionaries import TRADESKILL_IDS, CONTAINER_IDS
import random

def create_db_connection():
    try:
        db = mysql.connector.connect(
            host="192.168.1.105",
            user="eqemu",
            password="eqemu",
            database="peq"
        )
        return db
    except Error as e:
        print(f"Error: {e}")
        return None

db = create_db_connection()
cursor = db.cursor() if db else None

# Helper functions
def refresh_treeview(tree):
    """Refresh the given Treeview by clearing and repopulating it."""
    tree.delete(*tree.get_children())
    if tree == recipe_tree:
        load_recipes()
    elif tree == components_tree:
        load_recipe_entries()
    elif tree == containers_tree:
        load_recipe_entries()
    elif tree == results_tree:
        load_recipe_entries()

def fetch_data(query, params=()):
    """Fetch data from the database."""
    if cursor:
        cursor.execute(query, params)
        return cursor.fetchall()
    return []

def execute_update(query, params=()):
    """Execute an update query (INSERT, UPDATE, DELETE)."""
    if cursor:
        try:
            cursor.execute(query, params)
            db.commit()
            return True
        except Error as e:
            print(f"Error updating data: {e}")
            db.rollback()
            return False
    return False

# Recipe and entry loading
def load_recipes(event=None):
    """Load recipes based on the selected tradeskill."""
    recipe_tree.delete(*recipe_tree.get_children())
    clear_recipe_entries()
    tradeskill_name = tradeskill_var.get()
    tradeskill_id = next((id for id, name in TRADESKILL_IDS.items() if name == tradeskill_name), None)
    if tradeskill_id:
        data = fetch_data("SELECT id, name, skillneeded, trivial, nofail, replace_container, notes, must_learn, learned_by_item_id, quest, enabled, min_expansion, max_expansion FROM tradeskill_recipe WHERE tradeskill = %s", (tradeskill_id,))
        for row in data:
            recipe_tree.insert("", "end", values=row)

def clear_recipe_entries():
    """Clear all recipe entry subtrees."""
    for subtree in [components_tree, containers_tree, results_tree]:
        subtree.delete(*subtree.get_children())

def load_recipe_entries(event=None):
    """Load recipe entries for the selected recipe."""
    clear_recipe_entries()
    selected = recipe_tree.selection()
    if selected:
        recipe_id = recipe_tree.item(selected[0], "values")[0]
        query = """
        SELECT tre.id, tre.item_id, COALESCE(i.name, 'No Name') AS name, tre.successcount, tre.failcount, tre.componentcount, tre.salvagecount, tre.iscontainer
        FROM tradeskill_recipe_entries tre
        LEFT JOIN items i ON tre.item_id = i.id
        WHERE tre.recipe_id = %s
        """
        data = fetch_data(query, (recipe_id,))
        for row in data:
            entry_id, item_id, item_name, successcount, failcount, componentcount, salvagecount, iscontainer = row
            if iscontainer:
                container_name = get_container_name(item_id)
                containers_tree.insert("", "end", values=(entry_id, item_id, container_name))
            elif successcount > 0:
                results_tree.insert("", "end", values=(entry_id, item_id, item_name, successcount))
            else:
                components_tree.insert("", "end", values=(entry_id, item_id, item_name, componentcount, failcount, salvagecount))

def get_container_name(container_id):
    """Get container name from ID."""
    if container_id in CONTAINER_IDS:
        return CONTAINER_IDS[container_id]
    item_name = fetch_data("SELECT name FROM items WHERE id = %s", (container_id,))
    return item_name[0][0] if item_name else f"Unknown Container (ID: {container_id})"

# Delete functions
def delete_selected_container():
    """Delete the selected container from the database and Treeview."""
    selected_item = containers_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a container to delete.")
        return
    entry_id = containers_tree.item(selected_item, "values")[0]
    if execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
        refresh_treeview(containers_tree)

def delete_selected_comp():
    """Delete the selected component from the database and Treeview."""
    selected_item = components_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a component to delete.")
        return
    entry_id = components_tree.item(selected_item, "values")[0]
    if execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
        refresh_treeview(components_tree)

def delete_selected_result():
    """Delete the selected result from the database and Treeview."""
    selected_item = results_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a result to delete.")
        return
    entry_id = results_tree.item(selected_item, "values")[0]
    if execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
        refresh_treeview(results_tree)


# Helper function to get the current recipe ID
def get_current_recipe_id():
    """Get the current recipe ID from the selected recipe in the recipe_tree."""
    selected = recipe_tree.selection()
    if not selected:
        messagebox.showwarning("No Recipe Selected", "Please select a recipe first.")
        return None
    recipe_id = recipe_tree.item(selected[0], "values")[0]
    return recipe_id

# Add functions
def add_random_comp():
    """Add a random component to the database and Treeview."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    cursor.execute("SELECT id FROM items ORDER BY RAND() LIMIT 1")
    random_item_id = cursor.fetchone()[0]
    
    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 0, 0, 1, 0, 0)",
        (recipe_id, random_item_id)
    ):
        refresh_treeview(components_tree)

def add_stock_container():
    """Add a random stock container to the database and Treeview."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    random_container_id = random.choice(list(CONTAINER_IDS.keys()))
    
    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 0, 0, 1, 0, 1)",
        (recipe_id, random_container_id)
    ):
        refresh_treeview(containers_tree)

def add_random_result():
    """Add a random result to the database and Treeview."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    cursor.execute("SELECT id FROM items ORDER BY RAND() LIMIT 1")
    random_item_id = cursor.fetchone()[0]
    
    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 1, 0, 1, 0, 0)",
        (recipe_id, random_item_id)
    ):
        refresh_treeview(results_tree)

def add_specific_comp():
    """Add a specific component based on the item ID entered in the entry widget."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    item_id = comp_itemid_var.get().strip()
    if not item_id or not item_id.isdigit():
        messagebox.showwarning("Invalid Input", "Please enter a valid item ID.")
        return

    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 0, 0, 1, 0, 0)",
        (recipe_id, int(item_id))
    ):
        refresh_treeview(components_tree)

def add_specific_container():
    """Add a specific container based on the container ID entered in the entry widget."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    container_id = contain_itemid_var.get().strip()
    if not container_id or not container_id.isdigit():
        messagebox.showwarning("Invalid Input", "Please enter a valid container ID.")
        return

    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 0, 0, 1, 0, 1)",
        (recipe_id, int(container_id))
    ):
        refresh_treeview(containers_tree)

def add_specific_result():
    """Add a specific result based on the item ID entered in the entry widget."""
    recipe_id = get_current_recipe_id()
    if recipe_id is None:
        return
        
    item_id = result_itemid_var.get().strip()
    if not item_id or not item_id.isdigit():
        messagebox.showwarning("Invalid Input", "Please enter a valid item ID.")
        return

    if execute_update(
        "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
        "VALUES (%s, %s, 1, 0, 1, 0, 0)",
        (recipe_id, int(item_id))
    ):
        refresh_treeview(results_tree)

# Search and create functions
def search_recipes():
    """Search recipes by name or ID."""
    search_term = search_var.get().strip()
    if not search_term:
        recipe_tree.delete(*recipe_tree.get_children())
        return
    recipe_tree.delete(*recipe_tree.get_children())
    query = """
    SELECT id, name, skillneeded, trivial, nofail, replace_container, notes, must_learn, learned_by_item_id, quest, enabled, min_expansion, max_expansion
    FROM tradeskill_recipe
    WHERE name LIKE %s OR id = %s
    """
    data = fetch_data(query, (f"%{search_term}%", search_term if search_term.isdigit() else -1))
    for row in data:
        recipe_tree.insert("", "end", values=row)


def create_new_recipe():
    #not implemented yet
    return
    
def open_item_search():  # Function to open the item search popout window
    popout = tk.Toplevel(root)
    popout.title("Search Item by ID")
    popout.geometry("600x400")

    item_id_var = tk.StringVar()  # Item ID Entry
    ttk.Label(popout, text="Item ID:").grid(row=0, column=0, padx=5, pady=5)
    item_id_entry = ttk.Entry(popout, textvariable=item_id_var)
    item_id_entry.grid(row=0, column=1, padx=5, pady=5)

    def search_item():  # Search Button
        item_id = item_id_var.get().strip()
        if not item_id.isdigit():
            tk.messagebox.showerror("Error", "Please enter a valid numeric Item ID.")
            return

        item_id = int(item_id)

        # Clear previous results
        for subtree in [components_results_tree, results_results_tree]:
            subtree.delete(*subtree.get_children())

        # Fetch item name
        item_name = fetch_data("SELECT name FROM items WHERE id = %s", (item_id,))
        if not item_name:
            tk.messagebox.showerror("Error", f"Item ID {item_id} not found in the database.")
            return
        item_name = item_name[0][0]

        # Fetch occurrences in Components (across all recipes)
        components_data = fetch_data("""
        SELECT tre.recipe_id, r.name, tre.componentcount
        FROM tradeskill_recipe_entries tre
        JOIN tradeskill_recipe r ON tre.recipe_id = r.id
        WHERE tre.item_id = %s AND tre.iscontainer = 0 AND tre.successcount = 0
        """, (item_id,))
        for row in components_data:
            components_results_tree.insert("", "end", values=row)

        # Fetch occurrences in Results (across all recipes)
        results_data = fetch_data("""
        SELECT tre.recipe_id, r.name, tre.successcount
        FROM tradeskill_recipe_entries tre
        JOIN tradeskill_recipe r ON tre.recipe_id = r.id
        WHERE tre.item_id = %s AND tre.successcount > 0
        """, (item_id,))
        for row in results_data:
            results_results_tree.insert("", "end", values=row)

        # Update headers
        components_header.config(text=f"Components (Item: {item_name})")
        results_header.config(text=f"Results (Item: {item_name})")

    ttk.Button(popout, text="Search", command=search_item).grid(row=0, column=2, padx=5, pady=5)

    def link_to_recipe(event):  # Function to link back to the recipe in the main window
        selected_tree = event.widget
        selected_item = selected_tree.selection()
        if selected_item:
            recipe_id = selected_tree.item(selected_item[0], "values")[0]

            # Fetch the tradeskill for the selected recipe
            query = """
            SELECT tradeskill
            FROM tradeskill_recipe
            WHERE id = %s
            """
            tradeskill_id = fetch_data(query, (recipe_id,))
            if tradeskill_id:
                tradeskill_id = tradeskill_id[0][0]
                # Set the dropdown to the correct tradeskill
                tradeskill_name = TRADESKILL_IDS.get(tradeskill_id, "Unknown Tradeskill")
                tradeskill_var.set(tradeskill_name)
                # Load recipes for the selected tradeskill
                load_recipes()

            # Find and select the recipe in the main window's recipe_tree
            for child in recipe_tree.get_children():
                if recipe_tree.item(child, "values")[0] == recipe_id:
                    recipe_tree.selection_set(child)
                    recipe_tree.focus(child)
                    recipe_tree.see(child)
                    # Load the recipe entries for the selected recipe
                    load_recipe_entries()
                    break

    # Components Results Treeview
    components_header = ttk.Label(popout, text="Components", font=("Arial", 12, "bold"))
    components_header.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    components_results_tree = ttk.Treeview(popout, columns=("Recipe ID", "Recipe Name", "Component Count"), show="headings")
    for col in ("Recipe ID", "Recipe Name", "Component Count"):
        components_results_tree.heading(col, text=col)
        components_results_tree.column(col, width=150, stretch=True)
    components_results_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    components_results_tree.bind("<ButtonRelease-1>", link_to_recipe)

    # Results Results Treeview
    results_header = ttk.Label(popout, text="Results", font=("Arial", 12, "bold"))
    results_header.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    results_results_tree = ttk.Treeview(popout, columns=("Recipe ID", "Recipe Name", "Success Count"), show="headings")
    for col in ("Recipe ID", "Recipe Name", "Success Count"):
        results_results_tree.heading(col, text=col)
        results_results_tree.column(col, width=150, stretch=True)
    results_results_tree.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    results_results_tree.bind("<ButtonRelease-1>", link_to_recipe)

class TreeviewEdit:  # Cell editing functionality
    def __init__(self, tree, editable_columns=None):
        self.tree = tree
        self.editable_columns = editable_columns or []  # List of column indices that can be edited
        self.editing = False
        self.edit_cell = None
        self.edit_entry = None
        
        # Bind double-click to start editing
        self.tree.bind("<Double-1>", self.start_edit)
        # Bind Escape to cancel editing
        self.tree.bind("<Escape>", self.cancel_edit)
        
    def start_edit(self, event):
        # Identify the item and column that was clicked
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1
        
        # Check if this column is editable
        if column_index not in self.editable_columns:
            return
            
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        # Get the current value
        current_value = self.tree.item(item_id, "values")[column_index]
        
        # Calculate position for the entry widget
        x, y, width, height = self.tree.bbox(item_id, column)
        
        # Create an entry widget
        self.edit_entry = ttk.Entry(self.tree)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.focus_set()
        
        # Bind events to save or cancel
        self.edit_entry.bind("<Return>", lambda e: self.save_edit(item_id, column_index))
        self.edit_entry.bind("<FocusOut>", lambda e: self.cancel_edit(e))
        
        self.editing = True
        self.edit_cell = (item_id, column_index)
    
    def save_edit(self, item_id, column_index):
        if not self.editing:
            return
            
        # Get the new value from the entry widget
        new_value = self.edit_entry.get()
        
        # Get all values from the tree item
        values = list(self.tree.item(item_id, "values"))
        
        # Validate the new value based on the column type
        try:
            # For numeric columns, try to convert to int or float
            if column_index in [0, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]:  # Numeric columns in recipe_tree
                new_value = int(new_value)
            elif column_index in [0, 1, 3, 4, 5] and self.tree == components_tree:  # Numeric columns in components_tree
                new_value = int(new_value)
            elif column_index in [0, 1] and self.tree == containers_tree:  # Numeric columns in components_tree
                new_value = int(new_value)
            elif column_index == [0, 1, 3] and self.tree == results_tree:  # Success count in results_tree
                new_value = int(new_value)
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid numeric value.")
            self.edit_entry.focus_set()
            return
        
        # Update the value in the tree
        values[column_index] = new_value
        self.tree.item(item_id, values=values)
        
        # Update the database
        self.update_database(item_id, column_index, new_value)
        
        # Clean up
        if self.edit_entry:
            self.edit_entry.destroy()
        self.editing = False
        self.edit_cell = None
    
    def cancel_edit(self, event):
        if self.editing and self.edit_entry:
            self.edit_entry.destroy()
            self.editing = False
            self.edit_cell = None
    
    def update_database(self, item_id, column_index, new_value):
        # Get the primary key and other values of the selected row
        values = self.tree.item(item_id, "values")

        # Determine which table and column to update based on the treeview and column index
        if self.tree == recipe_tree:
            # Recipe tree (tradeskill_recipe table)
            recipe_id = values[0]  # First column is the recipe ID

            # Map column index to database column name
            column_map = {
                1: "name",
                2: "skillneeded",
                3: "trivial",
                4: "nofail",
                5: "replace_container",
                6: "notes",
                7: "must_learn",
                8: "learned_by_item_id",
                9: "quest",
                10: "enabled",
                11: "min_expansion",
                12: "max_expansion"
            }

            if column_index in column_map:
                column_name = column_map[column_index]
                query = f"UPDATE tradeskill_recipe SET {column_name} = %s WHERE id = %s"
                success = execute_update(query, (new_value, recipe_id))
                if success:
                    messagebox.showinfo("Success", f"Recipe {recipe_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update recipe {recipe_id}.")

        elif self.tree in [components_tree, results_tree, containers_tree]:
            # Components, Results, or Containers tree (tradeskill_recipe_entries table)
            entry_id = values[0]  # First column is the entry ID (primary key)

            # Map column index to database column name
            column_map = {
                0: "id",  # entry_id
                1: "item_id",
                3: "componentcount",
                4: "failcount",
                5: "salvagecount"
            }

            if column_index in column_map:
                column_name = column_map[column_index]
                # Use entry_id to identify the specific row
                query = f"UPDATE tradeskill_recipe_entries SET {column_name} = %s WHERE id = %s"
                success = execute_update(query, (new_value, entry_id))
                if success:
                    messagebox.showinfo("Success", f"Entry {entry_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update entry {entry_id}.")

        # Additional logic for specific trees (if needed)
        if self.tree == results_tree and column_index == 3:  # Success count
            query = "UPDATE tradeskill_recipe_entries SET successcount = %s WHERE id = %s"
            success = execute_update(query, (new_value, entry_id))
            if success:
                messagebox.showinfo("Success", f"Success count for entry {entry_id} updated successfully.")
            else:
                messagebox.showerror("Error", f"Failed to update success count for entry {entry_id}.")

        if self.tree == containers_tree and column_index == 1:  # Container ID
            query = "UPDATE tradeskill_recipe_entries SET item_id = %s WHERE id = %s"
            success = execute_update(query, (new_value, entry_id))
            if success:
                messagebox.showinfo("Success", f"Container for entry {entry_id} updated successfully.")
                # Update the container name in the tree
                container_name = get_container_name(new_value)
                new_values = list(values)
                new_values[2] = container_name
                self.tree.item(item_id, values=new_values)
            else:
                messagebox.showerror("Error", f"Failed to update container for entry {entry_id}.")

# Define the root window
root = tk.Tk()
root.title("Tradeskill Manager")
root.geometry("1400x800")
style = theme.set_dark_theme(root)

comp_itemid_var = tk.StringVar()
contain_itemid_var = tk.StringVar()
result_itemid_var = tk.StringVar()

##Begin Top Frame
top_root = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
top_root.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Search Frame
search_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
search_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

# Tradeskill search by dropdown

ttk.Label(search_frame, text="List Recipes By\n   Tradeskill").grid(row=0, column=0)

tradeskill_var = tk.StringVar()
tradeskill_dropdown = ttk.Combobox(search_frame, textvariable=tradeskill_var, state="readonly")
tradeskill_dropdown["values"] = ["Select a Tradeskill"] + list(TRADESKILL_IDS.values())
tradeskill_dropdown.current(0)
tradeskill_dropdown.grid(row=2, column=0, sticky="w", padx=5, pady=5)
tradeskill_dropdown.bind("<<ComboboxSelected>>", load_recipes)


find_byitem_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
find_byitem_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

ttk.Label(find_byitem_frame, text="Search Recipe\n    by Item:").grid(row=0, column=0)
ttk.Button(find_byitem_frame, text="Search by Item ID", command=open_item_search).grid(row=2, column=0, padx=5, pady=5)

lookup_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
lookup_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

ttk.Label(lookup_frame, text=" Search Recipe by\nName or Recipe ID:").grid(row=0, column=0)
search_var = tk.StringVar()
search_entry = ttk.Entry(lookup_frame, textvariable=search_var)
search_entry.grid(row=1, column=0, sticky="w")
search_button = ttk.Button(lookup_frame, text="Search", command=search_recipes)
search_button.grid(row=2, column=0, padx=5, pady=5)

#create new recipe frame

create_recipe_frame = ttk.Frame(top_root, relief=tk.SUNKEN, borderwidth=2)
create_recipe_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

ttk.Label(create_recipe_frame, text="New Recipe").grid(row=0, column=0)
ttk.Button(create_recipe_frame, text="Create", command=create_new_recipe).grid(row=1, column=0, padx=5, pady=18)

###BEGIN MIDDLE ROOT FRAME###

middle_root_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
middle_root_frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")

# Recipe Treeview Frame

recipe_view_frame = ttk.Frame(middle_root_frame, relief=tk.SUNKEN, borderwidth=2)
recipe_view_frame.grid(row=0, column=0, sticky="w", pady=5, padx=5)

recipe_tree = ttk.Treeview(recipe_view_frame, columns=("\nID", "\nName", "  Skill\nNeeded", "\nTrivial", " No\nFail", " Replace\nContainer", "\nNotes", "Must\nLearn", "Learned by\n  Item ID", "\nQuest", "\nEnabled?", "Min\nXpac", "Max\nXpac"), show="headings")
for col in ("\nID", "\nName", "  Skill\nNeeded", "\nTrivial", " No\nFail", " Replace\nContainer", "\nNotes", "Must\nLearn", "Learned by\n  Item ID", "\nQuest", "\nEnabled?", "Min\nXpac", "Max\nXpac"):
    recipe_tree.heading(col, text=col)
    recipe_tree.column(col, width=80, stretch=True, anchor="center")
recipe_tree.grid(row=1, column=0, columnspan=3, sticky="w")
recipe_tree.bind("<<TreeviewSelect>>", load_recipe_entries)

recipe_tree.column("\nID", width=45, stretch=False)
recipe_tree.column("\nName", width=150, stretch=True)
recipe_tree.column("  Skill\nNeeded", width=55, stretch=False)
recipe_tree.column("\nTrivial", width=45, stretch=False)
recipe_tree.column(" No\nFail", width=35, stretch=False)
recipe_tree.column(" Replace\nContainer", width=60, stretch=False)
recipe_tree.column("\nNotes", width=120, stretch=False)
recipe_tree.column("Must\nLearn", width=50, stretch=False)
recipe_tree.column("Learned by\n  Item ID", width=70, stretch=False)
recipe_tree.column("\nQuest", width=40, stretch=False)
recipe_tree.column("\nEnabled?", width=60, stretch=False)
recipe_tree.column("Min\nXpac", width=40, stretch=False)
recipe_tree.column("Max\nXpac", width=40, stretch=False)

###BEGIN BOTTOM ROOT FRAME###
bottom_root_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
bottom_root_frame.grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Components Frame
components_frame = ttk.Frame(bottom_root_frame, relief=tk.SUNKEN, borderwidth=2)
components_frame.grid(row=0, column=0, sticky="w", padx=5, pady=5)

# Components Header
ttk.Button(components_frame, text="Delete Selected", command=delete_selected_comp).grid(row=0, column=1, padx=2, pady=2)
ttk.Button(components_frame, text="Add Random", command=add_random_comp).grid(row=1, column=1, padx=2, pady=2)
ttk.Button(components_frame, text="Add Item by ID:", command=add_specific_comp).grid(row=0, column=2, padx=2, pady=1)
comp_itemid = ttk.Entry(components_frame, textvariable=comp_itemid_var).grid(row=1, column=2)
ttk.Label(components_frame, text="Components", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)

# Treeview
components_tree = ttk.Treeview(components_frame, columns=("Entry\n  ID", "Item\n ID", "\nItem Name", "Component\n   Count", "  Fail\nCount", "Salvage\n Count"), show="headings")
for col in ("Entry\n  ID", "Item\n ID", "\nItem Name", "Component\n   Count", "  Fail\nCount", "Salvage\n Count"):
    components_tree.heading(col, text=col)
    components_tree.column(col, width=100, stretch=True, anchor="center")
components_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=4)

# Set column widths and stretch behavior
components_tree.column("Entry\n  ID", width=50, stretch=False)
components_tree.column("Item\n ID", width=55, stretch=False)
components_tree.column("\nItem Name", width=150, stretch=False)
components_tree.column("Component\n   Count", width=70, stretch=False)
components_tree.column("  Fail\nCount", width=55, stretch=False)
components_tree.column("Salvage\n Count", width=60, stretch=False)

# Recipe Entries Frame (container)
containers_frame = ttk.Frame(bottom_root_frame, relief=tk.SUNKEN, borderwidth=2)
containers_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)

# Containers Header
ttk.Button(containers_frame, text="Delete Selected", command=delete_selected_comp).grid(row=0, column=1, padx=2, pady=2)
ttk.Button(containers_frame, text="Add Random", command=add_random_comp).grid(row=1, column=1, padx=2, pady=2)
ttk.Button(containers_frame, text="Add Container by ID:", command=add_specific_container).grid(row=0, column=2, padx=2, pady=1)
contain_itemid = ttk.Entry(containers_frame, textvariable=contain_itemid_var).grid(row=1, column=2)
ttk.Label(containers_frame, text="Containers", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)

# Containers Treeview
containers_tree = ttk.Treeview(containers_frame, columns=("Entry\n  ID", "Container\n     ID", "Container\n  Name"), show="headings")
for col in ("Entry\n  ID", "Container\n     ID", "Container\n  Name"):
    containers_tree.heading(col, text=col)
    containers_tree.column(col, width=100, stretch=True, anchor="center")
containers_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)

containers_tree.column("Entry\n  ID", width=50, stretch=False)
containers_tree.column("Container\n     ID", width=60, stretch=False)
containers_tree.column("Container\n  Name", width=150, stretch=False)

# Recipe Entries Frame (container)
results_frame = ttk.Frame(bottom_root_frame, relief=tk.SUNKEN, borderwidth=2)
results_frame.grid(row=0, column=2, sticky="w", padx=5, pady=5)

# Results Header
ttk.Button(results_frame, text="Delete Selected", command=delete_selected_comp).grid(row=0, column=1, padx=2, pady=2)
ttk.Button(results_frame, text="Add Random", command=add_random_comp).grid(row=1, column=1, padx=2, pady=2)
ttk.Button(results_frame, text="Add Item by ID:", command=add_specific_result).grid(row=0, column=2, padx=2, pady=1)
result_itemid = ttk.Entry(results_frame, textvariable=result_itemid_var).grid(row=1, column=2)
ttk.Label(results_frame, text="Results", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)

# Results Treeview
results_tree = ttk.Treeview(results_frame, columns=("Entry\n  ID", "Item\n ID", " Item\nName", "Success\n  Count"), show="headings")
for col in ("Entry\n  ID", "Item\n ID", " Item\nName", "Success\n  Count"):
    results_tree.heading(col, text=col)
    results_tree.column(col, width=100, stretch=True, anchor="center")
results_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)

results_tree.column("Entry\n  ID", width=50, stretch=False)
results_tree.column("Item\n ID", width=50, stretch=False)
results_tree.column(" Item\nName", width=150, stretch=False)
results_tree.column("Success\n  Count", width=60, stretch=False)

## End of relevant code

# Add edit functionality to treeviews
recipe_editor = TreeviewEdit(
    recipe_tree, 
    editable_columns=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # All columns
)

components_editor = TreeviewEdit(
    components_tree, 
    editable_columns=[0, 1, 3, 4, 5]  # Component Count, Fail Count, Salvage Count
)

containers_editor = TreeviewEdit(
    containers_tree, 
    editable_columns=[0, 1]  # Container ID
)

results_editor = TreeviewEdit(
    results_tree, 
    editable_columns=[0, 1, 3]  # Success Count
)

# Add edit instructions label
edit_label = ttk.Label(root, text="Double-click most cells to edit. Press Enter to save.", font=("Arial", 10, "italic"))
edit_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

# Function to close the database connection on exit
def on_closing():
    if db:
        db.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
if __name__ == "__main__":
    root.mainloop()