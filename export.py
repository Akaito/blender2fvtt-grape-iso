# Terminology:
#   blender wall: an object named `wall*` in Blender.
#   foundry wall: a start/end point pair to be made in Foundry.

import bpy
import json
from mathutils import *
from math import *
import os
import sys


CAMERA_NAME = 'iso-camera'
OUTPUT_FOLDER = 'C:\\Users\\akait\\AppData\\Local\\FoundryVTT\\Data\\worlds\\5e-srd\\assets\\grape test\\iso-walls'
FOUNDRY_GRID_SIZE = 100
#BLENDER_INCHES_PER_WORLD_UNIT = 1  # TODO

# Don't use real camera position, since it
#   could be on the 'wrong' side of the origin, etc.
TOWARD_CAMERA_DIR = Vector((1,-1,0)).normalized()
# Note: This is just the orthographic projection's translation (T).
#       Missing the scale (S).
#       See https://en.wikipedia.org/wiki/Orthographic_projection#Geometry
ORTHO_PROJ = Matrix.OrthoProjection(
        Vector((1,-1,1)),
        4
        )
print('ORTHO_PROJ', ORTHO_PROJ)

# Note: a 1x1 floor tile is roughly a PPI*1.8 x PPI*1.06 image (see The Iso Explorer).
# Note: a 1x1 floor tile has Blender camera ortho scale very near to sqrt(2).
# Next: Once the larget object is found, figure out if it's tall or wide, and scale
#       everything by that.
#       Or, stick to floor measurements?
# Next: Something with max X length + max Y length * WIDTH_PER_XY?
# If the rendered object is straight up/down from its max base,
# max X length * max Y length * WIDTH_PER_XY is the output image width.
# For example, a 2x2 patch of ground would yield 2*2*WIDTH_PER_XY
#MAGIC_SCALE = 1.8
MAGIC_SCALE = sqrt(pi)
WIDTH_PER_XY = (FOUNDRY_GRID_SIZE * MAGIC_SCALE) / 2


