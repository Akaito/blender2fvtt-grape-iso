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
        #if object.name != 'wall.002': continue
        if object.name.startswith('wall'):
            print('Object [{}]'.format(object.name))
            mesh = object.data
            obj_pos__world = object.location
            print('obj world pos: {}'.format(obj_pos__world))
            bbox_center__world, bbox_center_bottom__world = vec_center_bottom(object.bound_box, object.matrix_world)
            print('bbox_center__world: {}'.format(bbox_center__world))
            print('     bottom:        {}'.format(bbox_center_bottom__world))

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

