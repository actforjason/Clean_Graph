import bpy
import bpy.utils.previews
from bpy_extras import anim_utils

class SmartFilter_PT_Panel(bpy.types.Panel):
    bl_label = "Focus FCurves"
    bl_idname = "OBJECT_PT_focus_fcurves"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    bl_order = 8

    @classmethod
    def poll(cls, context):
        return getattr(context.scene, 'show_panels', [False]*8)[7]

    def draw(self, context):
        scene = context.scene
   
        layout = self.layout

        
        focus_box = layout.box()
        focus_box.label(text="Focus FCurves", icon='CURVE_DATA')

        
        component_box = focus_box.box()
        component_box.label(text="Select Components:")
        row = component_box.row(align=True)
        row.prop(context.scene, "fc_keep_w", text="W")
        row.prop(context.scene, "fc_keep_x", text="X")
        row.prop(context.scene, "fc_keep_y", text="Y")
        row.prop(context.scene, "fc_keep_z", text="Z")

        
        channel_box = focus_box.box()
        channel_box.label(text="Select Channels:")
        row = channel_box.row(align=True)
        row.prop(context.scene, "fc_keep_location", text="Location")
        row.prop(context.scene, "fc_keep_rotation", text="Rotation")
        row.prop(context.scene, "fc_keep_scale", text="Scale")

        
        operator_box = layout.box()
        operator_box.label(text="Focus On", icon_value=418)
        operator_box.operator("graph.focus_fcurves", text="Focus FCurves", icon_value=254)

        
        delete_box = layout.box()
        delete_box.label(text="Delete", icon='X')
        row = delete_box.row(align=False)
        row.operator("graph.delete_fcurves", text="Delete FCurves", icon='X')
        row.operator("graph.delete_selected_bone_channels", text="Delete Channel", icon='X')

        
        save_apply_box = layout.box()
        save_apply_box.label(text="choose/connect ", icon='FILE_TICK')
        save_apply_box.operator("object.save_fcurves", text="Choose FCurves", icon='FILE_NEW')
        save_apply_box.operator("object.apply_fcurves", text="connect FCurves", icon='FILE_TICK')


class FocusFCurvesOperator(bpy.types.Operator):
    bl_idname = "graph.focus_fcurves"
    bl_label = "Focus F-Curves"
    bl_description = "Choose fcurves in the frame range to show them and hide the others"
    def should_keep(self, scene, data_path, index):
        if 'location' in data_path:
            if scene.fc_keep_location:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_euler' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_quaternion' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_w and index == 0:
                    return True
                if scene.fc_keep_x and index == 1:
                    return True
                if scene.fc_keep_y and index == 2:
                    return True
                if scene.fc_keep_z and index == 3:
                    return True
        if 'scale' in data_path:
            if scene.fc_keep_scale:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        return False

    def execute(self, context):
        scene = context.scene
        
        bpy.ops.graph.reveal()

        bpy.ops.graph.select_all(action='DESELECT')

        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    fcurve.hide = not self.should_keep(scene, fcurve.data_path, fcurve.array_index)

        
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end

        for obj in bpy.context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        if start_frame <= keyframe.co[0] <= end_frame:
                            keyframe.select_control_point = True

        
        active_obj = bpy.context.active_object
        if active_obj and active_obj.animation_data and active_obj.animation_data.action:
            action = active_obj.animation_data.action
            slot = active_obj.animation_data.action_slot
            if not slot:
                slot = action.slots.new(id_type=active_obj.rna_type.identifier, name=active_obj.name + "_slot")
                active_obj.animation_data.action_slot = slot
            channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
            for curve in channelbag.fcurves:
                curve.select = True

        bpy.ops.graph.view_selected()

        return {'FINISHED'}

