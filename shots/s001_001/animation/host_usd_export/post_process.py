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

def rename_joint(joint):
    # hacky way to make joint names nicer
    # Maya added a few extra bits we can take out
    n = joint
    n = n.replace("Odie_rig_","")
    n = n.replace("_M","")
    return n

# load animation file from Stephanie and retrieve original prims
#
stage = Usd.Stage.Open("odie_idea01_animation_v02.usd")
anim_frame_start = stage.GetStartTimeCode()
anim_frame_end = stage.GetEndTimeCode()
anim_fps = stage.GetTimeCodesPerSecond()
original_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath("/odieRig/Odie_rig_root"))
original_skeleton_animation = UsdSkel.Animation(stage.GetPrimAtPath("/odieRig/Odie_rig_root/Animation"))
original_mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/odieRig/Odie_rig_Odie1"))
original_skel_api = UsdSkel.BindingAPI(original_mesh.GetPrim())

# create the skeleton layer for the odie asset
#
skeleton_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "assets", "odie", "proxy", "skeleton", "index.usda")
skeleton_layer_stage = pipe_globals.stage_begin(skeleton_layer_path)
over_main = skeleton_layer_stage.OverridePrim("/main")
# re-define geo as SkelRoot and apply SkelBindingAPI
skelroot = UsdSkel.Root.Define(skeleton_layer_stage, over_main.GetPath().AppendChild("geo"))
UsdSkel.BindingAPI.Apply(skelroot.GetPrim())
# create new skeleton from original and rename joints
skeleton = UsdSkel.Skeleton.Define(skeleton_layer_stage, skelroot.GetPath().AppendChild("skeleton"))
skeleton.GetBindTransformsAttr().Set( original_skeleton.GetBindTransformsAttr().Get())
skeleton.GetRestTransformsAttr().Set( original_skeleton.GetRestTransformsAttr().Get())
joints = original_skeleton.GetJointsAttr().Get()
new_joints = []
for joint in joints:
    new_joints.append(rename_joint(joint))
skeleton.GetJointsAttr().Set(new_joints)
# add skeleton to skel root
UsdSkel.BindingAPI(skelroot.GetPrim()).GetSkeletonRel().AddTarget(skeleton.GetPath())
# from original mesh, get the skinning weights, as the skeleton layer should bring the skinning weights for the geo as well as the skel joints
over_geo_body_prim = skeleton_layer_stage.OverridePrim("/main/geo/body")
UsdSkel.BindingAPI.Apply(over_geo_body_prim)
skel_api = UsdSkel.BindingAPI(over_geo_body_prim)
skel_api.GetGeomBindTransformAttr().Set(original_skel_api.GetGeomBindTransformAttr().Get())
jointIndices = skel_api.CreateJointIndicesPrimvar(False, 5)
jointIndices.Set(original_skel_api.GetJointIndicesAttr().Get())
jointWeights = skel_api.CreateJointWeightsPrimvar(False, 5)
jointWeights.Set(original_skel_api.GetJointWeightsAttr().Get())
joints = original_skel_api.GetJointsAttr().Get()
new_joints = []
for joint in joints:
    new_joints.append(rename_joint(joint))
skel_api.GetJointsAttr().Set(new_joints)
# close skeleton layer
pipe_globals.stage_end( skeleton_layer_stage )

# create shot animation layer by overriding the skeleton animation to the skelroot of the asset odie
#
animation_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "odie01", "animation", "animated_proxy.usd")
animation_layer_frame_start = 1000
# increase length by 100 frames, to give some extra seconds for some lights potentially to get on
animation_layer_frame_end = animation_layer_frame_start + ( anim_frame_end - anim_frame_start ) + 100.0
animation_layer_stage = pipe_globals.stage_begin(animation_layer_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
# add a new skeleton animation prim and link it to the skelroot over
over_skel_root = UsdSkel.Root( animation_layer_stage.OverridePrim("/main/proxy/geo") )
skeleton_animation = UsdSkel.Animation.Define(animation_layer_stage, "/main/proxy/geo/animation")
# bind animation to odie skelroot
UsdSkel.BindingAPI(over_skel_root).GetAnimationSourceRel().AddTarget(skeleton_animation.GetPath())
# copy static and animated attributes from original skeleton animation to new one, remapping the frames to the shot framerange
i = 0
for input_frame in range( int(anim_frame_start), int(anim_frame_end) ):
    rotations = original_skeleton_animation.GetRotationsAttr().Get(float(input_frame))
    skeleton_animation.GetRotationsAttr().Set(rotations, float(animation_layer_frame_start + 100.0 + i))
    translations = original_skeleton_animation.GetTranslationsAttr().Get(float(input_frame))
    skeleton_animation.GetTranslationsAttr().Set(translations, float(animation_layer_frame_start + 100.0 + i))
    i += 1
joints = original_skeleton_animation.GetJointsAttr().Get()
new_joints = []
for joint in joints:
    new_joints.append(rename_joint(joint))
skeleton_animation.GetJointsAttr().Set(new_joints)
scales = original_skeleton_animation.GetScalesAttr().Get()
skeleton_animation.GetScalesAttr().Set(scales)
# close animated payload...
pipe_globals.stage_end( animation_layer_stage )
# ...and recompose in odie01 animation fragment
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
