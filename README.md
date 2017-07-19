## GAT-blender

Some usefull scripts for Blender. Will be updated to full Addon in the future.

# Current features (early ALPHA stage):
* Binding skeletons
	* Bones with same name can inherit transformations
	* Ability to map root bone of one armature to origin of of other aramture (removes extra root bone from export)
* Simple manager of all available Actions
	* Actions can be marked for Recording (Bakeing) and Export
	* Basic renaming in clean list view
* Automatic pushing of actions marked as "Exported" to NLA stack
	* Automates creation of NLA Tracks
	* Automates overwriting generated NLA Tracks