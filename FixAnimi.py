




import bpy
from bpy_extras import anim_utils


class GRAPH_OT_FindFlatKeyframes(bpy.types.Operator):
    bl_idname = "graph.find_flat_keyframes"
    bl_label = "Find Flat Keyframes"
    bl_description = "Find and mark keyframes with the same value within the same F-Curve"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            context.area.type = 'GRAPH_EDITOR'

        selected_fcurves = context.selected_editable_fcurves
        if not selected_fcurves:
            self.report({'INFO'}, "No selected keyframes found.")
            return {'CANCELLED'}

        original_start_frame = context.scene.frame_start
        original_end_frame = context.scene.frame_end

        selected_keyframes = [
            keyframe.co.x for fcurve in selected_fcurves
            for keyframe in fcurve.keyframe_points if keyframe.select_control_point
        ]

        if selected_keyframes:
            new_start_frame = int(min(selected_keyframes))
            new_end_frame = int(max(selected_keyframes))
            context.scene.frame_start = new_start_frame
            context.scene.frame_end = new_end_frame

        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end

        existing_marker_names = set()

        channel_map = {
            "location": {0: "x", 1: "y", 2: "z"},
            "rotation_euler": {0: "x", 1: "y", 2: "z"},
            "rotation_quaternion": {0: "w", 1: "x", 2: "y", 3: "z"},
            "scale": {0: "x", 1: "y", 2: "z"}
        }

        channel_abbreviations = {
            "location": "loc",
            "rotation_euler": "rot",
            "rotation_quaternion": "quat",
            "scale": "scale"
        }

        def get_channel_type(data_path):
            if "location" in data_path:
                return "location"
            elif "rotation_euler" in data_path:
                return "rotation_euler"
            elif "rotation_quaternion" in data_path:
                return "rotation_quaternion"
            elif "scale" in data_path:
                return "scale"
            return "unknown"

        bpy.ops.graph.select_all(action='DESELECT')

        for fcurve in selected_fcurves:
            value_to_frames = {}

            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co.x <= end_frame:
                    value = keyframe.co.y
                    frame = int(keyframe.co.x)
                    value_to_frames.setdefault(value, []).append(frame)

            for value, frames in value_to_frames.items():
                if len(frames) > 1:
                    for i in range(len(frames) - 1):
                        first_frame = frames[i]
                        second_frame = frames[i + 1]
                        data_path = fcurve.data_path
                        channel_type = get_channel_type(data_path)
                        channel_short = channel_abbreviations.get(channel_type, channel_type)
                        axis = channel_map.get(channel_type, {}).get(fcurve.array_index, 'unknown')
                        marker_name = f"{channel_short}_{axis}_{second_frame}"

                        if marker_name not in existing_marker_names:
                            existing_marker_names.add(marker_name)
                            marker = context.scene.timeline_markers.new(name=marker_name)
                            marker.frame = first_frame

        context.scene.frame_start = original_start_frame
        context.scene.frame_end = original_end_frame
        self.report({'INFO'}, "Markers added for flat keyframes.")
        return {'FINISHED'}


class GRAPH_OT_CleanFlatKeyframes(bpy.types.Operator):
    bl_idname = "graph.clean_flat_keyframes"
    bl_label = "Clean Flat Keyframes"
    bl_description = "Remove flat keyframes (same value) within the selected range"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            context.area.type = 'GRAPH_EDITOR'

        original_start_frame = context.scene.frame_start
        original_end_frame = context.scene.frame_end
        selected_fcurves = context.selected_editable_fcurves

        if not selected_fcurves:
            self.report({'INFO'}, "No selected F-Curves found.")
            return {'CANCELLED'}

        selected_keyframes = [kf.co.x for fcurve in selected_fcurves for kf in fcurve.keyframe_points if kf.select_control_point]
        if selected_keyframes:
            context.scene.frame_start = int(min(selected_keyframes))
            context.scene.frame_end = int(max(selected_keyframes))

        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end

        for fcurve in selected_fcurves:
            value_to_keyframes = {}
            for kp in fcurve.keyframe_points:
                if start_frame <= kp.co.x <= end_frame:
                    value_to_keyframes.setdefault(kp.co.y, []).append(kp)

            for value, kps in value_to_keyframes.items():
                if len(kps) > 1:
                    # Keep only the one closest to current frame
                    current_frame = context.scene.frame_current
                    nearest_kp = min(kps, key=lambda k: abs(k.co.x - current_frame))
                    for kp in kps:
                        if kp != nearest_kp:
                            fcurve.keyframe_points.remove(kp)

        context.scene.frame_start = original_start_frame
        context.scene.frame_end = original_end_frame
        self.report({'INFO'}, "Flat keyframes cleaned.")
        return {'FINISHED'}


