"""MONARCH / THE VAULT — an original joint-driven 3D motion proof.

No old photographic scene plates. No 2D warps, squash/stretch, optical flow,
frame interpolation, or photo-camera zoom used as body movement.
The identity-only head is recovered from the user's measured face surface.
Everything else here (set, outfit, skeleton, hands, performance, crown) is new.

Usage (Blender 4.2.22 Python module):
  python build_vault.py --identity-root /path/to/private/source --output scene.blend
"""
from __future__ import annotations
import argparse
import json
import math
import random
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

import identity_head as identity
from motion_math import targets, two_bone, ease

FPS = 24
PERFORMANCE_FRAMES = 120
CROWN_FRAMES = 48
RIG = None
MATS = {}
PI = math.pi


def mat(name, rgb, metal=0., rough=.5, emission=0.):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emission:
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m


def texture(m, scale=140, strength=.16, distance=.0005):
    nodes=m.node_tree.nodes; links=m.node_tree.links
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=2
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength
    bump.inputs['Distance'].default_value=distance
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
    return m


def mesh(name, verts, faces, material, smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    for p in data.polygons:p.use_smooth=smooth
    return obj


def cube(name, p, dims, material, bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod=obj.modifiers.new('Finished edges','BEVEL');mod.width=bevel;mod.segments=3
        obj.modifiers.new('Planar normals','WEIGHTED_NORMAL')
    return obj


def sphere(name, p, radii, material, seg=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=p)
    obj=bpy.context.object;obj.name=name
    obj.scale=radii;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(material)
    for f in obj.data.polygons:f.use_smooth=True
    return obj


def curve(name, points, material, radius=.0012):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius
    data.bevel_resolution=2;data.resolution_u=10
    s=data.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for point,p in zip(s.bezier_points,points):
        point.co=p;point.handle_left_type='AUTO';point.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    data.materials.append(material);return obj


def parent_bone(obj, bone):
    bpy.context.view_layer.update();world=obj.matrix_world.copy()
    obj.parent=RIG;obj.parent_type='BONE';obj.parent_bone=bone
    bpy.context.view_layer.update();obj.matrix_world=world
    obj['attached_joint']=bone
    return obj


def skin(obj, weight_function):
    groups={}
    for v in obj.data.vertices:
        weights=weight_function(obj.matrix_world @ v.co)
        total=sum(weights.values())
        for bone,w in weights.items():
            if w<1e-8:continue
            if bone not in groups:groups[bone]=obj.vertex_groups.new(name=bone)
            groups[bone].add([v.index],w/total,'REPLACE')
    mod=obj.modifiers.new('Anatomical skinning / unit bone scale','ARMATURE');mod.object=RIG
    mod.use_deform_preserve_volume=True
    # A skinned mesh must share the armature's world-space root motion.
    # Without this parent, root translation cancels inside modifier space,
    # while bone-parented shoes still travel: the observed floating cuffs.
    world=obj.matrix_world.copy();obj.parent=RIG;obj.matrix_world=world
    return obj


def torso_weights(p):
    if p.z<1.04:return {'pelvis':1}
    if p.z<1.24:
        w=ease((p.z-1.04)/.20);return {'pelvis':1-w,'spine':w}
    w=ease((p.z-1.24)/.18);return {'spine':1-w,'chest':w}


def tube(name, sections, material, segments=32, vertical=False, wrinkles=0., caps=True):
    verts=[];faces=[]
    for i,(p,rx,ry) in enumerate(sections):
        p=Vector(p)
        if vertical:u,v=Vector((1,0,0)),Vector((0,1,0))
        else:
            delta=Vector(sections[min(i+1,len(sections)-1)][0])-Vector(sections[max(i-1,0)][0])
            delta.normalize();u=delta.cross(Vector((0,1,0))).normalized();v=delta.cross(u).normalized()
        for j in range(segments):
            angle=2*PI*j/segments
            fold=wrinkles*(.64*math.sin(8*angle+i*1.9)+.36*math.sin(13*angle-i*.7))
            verts.append(tuple(p+u*((rx+fold)*math.cos(angle))+v*((ry+fold)*math.sin(angle))))
    for i in range(len(sections)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    if caps:
        faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(sections)-1)*segments+j for j in range(segments))])
    obj=mesh(name,verts,faces,material)
    sub=obj.modifiers.new('Cloth surface resolution','SUBSURF');sub.levels=1;sub.render_levels=1
    return obj


