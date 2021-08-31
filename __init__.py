bl_info = {
    "name": "AssetLibraryTools",
    "description": "AssetLibraryTools is a free addon which aims to speed up the process of creating asset libraries with the asset browser, This addon is currently very much experimental as is the asset browser in blender.",
    "author": "Lucian James (LJ3D)",
    "version": (0, 1, 7),
    "blender": (3, 0, 0),
    "location": "3D View > Tools",
    "warning": "Developed in 3.0 ALPHA. May be unstable or broken in future versions", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/LJ3D/AssetLibraryTools/wiki",
    "tracker_url": "https://github.com/LJ3D/AssetLibraryTools",
    "category": "3D View"
}

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )
import pathlib
import re
import os


# ------------------------------------------------------------------------
#    Stuff
# ------------------------------------------------------------------------ 

diffNames = ["diffuse", "diff", "albedo", "base", "col", "color"]
sssNames = ["sss", "subsurface"]
metNames = ["metallic", "metalness", "metal", "mtl", "met"]
specNames = ["specularity", "specular", "spec", "spc"]
roughNames = ["roughness", "rough", "rgh", "gloss", "glossy", "glossiness"]
normNames = ["normal", "nor", "nrm", "nrml norm"]
dispNames = ["displacement", "displace", "disp", "dsp", "height", "heightmap", "bump", "bmp"]
alphaNames = ["alpha", "opacity"]
emissiveNames = ["emissive", "emission"]

# Find the type of PBR texture a file is based on its name
def FindPBRTextureType(fname):
    # Split filename into components
    # 'WallTexture_diff_2k.002.jpg' -> ['Wall', 'Texture', 'diff', 'k']
    # Remove digits
    fname = ''.join(i for i in fname if not i.isdigit())
    # Separate CamelCase by space
    fname = re.sub("([a-z])([A-Z])","\g<1> \g<2>",fname)
    # Replace common separators with SPACE
    seperators = ['_', '.', '-', '__', '--', '#']
    for sep in seperators:
        fname = fname.replace(sep, ' ')
    components = fname.split(' ')
    components = [c.lower() for c in components]
    
    # This is probably not the best way to do this lol
    PBRTT = None
    for i in components:
        if i in diffNames:
            PBRTT = "diff"
        if i in sssNames:
            PBRTT = "sss"
        if i in metNames:
            PBRTT = "met"
        if i in specNames:
            PBRTT = "spec"
        if i in roughNames:
            PBRTT = "rough"
        if i in normNames:
            PBRTT = "norm"
        if i in dispNames:
            PBRTT = "disp"
        if i in alphaNames:
            PBRTT = "alpha"
        if i in emissiveNames:
            PBRTT = "emission"
    return PBRTT