class GRAPH_OT_FindDriftKeyframes(bpy.types.Operator):
    bl_idname = "graph.find_drift_keyframes"
    bl_label = "Find Drift Keyframes"
    bl_description = "Find and mark keyframes with different values (drift keyframes)"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            context.area.type = 'GRAPH_EDITOR'

        selected_fcurves = context.selected_editable_fcurves
        if not selected_fcurves:
            self.report({'INFO'}, "No selected F-Curves.")
            return {'CANCELLED'}

        original_start_frame = context.scene.frame_start
        original_end_frame = context.scene.frame_end

        selected_frames = [kf.co.x for f in selected_fcurves for kf in f.keyframe_points if kf.select_control_point]
        if selected_frames:
            context.scene.frame_start = int(min(selected_frames))
            context.scene.frame_end = int(max(selected_frames))

        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end

        channel_map = {
            "location": {0: "x", 1: "y", 2: "z"},
            "rotation_euler": {0: "x", 1: "y", 2: "z"},
            "rotation_quaternion": {0: "w", 1: "x", 2: "y", 3: "z"},
            "scale": {0: "x", 1: "y", 2: "z"}
        }
        channel_abbreviations = {
            "location": "loc", "rotation_euler": "rot",
            "rotation_quaternion": "quat", "scale": "scale"
        }

        def get_channel_type(dp):
            for k in channel_abbreviations:
                if k in dp:
                    return k
            return "unknown"

        existing_markers = set()
        bpy.ops.graph.select_all(action='DESELECT')

        for fcurve in selected_fcurves:
            values_in_range = [kp.co.y for kp in fcurve.keyframe_points if start_frame <= kp.co.x <= end_frame]
            unique_values = set(values_in_range)

            for kp in fcurve.keyframe_points:
                if start_frame <= kp.co.x <= end_frame and kp.co.y in unique_values and values_in_range.count(kp.co.y) == 1:
                    kp.select_control_point = True

                    dp = fcurve.data_path
                    ct = get_channel_type(dp)
                    axis = channel_map.get(ct, {}).get(fcurve.array_index, "?")
                    name = f"Drift_{channel_abbreviations.get(ct, ct)}_{axis}"

                    unique_name = name
                    i = 1
                    while unique_name in existing_markers:
                        unique_name = f"{name}_{i}"
                        i += 1
                    existing_markers.add(unique_name)

                    marker = context.scene.timeline_markers.new(name=unique_name)
                    marker.frame = int(kp.co.x)

        context.scene.frame_start = original_start_frame
        context.scene.frame_end = original_end_frame
        self.report({'INFO'}, "Drift keyframes marked.")
        return {'FINISHED'}


