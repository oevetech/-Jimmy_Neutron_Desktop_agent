import bpy
import bmesh
import math
import mathutils
import os

PROJECT_ROOT = r"C:\Users\everaldolima\jimmy-neutron-pet"
BLEND_ROCKET = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "foguete_strato_xl.blend")
FBX_DIR = os.path.join(PROJECT_ROOT, "tools3d", "fbx")
RAW_BASE_DIR = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "raw_voo")
TEX_PATH = os.path.join(PROJECT_ROOT, "tools3d", "jimmy_cor.png")

ANIM_CONFIGS = [
    {
        "name": "voo_pendura",
        "fbx": "jimmy_flight_pendura.fbx",
        "loc": (0.7, -0.25, -0.65),
        "rot": (math.radians(-10), math.radians(-15), math.radians(-80)),
        "scale": (1.1, 1.1, 1.1),
        "frames": [5, 25]  # 2 quadros para pendurado
    },
    {
        "name": "voo_escala",
        "fbx": "jimmy_flight_climb.fbx",
        "loc": (0.95, -0.22, -0.25),
        "rot": (math.radians(-5), math.radians(-20), math.radians(-85)),
        "scale": (1.1, 1.1, 1.1),
        "frames": [5, 15]  # 2 quadros para escala
    },
    {
        "name": "voo_senta",
        "fbx": "jimmy_flight_senta.fbx",
        "loc": (1.35, -0.05, 0.42),
        "rot": (math.radians(5), math.radians(-15), math.radians(-85)),
        "scale": (1.1, 1.1, 1.1),
        "frames": [5, 25]  # 2 quadros para senta
    },
    {
        "name": "voo_monta",
        "fbx": "jimmy_flight_pilot.fbx",
        "loc": (1.45, 0.0, 0.38),
        "rot": (math.radians(0), math.radians(-10), math.radians(-90)),
        "scale": (1.1, 1.1, 1.1),
        "frames": [5, 20, 35, 50, 65]  # 5 quadros para voo_monta (0..4)
    }
]

def render_anim(cfg):
    anim_name = cfg["name"]
    out_dir = os.path.join(RAW_BASE_DIR, anim_name)
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"\n==========================================")
    print(f"Configurando cena para '{anim_name}'...")
    print(f"==========================================")
    
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND_ROCKET)
    sc = bpy.context.scene

    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.resolution_x = 800
    sc.render.resolution_y = 800
    sc.view_settings.view_transform = "Standard"

    # Importa Jimmy FBX
    fbx_path = os.path.join(FBX_DIR, cfg["fbx"])
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

    # Jimmy escala e pose relativa
    arm_jimmy.scale = cfg["scale"]
    arm_jimmy.rotation_euler = cfg["rot"]
    arm_jimmy.location = cfg["loc"]

    bpy.context.view_layer.update()

    # Raiz de voo inclinada 28 graus
    root = bpy.data.objects.new("RootFlight", None)
    sc.collection.objects.link(root)
    root.location = (1.8, 0, 0)

    rocket_objs = [o for o in sc.collection.objects if o.type == "MESH" and o != me_jimmy]
    for o in rocket_objs:
        o.parent = root
    arm_jimmy.parent = root

    root.rotation_euler = (0, math.radians(-28), 0)

    # Câmera ortográfica padronizada
    cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
    cam.location = (2.9, -7.5, 0.85)
    cam.rotation_euler = (math.radians(78), 0, math.radians(-2))
    cam.data.ortho_scale = 6.2

    # Renderiza cada quadro
    for idx, f_num in enumerate(cfg["frames"]):
        sc.frame_set(f_num)
        out_png = os.path.join(out_dir, f"raw_{idx:02d}.png")
        sc.render.filepath = out_png
        bpy.ops.render.render(write_still=True)
        print(f"[{anim_name}] Quadro {idx:02d} (frame {f_num}) salvo em: {out_png}")

for cfg in ANIM_CONFIGS:
    render_anim(cfg)

print("\nRenderização de todas as 4 animações do voo concluída com sucesso!")
