




import bpy
from bpy_extras import anim_utils


# Define custom property group
class KeyframeToolsProps(bpy.types.PropertyGroup):
    new_frame_interval: bpy.props.IntProperty(
        name="Frame Interval",
        description="Number of frames between keyframes",
        default=5,
        min=1
    )
    
    my_custom_spacing: bpy.props.IntProperty(
        name="Custom Spacing",
        description="Spacing between keyframes",
        default=10,
        min=1
    )
    
    keyframe_step: bpy.props.IntProperty(
        name="Keyframe Step",
        description="Step between frames for keyframe insertion",
        default=2,
        min=1,
        options={'ANIMATABLE'}
    )

# Define operators
class OBJECT_OT_add_keyframes(bpy.types.Operator):
    bl_idname = "object.add_keyframes"
    bl_label = "Add Keyframes"
    bl_description = "Add keyframes between selected keyframes"

    def execute(self, context):
        context.area.type = 'GRAPH_EDITOR'
        selected_fcurves = context.selected_editable_fcurves
        props = context.scene.keyframe_tools_props
        frame_interval = props.new_frame_interval

        for fcurve in selected_fcurves:
            selected_keyframes = [kf for kf in fcurve.keyframe_points if kf.select_control_point]

            for i in range(len(selected_keyframes) - 1):
                current_keyframe = selected_keyframes[i]
                next_keyframe = selected_keyframes[i + 1]
                frame_diff = int(next_keyframe.co.x - current_keyframe.co.x)

                if frame_diff > frame_interval:
                    new_frame = current_keyframe.co.x + frame_interval
                    new_keyframe = fcurve.keyframe_points.insert(new_frame, fcurve.evaluate(new_frame))
                    new_keyframe.interpolation = current_keyframe.interpolation

        self.report({'INFO'}, "Additional keyframes have been added between the selected points or keyframes.")
        return {'FINISHED'}


class OBJECT_OT_insert_keyframes(bpy.types.Operator):
    bl_idname = "object.insert_keyframes"
    bl_label = "Insert Keyframes"
    bl_description = "Insert Keyframes for Selected Bones"

    def execute(self, context):
        self.insert_keyframes_for_selected_bones()
        return {'FINISHED'}
    
    def insert_keyframes_for_selected_bones(self):
        context = bpy.context
        context.area.type = 'GRAPH_EDITOR'
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        current_frame = scene.frame_current

        if context.object.mode != 'POSE':
            bpy.ops.object.posemode_toggle()

        selected_bones = context.selected_pose_bones

        for bone in selected_bones:
            for frame in [start_frame, current_frame, end_frame]:
                scene.frame_set(frame)

                if context.object.animation_data and context.object.animation_data.action:
                    bpy.ops.graph.keyframe_insert(type='SEL')
                else:
                    bone.keyframe_insert(data_path="location")
                    rotation_path = "rotation_quaternion" if bone.rotation_mode == 'QUATERNION' else "rotation_euler"
                    bone.keyframe_insert(data_path=rotation_path)
                    bone.keyframe_insert(data_path="scale")

        scene.frame_set(current_frame)
        print("Keyframes inserted for selected bones on start, current, and end frames.")


class OBJECT_OT_insert_keyframes_with_spacing(bpy.types.Operator):
    bl_idname = "object.insert_keyframes_with_spacing"
    bl_label = "Insert Keyframes with Spacing"
    bl_description = "Insert Keyframes with Increasing Spacing"

    def execute(self, context):
        self.insert_keyframes_with_increasing_spacing()
        return {'FINISHED'}
    
    def insert_keyframes_with_increasing_spacing(self):
        context = bpy.context
        scene = context.scene
        props = scene.keyframe_tools_props
        end_frame = scene.frame_end
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return
        
        for obj in selected_objects:
            if not obj.animation_data or not obj.animation_data.action:
                print(f"Warning: Object '{obj.name}' has no animation data.")
                continue
            
            action = obj.animation_data.action
            slot = obj.animation_data.action_slot
            if action and slot:
                channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
                selected_fcurves = [fcurve for fcurve in channelbag.fcurves if fcurve.select]
            
            if not selected_fcurves:
                print(f"Warning: No FCurves selected in object '{obj.name}'.")
                continue
            
            for fcurve in selected_fcurves:
                selected_keyframes = sorted(
                    keyframe.co.x for keyframe in fcurve.keyframe_points if keyframe.select_control_point
                )
                
                if len(selected_keyframes) < 2:
                    print(f"Warning: Object '{obj.name}', FCurve '{fcurve.data_path}' has less than 2 selected keyframes.")
                    continue
                
                initial_spacing = props.my_custom_spacing
                print(f"Initial spacing between the first two selected keyframes in FCurve '{fcurve.data_path}' is {initial_spacing} frames.")
                next_frame = selected_keyframes[0]
                spacing_increment = initial_spacing
                
                while next_frame < end_frame:
                    next_frame += spacing_increment
                    if next_frame >= end_frame:
                        break

                    scene.frame_set(int(next_frame))
                    fcurve.keyframe_points.insert(frame=next_frame, value=fcurve.evaluate(next_frame), options={'FAST'})
                    spacing_increment += initial_spacing
                
                print(f"Inserted keyframes (with increasing spacing) for object '{obj.name}'.")


