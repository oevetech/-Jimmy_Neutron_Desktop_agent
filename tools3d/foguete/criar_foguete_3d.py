import bpy
import bmesh
import math
import mathutils
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# Configurações do Render EEVEE
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = 800
sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"

# --- Materiais Cartoon Estilo Jimmy Neutron ---
def criar_mat(nome, cor, metallic=0.0, roughness=0.3, alpha=1.0):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.65
    if alpha < 1.0:
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else "HASHED"
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.85
    return mat

# Vermelho brilhante original
mat_vermelho = criar_mat("Mat_Vermelho", (0.83, 0.08, 0.07, 1.0), metallic=0.06, roughness=0.20)
# Cromo ultra reflexivo para o nariz
mat_chrome = criar_mat("Mat_Chrome", (0.88, 0.90, 0.95, 1.0), metallic=0.95, roughness=0.10)
# Turbina traseira em metal escuro
mat_nozzle = criar_mat("Mat_Nozzle", (0.18, 0.19, 0.22, 1.0), metallic=0.85, roughness=0.30)
# Cúpula de vidro bolha com leve reflexo ciano
mat_vidro = criar_mat("Mat_Vidro", (0.50, 0.88, 0.98, 0.50), metallic=0.05, roughness=0.06, alpha=0.50)
# Interior da cabine (painel e assento)
mat_interior = criar_mat("Mat_Interior", (0.12, 0.13, 0.15, 1.0), metallic=0.2, roughness=0.5)
mat_painel = criar_mat("Mat_Painel", (1.0, 0.65, 0.05, 1.0), metallic=0.1, roughness=0.3)

# Contorno toon preto (Solidify inverted-hull)
mat_outline = bpy.data.materials.new("Mat_Outline")
mat_outline.use_nodes = True
mat_outline.use_backface_culling = True
p_out = mat_outline.node_tree.nodes["Principled BSDF"]
p_out.inputs["Base Color"].default_value = (0.015, 0.015, 0.02, 1.0)
p_out.inputs["Roughness"].default_value = 1.0

def add_outline(obj, thickness=0.018):
    obj.data.materials.append(mat_outline)
    so = obj.modifiers.new("Outline", "SOLIDIFY")
    so.thickness = thickness
    so.offset = 1.0
    so.use_flip_normals = True
    so.material_offset = len(obj.data.materials) - 1
    so.use_rim = False

# 1. Fuselagem Aerodinâmica Torpedo
bm = bmesh.new()
profile = [
    (0.00, 0.28),   # Traseira
    (0.25, 0.38),
    (0.60, 0.48),
    (1.10, 0.54),   # Barriga máxima
    (1.65, 0.53),
    (2.15, 0.46),
    (2.55, 0.36),
    (2.80, 0.26),   # Encontro com o nariz cromado
]

segments = 36
rings = []
for x, r in profile:
    ring = []
    for i in range(segments):
        th = (2.0 * math.pi * i) / segments
        y = r * math.cos(th)
        z = r * math.sin(th)
        ring.append(bm.verts.new((x, y, z)))
    rings.append(ring)

for l in range(len(rings) - 1):
    r1, r2 = rings[l], rings[l+1]
    for i in range(segments):
        i_next = (i + 1) % segments
        bm.faces.new((r1[i], r2[i], r2[i_next], r1[i_next]))

cap_back = bm.verts.new((profile[0][0], 0, 0))
for i in range(segments):
    i_next = (i + 1) % segments
    bm.faces.new((cap_back, rings[0][i], rings[0][i_next]))

cap_front = bm.verts.new((profile[-1][0], 0, 0))
for i in range(segments):
    i_next = (i + 1) % segments
    bm.faces.new((cap_front, rings[-1][i_next], rings[-1][i]))

bm.normal_update()
me_body = bpy.data.meshes.new("FuselagemMesh")
bm.to_mesh(me_body)
bm.free()

obj_body = bpy.data.objects.new("Fuselagem", me_body)
sc.collection.objects.link(obj_body)
obj_body.data.materials.append(mat_vermelho)
add_outline(obj_body, thickness=0.016)
sub = obj_body.modifiers.new("Subsurf", "SUBSURF")
sub.levels = 1
sub.render_levels = 2

# 2. Cone de Nariz Cromado
bm_cone = bmesh.new()
cone_profile = [
    (2.80, 0.26),
    (3.10, 0.19),
    (3.35, 0.12),
    (3.55, 0.05),
    (3.64, 0.015),
]
rings_cone = []
for x, r in cone_profile:
    ring = []
    for i in range(segments):
        th = (2.0 * math.pi * i) / segments
        ring.append(bm_cone.verts.new((x, r * math.cos(th), r * math.sin(th))))
    rings_cone.append(ring)

for l in range(len(rings_cone) - 1):
    r1, r2 = rings_cone[l], rings_cone[l+1]
    for i in range(segments):
        i_next = (i + 1) % segments
        bm_cone.faces.new((r1[i], r2[i], r2[i_next], r1[i_next]))

cap_cone_front = bm_cone.verts.new((cone_profile[-1][0], 0, 0))
for i in range(segments):
    i_next = (i + 1) % segments
    bm_cone.faces.new((cap_cone_front, rings_cone[-1][i_next], rings_cone[-1][i]))

bm_cone.normal_update()
me_cone = bpy.data.meshes.new("ConeMesh")
bm_cone.to_mesh(me_cone)
bm_cone.free()
obj_cone = bpy.data.objects.new("NoseCone", me_cone)
sc.collection.objects.link(obj_cone)
obj_cone.data.materials.append(mat_chrome)
add_outline(obj_cone, thickness=0.014)

