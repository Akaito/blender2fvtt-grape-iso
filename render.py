import bpy
import json
from mathutils import *
#from math import *
import os
import sys

CAMERA_NAME = 'iso-camera'
OUTPUT_FOLDER = r'C:\Users\akait\AppData\Local\FoundryVTT\Data\worlds\5e-srd\assets\grape test\iso-walls'
PPI = 100

context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ RENDER.PY ~*~')


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

camera = bpy.data.objects[CAMERA_NAME]  # or bpy.context.active_object
render = bpy.context.scene.render

P = Vector((-0.002170146, 0.409979939, 0.162410125))

print("Projecting point {} for camera '{:s}' into resolution {:d}x{:d}..."
      .format(P, camera.name, render.resolution_x, render.resolution_y))

proj_p = project_3d_point(camera=camera, p=P, render=render)
print("Projected point (homogeneous coords): {}.".format(proj_p))

proj_p_pixels = Vector(((render.resolution_x-1) * (proj_p.x + 1) / 2, (render.resolution_y - 1) * (proj_p.y - 1) / (-2)))
print("Projected point (pixel coords): {}.".format(proj_p_pixels))
## end Blender Stack Exchange code for world->pixel projection.
#####


def calc_largest_ortho_scale(camera):
    largest_ortho = 0
    for object in bpy.data.objects:
        object.select_set(True)
        print(bpy.ops.view3d.camera_to_view_selected())
        object.select_set(False)
        # TODO : Why is our main camera named 'Camera' in this collection?
        if bpy.data.cameras['Camera'].ortho_scale > largest_ortho:
            largest_ortho = bpy.data.cameras['Camera'].ortho_scale
    return largest_ortho


def do_render(camera, largest_ortho, obj, outpath):
    # select object and move camera to it
    #context.view_layer.objects.active = bpy.data.objects[obj.name]
    obj.select_set(True)
    print(bpy.ops.view3d.camera_to_view_selected())
    obj.select_set(False)
    bpy.data.cameras['Camera'].ortho_scale = largest_ortho

    # set output resolution
    origin__camera = \
            project_3d_point(camera, Vector((0,0,0)))
    originPlusOne__camera = \
            project_3d_point(camera, Vector((1,0,0)))
    cameraUnitsPerLateralWorldUnit = (originPlusOne__camera - origin__camera).length
    print('cameraUnitsPerLateralWorldUnit', cameraUnitsPerLateralWorldUnit)

    # TODO : Why is our main camera named 'Camera' in this collection?
    scene.render.resolution_x = PPI * bpy.data.cameras['Camera'].ortho_scale
    scene.render.resolution_y = PPI * bpy.data.cameras['Camera'].ortho_scale

    # render to file
    context.scene.render.filepath = os.path.join(outpath, '{}.png'.format(obj.name))
    bpy.ops.render.render(write_still = True)


def main():
    camera = scene.collection.all_objects.get(CAMERA_NAME)
    assert camera is not None
    objects = bpy.data.objects

    # Store original settings so we can restore them later.
    original_render_states = {}
    original_transparent = scene.render.film_transparent
    scene.render.film_transparent = True
    #depsgraph = context.evaluated_depsgraph_get()

    # Render-hide and deslect everything, first storing off initial rendering state.
    for object in objects:
        original_render_states[object.name] = object.hide_render
        #object.hide_render = object.name.startswith('wall')
        object.hide_render = object.type == 'MESH'
        object.select_set(False)

    largest_ortho = calc_largest_ortho_scale(camera)

    # Camera test stuff
    #print(camera.data)
    #print(camera.data.view_frame())
    #print(camera.location)
    #print(camera.camera_fit_coords(objects['wall.weird'].id, objects['wall.weird'].location))
    #print(camera.camera_fit_coords(depsgraph, [1]))
    #return

    # Render wall sprites.
    count = 0
    for object in objects:
        count += 1
        # skip non-wall objects
        if not object.name.startswith('wall'): continue

        print('Rendering sprite for {}'.format(object.name))
        object.hide_render = False
        do_render(camera, largest_ortho, object, OUTPUT_FOLDER)
        object.hide_render = True
    print('Enumerated {} of {} objects'.format(count, len(objects)))

    # restore original render states
    scene.render.film_transparent = original_transparent 
    for object in objects:
        object.hide_render = original_render_states[object.name]

main()
print('Done rendering.')

