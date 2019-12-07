#!/bin/sh
# -*- coding: utf-8 -*-

import sys
#sys.path.insert( 0, '.' )

import wx.glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

#from PIL import Image
#try: from PIL import ImageGrab # WINDOWS only
#except: pass

import datetime
import copy

from numpy import *
try:
    from scipy.interpolate import splprep,splev
except: pass

#import multiprocessing


import lib
import const

class GLCanvas(wx.glcanvas.GLCanvas):
    """ Open GLcanvas
    
    :param obj parent: parent object ('View_Frm' class instance in FU)
    :param obj draw: instance of MolDraw class
    """
    def __init__(self,parent,draw,*args,**kwargs):
        attribList = (wx.glcanvas.WX_GL_RGBA, # RGBA
                      wx.glcanvas.WX_GL_DOUBLEBUFFER, # Double Buffered
                      wx.glcanvas.WX_GL_DEPTH_SIZE, 24) # 32 bit ... does not work on Debian7.8
        super(GLCanvas, self).__init__(parent,attribList=attribList,*args,**kwargs)
        #       
        self.draw=draw
        
        self.popup=False
        # canvas event handlers
        self.mdlwin=parent
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        ###self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnEraseBG)
        self.Bind(wx.EVT_SET_FOCUS,self.OnFocus)
        self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnterWindow)
        #self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeaveWindow)
        # mouse event handlers
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        self.Bind(wx.EVT_RIGHT_UP,self.OnMouseRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnMouseLeftDClick)
        # keyboard event handlers
        self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)   
        self.Bind(wx.EVT_KEY_UP,self.OnKeyUp)
    
    def OnFocus(self,event):
        """ Focus event handler. not used 
        """
        event.Skip()
        return   
        self.SetFocus()

    def OnEnterWindow(self,event):
        """ EnterWindow event handler
        """
        #self.SetFocus()
        event.Skip()
        
    def OnLeaveWindow(self,event):
        """ LeaveWindow event handler
        """
        #self.ReleaseMouse()
        event.Skip()
        return
         
    def OnKeyDown(self,event):
        """ KeyDown event handler
        """
        self.mdlwin.OnKeyDown(event)
        event.Skip()

    def OnKeyUp(self,event):
        """ KeyUp event handler
        """
        self.mdlwin.OnKeyUp(event)
        event.Skip()

    def OnPaint(self, event):
        """ Paint event handler
        """
        self.draw.Paint()
        event.Skip()
        
    def OnResize(self, event):
        """ Resize event handler
        """
        self.mdlwin.OnResize(event)
        event.Skip()

    def OnMove(self,event):
        """ Move event handler
        """
        event.Skip()
        self.mdlwin.OnMove(event)
        
    def OnEraseBG(self, event):
        """ EraseBG event handler
        """
        pass  # Do nothing, to avoid flashing on MSWin

    def OnMouseLeftDClick(self,event):
        """ MouseLeftDown event handler 
        """
        self.mdlwin.OnMouseLeftDClick(event)
            
    def OnMouseLeftDown(self, event):
        """ MouseLeftDown event handler
        """
        self.mdlwin.OnMouseLeftDown(event)

    def OnMouseLeftUp(self, event):
        """ MouseLeftUp event handler
        """
        #if not self.mdlwin.GetViewReady(): return
        self.mdlwin.OnMouseLeftUp(event)

    def OnMouseMove(self, event):
        """ MouseMove event handler
        """
        #if not self.mdlwin.GetViewReady(): return
        self.mdlwin.OnMouseMove(event)

    def OnMouseWheel(self, event):
        """ MouseWhell event handler
        """
        #if not self.mdlwin.GetViewReady(): return
        self.mdlwin.OnMouseWheel(event)

    def OnMouseRightDown(self, event):
        """ MouseRightDown event handler 
        """
        #if not self.mdlwin.GetViewReady(): return
        self.mdlwin.OnMouseRightDown(event)
        
    def OnMouseRightUp(self, event):
        """ MouseRightUp event handler
        """
        #if not self.mdlwin.GetViewReady(): return
        self.mdlwin.OnMouseRightUp(event)

