


import bpy
from mathutils import Vector
import math
from bpy_extras import anim_utils


class DuplicateKeyframesOperator(bpy.types.Operator):
    """Apply the repeat number"""
    bl_idname = "graph.duplicate_keyframes"
    bl_label = "Duplicate Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.area.type != 'GRAPH_EDITOR':
            self.report({'ERROR'}, "Please run this operator in the Graph Editor.")
            return {'CANCELLED'}

        selected_fcurves = bpy.context.selected_editable_fcurves
        if selected_fcurves:
            duplicate_count = bpy.context.scene.keyframe_duplicate_count

            for fcurve in selected_fcurves:
                selected_keyframes = [kf for kf in fcurve.keyframe_points if kf.select_control_point]

                if len(selected_keyframes) >= 2:
                    start_keyframe = selected_keyframes[0]
                    end_keyframe = selected_keyframes[-1]

                    start_keyframe.handle_left_type = 'VECTOR'
                    start_keyframe.handle_right_type = 'VECTOR'
                  
                    keyframe_distances = []
                    for i in range(len(selected_keyframes) - 1):
                        keyframe_distances.append(selected_keyframes[i + 0].co[0] - selected_keyframes[i].co[0])
                  
                    offset = end_keyframe.co[0] - start_keyframe.co[0] + keyframe_distances[0]
                    for d in range(duplicate_count):
                        new_keyframes = []
                        for i, keyframe in enumerate(selected_keyframes):
                            new_frame = keyframe.co[0] + (d + 1) * offset
                            new_value = keyframe.co[1]  

                            new_keyframe = fcurve.keyframe_points.insert(frame=new_frame, value=new_value)
                            new_keyframe.interpolation = keyframe.interpolation

                            # Copy handle types and positions
                            new_keyframe.handle_left_type = keyframe.handle_left_type
                            new_keyframe.handle_right_type = keyframe.handle_right_type
                            new_keyframe.handle_left = keyframe.handle_left + Vector((new_frame - keyframe.co[0], 0))
                            new_keyframe.handle_right = keyframe.handle_right + Vector((new_frame - keyframe.co[0], 0))

                            new_keyframes.append(new_keyframe)
                            if i < len(keyframe_distances):
                                offset += keyframe_distances[i]

                        if new_keyframes:
                            new_keyframes[0].handle_left_type = 'VECTOR'
                            new_keyframes[0].handle_right_type = 'VECTOR'
                            new_keyframes[-1].handle_left_type = 'VECTOR'
                            new_keyframes[-1].handle_right_type = 'VECTOR'

            # Update the F-Curves
            for fcurve in selected_fcurves:
                fcurve.update()

            self.report({'INFO'}, "Keyframes duplicated and moved successfully.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No F-Curves selected.")
            return {'CANCELLED'}


class MatchToRepeatOperator(bpy.types.Operator):
    """Match keyframes that are in the start and end frame ranges and setup the handle"""
    bl_idname = "graph.match_to_repeat"
    bl_label = "Match to Repeat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.area.type = 'GRAPH_EDITOR'
        bpy.ops.graph.reveal()
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

        action = bpy.context.object.animation_data.action
        slot = bpy.context.object.animation_data.action_slot
        if action and slot:
            channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
            for fcurve in channelbag.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x == bpy.context.scene.frame_start:
                        keyframe.select_control_point = True
                        keyframe.select_left_handle = True
                        keyframe.select_right_handle = True

        # Duplicate and move keyframes
        bpy.ops.graph.duplicate_move(
            GRAPH_OT_duplicate={"mode": 'TRANSLATION'},
            TRANSFORM_OT_translate={
                "value": (bpy.context.scene.frame_end - bpy.context.scene.frame_start, 0, 0),
                "orient_type": 'GLOBAL',
                "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                "orient_matrix_type": 'GLOBAL',
                "constraint_axis": (True, False, False),
                "proportional_edit_falloff": 'SMOOTH',
                "proportional_size": 1,
                "snap": True,
                "snap_elements": {'VERTEX'},
            
                "snap_target": 'CLOSEST',
                "use_snap_self": True,
                "use_snap_edit": True,
                "use_snap_nonedit": True,

                "use_duplicated_keyframes": True,

            }
        )

        bpy.ops.graph.reveal()
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.graph.select_column(mode='CFRA')
        bpy.ops.graph.handle_type(type='FREE')
        bpy.ops.graph.select_key_handles(
            left_handle_action='DESELECT',
            right_handle_action='SELECT',
            key_action='DESELECT'
        )
        bpy.ops.graph.handle_type(type='VECTOR')
        bpy.ops.graph.reveal()
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.context.scene.frame_set(bpy.context.scene.frame_end)
        bpy.ops.graph.select_column(mode='CFRA')
        bpy.ops.graph.handle_type(type='FREE')
        bpy.ops.graph.select_key_handles(
            left_handle_action='SELECT',
            right_handle_action='DESELECT',
            key_action='DESELECT'
        )
        bpy.ops.graph.handle_type(type='VECTOR')
        bpy.ops.graph.reveal()
        bpy.ops.graph.select_all(action='DESELECT')
        for obj in bpy.context.selected_objects:
            action = obj.animation_data.action
            slot = obj.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for fc in channelbag.fcurves:
                    for kp in fc.keyframe_points:
                        if bpy.context.scene.frame_start <= kp.co[0] <= bpy.context.scene.frame_end:
                            kp.select_control_point = True

        active_obj = bpy.context.active_object
        if active_obj and active_obj.animation_data and active_obj.animation_data.action:
            action = active_obj.animation_data.action
            slot = active_obj.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for curve in channelbag.fcurves:
                    curve.select = True
        if bpy.context.active_object and bpy.context.active_object.mode == 'POSE':
            bpy.context.area.type = 'GRAPH_EDITOR'
            action = bpy.context.active_object.animation_data.action
            slot = bpy.context.active_object.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for curve in channelbag.fcurves:
                    curve.select = True
            bpy.ops.graph.select_all(action='DESELECT')
            for obj in bpy.context.selected_objects:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if action and slot:
                    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                    for fc in channelbag.fcurves:
                        for kp in fc.keyframe_points:
                            if bpy.context.scene.frame_start <= kp.co[0] <= bpy.context.scene.frame_end:
                                kp.select_control_point = True

            
            bpy.ops.anim.channels_select_all(action='SELECT')
     
        return {'FINISHED'}

