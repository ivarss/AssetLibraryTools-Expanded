bl_info = {
    "name": "AssetLibraryTools_Expanded",
    "description": "AssetLibraryTools is a free addon which aims to speed up the process of creating asset libraries with the asset browser, this is an expanded version of that plugin",
    "author": "Lucian James (LJ3D), Kasper Ivarsson (Ivarss)",
    "version": (0, 0, 1),
    "blender": (3, 6, 0),
    "location": "3D View > Tools",
    "warning": "Developed in 3.6 . May be unstable or broken in future versions", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/LJ3D/AssetLibraryTools/wiki",
    "tracker_url": "https://github.com/LJ3D/AssetLibraryTools",
    "category": "3D View"
}


import bpy
from bpy.props import (
    BoolProperty,
    IntProperty,
    StringProperty,
)

from . import operators
from . import preferences
from . import interface


def register():
    operators.register()
    interface.register()
    preferences.register()


def unregister():
    preferences.unregister()
    interface.unregister()
    operators.unregister()
