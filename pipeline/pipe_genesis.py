#!/bin/env python

import os
import sys
sys.dont_write_bytecode = True

import pipe_globals

from pxr import Sdf, UsdGeom, Usd

CATEGORY_CHARACTERS = "characters"
CATEGORY_ENVIRONMENTS = "environments"
CATEGORY_CAMERAS = "cameras"
CATEGORY_LIGHTS = "lights"
CATEGORY_RENDERSETTINGS = "rendersettings"

COMPOSITION_ARC_REFERENCE = "reference"
COMPOSITION_ARC_SUBLAYER = "sublayer"

NAME = "name"
TYPE = "type"
ASSET = "asset"
ARC = "arc"
ELEMENTS = "elements"
START_TIMECODE = "startTimeCode"
END_TIMECODE = "endTimeCode"
FRAMES_PER_SECOND = "framesPerSecond"

ASSETS = [
    "odie",
    "terrain",
]

SHOTS = [
    {
        NAME:"s001_001",
        START_TIMECODE:1000.0,
        END_TIMECODE:1480.0,
        FRAMES_PER_SECOND:24.0,
        ELEMENTS: [
            {
                NAME:"odie01",
                TYPE:CATEGORY_CHARACTERS,
                ASSET:"odie",
                ARC: COMPOSITION_ARC_REFERENCE,
            },
            {
                NAME:"terrain01",
                TYPE:CATEGORY_ENVIRONMENTS,
                ASSET:"terrain",
                ARC: COMPOSITION_ARC_REFERENCE,
            },
            {
                NAME:"renderCam",
                TYPE:CATEGORY_CAMERAS,
                ASSET:None,
                ARC: COMPOSITION_ARC_REFERENCE,
            },            
            {
                NAME:"envLights",
                TYPE:CATEGORY_LIGHTS,
                ASSET:None,
                ARC: COMPOSITION_ARC_REFERENCE,
            },            
            {
                NAME:"lightRig01",
                TYPE:CATEGORY_LIGHTS,
                ASSET:None,
                ARC: COMPOSITION_ARC_SUBLAYER,
            },            
            {
                NAME:"renderPasses",
                TYPE:CATEGORY_LIGHTS,
                ASSET:None,
                ARC: COMPOSITION_ARC_SUBLAYER,
            },            
        ]
    },
]

PURPOSES = ["proxy", "render"]
FRAGMENT_MODEL = "model"
FRAGMENT_SURFACE = "surface"
FRAGMENT_BINDING = "binding"
FRAGMENT_ANIMATION = "animation"
FRAGMENT_LIGHTING = "lighting"
FRAGMENT_FX = "fx"
FRAGMENT_RENDERSETTINGS = "rendersettings"
FRAGMENT_SKELETON = "skeleton"

FRAGMENTS_ASSET = [FRAGMENT_MODEL, FRAGMENT_SKELETON, FRAGMENT_SURFACE, FRAGMENT_BINDING]
FRAGMENTS_ELEMENT = [FRAGMENT_ANIMATION, FRAGMENT_LIGHTING, FRAGMENT_FX]
FRAGMENTS_SHOT = [FRAGMENT_ANIMATION, FRAGMENT_LIGHTING, FRAGMENT_FX, FRAGMENT_RENDERSETTINGS]

HOST_WIP = "host_wip"
HOST_USD_EXPORT = "host_usd_export"