class DeleteFCurvesOperator(bpy.types.Operator):
  
    bl_idname = "graph.delete_fcurves"
    bl_label = "Delete FCurves"
    bl_description = "Delete all keyframes from choosing Fcurves in the frame range"
    def should_keep(self, scene, data_path, index):
        if 'location' in data_path:
            if scene.fc_keep_location:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_euler' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_quaternion' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_w and index == 0:
                    return True
                if scene.fc_keep_x and index == 1:
                    return True
                if scene.fc_keep_y and index == 2:
                    return True
                if scene.fc_keep_z and index == 3:
                    return True
        if 'scale' in data_path:
            if scene.fc_keep_scale:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        return False

    def execute(self, context):
        scene = context.scene
        
        bpy.ops.graph.reveal()

        bpy.ops.graph.select_all(action='DESELECT')

        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    fcurve.hide = not self.should_keep(scene, fcurve.data_path, fcurve.array_index)

        
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end

        for obj in bpy.context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        if start_frame <= keyframe.co[0] <= end_frame:
                            keyframe.select_control_point = True

        
        active_obj = bpy.context.active_object
        if active_obj and active_obj.animation_data and active_obj.animation_data.action:
            action = active_obj.animation_data.action
            slot = active_obj.animation_data.action_slot
            if not slot:
                slot = action.slots.new(id_type=active_obj.rna_type.identifier, name=active_obj.name + "_slot")
                active_obj.animation_data.action_slot = slot
            channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
            for curve in channelbag.fcurves:
                curve.select = True

        bpy.ops.graph.delete()

        self.report({'INFO'}, "FCurves deleted successfully.")
        return {'FINISHED'}


def get_frame(self):
    return bpy.context.scene.frame_current

def set_frame(self, value):
    bpy.context.scene.frame_current = value

bpy.types.Scene.frame_slider = bpy.props.IntProperty(
    name="",
    description="Move the current frame",
    default=0,
    min=0,
    max=1000,  
    get=get_frame,
    set=set_frame
)


def frame_change_handler(scene):
    scene.frame_slider = scene.frame_current


bpy.app.handlers.frame_change_pre.append(frame_change_handler)


class GRAPH_OT_SetFrame(bpy.types.Operator):
    bl_idname = "graph.set_frame"
    bl_label = "Set Current Frame"
    
    def execute(self, context):
        return {'FINISHED'}


def graph_editor_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.prop(context.scene, "frame_slider")

class DeleteChannelOperator(bpy.types.Operator):
    """Delete the channel chosen based on user selection for selected bones"""
    bl_idname = "graph.delete_selected_bone_channels"
    bl_label = "Delete Selected Bone Channels"

    def execute(self, context):
        
        if bpy.context.area.type != 'GRAPH_EDITOR':
            self.report({'ERROR'}, "Please run this operator in the Graph Editor.")
            return {'CANCELLED'}

        
        if context.mode != 'POSE':
            self.report({'ERROR'}, "This operator requires Pose mode on the armature.")
            return {'CANCELLED'}

        
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "No armature selected.")
            return {'CANCELLED'}

        
        if not obj.animation_data or not obj.animation_data.action:
            self.report({'ERROR'}, "No animation data found for the selected armature.")
            return {'CANCELLED'}

        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        if not slot:
            slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
            obj.animation_data.action_slot = slot
        channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)

        
        selected_pose_bones = context.selected_pose_bones
        if not selected_pose_bones:
            self.report({'ERROR'}, "No bones selected.")
            return {'CANCELLED'}
        selected_bones = [pbone.name for pbone in selected_pose_bones]

        
        fcurves = list(channelbag.fcurves)  
        for curve in fcurves:
            data_path = curve.data_path

            
            for bone_name in selected_bones:
                if f'pose.bones["{bone_name}"]' in data_path:
                    index = curve.array_index
                    if 'location' in data_path and context.scene.fc_keep_location:
                        if context.scene.fc_keep_x and index == 0:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_y and index == 1:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_z and index == 2:
                            channelbag.fcurves.remove(curve)
                    elif 'rotation_euler' in data_path and context.scene.fc_keep_rotation:
                        if context.scene.fc_keep_x and index == 0:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_y and index == 1:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_z and index == 2:
                            channelbag.fcurves.remove(curve)
                    elif 'rotation_quaternion' in data_path and context.scene.fc_keep_rotation:
                        if context.scene.fc_keep_w and index == 0:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_x and index == 1:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_y and index == 2:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_z and index == 3:
                            channelbag.fcurves.remove(curve)
                    elif 'scale' in data_path and context.scene.fc_keep_scale:
                        if context.scene.fc_keep_x and index == 0:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_y and index == 1:
                            channelbag.fcurves.remove(curve)
                        if context.scene.fc_keep_z and index == 2:
                            channelbag.fcurves.remove(curve)

        self.report({'INFO'}, "F-Curves deleted for selected bones successfully.")
        return {'FINISHED'}