class GRAPH_OT_CleanDriftKeyframes(bpy.types.Operator):
    bl_idname = "graph.clean_drift_keyframes"
    bl_label = "Clean Drift Keyframes"
    bl_description = "Remove drift keyframes (different values) within the selected range"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            context.area.type = 'GRAPH_EDITOR'

        selected_fcurves = context.selected_editable_fcurves
        if not selected_fcurves:
            self.report({'INFO'}, "No F-Curves selected.")
            return {'CANCELLED'}

        selected_frames = [kp.co.x for f in selected_fcurves for kp in f.keyframe_points if kp.select_control_point]
        if selected_frames:
            context.scene.frame_start = int(min(selected_frames))
            context.scene.frame_end = int(max(selected_frames))

        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end

        bpy.ops.graph.select_all(action='DESELECT')

        for fcurve in selected_fcurves:
            values_in_range = [kp.co.y for kp in fcurve.keyframe_points if start_frame <= kp.co.x <= end_frame]
            unique_values_once = {v for v in values_in_range if values_in_range.count(v) == 1}

            for kp in fcurve.keyframe_points:
                if start_frame <= kp.co.x <= end_frame and kp.co.y in unique_values_once:
                    kp.select_control_point = True

        bpy.ops.graph.delete()
        self.report({'INFO'}, "Drift keyframes removed.")
        return {'FINISHED'}


class GRAPH_OT_CreateFlatSpace(bpy.types.Operator):
    bl_idname = "graph.create_flat_space"
    bl_label ="Create Flat Space"
    bl_description = "Create a flat space between the current frame and selected keyframe"

    def execute(self, context):
        current_frame = context.scene.frame_current
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            self.report({'ERROR'}, "No F-Curves selected")
            return {'CANCELLED'}

        target_frame = None
        target_value = None
        for fcurve in fcurves:
            for kp in fcurve.keyframe_points:
                if kp.select_control_point:
                    target_frame = kp.co.x
                    target_value = kp.co.y
                    break
            if target_frame is not None:
                break

        if target_frame is None:
            self.report({'ERROR'}, "No keyframe selected")
            return {'CANCELLED'}

        min_f = min(current_frame, target_frame)
        max_f = max(current_frame, target_frame)

        for fcurve in fcurves:
            for kp in fcurve.keyframe_points:
                if min_f < kp.co.x < max_f:
                    kp.co.y = target_value

        bpy.ops.graph.snap(type='HORIZONTAL')
        self.report({'INFO'}, "Flat space created.")
        return {'FINISHED'}


class QuickCleanerOperator(bpy.types.Operator):
    """Keep only keyframes at regular intervals and delete the rest"""
    bl_idname = "scene.clean_markers"
    bl_label = "Interval Cleanup"

    def execute(self, context):
        scene = context.scene
        selected_fcurves = context.selected_editable_fcurves

        # Snap selected keyframes to nearest frame
        for fcurve in selected_fcurves:
            for kp in fcurve.keyframe_points:
                if kp.select_control_point:
                    offset = round(kp.co.x) - kp.co.x
                    kp.co.x += offset
                    kp.handle_left.x += offset
                    kp.handle_right.x += offset

        frames = [kp.co.x for f in selected_fcurves for kp in f.keyframe_points if kp.select_control_point]
        if not frames:
            return {'CANCELLED'}

        scene.frame_start = int(min(frames))
        scene.frame_end = int(max(frames))

        interval = getattr(scene, "mark_interval", 10)
        num_marks = (scene.frame_end - scene.frame_start) // interval
        scene.frame_end = scene.frame_start + num_marks * interval

        # Add markers
        for i in range(num_marks + 1):
            frame = scene.frame_start + i * interval
            scene.timeline_markers.new(name=f"Mark_{frame}", frame=frame)

        # Select keyframes at markers
        bpy.ops.graph.select_all(action='DESELECT')
        for marker in scene.timeline_markers:
            if scene.frame_start <= marker.frame <= scene.frame_end:
                bpy.context.scene.frame_set(int(marker.frame))
                bpy.ops.graph.select_column(mode='MARKERS_COLUMN')

        # Invert selection and delete non-interval keyframes
        bpy.ops.graph.select_all(action='INVERT')
        bpy.ops.graph.delete()

        # Clean up markers
        for marker in list(scene.timeline_markers):
            if scene.frame_start <= marker.frame <= scene.frame_end:
                scene.timeline_markers.remove(marker)

        self.report({'INFO'}, "Interval cleanup complete.")
        return {'FINISHED'}


