# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty
from nodeitems_utils import node_categories_iter

import operators
import interface



# ------------------------------------------------------------------------
#    Properties
# ------------------------------------------------------------------------ 

class properties(PropertyGroup):
    
    # Material import properties
    mat_import_path : StringProperty(
        name = "Import directory",
        description = "Choose a directory to batch import PBR texture sets from.\nFormat your files like this: ChosenDirectory/PBRTextureName/textureFiles",
        default = "",
        maxlen = 1024,
        subtype = 'DIR_PATH'
        )
    skip_existing : BoolProperty(
        name = "Skip existing",
        description = "Dont import materials if a material with the same name already exists",
        default = True
        )
    tex_ignore_filter : StringProperty(
        name = "Tex name filter",
        description = "Filter unwanted textures by a common string in the name (such as DX, which denotes a directX normal map)",
        default = "",
        maxlen = 1024,
        )
    use_fake_user : BoolProperty(
        name = "Use fake user",
        description = "Use fake user on imported materials",
        default = True
        )
    use_real_displacement : BoolProperty(
        name = "Use real displacement",
        description = "Enable real geometry displacement in the material settings (cycles only)",
        default = False
        )
    add_extranodes : BoolProperty(
        name = "Add utility nodes",
        description = "Adds nodes to the imported materials for easy control",
        default = False
        )
    texture_mapping : EnumProperty(
        name='Mapping',
        default='UV',
        items=[('UV', 'UV', 'Use UVs to control mapping'),
        ('Object', 'Object', 'Wrap texture along world coords')])
    import_diff : BoolProperty(
        name = "Import diffuse",
        description = "",
        default = True
        )
    import_sss : BoolProperty(
        name = "Import SSS",
        description = "",
        default = True
        )
    import_met : BoolProperty(
        name = "Import metallic",
        description = "",
        default = True
        )
    import_spec : BoolProperty(
        name = "Import specularity",
        description = "",
        default = True
        )   
    import_rough : BoolProperty(
        name = "Import roughness",
        description = "",
        default = True
        )
    import_emission : BoolProperty(
        name = "Import emission",
        description = "",
        default = True
        )
    import_alpha : BoolProperty(
        name = "Import alpha",
        description = "",
        default = True
        )
    import_norm : BoolProperty(
        name = "Import normal",
        description = "",
        default = True
        )
    import_disp : BoolProperty(
        name = "Import displacement",
        description = "",
        default = True
        )
    
    
    # Model import properties
    model_import_path : StringProperty(
        name = "Import directory",
        description = "Choose a directory to batch import models from.\nSubdirectories are checked recursively",
        default = "",
        maxlen = 1024,
        subtype = 'DIR_PATH'
        )
    hide_after_import : BoolProperty(
        name = "Hide models after import",
        description = "Reduces viewport polycount, prevents low framerate/crashes.\nHides each model individually straight after import",
        default = False
        )
    move_to_new_collection_after_import : BoolProperty(
        name = "Move models to new collection after import",
        description = "",
        default = False
        )
    join_new_objects : BoolProperty(
        name = "Join all models in each file together after import",
        description = "",
        default = False
        )
    import_fbx : BoolProperty(
        name = "Import FBX files",
        description = "",
        default = True
        )
    import_gltf : BoolProperty(
        name = "Import GLTF files",
        description = "",
        default = True
        )
    import_obj : BoolProperty(
        name = "Import OBJ files",
        description = "",
        default = True
        )
    import_x3d : BoolProperty(
        name = "Import X3D files",
        description = "",
        default = True
        )
        
        
    # Batch append properties
    append_path : StringProperty(
        name = "Import directory",
        description = "Choose a directory to batch append from.",
        default = "",
        maxlen = 1024,
        subtype = 'DIR_PATH'
        )
    append_recursive_search : BoolProperty(
        name = "Search for .blend files in subdirs recursively",
        description = "",
        default = False
        )
    append_move_to_new_collection_after_import : BoolProperty(
        name = "Move objects to new collection after import",
        description = "",
        default = False
        )
    append_join_new_objects : BoolProperty(
        name = "Join all objects in each file together after import",
        description = "",
        default = False
        )
    appendType : EnumProperty(
        name="Append",
        description="Choose type to append",
        items=[ ('objects', "Objects", ""),
                ('materials', "Materials", ""),
                ]
        )
    deleteLights : BoolProperty(
        name = "Dont append lights",
        description = "",
        default = True
        )
    deleteCameras : BoolProperty(
        name = "Dont append cameras",
        description = "",
        default = True
        )
    
    
    # Asset management properties
    markunmark : EnumProperty(
        name="Operation",
        description="Choose whether to mark assets, or unmark assets",
        items=[ ('mark', "Mark assets", ""),
                ('unmark', "Unmark assets", ""),
               ]
        )
    assettype : EnumProperty(
        name="On type",
        description="Choose a type of asset to mark/unmark",
        items=[ ('objects', "Objects", ""),
                ('materials', "Materials", ""),
                ('images', "Images", ""),
                ('textures', "Textures", ""),
                ('meshes', "Meshes", ""),
               ]
        )
    previewgentype : EnumProperty(
        name="Asset type",
        description="Choose a type of asset to mark/unmark",
        items=[ ('objects', "Objects", ""),
                ('materials', "Materials", ""),
                ('images', "Images", ""),
                ('textures', "Textures", ""),
                ('meshes', "Meshes", ""),
               ]
        )
    
    
    # Utilities panel properties
    deleteType : EnumProperty(
        name="Delete all",
        description="Choose type to batch delete",
        items=[ ('objects', "Objects", ""),
                ('materials', "Materials", ""),
                ('images', "Images", ""),
                ('textures', "Textures", ""),
                ('meshes', "Meshes", ""),
               ]
        )
    dispNewScale: FloatProperty(
        name = "New Displacement Scale",
        description = "A float property",
        default = 0.1,
        min = 0.0001
        )
    
    
    # Asset snapshot panel properties
    resolution : IntProperty(
            name="Preview Resolution",
            description="Resolution to render the preview",
            min=1,
            soft_max=500,
            default=256
            )
    
    
    # CC0AssetDownloader properties
    downloader_save_path : StringProperty(
        name = "Save location",
        description = "Choose a directory to save assets to",
        default = "",
        maxlen = 1024,
        subtype = 'DIR_PATH'
        )
    keywordFilter : StringProperty(
        name = "Keyword filter",
        description = "Enter a keyword to filter assets by, leave empty if you do not wish to filter.",
        default = "",
        maxlen = 1024,
        )
    showAllDownloadAttribs: BoolProperty(
        name = "Show all download attributes",
        description = "",
        default = True
        )
    attributeFilter : EnumProperty(
        name="Attribute filter",
        description="Choose attribute to filter assets by",
        items=listDownloadAttribs
        )
    extensionFilter : EnumProperty(
        name="Extension filter",
        description="Choose file extension to filter assets by",
        items=[ ('None', "None", ""),
                ('zip', "ZIP", ""),
                ('obj', "OBJ", ""),
                ('exr', "EXR", ""),
                ('sbsar', "SBSAR", ""),
               ]
        )
    unZip : BoolProperty(
        name = "Unzip downloaded zip files",
        description = "",
        default = True
        )
    deleteZips : BoolProperty(
        name = "Delete zip files after they have been unzipped",
        description = "",
        default = True
        )
    skipDuplicates : BoolProperty(
        name = "Dont download files which already exist",
        description = "",
        default = True
        )
    terminal : EnumProperty(
        name="Terminal",
        description="Choose terminal to run script with",
        items=[ ('cmd', "cmd", ""),
                ('gnome-terminal', "gnome-terminal", ""),
                ('konsole', 'konsole', ""),
                ('xterm', 'xterm', ""),
               ]
        )
    
    
    # SBSAR import properties
    sbsar_import_path : StringProperty(
        name = "Import directory",
        description = "Choose a directory to batch import sbsar files from.\nSubdirectories are checked recursively",
        default = "",
        maxlen = 1024,
        subtype = 'DIR_PATH'
        )
    
    
    # UI properties

    matImport_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    matImportOptions_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    append_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    modelImport_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    modelImportOptions_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    assetBrowserOpsRow_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    utilRow_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    snapshotRow_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    assetDownloaderRow_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )
    sbsarImport_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )

