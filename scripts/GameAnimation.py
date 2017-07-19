import pdb
import bpy
from bpy.app.handlers import persistent
from bpy.props import IntProperty, FloatProperty

# ====================== FUNCTIONS ======================

def _get_puppet(context):
  return context.scene.puppet_armature

def _get_performer(context):
    return context.scene.performer_armature

def _is_exported_action(action_name):
    for prop in bpy.context.scene.exported_actions:
        if prop.action_name == action_name:
            return True
    return False

def _add_action_to_exported(action_name):
    if not _is_exported_action(action_name):
        item = bpy.context.scene.exported_actions.add()
        item.action_name = action_name

def _remove_action_from_exported(action_name):
    if _is_exported_action(action_name):
        index = 0
        for prop in bpy.context.scene.exported_actions:
            if prop.action_name == action_name:
                bpy.context.scene.exported_actions.remove(index)
                return True
            else:
                index += 1
    return False


# ====================== PROPERTIES ======================

# Each Action will store special flags to decide if it will be exported.
class ExportedActions(bpy.types.PropertyGroup):
    action_name = bpy.props.StringProperty()

class GATSettings(bpy.types.PropertyGroup):
    use_root_retarget = bpy.props.BoolProperty(name = "Use root retargeting", description = "Retarget performer root bone to puppet object itself (used to eliminate additional root bone in some engines)", default = False)


# ====================== OPERATORS ======================

# WEIGHT PAINTING

class SimpleTestAnimation(bpy.types.Operator):
    """Creates simple animations for weight painting testing purposes"""
    bl_idname = "anim.simple_test_animation"
    bl_label = "Simple Test Animation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        ba = bpy.data.actions.new("TestAnimation")
        context.active_object.animation_data_create()
        context.active_object.animation_data.action = ba

        frame = 1
        context.scene.frame_set(frame)
        #TODO add support for objects...
        #bpy.ops.object.rotation_clear()
        bpy.ops.pose.rot_clear()
        bpy.ops.anim.keyframe_insert_menu()

        frame = self.animate(context, frame, [True, False, False])
        frame = self.animate(context, frame, [False, False, True])
        frame = self.animate(context, frame, [False, True, False])

        return {'FINISHED'}

    def animate(self, context, frame, axis = [False, False, False]):
        for i in [1, -1]:
            print(i)
            frame += 10
            context.scene.frame_set(frame)
            bpy.ops.transform.rotate(value = (i * 45), constraint_axis = axis, constraint_orientation = 'LOCAL')
            bpy.ops.anim.keyframe_insert_menu()

            frame += 10
            context.scene.frame_set(frame)
            #bpy.ops.object.rotation_clear()
            bpy.ops.pose.rot_clear()
            bpy.ops.anim.keyframe_insert_menu()
            print("It ends?")
        return frame


class ModalOperator(bpy.types.Operator):
    """Move an object with the mouse, example"""
    bl_idname = "object.modal_operator"
    bl_label = "Simple Modal Operator"

    first_mouse_x = IntProperty()
    first_value = FloatProperty()

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            context.object.location.x = self.first_value - delta * 0.01 / context.scene.unit_settings.scale_length

        elif event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.object.location.x = self.first_value
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object:
            self.first_mouse_x = event.mouse_x
            self.first_value = context.object.location.x

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


# RETARGETING

class CreateBakedAction(bpy.types.Operator):
    """Creates Actions based on the ones marked for export with baked frames in specified frame range"""
    bl_idname = "anim.create_baked_actions"
    bl_label = "Create Baked Actions"

    action_name = bpy.props.StringProperty()
    frame_range = bpy.props.FloatVectorProperty(name = "frame_range", size = 2)

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        actions = bpy.data.actions

        #TODO make overwriting optional for now hardcoded
        if actions.find(self.action_name + "_Exp") != -1:
            actions.remove(actions[self.action_name + "_Exp"])
        # Create Empty Baked Action
        ba = actions.new(self.action_name + "_Exp")
        context.active_object.animation_data.action = ba

        # Bake Armature
        bpy.ops.object.mode_set(mode='OBJECT')
        self.bake(context)

        # Bake Bones
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        self.bake(context)

        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

    def bake(self, context):
        # TODO add ability to specify number of cuted out frames.
        for f in range(int(self.frame_range[0]), int(self.frame_range[1]) + 1, 1):
            context.scene.frame_set(f)
            bpy.ops.anim.keyframe_insert_menu()

        # Ensure all keyframes are selected...
        obj = bpy.context.object
        action = obj.animation_data.action
        for fcurve in action.fcurves :
            for p in fcurve.keyframe_points :
                p.select_control_point

        for area in bpy.context.screen.areas:
            if area.type == 'DOPESHEET_EDITOR':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.action.snap(override, type='NEAREST_FRAME')
                bpy.ops.action.interpolation_type(override, type='LINEAR')
                #bpy.ops.action.keyframe_type(type='JITTER')
                break


