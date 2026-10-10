import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, FloatProperty, PointerProperty
from mathutils import Quaternion










_SEPARATORS = ".-_ :"


_SIDE_TOKENS = (
    ("left", "right"),
    ("Left", "Right"),
    ("LEFT", "RIGHT"),
    ("l", "r"),
    ("L", "R"),
)


_EMBEDDED_TOKENS = (
    ("Left", "Right"),
    ("left", "right"),
    ("LEFT", "RIGHT"),
)


def _swap_token(word):
    """Return (opposite word, side of the word given) or (None, None)."""
    for a, b in _SIDE_TOKENS:
        if word == a:
            return b, 'L'
        if word == b:
            return a, 'R'
    return None, None


def _swap_embedded(base):
    """Swap a Left/Right word sitting inside a name, such as 'mixamorig:LeftHand'."""
    for a, b in _EMBEDDED_TOKENS:
        i = base.find(a)
        j = base.find(b)
        if i != -1 and (j == -1 or i < j):
            return base[:i] + b + base[i + len(a):], 'L'
        if j != -1:
            return base[:j] + a + base[j + len(b):], 'R'
    return None, None


def _opposite_name(name):
    """Return (opposite side name, side) or (None, None) for a centre bone."""
    if len(name) < 2:
        return None, None

    base, number = name, ""
    dot = base.rfind(".")
    if dot > 0 and base[dot + 1:].isdigit():
        number = base[dot:]
        base = base[:dot]

    
    for i in range(len(base) - 1, 0, -1):
        if base[i] in _SEPARATORS:
            swapped, side = _swap_token(base[i + 1:])
            if swapped is not None:
                return base[:i + 1] + swapped + number, side
            break

    
    for i in range(1, len(base)):
        if base[i] in _SEPARATORS:
            swapped, side = _swap_token(base[:i])
            if swapped is not None:
                return swapped + base[i:] + number, side
            break

    
    swapped, side = _swap_embedded(base)
    if swapped is not None:
        return swapped + number, side

    
    flipper = getattr(bpy.utils, "flip_name", None)
    if flipper is not None:
        try:
            flipped = flipper(name)
        except Exception:
            flipped = name
        if flipped and flipped != name:
            
            
            return flipped, ('L' if name < flipped else 'R')

    return None, None

















_AXIS_INDEX = {
    'location': (("x", 0), ("y", 1), ("z", 2)),
    'scale': (("x", 0), ("y", 1), ("z", 2)),
    'rotation_euler': (("x", 0), ("y", 1), ("z", 2)),
    'rotation_quaternion': (("w", 0), ("x", 1), ("y", 2), ("z", 3)),
    'rotation_axis_angle': (("w", 0), ("x", 1), ("y", 2), ("z", 3)),
}


def _read_quaternion(owner):
    """Read a bone or object rotation as a quaternion, whatever its mode."""
    mode = owner.rotation_mode
    if mode == 'QUATERNION':
        return Quaternion(owner.rotation_quaternion)
    if mode == 'AXIS_ANGLE':
        aa = owner.rotation_axis_angle
        return Quaternion((aa[1], aa[2], aa[3]), aa[0])
    return owner.rotation_euler.to_quaternion()


def _flip_quaternion(quat):
    return Quaternion((quat.w, quat.x, -quat.y, -quat.z))


def _quaternion_to_owner_mode(quat, owner):
    """Express a quaternion in whatever rotation mode the target uses."""
    mode = owner.rotation_mode
    if mode == 'QUATERNION':
        return 'rotation_quaternion', [quat.w, quat.x, quat.y, quat.z]
    if mode == 'AXIS_ANGLE':
        axis, angle = quat.to_axis_angle()
        return 'rotation_axis_angle', [angle, axis.x, axis.y, axis.z]
    
    
    eul = quat.to_euler(mode, owner.rotation_euler)
    return 'rotation_euler', [eul.x, eul.y, eul.z]


def _reciprocal(value):
    """The other side of one, leaving a flat scale of zero where it is."""
    if abs(value) < 1e-6:
        return value
    return 1.0 / value













def _bone_selected(pb):
    value = getattr(pb, "select", None)           
    if value is None:
        value = getattr(pb.bone, "select", False)  
    return bool(value)


def _bone_hidden(pb):
    value = getattr(pb, "hide", None)
    if value is None:
        value = getattr(pb.bone, "hide", False)
    return bool(value)


def _selected_pose_bones(context, obj):
    """The selected, visible bones of the armature being posed."""
    bones = getattr(context, "selected_pose_bones_from_active_object", None)
    if bones is None:
        bones = getattr(context, "selected_pose_bones", None)
        if bones is not None:
            bones = [pb for pb in bones if pb.id_data.name == obj.name]
    if bones is not None:
        return list(bones)
    return [pb for pb in obj.pose.bones
            if _bone_selected(pb) and not _bone_hidden(pb)]