class GRAPH_OT_snap_keyframes_to_frame(bpy.types.Operator):
    """Snaps selected keyframes and their handles to the nearest frame"""
    bl_idname = "graph.snap_keyframes_to_frame"
    bl_label = "Snap Selected Keyframes to Frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for fcurve in context.selected_editable_fcurves:
            for kp in fcurve.keyframe_points:
                if kp.select_control_point:
                    offset = round(kp.co.x) - kp.co.x
                    kp.co.x += offset
                    kp.handle_left.x += offset
                    kp.handle_right.x += offset
        self.report({'INFO'}, "Snapped to nearest frame.")
        return {'FINISHED'}


class OBJECT_OT_add_markers(bpy.types.Operator):
    bl_idname = "object.add_markers"
    bl_label = "Find Density"
    bl_description = "Add markers where gap between selected keyframes equals interval"

    def execute(self, context):
        context.area.type = 'GRAPH_EDITOR'
        interval = context.scene.marker_frame_interval
        if interval <= 0:
            return {'CANCELLED'}

        for fcurve in context.selected_editable_fcurves:
            kps = sorted([kp for kp in fcurve.keyframe_points if kp.select_control_point], key=lambda k: k.co.x)
            for i in range(len(kps) - 1):
                diff = int(kps[i + 1].co.x - kps[i].co.x)
                if diff == interval:
                    frame = int(kps[i + 1].co.x)
                    marker = context.scene.timeline_markers.new(name=str(diff))
                    marker.frame = frame

        self.report({'INFO'}, "Density markers added.")
        return {'FINISHED'}


class QuickFix_PT_Panel(bpy.types.Panel):
    bl_label = "Quick Fix Tools"
    bl_idname = "GRAPH_PT_Quick_Fix_tools"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    bl_order = 7

    @classmethod
    def poll(cls, context):
        return getattr(context.scene, 'show_panels', [False]*10)[6]

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)

        box = col.box()
        c = box.column(align=True)
        c.label(text="Interval Cleanup", icon='SORTTIME')
        row = c.row(align=True)
        row.prop(scene, "mark_interval", text="Interval")
        row.operator("scene.clean_markers", text="", icon='BRUSH_DATA')

        box = col.box()
        c = box.column(align=True)
        c.label(text="Flat/Drift Detection", icon='RESTRICT_SELECT_OFF')
        row = c.row(align=True)
        row.operator("graph.find_flat_keyframes", text="Find Flat", icon='VIEWZOOM')
        row.operator("graph.clean_flat_keyframes", text="Clean", icon='X')
        row = c.row(align=True)
        row.operator("graph.find_drift_keyframes", text="Find Drift", icon='VIEWZOOM')
        row.operator("graph.clean_drift_keyframes", text="Clean", icon='X')

        row = c.row(align=True)
        row.operator("object.add_markers", text="Find Density", icon='MARKER_HLT')
        row.prop(scene, "marker_frame_interval", text="")

        box = col.box()
        c = box.column(align=True)
        c.label(text="Flat Space", icon='MODIFIER')
        c.operator("graph.create_flat_space", text="Create Flat Space", icon='ADD')

        box = col.box()
        c = box.column(align=True)
        c.label(text="Keyframe Snapping", icon='SNAP_ON')
        c.operator("graph.snap_keyframes_to_frame", text="Snap to Frame", icon='SNAP_FACE')


classes = (
    QuickCleanerOperator,
    GRAPH_OT_FindFlatKeyframes,
    GRAPH_OT_CleanFlatKeyframes,
    GRAPH_OT_FindDriftKeyframes,
    GRAPH_OT_CleanDriftKeyframes,
    OBJECT_OT_add_markers,
    GRAPH_OT_CreateFlatSpace,
    GRAPH_OT_snap_keyframes_to_frame,
    QuickFix_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.mark_interval = bpy.props.IntProperty(
        name="Mark Interval", default=4, min=1
    )
    bpy.types.Scene.marker_frame_interval = bpy.props.IntProperty(
        name="Marker Interval", default=0, min=0
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.mark_interval
    del bpy.types.Scene.marker_frame_interval


if __name__ == "__main__":
    register()