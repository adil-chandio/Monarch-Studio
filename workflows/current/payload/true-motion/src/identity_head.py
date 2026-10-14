"""Identity-only surface/groom adapter.

Recovered from the user's MONARCH_CHAOS_3D_SOURCE.zip, not a scene/plate.
Uses their measured 468-vertex face and real captured UV texture; approximate,
not an exact head scan. The room, body, clothes, rig and performance are new.
"""
import math
import random
from pathlib import Path
import bpy
from mathutils import Vector
PI = math.pi
ROOT = None
RIG = None
HEAD_Z = 1.64
SKIN = HAIR = HAIR_SHEEN = None

def material(name, color, metallic=0, rough=.5, emission=None):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1)
        p.inputs['Emission Strength'].default_value=emission
        m.cycles.emission_sampling='NONE'
    return m

def textured(m,scale=90, strength=.12, distance=.001, detail=3):
    n=m.node_tree.nodes;l=m.node_tree.links
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=detail
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=distance
    l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
    return m

def mesh(name,verts,faces,mat=None,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    if mat:me.materials.append(mat)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    return o

def uv_sphere(name,loc,scale,mat,seg=32,rings=20):
    verts=[];faces=[]
    for i in range(rings+1):
        phi=PI*i/rings
        for j in range(seg):
            a=2*PI*j/seg
            verts.append((scale[0]*math.sin(phi)*math.cos(a),scale[1]*math.sin(phi)*math.sin(a),scale[2]*math.cos(phi)))
    for i in range(rings):
        for j in range(seg):
            k=i*seg+j; q=i*seg+(j+1)%seg
            faces.append((k,q,q+seg,k+seg))
    o=mesh(name,verts,faces,mat);o.location=loc;return o

def path_curve(name,points,radius,mat,radii=None,poly=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=10
    c.bevel_depth=radius;c.bevel_resolution=3;c.resolution_u=10
    if poly:
        s=c.splines.new('POLY');s.points.add(len(points)-1)
        for i,p in enumerate(points):
            s.points[i].co=(*p,1)
            if radii:s.points[i].radius=radii[i]
    else:
        s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
        for i,p in enumerate(points):
            b=s.bezier_points[i];b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
            if radii:b.radius=radii[i]
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(mat);return o

def strands(name,lines,mat,radius):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=4;c.bevel_resolution=1;c.bevel_depth=radius
    for line in lines:
        s=c.splines.new('POLY');s.points.add(len(line)-1)
        for j,xyz in enumerate(line):
            s.points[j].co=(*xyz,1);s.points[j].radius=max(.06,(1-j/len(line))**.6)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(mat);return o

def bind(o,bone):
    # Bone-parent meshes and curves with their rest-world transform preserved.
    bpy.context.view_layer.update();m=o.matrix_world.copy()
    o.parent=RIG;o.parent_type='BONE';o.parent_bone=bone
    bpy.context.view_layer.update();o.matrix_world=m
    return o

def build_face(data):
    texpath=ROOT/'work/character'/data['albedo']
    m=material('Captured face albedo · actual reference',(.48,.29,.21),rough=.62)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(texpath));t.image.pack();t.interpolation='Linear'
    mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[2].default_value=(.43,.42,.40,1)
    l.new(t.outputs['Color'],mul.inputs[1]);l.new(mul.outputs[0],p.inputs['Base Color'])
    p.inputs['Subsurface Weight'].default_value=.045;p.inputs['Subsurface Scale'].default_value=.002;p.inputs['Subsurface Radius'].default_value=(.9,.35,.2)
    p.inputs['Specular IOR Level'].default_value=.27
    textured(m,160,.065,.0004)
    verts=[(x,y,z+HEAD_Z) for x,y,z in data['vertices']]
    o=mesh('FACE · 468 measured landmarks, subdivided surface',verts,data['triangles'],m)
    uv=o.data.uv_layers.new(name='Reference UV')
    for poly in o.data.polygons:
        for li in poly.loop_indices:uv.data[li].uv=data['uv'][o.data.loops[li].vertex_index]
    sub=o.modifiers.new('Facial surface smoothing','SUBSURF');sub.levels=2;sub.render_levels=2
    bind(o,'head')
    # Closed cranial back; never a flat face card.
    oval=[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
    ext=[];ev=[];ef=[];euvs=[]
    for i in oval:
        x,y,z=data['vertices'][i]
        lift=.032*max(0,min(1,(z-.025)/.071))**1.2
        ext.append((x,y+.026*lift/.032,z+lift))
        ev.append((x,y,z+HEAD_Z));euvs.append(data['uv'][i])
    albedo_height=bpy.data.images.get('face_albedo.png').size[1]
    pixels_per_meter=data['face_height_pixels']/.195
    for i,(x,y,z) in zip(oval,ext):
        lift=z-data['vertices'][i][2]
        ev.append((x,y,z+HEAD_Z));euvs.append([data['uv'][i][0],data['uv'][i][1]+lift*pixels_per_meter/albedo_height])
    for j in range(len(oval)):
        k=(j+1)%len(oval)
        ef.append((j,k,len(oval)+k,len(oval)+j))
    fore=mesh('Measured forehead continuation',ev,ef,m)
    layer=fore.data.uv_layers.new(name='Reference UV')
    for poly in fore.data.polygons:
        for li in poly.loop_indices:layer.data[li].uv=euvs[fore.data.loops[li].vertex_index]
    bind(fore,'head')
    cv=[];cf=[];count=len(oval)
    for j in range(13):
        a=j/12*PI/2
        for x,y,z in ext:
            cv.append((x*math.cos(a),y*math.cos(a)+.094*math.sin(a),HEAD_Z+.009+(z-.009)*math.cos(a)))
    for j in range(12):
        for i in range(count):cf.append((j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i))
    skull=mesh('Closed cranial volume',cv,cf,SKIN);bind(skull,'head')
    bind(uv_sphere('Neck',(0,.017,HEAD_Z-.114),(.051,.052,.064),SKIN),'head')
    # The supplied eye appearance is mapped to curved eye surfaces, preserving
    # aperture/iris proportions instead of inventing large cartoon eyeballs.
    eye_loops=[('L',[33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]),
               ('R',[263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466])]
    for side,loop in eye_loops:
        rim=[Vector(verts[i]) for i in loop]
        center=sum(rim,Vector())/len(rim);center.y-=.0018
        eye=mesh('Captured curved eye '+side,[tuple(v) for v in rim]+[tuple(center)],
                 [(j,(j+1)%len(loop),len(loop)) for j in range(len(loop))],m)
        euv=eye.data.uv_layers.new(name='Reference UV')
        coords=[data['uv'][i] for i in loop]
        coords.append([sum(v[k] for v in coords)/len(coords) for k in range(2)])
        for poly in eye.data.polygons:
            for li in poly.loop_indices:euv.data[li].uv=coords[eye.data.loops[li].vertex_index]
        bind(eye,'head')
    # Shallow closed mouth cavity behind the captured lips.
    mouth=material('Mouth interior',(.018,.002,.003),rough=.75)
    mp=Vector(verts[13]);mp.y+=.004
    bind(uv_sphere('Mouth aperture',mp,(.023,.004,.003),mouth),'head')
    # Ear geometry with separate helix and concha.
    earshade=material('Ear concha',(.22,.107,.063),rough=.7)
    for s in [-1,1]:
        ear=(s*.083,.006,HEAD_Z-.019)
        bind(uv_sphere('Ear',ear,(.011,.013,.025),SKIN),'head')
        bind(uv_sphere('Ear inner concha',(s*.091,-.003,HEAD_Z-.018),(.0035,.009,.016),earshade),'head')
        pts=[(s*(.087+.007*math.cos(a)),.002+.011*math.sin(a),HEAD_Z-.016+.022*math.cos(a)) for a in [2*PI*j/24 for j in range(25)]]
        bind(path_curve('Ear helix',pts,.002,SKIN,poly=True),'head')
    return o

def build_hair(face_data):
    # Scalp and groom: an asymmetric swept part, modelled from the supplied side views.
    v=[];f=[];seg=80;rings=22
    for i in range(rings+1):
        for j in range(seg):
            a=2*PI*j/seg
            front=max(0,-math.sin(a))
            maxphi=2.12-1.14*front
            phi=maxphi*i/rings
            sweep=.007*math.sin(a*2+phi*3)*math.sin(phi)
            x=.092*math.sin(phi)*math.cos(a)+sweep
            y=.016+.101*math.sin(phi)*math.sin(a)
            z=HEAD_Z+.060+.096*math.cos(phi)+.006*math.cos(a*3)*math.sin(phi)
            v.append((x,y,z))
    for i in range(rings):
        for j in range(seg):f.append((i*seg+j,i*seg+(j+1)%seg,(i+1)*seg+(j+1)%seg,(i+1)*seg+j))
    bind(mesh('Sculpted hair volume · swept part',v,f,HAIR),'head')
    lines=[]
    # Hundreds of actual hair curves along the scalp, not an image alpha card.
    for i in range(620):
        a=random.uniform(0,2*PI);front=max(0,-math.sin(a));maxphi=2.12-1.14*front
        start=random.uniform(.10,.40);end=random.uniform(maxphi*.7,maxphi)
        line=[]
        for j in range(9):
            u=j/8;phi=start+(end-start)*u
            theta=a+.2*math.sin(u*PI)*(-1 if math.cos(a)<0 else 1)
            rr=.0015+random.uniform(0,.0006)
            line.append(((.092+rr)*math.sin(phi)*math.cos(theta)+.007*math.sin(theta*2+phi*3)*math.sin(phi),
                         .016+(.101+rr)*math.sin(phi)*math.sin(theta),
                         HEAD_Z+.060+(.097+rr)*math.cos(phi)+.006*math.cos(theta*3)*math.sin(phi)))
        lines.append(line)
    bind(strands('Groom · scalp strands',lines,HAIR_SHEEN,.00032),'head')
    # Forehead curtains, asymmetrical as in the reference.
    for s in [-1,1]:
        lines=[]
        for i in range(110):
            off=random.uniform(-.010,.010); depth=random.uniform(-.006,.006)
            start=Vector((.012+off,-.025+depth,HEAD_Z+.157))
            mid1=Vector((s*.05+off,-.088+depth,HEAD_Z+.155))
            mid2=Vector((s*.092+off*.4,-.073+depth,HEAD_Z+.098))
            end=Vector((s*.087+off*.5,-.040+depth,HEAD_Z+(.012 if s<0 else .039)+random.uniform(-.015,.015)))
            line=[]
            for j in range(15):
                u=j/14;p=(1-u)**3*start+3*(1-u)**2*u*mid1+3*(1-u)*u*u*mid2+u**3*end
                line.append(tuple(p))
            lines.append(line)
        bind(strands('Swept fringe '+str(s),lines,HAIR_SHEEN,.0008),'head')
    # Sparse beard groom from the dark lower-face pixels, preserving the captured outline.
    from PIL import Image
    import numpy as np
    img=np.asarray(Image.open(ROOT/'work/character/face_albedo.png').convert('RGB'))
    verts=[Vector((x,y,z+HEAD_Z)) for x,y,z in face_data['vertices']]
    uvs=face_data['uv'];lines=[]
    triangles=face_data['triangles']
    for _ in range(4500):
        tri=random.choice(triangles);a,b,c=[verts[i] for i in tri]
        r1,r2=random.random(),random.random()
        if r1+r2>1:r1,r2=1-r1,1-r2
        p=a*(1-r1-r2)+b*r1+c*r2
        if p.z>HEAD_Z-.014 or abs(p.x)<.025 and p.z>HEAD_Z-.071:continue
        uv=[uvs[tri[0]][k]*(1-r1-r2)+uvs[tri[1]][k]*r1+uvs[tri[2]][k]*r2 for k in range(2)]
        px=min(img.shape[1]-1,max(0,int(uv[0]*img.shape[1])));py=min(img.shape[0]-1,max(0,int((1-uv[1])*img.shape[0])))
        col=img[py,px].astype(float)
        if col.mean()>112:continue
        normal=(b-a).cross(c-a).normalized()
        if normal.y>0:normal=-normal
        end=p+normal*random.uniform(.0014,.0038)+Vector((0,0,-.0018))
        lines.append([tuple(p),tuple((p+end)/2+normal*.0006),tuple(end)])
    bind(strands('Reference-shaped beard fibers',lines,HAIR,.00009),'head')

def make_head(rig, source_root, head_z=1.64):
    import json
    global RIG, ROOT, HEAD_Z, SKIN, HAIR, HAIR_SHEEN
    RIG=rig; ROOT=Path(source_root); HEAD_Z=head_z
    random.seed(1457)
    data=json.loads((ROOT/'work/character/face_mesh.json').read_text())
    SKIN=material('Identity / warm skin',(.28,.135,.074),rough=.60)
    p=SKIN.node_tree.nodes.get('Principled BSDF')
    p.inputs['Subsurface Weight'].default_value=.055
    p.inputs['Subsurface Scale'].default_value=.002
    p.inputs['Specular IOR Level'].default_value=.23
    HAIR=material('Identity / black hair',(.005,.0035,.0025),rough=.44)
    textured(HAIR,450,.08,.00012)
    HAIR_SHEEN=material('Identity / groom highlights',(.009,.006,.004),rough=.40)
    head=build_face(data)
    build_hair(data)
    return head
