bl_info = {
    "name": "Pin key",
    "blender": (4, 2, 0),
    "category": "Animation",
    "version": (1, 0, 0),
    "author": "Hamdi Amer",
    "description": "Track and display selected keyframe Information in the Graph Editor",
    "location": "Graph Editor > Sidebar > Keyframe Tracking",
}

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import anim_utils


active_tracker_operator = None
persistent_keyframe_data = []  
current_keyframe_data = []  

def ensure_channelbag(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return None
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    if not slot:
        slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
        obj.animation_data.action_slot = slot
    return anim_utils.action_ensure_channelbag_for_slot(action, slot)

class KeyframeTrackerOperator(bpy.types.Operator):
    """Track selected keyframe data"""
    bl_idname = "graph.keyframe_tracker_operator"
    bl_label = "Keyframe Tracker Operator"
    bl_options = {'REGISTER'}

    _timer = None
    _handle = None
    _is_running = False

    def modal(self, context, event):
        if not self._is_running:
            return {'CANCELLED'}

        if event.type == 'TIMER':
            self.draw_callback_px(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        global active_tracker_operator
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceGraphEditor.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')

        active_tracker_operator = self
        self._is_running = True
        return {'RUNNING_MODAL'}

    def draw_callback_px(self, context):
        global current_keyframe_data, persistent_keyframe_data

        if context.area.type != 'GRAPH_EDITOR':
            return

        obj = context.active_object
        if not obj:
            return

        channelbag = ensure_channelbag(obj)
        if not channelbag:
            return

        region = context.region
        view2d = context.region.view2d

        current_keyframe_data.clear()

        # Collect all selected keyframes
        selected_fcurves = bpy.context.selected_editable_fcurves
        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    current_keyframe_data.append((keyframe.co.x, keyframe.co.y))

        # Combine current and persistent keyframe data
        display_data = persistent_keyframe_data + current_keyframe_data

        if not display_data:
            return

        font_size = context.window_manager.keyframe_tracker_font_size
        color_background = context.window_manager.keyframe_tracker_background_color
        color_text_frame = context.window_manager.keyframe_tracker_text_frame_color
        color_text_value = context.window_manager.keyframe_tracker_text_value_color
        color_shadow = (0, 0, 0, 0.0)

        blf.size(0, font_size)

        for frame_number, value in display_data:
            pos = view2d.view_to_region(frame_number, value, clip=False)

            if pos:
                text_frame = f"🕒 Frame: {frame_number:.2f}"
                text_value = f"📊 Value: {value:.2f}"

                text_frame_width, text_frame_height = blf.dimensions(0, text_frame)
                text_value_width, text_value_height = blf.dimensions(0, text_value)

                max_text_width = max(text_frame_width, text_value_width)
                total_text_height = text_frame_height + text_value_height + 12

                margin = 6
                vertices = [
                    (pos[0] - margin, pos[1] - margin),
                    (pos[0] + max_text_width + margin, pos[1] - margin),
                    (pos[0] + max_text_width + margin, pos[1] + total_text_height + margin),
                    (pos[0] - margin, pos[1] + total_text_height + margin)
                ]

                gpu.state.blend_set('ALPHA')

                shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices})
                shader.bind()
                shader.uniform_float("color", color_background)
                batch.draw(shader)

                shadow_offset = 2
                blf.position(0, pos[0] + shadow_offset, pos[1] + text_value_height + 7 + shadow_offset, 0)
                blf.color(0, *color_shadow)
                blf.draw(0, text_frame)

                blf.position(0, pos[0] + shadow_offset, pos[1] + shadow_offset, 0)
                blf.color(0, *color_shadow)
                blf.draw(0, text_value)

                blf.position(0, pos[0], pos[1] + text_value_height + 7, 0)
                blf.color(0, *color_text_frame)
                blf.draw(0, text_frame)

                blf.position(0, pos[0], pos[1], 0)
                blf.color(0, *color_text_value)
                blf.draw(0, text_value)

                gpu.state.blend_set('NONE')

    def cancel(self, context):
        global active_tracker_operator
        context.window_manager.event_timer_remove(self._timer)
        if self._handle:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self._handle, 'WINDOW')
        self._is_running = False
        active_tracker_operator = None


class KeepTextVisibleOperator(bpy.types.Operator):
    """Keep Text Visible for Selected Keyframes"""
    bl_idname = "graph.keep_text_visible_operator"
    bl_label = "Keep Text Visible Operator"

    def execute(self, context):
        global persistent_keyframe_data, current_keyframe_data
        # Store the currently selected keyframes into the persistent list
        persistent_keyframe_data.extend(current_keyframe_data)
        
        return {'FINISHED'}