#####
## Code from https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix/86570#86570
def project_3d_point(camera: bpy.types.Object,
                     p: Vector,
                     render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """
    Given a camera and its projection matrix M;
    given p, a 3d point to project:

    Compute P’ = M * P
    P’= (x’, y’, z’, w')

    Ignore z'
    Normalize in:
    x’’ = x’ / w’
    y’’ = y’ / w’

    x’’ is the screen coordinate in normalised range -1 (left) +1 (right)
    y’’ is the screen coordinate in  normalised range -1 (bottom) +1 (top)

    :param camera: The camera for which we want the projection
    :param p: The 3D point to project
    :param render: The render settings associated to the scene.
    :return: The 2D projected point in normalized range [-1, 1] (left to right, bottom to top)
    """

    if camera.type != 'CAMERA':
        raise Exception("Object {} is not a camera.".format(camera.name))

    if len(p) != 3:
        raise Exception("Vector {} is not three-dimensional".format(p))

    # Get the two components to calculate M
    modelview_matrix = camera.matrix_world.inverted()
    projection_matrix = camera.calc_matrix_camera(
        bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph,
        x = render.resolution_x,
        y = render.resolution_y,
        scale_x = render.pixel_aspect_x,
        scale_y = render.pixel_aspect_y,
    )

    # print(projection_matrix * modelview_matrix)

    # Compute P’ = M * P
    p1 = projection_matrix @ modelview_matrix @ Vector((p.x, p.y, p.z, 1))

    # Normalize in: x’’ = x’ / w’, y’’ = y’ / w’
    p2 = Vector(((p1.x/p1.w, p1.y/p1.w)))

    return p2

#camera = bpy.data.objects[CAMERA_NAME]  # or bpy.context.active_object
render = bpy.context.scene.render

'''
P = Vector((-0.002170146, 0.409979939, 0.162410125))

print("Projecting point {} for camera '{:s}' into resolution {:d}x{:d}..."
      .format(P, camera.name, render.resolution_x, render.resolution_y))

proj_p = project_3d_point(camera=camera, p=P, render=render)
print("Projected point (homogeneous coords): {}.".format(proj_p))

proj_p_pixels = Vector(((render.resolution_x-1) * (proj_p.x + 1) / 2, (render.resolution_y - 1) * (proj_p.y - 1) / (-2)))
print("Projected point (pixel coords): {}.".format(proj_p_pixels))
'''
## end Blender Stack Exchange code for world->pixel projection.
#####

# Functionized code from the Stack Exchange example, above.
def pixel_from_camera(point__camera: Vector, render_width, render_height) -> Vector:
    return Vector((
            (render_height - 1) * (point__camera.y - 1) / -2,
            (render_width  - 1) * (point__camera.x + 1) /  2
            ))


def get_resolution(ortho_scale):
    return (FOUNDRY_GRID_SIZE * MAGIC_SCALE) * (ortho_scale / sqrt(2))


# Mostly just here to help debug by filtering down to objects of interest.
def all_objects():
    return [o for o in bpy.data.objects if o.name == 'wall.floorTile1x1']
    return bpy.data.objects


def do_render(camera, largest_ortho, obj, outpath):
    # select object and move camera to it
    #context.view_layer.objects.active = bpy.data.objects[obj.name]
    obj.select_set(True)
    print(bpy.ops.view3d.camera_to_view_selected())
    obj.select_set(False)
    #bpy.data.cameras['Camera'].ortho_scale = largest_ortho
    ortho_scale = bpy.data.cameras['Camera'].ortho_scale

    # set output resolution
    # TODO : Why is our main camera named 'Camera' in this collection?
    scene.render.resolution_x = get_resolution(ortho_scale)
    scene.render.resolution_y = get_resolution(ortho_scale)

    # render to file
    context.scene.render.filepath = os.path.join(outpath, '{}.png'.format(obj.name))
    bpy.ops.render.render(write_still = True)


def calc_largest_ortho_scale(camera):
    largest_ortho = 0
    render_size = 0
    for object in all_objects():
        if object.type != 'MESH': continue
        object.select_set(True)
        print(bpy.ops.view3d.camera_to_view_selected())
        object.select_set(False)
        current_ortho_scale = bpy.data.cameras['Camera'].ortho_scale
        print(object.name, 'has ortho scale', current_ortho_scale)
        # TODO : Why is our main camera named 'Camera' in this collection?
        if current_ortho_scale > largest_ortho:
            largest_ortho = bpy.data.cameras['Camera'].ortho_scale
            render_size = get_resolution(largest_ortho)
    print('largest_ortho', largest_ortho)
    return largest_ortho, render_size


# deprecated
def calc_render_size(ortho_scale, object, camera):
    #min_x = sys.maxint
    #max_x = -sys.maxint
    #min_y = sys.maxint
    #max_y = -sys.maxin
    # Foundry PPI (scene grid size) with grape_juice-isometrics wants
    # a 1x1 floor tile image to be about 180 x 106 pixels.
    # (Going by The Iso Explorer's assets.)
    pass

    # (x+y) * (FOUNDRY_GRID_SIZE * 0.9)
    # (x+y) * (FOUNDRY_GRID_SIZE * 0.9) * (ortho_scale / sqrt(2))


context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ EXPORT.PY ~*~')


def vec_center(vec_list):
    center = Vector((0,0,0))
    for pos in vec_list:
        center += Vector(pos)
    center /= len(vec_list)
    return center

def vec_center_bottom(vec_list, mat=None):
    center = Vector((0,0,0))
    z_min = sys.float_info.max
    for pos in vec_list:
        z_min = min(z_min, pos[2])
        center += Vector(pos)
    center /= len(vec_list)
    bottom = Vector((center.x, center.y, z_min))
    if mat is None:
        return center, bottom
    return mat @ center, mat @ bottom


def prepare():
    # TODO : Again with the special camera name.
    camera = bpy.data.cameras['Camera']
    cleanup_data = {
            'film_transparent': scene.render.film_transparent,
            'objects': {},
            'render_resolution_x': scene.render.resolution_x,
            'render_resolution_y': scene.render.resolution_y,
            'Camera': {
                #'ortho_scale': camera.ortho_scale,  # TODO
                #'location': camera.location,  # TODO
                'type': camera.type,
                }
            }
    scene.render.film_transparent = True
    # Just have to have a square output for now.  Scale determined later.
    # Future optimization: Pull camera in to exact object dimensions?
    scene.render.resolution_x = 100
    scene.render.resolution_y = 100
    camera.type = 'ORTHO'

    # Prepare all objects.
    for object in bpy.data.objects:
        cleanup_data['objects'][object.name] = {
                'selected': object.select_get(),
                'hide_render': object.hide_render,
                }
        object.select_set(False) # deselect objects
        object.hide_render = object.type == 'MESH'  # hide mesh objects

    return cleanup_data


def cleanup(cleanup_data):
    # restore original render, etc. states
    scene.render.film_transparent = cleanup_data['film_transparent']
    scene.render.resolution_x = cleanup_data['render_resolution_x']
    scene.render.resolution_y = cleanup_data['render_resolution_y']
    bpy.data.cameras['Camera'].type = cleanup_data['Camera']['type']
    for object in bpy.data.objects:
        obj_data = cleanup_data['objects'][object.name]
        object.hide_render = obj_data['hide_render']
        object.select_set(obj_data['selected'])


def main(should_render = True):
    #camera = scene.collection.all_objects.get(CAMERA_NAME)
    camera = bpy.data.objects[CAMERA_NAME]
    assert camera is not None, 'Please have a camera named {}'.format(CAMERA_NAME)
    assert camera.track_axis == 'NEG_Z', 'Currently only support cameras that track the negative-z axis.'
    # TODO : Fix hard-coded special camera name.
    camera_camera = bpy.data.cameras['Camera']
    jsn = {
            'blenderWalls': [],
            'scale': 0,  # TODO
            }

    objects = all_objects()

    largest_ortho, largest_render_size = calc_largest_ortho_scale(camera)
    scene.render.resolution_x = largest_render_size
    scene.render.resolution_y = largest_render_size

    for object in objects:
        #if object.name != 'wall.001': continue  # debugging-only!
        if object.name.startswith('wall'):
            print('Object [{}]'.format(object.name))
            mesh = object.data
            obj_pos__world = object.location
            print('obj world pos: {}'.format(obj_pos__world))
            bbox_center__world, bbox_center_bottom__world = vec_center_bottom(object.bound_box, object.matrix_world)
            print('bbox_center__world: {}'.format(bbox_center__world))
            print('     bottom:        {}'.format(bbox_center_bottom__world))

            object.select_set(True)
            bpy.ops.view3d.camera_to_view_selected()  # place camera
            object.select_set(False)
            # TODO : Special object name 'Camera': why?
            ortho_scale = camera_camera.ortho_scale
            #print(object.name, 'ortho_scale', ortho_scale)
            resolution = get_resolution(ortho_scale)
            render.resolution_x = resolution
            render.resolution_y = resolution
            #camera_pos = camera.location
            #print(object.name, 'camera is at', camera_pos)

            camera_forward__world = (camera.matrix_world @ Vector((0,0,-1))) - camera.location
            camera_upper_left__world = (camera.matrix_world @ Vector((-ortho_scale/2,ortho_scale/2,0)))
            render_upper_left__world = geometry.intersect_line_plane(
                    camera_upper_left__world,
                    camera_upper_left__world + camera_forward__world,
                    Vector((0,0,0)),
                    Vector((0,0,1))
                    )
            print('anti-camera upper-left', render_upper_left__world)

            '''
            print('camera scale:', bpy.data.cameras['Camera'].ortho_scale)
            originInCamera = \
                    project_3d_point(camera, Vector((0,0,0)))
            originPlusOneInCamera = \
                    project_3d_point(camera, Vector((1,0,0)))
            cameraUnitsPerLateralWorldUnit = (originPlusOneInCamera - originInCamera).length
            '''

            walls = []
            for edge in mesh.edges:
                edge_v0__local = Vector(mesh.vertices[edge.vertices[0]].co)
                edge_v1__local = Vector(mesh.vertices[edge.vertices[1]].co)
                #print('edge v0 local:   {}'.format(edge_v0__local))
                #print('edge v1 local:   {}'.format(edge_v1__local))

                edge_v0__world = object.matrix_world @ edge_v0__local
                edge_v1__world = object.matrix_world @ edge_v1__local
                #print('edge v0 world:  {}'.format(edge_v0__world))
                #print('edge v1 world:  {}'.format(edge_v1__world))

                # ignore edges not along the bbox's bottom plane
                if abs(bbox_center_bottom__world.z - edge_v0__world.z) > 0.01: continue
                if abs(bbox_center_bottom__world.z - edge_v1__world.z) > 0.01: continue

                is_front_facing = False
                # Edge is only a front-facing exported wall if
                #   at least one face using it is front-facing.
                for polygon in mesh.polygons:
                    if edge.vertices[0] not in polygon.vertices: continue
                    if edge.vertices[1] not in polygon.vertices: continue
                    print('poly normal:  {}'.format(polygon.normal))
                    (_, rot, _) = object.matrix_world.decompose()
                    normal__world = (rot @ polygon.normal).normalized()
                    print('normal world: {}'.format(normal__world))
                    is_front = normal__world.dot(TOWARD_CAMERA_DIR) > 0
                    if is_front:
                        is_front_facing = True
                        break

                #print('is front? {}'.format(is_front_facing))

                edge_v0__render = project_3d_point(camera, edge_v0__world)
                edge_v1__render = project_3d_point(camera, edge_v1__world)
                #print('edge_v0__world:', edge_v0__world)
                #print('edge_v0__render:', edge_v0__render)

                edge_v0__pixel = pixel_from_camera(edge_v0__render, get_resolution(ortho_scale), get_resolution(ortho_scale))
                edge_v1__pixel = pixel_from_camera(edge_v1__render, get_resolution(ortho_scale), get_resolution(ortho_scale))

                walls.append({
                    #'texture': obj.data.image?
                    'isFrontFacing': is_front_facing,
                    'a': {
                        'world': [
                            #'{:0.6}'.format(edge_v0__world.x),
                            round(edge_v0__world.x, 6),
                            round(edge_v0__world.y, 6),
                            round(edge_v0__world.z, 6),
                            ],
                        'renderCamera': [
                            round(edge_v0__render.x, 6),
                            round(edge_v0__render.y, 6),
                            ],
                        'imagePixel': [
                            round(edge_v0__pixel.x, 6),
                            round(edge_v0__pixel.y, 6),
                            ],
                        },
                    'b': {
                        'world': [
                            round(edge_v1__world.x, 6),
                            round(edge_v1__world.y, 6),
                            round(edge_v1__world.z, 6),
                            ],
                        'renderCamera': [
                            round(edge_v1__render.x, 6),
                            round(edge_v1__render.y, 6),
                            ],
                        'imagePixel': [
                            round(edge_v1__pixel.x, 6),
                            round(edge_v1__pixel.y, 6),
                            ],
                        },
                })

            # Add to blender walls any objects resulting in at least one Foundry wall.
            if len(walls) > 0:
                jsn['blenderWalls'].append({
                    'blenderObjectName': object.name,
                    'foundryWalls': walls,
                    'renderUpperLeftWorld': [
                        round(render_upper_left__world.x, 6),
                        round(render_upper_left__world.y, 6),
                        ],
                    #'renderUnitsPerLateralWorldUnit': cameraUnitsPerLateralWorldUnit,
                    'renderWidth': get_resolution(ortho_scale),
                    'renderHeight': get_resolution(ortho_scale),
                })

    # Render wall sprites.
    if should_render:
        for object in all_objects():
            # skip non-mesh objects
            if not object.type == 'MESH': continue
            # skip non-wall objects
            #if not object.name.startswith('wall'): continue

            print('Rendering sprite for {}'.format(object.name))
            object.hide_render = False
            do_render(camera, largest_ortho, object, OUTPUT_FOLDER)
            object.hide_render = True

    #print(json.dumps(jsn, indent=2, sort_keys=True))
    print(json.dumps(jsn, sort_keys=True))

cleanup_data = prepare()
try:
    main()
finally:
    cleanup(cleanup_data)

