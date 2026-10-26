import bpy, sys, os
out_dir = sys.argv[sys.argv.index("--")+1]
ob = [o for o in bpy.data.objects if o.type == "MESH"][0]
# Só a cor base (o Mixamo ignora metálico/rugosidade); textura em 2048
mat = ob.data.materials[0]
base = None
for n in mat.node_tree.nodes:
    if n.type == "BSDF_PRINCIPLED":
        l = n.inputs["Base Color"].links
        if l and l[0].from_node.type == "TEX_IMAGE": base = l[0].from_node.image
print("BASE", base and base.name)
base.scale(2048, 2048)
base.filepath_raw = os.path.join(out_dir, "jimmy_cor.png"); base.file_format = "PNG"; base.save()
for n in list(mat.node_tree.nodes):
    if n.type == "TEX_IMAGE" and n.image is not base: mat.node_tree.nodes.remove(n)
for o in list(bpy.data.objects):
    if o is not ob: bpy.data.objects.remove(o)
bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, "jimmy.obj"), export_materials=True,
                      path_mode="RELATIVE", export_normals=True, export_uv=True, forward_axis="NEGATIVE_Z", up_axis="Y")
