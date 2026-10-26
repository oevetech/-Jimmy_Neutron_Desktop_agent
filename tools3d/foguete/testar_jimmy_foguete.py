import bpy
import bmesh
import math
import mathutils
import os

# 1. Abre a cena com o foguete 3D
blend_rocket = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_rocket)
sc = bpy.context.scene

# 2. Importa o Jimmy (pose sentado/montado)
fbx_jimmy = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx\13_doze_sit.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_jimmy)

# Localiza armature e mesh do Jimmy importados
arm_jimmy = [o for o in bpy.data.objects if o.type == "ARMATURE" and o.name.startswith("Armature")][0]
me_jimmy = [o for o in arm_jimmy.children if o.type == "MESH"][0]

# 3. Aplica textura do Jimmy e material cartoon
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

# Contorno preto (inverted hull) no Jimmy
mat_outline = [m for m in bpy.data.materials if m.name == "Mat_Outline"][0]
me_jimmy.data.materials.append(mat_outline)
so_j = me_jimmy.modifiers.new("Outline", "SOLIDIFY")
so_j.thickness = 0.014
so_j.offset = 1.0
so_j.use_flip_normals = True
so_j.material_offset = len(me_jimmy.data.materials) - 1
so_j.use_rim = False

# 4. Posiciona e escala o Jimmy sentado na parte superior da fuselagem do foguete
# No nosso foguete:
# - Eixo X é o comprimento (traseira em 0, cabine em 1.95, nariz em 3.7)
# - Eixo Z é a altura (topo da fuselagem fica em Z ~ 0.50)
# Jimmy original tem ~1.8m de altura no FBX (escala Mixamo)
arm_jimmy.scale = (0.009, 0.009, 0.009)
# Rotaciona para olhar para a frente (+X)
arm_jimmy.rotation_euler = (0, 0, math.radians(-90))
# Coloca sentado logo atrás da cabine / sobre a fuselagem
arm_jimmy.location = (1.45, 0.0, 0.48)

# 5. Ajusta a câmera Ortho para enquadrar o conjunto Jimmy + Foguete
cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
cam.data.ortho_scale = 5.2
cam.location = (1.7, -6.5, 1.45)
cam.rotation_euler = (math.radians(78), 0, math.radians(-3))

# Salva arquivo combinado
out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\jimmy_no_foguete.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

# Renderiza prévia de teste
out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\previa_jimmy_foguete.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Prévia do Jimmy no Foguete renderizada com sucesso em:", out_png)
