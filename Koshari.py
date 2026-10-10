bl_info = {
    "name": "Koshari",
    "author": "Hamdi Amer",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "Graph Editor > Header",
    "description": "Draw and edit the keyframes",
    "category": "Animation",
}

import bpy
import blf
import gpu
import math
import time
from collections import defaultdict
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.props import BoolProperty
from bpy.props import IntProperty, EnumProperty



_CIRCLE_SEGMENTS = 24
_CIRCLE_OFFSETS = [(math.cos(i * 2.0 * math.pi / _CIRCLE_SEGMENTS), 
                    math.sin(i * 2.0 * math.pi / _CIRCLE_SEGMENTS)) 
                   for i in range(_CIRCLE_SEGMENTS + 1)]

# -------------------------------------------------------------------
# VISUAL DRAWING
# -------------------------------------------------------------------
def draw_ui_callback(self, context):
    if not self.is_running or not context.region:
        return
        
    region = context.region
    view2d = region.view2d
    mx, my = self.mouse_x, self.mouse_y

    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    gpu.state.line_width_set(2.0)
    gpu.state.blend_set('ALPHA')

    # Default UI State
    color = (0.2, 0.8, 1.0, 0.6) 
    shape = 'CIRCLE'
    
    if self.hover_target:
        ttype = self.hover_target['type']
        kp_interp = 'BEZIER'
        try:
            fcurve = self.hover_target['fcurve']
            kp = fcurve.keyframe_points[self.hover_target['kp_idx']]
            kp_interp = kp.interpolation
        except Exception:
            pass

        if ttype == 'KEYFRAME':
            if kp_interp == 'CONSTANT':
                shape = 'SQUARE'
                color = (0.2, 0.9, 0.3, 0.8) 
            elif kp_interp == 'LINEAR':
                shape = 'DIAMOND'
                color = (0.9, 0.9, 0.1, 0.8) 
            else:
                shape = 'CIRCLE'
                color = (1.0, 0.6, 0.0, 0.8)
                
        elif ttype in {'LEFT_HANDLE', 'RIGHT_HANDLE'}:
            color = (0.8, 0.2, 1.0, 0.8) 
            shape = 'CIRCLE'

   
    radius = 15
    if shape == 'SQUARE':
        vertices = [
            (mx - radius, my - radius),
            (mx + radius, my - radius),
            (mx + radius, my + radius),
            (mx - radius, my + radius),
            (mx - radius, my - radius) 
        ]
    elif shape == 'DIAMOND':
        vertices = [
            (mx, my - radius - 5),
            (mx + radius + 5, my),
            (mx, my + radius + 5),
            (mx - radius - 5, my),
            (mx, my - radius - 5) 
        ]
    else:
        vertices = [(mx + cx * radius, my + cy * radius) for cx, cy in _CIRCLE_OFFSETS]
        
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

    
    try:
        frame_val, _ = view2d.region_to_view(mx, my)
        font_id = 0
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.size(font_id, 18)
        blf.position(font_id, mx + 25, my - 10, 0)
        if frame_val < 0:
            blf.color(font_id, 1.0, 0.2, 0.2, 1.0)
        else:
            blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, str(round(frame_val)))
        blf.disable(font_id, blf.SHADOW)
    except Exception:
        pass

    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')