class ClearTextVisibleOperator(bpy.types.Operator):
    """Clear Text Visibility for Keyframes"""
    bl_idname = "graph.clear_text_visible_operator"
    bl_label = "Clear Text Visibility Operator"

    def execute(self, context):
        global persistent_keyframe_data
        # Clear the list that holds persistent keyframe data
        persistent_keyframe_data.clear()
        return {'FINISHED'}


class ActivateKeyframeTracker(bpy.types.Operator):
    """Activate Keyframe Tracker"""
    bl_idname = "graph.activate_keyframe_tracker"
    bl_label = "Activate Keyframe Tracker"

    def execute(self, context):
        context.window_manager.auto_update_active = True
        bpy.ops.graph.keyframe_tracker_operator('INVOKE_DEFAULT')
        return {'FINISHED'}

class DeactivateKeyframeTracker(bpy.types.Operator):
    """Deactivate Keyframe Tracker"""
    bl_idname = "graph.deactivate_keyframe_tracker"
    bl_label = "Deactivate Keyframe Tracker"

    def execute(self, context):
        global active_tracker_operator
        context.window_manager.auto_update_active = False
        if active_tracker_operator:
            active_tracker_operator.cancel(context)
        else:
            self.report({'WARNING'}, "No active keyframe tracker to deactivate.")
        return {'FINISHED'}

class KeyframeTrackerPanel(bpy.types.Panel):
    """Creates a Panel in the Graph Editor"""
    bl_label = "Keyframe Tracker"
    bl_idname = "GRAPH_PT_keyframe_tracker_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Clean Graph"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return getattr(context.scene, 'show_panels', [False]*8)[2]
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        box = layout.box()
        box.label(text="Appearance Settings", icon='COLOR')  
        box.prop(wm, "keyframe_tracker_font_size", text="Font Size")

        box = layout.box()
        layout.prop(wm, "keyframe_tracker_background_color", text="Background Color")                
        layout.prop(wm, "keyframe_tracker_text_frame_color", text="Frame Text Color")
        layout.prop(wm, "keyframe_tracker_text_value_color", text="Value Text Color")
        box = layout.box()

        box = layout.box()
        box.label(text="keyframe info", icon='RECOVER_LAST')  

        if not wm.auto_update_active:
            box.operator("graph.activate_keyframe_tracker", text="Activate Auto Update", icon='PLAY')
        else:
            box.operator("graph.deactivate_keyframe_tracker", text="Deactivate Auto Update", icon='PAUSE')

        row = box.row(align=False)
        row.operator("graph.keep_text_visible_operator", text="Keep Text Visible", icon='PINNED')
        row.operator("graph.clear_text_visible_operator", text="Clear Text Visibility", icon='X')






classes = (
    KeyframeTrackerOperator,
    ActivateKeyframeTracker,    
    DeactivateKeyframeTracker,    
    KeepTextVisibleOperator,
    ClearTextVisibleOperator,
    KeyframeTrackerPanel,
    
    
    
)



def register():

    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Register custom properties
    bpy.types.WindowManager.auto_update_active = bpy.props.BoolProperty(
        name="Auto Update Active",
        description="Auto update the keyframe tracker",
        default=False
    )
    bpy.types.WindowManager.keyframe_tracker_font_size = bpy.props.IntProperty(
        name="Font Size",
        description="Font size for keyframe tracker text",
        default=15,
        min=5,
        max=50
    )
    bpy.types.WindowManager.keyframe_tracker_background_color = bpy.props.FloatVectorProperty(
        name="Background Color",
        description="Background color for keyframe tracker",
        subtype='COLOR',
        default=(0.1, 0.1, 0.1, 0.3),
        min=0.0,
        max=1.0,
        size=4
    )



    bpy.types.WindowManager.keyframe_tracker_text_frame_color = bpy.props.FloatVectorProperty(
        name="Frame Text Color",
        description="Frame Text color for keyframe tracker",
        subtype='COLOR',
        default=(1.0, 0.559535, 0.1, 1.0),
        min=0.0,
        max=1.0,
        size=4
    )


    bpy.types.WindowManager.keyframe_tracker_text_value_color = bpy.props.FloatVectorProperty(
  

        name="Value Text Color",
        description="Value Text color for keyframe tracker",
        subtype='COLOR',
        default=(0.693219, 1.0, 0.15, 1.0),
        min=0.0,
        max=1.0,
        size=4
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    # Unregister custom properties
    del bpy.types.WindowManager.auto_update_active
    del bpy.types.WindowManager.keyframe_tracker_font_size
    del bpy.types.WindowManager.keyframe_tracker_background_color
    del bpy.types.WindowManager.keyframe_tracker_text_frame_color
    del bpy.types.WindowManager.keyframe_tracker_text_value_color

if __name__ == "__main__":
    register()