import bpy
import bmesh
import math
import mathutils
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Abre o modelo do Foguete
blend_rocket = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_rocket)
sc = bpy.context.scene

# Configurações do Render EEVEE
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

# 2. Importa o Jimmy (FBX com armature e pose sentada)
fbx_jimmy = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx\13_doze_sit.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_jimmy)

arm_jimmy = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("Armature")][0]
me_jimmy = [o for o in arm_jimmy.children if o.type == "MESH"][0]

# 3. Textura e Material Cartoon do Jimmy
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

# 4. Ajusta escala e posição do Jimmy sobre o foguete
# Jimmy FBX nativo tem ~0.95 de altura (me_jimmy.dimensions.y no espaço local)
# Escala 1.15 dá o tamanho perfeito relativo ao foguete
arm_jimmy.scale = (1.15, 1.15, 1.15)
# Rotação para olhar para frente (+X) e ligeiramente inclinado para a ação
arm_jimmy.rotation_euler = (math.radians(12), math.radians(-15), math.radians(-80))
# Posição sobre a fuselagem logo atrás da cabine
arm_jimmy.location = (1.35, -0.05, 0.42)

# 5. Inclina o conjunto Foguete + Jimmy em 30° para cima (atitude de voo ascendente)
# Cria um Empty como raiz para rotacionar tudo junto
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(1.5, 0, 0))
root_flight = bpy.context.active_object
root_flight.name = "RootFlight"

# Agrupa todos os objetos do foguete e o Jimmy sob o Empty
rocket_objs = [o for o in sc.collection.objects if o.type == "MESH" and o != me_jimmy]
for obj in rocket_objs:
    obj.parent = root_flight

arm_jimmy.parent = root_flight

# Aplica a rotação de decolagem de 30° (empina o nariz para cima)
# No espaço local, inclina o eixo Y negativo (nariz sobe em Z)
root_flight.rotation_euler = (0, math.radians(-30), 0)

# 6. Câmera Ortho enquadrando a decolagem dinâmica
cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
cam.data.ortho_scale = 5.6
cam.location = (1.6, -6.5, 1.5)
cam.rotation_euler = (math.radians(78), 0, math.radians(-3))

# Salva arquivo blend para ajustes
out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\cena_voo_monta.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

# Renderiza teste
out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\teste_voo_monta_800.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Render voo_monta concluído com sucesso:", out_png)
