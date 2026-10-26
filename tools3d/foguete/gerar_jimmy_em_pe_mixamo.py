import bpy
import bmesh
import math
import os
import zipfile

blend_path = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\vistas_novo_jimmy\jimmy_cabelo_ajustado.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh_obj = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)

# 1. Rotaciona +90° em X para colocar o Jimmy EM PÉ (Z = Altura, X = Braços abertos, Y = Frente/Costas)
mesh_obj.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(rotation=True)

# 2. Alinha a sola dos pés no chão (Z = 0.0)
min_z = min(v.co.z for v in mesh_obj.data.vertices)
mesh_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# 3. Limpa faces degeneradas e aplica Decimate para 40.000 polígonos
n_poly = len(mesh_obj.data.polygons)
print(f"Polígonos antes: {n_poly}")
if n_poly > 45000:
    mod_dec = mesh_obj.modifiers.new("Decimate", "DECIMATE")
    mod_dec.ratio = 40000 / n_poly
    bpy.ops.object.modifier_apply(modifier="Decimate")

print("Dimensões finais em pé (X, Y, Z):", mesh_obj.dimensions)
print("Polígonos finais:", len(mesh_obj.data.polygons))

out_dir = r"C:\Users\everaldolima\Downloads"

# 4. Exporta FBX otimizado e perfeitamente em pé
fbx_path = os.path.join(out_dir, "jimmy_mixamo_pronto.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    add_leaf_bones=False,
    bake_anim=False,
    path_mode="COPY",
    embed_textures=True
)
print("FBX pronto exportado:", fbx_path, f"({os.path.getsize(fbx_path)//1024} KB)")

# 5. Exporta OBJ em pé
obj_path = os.path.join(out_dir, "jimmy_mixamo_pronto.obj")
mtl_path = os.path.join(out_dir, "jimmy_mixamo_pronto.mtl")
bpy.ops.wm.obj_export(
    filepath=obj_path,
    export_selected_objects=True,
    export_materials=True,
    export_normals=True,
    export_uv=True,
    forward_axis="NEGATIVE_Y",
    up_axis="Z"
)
print("OBJ pronto exportado:", obj_path, f"({os.path.getsize(obj_path)//1024} KB)")

# 6. Cria ZIP completo pronto para arrastar no Mixamo
tex_file = os.path.join(out_dir, "jimmy_textura.png")
zip_path = os.path.join(out_dir, "jimmy_mixamo_pronto.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(obj_path, "jimmy_mixamo_pronto.obj")
    if os.path.exists(mtl_path):
        z.write(mtl_path, "jimmy_mixamo_pronto.mtl")
    if os.path.exists(tex_file):
        z.write(tex_file, "jimmy_textura.png")

print("ZIP pronto exportado:", zip_path, f"({os.path.getsize(zip_path)//1024} KB)")