# Principled prefs
class NWPrincipledPreferences(bpy.types.PropertyGroup):
    base_color: StringProperty(
        name='Base Color',
        default='diffuse diff albedo base col color basecolor',
        description='Naming Components for Base Color maps')
    sss_color: StringProperty(
        name='Subsurface Color',
        default='sss subsurface',
        description='Naming Components for Subsurface Color maps')
    metallic: StringProperty(
        name='Metallic',
        default='metallic metalness metal mtl',
        description='Naming Components for metallness maps')
    specular: StringProperty(
        name='Specular',
        default='specularity specular spec spc',
        description='Naming Components for Specular maps')
    normal: StringProperty(
        name='Normal',
        default='normal nor nrm nrml norm',
        description='Naming Components for Normal maps')
    bump: StringProperty(
        name='Bump',
        default='bump bmp',
        description='Naming Components for bump maps')
    rough: StringProperty(
        name='Roughness',
        default='roughness rough rgh',
        description='Naming Components for roughness maps')
    gloss: StringProperty(
        name='Gloss',
        default='gloss glossy glossiness',
        description='Naming Components for glossy maps')
    displacement: StringProperty(
        name='Displacement',
        default='displacement displace disp dsp height heightmap',
        description='Naming Components for displacement maps')
    transmission: StringProperty(
        name='Transmission',
        default='transmission transparency',
        description='Naming Components for transmission maps')
    emission: StringProperty(
        name='Emission',
        default='emission emissive emit',
        description='Naming Components for emission maps')
    alpha: StringProperty(
        name='Alpha',
        default='alpha opacity',
        description='Naming Components for alpha maps')
    ambient_occlusion: StringProperty(
        name='Ambient Occlusion',
        default='ao ambient occlusion',
        description='Naming Components for AO maps')


