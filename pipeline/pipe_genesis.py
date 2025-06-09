#!/bin/env python

import os
import sys

import pipe_globals

from pxr import Sdf, UsdGeom, Usd



def main(args):
    assets = pipe_globals.get_array_value_from_args(args, "-a", "--asset")
    shots = pipe_globals.get_array_value_from_args(args, "-s", "--shot")

    purposes = ["proxy", "render"]
    fragments = ["model", "surface", "binding"]
    
    show_root = pipe_globals.get_show_folder()
    assets_root = pipe_globals.get_subfolder(show_root, "assets")
    shots_root = pipe_globals.get_subfolder(show_root, "shots")

    for asset in assets:
        # Asset/index.usda in the asset main folder defines the purpose-prims
        # and it references purpose/index.usda on each purpose prim.
        #
        # Purpose/index.usda defines "geo" and "mtl" and sublayers
        # all fragment/index.usda based on a specific fragment-order.
        #
        # Fragment/index.usda uses its payload (for model and surface) and "data" files based
        # on its internal requirements.
        #
        # "data" folder may contain extra bits like mtlx files or
        # textures or VDBs, etc.
        #
        # asset [folder]
        #  - index.usda
        #  - purpose [folder]
        #    - fragment [folder]
        #      - index.usda
        #      - payload.usda [only for model and surface]
        #      - data [folder]
        #        - extra files...
        #    - index.usda
        asset_name = asset
        asset_folder = pipe_globals.get_subfolder(assets_root, asset_name)
        asset_filename = os.path.join(asset_folder, "index.usda")
        asset_stage = pipe_globals.stage_begin(asset_filename)
        asset_root_prim = pipe_globals.create_root_prim(asset_stage, "component", asset_name, asset_filename, "latest")

        for purpose in purposes:
            purpose_folder = pipe_globals.get_subfolder(asset_folder, purpose)
            purpose_filename = os.path.join(purpose_folder, "index.usda")
            purpose_stage = pipe_globals.stage_begin(purpose_filename)
            purpose_root_prim = pipe_globals.create_root_prim(purpose_stage)
            
            for fragment in fragments:
                fragment_folder = pipe_globals.get_subfolder(purpose_folder, fragment)
                fragment_filename = os.path.join(fragment_folder, "index.usda")
                fragment_stage = pipe_globals.stage_begin(fragment_filename)
                fragment_root_prim = pipe_globals.create_root_prim(fragment_stage)

                if fragment in ["model", "surface"]:
                    # model and surface have their scope-prim and payloaded onto them
                    scope_prim_name = "geo"
                    if fragment == "surface":
                        scope_prim_name = "mtl"
                    scope_prim = UsdGeom.Scope.Define(fragment_stage, fragment_root_prim.GetPath().AppendChild(scope_prim_name))
                    payload_filename = os.path.join(fragment_folder, "payload.usda")
                    if not os.path.isfile(payload_filename):
                        payload_stage = pipe_globals.stage_begin(payload_filename)
                        payload_root_prim = pipe_globals.create_root_prim(payload_stage)
                        payload_stage.SetDefaultPrim(payload_root_prim)
                        pipe_globals.stage_end(payload_stage)

                    scope_prim.GetPrim().GetPayloads().AddPayload(pipe_globals.anchor_path(payload_filename, fragment_stage.GetRootLayer().identifier))

                fragment_stage.SetDefaultPrim(fragment_root_prim)
                pipe_globals.stage_end(fragment_stage)

                purpose_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(fragment_filename, purpose_stage.GetRootLayer().identifier))

            
            purpose_stage.SetDefaultPrim(purpose_root_prim)
            pipe_globals.stage_end(purpose_stage)

            asset_purpose_prim = UsdGeom.Scope.Define(asset_stage, asset_root_prim.GetPath().AppendChild(purpose))
            asset_purpose_prim.GetPrim().GetAttribute("purpose").Set(purpose)
            asset_purpose_prim.GetPrim().GetReferences().AddReference(pipe_globals.anchor_path(purpose_filename,asset_stage.GetRootLayer().identifier))
         
        pipe_globals.stage_end(asset_stage)

if __name__ == '__main__':
    main(sys.argv)