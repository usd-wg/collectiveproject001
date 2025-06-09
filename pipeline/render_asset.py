#!/bin/env python

import sys
import subprocess
import tempfile

import os
import pipe_globals
from pxr import UsdGeom


def main(args):
    assets = pipe_globals.get_array_value_from_args(args, "-a", "--asset")
    shots = pipe_globals.get_array_value_from_args(args, "-s", "--shot")
    framestart = int(pipe_globals.get_value_from_args(args,"-fs","--framestart"))
    frameend = int(pipe_globals.get_value_from_args(args,"-fe","--frameend"))
    resolution = [1024,768]

    if len(assets) == 0 and len(shots) == 0:
        # nothing to render
        exit(0)

    show_root = pipe_globals.get_show_folder()

    assets_root = pipe_globals.get_subfolder(show_root, "assets")
    for asset in assets:
        asset_name = asset
        asset_folder = pipe_globals.get_subfolder(assets_root, asset_name)
        asset_filename = os.path.join(asset_folder, "index.usda")
        renders_folder = pipe_globals.get_subfolder(asset_folder, "usdrecord_renders")

        # make turntable file, with animated camera
        render_usd_filename = os.path.join(renders_folder, "turntable.usda")
        stage = pipe_globals.stage_begin(render_usd_filename, start=0.0, end=float(frameend-framestart+1))
        stage.GetRootLayer().subLayerPaths = [pipe_globals.anchor_path(asset_filename, stage.GetRootLayer().identifier)]
        (camera_xform_prim, camera_prim) = pipe_globals.create_default_camerarig(stage, resolution=resolution)
        pipe_globals.make_turntable(stage, camera_xform_prim, camera_prim)
        rendervar_prim = pipe_globals.create_rendervar(stage, aov_name="rgba", aov_source="rgba", aov_format="")
        # NOTE: usdrecord with storm don't use RenderProduct for output images
        #       we are going to pass the filename-pattern directly to usdrecord
        renderproduct_prim = pipe_globals.create_renderproduct(stage, product_name="rgba", camera_prim=camera_prim, product_filepath="placeholder.jpg", resolution=resolution)
        pipe_globals.add_var_to_product(rendervar_prim, renderproduct_prim)
        rendersettings_prim = pipe_globals.create_rendersettings(stage, camera_prim=camera_prim)
        pipe_globals.add_product_to_rendersettings( renderproduct_prim, rendersettings_prim )
        pipe_globals.stage_end(stage)

        for purpose in ["proxy","render"]:
            render_jpg_filename = os.path.join(renders_folder, f"output_{purpose}.####.jpg")
            usdrecord_args = [
                "usdrecord",
                "--renderSettingsPrimPath",
                str(rendersettings_prim.GetPath()),
                "--purposes",
                purpose,
                "--frames",
                f"{framestart}:{frameend}x1",
                "--camera",
                str(camera_prim.GetPath()),
                "--imageWidth",
                str(resolution[0]),
                render_usd_filename,
                render_jpg_filename,
            ]
            print(usdrecord_args)
            subprocess.run(usdrecord_args, shell=True)

        # reviewer with quad/card and animated texture so we can use usdview
        reviewer_filename = os.path.join(renders_folder, "reviewer.usda")
        reviewer_stage = pipe_globals.stage_begin(reviewer_filename, start=0.0, end=float(frameend-framestart+1))
        pipe_globals.make_reviewer_per_purpose(reviewer_stage, purpose="proxy", textures="output_proxy.####.jpg", framestart=framestart, frameend=frameend, resolution=resolution)
        pipe_globals.make_reviewer_per_purpose(reviewer_stage, purpose="render", textures="output_render.####.jpg", framestart=framestart, frameend=frameend, resolution=resolution)
        pipe_globals.stage_end(reviewer_stage)
        

if __name__ == '__main__':
    main(sys.argv)