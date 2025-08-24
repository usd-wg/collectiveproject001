#!/bin/env python

import sys
sys.dont_write_bytecode = True
import subprocess

import os
import pipe_globals
from pxr import Usd, UsdGeom, UsdRender


def main(args):
    # Shot name will default to s001_001 if not provided
    # We assume we have one pass for now, otherwise we need to handle passes too.
    # RenderSettings are either stored in the stage or created by default.
    # Without any argument, this commandline will render the default shot with either
    # default values or rendersettings specified in the shot file.
    input_shot = pipe_globals.get_value_from_args(args, "-s", "--shot")
    if input_shot == "":
        input_shot = "s001_001"
    show_root = pipe_globals.get_show_folder()
    shots_root = pipe_globals.get_subfolder(show_root, "shots")
    shot_folder = pipe_globals.get_subfolder(shots_root, input_shot)
    shot_filepath = os.path.join(shot_folder, "index.usda")
    renders_folder = pipe_globals.get_subfolder(shot_folder, "usdrecord_renders")
    snapshot_filepath = os.path.join(renders_folder, "snapshot.usda")
    render_filepath = shot_filepath

    renderer = "GL"
    input_renderer = pipe_globals.get_value_from_args(args,"-r","--renderer")
    if input_renderer in ["GL", "storm", "Storm"]:
        renderer = "GL"
    elif input_renderer in ["RenderMan RIS", "renderman", "prman", "RenderMan", "Renderman"]:
        renderer = "RenderMan RIS"

    purpose = "proxy"
    input_purpose = pipe_globals.get_value_from_args(args,"-p","--purpose")
    if input_purpose != "":
        purpose = input_purpose

    render_jpg_filename = os.path.join(renders_folder, f"{input_shot}_{purpose}_{renderer}_rgba.####.jpg")

    # open the stage to find all necessary details for rendering
    shot_stage = Usd.Stage.Open(shot_filepath)
    # frame-range metadata
    framestart = shot_stage.GetStartTimeCode()
    frameend = shot_stage.GetEndTimeCode()
    fps = shot_stage.GetFramesPerSecond()
    # overridden by inputs ?
    input_framestart = pipe_globals.get_value_from_args(args,"-fs","--framestart")
    if input_framestart != "":
        framestart = int(input_framestart)
    input_frameend = pipe_globals.get_value_from_args(args,"-fe","--frameend")
    if input_frameend != "":
        frameend = int(input_frameend)
    
    # find rendersettings
    rendersettings_prim = UsdRender.Settings.GetStageRenderSettings(shot_stage)
    # are we overriding the rendersettings ?
    input_rendersettings_primpath = pipe_globals.get_value_from_args(args,"-rs","--rendersettings")
    if input_rendersettings_primpath != "":
        rendersettings_prim = shot_stage.GetPrimAtPath(input_rendersettings_primpath)
    # last chance is to find the first rendersettings prim in this shot
    for prim in shot_stage.Traverse():
        if prim.IsA(UsdRender.Settings):
            rendersettings_prim = prim
            break
    # If no rendersettings has been found, we now have to create one
    # and for that, we need a snapshot file to hold our overrides
    if not rendersettings_prim:
        # we need to create a snapshot file for overrides and we are going to render that one
        render_filepath = snapshot_filepath
        shot_stage = pipe_globals.stage_begin(snapshot_filepath, start=framestart, end=frameend, fps=fps)
        # sublayer original shot file
        shot_stage.GetRootLayer().subLayerPaths.append(shot_filepath)
        # search for the first camera prim and add it to the rendersettings
        camera_prim = None
        for prim in shot_stage.Traverse():
            if prim.IsA(UsdGeom.Camera):
                camera_prim = prim
                break
        if not camera_prim:
            print("ERROR camera not found in input shot file")
            exit(1)
        # create default render products
        rendervar_prim = pipe_globals.create_rendervar(shot_stage, aov_name="rgba", aov_source="rgba", aov_format="")
        # NOTE: usdrecord with storm don't use RenderProduct for output images
        #       we are going to pass the filename-pattern directly to usdrecord
        default_resolution = [1024, 768]
        renderproduct_prim = pipe_globals.create_renderproduct(shot_stage, product_name="rgba", camera_prim=camera_prim, product_filepath=render_jpg_filename, resolution=default_resolution)
        pipe_globals.add_var_to_product(rendervar_prim, renderproduct_prim)
        rendersettings_prim = pipe_globals.create_rendersettings(shot_stage, camera_prim=camera_prim)
        pipe_globals.add_product_to_rendersettings( renderproduct_prim, rendersettings_prim )
        # save snapshot file
        pipe_globals.stage_end(shot_stage)

    usdrecord_args = [
        "usdrecord",
        "--renderSettingsPrimPath",
        str(rendersettings_prim.GetPath()),
        "--renderer",
        renderer,
        "--purposes",
        purpose,
        "--frames",
        f"{framestart}:{frameend}x1",
        render_filepath,
        render_jpg_filename,
    ]
    print(" ".join(usdrecord_args))
    subprocess.run(usdrecord_args, shell=True)

if __name__ == '__main__':
    main(sys.argv)