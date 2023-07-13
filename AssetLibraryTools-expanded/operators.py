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
import time
import random
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy_extras.node_utils import connect_sockets
from mathutils import Vector
from os import path
from glob import glob
from copy import copy
from itertools import chain
import preferences
import interface
# ------------------------------------------------------------------------
#    Stuff
# ------------------------------------------------------------------------ 

diffNames = ["diffuse", "diff", "albedo", "base", "col", "color"]
sssNames = ["sss", "subsurface"]
metNames = ["metallic", "metalness", "metal", "mtl", "met"]
specNames = ["specularity", "specular", "spec", "spc"]
roughNames = ["roughness", "rough", "rgh", "gloss", "glossy", "glossiness"]
normNames = ["normal", "nor", "nrm", "nrml", "norm"]
dispNames = ["displacement", "displace", "disp", "dsp", "height", "heightmap", "bump", "bmp"]
alphaNames = ["alpha", "opacity"]
emissiveNames = ["emissive", "emission"]

nameLists = [diffNames, sssNames, metNames, specNames, roughNames, normNames, dispNames, alphaNames, emissiveNames]
texTypes = ["diff", "sss", "met", "spec", "rough", "norm", "disp", "alpha", "emission"]

# Find the type of PBR texture a file is based on its name
def FindPBRTextureType(fname):
    PBRTT = None
    # Remove digits
    fname = ''.join(i for i in fname if not i.isdigit())
    # Separate CamelCase by space
    fname = re.sub("([a-z])([A-Z])","\g<1> \g<2>",fname)
    # Replace common separators with SPACE
    seperators = ['_', '.', '-', '__', '--', '#']
    for sep in seperators:
        fname = fname.replace(sep, ' ')
    # Set entire string to lower case
    fname = fname.lower()
    # Find PBRTT
    i = 0
    for nameList in nameLists:
        for name in nameList:
            if name in fname:
                PBRTT = texTypes[i]
        i+=1
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
    
    def setMapping(node):
        tool = bpy.context.scene.assetlibrarytools
        if tool.texture_mapping == 'Object':
                node.projection = 'BOX'
                node.projection_blend = 1
    
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
        links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
        node_mapping = shaderSetup.createNode(mat, "ShaderNodeMapping", "node_mapping", (-1300,0))
        node_texCoord = shaderSetup.createNode(mat, "ShaderNodeTexCoord", "node_texCoord", (-1500,0))
        links.new(node_texCoord.outputs[tool.texture_mapping], node_mapping.inputs['Vector'])
        if tool.add_extranodes:
            node_scaleValue = shaderSetup.createNode(mat, "ShaderNodeValue", "node_scaleValue", (-1500, -300))
            node_scaleValue.outputs['Value'].default_value = 1
            links.new(node_scaleValue.outputs['Value'], node_mapping.inputs['Scale'])
        
        # Create, fill, and link texture nodes
        imported_tex_nodes = 0
        if diffuseTexture != None and tool.import_diff != False:
            node_imTexDiffuse = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexDiffuse", (-800,300-(300*imported_tex_nodes)))
            node_imTexDiffuse.image = diffuseTexture
            links.new(node_imTexDiffuse.outputs['Color'], node_principled.inputs['Base Color'])
            links.new(node_mapping.outputs['Vector'], node_imTexDiffuse.inputs['Vector'])
            shaderSetup.setMapping(node_imTexDiffuse)
            imported_tex_nodes += 1
            
        if sssTexture != None and tool.import_sss != False:
            node_imTexSSS = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexSSS", (-800,300-(300*imported_tex_nodes)))
            node_imTexSSS.image = sssTexture
            links.new(node_imTexSSS.outputs['Color'], node_principled.inputs['Subsurface'])
            links.new(node_mapping.outputs['Vector'], node_imTexSSS.inputs['Vector'])
            shaderSetup.setMapping(node_imTexSSS)
            imported_tex_nodes += 1
            
        if metallicTexture != None and tool.import_met != False:
            node_imTexMetallic = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexMetallic", (-800,300-(300*imported_tex_nodes)))
            node_imTexMetallic.image = metallicTexture
            links.new(node_imTexMetallic.outputs['Color'], node_principled.inputs['Metallic'])
            links.new(node_mapping.outputs['Vector'], node_imTexMetallic.inputs['Vector'])
            shaderSetup.setMapping(node_imTexMetallic)
            imported_tex_nodes += 1
            
        if specularTexture != None and tool.import_spec != False:
            node_imTexSpecular = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexSpecular", (-800,300-(300*imported_tex_nodes)))
            node_imTexSpecular.image = specularTexture
            links.new(node_imTexSpecular.outputs['Color'], node_principled.inputs['Specular'])
            links.new(node_mapping.outputs['Vector'], node_imTexSpecular.inputs['Vector'])
            shaderSetup.setMapping(node_imTexSpecular)
            imported_tex_nodes += 1
            
        if roughnessTexture != None and tool.import_rough != False:
            node_imTexRoughness = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexRoughness", (-800,300-(300*imported_tex_nodes)))
            node_imTexRoughness.image = roughnessTexture
            if tool.add_extranodes:
                node_imTexRoughnessColourRamp = shaderSetup.createNode(mat, "ShaderNodeValToRGB", "node_imTexRoughnessColourRamp", (-550,300-(300*imported_tex_nodes)))
                links.new(node_imTexRoughness.outputs['Color'], node_imTexRoughnessColourRamp.inputs['Fac'])
                links.new(node_imTexRoughnessColourRamp.outputs['Color'], node_principled.inputs['Roughness'])
            else:
                links.new(node_imTexRoughness.outputs['Color'], node_principled.inputs['Roughness'])
            links.new(node_mapping.outputs['Vector'], node_imTexRoughness.inputs['Vector'])
            shaderSetup.setMapping(node_imTexRoughness)
            imported_tex_nodes += 1
            
        if emissionTexture != None and tool.import_emission != False:
            node_imTexEmission = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexEmission", (-800,300-(300*imported_tex_nodes)))
            node_imTexEmission.image = emissionTexture
            links.new(node_imTexEmission.outputs['Color'], node_principled.inputs['Emission'])
            links.new(node_mapping.outputs['Vector'], node_imTexEmission.inputs['Vector'])
            shaderSetup.setMapping(node_imTexEmission)
            imported_tex_nodes += 1
            
        if alphaTexture != None and tool.import_alpha != False:
            node_imTexAlpha = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexAlpha", (-800,300-(300*imported_tex_nodes)))
            node_imTexAlpha.image = alphaTexture
            links.new(node_imTexAlpha.outputs['Color'], node_principled.inputs['Alpha'])
            links.new(node_mapping.outputs['Vector'], node_imTexAlpha.inputs['Vector'])
            shaderSetup.setMapping(node_imTexAlpha)
            imported_tex_nodes += 1
            
        if normalTexture != None and tool.import_norm != False:
            node_imTexNormal = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexNormal", (-800,300-(300*imported_tex_nodes)))
            node_imTexNormal.image = normalTexture
            node_normalMap = shaderSetup.createNode(mat, "ShaderNodeNormalMap", "node_normalMap", (-500,300-(300*imported_tex_nodes)))
            links.new(node_imTexNormal.outputs['Color'], node_normalMap.inputs['Color'])
            links.new(node_normalMap.outputs['Normal'], node_principled.inputs['Normal'])
            links.new(node_mapping.outputs['Vector'], node_imTexNormal.inputs['Vector'])
            shaderSetup.setMapping(node_imTexNormal)
            imported_tex_nodes += 1
            
        if displacementTexture != None and tool.import_disp != False:
            node_imTexDisplacement = shaderSetup.createNode(mat, "ShaderNodeTexImage", "node_imTexDisplacement", (-800,300-(300*imported_tex_nodes)))
            node_imTexDisplacement.image = displacementTexture
            node_imTexDisplacement.interpolation = 'Smart'
            node_displacement = shaderSetup.createNode(mat, "ShaderNodeDisplacement", "node_displacement", (-200,-600))
            links.new(node_imTexDisplacement.outputs['Color'], node_displacement.inputs['Height'])
            links.new(node_displacement.outputs['Displacement'], node_output.inputs['Displacement'])
            links.new(node_mapping.outputs['Vector'], node_imTexDisplacement.inputs['Vector'])
            shaderSetup.setMapping(node_imTexDisplacement)
            imported_tex_nodes += 1
        
        return mat


