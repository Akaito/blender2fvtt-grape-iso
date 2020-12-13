import bpy
import json
import mathutils
import math
import sys

CAMERA_NAME = 'iso-camera'

context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ EXPORT.PY ~*~')

print(dir(context))
print(dir(scene))

'''
def get_wall_endpoints(obj):
    print('getting endpoints for {}'.format(obj.name))
    print(obj.dimensions)
    world_mtx = obj.matrix_world
    print(world_mtx)
    print(world_mtx.translation)
    obj_origin__world = obj.matrix_world.translation
    obj_dims = obj.dimensions
    return [
            {obj_origin__world.x, obj_origin__world.y, obj_origin__world.z},
            ]
'''

def export_wall(jsn, obj):
    print('export a wall')
    #print(obj.matrix_basis)
    #print(obj.matrix_local)
    #print(obj.matrix_world)
    dims_vec = mathutils.Vector((obj.dimensions.x, obj.dimensions.y, obj.dimensions.z))
    origin = obj.matrix_world.translation
    # Transform dimensions (the object-local bounding box)
    #   by the object's rotation.
    dimensions__world = (obj.matrix_basis.decompose()[1]) @ dims_vec
    jsn.append({
        'name': obj.name, # for hooking up tiles/textures later
        #'texture': obj.data.image?
        'origin': [
            round(origin.x, 6),
            round(origin.y, 6),
            round(origin.z, 6),
            ],
        'farPoint': [
            round(origin.x + dimensions__world.x, 6),
            round(origin.y + dimensions__world.y, 6),
            round(origin.z + dimensions__world.z, 6),
            ],
        })


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
            'walls': []
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
            camera_from_origin__world = camera.location.normalized()
            for edge in mesh.edges:
                edge_v0__local = mathutils.Vector(mesh.vertices[edge.vertices[0]].co)
                edge_v1__local = mathutils.Vector(mesh.vertices[edge.vertices[1]].co)

                edge_v0__world = object.matrix_world @ edge_v0__local
                edge_v1__world = object.matrix_world @ edge_v1__local
                print('edge v0 world:  {}'.format(edge_v0__world))
                print('edge v1 world:  {}'.format(edge_v1__world))

                edge_midpoint__world = (edge_v0__world + edge_v1__world) / 2

                # ignore edges not along the bbox's bottom plane
                if abs(bbox_center_bottom__world.z - edge_v0__world.z) > 0.01: continue
                if abs(bbox_center_bottom__world.z - edge_v1__world.z) > 0.01: continue

                midpoint_from_bbox__world = edge_midpoint__world - bbox_center_bottom__world
                is_front_facing = camera_from_origin__world.dot(midpoint_from_bbox__world) > 0
                print('midpoint world: {}'.format(edge_midpoint__world))
                print('is front? {}'.format(is_front_facing))

                jsn['walls'].append({
                    'blenderObjectName': object.name, # for hooking up tiles/textures later
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
            #return

    print(json.dumps(jsn, indent=2, sort_keys=True))
main()

