import bpy
import json
import mathutils
import math
import os
import sys

CAMERA_NAME = 'iso-camera'

context = bpy.context
scene = context.scene

print('')
print('')
print('')
print('~*~ RENDER.PY ~*~')


def do_render(camera, obj, outpath):
    bpy.context.scene.render.filepath = os.path.join(outpath, '{}.png'.format(obj.name))
    bpy.ops.render.render(write_still = True)


def main():
    camera = scene.collection.all_objects.get(CAMERA_NAME)
    assert camera is not None
    objects = bpy.data.objects

    # Store original settings so we can restore them later.
    original_render_states = {}
    original_transparent = scene.render.film_transparent
    scene.render.film_transparent = True

    # Hide everything, first storing off initial rendering state.
    for object in objects:
        original_render_states[object.name] = object.hide_render
        object.hide_render = \
            object.name.startswith('wall')

    # Camera test stuff
    print(camera.data)
    print(camera.data.view_frame())
    return

    # Render wall sprites.
    count = 0
    for object in objects:
        count += 1
        if not object.name.startswith('wall'): continue
        print('Rendering sprite for {}'.format(object.name))
        object.hide_render = False
        do_render(camera, object, 'C:/Users/akait/Pictures/blender')
        object.hide_render = True
    print('Enumerated {} of {} objects'.format(count, len(objects)))

    # restore original render states
    scene.render.film_transparent = original_transparent 
    for object in objects:
        object.hide_render = original_render_states[object.name]

main()
print('Done rendering.')

