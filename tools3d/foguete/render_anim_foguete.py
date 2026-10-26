import bpy
import bmesh
import math
import mathutils
import os

# Abre o arquivo .blend do foguete que criamos
blend_file = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.open_mainfile(filepath=blend_file)
sc = bpy.context.scene

# Configura render
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

out_raw_dir = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\raw_frames"
os.makedirs(out_raw_dir, exist_ok=True)

# Coleta todos os objetos do foguete para animar o hover sutil
mesh_objs = [o for o in sc.collection.objects if o.type == "MESH"]
sun_key = [o for o in sc.collection.objects if o.name == "SunKey"][0]
base_transforms = {o.name: (o.location.copy(), o.rotation_euler.copy()) for o in mesh_objs}

N_FRAMES = 16
for i in range(N_FRAMES):
    t = (2.0 * math.pi * i) / N_FRAMES
    # Flutuação vertical sutil (bobbing)
    dz = math.sin(t) * 0.035
    # Inclinação aerodinâmica sutilíssima de arfagem (pitch)
    pitch = math.sin(t) * math.radians(0.8)
    
    for obj in mesh_objs:
        base_loc, base_rot = base_transforms[obj.name]
        obj.location = mathutils.Vector((base_loc.x, base_loc.y, base_loc.z + dz))
        obj.rotation_euler = mathutils.Euler((base_rot.x, base_rot.y + pitch, base_rot.z))
        
    # Brilho dinâmico na agulha e vidro (o sol gira suavemente)
    sun_rot_x = math.radians(50) + math.sin(t) * math.radians(4.0)
    sun_key.rotation_euler.x = sun_rot_x
    
    # Atualiza cena e renderiza
    sc.frame_set(i)
    raw_path = os.path.join(out_raw_dir, f"raw_{i:02d}.png")
    sc.render.filepath = raw_path
    bpy.ops.render.render(write_still=True)
    print(f"Quadro {i:02d}/{N_FRAMES} renderizado.")

print("Renderização de todos os quadros concluída com sucesso!")
