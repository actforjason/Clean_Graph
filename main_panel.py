import bpy

class GRAPH_OT_TogglePanel(bpy.types.Operator):
    bl_idname = "graph.toggle_panel"
    bl_label = "Toggle Panel"
    bl_options = {'INTERNAL'}
    panel_index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.show_panels[self.panel_index] = not scene.show_panels[self.panel_index]
        return {'FINISHED'}

class EM_PT_AnimationControlPanel(bpy.types.Panel):
    bl_label = "Animation Control"
    bl_idname = "EM_PT_AnimationControlPanel"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Clean Graph"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        main_col = layout.column(align=True)
        header_box = main_col.box()
        header_row = header_box.row()
        header_row.alignment = 'CENTER'
        header_row.label(text="Panel Menu", icon='MENU_PANEL')
        panel_info = [
            ("Motion Path Panel", 'ANIM_DATA'),
            ("Smart Insert Panel", 'KEYTYPE_KEYFRAME_VEC'),
            ("Pin Keyframe Panel", 'PINNED'),
            ("Draw Animation Panel", 'LINE_DATA'),
            ("Folow Motion Panel", 'ACTION'),
            ("Repeat Animation  Panel", 'RECOVER_LAST'),
            ("Fix Animation Panel", 'SCRIPT'),
            ("Filter Animation Panel", 'OVERLAY'),            
            
        ]
        for i in range(0, len(panel_info), 3):
            box = main_col.box()
            row = box.row()
            for j in range(3):
                index = i + j
                if index < len(panel_info):
                    label, icon = panel_info[index]
                    props = row.operator("graph.toggle_panel", text=label, icon=icon, depress=scene.show_panels[index])
                    props.panel_index = index



def register():
    bpy.types.Scene.show_panels = bpy.props.BoolVectorProperty(
        name="Show Panels",
        size=8,
        default=(False, False, False, False, False, False, False, False),
    )
    bpy.utils.register_class(GRAPH_OT_TogglePanel)
    bpy.utils.register_class(EM_PT_AnimationControlPanel)

def unregister():
    del bpy.types.Scene.show_panels
    bpy.utils.unregister_class(EM_PT_AnimationControlPanel)
    bpy.utils.unregister_class(GRAPH_OT_TogglePanel)