class SyncActionsStrips(bpy.types.Operator):
    """Removes Auto generated tracks (AutoGen) and pushes exported actions to NLA tracks"""
    bl_idname = "anim.sync_actions_strips"
    bl_label = "Sync Actions in NLA"

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        puppet = _get_puppet(context)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[puppet.name].select = True
        context.scene.objects.active = puppet
        print("HERE ================================= "+ str(context.scene.objects.active))

        # Delete AutGen nla_tracks
        for track in puppet.animation_data.nla_tracks:
            if track.name == "AutoGen":
                puppet.animation_data.nla_tracks.remove(track)

        for action in bpy.data.actions:
            if action.name[-4:] == "_Exp":
                context.active_object.animation_data.action = action
                for area in bpy.context.screen.areas:
                    if area.type == 'NLA_EDITOR':
                        override = bpy.context.copy()
                        override['area'] = area
                        bpy.ops.nla.action_pushdown(override, channel_index=1)
                        break
                tracks = puppet.animation_data.nla_tracks
                keys = puppet.animation_data.nla_tracks.keys()
                tracks[keys[-1]].name = "AutoGen"

        return {'FINISHED'}



class RecordExportedActions(bpy.types.Operator):
    """Create, bake and assign to Puppet NLA stash all actions marked for export."""
    bl_idname = "anim.record_exported_actions"
    bl_label = "Record Actions for Export"

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        puppet = _get_puppet(context)
        performer = _get_performer(context)

        #TODO Fix context polling and make this one into function same line are in NLA sync...
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[puppet.name].select = True
        context.scene.objects.active = puppet
        print("HERE ================================= "+ str(context.scene.objects.active))

        self.record(context, performer)

        return {'FINISHED'}

    def record(self, context, performer):
        for action in bpy.data.actions:
            if _is_exported_action(action.name):
                # Set Source Action on Performer for Bake
                performer.animation_data.action = action
                # Bake
                bpy.ops.anim.create_baked_actions(action_name = action.name, frame_range = action.frame_range)


class ExportAction(bpy.types.Operator):
    """Mark action for export"""
    bl_idname = "scene.export_action"
    bl_label = "Mark Action for Export"

    action_name = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        _add_action_to_exported(self.action_name)
        return {'FINISHED'}


class UnexportAction(bpy.types.Operator):
    """Unmark action for export"""
    bl_idname = "scene.unexport_action"
    bl_label = "Mark Action for Export"

    action_name = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        print("works...")
        _remove_action_from_exported(self.action_name)
        return {'FINISHED'}


class PushExportAction(bpy.types.Operator):
    """Exported action, will be pushed to NLA track as a animation strip"""
    bl_idname = "scene.push_export_action"
    bl_label = "Push Exported Action"

    @classmethod
    def poll(cls, context):
        #TODO
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}


class ToggleBindArmatures(bpy.types.Operator):
    """Bind transformations of bones with same name from Performer to Puppet"""
    bl_idname = "object.toggle_bind_armatures"
    bl_label = "Bind Armatures"

    invert = bpy.props.BoolProperty(default = False)
    root_target = bpy.props.StringProperty(default = "")

    @classmethod
    def poll(cls, context):
        #return context.active_object is not None
        return context.scene.performer_armature is not None \
        and context.scene.puppet_armature is not None

    def execute(self, context):
        if context.scene.gat_settings.use_root_retarget == False:
            context.scene.performers_root = ""
        if not self.invert:
            self.bind(context)
        else:
            self.unbind(context)
        return {'FINISHED'}

    def bind(self, context):
        """Add "Copy Transform" constraint to "puppet" armature bones
        with "performer" armature as constraints target."""

        performer = context.scene.performer_armature
        puppet = context.scene.puppet_armature

        for bone in puppet.pose.bones:
            if performer.pose.bones.find(bone.name) != -1:
                con = bone.constraints.new('COPY_TRANSFORMS')
                con.name = "GAT_CopyTransforms"
                con.owner_space = "WORLD" #formely POSE WORLD
                con.target = performer
                con.subtarget = bone.name
            else:
                print("Bone " + bone.name + " can't match bone in performer armature.")

        if self.root_target != "":
            con = puppet.constraints.new('COPY_TRANSFORMS')
            con.name = "GAT_CopyTransforms"
            con.target = performer
            con.subtarget = self.root_target

        bpy.context.scene.armatures_bound = True
        self.invert = True

    def unbind(self, context):
        """Remove "Copy Transform" constraint from "puppet" armature bones
        that are part of GAT (based on constraints name)"""

        puppet = context.scene.puppet_armature
        print("WHAT THE HELL!!!")
        for bone in puppet.pose.bones:
            for con in bone.constraints:
                if con.name[0:3] == "GAT":
                    bone.constraints.data.constraints.remove(con)
        for con in puppet.constraints:
            if con.name[0:3] == "GAT":
                puppet.constraints.data.constraints.remove(con)
        bpy.context.scene.armatures_bound = False
        self.invert = False


# ====================== PANELS ======================

class GATPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Animation"

