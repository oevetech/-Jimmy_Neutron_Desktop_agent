"""Voo do Jimmy no foguete em 3D (v2): pendura, escala, senta e monta.

blender -b -P voo_v2.py -- saida_raiz anim[,anim...] [previa]
Grava saida_raiz/<anim>/raw_XX.png. Todas as fases usam o MESMO enquadramento
(baseado só no foguete), para o foguete não mudar de tamanho na troca de fase.
"""
import bpy, sys, os, math, mathutils

RAIZ = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d"
BLEND = os.path.join(RAIZ, "foguete", "foguete_strato_xl.blend")
TEX = os.path.join(RAIZ, "jimmy_novo_cor.png")   # textura do modelo novo (b16fc…)
args = sys.argv[sys.argv.index("--") + 1:]
OUT, ANIMS = args[0], args[1].split(",")
PREVIA = len(args) > 2 and args[2] == "previa"

ESCALA = 2.2     # altura em pé ~2,4 (o foguete tem 4,2)
INCLINA = 28     # foguete subindo
FINO = 0.78      # diâmetro do foguete (pernas do Jimmy são curtas para o casco original)
CAMPO = 1.45     # largura do quadro em relação ao comprimento do foguete inclinado

def env(nome, padrao):
    return float(os.environ.get(nome, padrao))

# Cada fase: animação do Mixamo, como o Jimmy fica preso ao foguete e as poses por quadro.
#  ancora: osso que vai no ponto 'alvo' (coordenadas do foguete, antes de afinar o diâmetro)
#  em_pe: True = Jimmy fica na vertical do mundo (pendurado); False = inclina junto com o foguete
#  rumo: para onde ele olha (90 = bico do foguete, 0 = câmera)
MONTADO = dict(fbx="jimmy_flight_pilot.fbx", ancora="Hips", alvo=(0.95, 0.0, 0.56), em_pe=False, rumo=90,
               pernas=dict(desce=70, abre=45))
FASES = {
    "voo_monta": dict(MONTADO, quadros=[
        dict(f=60,  tronco=18, cabeca=-10, braco=0,  chama=0.8),
        dict(f=90,  tronco=10, cabeca=-4,  braco=0,  chama=1.0),
        dict(f=120, tronco=-6, cabeca=6,   braco=10, chama=1.15),
        dict(f=150, tronco=-12, cabeca=10, braco=18, chama=0.95),
        dict(f=180, tronco=-8, cabeca=4,   braco=12, chama=1.2)]),
    # Acabou de subir: debruçado para frente, agarrado, com medo
    "voo_senta": dict(MONTADO, quadros=[
        dict(f=60, tronco=28, cabeca=-14, braco=-8, chama=0.9)]),
    # Decolando pendurado embaixo do casco, pernas balançando
    "voo_pendura": dict(fbx="jimmy_hang_idle.fbx", ancora="Hands",
                        alvo=(env("P_X", "1.7"), env("P_Y", "-0.7"), env("P_Z", "-0.45")),
                        em_pe=True, rumo=env("P_RUMO", "20"), quadros=[
        dict(f=30, chute=22, ombro=env("P_OMBRO", "10"), estica=env("P_ESTICA", "2.0"), chama=1.1),
        dict(f=90, chute=-22, ombro=env("P_OMBRO", "10") - 6, estica=env("P_ESTICA", "2.0"), chama=0.85)]),
    # Escalando a lateral para chegar em cima
    "voo_escala": dict(fbx="jimmy_braced_hang.fbx", ancora="Hands",
                       alvo=(env("E_X", "1.4"), env("E_Y", "-0.8"), env("E_Z", "0.45")),
                       em_pe=True, rumo=env("E_RUMO", "40"), quadros=[
        dict(f=20, ombro=env("E_OMBRO", "-90"), estica=env("E_ESTICA", "1.8"), chama=1.0)]),
}

def gira(arm, nome, eixo, graus):
    b = arm.pose.bones.get("mixamorig:" + nome)
    if b: b.rotation_quaternion = b.rotation_quaternion @ mathutils.Quaternion(eixo, math.radians(graus))

def gira_corpo(arm, nome, eixo, graus):
    """Gira o osso em torno de um eixo do corpo (espaço da armature: X = esquerda do Jimmy,
    Y = cima, Z = frente), independente da orientação local do osso."""
    bpy.context.view_layer.update()
    b = arm.pose.bones["mixamorig:" + nome]
    local = (b.matrix.to_3x3().normalized().inverted() @ mathutils.Vector(eixo)).normalized()
    b.rotation_quaternion = b.rotation_quaternion @ mathutils.Quaternion(local, math.radians(graus))

