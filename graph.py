#!/bin/sh
# -*- coding:utf-8


import os
import wx 
import copy

#import matplotlib
#matplotlib.interactive( True )
#from matplotlib.figure import Figure
#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx

import ctrl
import lib
import const
import fumodel

class BarGraph(wx.Panel):
    # plot bargraph
    def __init__(self,parent,id,graph,pos,size,bgcolor):
        wx.Panel.__init__(self,parent,id,pos=pos,size=size) #,style=wx.MINIMIZE_BOX ) #,
        #       style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent # pltpan
        self.graph=graph # fugraph
        # background color
        self.buffer=None
        self.bgcolor=bgcolor
        self.SetBackgroundColour(self.bgcolor)
        self.font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        self.fontsize=[6,10]
        self.fontcolor='black'
        # set graph size
        self.size=self.GetClientSize()
        self.wplt=self.size[0]; self.hplt=self.size[1]
        # title and axis labels
        self.title='' # title text 
        self.xlabel='' # title for x-axis
        self.ylabel='' # title for y-axis
        # plot data
        self.ndata=0 # number of data
        self.data=[] # plot data
        self.order=[] # order of plot

        self.itemlist=self.SetDefaultItemList()
        self.extradata=False # only 1 extra data is allowed
        self.extradatalabel='' # label of extra data
        self.extposivalue=0.0
        
        self.maxplotdata=0 # number of plot data; ndata or ndata+1(extra)
        self.begindata=0 # the first sequence number of data to plot
        self.ifocus=1 # seq. number of data to be drawn with thick frame
        # remark
        self.remarklist=[]
        self.remarkboxsize=[10,8] # tile:[width,hight]
        self.wremark=0 # 10  width of remark
        self.rank=10 #
        # x-axis range
        self.wytitle=30
        self.wylabel=50
        self.fvaluemess=False; fvalue=""
        #self.xinipos=self.wytitle+self.wylabel+10
        #self.xendpos=self.wplt-self.wremark-15

        self.xunit=12 # barwidth*2+2
        self.barwidth=5
        self.hxtitle=20 # x axis title hight
        self.hxlabel=30
        # y-axis range
        self.htitle=25 # title hight
        #self.yinipos=self.hplt-self.htitle-self.hxtitle-self.hxlabel-10
        #self.yendpos=self.htitle+10
        self.yrangemin=-50.0  # +/- y max value
        self.yrangemax=50.0
        self.yrange=self.yrangemax
        self.yunit=0 # =(self.yinipos-self.yendpos)/(2.0*self.yrange)
        #self.rankposi=10; self.ranknega=10
        self.scaleoutposi=0.0; self.scaleoutnega=0.0
        # additional info
        self.addinfo=[]
        # mouse operation
        self.mouseleftdown=False
        self.mousepos=[0,0]
        # set buffer for plot
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        # activate mouse event drivers
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        #self.Bind(wx.EVT_SIZE,self.OnResize)
        #
        self.SetPlotSize(self.wplt,self.hplt)

    def SetBackgroundColor(self,color):
        self.bgcolor=color
        self.Plot(True)
    
    def SetRankColor(self,negacolor,posicolor,negascaleoutcolor,posiscaleoutcolor):
        self.negacolor=negacolor
        self.posicolor=posicolor
        self.negascaleoutcolor=negascaleoutcolor
        self.posiscaleoutcolor=posiscaleoutcolor
        self.Plot(True)
    
    def SetDefaultItemList(self):
        c1=const.RGBColor255['gray'] #['black']
        c2=const.RGBColor255['gold'] #['yellow']
        c3=const.RGBColor255['red']
        c4=const.RGBColor255['green']
        c5=const.RGBColor255['magenta']
        c6=const.RGBColor255['white']
        itemlist=[['1',c1],['2',c2],['3',c3],['4',c4],['5',c5],['6',c6]] 
        return itemlist
    
    def SetData(self,data,order):
        # data: [1,data1,data2,...,[2,..],[extradatalabe,extradata]]
        # extradata: True or False
        self.data=data
        self.ndata=len(data)
        self.order=order
        if len(order) <= 0:
            for i in range(self.ndata): self.order.append(i)
        
        self.maxplotdata=len(self.data)+1

    def SetItemNameAndColor(self,itemlist):
        # itemlist:[[item name,itemcolor],...]
        self.itemlist=itemlist

    def SetAdditionalInfo(self,info):
        if len(info) <= 0: self.addinfo=[]
        else:
            self.addinfo=[]
            for s in info:
                self.addinfo.append(s)

    def SetTitle(self,title):
        self.title=title    
    
    def SetAxisLabel(self,xlabel,ylabel):
        self.xlabel=xlabel
        self.ylabel=ylabel
        
    def SetYRange(self,ymin,ymax):
        self.yrangemin=ymin
        self.yrangemax=ymax
        self.yrange=self.yrangemax
        self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)      
    #def SetBeginDataNumber(self,number):
    #    self.begindata=number

    def SetRemark(self,remarkboxsize,remarklist):
        # set remarklist and itemlist
        # remarklist: ['label',color],..]
        self.remarkboxsiz=remarkboxsize
        self.remarklist=remarklist
        self.itemlist=remarklist
        if len(remarklist) <= 0: self.wremark=0
        else: self.wremark=55
        self.xendpos=self.wplt-self.wremark-15

    def SetFont(self,font,fontsize):
        # font: wxfont, fontsize:[w,h] in pixels
        self.font=font
        self.fontsize=fontsize
                
    def Plot(self,on):
        self.ndata=len(self.data)        
        if self.ndata <= 0: return
        #!!!!!self.SetPlotRange()
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        dc=wx.BufferedDC(None,self.buffer)
        backBrush=wx.Brush(self.bgcolor,wx.SOLID) #'white', wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()
        if not on: return
        # plot
        dc=wx.BufferedDC(wx.ClientDC(self),self.buffer)
        
        dc.SetFont(self.font)
        
        orgy=self.FindYpos(0.0)
        #self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        hmax=self.yrange*self.yunit
        ndat=self.ndata
        ###self.maxplotdata=ndat+1
        nitem=len(self.data[0])
        
        if nitem < 2:
            dlg=lib.MessageBoxOK("No item to plot in data.","BarGraph(Plot)")
            return        
        for i in range(self.begindata,ndat): #self.nfrg):
            ii=self.order[i]
            x=self.FindXpos(i)
            if x > self.xendpos: continue
            if nitem > 2: x += 2
            else: x += 4
            xtxt=x-2 #+3
            #    
            value=self.data[ii][1]
            hight=abs(value)*self.yunit
            if hight > hmax:
                hight=hmax
                ys=self.yinipos
                if value > 0: ys=self.yendpos-10
                dc.DrawText("*",xtxt+2,ys) # mark scale out
            y=orgy
            if value > 0.0:
                y=orgy-hight
            item=self.itemlist[0][0]; col=self.itemlist[0][1]
            dc.SetBrush(wx.Brush(col,wx.SOLID))
            #
            col0='lightgray' #const.RGBColor255['gray01'] #col # 'gray01' #'lightgray'
            dc.SetPen(wx.Pen(col0,1)) #,1))
            if y < orgy: y += 1
            dc.DrawRectangle(x,y,self.barwidth,hight)
            if nitem > 2:
                x += 4
                self.PlotItemsInStackBar(dc,ii,x)
        # draw title,axis labels
        self.DrawTitle(dc)
        self.DrawAxisLabel(dc)
        #
        self.DrawYAxis(dc)
        self.DrawXAxis(dc)
        # 
        if self.fvaluemess: self.DrawFunctionValue(dc)
        # draw remark
        if len(self.remarklist) > 0:
            self.DrawRemark(dc)
        # needed for Mac OSX
        self.Refresh()
        self.Update()
                          
    def DrawTitle(self,dc):
        if len(self.title) > 0:
            x=self.wplt/2
            ltxt=len(self.title)*self.fontsize[0]
            x -= ltxt/2
            y=10
            dc.DrawText(self.title,x,y)
    
    def DrawFunctionValue(self,dc):
        x=self.FindXpos(self.begindata)+20; y=25
        dc.DrawText(self.fvalue,x,y)
    
    def DrawAxisLabel(self,dc):
        if len(self.xlabel) > 0:
            x=self.wplt/2
            ltxt=len(self.xlabel)*self.fontsize[0]
            x -= ltxt/2
            y=self.hplt-20
            dc.DrawText(self.xlabel,x,y)
        
        if len(self.ylabel) > 0:
            x=15  
            y=(self.yendpos+self.yinipos)/2
            ltxt=len(self.ylabel)*self.fontsize[0]
            y += ltxt/2
            dc.DrawRotatedText(self.ylabel,x,y,90.0)
        
    def PlotItemsInStackBar(self,dc,ii,x):
        # plot subitems in stacked bargraph      
        orgy=self.FindYpos(0.0)
        self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)

        xtxt=x
        #cmp=['es','ex','ct','cr','1b']
        negay=orgy; posiy=orgy
        #ncmp=7
        ncmp=len(self.data[0])-2
        # plot loop 
        for ic in range(ncmp):
            value=self.data[ii][ic+2]
            cmpo=self.itemlist[ic+1][0]
            col=self.itemlist[ic+1][1]

            dc.SetBrush(wx.Brush(col,wx.SOLID))
            
            hight=abs(value)*self.yunit
            y=posiy
            if value > 0.0:
                if posiy > self.yendpos:
                    y=posiy-hight
                    if y < orgy: y += 1
                    if y < self.yendpos: 
                        hight=posiy-self.yendpos; y=posiy-hight
                        dc.DrawText("*",x,self.yendpos-10)
                    posiy=y #; hight += 1
                    dc.DrawRectangle(xtxt,y,self.barwidth,hight)
            else:
                y=negay
                if negay < self.yinipos:  
                    if negay+hight > self.yinipos:
                        hight=self.yinipos-negay
                        dc.DrawText("*",x,self.yinipos)   
                    negay=negay+hight #; y -= 1
                    dc.DrawRectangle(x,y,self.barwidth,hight)

    def DrawXAxis(self,dc):
        # draw x-aixs
        # extra: text to plot at ndata +1 position
        dc.SetPen(wx.Pen('black'))
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-10
        self.yendpos=self.htitle+10
        orgy=self.FindYpos(0.0)
        # x-axis
        x0=self.FindXpos(self.begindata)
        ndat=len(self.data)
        # x-axis
        x1=self.FindXpos(ndat)+self.xunit/2
        if x1 > self.xendpos: x1=self.xendpos+self.xunit/2
        dc.DrawLine(self.xinipos,orgy,x1,orgy)
        if self.extradata: ndat -= 1
        # x scale mark
        ks=1
        ytext=self.yinipos+35      
        for i in range(self.begindata,ndat):
            ordr=self.order[i]
            x=self.FindXpos(i)
            if x > self.xendpos: continue
            dc.DrawLine(x,orgy-2,x,orgy+2)    
            ii=self.data[ordr][0]

            if isinstance(ii,int): text=('%4d' % ii)
            else: text=ii
            text=text.rjust(4) #; text=text.strip() 
            if isinstance(ii,int): # and (ii == 1 or (ii % ks)) == 0:
                xtext=self.FindXpos(i) #+3          
                dc.DrawRotatedText(text,xtext,ytext,90.0)
        x=self.FindXpos(ndat)
        dc.DrawLine(x,orgy-2,x,orgy+2)    
        if self.extradata:
            x=self.FindXpos(ndat)
            if x <= self.xendpos:
                dc.DrawLine(x,orgy-2,x,orgy+2)
                text=self.data[ndat][0]
                text=text.rjust(4)   
                xtext=x #+3
                dc.DrawRotatedText(text,xtext,ytext,90.0)

    def DrawYAxis(self,dc):
        # draw y-axis
        dc.SetPen(wx.Pen('black'))
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-10
        self.yendpos=self.htitle+10
        orgy=self.FindYpos(0.0)
        # y-axis
        dc.DrawLine(self.xinipos,self.yinipos,self.xinipos,self.yendpos)
        ndat=len(self.data)
        # y-axis
        dc.SetFont(self.font)
        dc.SetTextForeground(self.fontcolor)
        #y=0.0
        text='0.0'; ns=len(text)
        dc.DrawText(text,self.xinipos-8*ns-2,orgy-5)
        # axis label
        yinc=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        # positive axis        
        yinc=self.yrange/5.0
        for i in range(1,6):
            val=yinc*float(i)
            y=self.FindYpos(val)  
            dc.DrawLine(self.xinipos-1,y,self.xinipos+3,y)
            text=('%4.1f' % val); text=text.strip(); ns=len(text)
            if self.yrange < 1.0:
                text=('%4.2f' % val); text=text.strip(); ns=len(text)
            if self.yrange < 0.1:
                text=('%5.3f' % val); text=text.strip(); ns=len(text)
            dc.DrawText(text,self.xinipos-8*ns-2,y-5)           
        # negative axis
        for i in range(1,6):
            val=-yinc*float(i)
            y=self.FindYpos(val)
            dc.DrawLine(self.xinipos-1,y,self.xinipos+3,y)
            text=('%4.1f' % val); text=text.strip(); ns=len(text)
            if self.yrange < 1.0:
                text=('%4.2f' % val); text=text.strip(); ns=len(text)
            if self.yrange < 0.1:
                text=('%5.3f' % val); text=text.strip(); ns=len(text)
            dc.DrawText(text,self.xinipos-8*ns-2,y-5)
    
    def DrawRemark(self,dc):
        wb=self.remarkboxsize[0]; hb=self.remarkboxsize[1]; yw=hb+10
        # white rectangle for remark
        x=self.wplt-self.wremark; yi=self.htitle-2; yf=self.hplt-yi     
        dc.SetPen(wx.Pen(self.bgcolor)) #"white"))
        dc.SetBrush(wx.Brush(self.bgcolor,wx.SOLID))
        dc.DrawRectangle(x,yi,self.wremark,yf)
        dc.SetPen(wx.Pen("black"))
        # plot position
        ncmp=len(self.remarklist)
        for i in range(ncmp):        
            txt=self.remarklist[i][0]
            col=self.remarklist[i][1]
            y=self.yendpos+yw*i
            dc.SetBrush(wx.Brush(col,wx.SOLID))
            dc.DrawRectangle(x,y,wb,hb)
            dc.DrawText(txt,x+12,y-3)

    def SetPlotSize(self,wplt,hplt):
        size=self.GetSize()
        wpltmax=size[0]; hpltmax=size[1]
        if wplt > wpltmax: wplt=wpltmax
        if hplt > hpltmax: hplt=hpltmax
        self.wplt=wplt; self.hplt=hplt
        self.xinipos=self.wytitle+self.wylabel+10
        self.xendpos=self.wplt-self.wremark-20
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-10
        self.yendpos=self.htitle+10
        self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)        

    def FindXpos(self,value):
        x=self.xinipos+self.xunit/2+(value-self.begindata)*self.xunit
        return x
    
    def FindYpos(self,value):
        #
        maxv=self.yrange; minv=-self.yrange
        delv=(self.yinipos-self.yendpos)/(maxv-minv)
        y=self.yinipos-(value-minv)*delv
        return y
    
    def GetXValue(self,pos):
        xvalue=-1
        x=pos[0]
        xvalue=x-self.xinipos-self.xunit/2
        xvalue=xvalue/self.xunit+self.begindata
        if xvalue < 0 or xvalue > len(self.data): xvalue=-1   
        return xvalue

    def MakeFunctionValueMess(self,ix):
        mess=''
        if ix < 0 or ix >= len(self.data): return mess
        ixx=self.order[ix]
        ixxx=self.data[ixx][0]
        fmt='%7.3f'
        if self.title[0:9] == 'PIE/PIEDA': fmt='%7.2f'
        mess="data="+str(ixxx)+', value=['
        for j in range(1,len(self.data[ixx])):
            mess=mess+(fmt % self.data[ixx][j])+','
        n=len(mess)
        mess=mess[:n-1]+']'
        if len(self.addinfo) > 0:
            mess=mess+self.addinfo[ixx]  
        return mess,ixx
         
    def ClearGraph(self):
        self.SetBackgroundColour(self.bgcolor)

    def Replot(self,xmove):
        # shift graph by xmove and plot
        xmaxplt=self.wplt-(self.xinipos+self.wremark)-10
        pltnmb=int(xmaxplt/self.xunit)
        maxnmb=self.maxplotdata-pltnmb
        
        if maxnmb < 0: maxnmb=0
        xshift=5
        if self.maxplotdata > 100: xshift=10
        if self.maxplotdata > 500: xshift=50
        if self.maxplotdata > 5000: xshift=500
        if xmove > 0: self.begindata += xshift
        elif xmove < 0: self.begindata -= xshift
        if self.begindata < 0: self.begindata=0
        elif self.begindata > maxnmb: self.begindata=maxnmb
        self.Plot(True)
    
    def OnMouseLeftDown(self,event):
        self.mouseleftdown=True
        self.mousepos=event.GetPosition()
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) #wx.CURSOR_HAND))        
        self.mouseleftdownpos=self.mousepos
        #cursors = [ wx.CURSOR_ARROW, wx.CURSOR_HAND, wx.CURSOR_WATCH, wx.CURSOR_SPRAYCAN, wx.CURSOR_PENCIL,
        #             wx.CURSOR_CROSS, wx.CURSOR_QUESTION_ARROW, wx.CURSOR_POINT_LEFT, wx.CURSOR_SIZING]        
    
    def OnMouseMove(self,event):
        self.fvaluemess=False; self.fvalue=''
        pos=event.GetPosition()
        diff=pos-self.mousepos
        if not self.mouseleftdown: return
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) 
        #
        self.Replot(diff[0])
        #
        self.mousepos=pos

    def OnMouseLeftUp(self,event):
        if not self.mouseleftdown: return 
        pos=event.GetPosition()
        diff=pos-self.mouseleftdownpos       
        if abs(diff[0]) != 0 or abs(diff[1]) != 0:
            self.fvaluemess=False; self.fvalue=''
        else:
            try: 
                ix=self.GetXValue(self.mousepos)
                self.fvaluemess=True
                self.fvalue,ixx=self.MakeFunctionValueMess(ix)
                self.Plot(True)
                self.graph.SelectFragmetAndDrawMolView(ixx,True)
            except: pass
            #
            #self.graph.MouseLeftClick(self.mousepos)
        self.mouseleftdown=False        
        self.SetCursor(wx.NullCursor)
    
    def DrawBarValue(self,ibar):
        try: 
            self.fvaluemess=True
            self.fvalue,ixx=self.MakeFunctionValueMess(ibar)
            self.Plot(True)
            self.graph.SelectFragmetAndDrawMolView(ixx,True)
        except: pass
        
    def OnMouseRightDown(self,event): 
        self.fvaluemess=False; self.fvalue=''
        self.Plot(True)
        self.graph.SelectFragmetAndDrawMolView(-1,False)
        
    def OnResize(self,event):
        self.Plot(True)
        
