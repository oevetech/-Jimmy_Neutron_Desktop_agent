import bpy
import bmesh
import math
import mathutils
import os
import sys

# Limpa cena inicial
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# Configura render EEVEE e transparência
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 400
sc.render.resolution_y = 400
sc.view_settings.view_transform = "Standard"

# --- Materiais Cartoon ---
def criar_mat(nome, cor, metallic=0.0, roughness=0.4, alpha=1.0):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else "HASHED"
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.8
    return mat

mat_vermelho = criar_mat("Foguete_Vermelho", (0.86, 0.08, 0.11, 1.0), metallic=0.05, roughness=0.38)
mat_amarelo = criar_mat("Foguete_Amarelo", (1.0, 0.76, 0.02, 1.0), metallic=0.02, roughness=0.35)
mat_metal = criar_mat("Foguete_Metal", (0.80, 0.83, 0.88, 1.0), metallic=0.85, roughness=0.22)
mat_vidro = criar_mat("Foguete_Vidro", (0.35, 0.78, 0.95, 0.55), metallic=0.1, roughness=0.1, alpha=0.55)
mat_escuro = criar_mat("Foguete_Escuro", (0.12, 0.13, 0.16, 1.0), metallic=0.3, roughness=0.6)

# Material de contorno cartoon preto
mat_contorno = bpy.data.materials.new("Contorno_Preto")
mat_contorno.use_nodes = True
mat_contorno.use_backface_culling = True
p_cont = mat_contorno.node_tree.nodes["Principled BSDF"]
p_cont.inputs["Base Color"].default_value = (0.02, 0.02, 0.03, 1.0)
p_cont.inputs["Roughness"].default_value = 1.0

def add_outline(obj, thickness=0.022):
    obj.data.materials.append(mat_contorno)
    so = obj.modifiers.new("Contorno", "SOLIDIFY")
    so.thickness = thickness
    so.offset = 1.0
    so.use_flip_normals = True
    so.material_offset = len(obj.data.materials) - 1
    so.use_rim = False

# 1. Fuselagem (Corpo do Foguete)
bm = bmesh.new()
lathe_profile = [
    (0.40, 0.15),   # Base bocal
    (0.52, 0.45),
    (0.66, 0.95),
    (0.70, 1.45),   # Barriga
    (0.68, 1.95),
    (0.56, 2.50),
    (0.38, 2.95),
    (0.16, 3.35),
    (0.01, 3.50),   # Ponta do nariz
]

segments = 32
layers = []
for r, z in lathe_profile:
    ring = []
    for i in range(segments):
        th = (2.0 * math.pi * i) / segments
        x = r * math.cos(th)
        y = r * math.sin(th)
        ring.append(bm.verts.new((x, y, z)))
    layers.append(ring)

# Conecta anéis
for l in range(len(layers) - 1):
    r1, r2 = layers[l], layers[l+1]
    for i in range(segments):
        i_next = (i + 1) % segments
        bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))

# Fecha tampa inferior
bottom_center = bm.verts.new((0, 0, lathe_profile[0][1]))
for i in range(segments):
    i_next = (i + 1) % segments
    bm.faces.new((bottom_center, layers[0][i_next], layers[0][i]))

# Fecha tampa superior
top_center = bm.verts.new((0, 0, lathe_profile[-1][1]))
for i in range(segments):
    i_next = (i + 1) % segments
    bm.faces.new((top_center, layers[-1][i], layers[-1][i_next]))

bm.normal_update()
me_body = bpy.data.meshes.new("FuselagemMesh")
bm.to_mesh(me_body)
bm.free()

obj_body = bpy.data.objects.new("Fuselagem", me_body)
sc.collection.objects.link(obj_body)
obj_body.data.materials.append(mat_vermelho)
add_outline(obj_body, thickness=0.024)

# Subsurf para suavidade perfeita
sub = obj_body.modifiers.new("Subsurf", "SUBSURF")
sub.levels = 1
sub.render_levels = 2

# 2. Agulha / Antena da Ponta (Cromada)
bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.45, location=(0, 0, 3.65))
obj_needle = bpy.context.active_object
obj_needle.name = "Agulha"
obj_needle.data.materials.append(mat_metal)
add_outline(obj_needle, thickness=0.015)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0, 0, 3.90))
obj_needle_tip = bpy.context.active_object
obj_needle_tip.name = "PontaAgulha"
obj_needle_tip.data.materials.append(mat_metal)
add_outline(obj_needle_tip, thickness=0.015)

