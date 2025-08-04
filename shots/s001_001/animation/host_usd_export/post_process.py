import importlib.util
import os
import sys
sys.dont_write_bytecode = True

module_name = "pipe_globals"
module_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "pipeline", "pipe_globals.py")
spec = importlib.util.spec_from_file_location(module_name, module_path)
pipe_globals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipe_globals)

from pxr import Usd, UsdGeom, UsdSkel

# load animation file from Stephanie
stage = Usd.Stage.Open("odie_idea01_animation_v02.usd")
anim_frame_start = stage.GetStartTimeCode()
anim_frame_end = stage.GetEndTimeCode()
anim_fps = stage.GetTimeCodesPerSecond()
# bake all SkelRoot meshes, we should be fine with this, it's only Odie and we need only one mesh
UsdSkel.BakeSkinning(stage.Traverse())

# create binary data for odie01 animation payload
#
animation_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "odie01", "animation", "animated_proxy.usd")
animation_layer_frame_start = 1000
# increase length by 100 frames, to give some extra seconds for some lights potentially to get on
animation_layer_frame_end = animation_layer_frame_start + ( anim_frame_end - anim_frame_start ) + 100.0
animation_layer_stage = pipe_globals.stage_begin(animation_layer_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
# override main mesh under the proxy purpose only (render purpose TODO)
over_mesh = UsdGeom.Mesh( animation_layer_stage.OverridePrim("/main/proxy/geo/body") )
mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/odieRig/Odie_rig_Odie1"))
i = 0
for input_frame in range( int(anim_frame_start), int(anim_frame_end) ):
    points = mesh.GetPointsAttr().Get(float(input_frame))
    over_mesh.CreatePointsAttr().Set(points, float(animation_layer_frame_start + 100.0 + i))
    i += 1
pipe_globals.stage_end( animation_layer_stage )
# recompose in odie01 animation fragment
animation_frag_path = os.path.join(os.path.dirname(__file__), "..", "..", "odie01", "animation", "index.usda")
frag_stage = pipe_globals.stage_begin(animation_frag_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
frag_stage.GetRootLayer().subLayerPaths.append("animated_proxy.usd")
pipe_globals.stage_end( frag_stage )

# create camera file
#
# read camera from input stage
input_camera = UsdGeom.Camera(stage.GetPrimAtPath("/cameraGroup/CAMERA"))
# create camera animation layer
camera_animation_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "renderCam", "animation", "index.usda")
camera_animation_stage = pipe_globals.stage_begin(camera_animation_layer_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
main_xform = UsdGeom.Xform.Define(camera_animation_stage,"/main")
# copy camera xform onto main xform 
# NOTE: I tend not to set transform on camera directly
transformOp = main_xform.AddTransformOp()
transformOp.Set( UsdGeom.Imageable(input_camera.GetPrim()).ComputeLocalToWorldTransform(0.0) )
# create camera and copy attributes over from input camera
camera_prim = UsdGeom.Camera.Define(camera_animation_stage,main_xform.GetPath().AppendChild("mono"))
camera_prim.CreateFocalLengthAttr().Set(input_camera.GetFocalLengthAttr().Get())
camera_prim.CreateFocusDistanceAttr().Set(input_camera.GetFocusDistanceAttr().Get())
camera_prim.CreateClippingRangeAttr().Set(input_camera.GetClippingRangeAttr().Get())
camera_prim.CreateHorizontalApertureAttr().Set(input_camera.GetHorizontalApertureAttr().Get())
camera_prim.CreateVerticalApertureAttr().Set(input_camera.GetVerticalApertureAttr().Get())
pipe_globals.stage_end( camera_animation_stage )

# create terrain01 file with terrain and cube/seat
#