def create_rig():
    data=bpy.data.armatures.new('MONARCH / standing anatomical rig')
    obj=bpy.data.objects.new('MONARCH_SKELETON',data);bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    specs=[('pelvis',(0,0,.94),(0,0,1.075),None),
           ('spine',(0,0,1.075),(0,0,1.32),'pelvis'),
           ('chest',(0,0,1.32),(0,0,1.50),'spine'),
           ('neck',(0,0,1.50),(0,0,1.565),'chest'),
           ('head',(0,0,1.565),(0,0,1.80),'neck')]
    for side,s in [('L',-1),('R',1)]:
        specs.extend([
            (f'upper.{side}',(s*.208,0,1.476),(s*.310,0,1.205),'chest'),
            (f'forearm.{side}',(s*.310,0,1.205),(s*.340,-.020,.948),f'upper.{side}'),
            (f'hand.{side}',(s*.340,-.020,.948),(s*.344,-.022,.871),f'forearm.{side}'),
            (f'thigh.{side}',(s*.100,0,.940),(s*.103,-.050,.515),'pelvis'),
            (f'shin.{side}',(s*.103,-.050,.515),(s*.105,0,.095),f'thigh.{side}'),
            (f'foot.{side}',(s*.105,0,.095),(s*.105,-.19,.065),f'shin.{side}'),
        ])
        for d in range(4):
            x=s*.344+(d-1.5)*.015
            length=[.066,.080,.074,.058][d]
            p0=(x,-.022,.888)
            p1=(x,-.025,.888-length*.46)
            p2=(x,-.030,.888-length*.78)
            p3=(x,-.034,.888-length)
            for k,(a,b) in enumerate([(p0,p1),(p1,p2),(p2,p3)]):
                specs.append((f'finger.{side}.{d}.{k}',a,b,f'hand.{side}' if k==0 else f'finger.{side}.{d}.{k-1}'))
        specs.append((f'thumb.{side}',(s*.322,-.018,.921),(s*.302,-.044,.880),f'hand.{side}'))
    for name,head,tail,parent in specs:
        bone=data.edit_bones.new(name);bone.head=head;bone.tail=tail
        if parent:bone.parent=data.edit_bones[parent]
        bone.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT');obj.select_set(False);obj.show_in_front=True
    for p in obj.pose.bones:p.rotation_mode='QUATERNION'
    obj['bone_scale_policy']='Never animate scale; all scales remain (1,1,1).'
    return obj