# -------------------------------------------------------------------
# CORE OPERATOR
# -------------------------------------------------------------------
class GRAPH_OT_SmartDraw(bpy.types.Operator):
    bl_idname = "graph.smart_draw"
    bl_label = "Smart Draw Keyframes"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

    is_running = False
    mouse_x = 0
    mouse_y = 0
    drawing = False
    hover_target = None 

    def modal(self, context, event):
        mouse_area = None
        if context.screen:
            for area in context.screen.areas:
                if area.x <= event.mouse_x <= area.x + area.width and \
                   area.y <= event.mouse_y <= area.y + area.height:
                    mouse_area = area
                    break
                    
        if not mouse_area or mouse_area.type != 'GRAPH_EDITOR':
            return self.cancel_op(context)

        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return self.cancel_op(context)

        if event.type == 'MOUSEMOVE':
            if self.drawing and self.hover_target:
                self.update_target(context)
            else:
                self.scan_proximity(context)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self.scan_proximity(context)
                
                self.drawing = True
                if not self.hover_target:
                    self.insert_keyframe(context)
                else:
                    self.hover_target['fcurve'].select = True
                    try:
                        kp = self.hover_target['fcurve'].keyframe_points[self.hover_target['kp_idx']]
                        kp.select_control_point = True
                        
                        if self.hover_target['type'] == 'LEFT_HANDLE':
                            kp.select_left_handle = True
                        elif self.hover_target['type'] == 'RIGHT_HANDLE':
                            kp.select_right_handle = True
                    except IndexError:
                        pass
            elif event.value == 'RELEASE':
                self.drawing = False
                if self.hover_target and self.hover_target['fcurve']:
                    self.hover_target['fcurve'].update()
            
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type != 'GRAPH_EDITOR':
            return {'CANCELLED'}

        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y
        self.is_running = True
        self.drawing = False
        self.hover_target = None

        self._handle = bpy.types.SpaceGraphEditor.draw_handler_add(
            draw_ui_callback, (self, context), 'WINDOW', 'POST_PIXEL'
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_op(self, context):
        self.is_running = False
        if hasattr(self, '_handle') and self._handle:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self._handle, 'WINDOW')
        context.area.tag_redraw()
        return {'CANCELLED'}



    def _get_active_fcurves(self, context, action):
        obj = context.active_object
        if not obj: return []        
        all_fcurves = get_action_fcurves(action)
        active_fc = getattr(context, 'active_editable_fcurve', None)
        if active_fc and not active_fc.hide and not active_fc.lock:
            return [active_fc]


        selected_fcurves = [fc for fc in all_fcurves if fc.select and not fc.hide and not fc.lock]
        if selected_fcurves: return selected_fcurves
        if obj.type == 'ARMATURE' and obj.mode == 'POSE':
            sel_bones = {f'pose.bones["{b.name}"]' for b in context.selected_pose_bones}
            if sel_bones:
                bone_fcurves = [
                    fc for fc in all_fcurves 
                    if not fc.hide and not fc.lock and any(b in fc.data_path for b in sel_bones)
                ]
                if bone_fcurves: return bone_fcurves
                    
        return [fc for fc in all_fcurves if not fc.hide and not fc.lock]

    def _get_keyframes_in_radius(self, kps, target_frame, radius):
        n = len(kps)
        if n == 0: return []

        low, high = 0, n - 1
        closest_idx = 0

        while low <= high:
            mid = (low + high) // 2
            frame = kps[mid].co[0]
            if frame < target_frame: low = mid + 1
            elif frame > target_frame: high = mid - 1
            else:
                closest_idx = mid
                break
        else:
            if high < 0: closest_idx = low
            elif low >= n: closest_idx = high
            else:
                if abs(kps[low].co[0] - target_frame) < abs(kps[high].co[0] - target_frame):
                    closest_idx = low
                else: closest_idx = high

        results = []
        i = closest_idx
        while i >= 0 and abs(kps[i].co[0] - target_frame) <= radius:
            results.append(i)
            i -= 1
            
        i = closest_idx + 1
        while i < n and abs(kps[i].co[0] - target_frame) <= radius:
            results.append(i)
            i += 1

        return results

    def scan_proximity(self, context):
        self.hover_target = None
        obj = context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action: return

        view2d = context.region.view2d
        
        try:
            frame_center, _ = view2d.region_to_view(self.mouse_x, self.mouse_y)
            frame_edge, _ = view2d.region_to_view(self.mouse_x + 30, self.mouse_y)
            base_radius = abs(frame_edge - frame_center)
            search_radius_frames = max(base_radius * 2, 50.0) 
        except Exception:
            frame_center = 0
            search_radius_frames = 50.0
        
        valid_fcurves = self._get_active_fcurves(context, obj.animation_data.action)
        
        closest_kf_dist = 400   
        closest_handle_dist = 400 
        
        best_kf = None
        best_handle = None
        
        active_fc = getattr(context, 'active_editable_fcurve', None)

        for fcurve in valid_fcurves:
            is_rad = any(x in fcurve.data_path for x in ('rotation_euler', 'rotation_axis_angle'))
            nearby_indices = self._get_keyframes_in_radius(fcurve.keyframe_points, frame_center, search_radius_frames)

            for idx in nearby_indices:
                kp = fcurve.keyframe_points[idx]
                
                val_disp = math.degrees(kp.co[1]) if is_rad else kp.co[1]
                kf_coords = view2d.view_to_region(kp.co[0], val_disp, clip=False)
                
                if kf_coords:
                    sx, sy = kf_coords
                    dist_sq = (sx - self.mouse_x)**2 + (sy - self.mouse_y)**2
                    
                    
                    if dist_sq < closest_kf_dist or (best_kf and fcurve == active_fc and abs(dist_sq - closest_kf_dist) < 25):
                        closest_kf_dist = dist_sq
                        best_kf = {'fcurve': fcurve, 'kp_idx': idx, 'type': 'KEYFRAME'}

              
                interp = getattr(kp, 'interpolation', 'BEZIER')
                if interp == 'BEZIER' and kp.select_control_point:
                    l_val = math.degrees(kp.handle_left[1]) if is_rad else kp.handle_left[1]
                    l_coords = view2d.view_to_region(kp.handle_left[0], l_val, clip=False)
                    if l_coords:
                        hx1, hy1 = l_coords
                        d1 = (hx1 - self.mouse_x)**2 + (hy1 - self.mouse_y)**2
                        
                 
                        if d1 < closest_handle_dist or (best_handle and fcurve == active_fc and abs(d1 - closest_handle_dist) < 25):
                            closest_handle_dist = d1
                            best_handle = {'fcurve': fcurve, 'kp_idx': idx, 'type': 'LEFT_HANDLE'}

                    r_val = math.degrees(kp.handle_right[1]) if is_rad else kp.handle_right[1]
                    r_coords = view2d.view_to_region(kp.handle_right[0], r_val, clip=False)
                    if r_coords:
                        hx2, hy2 = r_coords
                        d2 = (hx2 - self.mouse_x)**2 + (hy2 - self.mouse_y)**2
                        
                     
                        if d2 < closest_handle_dist or (best_handle and fcurve == active_fc and abs(d2 - closest_handle_dist) < 25):
                            closest_handle_dist = d2
                            best_handle = {'fcurve': fcurve, 'kp_idx': idx, 'type': 'RIGHT_HANDLE'}

        if best_handle and closest_handle_dist < closest_kf_dist:
            self.hover_target = best_handle
        elif best_kf:
            self.hover_target = best_kf

    def _get_closest_fcurve_to_mouse(self, context, valid_fcurves, frame_f):
        active_fc = getattr(context, 'active_editable_fcurve', None)
        if active_fc and active_fc in valid_fcurves:
            return active_fc
            
        view2d = context.region.view2d
        closest_fc = valid_fcurves[0]
        min_dist = float('inf')
        
        for fc in valid_fcurves:
            val = fc.evaluate(frame_f)
            is_rad = any(x in fc.data_path for x in ('rotation_euler', 'rotation_axis_angle'))
            disp_val = math.degrees(val) if is_rad else val
            coords = view2d.view_to_region(frame_f, disp_val, clip=False)
            if not coords: continue
            _, sy = coords
            dist = abs(sy - self.mouse_y)
            if dist < min_dist:
                min_dist = dist
                closest_fc = fc
        return closest_fc

    def insert_keyframe(self, context):
        obj = context.active_object
        if not obj: return
        if not obj.animation_data: obj.animation_data_create()
        if not obj.animation_data.action: obj.animation_data.action = bpy.data.actions.new("Action")
        
        action = obj.animation_data.action
        valid_fcurves = self._get_active_fcurves(context, action)
        if not valid_fcurves: return

        view2d = context.region.view2d
        frame_f, val_f = view2d.region_to_view(self.mouse_x, self.mouse_y)
        frame = round(frame_f)

        if frame < 0:
            return

        fcurve = self._get_closest_fcurve_to_mouse(context, valid_fcurves, frame_f)
        is_rad = any(x in fcurve.data_path for x in ('rotation_euler', 'rotation_axis_angle'))
        stored_val = math.radians(val_f) if is_rad else val_f

       
        kp = fcurve.keyframe_points.insert(frame, stored_val)
        idx = 0
        for i, p in enumerate(fcurve.keyframe_points):
            if abs(p.co[0] - frame) < 0.001 and abs(p.co[1] - stored_val) < 0.001:
                idx = i
                break
        
        ref_kp = None
        if idx > 0:
            ref_kp = fcurve.keyframe_points[idx - 1]
        elif len(fcurve.keyframe_points) > 1:
            ref_kp = fcurve.keyframe_points[idx + 1]

        if ref_kp:
            kp.interpolation = ref_kp.interpolation
            if ref_kp.interpolation == 'BEZIER':
                kp.handle_left_type = getattr(ref_kp, 'handle_left_type', 'ALIGNED')
                kp.handle_right_type = getattr(ref_kp, 'handle_right_type', 'ALIGNED')
        else:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'ALIGNED'
            kp.handle_right_type = 'ALIGNED'
        
        fcurve.update()
        
        self.hover_target = {'fcurve': fcurve, 'kp_idx': idx, 'type': 'KEYFRAME'}
        self.hover_target['fcurve'].select = True
        try:
            fcurve.keyframe_points[idx].select_control_point = True
        except IndexError:
            pass

    def update_target(self, context):
        target = self.hover_target
        fcurve = target['fcurve']
        
        try:
            kp = fcurve.keyframe_points[target['kp_idx']]
        except IndexError:
            return 
            
        ttype = target['type']
        view2d = context.region.view2d
        frame_f, val_f = view2d.region_to_view(self.mouse_x, self.mouse_y)
        
        is_rad = any(x in fcurve.data_path for x in ('rotation_euler', 'rotation_axis_angle'))
        stored_val = math.radians(val_f) if is_rad else val_f

        if ttype == 'KEYFRAME':
            frame = max(0, round(frame_f))  # Do not allow dragging to negative frames
            old_co = Vector(kp.co)
            kp.co = (frame, stored_val)
            delta = Vector(kp.co) - old_co
            
            kp.handle_left = Vector(kp.handle_left) + delta
            kp.handle_right = Vector(kp.handle_right) + delta

        elif ttype == 'LEFT_HANDLE':
            if kp.handle_left_type in {'AUTO', 'AUTO_CLAMPED'}:
                kp.handle_left_type = 'ALIGNED'
                
            kp.handle_left = (frame_f, stored_val)
            
            if kp.handle_left_type == 'ALIGNED' and kp.handle_right_type == 'ALIGNED':
                co = Vector(kp.co)
                vec = co - Vector(kp.handle_left)
                if vec.length > 0:
                    old_len = (Vector(kp.handle_right) - co).length
                    kp.handle_right = co + vec.normalized() * old_len

        elif ttype == 'RIGHT_HANDLE':
            if kp.handle_right_type in {'AUTO', 'AUTO_CLAMPED'}:
                kp.handle_right_type = 'ALIGNED'
                
            kp.handle_right = (frame_f, stored_val)
            
            if kp.handle_right_type == 'ALIGNED' and kp.handle_left_type == 'ALIGNED':
                co = Vector(kp.co)
                vec = Vector(kp.handle_right) - co
                if vec.length > 0:
                    old_len = (Vector(kp.handle_left) - co).length
                    kp.handle_left = co - vec.normalized() * old_len