# This code is bad!!!!
# But i dont want to fix it!!!!
# And neither do I!  /Ivarss
def listDownloadAttribs(scene, context):
    scene = context.scene
    tool = scene.assetlibrarytools
    if tool.showAllDownloadAttribs == True:
        attribs = ['None', '1K-JPG', '1K-PNG', '2K-JPG', '2K-PNG', '4K-JPG', '4K-PNG', '8K-JPG', '8K-PNG', '12K-HDR', '16K-HDR', '1K-HDR', '2K-HDR', '4K-HDR', '8K-HDR', '12K-TONEMAPPED', '16K-TONEMAPPED', '1K-TONEMAPPED', '2K-TONEMAPPED', '4K-TONEMAPPED', '8K-TONEMAPPED', '12K-JPG', '12K-PNG', '16K-JPG', '16K-PNG', '1K-HQ-JPG', '1K-HQ-PNG', '1K-LQ-JPG', '1K-LQ-PNG', '1K-SQ-JPG', '1K-SQ-PNG', '2K-HQ-JPG', '2K-HQ-PNG', '2K-LQ-JPG', '2K-LQ-PNG', '2K-SQ-JPG', '2K-SQ-PNG', '4K-HQ-JPG', '4K-HQ-PNG', '4K-LQ-JPG', '4K-LQ-PNG', '4K-SQ-JPG', '4K-SQ-PNG', 'HQ', 'LQ', 'SQ', '24K-JPG', '24K-PNG', '32K-JPG', '32K-PNG', '6K-JPG', '6K-PNG', '2K', '4K', '8K', '1K', 'CustomImages', '16K', '9K', '1000K', '250K', '25K', '5K-JPG', '5K-PNG', '2kPNG', '4kPNG', '2kPNG-PNG', '4kPNG-PNG', '9K-JPG', '10K-JPG', '7K-JPG', '7K-PNG', '3K-JPG', '3K-PNG', '9K-PNG', '33K-JPG', '33K-PNG', '15K-JPG', '15K-PNG']
    else:
        attribs = ['None', '1K-JPG', '1K-PNG', '2K-JPG', '2K-PNG', '4K-JPG', '4K-PNG', '8K-JPG', '8K-PNG']
    items = []
    for a in attribs:
        items.append((a, a, ""))
    return items


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
            if tool.tex_ignore_filter != "": # Remove filepaths of textures which contain a filtered string, if a filter is chosen.
                for fp in filePaths:
                    if tool.tex_ignore_filter in fp.name:
                        filePaths.pop(filePaths.index(fp))
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