def garment():
    suit=MATS['suit'];shirt=MATS['shirt'];seam=MATS['seam'];skinmat=MATS['skin']
    sections=[((0,0,.88),.177,.113),((0,0,.945),.181,.115),((0,0,1.03),.170,.114),
              ((0,0,1.14),.158,.107),((0,.003,1.27),.174,.114),
              ((0,0,1.39),.201,.116),((0,.006,1.465),.209,.093),
              ((0,.010,1.502),.088,.065)]
    base=tube('Black cotton shirt / anatomical torso',sections,shirt,48,True,wrinkles=.0009)
    skin(base,torso_weights)
    # A real open-front shell rather than a texture pretending to be a blazer.
    vertices=[];faces=[];rings=48
    for i,((cx,cy,z),rx,ry) in enumerate(sections):
        gap=[.03,.035,.045,.045,.18,.41,.57,.75][min(i,7)]
        for j in range(rings+1):
            a=gap+(2*PI-2*gap)*j/rings
            wr=.0011*math.sin(9*a+i*.6)
            vertices.append((cx+(rx+.007+wr)*math.sin(a),cy-(ry+.008+wr)*math.cos(a),z))
    for i in range(len(sections)-1):
        for j in range(rings):
            a=i*(rings+1)+j;faces.append((a,a+1,a+rings+2,a+rings+1))
    jacket=mesh('New tailored charcoal blazer / open front',vertices,faces,suit)
    skin(jacket,torso_weights)
    solid=jacket.modifiers.new('Wool shell thickness','SOLIDIFY');solid.thickness=.004
    sub=jacket.modifiers.new('Tailoring smoothness','SUBSURF');sub.levels=1;sub.render_levels=1
    for side,s in [('L',-1),('R',1)]:
        verts=[(s*.070,-.055,1.505),(s*.151,-.096,1.447),(s*.112,-.123,1.414),
               (s*.148,-.128,1.374),(s*.038,-.121,1.150),(s*.052,-.128,1.290)]
        lapel=mesh('Notch lapel '+side,verts,[(0,1,2,5),(2,3,4,5)],MATS['lapel'],False)
        skin(lapel,torso_weights)
        so=lapel.modifiers.new('Folded lapel thickness','SOLIDIFY');so.thickness=.004
        be=lapel.modifiers.new('Rolled lapel edge','BEVEL');be.width=.003;be.segments=3
        parent_bone(curve('Lapel edge stitch '+side,[verts[0],verts[5],verts[4]],seam,.00075),'chest')
        # Continuous shoulder drape covers the torso/upper-sleeve seam.
        cap=mesh('Sewn shoulder bridge '+side,
            [(s*.065,-.055,1.505),(s*.073,.066,1.508),
             (s*.224,.065,1.468),(s*.224,-.073,1.465),
             (s*.246,-.058,1.427),(s*.244,.061,1.426),
             (s*.171,-.113,1.408),(s*.171,.108,1.406)],
            [(0,1,2,3),(3,2,5,4),(0,3,4,6),(1,7,5,2)],suit)
        def shoulder_weights(p,side=side):
            w=.75*ease((abs(p.x)-.120)/.115)
            return {'chest':1-w,f'upper.{side}':w}
        skin(cap,shoulder_weights)
        so=cap.modifiers.new('Shoulder cloth thickness','SOLIDIFY');so.thickness=.006
        # Shirt collar flaps and dark center placket, in actual depth.
        collar=mesh('Open shirt collar '+side,[(s*.057,-.039,1.534),(s*.077,-.084,1.476),(s*.035,-.111,1.423),(s*.029,-.049,1.507)],[(0,1,2,3)],shirt,False)
        skin(collar,torso_weights)
        mod=collar.modifiers.new('Cotton collar thickness','SOLIDIFY');mod.thickness=.002
        parent_bone(cube('Hip pocket flap '+side,(s*.123,-.105,1.006),(.090,.009,.025),suit,.004),'pelvis')
        parent_bone(curve('Hip pocket seam '+side,[(s*.17,-.103,1.023),(s*.126,-.120,1.023),(s*.079,-.109,1.023)],seam,.0008),'pelvis')
        sleeve=tube('Single skinned sleeve '+side,[
            ((s*.177,.002,1.450),.076,.091),((s*.212,.002,1.430),.075,.081),((s*.240,.002,1.398),.068,.073),
            ((s*.274,.000,1.331),.061,.065),((s*.305,-.003,1.247),.056,.059),
            ((s*.311,-.002,1.205),.053,.055),((s*.319,-.009,1.150),.049,.052),
            ((s*.327,-.013,1.073),.044,.047),((s*.338,-.019,.966),.035,.036),((s*.339,-.020,.954),.035,.035),((s*.339,-.020,.950),.035,.035)],suit,40,wrinkles=.0022,caps=False)
        def arm_weights(p,side=side):
            elbow=ease((1.27-p.z)/.14);shoulder=ease((1.50-p.z)/.095)
            return {'chest':1-shoulder,f'upper.{side}':shoulder*(1-elbow),f'forearm.{side}':shoulder*elbow}
        skin(sleeve,arm_weights)
        cuff=tube('Black shirt cuff '+side,[((s*.338,-.019,.970),.034,.035),((s*.340,-.020,.944),.033,.034)],shirt,32)
        parent_bone(cuff,f'forearm.{side}')
        for k in range(3):
            parent_bone(sphere('Sleeve button '+side,(s*.373,-.018,.987+k*.015),(.003,.006,.006),MATS['button'],12,8),f'forearm.{side}')
        hand(side,s)
        pants=tube('Continuous wool trousers '+side,[
            ((s*.099,.000,1.020),.102,.099),((s*.103,.002,.937),.101,.105),
            ((s*.102,-.015,.834),.094,.094),((s*.104,-.038,.671),.078,.081),
            ((s*.103,-.050,.534),.067,.070),((s*.104,-.044,.468),.065,.066),
            ((s*.105,-.030,.348),.058,.057),((s*.105,-.013,.217),.048,.045),
            ((s*.105,-.002,.137),.046,.047),((s*.105,-.001,.106),.047,.047),((s*.105,-.001,.100),.047,.047)],suit,40,wrinkles=.0025,caps=False)
        def leg_weights(p,side=side):
            h=ease((.96-p.z)/.085);k=ease((.590-p.z)/.15)
            return {'pelvis':1-h,f'thigh.{side}':h*(1-k),f'shin.{side}':h*k}
        skin(pants,leg_weights)
        shoe=sphere('Calf-leather derby '+side,(s*.106,-.070,.087),(.065,.146,.057),MATS['shoe'],40,24)
        parent_bone(shoe,f'foot.{side}')
        parent_bone(cube('Stitched leather outsole '+side,(s*.106,-.067,.033),(.129,.279,.037),MATS['rubber'],.026),f'foot.{side}')
        parent_bone(cube('Stacked derby heel '+side,(s*.106,.024,.022),(.105,.081,.039),MATS['shoe'],.010),f'foot.{side}')
        for k in range(4):
            yy=-.018-k*.018
            parent_bone(curve('Lace '+side,[(s*.106-.028,yy,.134),(s*.106,yy-.008,.143),(s*.106+.028,yy,.134)],MATS['seam'],.0016),f'foot.{side}')
    parent_bone(curve('Breast welt',[(.074,-.124,1.353),(.159,-.115,1.365)],seam,.0022),'chest')
    for z in [1.124,1.059]:
        button=sphere('Horn jacket button',(.023,-.131,z),(.009,.003,.009),MATS['button'],20,12)
        parent_bone(button,'pelvis' if z<1.1 else 'spine')