class GRAPH_OT_DoubleClickTracker(bpy.types.Operator):
    bl_idname = "graph.double_click_tracker"
    bl_label = "Double Click Tracker"
    bl_options = {'REGISTER'}

    _timer = None
    _last_click = 0.0
    _clicks = 0

    def modal(self, context, event):
        wm = context.window_manager
        
        if not wm.graph_tracking_active:
            self.cancel_tracker(context)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            mouse_area = None
            if context.screen:
                for area in context.screen.areas:
                    if area.x <= event.mouse_x <= area.x + area.width and \
                       area.y <= event.mouse_y <= area.y + area.height:
                        mouse_area = area
                        break

            if mouse_area and mouse_area.type == 'GRAPH_EDITOR':
                now = time.time()
                if self._clicks == 0 or (now - self._last_click > 0.3):
                    self._clicks = 1
                    self._last_click = now
                else:
                    bpy.ops.graph.smart_draw('INVOKE_DEFAULT')
                    self._clicks = 0
                return {'PASS_THROUGH'}
            self._clicks = 0
            
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        if wm.graph_tracking_active:
            wm.graph_tracking_active = False
            self.cancel_tracker(context)
            return {'FINISHED'}
        else:
            wm.graph_tracking_active = True
            self._timer = wm.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

    def cancel_tracker(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        return {'CANCELLED'}



def get_action_fcurves(action):
    """Backwards-compatible F-Curve retrieval (handles Blender 5.0+ Slotted Actions)."""
    if hasattr(action, "fcurves"):
        return action.fcurves
    
    fcurves = []
    if hasattr(action, "layers"):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for cb in strip.channelbags:
                        fcurves.extend(cb.fcurves)
    return fcurves


def get_visible_fcurves(context):
    """Return all visible, unlocked fcurves for the active object."""
    obj = context.active_object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return []
        
    all_fcurves = get_action_fcurves(obj.animation_data.action)
    
    return [
        fc for fc in all_fcurves
        if not fc.hide and not fc.lock
    ]


# -------------------------------------------------------------------
# OPTIMIZED CACHE SYSTEM (with view change detection)
# -------------------------------------------------------------------
class KeyframeCache:
    def __init__(self):
        self.grid_size = 50
        self.visible_fcurves = []
        self.keyframe_coords = defaultdict(list)
        self.grid = defaultdict(list)
        self.last_keyframes = {}
        self.first_keyframes = {}
        self.last_update_time = 0
        self.update_interval = 0.3
        self.last_visible_count = 0
        self.last_view_rect = None 

    def needs_update(self, context):
        if not context.selected_objects:
            return True

       
        if context.region and context.region.view2d:
            try:
                view2d = context.region.view2d
                xmin, ymin = view2d.region_to_view(0, 0)
                xmax, ymax = view2d.region_to_view(context.region.width, context.region.height)
                current_rect = (xmin, ymin, xmax, ymax)
                if self.last_view_rect is None or current_rect != self.last_view_rect:
                    self.last_view_rect = current_rect
                    return True
            except:
                pass

        if time.time() - self.last_update_time > self.update_interval:
            return True
        if len(get_visible_fcurves(context)) != self.last_visible_count:
            return True
        return False

    def update(self, context, view2d):
        self.visible_fcurves.clear()
        self.keyframe_coords.clear()
        self.grid.clear()
        self.last_keyframes.clear()
        self.first_keyframes.clear()

        visible_fcurves = get_visible_fcurves(context)
        self.visible_fcurves = visible_fcurves
        self.last_visible_count = len(visible_fcurves)

        for fcurve in visible_fcurves:
            if fcurve.keyframe_points:
                self.first_keyframes[fcurve] = fcurve.keyframe_points[0]
                self.last_keyframes[fcurve] = fcurve.keyframe_points[-1]

            for kp in fcurve.keyframe_points:
                try:
                    screen_x, screen_y = view2d.view_to_region(kp.co[0], kp.co[1])
                    self.keyframe_coords[fcurve].append((kp.co[0], kp.co[1], screen_x, screen_y, kp))

                    grid_x = int(screen_x / self.grid_size)
                    grid_y = int(screen_y / self.grid_size)
                    self.grid[(grid_x, grid_y)].append((fcurve, kp, screen_x, screen_y, 'KEYFRAME'))
                except:
                    continue

        
        try:
            xmin, ymin = view2d.region_to_view(0, 0)
            xmax, ymax = view2d.region_to_view(context.region.width, context.region.height)
            self.last_view_rect = (xmin, ymin, xmax, ymax)
        except:
            self.last_view_rect = None

        self.last_update_time = time.time()

    def clear(self):
        self.visible_fcurves.clear()
        self.keyframe_coords.clear()
        self.grid.clear()
        self.last_keyframes.clear()
        self.first_keyframes.clear()
        self.last_visible_count = 0
        self.last_view_rect = None


_keyframe_cache = KeyframeCache()


# -------------------------------------------------------------------
# VISUAL DRAWING (unchanged)
# -------------------------------------------------------------------
def draw_enhanced_cursor(self, context, mx, my, shader):
    region = context.region
    radius = min(self.selection_radius_px, 50)
    
    if self.scale_mode == 'X':
        primary_color = (1.0, 0.5, 0.3, 0.8) if self._range_active else (1.0, 0.4, 0.2, 0.6)
        secondary_color = (1.0, 0.3, 0.1, 0.4)
    elif self.scale_mode == 'Y':
        primary_color = (0.3, 0.9, 0.4, 0.8) if self._range_active else (0.2, 0.8, 0.3, 0.6)
        secondary_color = (0.1, 0.7, 0.2, 0.4)
    else:
        primary_color = (0.9, 0.7, 0.2, 0.8) if self._range_active else (0.8, 0.6, 0.1, 0.6)
        secondary_color = (0.7, 0.5, 0.1, 0.4)
    
    pulse_factor = 1.0 + 0.1 * math.sin(time.time() * 6.0) if self._range_active else 1.0
    pulsed_radius = radius * pulse_factor
    
   
    gpu.state.line_width_set(4.0)
    outer_radius = pulsed_radius + 3
    segments = max(24, min(64, int(outer_radius * 1.2)))
    angle_step = 2 * math.pi / segments
    outer_vertices = [(mx + math.cos(i * angle_step) * outer_radius, my + math.sin(i * angle_step) * outer_radius) for i in range(segments + 1)]
    outer_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": outer_vertices})
    shader.uniform_float("color", (*primary_color[:3], primary_color[3] * 0.3))
    outer_batch.draw(shader)
    
    gpu.state.line_width_set(2.5)
    main_vertices = [(mx + math.cos(i * angle_step) * pulsed_radius, my + math.sin(i * angle_step) * pulsed_radius) for i in range(segments + 1)]
    main_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": main_vertices})
    shader.uniform_float("color", primary_color)
    main_batch.draw(shader)
    
    gpu.state.line_width_set(1.5)
    inner_radius = pulsed_radius * 0.7
    inner_vertices = [(mx + math.cos(i * angle_step) * inner_radius, my + math.sin(i * angle_step) * inner_radius) for i in range(segments + 1)]
    inner_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": inner_vertices})
    shader.uniform_float("color", (*secondary_color[:3], secondary_color[3] * 0.8))
    inner_batch.draw(shader)
    
    line_length = pulsed_radius * 0.8
    gpu.state.line_width_set(2.0)
    crosshair_vertices = [
        (mx - line_length, my), (mx - inner_radius, my),
        (mx + inner_radius, my), (mx + line_length, my),
        (mx, my - line_length), (mx, my - inner_radius),
        (mx, my + inner_radius), (mx, my + line_length)
    ]
    cap_size = 4
    caps_vertices = [
        (mx - line_length - cap_size, my), (mx - line_length + cap_size, my),
        (mx + line_length - cap_size, my), (mx + line_length + cap_size, my),
        (mx, my - line_length - cap_size), (mx, my - line_length + cap_size),
        (mx, my + line_length - cap_size), (mx, my + line_length + cap_size)
    ]
    crosshair_batch = batch_for_shader(shader, 'LINES', {"pos": crosshair_vertices})
    caps_batch = batch_for_shader(shader, 'LINES', {"pos": caps_vertices})
    shader.uniform_float("color", (*primary_color[:3], primary_color[3] * 0.6))
    crosshair_batch.draw(shader)
    shader.uniform_float("color", (*primary_color[:3], primary_color[3] * 0.8))
    caps_batch.draw(shader)
    
    center_size = 3
    center_vertices = [
        (mx - center_size, my), (mx + center_size, my),
        (mx, my - center_size), (mx, my + center_size)
    ]
    center_batch = batch_for_shader(shader, 'LINES', {"pos": center_vertices})
    shader.uniform_float("color", (1.0, 1.0, 1.0, 0.9))
    center_batch.draw(shader)


def draw_enhanced_origin(self, context, view2d, shader):
    try:
        origin_x, origin_y = view2d.view_to_region(self._origin_frame, self._origin_value)
        
        if self.scale_mode == 'X':
            origin_color = (1.0, 0.6, 0.3, 0.9)
            axis_colors = {'X': (1.0, 0.4, 0.2, 0.7), 'Y': (0.3, 0.3, 0.3, 0.3)}
        elif self.scale_mode == 'Y':
            origin_color = (0.3, 0.9, 0.5, 0.9)
            axis_colors = {'X': (0.3, 0.3, 0.3, 0.3), 'Y': (0.2, 0.8, 0.4, 0.7)}
        else:
            origin_color = (0.9, 0.8, 0.3, 0.9)
            axis_colors = {'X': (0.9, 0.6, 0.2, 0.6), 'Y': (0.7, 0.9, 0.3, 0.6)}
        
       
        outer_radius = 12
        gpu.state.line_width_set(3.0)
        segments = 32
        outer_vertices = [(origin_x + math.cos(i * (2*math.pi/segments)) * outer_radius, origin_y + math.sin(i * (2*math.pi/segments)) * outer_radius) for i in range(segments + 1)]
        outer_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": outer_vertices})
        shader.uniform_float("color", (*origin_color[:3], origin_color[3] * 0.3))
        outer_batch.draw(shader)
        
        main_radius = 8
        gpu.state.line_width_set(2.5)
        circle_vertices = [(origin_x + math.cos(i * (2*math.pi/segments)) * main_radius, origin_y + math.sin(i * (2*math.pi/segments)) * main_radius) for i in range(segments + 1)]
        circle_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": circle_vertices})
        shader.uniform_float("color", origin_color)
        circle_batch.draw(shader)
        
        
        axis_length = 20
        gpu.state.line_width_set(2.0)
        if self.scale_mode in ['X', 'BOTH']:
            x_vertices = [(origin_x - axis_length, origin_y), (origin_x - main_radius, origin_y),
                          (origin_x + main_radius, origin_y), (origin_x + axis_length, origin_y),
                          (origin_x + axis_length - 5, origin_y - 3), (origin_x + axis_length, origin_y), (origin_x + axis_length - 5, origin_y + 3)]
            x_batch = batch_for_shader(shader, 'LINES', {"pos": x_vertices})
            shader.uniform_float("color", axis_colors['X'])
            x_batch.draw(shader)
        if self.scale_mode in ['Y', 'BOTH']:
            y_vertices = [(origin_x, origin_y - axis_length), (origin_x, origin_y - main_radius),
                          (origin_x, origin_y + main_radius), (origin_x, origin_y + axis_length),
                          (origin_x - 3, origin_y + axis_length - 5), (origin_x, origin_y + axis_length), (origin_x + 3, origin_y + axis_length - 5)]
            y_batch = batch_for_shader(shader, 'LINES', {"pos": y_vertices})
            shader.uniform_float("color", axis_colors['Y'])
            y_batch.draw(shader)
        
        gpu.state.line_width_set(1.5)
        cross_size = 4
        cross_vertices = [(origin_x - cross_size, origin_y), (origin_x + cross_size, origin_y),
                          (origin_x, origin_y - cross_size), (origin_x, origin_y + cross_size)]
        cross_batch = batch_for_shader(shader, 'LINES', {"pos": cross_vertices})
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.9))
        cross_batch.draw(shader)
        
        pulse = 1.0 + 0.1 * math.sin(time.time() * 5.0)
        pulse_radius = main_radius * pulse
        pulse_vertices = [(origin_x + math.cos(i * (2*math.pi/segments)) * pulse_radius, origin_y + math.sin(i * (2*math.pi/segments)) * pulse_radius) for i in range(segments + 1)]
        gpu.state.line_width_set(1.0)
        pulse_batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": pulse_vertices})
        shader.uniform_float("color", (*origin_color[:3], origin_color[3] * 0.2))
        pulse_batch.draw(shader)
    except:
        pass


