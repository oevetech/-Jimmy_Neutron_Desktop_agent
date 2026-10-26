import bpy
import bmesh
import math
import mathutils
import os

fbx_path = r"C:\Users\everaldolima\Downloads\b16fc22bbd045b94d5ab6fbec3cae750.fbx"
out_dir = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\vistas_novo_jimmy"
os.makedirs(out_dir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
me = mesh_obj.data

# Modifica os vértices do cabelo na parte de trás da cabeça
# Y é a altura (pescoço ~0.55, topo da cabeça ~1.10)
# Z é a profundidade (Z positivo é frente/nariz, Z negativo é nuca/trás)
# Atualmente Z chega a -0.348 atrás, quando o pescoço está em -0.095

count_mod = 0
for v in me.vertices:
    x, y, z = v.co.x, v.co.y, v.co.z
    
    # Região da cabeça e cabelo (Y entre 0.55 e 1.05) e parte traseira (Z < -0.10)
    if y > 0.52 and z < -0.10:
        # Fator de altura: suaviza a transição perto da nuca (y=0.52..0.62) e perto do topo (y=0.95..1.05)
        if y < 0.62:
            weight_y = (y - 0.52) / 0.10
        elif y > 0.95:
            weight_y = max(0.0, 1.0 - (y - 0.95) / 0.10)
        else:
            weight_y = 1.0
            
        # Profundidade excessiva além de -0.10
        dist_traseira = (-0.10) - z   # positivo para quem está muito pra trás
        
        # Reduz a protuberância excessiva em ~45%, recolhendo o volume para frente
        # Mantém a curvatura suave e esférica natural
        delta_z = dist_traseira * 0.44 * weight_y
        v.co.z += delta_z
        count_mod += 1

me.update()
print(f"Vértices ajustados no cabelo: {count_mod}")

# Salva blend ajustado
blend_ajustado = os.path.join(out_dir, "jimmy_cabelo_ajustado.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_ajustado)

# Configura render da vista lateral para comparar
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.view_settings.view_transform = "Standard"

sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), math.radians(-25), math.radians(45))

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
d = mesh_obj.dimensions
cam_data.ortho_scale = max(d) * 1.35
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

c = mesh_obj.matrix_world @ (sum((mathutils.Vector(b) for b in mesh_obj.bound_box), mathutils.Vector()) / 8)

# Vista lateral direita
cam.location = c + mathutils.Vector((3.0, 0, 0))
cam.rotation_euler = (math.radians(90), 0, math.radians(90))

out_png = os.path.join(out_dir, "lado_direito_ajustado.png")
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Prévia lateral ajustada salva em:", out_png)
