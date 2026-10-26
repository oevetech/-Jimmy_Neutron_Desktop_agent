import bpy
import bmesh
import math
import mathutils
import os

# 1. Abre o modelo do Foguete Strato XL
blend_rocket = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_rocket)
sc = bpy.context.scene

sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

# 2. Importa o Jimmy pendurado (Mixamo FBX)
fbx_pendura = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx\jimmy_flight_pendura.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_pendura)

# Armature e Mesh do Jimmy
arm_jimmy = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("Armature")][0]
me_jimmy = [o for o in arm_jimmy.children if o.type == "MESH"][0]

# Material Toon do Jimmy
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

# Contorno Toon no Jimmy
mat_outline = [m for m in bpy.data.materials if m.name == "Mat_Outline"][0]
me_jimmy.data.materials.append(mat_outline)
so_j = me_jimmy.modifiers.new("Outline", "SOLIDIFY")
so_j.thickness = 0.015
so_j.offset = 1.0
so_j.use_flip_normals = True
so_j.material_offset = len(me_jimmy.data.materials) - 1
so_j.use_rim = False

# 3. Escala e Posição do Jimmy pendurado
# O FBX do Mixamo vem com escala 0.01 por padrão do Blender. Multiplicando por 100 * 1.1 = 110
arm_jimmy.scale = (1.1, 1.1, 1.1)

# Posição do Jimmy pendurado na lateral da fuselagem / aleta
# As mãos do Jimmy ficam no topo do modelo dele (Z alto), corpo para baixo
# Vamos posicionar as mãos agarradas na aleta inferior ou na borda da fuselagem
arm_jimmy.rotation_euler = (math.radians(-10), math.radians(-15), math.radians(-80))
arm_jimmy.location = (0.7, -0.25, -0.65)

bpy.context.view_layer.update()

# 4. Inclina conjunto Foguete + Jimmy para atitude de subida (30°)
root = bpy.data.objects.new("RootFlight", None)
sc.collection.objects.link(root)
root.location = (1.8, 0, 0)

rocket_objs = [o for o in sc.collection.objects if o.type == "MESH" and o != me_jimmy]
for o in rocket_objs:
    o.parent = root

arm_jimmy.parent = root

# Inclina o foguete para subir apontando para a direita/cima (empina ~28°)
root.rotation_euler = (0, math.radians(-28), 0)

# Câmera ortográfica
cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
cam.data.ortho_scale = 6.2
cam.location = (1.8, -7.0, 1.1)
cam.rotation_euler = (math.radians(78), 0, math.radians(-2))

out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\cena_voo_pendura.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\teste_voo_pendura.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Render teste voo_pendura concluído com sucesso:", out_png)
