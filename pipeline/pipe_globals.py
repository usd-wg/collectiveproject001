from pxr import Usd, UsdGeom, Sdf, UsdRender, Gf, UsdShade

import os
import math
import pathlib


def stage_begin(filename, start=1.0, end=1.0, fps=24.0):
    layer = Sdf.Layer.CreateNew( filename, args={'format':'usda'} )
    stage = Usd.Stage.Open( layer )
    stage.SetStartTimeCode(start)
    stage.SetEndTimeCode(end)
    stage.SetTimeCodesPerSecond(fps)
    stage.SetFramesPerSecond(fps)
    stage.SetMetadata("metersPerUnit", 0.01 )
    stage.SetMetadata("upAxis", "Y")
    return stage


def stage_end(stage):
    stage.GetRootLayer().Save()

# For Asset Paths, use POSIX-style paths (/), which still work in USD on Windows (but not the reverse)
def anchor_path(path, root_path):
    # NOTE: pathlib.Path.relpath() supports walk_up kwarg in 3.12+
    return pathlib.Path(os.path.relpath(path, os.path.dirname(root_path))).as_posix()

# For un-anchored Asset Path identifiers (e.g. assetInfo), assume relative to show root
def get_identifier_from_filename(asset_filename):
    return pathlib.Path(asset_filename).relative_to(pathlib.Path(get_show_folder())).as_posix()

def get_or_create_world_prim(stage):
    root_path = Sdf.Path.absoluteRootPath
    world_prim_path = root_path.AppendChild("World")
    world_prim = stage.GetPrimAtPath(world_prim_path)
    if not world_prim:
        # world prim as xform to be able to transform it
        world_prim = UsdGeom.Xform.Define(stage,world_prim_path)
        world_prim.GetPrim().SetMetadata("kind","group")
    return world_prim


def get_or_create_cameras_prim(stage):
    world_prim = get_or_create_world_prim(stage)
    cameras_prim_path = world_prim.GetPath().AppendChild("Cameras")
    cameras_prim = stage.GetPrimAtPath(cameras_prim_path)
    if not cameras_prim:
        cameras_prim = UsdGeom.Scope.Define(stage,cameras_prim_path)
        #cameras_prim.GetPrim().SetMetadata("kind","group")
    return cameras_prim


def get_default_camera_settings():
    return {
            "shutter:open":  { "type":Sdf.ValueTypeNames.Double,   "value":0.0 },
            "shutter:close": { "type":Sdf.ValueTypeNames.Double,   "value":0.0 }
        }


def create_default_camerarig( stage, camera_settings={}, resolution=[1024,768]):
    # force-create default camera as root-xform with any camera-rig underneath
    # NOTE: Do we need a full rig ? Maybe not, could simplify this.
    cameras_prim = get_or_create_cameras_prim(stage)
    camera_xform_name = "mainCamera"
    camera_name = "mono" # mono, left, right, center, etc.
    camera_xform_prim_path = cameras_prim.GetPath().AppendChild(camera_xform_name)
    camera_xform_prim = UsdGeom.Xform.Define(stage,camera_xform_prim_path)
    camera_prim_path = camera_xform_prim.GetPath().AppendChild(camera_name)
    camera_prim = UsdGeom.Camera.Define(stage,camera_prim_path)
    
    camera_prim.CreateFocalLengthAttr().Set(32.0)
    camera_prim.CreateClippingRangeAttr().Set((0.1,100000.0))
    camera_prim.CreateHorizontalApertureAttr().Set(resolution[0]/100.0)
    camera_prim.CreateVerticalApertureAttr().Set(resolution[1]/100.0)
    if len(camera_settings) == 0:
        camera_settings = get_default_camera_settings()
    for s in camera_settings.keys():
        camera_prim.GetPrim().CreateAttribute( "%s" % s, camera_settings[s]["type"] ).Set( camera_settings[s]["value"] )

    return (camera_xform_prim, camera_prim)


def make_turntable( stage, camera_xform_prim, camera_prim, frame_begin=1.0, frame_end=120.0, bbox=None, bbox_dist_multiplier=2.0, elevation=10):
    if bbox is None:
        # scene bounds
        bbox = UsdGeom.BBoxCache(0.0,["render","proxy","default"],useExtentsHint=True).ComputeWorldBound( stage.GetPseudoRoot() )

    ccenter = bbox.ComputeCentroid()
    crange = bbox.ComputeAlignedRange()
    dim = crange.GetSize()
    plane_corner = Gf.Vec2d(dim[0], dim[1])/2
    plane_radius = math.sqrt( Gf.Dot(plane_corner, plane_corner) )
    half_fov = 12
    distance = plane_radius / math.tan( Gf.DegreesToRadians( half_fov ) )
    distance += dim[2] * bbox_dist_multiplier

    #camera_xform_prim.ClearXformOpOrder()
    translateOp = camera_xform_prim.AddTranslateOp( opSuffix="zoomedIn" )
    rotateYOp = camera_xform_prim.AddRotateYOp( opSuffix="zoomedIn" )
    rotateXOp = camera_xform_prim.AddRotateXOp( opSuffix="zoomedIn" )

    for frame in range(int(frame_begin), int(frame_end)):
        cf = frame - frame_begin
        cr = cf*360.0/(frame_end - frame_begin)
        y_pos = math.sin(Gf.DegreesToRadians( elevation ))*distance
        y_pos_cos = math.cos(Gf.DegreesToRadians( elevation ))
        x_pos = (math.sin(Gf.DegreesToRadians( cr ))*distance)*y_pos_cos
        z_pos = (math.cos(Gf.DegreesToRadians( cr ))*distance)*y_pos_cos
        translateOp.Set( ccenter + Gf.Vec3d(x_pos, y_pos, z_pos), frame )        
        rotateYOp.Set( cr, frame )
        rotateXOp.Set( -elevation, frame )

    return True