# Display a message in the blender UI
def DisplayMessageBox(message = "", title = "Info", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# Class with functions for setting up shaders
class shaderSetup():
    
    def createNode(mat, type, name="newNode", location=(0,0)):
        nodes = mat.node_tree.nodes
        n = nodes.new(type=type)
        n.name = name
        n.location = location
        return n
    
    def simplePrincipledSetup(name, files):
        tool = bpy.context.scene.assetlibrarytools
        # Create a new empty material
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links 
        nodes.clear() # Delete all nodes
        
        # Load textures
        diffuseTexture = None
        sssTexture = None
        metallicTexture = None
        specularTexture = None
        roughnessTexture = None
        emissionTexture = None
        alphaTexture = None
        normalTexture = None
        displacementTexture = None
        for i in files:
            t = FindPBRTextureType(i.name)
            if t == "diff":
                diffuseTexture = bpy.data.images.load(str(i))
            elif t == "sss":
                sssTexture = bpy.data.images.load(str(i))
                sssTexture.colorspace_settings.name = 'Non-Color'
            elif t == "met":
                metallicTexture = bpy.data.images.load(str(i))
                metallicTexture.colorspace_settings.name = 'Non-Color'
            elif t == "spec":
                specularTexture = bpy.data.images.load(str(i))
                specularTexture.colorspace_settings.name = 'Non-Color'
            elif t == "rough":
                roughnessTexture = bpy.data.images.load(str(i))
                roughnessTexture.colorspace_settings.name = 'Non-Color'
            elif t == "emission":
                emissionTexture = bpy.data.images.load(str(i))  
            elif t == "alpha":
                alphaTexture = bpy.data.images.load(str(i))
                alphaTexture.colorspace_settings.name = 'Non-Color'
            elif t == "norm":
                normalTexture = bpy.data.images.load(str(i))
                normalTexture.colorspace_settings.name = 'Non-Color'
            elif t == "disp":
                displacementTexture = bpy.data.images.load(str(i))
                displacementTexture.colorspace_settings.name = 'Non-Color'
        
        # Create base nodes
        node_output = shaderSetup.createNode(mat, "ShaderNodeOutputMaterial", "node_output", (250,0))
        node_principled = shaderSetup.createNode(mat, "ShaderNodeBsdfPrincipled", "node_principled", (-300,0))
        node_mapping = shaderSetup.createNode(mat, "ShaderNodeMapping", "node_mapping", (-1300,0))
        node_texCoord = shaderSetup.createNode(mat, "ShaderNodeTexCoord", "node_texCoord", (-1500,0))
        # Link base nodes
        links.new(node_principled.outputs[0], node_output.inputs[0])
        links.new(node_texCoord.outputs[2], node_mapping.inputs[0])
        
        # Create, fill, and link texture nodes
        imported_tex_nodes = 0
        if diffuseTexture != None and tool.import_diff != False:
            node_imTexDiffuse = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexDiffuse", (-800,300-(300*imported_tex_nodes)))
            node_imTexDiffuse.image = diffuseTexture
            links.new(node_imTexDiffuse.outputs[0], node_principled.inputs[0])
            links.new(node_mapping.outputs[0], node_imTexDiffuse.inputs[0])
            imported_tex_nodes += 1
            
        if sssTexture != None and tool.import_sss != False:
            node_imTexSSS = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexSSS", (-800,300-(300*imported_tex_nodes)))
            node_imTexSSS.image = sssTexture
            links.new(node_imTexSSS.outputs[0], node_principled.inputs[1])
            links.new(node_mapping.outputs[0], node_imTexSSS.inputs[0])
            imported_tex_nodes += 1
            
        if metallicTexture != None and tool.import_met != False:
            node_imTexMetallic = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexMetallic", (-800,300-(300*imported_tex_nodes)))
            node_imTexMetallic.image = metallicTexture
            links.new(node_imTexMetallic.outputs[0], node_principled.inputs[4])
            links.new(node_mapping.outputs[0], node_imTexMetallic.inputs[0])
            imported_tex_nodes += 1
            
        if specularTexture != None and tool.import_spec != False:
            node_imTexSpecular = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexSpecular", (-800,300-(300*imported_tex_nodes)))
            node_imTexSpecular.image = specularTexture
            links.new(node_imTexSpecular.outputs[0], node_principled.inputs[5])
            links.new(node_mapping.outputs[0], node_imTexSpecular.inputs[0])
            imported_tex_nodes += 1
            
        if roughnessTexture != None and tool.import_rough != False:
            node_imTexRoughness = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexRoughness", (-800,300-(300*imported_tex_nodes)))
            node_imTexRoughness.image = roughnessTexture
            links.new(node_imTexRoughness.outputs[0], node_principled.inputs[7])
            links.new(node_mapping.outputs[0], node_imTexRoughness.inputs[0])
            imported_tex_nodes += 1
            
        if emissionTexture != None and tool.import_emission != False:
            node_imTexEmission = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexEmission", (-800,300-(300*imported_tex_nodes)))
            node_imTexEmission.image = emissionTexture
            links.new(node_imTexEmission.outputs[0], node_principled.inputs[17])
            links.new(node_mapping.outputs[0], node_imTexEmission.inputs[0])
            imported_tex_nodes += 1
            
        if alphaTexture != None and tool.import_alpha != False:
            node_imTexAlpha = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexAlpha", (-800,300-(300*imported_tex_nodes)))
            node_imTexAlpha.image = alphaTexture
            links.new(node_imTexAlpha.outputs[0], node_principled.inputs[19])
            links.new(node_mapping.outputs[0], node_imTexAlpha.inputs[0])
            imported_tex_nodes += 1
            
        if normalTexture != None and tool.import_norm != False:
            node_imTexNormal = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexNormal", (-800,300-(300*imported_tex_nodes)))
            node_imTexNormal.image = normalTexture
            node_normalMap = shaderSetup.createNode(mat, "ShaderNodeNormalMap", "node_normalMap", (-500,300-(300*imported_tex_nodes)))
            links.new(node_imTexNormal.outputs[0], node_normalMap.inputs[1])
            links.new(node_normalMap.outputs[0], node_principled.inputs[20])
            links.new(node_mapping.outputs[0], node_imTexNormal.inputs[0])
            imported_tex_nodes += 1
            
        if displacementTexture != None and tool.import_disp != False:
            node_imTexDisplacement = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexDisplacement", (-800,300-(300*imported_tex_nodes)))
            node_imTexDisplacement.image = displacementTexture
            node_displacement = shaderSetup.createNode(mat, "ShaderNodeDisplacement", "node_displacement", (-200,-600))
            links.new(node_imTexDisplacement.outputs[0], node_displacement.inputs[0])
            links.new(node_displacement.outputs[0], node_output.inputs[2])
            links.new(node_mapping.outputs[0], node_imTexDisplacement.inputs[0])
            imported_tex_nodes += 1
        
        return mat


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
        name = "Search for .blend files in surbdirs recursively",
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
    attributeFilter : EnumProperty(
        name="Attribute filter",
        description="Choose attribute to filter assets by",
        items=[ ('None', "None", ""),
                ('1K-JPG', "1K-JPG", ""),
                ('2K-JPG', "2K-JPG", ""),
                ('4K-JPG', "4K-JPG", ""),
                ('8K-JPG', "8K-JPG", ""),
                ('1K-PNG', "1K-PNG", ""),
                ('2K-PNG', "2K-PNG", ""),
                ('4K-PNG', "4K-PNG", ""),
                ('8K-PNG', "8K-PNG", ""),
               ]
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
    terminal : EnumProperty(
        name="Terminal",
        description="Choose terminal to run script with",
        items=[ ('cmd', "cmd", ""),
                ('gnome-terminal', "gnome-terminal", ""),
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
    sbsarImport_expanded : BoolProperty(
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
    assetDownloaderRow_expanded : BoolProperty(
        name = "Click to expand",
        description = "",
        default = False
        )


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class OT_BatchImportPBR(Operator):
    bl_label = "Import PBR textures"
    bl_idname = "alt.batchimportpbr"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        n_imp = 0 # Number of materials imported
        n_del = 0 # Number of materials deleted (due to no textures after import)
        n_skp = 0 # Number of materials skipped due to them already existing
        existing_mat_names = []
        subdirectories = [x for x in pathlib.Path(tool.mat_import_path).iterdir() if x.is_dir()] # Get subdirs in directory selected in UI
        for sd in subdirectories:
            filePaths = [x for x in pathlib.Path(sd).iterdir() if x.is_file()] # Get filepaths of textures
            # Get existing material names if skipping existing materials is turned on
            if tool.skip_existing == True:
                existing_mat_names = []
                for mat in bpy.data.materials:
                    existing_mat_names.append(mat.name)
            # check if the material thats about to be imported exists or not, or if we dont care about skipping existing materials.
            if (sd.name not in existing_mat_names) or (tool.skip_existing != True):
                mat = shaderSetup.simplePrincipledSetup(sd.name, filePaths) # Create shader using filepaths of textures
                if tool.use_fake_user == True: # Enable fake user (if desired)
                    mat.use_fake_user = True
                if tool.use_real_displacement == True: # Enable real displacement (if desired)
                    mat.cycles.displacement_method = 'BOTH'
                # Delete the material if it contains no textures
                hasTex = False
                for n in mat.node_tree.nodes: 
                    if n.type == 'TEX_IMAGE': # Check if shader contains textures, if yes, then its worth keeping
                        hasTex = True
                if hasTex == False:
                    bpy.data.materials.remove(mat) # Delete material if it contains no textures
                    n_del += 1
                else:
                    n_imp += 1
            else:
                n_skp += 1
        if (n_del > 0) and (n_skp > 0):
            DisplayMessageBox("Complete, {0} materials imported, {1} were deleted after import because they contained no textures (No recognised textures were found in the folder), {2} skipped because they already exist".format(n_imp,n_del,n_skp))
        elif n_skp > 0:
            DisplayMessageBox("Complete, {0} materials imported. {1} skipped because they already exist".format(n_imp, n_skp))
        elif n_del > 0:
            DisplayMessageBox("Complete, {0} materials imported, {1} were deleted after import because they contained no textures (No recognised textures were found in the folder)".format(n_imp,n_del))
        else:
            DisplayMessageBox("Complete, {0} materials imported".format(n_imp))
        return{'FINISHED'}


class OT_ImportModels(Operator):
    bl_label = "Import models"
    bl_idname = "alt.importmodels"
    
    # Hide new objects works by comparing a list of objects before (x) happened with the current list via bpy.context.scene.objects to get the list of new objects, then hides those new objects
    def hideNewObjects(old_objects):
        scene = bpy.context.scene
        tool = scene.assetlibrarytools
        imported_objects = set(bpy.context.scene.objects) - old_objects
        if tool.hide_after_import == True:
            for object in imported_objects:
                object.hide_set(True)
    
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        p = pathlib.Path(str(tool.model_import_path))
        i = 0 # Number of imported objects
        # Import FBX files
        if tool.import_fbx == True:
            fbxFilePaths = [x for x in p.glob('**/*.fbx') if x.is_file()] # Get filepaths of files with the extension .fbx in the selected directory (and subdirs, recursively)
            for filePath in fbxFilePaths:
                old_objects = set(context.scene.objects)
                bpy.ops.import_scene.fbx(filepath=str(filePath))
                OT_ImportModels.hideNewObjects(old_objects)
                i += 1
        # Import GLTF files
        if tool.import_gltf == True:
            gltfFilePaths = [x for x in p.glob('**/*.gltf') if x.is_file()] # Get filepaths of files with the extension .gltf in the selected directory (and subdirs, recursively)
            for filePath in gltfFilePaths:
                old_objects = set(context.scene.objects)
                bpy.ops.import_scene.gltf(filepath=str(filePath))
                OT_ImportModels.hideNewObjects(old_objects)
                i += 1
        # Import OBJ files
        if tool.import_obj == True:
            objFilePaths = [x for x in p.glob('**/*.obj') if x.is_file()] # Get filepaths of files with the extension .obj in the selected directory (and subdirs, recursively)
            for filePath in objFilePaths:
                old_objects = set(context.scene.objects)
                bpy.ops.import_scene.obj(filepath=str(filePath))
                OT_ImportModels.hideNewObjects(old_objects)
                i += 1
        # Import X3D files
        if tool.import_x3d == True:
            x3dFilePaths = [x for x in p.glob('**/*.x3d') if x.is_file()] # Get filepaths of files with the extension .x3d in the selected directory (and subdirs, recursively)
            for filePath in x3dFilePaths:
                old_objects = set(context.scene.objects)
                bpy.ops.import_scene.x3d(filepath=str(filePath))
                OT_ImportModels.hideNewObjects(old_objects)
                i += 1
        DisplayMessageBox("Complete, {0} models imported".format(i))
        return{'FINISHED'}


class OT_BatchAppend(Operator):
    bl_label = "Append"
    bl_idname = "alt.batchappend"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        p = pathlib.Path(str(tool.append_path))
        link = False # append, set to true to keep the link to the original file
        if tool.append_recursive_search == True:
            blendFilePaths = [x for x in p.glob('**/*.blend') if x.is_file()] # Get filepaths of files with the extension .blend in the selected directory (and subdirs, recursively)
        else:
            blendFilePaths = [x for x in p.glob('*.blend') if x.is_file()] # Get filepaths of files with the extension .blend in the selected directory    
        for path in blendFilePaths:
            if tool.appendType == 'objects':
                # link all objects
                with bpy.data.libraries.load(str(path), link=link) as (data_from, data_to):
                    data_to.objects = data_from.objects
                #link object to current scene
                for obj in data_to.objects:
                    removed = False
                    if obj is not None:
                       #bpy.context.scene.objects.link(obj) # Blender 2.7x
                       bpy.context.collection.objects.link(obj) # Blender 2.8x   
                    # remove cameras
                    if removed == False and tool.deleteCameras == True: # This stops an error from occuring if obj is already deleted
                        if obj.type == 'CAMERA':
                            bpy.data.objects.remove(obj)
                            removed = True      
                    # remove lights
                    if removed == False and tool.deleteLights == True: # This stops an error from occuring if obj is already deleted
                        if obj.type == 'LIGHT':
                            bpy.data.objects.remove(obj)
                            removed = True
            if tool.appendType == 'materials':
                with bpy.data.libraries.load(str(path), link=link) as (data_from, data_to):
                    data_to.materials = data_from.materials
        if tool.appendType == 'objects':
             DisplayMessageBox("Complete, objects appended")
        if tool.appendType == 'materials':
            DisplayMessageBox("Complete, materials appended")
        return{'FINISHED'}


class OT_ManageAssets(Operator):
    bl_label = "Go"
    bl_idname = "alt.manageassets"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        i = 0 # Number of assets modified
        # Mark assets
        if tool.markunmark == 'mark':
            if tool.assettype == 'objects':
                for object in bpy.data.objects:
                    object.asset_mark()
                    i += 1
            if tool.assettype == 'materials':
                for mat in bpy.data.materials:
                    mat.asset_mark()
                    i += 1
            if tool.assettype == 'images':
                for image in bpy.data.images:
                    image.asset_mark()
                    i += 1      
            if tool.assettype == 'textures':
                for texture in bpy.data.textures:
                    texture.asset_mark()
                    i += 1   
            if tool.assettype == 'meshes':
                for mesh in bpy.data.meshes:
                    mesh.asset_mark()
                    i += 1
            DisplayMessageBox("Complete, {0} assets marked".format(i))
        # Unmark assets
        if tool.markunmark == 'unmark':
            if tool.assettype == 'objects':
                for object in bpy.data.objects:
                    object.asset_clear()
                    i += 1
            if tool.assettype == 'materials':
                for mat in bpy.data.materials:
                    mat.asset_clear()
                    i += 1 
            if tool.assettype == 'images':
                for image in bpy.data.images:
                    image.asset_clear()
                    i += 1  
            if tool.assettype == 'textures':
                for texture in bpy.data.textures:
                    texture.asset_clear()
                    i += 1
            if tool.assettype == 'meshes':
                for mesh in bpy.data.meshes:
                    mesh.asset_clear()
                    i += 1
            DisplayMessageBox("Complete, {0} assets unmarked".format(i))
        return {'FINISHED'}


class OT_BatchDelete(Operator):
    bl_label = "Go"
    bl_idname = "alt.batchdelete"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        i = 0 # Number of items deleted
        if tool.deleteType == 'objects':
            for object in bpy.data.objects:
                bpy.data.objects.remove(object)
                i += 1
        if tool.deleteType == 'materials':
            for mat in bpy.data.materials:
                bpy.data.materials.remove(mat)
                i += 1
        if tool.deleteType == 'images':
            while len(bpy.data.images) > 0: # Cant use a for loop like the other "delete all" operations for some reason
                bpy.data.images.remove(bpy.data.images[0])
                i += 1
        if tool.deleteType == 'textures':
            for tex in bpy.data.textures:
                bpy.data.textures.remove(tex)
                i += 1    
        if tool.deleteType == 'meshes':
            for mesh in bpy.data.meshes:
                bpy.data.meshes.remove(mesh)
                i += 1
        DisplayMessageBox("Done, {0} {1} deleted".format(i, tool.deleteType))
        return {'FINISHED'}


class OT_UseDisplacementOnAll(Operator):
    bl_label = "Use real displacement on all materials"
    bl_idname = "alt.userealdispall"
    def execute(self, context):
        for mat in bpy.data.materials:
            mat.cycles.displacement_method = 'BOTH'
        DisplayMessageBox("Done")
        return {'FINISHED'}


class OT_ChangeAllDisplacementScale(Operator):
    bl_label = "Change displacement scale on all materials"
    bl_idname = "alt.changealldispscale"
    def execute(self, context):
        tool = context.scene.assetlibrarytools
        i = 0 # number of nodes changed
        for mat in bpy.data.materials:
            if mat is not None and mat.use_nodes and mat.node_tree is not None:
                for node in mat.node_tree.nodes:
                    if node.type == 'DISPLACEMENT':
                        node.inputs[2].default_value = tool.dispNewScale
                        i += 1
        DisplayMessageBox("Done, {0} nodes changed".format(i,))
        return {'FINISHED'}


class OT_AssetDownloaderOperator(Operator):
    bl_label = "Run script"
    bl_idname = "alt.assetdownloader"
    def execute(self, context):
        tool = context.scene.assetlibrarytools
        ur = bpy.utils.user_resource('SCRIPTS')
        # Do some input checking
        if tool.downloader_save_path == '':
            DisplayMessageBox("Enter a save path", "Warning", "ERROR")
        if tool.keywordFilter == "":
            tool.keywordFilter = 'None'
        # Start ALT_CC0AssetDownloader.py via chosen terminal
        if tool.terminal == 'gnome-terminal':
            os.system('gnome-terminal -e "python3 {0}/ALT_CC0AssetDownloader.py {1} {2} {3} {4} {5} {6} {7}"'.format(ur+'/addons/AssetLibraryTools', tool.downloader_save_path, tool.keywordFilter, tool.attributeFilter, tool.extensionFilter, str(tool.unZip), str(tool.deleteZips), str(tool.skipDuplicates)))
        if tool.terminal == 'cmd':
            os.system('start cmd /k \"cd /D {0} & python ALT_CC0AssetDownloader.py {1} {2} {3} {4} {5} {6} {7}'.format(ur+'\\addons\\AssetLibraryTools', tool.downloader_save_path, tool.keywordFilter, tool.attributeFilter, tool.extensionFilter, str(tool.unZip), str(tool.deleteZips), str(tool.skipDuplicates)))  
        return {'FINISHED'}


class OT_ImportSBSAR(Operator):
    bl_label = "Import SBSAR files"
    bl_idname = "alt.importsbsar"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        p = pathlib.Path(str(tool.sbsar_import_path))
        i = 0 # number of files imported
        files = [x for x in p.glob('**/*.sbsar') if x.is_file()] # Get filepaths of files with the extension .sbsar in the selected directory (and subdirs, recursively)
        for f in files:
            try:
                bpy.ops.substance.load_sbsar(filepath=str(f), description_arg=True, files=[{"name":f.name, "name":f.name}], directory=str(f).replace(f.name, ""))
                i += 1
            except:
                print("SBSAR import failure")
        DisplayMessageBox("Complete, {0} sbsar files imported".format(i))
        return{'FINISHED'}


# ------------------------------------------------------------------------
#    UI
# ------------------------------------------------------------------------

class OBJECT_PT_panel(Panel):
    bl_label = "AssetLibraryTools"
    bl_idname = "OBJECT_PT_assetlibrarytools_panel"
    bl_category = "AssetLibraryTools"
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
                matImportBox.separator()
                matImportBox.label(text="Material settings:")
                matImportBox.prop(tool, "use_fake_user")
                matImportBox.prop(tool, "use_real_displacement")
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
            utilBox.prop(tool, "dispNewScale")
            utilBox.operator("alt.changealldispscale")
            utilBox.separator()
            utilBox.operator("alt.userealdispall")
            
        
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
            assetDownloaderBox.prop(tool, "downloader_save_path")
            assetDownloaderBox.label(text='Make sure to uncheck "Relative Path"!', icon="ERROR")
            assetDownloaderBox.prop(tool, "keywordFilter")
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


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    properties,
    OT_BatchImportPBR,
    OT_ImportModels,
    OT_BatchAppend,
    OT_ManageAssets,
    OT_BatchDelete,
    OT_UseDisplacementOnAll,
    OT_ChangeAllDisplacementScale,
    OT_AssetDownloaderOperator,
    OT_ImportSBSAR,
    OBJECT_PT_panel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.assetlibrarytools = PointerProperty(type=properties)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.assetlibrarytools

if __name__ == "__main__":
    register()
