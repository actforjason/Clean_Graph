import bpy 
import math
import numpy as np
from bpy.props import EnumProperty, IntProperty, BoolProperty
from bpy_extras import anim_utils

def ensure_channelbag(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return None
    action = obj.animation_data.action
    slot = obj.animation_data.action_slot
    if not slot:
        slot = action.slots.new(id_type=obj.rna_type.identifier, name=obj.name + "_slot")
        obj.animation_data.action_slot = slot
    return anim_utils.action_ensure_channelbag_for_slot(action, slot)

class GRAPH_OT_DrawKeyframes(bpy.types.Operator):
    """Draw Keyframes in Graph Editor with Interpolation Selection by clicking the mouse"""
    bl_idname = "graph.draw_keyframes"
    bl_label = "Draw Keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    _drawing = False
    _prev_mouse_pos = None
    _selected_keyframe = None
    _selected_fcurves = []
    _handles_set = False

    def modal(self, context, event):
        """Handle modal events for drawing keyframes."""
        
        if event.type in {'ESC', 'RIGHTMOUSE'} or not context.area:
            return self.cancel(context)
            
        if context.area.type != 'GRAPH_EDITOR':
            self.report({'WARNING'}, "Active area is no longer a Graph Editor")
            return self.cancel(context)

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self._start_drawing(context, event)
            elif event.value == 'RELEASE':
                self._stop_drawing(context)
            return {'RUNNING_MODAL'}

        if self._drawing and event.type == 'MOUSEMOVE':
            self._update_drawing(context, event)
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        """Initialize the operator."""
        if context.area.type == 'GRAPH_EDITOR':
            context.window_manager.modal_handler_add(self)
            context.window_manager.graph_draw_keyframes = True
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active area is not a Graph Editor")
            return {'CANCELLED'}

    def _start_drawing(self, context, event):
        """Initialize drawing by capturing the initial mouse position."""
        self._drawing = True
        self._prev_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self._handles_set = False
        self.add_keyframe(context, *self._prev_mouse_pos)

    def _stop_drawing(self, context):
        """Stop the drawing process and clear the selection."""
        self._drawing = False
        self._clear_selection()
        context.area.tag_redraw()

    def _update_drawing(self, context, event):
        """Update the selected keyframe's position based on mouse movement."""
        if self._selected_keyframe and self._selected_fcurves:
            mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
            if (abs(mouse_x - self._prev_mouse_pos[0]) > 1 or
                    abs(mouse_y - self._prev_mouse_pos[1]) > 1):
                self.modify_keyframe(context, mouse_x, mouse_y)
                self._prev_mouse_pos = (mouse_x, mouse_y)

    def add_keyframe(self, context, mouse_x, mouse_y):
        """Add or select a keyframe at the specified mouse position."""
        region = context.region
        view2d = region.view2d
        frame, value = view2d.region_to_view(mouse_x, mouse_y)
        frame = round(frame)
        
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE' or not obj.animation_data or not obj.animation_data.action:
            self._clear_selection()
            return

        bone = context.active_pose_bone
        if not bone:
            self.report({'WARNING'}, "No bone selected")
            self._clear_selection()
            return

        channelbag = ensure_channelbag(obj)
        if not channelbag:
            self._clear_selection()
            return

        bone_fcurves = [fcurve for fcurve in channelbag.fcurves 
                        if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]')]
        
        self._selected_fcurves = [fcurve for fcurve in bone_fcurves if fcurve.select]
        if not self._selected_fcurves:
            self._selected_fcurves = bone_fcurves
            
        bpy.ops.graph.select_all(action='DESELECT')
        for fcurve in self._selected_fcurves:
            close_keyframe = next(
                (kf for kf in fcurve.keyframe_points if abs(kf.co[0] - frame) < 1),
                None
            )

            if close_keyframe:
                self._selected_keyframe = close_keyframe
                self._select_keyframe(self._selected_keyframe, True)
                continue
            
            
            is_quaternion = 'rotation_quaternion' in fcurve.data_path
            is_euler = 'rotation_euler' in fcurve.data_path
            
            
            if is_euler:
                value = math.radians(value)
            
            
            self._selected_keyframe = fcurve.keyframe_points.insert(frame, value, options={'FAST'})
            
            
            interp = context.window_manager.graph_keyframe_interpolation
            
            
            if is_quaternion:
                
                if interp == 'BEZIER':
                    
                    
                    self._selected_keyframe.interpolation = 'BEZIER'
                else:
                    self._selected_keyframe.interpolation = interp
            else:
                
                self._selected_keyframe.interpolation = interp
                
            self._select_keyframe(self._selected_keyframe, True)
            fcurve.update()

    def modify_keyframe(self, context, mouse_x, mouse_y):
        """Modify the selected keyframe's value based on mouse movement."""
        if not self._selected_fcurves:
            return

        region = context.region
        view2d = region.view2d
        frame, value = view2d.region_to_view(mouse_x, mouse_y)
        frame = round(frame)

        for fcurve in self._selected_fcurves:
            keyframes = fcurve.keyframe_points
            if not keyframes:
                continue
                
            closest_keyframe = min(keyframes, key=lambda kp: abs(kp.co[0] - frame))
            
            
            if 'rotation_euler' in fcurve.data_path:
                value = math.radians(value)
                
            closest_keyframe.co = (frame, value)
            
            if not self._handles_set:
                self._set_handles(closest_keyframe)
                self._handles_set = True
                
            fcurve.update()

    def _set_handles(self, keyframe):
        """Set the handles for a Bezier keyframe to AUTO."""
        
        if keyframe and keyframe.interpolation == 'BEZIER':
            keyframe.handle_left_type = 'AUTO'
            keyframe.handle_right_type = 'AUTO'

    def _select_keyframe(self, keyframe, select=True):
        """Select or deselect a keyframe."""
        if keyframe:
            keyframe.select_control_point = select
            keyframe.select_left_handle = select
            keyframe.select_right_handle = select

    def _clear_selection(self):
        """Clear the selected keyframe and F-Curves."""
        self._selected_keyframe = None
        self._selected_fcurves = []

    def cancel(self, context):
        """Handle the operator cancellation."""
        self._clear_selection()
        self._drawing = False
        context.window_manager.graph_draw_keyframes = False
        context.area.tag_redraw()
        return {'CANCELLED'}



class GRAPH_OT_FreeKeyframes(bpy.types.Operator):
    """Draw Keyframes in Graph Editor with Linear Interpolation by dragging the mouse"""
    bl_idname = "graph.free_keyframes"
    bl_label = "Draw Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    _drawing = False
    _prev_mouse_pos = None
    _min_distance = 2  

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'} or not context.area:
            return self.cancel(context)
            
        if context.area.type != 'GRAPH_EDITOR':
            self.report({'WARNING'}, "Active area is no longer a Graph Editor")
            return self.cancel(context)

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self._drawing = True
            self._prev_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            self.add_keyframe(context, *self._prev_mouse_pos)
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self._drawing = False
            return {'RUNNING_MODAL'}

        if self._drawing and event.type == 'MOUSEMOVE':
            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            distance = math.hypot(
                mouse_pos[0] - self._prev_mouse_pos[0],
                mouse_pos[1] - self._prev_mouse_pos[1]
            )
            
            if distance > self._min_distance:
                self._prev_mouse_pos = mouse_pos
                self.add_keyframe(context, *mouse_pos)
            return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}

    def add_keyframe(self, context, mouse_x, mouse_y):
        """Add a keyframe at the given mouse position with Linear Interpolation"""
        region = context.region
        view2d = region.view2d
        frame, value = view2d.region_to_view(mouse_x, mouse_y)
        frame = round(frame)
        
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            return

        if obj.mode != 'POSE' or not context.active_pose_bone:
            return
            
        bone = context.active_pose_bone
        channelbag = ensure_channelbag(obj)
        if not channelbag:
            return

        
        selected_fcurves = [
            fcurve for fcurve in channelbag.fcurves 
            if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]') and fcurve.select
        ]
        if not selected_fcurves:
            selected_fcurves = [
                fcurve for fcurve in channelbag.fcurves 
                if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]')
            ]

        for fcurve in selected_fcurves:
            
            is_quaternion = 'rotation_quaternion' in fcurve.data_path
            is_euler = 'rotation_euler' in fcurve.data_path
            
            current_value = value
            
            
            if is_euler:
                current_value = math.radians(value)
            
            
            keyframe = fcurve.keyframe_points.insert(frame, current_value, options={'FAST'})
            
            
            if is_quaternion:
                
                keyframe.interpolation = 'LINEAR'
            else:
                
                keyframe.interpolation = 'LINEAR'
                
            
            fcurve.update()
            
        context.area.tag_redraw()

    def invoke(self, context, event):
        """Initialize the operator."""
        if context.area.type == 'GRAPH_EDITOR':
            context.window_manager.modal_handler_add(self)
            context.window_manager.graph_free_keyframes = True 
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active area is not a Graph Editor")
            return {'CANCELLED'}
        
    def cancel(self, context):
        """Handle the operator cancellation."""
        self._drawing = False
        context.window_manager.graph_free_keyframes = False
        context.area.tag_redraw()
        return {'CANCELLED'}