def _build_pairs(context):
    """Return (pairs, unpaired count).

    A pair is (source object, source bone, target object, target bone). Names
    are stored rather than the bones themselves, because these are held on to
    between timer ticks and a pose bone reference does not survive an undo.
    """
    obj = context.object
    if obj is None:
        return [], 0

    pairs = []
    unpaired = 0
    claimed = set()

    if obj.type == 'ARMATURE' and obj.mode == 'POSE':
        selected = _selected_pose_bones(context, obj)
        selected_names = {pb.name for pb in selected}
        active = context.active_pose_bone
        active_name = active.name if active is not None else ""

        for pb in selected:
            opposite_name, side = _opposite_name(pb.name)
            other = obj.pose.bones.get(opposite_name) if opposite_name else None

            if other is None or other == pb:
                
                
                
                unpaired += 1
                continue

            if other.name in selected_names:
                
                
                
                
                if other.name == active_name:
                    continue
                if pb.name == active_name:
                    source, target = pb, other
                else:
                    source, target = (pb, other) if side == 'L' else (other, pb)
            else:
                source, target = pb, other

            if target.name == active_name or target.name in claimed:
                continue
            claimed.add(target.name)
            pairs.append((obj.name, source.name, obj.name, target.name))

        return pairs, unpaired

    
    
    objects = list(context.selected_objects)
    if obj not in objects:
        objects.append(obj)
    names = {o.name for o in objects}

    for o in objects:
        opposite_name, side = _opposite_name(o.name)
        other = bpy.data.objects.get(opposite_name) if opposite_name else None

        if other is None or other == o:
            unpaired += 1
            continue

        if other.name in names:
            if other.name == obj.name:
                continue
            if o.name == obj.name:
                source, target = o, other
            else:
                source, target = (o, other) if side == 'L' else (other, o)
        else:
            source, target = o, other

        if target.name == obj.name or target.name in claimed:
            continue
        claimed.add(target.name)
        pairs.append((source.name, "", target.name, ""))

    return pairs, unpaired


def _resolve_owner(obj_name, bone_name):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        return None
    if bone_name:
        if obj.pose is None:
            return None
        return obj.pose.bones.get(bone_name)
    return obj


def _channels_chosen(st):
    if not (st.use_location or st.use_rotation or st.use_scale):
        return False
    return bool(st.use_w or st.use_x or st.use_y or st.use_z)








def _plan(st, pairs):
    entries = []

    for src_obj, src_bone, tgt_obj, tgt_bone in pairs:
        source = _resolve_owner(src_obj, src_bone)
        target = _resolve_owner(tgt_obj, tgt_bone)
        if source is None or target is None:
            
            continue

        def add(prop, index, mirrored, _t=target, _o=tgt_obj, _b=tgt_bone):
            entries.append((_o, _b, prop, index, getattr(_t, prop)[index], mirrored))

        if st.use_location:
            loc = source.location
            mirrored = [-loc[0], loc[1], loc[2]]
            if st.invert:
                mirrored = [-value for value in mirrored]
            for letter, index in _AXIS_INDEX['location']:
                if getattr(st, "use_" + letter):
                    add('location', index, mirrored[index])

        if st.use_rotation:
            quat = _flip_quaternion(_read_quaternion(source))
            if st.invert:
                
                quat = quat.conjugated()
            current = _read_quaternion(target)
            
            if current.dot(quat) < 0.0:
                quat = Quaternion((-quat.w, -quat.x, -quat.y, -quat.z))
            prop, values = _quaternion_to_owner_mode(quat, target)
            for letter, index in _AXIS_INDEX[prop]:
                if getattr(st, "use_" + letter):
                    add(prop, index, values[index])

        if st.use_scale:
            scale = source.scale
            values = [scale[0], scale[1], scale[2]]
            if st.invert:
                values = [_reciprocal(value) for value in values]
            for letter, index in _AXIS_INDEX['scale']:
                if getattr(st, "use_" + letter):
                    add('scale', index, values[index])

    return entries









class _RealTimeState:
    def __init__(self):
        
        self.base = {}
        
        self.pairs = []
        self.pairs_key = None
        self.unpaired = 0
        self.frame = None

    def clear(self):
        self.base.clear()
        self.pairs = []
        self.pairs_key = None
        self.unpaired = 0
        self.frame = None

    def release(self):
        """Hand the driven channels back the pose they held before the mirror."""
        for (obj_name, bone_name, prop, index), value in self.base.items():
            owner = _resolve_owner(obj_name, bone_name)
            if owner is None:
                continue
            try:
                getattr(owner, prop)[index] = value
            except (AttributeError, IndexError, TypeError):
                pass
        self.base.clear()


