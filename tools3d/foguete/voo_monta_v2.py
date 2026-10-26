"""Jimmy montado no foguete (voo_monta), versão 2.

blender -b -P voo_monta_v2.py -- saida_dir [previa]
Jimmy grande (cabeça ~ diâmetro do foguete), sentado em cima atrás da cabine,
pernas abertas dos dois lados do casco, mãos na borda da cabine, chama no motor.
"""
import bpy, sys, os, math, mathutils

RAIZ = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d"
BLEND = os.path.join(RAIZ, "foguete", "foguete_strato_xl.blend")
FBX = os.path.join(RAIZ, "fbx", "jimmy_flight_pilot.fbx")
TEX = os.path.join(RAIZ, "jimmy_novo_cor.png")   # textura do modelo novo (b16fc…)
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
PREVIA = len(args) > 1 and args[1] == "previa"
os.makedirs(OUT, exist_ok=True)

ESCALA = 2.2            # altura em pé ~2,4 (o foguete tem 4,2)
ASSENTO = (0.95, 0.0)   # x, y do quadril em cima do casco
INCLINA = 28            # foguete subindo
PERNA_DESCE = float(os.environ.get("PERNA_DESCE", "70"))
PERNA_ABRE = float(os.environ.get("PERNA_ABRE", "45"))
ASSENTO_Z = float(os.environ.get("ASSENTO_Z", "0.56"))   # altura do quadril (antes de afinar)
FINO = float(os.environ.get("FINO", "0.78"))             # diâmetro do foguete

# Poses por quadro: 0-1 medo (agarrado, encolhido), 2-4 vento (corpo para trás, braços)
QUADROS = [
    dict(f=60,  tronco=18, cabeca=-10, braco=0,   chama=0.8),
    dict(f=90,  tronco=10, cabeca=-4,  braco=0,   chama=1.0),
    dict(f=120, tronco=-6, cabeca=6,   braco=10,  chama=1.15),
    dict(f=150, tronco=-12, cabeca=10, braco=18,  chama=0.95),
    dict(f=180, tronco=-8, cabeca=4,   braco=12,  chama=1.2),
]

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"
foguete = [o for o in sc.objects if o.type == "MESH"]

# Foguete com menos brilho de plástico, mais cara de desenho
for m in bpy.data.materials:
    if m.node_tree and m.name != "Mat_Outline":
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Roughness"].default_value = max(n.inputs["Roughness"].default_value, 0.55)
                if "Specular IOR Level" in n.inputs:
                    n.inputs["Specular IOR Level"].default_value = 0.2

# --- Jimmy ---
bpy.ops.import_scene.fbx(filepath=FBX)
arm = [o for o in sc.objects if o.type == "ARMATURE"][0]
me = [o for o in arm.children if o.type == "MESH"][0]
mat = me.data.materials[0]; nt = mat.node_tree
bsdf = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
for n in list(nt.nodes):
    if n.type == "TEX_IMAGE": nt.nodes.remove(n)
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(TEX)
nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["Roughness"].default_value = 0.8
if "Specular IOR Level" in bsdf.inputs: bsdf.inputs["Specular IOR Level"].default_value = 0.15
contorno = bpy.data.materials["Mat_Outline"]
me.data.materials.append(contorno)
so = me.modifiers.new("Contorno", "SOLIDIFY")
so.thickness = 0.012; so.offset = 1.0; so.use_flip_normals = True; so.use_rim = False
so.material_offset = len(me.data.materials) - 1

arm.scale = (0.01 * ESCALA * 100,) * 3 if arm.scale[0] < 0.1 else (ESCALA,) * 3
arm.rotation_euler = (math.radians(90), 0, math.radians(90))   # olha para +X (bico)

# Amostra a pose da animação e solta a action para podermos somar ajustes
acao = arm.animation_data.action
def amostra(f):
    arm.animation_data.action = acao
    sc.frame_set(f)
    pose = {b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in arm.pose.bones}
    arm.animation_data.action = None
    return pose

def gira(nome, eixo, graus):
    b = arm.pose.bones.get("mixamorig:" + nome)
    if b: b.rotation_quaternion = b.rotation_quaternion @ mathutils.Quaternion(eixo, math.radians(graus))

def gira_corpo(nome, eixo, graus):
    """Gira o osso em torno de um eixo do corpo (espaço da armature: X = esquerda do Jimmy,
    Y = cima, Z = frente), independente da orientação local do osso."""
    bpy.context.view_layer.update()
    b = arm.pose.bones["mixamorig:" + nome]
    local = (b.matrix.to_3x3().normalized().inverted() @ mathutils.Vector(eixo)).normalized()
    b.rotation_quaternion = b.rotation_quaternion @ mathutils.Quaternion(local, math.radians(graus))

# --- Chama ---
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.3, depth=1.2, location=(-0.9, 0, 0),
                                rotation=(0, math.radians(-90), 0))   # base no bocal, ponta para trás
