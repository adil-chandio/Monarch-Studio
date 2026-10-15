"""Full-length OWN-CHARACTER 2.5D recreation of the confirmed main reference.

Photographic, image-based skeletal skinning with bounded motions, rigid facial
core/props, anchored boots, authored camera/effects and original reference audio.
NOT reconstructed 3D, natural AI performance, or exact reference choreography.
Reference VIDEO pixels are not read by the picture renderer. Other-chat chair
assets/outlines are not used. Images are new, reference-specific owner scenes.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

W,H,FPS,END=720,1280,30,1332
FF=imageio_ffmpeg.get_ffmpeg_exe()
cv2.setNumThreads(2)
X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
FONTS=Path('/usr/share/fonts/truetype/dejavu')


def sha(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
    return d.hexdigest()


def ease(v):
    q=np.clip(v,0,1);return q*q*(3-2*q)


def T(x,y):return np.array([[1.,0.,x],[0.,1.,y],[0.,0.,1.]])
def R(a):
    a=math.radians(a);c,s=math.cos(a),math.sin(a)
    return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])
def about(p,a=0.,shift=(0.,0.)):return T(p[0]+shift[0],p[1]+shift[1])@R(a)@T(-p[0],-p[1])
def point(m,p):return (m@np.r_[p,1.])[:2]


def bone_matrix(a,b,c,d):
    # Rigid rotation/translation only: no bone-length image scaling.
    a,b,c,d=map(lambda x:np.asarray(x,float),(a,b,c,d))
    v=b-a;u=d-c
    angle=math.degrees(math.atan2(u[1],u[0])-math.atan2(v[1],v[0]))
    return T(*c)@R(angle)@T(*(-a))


def ik(a,b,c,new_a,target):
    a,b,c,new_a,target=map(lambda x:np.asarray(x,float),(a,b,c,new_a,target))
    l1=np.linalg.norm(b-a);l2=np.linalg.norm(c-b)
    delta=target-new_a;distance=float(np.linalg.norm(delta));u=delta/max(distance,1e-8)
    length=np.clip(distance,abs(l1-l2)+1e-5,l1+l2-1e-5)
    tip=new_a+u*length
    along=(l1*l1-l2*l2+length*length)/(2*length)
    height=math.sqrt(max(0.,l1*l1-along*along));v=np.array([-u[1],u[0]])
    options=[new_a+u*along+v*height,new_a+u*along-v*height]
    guess=b+(new_a-a)*.5+(tip-c)*.5
    joint=min(options,key=lambda p:np.linalg.norm(p-guess))
    return bone_matrix(a,b,new_a,joint),bone_matrix(b,c,joint,tip),tip,float(np.linalg.norm(tip-target))


def distance(a,b):
    a=np.array(a,float);b=np.array(b,float);v=b-a
    u=np.clip(((X-a[0])*v[0]+(Y-a[1])*v[1])/(np.dot(v,v)+1e-8),0,1)
    return (X-a[0]-u*v[0])**2+(Y-a[1]-u*v[1])**2


def polygon(points):
    m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.int32(points)],255);return m


# All coordinates refer to NEW normalized source artwork, not reference-actor pixels.
HEAD=[(361,214),(395,222),(417,243),(425,272),(420,312),(409,349),(399,369),(393,380),(325,381),(317,359),(306,338),(300,310),(296,280),(304,248),(323,229)]
LOWER=[(464,745),(463,793),(463,863),(456,927),(465,1023),(462,1084),(453,1126),(462,1158),(480,1184),(481,1205),(456,1210),(429,1205),(418,1186),(410,1153),(405,1114),(397,1060),(391,981),(381,880),(369,774),(363,760),(357,798),(346,885),(336,981),(331,1068),(325,1133),(327,1162),(319,1191),(299,1206),(264,1211),(245,1205),(242,1192),(252,1170),(273,1130),(273,1091),(267,1048),(268,959),(265,923),(257,835),(250,753)]
P01=HEAD+[(410,378),(441,389),(481,402),(493,422),(499,482),(505,532),(519,582),(525,625),(525,714),(518,735),(519,757),(509,779),(489,795),(474,804),(465,800),(468,780),(477,749),(474,731)]+LOWER+[(223,739),(226,710),(233,668),(240,615),(242,544),(238,511),(223,529),(205,541),(184,544),(167,536),(159,519),(165,486),(181,443),(194,406),(206,390),(216,370),(217,341),(218,309),(226,293),(235,287),(239,306),(244,279),(254,277),(258,302),(264,280),(273,281),(276,290),(272,313),(279,291),(287,296),(285,316),(278,337),(293,330),(302,331),(298,342),(282,364),(276,374),(258,390),(249,400),(268,395),(303,383),(326,374)]
P02=HEAD+[(419,380),(454,388),(484,406),(499,438),(511,473),(528,499),(536,482),(545,455),(550,442),(544,420),(537,395),(533,377),(526,366),(529,359),(540,367),(549,389),(552,363),(558,335),(565,327),(573,330),(571,359),(577,327),(586,323),(594,325),(593,357),(601,334),(608,339),(608,352),(601,382),(612,359),(619,361),(620,372),(611,401),(602,427),(598,447),(599,460),(586,493),(570,533),(554,560),(537,577),(516,574),(491,557),(480,536),(481,595),(486,668),(499,738)]+LOWER+[(232,741),(240,686),(244,621),(242,541),(229,556),(209,571),(185,578),(170,575),(153,554),(141,528),(132,491),(129,464),(137,447),(135,431),(124,404),(115,379),(110,358),(115,348),(122,351),(130,376),(125,350),(124,333),(130,327),(138,329),(145,363),(141,333),(145,323),(153,322),(161,328),(166,359),(162,336),(169,330),(177,335),(180,366),(178,386),(190,372),(201,364),(206,370),(202,387),(190,409),(181,430),(180,449),(182,472),(193,499),(209,475),(220,440),(235,407),(266,394),(302,382),(325,375)]
P03=HEAD+[(417,378),(447,394),(470,408),(479,426),(481,475),(490,521),(495,565),(497,613),(507,667),(516,716),(514,750),(505,775),(489,789),(475,791),(473,777),(479,754),(480,743),(466,750),(468,800),(459,868),(454,945),(456,1041),(451,1079),(460,1109),(484,1129),(512,1147),(522,1164),(521,1180),(507,1186),(474,1182),(432,1172),(409,1161),(394,1146),(390,1113),(391,1072),(383,1012),(373,943),(367,856),(361,779),(350,793),(337,879),(329,954),(324,1057),(328,1116),(337,1151),(348,1182),(347,1202),(339,1217),(321,1225),(301,1222),(280,1212),(268,1190),(269,1164),(277,1127),(277,1069),(272,1021),(272,960),(276,907),(281,841),(288,769),(271,761),(253,760),(252,783),(238,797),(223,791),(214,777),(211,752),(203,730),(206,678),(205,631),(204,585),(212,541),(217,492),(221,444),(232,410),(264,396),(302,381),(322,373)]
PROP03=[(253,646),(306,652),(310,670),(303,702),(292,731),(279,744),(277,765),(289,769),(294,790),(290,819),(280,858),(272,904),(267,942),(266,975),(255,986),(249,1019),(239,1022),(236,1005),(220,989),(214,970),(220,949),(226,919),(225,890),(218,880),(211,861),(202,850),(202,828),(210,797),(222,779),(220,753),(239,740),(242,712)]
P04=[(0,832),(88,792),(160,758),(204,726),(195,694),(177,662),(166,626),(163,584),(156,550),(137,529),(126,501),(119,454),(119,410),(123,366),(138,323),(153,293),(174,264),(198,238),(234,215),(271,194),(310,175),(350,155),(390,146),(432,151),(464,169),(491,196),(519,228),(546,255),(571,294),(585,338),(592,384),(592,428),(589,472),(572,505),(558,527),(550,559),(537,602),(521,642),(502,678),(487,710),(502,744),(558,782),(629,817),(719,853),(719,1279),(0,1279)]
P05=[(164,188),(191,231),(221,294),(254,366),(284,437),(308,508),(334,578),(361,631),(399,635),(420,649),(403,683),(397,711),(427,733),(450,766),(479,815),(506,856),(554,894),(568,918),(614,934),(680,1009),(719,1070),(719,1279),(611,1279),(558,1200),(513,1129),(480,1069),(472,1037),(444,1015),(412,1004),(386,985),(353,971),(337,956),(330,935),(303,922),(294,904),(300,884),(291,865),(292,846),(302,829),(290,816),(289,795),(298,781),(296,755),(307,733),(324,720),(327,702),(314,689),(282,693),(278,680),(303,672),(295,643),(278,635),(264,595),(246,537),(225,472),(207,408),(192,347),(179,292),(169,237)]

# Trace the complete reflective prop silhouette; colour segmentation can erase
# silver blade highlights as if they were background.
P05=[(168,187),(190,213),(223,266),(251,322),(280,390),(312,456),(343,523),(367,574),(380,594),(385,600),(379,606),(391,624),(404,636),(412,633),(411,644),(401,661),(394,682),(395,699),(419,712),(444,733),(463,758),(477,790),(487,820),(520,852),(546,874),(559,894),(590,925),(606,932),(664,991),(719,1053),(719,1279),(615,1279),(575,1203),(541,1143),(498,1088),(477,1067),(468,1047),(470,1020),(469,998),(458,1002),(444,977),(424,967),(406,954),(379,957),(358,946),(344,930),(340,916),(316,909),(304,900),(298,886),(300,874),(294,866),(290,852),(292,837),(299,826),(292,816),(293,801),(300,788),(295,779),(296,765),(303,753),(300,742),(303,729),(313,716),(307,708),(316,698),(326,697),(310,690),(284,690),(279,684),(282,674),(303,677),(307,647),(291,640),(280,632),(280,616),(275,596),(264,559),(249,512),(235,465),(221,411),(210,372),(196,317),(183,267),(175,226)]

# Trace head-right -> body -> head-left, not a self-intersecting head loop.
P01=HEAD[:8]+P01[len(HEAD):]+HEAD[8:]
P02=HEAD[:8]+P02[len(HEAD):]+HEAD[8:]
P03=HEAD[:8]+P03[len(HEAD):]+HEAD[8:]

CONFIG={
 'raised':{'file':'01_RAISED_HAND.png','outline':P01,'head':(360,387),'face_box':(323,254,408,354),'root':(360,712),'neck':(360,393),
 'arms':{'L':[(280,418),(194,499),(230,392),(250,339)],'R':[(473,418),(493,564),(500,729),(491,770)]},
 'legs':{'L':[(311,719),(296,937),(294,1137),(282,1182)],'R':[(413,716),(419,946),(436,1137),(450,1186)]},
 'head_zone':(299,205,426,376),'feet':[(237,1130,337,1214),(399,1128,491,1215)]},
 'open':{'file':'02_OPEN_ARMS.png','outline':P02,'head':(360,387),'face_box':(323,254,408,354),'root':(360,712),'neck':(360,393),
 'arms':{'L':[(267,419),(188,533),(157,443),(157,384)],'R':[(467,417),(539,533),(576,448),(581,390)]},
 'legs':{'L':[(311,719),(296,937),(294,1137),(282,1182)],'R':[(413,716),(419,946),(436,1137),(450,1186)]},
 'head_zone':(299,205,426,376),'feet':[(237,1130,337,1214),(399,1128,491,1215)]},
 'red':{'file':'03_RED_ANGLE.png','outline':P03,'prop_outline':PROP03,'head':(361,384),'face_box':(320,249,407,352),'root':(371,703),'neck':(361,391),
 'arms':{'L':[(266,416),(232,574),(233,743),(239,774)],'R':[(464,421),(477,588),(493,736),(490,773)]},
 'legs':{'L':[(318,719),(301,927),(302,1125),(307,1190)],'R':[(407,713),(424,926),(425,1095),(459,1155)]},
 'head_zone':(297,206,426,374),'feet':[(259,1123,352,1226),(386,1094,530,1194)]},
 'close':{'file':'04_CLOSE_SMIRK.png','outline':P04,'head':(357,820),'face_box':(206,350,525,720),'root':(360,1190),'neck':(357,846),
 'arms':{},'legs':{},'head_zone':(110,132,601,812),'feet':[]},
 'blade':{'file':'05_BLADE_POV.png','outline':P05,'prop_only':True,'pivot':(507,938)},
}


class Rig:
    def __init__(self,name,root):
        self.name=name;self.c=CONFIG[name]
        rgb=ImageOps.fit(Image.open(root/'assets'/self.c['file']).convert('RGB'),(W,H),Image.Resampling.LANCZOS)
        self.image=cv2.cvtColor(np.array(rgb),cv2.COLOR_RGB2BGR)
        mask=polygon(self.c['outline'])
        self.prop=polygon(self.c['prop_outline']) if 'prop_outline' in self.c else np.zeros_like(mask)
        mask=cv2.max(mask,self.prop)
        # Conservative hand-authored outline, refined only within a small edge band.
        gc=np.zeros((H,W),np.uint8)
        expanded=cv2.dilate(mask,np.ones((31,31),np.uint8))
        eroded=cv2.erode(mask,np.ones((21,21),np.uint8))
        gc[expanded>0]=cv2.GC_PR_BGD;gc[mask>0]=cv2.GC_PR_FGD;gc[eroded>0]=cv2.GC_FGD
        if name=='raised':
            # Real negative space between the raised thumb and cheek/collar.
            # Keep it background rather than skinning a dark wall band as a digit.
            gap=polygon([(303,325),(315,330),(323,357),(321,374),(278,389),(270,381),(289,358),(302,343)])
            gc[gap>0]=cv2.GC_BGD
        if not self.c.get('prop_only'):
            try:
                cv2.grabCut(self.image,gc,None,np.zeros((1,65)),np.zeros((1,65)),2,cv2.GC_INIT_WITH_MASK)
                refined=np.uint8((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD))*255
                mask=cv2.bitwise_and(refined,expanded)
            except cv2.error:pass
        tip_boxes={
            'raised':[(225,282,243,319),(243,273,261,315),(260,271,278,317),(276,282,293,328)],
            'open':[(113,340,135,375),(129,322,149,362),(144,315,166,356),(163,327,184,371),
                    (551,326,573,370),(573,316,596,361),(593,327,612,377),(606,350,625,397)]
        }
        # Specular highlights on black glove tips can be misclassified as wall.
        # Repair only each digit's small convex cap, never connect whole fingers.
        for x0,y0,x1,y1 in tip_boxes.get(name,[]):
            roi=mask[y0:y1,x0:x1];ys,xs=np.nonzero(roi)
            if len(xs)>3:
                hull=cv2.convexHull(np.stack((xs,ys),axis=1).astype(np.int32))
                cv2.fillConvexPoly(roi,hull,255)
        self.mask=mask
        self.alpha=np.clip(cv2.distanceTransform(mask,cv2.DIST_L2,5)/1.8,0,1).astype(np.float32)
        removal_size=29 if self.c.get('prop_only') else 7
        removal=cv2.dilate(mask,np.ones((removal_size,removal_size),np.uint8))
        self.clean=cv2.inpaint(self.image,removal,4,cv2.INPAINT_TELEA).astype(np.float32)
        self.rigid_prop_image=None
        if name=='red':
            # The gun and gripping glove are a separate rigid layer. Never bend
            # them by mixing hand and thigh image-skinning weights.
            glove=polygon([(209,731),(245,727),(262,744),(282,765),(277,788),(250,802),(224,797),(211,781),(206,754)])
            self.prop=cv2.max(self.prop,glove)
            self.rigid_prop_image=self.image.copy()
            self.rigid_prop_alpha=self.alpha*np.clip(cv2.distanceTransform(self.prop,cv2.DIST_L2,5)/1.6,0,1)
            person_mask=cv2.bitwise_and(mask,polygon(P03))
            self.mask=person_mask
            self.alpha=np.clip(cv2.distanceTransform(person_mask,cv2.DIST_L2,5)/1.8,0,1).astype(np.float32)
            under=cv2.bitwise_and(cv2.dilate(self.prop,np.ones((5,5),np.uint8)),person_mask)
            self.image=cv2.inpaint(self.image,under,4,cv2.INPAINT_TELEA)
        if self.c.get('prop_only'):return
        c=self.c;rootp=c['root'];neck=c['neck']
        bones=[('root',(rootp[0]-55,rootp[1]),(rootp[0]+55,rootp[1]),70),
               ('spine',rootp,neck,75 if name!='close' else 200),
               ('head',c['head'],(c['head'][0],c['head'][1]-(140 if name!='close' else 520)),42 if name!='close' else 160)]
        for side,(a,b,w,h) in c['arms'].items():
            bones.extend([(f'upper.{side}',a,b,29),(f'fore.{side}',b,w,27),(f'hand.{side}',w,h,24)])
        for side,(a,b,w,h) in c['legs'].items():
            bones.extend([(f'thigh.{side}',a,b,38),(f'shin.{side}',b,w,31),(f'foot.{side}',w,h,26)])
        raw=[]
        for key,a,b,radius in bones:
            v=np.exp(-distance(a,b)/(2*radius**2)).astype(np.float32)
            if key=='head':v*=4
            raw.append(v)
        weights=np.stack(raw);weights/=np.maximum(weights.sum(axis=0),1e-8)
        self.names=[b[0] for b in bones];self.weights=dict(zip(self.names,weights))
        x0,y0,x1,y1=c['head_zone'];region=(X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1)
        # Facial core is rigid: no eye/mouth/cheek warps or breathing scale.
        for key in self.names:self.weights[key][region]=1. if key=='head' else 0.
        for side,box in zip(['L','R'],c['feet']):
            x0,y0,x1,y1=box;reg=(X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1)
            for key in self.names:self.weights[key][reg]=1. if key==f'foot.{side}' else 0.
        self.arm_alpha={}
        for side in c['arms']:
            weight=sum(self.weights[k] for k in [f'upper.{side}',f'fore.{side}',f'hand.{side}'])
            self.arm_alpha[side]=self.alpha*np.clip((weight-.18)/.58,0,1)

    def pose(self,t):
        c=self.c;small=.34 if self.name=='close' else 1.
        root=T(.9*math.sin(t*.71)*small,(2.0+.7*math.sin(t*1.22))*small)
        spine=root@about(c['root'],a=.48*math.sin(t*.83)*small)
        head=spine@about(c['head'],a=(-1.35*math.sin(t*.55)+.35*math.sin(t*1.23))*small)
        m={'root':root,'spine':spine,'head':head};residual=0.
        for side,(a,b,w,h) in c['arms'].items():
            aa=point(spine,a);base=point(spine,w)
            if self.name=='raised' and side=='L':shift=np.array([3.2*math.sin(t*1.19),-3.0*math.sin(t*.97)])
            elif self.name=='open':shift=np.array([(1 if side=='R' else -1)*4*math.sin(t*1.1),-4*math.sin(t*.8+.4)])
            else:shift=np.array([.35*math.sin(t),.30*math.sin(t*.8)])
            target=base+shift
            upper,fore,tip,error=ik(a,b,w,aa,target);residual=max(residual,error)
            m[f'upper.{side}']=upper;m[f'fore.{side}']=fore
            grip_angle=.50*math.sin(t*1.2) if self.name!='red' else .10*math.sin(t)
            m[f'hand.{side}']=about(w,a=grip_angle,shift=tip-np.asarray(w))
        for side,(a,b,w,h) in c['legs'].items():
            upper,shin,tip,error=ik(a,b,w,point(root,a),w);residual=max(residual,error)
            m[f'thigh.{side}']=upper;m[f'shin.{side}']=shin;m[f'foot.{side}']=np.eye(3)
        return m,residual

    def render(self,t,metrics=False):
        if self.c.get('prop_only'):
            angle=11*math.sin(t*1.15)-3.5*math.sin(t*2.1)
            m=about(self.c['pivot'],a=angle,shift=(3*math.sin(t*.9),-5*math.sin(t*1.1)))
            actor=cv2.warpAffine(self.image,m[:2],(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32)
            alpha=cv2.warpAffine(self.alpha,m[:2],(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            return actor,alpha,{'kind':'rigid_prop_layer','max_anchor_error_px':0.}
        transforms,error=self.pose(t);dx=np.zeros((H,W),np.float32);dy=dx.copy()
        for key,m in transforms.items():
            q=self.weights[key]
            dx+=q*((m[0,0]-1)*X+m[0,1]*Y+m[0,2])
            dy+=q*(m[1,0]*X+(m[1,1]-1)*Y+m[1,2])
        mx=X-dx;my=Y-dy
        for _ in range(3):
            mx2=X-cv2.remap(dx,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
            my2=Y-cv2.remap(dy,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
            mx,my=mx2,my2
        actor=cv2.remap(self.image,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32)
        alpha=cv2.remap(self.alpha,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        if self.rigid_prop_image is not None:
            pm=transforms['hand.L'][:2]
            prop_rgb=cv2.warpAffine(self.rigid_prop_image,pm,(W,H),flags=cv2.INTER_LINEAR).astype(np.float32)
            pa=cv2.warpAffine(self.rigid_prop_alpha,pm,(W,H),flags=cv2.INTER_LINEAR)
            combined=alpha+pa*(1-alpha)
            premul=actor*alpha[:,:,None]*(1-pa[:,:,None])+prop_rgb*pa[:,:,None]
            actor=premul/np.maximum(combined[:,:,None],1e-6);alpha=combined
        info={'kind':'bounded_skeletal_image_skinning','max_anchor_error_px':round(error,6),
              'max_displacement_px':round(float(np.max(np.hypot(dx[self.mask>0],dy[self.mask>0]))),5)}
        if metrics:
            gyx,gxx=np.gradient(mx);gyy,gxy=np.gradient(my);det=gxx*gyy-gyx*gxy
            info['min_inverse_jacobian']=float(det[self.mask>0].min())
            x0,y0,x1,y1=self.c['face_box'];core=det[y0:y1,x0:x1]
            info['face_det_error']=float(np.max(np.abs(core-1)))
            info['bone_scale_error']=max(float(np.max(np.abs(np.linalg.svd(m[:2,:2])[1]-1))) for m in transforms.values())
        return actor,alpha,info


# Authored coverage/cut plan follows the reference's major phases and pulses.
# It is a 2.5D recreation, not a claim that every source camera/pose is replicated.
SHOTS=[
 (0,272,'room',1.03,-6,6),(272,298,'raised',1.02,0,-4),(298,322,'raised',1.12,-4,4),
 (322,356,'raised',1.64,3,-3),(356,394,'raised',1.21,-6,6),(394,428,'open',1.08,0,0),
 (428,461,'open',1.10,-4,4),(461,492,'open',1.50,4,-4),(492,517,'red',1.20,-16,-8),
 (517,540,'red',1.52,-15,5),(540,558,'red',1.85,-23,7),(558,578,'raised',1.2,5,-6),
 (578,607,'red',1.13,8,-5),(607,633,'red',1.12,-10,8),(633,661,'red',1.12,9,-4),
 (661,684,'red',1.30,-5,6),(684,698,'wide',1.18,-7,6),(698,730,'red',1.10,-10,6),
 (730,755,'red',1.44,7,-4),(755,780,'red',1.1,-9,7),(780,802,'close',1.03,-7,6),
 (802,826,'red',1.24,14,-7),(826,853,'wide',1.21,5,-7),(853,883,'red',1.02,-3,3),
 (883,900,'open',1.06,0,0),(900,966,'blade',1.03,-5,9),(966,991,'red',1.17,-5,5),
 (991,1013,'red',1.28,12,-6),(1013,1038,'red',1.1,-6,7),(1038,1067,'red',1.23,13,-8),
 (1067,1092,'close',1.03,-4,4),(1092,1111,'raised',1.2,5,-3),
 (1111,1133,'close',1.06,176,7),(1133,1158,'red',1.12,17,7),
 (1158,1182,'close',1.10,-3,3),(1182,1224,'logo',1.,0,0),(1224,1332,'outro',1.,0,0)]
assert SHOTS[0][0]==0 and SHOTS[-1][1]==END
assert all(a[1]==b[0] for a,b in zip(SHOTS,SHOTS[1:]))


def branding():
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    f=ImageFont.truetype(str(FONTS/'DejaVuSans.ttf'),12)
    d.text((W-141,31),'MONARCH STUDIO',font=f,fill=(230,230,230,135))
    return np.asarray(im)[:,:,:3][:,:,::-1].astype(np.float32),np.asarray(im)[:,:,3:4].astype(np.float32)/255


def method_label():
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    f=ImageFont.truetype(str(FONTS/'DejaVuSans.ttf'),14)
    text='2.5D  /  RIGGED CHARACTER RECREATION'
    d.text(((W-d.textlength(text,font=f))/2,H-66),text,font=f,fill=(211,216,220,220))
    a=np.asarray(im);return a[:,:,:3][:,:,::-1].astype(np.float32),a[:,:,3:4].astype(np.float32)/255


class Film:
    def __init__(self,root,metrics_csv,outro=None):
        self.root=root;self.rigs={n:Rig(n,root) for n in CONFIG}
        self.room=cv2.cvtColor(np.asarray(ImageOps.fit(Image.open(root/'assets/00_ROOM.png').convert('RGB'),(W,H),Image.Resampling.LANCZOS)),cv2.COLOR_RGB2BGR).astype(np.float32)
        self.metrics_sha256=sha(metrics_csv)
        rows=list(csv.DictReader(Path(metrics_csv).open()))
        self.luma=np.array([float(r['mean_luma']) for r in rows]);self.delta=np.array([float(r['mean_abs_luma_change']) for r in rows]);assert len(rows)==END
        self.local_mean=np.convolve(np.pad(self.luma,(10,10),mode='edge'),np.ones(21)/21,mode='valid')
        rng=np.random.default_rng(116)
        self.particles=[(rng.uniform(0,W),rng.uniform(0,H),rng.uniform(.5,2.),rng.uniform(6,24),rng.uniform(.5,1.8)) for _ in range(34)]
        self.mark,self.mark_a=branding();self.label,self.label_a=method_label()
        self.outro=[]
        if outro:
            reader=imageio_ffmpeg.read_frames(str(outro),pix_fmt='rgb24',output_params=['-vf',f'scale={W}:{H}']);next(reader)
            self.outro=[np.frombuffer(b,np.uint8).reshape(H,W,3)[:,:,::-1].copy() for b in reader]
            assert len(self.outro)==108
        self.vignette=np.clip(1-.28*((X-W/2)/(W*.6))**2-.08*((Y-H/2)/(H*.63))**2,.42,1)[:,:,None]

    def shot_for(self,index):return next(s for s in SHOTS if s[0]<=index<s[1])

    def scene(self,index,metrics=False):
        t=index/FPS;s=self.shot_for(index);start,end,name,z,roll,travel=s
        u=(index-start)/max(1,end-start-1);info={'frame':index,'scene':name}
        if name=='outro':return self.outro[index-1224].copy(),info
        if name=='logo':
            # A new graphic prelude in the reference's creator-logo interval.
            if self.outro:base=self.outro[52].astype(np.float32)
            else:base=np.zeros((H,W,3),np.float32)
            grey=cv2.cvtColor(np.uint8(base),cv2.COLOR_BGR2GRAY)
            base=np.repeat(grey[:,:,None],3,axis=2).astype(np.float32)
            reveal=float(ease(u*3));base*=reveal
            if index in (1183,1184,1202,1204):base=255-base
            if index>=1217:base*=float(ease((1224-index)/7))
            return np.uint8(np.clip(base,0,255)),info
        if name=='room':
            f=self.room.copy()
            # Distant light/parallax variation only, not claimed as actor movement.
            parallax=1.1*math.sin(t*.46)*(1-ease((Y-560)/480))
            f=cv2.remap(f,X+parallax,Y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
            anchor=(360,650)
        elif name=='wide':
            rig=self.rigs['red'];actor,alpha,ri=rig.render(t,metrics);info.update(ri);f=self.room.copy()
            scale=.165;mat=np.array([[scale,0,360-scale*365],[0,scale,730-scale*1208]],np.float32)
            ac=cv2.warpAffine(actor,mat,(W,H));aa=cv2.warpAffine(alpha,mat,(W,H))[:,:,None]
            shadow=np.zeros((H,W),np.float32);cv2.ellipse(shadow,(360,733),(25,4),0,0,360,.38,-1)
            shadow=cv2.GaussianBlur(shadow,(0,0),4);f*=1-shadow[:,:,None]
            f=f*(1-aa)+ac*.72*aa;anchor=(360,680)
        else:
            rig=self.rigs[name];actor,alpha,ri=rig.render(t,metrics);info.update(ri);f=rig.clean.copy()
            if name=='open' and 394<=index<492:
                # Intentional arm echoes, separate from the two real source arms.
                strength=.17*(.65+.35*math.sin(t*6)**2)
                for side in ['L','R']:
                    aa,bb,ww,hh=[np.array(p,float) for p in rig.c['arms'][side]]
                    length1=np.linalg.norm(bb-aa);length2=np.linalg.norm(ww-bb)
                    for k,tilt in enumerate([-32,0,32]):
                        angle=-90+tilt+(4*math.sin(t*1.4+k))
                        if side=='R':angle=-180-angle
                        direction=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))])
                        eb=aa+direction*length1;ew=eb+direction*length2
                        eh=ew+direction*np.linalg.norm(hh-ww)
                        mats=[bone_matrix(aa,bb,aa,eb),bone_matrix(bb,ww,eb,ew),bone_matrix(ww,hh,ew,eh)]
                        keys=[f'upper.{side}',f'fore.{side}',f'hand.{side}']
                        total=sum(rig.weights[key] for key in keys)+1e-7
                        for key,mat in zip(keys,mats):
                            part=rig.arm_alpha[side]*rig.weights[key]/total
                            ghost=245-cv2.warpAffine(rig.image.astype(np.float32),mat[:2],(W,H))*.45
                            ga=cv2.warpAffine(part,mat[:2],(W,H))[:,:,None]*strength
                            f=f*(1-ga)+ghost*ga
            a=alpha[:,:,None];f=f*(1-a)+actor*a
            anchor=(360,550) if z>1.40 and name in ('raised','open','red') else (360,650)
            if name=='close':anchor=(360,630)
            if name=='blade':anchor=(400,700)
        # Authored camera roll/push follows the reference's coverage family.
        scale=z*(1+.045*float(ease(u)))
        if name=='room':scale=1.03+.25*float(ease(t/9.07))
        angle=roll+travel*float(ease(u))+.3*math.sin(t*1.4)
        if name=='room':angle=-7+11*math.sin(t*.36)
        m=cv2.getRotationMatrix2D(anchor,angle,scale)
        m[0,2]+=1.5*math.sin(t*3.2);m[1,2]+=.9*math.sin(t*2.7)
        f=cv2.warpAffine(f,m,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        # Reference-driven light pulse timing; bounded levels keep faces readable.
        gray=cv2.cvtColor(np.uint8(np.clip(f,0,255)),cv2.COLOR_BGR2GRAY).astype(np.float32)
        if index<492:
            sat=.09 if index>=272 else .28;f=gray[:,:,None]*(1-sat)+f*sat
        else:
            f[:,:,2]*=1.05;f[:,:,0]*=.94
        gain=np.clip((self.luma[index]+17)/(self.local_mean[index]+17),.67,1.38)
        base=.48 if name=='room' else (.84 if index<492 else .92)
        f*=float(gain*base)
        impulse=max(0.,(self.luma[index]-self.local_mean[index]-12)/100)
        f+=min(.22,impulse)*95
        # Small atmosphere and camera-transient accents, never body warp fields.
        dust=np.zeros((H,W),np.float32)
        face_center=None
        if name in ('raised','open','red','close'):
            box=self.rigs[name].c['face_box'];fc=np.array([(box[0]+box[2])/2,(box[1]+box[3])/2,1.])
            face_center=m@fc;face_radius=max(box[2]-box[0],box[3]-box[1])*.8*scale
        for px,py,depth,speed,radius in self.particles:
            xx=int((px+8*math.sin(t*.3+depth))%W);yy=int((py-t*speed)%H)
            if face_center is not None and np.linalg.norm(np.array([xx,yy])-face_center)<face_radius:continue
            cv2.circle(dust,(xx,yy),max(1,int(radius)),5.,-1,cv2.LINE_AA)
        f+=cv2.GaussianBlur(dust,(0,0),.55)[:,:,None]
        if index>=492 and self.delta[index]>28:
            band_y=(index*73)%H;h=2+(index%4)
            f[band_y:band_y+h]=np.roll(f[band_y:band_y+h],(index%9)-4,axis=1)
        f*=self.vignette
        # The tiny own-brand mark replaces rather than copies source creator branding.
        f=f*(1-self.mark_a)+self.mark*self.mark_a
        if index<75:
            opacity=float(ease(index/10)*ease((75-index)/15));a=self.label_a*opacity
            f=f*(1-a)+self.label*a
        if index<6:f*=float(ease(index/6))
        return np.uint8(np.clip(f,0,255)),info


def fingerprint(root,outro):
    return {'method':'whole-character photographic rigged 2.5D; not natural 3D performance',
            'width':W,'height':H,'fps':FPS,'frames':END,'renderer_sha256':sha(__file__),
            'images':{p.name:sha(p) for p in sorted((root/'assets').glob('*.png'))},
            'outro_sha256':sha(outro)}


def preview(film,work):
    work.mkdir(parents=True,exist_ok=True)
    for name,rig in film.rigs.items():
        cv2.imwrite(str(work/(name+'_matte.png')),np.uint8(rig.alpha*255))
        actor,a,info=rig.render(3.7,True)
        raw=np.uint8(np.clip(rig.clean*(1-a[:,:,None])+actor*a[:,:,None],0,255))
        cv2.imwrite(str(work/(name+'_ungraded.jpg')),raw)
        (work/(name+'_metrics.json')).write_text(json.dumps(info,indent=2)+'\n')
    times=[1,8.5,9.7,11.3,13.7,15.2,17.3,20.5,23,26.3,30.8,34.1,37.2,38.9,40.,42.]
    for page in range(2):
        board=Image.new('RGB',(1080,1000),'#10171d');d=ImageDraw.Draw(board)
        for j,t in enumerate(times[page*8:(page+1)*8]):
            i=min(END-1,round(t*FPS));f,info=film.scene(i,True)
            rgb=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));rgb.save(work/f'frame_{i:04d}.jpg',quality=95)
            pic=rgb.resize((265,471),Image.Resampling.LANCZOS);x=j%4*270;y=j//4*500
            board.paste(pic,(x,y+24));d.text((x+6,y+5),f'{i/FPS:.3f}s | {info["scene"]}',fill='white')
        board.save(work/f'FILM_REVIEW_{page}.jpg',quality=93)
    print('PRIVATE_FULL_TIMELINE_PREVIEW_READY',flush=True)


def render(film,root,work,output,outro):
    work.mkdir(parents=True,exist_ok=True);chunks=work/'chunks';chunks.mkdir(exist_ok=True)
    expected=fingerprint(root,outro);expected['reference_metrics_sha256']=film.metrics_sha256;cfg=work/'render_settings.json'
    if cfg.exists() and json.loads(cfg.read_text())!=expected:raise RuntimeError('Stale rigged render cache; choose a new work directory.')
    cfg.write_text(json.dumps(expected,indent=2)+'\n')
    logs=[];started=time.monotonic()
    for n,shot in enumerate(SHOTS):
        start,end,name,*_=shot;dest=chunks/f'shot_{n:02d}.mp4';receipt=dest.with_suffix('.json')
        if dest.exists() and receipt.exists():
            prior=json.loads(receipt.read_text())
            if prior.get('sha256')==sha(dest) and prior.get('frames')==end-start:
                print('REUSE_SHOT',n,name,flush=True);logs.append(prior);continue
        tmp=dest.with_name(dest.stem+'.partial.mp4')
        enc=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}',
            '-r',str(FPS),'-i','pipe:0','-an','-frames:v',str(end-start),'-c:v','libx264','-threads','2',
            '-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)],stdin=subprocess.PIPE)
        shot_metrics=[];t0=time.monotonic()
        try:
            for i in range(start,end):
                f,info=film.scene(i,metrics=(i%30==0 or i in (start,end-1)))
                enc.stdin.write(f.tobytes())
                if 'min_inverse_jacobian' in info:shot_metrics.append(info)
            enc.stdin.close();code=enc.wait()
            if code:raise RuntimeError('Shot encoding failed: '+str(n))
        except BaseException:
            enc.kill();enc.wait();raise
        got,secs=imageio_ffmpeg.count_frames_and_secs(str(tmp));assert got==end-start,(n,got,end-start)
        os.replace(tmp,dest)
        row={'shot':n,'scene':name,'in_frame':start,'out_frame_exclusive':end,'frames':got,'sha256':sha(dest),
             'seconds':secs,'render_seconds':round(time.monotonic()-t0,2),'sampled_rig_metrics':shot_metrics}
        receipt.write_text(json.dumps(row,indent=2)+'\n');logs.append(row)
        (work/'progress.json').write_text(json.dumps({'shots_complete':len(logs),'total_shots':len(SHOTS),'last_frame':end-1}))
        print('SHOT_COMPLETE',n,name,end-start,'frames',round(time.monotonic()-t0,1),'s',flush=True)
    concat=work/'concat.txt';concat.write_text(''.join("file '"+str((chunks/f'shot_{j:02d}.mp4').resolve())+"'\n" for j in range(len(SHOTS))))
    output.parent.mkdir(parents=True,exist_ok=True);temp=output.with_name(output.stem+'.partial.mp4')
    subprocess.run([FF,'-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c:v','copy','-an','-movflags','+faststart',str(temp)],check=True)
    frames,seconds=imageio_ffmpeg.count_frames_and_secs(str(temp));assert frames==END and abs(seconds-44.4)<.034,(frames,seconds)
    os.replace(temp,output)
    report={'status':'complete_full_length_2_5d_picture_only','file':str(output),'sha256':sha(output),
            'frames':frames,'fps':FPS,'seconds':seconds,'width':W,'height':H,'shots':logs,
            'method':'image-based bounded skeletal skinning / rigid props / authored camera and effects',
            'image_space_skinning_used':True,'face_expression_morphing':False,'head_pose_kind':'rigid 2D tilt, no fabricated yaw',
            'reference_actor_video_pixels_used':False,'new_whole_character_source_images':True,
            'natural_ai_performance':False,'reconstructed_3d_human':False,'pixel_perfect_choreography_claimed':False,
            'reference_timing_scope':'Major phase/cut family and measured light-pulse timing; not every source pose/camera trajectory.',
            'total_render_seconds':round(time.monotonic()-started,2),'audio_pending_reference_conform':True,'settings':expected}
    (work/'PICTURE_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('COMPLETE_2_5D_PICTURE',output,frames,seconds,flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--metrics',type=Path,required=True);p.add_argument('--outro',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--preview',action='store_true');a=p.parse_args()
    film=Film(a.root,a.metrics,a.outro)
    if a.preview:preview(film,a.work)
    else:
        if not a.output:raise ValueError('--output required')
        render(film,a.root,a.work,a.output,a.outro)


if __name__=='__main__':main()