class NWAddPrincipledSetup(Operator, NWBase, ImportHelper):
    bl_idname = "node.nw_add_textures_for_principled"
    bl_label = "Principled Texture Setup"
    bl_description = "Add Texture Node Setup for Principled BSDF"
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name='Directory',
        subtype='DIR_PATH',
        default='',
        description='Folder to search in for image files'
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    relative_path: BoolProperty(
        name='Relative Path',
        description='Set the file path relative to the blend file, when possible',
        default=True
    )

    order = [
        "filepath",
        "files",
    ]

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'LEFT'

        layout.prop(self, 'relative_path')

    @classmethod
    def poll(cls, context):
        valid = False
        if nw_check(context):
            space = context.space_data
            if space.tree_type == 'ShaderNodeTree':
                valid = True
        return valid

    def execute(self, context):
        # Check if everything is ok
        if not self.directory:
            self.report({'INFO'}, 'No Folder Selected')
            return {'CANCELLED'}
        if not self.files[:]:
            self.report({'INFO'}, 'No Files Selected')
            return {'CANCELLED'}

        nodes, links = get_nodes_links(context)
        active_node = nodes.active
        if not (active_node and active_node.bl_idname == 'ShaderNodeBsdfPrincipled'):
            self.report({'INFO'}, 'Select Principled BSDF')
            return {'CANCELLED'}

        # Filter textures names for texturetypes in filenames
        # [Socket Name, [abbreviations and keyword list], Filename placeholder]
        tags = context.preferences.addons[__package__].preferences.principled_tags
        normal_abbr = tags.normal.split(' ')
        bump_abbr = tags.bump.split(' ')
        gloss_abbr = tags.gloss.split(' ')
        rough_abbr = tags.rough.split(' ')
        socketnames = [
            ['Displacement', tags.displacement.split(' '), None],
            ['Base Color', tags.base_color.split(' '), None],
            ['Subsurface Color', tags.sss_color.split(' '), None],
            ['Metallic', tags.metallic.split(' '), None],
            ['Specular', tags.specular.split(' '), None],
            ['Roughness', rough_abbr + gloss_abbr, None],
            ['Normal', normal_abbr + bump_abbr, None],
            ['Transmission', tags.transmission.split(' '), None],
            ['Emission', tags.emission.split(' '), None],
            ['Alpha', tags.alpha.split(' '), None],
            ['Ambient Occlusion', tags.ambient_occlusion.split(' '), None],
        ]

        match_files_to_socket_names(self.files, socketnames)
        # Remove socketnames without found files
        socketnames = [s for s in socketnames if s[2]
                       and path.exists(self.directory + s[2])]
        if not socketnames:
            self.report({'INFO'}, 'No matching images found')
            print('No matching images found')
            return {'CANCELLED'}

        # Don't override path earlier as os.path is used to check the absolute path
        import_path = self.directory
        if self.relative_path:
            if bpy.data.filepath:
                try:
                    import_path = bpy.path.relpath(self.directory)
                except ValueError:
                    pass

        # Add found images
        print('\nMatched Textures:')
        texture_nodes = []
        disp_texture = None
        ao_texture = None
        normal_node = None
        roughness_node = None
        for i, sname in enumerate(socketnames):
            print(i, sname[0], sname[2])

            # DISPLACEMENT NODES
            if sname[0] == 'Displacement':
                disp_texture = nodes.new(type='ShaderNodeTexImage')
                img = bpy.data.images.load(path.join(import_path, sname[2]))
                disp_texture.image = img
                disp_texture.label = 'Displacement'
                if disp_texture.image:
                    disp_texture.image.colorspace_settings.is_data = True

                # Add displacement offset nodes
                disp_node = nodes.new(type='ShaderNodeDisplacement')
                # Align the Displacement node under the active Principled BSDF node
                disp_node.location = active_node.location + Vector((100, -700))
                link = connect_sockets(disp_node.inputs[0], disp_texture.outputs[0])

                # TODO Turn on true displacement in the material
                # Too complicated for now

                # Find output node
                output_node = [n for n in nodes if n.bl_idname == 'ShaderNodeOutputMaterial']
                if output_node:
                    if not output_node[0].inputs[2].is_linked:
                        link = connect_sockets(output_node[0].inputs[2], disp_node.outputs[0])

                continue

            # AMBIENT OCCLUSION TEXTURE
            if sname[0] == 'Ambient Occlusion':
                ao_texture = nodes.new(type='ShaderNodeTexImage')
                img = bpy.data.images.load(path.join(import_path, sname[2]))
                ao_texture.image = img
                ao_texture.label = sname[0]
                if ao_texture.image:
                    ao_texture.image.colorspace_settings.is_data = True

                continue

            if not active_node.inputs[sname[0]].is_linked:
                # No texture node connected -> add texture node with new image
                texture_node = nodes.new(type='ShaderNodeTexImage')
                img = bpy.data.images.load(path.join(import_path, sname[2]))
                texture_node.image = img

                # NORMAL NODES
                if sname[0] == 'Normal':
                    # Test if new texture node is normal or bump map
                    fname_components = split_into_components(sname[2])
                    match_normal = set(normal_abbr).intersection(set(fname_components))
                    match_bump = set(bump_abbr).intersection(set(fname_components))
                    if match_normal:
                        # If Normal add normal node in between
                        normal_node = nodes.new(type='ShaderNodeNormalMap')
                        link = connect_sockets(normal_node.inputs[1], texture_node.outputs[0])
                    elif match_bump:
                        # If Bump add bump node in between
                        normal_node = nodes.new(type='ShaderNodeBump')
                        link = connect_sockets(normal_node.inputs[2], texture_node.outputs[0])

                    link = connect_sockets(active_node.inputs[sname[0]], normal_node.outputs[0])
                    normal_node_texture = texture_node

                elif sname[0] == 'Roughness':
                    # Test if glossy or roughness map
                    fname_components = split_into_components(sname[2])
                    match_rough = set(rough_abbr).intersection(set(fname_components))
                    match_gloss = set(gloss_abbr).intersection(set(fname_components))

                    if match_rough:
                        # If Roughness nothing to to
                        link = connect_sockets(active_node.inputs[sname[0]], texture_node.outputs[0])

                    elif match_gloss:
                        # If Gloss Map add invert node
                        invert_node = nodes.new(type='ShaderNodeInvert')
                        link = connect_sockets(invert_node.inputs[1], texture_node.outputs[0])

                        link = connect_sockets(active_node.inputs[sname[0]], invert_node.outputs[0])
                        roughness_node = texture_node

                else:
                    # This is a simple connection Texture --> Input slot
                    link = connect_sockets(active_node.inputs[sname[0]], texture_node.outputs[0])

                # Use non-color for all but 'Base Color' Textures
                if not sname[0] in ['Base Color', 'Emission'] and texture_node.image:
                    texture_node.image.colorspace_settings.is_data = True

            else:
                # If already texture connected. add to node list for alignment
                texture_node = active_node.inputs[sname[0]].links[0].from_node

            # This are all connected texture nodes
            texture_nodes.append(texture_node)
            texture_node.label = sname[0]

        if disp_texture:
            texture_nodes.append(disp_texture)

        if ao_texture:
            # We want the ambient occlusion texture to be the top most texture node
            texture_nodes.insert(0, ao_texture)

        # Alignment
        for i, texture_node in enumerate(texture_nodes):
            offset = Vector((-550, (i * -280) + 200))
            texture_node.location = active_node.location + offset

        if normal_node:
            # Extra alignment if normal node was added
            normal_node.location = normal_node_texture.location + Vector((300, 0))

        if roughness_node:
            # Alignment of invert node if glossy map
            invert_node.location = roughness_node.location + Vector((300, 0))

        # Add texture input + mapping
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = active_node.location + Vector((-1050, 0))
        if len(texture_nodes) > 1:
            # If more than one texture add reroute node in between
            reroute = nodes.new(type='NodeReroute')
            texture_nodes.append(reroute)
            tex_coords = Vector((texture_nodes[0].location.x,
                                 sum(n.location.y for n in texture_nodes) / len(texture_nodes)))
            reroute.location = tex_coords + Vector((-50, -120))
            for texture_node in texture_nodes:
                link = connect_sockets(texture_node.inputs[0], reroute.outputs[0])
            link = connect_sockets(reroute.inputs[0], mapping.outputs[0])
        else:
            link = connect_sockets(texture_nodes[0].inputs[0], mapping.outputs[0])

        # Connect texture_coordiantes to mapping node
        texture_input = nodes.new(type='ShaderNodeTexCoord')
        texture_input.location = mapping.location + Vector((-200, 0))
        link = connect_sockets(mapping.inputs[0], texture_input.outputs[2])

        # Create frame around tex coords and mapping
        frame = nodes.new(type='NodeFrame')
        frame.label = 'Mapping'
        mapping.parent = frame
        texture_input.parent = frame
        frame.update()

        # Create frame around texture nodes
        frame = nodes.new(type='NodeFrame')
        frame.label = 'Textures'
        for tnode in texture_nodes:
            tnode.parent = frame
        frame.update()

        # Just to be sure
        active_node.select = False
        nodes.update()
        links.update()
        force_update(context)
        return {'FINISHED'}