class TileGraph(wx.Panel):
    # plot 2D tile graph
    def __init__(self,parent,id,graph,pos,size,bgcolor):
        wx.Panel.__init__(self,parent,id,pos=pos,size=size) #,style=wx.MINIMIZE_BOX ) #,
        #       style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)
        self.focus=0
        self.parent=parent
        self.graph=graph # fugraph
        # background color
        self.buffer=None
        self.bgcolor=bgcolor
        self.SetBackgroundColour(self.bgcolor)
        self.font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        self.fontsize=[6,8]
        self.fontcolor='black'
        # set graph size
        self.size=self.GetClientSize()
        self.wplt=self.size[0]; self.hplt=self.size[1]
        # title and axis labels
        self.title='' # title text 
        self.xlabel='' # title for x-axis
        self.ylabel='' # title for y-axis
        # plot data
        self.ndata=0 # number of data
        self.data=[] # [[[1,1,value,flag],..[1,n,value,flag]],[[2,1,value,flag],..]],.
        self.order=[]
        #self.itemlist=[] # [['name',col],..]
        #self.itemlist=self.SetDefaultItemList()
        self.extradata=False # only 1 extra data is allowed
        self.extradatalabel='' # label of extra data
        self.extposivalue=0.0
        self.extnegavalue=0.0
        self.maxplotdata=0 # number of plot data; ndata or ndata+1(extra)
        self.xbegindata=0 # the first sequence number of data to plot
        self.ybegindata=0 # the first sequence number of data to plot
        # remark
        self.remarklist=[]
        self.remarkboxsize=[8,8]
        self.remarktext=''
        self.hremark=20
        self.rankposi=10
        self.ranknega=10
        # rank color
        self.posicolor='red' # will be converted to RBG255
        self.negacolor='blue' # will be converted to RGB255
        self.extnegacolor=[0,255,255] #'cyan'
        self.extposicolor=[255,0,152] #'magenta'
        self.colorcode1=[255,255,0] #'yellow'
        self.colorcode2=[255,204,0] # 'gold'
        self.SetRankColor(self.negacolor,self.posicolor,self.extnegacolor,
                          self.extposicolor,self.colorcode1,self.colorcode2)
        self.tilesize=[10,10]
        # x-axis range
        self.wytitle=30
        self.wylabel=50
        self.wremark=55 # width of remark
        self.xinipos=self.wytitle+self.wylabel+10 # from left to right
        self.xendpos=self.wplt-self.wremark-40 #20

        self.xunit=12 # barwidth*2+2
        self.barwidth=5
        self.hxtitle=20 # x axis title hight
        self.hxlabel=30
        # y-axis range
        self.htitle=25 # title hight
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-20 # -10 from top to bottom
        self.yendpos=self.htitle+10
        self.yrangemin=-50.0
        self.yrangemax=50.0  # +/- y max value
        self.yrange=self.yrangemax
        self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        #self.rankposi=10; self.ranknega=10
        self.scaleoutposi=0.0; self.scaleoutnega=0.0
        # plot panel
        self.SetPlotSize(self.wplt,self.hplt)
        # mouse operation
        self.mouseleftdown=False
        self.mousepos=[0,0]
        # set buffer for plot
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        # activate mouse event drivers
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)

    def SetBackgroundColor(self,color):
        self.bgcolor=color
        self.Plot(True)
    
    def SetRankColor(self,negacolor,posicolor,extnegacolor,extposicolor,
                     colorcode1,colorcode2):
        posicol=const.HSVCol[posicolor]
        negacol=const.HSVCol[negacolor]
        self.extposicolor=extposicolor #lib.HSVtoRGB(const.HSVCol[extposicolor])
        self.extnegacolor=extnegacolor #lib.HSVtoRGB(const.HSVCol[extnegacolor]) #['cyan'])
        rankposi=self.rankposi; ranknega=self.ranknega
  
        self.rankposicolor=[]; self.ranknegacolor=[]
        # rank color for positive value:  red -> white
        if rankposi > 0: 
            grad=1.0/float(rankposi)
            for i in range(rankposi):
                col=list(posicol)
                col[1]=0.9-grad*(ranknega-i) + 0.1
                self.rankposicolor.append(lib.HSVtoRGB(col))
        # rank color for negative  value: white -> blue
        if ranknega > 0: 
            grad=1.0/float(ranknega)
            for i in range(ranknega):
                col=list(negacol)
                col[1]=0.9-grad*(ranknega-i) + 0.1       
                self.ranknegacolor.append(lib.HSVtoRGB(col))
        
        self.extnegacolor=extnegacolor
        self.extposicolor=extposicolor
        self.colorcode1=colorcode1
        self.colorcode2=colorcode2

    def SetData(self,data,order):
        # data: [[[1,1,value,flag],..[1,n,value,flag]],[[2,1,value,flag],..]],.
        # flag=1 for diagonal,=2 for covalent bonded fragment
        self.data=data
        self.plotdata=copy.deepcopy(data)
        self.ndata=len(data)
        self.order=order
        if len(order) <= 0:
            for i in range(self.ndata): self.order.append(i)
        self.plotdata=self.MakePlotData()
    
    def MakePlotData(self):
        plotdata=[]
        rankposi=self.yrange/self.rankposi
        ranknega=self.yrange/self.ranknega
        for i in range(len(self.data)):
            dati=self.data[i]
            tmpi=[]
            for j in range(len(dati)):
                #tmp=[] #; tmp.append(data[j][0]); tmp.append(data[j][1])
                if dati[j][2] == 1:
                    col=self.colorcode1
                elif dati[j][2] == 2:
                    #col='yellow'
                    col=self.colorcode2
                else:
                    value=dati[j][1]
                    if value >= 0:
                        rank=int(value/rankposi)
                        if rank < self.rankposi:
                            col=self.rankposicolor[rank]
                        else:
                            self.extposivalue=value
                            col=self.extposicolor
                    else:
                        rank=int(abs(value)/ranknega)
                        if rank < self.ranknega:
                            col=self.ranknegacolor[rank]
                        else:
                            self.extnegavalue=value
                            col=self.extnegacolor
                tmpi.append(col)
            plotdata.append(tmpi)
                    
        return plotdata
                  
    def SetItemNameAndColor(self,itemlist):
        self.itemlist=itemlist

    def SetTitle(self,title):
        self.title=title    
    
    def SetAxisLabel(self,xlabel,ylabel):
        self.xlabel=xlabel
        self.ylabel=ylabel
        
    def SetFocus(self,focus):
        # focus: data number from 0,1,...
        self.focus=focus

    def SetYRange(self,yrangemin,yrangemax):
        self.yrange=yrangemax
        self.yrangemin=-yrangemin
        self.yrangemax=yrangemax
        self.MakePlotData()

    def SetPlotSize(self,wplt,hplt):
        size=self.GetClientSize()
        wpltmax=size[0]; hpltmax=size[1]
        if wplt > wpltmax: wplt=wpltmax
        if hplt > hpltmax: hplt=hpltmax
        self.wplt=wplt; self.hplt=hplt
        self.xinipos=self.wytitle+self.wylabel+10
        self.xendpos=self.wplt-self.wremark-40 #20
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-20 #10
        self.yendpos=self.htitle+10
        self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)        

    def SetBeginDataNumber(self,number):
        self.begindata=number

    def SetRemark(self,remarkboxsize,remarklist):
        # remarkboxsize: [[width,hight],...]
        # remarklist: ['label',color],..]
        self.remarkboxsiz=remarkboxsize
        self.remarklist=remarklist
        #lbl=remarklist.keys()
    def SetRemarkTitle(self,text):
        self.remarktext=text

    def SetFont(self,font,fontsize):
        # font: wxfont, fontsize:[w,h] in pixels
        self.font=font
        self.fontsize=fontsize
                
    def Plot(self,on):
        if len(self.data) <= 0: return  
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        dc=wx.BufferedDC(None,self.buffer)
        backBrush=wx.Brush(self.bgcolor,wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()
        if not on: return 
        # plot
        dc=wx.BufferedDC(wx.ClientDC(self),self.buffer) 
        #
        dc.SetFont(self.font)
        # set color data
        #!!plotdata=self.SetPlotData()
        x0=65; y0=30+self.htitle; dx=self.tilesize[0]; dy=self.tilesize[1]
        #y=y0; 
        y=self.yinipos #self.hplt-self.hxlabel-35 #-15
        xmax=self.xendpos #self.self.wplt-self.wremark-20
        
        ltxt=len(str(self.ndata))*self.fontsize[0]      
        xtxt=20 #40
        ii=-1
        
        for i in range(self.ybegindata,self.ndata):
            iord=self.order[i]
            ###data=self.plotdata[iord]
            #ii += 1
            ii=iord+1 #data[iord][0] #
            x=x0
            #if ii == 0  or (i+1) % 5 == 0: #=self.nfrg-i
            #if i+1 % 5 == 0:
            text='%4d' % ii # (i+1)
            dc.DrawText(text,xtxt,y)            
            for j in range(self.xbegindata,self.ndata):
                jord=self.order[j]
                col0=const.RGBColor255['gray01'] #gray0'light gray'
                
                if iord == self.focus-1 or jord == self.focus-1: col0='black'
                dc.SetPen(wx.Pen(col0,1))
                col=self.plotdata[i][j]
                dc.SetBrush(wx.Brush(col,wx.SOLID))
                dc.DrawRectangle(x,y,dx,dy)
                x += dx
                
                if x > xmax: break
                
            y -= dy
        #if (self.ndata % 5) != 0:
        y += dy
        text='%4d' % (self.ndata)
        dc.DrawText(text,xtxt,y)            

            ###if y < y0: break
        # plot fragment number in x-axis
        x=x0+2; ylbl=self.hplt-self.hxlabel+ltxt-20 # -0
        x=x0-2
        ii=-1
        for i in range(self.xbegindata,self.ndata):
            iord=self.order[i]
            #data=self.plotdata[iodr]
            #ii += 1
            #if ii == 0 or (i+1) % 5 == 0:
            ii=iord+1 #data[iord][0]
            text='%4d' % ii; text=text.strip()
            dc.DrawRotatedText(text,x,ylbl,90.0)
                #self.DrawTextV(dc,x,ylbl,text) #,'black')
            x += dx
            if x > xmax: break
    

        self.DrawTitle(dc)
        self.DrawAxisLabel(dc)
        #
        textcol='black'
        hplt=self.hplt-self.htitle
        text='PIE/PIEDA'
        x=self.wplt-self.wremark-20
        y=self.htitle
        self.DrawRemark(dc,x,y,self.remarktext) #,self.wremark,self.hremark,textcol,"white") #self.wcolsc,hplt,textcol,"white")
        # needed for Mac OSX
        self.Refresh()
        self.Update()
           
    def DrawTitle(self,dc):
        size=self.GetClientSize()
        w=size[0]; h=size[1]        
        # set background for title
        rgb=self.bgcolor
        dc.SetPen(wx.Pen(rgb))
        dc.SetBrush(wx.Brush(rgb,wx.SOLID))
        x=0; y=0; wtxt=w
        dc.DrawRectangle(x,y,wtxt,self.htitle)
        # plot title
        txtsize=len(self.title)*6
        xtxt=int(w/2)-int(txtsize/2)-self.wremark
        dc.DrawText(self.title,xtxt,8) 
    
    def DrawAxisLabel(self,dc):
        if len(self.xlabel) > 0:
            x=self.wplt/2-self.wremark
            ltxt=len(self.xlabel)*self.fontsize[0]
            x -= ltxt/2
            y=self.hplt-25 #20
            dc.DrawText(self.xlabel,x,y)

        if len(self.ylabel) > 0:
            x=10 #15  
            y=(self.yendpos+self.yinipos)/2
            ltxt=len(self.ylabel)*self.fontsize[0]
            y += ltxt/2
            dc.DrawRotatedText(self.ylabel,x,y,90.0)
        
    def FindXpos(self,value):
        x=self.xinipos+self.xunit/2+(value-self.xbegindata)*self.xunit
        return x
    
    def FindYpos(self,value):
        #
        maxv=self.yrange
        minv=-self.yrange
        delv=(self.yinipos-self.yendpos)/(maxv-minv)
        y=self.yinipos-(value-minv)*delv
        return y
    
    def DrawRemark(self,dc,x,y,remarktext):
        # plot: True: on FMO plot panel, False: on Main Window
        wbox=self.remarkboxsize[0]; hbox=self.remarkboxsize[1]
        dc.SetFont(self.font)
        dc.SetTextForeground('black')
        #
        rankposi=self.rankposi
        ranknega=self.ranknega
        maxrankval=self.yrange #self.maxrankvalue
        minrankval=-self.yrange #self.minrankvalue
        # scaled out negative and positive energy
        extposival=self.extposivalue
        extnegaval=self.extnegavalue
        # make white rectangle for color scale
        col=self.bgcolor
        dc.SetPen(wx.Pen(col)) #"white"))
        dc.SetBrush(wx.Brush(col,wx.SOLID))
        #hplt=self.hplt-self.htitle
        x0=x; y0=y
        ####dc.DrawRectangle(x0,y0,width,hight) #x-10,y,width,hight) #self.wcolsc+10,hplt)
        # draw remark
        if len(remarktext) > 0:
            dc.DrawText(remarktext,x0,y0)
            y0 += 20
        # positive value
        x=x0+5; y=y0
        if extposival > 0.00001:
            dc.SetPen(wx.Pen(self.extposicolor))
            dc.SetBrush(wx.Brush(self.extposicolor)) #(r,g,b))
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y-6
            if self.yrange > 1.0:
                txt=extposival; txt='% 4.1f' % txt
            else:
                txt=extposival; txt='% 4.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,y-4)
        y += hbox+4            

        yy=y
        if maxrankval > 0.0:
            delposi=self.yrange/3.0 #float(rankposi)
            yy=yy+hbox*(rankposi-1)
            for i in range(rankposi):
                col=self.rankposicolor[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,yy,wbox,hbox)
                if i == 0 or i == 3 or i == 6 or i == rankposi-1:
                    xtxt=x+20; ytxt=yy-4
                    if i == 0: txt=0.0
                    else: txt=delposi*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='% 4.1f' % txt
                    else:
                        txt='% 4.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,yy-4)
                yy -= hbox
                y += hbox
        # negative value
        if minrankval < 0.0:
            delnega=-self.yrange/3.0
            for i in range(1,ranknega): # skip zero
                col=self.ranknegacolor[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,y,wbox,hbox)
                if i == 3 or i == 6 or i == ranknega-1:
                    xtxt=x+20; ytxt=y+4
                    txt=delnega*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='%5.1f' % txt
                    else:
                        txt='%5.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,ytxt-4)
                y += hbox
        if extnegaval < -0.00001:
            dc.SetPen(wx.Pen(self.extnegacolor))
            dc.SetBrush(wx.Brush(self.extnegacolor))
            y += 4
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y+4
            txt=extnegaval
            if self.yrange > 1.0:
                txt='% 5.1f' % txt
            else:
                txt='% 5.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,ytxt-4)
                                     
    def GetColor(self,val,code):
        col=[255,255,255]
        if code == 0:
            if val > 0:
                unit=self.yrange/self.rankposi
                rank=int(val/unit)
                if rank >= self.rankposi: col=self.extposicolor
                else: col=self.rankposicolor[rank] 
            else:
                unit=self.yrange/self.ranknega
                rank=int(abs(val)/unit)
                if rank >= self.ranknega: col=self.extnegacolor
                else: col=self.ranknegacolor[rank]        
        elif code == 1: col=self.colorcode1
        elif code == 2: col=self.colorcode2
        
        return col
    
    def DrawRemarkGen(self,dc,x,y,remarktext,width,hight,textcol,bgcolor):
        # plot: True: on FMO plot panel, False: on Main Window
        wbox=self.remarkboxsize[0]; hbox=self.remarkboxsize[1]
        dc.SetFont(self.font)
        dc.SetTextForeground(textcol)
        #
        rankposi=self.rankposi
        ranknega=self.ranknega
        maxrankval=self.yrange #self.maxrankvalue
        minrankval=-self.yrange #self.minrankvalue
        # scaled out negative and positive energy
        extposival=self.extposivalue
        extnegaval=self.extnegavalue
        # make white rectangle for color scale
        rgb=bgcolor
        #rgb=const.RGBColor['white']
        #if not plot: rgb=const.RGBColor['black']
        #if plot: # on FMO plot panel, if not, on main window
        #y=y+self.htitle
        #rgb=self.bgcolor #[255,255,255] # backgroundcolor:white
        #rgb=const.RGBColor['white']
        dc.SetPen(wx.Pen(rgb)) #"white"))
        dc.SetBrush(wx.Brush(rgb,wx.SOLID))
        #hplt=self.hplt-self.htitle
        x0=x; y0=y
        dc.DrawRectangle(x0,y0,width,hight) #x-10,y,width,hight) #self.wcolsc+10,hplt)
        # draw remark
        if len(remarktext) > 0: dc.DrawText(remarktext,x0,y0)
        # positive value
        x=x0+5; y=y0+20
        if extposival > 0.00001:
            dc.SetPen(wx.Pen(self.extcolorposi))
            dc.SetBrush(wx.Brush(self.extcolorposi)) #(r,g,b))
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y-6
            if self.yrange > 1.0:
                txt=extposival; txt='% 4.1f' % txt
            else:
                txt=extposival; txt='% 4.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,y-4)
        y += hbox+4            

        yy=y
        if maxrankval > 0.0:
            delposi=self.yrange/3.0 #float(rankposi)
            yy=yy+hbox*(rankposi-1)
            for i in range(rankposi):
                col=self.rankcolorposi[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,yy,wbox,hbox)
                if i == 0 or i == 3 or i == 6 or i == rankposi-1:
                    xtxt=x+20; ytxt=yy-4
                    if i == 0: txt=0.0
                    else: txt=delposi*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='% 4.1f' % txt
                    else:
                        txt='% 4.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,yy-4)
                yy -= hbox
                y += hbox
        # negative value
        if minrankval < 0.0:
            delnega=-self.yrange/3.0
            for i in range(1,ranknega): # skip zero
                col=self.rankcolornega[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,y,wbox,hbox)
                if i == 3 or i == 6 or i == ranknega-1:
                    xtxt=x+20; ytxt=y+4
                    txt=delnega*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='%5.1f' % txt
                    else:
                        txt='%5.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,ytxt-4)
                y += hbox
        if extnegaval < -0.00001:
            dc.SetPen(wx.Pen(self.extcolornega))
            dc.SetBrush(wx.Brush(self.extcolornega))
            y += 4
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y+4
            txt=extnegaval
            if self.yrange > 1.0:
                txt='% 5.1f' % txt
            else:
                txt='% 5.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,ytxt-4)
                                     
    def ClearGraph(self):
        self.SetBackgroundColour(self.bgcolor)

    def Replot(self,xmove,ymove):
        # shift graph by xmove and plot
        xmaxplt=self.wplt-(self.xinipos+self.wremark)-5 # defined in PlotPIE2D and 10 in cloor scale
        xmaxnmb=self.ndata-int(xmaxplt/10) #
        ymaxplt=self.hplt-self.hxlabel-self.htitle-self.hxtitle-10 #15 # y-y0? in PlotPIE2D
        ymaxnmb=self.ndata-int(ymaxplt/10) # 10: box size in 2d plot defined in PlotPIE2D
        if ymaxnmb < 0: ymaxnmb=0
        if xmaxnmb < 0: xmaxnmb=0
        xshift=0; yshift=0
        if abs(xmove) > 2: xshift=abs(xmove)/2 # /2 for adjust sensitivity
        if abs(ymove) > 2: yshift=abs(ymove)/2 #1
        if xmove > 0: self.xbegindata += xshift
        elif xmove < 0: self.xbegindata -= xshift
        if self.xbegindata < 0: self.xbegindata=0
        elif self.xbegindata > xmaxnmb: self.xbegindata=xmaxnmb
        
        if ymove > 0: self.ybegindata -= yshift
        elif ymove < 0: self.ybegindata += yshift
        if self.ybegindata < 0: self.ybegindata=0
        elif self.ybegindata > ymaxnmb: self.ybegindata=ymaxnmb
                
        self.Plot(True)

    
    def OnMouseLeftDown(self,event):
        self.mouseleftdown=True
        self.mousepos=event.GetPosition()
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) #wx.CURSOR_HAND))        
        #cursors = [ wx.CURSOR_ARROW, wx.CURSOR_HAND, wx.CURSOR_WATCH, wx.CURSOR_SPRAYCAN, wx.CURSOR_PENCIL,
        #             wx.CURSOR_CROSS, wx.CURSOR_QUESTION_ARROW, wx.CURSOR_POINT_LEFT, wx.CURSOR_SIZING]
        self.mouseleftdownpos=self.mousepos
       
    def OnMouseMove(self,event):
        if not self.mouseleftdown: return   
        pos=event.GetPosition()
        diff=pos-self.mousepos
        if not self.mouseleftdown: return
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) 
        self.Replot(diff[0],diff[1])
        self.mousepos=pos

    def OnMouseLeftUp(self,event):
        if not self.mouseleftdown: return         
        self.mouseleftdown=False
        self.SetCursor(wx.NullCursor)
        pos=event.GetPosition()
        diff=pos-self.mouseleftdownpos       
        return
        
        """ need modification. """
        if abs(diff[0]) != 0 or abs(diff[1]) != 0:
            self.fvaluemess=False; self.fvalue=''
        else:
            ix,iy=self.GetXYValue(self.mousepos)
            self.fvaluemess=True
            self.fvalue,ixx,iyy=self.MakeFunctionValueMess(ix,iy)
            self.Plot(True)
            self.graph.SelectFragmetAndDrawMolView(ixx,False)
            self.graph.SelectFragmetAndDrawMolView(iyy,True)
        
        self.SetCursor(wx.NullCursor)
        self.mouseleftdown=False
        
    def GetXYValue(self,pos):
        """ need modification. just copied from BarGraph. need modification"""
        xvalue=-1
        x=pos[0]; y=pos[1]
        xvalue=self.FindXpos(x) #x-self.xinipos-self.xunit/2
        #xvalue=xvalue/self.xunit+self.begindata
        yvalue=self.FindYpos(y)
        #if xvalue < 0 or xvalue > len(self.data): xvalue=-1   
        print 'xvalue,yvalue',xvalue,yvalue
        return xvalue,yvalue

    def MakeFunctionValueMess(self,ix,iy):
        """ need modification. just copied from BarGraph. need modification"""
        mess=''
        if ix < 0 or ix >= len(self.data): return mess
        ixx=self.order[ix]
        ixxx=self.data[ixx][0]
        fmt='%7.3f'
        if self.title[0:9] == 'PIE/PIEDA': fmt='%7.2f'
        mess="data="+str(ixxx)+', value=['
        for j in range(1,len(self.data[ixx])):
            mess=mess+(fmt % self.data[ixx][j])+','
        n=len(mess)
        mess=mess[:n-1]+']'
        if len(self.addinfo) > 0:
            mess=mess+self.addinfo[ixx]  
        return mess,ixx,iyy