def add_product_to_rendersettings( product_prim, rendersettings_prim ):
    if rendersettings_prim is not None and product_prim is not None:
        rendersettings_prim.GetProductsRel().AddTarget( product_prim.GetPath() )


def add_var_to_product( var_prim, product_prim ):
    if product_prim is not None and var_prim is not None:
        product_prim.GetOrderedVarsRel().AddTarget( var_prim.GetPath() )


def create_renderproduct(
    stage,
    product_name='',
    product_filepath='',
    driver_parameters={},
    camera_prim=None,
    resolution=[1024,768],
    ndc=(0,0,1,1),
    par=1.0,
    ):

    prim = UsdRender.Product.Define( stage, "/Render/Products/{name}".format(name=product_name) )
    prim.GetAspectRatioConformPolicyAttr().Set( "expandAperture" )
    prim.GetProductNameAttr().Set( product_filepath )
    prim.GetResolutionAttr().Set( Gf.Vec2i( resolution ) )
    prim.GetDataWindowNDCAttr().Set( ndc )
    prim.GetPixelAspectRatioAttr().Set( par )
    prim.GetInstantaneousShutterAttr().Set(False)
    
    prim.GetCameraRel().SetTargets( [ camera_prim.GetPath() ] )

    driver_parameters = {
        "imageName":{ "type":Sdf.ValueTypeNames.String, "value":"beauty" },
        "partName":{ "type":Sdf.ValueTypeNames.String, "value":"rgba" },
        "driver:imagePath":{ "type":Sdf.ValueTypeNames.String, "value":product_filepath },
        "driver:aovNames":{ "type":Sdf.ValueTypeNames.String, "value":"rgba" },
        "driver:parameters:subimage":{ "type":Sdf.ValueTypeNames.String, "value":"rgba" },
    } 
    for a in driver_parameters.keys():
        prim.GetPrim().CreateAttribute( a, driver_parameters[a]["type"] ).Set( driver_parameters[a]["value"] )

    return prim


def create_rendervar(
    stage, 
    aov_name='',
    aov_source='',
    aov_format='',
    ):

    prim = UsdRender.Var.Define( stage, "/Render/Products/Vars/{name}".format(name=aov_name) )

    prim.GetSourceNameAttr().Set( aov_name )
    prim.GetPrim().CreateAttribute( "driver:parameters:aov:name", Sdf.ValueTypeNames.String ).Set( aov_name )
    prim.GetPrim().CreateAttribute( "driver:parameters:aov:source", Sdf.ValueTypeNames.String ).Set( aov_source )
    if aov_format != '':
        prim.GetPrim().CreateAttribute( "driver:parameters:aov:format", Sdf.ValueTypeNames.String ).Set( aov_format )

    return prim


def create_rendersettings( 
        stage, 
        prim_path='/Render/rendersettings', 
        resolution=[1024,768], 
        camera_prim=None, 
        ndc=(0,0,1,1), 
        par=1.0, 
        purposes=["default"], 
        render_settings={} ):
    prim = None
    render_scope_prim = UsdGeom.Scope.Define( stage, '/Render' )
    prim = UsdRender.Settings.Define( stage, prim_path )

    prim.GetAspectRatioConformPolicyAttr().Set( "expandAperture" )
    prim.GetResolutionAttr().Set( Gf.Vec2i( resolution ) )
    prim.GetDataWindowNDCAttr().Set( ndc )
    prim.GetPixelAspectRatioAttr().Set( par )
    prim.GetInstantaneousShutterAttr().Set( False )
    prim.GetIncludedPurposesAttr().Set( purposes )

    stage.SetMetadata("renderSettingsPrimPath", prim_path )

    prim.GetCameraRel().SetTargets( [ camera_prim.GetPath() ] )

    for k in render_settings.keys():
        attr = prim.GetPrim().CreateAttribute( k, render_settings[k]["type"] )
        attr.Set( render_settings[k]["value"] )

    return prim