def hand(side,s):
    sk=MATS['skin']
    palm=sphere('Anatomical palm '+side,(s*.342,-.020,.909),(.036,.020,.047),sk,32,20)
    parent_bone(palm,f'hand.{side}')
    for d in range(4):
        for k in range(3):
            bone=RIG.data.bones[f'finger.{side}.{d}.{k}']
            a,b=bone.head_local,bone.tail_local;r=.0074*(1-.13*k)
            seg=tube(f'Digit {side} {d}/{k}',[(tuple(a),r,r*.93),(tuple(a.lerp(b,.50)),r,r*.98),(tuple(b),r*.9,r*.85)],sk,16)
            parent_bone(seg,bone.name)
            parent_bone(sphere('Finger joint '+side,tuple(a),(r,r,r),sk,16,10),bone.name)
            if k==2:
                nail=sphere('Fingernail '+side,tuple(a.lerp(b,.7)+Vector((0,-.006,0))),(.0051,.0013,.007),MATS['nail'],16,10)
                parent_bone(nail,bone.name)
    bone=RIG.data.bones[f'thumb.{side}'];a,b=bone.head_local,bone.tail_local
    thumb=tube('Thumb '+side,[(tuple(a),.011,.012),(tuple(a.lerp(b,.5)),.010,.010),(tuple(b),.008,.008)],sk,20)
    parent_bone(thumb,bone.name)
    parent_bone(sphere('Thumb tip '+side,tuple(b),(.008,.008,.010),sk,16,10),bone.name)