_realtime = _RealTimeState()


def _realtime_running():
    wm = getattr(bpy.context, "window_manager", None)
    return bool(wm is not None and getattr(wm, "cg_mirror_realtime", False))


def _selection_key(context):
    """What the pairs depend on, so they are only rebuilt when it moves."""
    obj = context.object
    if obj is None:
        return None
    if obj.type == 'ARMATURE' and obj.mode == 'POSE':
        active = context.active_pose_bone
        return (
            obj.name, obj.mode,
            tuple(sorted(pb.name for pb in _selected_pose_bones(context, obj))),
            active.name if active is not None else "",
        )
    return (
        obj.name, obj.mode,
        tuple(sorted(o.name for o in context.selected_objects)),
        obj.name,
    )


def _pairs_for(context):
    key = _selection_key(context)
    if key is None:
        return [], 0
    if key != _realtime.pairs_key:
        _realtime.pairs, _realtime.unpaired = _build_pairs(context)
        _realtime.pairs_key = key
    return _realtime.pairs, _realtime.unpaired


def _realtime_tick(context):
    st = context.scene.cg_mirror
    if not _channels_chosen(st):
        return

    frame = context.scene.frame_current
    if _realtime.frame != frame:
        
        
        _realtime.base.clear()
        _realtime.frame = frame

    pairs, _unpaired = _pairs_for(context)
    if not pairs:
        return

    influence = st.influence
    seen = set()

    for obj_name, bone_name, prop, index, current, mirrored in _plan(st, pairs):
        key = (obj_name, bone_name, prop, index)
        seen.add(key)
        if key not in _realtime.base:
            
            
            _realtime.base[key] = current

        base = _realtime.base[key]
        value = base + influence * (mirrored - base)

        owner = _resolve_owner(obj_name, bone_name)
        if owner is None:
            continue
        values = getattr(owner, prop)
        
        
        if abs(values[index] - value) > 1e-7:
            values[index] = value

    for key in list(_realtime.base.keys()):
        if key not in seen:
            del _realtime.base[key]


def _auto_key_driven(context):
    """Key whatever the mirror drove, so stopping leaves something behind.

    Only runs when Blender's own auto keying is switched on, and only on the
    channels the mirror actually touched.
    """
    if not context.scene.tool_settings.use_keyframe_insert_auto:
        return
    for obj_name, bone_name, prop, index in list(_realtime.base.keys()):
        owner = _resolve_owner(obj_name, bone_name)
        if owner is None:
            continue
        try:
            owner.keyframe_insert(data_path=prop, index=index)
        except (RuntimeError, TypeError):
            pass