class OT_ImportModels(Operator):
    bl_label = "Import models"
    bl_idname = "alt.importmodels"
    
    # Hide new objects works by comparing a list of objects before (x) happened with the current list via bpy.context.scene.objects to get the list of new objects, then hides those new objects
    def hideNewObjects(old_objects):
        scene = bpy.context.scene
        tool = scene.assetlibrarytools
        if tool.hide_after_import == True:
            imported_objects = set(bpy.context.scene.objects) - old_objects
            for object in imported_objects:
                object.hide_set(True)
    
    def moveNewObjectsToNewCollection(old_objects, collName):
        scene = bpy.context.scene
        tool = scene.assetlibrarytools
        if tool.move_to_new_collection_after_import == True: 
            imported_objects = set(bpy.context.scene.objects) - old_objects
            newCollection = bpy.data.collections.new(collName)
            bpy.context.scene.collection.children.link(newCollection)
            for obj in imported_objects:
                for uc in obj.users_collection:
                    uc.objects.unlink(obj)
                newCollection.objects.link(obj)
    
    def joinAllNewObjects(old_objects):
        scene = bpy.context.scene
        tool = scene.assetlibrarytools
        if tool.join_new_objects == True:
            imported_objects = set(bpy.context.scene.objects) - old_objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_objects:
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
            bpy.ops.object.join()
    
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        p = pathlib.Path(str(tool.model_import_path))
        imported = 0 # Number of imported objects
        errors = 0 # Number of import errors
        # Import FBX files
        if tool.import_fbx == True:
            fbxFilePaths = [x for x in p.glob('**/*.fbx') if x.is_file()] # Get filepaths of files with the extension .fbx in the selected directory (and subdirs, recursively)
            for filePath in fbxFilePaths:
                old_objects = set(context.scene.objects)
                try:
                    bpy.ops.import_scene.fbx(filepath=str(filePath))
                    imported += 1
                except:
                    print("FBX import error")
                    errors += 1
                OT_ImportModels.hideNewObjects(old_objects)
                OT_ImportModels.moveNewObjectsToNewCollection(old_objects, filePath.name)
                OT_ImportModels.joinAllNewObjects(old_objects)
        # Import GLTF files
        if tool.import_gltf == True:
            gltfFilePaths = [x for x in p.glob('**/*.gltf') if x.is_file()] # Get filepaths of files with the extension .gltf in the selected directory (and subdirs, recursively)
            for filePath in gltfFilePaths:
                old_objects = set(context.scene.objects)
                try:
                    bpy.ops.import_scene.gltf(filepath=str(filePath))
                    imported += 1
                except:
                    print("GLTF import error")
                    errors += 1
                OT_ImportModels.hideNewObjects(old_objects)
                OT_ImportModels.moveNewObjectsToNewCollection(old_objects, filePath.name)
                OT_ImportModels.joinAllNewObjects(old_objects)
        # Import OBJ files
        if tool.import_obj == True:
            objFilePaths = [x for x in p.glob('**/*.obj') if x.is_file()] # Get filepaths of files with the extension .obj in the selected directory (and subdirs, recursively)
            for filePath in objFilePaths:
                old_objects = set(context.scene.objects)
                try:
                    bpy.ops.import_scene.obj(filepath=str(filePath))
                    imported += 1
                except:
                    print("OBJ import error")
                    errors += 1
                OT_ImportModels.hideNewObjects(old_objects)
                OT_ImportModels.moveNewObjectsToNewCollection(old_objects, filePath.name)
                OT_ImportModels.joinAllNewObjects(old_objects)
        # Import X3D files
        if tool.import_x3d == True:
            x3dFilePaths = [x for x in p.glob('**/*.x3d') if x.is_file()] # Get filepaths of files with the extension .x3d in the selected directory (and subdirs, recursively)
            for filePath in x3dFilePaths:
                old_objects = set(context.scene.objects)
                try:
                    bpy.ops.import_scene.x3d(filepath=str(filePath))
                    imported += 1
                except:
                    print("X3D import error")
                    errors += 1
                OT_ImportModels.hideNewObjects(old_objects)
                OT_ImportModels.moveNewObjectsToNewCollection(old_objects, filePath.name)
                OT_ImportModels.joinAllNewObjects(old_objects)
        if errors == 0:
            DisplayMessageBox("Complete, {0} models imported".format(imported))
        else:
            DisplayMessageBox("Complete, {0} models imported. {1} import errors".format(imported, errors))
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
                # Create new collection
                if tool.append_move_to_new_collection_after_import:
                    newCollection = bpy.data.collections.new(str(path.name))
                    bpy.context.scene.collection.children.link(newCollection)
                #link object to collection
                for obj in data_to.objects:
                    removed = False
                    if obj != None:
                        if tool.append_move_to_new_collection_after_import:
                            newCollection.objects.link(obj)
                        else:
                            bpy.context.collection.objects.link(obj)
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
                # Join objects if option turned on
                if tool.append_join_new_objects:
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in data_to.objects:
                        bpy.context.view_layer.objects.active = obj
                        obj.select_set(True)
                    bpy.ops.object.join()
                    
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


