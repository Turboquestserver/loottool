# loottool
Loot editing tool for EQEmu

This is a pretty basic looking loot editor that was inspired by Georgess loot edit tool.  

I just got sick of it slowly losing functionality and decided to replicate it in python and with the help of LLMs.

You can search by Zone (shortname), NPC Name (or partial), or Loot Table and it will display a NPC tree in the bottom frame.  Select an NPC and it will show you the loot information.

All the trees are editable, so you can make NPC edits as well as loot table, and loot drop edits.

Item Lookup utility allows you to look an item up by ID and it will show you any loot table ID & Name, any Lootdrop ID & Name, as well as all the NPCs that have that Loot Table assigned to them.

Unused IDs button shows first 10 unused Loot Table & Loot Drop IDs.  If you use the "Create new Loot Table..." button it will consume the lowest table ID and drop ID to create your new table (Item 1001 placeholder).

Add specific item allows you to add your own item to the loot drop.  Add random will select a random item from your items database and add it to the current loot drop.

Most of these functions have been tested, however I would advice making a backup prior to using the editing tool, as there are a lot of editable columns and I haven't tested every single one.

I will be adding more features, and am accepting suggestions.