class SelectKeyframesOperator(bpy.types.Operator):
    """select and make all Channels available to use the repeat button"""
    bl_idname = "graph.select_keyframes_in_range"
    bl_label = "Select Keyframes in Range"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.area.type = 'GRAPH_EDITOR'
        bpy.ops.graph.reveal()
        bpy.ops.anim.channels_setting_disable(type='MUTE')
        bpy.ops.anim.channels_setting_disable(type='PROTECT')

        active_obj = context.active_object
        if active_obj and active_obj.animation_data and active_obj.animation_data.action:
            action = active_obj.animation_data.action
            slot = active_obj.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for curve in channelbag.fcurves:
                    curve.select = True

        if active_obj and active_obj.mode == 'POSE':
            action = active_obj.animation_data.action
            slot = active_obj.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                for curve in channelbag.fcurves:
                    curve.select = True
            bpy.ops.graph.select_all(action='DESELECT')
            scene = context.scene
            start_frame = scene.frame_start
            end_frame = scene.frame_end
            for obj in context.selected_objects:
                action = obj.animation_data.action
                slot = obj.animation_data.action_slot
                if action and slot:
                    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                    for fc in channelbag.fcurves:
                        for kp in fc.keyframe_points:
                            if start_frame <= kp.co[0] <= end_frame:
                                kp.select_control_point = True

        bpy.ops.anim.channels_select_all(action='SELECT')

        return {'FINISHED'}

class RepeatAnimationPanel(bpy.types.Panel):
    bl_label = "Repeat Animation"
    bl_idname = "GRAPH_PT_RepeatAnimationPanel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    

    @classmethod
    def poll(cls, context):
        return context.scene.show_panels[5]

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        
        box = layout.box()
        row = box.row()
        row.label(text="Setup Tools", icon='SETTINGS')
        
        col = box.column(align=True)
        col.operator(
            SelectKeyframesOperator.bl_idname, 
            text="Setup Channels"
        )
        col.operator(
            MatchToRepeatOperator.bl_idname, 
            text="Match to Repeat"
        )
        
        box = layout.box()
        row = box.row()
        row.label(text="Repeat Tools", icon='DUPLICATE')
        
        col = box.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(scene, "keyframe_duplicate_count", text="Count")
        
        row = box.row()
        row.scale_y = 1.5
        row.operator(
            DuplicateKeyframesOperator.bl_idname, 
            text="Repeat Keyframes", 
            icon='FILE_REFRESH'
        )
        





classes = (
   
    SelectKeyframesOperator,
    MatchToRepeatOperator,
    DuplicateKeyframesOperator,

    RepeatAnimationPanel,

)

def register():
    for cls in classes:       
        bpy.utils.register_class(cls)

    bpy.types.Scene.keyframe_duplicate_count = bpy.props.IntProperty(
        name="Keyframe Duplicate Count",
        description="Number of times to duplicate keyframes",
        default=1,
        min=1,  
        max=100  
    )

def unregister():            
    for cls in classes:       
        bpy.utils.unregister_class(cls)    


if __name__ == "__main__":
    register()     