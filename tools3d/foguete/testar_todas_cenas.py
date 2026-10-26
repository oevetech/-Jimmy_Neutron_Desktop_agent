import bpy
import bmesh
import math
import mathutils
import os

PROJECT_ROOT = r"C:\Users\everaldolima\jimmy-neutron-pet"
BLEND_ROCKET = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "foguete_strato_xl.blend")
FBX_DIR = os.path.join(PROJECT_ROOT, "tools3d", "fbx")
OUT_DIR = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "previa")
os.makedirs(OUT_DIR, exist_ok=True)
TEX_PATH = os.path.join(PROJECT_ROOT, "tools3d", "jimmy_cor.png")

def setup_scene(fbx_name, jimmy_loc, jimmy_rot, jimmy_scale, frame_num, out_name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND_ROCKET)
    sc = bpy.context.scene

    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.resolution_x = 800
    sc.render.resolution_y = 800
    sc.view_settings.view_transform = "Standard"

    # Importa Jimmy FBX
    fbx_path = os.path.join(FBX_DIR, fbx_name)
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    arm_jimmy = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("Armature")][0]
    me_jimmy = [o for o in arm_jimmy.children if o.type == "MESH"][0]

    # Material Toon do Jimmy
    img = bpy.data.images.load(TEX_PATH)
    mat_jimmy = me_jimmy.data.materials[0]
    nt = mat_jimmy.node_tree
    bsdf = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.65
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
    bsdf.inputs["Metallic"].default_value = 0.0

    # Contorno Toon no Jimmy
    mat_outline = [m for m in bpy.data.materials if m.name == "Mat_Outline"][0]
    me_jimmy.data.materials.append(mat_outline)
    so_j = me_jimmy.modifiers.new("Outline", "SOLIDIFY")
    so_j.thickness = 0.015
    so_j.offset = 1.0
    so_j.use_flip_normals = True
    so_j.material_offset = len(me_jimmy.data.materials) - 1
    so_j.use_rim = False

    # Define frame da animação
    sc.frame_set(frame_num)

    # Jimmy escala e pose relativa
    arm_jimmy.scale = jimmy_scale
    arm_jimmy.rotation_euler = jimmy_rot
    arm_jimmy.location = jimmy_loc

    bpy.context.view_layer.update()

    # Raiz de voo (Root) inclinada 28 graus
    root = bpy.data.objects.new("RootFlight", None)
    sc.collection.objects.link(root)
    root.location = (1.8, 0, 0)

    rocket_objs = [o for o in sc.collection.objects if o.type == "MESH" and o != me_jimmy]
    for o in rocket_objs:
        o.parent = root
    arm_jimmy.parent = root

    root.rotation_euler = (0, math.radians(-28), 0)

    # Câmera ortográfica perfeitamente enquadrada
    cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
    cam.location = (2.9, -7.5, 0.85)
    cam.rotation_euler = (math.radians(78), 0, math.radians(-2))
    cam.data.ortho_scale = 6.2

    out_png = os.path.join(OUT_DIR, out_name)
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print(f"Renderizado com sucesso: {out_png}")

# Configurações de cada fase
setup_scene(
    fbx_name="jimmy_flight_pendura.fbx",
    jimmy_loc=(0.7, -0.25, -0.65),
    jimmy_rot=(math.radians(-10), math.radians(-15), math.radians(-80)),
    jimmy_scale=(1.1, 1.1, 1.1),
    frame_num=1,
    out_name="previa_pendura.png"
)

setup_scene(
    fbx_name="jimmy_flight_climb.fbx",
    jimmy_loc=(0.95, -0.22, -0.25),
    jimmy_rot=(math.radians(-5), math.radians(-20), math.radians(-85)),
    jimmy_scale=(1.1, 1.1, 1.1),
    frame_num=5,
    out_name="previa_escala.png"
)

setup_scene(
    fbx_name="jimmy_flight_senta.fbx",
    jimmy_loc=(1.35, -0.05, 0.42),
    jimmy_rot=(math.radians(5), math.radians(-15), math.radians(-85)),
    jimmy_scale=(1.1, 1.1, 1.1),
    frame_num=1,
    out_name="previa_senta.png"
)

setup_scene(
    fbx_name="jimmy_flight_pilot.fbx",
    jimmy_loc=(1.45, 0.0, 0.38),
    jimmy_rot=(math.radians(0), math.radians(-10), math.radians(-90)),
    jimmy_scale=(1.1, 1.1, 1.1),
    frame_num=10,
    out_name="previa_monta.png"
)
