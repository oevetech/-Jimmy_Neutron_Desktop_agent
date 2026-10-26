import bpy
import bmesh
import math
import mathutils
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

blend_rocket = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_rocket)
sc = bpy.context.scene

sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

# Importa o Jimmy
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

# Contorno Toon no Jimmy
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

# Rotação para olhar para a frente (+X) com leve inclinação de pilotagem
arm_jimmy.rotation_euler = (0, math.radians(-20), math.radians(-90))

# Posição: Jimmy sentado logo atrás da cúpula do cockpit (X=1.65, Z=0.52)
arm_jimmy.location = (1.65, 0.0, 0.52)

bpy.context.view_layer.update()

# Câmera Ortho inclinada para cima (+25° para subida)
cam = [o for o in sc.collection.objects if o.type == "CAMERA"][0]
cam.data.ortho_scale = 6.2
cam.location = (2.0, -7.0, 1.4)
cam.rotation_euler = (math.radians(78), math.radians(25), math.radians(-3))

# Renderiza teste
out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\teste_pos_cockpit.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Render teste pos cockpit concluído:", out_png)