class OBJECT_OT_add_and_snap_keyframes(bpy.types.Operator):
    bl_idname = "object.add_and_snap_keyframes"
    bl_label = "Add and Snap Keyframes"
    bl_description = "Add new keyframes between selected keyframes and snap them to the nearest frame"

    def execute(self, context):
        context.area.type = 'GRAPH_EDITOR'
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            keyframes = fcurve.keyframe_points
            new_keyframes = []

            for i in range(len(keyframes) - 1, 0, -1):
                current_keyframe = keyframes[i]
                prev_keyframe = keyframes[i - 1]

                if current_keyframe.select_control_point and prev_keyframe.select_control_point:
                    frame = (current_keyframe.co.x + prev_keyframe.co.x) / 2
                    value = fcurve.evaluate(frame)
                    new_keyframe = keyframes.insert(frame, value)
                    new_keyframes.append(new_keyframe)

            for keyframe in new_keyframes:
                keyframe.select_control_point = True

        self.report({'INFO'}, "New keyframes added between selected keyframes.")
        selected_fcurves = context.selected_editable_fcurves

        for fcurve in selected_fcurves:
            keyframes = fcurve.keyframe_points

            for keyframe in keyframes:
                if keyframe.select_control_point:
                    keyframe.co.x = round(keyframe.co.x)

        self.report({'INFO'}, "Snapped keyframes to nearest frame.")
        bpy.ops.graph.handle_type(type='AUTO')

        return {'FINISHED'}


class OBJECT_OT_insert_keyframes_step(bpy.types.Operator):
    bl_idname = "object.insert_keyframes_step"
    bl_label = "Insert Keyframes Step"
    bl_description = "Insert keyframes at intervals defined by the keyframe step"

    def execute(self, context):
        current_area = context.area.type
        current_frame = context.scene.frame_current
        context.area.type = 'GRAPH_EDITOR'
        scene = context.scene
        props = scene.keyframe_tools_props
        keyframe_step = props.keyframe_step
        start_frame = scene.frame_start
        end_frame = scene.frame_end

        if context.object.mode != 'POSE':
            bpy.ops.object.posemode_toggle()

        selected_bones = context.selected_pose_bones
        selected_fcurves = context.selected_editable_fcurves

        if selected_fcurves:
            for fcurve in selected_fcurves:
                for frame in range(current_frame, end_frame + 1, keyframe_step):
                    scene.frame_set(frame)
                    fcurve.keyframe_points.insert(frame, fcurve.evaluate(frame))

        scene.frame_set(current_frame)
        context.area.type = current_area
        return {'FINISHED'}


class SmartInsert_PT_Panel(bpy.types.Panel):
    bl_label = "Keyframe Tools"
    bl_idname = "GRAPH_PT_custom_panel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Clean Graph'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return context.scene.show_panels[1]    

    def draw(self, context):
        layout = self.layout
        props = context.scene.keyframe_tools_props
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Subdivide Tool
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Subdivide", icon='IPO_EASE_IN_OUT')
        col.operator("object.add_and_snap_keyframes")
        
        # Fill Tool
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Fill", icon='FCURVE')
        col.prop(props, "new_frame_interval")
        col.operator("object.add_keyframes")
        
        # Step Insert
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Step Insert", icon='SNAP_INCREMENT')
        col.prop(props, "keyframe_step")
        col.operator("object.insert_keyframes_step")
        
        # Spaced Insert
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Spaced Insert", icon='ARROW_LEFTRIGHT')
        col.prop(props, "my_custom_spacing")
        col.operator("object.insert_keyframes_with_spacing")

# List of all classes
classes = (
    KeyframeToolsProps,
    OBJECT_OT_add_keyframes,
    OBJECT_OT_insert_keyframes,
    OBJECT_OT_insert_keyframes_with_spacing,
    OBJECT_OT_add_and_snap_keyframes,
    OBJECT_OT_insert_keyframes_step,
    SmartInsert_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register our property group under scene
    bpy.types.Scene.keyframe_tools_props = bpy.props.PointerProperty(type=KeyframeToolsProps)

def unregister():
    # Remove property group first
    del bpy.types.Scene.keyframe_tools_props
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()