def _tag_redraw(context):
    screen = getattr(context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        if area.type in {'VIEW_3D', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR'}:
            area.tag_redraw()


def _influence_update(self, context):
    """The next tick reads the new value, this only keeps the panel live."""
    _tag_redraw(context)


def _option_update(self, context):
    """Axis, channel or Invert changed, so work the mirror out again."""
    if not _realtime_running():
        return
    
    
    
    
    _realtime.release()
    _realtime.pairs_key = None
    _tag_redraw(context)


@persistent
def _clear_on_load(_dummy):
    _realtime.clear()
    wm = getattr(bpy.context, "window_manager", None)
    if wm is not None and hasattr(wm, "cg_mirror_realtime"):
        wm.cg_mirror_realtime = False






class MIRRORPRO_Settings(bpy.types.PropertyGroup):
    """Advanced Mirror options, stored on the Scene."""

    
    use_w: BoolProperty(
        name="W",
        description="Include the W component of quaternion or axis angle rotation",
        default=True, update=_option_update,
    )
    use_x: BoolProperty(
        name="X", description="Include the X component",
        default=True, update=_option_update,
    )
    use_y: BoolProperty(
        name="Y", description="Include the Y component",
        default=True, update=_option_update,
    )
    use_z: BoolProperty(
        name="Z", description="Include the Z component",
        default=True, update=_option_update,
    )

    
    use_location: BoolProperty(
        name="Location", description="Mirror location",
        default=True, update=_option_update,
    )
    use_rotation: BoolProperty(
        name="Rotation",
        description="Mirror rotation, in whatever rotation mode the bone uses",
        default=True, update=_option_update,
    )
    use_scale: BoolProperty(
        name="Scale", description="Mirror scale",
        default=True, update=_option_update,
    )

    
    invert: BoolProperty(
        name="Invert",
        description=(
            "Flip the pose the symmetry bone receives. The bone you have "
            "selected always drives and is never written to, so it stays free "
            "to pose either way. Off is a straight mirror, on turns that "
            "mirror inside out, so the far side swings against the near one "
            "instead of along with it"
        ),
        default=False,
        update=_option_update,
    )

    
    influence: FloatProperty(
        name="Influence",
        description=(
            "How far the symmetry bones travel towards the mirrored pose. "
            "0.0 leaves them alone, 1.0 is a full mirror"
        ),
        default=1.0, min=0.0, max=1.0, subtype='FACTOR',
        update=_influence_update,
    )






class MIRRORPRO_OT_RealTime(bpy.types.Operator):
    """Keep mirroring while you pose, so the symmetry bone follows along. Press again to stop"""

    bl_idname = "motion_path.advanced_mirror_realtime"
    bl_label = "Real Time Mirror"

    _timer = None

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        wm = context.window_manager

        if wm.cg_mirror_realtime:
            
            wm.cg_mirror_realtime = False
            return {'FINISHED'}

        st = context.scene.cg_mirror
        if not _channels_chosen(st):
            self.report({'WARNING'}, "Pick at least one axis and one channel first")
            return {'CANCELLED'}

        _realtime.clear()
        pairs, unpaired = _pairs_for(context)
        if not pairs:
            _realtime.clear()
            if unpaired:
                self.report(
                    {'WARNING'},
                    "No opposite side found. Check the naming, such as .L and .R",
                )
            else:
                self.report({'WARNING'}, "Nothing selected to mirror")
            return {'CANCELLED'}

        _realtime.frame = context.scene.frame_current
        wm.cg_mirror_realtime = True
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)

        message = "Real time mirror on, %d following" % len(pairs)
        if unpaired:
            message += ", %d with no opposite side" % unpaired
        self.report({'INFO'}, message)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm = context.window_manager

        if not wm.cg_mirror_realtime:
            self._finish(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            try:
                _realtime_tick(context)
            except Exception as error:
                print("Advanced Mirror real time stopped:", error)
                wm.cg_mirror_realtime = False
                self._finish(context)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _finish(self, context):
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        
        try:
            _auto_key_driven(context)
        except Exception as error:
            print("Advanced Mirror auto key skipped:", error)
        _realtime.clear()
        _tag_redraw(context)






class MIRRORPRO_PT_AdvancedMirror(bpy.types.Panel):
    """Advanced Mirror section inside the Motion Path Pro panel"""

    bl_idname = "VIEW3D_PT_motion_path_advanced_mirror"
    bl_label = "Advanced Mirror"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Motion Path'
    bl_parent_id = "VIEW3D_PT_motion_path"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        st = context.scene.cg_mirror
        live = context.window_manager.cg_mirror_realtime

        
        axis_box = layout.box()
        axis_box.label(text="Select Axis:")
        row = axis_box.row(align=True)
        row.prop(st, "use_w", text="W")
        row.prop(st, "use_x", text="X")
        row.prop(st, "use_y", text="Y")
        row.prop(st, "use_z", text="Z")

        
        channel_box = layout.box()
        channel_box.label(text="Select Channels:")
        row = channel_box.row(align=True)
        row.prop(st, "use_location", text="Location")
        row.prop(st, "use_rotation", text="Rotation")
        row.prop(st, "use_scale", text="Scale")

        
        layout.prop(st, "invert", text="Invert", icon='ARROW_LEFTRIGHT', toggle=True)


        
        layout.prop(st, "influence", text="Influence", slider=True)

        
        row = layout.row()
        row.scale_y = 1.5
        if live:
            row.operator("motion_path.advanced_mirror_realtime",
                         text="Mirror", icon='MOD_MIRROR', depress=True)
        else:
            row.operator("motion_path.advanced_mirror_realtime",
                         text="Mirror", icon='MOD_MIRROR')







classes = (
    MIRRORPRO_Settings,
    MIRRORPRO_OT_RealTime,
    MIRRORPRO_PT_AdvancedMirror,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.cg_mirror = PointerProperty(type=MIRRORPRO_Settings)
    bpy.types.WindowManager.cg_mirror_realtime = BoolProperty(
        name="Real Time Mirror",
        description="Keep the mirror running while you pose",
        default=False,
    )

    if _clear_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_clear_on_load)


def unregister():
    if _clear_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_clear_on_load)

    wm = getattr(bpy.context, "window_manager", None)
    if wm is not None and hasattr(wm, "cg_mirror_realtime"):
        wm.cg_mirror_realtime = False

    _realtime.clear()

    if hasattr(bpy.types.WindowManager, "cg_mirror_realtime"):
        del bpy.types.WindowManager.cg_mirror_realtime
    if hasattr(bpy.types.Scene, "cg_mirror"):
        del bpy.types.Scene.cg_mirror

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
