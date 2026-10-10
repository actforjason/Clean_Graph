import bpy
import random


class SmartOffsetProperties(bpy.types.PropertyGroup):
    """Container for all Smart Offset properties to avoid cluttering Scene ID"""
    keyframe_offset: bpy.props.IntProperty(
        name="Keyframe Offset",
        description="Positive offset time for selected keyframes",
        default=1,
        min=1,
        max=100
    )
    
    keyframe_value_offset: bpy.props.FloatProperty(
        name="Keyframe Value Offset",
        description="Positive offset amount for selected keyframe values",
        default=1.0,
        min=0.1,
        max=100.0
    )
    
    random_range: bpy.props.FloatProperty(
        name="Random Range",
        description="Range for randomizing keyframe values",
        default=0.0
    )
    
    max_offset_ratio: bpy.props.FloatProperty(
        name="Max Offset Ratio",
        description="Maximum offset ratio for keyframe randomization",
        default=0.0,
        min=0.0,
        max=1.0
    )


class OffsetKeyframesPositiveXOperator(bpy.types.Operator):
    """Offset selected keyframes forward on the X axis"""
    bl_idname = "graph.offset_keyframes_x_positive"
    bl_label = "Offset Keyframes Forward"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.area.type == 'GRAPH_EDITOR' and
            context.selected_editable_fcurves
        )

    def execute(self, context):
        props = context.scene.smart_offset_props
        offset_value = props.keyframe_offset
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.co[0] += offset_value
                    keyframe.handle_left[0] += offset_value
                    keyframe.handle_right[0] += offset_value

        for marker in context.scene.timeline_markers:
            if marker.select:
                marker.frame += offset_value                    

        return {'FINISHED'}


class OffsetKeyframesNegativeXOperator(bpy.types.Operator):
    """Offset selected keyframes backward on the X axis"""
    bl_idname = "graph.offset_keyframes_x_negative"
    bl_label = "Offset Keyframes Backward"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.area.type == 'GRAPH_EDITOR' and
            context.selected_editable_fcurves
        )

    def execute(self, context):
        props = context.scene.smart_offset_props
        offset_value = props.keyframe_offset
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.co[0] -= offset_value
                    keyframe.handle_left[0] -= offset_value
                    keyframe.handle_right[0] -= offset_value

        for marker in context.scene.timeline_markers:
            if marker.select:
                marker.frame -= offset_value                    

        return {'FINISHED'}


class AdjustKeyframeValuesPositiveOperator(bpy.types.Operator):
    """Increase selected keyframe values on the Y axis"""
    bl_idname = "graph.adjust_keyframe_values_positive"
    bl_label = "Increase Keyframe Values"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.smart_offset_props
        value_offset = props.keyframe_value_offset
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.co[1] += value_offset
                    keyframe.handle_left.y += value_offset
                    keyframe.handle_right.y += value_offset

        context.area.tag_redraw()
        return {'FINISHED'}


class AdjustKeyframeValuesNegativeOperator(bpy.types.Operator):
    """Decrease selected keyframe values on the Y axis"""
    bl_idname = "graph.adjust_keyframe_values_negative"
    bl_label = "Decrease Keyframe Values"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.smart_offset_props
        value_offset = props.keyframe_value_offset
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.co[1] -= value_offset
                    keyframe.handle_left.y -= value_offset
                    keyframe.handle_right.y -= value_offset

        context.area.tag_redraw()
        return {'FINISHED'}


class ORandomizeKeyframesACOperator(bpy.types.Operator):
    """Skip randomizing the first keyframe value And Randomize The Other Selected Keyframe Values On Y Axis"""
    bl_idname = "graph.smart_randomize"
    bl_label = "Randomize Keyframes"

    def execute(self, context):
        props = context.scene.smart_offset_props
        random_range = props.random_range
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            selected_points = [p for p in fcurve.keyframe_points if p.select_control_point]

            if selected_points:
                first_point_value = selected_points[0].co[1]

            for point in selected_points:
                current_value = point.co[1]

                if point == selected_points[0]:
                    continue
                
                new_value = current_value + random.uniform(-abs(random_range), abs(random_range))

                if random_range > 0:
                    point.co[1] = max(0, new_value)
                else:
                    point.co[1] = min(0, new_value)

            if selected_points:
                selected_points[0].co[1] = first_point_value

        bpy.ops.graph.handle_type(type='AUTO')
        return {'FINISHED'}


