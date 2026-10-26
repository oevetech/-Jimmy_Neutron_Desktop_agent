"""Renderiza uma animação do Mixamo de lado (olhando para a direita), fundo transparente, em quadros PNG."""
import bpy, sys, os, math, mathutils
a = sys.argv[sys.argv.index("--")+1:]
fbx, tex, out_dir, n_quadros = a[0], a[1], a[2], int(a[3])
ANG = math.radians(float(a[4]) if len(a) > 4 else 40)   # 0 = perfil puro; 40 = três quartos, mostrando o rosto
PX, BASE_PX, TOPO_PX = 277, 273, 9          # mesmo enquadramento do jimmy_walk atual
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
me = [o for o in bpy.data.objects if o.type == "MESH"][0]
sc = bpy.context.scene
act = arm.animation_data.action
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])

# Material: textura original, sem brilho plástico
img = bpy.data.images.load(tex)
mat = me.data.materials[0]; nt = mat.node_tree
bsdf = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.75
if "Specular IOR Level" in bsdf.inputs: bsdf.inputs["Specular IOR Level"].default_value = 0.2
bsdf.inputs["Metallic"].default_value = 0.0

# Contorno de desenho (casca invertida preta)
loc = [v.co for v in me.data.vertices]
alt_local = max(max(c[i] for c in loc) - min(c[i] for c in loc) for i in range(3))
preto = bpy.data.materials.new("contorno"); preto.use_nodes = True
pb = preto.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.02, 0.02, 0.03, 1); pb.inputs["Roughness"].default_value = 1
preto.use_backface_culling = True
me.data.materials.append(preto)
so = me.modifiers.new("contorno", "SOLIDIFY")
so.thickness = alt_local * 0.008; so.offset = 1; so.use_flip_normals = True
so.material_offset = len(me.data.materials) - 1; so.use_rim = False

# Mede a altura e o chão ao longo da animação (posições do mundo)
dg = bpy.context.evaluated_depsgraph_get()
zs_min, zs_max = [], []
quadros = [f0 + round(i * (f1 - f0) / n_quadros) for i in range(n_quadros)]
hip = [b for b in arm.pose.bones if b.name.endswith("Hips")][0]
for f in quadros:
    sc.frame_set(f)
    ev = me.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh(); mw = me.matrix_world
    zs = [(mw @ v.co).z for v in m.vertices]; ev.to_mesh_clear()
    zs_min.append(min(zs)); zs_max.append(max(zs))
chao, topo = min(zs_min), max(zs_max)
H = topo - chao

# Se o personagem estiver deitado (ex: caindo, deitado), usa a altura do modelo em pe para nao dar zoom excessivo
rest_zs = [(mw @ v.co).z for v in me.data.vertices]
rest_h = max(rest_zs) - min(rest_zs) if rest_zs else H
usou_rest = False
if H < rest_h * 0.75:
    H = rest_h * 1.15
    usou_rest = True

escala = H * PX / (BASE_PX - TOPO_PX)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = escala; cam.data.clip_end = H * 100; cam.data.clip_start = H * 0.001
sc.camera = cam
olhar = mathutils.Vector((math.cos(ANG), math.sin(ANG), 0))        # a frente do Jimmy (-Y) fica à direita da imagem
cam.rotation_euler = (math.radians(90), 0, ANG - math.radians(90))
if usou_rest:
    cam_z = (topo + chao) / 2
else:
    cam_z = chao - escala / 2 + BASE_PX / PX * escala

sol = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN")); sc.collection.objects.link(sol)
sol.data.energy = 2.6
sol.rotation_euler = (olhar + mathutils.Vector((0.35, -0.3, -0.9))).to_track_quat("-Z", "Y").to_euler()   # luz vinda da frente, de cima
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 1.5
sc.render.engine = "BLENDER_EEVEE"; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = PX
sc.view_settings.view_transform = "Standard"
os.makedirs(out_dir, exist_ok=True)
for i, f in enumerate(quadros):
    sc.frame_set(f)
    p = arm.matrix_world @ hip.head                                # câmera acompanha o quadril (anda no lugar)
    cam.location = mathutils.Vector((p.x, p.y, cam_z)) - olhar * H * 10
    sc.render.filepath = os.path.join(out_dir, f"{i:02d}.png")
    bpy.ops.render.render(write_still=True)
print("PRONTO", len(quadros), "quadros", quadros)