# 3. Agulha Cromada & Esfera da Ponta
bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.50, location=(3.89, 0, 0), rotation=(0, math.radians(90), 0))
obj_needle = bpy.context.active_object
obj_needle.name = "Needle"
obj_needle.data.materials.append(mat_chrome)
add_outline(obj_needle, thickness=0.010)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.046, location=(4.14, 0, 0))
obj_tip = bpy.context.active_object
obj_tip.name = "NeedleTip"
obj_tip.data.materials.append(mat_chrome)
add_outline(obj_tip, thickness=0.010)

# 4. Bocal da Turbina Traseira
bpy.ops.mesh.primitive_cone_add(radius1=0.34, radius2=0.23, depth=0.32, location=(-0.16, 0, 0), rotation=(0, math.radians(-90), 0))
obj_nozzle = bpy.context.active_object
obj_nozzle.name = "Nozzle"
obj_nozzle.data.materials.append(mat_nozzle)
add_outline(obj_nozzle, thickness=0.016)

# Interior do bocal
bpy.ops.mesh.primitive_circle_add(radius=0.29, fill_type="NGON", location=(-0.30, 0, 0), rotation=(0, math.radians(-90), 0))
obj_nozzle_in = bpy.context.active_object
obj_nozzle_in.data.materials.append(mat_interior)

# 5. Cabine Bolha
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.34, location=(1.95, 0, 0.42))
obj_glass = bpy.context.active_object
obj_glass.name = "CockpitGlass"
obj_glass.scale = (1.45, 0.78, 0.68)
bpy.ops.object.transform_apply(scale=True)
obj_glass.data.materials.append(mat_vidro)
add_outline(obj_glass, thickness=0.012)

# Aro cromado
bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.024, location=(1.95, 0, 0.38))
obj_rim = bpy.context.active_object
obj_rim.name = "CockpitRim"
obj_rim.scale = (1.48, 0.82, 0.52)
bpy.ops.object.transform_apply(scale=True)
obj_rim.data.materials.append(mat_chrome)
add_outline(obj_rim, thickness=0.010)

# Interior
bpy.ops.mesh.primitive_cube_add(size=0.18, location=(1.85, 0, 0.40))
obj_seat = bpy.context.active_object
obj_seat.scale = (1.1, 0.58, 0.68)
bpy.ops.object.transform_apply(scale=True)
obj_seat.data.materials.append(mat_interior)

bpy.ops.mesh.primitive_torus_add(major_radius=0.07, minor_radius=0.014, location=(2.14, 0, 0.44), rotation=(0, math.radians(35), 0))
obj_wheel = bpy.context.active_object
obj_wheel.data.materials.append(mat_painel)

# 6. As 3 Aletas Grandes Retro Swept-Wing
def criar_aleta(rot_x, nome):
    bm_fin = bmesh.new()
    fin_pts = [
        (0.10, 0.28),    # Raiz traseira
        (-0.50, 0.95),   # Ponta varrida para trás
        (-0.40, 1.10),   # Curva superior da ponta
        (0.15, 1.14),    # Borda superior máxima
        (0.55, 0.92),    # Curva frontal aerodinâmica
        (1.05, 0.54),    # Fixação frontal na fuselagem
        (0.85, 0.42),
    ]
    t = 0.038
    v_front = [bm_fin.verts.new((p[0], -t, p[1])) for p in fin_pts]
    v_back  = [bm_fin.verts.new((p[0],  t, p[1])) for p in fin_pts]
    bm_fin.faces.new(v_front)
    bm_fin.faces.new(list(reversed(v_back)))
    n = len(fin_pts)
    for i in range(n):
        i_next = (i + 1) % n
        bm_fin.faces.new((v_front[i], v_back[i], v_back[i_next], v_front[i_next]))
    bm_fin.normal_update()
    me_fin = bpy.data.meshes.new(nome + "Mesh")
    bm_fin.to_mesh(me_fin)
    bm_fin.free()
    
    obj_fin = bpy.data.objects.new(nome, me_fin)
    sc.collection.objects.link(obj_fin)
    obj_fin.data.materials.append(mat_vermelho)
    add_outline(obj_fin, thickness=0.016)
    sub = obj_fin.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    obj_fin.rotation_euler = (math.radians(rot_x), 0, 0)
    return obj_fin

criar_aleta(90, "Aleta_Superior")
criar_aleta(215, "Aleta_Inferior_Chao")
criar_aleta(325, "Aleta_Inferior_Frente")

# 7. Câmera Ortho Enquadrada com folga segura
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 5.8
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

cam.location = (1.8, -6.5, 1.35)
cam.rotation_euler = (math.radians(78), 0, math.radians(-3))

# 8. Iluminação
sun_data = bpy.data.lights.new("SunKey", "SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("SunKey", sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-25), math.radians(35))

fill_data = bpy.data.lights.new("SunFill", "SUN")
fill_data.energy = 1.5
fill = bpy.data.objects.new("SunFill", fill_data)
sc.collection.objects.link(fill)
fill.rotation_euler = (math.radians(-35), math.radians(40), math.radians(-65))

rim_data = bpy.data.lights.new("SunRim", "SUN")
rim_data.energy = 1.2
rim = bpy.data.objects.new("SunRim", rim_data)
sc.collection.objects.link(rim)
rim.rotation_euler = (math.radians(-60), math.radians(-30), math.radians(120))

# Salva .blend
out_blend = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\foguete_strato_xl.blend"
bpy.ops.wm.save_as_mainfile(filepath=out_blend)

# Renderiza render bruto
raw_png = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\raw_render_parked.png"
sc.render.filepath = raw_png
bpy.ops.render.render(write_still=True)
print("Render bruto concluído:", raw_png)