chama = bpy.context.active_object; chama.name = "Chama"
mc = bpy.data.materials.new("Mat_Chama"); mc.use_nodes = True
em = mc.node_tree.nodes.new("ShaderNodeEmission")
cr = mc.node_tree.nodes.new("ShaderNodeValToRGB")
geo = mc.node_tree.nodes.new("ShaderNodeTexCoord")
sep = mc.node_tree.nodes.new("ShaderNodeSeparateXYZ")
mc.node_tree.links.new(geo.outputs["Generated"], sep.inputs[0])
mc.node_tree.links.new(sep.outputs["Z"], cr.inputs[0])
cr.color_ramp.elements[0].color = (1.0, 0.85, 0.2, 1); cr.color_ramp.elements[1].color = (1.0, 0.25, 0.0, 1)
mc.node_tree.links.new(cr.outputs[0], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
out = [n for n in mc.node_tree.nodes if n.type == "OUTPUT_MATERIAL"][0]
mc.node_tree.links.new(em.outputs[0], out.inputs["Surface"])
chama.data.materials.append(mc)
miolo = chama.copy(); miolo.data = chama.data.copy(); sc.collection.objects.link(miolo)
miolo.scale = (0.55, 0.55, 0.7); miolo.location = (-0.75, 0, 0)

# --- Raiz inclinada: foguete + Jimmy + chama ---
raiz = bpy.data.objects.new("Raiz", None); sc.collection.objects.link(raiz)
# Foguete mais fino (as pernas do Jimmy são curtas para abraçar o casco original)
fino = bpy.data.objects.new("Fino", None); sc.collection.objects.link(fino)
fino.scale = (1, FINO, FINO); fino.parent = raiz
for o in foguete + [chama, miolo]:
    o.parent = fino
arm.parent = raiz
raiz.rotation_euler = (0, math.radians(-INCLINA), 0)

cam = sc.camera
cam.data.type = "ORTHO"
cam.rotation_euler = (math.radians(90), 0, 0)

def posiciona_jimmy():
    """Põe o quadril em cima do casco no ASSENTO."""
    bpy.context.view_layer.update()
    hips = arm.pose.bones["mixamorig:Hips"]
    alvo_local = mathutils.Vector((ASSENTO[0], ASSENTO[1], ASSENTO_Z * FINO))  # topo do casco
    cur = raiz.matrix_world.inverted() @ (arm.matrix_world @ hips.head)
    arm.location += alvo_local - cur
    bpy.context.view_layer.update()

def limites():
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in [me] + foguete + [chama]:
        ev = o.evaluated_get(dg); m = ev.to_mesh()
        pts += [ev.matrix_world @ v.co for v in m.vertices]
        ev.to_mesh_clear()
    lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
    hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi

lista = QUADROS[2:3] if PREVIA else QUADROS
for idx, q in enumerate(lista):
    pose = amostra(q["f"])
    for b in arm.pose.bones:
        b.location, b.rotation_quaternion = pose[b.name]
    # Pernas abertas para os lados do casco
    for lado, s in (("Left", 1), ("Right", -1)):
        gira_corpo(lado + "UpLeg", (1, 0, 0), PERNA_DESCE)      # coxa desce em diagonal
        gira_corpo(lado + "UpLeg", (0, 0, 1), s * PERNA_ABRE)   # e abre para o lado do casco
        gira_corpo(lado + "Leg", (1, 0, 0), -PERNA_DESCE * 0.6) # canela volta a ficar quase vertical
    # Tronco/cabeça conforme o momento
    gira("Spine", (1, 0, 0), q["tronco"]); gira("Head", (1, 0, 0), q["cabeca"])
    gira("LeftArm", (1, 0, 0), -q["braco"]); gira("RightArm", (1, 0, 0), -q["braco"])
    posiciona_jimmy()
    s = q["chama"]; chama.scale = (1.0, 1.0, s); miolo.scale = (0.55, 0.55, 0.7 * s)  # comprimento = Z do cone
    if idx == 0:
        # Enquadramento fixo para todos os quadros (senão o foguete "pula" de tamanho)
        lo, hi = limites(); c = (lo + hi) / 2; d = hi - lo
        cam.data.ortho_scale = max(d.x, d.z) * 1.15
        cam.location = (c.x, c.y - 20, c.z)
    sc.render.filepath = os.path.join(OUT, f"raw_{idx:02d}.png")
    bpy.ops.render.render(write_still=True)
    if PREVIA:
        # vista de frente também (pernas abertas?)
        cam.location = c + raiz.matrix_world.to_3x3() @ mathutils.Vector((12, 0, 0))
        cam.rotation_euler = (raiz.matrix_world.to_3x3() @ mathutils.Vector((-1, 0, 0))).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, "previa_frente.png")
        bpy.ops.render.render(write_still=True)
print("PRONTO", OUT)
