# Game Art Toolbag (GAT) for Blender

Some useful scripts for Blender. Will be updated to full Add-on in the future.

## Current features (early ALPHA stage):
1. Animation Transfer ("Binding" skeletons)
	* Set of tools to help separating rigs designed mainly for animation from the ones designed for real time and in-engine use.
	* Bones with matching name can inherit transformations
	* Ability to map root bone of one armature to origin of another armature (removes extra root bone from export)
1. Simple manager of all available Actions
	* Simplifies and speedups managing and exporting huge sets of actions
	* Actions can be marked for Recording (Baking) and Export
	* Basic renaming in clean list view
1. Automatic pushing of actions marked as "Exported" to NLA stack
	* Automates creation of NLA Tracks for exporting chosen animations
	* Automates updating exported NLA Tracks
1. "Simple Animation Test" operator
	* Create simple rotation animation for selected bone
	* Use it to test your weight painting while working on it
1. "Clear Bone Locks" operator
	* Clears all bone transformations locks for selected bones