class RandomizeKeyframesOperator(bpy.types.Operator):
    """Randomize Keyframe Values On Y Axis"""
    bl_idname = "graph.randomize_keyframes"
    bl_label = "Randomize Keyframes"

    def execute(self, context):
        props = context.scene.smart_offset_props
        random_range = props.random_range
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            selected_points = [p for p in fcurve.keyframe_points if p.select_control_point]
            for point in selected_points:
                current_value = point.co[1]
                point.co[1] = current_value + random.uniform(-random_range, random_range)

        bpy.ops.graph.handle_type(type='AUTO')
        return {'FINISHED'}


def offset_keyframes_randomly(keyframes, max_offset_ratio):
    frame_range = bpy.context.scene.frame_end - bpy.context.scene.frame_start
    for i, keyframe in enumerate(keyframes):
        original_x = keyframe.co.x
        random_offset = random.uniform(-max_offset_ratio, max_offset_ratio) * frame_range
        new_x = original_x + random_offset
        
        if i > 0:
            prev_keyframe = keyframes[i - 1]
            new_x = max(prev_keyframe.co.x, new_x)
        
        new_x = max(bpy.context.scene.frame_start, min(bpy.context.scene.frame_end, new_x))
        keyframe.co.x = new_x


class RandomOffsetKeyframesOperator(bpy.types.Operator):
    """Offset selected keyframes randomly along the X-axis"""
    bl_idname = "graph.offset_keyframes"
    bl_label = "Random Offset Keyframes"

    def execute(self, context):
        props = context.scene.smart_offset_props
        max_offset_ratio = props.max_offset_ratio
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            selected_keyframes = [keyframe for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
            offset_keyframes_randomly(selected_keyframes, max_offset_ratio)

        bpy.ops.graph.handle_type(type='AUTO_CLAMPED')
        return {'FINISHED'}


class StretchAfterKeyframes(bpy.types.Operator):
    """Stretch keyframes after current frame to end frame range"""
    bl_idname = "graph.scale_keyframes_after_current"
    bl_label = "Scale Keyframes After Current Frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.area.type = 'GRAPH_EDITOR'
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        current_frame = scene.frame_current
        selected_fcurves = context.selected_editable_fcurves

        if not selected_fcurves:
            self.report({'WARNING'}, "No F-Curves selected")
            return {'CANCELLED'}

        max_valid_frame = None
        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co.x <= end_frame and keyframe.co.x >= current_frame:
                    if max_valid_frame is None or keyframe.co.x > max_valid_frame:
                        max_valid_frame = keyframe.co.x

        if max_valid_frame is None:
            self.report({'WARNING'}, "No valid keyframes found after the current frame")
            return {'CANCELLED'}

        scale_factor = (end_frame - current_frame) / (max_valid_frame - current_frame)

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co.x <= end_frame and keyframe.co.x >= current_frame:
                    keyframe.co.x = current_frame + (keyframe.co.x - current_frame) * scale_factor
                    offset = round(keyframe.co.x) - keyframe.co.x
                    keyframe.co.x += offset
                    keyframe.handle_left.x = current_frame + (keyframe.handle_left.x - current_frame) * scale_factor + offset
                    keyframe.handle_right.x = current_frame + (keyframe.handle_right.x - current_frame) * scale_factor + offset
        
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.ops.graph.select_column(mode='CFRA')
        bpy.ops.graph.handle_type(type='AUTO')
        bpy.ops.anim.channels_select_all(action='SELECT')

        self.report({'INFO'}, "Selected keyframes scaled on the x-axis after the current frame.")
        return {'FINISHED'}


class Stretch_ScaleKeyframes(bpy.types.Operator):
    """Stretch keyframes Before current frame to start frame range"""
    bl_idname = "graph.scale_selected_keyframes"
    bl_label = "Scale Selected Keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'GRAPH_EDITOR'

    def execute(self, context):
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        current_frame = scene.frame_current
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            keyframes_to_select = [
                keyframe for keyframe in fcurve.keyframe_points
                if (start_frame <= keyframe.co.x <= current_frame)
            ]
            for keyframe in keyframes_to_select:
                keyframe.select_control_point = True

        min_frame = min(
            keyframe.co.x
            for fcurve in selected_fcurves
            for keyframe in fcurve.keyframe_points
            if start_frame <= keyframe.co.x <= current_frame
        )
        max_frame = max(
            keyframe.co.x
            for fcurve in selected_fcurves
            for keyframe in fcurve.keyframe_points
            if start_frame <= keyframe.co.x <= current_frame
        )

        scale_factor = (current_frame - start_frame) / (max_frame - min_frame)

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co.x <= current_frame:
                    keyframe.co.x = start_frame + (keyframe.co.x - min_frame) * scale_factor
                    offset = round(keyframe.co.x) - keyframe.co.x
                    keyframe.co.x += offset
                    keyframe.handle_left.x = start_frame + (keyframe.handle_left.x - min_frame) * scale_factor
                    keyframe.handle_right.x = start_frame + (keyframe.handle_right.x - min_frame) * scale_factor
        
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.ops.graph.select_column(mode='CFRA')
        bpy.ops.graph.handle_type(type='AUTO')
        bpy.ops.anim.channels_select_all(action='SELECT')
        
        return {'FINISHED'}


class ScaleAndSnapKeyframesOperator(bpy.types.Operator):
    bl_idname = "graph.scale_and_snap_keyframes"
    bl_label = "Scale and Snap Keyframes"
    bl_description = "Scales selected keyframes to fit within the frame range and snaps them to the nearest frame"
    
    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            context.area.type = 'GRAPH_EDITOR'

        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        selected_fcurves = context.selected_editable_fcurves

        if not selected_fcurves:
            self.report({'WARNING'}, "No keyframes selected.")
            return {'CANCELLED'}

        min_frame = float('inf')
        max_frame = float('-inf')

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    min_frame = min(min_frame, keyframe.co.x)
                    max_frame = max(max_frame, keyframe.co.x)

        if max_frame == min_frame:
            self.report({'WARNING'}, "All selected keyframes are on the same frame.")
            return {'CANCELLED'}

        scale_factor = (end_frame - start_frame) / (max_frame - min_frame)

        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.co.x = start_frame + (keyframe.co.x - min_frame) * scale_factor
                    offset = round(keyframe.co.x) - keyframe.co.x
                    keyframe.co.x += offset
                    keyframe.handle_left.x = start_frame + (keyframe.handle_left.x - min_frame) * scale_factor + offset
                    keyframe.handle_right.x = start_frame + (keyframe.handle_right.x - min_frame) * scale_factor + offset

        context.area.tag_redraw()
        self.report({'INFO'}, "Keyframes have been scaled and snapped to the nearest frame.")
        return {'FINISHED'}


class ScaleKeyframesOperator(bpy.types.Operator):
    """Scale Selected Keyframes on X Axis and Snap to Nearest Frame"""
    bl_idname = "graph.scale_keyframes_x"
    bl_label = "Scale Keyframes X"
    bl_options = {'REGISTER', 'UNDO'}

    scale_factor: bpy.props.FloatProperty(
        name="Scale Factor",
        description="Factor to scale keyframes on the X axis",
        default=1.0
    )

    @classmethod
    def poll(cls, context):
        return context.area.type == 'GRAPH_EDITOR' and context.selected_editable_fcurves

    def invoke(self, context, event):
        self.scale_factor = 1.0
        return self.execute(context)

    def execute(self, context):
        current_frame = context.scene.frame_current
        fcurves = context.selected_editable_fcurves

        if not fcurves:
            self.report({'ERROR'}, "No fcurves selected")
            return {'CANCELLED'}

        for fcurve in fcurves:
            selected_keyframes = [keyframe for keyframe in fcurve.keyframe_points if keyframe.select_control_point]

            if not selected_keyframes:
                continue

            for keyframe in selected_keyframes:
                x_val = keyframe.co[0]
                handle_left_x = keyframe.handle_left[0]
                handle_right_x = keyframe.handle_right[0]

                offset = round(keyframe.co[0]) - keyframe.co[0]
                keyframe.co[0] += offset
                keyframe.co[0] = (x_val - current_frame) * self.scale_factor + current_frame
                keyframe.handle_left[0] = (handle_left_x - current_frame) * self.scale_factor + current_frame
                keyframe.handle_right[0] = (handle_right_x - current_frame) * self.scale_factor + current_frame

            fcurve.update()

        context.area.tag_redraw()
        return {'FINISHED'}


class SmartOffset_PT_Panel(bpy.types.Panel):
    bl_label = "Smart Offset"
    bl_idname = "GRAPH_PT_smart_offset"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    bl_order = 5

    @classmethod
    def poll(cls, context):
        return context.scene.show_panels[4]

    def draw(self, context):
        layout = self.layout
        props = context.scene.smart_offset_props
        
        main_box = layout.box()
        col = main_box.column(align=True)
        col.label(text="Keyframe Manipulation", icon='GRAPH')
        
        row = col.row(align=True)
        row.operator("graph.scale_selected_keyframes", text="Stretch Before", icon='TRIA_LEFT')
        row.operator("graph.scale_keyframes_after_current", text="Stretch After", icon='TRIA_RIGHT')
        col.operator("graph.scale_and_snap_keyframes", text="Squash and Stretch", icon='FULLSCREEN_ENTER')
        
        # X Offset Tools
        offset_box = layout.box()
        col = offset_box.column(align=True)
        col.label(text="Offset Tools", icon='ARROW_LEFTRIGHT')
        
        # X Offset Section
        row = col.row(align=True)      
        row.operator(OffsetKeyframesNegativeXOperator.bl_idname, text="", icon='TRIA_LEFT')    
        row.prop(props, "keyframe_offset", text="Position Offset")             
        row.operator(OffsetKeyframesPositiveXOperator.bl_idname, text="", icon='TRIA_RIGHT')

        
        # Y Offset Section
        col.separator()
        row = col.row(align=True)
        row.prop(props, "keyframe_value_offset", text=" Values Offset")
        row.operator(AdjustKeyframeValuesPositiveOperator.bl_idname, text="", icon='TRIA_UP')
        row.operator(AdjustKeyframeValuesNegativeOperator.bl_idname, text="", icon='TRIA_DOWN')
        
        # Randomization Section
        random_box = layout.box()
        col = random_box.column(align=True)
        col.label(text="Randomization", icon='GRID')
        
        col.prop(props, "random_range", text="Y Range")
        row = col.row(align=True)
        row.operator(RandomizeKeyframesOperator.bl_idname, text="Randomize Y Values", icon='RNDCURVE')
        row.operator("graph.smart_randomize", text="Smart Randomize", icon='OUTLINER_DATA_CURVES')
        
        col.separator()
        col.prop(props, "max_offset_ratio", text="X Max Ratio")
        col.operator(RandomOffsetKeyframesOperator.bl_idname, text="Offset X Values", icon='ARROW_LEFTRIGHT')
        
        # Scaling Section
        scale_box = layout.box()
        scale_box.label(text="Scaling", icon='FULLSCREEN_EXIT')
        scale_box.operator(ScaleKeyframesOperator.bl_idname, text="Scale Keyframes")


classes = (
    SmartOffsetProperties,
    ScaleAndSnapKeyframesOperator,
    StretchAfterKeyframes,
    Stretch_ScaleKeyframes,
    OffsetKeyframesPositiveXOperator,
    OffsetKeyframesNegativeXOperator,
    AdjustKeyframeValuesPositiveOperator,
    AdjustKeyframeValuesNegativeOperator,
    RandomizeKeyframesOperator,
    ORandomizeKeyframesACOperator,
    RandomOffsetKeyframesOperator,
    ScaleKeyframesOperator,
    SmartOffset_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.smart_offset_props = bpy.props.PointerProperty(
        type=SmartOffsetProperties
    )


def unregister():
    del bpy.types.Scene.smart_offset_props
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()