def draw_enhanced_range(self, context, view2d, shader):
    
    region = context.region
    if self._range_selecting:
        try:
            start_x, start_y = self._range_start_pos
            current_x, current_y = self._current_mouse_x, self._current_mouse_y
            
            range_color = (0.9, 0.7, 0.3, 0.1)
            border_color = (0.9, 0.7, 0.3, 0.8)
            
            rect_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            rect_vertices = [(start_x, start_y), (current_x, start_y), (current_x, current_y), (start_x, current_y)]
            rect_indices = [(0,1,2),(0,2,3)]
            rect_batch = batch_for_shader(rect_shader, 'TRIS', {"pos": rect_vertices}, indices=rect_indices)
            rect_shader.bind()
            rect_shader.uniform_float("color", range_color)
            rect_batch.draw(rect_shader)
            
            gpu.state.line_width_set(2.5)
            offset = 2
            border_vertices = [
                (start_x - offset, start_y - offset), (current_x + offset, start_y - offset),
                (current_x + offset, start_y - offset), (current_x + offset, current_y + offset),
                (current_x + offset, current_y + offset), (start_x - offset, current_y + offset),
                (start_x - offset, current_y + offset), (start_x - offset, start_y - offset)
            ]
            border_batch = batch_for_shader(shader, 'LINES', {"pos": border_vertices})
            shader.bind()
            shader.uniform_float("color", (*border_color[:3], border_color[3] * 0.5))
            border_batch.draw(shader)
            
            gpu.state.line_width_set(1.5)
            inner_border_vertices = [
                (start_x, start_y), (current_x, start_y),
                (current_x, start_y), (current_x, current_y),
                (current_x, current_y), (start_x, current_y),
                (start_x, current_y), (start_x, start_y)
            ]
            inner_batch = batch_for_shader(shader, 'LINES', {"pos": inner_border_vertices})
            shader.uniform_float("color", border_color)
            inner_batch.draw(shader)
            
            corner_size = 8
            for cx, cy in [(start_x, start_y), (current_x, start_y), (current_x, current_y), (start_x, current_y)]:
                corner_vertices = [(cx - corner_size, cy), (cx + corner_size, cy),
                                   (cx, cy - corner_size), (cx, cy + corner_size)]
                corner_batch = batch_for_shader(shader, 'LINES', {"pos": corner_vertices})
                shader.uniform_float("color", border_color)
                corner_batch.draw(shader)
        except:
            pass
    
    elif self._range_active:
        try:
            range_start_x, _ = view2d.view_to_region(self._range_start_frame, 0)
            range_end_x, _ = view2d.view_to_region(self._range_end_frame, 0)
            
            pulse = 0.5 + 0.5 * math.sin(time.time() * 2.0)
            range_color = (0.9, 0.7, 0.3, 0.05 + 0.02 * pulse)
            line_color = (0.9, 0.7, 0.3, 0.4 + 0.1 * pulse)
            
            rect_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            rect_vertices = [(range_start_x, 0), (range_end_x, 0), (range_end_x, region.height), (range_start_x, region.height)]
            rect_batch = batch_for_shader(rect_shader, 'TRIS', {"pos": rect_vertices})
            rect_shader.bind()
            rect_shader.uniform_float("color", range_color)
            rect_batch.draw(rect_shader)
            
            gpu.state.line_width_set(1.5 + 0.5 * pulse)
            line_vertices = [(range_start_x, 0), (range_start_x, region.height),
                             (range_end_x, 0), (range_end_x, region.height)]
            line_batch = batch_for_shader(shader, 'LINES', {"pos": line_vertices})
            shader.bind()
            shader.uniform_float("color", line_color)
            line_batch.draw(shader)
            
            edge_vertices = [(range_start_x, 0), (range_end_x, 0),
                             (range_start_x, region.height), (range_end_x, region.height)]
            edge_batch = batch_for_shader(shader, 'LINES', {"pos": edge_vertices})
            shader.uniform_float("color", (*line_color[:3], line_color[3] * 0.7))
            edge_batch.draw(shader)
        except:
            pass


