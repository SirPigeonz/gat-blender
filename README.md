# Game Art Toolbag (GAT) for Blender

Some usefull scripts for Blender. Will be updated to full Addon in the future.

## Current features (early ALPHA stage):
1. Animation Transfer ("Binding" skeletons)
	* Bones with same name can inherit transformations
	* Ability to map root bone of one armature to origin of of other aramture (removes extra root bone from export)
1. Simple manager of all available Actions
	* Actions can be marked for Recording (Baking) and Export
	* Basic renaming in clean list view
1. Automatic pushing of actions marked as "Exported" to NLA stack
	* Automates creation of NLA Tracks
	* Automates overwriting generated NLA Tracks
1. "Simple Animation Test" operator
	* Create simple rotation animation for selected bone
	* Use it to test your weight painting while working on it
1. "Clear Bone Locks" operator
	* Clears all bone transformations locks for selected bones