class OT_GenerateAssetPreviews(Operator):
    bl_label = "Generate previews"
    bl_idname = "alt.generateassetpreviews"
    def execute(self, context):
        scene = context.scene
        tool = scene.assetlibrarytools
        if tool.previewgentype == 'objects':
            for obj in bpy.data.objects:
                if obj.asset_data:
                    obj.asset_generate_preview()
        if tool.previewgentype == 'materials':
            for mat in bpy.data.materials:
                if mat.asset_data:
                    mat.asset_generate_preview()
        if tool.previewgentype == 'images':
            for img in bpy.data.images:
                if img.asset_data:
                    img.asset_generate_preview()
        if tool.previewgentype == 'textures':
            for tex in bpy.data.textures:
                if tex.asset_data:
                    tex.asset_generate_preview()      
        if tool.previewgentype == 'meshes':
            for mesh in bpy.data.meshes:
                if mesh.asset_data:
                    mesh.asset_generate_preview()      
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


class OT_SimpleDelDupeMaterials(Operator):
    bl_label = "Clean up duplicate materials (simple)"
    bl_idname = "alt.simpledeldupemats"
    def execute(self, context):
        for obj in bpy.data.objects:
            for slt in obj.material_slots:
                part = slt.name.rpartition('.')
                if part[2].isnumeric() and part[0] in bpy.data.materials:
                    slt.material = bpy.data.materials.get(part[0])
        DisplayMessageBox("Done")
        return {'FINISHED'}


