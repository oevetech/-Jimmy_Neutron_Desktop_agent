import bpy
import math
import mathutils
import os

fbx_path = r"C:\Users\everaldolima\Downloads\b16fc22bbd045b94d5ab6fbec3cae750.fbx"
out_dir = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\vistas_novo_jimmy"
os.makedirs(out_dir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = False
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.view_settings.view_transform = "Standard"

bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
print("Malha:", mesh_obj.name, "Vértices:", len(mesh_obj.data.vertices), "Polígonos:", len(mesh_obj.data.polygons))

# Configura iluminação
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), math.radians(-25), math.radians(45))

# Câmera Ortho
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
d = mesh_obj.dimensions
cam_data.ortho_scale = max(d) * 1.35
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

# Centro do objeto
c = mesh_obj.matrix_world @ (sum((mathutils.Vector(b) for b in mesh_obj.bound_box), mathutils.Vector()) / 8)

vistas = [
    ("frente", (0, -3.0, 0), (math.radians(90), 0, 0)),
    ("lado_direito", (3.0, 0, 0), (math.radians(90), 0, math.radians(90))),
    ("lado_esquerdo", (-3.0, 0, 0), (math.radians(90), 0, math.radians(-90))),
    ("costas", (0, 3.0, 0), (math.radians(90), 0, math.radians(180))),
    ("tres_quartos", (2.0, -2.5, 0.5), (math.radians(78), 0, math.radians(38))),
]

for nome, offset, rot in vistas:
    cam.location = c + mathutils.Vector(offset)
    cam.rotation_euler = rot
    out_file = os.path.join(out_dir, f"{nome}.png")
    sc.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print("Salvo:", out_file)

print("Todas as vistas renderizadas com sucesso!")