class EnergyGraph(wx.Panel):
    # plot bargraph
    def __init__(self,parent,id,pos,size,bgcolor,retobj=None):
        wx.Panel.__init__(self,parent,id,pos=pos,size=size) #,style=wx.MINIMIZE_BOX ) #,
        #       style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent # pltpan
        self.retobj=retobj
        # background color
        self.bgcolor=bgcolor
        self.SetBackgroundColour(self.bgcolor)
        self.font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_NORMAL, False, 'Courier 8 Pitch')
        self.fontsize=[6,10]
        self.fontcolor='black'
        self.barcolor='black'
        self.selectbarcolor='red'
        self.barthick=2
        # set graph size
        self.size=self.GetClientSize()
        self.wplt=self.size[0]; self.hplt=self.size[1]
        # title and axis labels
        self.title='i=10.e=-10.23' # title text 
        self.htitle=10 # title hight
        self.xlabel='' # title for x-axis
        self.ylabel='Energy(eV)' # title for y-axis
        # plot data
        self.ndata=0 # number of data
        self.data=[] # plot data
        self.minvalue=-100.0
        self.maxvalue=100.0
        self.selectdatadic={}

        self.maxplotdata=0 # number of plot data; ndata or ndata+1(extra)
        #self.beginvalue=0 # the first sequence number of data to plot
        # x-axis range
        self.wytitle=5
        self.wylabel=30
        self.xinipos=self.wytitle+self.wylabel+5
        self.xendpos=self.wplt-15 #self.wremark-15

        self.xunit=12 # barwidth*2+2
        self.barwidth=5
        self.hxtitle=0 #20 # x axis title hight
        self.hxlabel=0 #30
        # y-axis range
        self.yinipos=self.hplt-self.htitle-self.hxtitle-self.hxlabel-10
        self.yendpos=self.htitle+10
        self.yrangemin=-15.0  # +/- y max value
        self.yrangemax=5.0
        self.yrange=self.yrangemax-self.yrangemin
        self.yunit=(self.yinipos-self.yendpos)/self.yrange
        # mouse operation
        self.mouseleftdown=False
        self.mousepos=[0,0]
        # set buffer for plot
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        # activate mouse event drivers
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        #self.Bind(wx.EVT_SIZE,self.OnResize)
        #
        self.SetPlotSize(self.wplt,self.hplt)

    def SetBackgroundColor(self,color):
        self.bgcolor=color
        self.Plot(True)
    
    def SetData(self,data):
        # data: [[-20,-28.0,...],[-22,-18,...]], [alpha orgital eenrgy list,beta orbital energy list]
        self.data=data
        self.ndata=len(self.data)
        minv=10000.0; maxv=-10000.0
        for i in range(self.ndata):
             mini=min(self.data[i])
             maxi=max(self.data[i])
             minv=min([minv,mini])
             maxv=max([maxv,maxi])
        self.minvalue=minv
        self.maxvalue=maxv
        
    def SetTitle(self,title):
        self.title=title    
    
    def SetYAxisLabel(self,ylabel):
        self.ylabel=ylabel
    
    def GetYRange(self):
        return self.yrangemin,self.yrangemax
            
    def SetYRange(self,ymin,ymax):
        try:
            self.yrangemin=ymin
            self.yrangemax=ymax
            self.yrange=self.yrangemax-self.yrangemin
            self.yunit=(self.yinipos-self.yendpos)/self.yrange #(2.0*self.yrange)      
        except: pass
    #def SetBeginDataNumber(self,number):
    #    self.beginvalue=number

    def SetFont(self,font,fontsize):
        # font: wxfont, fontsize:[w,h] in pixels
        self.font=font
        self.fontsize=fontsize
                
    def Plot(self,on):
        self.ndata=len(self.data)
        if self.ndata <= 0: return
        #!!!!!self.SetPlotRange()
        self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
        dc=wx.BufferedDC(None,self.buffer)
        backBrush=wx.Brush(self.bgcolor,wx.SOLID) #'white', wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()
        if not on: return
        # plot
        dc=wx.BufferedDC(wx.ClientDC(self),self.buffer)
        
        dc.SetFont(self.font)
        
        orgy=self.FindYPos(0.0)
        #self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        #hmax=self.yrange*self.yunit
        ndat=len(self.data)
        #nedat=len(self.data[0])
        #if ndat == 1: self.maxplotdata=nedat+1
        #else:
        #    nedat1=len(self.data[0]); nedat2=len(self.data[1])
        #    self.maxplotdata=max([nedat1,nedat2])+1
        #print 'maxplotdata',self.maxplotdata
        x0=self.xinipos+10 #8 #self.wylabel
        barwidth=15
        if ndat == 1: x0=x0+8
        if ndat > 1: barwidth=10 
        
        self.xrangeofdata=[]
        ii=-1
        for i in range(ndat): #self.beginvalue,ndat): #self.nfrg):
            ii += 1
            x=x0+ii*(barwidth+8)
            self.xrangeofdata.append([x,x+barwidth])
            for j in range(len(self.data[i])):
                value=self.data[i][j]
                if value < self.yrangemin-1: continue
                if value > self.yrangemax+1: continue
                y=self.FindYPos(value)
                col0='black' #const.RGBColor255['gray01'] #col # 'gray01' #'lightgray'
                if self.selectdatadic.has_key(i):
                    if self.selectdatadic[i] == j: col0='red'
                dc.SetPen(wx.Pen(col0,self.barthick)) #,1))
                dc.DrawLine(x,y,x+barwidth,y)
        # zero level
        xs=self.xinipos
        xe=xs+(self.wplt-self.xinipos)-5
        color='black'
        dc.SetPen(wx.Pen(color,1,wx.DOT))
        dc.DrawLine(xs,orgy,xe,orgy)
        # draw title,axis labels
        self.DrawTitle(dc)
        self.DrawYAxisLabel(dc)
        self.DrawYAxis(dc)
        # needed for Mac OSX
        self.Refresh()
        self.Update()

    def DrawTitle(self,dc):
        if len(self.title) > 0:
            x=self.wplt/2
            ltxt=len(self.title)*self.fontsize[0]
            x -= ltxt/2
            y=2
            dc.DrawText(self.title,x,y)
    
    def DrawYAxisLabel(self,dc):
        if len(self.ylabel) > 0:
            x=5 #15  
            y=(self.yendpos+self.yinipos)/2
            ltxt=len(self.ylabel)*self.fontsize[0]
            y += ltxt/2
            dc.DrawRotatedText(self.ylabel,x,y,90.0)
        
    def DrawYAxis(self,dc):
        # draw y-axis
        dc.SetPen(wx.Pen('black'))
        #self.yinipos=self.hplt-self.hxtitle-self.hxlabel-10
        #self.yendpos=self.htitle+10
        orgy=self.FindYPos(0.0)
        # y-axis
        dc.DrawLine(self.xinipos,self.yinipos+5,self.xinipos,self.yendpos-5)
        #ndat=len(self.data)
        # y-axis
        dc.SetFont(self.font)
        dc.SetTextForeground(self.fontcolor)
        #y=0.0
        text='0'; ns=len(text)
        dc.DrawText(text,self.xinipos-8*ns-2,orgy-5)
        # axis label
        #yinc=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        # positive axis        
        yinc=5 
        np=int(self.yrangemax/yinc)+2
        for i in range(1,np):
            val=yinc*float(i)
            if val > self.yrangemax+yinc: continue
            if val < self.yrangemin-yinc: continue
            y=self.FindYPos(val)  
            dc.DrawLine(self.xinipos-1,y,self.xinipos+3,y)
            text=('%4.0f' % val); text=text.strip(); ns=len(text)
            #if self.yrange < 1.0:
            #    text=('%4.2f' % val); text=text.strip(); ns=len(text)
            #dc.DrawText(text,self.xinipos-8*ns-2,y-5)  
            dc.DrawText(text,self.xinipos-6*ns-2,y-5)             
        # negative axis
        np=int(abs(self.yrangemin)/yinc)+2    
        for i in range(1,np):      
            val=-yinc*float(i)
            if val < self.yrangemin-yinc: continue
            if val > self.yrangemax+yinc: continue
            y=self.FindYPos(val)
            dc.DrawLine(self.xinipos-1,y,self.xinipos+3,y)
            text=('%4.0f' % val); text=text.strip(); ns=len(text)
            dc.DrawText(text,self.xinipos-6*ns-2,y-5)

    def SetPlotSize(self,wplt,hplt):
        size=self.GetSize()
        wpltmax=size[0]; hpltmax=size[1]
        if wplt > wpltmax: wplt=wpltmax
        if hplt > hpltmax: hplt=hpltmax
        self.wplt=wplt; self.hplt=hplt
        self.xinipos=self.wytitle+self.wylabel+5
        #!!!self.xendpos=self.wplt-self.wremark-20
        self.yinipos=self.hplt-self.hxtitle-self.hxlabel-10
        self.yendpos=self.htitle+10
        
        #self.yunit=(self.yinipos-self.yendpos)/(2.0*self.yrange)
        self.yunit=(self.yinipos-self.yendpos)/self.yrange  

    def FindXPos(self,value):
        #x=self.xinipos+self.xunit/2+(value-self.beginvalue)*self.xunit
        x=self.xinipos+self.xunit/2+value*self.xunit
        return x
    
    def FindYPos(self,value):
        y=int(self.yinipos-(value-self.yrangemin)*self.yunit)
        return y

    def GetDataFromPos(self,pos):
        xvalue=-1
        idat=-1; iorb=-1
        x=pos[0]
        for i in range(len(self.xrangeofdata)):
            xmin=self.xrangeofdata[i][0]
            xmax=self.xrangeofdata[i][1]
            if x > xmin and x < xmax:
                idat=i; break
        if idat < 0: return idat,iorb
        #
        y=pos[1]
        for i in range(len(self.data[idat])):
            ypos=self.FindYPos(self.data[idat][i])
            ymin=ypos-3; ymax=ypos+3
            if y > ymin and y < ymax:
                iorb=i; break
        #self.selectdatadic={}
        if idat >= 0 and iorb >= 0: 
            try: self.retobj.SelectedOrbFromEnergyGraph(idat,iorb)
            except:
                self.selectdatadic={}
                self.selectdatadic[idat]=iorb
            self.SetTitleMessage(idat,iorb)
            self.Plot(True)
        return idat,iorb
    
    def SelectOrbital(self,spin,iorb):
        """ spin=0 for alpha, =1 for beta, =-1 for rhf orb """
        self.selectdatadic={}
        self.selectdatadic[spin]=iorb
        self.SetTitleMessage(spin,iorb)
        self.Plot(True)
    
    def GetXPos(self,pos):
        xvalue=-1
        x=pos[0]
        xvalue=x-self.xinipos-self.xunit/2
        xvalue=xvalue/self.xunit #+self.beginvalue
        if xvalue < 0 or xvalue > len(self.data): xvalue=-1   
        return xvalue

    def MakeFunctionValueMess(self,idat,iorb):
        mess=''
        if idat == -1 or iorb == -1: return mess

        value=self.data[idat][iorb]
        fmt='%7.3f'
        if len(self.data) == 2: 
            if idat == 0: mess='alpha:'
            elif idat == 1: mess='beta:'
        mess=mess+"orb="+str(iorb)+', value='+(fmt % value)
        return mess
         
    def ClearGraph(self):
        self.SetBackgroundColour(self.bgcolor)

    def Replot(self,ymove):
        yshift=ymove*0.5
        ymax=self.yrangemax+yshift
        ymin=self.yrangemin+yshift     
        #if ymax < self.maxvalue and ymin > self.minvalue:
        self.yrangemin=ymin
        self.yrangemax=ymax
        
        self.Plot(True)
    
    def OnMouseLeftDown(self,event):
        self.mouseleftdown=True
        self.mousepos=event.GetPosition()
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) #wx.CURSOR_HAND))        
        self.mouseleftdownpos=self.mousepos
        #cursors = [ wx.CURSOR_ARROW, wx.CURSOR_HAND, wx.CURSOR_WATCH, wx.CURSOR_SPRAYCAN, wx.CURSOR_PENCIL,
        #             wx.CURSOR_CROSS, wx.CURSOR_QUESTION_ARROW, wx.CURSOR_POINT_LEFT, wx.CURSOR_SIZING]        
    
    def OnMouseMove(self,event):
        #self.fvaluemess=False; self.fvalue=''
        pos=event.GetPosition()
        diff=pos-self.mousepos
        if not self.mouseleftdown: return
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND)) 
        #
        self.Replot(diff[1])
        #
        self.mousepos=pos
        
        #idat,iorb=self.GetDataFromPos(pos)
        #print 'pos,idat,iorb',pos,idat,iorb
        #self.SetTitleMessage(idat,iorb)

    def SetTitleMessage(self,idat,iorb):
        label=['a:','b:']; fmt='%7.2f'
        if idat < 0 or iorb < 0: self.title=''
        else:
            if len(self.data) >= 2: self.title=label[idat]
            else: self.title='o:'
            value=self.data[idat][iorb]
            self.title=self.title+str(iorb)+', e='+(fmt % value)
        
        self.Plot(True)
                
    def OnMouseLeftUp(self,event):
        if not self.mouseleftdown: return 
        pos=event.GetPosition()
        diff=pos-self.mouseleftdownpos       
        if abs(diff[0]) != 0 or abs(diff[1]) != 0:
            #self.fvaluemess=False; self.fvalue=''
            pass
        else:
            idat,iorb=self.GetDataFromPos(pos)
            self.SetTitleMessage(idat,iorb)
        self.mouseleftdown=False        
        self.SetCursor(wx.NullCursor)
    
    def OnMouseRightDown(self,event):
        """ will be used to pop up orbital information, number,energy,..."""
        pass
        #self.fvaluemess=False; self.fvalue=''
        self.Plot(True)
    
    def OnMove(self,event):
        self.Plot(True)
    
    def OnResize(self,event):
        self.OnMove(1)
        