def monta_cena(fase):
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
    bpy.ops.import_scene.fbx(filepath=os.path.join(RAIZ, "fbx", fase["fbx"]))
    arm = [o for o in sc.objects if o.type == "ARMATURE"][0]
    me = [o for o in arm.children if o.type == "MESH"][0]
    mat = me.data.materials[0]; nt = mat.node_tree
    bsdf = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    for n in list(nt.nodes):
        if n.type == "TEX_IMAGE": nt.nodes.remove(n)
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(TEX)
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.0   # o FBX do Mixamo vem metálico (Jimmy cor de bronze)
    bsdf.inputs["Roughness"].default_value = 0.8
    if "Specular IOR Level" in bsdf.inputs: bsdf.inputs["Specular IOR Level"].default_value = 0.15
    me.data.materials.append(bpy.data.materials["Mat_Outline"])
    so = me.modifiers.new("Contorno", "SOLIDIFY")
    so.thickness = 0.012; so.offset = 1.0; so.use_flip_normals = True; so.use_rim = False
    so.material_offset = len(me.data.materials) - 1
    arm.scale = (ESCALA,) * 3

    # --- Chama ---
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.3, depth=1.2, location=(-0.9, 0, 0),
                                    rotation=(0, math.radians(-90), 0))   # base no bocal, ponta para trás
    chama = bpy.context.active_object; chama.name = "Chama"
    mc = bpy.data.materials.new("Mat_Chama")
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
    miolo.location = (-0.75, 0, 0)

    # --- Raiz inclinada (foguete afinado + chama; Jimmy junto se estiver montado) ---
    raiz = bpy.data.objects.new("Raiz", None); sc.collection.objects.link(raiz)
    fino = bpy.data.objects.new("Fino", None); sc.collection.objects.link(fino)
    fino.scale = (1, FINO, FINO); fino.parent = raiz
    for o in foguete + [chama, miolo]:
        o.parent = fino
    raiz.rotation_euler = (0, math.radians(-INCLINA), 0)
    if fase["em_pe"]:
        arm.rotation_euler = (math.radians(90), 0, math.radians(fase["rumo"]))
    else:
        arm.parent = raiz
        arm.rotation_euler = (math.radians(90), 0, math.radians(fase["rumo"]))
    bpy.context.view_layer.update()

    # Câmera: mesmo enquadramento em todas as fases, calculado só pelo foguete
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in foguete:
        ev = o.evaluated_get(dg); m = ev.to_mesh()
        pts += [ev.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
    lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
    hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2
    cam = sc.camera; cam.data.type = "ORTHO"
    cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.ortho_scale = (hi.x - lo.x) * CAMPO
    cam.location = (c.x - 0.3, c.y - 20, c.z)
    return sc, arm, raiz, chama, miolo, cam

def ancora_mundo(arm, nome):
    bpy.context.view_layer.update()
    if nome == "Hands":
        l, r = arm.pose.bones["mixamorig:LeftHand"], arm.pose.bones["mixamorig:RightHand"]
        return arm.matrix_world @ ((l.head + r.head) / 2)
    return arm.matrix_world @ arm.pose.bones["mixamorig:" + nome].head

def renderiza(anim):
    fase = FASES[anim]
    sc, arm, raiz, chama, miolo, cam = monta_cena(fase)
    acao = arm.animation_data.action
    pasta = os.path.join(OUT, anim); os.makedirs(pasta, exist_ok=True)
    quadros = fase["quadros"][:1] if PREVIA else fase["quadros"]
    for idx, q in enumerate(quadros):
        arm.animation_data.action = acao
        sc.frame_set(q["f"])
        pose = {b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in arm.pose.bones}
        arm.animation_data.action = None
        for b in arm.pose.bones:
            b.location, b.rotation_quaternion = pose[b.name]
        if "pernas" in fase:   # montado: pernas abertas dos dois lados do casco
            p = fase["pernas"]
            for lado, s in (("Left", 1), ("Right", -1)):
                gira_corpo(arm, lado + "UpLeg", (1, 0, 0), p["desce"])
                gira_corpo(arm, lado + "UpLeg", (0, 0, 1), s * p["abre"])
                gira_corpo(arm, lado + "Leg", (1, 0, 0), -p["desce"] * 0.6)
        if "estica" in q:      # braços compridos de desenho, para as mãos passarem do cabelo
            for lado in ("Left", "Right"):
                for osso in ("Arm", "ForeArm"):
                    b = arm.pose.bones["mixamorig:" + lado + osso]
                    b.scale = (1, q["estica"], 1)
                    arm.data.bones["mixamorig:" + lado + osso].inherit_scale = "NONE" if osso == "ForeArm" else "FULL"
                arm.data.bones["mixamorig:" + lado + "Hand"].inherit_scale = "NONE"
        if "ombro" in q:       # traz os braços de cima da cabeça (escondidos no cabelo) para a frente
            gira_corpo(arm, "LeftArm", (1, 0, 0), q["ombro"]); gira_corpo(arm, "RightArm", (1, 0, 0), q["ombro"])
        if "chute" in q:       # pendurado: pernas balançando, uma para cada lado
            gira_corpo(arm, "LeftUpLeg", (1, 0, 0), -q["chute"])
            gira_corpo(arm, "RightUpLeg", (1, 0, 0), q["chute"])
        gira(arm, "Spine", (1, 0, 0), q.get("tronco", 0)); gira(arm, "Head", (1, 0, 0), q.get("cabeca", 0))
        gira(arm, "LeftArm", (1, 0, 0), -q.get("braco", 0)); gira(arm, "RightArm", (1, 0, 0), -q.get("braco", 0))
        # Encaixa a âncora (quadril ou mãos) no ponto do casco
        a = fase["alvo"]
        alvo = raiz.matrix_world @ mathutils.Vector((a[0], a[1] * FINO, a[2] * FINO))
        cur = ancora_mundo(arm, fase["ancora"])
        delta = alvo - cur
        if arm.parent: delta = arm.parent.matrix_world.to_3x3().inverted() @ delta
        arm.location += delta
        s = q["chama"]; chama.scale = (1.0, 1.0, s); miolo.scale = (0.55, 0.55, 0.7 * s)  # comprimento = Z do cone
        sc.render.filepath = os.path.join(pasta, f"raw_{idx:02d}.png")
        bpy.ops.render.render(write_still=True)

for a in ANIMS:
    renderiza(a)
print("PRONTO", OUT, ANIMS)