class SaveFCurvesOperator(bpy.types.Operator):
    """save the chosen fcurve"""
    
    bl_idname = "object.save_fcurves"
    bl_label = "Save F-Curves"
    bl_options = {'REGISTER', 'UNDO'}

    def should_keep(self, scene, data_path, index):
        if 'location' in data_path:
            if scene.fc_keep_location:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_euler' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        if 'rotation_quaternion' in data_path:
            if scene.fc_keep_rotation:
                if scene.fc_keep_w and index == 0:
                    return True
                if scene.fc_keep_x and index == 1:
                    return True
                if scene.fc_keep_y and index == 2:
                    return True
                if scene.fc_keep_z and index == 3:
                    return True
        if 'scale' in data_path:
            if scene.fc_keep_scale:
                if scene.fc_keep_x and index == 0:
                    return True
                if scene.fc_keep_y and index == 1:
                    return True
                if scene.fc_keep_z and index == 2:
                    return True
        return False

    def execute(self, context):
        scene = context.scene
        
        bpy.ops.graph.reveal()
        bpy.ops.graph.select_all(action='DESELECT')

        start_frame = scene.frame_start
        end_frame = scene.frame_end

        
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    if self.should_keep(scene, fcurve.data_path, fcurve.array_index):
                        fcurve.select = True
                        
                        
                        for keyframe in fcurve.keyframe_points:
                            if start_frame <= keyframe.co[0] <= end_frame:
                                keyframe.select_control_point = True

        
        selected_fcurves_exist = False
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if not slot:
                    slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                    obj.animation_data.action_slot = slot
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fcurve in channelbag.fcurves:
                    if fcurve.select:
                        selected_fcurves_exist = True
                        break
                if selected_fcurves_exist:
                    break

        if selected_fcurves_exist:
            bpy.ops.graph.copy()
            self.report({'INFO'}, "Selected F-curves copied to clipboard")
        else:
            self.report({'WARNING'}, "No F-curves selected based on current settings")

        return {'FINISHED'}

