



import bpy
import bpy.utils.previews
import os
from bpy_extras import anim_utils

import blf
import gpu
from gpu_extras.batch import batch_for_shader
import math
import time
from mathutils import Vector
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
from collections import defaultdict




addon_keymaps = {}
_icons = None

def get_active_channelbag(context):
    obj = context.active_object
    if not obj or not obj.animation_data:
        return None
    anim_data = obj.animation_data
    action = anim_data.action
    if not action:
        return None
    slot = anim_data.action_slot
    if not slot:
        return None
    channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
    return channelbag

class FRO_OT_Setup_Handle_R_159B9(bpy.types.Operator):
    bl_idname = "kro.setup_handle_r_159b9"
    bl_label = "Setup Handle R"
    bl_description = "Set right handles to Vector"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    bpy.ops.graph.handle_type(override, type='FREE')
                    for fcurve in context.selected_editable_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.select_control_point:
                                keyframe.select_right_handle = True
                                keyframe.select_left_handle = False
                                keyframe.select_control_point = False
                    bpy.ops.graph.handle_type(override, type='VECTOR')
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        bpy.ops.graph.handle_type(type='FREE')
        for fcurve in context.selected_editable_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.select_right_handle = True
                    keyframe.select_left_handle = False
                    keyframe.select_control_point = False
        bpy.ops.graph.handle_type(type='VECTOR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Setup_Handle_L_Bea06(bpy.types.Operator):
    bl_idname = "kro.setup_handle_l_bea06"
    bl_label = "Setup Handle L"
    bl_description = "Set left handles to Vector"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    bpy.ops.graph.handle_type(override, type='FREE')
                    for fcurve in context.selected_editable_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.select_control_point:
                                keyframe.select_left_handle = True
                                keyframe.select_right_handle = False
                                keyframe.select_control_point = False
                    bpy.ops.graph.handle_type(override, type='VECTOR')
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        bpy.ops.graph.handle_type(type='FREE')
        for fcurve in context.selected_editable_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    keyframe.select_left_handle = True
                    keyframe.select_right_handle = False
                    keyframe.select_control_point = False
        bpy.ops.graph.handle_type(type='VECTOR')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)






class FRO_MT_Custom_Menu(bpy.types.Menu):
    bl_label = "Handle_Setup"
    bl_idname = "FRO_MT_Custom_Menu"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Interpolation Types", icon='IPO_LINEAR')
        layout.operator('graph.interpolation_type', text='Bezier', icon='IPO_BEZIER').type = 'BEZIER'
        layout.operator('graph.interpolation_type', text='Constant', icon='IPO_CONSTANT').type = 'CONSTANT'
        layout.operator('graph.interpolation_type', text='Linear', icon='IPO_LINEAR').type = 'LINEAR'

        layout.separator()
        
        
        layout.label(text="Handle Types", icon='CURVE_BEZCIRCLE')
        layout.operator('graph.handle_type', text='Auto', icon='SMOOTHCURVE').type = 'AUTO'
        layout.operator('graph.handle_type', text='Vector', icon='SHARPCURVE').type = 'VECTOR'
        layout.operator('graph.handle_type', text='Auto Clamped', icon='SPHERECURVE').type = 'AUTO_CLAMPED'
        layout.operator('graph.handle_type', text='Aligned', icon='LINCURVE').type = 'ALIGNED'
        layout.operator("graph.snap", text="Flat Handles", icon='NOCURVE').type = 'HORIZONTAL'
        
        layout.separator()
        layout.label(text="Handle Types Plus", icon='MOD_SIMPLIFY')        
        layout.operator('kro.setup_handle_r_159b9', text='Setup Handle R', icon='FORWARD')
        layout.operator('kro.setup_handle_l_bea06', text='Setup Handle L', icon='BACK')








def __icon(name):
    global _icons
    icon = _icons[name]
    return icon

class FRO_MT_CustomMenu(bpy.types.Menu):
    bl_label = "Smart_Select"
    bl_idname = "FRO_MT_custom_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator('kro.smart_select_36c8d', text='Smart Select', icon='SHADERFX')
        layout.operator('kro.select_after_dd961', text='Select After', icon='FORWARD')
        layout.operator('kro.select_before_96bb3', text='Select Before', icon='BACK')
        layout.operator('kro.select_after_before_a83f0', text='Select After/Before', icon='CENTER_ONLY')
        layout.operator('kro.select_all_2af27', text='Select All', icon='ARROW_LEFTRIGHT')


def menu_func_1(self, context):
    self.layout.menu(FRO_MT_CustomMenu.bl_idname)