class GRAPH_OT_QuickCleaner(bpy.types.Operator):
    """Clean keyframes by reducing density and applying consistent interpolation"""
    bl_idname = "graph.quick_cleaner"
    bl_label = "Clean Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.animation_data

    def execute(self, context):
        scene = context.scene
        interval = scene.mark_interval        
        selected_fcurves = context.selected_editable_fcurves
        if not selected_fcurves:
            self.report({'WARNING'}, "No F-Curves selected")
            return {'CANCELLED'}

        self.snap_keyframes(selected_fcurves)
        
        frame_range = self.get_frame_range(selected_fcurves)
        if not frame_range:
            self.report({'WARNING'}, "No keyframes found in selected F-Curves")
            return {'CANCELLED'}
        
        self.reduce_keyframes(selected_fcurves, frame_range, interval)
        self.apply_interpolation(selected_fcurves)
        
        return {'FINISHED'}

    def snap_keyframes(self, fcurves):
        """Snap keyframes to integer frames"""
        for fcurve in fcurves:
            for keyframe in fcurve.keyframe_points:
                
                new_frame = round(keyframe.co.x)
                offset = new_frame - keyframe.co.x
                keyframe.co.x = new_frame                           
                keyframe.handle_left.x += offset
                keyframe.handle_right.x += offset

    def get_frame_range(self, fcurves):
        """Get min and max frame from selected keyframes"""
        frames = []
        for fcurve in fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    frames.append(keyframe.co.x)
        
        if not frames:
            return None
            
        return (min(frames), max(frames))

    def reduce_keyframes(self, fcurves, frame_range, interval):
        """Reduce keyframe density using numpy for efficiency"""
        min_frame, max_frame = frame_range
        keep_frames = set(np.arange(min_frame, max_frame + 1, interval))
        
        for fcurve in fcurves:
           
            to_delete = []
            for i, keyframe in enumerate(fcurve.keyframe_points):
                if keyframe.select_control_point and round(keyframe.co.x) not in keep_frames:
                    to_delete.append(i)
            
            for i in sorted(to_delete, reverse=True):
                fcurve.keyframe_points.remove(fcurve.keyframe_points[i])
            
            fcurve.update()

    def apply_interpolation(self, fcurves):
        """Apply consistent interpolation to all keyframes"""
        for fcurve in fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'BEZIER'
                if keyframe.interpolation == 'BEZIER':
                    keyframe.handle_left_type = 'AUTO'
                    keyframe.handle_right_type = 'AUTO'