# Addon prefs
class ALTexpanded(bpy.types.AddonPreferences):
    bl_idname = __package__
    merge_hide: EnumProperty(
        name="Hide Mix nodes",
        items=(
            ("ALWAYS", "Always", "Always collapse the new merge nodes"),
            ("NON_SHADER", "Non-Shader", "Collapse in all cases except for shaders"),
            ("NEVER", "Never", "Never collapse the new merge nodes")
        ),
        default='NON_SHADER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specify whether to collapse them or show the full node with options expanded")
    merge_position: EnumProperty(
        name="Mix Node Position",
        items=(
            ("CENTER", "Center", "Place the Mix node between the two nodes"),
            ("BOTTOM", "Bottom", "Place the Mix node at the same height as the lowest node")
        ),
        default='CENTER',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specify the position of the new nodes")

    show_hotkey_list: BoolProperty(
        name="Show Hotkey List",
        default=False,
        description="Expand this box into a list of all the hotkeys for functions in this addon"
    )
    hotkey_list_filter: StringProperty(
        name="        Filter by Name",
        default="",
        description="Show only hotkeys that have this text in their name",
        options={'TEXTEDIT_UPDATE'}
    )
    show_principled_lists: BoolProperty(
        name="Show Principled naming tags",
        default=False,
        description="Expand this box into a list of all naming tags for principled texture setup"
    )
    principled_tags: bpy.props.PointerProperty(type=NWPrincipledPreferences)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "merge_position")
        col.prop(self, "merge_hide")

        box = layout.box()
        col = box.column(align=True)
        col.prop(
            self,
            "show_principled_lists",
            text='Edit tags for auto texture detection in Principled BSDF setup',
            toggle=True)
        if self.show_principled_lists:
            tags = self.principled_tags

            col.prop(tags, "base_color")
            col.prop(tags, "sss_color")
            col.prop(tags, "metallic")
            col.prop(tags, "specular")
            col.prop(tags, "rough")
            col.prop(tags, "gloss")
            col.prop(tags, "normal")
            col.prop(tags, "bump")
            col.prop(tags, "displacement")
            col.prop(tags, "transmission")
            col.prop(tags, "emission")
            col.prop(tags, "alpha")
            col.prop(tags, "ambient_occlusion")


#
#  REGISTER/UNREGISTER CLASSES
#

classes = (
    NWPrincipledPreferences, ALTexpanded
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)



def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