def area(name,pos,target,watts,rgb,size,size_y=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=watts;d.color=rgb;d.size=size
    if size_y:d.shape='RECTANGLE';d.size_y=size_y
    obj=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj


def cylinder(name,pos,radius,depth,material,axis_y=False,vertices=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    obj=bpy.context.object;obj.name=name
    if axis_y:obj.rotation_euler.x=PI/2
    obj.data.materials.append(material)
    be=obj.modifiers.new('Precision metal bevel','BEVEL');be.width=.008;be.segments=3
    obj.modifiers.new('Machined normals','WEIGHTED_NORMAL')
    return obj


def ring(name,center,radius,width,depth,material,segments=128):
    verts=[];faces=[]
    for y in [-depth/2,depth/2]:
        for r in [radius-width/2,radius+width/2]:
            for j in range(segments):
                a=j*2*PI/segments
                verts.append((center[0]+r*math.cos(a),center[1]+y,center[2]+r*math.sin(a)))
    for j in range(segments):
        k=(j+1)%segments
        faces.extend([(j,k,segments+k,segments+j),(segments+j,segments+k,3*segments+k,3*segments+j),
                      (2*segments+j,2*segments+k,k,j),(3*segments+j,3*segments+k,2*segments+k,2*segments+j)])
    obj=mesh(name,verts,faces,material,False)
    be=obj.modifiers.new('Machined ring edges','BEVEL');be.width=.005;be.segments=2
    obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return obj


def vault_set():
    floor=MATS['floor'];wall=MATS['wall'];metal=MATS['metal'];accent=MATS['red']
    cube('Concrete foundation',(0,-.25,-.075),(8,9,.14),wall,.01)
    for x in range(-5,6):
        for y in range(-5,5):
            tile=cube('Wet slate tile',(x*.71,y*.71,-.003),(.700,.700,.028),floor,.005)
    cube('Vault back wall',(0,1.73,1.65),(6,.26,3.4),wall,.02)
    for x in [-2.4,2.4]:cube('Heavy concrete pier',(x,.40,1.64),(.38,2.55,3.4),wall,.022)
    cube('Coarse ceiling',(0,.2,3.28),(5.2,3.7,.20),wall,.02)
    cylinder('Solid vault door',(0,1.53,1.27),1.205,.15,metal,True)
    ring('Heavy rim',(0,1.395,1.27),1.165,.080,.14,MATS['bezel'])
    ring('Inner dark seal',(0,1.375,1.27),.865,.040,.065,MATS['rubber'])
    ring('Brushed inner ring',(0,1.353,1.27),.83,.045,.04,MATS['metal'])
    for j in range(16):
        a=j*2*PI/16;rad=.996
        ob=cube('Vault radial locking lug',(rad*math.sin(a),1.33,1.27+rad*math.cos(a)),(.130,.078,.264),MATS['metal'],.012)
        ob.rotation_euler.y=a
        for dr in [-.067,.067]:
            pos=((rad+dr)*math.sin(a),1.278,1.27+(rad+dr)*math.cos(a))
            cylinder('Recessed fastener',pos,.010,.009,MATS['button'],True,12)
    for x in [-1.67,1.67]:
        cube('Low red practical channel',(x,1.345,.133),(1.005,.061,.039),MATS['rubber'],.008)
        cube('Low red luminous tube',(x,1.308,.133),(.918,.013,.017),accent,.008)
        area('Red floor bounce',(x,1.12,.16),(x,.05,.02),26,(1,.019,.007),.8,.08)
    cube('Overhead practical housing',(0,.58,3.09),(1.63,.19,.105),MATS['rubber'],.016)
    cube('Overhead opal source',(0,.558,3.029),(1.48,.126,.009),MATS['white'],.012)
    area('Soft warm overhead',(-.35,-.90,3.10),(0,-.03,1.18),65,(1,.83,.68),1.50,1.1)
    area('Face-neutral key',(-1.80,-2.15,2.45),(0,0,1.35),55,(1,.91,.80),1.55)
    area('Cool rim',(1.23,.56,2.18),(0,-.03,1.30),50,(.38,.59,1),.90,1.60)
    area('Quiet frontal fill',(1.30,-2.65,1.30),(0,0,1.20),9,(.62,.80,1),2.0)
    # Low object count, no atmospheric post-warp, no screen-space glow.


def setup_scene(scene,width=540,samples=12):
    scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=samples;scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.08
    scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2
    scene.cycles.glossy_bounces=3;scene.cycles.transmission_bounces=2
    scene.cycles.use_light_tree=True
    scene.render.resolution_x=width;scene.render.resolution_y=round(width*16/9)
    scene.render.resolution_percentage=100;scene.render.fps=FPS
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.use_persistent_data=True
    scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new(scene.name+' / atmosphere');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.032,.044,.061,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.035
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.65
    scene['native_frames_only']=True
    scene['image_warp']=False


def camera(name,pos,look,lens=54):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(look)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens;data.sensor_fit='VERTICAL';data.sensor_height=36
    data.dof.use_dof=False
    return obj


def set_bone_pose(name,head,tail):
    p=RIG.pose.bones[name];rest=RIG.data.bones[name]
    direction=Vector(tail)-Vector(head)
    q=(rest.tail_local-rest.head_local).normalized().rotation_difference(direction.normalized())
    rot=q.to_matrix() @ rest.matrix_local.to_3x3()
    M=rot.to_4x4();M.translation=Vector(head)
    p.matrix=M


def animate(scene):
    audit=[]
    for f in range(1,PERFORMANCE_FRAMES+1):
        scene.frame_set(f);t=(f-1)/FPS;tar=targets(t)
        root=tar['root'];RIG.location=root
        RIG.keyframe_insert('location',frame=f)
        breath=.0020*math.sin(2*PI*t/3.8)
        for name,angles in [('pelvis',(0,.012*math.sin(PI*tar['left_step']),0)),
                            ('spine',(.012+breath,0,.025*tar['adjust'])),
                            ('chest',(-.020*tar['adjust'],0,-.045*tar['adjust'])),
                            ('neck',(0,0,0)),('head',(.018*tar['adjust'],0,tar['head_yaw']))]:
            from mathutils import Euler
            p=RIG.pose.bones[name];p.rotation_quaternion=Euler(angles,'XYZ').to_quaternion()
            p.location=(0,0,0);p.scale=(1,1,1)
        bpy.context.view_layer.update()
        frameaudit={'frame':f,'time':t,'root':list(root),'joint_targets':{},'residuals':{}}
        for side,s in [('L',-1),('R',1)]:
            for limb,b1,b2,tip,pole in [
                ('leg',f'thigh.{side}',f'shin.{side}',tar['feet'][side]-root,np.array([s*.10,-.65,.55])),
                ('arm',f'upper.{side}',f'forearm.{side}',tar['hands'][side]-root,np.array([s*(.35+.16*tar['adjust']),.08-.19*tar['adjust'],1.22]))]:
                a=RIG.pose.bones[b1].head.copy()
                j,end,error=two_bone(a,tip,RIG.data.bones[b1].length,RIG.data.bones[b2].length,pole)
                set_bone_pose(b1,a,j);bpy.context.view_layer.update()
                set_bone_pose(b2,j,end);bpy.context.view_layer.update()
                frameaudit['residuals'][limb+'.'+side]=error
                if limb=='leg':
                    pitch=.13*math.sin(PI*tar['left_step']) if side=='L' else 0
                    delta=Vector((0,-.19,-.030));delta.rotate(Quaternion((1,0,0),pitch))
                    set_bone_pose(f'foot.{side}',end,Vector(end)+delta)
                    frameaudit['joint_targets']['ankle.'+side]=list(np.asarray(end)+root)
                else:
                    # Both hands rotate as rigid anatomical chains; no skin/image squashing.
                    blend=tar['adjust']
                    direction=Vector((s*.004,-.002,-.077)).lerp(Vector((.077 if side=='L' else -.065,-.010,-.008)),blend)
                    direction.normalize();direction*=RIG.data.bones[f'hand.{side}'].length
                    set_bone_pose(f'hand.{side}',end,Vector(end)+direction)
                    frameaudit['joint_targets']['wrist.'+side]=list(np.asarray(end)+root)
            bpy.context.view_layer.update()
            for d in range(4):
                for k in range(3):
                    p=RIG.pose.bones[f'finger.{side}.{d}.{k}']
                    curl=.08+.21*tar['adjust']+(k*.07)*tar['adjust']
                    p.rotation_quaternion=Quaternion((1,0,0),curl)
            RIG.pose.bones[f'thumb.{side}'].rotation_quaternion=Quaternion((0,1,0),s*.10*tar['adjust'])
        for p in RIG.pose.bones:
            p.keyframe_insert('location',frame=f);p.keyframe_insert('rotation_quaternion',frame=f)
            # Scale is neither keyed nor used as a substitute for motion.
        bpy.context.view_layer.update()
        frameaudit['bone_scales']={p.name:list(p.scale) for p in RIG.pose.bones}
        audit.append(frameaudit)
    for action in bpy.data.actions:
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
    scene.frame_set(1)
    return audit


def text_obj(name,string,location,size,material,spacing=1.0):
    d=bpy.data.curves.new(name,'FONT');d.body=string;d.align_x='CENTER';d.size=size
    d.space_character=spacing;d.extrude=.004;d.bevel_depth=.0015;d.bevel_resolution=2
    font=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    if font.exists():d.font=bpy.data.fonts.load(str(font))
    obj=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(obj)
    obj.location=location;obj.rotation_euler=(PI/2,0,0);d.materials.append(material)
    return obj


def crown_scene(width,samples):
    scene=bpy.data.scenes.new('02 / MONARCH STUDIO / CROWN');bpy.context.window.scene=scene
    setup_scene(scene,width,samples);scene.frame_end=CROWN_FRAMES
    gold=mat('Warm satin 24k gold',(.64,.385,.085),metal=.88,rough=.22)
    dark=mat('Midnight basalt',(.009,.013,.019),rough=.59)
    cube('End-card monolith',(0,.64,1.14),(5,.20,4),dark,.02)
    pivot=bpy.data.objects.new('Crown turntable',None);bpy.context.collection.objects.link(pivot);pivot.location=(0,0,1.47)
    vertices=[];faces=[];n=120
    for inside in [False,True]:
        radius=.327 if not inside else .304
        for top in [False,True]:
            for j in range(n):
                a=2*PI*j/n
                tooth=(.5+.5*math.cos(a*7))**1.40
                z=.040+(.090+.135*tooth if top else 0)
                vertices.append((radius*math.sin(a),radius*math.cos(a),z))
    for j in range(n):
        k=(j+1)%n
        faces.extend([(j,k,n+k,n+j),(2*n+j,3*n+j,3*n+k,2*n+k),
                      (n+j,n+k,3*n+k,3*n+j),(j,2*n+j,2*n+k,k)])
    crown=mesh('Seven-point original crown',vertices,faces,gold)
    crown.parent=pivot
    be=crown.modifiers.new('Polished crown edges','BEVEL');be.width=.004;be.segments=3
    for z in [.042,.072]:
        pts=[(.329*math.sin(j*2*PI/64),.329*math.cos(j*2*PI/64),z) for j in range(65)]
        band=curve('Crown rolled rim',pts,gold,.007);band.parent=pivot
    for j in range(7):
        a=j*2*PI/7
        jewel=sphere('Crown peak gold orb',(.327*math.sin(a),.327*math.cos(a),.274),(.016,.016,.016),gold,20,12)
        jewel.parent=pivot
    text_obj('Brand / MONARCH','MONARCH',(0,-.035,1.137),.225,gold,1.16)
    text_obj('Brand / STUDIO','STUDIO',(0,-.035,.912),.145,gold,1.68)
    curve('Brand underline',[(-.40,-.039,.828),(.40,-.039,.828)],gold,.0015)
    scene.camera=camera('Crown camera',(0,-3.75,1.39),(0,0,1.33),61)
    area('Gold key',(-1.35,-1.5,2.4),(0,0,1.5),85,(1,.86,.60),1.45)
    area('Soft cool card rim',(1.0,.1,2.12),(0,0,1.5),70,(.57,.75,1),1.10)
    area('Lettering fill',(0,-1.8,.9),(0,0,1.1),12,(1,.94,.78),1.3)
    for f in range(1,CROWN_FRAMES+1):
        u=(f-1)/(CROWN_FRAMES-1)
        pivot.rotation_euler.z=math.radians(-12+24*ease(u))
        pivot.location.z=1.47+.014*math.sin(PI*u)
        pivot.keyframe_insert('rotation_euler',frame=f);pivot.keyframe_insert('location',frame=f)
    return scene


def main():
    global RIG,MATS
    p=argparse.ArgumentParser();p.add_argument('--identity-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--width',type=int,default=540)
    p.add_argument('--samples',type=int,default=12);a=p.parse_args()
    random.seed(294);bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.name='01 / THE VAULT / FIXED-CAMERA MOTION'
    setup_scene(scene,a.width,a.samples);scene.frame_end=PERFORMANCE_FRAMES
    MATS={
        'suit':texture(mat('Charcoal woven wool',(.019,.022,.026),rough=.76),230,.18,.00034),
        'lapel':texture(mat('Tailored lapel wool',(.024,.027,.032),rough=.69),250,.13,.00025),
        'shirt':texture(mat('Black open collar cotton',(.008,.010,.013),rough=.85),220,.12,.00025),
        'seam':mat('Tonal charcoal stitch',(.038,.041,.046),rough=.79),
        'skin':texture(mat('Hands warm skin',(.28,.135,.074),rough=.63),120,.04,.0003),
        'nail':mat('Natural fingernails',(.50,.32,.235),rough=.45),
        'button':mat('Polished horn buttons',(.012,.015,.018),metal=.17,rough=.3),
        'shoe':texture(mat('Black calf leather',(.012,.014,.016),rough=.29),190,.08,.00022),
        'rubber':mat('Dark seals and sole rubber',(.008,.010,.012),rough=.76),
        'wall':texture(mat('Cast anthracite concrete',(.064,.070,.076),rough=.89),35,.30,.006),
        'floor':texture(mat('Damp slate',(.059,.066,.073),rough=.24),21,.20,.002),
        'metal':texture(mat('Brushed vault steel',(.061,.067,.071),metal=.65,rough=.43),115,.06,.0003),
        'bezel':mat('Vault rim tungsten',(.105,.094,.081),metal=.70,rough=.39),
        'red':mat('Crimson practical light',(1,.012,.006),emission=3.5),
        'white':mat('Warm overhead opal',(1,.88,.70),emission=3),
    }
    RIG=create_rig();garment();identity.make_head(RIG,a.identity_root,1.64)
    vault_set();scene.camera=camera('Fixed proof camera',(.45,-3.85,1.29),(0,-.045,1.10),54)
    scene['camera_policy']='Completely fixed camera for the whole five-second body proof.'
    scene['identity_status']='Approximate capture-derived head, not a measured full head scan or user-approved final.'
    scene['shot_provenance']='New set, new outfit, new rig, new motion. Identity surface only derived from the original personal capture.'
    audit=animate(scene)
    end=crown_scene(a.width,a.samples)
    bpy.context.window.scene=scene;scene.frame_set(1)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    for font in bpy.data.fonts:
        if font.filepath and font.filepath != '<builtin>' and not font.packed_file:
            try:font.pack()
            except RuntimeError:pass
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()),compress=True)
    report={'scene_file':a.output.name,'fps':FPS,'performance_frames':PERFORMANCE_FRAMES,
            'crown_frames':CROWN_FRAMES,'width':a.width,'height':round(a.width*16/9),'samples':a.samples,
            'bone_count':len(RIG.data.bones),'skinned_mesh_count':sum(any(m.type=='ARMATURE' for m in o.modifiers) for o in scene.objects),
            'no_scene_plates':True,'no_image_space_warps':True,'no_interpolation':True,
            'likeness_review':'pending; approximate head texture/geometry','animation':audit}
    (a.output.parent/'motion_audit.json').write_text(json.dumps(report,indent=2))
    print('SCENE_READY',a.output, 'bones',len(RIG.data.bones),flush=True)


if __name__=='__main__':main()
