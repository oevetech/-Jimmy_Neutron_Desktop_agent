import bpy, sys, math, mathutils
args = sys.argv[sys.argv.index("--")+1:]
src, out_dir = args
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in bpy.data.objects if o.type == "MESH"][0]
print("ROT", tuple(round(math.degrees(r)) for r in ob.rotation_euler), "SCALE", tuple(ob.scale))
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# Malha mais leve para o Mixamo (~40 mil triângulos)
m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = 40000 / len(ob.data.polygons)
bpy.ops.object.modifier_apply(modifier="dec")
d = ob.dimensions
print("DIMS depois", tuple(round(x,3) for x in d), "faces", len(ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out_dir + "/jimmy_leve.blend")
# Prévias: frente, lado e cima, para descobrir a orientação
cam_data = bpy.data.cameras.new("c"); cam_data.type = "ORTHO"; cam_data.ortho_scale = max(d) * 1.3
cam = bpy.data.objects.new("c", cam_data); bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN")); bpy.context.scene.collection.objects.link(sun)
sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(30))
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = sc.render.resolution_y = 400
sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.8, 0.8, 0.8)
c = ob.matrix_world @ (sum((mathutils.Vector(b) for b in ob.bound_box), mathutils.Vector()) / 8)
for nome, direcao in (("frente_y", (0, -1, 0)), ("lado_x", (1, 0, 0)), ("cima_z", (0, 0, 1))):
    v = mathutils.Vector(direcao)
    cam.location = c + v * 5
    cam.rotation_euler = (-v).to_track_quat("-Z", "Y" if nome != "cima_z" else "Y").to_euler()
    sc.render.filepath = f"{out_dir}/previa_{nome}.png"
    bpy.ops.render.render(write_still=True)