class MolDraw():
    """ Draw molecular model on glcanvas

    :param obj parent: window object (View_Frm class instance in FU)
    """
    def __init__(self,parent):
        self.mdlwin=parent
        self.classname='MolDraw'
        # create GLCanvas
        self.canvas=GLCanvas(self.mdlwin,self)
        self.canvas_size=self.canvas.GetSize()
        # initialize once
        self.gl_initialized=False
        self.canvas_size=[]
        self.busy=False
        #self.showbusycusor=False
        self.showdrawingmess=True
        self.updated=True
        self.mess=''
        self.messfield=1 # field # in parent statusbar
        self.bgcolor=[0.0,0.0,0.0,1.0]
        # flags for draw object
        self.fog = False  # fogscale=20
        self.fogscale=100 # fog strength. 0-100.
        self.fogscale_max=100 # fixd in the 'Control_frm' class
        self.stereo=0 # off, 1:cross eye, 2:parallel eye
        self.DisplayList = None
        self.rasposz=[] # z-position
        self.rasposzmax=100 #raste max z
        self.rasposzmin=-100 # raster minz
        self.atmcc=[] # [[i,cc],...]
        # initial view position
        self.eyepos = [0.0, 0.0, 300.0]; self.eyepossav=self.eyepos
        self.center = [0.0, 0.0, 0.0]; self.centersav=self.center
        self.upward = [0.0, 1.0, 0.0]; self.upwardsav=self.upward
        self.ratio = 1.0; self.ratiosav=self.ratio # angstrom per pixel
        # store method and data for draw
        self.drwitemlst=['Distance','Tube','CAlpha','BDA points','xyz-axis',
            'Multiple bond','Hydrogen/vdW bond','selectsphere','selectbox',
            'rot-axis','Paint fragment','Formal charge','Element',
            'Fragment name','Layer by color','Fragment name',
            'Residue name','Residue name+number','Atom number','Atom name',
            'Atom name+number','Element','cube-data']

        self.DrawObjDic={}
        self.labeldic={}
        # default values
        self.defaultparams=self.DefaultParams()
        self.default_arrowhead=0.3 

    def DefaultParams(self):
        """ Return default paramters
        
        :return dic params: {'parameter name': value,...}
        """
        params={
        'nslice':15, # number of slice for sphere
        'stipple':[2,0xcccc], # broken line pattern data:[factor,pattern]
        'font':GLUT_BITMAP_8_BY_13, # 8 by 13 pixel
        'fontcolor':[0.0,1.0,0.0,1.0], # font color:green
        'objcolor':[0.0,1.0,0.0,1.0], # object color:green
        'textcolor':[0.5,0.5,0.5,1.0], # text color:gray 
        'arrowhead':0.3 # arrow head
                       }
        return params

    @staticmethod
    def GetBitmapFont(style):
        """ Bitmap fonts
        
        :param int style: 0-6.
        :return: bmpfont(obj) - bitmap font object
        :note: the caller should imports OpenGL.GLUT
        """
        if style == 0: bmpfont=GLUT_BITMAP_8_BY_13 # 8 by 13 pixel
        elif style == 1: bmpfont=GLUT_BITMAP_9_BY_15
        elif style == 2: bmpfont=GLUT_BITMAP_TIMES_ROMAN_10
        elif style == 3: bmpfont=GLUT_BITMAP_TIMES_ROMAN_24
        elif style == 4: bmpfont=GLUT_BITMAP_HELVETICA_10
        elif style == 5: bmpfont=GLUT_BITMAP_HELVETICA_12
        elif style == 6: bmpfont=GLUT_BITMAP_HELVETICA_18
        else: bmpfont=GLUT_BITMAP_8_BY_13
        return bmpfont
    
    def InitGL(self):
        """ Initialize GL canvas
        """
        if not self.gl_initialized:
            glutInit(sys.argv)
            self.gl_initialized=True
        light_diffuse = [1.0, 1.0, 1.0, 1.0]
        light_position = [self.eyepos[0], self.eyepos[1], self.eyepos[2], 0.0]
        #
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        #
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glClearColor(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
        glClearDepth(1.0)
        #
        self.gl_initialized=True

    def ChangeWinSize(self,size):
        """ not used """
        return
        
        self.canvas_size=size
        self.CenterMolecular
        self.FitMolecular()
        self.Draw()

    def SetViewItems(self,viewitems):
        if viewitems.has_key('viewpos'):
            lst=viewitems['viewpos']
            self.eyepos=lst[0]; self.center=lst[1]; self.upward=lst[2]; self.ratio=lst[3]   
        if viewitems.has_key('Fog'): self.fog=viewitems['Fog']
        if viewitems.has_key('fogscale'): self.fogscale=viewitems['fogscale']
            #xxdrwitems['section']=self.section
        if viewitems.has_key('stereo'): self.stereo=viewitems['stereo']
        if viewitems.has_key('bgcolor'): self.bgcolor=viewitems['bgcolor']
           
    def GetViewItems(self):
        viewitems={}
        viewitems['viewpos']=[self.eyepos,self.center,self.upward,self.ratio]
        viewitems['Fog']=self.fog
        viewitems['fogscale']=self.fogscale
        #xxdrwitems['section']=self.section
        viewitems['stereo']=self.stereo
        viewitems['bgcolor']=self.bgcolor
        
        return viewitems

    def GetDrawObjs(self):
        """ Return current draw data
        :return: drwitems - {'Item name':True or False,...}
        """
        drwobjs={}
        
        for labobj,objlst in self.DrawObjDic.iteritems():
            items=labobj.split(':')
            label=items[0].strip(); objnam=items[1].strip()
            if label in self.drwitemlst:
                drwobjs[label]=[objnam,objlst[1]]
        return drwobjs
    
    def IsDrawLabel(self,label):
        """ 
        :return: True for drawn, False for not
        """
        ans=False
        for labobj,objlst in self.DrawObjDic.iteritems():
            items=labobj.split(':')
            lab=items[0].strip(); objnam=items[1].strip()
            if lab == label:
                ans=True; break
        return ans
    
    def SetDrawObjs(self,drwobjdic):
        self.DrawObjDic=drwobjdic
        
    def ResetDraw(self):
        """ Reset all darw parameters (labeldic,eyepos,cenetr,upward,ratio,fog,fogscale)
        """
        # set defaults
        self.labeldic={}
        self.eyepos = [0.0, 0.0, 300.0]; self.eyepossav=self.eyepos
        self.center = [0.0, 0.0, 0.0]; self.centersav=self.center
        self.upward = [0.0, 1.0, 0.0]; self.upwardsav=self.upward
        self.ratio = 1.0; self.ratiosav=self.ratio #MolView.DEFAULT_RATIO  # angstrom per pixel
        self.fog = False  # fogscale=20
        self.fogscale=self.fogscale_max # fog strength. 0-100.
        #xxself.section=False
        self.stereo=False
        #
        self.DrawObjDic={}
        
    def Busy(self):
        """ Return busy flag(self.busy) """
        return self.busy

    def Mess(self,mess):
        """ Add class name to message to self.mess variable 
        
        :param str mess: message
        """
        items=mess.split(':',1)
        if len(items) == 0: mess=self.classname+mess
        else: mess=self.classname+'('+items[0]+'): '+items[1]
        self.mess=self.mess+mess+'\n'
    
    def Message(self,mess):
        try: self.mdlwin.SetStatusText(mess,self.messfield)
        except: print mess
            
    def Circle2DToLineData(self,circledat):
        """ not completed """
        # [ [ndiv(int),center(lst:3),radius(float),color(lst:3),thick(int),
        #stipple(lst:2)],...]

        linedat=[]
        for ndiv,center,radius,color,thick,stipple in circledat:
            x0=center[0]; y0=center[1]; z0=center[2] 
            ndiv4=ndiv/4; nt=4*ndiv4; dang=(2.0*pi)/nt
            nd2=ndiv4; nd3=ndiv4*2; nd4=ndiv4*3
            tmp=[]; x=nt*[0.0]; y=nt*[0.0]
            for i in range(ndiv4): 
                ang=float(i)*dang
                x1=radius*cos(ang); y1=radius*sin(ang)
                x[i]=x1; y[i]=y1
                x[nd2+i]=-y1; y[nd2+i]= x1
                x[nd3+i]=-x1; y[nd3+i]=-y1
                x[nd4+i]= y1; y[nd4+i]=-x1
            for i in range(nt): tmp.append([x[i]+x0,y[i]+y0,z0])
            linedat.append([tmp,color,thick,stipple])

        return linedat

    def Square2DToLineData(self,squaredat):
        """
        Convert rectangle data to lines data
        
        :param lst rectdata: [ [left upper point(lst:3), lower right point(lst:3),
        color(lst:3),thick(int),stipple(lst:2)],..]
        :return: linedata: data for draw lines. See the 'DrawLine' method.
        :rtype: lst
        """
        """
        [ [(x1,y1,z1),(x2,y2,z2),...](lst), color(lst:3),thick(int),stipple(lst:2)],
        """
        linedat=[]
        for pnt1,pnt3,color,thick,stipple in squaredat:
            tmp=[]
            pnt2=[pnt1[0],pnt3[1],pnt1[2]]
            pnt4=[pnt3[0],pnt1[1],pnt1[2]]
            tmp.append([pnt1,pnt2,pnt3,pnt4])
            tmp.append(color)
            tmp.append(thick)
            tmp.append(stipple)
            linedat.append(tmp)
        return linedat
                    
    def DelDrawObj(self,label):
        """ Delete draw data
        
        :param str label: draw data label
        :seealso: SetDrawData()
        """
        dellst=[]
        for lab,draw in self.DrawObjDic.iteritems(): # lab='label'+':'+'objname'
            item=lab.split(':')[0]
            if item == label: dellst.append(lab)
        for lab in dellst: del self.DrawObjDic[lab]

    def IsDrawObj(self,label):
        """ Is drawdata aveilable?
        
        :param str label: draw data label
        :return: True for exists, False for does not
        """
        ans=False
        for lab,obj in self.DrawObjDic.iteritems():
            lab=lab.split(':')[0]
            if label == lab: ans=True
        return ans

    def IsDrawLabelObj(self,labobj):
        """ Is draw label?
        
        :param str labobj: draw label+object name, ex. 'Message:MESSAG'
        :return: True for exists, False for does not
        """
        if self.DrawObjDic.has_key(labobj): return True
        else: return False

    def SetMultipleData(self,label,data):
        """
        Set multiple draw data.
        
        :param lst data: [item,label,True/False,drwdat]. See 'SetDrawData'.
        """
        if len(data) <= 0:
            self.Mess('SetMultipleData: No data.'); return
        for object,drwdat in data:
            self.SetDrawData(label,object,drwdat)
    
    def SetDrawData(self,label,object,data):
        """ Set draw data.
        
        :param str label: label to distinguish data of the same object.
        :param str object: object name is one of 'LINE',''LINES','STICK','STICS',SPHERE','BOX','LABEL','TUBE','AXIS','CUBE','ARROW', or 'EXTRABOND'.
        :param lst data: draw data. See each draw object method for the data structure.
        """      
        labobj=label+':'+object
        #
        if object == 'ATOMS': 
            self.DrawObjDic[labobj]=[self.DrawAtoms,data]
        elif object == 'BONDS': 
            self.DrawObjDic[labobj]=[self.DrawBonds,data]
        elif object == 'SPLINE2D':
            self.lineline=on
            if len(data) <= 0: self.lineline=False
            if on:
                linedat=self.SplineFit(data)
                self.DrawLine(linedat)
                self.DrawObjDic[labobj]=[self.DrawLine,data]
                ###self.Line2D(linedat)
            else: self.linelinedata=[]           
        #elif object == 'MESSAGE':
        #    self.message=on
        #    if len(data) <= 0: self.message=False
        #    if on: self.messagedata=data
        #    else: self.messagedata=[]
        elif object == 'XYZAXIS': self.DrawObjDic[labobj]=[self.DrawXYZAxis,data] 
        elif object == 'AXIS': self.DrawObjDic[labobj]=[self.DrawAxis,data]
        elif object == 'LINE2D': self.DrawObjDic[labobj]=[self.DrawLine2D,data] 
        elif object == 'LINE': self.DrawObjDic[labobj]=[self.DrawLine,data] 
        elif object == 'CIRCLE2D': self.DrawObjDic[labobj]=[self.DrawCircle2D,data]
        elif object == 'SQUARE2D': self.DrawObjDic[labobj]=[self.DrawSquare2D,data]
        elif object == 'LABEL2D': self.DrawObjDic[labobj]=[self.DrawLabel2D,data]
        elif object == 'LABEL': self.DrawObjDic[labobj]=[self.DrawLabel,data]
        elif object == 'SPHERE': self.DrawObjDic[labobj]=[self.DrawSphere,data]
        elif object == 'BOX': self.DrawObjDic[labobj]=[self.DrawBox,data]
        elif object == 'TUBE': self.DrawObjDic[labobj]=[self.DrawTube,data]
        elif object == 'CUBE': self.DrawObjDic[labobj]=[self.DrawCube,data]          
        elif object == 'ARROW': self.DrawObjDic[labobj]=[self.DrawArrow,data]
        elif object == 'EXTRABOND': self.DrawObjDic[labobj]=[self.DrawExtraBond,data]
        elif object == 'BDAPOINT': self.DrawObjDic[labobj]=[self.DrawBDAPoint,data]
        elif object == 'MESSAGE': self.DrawObjDic[labobj]=[self.DrawMessageText,data]
        #
        if object == 'LABEL': self.labeldic[label]=True
            
    def ClearScreen(self):
        """ Clear screen (not used) """
        # this routne is not tested
        bg=self.bgcolor
        glClearColor(bg[0],bg[1],bg[2],bg[3])
        glClear(GL_COLOR_BUFFER_BIT)
        glFlush()
    
    def GetAtomRasPosZ(self):
        """ Return z-raster positions
        
        :return: z-raster position - self.rasposz
        :seealso: FindAtomRasPosZ()
        """
        # ret rasposz(lst): z value of rater position of selected atoms,[rasposz(float),...]
        if not self.fog: self.rasposz=self.FindAtomRasPosZ()
        #self.rasposz=self.FindAtomRasPosZ()
        return self.rasposz

    def GetMinMaxRasPosZ(self):
        """ Return max/min z raster position
        
        :return: min z value(int), max z vale(int) - self.rasposzmin,self.rasposzmax
        """
        return self.rasposzmin,self.rasposzmax
    
    def GetRatio(self):
        """ Return ratio parameter
        
        :return: ratio(float) - self.ratio (angstroms per pixel)
        """
        return self.ratio
    
    def SetRatio(self,ratio):
        """ Set ratio parameter
        
        :param float ratio: set ratio (angstroms per pixel)
        """
        self.ratio=ratio
    
    def GetRasterPosition(self,x,y,z):
        """ Return raster position (rx,ry) of world coordinaet (x,y,z)
        
        :param float x: x world coordinates
        :param float y: y world coordinates
        :param float z: z world coordinates
        :return: x(float),y(float),z(float) - raster coodinates
        """
        #[w,h]=self.canvas.GetClSize()
        rx=-1; ry=-1; rz=-1
        try:
            glRasterPos3f(x,y,z)
            [rx,ry,rz,rw]=glGetIntegerv(GL_CURRENT_RASTER_POSITION) 
            #ry=h-ry
            pos=array([x,y,z])
            eye = array(self.eyepos)
            ctr = array(self.center)
            e2c = ctr - eye
            e2c /= linalg.norm(e2c)
            e2p = pos - eye
            d = dot(e2p, e2c)
            rz=d
        except: pass

        return rx,ry,rz

    def GetRasterPositionOfAtom(self,x,y,z):
        """ Return raster position (rx,ry) of world coordinaet (x,y,z)
        
        :param float x: x world coordinates
        :param float y: y world coordinates
        :param float z: z world coordinates
        :return: x(float),y(float),z(float) - raster coodinates
        """
        [w,h]=self.canvas.GetClientSize()
        rx=-1; ry=-1
        try:
            glRasterPos3f(x,y,z)
            [rx,ry,rz,rw]=glGetIntegerv(GL_CURRENT_RASTER_POSITION) 
            ry=h-ry
        except: pass

        return rx,ry

    def GetWorldCoordAtRasPos2(self,rasx,rasy):
        """ Compute object coordinates from window coordinates
        
        :param float rasx,rasy: window coordinates
        :return: objx(float),objy(float),objz(float) - object coordinates
        """
        #self.FitMolecular()
        #self.SetCamera()
        #      
        modelview=glGetDoublev(GL_MODELVIEW_MATRIX)
        projection=glGetDoublev(GL_PROJECTION_MATRIX)
        viewport=glGetIntegerv(GL_VIEWPORT)
        winw=viewport[2]; winh=viewport[3]
        x=rasx; y=winh-rasy             
        z=glReadPixels(x,y,1,1,GL_DEPTH_COMPONENT,GL_FLOAT)
        objx,objy,objz=gluUnProject(x,y,z,modelview,projection,viewport)
        return objx,objy,objz

    def UnProject(self,targx,targy,targz): 
        model=glGetDoublev(GL_MODELVIEW_MATRIX)
        proj=glGetDoublev(GL_PROJECTION_MATRIX)
        view=glGetIntegerv(GL_VIEWPORT)
        objx=0; objy=0; objz=0; w=0.0
        h=view[3]
        targy=h-targy
        pm=proj*model #numpy.cross(proj,model)
        invpm=linalg.inv(pm)
        v0=2.0*(targx-view[0])/view[2]-1.0 # -1 ~ +1/0
        v1=2.0*(targy-view[1])/view[3]-1.0
        v2=2*targz-1.0
        v3=1.0
        objx=invpm[0][0]*v0+invpm[0][1]*v1+invpm[0][2]*v2
        objy=invpm[1][0]*v0+invpm[1][1]*v1+invpm[1][2]*v2
        objz=invpm[2][0]*v0+invpm[2][1]*v1+invpm[2][2]*v2
        xmin,xmax,ymin,ymax,unit=self.GetCoordinateMinMax()
        #[w,h]=self.canvas.GetSize()
        #objx *= w
        #objy *= h
        #objz -= self.center[2]
        return objx,objy,objz

    def DrawCube(self,drwdat):
        """
        Draw cube data.
        
        :param lst drwdat: params and polys lists
        [params,polys]=[style,poscolor,negacolor,opaciy] and polys: [polygon data]
        """
        params=drwdat[0]; polys=drwdat[1]
        if len(polys[0]) == 0:
            self.Mess('Cube: No polygon data in '+str(ndat)+' data'); return
        style=params[0] # 0: soild, 1:wire
        if style > 1 or style < 0: style=0
        #
        try:
            if style == 0: # solid
                glEnable(GL_LIGHTING)
                glEnable(GL_CULL_FACE)
                glCullFace(GL_FRONT)
            if style == 1: # wire
                glDisable(GL_LIGHTING)
                glDisable(GL_CULL_FACE)
            
            glEnable(GL_COLOR_MATERIAL)
            colpos=params[1]; colneg=params[2]
            if len(colpos) <= 0: colpos=[1.0,0.0,0.0]
            if len(colneg) <= 0: colneg=[0.0,0.0,1.0]
            opacity=params[3]  # self.moplot_transparency
            if opacity < 0.01: return
            # print 'style,colpos,colneg,opacityb in Cubes',style,colpos,colneg,opacity
            for i in range(2):
                if i == 0: rgb=colpos
                else: rgb=colneg
                for triangle in polys[i]:
                    midpos = [ triangle[0], triangle[1], triangle[2] ]
                    vnorm  = triangle[3]
                    if style == 0:
                        glBegin(GL_TRIANGLES)
                        for ii in range(0,3):
                            glNormal3f(vnorm[0], vnorm[1], vnorm[2])
                            glColor4f(rgb[0], rgb[1], rgb[2], opacity)
                            glVertex3f(midpos[ii][0], midpos[ii][1], midpos[ii][2])
                        glEnd()
                        glBegin(GL_TRIANGLES)
                        for ii in range(2,-1,-1):
                            glNormal3f(-vnorm[0], -vnorm[1], -vnorm[2])
                            glColor4f(rgb[0], rgb[1], rgb[2], opacity)
                            glVertex3f(midpos[ii][0], midpos[ii][1], midpos[ii][2])
                        glEnd()
                    if style == 1:
                        glBegin(GL_LINE_STRIP)
                        for ii in range(0,3):
                            glColor4f(rgb[0], rgb[1], rgb[2], opacity)
                            glVertex3f(midpos[ii][0], midpos[ii][1], midpos[ii][2])
                        glEnd()
    
            glDisable(GL_CULL_FACE);
            glDisable(GL_COLOR_MATERIAL)
        except:
            self.Mess('Cube: Failed to draw cube. data number='+str(ndat))
            
    def DrawText(self,text,font,pos,color):
        # draw bitmap characters at pos with font and color, text, in 3D
        if len(text) <= 0:
            self.Mess('DrawText: No data.'); return
        if not font: font=self.defaultparams['font']
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glColor3f(color[0],color[1],color[2])
        glRasterPos3f(pos[0],pos[1],pos[2]) 
        for c in text: glutBitmapCharacter(font, ord(c))
        glPopMatrix()

    def DrawText2D(self,text,font,pos,color):
        if len(text) <= 0:
            self.Mess('DrawText2D: No data.'); return
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(color[0],color[1],color[2])
        glRasterPos2f(pos[0],pos[1]) #,pos[2]) 
        for c in text: glutBitmapCharacter(font, ord(c))
        glPopMatrix()
        
    def DrawXYZAxis(self,drwdat):
        # draw x-, y-, z-axis
        # data(ins): XYZAxisData instance
        """ Draw xyz-axis
        
        :param lst drwdat: [xmin(float),xmax(float),ymin(float),ymax(float),zmin(float),zmax(float),xlab(str),ylab(str),zlab(str),
        xcolor[r,g,b],ycolor[r,g,b],zcolor[r,g,b],thick(int),stipple[factor(float),pattrn(int)]]
        """
        #thick=data.thick; fac=data.stipplef; pat=data.stipplep
        #xcolor=data.xcolor; ycolor=data.ycolor; zcolor=data.zcolor
        #xmin=data.xmin; ymin=data.ymin; zmin=data.zmin
        #xmax=data.xmax; ymax=data.ymax; zmax=data.zmax

        #thick=data.thick; fac=data.stipplef; pat=data.stipplep
        
        if len(drwdat) <= 0: return
        xmin=drwdat[0][0]; xmax=drwdat[0][1]
        ymin=drwdat[1][0]; ymax=drwdat[1][1]
        zmin=drwdat[2][0]; zmax=drwdat[2][1]
        xlab=drwdat[3][0]; ylab=drwdat[3][1]; zlab=drwdat[3][2]
        xcolor=drwdat[4]; ycolor=drwdat[5]; zcolor=drwdat[6]
        thick=drwdat[7] #line thickness
        fac=drwdat[8][0] #stipplef; 
        pat=drwdat[8][1] #stipplep
        #
        axisorg=self.center
        font=GLUT_BITMAP_8_BY_13
        #
        glPushMatrix()
        #glLoadIdentity();
        glTranslatef(axisorg[0], axisorg[1], axisorg[2])
        glLineStipple(fac,pat) #2,0xcccc)
        glEnable(GL_LINE_STIPPLE)
        glDisable(GL_LIGHTING)
        glLineWidth(thick) #self.axisthick)         
        glBegin(GL_LINES)
        # x-axis
        glColor3f(xcolor[0],xcolor[1],xcolor[2])
        glVertex3f(xmin,0.0,0.0); glVertex3f(xmax,0.0,0.0) 
        #glPopMatrix()
        # y-axis
        glColor3f(ycolor[0],ycolor[1],ycolor[2])
        glVertex3f(0.0,ymin,0.0); glVertex3f(0.0,ymax,0.0)
        # z-axis 
        glColor3f(zcolor[0],zcolor[1],zcolor[2])
        glVertex3f(0.0,0.0,zmin); glVertex3f(0.0,0.0,zmax)
        #          
        glEnd()
        glPopMatrix()
        glDisable(GL_LINE_STIPPLE)            
        # axis-labels
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(axisorg[0], axisorg[1], axisorg[2])
        glColor3f(xcolor[0],xcolor[1],xcolor[2]) 
        glRasterPos3f(xmax+0.5,0.0,0.0) 
        glutBitmapCharacter(font,ord(xlab))
        glColor3f(ycolor[0],ycolor[1],ycolor[2]) 
        glRasterPos3f(0.0,ymax+0.5,0.0) 
        glutBitmapCharacter(font,ord(ylab))
        glColor3f(zcolor[0],zcolor[1],zcolor[2]) 
        glRasterPos3f(0.0,0.0,zmax+0.5) 
        glutBitmapCharacter(font,ord(zlab))
        glPopMatrix()

    def DrawAxis(self,drwdat):
        """ Draw axis
        
        :param lst drwdat: [pnt1,pnt2,lab,color,thick,stpple]
        """
        #thick=data.thick; fac=data.stipplef; pat=data.stipplep
        #color=data.color; pnt1=data.pnt1; pnt2=data.pnt2

        if len(drwdat) <= 0: return
        #for p1,p2,lab,col,thick,stipple in drawlst:
        pnt1=drwdat[0]; pnt2=drwdat[1]; lab=drwdat[3]
        color=drwdat[6]; thick=drwdat[7]; stipple=drwdat[8]
        
        axisorg=self.center
        #
        glPushMatrix()
        #glLoadIdentity();
        glTranslatef(axisorg[0], axisorg[1], axisorg[2])
        glLineStipple(fac,pat) #2,0xcccc)
        glEnable(GL_LINE_STIPPLE)
        glDisable(GL_LIGHTING)
        glLineWidth(thick) #self.axisthick)         
        glBegin(GL_LINES)
        # drawline
        glColor3f(color[0],color[1],color[2])
        glVertex3f(pnt1[0],pnt1[1],pnt1[2])
        glVertex3f(pnt2[0],pnt2[1],pnt2[2]) 
        #          
        glEnd()
        glPopMatrix()
        glDisable(GL_LINE_STIPPLE)            

    def DrawLine2D(self,drwdat):
        """ 
        Draw single line between points
        
        :param lst drwdat: [[ [x1,y1,z1],[x2,y2,z2],...],color(lst:3),thick(int),stipple(lst:2)],...] ]
        """
        if len(drwdat) <= 0: return
        print 'drwdat in Line2D',drwdat
        #org=self.center
        #glTranslatef(org[0],org[1],org[2])
        #       
        for pnts,color,thick,stipple in drwdat:
            glPushMatrix()
            glLineStipple(stipple[0],stipple[1]) #fac,pat) #2,0xcccc)
            glEnable(GL_LINE_STIPPLE)
            glDisable(GL_LIGHTING)
            glLineWidth(thick)
            glColor3f(color[0],color[1],color[2]) 
            # draw lines
            glBegin(GL_LINE_LOOP)
            for i in xrange(len(pnts)):     
                pnt1=pnts[i]
                glVertex3f(pnt1[0],pnt1[1],pnt1[2])
            glEnd()              
            glPopMatrix()

        glDisable(GL_LINE_STIPPLE)            

    def DrawLines2D(self,drwdat):
        """ 
        Draw  miltiple lines between points.
        
        :param lst drwdat: [ [ [x1,y1,z1],[x2,y2,z2]],color(lst:3),thick(int),multiple(int),stipple(lst:2)],...] ]
        """
        if len(drwdat) <= 0: return
        # center
        org=self.center
        #
        glPushMatrix()
        glTranslatef(org[0],org[1],org[2])
        #       
        for pnts,color,thick,multiple,stipple in drwdat:
            delta=0; mline=[]; pnt1=onts[0]; pnt2=pnts[1]
            if multiple > 1:
                delta=thick/2
                if delta < 1: delta=1
                if multiple % 2 == 0:
                    for i in range(multiple/2):
                        mlines.append(x)
            glPushMatrix()
            glLoadIdentity()
            glLineStipple(stipple[0],stipple[1]) #fac,pat) #2,0xcccc)
            glEnable(GL_LINE_STIPPLE)
            glDisable(GL_LIGHTING)
            glLineWidth(thick)
            glColor3f(color[0],color[1],color[2])   
            # draw lines
            glBegin(GL_LINES)
            for i in range(multiple):
                    
                pnt1=array(pnts[i]) #; pnt2=array(pnts[i+1])
                glVertex3f(pnt1[0],pnt1[1],pnt1[2])       
            glEnd()              
            glPopMatrix()
        
        glPopMatrix()
        glDisable(GL_LINE_STIPPLE)            

    def DrawLine(self,data):
        """ 
        Draw single line between 2 points
        
        :param lst data: [ [ [x1,y1,z1],[x2,y2,z2],...],color(lst:3),thick(int),stipple(lst:2)],...] ]
        """
        if len(data) <= 0: return
        
        glDisable(GL_LIGHTING)
        for pnts,color,thick,stipple in data:
            glLineWidth(thick)    
            glColor(color)    
            glLineWidth(thick) 
            if len(stipple) > 0: glEnable(GL_LINE_STIPPLE)
            for i in range(0,len(pnts),2):
                pnt1=pnts[i]; pnt2=pnts[i+1]
                glBegin(GL_LINES)
                glVertex3f(pnt1[0],pnt1[1],pnt1[2])
                glVertex3f(pnt2[0],pnt2[1],pnt2[2])
                glEnd()
        if len(stipple) > 0: glDisable(GL_LINE_STIPPLE)

    def DrawStick(self,data):
        """ 
        Draw single line between points
        
        :param lst data:  [ [ [x1,y1,z1],[x2,y2,z2],...],color(lst:3),thick(int),stipple(lst:2)],...] ]
        """
        # data:[[i,show flag,model #,color,thick,kind,icoord list,j,show flag,model #,color,thick,kind,jcoord list],..]
        if len(data) <= 0: return
            
        NSLICE = 15
        # setting for line model
        glEnable(GL_LINE_SMOOTH);
        #
        stickbold=2
        glLineWidth(stickbold)
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        """for pnts,color,thick,stipple in drwdat"""
        #for i,model0,cc0,bndmulti0,visible0,color0,thick0,j,model1,cc1,bndmulti1,visible1,color1,thick1 in data:
        for pnts,color,thick in data: # pnts:[pnt1,pnt2,...]
            pos0=[0.0,0.0,0.0]
            pos0[0]=cc0[0]; pos0[1]=cc0[1]; pos0[2]=cc0[2]
            pos0=array(pos0)
            if not visible0 and not visible1: continue    
            pos1=[0.0,0.0,0.0]
            pos1[0]=cc1[0]; pos1[1]=cc1[1]; pos1[2]=cc1[2]
            pos1=array(pos1)
            center=[0.0,0.0,0.0]
            center[0]=0.5*(pos0[0]+pos1[0])
            center[1]=0.5*(pos0[1]+pos1[1])
            center[2]=0.5*(pos0[2]+pos1[2])
            center=array(center)
            dm0_lin = ( model0 == 0 )
            dm0_stk = ( model0 == 1)
            dm0_bas = ( model0 == 2)
            dm1_lin = ( model1 == 0)
            dm1_stk = ( model1 == 1)
            dm1_bas = ( model1 == 2)
            # Line
            glDisable(GL_LIGHTING)
            #!!!glLoadIdentity()
            if dm0_lin and visible0:
                # atom0 -> center
                glLineWidth(thick0)    
                glColor(color0)                           
                glBegin(GL_LINES)
                glVertex3fv(pos0)
                glVertex3fv(center)
                glEnd()
            if dm1_lin and visible1:
                # center -> atom1
                glLineWidth(thick1)                        
                glColor(color1)                           
                glBegin(GL_LINES)
                glVertex3fv(center)
                glVertex3fv(pos1)
                glEnd()
            # Stick
            if dm0_bas or dm0_stk or dm1_bas or dm1_stk:
                vb = center - pos0
                length = linalg.norm(vb)
                axis = array([0.0, 0.0, length]) + vb
                glEnable(GL_LIGHTING)
                #!!!glLoadIdentity()
                glPushMatrix()                                                        
                glTranslatef(pos0[0], pos0[1], pos0[2])
                glRotatef(180.0, axis[0], axis[1], axis[2])
                if ( dm0_bas or dm0_stk ) and visible0:
                    # atom0 -> center 
                    glPushMatrix()
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, color0)
                    gluQuadricDrawStyle(self.qobj, GLU_FILL)
                    gluQuadricNormals(self.qobj, GLU_SMOOTH)
                    gluCylinder(self.qobj, 0.1*thick0, 0.1*thick0, length, NSLICE, 1)
                    if not ( ( dm1_bas or dm1_stk ) and visible1 ):
                        glPushMatrix()
                        glTranslatef(0.0, 0.0, length)
                        gluDisk(self.qobj, 0.0, 0.1*thick0, NSLICE, 1)
                        glPopMatrix()
                    if dm0_stk:
                        glPushMatrix()
                        gluQuadricOrientation(self.qobj, GLU_INSIDE)
                        gluDisk(self.qobj, 0.0, 0.1*thick1, NSLICE, 1)
                        gluQuadricOrientation(self.qobj, GLU_OUTSIDE)
                        glPopMatrix()
                    glPopMatrix()
                if ( dm1_bas or dm1_stk ) and (visible1 or visible0):    
                    # center -> atom1
                    glPushMatrix()
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, color1)
                    glTranslatef(0.0, 0.0, length)
                    gluQuadricDrawStyle(self.qobj, GLU_FILL)
                    gluQuadricNormals(self.qobj, GLU_SMOOTH)
                    gluCylinder(self.qobj, 0.1*thick1, 0.1*thick1, length, NSLICE, 1)
                    if not ( ( dm0_bas or dm0_stk ) and visible0 ):
                        glPushMatrix()
                        gluQuadricOrientation(self.qobj, GLU_INSIDE)
                        gluDisk(self.qobj, 0.0, 0.1*thick0, NSLICE, 1)
                        gluQuadricOrientation(self.qobj, GLU_OUTSIDE)
                        glPopMatrix()
                    if dm1_stk:
                        glPushMatrix()
                        glTranslatef(0.0, 0.0, length)
                        gluDisk(self.qobj, 0.0, 0.1*thick1, NSLICE, 1)
                        glPopMatrix()
                    glPopMatrix()
                glPopMatrix()

    def DrawSticks(self,drwdat):
        """ not coded yet """
        pass
                    
    def DrawCircle2D(self,drwdat):
        """ 
        Draw circle using 'DrawLine2D'.
        
        :param lst drwdat: [ [(x1,y1,z1),(x2,y2,z2),...](lst), color(lst:3),thick(int),stipple(lst:2)],
        [ [coords],color,...] ]. The data format is the same as those for the 'DrawLine2D' method.
        """
        if len(drwdat) <= 0: return
        linedat=self.Circle2DToLineData(drwdat)
        self.DrawLine2D(linedat)

    def DrawSquare2D(self,drwdat):
        """ 
        Draw square using 'DrawLine2D'.
        
        :param lst drwdat: [ [(x1,y1,z1),(x2,y2,z2),...](lst), color(lst:3),thick(int),stipple(lst:2)],
        [ [coords],color,...] ]. The data format is the same as those for the 'DrawLine2D' method.
        """
        if len(drwdat) <= 0:
            self.Mess('DrawSquare2D: No data.'); return
        linedat=self.Square2DToLineData(drwdat)
        self.DrawLine2D(linedat)

    def DrawLabel2D(self,drwdat):
        """
        Draw labels at raster position using 'DrawText2D'.
        
        :param lst drwdat: [[label(str),font(obj),pos(lst),color(lst)],..].
        font:bitmap font object, pos:[x(int),y(int)], color:[R(float),G(float),B(float)]
        """
        if len(drwdat) <= 0: return
        for label,font,pos,color in drwdat:           
            if not font: font=self.defaultparams['font']
            self.DrawText2D(label,font,pos,color)
             
    def DrawMessageText(self,drwdat):
        """
        Draw labels at raster position using 'DrawText2D'.
        
        :param lst drwdat: [[label(str),font(obj),left(str),posx,top(str),posy,color(lst)],..].
        left:'left' or 'right', top:'top' or 'bottom'
        posx and posy are positions measure from let and top, respectively. 
        font:bitmap font object, pos:[x(int),y(int)], color:[R(float),G(float),B(float)]
        """
        if len(drwdat) <= 0: return
        for label,font,left,xpos,top,ypos,color in drwdat:           
            if not font: font=self.defaultparams['font']
            pos=self.GetCoordinateAt(left,xpos,top,ypos)
            self.DrawText2D(label,font,pos,color)

             
    def DrawLabel(self,drwdata):
        """
        Draw labels at world coordinate using 'DrawText'.
        
        :param lst drwdat: [[label(str),font(obj),cc(lst),color(lst)],..].
        cc:[x(float),y(float),z(float)], color:[R(float),G(float),B(float)]
        """
        # drawdata: [[drawdata[0].label,drawdata[0].cc,drawdata[0].color],..]
        if len(drwdata) <= 0: return
        for label,font,cc,color in drwdata:    
            #label=d.label; pos=d.cc; color=d.color
            try:
                if not font: font=self.defaultparams['font']
                self.DrawText(label,font,cc,color)
            except: self.Mess('DrawLabel: Failed to draw.')

    def DrawBDAPoint(self,drwdat):
        """ Draw FMO/BDA points by circle
        
        :param lst drawdbadata: [[radius,pos,color,nslice],..]
        """
        if len(drwdat) <= 0: return
        NSLICE = 4 #15
        for rad,pos,color,nslice in drwdat:
            glDisable(GL_LIGHTING)
            #!!!glLoadIdentity()
            glPushMatrix()
            glTranslatef(pos[0],pos[1],pos[2])
            glColor3f(color[0],color[1],color[2])
            glutSolidSphere(rad, NSLICE, NSLICE)
            glPopMatrix()
            
    def DrawExtraBond(self,data):
        # data(lst): [d0(ins),d1(ins),...], see DrawExtraBondData class for d(ins)
        ndat=len(data)
        if ndat <= 0: return

        glPushMatrix()
        #glDrawLineStipple(2,0xAAA)
        glLineStipple(1, 0xcccc); 
        glEnable(GL_LINE_STIPPLE)
                
        glDisable(GL_LIGHTING)
        #for d in data: #p0,p1,color, thick in data:
        #    p0=d.cc0; p1=d.cc1; color=d.color; thick=d.thick
        for p0,p1,color,thick in data:
            ####glDisable(GL_LIGHTING)
            #!!!glLoadIdentity()
            glColor(color)
            glLineWidth(thick)
            glBegin(GL_LINES)
            x0=p0[0]; y0=p0[1]; z0=p0[2]
            x1=p1[0]; y1=p1[1]; z1=p1[2]
            glVertex3f(x0,y0,z0); glVertex3f(x1,y1,z1)        
            glEnd()
        
        glDisable(GL_LINE_STIPPLE) 
        
        glPopMatrix()

    def DrawArrow(self,data):
        """ Draw arrow
        
        :param lst data: [[[x0,y0,z0],[x1,y1,z1],color,thick],...]
        """       
        if len(data) <= 0: return
        ndat=len(data)
        if ndat <= 0: return
        NSLICE = 15
        font = GLUT_BITMAP_8_BY_13
        #labelcolor0=0.0; labelcolor1=1.0; labelcolor2=0.0
        labelpos=[[0.5,0.0,0.0],[0.0,0.5,0.0],[0.0,0.0,0.5]]
        #
        glPushMatrix()
        #glEnable(GL_LIGHTING)
        #for d in data: #p0,p1,color in data:
        for p0,p1,color,thick,head in data:
            #p0=d.cc0; p1=d.cc1; color=d.color; thick=d.thick; label=d.label
            if len(color) <= 0: color=self.defaultparams['objcolor']
            if head <= 0: head=self.defaultparams['arrowhead']
            glEnable(GL_LIGHTING)          
            #
            p0=array(p0); p1=array(p1)
            vb=p1-p0
            length=linalg.norm(vb)
            axis=array([0.0,0.0,length])+vb
            glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            # stick
            glPushMatrix()
            glTranslatef(p0[0],p0[1],p0[2])
            glRotatef(180.0,axis[0],axis[1],axis[2])
            q0=gluNewQuadric()
            gluQuadricDrawStyle(q0,GLU_FILL)
            gluCylinder(q0, 0.1*thick,0.1*thick,length*(1.0-head), NSLICE, 1)
            # disk
            glPushMatrix()
            gluQuadricOrientation(q0, GLU_INSIDE)
            gluDisk(q0, 0.0, 0.1*thick, NSLICE, 1)
            gluQuadricOrientation(q0, GLU_OUTSIDE)
            glPopMatrix()    
            # head
            glPushMatrix()
            ##
            glTranslated(0.0,0.0,length*(1.0-head))
            q1=gluNewQuadric()
            gluQuadricDrawStyle(q1,GLU_FILL)
            gluCylinder(q1,0.2*thick,0.0,head*length,NSLICE,1)
            # disk
            glPushMatrix()
            gluQuadricOrientation(q1,GLU_INSIDE)
            gluDisk(q1, 0.0, 0.2*thick, NSLICE, 1)
            gluQuadricOrientation(q1, GLU_OUTSIDE)
            glPopMatrix()
            ##
            glPopMatrix()

            glPopMatrix()
            # draw label
            """
            if len(label) <= 0: pass
            else:
                glDisable(GL_LIGHTING)
                #!!!glLoadIdentity()
                glColor3f(color[0],color[1],color[2])
                pos0=p1[0]+labelpos[i][0]; pos1=p1[1]+labelpos[i][1]; pos2=p1[2]+labelpos[i][2]
                glRasterPos3f(pos0,pos1,pos2) 
                for c in label: glutBitmapCharacter(font,ord(c))
             """                         
        glPopMatrix()
    
    def DrawSphere(self,data):
        """
        Draw sphere.
        
        :param lst data: [ [(x1,y1,z1),(x2,y2,z2),...](lst), color(lst:3),thick(int),stipple(lst:2)]
        """
        ndat=len(data)
        if len(data) <= 0:
            self.Mess('DrawSphere: No draw data.'); return
        glEnable(GL_LIGHTING)
        for pos,rad,color,nslice in data:
            if nslice <= 0: nslice=self.defaultparams['nslice'] # #default NSLICE=15
            color=array(color)
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            glutSolidSphere(rad,nslice,nslice)
            glPopMatrix()
       
    def DrawBox(self,drwdat):
        """ Draw box
        
        :param lst drwdat: point coordinates and color[ [pnt1,pnt2,color],...]
        pnt1:origin [x,y,z], pnt2:[x,y,z] point facing origin
        """
        boxdat=[]
        for [x,y,z],w,h,d,color in drwdat: # pnt1: orgin, pnt2: vertex facing pnt1
            # points defining 6 faces 1-24
            # lef side face:[1-4], right side face:[5-8], rear face:[9-12]
            # front face:[13-16], bottom face:[17-20],top face:[21-24]
            # 8 unique point defining vertex: 1(13,17),2(14,21),3(10,22),
            # 4(9,18),5(16,20),6(15,24),7(11,23),8(12,19)
            p1=[x  ,y  ,z  ]; p9=p1;  p17=p1   
            p2=[x+w,y  ,z  ]; p13=p2; p20=p2
            p3=[x+w,y-h,z  ]; p16=p3; p24=p3
            p4=[x,  y-h,z  ]; p12=p4; p21=p4
            p5=[x,  y,  z-d]; p10=p5; p18=p5
            p6=[x+w,y,  z-d]; p14=p6; p19=p6
            p7=[x+w,y-h,z-d]; p15=p7; p23=p7
            p8=[x,  y-h,z-d]; p11=p8; p22=p8
            boxdat.append([p4,p3,p2,p1,color]) # front 
            boxdat.append([p5,p6,p7,p8,color]) # back
            boxdat.append([p9,p10,p11,p12,color]) # left side
            boxdat.append([p16,p15,p14,p13,color]) # right side
            boxdat.append([p17,p18,p19,p20,color]) # top
            boxdat.append([p24,p23,p22,p21,color]) # bottom
        self.DrawPlane(boxdat)

    def DrawPlane(self,drwdat):
        """
        Draw plane.
        
        :param lst drwdat: [ [pnt1,pnt2,pnt3,pnt4,color],..]
        pnti(i=1-4):[x,y,z], color:[R,G,B,A]
        """
        #center=self.center
        glEnable(GL_COLOR_MATERIAL)
        #glPushMatrix()
        #glLoadIdentity()
        #
        for pnt1,pnt2,pnt3,pnt4,color in drwdat:
            normal=lib.NormalVector(pnt1,pnt2,pnt3)
            #glPushMatrix()
            #glTranslated(center[0],center[1],center[2])
            glBegin(GL_POLYGON)
            glColor4f(color[0], color[1], color[2], color[3])
            glNormal3f(normal[0],normal[1],normal[2])
            glVertex3f(pnt1[0],pnt1[1],pnt1[2])
            glVertex3f(pnt2[0],pnt2[1],pnt2[2])
            glVertex3f(pnt3[0],pnt3[1],pnt3[2])
            glVertex3f(pnt4[0],pnt4[1],pnt4[2])
            glEnd()
            #glPopMatrix() 
        #
        
        #glPopMatrix()
        glDisable(GL_COLOR_MATERIAL)
                      
    def DrawTube(self,drwdat):
        """ Draw tube
         
        :param lst drwdat: [[cc,color,weight,radius],...]
        """
        if len(drwdat) <= 0: return
        NSLICE = 5 #11 #15
        for dat in drwdat:
            xx=[]; yy=[]; zz=[]; wt=[]
            for cc,color,weit,rad in dat:
                xx.append(cc[0])
                yy.append(cc[1])
                zz.append(cc[2])
                wt.append(weit)
            if len(xx) > 0:
                sinarray = []
                cosarray = []
                for i in range(NSLICE + 1):
                    sinarray.append(sin(2.0 * pi * i / NSLICE))
                    cosarray.append(cos(2.0 * pi * i / NSLICE))
                glEnable(GL_LIGHTING)
                
                #color=self.model.mol.tube_color
                
                glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            ###glLoadIdentity()
            # spline interpolation
            x = array(xx)
            y = array(yy)
            z = array(zz)
            #tckp, u = splprep([x, y, z], s=3.0, k=2, nest= -1)
            tckp, u = splprep([x, y, z], w=wt, s=20.0, k=3, nest= -1)
            xnew, ynew, znew = splev(linspace(0, 1, 4 * len(x)), tckp)
            npt = len(xnew)
            # postion array
            posarray = []
            for i in range(npt):
                x = xnew[i]
                y = ynew[i]
                z = znew[i]
                posarray.append(array([x, y, z]))
            # moving vector, and normal ventors
            vec0 = posarray[1] - posarray[0]
            if vec0[0] * vec0[0] > 0.00001:
                e0 = array([vec0[1], -vec0[0], 0.0])
            else:
                e0 = cross(vec0, array([1.0, 0.0, 0.0]))
            e0 /= linalg.norm(e0)
            e1 = cross(e0, vec0)
            e1 /= linalg.norm(e1)
            vecarray = [vec0]
            e0array = [e0]
            e1array = [e1]
            for i in range(1, npt):
                if i == npt - 1:
                    vec0 = posarray[i] - posarray[i - 1]
                else:
                    vec0 = posarray[i + 1] - posarray[i - 1]
                vecarray.append(vec0)
                e1 = cross(e0, vec0)
                e1 /= linalg.norm(e1)
                e1array.append(e1)
                e0 = cross(vec0, e1)
                e0 /= linalg.norm(e0)
                e0array.append(e0)
            for i in range(npt - 1):
                pos0 = posarray[i]
                pos1 = posarray[i + 1]
                e0_0 = e0array[i]
                e1_0 = e1array[i]
                e0_1 = e0array[i + 1]
                e1_1 = e1array[i + 1]
                glBegin(GL_TRIANGLE_STRIP)
                for j in range(NSLICE + 1):
                    u = sinarray[j]
                    v = cosarray[j]
                    vnorm = u * e0_0 + v * e1_0
                    pos = pos0 + rad * vnorm #self.rad_tube * vnorm
                    glNormal3f(vnorm[0], vnorm[1], vnorm[2])
                    glVertex3f(pos[0], pos[1], pos[2])
                    vnorm = u * e0_1 + v * e1_1
                    pos = pos1 + rad * vnorm #self.rad_tube * vnorm
                    glNormal3f(vnorm[0], vnorm[1], vnorm[2])
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()
            # disc
            for i in range(0, npt, npt - 1):
                pos0 = posarray[i]
                e0 = e0array[i]
                e1 = e1array[i]
                vec0 = vecarray[i]
                vec0 /= linalg.norm(vec0)
                if i == 0:
                    vec0 = -vec0
                glBegin(GL_POLYGON)
                glNormal3f(vec0[0], vec0[1], vec0[2])
                for j in range(NSLICE):
                    u = sinarray[j]
                    v = cosarray[j]
                    vnorm = u * e0 + v * e1
                    pos = pos0 + rad * vnorm #self.rad_tube * vnorm
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()

    def SplineFit(self,data):
        """ Return spline fit data """
        # lst(lst): [(res)[[[cc,color,wt,rad],..],...](res)],...]
        if len(data) <= 0: return
        linedat=[]
        for dat in data:
            xx=[]; yy=[]; zz=[]; wt=[]
            for cc,color,weit,thick in dat: #thick,stipple,weit in dat:
                xx.append(cc[0]); yy.append(cc[1]); zz.append(cc[2])
                wt.append(weit)
            # spline interpolation
            x = array(xx); y = array(yy); z = array(zz)
            #tckp, u = splprep([x, y, z], s=3.0, k=2, nest= -1)
            tckp, u = splprep([x, y, z], w=wt, s=20.0, k=3, nest= -1)
            xnew, ynew, znew = splev(linspace(0, 1, 4 * len(x)), tckp)
            npt = len(xnew)
            # postion array
            pos = []
            for i in range(npt):
                x = xnew[i]; y = ynew[i]; z = znew[i]
                pos.append(array([x, y, z]))
            
            
            stipple=[2,0xcccc]
            linedat.append([pos,color,4,stipple])
    
        return linedat
  
    def SplineFitStick(self,drwdat):
        """ Draw spline fit tube ? """
        # lst(lst): [(res)[[[cc,color,wt,rad],..],...](res)],...]
        if len(drwdat) <= 0: return
        NSLICE = 5 #11 #15
        for dat in drwdat:
            xx=[]; yy=[]; zz=[]; wt=[]
            for cc,color,weit,rad in dat:
                xx.append(cc[0])
                yy.append(cc[1])
                zz.append(cc[2])
                wt.append(weit)
            if len(xx) > 0:
                sinarray = []
                cosarray = []
                for i in range(NSLICE + 1):
                    sinarray.append(sin(2.0 * pi * i / NSLICE))
                    cosarray.append(cos(2.0 * pi * i / NSLICE))
                glEnable(GL_LIGHTING)
                #color=self.model.mol.tube_color
                glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
            ###glLoadIdentity()
            # spline interpolation
            x = array(xx)
            y = array(yy)
            z = array(zz)
            #tckp, u = splprep([x, y, z], s=3.0, k=2, nest= -1)
            tckp, u = splprep([x, y, z], w=wt, s=20.0, k=3, nest= -1)
            xnew, ynew, znew = splev(linspace(0, 1, 4 * len(x)), tckp)
            npt = len(xnew)
            # postion array
            posarray = []
            for i in range(npt):
                x = xnew[i]
                y = ynew[i]
                z = znew[i]
                posarray.append(array([x, y, z]))
            # moving vector, and normal ventors
            vec0 = posarray[1] - posarray[0]
            if vec0[0] * vec0[0] > 0.00001:
                e0 = array([vec0[1], -vec0[0], 0.0])
            else:
                e0 = cross(vec0, array([1.0, 0.0, 0.0]))
            e0 /= linalg.norm(e0)
            e1 = cross(e0, vec0)
            e1 /= linalg.norm(e1)
            vecarray = [vec0]
            e0array = [e0]
            e1array = [e1]
            for i in range(1, npt):
                if i == npt - 1:
                    vec0 = posarray[i] - posarray[i - 1]
                else:
                    vec0 = posarray[i + 1] - posarray[i - 1]
                vecarray.append(vec0)
                e1 = cross(e0, vec0)
                e1 /= linalg.norm(e1)
                e1array.append(e1)
                e0 = cross(vec0, e1)
                e0 /= linalg.norm(e0)
                e0array.append(e0)
            for i in range(npt - 1):
                pos0 = posarray[i]
                pos1 = posarray[i + 1]
                e0_0 = e0array[i]
                e1_0 = e1array[i]
                e0_1 = e0array[i + 1]
                e1_1 = e1array[i + 1]
                glBegin(GL_TRIANGLE_STRIP)
                for j in range(NSLICE + 1):
                    u = sinarray[j]
                    v = cosarray[j]
                    vnorm = u * e0_0 + v * e1_0
                    pos = pos0 + rad * vnorm #self.rad_tube * vnorm
                    glNormal3f(vnorm[0], vnorm[1], vnorm[2])
                    glVertex3f(pos[0], pos[1], pos[2])
                    vnorm = u * e0_1 + v * e1_1
                    pos = pos1 + rad * vnorm #self.rad_tube * vnorm
                    glNormal3f(vnorm[0], vnorm[1], vnorm[2])
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()
            # disc
            for i in range(0, npt, npt - 1):
                pos0 = posarray[i]
                e0 = e0array[i]
                e1 = e1array[i]
                vec0 = vecarray[i]
                vec0 /= linalg.norm(vec0)
                if i == 0:
                    vec0 = -vec0
                glBegin(GL_POLYGON)
                glNormal3f(vec0[0], vec0[1], vec0[2])
                for j in range(NSLICE):
                    u = sinarray[j]
                    v = cosarray[j]
                    vnorm = u * e0 + v * e1
                    pos = pos0 + rad * vnorm #self.rad_tube * vnorm
                    glVertex3f(pos[0], pos[1], pos[2])
                glEnd()
    
    def DrawAtoms(self,data):
        """ Draw atom sphere
        
        :param lst data: [[i,model,coordinate,color,radius],...]
        """
        if len(data) <= 0: return
        #self.rad_cpk_scale=self.model.mol.rad_cpk_scale
        NSLICE = 15
        #for d in data:
        for idx,model,cc,color,rad in data:
            #color=d.color; draw_model=d.model; rad=d.radius; cc=d.cc
            #if draw_model == 3: rad *= self.rad_cpk_scale            
            pos=[0.0,0.0,0.0]
            pos[0]=float(cc[0]); pos[1]=float(cc[1]); pos[2]=float(cc[2])
            pos=array(pos)        
            if model == 0:
                glDisable(GL_LIGHTING)
                #!!!glLoadIdentity()
                glPushMatrix()
                #glColor3f(color[0], color[1], color[2])
                glColor4f(color[0], color[1], color[2],color[3])
                glTranslatef(pos[0], pos[1], pos[2])
                glutSolidSphere(rad, NSLICE, NSLICE) #self.rad_ball, NSLICE, NSLICE)                   
                glPopMatrix()
            if model == 1 or model == 2:
                glEnable(GL_LIGHTING)
                #!!!glLoadIdentity()
                glPushMatrix()
                glTranslatef(pos[0], pos[1], pos[2])
                glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
                
                glutSolidSphere(rad, NSLICE, NSLICE) #self.rad_ball, NSLICE, NSLICE
                  
                glPopMatrix()
            if model == 3:
                #rad = atom.GetRadius() * self.rad_cpk_scale
                glEnable(GL_LIGHTING)
                glPushMatrix()
                #glLoadIdentity()
                glTranslatef(pos[0], pos[1], pos[2])
                glMaterialfv(GL_FRONT, GL_DIFFUSE, color)
                glutSolidSphere(rad, NSLICE, NSLICE)                   
                glPopMatrix() 
 
    def DrawBonds(self,data):
        """ Draw bond line/stick
         
        :param lst data: [[i,model0,cc0,bndmulti0,cc0b,visible0,color0,thick0,j,model1,cc1,bndmulti1,cc1b,visible1,color1,thick1],..]
        """
        if len(data) <= 0: return
            
        NSLICE = 15
        # setting for line model
        glEnable(GL_LINE_SMOOTH);
        #
        #stickbold=2
        #glLineWidth(stickbold)
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA , GL_ONE_MINUS_SRC_ALPHA);
        for i,model0,cc0,bndmulti0,cc0b,visible0,color0,thick0,j,model1,cc1, \
                            bndmulti1,cc1b,visible1,color1,thick1 in data:
            pos0=[0.0,0.0,0.0]
            pos0[0]=cc0[0]; pos0[1]=cc0[1]; pos0[2]=cc0[2]
            pos0=array(pos0)
            if not visible0 and not visible1: continue    
            pos1=[0.0,0.0,0.0]
            pos1[0]=cc1[0]; pos1[1]=cc1[1]; pos1[2]=cc1[2]
            pos1=array(pos1)
            cc0b=array(cc0b); cc1b=array(cc1b)
            center=[0.0,0.0,0.0]
            center[0]=0.5*(pos0[0]+pos1[0])
            center[1]=0.5*(pos0[1]+pos1[1])
            center[2]=0.5*(pos0[2]+pos1[2])
            center=array(center)
            dm0_lin = ( model0 == 0 )
            dm0_stk = ( model0 == 1)
            dm0_bas = ( model0 == 2)
            dm1_lin = ( model1 == 0)
            dm1_stk = ( model1 == 1)
            dm1_bas = ( model1 == 2)
            # Line
            glDisable(GL_LIGHTING)
            glDisable(GL_LINE_STIPPLE)
            #!!!glLoadIdentity()
            if bndmulti0 >= 2: #= 2 or bndmulti0 == 3:
                v01 = pos1 - pos0
                vp = array([0.0,0.0,0.0])
                pos2=cc0b
                if len(pos2) <= 0: pos2=cc1b
                if len (pos2) <= 0: pos2=array([0.0,0.0,1.0])            
                v02 = pos2-pos0 
                vp = cross(v01, v02)
                if linalg.norm(vp) < 1.0e-10:
                    if v01[2] > 1.0e-10:
                        vp =array( [v01[1], -v01[0], 0.0] )
                    else:
                        vp =array( [v01[2], 0.0, -v01[0]] )
                vp2 = cross(v01, vp)
                vp2 /= linalg.norm(vp2)
                vp2 *= 0.1
            #if btype == BOND_TYPE.DOUBLE:
            if bndmulti0 == 1:
                if model0 == 0 and visible0:
                    # atom0 -> center
                    glLineWidth(thick0)    
                    glColor(color0)                           
                    glBegin(GL_LINES)
                    glVertex3fv(pos0)
                    glVertex3fv(center)
                    glEnd()
                if model1 == 0 and visible1:
                    # center -> atom1
                    glLineWidth(thick1)                        
                    glColor(color1)                           
                    glBegin(GL_LINES)
                    glVertex3fv(center)
                    glVertex3fv(pos1)
                    glEnd()
            #elif btype == BOND_TYPE.DOUBLE or btype == BOND_TYPE.TRIPLE:
            elif bndmulti0 == 2:
                # double bond
                #if dm0_lin and visible0:
                if model0 == 0 and visible0:
                    # atom0 -> center
                    glLineWidth(thick0)  
                    glColor(color0)
                    glBegin(GL_LINES)
                    glVertex3fv(pos0+vp2)
                    glVertex3fv(center+vp2)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(pos0-vp2)
                    glVertex3fv(center-vp2)
                    glEnd()                   
                #if dm1_lin and visible1:
                if model1 == 0 and visible1:
                    # center -> atom1
                    glLineWidth(thick1)  
                    glColor(color1)
                    glBegin(GL_LINES)
                    glVertex3fv(center+vp2)
                    glVertex3fv(pos1+vp2)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(center-vp2)
                    glVertex3fv(pos1-vp2)
                    glEnd()

            elif bndmulti0 == 3:
                # triple bond
                #if dm0_lin and visible0:
                if model0 == 0 and visible0:
                    # atom0 -> center
                    glLineWidth(thick0)  
                    glColor(color0)
                    glBegin(GL_LINES)
                    glVertex3fv(pos0+vp2)
                    glVertex3fv(center+vp2)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(pos0)
                    glVertex3fv(center)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(pos0-vp2)
                    glVertex3fv(center-vp2)
                    glEnd()

                #if dm1_lin and visible1:
                if model1 == 0 and visible1:
                    # center -> atom1
                    glLineWidth(thick1)  
                    glColor(color1)
                    glBegin(GL_LINES)
                    glVertex3fv(center+vp2)
                    glVertex3fv(pos1+vp2)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(center)
                    glVertex3fv(pos1)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3fv(center-vp2)
                    glVertex3fv(pos1-vp2)
                    glEnd()

            elif bndmulti0 == 4:
                # double bond
                #if dm0_lin and visible0:
                if model0 == 0 and visible0:
                    # atom0 -> center
                    glLineWidth(thick0)  
                    glColor(color0)
                    glBegin(GL_LINES)
                    glVertex3fv(pos0+vp2)
                    glVertex3fv(center+vp2)
                    glEnd()

                    glEnable(GL_LINE_STIPPLE)
                    glLineStipple(2,0xcccc) #1, 0xAAAA) #2,0xF0F0) #5,0x5555) #2,0xcccc) #1,0xF0F0)
                    
                    glBegin(GL_LINES)
                    glVertex3fv(pos0-vp2)
                    glVertex3fv(center-vp2)
                    glEnd()
                    
                    glDisable(GL_LINE_STIPPLE)                    
                #if dm1_lin and visible1:
                if model1 == 0 and visible1:
                    # center -> atom1
                    #glDisable(GL_LINE_STIPPLE)
                    glLineWidth(thick1)  
                    glColor(color1)
                    glBegin(GL_LINES)
                    glVertex3fv(center+vp2)
                    glVertex3fv(pos1+vp2)
                    glEnd()
                    
                    glEnable(GL_LINE_STIPPLE)
                    glLineStipple(2,0xcccc) #1, 0xAAAA) #2,0xF0F0)#5,0x5555) #2,0xcccc) #1,0xF0F0)
                   
                    glBegin(GL_LINES)
                    glVertex3fv(center-vp2)
                    glVertex3fv(pos1-vp2)
                    glEnd()
                    glDisable(GL_LINE_STIPPLE)
            """
            else: # aromatic bond
                aroma_center = 0  # dummy not working !!bond.GetAromaCenter()
                vp0 = aroma_center - pos0
                vp1 = aroma_center - pos1
                vp0 /= linalg.norm(vp0)
                vp1 /= linalg.norm(vp1)
                vp0 *= 0.2
                vp1 *= 0.2
                vpc = ( vp0 + vp1 ) * 0.5
                if dm0_lin and visible0:
                    # atom0 -> center
                    glColor(color0)
                    glBegin(GL_LINES)
                    glVertex3fv(pos0)
                    glVertex3fv(center)
                    glEnd()
                    glEnable(GL_LINE_STIPPLE)
                    glLineStipple(1 , 0xF0F0)
                    glBegin(GL_LINES)
                    glVertex3fv(pos0+vp0)
                    glVertex3fv(center+vpc)
                    glEnd()
                    glDisable(GL_LINE_STIPPLE)

                if dm1_lin and visible1:
                    # center -> atom1
                    glColor(color1)
                    glBegin(GL_LINES)
                    glVertex3fv(center)
                    glVertex3fv(pos1)
                    glEnd()
                    glEnable(GL_LINE_STIPPLE)
                    glLineStipple(1 , 0xF0F0)
                    glBegin(GL_LINES)
                    glVertex3fv(center+vpc)
                    glVertex3fv(pos1+vp1)
                    glEnd()
                    glDisable(GL_LINE_STIPPLE)
            """
            # Stick
            if dm0_bas or dm0_stk or dm1_bas or dm1_stk:
                vb = center - pos0
                length = linalg.norm(vb)
                axis = array([0.0, 0.0, length]) + vb
                glEnable(GL_LIGHTING)
                #!!!glLoadIdentity()
                glPushMatrix()                                                        
                glTranslatef(pos0[0], pos0[1], pos0[2])
                glRotatef(180.0, axis[0], axis[1], axis[2])
                if ( dm0_bas or dm0_stk ) and visible0:
                    # atom0 -> center 
                    glPushMatrix()
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, color0)
                    gluQuadricDrawStyle(self.qobj, GLU_FILL)
                    gluQuadricNormals(self.qobj, GLU_SMOOTH)
                    gluCylinder(self.qobj, 0.1*thick0, 0.1*thick0, length, NSLICE, 1)
                    if not ( ( dm1_bas or dm1_stk ) and visible1 ):
                        glPushMatrix()
                        glTranslatef(0.0, 0.0, length)
                        gluDisk(self.qobj, 0.0, 0.1*thick0, NSLICE, 1)
                        glPopMatrix()
                    if dm0_stk:
                        glPushMatrix()
                        gluQuadricOrientation(self.qobj, GLU_INSIDE)
                        gluDisk(self.qobj, 0.0, 0.1*thick1, NSLICE, 1)
                        gluQuadricOrientation(self.qobj, GLU_OUTSIDE)
                        glPopMatrix()
                    glPopMatrix()
                if ( dm1_bas or dm1_stk ) and (visible1 or visible0):    
                    # center -> atom1
                    glPushMatrix()
                    glMaterialfv(GL_FRONT, GL_DIFFUSE, color1)
                    glTranslatef(0.0, 0.0, length)
                    gluQuadricDrawStyle(self.qobj, GLU_FILL)
                    gluQuadricNormals(self.qobj, GLU_SMOOTH)
                    gluCylinder(self.qobj, 0.1*thick1, 0.1*thick1, length, NSLICE, 1)
                    if not ( ( dm0_bas or dm0_stk ) and visible0 ):
                        glPushMatrix()
                        gluQuadricOrientation(self.qobj, GLU_INSIDE)
                        gluDisk(self.qobj, 0.0, 0.1*thick0, NSLICE, 1)
                        gluQuadricOrientation(self.qobj, GLU_OUTSIDE)
                        glPopMatrix()
                    if dm1_stk:
                        glPushMatrix()
                        glTranslatef(0.0, 0.0, length)
                        gluDisk(self.qobj, 0.0, 0.1*thick1, NSLICE, 1)
                        glPopMatrix()
                    glPopMatrix()
                glPopMatrix()
                    
    def MakeDisplayList(self):
        """ Make display list """
        self.busy=True
        #self.mdlwin.BusyIndicator('On','Drawing ..')
        try:
            if self.DisplayList: glDeleteLists(self.DisplayList, 1)
            NSLICE = 15
            self.DisplayList = glGenLists(1)
            self.gllst=glNewList(self.DisplayList, GL_COMPILE)
            glMatrixMode(GL_MODELVIEW)
            # for Cylinder Stick
            self.qobj = gluNewQuadric()
            #          
            arwobj='rot-axis:ARROW'
            if self.DrawObjDic.has_key(arwobj):
                drawmethod=self.DrawObjDic[arwobj][0]; data=self.DrawObjDic[arwobj][1]
                drawmethod(data)
            atmobj='atoms:ATOMS'
            if self.DrawObjDic.has_key(atmobj):
                drawmethod=self.DrawObjDic[atmobj][0]; data=self.DrawObjDic[atmobj][1]
                drawmethod(data)
            bndobj='bonds:BONDS'
            if self.DrawObjDic.has_key(bndobj):
                drawmethod=self.DrawObjDic[bndobj][0]; data=self.DrawObjDic[bndobj][1]
                drawmethod(data)
            #
            for label,draw in self.DrawObjDic.iteritems():
                if label == atmobj or label == bndobj or label == arwobj: continue
                drawmethod=self.DrawObjDic[label][0]; data=self.DrawObjDic[label][1]
                if not drawmethod: continue
                drawmethod(data)

            if len(self.mess) > 0:
                items=self.mess.split(')',1)
                mess=items[0]+':) [label='+label+'] '+items[1]
                self.Message(mess)
                self.mess=''

            gluDeleteQuadric(self.qobj)

            glEndList()

            glFlush()
        except:
            mess=self.classname+'(MakedisplayList):Fatal error ocuured. '
            mess=mess+'Quit the program.'
            self.mdlwin.model.Quit()

        self.updated=False
        self.busy=False
                
    def Draw(self):
        """ Draw currently set objects (by the SetDrawData method) on canvas
        """
        if not self.gl_initialized: return
        self.busy=True
        # busyindicator
        self.mdlwin.BusyIndicator('On','Drawing ..') 
        #    try: self.mdlwin.Message('Drawing ...',1,'')
        #    except: pass
        #
        try:
            if not self.DisplayList or self.updated:
                self.MakeDisplayList()     
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if self.stereo == 0: # off
                self.SetCamera()
                glCallList(self.DisplayList)
            
            if self.stereo == 1: # cross eye
                self.SetStereoCamera(True, False)
                glCallList(self.DisplayList)
                self.SetStereoCamera(False, True)
                glCallList(self.DisplayList)

            if self.stereo == 2: # pararell eye
                self.SetStereoCamera(True, True)
                glCallList(self.DisplayList)
                self.SetStereoCamera(False, False)
                glCallList(self.DisplayList)

            if self.canvas:
                self.canvas.SwapBuffers()
        except:
            mess=self.classname+'(Draw): Fatal error occured. '
            mess=mess+'Quit the program.'
            self.mdlwin.model.Quit()
                
        self.busy=False

        self.mdlwin.BusyIndicator('Off')
        #    try: self.mdlwin.Message('',1,'')
        #    except: pass

    def Paint(self):
        """ Paint 
        """
        if lib.GetPlatform() == 'WINDOWS':
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        else: wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        
        self.canvas.SetCurrent()
        if not self.gl_initialized:
            self.InitGL()
            self.gl_initialized=True
        self.Draw()
        
    def EraseBG(self):
        """ not used """
        pass # Do nothing, to aviod flashing on MWWin
    
    def FitMolecular(self,mol):
        """ Fit molecule to screen (recompute center and ratio).
        
        :param obj mol: instance of Molecule() class
        :seealso: molec.Molecule() class
        """
        ctr = array(self.center)
        eye = array(self.eyepos)
        upw = array(self.upward)
        #
        ec = ctr - eye  # eye -> center
        nvc = cross(ec, upw)  # unit vecter vertical to ec and upward
        nvc /= linalg.norm(nvc)
        #
        dx = -dot(nvc, ctr); dy = -dot(upw, ctr)
        xmin = sys.maxint; ymin = sys.maxint
        xmax = -sys.maxint - 1; ymax = -sys.maxint - 1
        #
        #if len(mol.atm) > 1:
        nmol=0
        for atom in mol.atm:
            if not atom.show: continue
            nmol += 1
            pos=[atom.cc[0],atom.cc[1],atom.cc[2]]
            pos=array(pos)
            x = dot(nvc, pos) + dx
            y = dot(upw, pos) + dy
            xmin = min(xmin, x); xmax = max(xmax, x)
            ymin = min(ymin, y); ymax = max(ymax, y)
            margin = 1.2 #1.0 #1.2
            w = max(xmax, -xmin) * 2.0 * margin
            h = max(ymax, -ymin) * 2.0 * margin
        #else:
        if nmol <= 1: w=5.0; h=5.0
        #
        self.canvas_size = self.canvas.GetSize()
        [canvas_w,canvas_h] = self.canvas_size
        ratio_w = w / float(canvas_w)
        ratio_h = h / float(canvas_h)
        if ratio_w > ratio_h:
            h = ratio_w * float(canvas_h)
            self.ratio = ratio_w
        else:
            w = ratio_h * float(canvas_w)
            self.ratio = ratio_h
                        
    def FindCenter(self,mol):
        """ Compute center of molecule
        
        :param obj mol: instance of Molecule class
        :return: coordinate of center, [x(float),y(float),z(float)]
        """
        natm=len(mol.atm)
        if natm == 0: return (0.0, 0.0, 0.0)
        xsum = 0.0; ysum = 0.0; zsum = 0.0
        nmol=0
        for atom in mol.atm:
            if not atom.show: continue
            xsum += atom.cc[0]; ysum += atom.cc[1]; zsum += atom.cc[2]
            nmol += 1
        xave = xsum / nmol; yave = ysum / nmol; zave = zsum / nmol     
        return (xave, yave, zave)
    
    def CenterMolecular(self,mol):
        """ Set center and eyeposition to cenetr
        
        :param obj mol: instance of Molecule class
        """
        ctr = array(self.FindCenter(mol))
        dif = ctr - array(self.center)
        eye = array(self.eyepos) + dif
        self.center = [ ctr[0], ctr[1], ctr[2] ]
        self.eyepos = [ eye[0], eye[1], eye[2] ]

    def SetCenterOfRot(self,ctr):
        """ Reset senter of rotation
        
        :param lst ctr: [x(float),y(float),z(float)]
        :seealso: CenterMolecular(), FindCenter()
        """
        #ctr = array(self.FindCenter())
        self.centersav=self.center
        self.eyepossav=self.eyepos
        self.ratiosav=self.ratio
        dif = ctr - array(self.center)
        eye = array(self.eyepos) + dif
        self.center = [ ctr[0], ctr[1], ctr[2] ]
        self.eyepos = [ eye[0], eye[1], eye[2] ]

    def RecoverCenterOfRot(self):
        """ Recover center of moleculae """
        
        self.center=self.centersav
        self.eyepos=self.eyepossav
        self.ratio=self.ratiosav
        
    def GetCenter(self):
        """ Return center of rotation
        
        :return: self.center - [x(float),y(float),z(float)]
        :rtype: lst
        """
        # center of rotation
        # ret center[lst]: [x(float),y(float),z(float)]
        return self.center

    def GetCanvasSize(self):
        """ Return canvas size
        
        :return: canvas size - [width(int),hight(int)]
        """
        return self.canvas.GetSize() 

    def SetViewAxis(self, xyz):
        """ Set view axis
        
        :param str xyz: option xyz is either 'x', 'y' or 'z'
        """
        self.eyepos[0] = self.center[0]
        self.eyepos[1] = self.center[1]
        self.eyepos[2] = self.center[2]
        self.upward = [0.0, 0.0, 0.0]
        if xyz == 'X':
            self.eyepos[0] += 1000.0
            self.upward[2] += 1.0
        if xyz == 'Y':
            self.eyepos[1] += 1000.0
            self.upward[0] += 1.0
        if xyz == 'Z':
            self.eyepos[2] += 1000.0
            self.upward[1] += 1.0

    def SetAtomCC(self,atmcc):
        """ Set atom ccordinates (set atomcc to self.atmcc)
        
        :param lst atmcc: atom coordinate list, [[x(float),y(float),z(float)],..]
        """
        self.atmcc=atmcc

    def GetCoordinateMinMax(self):
        """ Return Min/Max coordinates in canvas scale
        
        :return: xmin(float),xmax(float),ymin(float),ymax(float)
        """
        [canvas_w,canvas_h] = self.canvas.GetSize()
        w = canvas_w * self.ratio; h = canvas_h * self.ratio
        xmin = -0.5 * w; xmax = 0.5 * w
        ymin = -0.5 * h; ymax = 0.5 * h       
        unit=1.0/self.ratio
        return xmin,xmax,ymin,ymax,unit
        
    def ConvertRasterPosToCoordinate(self,pos):
        """
        Convert raster position(pixcel data) to coordinates(in Angstroms)
        
        :param lst pos: pos=[x(int),y(int)] in pixcel
        :return: cc=[x(floast),y(float)] in angstroms
        :rtype: lst
        """
        [w,h]=self.canvas.GetSize()
        xras=pos[0]/w; yras=(h-pos[1])/h
        xmin,xmax,ymin,ymax,unit=self.GetCoordinateMinMax()
        x=(xmax-xmin)*xras; y=(ymax-ymin)/yras
        return [x,y]

    def GetCoordinateAt(self,hori,hpix,vert,vpix):
        """
        Return Coordinate (Angstrom) at position(pixels) form canvas edge.
        
        :param str hiri: 'left','right' or 'middle'
        :param int hpix: distance(number of pixcels) form 'hori'
        :param str vert: 'top','bottom' or 'middle'
        :param int vpx: distance(number of pixels) form 'vert'
        """
        xmin,xmax,ymin,ymax,unit=self.GetCoordinateMinMax()
        if hori == 'left': x=xmin+hpix*self.ratio
        elif hori == 'right': x=xmax-hpix*self.ratio
        else: x=(xmax-xmin)*0.5+hpix*self.ratio
        if vert == 'top': y=ymax-vpix*self.ratio
        elif vert == 'bottom': y=ymin+vpix*self.ratio
        else: y=(ymax-ymin)*0.5+vpix*self.ratio 
        return [x,y]
        
    def SetCamera(self):
        """ Set camera """
        #!!!canvas_size = self.frame.canvas.GetSize()
        canvas_size = self.canvas.GetSize()
        #canvas_size = self.mdlwin.GetClientSize()
        canvas_w = canvas_size[0]
        canvas_h = canvas_size[1]
        w = canvas_w * self.ratio
        h = canvas_h * self.ratio
        left = -0.5 * w
        right = 0.5 * w
        bottom = -0.5 * h
        top = 0.5 * h
        # Clear Background
        glClearColor(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
        # set projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(left, right, bottom, top, -1000.0, 2000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.eyepos[0], self.eyepos[1], self.eyepos[2],
                  self.center[0], self.center[1], self.center[2],
                  self.upward[0], self.upward[1], self.upward[2])
        # set light position
        light_position = [self.eyepos[0], self.eyepos[1], self.eyepos[2], 0.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        # set viewport
        #!!!canvas_size = self.frame.canvas.GetSize()
        canvas_size = self.mdlwin.GetClientSize()
        glViewport(0,0,canvas_size[0],canvas_size[1])
        #
        if self.fog:
            self.rasposz=self.FindAtomRasPosZ() 
            self.rasposzmin=min(self.rasposz)
            self.rasposzmax=max(self.rasposz)
            zmin=self.rasposzmin; zmax=self.rasposzmax
            f=1.0-float(self.fogscale)/float(self.fogscale_max)
            dmax=zmax
            dmin=zmin+(zmax-zmin)*(1.0-f)**2                                            
            glEnable(GL_FOG)
            glFogfv(GL_FOG_COLOR, self.bgcolor)
            glFogi(GL_FOG_MODE , GL_LINEAR)
            glFogf(GL_FOG_START , dmin)
            glFogf(GL_FOG_END , dmax)
        else:
            glDisable(GL_FOG)

    def FindAtomRasPosZ(self):
        """ Compute Z-coordinate of atom raster positions
        
        :return: rasposz - z coordinate of raster positon, [z(float),...]
        :rtype: lst
        """
        rasposz=[] # kk added       
        eye = array(self.eyepos)
        ctr = array(self.center)
        e2c = ctr - eye
        e2c /= linalg.norm(e2c)
        for i,pos in self.atmcc:
            pos=array(pos)
            e2p = pos - eye
            d = dot(e2p, e2c)
            rasposz.append(d) 
        return rasposz        
                
    def SetRasterPosition(self):
        """ Set raster position """
        #!!!canvas_size = self.frame.canvas.GetSize()
        canvas_size = self.canvas.GetSize()
        #canvas_size = self.mdlwin.GetClientSize()
        canvas_w = canvas_size[0]
        canvas_h = canvas_size[1]

        w = canvas_w * self.ratio
        h = canvas_h * self.ratio

        left = -0.5 * w
        right = 0.5 * w
        bottom = -0.5 * h
        top = 0.5 * h
        #natm=len(self.atomdata); nbnd=len(self.bonddata)
        #if (self.fog or self.section) and (natm+nbnd) > 0:
        self.rasposz=[] # kk added 
        self.raszmax=0; self.raszmin=0       
        if len(self.atmcc) > 0:
            eye = array(self.eyepos)
            ctr = array(self.center)
            e2c = ctr - eye
            e2c /= linalg.norm(e2c)
            dmin = sys.float_info.max
            dmax = 0.0
            #
            #atmdic=self.MakeAtmPosDic()            
            for i in range(len(self.atmcc)):
                pos=self.atmcc[i][1]
                e2p = pos - eye
                d = dot(e2p, e2c)
                dmin = min(dmin, d)
                dmax = max(dmax, d)                
                self.rasposz.append(d*self.ratio) # kk added
                self.raszmax=dmax; self.raszmin=dmin

    def SetStereoCamera(self, bCameraLeft, bViewportLeft):
        """ Set stereo camera
        
        :param bool bCameraLeft: 
        :param bool bViewportLeft:
        """
        angle = pi * 3.5 / 180.0

        canvas_size = self.canvas.GetSize()
        #canvas_size = self.mdlwin.GetClientSize()
        canvas_w = canvas_size[0] / 2
        canvas_h = canvas_size[1]

        w = canvas_w * self.ratio
        h = canvas_h * self.ratio

        left = -0.5 * w
        right = 0.5 * w
        bottom = -0.5 * h
        top = 0.5 * h

        eye = array(self.eyepos)
        ctr = array(self.center)
        upw = array(self.upward)

        c2e = eye - ctr
        vleft = cross(c2e, upw)

        if bCameraLeft:
            c2enew = c2e * cos(angle) + vleft * sin(angle)
        else:
            c2enew = c2e * cos(angle) - vleft * sin(angle)
        eyenew = ctr + c2enew

        # set light position
        light_position = [self.eyepos[0], self.eyepos[1], self.eyepos[2], 0.0]
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)

        # set projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(left, right, bottom, top, -1000.0, 2000.0)
        gluLookAt(eyenew[0], eyenew[1], eyenew[2],
                  self.center[0], self.center[1], self.center[2],
                  self.upward[0], self.upward[1], self.upward[2])
        # set viewport
        canvas_size = self.canvas.GetSize()
        #canvas_size = self.mdlwin.GetClientSize()
        if bViewportLeft:
            glViewport(0, 0, canvas_size[0] / 2, canvas_size[1])
        else:
            glViewport(canvas_size[0] / 2, 0, canvas_size[0] / 2, canvas_size[1])

    def ResetRotation(self):
        """ Set view angle to initial value """
        self.eyepos = [0.0, 0.0, 300.0]
        self.upward = [0.0, 1.0, 0.0]
    
    def RotateByMatrix(self,rotmat):
        """ Rotate view by matrix
        
        :param lst rotmat: rotation matrix
        """
        rotmat=array(rotmat)
        ctr = array(self.center)
        eye = array(self.eyepos)
        upw = array(self.upward)

        ec = ctr - eye
        ec = dot(rotmat, ec)
        #ec, = array(ec)
        eye = ctr - ec
        upw = dot(rotmat, upw)
        #upw, = array(upw)
        upw /= linalg.norm(upw)
        #
        self.eyepos = [ eye[0], eye[1], eye[2] ]
        self.upward = [ upw[0], upw[1], upw[2] ]
        
    def MouseRotate(self,rotaxis,rot):
        """ Rotate view
        
        :param str rotaxis: 'x', 'y', 'z', 'inplane' or 'free'
        :params lst rot: mouse movement vector [x(int),y(int)]
        """
        # rotaxis(str): 'free','inplane','x','y', or 'z'
        # rot(float): rotation angle
        axis=[0.0,0.0,0.0]
        rot[1] = -rot[1]  #  Origin is left-top in wxPython
        ctr = array(self.center)
        eye = array(self.eyepos)
        upw = array(self.upward)
        ec = ctr - eye
        if rotaxis == 'x':
            if rot[0] > 0: axis[0]=1.0
            else: axis[0]=-1.0
        elif rotaxis == 'y':
            if rot[0] > 0: axis[1]=1.0
            else: axis[1]=-1.0
        elif rotaxis == 'z':
            if rot[0] > 0: axis[2]=1.0
            else: axis[2]=-1.0
        elif rotaxis == 'inplane': axis=eye*rot[0]
        elif rotaxis == 'free':
            # x unit vector in canvas
            nvc = cross(ec, upw)            
            nvc /= linalg.norm(nvc)
            # rotation axis
            axis = nvc * rot[1] - upw * rot[0]
        nrm=linalg.norm(axis)
        if nrm < 0.00000001: return
        axis /= nrm # linalg.norm(axis)
        nx = axis[0];  ny = axis[1]; nz = axis[2]
        
        PI2 = pi * 2.0
        t = sqrt(rot[0] * rot[0] + rot[1] * rot[1]) * PI2 / 300.0
        c = cos(t)
        s = sin(t)
        c1 = 1 - c
        rot = matrix([[ nx * nx * c1 + c     , nx * ny * c1 - nz * s, nx * nz * c1 + ny * s ],
                      [ ny * nx * c1 + nz * s, ny * ny * c1 + c     , ny * nz * c1 - nx * s ],
                      [ nz * nx * c1 - ny * s, nz * ny * c1 + nx * s, nz * nz * c1 + c      ]])

        ec = dot(rot, ec)
        ec, = array(ec)
        eye = ctr - ec

        upw = dot(rot, upw)
        upw, = array(upw)
        upw /= linalg.norm(upw)

        self.eyepos = [ eye[0], eye[1], eye[2] ]
        self.upward = [ upw[0], upw[1], upw[2] ]

    def MouseTranslate(self, dif):
        """ Translate molecule view
        
        :param str dif: mouse movement vector, [x(int),y(int)]
        """
        dif[1] = -dif[1]  #  Origin is left-top in wxPython

        ctr = array(self.center)
        eye = array(self.eyepos)
        upw = array(self.upward)

        ec = ctr - eye

        # x unit vector in canvas
        nvc = cross(ec, upw)
        nvc /= linalg.norm(nvc)

        # moved vector
        mov = (nvc * dif[0] + upw * dif[1]) * self.ratio
        ctr -= mov
        eye -= mov

        self.eyepos = [ eye[0], eye[1], eye[2] ]
        self.center = [ ctr[0], ctr[1], ctr[2] ]

    def Zoom(self, rot):
        """ Zoom view
        
        :param float rot: rotation angle of mouse wheel 
        """
        self.ratio *= 1.0 + rot * 0.001

    @staticmethod
    def RGB2Code(RGB):
        """ convert r,g,b (RGB) to a packed code
        
        :return: code - packed value
        :seealso: Code2RGB()
        """
        r = int(255.0 * RGB[0])
        g = int(255.0 * RGB[1])
        b = int(255.0 * RGB[2])
        rgb = (r * 256 + g) * 256 + b
        return "#%06x" % rgb

    @staticmethod
    def Code2RGB(colorcode):
        """ convert code to r,g,b (RGB)
        
        :return: RGB - [r,g,b,a] (a=1.0)
        :seealso: RGB2Code()
        """
        r = colorcode[1:3]
        r = int(r, 16)
        r = int(colorcode[1:3], 16) / 255.0
        g = int(colorcode[3:5], 16) / 255.0
        b = int(colorcode[5:7], 16) / 255.0
        RGB = [r, g, b, 1.0]
        return RGB

    def SetStereoView(self, stereo):
        """ Set stereo view option (self.stereo=stereo) """
        self.stereo = stereo
 
    def SetBGColor(self,color):
        """ Set background color
        
        :param lst color: background color [R,G,B,A]
        """
        self.bgcolor=color
    
    def SetUpdated(self,value):
        """ Set update flag (self.update=update)
        
        :param bool value: True or False
        """
        self.updated=value
        
    def GetUpdated(self):
        """ Return update flag
        
        :return: update(=self.update)
        :rtype: bool
        """
        return self.updated
    
    def SetShowBusyCursor(self,on):
        """ dummy """
        #self.showbusycusor=on
        return
    
    def SetShowDrawingMessage(self,on):
        self.showdrawingmess=on
             
    def SetFogScale(self,on,fogscale):
        """ Set fogscale
        
        :param bool on: True for on, False for off
        :param int fogscale: 0(dark)-15(bright)
        """
        self.fog=on
        if not on: self.fogscale=self.fogscale_max
        else: self.fogscale=fogscale
    
    def GetFogScale(self):
        """ Return fog scale value (0-15)
        
        :return: fogscale(float) - =self.fogscale
        """
        return self.fogscale

    def GetViewParams(self):
        """ Return view paramters (eye position,center, upward, ratio)
        
        :return: eyepos(lst) - [x(float],y[float),z(float)]
        :return: center(lst) - [x(float],y[float),z(float)]
        :return: upward(lst) - [x(float],y[float),z(float)]
        :return: ratio(float) - angstroms / pixcel
        :seealso: SetViewParams()
        """
        return self.eyepos,self.center,self.upward,self.ratio
    
    def SetViewParams(self,eyepos,center,upward,ratio):
        """ Set view paramters
        
        :param lst eyepos: [x(float],y[float),z(float)]
        :param lst center: [x(float],y[float),z(float)]
        :param lst upward: [x(float],y[float),z(float)]
        :param float ratio: angstroms / pixcel
        :seealso: GetViewParams()
        """
        self.eyepos=eyepos; self.center=center; self.upward=upward; self.ratio=ratio
             
    def GetLabelDic(self):
        """ Return draw object label dictionary
    
        :return: label - self.label
        :seealso: SetDrawData()
        """
        return self.labeldic
