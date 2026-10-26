import bpy
import bmesh
import math
import mathutils
import os

# Limpa e abre o modelo do foguete
blend_rocket = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_rocket)
sc = bpy.context.scene

sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

# Importa o Jimmy (pose sentado)
fbx_jimmy = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx\13_doze_sit.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_jimmy)

arm_jimmy = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("Armature")][0]
me_jimmy = [o for o in arm_jimmy.children if o.type == "MESH"][0]

# Aplica textura do Jimmy
tex_path = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\jimmy_cor.png"
img = bpy.data.images.load(tex_path)

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

# Contorno Toon
mat_outline = [m for m in bpy.data.materials if m.name == "Mat_Outline"][0]
me_jimmy.data.materials.append(mat_outline)
so_j = me_jimmy.modifiers.new("Outline", "SOLIDIFY")
so_j.thickness = 0.015
so_j.offset = 1.0
so_j.use_flip_normals = True
so_j.material_offset = len(me_jimmy.data.materials) - 1
so_j.use_rim = False

# Escala do Jimmy
arm_jimmy.scale = (1.1, 1.1, 1.1)

# Rotação para olhar para a frente (+X) montado na fuselagem
arm_jimmy.rotation_euler = (0, math.radians(-15), math.radians(-90))

# Posição sentado sobre a fuselagem
arm_jimmy.location = (1.30, 0.0, 0.52)

bpy.context.view_layer.update()

# Câmera Ortho inclinada para cima (+28° para empinar a subida para a direita)
cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
cam.data.ortho_scale = 6.0
cam.location = (1.8, -7.0, 1.3)
cam.rotation_euler = (math.radians(78), math.radians(28), math.radians(-3))

# Salva arquivo blend
out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\voo_monta_posicionado.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

# Renderiza teste
out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\teste_voo_monta_camera2.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Render teste 2 concluído com sucesso:", out_png)
