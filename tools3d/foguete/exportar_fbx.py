import bpy
import os

blend_path = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete\vistas_novo_jimmy\jimmy_cabelo_ajustado.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Exporta FBX corrigido para a pasta Downloads e para a pasta do projeto tools3d
out_fbx_downloads = r"C:\Users\everaldolima\Downloads\jimmy_corrigido_cabelo.fbx"
out_fbx_tools3d = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\jimmy_corrigido_cabelo.fbx"

for path in [out_fbx_downloads, out_fbx_tools3d]:
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=False,
        embed_textures=True,
        path_mode="COPY"
    )
    print(f"Exportado FBX com sucesso para: {path} ({os.path.getsize(path)//1024} KB)")
