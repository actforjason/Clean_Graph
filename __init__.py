bl_info = {
    "name" : "Clean Graph",
    "author" : "Hamdi Amer", 
    "description" : "Optimize, streamline & boost animation workflows",
    "blender" : (5, 0, 0),
    "version" : (2, 2, 2),
    "location" : "Graph Editor",
    "warning" : "Most operators in this Addon work only with bones",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "Animation" 
}


import bpy
from . import main_panel, DrawAni, FollowM, keyframede, motionpath, MirrorPro, PinKey, RepeatAr, Koshari, TapAnimi, FixAnimi, Filter

modules = (
    main_panel,
    DrawAni,
    FollowM,
    keyframede,
    motionpath,
    MirrorPro,
    PinKey,
    RepeatAr,
     Koshari,
    TapAnimi,
    FixAnimi,
    Filter,
   
)

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()