# What is Expanded?
I have added transmission to the PBR import system. I have also added a MixFactor for in cases where you need to use a mix of diffuse blended with something else.
For example i have a base albedo texture that does not have color and uses a MixFactor mixed with a RGB node to add color to its albedo.

Plans is to extend this more than this and add AO baked textures as well as well as to seperate the plugin into its own packages to make it easier to maintain and added upon by contributers.

# AssetLibraryTools

AssetLibraryTools is a free addon which aims to speed up the process of creating asset libraries with the asset browser, This addon is currently very much experimental as is the asset browser in blender.

# Features
* Batch import PBR materials from texture sets
  * Add real displacement to materials upon import
  * Add fake user to materials upon import
  * Skip materials that already exist
  * Import with UV or object mapping
  * Add extra utility nodes
  * Filter textures by string (dont load if contains x)
* Batch import models of various filetypes (fbx, gltf, obj, x3d)
  * Hide imported models straight after import
* Batch append objects/materials from multiple .blend files at once
  * Search for .blend files to append from in subdirs recursively
  * Dont append lights option
  * Dont append cameras option
* Batch download CC0 assets from ambientcg.com via a python script
  * Filter assets by: Keyword, Download attributes, File extension
  * Unzip downloaded zip files automatically
  * Delete zip files after unzip automatically
  * Skip downloading files that already exist
* Generate custom collection/object asset browser thumbnails (base code from https://github.com/johnnygizmo/asset_snapshot)
* Batch import SBSAR files via Adobe substance 3D add-on for blender
* Batch mark/unmark materials, meshes, objects, images, and textures as assets
* Batch generate asset previews
* Batch delete all materials/objects/textures/images/meshes
* Enable real displacement for cycles on all materials at once
* Change displacement scale on all materials at once
* Clean up duplicate materials (based on name)
* Clean up unused materials
* And more to come

![alt](https://user-images.githubusercontent.com/65134690/138753452-d354f9ec-fe30-4a73-b5a4-8f74ee03063a.png)