class OT_CleanupUnusedMaterials(Operator):
    bl_label = "Clean up unused materials"
    bl_idname = "alt.cleanupunusedmats"
    def execute(self, context):
        i = 0
        for mat in bpy.data.materials:
            if mat.users == 0:
                bpy.data.materials.remove(mat)
                i += 1
        DisplayMessageBox("Done, {0} unused materials deleted".format(i))
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
        DisplayMessageBox("Done, {0} nodes changed".format(i))
        return {'FINISHED'}


def snapshot(self,context,ob):
    scene = context.scene
    tool = scene.assetlibrarytools
    # Make sure we have a camera
    if bpy.context.scene.camera == None:
        bpy.ops.object.camera_add()
    
    #Save some basic settings
    camera = bpy.context.scene.camera    
    hold_camerapos = camera.location.copy()
    hold_camerarot = camera.rotation_euler.copy()
    hold_x = bpy.context.scene.render.resolution_x
    hold_y = bpy.context.scene.render.resolution_y 
    hold_filepath = bpy.context.scene.render.filepath
    
    # Find objects that are hidden in viewport and hide them in render
    tempHidden = []
    for o in bpy.data.objects:
        if o.hide_get() == True:
            o.hide_render = True
            tempHidden.append(o)
    
    # Change Settings
    bpy.context.scene.render.resolution_y = tool.resolution
    bpy.context.scene.render.resolution_x = tool.resolution
    switchback = False
    if bpy.ops.view3d.camera_to_view.poll():
        bpy.ops.view3d.camera_to_view()
        switchback = True
    
    # Ensure outputfile is set to png (temporarily, at least)
    previousFileFormat = scene.render.image_settings.file_format
    if scene.render.image_settings.file_format != 'PNG':
        scene.render.image_settings.file_format = 'PNG'
    
    filename = str(random.randint(0,100000000000))+".png"
    filepath = str(os.path.abspath(os.path.join(os.sep, 'tmp', filename)))
    bpy.context.scene.render.filepath = filepath
    
    #Render File, Mark Asset and Set Image
    bpy.ops.render.render(write_still = True)
    ob.asset_mark()
    override = bpy.context.copy()
    override['id'] = ob
    bpy.ops.ed.lib_id_load_custom_preview(override,filepath=filepath)
    
    # Unhide the objects hidden for the render
    for o in tempHidden:
        o.hide_render = False
    # Reset output file format
    scene.render.image_settings.file_format = previousFileFormat
    
    #Cleanup
    os.unlink(filepath)
    bpy.context.scene.render.resolution_y = hold_y
    bpy.context.scene.render.resolution_x = hold_x
    camera.location = hold_camerapos
    camera.rotation_euler = hold_camerarot
    bpy.context.scene.render.filepath = hold_filepath
    if switchback:
        bpy.ops.view3d.view_camera()