class GRAPH_PT_DrawKeyframesPanel(bpy.types.Panel):
    """Panel in the Graph Editor for Drawing Keyframes"""
    bl_label = "Keyframe Tools"
    bl_idname = "GRAPH_PT_draw_keyframes_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return getattr(context.scene, 'show_panels', [False]*8)[3]

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager

        
        main_box = layout.box()
        main_box.use_property_split = True
        main_box.use_property_decorate = False
        
        
        header = main_box.row()
        header.label(text="Keyframe Tools", icon='SETTINGS')
        
        
        drawing_box = main_box.box()
        drawing_box.label(text="Drawing Tools", icon='GREASEPENCIL')
        
        
        drawing_col = drawing_box.column(align=True)
        
        
        click_row = drawing_col.row(align=True)
        click_row.label(text="Precision Mode:", icon='DOT')
        if wm.graph_draw_keyframes:
            click_row.operator("graph.draw_keyframes", text="Stop", icon='PAUSE')
        else:
            click_row.operator("graph.draw_keyframes", text="Start", icon='RESTRICT_SELECT_OFF')
        
        
        drawing_col.label(text="Click to place keyframes", icon='BLANK1')
        
        
        drawing_col.separator(factor=0.5)
        
        
        interp_box = drawing_col.box()
        interp_box.label(text="Interpolation Settings", icon='CURVE_PATH')
        interp_box.prop(wm, "graph_keyframe_interpolation", text="Type")
        
        
        row = interp_box.row()
        if wm.graph_keyframe_interpolation == 'BEZIER':
            row.label(text="Smooth Curves", icon='SMOOTHCURVE')
        elif wm.graph_keyframe_interpolation == 'LINEAR':
            row.label(text="Straight Lines", icon='IPO_LINEAR')
        else:
            row.label(text="Constant Values", icon='FCURVE_SNAPSHOT')
        
        
        drawing_col.separator(factor=0.5)
        
        
        drag_row = drawing_col.row(align=True)
        drag_row.label(text="Freehand Mode:", icon='LINE_DATA')
        if wm.graph_free_keyframes:
            drag_row.operator("graph.free_keyframes", text="Stop", icon='PAUSE')
        else:
            drag_row.operator("graph.free_keyframes", text="Start", icon='FREEZE')
        
        
        drawing_col.label(text="Drag to draw keyframes", icon='BLANK1')
        
        
        drawing_col.separator(factor=1.0)

        
        cleanup_box = main_box.box()
        cleanup_box.label(text="Cleanup Tools", icon='BRUSH_DATA')
        
        
        interval_row = cleanup_box.row()
        interval_row.alignment = 'LEFT'
        interval_row.label(text="Frame Interval:")
        interval_row.prop(scene, "mark_interval", text="")
        
        
        interval_vis = cleanup_box.row()
        interval_vis.label(text=f"Key every {scene.mark_interval} frames")
        
        
        clean_row = cleanup_box.row()
        clean_row.scale_y = 1.5
        clean_row.operator("graph.quick_cleaner", text="Clean Keyframes", icon='BRUSH_DATA')
        
        
        status_row = cleanup_box.row(align=True)
        status_row.label(text="Status:")
        status_row.label(text="Ready", icon='CHECKMARK')
          
        
        help_box = main_box.box()
        help_box.label(text="Usage Tips:", icon='INFO')
        help_box.label(text="- Select F-Curves before drawing", icon='DOT')
        help_box.label(text="- Right-click cancels operations", icon='DOT')
        help_box.label(text="- ESC stops active tools", icon='DOT')
        
        
        footer = main_box.row()
        footer.alignment = 'CENTER'
        footer.label(text="Keyframe Tools v2.0", icon='NONE')


properties = {
    "graph_keyframe_interpolation": EnumProperty(
        name="Interpolation",
        items=[
            ('BEZIER', "Bezier", "Smooth interpolation"),
            ('LINEAR', "Linear", "Straight-line interpolation"),
            ('CONSTANT', "Constant", "Hold value until next keyframe")
        ],
        default='BEZIER'
    ),
    "graph_draw_keyframes": BoolProperty(default=False),
    "graph_free_keyframes": BoolProperty(default=False),
}

classes = (
    GRAPH_OT_DrawKeyframes,
  
    GRAPH_OT_FreeKeyframes,
    GRAPH_OT_QuickCleaner,
    GRAPH_PT_DrawKeyframesPanel,
)

def register():
    for prop_name, prop_value in properties.items():
        setattr(bpy.types.WindowManager, prop_name, prop_value)
    
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.mark_interval = IntProperty(
        name="Frame Interval",
        description="Number of frames between keyframes",
        default=4,
        min=1
    )

def unregister():

    for prop_name in properties:
        if hasattr(bpy.types.WindowManager, prop_name):
            delattr(bpy.types.WindowManager, prop_name)
    
    if hasattr(bpy.types.Scene, 'mark_interval'):
        del bpy.types.Scene.mark_interval
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()