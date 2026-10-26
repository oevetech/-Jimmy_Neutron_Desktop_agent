import bpy, sys, os, math, mathutils
src, out_dir = sys.argv[sys.argv.index("--")+1:]
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = 40000 / len(ob.data.polygons)
bpy.ops.object.modifier_apply(modifier="dec")
# Pés no chão, centralizado em X/Y
bb = [mathutils.Vector(b) for b in ob.bound_box]
minz = min(v.z for v in bb); cx = sum(v.x for v in bb)/8; cy = sum(v.y for v in bb)/8
ob.data.transform(mathutils.Matrix.Translation((-cx, -cy, -minz)))
# Cabelo de trás: puxa para frente o que passa da nuca (frente do modelo = -Y)
K = float(os.environ.get("K_CABELO", "0.5")); Y0 = 0.03; Z0, Z1 = 0.50, 0.60
for v in ob.data.vertices:
    x, y, z = v.co
    if y > Y0 and z > Z0:
        t = min(1.0, (z - Z0) / (Z1 - Z0)); t = t * t * (3 - 2 * t)
        v.co.y = Y0 + (y - Y0) * (1 - t * (1 - K))
d = ob.dimensions
print("DIMS", tuple(round(x,3) for x in d), "faces", len(ob.data.polygons))
# Só a cor base em 2048
mat = ob.data.materials[0]; base = None
for n in mat.node_tree.nodes:
    if n.type == "BSDF_PRINCIPLED":
        l = n.inputs["Base Color"].links
        if l and l[0].from_node.type == "TEX_IMAGE": base = l[0].from_node.image
print("BASE", base and base.name)
base.scale(2048, 2048)
base.filepath_raw = os.path.join(out_dir, "jimmy_cor.png"); base.file_format = "PNG"; base.save()
for n in list(mat.node_tree.nodes):
    if n.type == "TEX_IMAGE" and n.image is not base: mat.node_tree.nodes.remove(n)
bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, "jimmy.obj"), export_materials=True,
                      path_mode="RELATIVE", export_normals=True, export_uv=True,
                      export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y")
# Prévias para conferir a orientação (frente deve olhar para -Y)
sc = bpy.context.scene
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = max(d) * 1.3; sc.camera = cam
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(30))
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = sc.render.resolution_y = 400
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.8, 0.8, 0.8)
c = mathutils.Vector((0, 0, d.z/2))
for nome, v in (("frente_menosY", (0, -1, 0)), ("lado_X", (1, 0, 0)), ("tres_quartos", (0.7, -0.7, 0.15))):
    v = mathutils.Vector(v); cam.location = c + v * 5
    cam.rotation_euler = (-v).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out_dir, f"previa_{nome}.png")
    bpy.ops.render.render(write_still=True)
