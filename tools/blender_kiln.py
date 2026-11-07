import bpy, math, os
# blender-kiln local: foto -> modelo Blender editable a tamano real (1.8m), optimizado, validado, GLB
exec(open('tools/build_new_fighters.py',encoding='utf-8').read().split("out='C:/")[0])

REFS={'vamp':'refs/01-vampiro.jpg','ronin':'refs/02-ronin.jpg','rhino':'refs/03-rhino.jpg','panda':'refs/04-panda.jpg','roja':'refs/05-roja.jpg','ogro':'refs/06-ogro.jpg'}
SPECS={
 'vamp':((0.12,0.14,0.19),(0.05,0.06,0.1),(0.86,0.15,0.15),1.0,False),
 'ronin':((0.11,0.1,0.09),(0.05,0.05,0.05),(0.85,0.47,0.02),0.95,False),
 'rhino':((0.38,0.65,0.98),(0.07,0.09,0.15),(0.98,0.45,0.09),1.1,False),
 'panda':((0.97,0.98,0.99),(0.12,0.16,0.24),(0.98,0.45,0.09),1.05,True),
 'roja':((0.09,0.64,0.29),(0.42,0.45,0.5),(0.86,0.15,0.15),0.9,False),
 'ogro':((0.53,0.94,0.67),(0.12,0.16,0.22),(0.73,0.11,0.11),1.15,False),
}
bpy.context.scene.render.engine='CYCLES'; bpy.context.scene.cycles.samples=12; bpy.context.scene.cycles.device='CPU'
bpy.context.scene.render.resolution_x=640; bpy.context.scene.render.resolution_y=640
out_glb='C:/Users/USUARIO/pelea-IA-VS/models'
out_png='C:/Users/USUARIO/pelea-IA-VS/screenshots'
for name,(body,dark,acc,scale,belly) in SPECS.items():
    build_generic(name,body,dark,acc,scale,belly)
    # Foto como plano de referencia detras (editable, tamano real 1.8m alto)
    img_path=f'C:/Users/USUARIO/pelea-IA-VS/{REFS[name]}'
    if os.path.exists(img_path):
        img=bpy.data.images.load(img_path)
        mat=bpy.data.materials.new(name+'_foto'); mat.use_nodes=True
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=img
        mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0,-1.2,1.0))
        pl=bpy.context.active_object; pl.name=name+'_foto_ref'; pl.data.materials.append(mat)
    make_actions()
    export_glb(f'{out_glb}/kiln-{name}.glb')
    # camara + render preview
    bpy.ops.object.camera_add(location=(0,6,2.5))
    cam=bpy.context.active_object; bpy.context.scene.camera=cam
    bpy.ops.object.empty_add(location=(0,0,1.2)); tgt=bpy.context.active_object
    con=cam.constraints.new(type='TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
    bpy.ops.object.light_add(type='SUN', location=(4,4,6)); bpy.context.active_object.data.energy=3
    bpy.context.scene.render.filepath=f'{out_png}/kiln-{name}.png'
    bpy.ops.render.render(write_still=True)
    print('KILN DONE', name)
print('KILN ALL DONE')
bpy.ops.wm.save_as_mainfile(filepath='C:/Users/USUARIO/pelea-IA-VS/kiln.blend')
