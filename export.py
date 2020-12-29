# Terminology:
#   blender wall: an object named `wall*` in Blender.
#   foundry wall: a start/end point pair to be made in Foundry.

import bpy
import json
import mathutils
import math
import sys


CAMERA_NAME = 'iso-camera'
# Don't use real camera position, since it
#   could be on the 'wrong' side of the origin, etc.
TOWARD_CAMERA_DIR = mathutils.Vector((1,-1,0)).normalized()
# Note: This is just the orthographic projection's translation (T).
#       Missing the scale (S).
#       See https://en.wikipedia.org/wiki/Orthographic_projection#Geometry
ORTHO_PROJ = mathutils.Matrix.OrthoProjection(
        mathutils.Vector((1,-1,1)),
        4
        )
print('ORTHO_PROJ', ORTHO_PROJ)


#####
## Code from https://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix/86570#86570
def project_3d_point(camera: bpy.types.Object,
                     p: mathutils.Vector,
                     render: bpy.types.RenderSettings = bpy.context.scene.render) -> mathutils.Vector:
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
    p1 = projection_matrix @ modelview_matrix @ mathutils.Vector((p.x, p.y, p.z, 1))

    # Normalize in: x’’ = x’ / w’, y’’ = y’ / w’
    p2 = mathutils.Vector(((p1.x/p1.w, p1.y/p1.w)))

    return p2

camera = bpy.data.objects[CAMERA_NAME]  # or bpy.context.active_object
render = bpy.context.scene.render

P = mathutils.Vector((-0.002170146, 0.409979939, 0.162410125))

print("Projecting point {} for camera '{:s}' into resolution {:d}x{:d}..."
      .format(P, camera.name, render.resolution_x, render.resolution_y))

proj_p = project_3d_point(camera=camera, p=P, render=render)
print("Projected point (homogeneous coords): {}.".format(proj_p))

proj_p_pixels = mathutils.Vector(((render.resolution_x-1) * (proj_p.x + 1) / 2, (render.resolution_y - 1) * (proj_p.y - 1) / (-2)))
print("Projected point (pixel coords): {}.".format(proj_p_pixels))
## end Blender Stack Exchange code for world->pixel projection.
#####


context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ EXPORT.PY ~*~')

print(dir(context))
print(dir(scene))


def vec_center(vec_list):
    center = mathutils.Vector((0,0,0))
    for pos in vec_list:
        center += mathutils.Vector(pos)
    center /= len(vec_list)
    return center

def vec_center_bottom(vec_list, mat=None):
    center = mathutils.Vector((0,0,0))
    z_min = sys.float_info.max
    for pos in vec_list:
        z_min = min(z_min, pos[2])
        center += mathutils.Vector(pos)
    center /= len(vec_list)
    bottom = mathutils.Vector((center.x, center.y, z_min))
    if mat is None:
        return center, bottom
    return mat @ center, mat @ bottom


def main():
    camera = scene.collection.all_objects.get(CAMERA_NAME)
    assert camera is not None, 'Please have a camera named {}'.format(CAMERA_NAME)
    jsn = {
            'blenderWalls': []
    }

    objects = scene.collection.all_objects
    print('Number of objects: {}'.format(len(objects)))
    for object in objects:
        if object.name != 'wall.001': continue  # debugging-only!
        if object.name.startswith('wall'):
            print('Object [{}]'.format(object.name))
            mesh = object.data
            obj_pos__world = object.location
            print('obj world pos: {}'.format(obj_pos__world))
            bbox_center__world, bbox_center_bottom__world = vec_center_bottom(object.bound_box, object.matrix_world)
            print('bbox_center__world: {}'.format(bbox_center__world))
            print('     bottom:        {}'.format(bbox_center_bottom__world))

            # TODO : We also need to de-select EVERYTHING before doing this; like render.py.
            object.select_set(True)
            print(bpy.ops.view3d.camera_to_view_selected())
            object.select_set(False)

            walls = []
            for edge in mesh.edges:
                edge_v0__local = mathutils.Vector(mesh.vertices[edge.vertices[0]].co)
                edge_v1__local = mathutils.Vector(mesh.vertices[edge.vertices[1]].co)

                edge_v0__world = object.matrix_world @ edge_v0__local
                edge_v1__world = object.matrix_world @ edge_v1__local
                print('edge v0 world:  {}'.format(edge_v0__world))
                print('edge v1 world:  {}'.format(edge_v1__world))

                edge_midpoint__world = (edge_v0__world + edge_v1__world) / 2

                edge_vec = edge_v1__world - edge_v0__world
                left_norm = mathutils.Matrix

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

                print('midpoint world: {}'.format(edge_midpoint__world))
                print('is front? {}'.format(is_front_facing))

                # TODO : Why is it called 'Camera', and not the object's name?
                ortho_proj_scale = bpy.data.cameras['Camera'].ortho_scale
                #ortho_proj_scale_mtx = mathutils.Matrix.Scale(ortho_proj_scale)
                edge_v0__camera = (1 * ORTHO_PROJ) @ edge_v0__world
                edge_v1__camera = (1 * ORTHO_PROJ) @ edge_v1__world
                camera = bpy.data.objects[CAMERA_NAME]
                edge_v0__render = project_3d_point(camera, edge_v0__world)
                edge_v1__render = project_3d_point(camera, edge_v1__world)
                print('edge_v0__world:', edge_v0__world)
                print('edge_v0__render:', edge_v0__render)

                walls.append({
                    #'texture': obj.data.image?
                    'isFrontFacing': is_front_facing,
                    'a': [
                        round(edge_v0__world.x, 6),
                        round(edge_v0__world.y, 6),
                        round(edge_v0__world.z, 6),
                        ],
                    'b': [
                        round(edge_v1__world.x, 6),
                        round(edge_v1__world.y, 6),
                        round(edge_v1__world.z, 6),
                        ],
                })
            if len(walls) > 0:
                jsn['blenderWalls'].append({
                    'blenderObjectName': object.name,
                    'foundryWalls': walls,
                })

    print(json.dumps(jsn, indent=2, sort_keys=True))
main()

