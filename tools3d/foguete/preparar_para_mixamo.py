import bpy
import os
import zipfile
import shutil

blend_path = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\vistas_novo_jimmy\jimmy_cabelo_ajustado.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh_obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)

# 1. Aplica Decimate para reduzir de 500.000 para ~40.000 polígonos (padrão ideal do Mixamo)
n_poly = len(mesh_obj.data.polygons)
print(f"Polígonos originais: {n_poly}")

if n_poly > 50000:
    ratio = 45000 / n_poly
    mod_dec = mesh_obj.modifiers.new("Decimate", "DECIMATE")
    mod_dec.ratio = ratio
    bpy.ops.object.modifier_apply(modifier="Decimate")
    print(f"Polígonos após Decimate: {len(mesh_obj.data.polygons)}")

# Garante orientação perfeita (Frente = -Z, Cima = Y)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Diretórios de saída
out_dir_downloads = r"C:\Users\everaldolima\Downloads"
out_dir_tools = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d"

# 2. Salva textura base do Jimmy
tex_file = os.path.join(out_dir_downloads, "jimmy_cor.png")
# Procura imagem da textura no material
tex_found = False
for mat in mesh_obj.data.materials:
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                node.image.save_render(filepath=tex_file)
                tex_found = True
                break
    if tex_found: break

if not tex_found:
    orig_tex = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\jimmy_cor.png"
    if os.path.exists(orig_tex):
        shutil.copy2(orig_tex, tex_file)

# 3. Exporta como FBX otimizado (sem esqueleto fantasma)
fbx_out = os.path.join(out_dir_downloads, "jimmy_mixamo.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_out,
    use_selection=True,
    add_leaf_bones=False,
    bake_anim=False,
    path_mode="COPY",
    embed_textures=True
)
print("FBX para Mixamo gerado:", fbx_out, f"({os.path.getsize(fbx_out)//1024} KB)")

# 4. Exporta como OBJ (formato infalível no Mixamo, pois OBJ não contém esqueleto)
obj_out = os.path.join(out_dir_downloads, "jimmy_mixamo.obj")
mtl_out = os.path.join(out_dir_downloads, "jimmy_mixamo.mtl")
bpy.ops.wm.obj_export(
    filepath=obj_out,
    export_selected_objects=True,
    export_materials=True,
    export_normals=True,
    export_uv=True,
    forward_axis="NEGATIVE_Z",
    up_axis="Y"
)
print("OBJ para Mixamo gerado:", obj_out)

# 5. Cria pacote ZIP com OBJ + MTL + Textura (arraste e solte direto no Mixamo)
zip_out = os.path.join(out_dir_downloads, "jimmy_mixamo.zip")
with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(obj_out, "jimmy_mixamo.obj")
    if os.path.exists(mtl_out):
        z.write(mtl_out, "jimmy_mixamo.mtl")
    if os.path.exists(tex_file):
        z.write(tex_file, "jimmy_cor.png")

print(f"ZIP pronto para arrastar no Mixamo: {zip_out} ({os.path.getsize(zip_out)//1024} KB)")