def draw_enhanced_text(self, context):
    
    font_id = 0
    region = context.region
    
    mode_names = {'X': 'X Only  ⮕', 'Y': 'Y Only  ⬆', 'BOTH': 'Both Axes  ⭥'}
    operation_names = {'SCALE': 'Scale ⚖', 'OFFSET': 'Offset ↔'}
    
    status_lines = [
        "🎯 Scale Tool Active",
        f"Operation: {operation_names[self.operation_mode]}",
        f"Mode: {'Relative ⚖' if self.relative_scale else 'Uniform ⬌'}",
        f"Axes: {mode_names[self.scale_mode]}"
    ]
    if self._origin_set:
        status_lines.append(f"Origin: {self._origin_frame:.1f} | {self._origin_value:.2f}")
    if self._range_active:
        status_lines.append(f"Range: {self._range_start_frame} → {self._range_end_frame}")
    
    status_lines.extend([
        "Hotkeys:",
        "O: Toggle Operation (Scale/Offset)",
        "V: Cycle Axes (X/Y/Both)",
        "R: Toggle Mode (Relative/Uniform)",
        "X: Clear Range (if active)",
        "Left Click: Set Origin",
        "Drag: Set Range / Scale",
        "Esc/RMB: Cancel",
    ])
    
    text_height = 16
    line_spacing = 2
    total_height = len(status_lines) * (text_height + line_spacing) + 10
    text_width = 220
    padding = 8
    
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    panel_color = (0.1, 0.1, 0.1, 0.8)
    panel_border = (0.9, 0.7, 0.3, 0.3)
    
    panel_vertices = [(padding, padding), (padding + text_width, padding),
                      (padding + text_width, padding + total_height), (padding, padding + total_height)]
    panel_indices = [(0,1,2),(0,2,3)]
    
    gpu.state.blend_set('ALPHA')
    panel_batch = batch_for_shader(shader, 'TRIS', {"pos": panel_vertices}, indices=panel_indices)
    shader.bind()
    shader.uniform_float("color", panel_color)
    panel_batch.draw(shader)
    
    gpu.state.line_width_set(1.5)
    border_vertices = [
        (padding, padding), (padding + text_width, padding),
        (padding + text_width, padding), (padding + text_width, padding + total_height),
        (padding + text_width, padding + total_height), (padding, padding + total_height),
        (padding, padding + total_height), (padding, padding)
    ]
    border_batch = batch_for_shader(shader, 'LINES', {"pos": border_vertices})
    shader.uniform_float("color", panel_border)
    border_batch.draw(shader)
    
    blf.size(font_id, 11)
    for i, line in enumerate(status_lines):
        y_pos = padding + 5 + i * (text_height + line_spacing)
        blf.position(font_id, padding + 3, y_pos - 1, 0)
        blf.color(font_id, 0, 0, 0, 0.5)
        blf.draw(font_id, line)
        
        blf.position(font_id, padding + 5, y_pos, 0)
        if i == 0:
            blf.color(font_id, 0.9, 0.7, 0.3, 0.9)
        elif "Origin" in line or "Range" in line:
            blf.color(font_id, 0.8, 0.8, 0.8, 0.8)
        elif "Hotkeys:" in line:
            blf.color(font_id, 0.9, 0.7, 0.3, 0.9)
        else:
            blf.color(font_id, 0.9, 0.9, 0.9, 0.9)
        blf.draw(font_id, line)
    
    gpu.state.blend_set('NONE')


