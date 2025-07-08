# For the artists

The `shot` has `fragments` to be able to override globally any part of the scene, and those are `sublayered` at the shot level.

The shot is also referencing or sublayering `elements`, dependeing on whether the element is self-contained and it doesn't provide any contribution for other elements (referenced), or it brings wider-scope behaviours like RenderPasses and collections or general lightrigs, which might have to be put in specific hierarchy points of the environments (sublayered).

Each element has `fragments` that are sublayered at the element level.

Each fragment (in a shot or an element) corresponds to a task that an artist can work on.

All elements and fragments have been predefined by the pipeline, based on requirements of the shot, and they are all empty initially.

## Working on a task

Lets consider the task of working on a lighting task for the shot `s001_001`.

This shot has a `envLights` element and it's added as a `reference` which means it is fully embedded, and only its `main` prim (and all of its children) will be included in the shot.

This `envLights` element has a few fragments corresponding to specific tasks, and you've been assigned the `lighting` task.

You will end up modifying the `lighting` fragment of the element `envLights` in the shot `s001_001`.

Since the pipeline has build already all the files to pick those files in the final shot, you just have to save a new fragment file content and the shot is automatically picking it up.

So, the workflow is:

- clone the git repo
- create a new working branch (e.g. `my_awesome_env_lighting`)
- open your preferred DCC
- load the `s001_001/index.usda` to see its current status
- two options here, based on USD integration in the DCC:
    1) The DCC doesn't have great support of USD or I don't know how to do it differently:
        - create your lights (say, a sky and a sun for the envLights mostly)
        - when you are happy with the look, select the lights and export them in a USD file
        - save your DCC working file under `s001_001/envLights/lighting/host_wip/`
        - save your exported USD file under `s001_001/envLights/lighting/host_usd_export/`
        - `the pipeline` will then take care of converting your exported USD to a valid `lighting` fragment for this element.
    2) The DCC has the ability to create USD layers or targets specific layers and you know what you are doing it with this feature:
        - create your lights in the existing `lighting` fragment of the `envLights` reference, or in a new layer
        - save the existing `lighting` layer or export the new layer into the file `s001_001/envLights/lighting/index.usda`
- your branch now has update a few files, you can push it and either create an MR or let us know there is a new branch with your changes.
- `the pipeline` will then merge it in the main branch of the repo and trigger a new render of the whole shot.


Another example is working on the animation for the element `odie01` in the shot `s001_001`.

Just like the lighting example, here the fragment for your task is in `s001_001/odie01/animation/index.usda` and this is the file that needs to have the overs for the animated parts, as this is layered on top of the static asset.

The workflow is like the lighting one, with the two options.

We can prioritise option 1), so that it leaves only the saving of the working file and the exported USD to the artist, and we (`the pipeline`) will take care of ensuring that exported USD file becomes the new animation fragment for the `odie01` element.

NOTE: This is a shot-specific animation, which means it applies to the element `odie01` that is referencing the asset `odie`.
If we had a non-shot specific animation (walking cycles, etc) we would have added those to the asset, instead of the element under the shot.