class ApplyFCurvesOperator(bpy.types.Operator):
    """Apply the chosen fcurve to the root bone and invert it to create a loop animation in place"""
    
    bl_idname = "object.apply_fcurves"
    bl_label = "Apply F-Curves"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def should_keep(self, scene, data_path, index):
        """Helper function to check if the fcurve should be kept based on user settings."""
        if 'location' in data_path:
            return (scene.fc_keep_location and 
                    ((scene.fc_keep_x and index == 0) or 
                     (scene.fc_keep_y and index == 1) or 
                     (scene.fc_keep_z and index == 2)))
        elif 'rotation_euler' in data_path:
            return (scene.fc_keep_rotation and 
                    ((scene.fc_keep_x and index == 0) or 
                     (scene.fc_keep_y and index == 1) or 
                     (scene.fc_keep_z and index == 2)))
        elif 'rotation_quaternion' in data_path:
            return (scene.fc_keep_rotation and 
                    ((scene.fc_keep_w and index == 0) or 
                     (scene.fc_keep_x and index == 1) or 
                     (scene.fc_keep_y and index == 2) or 
                     (scene.fc_keep_z and index == 3)))
        elif 'scale' in data_path:
            return (scene.fc_keep_scale and 
                    ((scene.fc_keep_x and index == 0) or 
                     (scene.fc_keep_y and index == 1) or 
                     (scene.fc_keep_z and index == 2)))
        return False

    def delete_empty_channels(self, bone):
        """Deletes F-Curves on the given bone with no keyframes."""
        if bone is None:
            return
        action = bone.id_data.animation_data.action
        if action is None:
            return
        
        slot = bone.id_data.animation_data.action_slot
        if not slot:
            slot = action.slots.new(id_type=bone.id_data.rna_type.identifier, name=bone.id_data.name + "_slot")
            bone.id_data.animation_data.action_slot = slot
        channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
        
        
        fcurves_to_remove = []
        for fcurve in channelbag.fcurves:
            if fcurve.select and not fcurve.keyframe_points:
                fcurves_to_remove.append(fcurve)
        
        for fcurve in fcurves_to_remove:
            channelbag.fcurves.remove(fcurve)
        
        if fcurves_to_remove:
            print(f"Deleted {len(fcurves_to_remove)} empty channels from bone: {bone.name}")

    def delete_constant_fcurves(self, obj):
        """Deletes F-Curves on the given object with all keyframes having the same value."""
        if obj is None or not obj.animation_data or not obj.animation_data.action:
            return
        
        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        if not slot:
            slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
            obj.animation_data.action_slot = slot
        channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
        
        fcurves_to_remove = []
        
        for fcurve in channelbag.fcurves:
            if not fcurve.select:  
                continue
                
            keyframes = fcurve.keyframe_points
            if not keyframes:
                fcurves_to_remove.append(fcurve)
                continue
                
            first_value = keyframes[0].co.y
            if all(keyframe.co.y == first_value for keyframe in keyframes[1:]):
                fcurves_to_remove.append(fcurve)
        
        for fcurve in fcurves_to_remove:
            channelbag.fcurves.remove(fcurve)
        
        if fcurves_to_remove:
            print(f"Deleted {len(fcurves_to_remove)} constant-value F-Curves from object: {obj.name}")

    def shift_keyframes_to_zero(self, fcurves):
        """Adjust selected keyframes to make the first keyframe value zero."""
        for fcurve in fcurves:
            if fcurve.select:  
                keyframe_points = fcurve.keyframe_points
                if keyframe_points:
                    first_value = keyframe_points[0].co[1]
                    for keyframe in keyframe_points:
                        keyframe.co[1] -= first_value
                        keyframe.handle_left.y -= first_value
                        keyframe.handle_right.y -= first_value

    def execute(self, context):
        scene = context.scene
        original_area_type = context.area.type
        
        try:
            
            context.area.type = 'GRAPH_EDITOR'
            
            
            bpy.ops.anim.keyframe_insert_by_name(type="LocRotScale")
            bpy.ops.graph.reveal()
            bpy.ops.graph.select_all(action='DESELECT')

            
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    slot = obj.animation_data.action_slot
                    if not slot:
                        slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                        obj.animation_data.action_slot = slot
                    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                    for fcurve in channelbag.fcurves:
                        if self.should_keep(scene, fcurve.data_path, fcurve.array_index):
                            fcurve.select = True
                            
                            
                            start_frame = scene.frame_start
                            end_frame = scene.frame_end
                            for keyframe in fcurve.keyframe_points:
                                if start_frame <= keyframe.co[0] <= end_frame:
                                    keyframe.select_control_point = True

            
            selected_fcurves_exist = False
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    slot = obj.animation_data.action_slot
                    if not slot:
                        slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
                        obj.animation_data.action_slot = slot
                    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                    for fcurve in channelbag.fcurves:
                        if fcurve.select:
                            selected_fcurves_exist = True
                            break
                if selected_fcurves_exist:
                    break

            if not selected_fcurves_exist:
                self.report({'WARNING'}, "No F-curves selected based on current settings")
                return {'CANCELLED'}

            
            bpy.ops.graph.paste()
            
            
            bpy.ops.transform.resize(
                value=(-1, 1, 1),
                orient_type='GLOBAL',
                constraint_axis=(True, False, False),
                mirror=False,
                use_proportional_edit=False,
            )

            
            active_bone = context.active_pose_bone
            self.delete_empty_channels(active_bone)
            
            for obj in context.selected_objects:
                self.delete_constant_fcurves(obj)

            
            selected_fcurves = context.selected_editable_fcurves
            self.shift_keyframes_to_zero(selected_fcurves)

            self.report({'INFO'}, f"Applied operations to selected F-curves")

        except Exception as e:
            self.report({'ERROR'}, f"Error applying F-curves: {str(e)}")
            return {'CANCELLED'}
        finally:
            
            context.area.type = original_area_type

        return {'FINISHED'}
    
classes = (    
    

    FocusFCurvesOperator,
    DeleteFCurvesOperator,
    DeleteChannelOperator,
    SaveFCurvesOperator,
    ApplyFCurvesOperator,    
    SmartFilter_PT_Panel,
)


def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)    
    bpy.types.Scene.fc_keep_w = bpy.props.BoolProperty(name="W", default=False)
    bpy.types.Scene.fc_keep_x = bpy.props.BoolProperty(name="X", default=False)
    bpy.types.Scene.fc_keep_y = bpy.props.BoolProperty(name="Y", default=False)
    bpy.types.Scene.fc_keep_z = bpy.props.BoolProperty(name="Z", default=False)
    bpy.types.Scene.fc_keep_location = bpy.props.BoolProperty(name="Location", default=False)
    bpy.types.Scene.fc_keep_rotation = bpy.props.BoolProperty(name="Rotation", default=False)
    bpy.types.Scene.fc_keep_scale = bpy.props.BoolProperty(name="Scale", default=False)    
    
def unregister():
    
    for cls in classes:
        bpy.utils.unregister_class(cls)    
            
    del bpy.types.Scene.fc_keep_w
    del bpy.types.Scene.fc_keep_x
    del bpy.types.Scene.fc_keep_y
    del bpy.types.Scene.fc_keep_z
    del bpy.types.Scene.fc_keep_location
    del bpy.types.Scene.fc_keep_rotation
    del bpy.types.Scene.fc_keep_scale