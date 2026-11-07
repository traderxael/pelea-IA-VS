import bpy, math
exec(open('tools/blender_build.py',encoding='utf-8').read().split('def main():')[0].split('main()')[0])
from mathutils import Vector

# Escena Coliseo Romano en Blender: terreno romano, coliseo, puerta de donde salen los peleadores, Titan vs Volt
clear_scene()

# Mundo / cielo dia romano
world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.53, 0.71, 0.84, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 24
bpy.context.scene.cycles.device = 'CPU'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.film_transparent = False

stone = make_mat('stone',(0.8,0.75,0.66),roughness=0.9)
stoneD = make_mat('stoneD',(0.66,0.61,0.5),roughness=0.9)
sand = make_mat('sand',(0.85,0.7,0.5),roughness=1.0)
red = make_mat('red',(0.6,0.11,0.11),roughness=0.7)
gold = make_mat('gold',(0.96,0.62,0.04),metallic=0.4,roughness=0.4)
groundM = make_mat('ground',(0.69,0.55,0.34),roughness=1.0)
leafM = make_mat('leaf',(0.18,0.32,0.2),roughness=0.9)
trunkM = make_mat('trunk',(0.36,0.27,0.21),roughness=0.9)

# Terreno romano exterior
bpy.ops.mesh.primitive_circle_add(vertices=48, radius=45, location=(0,0,-0.35))
g=bpy.context.active_object; g.name='terreno_romano'; g.data.materials.append(groundM)
bpy.ops.mesh.primitive_plane_add(size=36, location=(0,-22,-0.3))
road=bpy.context.active_object; road.name='calzada'; road.data.materials.append(make_mat('road',(0.6,0.54,0.44),roughness=1))

# Arena de arena
bpy.ops.mesh.primitive_cylinder_add(radius=9, depth=0.6, location=(0,0,0), vertices=48)
floor=bpy.context.active_object; floor.name='arena_arena'; floor.data.materials.append(sand)

# Muros del coliseo: segmentos de caja (NO cilindro solido, taparia la arena)
for i in range(24):
    a=i/24*math.pi*2
    x,y=math.cos(a)*12.2, math.sin(a)*12.2
    bpy.ops.mesh.primitive_cube_add(location=(x,y,1.1), size=1)
    seg=bpy.context.active_object; seg.name=f'muro_seg_{i}'; seg.scale=(2.8,1.2,2.2); seg.rotation_euler=(0,0,-a+math.pi/2); seg.data.materials.append(stoneD)
    bpy.ops.mesh.primitive_cube_add(location=(x,y,3.0), size=1)
    seg2=bpy.context.active_object; seg2.name=f'muro_sup_{i}'; seg2.scale=(2.8,1.2,1.6); seg2.rotation_euler=(0,0,-a+math.pi/2); seg2.data.materials.append(stone)
bpy.ops.mesh.primitive_torus_add(major_radius=13, minor_radius=0.35, location=(0,0,3.9))
top=bpy.context.active_object; top.name='anillo_sup'; top.data.materials.append(stone)

# Columnas + banners
for i in range(20):
    a=i/20*math.pi*2
    x,y=math.cos(a)*12.3, math.sin(a)*12.3
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=4.2, location=(x,y,2.1), vertices=12)
    c=bpy.context.active_object; c.name=f'columna_{i}'; c.data.materials.append(stone)
    if i%2==0:
        bpy.ops.mesh.primitive_plane_add(size=1.1, location=(x*0.97,y*0.97,2.4))
        b=bpy.context.active_object; b.name=f'banner_{i}'; b.data.materials.append(red)
        b.rotation_euler=(0,0,-a+math.pi/2)

# Puerta de donde salen los peleadores (fondo -Y)
bpy.ops.mesh.primitive_cube_add(location=(0,-11.8,1.8), size=1)
gate=bpy.context.active_object; gate.name='puerta'; gate.scale=(3.2,0.6,3.6); gate.data.materials.append(stoneD)
bpy.ops.mesh.primitive_cube_add(location=(0,-11.8,1.4), size=1)
hole=bpy.context.active_object; hole.name='puerta_oscura'; hole.scale=(2.2,0.7,2.8); hole.data.materials.append(make_mat('dark',(0.11,0.07,0.02),roughness=1))
bpy.ops.mesh.primitive_cube_add(location=(0,-11.8,3.8), size=1)
gt=bpy.context.active_object; gt.name='puerta_dorado'; gt.scale=(3.6,0.8,0.5); gt.data.materials.append(gold)

# Cipreses y montanas
for i in range(10):
    a=i/10*math.pi*2+0.3; r=18+ (i%3)*4
    x,y=math.cos(a)*r, math.sin(a)*r
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.6, location=(x,y,0.4), vertices=8)
    t=bpy.context.active_object; t.data.materials.append(trunkM)
    bpy.ops.mesh.primitive_cone_add(radius1=0.9, depth=3.6, location=(x,y,2.6), vertices=8)
    l=bpy.context.active_object; l.data.materials.append(leafM)
for i in range(4):
    a=i/4*math.pi*2+0.8
    bpy.ops.mesh.primitive_cone_add(radius1=8, depth=7, location=(math.cos(a)*38, math.sin(a)*38, 1.5), vertices=6)
    m=bpy.context.active_object; m.data.materials.append(make_mat('mtn',(0.48,0.42,0.33),roughness=1))

# Luces
bpy.ops.object.light_add(type='SUN', location=(8,4,14))
sun=bpy.context.active_object; sun.data.energy=4
bpy.ops.object.light_add(type='POINT', location=(-5,4,5))
pt=bpy.context.active_object; pt.data.energy=200; pt.data.color=(1,0.6,0.2)

# Peleadores: Titan azul vs Volt rojo SIN borrar el coliseo
_orig_clear = clear_scene
clear_scene = lambda: None  # build_robot no debe borrar el coliseo ya construido
build_robot((0.15,0.39,0.92),0.75,(0.22,0.74,0.97),'titan')
titan_arm = arm_obj
titan_arm.location.x = -3
build_robot((0.86,0.15,0.15),0.75,(1.0,0.42,0.0),'volt')
volt_arm = arm_obj
volt_arm.location.x = 3
clear_scene = _orig_clear
bpy.context.scene.frame_set(1)
print('COLISEO scene built, objects:', len(bpy.context.scene.objects))

# Camara con Track-To (apunta seguro al centro)
bpy.ops.object.empty_add(location=(0,0,1.2))
target=bpy.context.active_object; target.name='target_centro'
bpy.ops.object.camera_add(location=(0,17,8))
cam=bpy.context.active_object; cam.name='camara_coliseo'
bpy.context.scene.camera=cam
con=cam.constraints.new(type='TRACK_TO'); con.target=target; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'

bpy.context.scene.render.filepath='C:/Users/USUARIO/pelea-IA-VS/screenshots/coliseo-blender.png'
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='C:/Users/USUARIO/pelea-IA-VS/coliseo.blend')
print('DONE coliseo render + blend')