class GameAnimationToolboxPanel(GATPanel, bpy.types.Panel):
    """Set of tools for Animator working with Games and Real Time."""
    bl_label = "Games Animation Toolbox (GAT)"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        performer = scene.performer_armature

        # Set Performer and Puppet armatures
        split = layout.split()
        col = split.column(align = True)
        col.label("Bind Armatures:")
        row = col.row(align = True)
        row.prop(scene, "performer_armature", "Performer")
        if context.scene.armatures_bound:
            row.label("", icon = 'LINKED')
        else:
            row.label("", icon = 'UNLINKED')
        row = col.row(align = True)
        row.prop(scene, "puppet_armature", "Puppet")
        if context.scene.armatures_bound:
            row.label("", icon = 'LINKED')
        else:
            row.label("", icon = 'UNLINKED')

        layout.separator()

        # Root retargeting
        col = layout.split().column(align = False)
        col.prop(scene.gat_settings, "use_root_retarget")
        col2 = col.split().column(align = False)
        if scene.gat_settings.use_root_retarget == True:
            col2.enabled = True
        else:
            col2.enabled = False
            #TODO add and call operator that will empty performer root when not used
        if performer:
            col2.prop_search(scene, "performers_root", performer.data, "bones", text = "Performers Root")

        layout.separator()

        # Bind Armatures Button
        col = layout.split().column()
        col.scale_y = 1.2
        if not bpy.context.scene.armatures_bound:
            op = col.operator("object.toggle_bind_armatures", "Bind Armatures", icon = 'POSE_HLT')
            op.root_target = scene.performers_root
        else:
            col.operator("object.toggle_bind_armatures", "Unbind Armatures", icon = 'ARMATURE_DATA')

        layout.separator()

        # Actions Management
        col = layout.split().column(align = True)
        row = col.row(align = True)
        row.label("Manage actions export:")
        #TODO Not sure if it will work ok if actions = []
        for action in bpy.data.actions:
            row = col.row(align = True)
            row2 = row.row(align = True)
            row2.scale_x = 1.4
            if _is_exported_action(action.name):
                op = row2.operator("scene.unexport_action", "", icon = "FILE_TICK")
                op.action_name = action.name
            elif action.name[-4:] == "_Exp" or action.name[-8:-4] == "_Exp":
                row2.operator("scene.unexport_action", "", icon = "NLA_PUSHDOWN", emboss = False)
            else:
                op = row2.operator("scene.export_action", "", icon = "DOT")
                op.action_name = action.name
            row.prop(action, "name", "", emboss = True)

        col = layout.split().column()
        col.scale_y = 1.2
        col.operator("anim.record_exported_actions", icon = 'REC')
        col.operator("anim.sync_actions_strips", "Push / Sync Exported to NLA" , icon = 'NLA')


# ====================== REGISTER ======================

def register():
    bpy.utils.register_class(SimpleTestAnimation)
    bpy.utils.register_class(ModalOperator)

    bpy.utils.register_class(CreateBakedAction)
    bpy.utils.register_class(SyncActionsStrips)
    bpy.utils.register_class(RecordExportedActions)
    bpy.utils.register_class(ToggleBindArmatures)
    bpy.utils.register_class(GameAnimationToolboxPanel)

    bpy.utils.register_class(GATSettings)
    bpy.types.Scene.gat_settings = bpy.props.PointerProperty(type = GATSettings)
    bpy.utils.register_class(ExportedActions)
    bpy.types.Scene.exported_actions = bpy.props.CollectionProperty(type = ExportedActions)
    bpy.types.Scene.performer_armature = bpy.props.PointerProperty(type = bpy.types.Object)
    bpy.types.Scene.puppet_armature = bpy.props.PointerProperty(type = bpy.types.Object)
    bpy.types.Scene.armatures_bound = bpy.props.BoolProperty(default = False)
    bpy.types.Scene.performers_root = bpy.props.StringProperty()

    bpy.utils.register_class(ExportAction)
    bpy.utils.register_class(UnexportAction)
    bpy.utils.register_class(PushExportAction)


def unregister():
    bpy.utils.unregister_class(ExportAction)
    bpy.utils.unregister_class(UnexportAction)
    bpy.utils.unregister_class(PushExportAction)

    del bpy.types.Scene.performers_root
    del bpy.types.Scene.armatures_bound
    del bpy.types.Scene.puppet_armature
    del bpy.types.Scene.performer_armature
    del bpy.types.Scene.exported_actions
    bpy.utils.unregister_class(ExportedActions)
    del bpy.types.Scene.gat_settings
    bpy.utils.unregister_class(GATSettings)

    bpy.utils.unregister_class(GameAnimationToolboxPanel)
    bpy.utils.unregister_class(ToggleBindArmatures)
    bpy.utils.unregister_class(RecordExportedActions)
    bpy.utils.unregister_class(SyncActionsStrips)
    bpy.utils.unregister_class(CreateBakedAction)

    bpy.utils.unregister_class(ModalOperator)
    bpy.utils.unregister_class(SimpleTestAnimation)


if __name__ == "__main__":
    register()

    # TEST CALL
