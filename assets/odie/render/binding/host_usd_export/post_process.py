import importlib.util
import os
import sys
sys.dont_write_bytecode = True

module_name = "pipe_globals"
module_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "pipeline", "pipe_globals.py")
spec = importlib.util.spec_from_file_location(module_name, module_path)
pipe_globals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipe_globals)

from pxr import Usd, UsdGeom, UsdSkel, Gf

def rename_joint(joint):
    # hacky way to make joint names nicer
    # Maya added a few extra bits we can take out
    n = joint
    n = n.replace("Odie_rig_","")
    n = n.replace("_M","")
    return n

def scaleXYZ(x):
    return Gf.Matrix4d().SetScale((x,x,x))
def rotateXYZ(ax,ay,az,x):
    return Gf.Matrix4d().SetRotate(Gf.Rotation((ax,ay,az),x))
def rotateX(x):
    return rotateXYZ(1,0,0,x)
def rotateY(x):
    return rotateXYZ(0,1,0,x)
def rotateZ(x):
    return rotateXYZ(0,0,1,x)

# load static file from Stephanie here
#
stage = Usd.Stage.Open("CarbonatedOdie_T_Pose_v06.usd")

# get original prims
#
original_skeleton = UsdSkel.Skeleton(stage.GetPrimAtPath("/SkelRoot/ODIE_Rigged/Root"))
original_mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/SkelRoot/Odie"))
original_skel_api = UsdSkel.BindingAPI(original_mesh.GetPrim())

# create the skeleton layer for the odie asset
#
skeleton_layer_path = os.path.join(os.path.dirname(__file__), "..", "..", "skeleton", "index.usda")
skeleton_layer_stage = pipe_globals.stage_begin(skeleton_layer_path)
over_main = skeleton_layer_stage.OverridePrim("/main")
# re-define geo as SkelRoot and apply SkelBindingAPI
skelroot = UsdSkel.Root.Define(skeleton_layer_stage, over_main.GetPath().AppendChild("geo"))
UsdSkel.BindingAPI.Apply(skelroot.GetPrim())

# create new skeleton from original and rename joints
#
skeleton = UsdSkel.Skeleton.Define(skeleton_layer_stage, skelroot.GetPath().AppendChild("skeleton"))

joints = original_skeleton.GetJointsAttr().Get()
new_joints = []
for joint in joints:
    new_joints.append(rename_joint(joint))
skeleton.GetJointsAttr().Set(new_joints)

# copy bind and rest transforms, transforming them to adjust for carbonated FBX transform space
#
orig_bind_transforms = original_skeleton.GetBindTransformsAttr().Get()
for i in range(len(orig_bind_transforms)):
    m = orig_bind_transforms[i] * scaleXYZ(0.01) * rotateY(180) * rotateX(90)
    orig_bind_transforms[i] = m
orig_rest_transforms = original_skeleton.GetRestTransformsAttr().Get()
for i in range(len(orig_rest_transforms)):
    m = orig_rest_transforms[i] * scaleXYZ(0.01) * rotateY(180)
    orig_rest_transforms[i] = m
    break
skeleton.GetBindTransformsAttr().Set( orig_bind_transforms )
skeleton.GetRestTransformsAttr().Set( orig_rest_transforms )

# add skeleton to skel root
UsdSkel.BindingAPI(skelroot.GetPrim()).GetSkeletonRel().AddTarget(skeleton.GetPath())

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