def create_root_prim(stage, kind="", asset_name="", asset_filename="", asset_version=""):
    root_path = Sdf.Path.absoluteRootPath
    asset_root_path = root_path.AppendChild("main")
    asset_root_prim = UsdGeom.Xform.Define(stage, asset_root_path)
    modelAPI = Usd.ModelAPI(asset_root_prim)
    if kind != "":
        modelAPI.SetKind(kind)
    if asset_name != "":
        modelAPI.SetAssetName(asset_name)
    if asset_filename != "":
        asset_identifier = get_identifier_from_filename(asset_filename)
        modelAPI.SetAssetIdentifier(asset_identifier)
    if asset_version != "":
        modelAPI.SetAssetVersion(asset_version)    
    return asset_root_prim.GetPrim()


def override_root_prim(stage):
    root_path = Sdf.Path.absoluteRootPath
    asset_root_path = root_path.AppendChild("main")
    asset_root_prim = stage.OverridePrim(asset_root_path)
    return asset_root_prim.GetPrim()


def get_array_value_from_args(args, flag_short, flag_long):
    result = []
    i = 1
    while(i < len(args)):
        curr_arg = args[i]
        if curr_arg in [flag_short,flag_long]:
            i+=1
            result.append(str(args[i]))
        i+=1
    return result


def get_value_from_args(args, flag_short, flag_long):
    result = ""
    i = 1
    while(i < len(args)):
        curr_arg = args[i]
        if curr_arg in [flag_short,flag_long]:
            i+=1
            result = str(args[i])
            break
        i+=1
    return result


def mkdir_safe(path):
    try:
        os.mkdir(path)
    except:
        pass


def get_subfolder(root_path, subfolder):
    folder = os.path.join( root_path, subfolder )
    mkdir_safe(folder)
    return folder


def keep_folder(folder):
    f = open("{}/.keep".format(folder), "w")
    f.close()


def get_show_folder():
    show_root = os.path.normpath( os.path.join( os.path.dirname(os.path.abspath(__file__)), ".." ) )
    return show_root


def make_reviewer_per_purpose(stage, purpose, textures, framestart, frameend, resolution):
    purpose_prim = UsdGeom.Scope.Define(stage, f"/{purpose}")
    purpose_prim.GetPrim().GetAttribute("purpose").Set(purpose)
    geo_scope = UsdGeom.Scope.Define(stage, purpose_prim.GetPath().AppendChild("geo"))
    screen_mesh = UsdGeom.Mesh.Define(stage, geo_scope.GetPath().AppendChild("screen"))
    screen_mesh.CreateOrientationAttr().Set(UsdGeom.Tokens.rightHanded)
    screen_mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
    # I like the quad with its center at zero
    half_width = resolution[0]/2.0
    half_height = resolution[1]/2.0
    points = [
        (-half_width, -half_height, 0.0),
        (half_width, -half_height, 0.0),
        (half_width, half_height, 0.0),
        (-half_width, half_height, 0.0),
    ]
    screen_mesh.CreatePointsAttr().Set(points)
    screen_mesh.CreateFaceVertexCountsAttr().Set([ 4 ])
    screen_mesh.CreateFaceVertexIndicesAttr().Set([ 0, 1, 2, 3 ])
    screen_mesh.CreateExtentAttr([(-half_width, -half_height, 0), (half_width, half_height, 0)])
    st_var = UsdGeom.PrimvarsAPI(screen_mesh).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    st_var.Set([(0,0),(1,0),(1,1),(0,1)])

    mtl_scope = UsdGeom.Scope.Define(stage, purpose_prim.GetPath().AppendChild("mtl"))
    material = UsdShade.Material.Define(stage, mtl_scope.GetPath().AppendChild("reviewer_material"))
    shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("reviewer_shader") )
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((1.0,1.0,1.0))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    st_shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("primvar_st") )
    st_shader.CreateIdAttr("UsdPrimvarReader_float2")
    st_shader.CreateInput('varname',Sdf.ValueTypeNames.Token).Set("st")

    read_shader = UsdShade.Shader.Define(stage, material.GetPath().AppendChild("texture_diffuseColor") )
    read_shader.CreateIdAttr("UsdUVTexture")
    file_input = read_shader.CreateInput("file", Sdf.ValueTypeNames.Asset )
    for frame in range(framestart,frameend+1):
        file_input.Set( textures.replace("####",f"{frame:04}"), float(frame) )
    read_shader.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(st_shader.ConnectableAPI(), 'result')
    read_shader.CreateOutput( "rgb", Sdf.ValueTypeNames.Float3 )

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(read_shader.ConnectableAPI(), 'rgb')
    
    material.CreateSurfaceOutput().ConnectToSource( shader.ConnectableAPI(), "surface" )

    UsdShade.MaterialBindingAPI.Apply(screen_mesh.GetPrim())
    UsdShade.MaterialBindingAPI(screen_mesh).Bind(material)