class OT_AssetSnapshotCollection(Operator):
    """Create a preview of a collection"""
    bl_idname = "view3d.asset_snaphot_collection"
    bl_label = "Asset Snapshot - Collection"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        snapshot(self, context,context.collection)
        return {'FINISHED'}


class OT_AssetSnapshotObject(Operator):
    """Create an asset preview of an object"""
    bl_idname = "view3d.object_preview"
    bl_label = "Asset Snapshot - Object"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        snapshot(self, context, bpy.context.view_layer.objects.active)
        return {'FINISHED'}


class OT_AssetDownloaderOperator(Operator):
    bl_label = "Run script"
    bl_idname = "alt.assetdownloader"
    def execute(self, context):
        tool = context.scene.assetlibrarytools
        ur = bpy.utils.user_resource('SCRIPTS')
        # Do some input checking
        if tool.downloader_save_path == '':
            DisplayMessageBox("Enter a save path", "Error", "ERROR")
        if ' ' in tool.downloader_save_path:
            DisplayMessageBox("Filepath invalid: space in filepath", "Error", "ERROR")
        if tool.keywordFilter == "":
            tool.keywordFilter = 'None'
        if ' ' not in tool.downloader_save_path and tool.downloader_save_path != '':
            # Start ALT_CC0AssetDownloader.py via chosen terminal
            if tool.terminal == 'xterm':
                os.system('xterm -e "python3 {0}/ALT_CC0AssetDownloader.py {1} {2} {3} {4} {5} {6} {7}"'.format(ur+'/addons/AssetLibraryTools', tool.downloader_save_path, tool.keywordFilter, tool.attributeFilter, tool.extensionFilter, str(tool.unZip), str(tool.deleteZips), str(tool.skipDuplicates)))
            if tool.terminal == 'konsole':
                os.system('konsole -e "python3 {0}/ALT_CC0AssetDownloader.py {1} {2} {3} {4} {5} {6} {7}"'.format(ur+'/addons/AssetLibraryTools', tool.downloader_save_path, tool.keywordFilter, tool.attributeFilter, tool.extensionFilter, str(tool.unZip), str(tool.deleteZips), str(tool.skipDuplicates)))
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
#    Registration
# ------------------------------------------------------------------------

classes = (
    OT_BatchImportPBR,
    OT_ImportModels,
    OT_BatchAppend,
    OT_ManageAssets,
    OT_GenerateAssetPreviews,
    OT_BatchDelete,
    OT_SimpleDelDupeMaterials,
    OT_CleanupUnusedMaterials,
    OT_UseDisplacementOnAll,
    OT_ChangeAllDisplacementScale,
    OT_AssetSnapshotCollection,
    OT_AssetSnapshotObject,
    OT_AssetDownloaderOperator,
    OT_ImportSBSAR,
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