class FRO_OT_Select_After_Before_A83F0(bpy.types.Operator):
    bl_idname = "kro.select_after_before_a83f0"
    bl_label = "Select_After_Before"
    bl_description = "Select all keyframes in the frame range except the keyframe on the current frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        return execute_in_graph_editor(context, self, self._execute_selection)

    def _execute_selection(self, context):
        """Execute the selection logic in proper Graph Editor context"""
        try:
            
            if bpy.ops.graph.select_all.poll():
                bpy.ops.graph.select_all(action='DESELECT')
            else:
                self.report({'WARNING'}, "Cannot deselect keyframes")
                return {'CANCELLED'}

            channelbag = get_active_channelbag(context)
            if not channelbag:
                self.report({'WARNING'}, "No active channelbag found")
                return {"CANCELLED"}
                
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
            current_frame = context.scene.frame_current
            
            
            for fcurve in channelbag.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if start_frame <= keyframe.co[0] <= end_frame:
                        if keyframe.co[0] != current_frame:
                            keyframe.select_control_point = True

            
            if bpy.ops.graph.view_selected.poll():
                bpy.ops.graph.view_selected()
                
            if bpy.ops.anim.channels_select_all.poll():
                bpy.ops.anim.channels_select_all(action='SELECT')

            return {"FINISHED"}
            
        except Exception as e:
            self.report({'ERROR'}, f"Selection operation failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Select_All_2Af27(bpy.types.Operator):
    bl_idname = "kro.select_all_2af27"
    bl_label = "Select_All"
    bl_description = "select all keyframes in the frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        channelbag = get_active_channelbag(context)
        if not channelbag:
            return {"CANCELLED"}
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                if obj_channelbag:
                    for fc in obj_channelbag.fcurves:
                        for kp in fc.keyframe_points:
                            if context.scene.frame_start <= kp.co[0] <= context.scene.frame_end:
                                kp.select_control_point = True

        if context.active_object and context.active_object.mode == 'POSE':
            if context.area.type != 'GRAPH_EDITOR':
                for area in context.screen.areas:
                    if area.type == 'GRAPH_EDITOR':
                        override = context.copy()
                        override['area'] = area
                        for curve in channelbag.fcurves:
                            curve.select = True
                        bpy.ops.graph.select_all(override, action='DESELECT')
                        for obj in context.selected_objects:
                            if obj.animation_data and obj.animation_data.action:
                                obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                                if obj_channelbag:
                                    for fc in obj_channelbag.fcurves:
                                        for kp in fc.keyframe_points:
                                            if context.scene.frame_start <= kp.co[0] <= context.scene.frame_end:
                                                kp.select_control_point = True
                        bpy.ops.graph.view_selected(override)
                        bpy.ops.anim.channels_select_all(override, action='SELECT')
                        return {"FINISHED"}
                self.report({'WARNING'}, "No Graph Editor found.")
                return {'CANCELLED'}

            for curve in channelbag.fcurves:
                curve.select = True
            bpy.ops.graph.select_all(action='DESELECT')
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                    if obj_channelbag:
                        for fc in obj_channelbag.fcurves:
                            for kp in fc.keyframe_points:
                                if context.scene.frame_start <= kp.co[0] <= context.scene.frame_end:
                                    kp.select_control_point = True

            bpy.ops.graph.view_selected()
            bpy.ops.anim.channels_select_all(action='SELECT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Select_After_Dd961(bpy.types.Operator):
    bl_idname = "kro.select_after_dd961"
    bl_label = "Select_After"
    bl_description = "Select all keyframes after the current frame to the end frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        try:
            channelbag = get_active_channelbag(context)
            if not channelbag:
                return {"CANCELLED"}
                
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
            current_frame = context.scene.frame_current
            
            
            self._deselect_all_keyframes(channelbag)
            
            
            selected_count = 0
            for fcurve in channelbag.fcurves:
                for keyframe in fcurve.keyframe_points:
                    if start_frame <= keyframe.co[0] <= end_frame and keyframe.co[0] > current_frame:
                        keyframe.select_control_point = True
                        selected_count += 1
            
            
            for fcurve in channelbag.fcurves:
                fcurve.select = True
            
            self.report({'INFO'}, f"Selected {selected_count} keyframes")
            return {"FINISHED"}
            
        except Exception as e:
            self.report({'ERROR'}, f"Selection operation failed: {str(e)}")
            return {'CANCELLED'}

    def _deselect_all_keyframes(self, channelbag):
        """Deselect all keyframes in channelbag"""
        for fcurve in channelbag.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.select_control_point = False
                
class FRO_OT_Select_Before_96Bb3(bpy.types.Operator):
    bl_idname = "kro.select_before_96bb3"
    bl_label = "Select_Before"
    bl_description = "Select all keyframes before the current frame to the start frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    bpy.ops.graph.select_all(override, action='DESELECT')
                    channelbag = get_active_channelbag(context)
                    if not channelbag:
                        return {"CANCELLED"}
                    start_frame = context.scene.frame_start
                    end_frame = context.scene.frame_end
                    current_frame = context.scene.frame_current
                    for fcurve in channelbag.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if start_frame <= keyframe.co[0] <= end_frame and keyframe.co[0] < current_frame:
                                keyframe.select_control_point = True
                    bpy.ops.graph.view_selected(override)
                    bpy.ops.anim.channels_select_all(override, action='SELECT')
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        bpy.ops.graph.select_all(action='DESELECT')
        channelbag = get_active_channelbag(context)
        if not channelbag:
            return {"CANCELLED"}
        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end
        current_frame = context.scene.frame_current
        for fcurve in channelbag.fcurves:
            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co[0] <= end_frame and keyframe.co[0] < current_frame:
                    keyframe.select_control_point = True

        bpy.ops.graph.view_selected()
        bpy.ops.anim.channels_select_all(action='SELECT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Smart_Select_36C8D(bpy.types.Operator):
    bl_idname = "kro.smart_select_36c8d"
    bl_label = "Smart_Select"
    bl_description = "select all keyframes in a specific fcurve between the current frame and the selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    current_frame = context.scene.frame_current
                    fcurves = context.selected_editable_fcurves
                    if not fcurves:
                        self.report({'ERROR'}, "No fcurves selected")
                        return {'CANCELLED'}
                    selected_keyframe_frame = next((keyframe.co[0] for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point), None)
                    if selected_keyframe_frame is None:
                        self.report({'ERROR'}, "No keyframes selected")
                        return {'CANCELLED'}
                    for fcurve in fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if min(current_frame, selected_keyframe_frame) <= keyframe.co[0] <= max(current_frame, selected_keyframe_frame):
                                keyframe.select_control_point = True
                            else:
                                keyframe.select_control_point = False
                    bpy.ops.graph.view_selected(override)
                    bpy.ops.anim.channels_select_all(override, action='SELECT')
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        current_frame = context.scene.frame_current
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            self.report({'ERROR'}, "No fcurves selected")
            return {'CANCELLED'}
        selected_keyframe_frame = next((keyframe.co[0] for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point), None)
        if selected_keyframe_frame is None:
            self.report({'ERROR'}, "No keyframes selected")
            return {'CANCELLED'}
        for fcurve in fcurves:
            for keyframe in fcurve.keyframe_points:
                if min(current_frame, selected_keyframe_frame) <= keyframe.co[0] <= max(current_frame, selected_keyframe_frame):
                    keyframe.select_control_point = True
                else:
                    keyframe.select_control_point = False

        bpy.ops.graph.view_selected()
        bpy.ops.anim.channels_select_all(action='SELECT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)










class FrameRangeToolsPopupOperator(bpy.types.Operator):
    bl_idname = "scene.frame_range_tools_popup"
    bl_label = "Frame Range Tools"
    bl_description = "Show all frame range tools in a popup menu"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=200)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Frame Range Tools", icon='PREVIEW_RANGE')
        layout.separator()
        layout.operator(SetupFrameRangePopupOperator.bl_idname, 
                        text="Set Custom Range", 
                        icon='PREVIEW_RANGE')
        
        layout.separator()
        layout.operator(SetFrameRangePopupOperator.bl_idname, 
                        text="Set Range from Current", 
                        icon='RECOVER_LAST')
        
        layout.separator()
        layout.operator(SetFrameRangeFromKeyframesOperator.bl_idname, 
                        text="Set from Selected Keys", 
                        icon='LIGHT_POINT')
        
        layout.separator()
        layout.operator(SetFrameRangeFromCurrentFrameOperator.bl_idname, 
                        text="Set from Current & Keys", 
                        icon='QUIT')
        
        layout.separator()

class SetFrameRangePopupOperator(bpy.types.Operator):
    bl_idname = "scene.set_frame_range_popup"
    bl_label = ""
    bl_description = "Set the frame start and end based on current frame and offset"

    def execute(self, context):
        scene = context.scene
        current_frame = scene.frame_current
        frame_offset_D = scene.frame_Smartoffset_R

        scene.frame_start = current_frame
        scene.frame_end = current_frame + frame_offset_D

        self.report({'INFO'}, f"Start frame set to: {current_frame}, End frame set to: {current_frame + frame_offset_D}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "frame_Smartoffset_R")

class SetupFrameRangePopupOperator(bpy.types.Operator):
    bl_idname = "scene.setup_frame_range_popup"
    bl_label = ""
    bl_description = "Set the frame start and end using custom offset values"

    def execute(self, context):
        scene = context.scene
        frame_start_offset = scene.frame_start_offset
        frame_end_offset = scene.frame_end_offset

        scene.frame_start = frame_start_offset
        scene.frame_end = frame_end_offset

        self.report({'INFO'}, f"Start frame set to: {frame_start_offset}, End frame set to: {frame_end_offset}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "frame_start_offset", text="Frame Start")
        layout.prop(context.scene, "frame_end_offset", text="Frame End")

class SetFrameRangeFromKeyframesOperator(bpy.types.Operator):
    bl_idname = "scene.set_frame_range_from_keyframes"
    bl_label = ""
    bl_description = "Set the frame range based on selected keyframes"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    fcurves = context.selected_editable_fcurves
                    if fcurves:
                        selected_keyframes = [keyframe.co.x for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
                        if selected_keyframes:
                            context.scene.frame_start = int(min(selected_keyframes))
                            context.scene.frame_end = int(max(selected_keyframes))
                            self.report({'INFO'}, f"Start Frame: {context.scene.frame_start}, End Frame: {context.scene.frame_end}")
                        else:
                            self.report({'WARNING'}, "No selected keyframes found.")
                    else:
                        self.report({'WARNING'}, "No selected keyframes found.")
                    return {'FINISHED'}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        fcurves = context.selected_editable_fcurves
        if fcurves:
            selected_keyframes = [keyframe.co.x for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
            if selected_keyframes:
                context.scene.frame_start = int(min(selected_keyframes))
                context.scene.frame_end = int(max(selected_keyframes))
                self.report({'INFO'}, f"Start Frame: {context.scene.frame_start}, End Frame: {context.scene.frame_end}")
            else:
                self.report({'WARNING'}, "No selected keyframes found.")
        else:
            self.report({'WARNING'}, "No selected keyframes found.")
        
        return {'FINISHED'}

class SetFrameRangeFromCurrentFrameOperator(bpy.types.Operator):
    bl_idname = "scene.set_frame_range_from_current_frame"
    bl_label = ""
    bl_description = "Set the frame range based on the current frame and selected keyframe"

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    scene = context.scene
                    current_frame = scene.frame_current
                    fcurves = context.selected_editable_fcurves
                    if fcurves:
                        selected_keyframes = [keyframe for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
                        if selected_keyframes:
                            min_frame = min(keyframe.co.x for keyframe in selected_keyframes)
                            max_frame = max(keyframe.co.x for keyframe in selected_keyframes)
                            scene.frame_start = int(min(current_frame, min_frame))
                            scene.frame_end = int(max(current_frame, max_frame))
                            self.report({'INFO'}, f"Start Frame: {scene.frame_start}, End Frame: {scene.frame_end}")
                        else:
                            self.report({'WARNING'}, "No selected keyframes found.")
                    else:
                        self.report({'WARNING'}, "No selected keyframes found.")
                    return {'FINISHED'}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        scene = context.scene
        current_frame = scene.frame_current
        fcurves = context.selected_editable_fcurves
        if fcurves:
            selected_keyframes = [keyframe for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
            if selected_keyframes:
                min_frame = min(keyframe.co.x for keyframe in selected_keyframes)
                max_frame = max(keyframe.co.x for keyframe in selected_keyframes)
                scene.frame_start = int(min(current_frame, min_frame))
                scene.frame_end = int(max(current_frame, max_frame))
                self.report({'INFO'}, f"Start Frame: {scene.frame_start}, End Frame: {scene.frame_end}")
            else:
                self.report({'WARNING'}, "No selected keyframes found.")
        else:
            self.report({'WARNING'}, "No selected keyframes found.")
        
        return {'FINISHED'}

def menu_func(self, context):
    layout = self.layout
    layout.operator(FrameRangeToolsPopupOperator.bl_idname, 
                    text="", 
                    icon='PREVIEW_RANGE', emboss=False)

    layout.separator()










class FRO_OT_D_Snapkey_A83F0(bpy.types.Operator):
    bl_idname = "kro.d_kropkey_a83f0"
    bl_label = "Snap-key"
    bl_description = "replace the keyframe on current frame with selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        
        has_selected_keyframes = False
        for fcurve in context.selected_editable_fcurves or []:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    has_selected_keyframes = True
                    break
            if has_selected_keyframes:
                break
        
        if not has_selected_keyframes:
            self.report({'WARNING'}, "No keyframes selected to copy")
            return {'CANCELLED'}

        
        return execute_in_graph_editor(context, self, self._execute_copy_paste)

    def _execute_copy_paste(self, context):
        """Execute copy-paste operations with proper context"""
        try:
            
            if bpy.ops.graph.copy.poll():
                bpy.ops.graph.copy()
            else:
                self.report({'ERROR'}, "Cannot copy keyframes")
                return {'CANCELLED'}

            
            if bpy.ops.graph.paste.poll():
                bpy.ops.graph.paste()
            else:
                self.report({'ERROR'}, "Cannot paste keyframes")
                return {'CANCELLED'}

            return {"FINISHED"}
        except Exception as e:
            self.report({'ERROR'}, f"Copy-paste operation failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Smart_Select_Dd961(bpy.types.Operator):
    bl_idname = "kro.smart_select_dd961"
    bl_label = "Smart_Select"
    bl_description = "select a specific axis between start and end frame range and focus on it"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        return execute_in_graph_editor(context, self, self._execute_logic)

    def _execute_logic(self, context):
        """Simplified execution logic"""
        try:
            
            selected_fcurves = context.selected_editable_fcurves
            if not selected_fcurves:
                self.report({'WARNING'}, "No F-Curves selected")
                return {'CANCELLED'}
            
            bpy.ops.graph.select_linked()
            bpy.ops.graph.hide(unselected=True)
            
            
            self._select_keyframes_in_range(context)
            
            return {"FINISHED"}
        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {str(e)}")
            return {'CANCELLED'}

    def _select_keyframes_in_range(self, context):
        """Helper method for keyframe selection"""
        scene = context.scene
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        
        bpy.ops.graph.select_all(action='DESELECT')
        
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(
                    obj.animation_data.action, 
                    obj.animation_data.action_slot
                )
                if obj_channelbag:
                    for fc in obj_channelbag.fcurves:
                        for kp in fc.keyframe_points:
                            if start_frame <= kp.co[0] <= end_frame:
                                kp.select_control_point = True

    def invoke(self, context, event):
        return self.execute(context)
    
class FRO_OT_Move_Keyframe_96Bb3(bpy.types.Operator):
    bl_idname = "kro.move_keyframe_96bb3"
    bl_label = "Move Keyframe"
    bl_description = "Move the selected keyframes to the current frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None and has_selected_keyframes(context)

    def execute(self, context):
        try:
            current_frame = context.scene.frame_current
            
            
            selected_frames = []
            for fcurve in context.selected_editable_fcurves or []:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.select_control_point:
                        selected_frames.append(keyframe.co.x)
            
            if not selected_frames:
                self.report({'WARNING'}, "No keyframes selected to move")
                return {'CANCELLED'}
            
            
            reference_frame = min(selected_frames)
            frame_offset = current_frame - reference_frame
            
            
            for fcurve in context.selected_editable_fcurves or []:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.select_control_point:
                        keyframe.co.x += frame_offset
                        
                        keyframe.handle_left.x += frame_offset
                        keyframe.handle_right.x += frame_offset
                
                
                fcurve.update()
            
            self.report({'INFO'}, f"Moved {len(selected_frames)} keyframes to frame {current_frame}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Move operation failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Select_Group_36C8D(bpy.types.Operator):
    bl_idname = "kro.select_group_36c8d"
    bl_label = "select_group"
    bl_description = "select all keyframes between the current frame and the selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        
        graph_editor_area = None
        if context.area and context.area.type == 'GRAPH_EDITOR':
            graph_editor_area = context.area
        else:
            
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    graph_editor_area = area
                    break
        
        if not graph_editor_area:
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        
        with context.temp_override(
            area=graph_editor_area,
            region=next((r for r in graph_editor_area.regions if r.type == 'WINDOW'), None),
            space_data=graph_editor_area.spaces.active
        ):
            return self._execute_in_graph_editor(context)

    def _execute_in_graph_editor(self, context):
        """Execute the actual logic with proper Graph Editor context"""
        scene = context.scene
        original_start_frame = scene.frame_start
        original_end_frame = scene.frame_end
        
        current_frame = scene.frame_current
        fcurves = context.selected_editable_fcurves
        
        if fcurves:
            selected_keyframes = [keyframe for fcurve in fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
            if selected_keyframes:
                min_frame = min(keyframe.co.x for keyframe in selected_keyframes)
                max_frame = max(keyframe.co.x for keyframe in selected_keyframes)
                if min_frame is not None and max_frame is not None:
                    start_frame = min(current_frame, min_frame)
                    end_frame = max(current_frame, max_frame)
                    
                    scene.frame_start = int(start_frame)
                    scene.frame_end = int(end_frame)
        
        
        bpy.ops.graph.select_all(action='DESELECT')
        bpy.ops.graph.reveal()
        bpy.ops.anim.channels_setting_disable(type='MUTE')
        bpy.ops.anim.channels_setting_disable(type='PROTECT')

        if context.active_object and context.active_object.mode == 'POSE':
            active_obj = context.active_object
            if active_obj and active_obj.animation_data and active_obj.animation_data.action:
                for curve in get_active_channelbag(context).fcurves:
                    curve.select = True
            bpy.ops.graph.select_all(action='DESELECT')
            start_frame = scene.frame_start
            end_frame = scene.frame_end
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                    if obj_channelbag:
                        for fc in obj_channelbag.fcurves:
                            for kp in fc.keyframe_points:
                                if start_frame <= kp.co[0] <= end_frame:
                                    kp.select_control_point = True
        bpy.ops.anim.channels_select_all(action='SELECT')


        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def has_selected_keyframes(context):
    """Check if there are any selected keyframes in editable fcurves"""
    if not context.selected_editable_fcurves:
        return False
    
    for fcurve in context.selected_editable_fcurves:
        for keyframe in fcurve.keyframe_points:
            if keyframe.select_control_point:
                return True
    return False

def execute_in_graph_editor(context, operator, execute_function):
    """Helper to execute functions in Graph Editor context with proper error handling"""
    
    if context.area and context.area.type == 'GRAPH_EDITOR':
        try:
            return execute_function(context)
        except Exception as e:
            operator.report({'ERROR'}, f"Operation failed: {str(e)}")
            return {'CANCELLED'}
    
    
    graph_editor_area = None
    for area in context.screen.areas:
        if area.type == 'GRAPH_EDITOR':
            graph_editor_area = area
            break
    
    if not graph_editor_area:
        operator.report({'WARNING'}, "No Graph Editor found. Please open a Graph Editor window.")
        return {'CANCELLED'}
    
    try:
        
        region = next((r for r in graph_editor_area.regions if r.type == 'WINDOW'), None)
        space_data = graph_editor_area.spaces.active
        
        if not region:
            operator.report({'ERROR'}, "Could not find WINDOW region in Graph Editor")
            return {'CANCELLED'}
        
        
        override = {
            'window': context.window,
            'screen': context.screen,
            'area': graph_editor_area,
            'region': region,
            'scene': context.scene,
            'space_data': space_data
        }
        
        
        with context.temp_override(**override):
            return execute_function(context)
            
    except Exception as e:
        operator.report({'ERROR'}, f"Context setup failed: {str(e)}")
        return {'CANCELLED'}










class FRO_OT_Jump_To_Endpiont_451B5(bpy.types.Operator):
    bl_idname = "kro.jump_to_endpiont_451b5"
    bl_label = "jump to endpiont"
    bl_description = "jump to end frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    bpy.ops.screen.frame_jump(override, end=False)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        bpy.ops.screen.frame_jump(end=False)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Jump_To_Keyframe_802E7(bpy.types.Operator):
    bl_idname = "kro.jump_to_keyframe_802e7"
    bl_label = "Jump to keyframe"
    bl_description = "Jump to previous keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        scene = context.scene
        selected_obj = context.object
        if not selected_obj:
            print("No object selected.")
            return {"CANCELLED"}
        
        keyframes = set()
        channelbag = get_active_channelbag(context)
        if channelbag:
            for fcurve in channelbag.fcurves:
                keyframes.update(int(kf.co[0]) for kf in fcurve.keyframe_points)
        
        sorted_keyframes = sorted(keyframes, reverse=True)
        current_frame = scene.frame_current
        previous_keyframe = None
        for kf in sorted_keyframes:
            if kf < current_frame:
                previous_keyframe = kf
                break
        
        if previous_keyframe is not None:
            scene.frame_set(previous_keyframe)
        else:
            print("No previous keyframe found for the selected object.")
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Play_Animation_F_11B2C(bpy.types.Operator):
    bl_idname = "kro.play_animation_f_11b2c"
    bl_label = "Play Animation f"
    bl_description = "Play Animation forward"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        scene = context.scene
        selected_obj = context.object
        if not selected_obj:
            print("No object selected.")
            return {"CANCELLED"}
        
        keyframes = set()
        channelbag = get_active_channelbag(context)
        if channelbag:
            for fcurve in channelbag.fcurves:
                keyframes.update(int(kf.co[0]) for kf in fcurve.keyframe_points)
        
        sorted_keyframes = sorted(keyframes)
        current_frame = scene.frame_current
        next_keyframe = None
        for kf in sorted_keyframes:
            if kf > current_frame:
                next_keyframe = kf
                break
        
        if next_keyframe is not None:
            scene.frame_set(next_keyframe)
        else:
            print("No next keyframe found for the selected object.")
        
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Move_To_End_220Ca(bpy.types.Operator):
    bl_idname = "kro.move_to_end_220ca"
    bl_label = "move_to_end"
    bl_description = "jump to the end range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        end_frame = scene.frame_end
        scene.frame_set(end_frame)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)










class FRO_OT_Jessica_D_D23F9(bpy.types.Operator):
    bl_idname = "kro.jessica_d_d23f9"
    bl_label = "Jessica_D"
    bl_description = "Delete unselected or unmarked keyframes in the frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    start_frame = context.scene.frame_start
                    end_frame = context.scene.frame_end
                    if context.scene.timeline_markers:
                        for marker in context.scene.timeline_markers:
                            if start_frame <= marker.frame <= end_frame:
                                marker.select = True
                    bpy.ops.graph.select_column(override, mode='MARKERS_COLUMN')
                    bpy.ops.graph.select_all(override, action='INVERT')
                    for fcurve in context.selected_editable_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            frame = keyframe.co.x
                            if frame < start_frame or frame > end_frame:
                                keyframe.select_control_point = False
                                keyframe.select_left_handle = False
                                keyframe.select_right_handle = False
                    bpy.ops.graph.delete(override)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end
        if context.scene.timeline_markers:
            for marker in context.scene.timeline_markers:
                if start_frame <= marker.frame <= end_frame:
                    marker.select = True
        bpy.ops.graph.select_column(mode='MARKERS_COLUMN')
        bpy.ops.graph.select_all(action='INVERT')
        for fcurve in context.selected_editable_fcurves:
            for keyframe in fcurve.keyframe_points:
                frame = keyframe.co.x
                if frame < start_frame or frame > end_frame:
                    keyframe.select_control_point = False
                    keyframe.select_left_handle = False
                    keyframe.select_right_handle = False
        bpy.ops.graph.delete()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Delete_Out_43A9B(bpy.types.Operator):
    bl_idname = "kro.delete_out_43a9b"
    bl_label = "Delete_Out"
    bl_description = "Delete all keyframes that out of the frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    if context.active_object and context.active_object.mode == 'POSE':
                        active_obj = context.active_object
                        if active_obj and active_obj.animation_data and active_obj.animation_data.action:
                            for curve in get_active_channelbag(context).fcurves:
                                curve.select = True
                        bpy.ops.graph.select_all(override, action='DESELECT')
                        scene = context.scene
                        start_frame = scene.frame_start
                        end_frame = scene.frame_end
                        for obj in context.selected_objects:
                            if obj.animation_data and obj.animation_data.action:
                                obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                                if obj_channelbag:
                                    for fc in obj_channelbag.fcurves:
                                        for kp in fc.keyframe_points:
                                            if start_frame <= kp.co[0] <= end_frame:
                                                kp.select_control_point = True
                    bpy.ops.graph.select_all(override, action='INVERT')
                    bpy.ops.graph.delete(override)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        if context.active_object and context.active_object.mode == 'POSE':
            active_obj = context.active_object
            if active_obj and active_obj.animation_data and active_obj.animation_data.action:
                for curve in get_active_channelbag(context).fcurves:
                    curve.select = True
            bpy.ops.graph.select_all(action='DESELECT')
            scene = context.scene
            start_frame = scene.frame_start
            end_frame = scene.frame_end
            for obj in context.selected_objects:
                if obj.animation_data and obj.animation_data.action:
                    obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                    if obj_channelbag:
                        for fc in obj_channelbag.fcurves:
                            for kp in fc.keyframe_points:
                                if start_frame <= kp.co[0] <= end_frame:
                                    kp.select_control_point = True
        bpy.ops.graph.select_all(action='INVERT')
        bpy.ops.graph.delete()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)










class FRO_OT_Delete_Marker_159B9(bpy.types.Operator):
    bl_idname = "kro.delete_marker_159b9"
    bl_label = "Delete Marker"
    bl_description = "Delete all selected markers"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'GRAPH_EDITOR' and context.scene.timeline_markers

    def execute(self, context):
        bpy.ops.marker.delete(confirm=False)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Delete_Marker_Key_Bea06(bpy.types.Operator):
    bl_idname = "kro.delete_marker_key_bea06"
    bl_label = "Delete_marker_key"
    bl_description = "Delete marker keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    bpy.ops.graph.select_all(override, action='DESELECT')
                    start_frame = context.scene.frame_start
                    end_frame = context.scene.frame_end
                    if context.scene.timeline_markers:
                        for marker in context.scene.timeline_markers:
                            if start_frame <= marker.frame <= end_frame:
                                marker.select = True
                    bpy.ops.graph.select_column(override, mode='MARKERS_COLUMN')
                    for fcurve in context.selected_editable_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            frame = keyframe.co.x
                            if frame < start_frame or frame > end_frame:
                                keyframe.select_control_point = False
                                keyframe.select_left_handle = False
                                keyframe.select_right_handle = False
                    bpy.ops.graph.delete(override)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        bpy.ops.graph.select_all(action='DESELECT')
        start_frame = context.scene.frame_start
        end_frame = context.scene.frame_end
        if context.scene.timeline_markers:
            for marker in context.scene.timeline_markers:
                if start_frame <= marker.frame <= end_frame:
                    marker.select = True
        bpy.ops.graph.select_column(mode='MARKERS_COLUMN')
        for fcurve in context.selected_editable_fcurves:
            for keyframe in fcurve.keyframe_points:
                frame = keyframe.co.x
                if frame < start_frame or frame > end_frame:
                    keyframe.select_control_point = False
                    keyframe.select_left_handle = False
                    keyframe.select_right_handle = False
        bpy.ops.graph.delete()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Delete_Between_2Af27(bpy.types.Operator):
    bl_idname = "kro.delete_between_2af27"
    bl_label = "Delete_between"
    bl_description = "Reducing the number of keyframes while preserving the shape of the fcurve"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        bpy.context.area.type = 'GRAPH_EDITOR'
        original_start_frame = bpy.context.scene.frame_start
        original_end_frame = bpy.context.scene.frame_end
        selected_fcurves = bpy.context.selected_editable_fcurves
        if selected_fcurves:
            selected_keyframes = [
                keyframe.co.x 
                for fcurve in selected_fcurves 
                for keyframe in fcurve.keyframe_points 
                if keyframe.select_control_point
            ]
            if selected_keyframes:
                bpy.context.scene.frame_start = int(min(selected_keyframes))
                bpy.context.scene.frame_end = int(max(selected_keyframes))
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end
        selected_keyframes = bpy.context.selected_editable_fcurves
        try:
            for fcurve in selected_keyframes:
                for keyframe in fcurve.keyframe_points:
                    frame = keyframe.co.x
                    if frame > start_frame and frame < end_frame:
                        fcurve.keyframe_points.remove(keyframe)
        except RuntimeError:
            pass
        bpy.context.scene.frame_start = original_start_frame
        bpy.context.scene.frame_end = original_end_frame
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Delete_Selected_D235E(bpy.types.Operator):
    bl_idname = "kro.delete_selected_d235e"
    bl_label = "Delete_selected"
    bl_description = "delete selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        
        has_selection = any(
            keyframe.select_control_point 
            for fcurve in context.selected_editable_fcurves or [] 
            for keyframe in fcurve.keyframe_points
        )
        
        if not has_selection:
            self.report({'WARNING'}, "No keyframes selected to delete")
            return {'CANCELLED'}

        return execute_in_graph_editor(context, self, self._execute_delete)

    def _execute_delete(self, context):
        """Execute delete operation"""
        try:
            if bpy.ops.graph.delete.poll():
                bpy.ops.graph.delete()
                return {"FINISHED"}
            else:
                self.report({'ERROR'}, "Cannot delete keyframes in current context")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Delete operation failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Delet_Channel_F0C68(bpy.types.Operator):
    bl_idname = "kro.delet_channel_f0c68"
    bl_label = "delet_channel"
    bl_description = "delete channel that doesn't have any animation data"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    active_bone = context.active_pose_bone
                    if active_bone:
                        action = active_bone.id_data.animation_data.action
                        if action:
                            fcurves_to_remove = [channel for channel in get_active_channelbag(context).fcurves if not channel.keyframe_points]
                            for channel in fcurves_to_remove:
                                get_active_channelbag(context).fcurves.remove(channel)
                    for obj in context.selected_objects:
                        if obj.animation_data and obj.animation_data.action:
                            obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                            if obj_channelbag:
                                fcurves_to_remove = []
                                for fcurve in obj_channelbag.fcurves:
                                    keyframes = fcurve.keyframe_points
                                    if not keyframes:
                                        continue
                                    first_value = keyframes[0].co.y
                                    if all(keyframe.co.y == first_value for keyframe in keyframes[1:]):
                                        fcurves_to_remove.append(fcurve)
                                for fcurve in fcurves_to_remove:
                                    obj_channelbag.fcurves.remove(fcurve)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        active_bone = context.active_pose_bone
        if active_bone:
            action = active_bone.id_data.animation_data.action
            if action:
                fcurves_to_remove = [channel for channel in get_active_channelbag(context).fcurves if not channel.keyframe_points]
                for channel in fcurves_to_remove:
                    get_active_channelbag(context).fcurves.remove(channel)
        for obj in context.selected_objects:
            if obj.animation_data and obj.animation_data.action:
                obj_channelbag = anim_utils.action_ensure_channelbag_for_slot(obj.animation_data.action, obj.animation_data.action_slot)
                if obj_channelbag:
                    fcurves_to_remove = []
                    for fcurve in obj_channelbag.fcurves:
                        keyframes = fcurve.keyframe_points
                        if not keyframes:
                            continue
                        first_value = keyframes[0].co.y
                        if all(keyframe.co.y == first_value for keyframe in keyframes[1:]):
                            fcurves_to_remove.append(fcurve)
                    for fcurve in fcurves_to_remove:
                        obj_channelbag.fcurves.remove(fcurve)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)











class FRO_OT_Add_Mark_31C1F(bpy.types.Operator):
    bl_idname = "kro.add_mark_31c1f"
    bl_label = "Add_Mark"
    bl_description = "Add marker for each selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    selected_fcurves = context.selected_editable_fcurves
                    selected_keyframe_count = 0
                    for fcurve in selected_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.select_control_point:
                                selected_keyframe_count += 1
                                marker = context.scene.timeline_markers.new(name=f"key_{selected_keyframe_count}")
                                marker.frame = int(keyframe.co.x)
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        selected_fcurves = context.selected_editable_fcurves
        selected_keyframe_count = 0
        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    selected_keyframe_count += 1
                    marker = context.scene.timeline_markers.new(name=f"key_{selected_keyframe_count}")
                    marker.frame = int(keyframe.co.x)
        print("Markers have been added for all selected keyframes.")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Sellect_Marks_E5Cea(bpy.types.Operator):
    bl_idname = "kro.sellect_marks_e5cea"
    bl_label = "sellect_marks"
    bl_description = "select all marks in the frame range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if context.area.type == 'GRAPH_EDITOR':
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
            if context.scene.timeline_markers:
                for marker in context.scene.timeline_markers:
                    if start_frame <= marker.frame <= end_frame:
                        marker.select = True
            else:
                print("No markers found.")
        else:
            print("The active window is not the Graph Editor.")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Number_Mark_A7Fb5(bpy.types.Operator):
    bl_idname = "kro.number_mark_a7fb5"
    bl_label = "Number_mark"
    bl_description = "calculate the number of frame between selected keyframe"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    selected_fcurves = context.selected_editable_fcurves
                    previous_frame = None
                    for fcurve in selected_fcurves:
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.select_control_point:
                                if previous_frame is not None:
                                    frame_diff = keyframe.co.x - previous_frame
                                    marker_name = f"{frame_diff:.2f}"
                                else:
                                    marker_name = "First_Key"
                                marker = context.scene.timeline_markers.new(name=marker_name)
                                marker.frame = int(keyframe.co.x)
                                previous_frame = keyframe.co.x
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        selected_fcurves = context.selected_editable_fcurves
        previous_frame = None
        for fcurve in selected_fcurves:
            for keyframe in fcurve.keyframe_points:
                if keyframe.select_control_point:
                    if previous_frame is not None:
                        frame_diff = keyframe.co.x - previous_frame
                        marker_name = f"{frame_diff:.2f}"
                    else:
                        marker_name = "First_Key"
                    marker = context.scene.timeline_markers.new(name=marker_name)
                    marker.frame = int(keyframe.co.x)
                    previous_frame = keyframe.co.x
        print("Markers with frame difference names have been added.")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)










class FRO_OT_Quick_Noise_Ef272(bpy.types.Operator):
    bl_idname = "kro.quick_noise_ef272"
    bl_label = "Quick_Noise"
    bl_description = "Add a Noise modifier to the selected keyframes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return get_active_channelbag(context) is not None

    def execute(self, context):
        if context.area.type != 'GRAPH_EDITOR':
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    override = context.copy()
                    override['area'] = area
                    active_bone = context.active_pose_bone
                    if active_bone:
                        if context.selected_editable_fcurves:
                            selected_keyframes = [keyframe.co.x for fcurve in context.selected_editable_fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
                            selected_fcurves = context.selected_editable_fcurves
                            for fcurve in selected_fcurves:
                                bpy.ops.graph.fmodifier_add(override, type='NOISE')
                                modifier = fcurve.modifiers[-1]
                                modifier.strength = 0.3
                                modifier.scale = 0.5
                                modifier.phase = 0
                                modifier.use_restricted_range = True
                                modifier.frame_start = int(min(selected_keyframes))
                                modifier.frame_end = int(max(selected_keyframes))
                    return {"FINISHED"}
            self.report({'WARNING'}, "No Graph Editor found.")
            return {'CANCELLED'}

        active_bone = context.active_pose_bone
        if active_bone:
            print("Active Bone:", active_bone.name)
            
            if context.selected_editable_fcurves:
                
                selected_keyframes = [keyframe.co.x for fcurve in context.selected_editable_fcurves for keyframe in fcurve.keyframe_points if keyframe.select_control_point]
                
                selected_fcurves = context.selected_editable_fcurves
                
                for fcurve in selected_fcurves:
                    bpy.ops.graph.fmodifier_add(type='NOISE')
                    modifier = fcurve.modifiers[-1]
                    modifier.strength = 0.3
                    modifier.scale = 0.5
                    modifier.phase = 0
                    modifier.use_restricted_range = True
                    
                    modifier.frame_start = int(min(selected_keyframes))
                    
                    modifier.frame_end = int(max(selected_keyframes))
                print("Noise modifier added to the selected F-Curves. Start and end frames set.")
            else:
                print("No selected keyframes.")
        else:
            print("No active bone.")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)












class FRO_OT_Toggle_Editor_Buttons(bpy.types.Operator):
    bl_idname = "kro.toggle_editor_buttons"
    bl_label = "Toggle Editor Buttons"
    bl_description = "Show/Hide editor buttons"
    bl_options = {"REGISTER"}

    def execute(self, context):
        wm = context.window_manager
        wm.kro_show_editor_buttons = not wm.kro_show_editor_buttons
        return {'FINISHED'}

class FRO_OT_Time_Line_76Ffa(bpy.types.Operator):
    bl_idname = "kro.time_line_76ffa"
    bl_label = "Time_Line"
    bl_description = "Switch to time line window"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        current_area = context.area
        current_screen = context.screen
        
        if current_area is None:
            print("No area found")
        else:
            
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0)  
            
            new_area = next((area for area in current_screen.areas if area != current_area and area.type == current_area.type), None)
            
            if new_area is None:
                print("New area not found after split")
            else:
                
                new_area.type = 'DOPESHEET_EDITOR'
                
                for space in new_area.spaces:
                    if space.type == 'DOPESHEET_EDITOR':
                        space.mode = 'TIMELINE'
                        break
                print("Split and setup complete")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Nla_Window_18De2(bpy.types.Operator):
    bl_idname = "kro.nla_window_18de2"
    bl_label = "NLA_Window"
    bl_description = "Switch to NLA window"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        current_area = context.area
        current_screen = context.screen
        
        if current_area is None:
            print("No area found")
        else:
            
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=1)  
            
            new_area = next((area for area in current_screen.areas if area != current_area and area.type == current_area.type), None)
            
            if new_area is None:
                print("New area not found after split")
            else:
                
                new_area.type = 'NLA_EDITOR'
        print("Split and setup complete")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class FRO_OT_Action_Editor_5E054(bpy.types.Operator):
    bl_idname = "kro.action_editor_5e054"
    bl_label = "Action_Editor"
    bl_description = "Switch to action editor window"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        current_area = context.area
        current_screen = context.screen
        
        if current_area is None:
            print("No area found")
        else:
            
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=1)  
            
            new_area = next((area for area in current_screen.areas if area != current_area and area.type == current_area.type), None)
            
            if new_area is None:
                print("New area not found after split")
            else:
                
                new_area.type = 'DOPESHEET_EDITOR'
                
                for space in new_area.spaces:
                    if space.type == 'DOPESHEET_EDITOR':
                        space.ui_mode = 'ACTION'
        print("Split and setup complete")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)



class GRAPH_OT_reload_all_icons(bpy.types.Operator):
    bl_idname = "graph.reload_all_icons"
    bl_label = "Reload All Missing Icons"
    bl_description = "Reload all missing icons in the add-on"

    def execute(self, context):
        global _icons

        
        if _icons is not None:
            bpy.utils.previews.remove(_icons)
        _icons = bpy.utils.previews.new()

        icon_names = [
            'Tomato.png', 'click.png', 'arrows.png', 'Farqw.png', 'Vawloi.png',
            'Qutdxqcq.png', 'Defaultrio.png', 'Delete key.png', 'spoertylem1.png',
            'Ethel.png', 'Sopqt.png', 'hamdi.png', 'black-hole.png' ,'Bread.png'
        ]

        icon_directory = os.path.join(os.path.dirname(__file__), "icons")  

        if not os.path.isdir(icon_directory):
            self.report({'WARNING'}, "Icon directory not found")
            return {'CANCELLED'}

        for icon_name in icon_names:
            icon_path = os.path.join(icon_directory, icon_name)
            
            
            if os.path.isfile(icon_path):
                _icons.load(icon_name, icon_path, 'IMAGE')
            else:
                self.report({'WARNING'}, f"Icon not found: {icon_name}")

        self.report({'INFO'}, "All icons reloaded successfully")
        return {'FINISHED'}


def kro_add_to_graph_mt_editor_menus_F5DA3(self, context):
    wm = context.window_manager
    layout = self.layout
    
    
    box_toggle = layout.box()
    box_toggle.scale_x = 1.3
    box_toggle.scale_y = 1.0
    icon = 'HIDE_OFF' if wm.kro_show_editor_buttons else 'HIDE_ON'
    box_toggle.operator("kro.toggle_editor_buttons", text="", 
                        icon=icon, emboss=False, 
                        depress=wm.kro_show_editor_buttons)

    if wm.kro_show_editor_buttons:
        layout.operator("graph.reload_all_icons", text="", icon='FILE_REFRESH')

        box_action = layout.box()
        box_action.scale_x = 1.35
        box_action.scale_y = 1.0
        box_action.operator('kro.action_editor_5e054', text='', 
                            icon='ACTION', emboss=False, depress=False)
        
        
        box_timeline = layout.box()
        box_timeline.scale_x = 1.3
        box_timeline.scale_y = 1.0
        box_timeline.operator('kro.time_line_76ffa', text='', 
                              icon='TIME', emboss=False, depress=False)
        
        
        box_nla = layout.box()
        box_nla.scale_x = 1.3
        box_nla.scale_y = 1.0
        box_nla.operator('kro.nla_window_18de2', text='', 
                         icon='NLA', emboss=False, depress=False)


def kro_add_to_graph_mt_editor_menus_32A6D(self, context):
    
    layout = self.layout
    scene = context.scene
    tool_settings = context.tool_settings    
    screen = context.screen
    if not (False):

        op = layout.operator('kro.smart_select_dd961', text='', icon_value=_icons['click.png'].icon_id, emboss=True, depress=False)
        box_8C66B = layout.box()
        box_8C66B.alert = False
        box_8C66B.enabled = True
        box_8C66B.active = True
        box_8C66B.use_property_split = False
        box_8C66B.use_property_decorate = False
        box_8C66B.alignment = 'Center'.upper()
        box_8C66B.scale_x = 1.2999999523162842
        box_8C66B.scale_y = 1.0
        box_8C66B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_8C66B.operator('kro.select_group_36c8d', text='', icon_value=_icons['Tomato.png'].icon_id, emboss=True, depress=False)
        layout.separator(factor=1.0)
        box_15374 = layout.box()
        box_15374.alert = False
        box_15374.enabled = True
        box_15374.active = True
        box_15374.use_property_split = False
        box_15374.use_property_decorate = False
        box_15374.alignment = 'Center'.upper()
        box_15374.scale_x = 1.2999999523162842
        box_15374.scale_y = 1.0
        box_15374.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_15374.operator('kro.move_keyframe_96bb3', text='', icon_value=_icons['arrows.png'].icon_id, emboss=False, depress=False)
        box_9276E = layout.box()
        box_9276E.alert = False
        box_9276E.enabled = True
        box_9276E.active = True
        box_9276E.use_property_split = False
        box_9276E.use_property_decorate = False
        box_9276E.alignment = 'Center'.upper()
        box_9276E.scale_x = 1.2999999523162842
        box_9276E.scale_y = 1.0
        box_9276E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_9276E.operator('kro.d_kropkey_a83f0', text='', icon_value=_icons['Farqw.png'].icon_id, emboss=False, depress=False)
        layout.separator(factor=1.0)
        box_18143 = layout.box()
        box_18143.alert = False
        box_18143.enabled = True
        box_18143.active = True
        box_18143.use_property_split = False
        box_18143.use_property_decorate = False
        box_18143.alignment = 'Expand'.upper()
        box_18143.scale_x = 1.2999999523162842
        box_18143.scale_y = 1.0
        box_18143.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_18143.operator('graph.blend_to_ease', text='', icon_value=_icons['Vawloi.png'].icon_id, emboss=True, depress=False)
        box_BF414 = layout.box()
        box_BF414.alert = False
        box_BF414.enabled = True
        box_BF414.active = True
        box_BF414.use_property_split = False
        box_BF414.use_property_decorate = False
        box_BF414.alignment = 'Expand'.upper()
        box_BF414.scale_x = 1.2999999523162842
        box_BF414.scale_y = 1.0
        box_BF414.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_BF414.operator('graph.push_pull', text='', icon_value=_icons['Qutdxqcq.png'].icon_id, emboss=False, depress=False)
        box_8272D = layout.box()
        box_8272D.alert = False
        box_8272D.enabled = True
        box_8272D.active = True
        box_8272D.use_property_split = False
        box_8272D.use_property_decorate = False
        box_8272D.alignment = 'Expand'.upper()
        box_8272D.scale_x = 1.2999999523162842
        box_8272D.scale_y = 1.0
        box_8272D.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_8272D.operator('graph.blend_to_default', text='', icon_value=_icons['Defaultrio.png'].icon_id, emboss=True, depress=False)
   


        layout.separator(factor=1.0)
        layout.prop(context.scene, "frame_current", text="")
            
  

        row = layout.row(align=True)
        row.prop(tool_settings, "use_keyframe_insert_auto", text="", toggle=True)
        sub = row.row(align=True)
        sub.active = tool_settings.use_keyframe_insert_auto
        layout.separator_spacer()

        box_3CED6 = layout.box()
        box_3CED6.alert = False
        box_3CED6.enabled = True
        box_3CED6.active = True
        box_3CED6.use_property_split = False
        box_3CED6.use_property_decorate = False
        box_3CED6.alignment = 'Expand'.upper()
        box_3CED6.scale_x = 1.2400000095367432
        box_3CED6.scale_y = 1.0
        box_3CED6.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_3CED6.operator('kro.jump_to_endpiont_451b5', text='', icon='TRIA_LEFT_BAR', emboss=True, depress=False)
        box_EFCF2 = layout.box()
        box_EFCF2.alert = False
        box_EFCF2.enabled = True
        box_EFCF2.active = True
        box_EFCF2.use_property_split = False
        box_EFCF2.use_property_decorate = False
        box_EFCF2.alignment = 'Expand'.upper()
        box_EFCF2.scale_x = 1.2999999523162842
        box_EFCF2.scale_y = 1.0
        box_EFCF2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_EFCF2.operator('kro.jump_to_keyframe_802e7', text='', icon='PREV_KEYFRAME', emboss=False, depress=False)
        box_DFCA7 = layout.box()
        box_DFCA7.alert = False
        box_DFCA7.enabled = True
        box_DFCA7.active = True
        box_DFCA7.use_property_split = False
        box_DFCA7.use_property_decorate = False
        box_DFCA7.alignment = 'Expand'.upper()
        box_DFCA7.scale_x = 1.0
        box_DFCA7.scale_y = 1.0
        row = layout.row(align=True)

        if not screen.is_animation_playing:
            row.operator("screen.animation_play", text="", icon="PLAY_REVERSE").reverse = True
            row.operator("screen.animation_play", text="", icon="PLAY")
        else:
            row.scale_x = 1.43
            row.operator("screen.animation_play", text="", icon="PAUSE")

        box_EF2DC = layout.box()
        box_EF2DC.alert = False
        box_EF2DC.enabled = True
        box_EF2DC.active = True
        box_EF2DC.use_property_split = False
        box_EF2DC.use_property_decorate = False
        box_EF2DC.alignment = 'Expand'.upper()
        box_EF2DC.scale_x = 1.0
        box_EF2DC.scale_y = 1.0
        box_EF2DC.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_EF2DC.operator('kro.play_animation_f_11b2c', text='', icon='NEXT_KEYFRAME', emboss=False, depress=False)
        box_13B41 = layout.box()
        box_13B41.alert = False
        box_13B41.enabled = True
        box_13B41.active = True
        box_13B41.use_property_split = False
        box_13B41.use_property_decorate = False
        box_13B41.alignment = 'Expand'.upper()
        box_13B41.scale_x = 1.0
        box_13B41.scale_y = 1.0
        box_13B41.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_13B41.operator('kro.move_to_end_220ca', text='', icon='TRIA_RIGHT_BAR', emboss=True, depress=False)
        layout.separator(factor=1.0)
        box_CCB12 = layout.box()
        box_CCB12.alert = True
        box_CCB12.enabled = True
        box_CCB12.active = True
        box_CCB12.use_property_split = False
        box_CCB12.use_property_decorate = False
        box_CCB12.alignment = 'Center'.upper()
        box_CCB12.scale_x = 1.2999999523162842
        box_CCB12.scale_y = 1.0
        box_CCB12.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_CCB12.operator('kro.delete_between_2af27', text='', icon='X', emboss=True, depress=False)
        box_71C97 = layout.box()
        box_71C97.alert = False
        box_71C97.enabled = True
        box_71C97.active = True
        box_71C97.use_property_split = False
        box_71C97.use_property_decorate = False
        box_71C97.alignment = 'Center'.upper()
        box_71C97.scale_x = 1.2999999523162842
        box_71C97.scale_y = 1.0
        box_71C97.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_71C97.operator('kro.delete_selected_d235e', text='', icon_value=_icons['Delete key.png'].icon_id, emboss=True, depress=False)
        box_3770E = layout.box()
        box_3770E.alert = False
        box_3770E.enabled = True
        box_3770E.active = True
        box_3770E.use_property_split = False
        box_3770E.use_property_decorate = False
        box_3770E.alignment = 'Center'.upper()
        box_3770E.scale_x = 1.2999999523162842
        box_3770E.scale_y = 1.0
        box_3770E.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_3770E.operator('kro.jessica_d_d23f9', text='', icon_value=_icons['spoertylem1.png'].icon_id, emboss=False, depress=False)
        box_0CFD2 = layout.box()
        box_0CFD2.alert = False
        box_0CFD2.enabled = True
        box_0CFD2.active = True
        box_0CFD2.use_property_split = False
        box_0CFD2.use_property_decorate = False
        box_0CFD2.alignment = 'Center'.upper()
        box_0CFD2.scale_x = 1.2999999523162842
        box_0CFD2.scale_y = 1.0
        box_0CFD2.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_0CFD2.operator('kro.delete_out_43a9b', text='', icon_value=_icons['Ethel.png'].icon_id, emboss=True, depress=False)
        box_9B722 = layout.box()
        box_9B722.alert = False
        box_9B722.enabled = True
        box_9B722.active = True
        box_9B722.use_property_split = False
        box_9B722.use_property_decorate = False
        box_9B722.alignment = 'Center'.upper()
        box_9B722.scale_x = 1.2999999523162842
        box_9B722.scale_y = 1.0
        box_9B722.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_9B722.operator('kro.delete_marker_key_bea06', text='', icon_value=_icons['Sopqt.png'].icon_id, emboss=False, depress=False)
        box_0656A = layout.box()
        box_0656A.alert = False
        box_0656A.enabled = True
        box_0656A.active = True
        box_0656A.use_property_split = False
        box_0656A.use_property_decorate = False
        box_0656A.alignment = 'Center'.upper()
        box_0656A.scale_x = 1.2999999523162842
        box_0656A.scale_y = 1.0
        box_0656A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_0656A.operator('kro.delete_marker_159b9', text='', icon_value=_icons['hamdi.png'].icon_id, emboss=True, depress=False)
        box_8673D = layout.box()
        box_8673D.alert = False
        box_8673D.enabled = True
        box_8673D.active = True
        box_8673D.use_property_split = False
        box_8673D.use_property_decorate = False
        box_8673D.alignment = 'Expand'.upper()
        box_8673D.scale_x = 1.2999999523162842
        box_8673D.scale_y = 1.0
        box_8673D.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_8673D.operator('kro.delet_channel_f0c68', text='', icon='X', emboss=True, depress=True)
        layout.separator(factor=1.0)
        box_87874 = layout.box()
        box_87874.alert = False
        box_87874.enabled = True
        box_87874.active = True
        box_87874.use_property_split = False
        box_87874.use_property_decorate = False
        box_87874.alignment = 'Expand'.upper()
        box_87874.scale_x = 1.3000000715255737
        box_87874.scale_y = 1.0
        box_87874.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_87874.operator('kro.add_mark_31c1f', text='', icon='MOD_FLUIDSIM', emboss=False, depress=False)
        box_77B4B = layout.box()
        box_77B4B.alert = False
        box_77B4B.enabled = True
        box_77B4B.active = True
        box_77B4B.use_property_split = False
        box_77B4B.use_property_decorate = False
        box_77B4B.alignment = 'Expand'.upper()
        box_77B4B.scale_x = 1.2999999523162842
        box_77B4B.scale_y = 1.0
        box_77B4B.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_77B4B.operator('kro.sellect_marks_e5cea', text='', icon='MARKER', emboss=False, depress=False)
        box_0096F = layout.box()
        box_0096F.alert = False
        box_0096F.enabled = True
        box_0096F.active = True
        box_0096F.use_property_split = False
        box_0096F.use_property_decorate = False
        box_0096F.alignment = 'Expand'.upper()
        box_0096F.scale_x = 1.2999998331069946
        box_0096F.scale_y = 1.0
        box_0096F.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_0096F.operator('kro.number_mark_a7fb5', text='', icon='USER', emboss=False, depress=False)
        layout.separator(factor=1.0)
        box_08A7A = layout.box()
        box_08A7A.alert = False
        box_08A7A.enabled = True
        box_08A7A.active = True
        box_08A7A.use_property_split = False
        box_08A7A.use_property_decorate = False
        box_08A7A.alignment = 'Center'.upper()
        box_08A7A.scale_x = 1.299999713897705
        box_08A7A.scale_y = 1.0
        box_08A7A.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_08A7A.operator('nla.bake', text='', icon_value=_icons['Bread.png'].icon_id, emboss=True, depress=False)
        
        box_8CE56 = layout.box()
        box_8CE56.alert = False
        box_8CE56.enabled = True
        box_8CE56.active = True
        box_8CE56.use_property_split = False
        box_8CE56.use_property_decorate = False
        box_8CE56.alignment = 'Expand'.upper()
        box_8CE56.scale_x = 1.2999999523162842
        box_8CE56.scale_y = 1.0
        box_8CE56.operator_context = "INVOKE_DEFAULT" if True else "EXEC_DEFAULT"
        op = box_8CE56.operator('kro.quick_noise_ef272', text='', icon_value=_icons['black-hole.png'].icon_id, emboss=True, depress=False)







classes = (




    FRO_OT_Setup_Handle_R_159B9,
    FRO_OT_Setup_Handle_L_Bea06,
    FRO_MT_Custom_Menu,


    FRO_OT_Select_After_Before_A83F0,
    FRO_OT_Select_All_2Af27,
    FRO_OT_Select_After_Dd961,
    FRO_OT_Select_Before_96Bb3,
    FRO_OT_Smart_Select_36C8D,
    FRO_MT_CustomMenu,

    FrameRangeToolsPopupOperator,
    SetupFrameRangePopupOperator,
    SetFrameRangePopupOperator,
    SetFrameRangeFromKeyframesOperator,
    SetFrameRangeFromCurrentFrameOperator,
    FRO_OT_D_Snapkey_A83F0,
    FRO_OT_Smart_Select_Dd961,


    FRO_OT_Move_Keyframe_96Bb3,
    FRO_OT_Select_Group_36C8D,
    FRO_OT_Jump_To_Endpiont_451B5,
    FRO_OT_Jump_To_Keyframe_802E7,    
    FRO_OT_Play_Animation_F_11B2C,
    FRO_OT_Move_To_End_220Ca,


    FRO_OT_Jessica_D_D23F9,
    FRO_OT_Delete_Out_43A9B,
    FRO_OT_Delete_Marker_159B9,
    FRO_OT_Delete_Marker_Key_Bea06,
    FRO_OT_Delete_Between_2Af27,
    FRO_OT_Delete_Selected_D235E,
    FRO_OT_Delet_Channel_F0C68,


    FRO_OT_Add_Mark_31C1F,
    FRO_OT_Sellect_Marks_E5Cea,
    FRO_OT_Number_Mark_A7Fb5,
    FRO_OT_Quick_Noise_Ef272,


    FRO_OT_Time_Line_76Ffa,    
    FRO_OT_Nla_Window_18De2,
    FRO_OT_Action_Editor_5E054,
    GRAPH_OT_reload_all_icons,
    FRO_OT_Toggle_Editor_Buttons, 
)


def register():

    global _icons

    
    _icons = bpy.utils.previews.new()

    
    for cls in classes:
        bpy.utils.register_class(cls)

    
    
    
    bpy.types.GRAPH_MT_editor_menus.append(draw_menu)
    bpy.types.GRAPH_MT_editor_menus.append(menu_func_1)
    bpy.types.GRAPH_MT_editor_menus.append(menu_func)
    bpy.types.GRAPH_MT_editor_menus.prepend(kro_add_to_graph_mt_editor_menus_F5DA3)
    
    bpy.types.GRAPH_MT_editor_menus.append(kro_add_to_graph_mt_editor_menus_32A6D)

    
    kcfg = bpy.context.window_manager.keyconfigs.addon
    if kcfg:
        km = kcfg.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
        kmi = km.keymap_items.new("wm.call_menu", type="V", value="PRESS", ctrl=True, shift=True)
        kmi.properties.name = "FRO_MT_Custom_Menu"
        addon_keymaps["d1054"] = (km, kmi)

    
 

    bpy.types.Scene.frame_Smartoffset_R = bpy.props.IntProperty(
        name="Setup range",
        description="Number of frames to set after the current frame",
        default=30,
        min=0,
        max=1000
    )

    bpy.types.Scene.frame_start_offset = bpy.props.IntProperty(
        name="Frame Start Offset",
        description="Number of frames to set for the start of the frame range",
        default=1,
        min=0,
        max=1000
    )

    bpy.types.Scene.frame_end_offset = bpy.props.IntProperty(
        name="Frame End Offset",
        description="Number of frames to set for the end of the frame range",
        default=30,
        min=0,
        max=1000
    )
    
    
    bpy.types.WindowManager.anim_deactivate_keyframe_operator = bpy.props.BoolProperty(
        name="Deactivate Keyframe Operator", default=False)
    
    icon_files = [
        'Tomato.png', 'click.png', 'arrows.png', 'Farqw.png',
        'Vawloi.png', 'Qutdxqcq.png', 'Defaultrio.png', 'Delete key.png',
        'spoertylem1.png', 'Ethel.png', 'Sopqt.png', 'hamdi.png', 'bread.png',
        'black-hole.png', 'Bread.png'
    ]
    for icon in icon_files:
        if not icon in _icons:
            _icons.load(icon, os.path.join(os.path.dirname(__file__), 'icons', icon), "IMAGE")

    bpy.types.Scene.frame_Smartoffset_R = bpy.props.IntProperty(
        name="Setup range",
        description="Number of frames to set after the current frame",
        default=30,
        min=0,
        max=1000
    )
    bpy.types.Scene.frame_start_offset = bpy.props.IntProperty(
        name="Frame Start Offset",
        description="Number of frames to set for the start of the frame range",
        default=1,
        min=0,
        max=1000
    )
    bpy.types.Scene.frame_end_offset = bpy.props.IntProperty(
        name="Frame End Offset",
        description="Number of frames to set for the end of the frame range",
        default=30,
        min=0,
        max=1000
    )


    bpy.types.WindowManager.kro_show_editor_buttons = bpy.props.BoolProperty(
        name="Show Editor Buttons",
        description="Toggle visibility of editor buttons in the Graph Editor toolbar",
        default=False
    )

    bpy.types.WindowManager.graph_scale_tool_active = BoolProperty(default=False)
    
    
def unregister():
    global _icons

    
    bpy.utils.previews.remove(_icons)
    _icons = None

    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    for km, kmi in addon_keymaps.values():
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    
    for cls in classes:
        bpy.utils.unregister_class(cls)

    
    bpy.types.GRAPH_MT_editor_menus.remove(draw_menu)
    bpy.types.GRAPH_MT_editor_menus.remove(menu_func_1)
    bpy.types.GRAPH_MT_editor_menus.remove(menu_func)
    bpy.types.GRAPH_MT_editor_menus.remove(kro_add_to_graph_mt_editor_menus_F5DA3)
    
    
    
    bpy.types.GRAPH_MT_editor_menus.remove(kro_add_to_graph_mt_editor_menus_32A6D)


    
    
    del bpy.types.Scene.frame_start_offset
    del bpy.types.Scene.frame_end_offset
    

def draw_menu(self, context):
    layout = self.layout
    layout.menu("FRO_MT_Custom_Menu")