def draw_scale_callback(self, context):
    if not self._is_running or not context.region:
        return
    
    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    region = context.region
    view2d = region.view2d
    mx, my = self._current_mouse_x, self._current_mouse_y
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('ALPHA')
    
    if self._origin_set and self.operation_mode == 'SCALE':
        draw_enhanced_origin(self, context, view2d, shader)
    
    draw_enhanced_range(self, context, view2d, shader)
    draw_enhanced_cursor(self, context, mx, my, shader)
    draw_enhanced_text(self, context)
    
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')


# -------------------------------------------------------------------
# MAIN OPERATOR
# -------------------------------------------------------------------
class GRAPH_OT_ScaleKeyframes(bpy.types.Operator):
    bl_idname = "graph.scale_keyframes"
    bl_label = "Scale Keyframes"
    bl_description = "Scale/Offset keyframes (all selected objects/bones)"
    bl_options = {'REGISTER', 'UNDO'}
        
    _is_running = False
    _drawing = False
    _last_scan_time = 0
    _scan_throttle = 0.05
    _draw_handler = None
    _current_mouse_x = 0
    _current_mouse_y = 0    
    _origin_set = False
    _origin_frame = 0
    _origin_value = 0   
    _range_start_frame = 0
    _range_end_frame = 0
    _range_active = False
    _range_selecting = False
    _range_start_pos = (0, 0)   
    _operation_start_pos = None
    _original_keyframes = []    
    _mouse_pressed = False
    _drag_started = False
    _drag_threshold = 8             
    _press_pos_x = 0
    _press_pos_y = 0
    
    selection_radius_px: IntProperty(default=20, min=10, max=100)
    scale_mode: EnumProperty(items=[('X',"X Only",""), ('Y',"Y Only",""), ('BOTH',"Both","")], default='X')
    relative_scale: BoolProperty(default=True)
    operation_mode: EnumProperty(items=[('SCALE',"Scale",""), ('OFFSET',"Offset","")], default='SCALE')
    
    def _set_origin(self, context, event):
        region = context.region
        view2d = region.view2d
        mx, my = event.mouse_region_x, event.mouse_region_y
        try:
            frame, value = view2d.region_to_view(mx, my)
        except:
            return
        
        if _keyframe_cache.needs_update(context):
            _keyframe_cache.update(context, view2d)
        
        grid_size = _keyframe_cache.grid_size
        grid_x = int(mx / grid_size)
        grid_y = int(my / grid_size)
        
        candidates = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (grid_x + dx, grid_y + dy)
                if key in _keyframe_cache.grid:
                    for entry in _keyframe_cache.grid[key]:
                        _, kp, sx, sy, typ = entry
                        if typ == 'KEYFRAME':
                            dist = math.sqrt((sx - mx)**2 + (sy - my)**2)
                            if dist <= self.selection_radius_px:
                                candidates.append((dist, kp.co[0], kp.co[1]))
        
        if candidates:
            candidates.sort(key=lambda x: x[0])
            self._origin_frame = candidates[0][1]
            self._origin_value = candidates[0][2]
        else:
            self._origin_frame = frame
            self._origin_value = value
        
        self._origin_set = True
        if context.area:
            context.area.tag_redraw()
    
    def _start_interaction(self, context, event):
        self._mouse_pressed = True
        self._drag_started = False
        self._press_pos_x = event.mouse_region_x
        self._press_pos_y = event.mouse_region_y
        self._drawing = True

        if context.region and context.region.view2d:
            if _keyframe_cache.needs_update(context):
                _keyframe_cache.update(context, context.region.view2d)
        context.area.tag_redraw()

    def _handle_click(self, context, event):
        """Simple click → move origin"""
        self._set_origin(context, event)
        self._drawing = False
        context.area.tag_redraw()

    def _start_drag(self, context, event):
        self._drag_started = True
        if not self._range_active:
            self._range_selecting = True
            self._range_start_pos = (self._press_pos_x, self._press_pos_y)
        else:
            self._start_operation(context, event)
        context.area.tag_redraw()

    def _start_operation(self, context, event):
        self._original_keyframes = []
        try:
            self._operation_start_pos = context.region.view2d.region_to_view(
                event.mouse_region_x, event.mouse_region_y
            )
        except:
            self._operation_start_pos = (self._origin_frame, self._origin_value)
        
        for fcurve in get_visible_fcurves(context):
            for idx, kp in enumerate(fcurve.keyframe_points):
                kp_frame = kp.co[0]
                if self._range_active and not (self._range_start_frame <= kp_frame <= self._range_end_frame):
                    continue
                
                self._original_keyframes.append((
                    fcurve, kp, idx, kp.co[0], kp.co[1],
                    tuple(kp.handle_left) if kp.interpolation == 'BEZIER' else None,
                    tuple(kp.handle_right) if kp.interpolation == 'BEZIER' else None,
                    kp.interpolation
                ))

    def _update_interaction(self, context, event):
        if not self._drawing:
            return
        if self._range_selecting:
            try:
                current_frame, _ = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
                start_frame, _ = context.region.view2d.region_to_view(self._range_start_pos[0], self._range_start_pos[1])
                self._range_start_frame = int(min(start_frame, current_frame))
                self._range_end_frame = int(max(start_frame, current_frame))
            except:
                pass
            context.area.tag_redraw()
        elif self._operation_start_pos:
            self._update_operation(context, event)

    def _update_operation(self, context, event):
        try:
            current_frame, current_value = context.region.view2d.region_to_view(
                event.mouse_region_x, event.mouse_region_y
            )
        except:
            return
        
        start_frame, start_value = self._operation_start_pos
        
        if self.operation_mode == 'SCALE':
            frame_scale = 1.0
            value_scale = 1.0
            
            if self.relative_scale:
                start_dist_x = start_frame - self._origin_frame
                current_dist_x = current_frame - self._origin_frame
                start_dist_y = start_value - self._origin_value
                current_dist_y = current_value - self._origin_value
                
                frame_scale = current_dist_x / start_dist_x if abs(start_dist_x) > 0.001 else 1.0
                value_scale = current_dist_y / start_dist_y if abs(start_dist_y) > 0.001 else 1.0
            else:
                frame_scale = 1.0 + (current_frame - start_frame) / 50.0
                value_scale = 1.0 + (current_value - start_value) / 50.0
            
            for fcurve, kp, idx, orig_frame, orig_value, h_left, h_right, interp in self._original_keyframes:
                try:
                    if idx >= len(fcurve.keyframe_points): continue
                    current_kp = fcurve.keyframe_points[idx]
                    
                    if self.scale_mode == 'X':
                        new_frame = round(self._origin_frame + (orig_frame - self._origin_frame) * frame_scale)
                        new_value = orig_value
                    elif self.scale_mode == 'Y':
                        new_frame = orig_frame
                        new_value = self._origin_value + (orig_value - self._origin_value) * value_scale
                    else:
                        new_frame = round(self._origin_frame + (orig_frame - self._origin_frame) * frame_scale)
                        new_value = self._origin_value + (orig_value - self._origin_value) * value_scale
                    
                    current_kp.co = (new_frame, new_value)
                    
                    if interp == 'BEZIER' and h_left and h_right:
                        if self.scale_mode == 'X':
                            new_left = (round(new_frame + (h_left[0] - orig_frame) * frame_scale), new_value + (h_left[1] - orig_value))
                            new_right = (round(new_frame + (h_right[0] - orig_frame) * frame_scale), new_value + (h_right[1] - orig_value))
                        elif self.scale_mode == 'Y':
                            new_left = (new_frame + (h_left[0] - orig_frame), new_value + (h_left[1] - orig_value) * value_scale)
                            new_right = (new_frame + (h_right[0] - orig_frame), new_value + (h_right[1] - orig_value) * value_scale)
                        else:
                            new_left = (round(new_frame + (h_left[0] - orig_frame) * frame_scale), new_value + (h_left[1] - orig_value) * value_scale)
                            new_right = (round(new_frame + (h_right[0] - orig_frame) * frame_scale), new_value + (h_right[1] - orig_value) * value_scale)
                        
                        current_kp.handle_left = new_left
                        current_kp.handle_right = new_right
                    
                    current_kp.select_control_point = True
                    fcurve.select = True
                except:
                    continue
        
        else:  
            frame_delta = current_frame - start_frame
            value_delta = current_value - start_value
            
            for fcurve, kp, idx, orig_frame, orig_value, h_left, h_right, interp in self._original_keyframes:
                try:
                    if idx >= len(fcurve.keyframe_points): continue
                    current_kp = fcurve.keyframe_points[idx]
                    
                    if self.scale_mode == 'X':
                        new_frame = round(orig_frame + frame_delta)
                        new_value = orig_value
                    elif self.scale_mode == 'Y':
                        new_frame = orig_frame
                        new_value = orig_value + value_delta
                    else:
                        new_frame = round(orig_frame + frame_delta)
                        new_value = orig_value + value_delta
                    
                    current_kp.co = (new_frame, new_value)
                    
                    if interp == 'BEZIER' and h_left and h_right:
                        new_left_x = h_left[0] + (frame_delta if self.scale_mode in ['X','BOTH'] else 0)
                        new_left_y = h_left[1] + (value_delta if self.scale_mode in ['Y','BOTH'] else 0)
                        new_right_x = h_right[0] + (frame_delta if self.scale_mode in ['X','BOTH'] else 0)
                        new_right_y = h_right[1] + (value_delta if self.scale_mode in ['Y','BOTH'] else 0)
                        current_kp.handle_left = (round(new_left_x), new_left_y)
                        current_kp.handle_right = (round(new_right_x), new_right_y)
                    
                    current_kp.select_control_point = True
                    fcurve.select = True
                except:
                    continue
        
        _keyframe_cache.last_update_time = 0
        if context.area:
            context.area.tag_redraw()

    def _stop_interaction(self, context, event):
        self._mouse_pressed = False

        if not self._drag_started:
            self._handle_click(context, event)
        else:
            if self._range_selecting:
                self._range_selecting = False
                self._range_active = True
            self._drawing = False
            self._operation_start_pos = None
            self._original_keyframes.clear()

        _keyframe_cache.last_update_time = 0
        if context.region and context.region.view2d:
            _keyframe_cache.update(context, context.region.view2d)
        if context.area:
            context.area.tag_redraw()

    def modal(self, context, event):
        if not context.area or context.area.type != 'GRAPH_EDITOR':
            return self.cancel(context)

        self._current_mouse_x = event.mouse_region_x
        self._current_mouse_y = event.mouse_region_y

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return self.cancel(context)

        if event.type == 'RET' and event.value == 'PRESS':
            return self.finish(context)

        if not self._drawing and not self._range_selecting:
            if event.type == 'O' and event.value == 'PRESS':
                self.operation_mode = 'OFFSET' if self.operation_mode == 'SCALE' else 'SCALE'
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            if event.type == 'X' and event.value == 'PRESS' and self._range_active:
                self._range_active = False
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            if event.type == 'V' and event.value == 'PRESS':
                modes = ['X', 'Y', 'BOTH']
                self.scale_mode = modes[(modes.index(self.scale_mode) + 1) % 3]
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            if event.type == 'R' and event.value == 'PRESS':
                self.relative_scale = not self.relative_scale
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            current_time = time.time()
            if current_time - self._last_scan_time > self._scan_throttle:
                if self._mouse_pressed and not self._drag_started:
                    dx = event.mouse_region_x - self._press_pos_x
                    dy = event.mouse_region_y - self._press_pos_y
                    if math.sqrt(dx**2 + dy**2) > self._drag_threshold:
                        self._start_drag(context, event)

                if self._drawing:
                    self._update_interaction(context, event)
                else:
                    context.area.tag_redraw()
                self._last_scan_time = current_time
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self._start_interaction(context, event)
            elif event.value == 'RELEASE':
                if self._mouse_pressed:
                    dx = event.mouse_region_x - self._press_pos_x
                    dy = event.mouse_region_y - self._press_pos_y
                    if math.sqrt(dx**2 + dy**2) > self._drag_threshold and not self._drag_started:
                        self._start_drag(context, event)
                    self._stop_interaction(context, event)
            return {'RUNNING_MODAL'}

        if event.type in {'Z', 'Y'} and event.ctrl:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area and context.area.type == 'GRAPH_EDITOR':
            context.window_manager.graph_scale_tool_active = True
            
            self._draw_handler = bpy.types.SpaceGraphEditor.draw_handler_add(
                draw_scale_callback, (self, context), 'WINDOW', 'POST_PIXEL'
            )
            
            self._is_running = True
            self._current_mouse_x = event.mouse_region_x
            self._current_mouse_y = event.mouse_region_y
            
            context.window_manager.modal_handler_add(self)
            
            if context.region and context.region.view2d:
                _keyframe_cache.update(context, context.region.view2d)
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active area is not a Graph Editor")
            return {'CANCELLED'}

    def cancel(self, context):
        if self._original_keyframes:
            for fcurve, kp, idx, orig_frame, orig_value, h_left, h_right, interp in self._original_keyframes:
                try:
                    if idx < len(fcurve.keyframe_points):
                        current = fcurve.keyframe_points[idx]
                        current.co = (orig_frame, orig_value)
                        if h_left is not None and h_right is not None:
                            current.handle_left = h_left
                            current.handle_right = h_right
                        current.select_control_point = True
                except:
                    continue
            for area in context.screen.areas:
                if area.type == 'GRAPH_EDITOR':
                    area.tag_redraw()

        self._is_running = False
        self._drawing = False
        self._range_active = False
        self._range_selecting = False
        self._origin_set = False
        context.window_manager.graph_scale_tool_active = False
        
        if self._draw_handler:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self._draw_handler, 'WINDOW')
            self._draw_handler = None
        
        if context.area:
            context.area.tag_redraw()
        return {'CANCELLED'}

    def finish(self, context):
        self._is_running = False
        self._drawing = False
        self._range_active = False
        self._range_selecting = False
        self._origin_set = False
        context.window_manager.graph_scale_tool_active = False
        
        if self._draw_handler:
            bpy.types.SpaceGraphEditor.draw_handler_remove(self._draw_handler, 'WINDOW')
            self._draw_handler = None
        
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