def main(args):
    # create main folders
    show_root = pipe_globals.get_show_folder()
    assets_root = pipe_globals.get_subfolder(show_root, "assets")
    shots_root = pipe_globals.get_subfolder(show_root, "shots")

    # create assets
    for asset in ASSETS:
        asset_name = asset
        asset_folder = pipe_globals.get_subfolder(assets_root, asset_name)
        asset_filename = os.path.join(asset_folder, "index.usda")
        asset_stage = pipe_globals.stage_begin(asset_filename)
        asset_root_prim = pipe_globals.create_root_prim(asset_stage, "component", asset_name, asset_filename, "latest")

        for purpose in PURPOSES:
            purpose_folder = pipe_globals.get_subfolder(asset_folder, purpose)
            purpose_filename = os.path.join(purpose_folder, "index.usda")
            purpose_stage = pipe_globals.stage_begin(purpose_filename)
            purpose_root_prim = pipe_globals.create_root_prim(purpose_stage)
            
            # create fragments
            for fragment in FRAGMENTS_ASSET:
                fragment_folder = pipe_globals.get_subfolder(purpose_folder, fragment)
                # create extra folders for artists working files
                pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_WIP) )
                pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_USD_EXPORT) )
                # create fragment placeholder if needed
                fragment_filename = os.path.join(fragment_folder, "index.usda")
                if not os.path.isfile(fragment_filename):
                    fragment_stage = pipe_globals.stage_begin(fragment_filename)
                    fragment_root_prim = pipe_globals.create_root_prim(fragment_stage)
                    fragment_stage.SetDefaultPrim(fragment_root_prim)
                    pipe_globals.stage_end(fragment_stage)
                purpose_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(fragment_filename, purpose_stage.GetRootLayer().identifier))

            purpose_stage.SetDefaultPrim(purpose_root_prim)
            pipe_globals.stage_end(purpose_stage)

            asset_purpose_prim = UsdGeom.Scope.Define(asset_stage, asset_root_prim.GetPath().AppendChild(purpose))
            asset_purpose_prim.GetPrim().GetAttribute("purpose").Set(purpose)
            asset_purpose_prim.GetPrim().GetReferences().AddReference(pipe_globals.anchor_path(purpose_filename,asset_stage.GetRootLayer().identifier))
        
        pipe_globals.stage_end(asset_stage)

    for shot in SHOTS:
        shot_name = shot[NAME]
        shot_folder = pipe_globals.get_subfolder(shots_root, shot_name)
        elements = shot[ELEMENTS]
        shot_filename = os.path.join(shot_folder, "index.usda")
        shot_stage = pipe_globals.stage_begin(shot_filename, start=shot[START_TIMECODE], end=shot[END_TIMECODE], fps=shot[FRAMES_PER_SECOND])
        shot_world_prim = pipe_globals.get_or_create_world_prim(shot_stage)

        for element in elements:
            element_name = element[NAME]
            element_type = element[TYPE]
            asset_name = element[ASSET]
            composition_arc = element[ARC]
            element_folder = pipe_globals.get_subfolder(shot_folder, element_name)
            element_filename = os.path.join(element_folder, "index.usda")
            element_stage = pipe_globals.stage_begin(element_filename)
            if asset_name:
                asset_folder = pipe_globals.get_subfolder(assets_root, asset_name)
                asset_filename = os.path.join(asset_folder, "index.usda")
                # reference maybe?
                element_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(asset_filename, element_stage.GetRootLayer().identifier))

            for fragment in FRAGMENTS_ELEMENT:
                fragment_folder = pipe_globals.get_subfolder(element_folder, fragment)
                # create extra folders for artists working files
                pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_WIP) )
                pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_USD_EXPORT) )
                fragment_filename = os.path.join(fragment_folder, "index.usda")
                if not os.path.isfile(fragment_filename):
                    fragment_stage = pipe_globals.stage_begin(fragment_filename)
                    pipe_globals.stage_end(fragment_stage)
                element_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(fragment_filename, element_stage.GetRootLayer().identifier))

            if composition_arc == COMPOSITION_ARC_REFERENCE:
                element_root_prim = pipe_globals.create_root_prim(element_stage)
                element_stage.SetDefaultPrim(element_root_prim)
            pipe_globals.stage_end(element_stage)

            if composition_arc == COMPOSITION_ARC_REFERENCE:
                element_type_prim_path = shot_world_prim.GetPath().AppendChild(element_type)
                element_type_prim = shot_stage.GetPrimAtPath(element_type_prim_path)
                if not element_type_prim:
                    element_type_prim = UsdGeom.Xform.Define(shot_stage,element_type_prim_path)
                    element_type_prim.GetPrim().SetMetadata("kind","group")
                element_prim_path = element_type_prim.GetPath().AppendChild(element_name)
                element_prim = shot_stage.GetPrimAtPath(element_prim_path)
                if not element_prim:
                    element_prim = UsdGeom.Xform.Define(shot_stage,element_prim_path)
                    element_prim.GetPrim().SetMetadata("kind","component")
                element_prim.GetPrim().GetReferences().AddReference(pipe_globals.anchor_path(element_filename, shot_stage.GetRootLayer().identifier))

            elif composition_arc == COMPOSITION_ARC_SUBLAYER:
                shot_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(element_filename, shot_stage.GetRootLayer().identifier))

        for fragment in FRAGMENTS_SHOT:
            fragment_folder = pipe_globals.get_subfolder(shot_folder, fragment)
            # create extra folders for artists working files
            pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_WIP) )
            pipe_globals.keep_folder( pipe_globals.get_subfolder(fragment_folder, HOST_USD_EXPORT) )
            fragment_filename = os.path.join(fragment_folder, "index.usda")
            if not os.path.isfile(fragment_filename):
                fragment_stage = pipe_globals.stage_begin(fragment_filename)
                pipe_globals.stage_end(fragment_stage)
            shot_stage.GetRootLayer().subLayerPaths.insert(0,pipe_globals.anchor_path(fragment_filename, shot_stage.GetRootLayer().identifier))

        pipe_globals.stage_end(shot_stage)

if __name__ == '__main__':
    main(sys.argv)
