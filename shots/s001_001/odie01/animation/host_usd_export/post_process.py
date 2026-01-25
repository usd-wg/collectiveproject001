import importlib.util
import os
import sys
sys.dont_write_bytecode = True

module_name = "pipe_globals"
module_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "pipeline", "pipe_globals.py")
spec = importlib.util.spec_from_file_location(module_name, module_path)
pipe_globals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipe_globals)

from pxr import Usd, UsdGeom, UsdSkel, Sdf, UsdShade

def rename_joint(joint):
    # hacky way to make joint names nicer
    # Maya added a few extra bits we can take out
    n = joint
    n = n.replace("Odie_rig1_","")
    n = n.replace("_M","")
    return n

# load animation file from Stephanie and retrieve original prims
#
stage = Usd.Stage.Open("odie_idea01_animation_v10.usd")
anim_frame_start = stage.GetStartTimeCode()
anim_frame_end = stage.GetEndTimeCode()
anim_fps = stage.GetTimeCodesPerSecond()
original_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath("/Odie_new_rig/Odie_rig1_root"))
original_skeleton_animation = UsdSkel.Animation(stage.GetPrimAtPath("/Odie_new_rig/Odie_rig1_root/Animation"))
original_mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/Odie_new_rig/Odie_rig1_Odie"))
original_skel_api = UsdSkel.BindingAPI(original_mesh.GetPrim())

# update original mesh from new one in the animation file
#
model_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "assets", "odie", "proxy", "model", "payload.usda")
model_layer_stage = pipe_globals.stage_begin(model_layer_path)
UsdGeom.SetStageMetersPerUnit(model_layer_stage, UsdGeom.LinearUnits.centimeters)
UsdGeom.SetStageUpAxis(model_layer_stage, UsdGeom.Tokens.y)
model_layer_main_prim = UsdGeom.Xform.Define(model_layer_stage, "/main")
model_layer_stage.SetDefaultPrim(model_layer_main_prim.GetPrim())
model_layer_mesh_prim = UsdGeom.Mesh.Define(model_layer_stage, model_layer_main_prim.GetPath().AppendChild("body"))
# copy specifiy properties from original mesh
model_layer_mesh_prim.GetDoubleSidedAttr().Set( original_mesh.GetDoubleSidedAttr().Get())
model_layer_mesh_prim.GetExtentAttr().Set( original_mesh.GetExtentAttr().Get())
model_layer_mesh_prim.GetFaceVertexCountsAttr().Set( original_mesh.GetFaceVertexCountsAttr().Get())
model_layer_mesh_prim.GetFaceVertexIndicesAttr().Set( original_mesh.GetFaceVertexIndicesAttr().Get())
model_layer_mesh_prim.GetPointsAttr().Set( original_mesh.GetPointsAttr().Get())
primvar_st = UsdGeom.PrimvarsAPI(model_layer_mesh_prim).CreatePrimvar("primvars:st", Sdf.ValueTypeNames.TexCoord2fArray)
primvar_st.SetInterpolation(UsdGeom.Tokens.faceVarying)
primvar_st.Set( original_mesh.GetPrim().GetAttribute("primvars:st").Get())
model_layer_mesh_prim.GetPrim().CreateAttribute("primvars:st:indices", Sdf.ValueTypeNames.IntArray).Set( original_mesh.GetPrim().GetAttribute("primvars:st:indices").Get())
# and geomsubsets
mapping_subsets = [
    ("Body_Primary","SG"),
    ("Body_Secondary","SG1"),
    ("Body_Tertiary","1SG2"),
    ("Eye_Pupil_Border","1SG3"),
    ("Eye_Pupil_Center","1SG4"),
    ("Eye_Iris","1SG5"),
    ("Eye_Sclera","1SG6"),
]
for m in mapping_subsets:
    UsdGeom.Subset.CreateGeomSubset(model_layer_mesh_prim, m[0], UsdGeom.Tokens.face, stage.GetPrimAtPath("/Odie_new_rig/Odie_rig1_Odie/Odie_rig1_Odie{}".format(m[1])).GetAttribute("indices").Get(), "materialBind", "partition")
# close model layer
pipe_globals.stage_end( model_layer_stage )


# create the skeleton layer for the odie asset
#
skeleton_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "assets", "odie", "proxy", "skeleton", "index.usda")
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
# make the skeleton purpose guide
skeleton.GetPrim().GetAttribute("purpose").Set("guide")
# from original mesh, get the skinning weights, as the skeleton layer should bring the skinning weights for the geo as well as the skel joints
over_geo_body_prim = skeleton_layer_stage.OverridePrim("/main/geo/body")
UsdSkel.BindingAPI.Apply(over_geo_body_prim)
skel_api = UsdSkel.BindingAPI(over_geo_body_prim)
skel_api.GetGeomBindTransformAttr().Set(original_skel_api.GetGeomBindTransformAttr().Get())
jointIndices = skel_api.CreateJointIndicesPrimvar(False, 4)
jointIndices.Set(original_skel_api.GetJointIndicesAttr().Get())
jointWeights = skel_api.CreateJointWeightsPrimvar(False, 4)
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
animation_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "animation", "animated_proxy.usd")
# match shot-frame range here
animation_layer_frame_start = 1000
animation_layer_frame_end = 1480
animation_layer_stage = pipe_globals.stage_begin(animation_layer_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
# add a new skeleton animation prim and link it to the skelroot over
over_skel_root = UsdSkel.Root( animation_layer_stage.OverridePrim("/main/proxy/geo") )
skeleton_animation = UsdSkel.Animation.Define(animation_layer_stage, "/main/proxy/geo/animation")
# bind animation to odie skelroot
UsdSkel.BindingAPI(over_skel_root).GetAnimationSourceRel().AddTarget(skeleton_animation.GetPath())
# copy static and animated attributes from original skeleton animation to new one, remapping the frames to the shot framerange
# and make sure to repeat frame 1101 position for all frames from 1000 to 1100
for input_frame in range( int(animation_layer_frame_start), int(animation_layer_frame_end) ):
    anim_input_frame = max(input_frame, 1101)
    rotations = original_skeleton_animation.GetRotationsAttr().Get(float(anim_input_frame))
    skeleton_animation.GetRotationsAttr().Set(rotations, float(input_frame))
    translations = original_skeleton_animation.GetTranslationsAttr().Get(float(anim_input_frame))
    skeleton_animation.GetTranslationsAttr().Set(translations, float(input_frame))
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
animation_frag_path = os.path.join(os.path.dirname(__file__), "..", "..", "animation", "index.usda")
frag_stage = pipe_globals.stage_begin(animation_frag_path, start=animation_layer_frame_start, end=animation_layer_frame_end, fps=anim_fps)
frag_stage.GetRootLayer().subLayerPaths.append("animated_proxy.usd")
pipe_globals.stage_end( frag_stage )