# -------------------------------------------------------------------
# PREFERENCES + HEADER + REGISTRATION (unchanged)
# -------------------------------------------------------------------
class GRAPHScalePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    selection_radius: IntProperty(name="Selection Radius", default=20, min=5, max=100)
    scale_mode: EnumProperty(items=[('X',"X Only",""), ('Y',"Y Only",""), ('BOTH',"Both","")], default='X')
    relative_scale: BoolProperty(default=True)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Tool Settings:", icon='TOOL_SETTINGS')
        box.prop(self, "selection_radius")
        box.prop(self, "scale_mode")
        box.prop(self, "relative_scale")










class GRAPH_MT_Saffron(bpy.types.Menu):
    bl_label = "Saffron"
    bl_idname = "GRAPH_MT_Saffron"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        layout.label(text="Draw", icon='GREASEPENCIL')
        draw_active = getattr(wm, "graph_tracking_active", False)
        draw_icon = 'SORTTIME' if draw_active else 'MOUSE_MOVE'
        draw_text = "Stop Draw" if draw_active else "Start Draw"
        layout.operator("graph.double_click_tracker", text=draw_text, icon=draw_icon)

        layout.separator()

        layout.label(text="Cursor", icon='PIVOT_CURSOR')
        scale_active = getattr(wm, 'graph_scale_tool_active', False)
        if scale_active:
            layout.operator("graph.scale_keyframes", text="Stop Edit", icon='X', depress=True)
        else:
            layout.operator("graph.scale_keyframes", text="Start Edit", icon='HAND')

def draw_saffron_header(self, context):
    if context.area.type == 'GRAPH_EDITOR':
        self.layout.menu("GRAPH_MT_Saffron", text="Koshari")

# -------------------------------------------------------------------
# REGISTER
# -------------------------------------------------------------------
classes = (
    GRAPH_OT_SmartDraw,
    GRAPH_OT_DoubleClickTracker,
    GRAPH_OT_ScaleKeyframes,
    GRAPHScalePreferences,
    GRAPH_MT_Saffron,
)

def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.graph_tracking_active = BoolProperty(default=False)
    bpy.types.WindowManager.graph_scale_tool_active = BoolProperty(default=False)
    bpy.types.GRAPH_MT_editor_menus.append(draw_saffron_header)

def unregister():
    bpy.types.GRAPH_MT_editor_menus.remove(draw_saffron_header)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for prop in ("graph_tracking_active", "graph_scale_tool_active"):
        if hasattr(bpy.types.WindowManager, prop):
            delattr(bpy.types.WindowManager, prop)

if __name__ == "__main__":
    register()