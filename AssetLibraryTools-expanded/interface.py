# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel, Menu
from bpy.props import StringProperty
from nodeitems_utils import node_categories_iter, NodeItemCustom

import operators

from .utils.constants import blend_types, geo_combine_operations, operations
from .utils.nodes import get_nodes_links, nw_check, NWBase


class OBJECT_PT_panel(Panel):
    bl_label = "AssetLibraryTools-Expanded"
    bl_idname = "OBJECT_PT_assetlibrarytools-expanded_panel"
    bl_category = "AssetLibraryTools-Expanded"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    
    @classmethod
    def poll(self,context):
        return context.mode

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        tool = scene.assetlibrarytools
        obj = context.scene.assetlibrarytools
        
        
        # Material import UI
        matImportBox = layout.box()
        matImportRow = matImportBox.row()
        matImportRow.prop(obj, "matImport_expanded",
            icon="TRIA_DOWN" if obj.matImport_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        matImportRow.label(text="Batch import PBR texture sets as simple materials")
        if obj.matImport_expanded:
            matImportBox.prop(tool, "mat_import_path")
            matImportBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            matImportBox.operator("alt.batchimportpbr")
            matImportOptionsRow = matImportBox.row()
            matImportOptionsRow.prop(obj, "matImportOptions_expanded",
                icon="TRIA_DOWN" if obj.matImportOptions_expanded else "TRIA_RIGHT",
                icon_only=True, emboss=False
            )
            matImportOptionsRow.label(text="Import options: ")
            if obj.matImportOptions_expanded:
                matImportOptionsRow = matImportBox.row()
                matImportBox.label(text="Import settings:")
                matImportBox.prop(tool, "skip_existing")
                matImportBox.prop(tool, "tex_ignore_filter")
                matImportBox.separator()
                matImportBox.label(text="Material settings:")
                matImportBox.prop(tool, "use_fake_user")
                matImportBox.prop(tool, "use_real_displacement")
                matImportBox.prop(tool, "add_extranodes")
                matImportBox.prop(tool, "texture_mapping")
                matImportBox.separator()
                matImportBox.label(text="Import following textures into materials (if found):")
                matImportBox.prop(tool, "import_diff")
                matImportBox.prop(tool, "import_sss")
                matImportBox.prop(tool, "import_met")
                matImportBox.prop(tool, "import_spec")
                matImportBox.prop(tool, "import_rough")
                matImportBox.prop(tool, "import_emission")
                matImportBox.prop(tool, "import_alpha")
                matImportBox.prop(tool, "import_norm")
                matImportBox.prop(tool, "import_disp")
        
        
        # Model import UI
        modelImportBox = layout.box()
        modelImportRow = modelImportBox.row()
        modelImportRow.prop(obj, "modelImport_expanded",
            icon="TRIA_DOWN" if obj.modelImport_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        modelImportRow.label(text="Batch import 3D models")
        if obj.modelImport_expanded:
            modelImportBox.prop(tool, "model_import_path")
            modelImportBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            modelImportBox.operator("alt.importmodels")
            modelImportOptionsRow = modelImportBox.row()
            modelImportOptionsRow.prop(obj, "modelImportOptions_expanded",
                icon="TRIA_DOWN" if obj.modelImportOptions_expanded else "TRIA_RIGHT",
                icon_only=True, emboss=False
            )
            modelImportOptionsRow.label(text="Import options: ")
            if obj.modelImportOptions_expanded:
                modelImportOptionsRow = modelImportBox.row()
                modelImportBox.label(text="Model options:")
                modelImportBox.prop(tool, "hide_after_import")
                modelImportBox.prop(tool, "move_to_new_collection_after_import")
                modelImportBox.prop(tool, "join_new_objects")
                modelImportBox.separator()
                modelImportBox.label(text="Search for and import the following filetypes:")
                modelImportBox.prop(tool, "import_fbx")
                modelImportBox.prop(tool, "import_gltf")
                modelImportBox.prop(tool, "import_obj")
                modelImportBox.prop(tool, "import_x3d")
        
        
        # Append from other .blend UI
        appendBox = layout.box()
        appendRow = appendBox.row()
        appendRow.prop(obj, "append_expanded",
            icon="TRIA_DOWN" if obj.append_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        appendRow.label(text="Batch append from .blend files")
        if obj.append_expanded:
            appendBox.prop(tool, "append_path")
            appendBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            appendBox.prop(tool, "append_recursive_search")
            appendBox.prop(tool, "append_move_to_new_collection_after_import")
            appendBox.prop(tool, "append_join_new_objects")
            appendBox.prop(tool, "appendType")
            if obj.appendType == 'objects':
                appendBox.prop(tool, "deleteLights")
                appendBox.prop(tool, "deleteCameras")
            appendBox.operator("alt.batchappend")
            
            
        # Asset browser operations UI
        assetBrowserOpsBox = layout.box()
        assetBrowserOpsRow = assetBrowserOpsBox.row()
        assetBrowserOpsRow.prop(obj, "assetBrowserOpsRow_expanded",
            icon="TRIA_DOWN" if obj.assetBrowserOpsRow_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        assetBrowserOpsRow.label(text="Asset browser operations")
        if obj.assetBrowserOpsRow_expanded:
            assetBrowserOpsRow = assetBrowserOpsBox.row()
            assetBrowserOpsBox.label(text="Batch mark/unmark assets:")
            assetBrowserOpsBox.prop(tool, "markunmark")
            assetBrowserOpsBox.prop(tool, "assettype")
            assetBrowserOpsBox.operator("alt.manageassets")
            assetBrowserOpsBox.label(text="Generate asset previews:")
            assetBrowserOpsBox.prop(tool, "previewgentype")
            assetBrowserOpsBox.operator("alt.generateassetpreviews")
            
        
        # Utility operations UI
        utilBox = layout.box()
        utilRow = utilBox.row()
        utilRow.prop(obj, "utilRow_expanded",
            icon="TRIA_DOWN" if obj.utilRow_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        utilRow.label(text="Utilities")
        if obj.utilRow_expanded:
            utilRow = utilBox.row()
            utilBox.prop(tool, "deleteType")
            utilBox.operator("alt.batchdelete")
            utilBox.separator()
            utilBox.label(text='Deletes based on material name, not material contents', icon="ERROR")
            utilBox.operator("alt.simpledeldupemats")
            utilBox.operator("alt.cleanupunusedmats")
            utilBox.separator()
            utilBox.prop(tool, "dispNewScale")
            utilBox.operator("alt.changealldispscale")
            utilBox.operator("alt.userealdispall")
        
        
        #Asset snapshot UI
        snapshotBox = layout.box()
        snapshotRow = snapshotBox.row()
        snapshotRow.prop(obj, "snapshotRow_expanded",
            icon="TRIA_DOWN" if obj.snapshotRow_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        snapshotRow.label(text="Asset snapshot")
        if obj.snapshotRow_expanded:
            snapshotBox.label(text='Sometimes crashes. SAVE YOUR FILES', icon="ERROR")
            snapshotBox.prop(tool, "resolution")
            snapshotBox.operator("view3d.object_preview")
            snapshotBox.operator("view3d.asset_snaphot_collection")
        
        
        # Asset downloader UI
        assetDownloaderBox = layout.box()
        assetDownloaderRow = assetDownloaderBox.row()
        assetDownloaderRow.prop(obj, "assetDownloaderRow_expanded",
            icon="TRIA_DOWN" if obj.assetDownloaderRow_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        assetDownloaderRow.label(text="Batch asset downloader [EXPERIMENTAL]")
        if obj.assetDownloaderRow_expanded:
            assetDownloaderRow = assetDownloaderBox.row()
            assetDownloaderBox.label(text='Downloads files from ambientcg.com')
            assetDownloaderBox.prop(tool, "downloader_save_path")
            assetDownloaderBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            assetDownloaderBox.prop(tool, "keywordFilter")
            assetDownloaderBox.prop(tool, "showAllDownloadAttribs")
            assetDownloaderBox.prop(tool, "attributeFilter")
            assetDownloaderBox.prop(tool, "extensionFilter")
            assetDownloaderBox.prop(tool, "unZip")
            assetDownloaderBox.prop(tool, "deleteZips")
            assetDownloaderBox.prop(tool, "skipDuplicates")
            assetDownloaderBox.prop(tool, "terminal")
            assetDownloaderBox.operator("alt.assetdownloader")
            
        
         # SBSAR import UI
        sbsarImportBox = layout.box()
        sbsarImportRow = sbsarImportBox.row()
        sbsarImportRow.prop(obj, "sbsarImport_expanded",
            icon="TRIA_DOWN" if obj.sbsarImport_expanded else "TRIA_RIGHT",
            icon_only=True, emboss=False
        )
        sbsarImportRow.label(text="Batch import SBSAR files [EXPERIMENTAL]")
        if obj.sbsarImport_expanded:
            sbsarImportBox.label(text="Requires adobe substance 3D add-on for Blender", icon="ERROR")
            sbsarImportBox.prop(tool, "sbsar_import_path")
            sbsarImportBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            sbsarImportBox.operator("alt.importsbsar")


def drawlayout(context, layout, mode='non-panel'):
    tree_type = context.space_data.tree_type

    col = layout.column(align=True)
    col.menu(NWMergeNodesMenu.bl_idname)
    col.separator()

    col = layout.column(align=True)
    col.menu(NWSwitchNodeTypeMenu.bl_idname, text="Switch Node Type")
    col.separator()

    if tree_type == 'ShaderNodeTree':
        col = layout.column(align=True)
        col.operator(operators.NWAddTextureSetup.bl_idname, text="Add Texture Setup", icon='NODE_SEL')
        col.operator(operators.NWAddPrincipledSetup.bl_idname, text="Add Principled Setup", icon='NODE_SEL')
        col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDetachOutputs.bl_idname, icon='UNLINKED')
    col.operator(operators.NWSwapLinks.bl_idname)
    col.menu(NWAddReroutesMenu.bl_idname, text="Add Reroutes", icon='LAYER_USED')
    col.separator()

    col = layout.column(align=True)
    col.menu(NWLinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected", icon='LINKED')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWLinkToOutputNode.bl_idname, icon='DRIVER')
    col.separator()

    col = layout.column(align=True)
    if mode == 'panel':
        row = col.row(align=True)
        row.operator(operators.NWClearLabel.bl_idname).option = True
        row.operator(operators.NWModifyLabels.bl_idname)
    else:
        col.operator(operators.NWClearLabel.bl_idname).option = True
        col.operator(operators.NWModifyLabels.bl_idname)
    col.menu(NWBatchChangeNodesMenu.bl_idname, text="Batch Change")
    col.separator()
    col.menu(NWCopyToSelectedMenu.bl_idname, text="Copy to Selected")
    col.separator()

    col = layout.column(align=True)
    if tree_type == 'CompositorNodeTree':
        col.operator(operators.NWResetBG.bl_idname, icon='ZOOM_PREVIOUS')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWReloadImages.bl_idname, icon='FILE_REFRESH')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWFrameSelected.bl_idname, icon='STICKY_UVS_LOC')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWAlignNodes.bl_idname, icon='CENTER_ONLY')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDeleteUnused.bl_idname, icon='CANCEL')
    col.separator()



classes = (
OBJECT_PT_panel
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)




def unregister():

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
