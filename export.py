import bpy
import json
import mathutils
import math

context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ EXPORT.PY ~*~')

print(dir(context))
print(dir(scene))

def get_wall_endpoints(obj):
    print('getting endpoints for {}'.format(obj.name))
    #print(obj.matrix_world)
    #print(obj.vertex_groups)
    print(obj.dimensions)
    world_mtx = obj.matrix_world
    print(world_mtx)
    print(world_mtx.translation)
    obj_origin__world = obj.matrix_world.translation
    obj_dims = obj.dimensions
    return [
            {obj_origin__world.x, obj_origin__world.y, obj_origin__world.z},
            ]

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


def main():
    jsn = {
            'walls': []}

    objects = scene.collection.all_objects
    print('Number of objects: {}'.format(len(objects)))
    for object in objects:
        #print('Object [{}]'.format(object.name))
        #print(dir(object))
        #print(object.bound_box)
        if object.name.startswith('wall'):
            export_wall(jsn['walls'], object)

    print(json.dumps(jsn, indent=2, sort_keys=True))
main()