# 3. Bocal da Turbina Inferior (Metal Escuro)
bpy.ops.mesh.primitive_cone_add(radius1=0.46, radius2=0.36, depth=0.32, location=(0, 0, 0.05))
obj_nozzle = bpy.context.active_object
obj_nozzle.name = "Bocal"
obj_nozzle.data.materials.append(mat_metal)
add_outline(obj_nozzle, thickness=0.02)

# 4. Cúpula da Cabine (Vidro Bolha Oval)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0, 0.52, 2.15))
obj_cockpit = bpy.context.active_object
obj_cockpit.name = "CabineVidro"
obj_cockpit.scale = (0.75, 0.65, 1.25)
obj_cockpit.rotation_euler = (math.radians(-14), 0, 0)
bpy.ops.object.transform_apply(scale=True, rotation=True)
obj_cockpit.data.materials.append(mat_vidro)
add_outline(obj_cockpit, thickness=0.016)

# Aro / Moldura da Cabine
bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.038, location=(0, 0.44, 2.12))
obj_rim = bpy.context.active_object
obj_rim.name = "AroCabine"
obj_rim.scale = (0.78, 0.8, 1.3)
obj_rim.rotation_euler = (math.radians(-14), 0, 0)
bpy.ops.object.transform_apply(scale=True, rotation=True)
obj_rim.data.materials.append(mat_metal)
add_outline(obj_rim, thickness=0.014)

# 5. As 3 Aletas Amarelas Estilizadas
def criar_aleta(angulo_graus, nome):
    bm_fin = bmesh.new()
    # Perfil 2D da aleta do Jimmy (curva retrô swept-wing)
    pts = [
        (0.66, 1.40),    # Topo fixado no corpo
        (1.05, 0.85),    # Curva externa
        (1.30, 0.20),    # Borda externa máxima
        (1.22, -0.15),   # Ponta inferior da aleta
        (0.68, -0.05),   # Retorno para a base
        (0.48, 0.25)     # Base inferior fixada no corpo
    ]
    t = 0.045 # semi-espessura
    
    verts_front = [bm_fin.verts.new((p[0], -t, p[1])) for p in pts]
    verts_back  = [bm_fin.verts.new((p[0],  t, p[1])) for p in pts]
    
    # Face frontal e traseira
    bm_fin.faces.new(verts_front)
    bm_fin.faces.new(list(reversed(verts_back)))
    
    # Lados / bordas
    n = len(pts)
    for i in range(n):
        i_next = (i + 1) % n
        bm_fin.faces.new((verts_front[i], verts_front[i_next], verts_back[i_next], verts_back[i]))
    
    bm_fin.normal_update()
    me_fin = bpy.data.meshes.new(nome + "Mesh")
    bm_fin.to_mesh(me_fin)
    bm_fin.free()
    
    obj_fin = bpy.data.objects.new(nome, me_fin)
    sc.collection.objects.link(obj_fin)
    obj_fin.data.materials.append(mat_amarelo)
    add_outline(obj_fin, thickness=0.02)
    
    # Rotação ao redor do eixo Z do foguete
    obj_fin.rotation_euler = (0, 0, math.radians(angulo_graus))
    return obj_fin

# Cria as 3 aletas em 0°, 120°, 240°
criar_aleta(0, "Aleta_Direita")
criar_aleta(120, "Aleta_Esquerda")
criar_aleta(240, "Aleta_Traseira")

# --- Câmera e Iluminação (Enquadramento 3/4 clássico) ---
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 4.8
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

# Ângulo 3/4 suave: olhando para a direita e levemente inclinado
ang = math.radians(38)
dist = 12.0
cam.location = (dist * math.cos(ang), dist * math.sin(ang), 1.9)
cam.rotation_euler = (math.radians(82), 0, ang + math.radians(90))

# Iluminação do Sol + Luz de preenchimento
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 2.8
sun = bpy.data.objects.new("Sun", sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), math.radians(-25), math.radians(65))

fill_data = bpy.data.lights.new("Fill", "SUN")
fill_data.energy = 1.2
fill = bpy.data.objects.new("Fill", fill_data)
sc.collection.objects.link(fill)
fill.rotation_euler = (math.radians(-30), math.radians(60), math.radians(-45))

# Salva arquivo Blender para edições futuras
out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("Arquivo .blend salvo em:", out_blend)

# Renderiza prévia
out_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\previa_foguete.png"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("Prévia renderizada em:", out_png)
