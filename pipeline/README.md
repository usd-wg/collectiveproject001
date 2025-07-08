# Structure and Pipeline

The USD structure and pipeline requirements are driven by the show/project and resources, so the following is specific to the `collectiveproject001`.

This could be reused for future collective projects or it may be modified/extended if different requirements are going to be fulfilled in the next projects.

## Asset

An asset is the individually versioned/published entity, defined as participant of other assets (Layouts) and/or shots.

### Purposes

For each asset we are going to define a two different resolutions: a `proxy` purpose low-res resolution and a `render` purpose high-res resolution.

`render` purpose resolution will be used for final renders, and the `proxy` purpose resolution could be used for fast realtime rendering, even though the `render` purpose resolution could be used for realtime rendering, depending on asset-complexity.

### Fragments

Each purpose resolution is maybe of various `fragment`, representing the various contributions of each task required to complete the asset.

There are fragments that are applied to the asset, and fragments that are applied to the shot (or the asset/element when in a shot).

For the asset-fragments, in this projects we are using:

- model
    - it contains the actual geometry of the asset, under a payload composition arc.
- surface
    - it contains the materials/shaders for the asset
- binding
    - it contains how the materials are bound to the geometry, maybe behind look-variants, using binding-collections or direct binding

A `data` folder may be created to contain extra bits like mtlx files or textures, VDBs, etc.

### Index.usda

The entry point file of an asset is its `index.usda` in the root of the asset folder.

### Files structure

Asset/index.usda in the asset main folder defines the purpose-prims
and it references purpose/index.usda on each purpose prim.

Purpose/index.usda defines "geo" and "mtl" and sublayers
all fragment/index.usda based on a specific fragment-order.

Fragment/index.usda uses its payload (for model and surface) and "data" files based
on its internal requirements.

"data" folder may contain extra bits like mtlx files or
textures or VDBs, etc.

- asset [folder]
    - index.usda
    - purpose [folder]
        - fragment [folder]
            - index.usda    
            - payload.usda [only for model and surface]
            - data [folder]
                - extra files...
        - index.usda

# Exporting and Publishing

To export and publish, the git-repo can be cloned, a new branch created and the necessary files updated.

When working on a specific task in the defined DCC, we want to be able to export/publish the usd-data related to the fragment of the task.

E.g.: when working on a modelling task, a new `model fragment` will need to be exported/published and this can be used to overwrite the existing files.

Publishing means committing and pushing new files to the main git repo in the working branch, updating the `CHANGELOG.md` with the notes of the new version. 

A merge-request will submit the work for review.

Once accepted, the merge-request is merged into the `main` branch and a new render should be triggered.