#!/bin/sh
# -*- coding: utf-8

# furwfile.py version history
# ver.0.2.0 (28Dec2014): the first version. 
#                        File r/w methods were collected from other modules
import sys
sys.path.insert(0,'.')
import os
import datetime
import copy
#import types
import wxversion
wxversion.select("2.8")
import wx
# fu modules
import lib
import ctrl
import const


def CommentFilter(s):
    s=s.strip()
    if len(s) <= 0: return None
    if s[:1] == '#': return None
    ns=s.find('#')
    if ns >= 0: s=s[ns:]
    s=s.strip()
    if len(s) <= 0: 
        return None
    else: return s
    
def WriteDirectoryOnFile(dirnam,filename):
    #
    f=open(filename,"w")
    f.write(dirnam)
    f.close

def WriteIntDat(filename,title,intdat,ndatainline,every,stcolumn):
    # filename: filename, intdat: list of integers, 
    # ndatainline(int): number of dat in a line,
    # every(int): make space every "every" data
    # stcolmun(int): start column 
    try:
        f=open(filename,"w")
    except IOError:
        lib.MessageBoxOK("Error(WriteIntDat): file="+filename,"")
    else:
        if len(title) > 0: f.write(title+'\n')
        blk=' '
        fi2='%2d'; nd=len(intdat)
        k=0; n=0; s=stcolumn*blk 
        for i in intdat:
            k += 1; n += 1; kk=k % every; nn=n % ndatainline
            if k == ndatainline:
                s=s+(fi2 % i)+',\n'; f.write(s)
                s=stcolumn*blk; k=0
            else:
                if n == nd:
                    s=s+(fi2 % i)+'\n'
                    f.write(s)
                else: s=s+(fi2 % i)+','
            if kk == 0 and nn != 0: s=s+'  '
               
def WriteSetFile(setfile,item,prgnam,text):
    # item: "program","parameter", or "argument"
    # format of setfile data: "program TINKER directry"
    #                         "paerameter TINKER prameter directory"
    if not os.path.exists(setfile):
        lib.MessageBoxOK("File not exists. file= "+setfile,"")
        return
    if len(text) <= 0:
        lib.MessageBoxOK("Empty data is not set in 'setfile'.","")
        return        
    itmprg=item+"&"+prgnam
    itmprgdic={} 
    # read
    f=open(setfile,"r")
    for s in f.readlines():
        ss=s; ss=ss.strip()
        dat=ss.split()
        if len(dat) <= 2: continue
        nam=dat[0]+"&"+dat[1]
        itmprgdic[nam]=dat[2]
        if len(dat) > 3:
            for i in range(3,len(dat)): itmprgdic[nam]=itmprgdic[nam]+"&"+dat[i]
    f.close()
    #
    itmprgdic[itmprg]=text
    # rewrite
    itmprglst=itmprgdic.keys()
    itmprglst.sort()
    #
    f=open(setfile,"w")
    for namprg in itmprglst: 
        namdat=namprg.split("&")
        nam=namdat[0]; prg=namdat[1]
        txt=itmprgdic[namprg]
        txtdat=txt.split("&")
        text=txtdat[0]
        for i in range(1,len(txtdat)): text=text+" "+txtdat[i]           
        dat=nam+" "+prg+" "+text
        f.write(dat+"\n")
    f.close()

def WriteBDADatFile(filename,molname,inpfile,frgnatdic,bdadic,frgnamlst,totalchg,frgchglst):
    # 'filename'(IN): file name
    # 'uniq'(IN): True for unique frgament only, False for all fragments
    d=lib.DateTimeText() 
    #inpfile=self.inpfile
    #molname=self.name
    #frgnatdic=self.CountAtomsInFragment()
    #bdadic=self.DictBDA(); 
    nbda=len(bdadic)
    #frgnamlst=self.ListFragmentName()
    nfrg=len(frgnamlst)
    #totalchg,frgchglst=self.ListFragmentCharge()
    chglst=[]
    for nam,chg in frgchglst: chglst.append(chg)
    #
    f=open(filename,'w')
    s='# BDA data created by fu. DateTime:'+lib.DateTimeText()+'\n'  
    f.write(s)
    s='# NOTE: BDA/BAA is numbered from 0 not 1!'+'\n'        
    f.write(s)
    s='# Input file: '+inpfile+'\n'
    f.write(s)
    s='# Number of BDA points: '+str(nbda)+'\n'
    f.write(s)
    s='# Number of fragment: '+str(nfrg)+'\n'
    f.write(s)
    s='# Charge of molecule: '+str(totalchg)+'\n'
    f.write(s)
    #
    s='MOLNAM '+molname+'\n'
    f.write(s)
    if nbda > 0:
        for i in xrange(len(frgnamlst)):
            nam=frgnamlst[i]; lst=bdadic[nam]
            for bda,baa in lst:
                s='BDABAA'+('%8d' % (bda+1))+('%8d' % (baa+1))+'     '+nam
                s=s+5*' '+('%4d' % chglst[i])+'\n'
                f.write(s)
        s='BDABAA      -1      -1'+5*' '+frgnamlst[nfrg-1]+5*' '+('%4d' % chglst[nfrg-1])+'\n'
        f.write(s)
    #        
    f.close()
                
def WriteFrgDatFileOld(frgfile,molnam,resnam,bdalst,frgtbl,frglst):
    if len(frgfile) <= 0: return
    
    blk=' '
    d=lib.DateTimeText()   
    #
    f=open(frgfile,'w')
    # h eader
    s='REMARK'+' Fragment data created by fu. DateTime:'+lib.DateTimeText()+'\n' 
    f.write(s)
    if len(molnam) > 0:
        s='REMARK'+' Molecule Name:'+molnam+'\n'
        f.write(s)
    if len(resnam) > 0:
        s='RESNAM '+blk+resnam+'\n'
        f.write(s)
    #BDABAA
    if len(bdalst) > 0:
        s='REMARK  SEQ#  BDA    BAA  BDA:ANAM/ANMB/RNAM/RNMB BAA:ANAM/ANMB/RNAM/RNMB'+'\n'
        f.write(s)
        for i in xrange(len(bdalst)):
            bda=bdalst[i][0]; baa=bdalst[i][1]
            aanam=bdalst[i][2]; aanmb=bdalst[i][3]
            arnam=bdalst[i][4]; arnmb=bdalst[i][5]
            banam=bdalst[i][6]; banmb=bdalst[i][7]
            brnam=bdalst[i][8]; brnmb=bdalst[i][9]
            #ssq='%6d' % (i+1); sbda='%6d' % (bda+1); sbaa='%6d' % (baa+1)
            ssq='%6d' % (i+1); sbda='%6d' % (bda); sbaa='%6d' % (baa)
            saa='%6d' % aanmb; sba='%6d' % banmb
            sar='%6d' % arnmb; sbr='%6d' % brnmb  
            s='BDABAA'+ssq+sbda+blk+sbaa+blk+aanam+blk+saa+blk+arnam+blk+sar+blk
            s=s+banam+blk+sba+blk+brnam+blk+sbr
            s=s+'\n' 
            f.write(s)
    # FRGMNT
    if len(frgtbl) > 0:
        s='REMARK  SEQ#  FRGNAM   CHG   # OF ATOMS'+'\n'
        f.write(s)
        for i in xrange(len(frgtbl)):
            # seq, frgnam, number of atoms in frg, frgchg
            frgnam=frgtbl[i][0]; frgnat=frgtbl[i][1]; frgchg=frgtbl[i][2]
            ssq='%6d' % (i+1); sfa='%6d' % frgnat; sch='%+4.1f' % frgchg
            if frgchg == 0.0: sch='%4.1f' % frgchg
            s='FRGMNT'+ssq+blk+frgnam+blk+sch+blk+sfa
            s=s+'\n'
            f.write(s)
    # FRGATM
    if len(frglst) > 0:
        s='REMARK  SEQ#  FRGNAM   ANAM/ANMB/RNAM/RNMB    CHG  ELM    X        Y        Z'+'\n'
        f.write(s)
        for i in xrange(len(frglst)):
            ssq='%6d' % (i+1)
            fnam=frglst[i][0]
            if len(fnam) == 6: fnam=fnam+' '
            aanam=frglst[i][1]; aanmb=frglst[i][2]
            arnam=frglst[i][3]; chanam=frglst[i][4]
            arnmb=frglst[i][5]; elm=frglst[i][6]
            saa='%6d' % aanmb; scn=chanam+' '; sar='%4d' % arnmb  
            chg=frglst[i][7]; schg='%+4.1f' % chg
            if chg == 0.0: schg='%4.1f' % chg
            xc=frglst[i][8]; sxc='%8.3f' % xc
            yc=frglst[i][9]; syc='%8.3f' % yc
            zc=frglst[i][10]; szc='%8.3f' % zc
            s='FRGATM'+ssq+blk+fnam+blk+aanam+blk+saa+blk+arnam+blk
            s=s+scn+sar+blk+schg+blk+elm+blk+sxc+blk+syc+blk+szc   
            s=s+'\n'
            f.write(s)
    f.write('END'+'\n')
    f.close()

def WriteFrgDatFile(frgfile,molnam,resnam,bdalst,frgtbl,frglst):
    if len(frgfile) <= 0: return
    
    blk=' '
    d=lib.DateTimeText()   
    #
    f=open(frgfile,'w')
    # h eader
    s='REMARK'+' Fragment data created by fu. DateTime:'+lib.DateTimeText()+'\n' 
    f.write(s)
    if len(molnam) > 0:
        s='REMARK'+' Molecule Name:'+molnam+'\n'
        f.write(s)
    if len(resnam) > 0:
        s='RESNAM '+blk+resnam+'\n'
        f.write(s)
    #BDABAA
    if len(bdalst) > 0:
        s='REMARK  SEQ#  BDA    BAA  BDA:ANAM/ANMB/RNAM/RNMB BAA:ANAM/ANMB/RNAM/RNMB'+'\n'
        f.write(s)
        for i in xrange(len(bdalst)):
            bda=bdalst[i][0]; baa=bdalst[i][1]
            aanam=bdalst[i][2]; aanmb=bdalst[i][3]
            arnam=bdalst[i][4]; arnmb=bdalst[i][5]
            acnam=bdalst[i][6]
            #banam=bdalst[i][6]; banmb=bdalst[i][7]
            #brnam=bdalst[i][8]; brnmb=bdalst[i][9]
            banam=bdalst[i][7]; banmb=bdalst[i][8]
            brnam=bdalst[i][9]; brnmb=bdalst[i][10]
            bcnam=bdalst[i][11]

            #achnam= 
            #ssq='%6d' % (i+1); sbda='%6d' % (bda+1); sbaa='%6d' % (baa+1)
            ssq='%6d' % (i+1); sbda='%6d' % (bda); sbaa='%6d' % (baa)
            saa='%6d' % aanmb; sba='%6d' % banmb
            sar='%4d' % arnmb; sbr='%4d' % brnmb  
            s='BDABAA'+ssq+sbda+blk+sbaa+blk+aanam+blk+saa+blk+arnam+blk+acnam+blk+sar+blk
            s=s+banam+blk+sba+blk+brnam+blk+bcnam+blk+sbr
            s=s+'\n' 
            f.write(s)
    # FRGMNT
    if len(frgtbl) > 0:
        s='REMARK  SEQ#  FRGNAM   CHG   # OF ATOMS'+'\n'
        f.write(s)
        for i in xrange(len(frgtbl)):
            # seq, frgnam, number of atoms in frg, frgchg
            frgnam=frgtbl[i][0]; frgnat=frgtbl[i][1]; frgchg=frgtbl[i][2]
            ssq='%6d' % (i+1); sfa='%6d' % frgnat; sch='%+4.1f' % frgchg
            if frgchg == 0.0: sch='%4.1f' % frgchg
            s='FRGMNT'+ssq+blk+frgnam+blk+sch+blk+sfa
            s=s+'\n'
            f.write(s)
    # FRGATM
    if len(frglst) > 0:
        s='REMARK  SEQ#  FRGNAM   ANAM/ANMB/RNAM/RNMB    CHG  ELM    X        Y        Z'+'\n'
        f.write(s)
        for i in xrange(len(frglst)):
            ssq='%6d' % (i+1)
            fnam=frglst[i][0]
            aanam=frglst[i][1]; aanmb=frglst[i][2]
            arnam=frglst[i][3]; chn=frglst[i][4].strip()+' ' 
            arnmb=frglst[i][5]; elm=frglst[i][6]
            #arnam=arnam+'     '; arnam=arnam[:10]
            saa='%6d' % aanmb; sar='%4d' % arnmb  
            chg=frglst[i][7]; schg='%+4.1f' % chg
            if chg == 0.0: schg='%4.1f' % chg
            xc=frglst[i][8]; sxc='%8.3f' % xc
            yc=frglst[i][9]; syc='%8.3f' % yc
            zc=frglst[i][10]; szc='%8.3f' % zc
            s='FRGATM'+ssq+blk+fnam+blk+aanam+blk+saa+blk+arnam+blk
            #s=s+sar+blk+schg+blk+elm+blk+sxc+blk+syc+blk+szc   
            s=s+chn+sar+blk+schg+blk+elm+blk+sxc+blk+syc+blk+szc   
            s=s+'\n'
            f.write(s)
    f.write('END'+'\n')
    f.close()
            
def WritePDBAtom(filename,pdbatm,pdbcon,comment):
    #pdbatm: [[label,natm,atmnam,alt,resnam,chain,resnmb,[fx,fy,fz],focc,fbfc,elm,chg],...]
    blk=' '; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; ff8='%8.3f'; ff6='%6.2f'
    fi6='%6d'
    f=open(filename,'w')
    d=datetime.datetime.now()
    s='REMARK Created by fu at '+lib.DateTimeText()+'\n' #'\r'+'\n'
    f.write(s)
    if len(comment) > 0: f.write(comment+'\n')
    for i in range(len(pdbatm)):
        label=pdbatm[i][0]
        s=blk*80; ires=0
        if label[0:3] == 'TER':
            s='TER'+3*blk
            natm=pdbatm[i][1]
            st=fi5 % natm
            s=s+st[0:5] # s[6:11], atom seq number

            """
            try:
                natm=pdbatm[i][1]
                st=fi5 % natm
                s=s+st[0:5] # s[6:11], atom seq number
                s=s+blk
                st=4*blk 
                s=s+st[0:4] # s[12:16] atmnam  
                s=s+blk  #s=s+st[0:1] # s[16:17], alt location           
                resnam=pdbatm[i][4]
                st=resnam 
                s=s+st[0:3] # s[17:20], resnam
                chain=pdbatm[i][5]
                s=s+blk+chain 
            except: pass
            """
        else:        
            natm=pdbatm[i][1]
            atmnam=pdbatm[i][2]
            alt=pdbatm[i][3]
            resnam=pdbatm[i][4]
            chain=pdbatm[i][5]
            resnmb=pdbatm[i][6]
            [fx,fy,fz]=pdbatm[i][7]
            focc=pdbatm[i][8]
            fbfc=pdbatm[i][9]
            elm=pdbatm[i][10]
            chg=pdbatm[i][11]

            s=label # s[0:6], rec name
            st=fi5 % natm
            s=s+st[0:5] # s[6:11], atom seq number
            s=s+blk
            st=atmnam+4*blk
            s=s+st[0:4] # s[12:16] atmnam  
            st=alt
            s=s+blk  #s=s+st[0:1] # s[16:17], alt location           
            st=resnam+3*blk
            s=s+st[0:3] # s[17:20], resnam
            s=s+blk+chain
            st=fi4 % resnmb+4*blk
            s=s+st[0:4] #s[22:26] resnumb
            s=s+blk # s[26:27], anchar 
            s=s+3*blk
            s=s+ff8 % fx ##s[30:38] x coord
            s=s+ff8 % fy #s[38:46] y coord
            s=s+ff8 % fz #s[46:54] z coord
            s=s+ff6 % focc #s[54:60] occupancy
            s=s+ff6 % fbfc #s[60:66] temperature factor
            s=s+10*blk
            st=elm
            st=st.strip(); st=st.rjust(2)+2*blk
            s=s+st[0:2] #s[76:78] element
            s=s+fi2 % chg #s[78:80] charge
            #
        f.write(s+'\n')
    
    if len(pdbcon) > 0 and len(pdbatm) <= 99999:
        for i in xrange(len(pdbcon)):
            if len(pdbcon[i]) > 0:
                #s='CONECT'+(fi5 % (i+1))
                s='CONECT'
                for j in pdbcon[i]: s=s+ (fi5 % (j+1))
                f.write(s+'\n')
    f.write('END\n') 
    if len(pdbatm) > 99999:
        print 'number of atoms is larger than 99999.'
        print 'warning(WritePDBAtom): conect data were not output!'
    f.close()
    
def WritePDBMolFile(filename,parnam,parfilnam,molatm,con):
    """ molatm self.atm in Molecule instance"""
    # 2013.2 KK
    blk=' '; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; fi6='%6d'
    ff8='%8.3f'; ff6='%6.2f'
    ires=0
    f=open(filename,'w')
    d=datetime.datetime.now()
    s='REMARK Created by fu at '+lib.DateTimeText()+'\n' #'\r'+'\n'
    f.write(s)
    if len(parnam) > 0:
        s='REMARK Modified from '+parnam+'('+parfilnam+').'+'\n' #'\r'+'\n'
        f.write(s)
    # env atoms
    coreresdic={}; nenv=0
    for atom in molatm:
        if atom.envflag: 
            nenv += 1; continue
        else:     
            resdat=lib.ResDat(atom)
            if not coreresdic.has_key(resdat): coreresdic[resdat]=[]
            coreresdic[resdat].append(resdat)
    if nenv > 0 and len(coreresdic) > 0:
        corereslst=coreresdic.keys()
        s='REMARK FUOPTION CORERES='+lib.ListToString(corereslst)+'\n'
        f.write(s)
    #
    for atom in molatm:
        #s=blk*80
        s=atom.MakePDBAtomText()
        s=s+'\n'
        f.write(s)
    # CONECT
    if len(molatm) > 99999:
        conect='CONECX'; frm=fi6
    else:
        conect='CONECT'; frm=fi5
    if con:
        for atom in molatm:
            s=conect+frm % atom.seqnmb
            for j in range(len(atom.conect)):
                s=s+frm % atom.conect[j]
            s=s+'\n'   
            f.write(s)
    f.write('END'+'\n')
    
    f.close()

def WriteTinkerXYZFile(xyzfile,molatm):
    """ molatm self.atm in Molecule instance"""
    #   642 crambin
    #     1  N3    17.047000   14.099000    3.625000   124     2     5     6     7
    #
    fi6='%6d'; ff12='%12.6f';
    #mess='Failed to read TINKER xyz file. file='+xyzfile
    blk=' '
    #
    f=open(xyzfile,'w') 
    #
    f.write('Tinker xyz file created by fu. '+lib.DateTimeText()+'\n' )
    #
    # write the first line
    snatm=fi6 % len(molatm)# ; snatm=snatm.rjust(6)
    f.write(snatm+2*blk+self.name+'\n')
    for atom in molatm:
        if atom.elm == 'XX': continue
        s=fi6 % (atom.seqnmb+1)
        atmnam=atom.atmnam
        if len(atom.ffatmnam) > 0: atmnam=atom.ffatmnam
        atmnam=atmnam+4*blk
        s=s+blk+atmnam[0:4]
        s=s+(ff12 % atom.cc[0])+(ff12 % atom.cc[1])+(ff12 % atom.cc[2])
        s=s+fi6 % atom.ffatmtyp
        con=atom.conect; con.sort()
        for i in con:
            ii=i+1; s=s+ (fi6 % ii)
        s=s+'\n'
        f.write(s)
    f.close()
 
def WriteXYZAtom(filename,pdbatm,bond,resfrg,ffatmtyp,comment):
    # 2013.2 KK
    blk=' '; blk2=2*blk; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; ff8='%8.3f'; ff6='%6.2f'
    ff12='%12.6f'; sq="'"; non="'None'"
    ires=0
    f=open(filename,'w')
    if len(comment) > 0: f.write(comment+'\n')
    d=datetime.datetime.now()
    s='XYZ file: Created by fu. DateTime='+lib.DateTimeText()+'\n'  #'\r'+'\n'
    f.write(s); f.write('\n')

    # label,elm,x,y,z
    nmb=0
    for i in xrange(len(pdbatm)):
        #s=blk*80
        if pdbatm[i][0][:3] == 'TER': continue
        s=''
        s=s+fi5 % (i+1) # label, seqence number
        s=s+blk2+pdbatm[i][10] # elm
        s=s+ff12 % pdbatm[i][7][0] # x
        s=s+ff12 % pdbatm[i][7][1] # y
        s=s+ff12 % pdbatm[i][7][2] # z
        s=s+'\n'
        f.write(s)
    f.write('\n')
    # BOND data
    if len(bond) > 0:
        f.write('BOND\n')
        #if len(bond) > 0:
        for i,j,k in bond:
            s=''
            s=s+fi5 % (i+1)+2*blk+fi5 % (j+1)+2*blk+(fi2 % k)
            f.write(s+'\n')
        f.write('\n')
    
    if len(resfrg) > 0:
        f.write('FRGMNT\n')
        for i in xrange(len(resfrg)):
            atmnam=resfrg[i][0]; seqnmb=resfrg[i][1]
            resnam=resfrg[i][2]; resnmb=resfrg[i][3]
            chainnam=resfrg[i][4]; charge=resfrg[i][5]
            grpnam=resfrg[i][6]
            frgnam=resfrg[i][7]; frgchg=resfrg[i][8]
            frgbaa=resfrg[i][9]
            s=''
            s=s+sq+atmnam+sq # atmnam
            s=s+blk2+sq+(fi5 % seqnmb)+sq # seqnmb
            s=s+blk2+sq+resnam+sq # resnam
            s=s+blk2+sq+(fi4 % resnmb)+sq
            s=s+blk2+sq+chainnam+sq
            s=s+blk2+sq+(ff6 % charge)+sq
            if grpnam == '': s=s+blk2+non
            else: s=s+blk2+sq+grpnam+sq
            if frgnam == '':
                s=s+blk2+non+blk2+non+blk2+non
            else:
                s=s+blk2+sq+frgnam+sq
                s=s+blk2+sq+(ff6 % frgchg)+sq
                #if atom.frgbaa >= 0:
                s=s+blk2+sq+(fi5 % frgbaa)+sq
                #else:s=s+blk2+"'   -1'" 
            # force field atom type
            if len(ffatmtyp) == 0:
                s=s+blk2+non+blk2+sq+(fi5 % 0)+sq
            else:
                s=s+blk2+sq+ffatmtyp[i][0]+sq
                s=s+blk2+sq+(fi5 % ffatmtyp[i][1])+sq
            
            f.write(s+'\n')
        f.write('\n')
    
    f.close()
                            
def WriteXYZMolFile(filename,molatm,bond,resfrg):
    """ molatm self.atm in Molecule instance"""
    # 2013.2 KK
   
    blk=' '; blk2=2*blk; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; ff8='%8.3f'; ff6='%6.2f'
    ff12='%12.6f'; sq="'"; non="'None'"
    ires=0
    f=open(filename,'w')
    d=datetime.datetime.now()
    s='XYZ file: Created by fu. DateTime='+lib.DateTimeText()+'\n'  #'\r'+'\n'
    f.write(s); f.write('\n')
    # label,elm,x,y,z
    for atom in molatm:
        #s=blk*80
        s=''
        s=s+(fi5 % (atom.seqnmb)) # label
        s=s+blk2+atom.elm # elm
        s=s+ff12 % atom.cc[0] # x
        s=s+ff12 % atom.cc[1] # y
        s=s+ff12 % atom.cc[2] # z
        s=s+'\n'
        f.write(s)
    f.write('\n')

    # BOND data
    if bond:
        f.write('BOND\n')
        for i in xrange(len(molatm)):
            atom=molatm[i]
            ii=atom.seqnmb
            if len(atom.conect) > 0:
                for j in range(len(atom.conect)):
                    s=''
                    try:
                        s=s+(fi5 % atom.seqnmb)+2*blk+(fi5 % atom.conect[j])+2*blk+(fi2 % atom.bndmulti[j])
                    except:
                        s=s+(fi5 % atom.seqnmb)+2*blk+(fi5 % atom.conect[j])+2*blk+(fi2 % 1)
                    s=s+'\n'
                    f.write(s)
        f.write('\n')
    
    if resfrg:
        f.write('FRGMNT\n')
        for atom in molatm:
            s=''
            s=s+sq+atom.atmnam+sq # atmnam
            s=s+blk2+sq+(fi5 % atom.seqnmb)+sq # seqnmb
            s=s+blk2+sq+atom.resnam+sq # resnam
            s=s+blk2+sq+(fi4 % atom.resnmb)+sq
            s=s+blk2+sq+atom.chainnam+sq
            
            s=s+blk2+sq+(ff6 % atom.charge)+sq # charge
            s=s+blk2+sq+atom.grpnam+sq # group name
            #if atom.frgnam == '':
            #    s=s+blk2+non+blk2+non+blk2+non
            #else:
            s=s+blk2+sq+atom.frgnam+sq
            s=s+blk2+sq+(ff6 % atom.frgchg)+sq
            #if atom.frgbaa >= 0:
            s=s+blk2+sq+(fi5 % atom.frgbaa)+sq
                #else:s=s+blk2+"'   -1'" 
            # force field atom type
            #if atom.ffatmtyp == 0:
            #    s=s+blk2+non+blk2+sq+(fi5 % atom.ffatmtyp)+sq
            #else:
            #    s=s+blk2+sq+atom.ffatmnam+sq
            #    s=s+blk2+sq+(fi5 % atom.ffatmtyp)+sq
            
            s=s+'\n'
            f.write(s)
        f.write('\n')
    
    f.close()

def ReadLoggingMethodFile(logmethfile):
    """
    
    :param str logmethfile: logging methd definition file
    :return dic methdic: {methodname: instancename,...}
    """
    methdic={}
    if len(logmethfile) <= 0: return methdic
    if not os.path.exists(logmethfile):
        print 'lib.ReadLoggingMethFile: file not found. file='+logmethfile
        return methdic
    f=open(logmethfile,'r')
    for s in f.readlines():
        s=s.strip()
        if s[:1] == '#': continue
        ns=s.find('#')
        if ns >= 0: s=s[:ns]
        items=lib.SplitStringAtSpaces(s)
        if len(items) < 2: continue
        classmeth=items[0].strip()
        try: methnam=classmeth.split('.')[1]
        except: continue
        instnam=items[1].strip()+'.'+methnam
        methdic[classmeth]=instnam
    f.close()
    return methdic
    
def ReadDatInFrgDat(frgfile):
    # note: sequence number of atoms begins from 1 in return data !
    # read fragment file (xxx.frg) and return molnam,bdalst
    resnam='   '; frglst=[]; frgchglst=[]; frgatmlst=[]; bdalst=[]
    frgdic={}
    try:
        f=open(frgfile,'r')
    except IOError:
        print 'Error(ReadPDBMol): File not found. file name=', frgfile
    else:        
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n','')
            if s.startswith('RESNAM',0,6): resnam=s[8:11]
            if s.startswith('BDABAA',0,6):
                tmp=[]
                aanam=s[26:30]; tmp.append(aanam)
                banam=s[49:53]; tmp.append(banam)
 
                bda=s[12:18]; tmp.append(int(bda)) # internal seq number
                baa=s[18:26]; tmp.append(int(baa)) # internal seq number
                #item=s.split()
                #bda=int(item[2]); baa=int(item[3])
                bdalst.append(tmp)

            if s.startswith('FRGMNT',0,6):
                item=s.split()
                frglst.append(item[2])
                frgchglst.append(float(item[3]))
            
            if s.startswith('FRGATM',0,6):
                #item=s.split()
                #nam=item[2]; ia=int(item[4])
                nam=s[13:19]; ia=int(s[24:31])
                if frgdic.has_key(nam): frgdic[nam].append(ia)
                else:
                    frgdic[nam]=[]; frgdic[nam].append(ia)
                #    print 'Error occured in reading fragment charge',s
    f.close()
    for nam in frglst: frgatmlst.append(frgdic[nam])
    
    return resnam,frglst,frgchglst,bdalst,frgatmlst

def ReadFrameFile(filcon):
    # 2013.2 KK
    blk=' '; blk4='    '; rcon='CONECT'; rnam='RESIDUE'
    ncon=0; condat=[]; resnam=''
    try:
        fcon=open(filcon)
    except IOError:
        print 'Error(ReadFrameFile): File not found. file name=', filcon
    else:        
        for s in fcon.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.startswith(rnam,0,7) == 1:
                resnam=s[10:13]
            if s.startswith(rcon,0,6) == 1:
                tmp=[]
                nl=len(s); s=s+blk*(80-nl)
                ncon += 1
                atmnam=s[12:16]
                con1=s[21:25]; con2=s[26:30]; con3=s[31:35]; con4=s[36:40]
                con5=s[41:45]; con6=s[46:50]; con7=s[51:55]; con8=s[56:60]
                tmp.append(atmnam)
                if con1 != blk4: tmp.append(con1)
                if con2 != blk4: tmp.append(con2)
                if con3 != blk4: tmp.append(con3)
                if con4 != blk4: tmp.append(con4)
                if con5 != blk4: tmp.append(con5)
                if con6 != blk4: tmp.append(con6)
                if con7 != blk4: tmp.append(con7)
                if con8 != blk4: tmp.append(con8)
                condat.append(tmp)

        fcon.close()                           

    return resnam,condat

def ReadFrgAtom(frgfile):
    # note: sequence number of atoms begins from 1 in return data !
    # read fragment file (xxx.frg) and return molnam,bdalst
    resnam='   '; frglst=[]; frgchglst=[]; frgatmlst=[]; bdalst=[]; atmdat=[]
    frgdic={}
    try:
        f=open(frgfile,'r')
    except IOError:
        print 'Error(ReadPDBMol): File not found. file name=', frgfile
    else:        
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n','')
            if s.startswith('RESNAM',0,6): resnam=s[8:11]
            if s.startswith('BDABAA',0,6):
                tmp=[]
                aanam=s[26:30]; tmp.append(aanam)
                banam=s[49:53]; tmp.append(banam)
 
                bda=s[12:18]; tmp.append(int(bda)) # internal seq number
                baa=s[18:26]; tmp.append(int(baa)) # internal seq number
                #item=s.split()
                #bda=int(item[2]); baa=int(item[3])
                bdalst.append(tmp)

            if s.startswith('FRGMNT',0,6):
                item=s.split()
                frglst.append(item[2])
                frgchglst.append(float(item[3]))
            
            if s.startswith('FRGATM',0,6):
                #item=s.split()
                frgnam=s[13:19]; atmnam=s[20:24]; ia=int(s[24:31])
                res=s[32:35]; chain=s[36:37]; resnmb=int(s[37:42])    
                chg=float(s[42:47:]); elm=s[48:50]
                x=float(s[50:59]); y=float(s[59:68]); z=float(s[68:77])
                #nam=item[2]; ia=int(item[4])
                if frgdic.has_key(frgnam): frgdic[frgnam].append(ia)
                else:
                    frgdic[frgnam]=[]; frgdic[frgnam].append(ia)
                resdat=res+':'+str(resnmb)+':'+chain
                cc=[x,y,z]
                """atmnam,resdat,elm,cc"""
                atmdat.append([ia,atmnam,resdat,cc,frgnam])
                #    print 'Error occured in reading fragment charge',s
    f.close()
    for nam in frglst: frgatmlst.append(frgdic[nam])
    # reorder atmdat
    iord=[]
    for lst in atmdat: iord.append(lst[0])
    indx=numpy.argsort(iord)
    tmp=[]
    for i in indx: tmp.append(atmdat[i])
    atmdat=tmp
    
    return resnam,frglst,frgchglst,bdalst,frgatmlst,atmdat

def ReadFrgDatFile(frgfile,natm):
    """ use ReadDatInFrgDat instead """
    # 2013.2 KK
    # read fragment file (xxx.frg) and return molnam,bdalst
    resnam='   '; bdalst=[]
    frgchglst=natm*[0.0]; frgatmlst=natm*[''] #['',-1]
    try:
        f=open(frgfile,'r')      
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n','')
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            if s.startswith('RESNAM',0,6):
                resnam=s[8:11]
                #molnam='POLYPEPTIDE'
            if s.startswith('BDABAA',0,6):
                tmp=[]
                aanam=s[26:30]; tmp.append(aanam)
                banam=s[49:53]; tmp.append(banam)
 
                bda=s[12:18]; tmp.append(int(bda)-1) # internal seq number
                baa=s[18:26]; tmp.append(int(baa)-1) # internal seq number
                #item=s.split()
                #bda=int(item[2]); baa=int(item[3])
                bdalst.append(tmp)
            #if s.startswith('FRGMNT',0,6):
            #    item=s.split()
            #    frgchglst.append(float(item[3]))
            if s.startswith('FRGATM',0,6):
                item=s.split()
                if len(item[2].strip()) == 6: case=0
                else: case=1
                if case == 0:    
                    #ia=int(s[24:31])-1
                    ia=int(s[7:12])-1
                    frgatmlst[ia]=s[13:19] #item[2]  #[item[2],int(item[4])]
                    chg=float(s[42:47]) #float(item[7])
                elif case == 1:
                    ia=int(s[25:32])-1
                    frgatmlst[ia]=s[13:19] # truncate the last one character
                    chg=float(s[43:48])
                neg=False
                if chg < 0.0: neg=True
                if abs(chg) > 0.29:
                    if abs(chg) < 0.4: # 0.3 -> 0.34
                        if neg: chg -= 0.04
                        else: chg += 0.04
                    else: # 0.5 -> 0.51, 1.0 > 1,01
                        if neg: chg -= 0.01
                        else: chg += 0.01
                else: chg=0.0
                frgchglst[ia]=chg
                
        f.close()
    except IOError:
        print 'Error(ReadFrgDat): File not found. file name=', frgfile

    return resnam,bdalst,frgchglst,frgatmlst

def ReadGMSOptGeom(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    #com0='***** EQUILIBRIUM GEOMETRY LOCATED' # [6:40]
    com0='COORDINATES OF ALL ATOMS ARE (ANGS)'
    com1=' -----' # [0:6]   CHARGE          LOW.POP.     CHARGE
    data=' 1           6.0   2.3410913281  -0.2869878297  -0.0070806229^'
    com2='**** THE GEOMETRY SEARCH IS NOT CONVERGED!'        
    endstr='STEP CPU TIME'
    newl='\n'
    ian=[]; xyz=[]
    ret=0
    try:
        fmo=open(filename)
        found0=False; found1=False #; found2=False
        for s in fmo.readlines():
            if not found1:
                #if s.startswith(com0,6,40) or s.startswith(com2,1,43):
                if s.startswith(com0,1,36):
                    if s.startswith(com2,1,43): ret=1
                    found0=True; continue
                if found0 and s.startswith(com1,0,6): # com1 is found
                    found1=True; ian=[]; xyz=[]
                    continue
            else:
                if s == newl:
                    found0=False; found1=False; continue
                if s.startswith(endstr,1,14):
                    found0=False; found1=False; continue
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                try:
                    ian.append(int(float(item[1])))
                    x=float(item[2]); y=float(item[3]); z=float(item[4])
                    xyz.append([x,y,z])
                except: pass
        fmo.close()
    
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        ret=2
    return ret,ian,xyz

def ReadLayer(layerfile):
    if len(layerfile) <= 0: return
    f=open(layerfile,"r")
    dat=[]
    for s in f.readlines():
        if s[0:1] == '#': continue
        s=s.replace(',',''); d=s.split()
        for i in d:
            dat.append(int(i))
    f.close() 
    nd=len(dat)

    return dat

def ReadNumberOfAtomsInFrgDat(frgfile):
    natm=-1
    try:
        f=open(frgfile,'r')      
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n','')
            if s.startswith('FRGATM',0,6): natm += 1
        f.close()
    except IOError:
        print 'Error(ReadNumberOfAtomsInFrgdat): File not found. file name=', frgfile
    return natm

def ReadPDBAtom(pdbfile):
    # 2013.2 KK
    # pick up "ATOM", "HETATM", "TAR" and "CONECT" data in pdb file
    # return pdbdat
    reca='ATOM  '; rech='HETATM'; rect='TER'; blk=' '
    recf='REMARK FUOPTION' # 0:15
    natm=0; ncon=0; pdbatm=[]; pdbcon=[]; pdbdat=[]; pdbmol=[]
    label='      '
    try:
        fpdb=open(pdbfile)
    except IOError:
        mess='Error(ReadPDBAtom): File not found. file name='+pdbfile
        #lib.MessageBoxOK(mess,"")
        print mess
        return [],[],{}
    else:        
        natm=0; pdbatm=[]; fuoptdic={}
        # atom data with dummy con data         
        for s in fpdb.readlines():
            ns=s.find('#') 
            if ns > 0: s=s[:ns]
            s=s.replace('\r','')
            s=s.replace('\n','')
            ns=len(s); s=s+(80-ns)*' '
            atmrec=0
            if s.startswith(reca,0,6) or \
                           s.startswith(rech,0,6):                  
                label=s[0:6]
                atmrec=1
                try:
                    atmnmb=int(s[6:11])
                except: atmnmb=0
                atmnam=s[12:16]
                alt=s[16:17]
                if alt != blk and alt != 'A': continue
                natm += 1
                resnam=s[17:20]
                chain=s[21:22]
                resnmb=0
                try:
                    if s[22:26] != blk*3:
                        resnmb=int(s[22:26])
                except:
                    resnmb=0
                # s[26:27]=Achar???
                # the followin two lines are special code for HyperChem ver.7
                if s[54:55] != blk:
                    s=s[0:27]+s[28:]+blk
                fx=float(s[30:38])
                fy=float(s[38:46])
                fz=float(s[46:54])
                focc=0.0
                try:
                    if s[54:60] != blk*6:
                        focc=float(s[54:60])
                except:
                    focc=0.0
                fbfc=0.0
                try:
                    if s[60:66] != blk*6:
                        fbfc=float(s[60:66])
                except:
                    fbfc=0.0
                elmdat=s[76:78]  # kk
                #if s[76:78] == blk*2:
                elm=lib.AtmNamToElm(atmnam)
                if elm == '??' and len(elmdat) > 0: elm=elmdat
                #if len(elmdat) > 0: elm=elmdat
                #else: elm=Molecule.AtmNamElm(atmnam)
                chg=0.0
                try:
                    if s[78:80] != blk*2:  # kk
                        chg=int(s[78:80])
                except:
                    chg=0                      
            elif s.startswith(rect,0,3):
                label='TER   '
                atmrec=1
                natm += 1
                atmnam=blk*4;
                atmnam=natm
                try:
                    if s[6:11] != blk*5: atmnmb=int(s[6:11])
                except: atmnmb=int(natm)
                try: resnam=s[17:20]
                except: resnam='   '
                try: chain=s[21:22]
                except: chain=' '
                #if s[22:26] != blk*3:
                #    resnmb=int(s[22:26])
                #else:
                #    resnmb=0
                resnmb=0
                alt=blk; fx=0.0; fy=0.0; fz=0.0
                elm='XX'; focc=0.0; fbfc=0.0; chg=0 
                try:
                    if s[7:12] != blk*5: atmnmb=int(s[6:11])
                except: atmnmb=natm
                #iconi.append(natm)
            # FUOPTION
            elif s.startswith(recf,0,15):
                opts=s[15:]
                items=opts.split('=')
                optnam=items[0].strip()
                if len(items) >= 2:
                    value=items[1].strip()
                    if value[0] == '[' and value[-1] == ']':
                        value=lib.StringToList(value)
                    fuoptdic[optnam]=value
                    continue
            else: continue
            ###if not atmrec: continue
            #label=s[0:6]
            dat=[label,natm,atmnam,alt,resnam,chain,resnmb,[fx,fy,fz],focc,fbfc,elm,chg]
            pdbatm.append(dat)
        # read conect data
        natm=len(pdbatm)
        reccon='CONECT'; reccox='CONECX'; ncon=0; pdbcon=natm*[]
        fpdb.seek(0)  
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s[0:1] == '#': continue
            if s.startswith(reccon,0,6):
                ns=len(s); s=s+(80-ns)*' '
                ncon += 1       
                item=[]; con=[]
                if s[6:11] != blk*5:
                    item.append(int(s[6:11]))
                if s[11:16] != blk*5:
                    item.append(int(s[11:16]))
                if s[16:21] != blk*5:
                    item.append(int(s[16:21]))
                if s[21:26] != blk*5:
                    item.append(int(s[21:26]))
                if s[26:31] != blk*5:
                    item.append(int(s[26:31]))
                if len(item) > 0:
                    for i in range(len(item)):
                        con.append(int(item[i])-1)
            if s.startswith(reccox,0,6):
                ns=len(s); s=s+(80-ns)*' '
                ncon += 1       
                item=[]; con=[]
                if s[6:12] != blk*5:
                    item.append(int(s[6:12]))
                if s[12:18] != blk*5:
                    item.append(int(s[12:18]))
                if s[18:24] != blk*5:
                    item.append(int(s[18:24]))
                if s[24:30] != blk*5:
                    item.append(int(s[24:30]))
                if s[30:36] != blk*5:
                    item.append(int(s[30:36]))
                if len(item) > 0:
                    for i in range(len(item)):
                        con.append(int(item[i])-1)
                pdbcon.append(con)            
        fpdb.close()                         
        if len(pdbatm) < 0 :
            mess="Error(ReadPDBAtom): No ATOM records in "+pdbfile
            #lib.MessageBoxOK(mess,"")
            print mess
        
        return pdbatm,pdbcon,fuoptdic

def ReadPDBMissingAtoms(pdbfile):
    # pick up "REMARK"-"MISSING ATOMS" data in pdb
    # missingatoms: [[chain,resnam,resnmb,[atmnam1,atmnam2,...]],...]
    #d=lib.DateTimeText()
    rem="REMARK"; key1="MISSING ATOM"; key2="M RES C" #SSEQI  ATOM"
    missingatoms=[]; key11="MISSING HETEROATOM"
    #rem='REMARK'; item=''
    try:
        fpdb=open(pdbfile)
    except IOError:
        print 'Error(ReadPDBRem): File not found. file name=', pdbfile
    else:        
        found1=False; found2=False
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.startswith(rem,0,6) and \
                   (s.startswith(key1,11,23) or s.startswith(key11,11,29)):
                found1=True; continue
            if found1 and s.startswith(key2,13,20):
                found2=True; continue
            if not found1 or not found2: continue
            tmp=s.split()
            if found1 and found2 and len(tmp) <= 2: break
            resnam=tmp[2].strip()
            chain=tmp[3].strip()
            try: resnmb=int(tmp[4].strip())
            except: break
            atmnam=[]
            try: 
                for i in range(5,len(tmp)):
                    nam=tmp[i].strip()  
                    if len(nam) == 2: nam=" "+nam+" "
                    if len(nam) == 3: nam=" "+nam
                    atmnam.append(nam)
            except: pass
            missingatoms.append([chain,resnam,resnmb,atmnam])
    fpdb.close()
    
    return found1,missingatoms

def ReadPDBMissingResidues(pdbfile):
    # pick up "REMARK"-"MISSING RESIDUES" data in pdb
    # missingresdues: [[chain,resnam,resnmb],...]
    #d=lib.DateTimeText()
    rem="REMARK"; key1="MISSING RESIDUES"; key2="M RES C SSSEQI"
    missingresidues=[]
    #rem='REMARK'; item=''
    try:
        fpdb=open(pdbfile)
    except IOError:
        print 'Error(ReadPDBRem): File not found. file name=', pdbfile
    else:        
        found1=False; found2=False
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.startswith(rem,0,6) and s.startswith(key1,11,27):
                found1=True; continue
            if found1 and s.startswith(key2,13,32):
                found2=True; continue
            if not found1 or not found2: continue
            tmp=s.split()
            if found1 and found2 and len(tmp) <= 2: break
            resnam=tmp[2].strip()
            chain=tmp[3].strip()
            try: resnmb=int(tmp[4].strip())
            except: break
            missingresidues.append([chain,resnam,resnmb])
    fpdb.close()
    
    return found1,missingresidues

def ReadPDBMol(pdbfile):
    # 2013.2 KK
    # pick up "ATOM", "HETATM", "TAR" and "CONECT" data in pdb file
    # return pdbdat
    def AppendCon(iconi,itmp):
        try: iconi.append(nmbdic[itmp])
        except: pass
        return iconi
    
    reca='ATOM  '; rech='HETATM'; rect='TER   '; recc='CONECT'; blk=' '
    recx='CONECX'
    recf='REMARK FUOPTION' # 0:15
    natm=0; ncon=0; pdbatm=[]; pdbcon=[]; pdbdat=[]; pdbmol=[]
    fuoptdic={}
    try:
        fpdb=open(pdbfile)
    except IOError:
        mess='Error(ReadPDBMol): File not found. file name='+pdbfile
        lib.MessageBoxOK(mess,"")
        return [],{}
    else:        
        coord=[]; connect=[]; atmname=[]; atmnumber=[]; resname=[]; resnumber=[]
        chaname=[]; altnate=[]; element=[]; occupation=[]; bfactor=[]; charge=[]
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            ns=len(s); s=s+(80-ns)*' '
            if s.startswith(reca,0,6) or \
              s.startswith(rech,0,6) or \
              s.startswith(rect,0,6):            
                nl=len(s)
                s=s+blk*(80-nl)
                pdbatm.append(s)
                natm += 1
            elif s.startswith(recc,0,6):
                nl=len(s)
                s=s+blk*(80-nl)
                pdbcon.append(s)
                ncon += 1
            elif s.startswith(recx,0,6):
                nl=len(s)
                s=s+blk*(80-nl)
                pdbcon.append(s)
                ncon += 1
            # FUOPTION
            elif s.startswith(recf,0,15):
                opts=s[15:]
                items=opts.split('=')
                optnam=items[0].strip()
                if len(items) >= 2:
                    value=items[1].strip()
                    if value[0] == '[' and value[-1] == ']':
                        value=lib.StringToList(value)
                    fuoptdic[optnam]=value
                    continue

        fpdb.close()                         
        pdbdat=pdbatm+pdbcon           
        if len(pdbdat) < 0 :
            mess="Error(ReadPDBMol): No ATOM records in "+pdbfile
            lib.MessageBoxOK(mess,"")
            return []
        nlen=len(pdbdat)
        if natm > 99999: extend=True
        else: extend=False
        natm=0; ncon=0; nmbdic={}; nalt=0; altlst=[]
        # atom data with dummy con data         
        for s in pdbatm: #dat:
            #tmp=[]
            iconi=[]
            if s.startswith(reca,0,6) or \
                           s.startswith(rech,0,6):                  
                try:
                    atmnmb=int(s[6:11])
                except: atmnmb=0
                atmnam=s[12:16]
                alt=s[16:17]
                if alt != blk and alt != 'A': 
                    nalt += 1
                    altlst.append(s)
                    continue
                natm += 1
                #if natm > 9999: natm=0
                resnam=s[17:20]
                chain=s[21:22]
                resnmb=0
                try:
                    if s[22:26] != blk*3:
                        resnmb=int(s[22:26])
                except:
                    resnmb=0
                # s[26:27]=Achar???
                # the followin two lines are special code for HyperChem ver.7
                if s[54:55] != blk:
                    s=s[0:27]+s[28:]+blk
                fx=float(s[30:38])
                fy=float(s[38:46])
                fz=float(s[46:54])
                focc=0.0
                try:
                    if s[54:60] != blk*6:
                        focc=float(s[54:60])
                except:
                    focc=0.0
                fbfc=0.0
                try:
                    if s[60:66] != blk*6:
                        fbfc=float(s[60:66])
                except:
                    fbfc=0.0
                elmdat=s[76:78]  # kk
                #if s[76:78] == blk*2:
                
                elm=lib.AtmNamToElm(atmnam)
                if elm == '??' and len(elmdat) > 0: elm=elmdat
                #if len(elmdat) > 0: elm=elmdat
                #else: elm=Molecule.AtmNamElm(atmnam)
                chg=0.0
                try:
                    if s[78:80] != blk*2:  # kk
                        chg=int(s[78:80])
                except:
                    chg=0                      
            elif s.startswith(rect,0,6):
                natm += 1
                #if natm > 9999: natm=0
                atmnam=blk*4;
                atmnmb=natm
                try:
                    if s[6:11] != blk*5:
                        atmnmb=int(s[6:11])
                except:
                    atmnmb=int(natm)
                resnam=s[17:20]
                chain=s[21:22]
                #if s[22:26] != blk*3:
                #    resnmb=int(s[22:26])
                #else:
                #    resnmb=0
                resnmb=0
                alt=blk; fx=0.0; fy=0.0; fz=0.0
                elm='XX'; focc=0.0; fbfc=0.0; chg=0 
                if s[7:12] != blk*5: atmnmb=int(s[6:11])
                else: atmnmb=natm
                #iconi.append(natm)
            else:
                continue 
            iconi.append(natm-1)
            if extend: nmbdic[natm]=natm-1
            else: nmbdic[atmnmb]=natm-1
            coord.append([fx,fy,fz]); connect.append(iconi)
            atmname.append(atmnam); atmnumber.append(atmnmb)
            resname.append(resnam); resnumber.append(resnmb)
            chaname.append(chain); altnate.append(alt)
            element.append(elm); occupation.append(focc)
            bfactor.append(fbfc); charge.append(chg)
        #
        for s in pdbcon: #pdbdat:
            iseq=-1
            if s.startswith(recc,0,6):
                ncon += 1       
                itmp=-1; iconi=[]; iseq=-1
                if s[6:11] != blk*5:
                    itmp=int(s[6:11])
                    if nmbdic.has_key(itmp): iseq=nmbdic[itmp]
                        #iseq=nmbdic[itmp]
                    else: continue
                if s[11:16] != blk*5:
                    itmp=int(s[11:16]); iconi=AppendCon(iconi,itmp)
                if s[16:21] != blk*5:
                    itmp=int(s[16:21]); iconi=AppendCon(iconi,itmp)
                if s[21:26] != blk*5:
                    itmp=int(s[21:26]); iconi=AppendCon(iconi,itmp)
                if s[26:31] != blk*5:
                    itmp=int(s[26:31]); iconi=AppendCon(iconi,itmp)
            elif s.startswith(recx,0,6):
                ncon += 1; iseq=-1      
                itmp=-1; iconi=[]
                if s[6:12] != blk*6:
                    itmp=int(s[6:12])
                    if nmbdic.has_key(itmp): iseq=nmbdic[itmp]
                        #iseq=nmbdic[itmp]
                    else: continue
                if s[12:18] != blk*6:
                    itmp=int(s[12:18]); iconi=AppendCon(iconi,itmp)
                if s[18:24] != blk*6:
                    itmp=int(s[18:24]); iconi=AppendCon(iconi,itmp)
                if s[24:30] != blk*6:
                    itmp=int(s[24:30]); iconi=AppendCon(iconi,itmp)
                if s[30:36] != blk*6:
                    itmp=int(s[30:36]); iconi=AppendCon(iconi,itmp)
            if len(iconi) > 0 and iseq >= 0:
                #
                connect[iseq]=connect[iseq]+iconi
                            
        if len(atmname) < 0 :
            mess="Error(ReadPDBMol): No atom data in "+pdbfile
            lib.MessageBoxOK(mess,"")
            return []
        
        pdbmol=[coord,connect,atmname,atmnumber,resname,resnumber,  \
                chaname,altnate,element,occupation,bfactor,charge]

        return pdbmol,fuoptdic

def ReadPDBRem(pdbfile,rem,key):
    # 2013.2 KK
    # rem: may be "REMARK" and "SEQRES" et al in 0-6 culomns.
    # key: may be "MISSSING RESIDUES" al., appearing in PDB REMARK
    #d=lib.DateTimeText()
    item=[]
    #rem='REMARK'; item=''
    try:
        fpdb=open(pdbfile)
    except IOError:
        print 'Error(ReadPDBRem): File not found. file name=', pdbfile
    else:        
        fount=False
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.startswith(rem,0,6) == 1:
                i=s.find(key)
                if i == -1: continue   
                else: found=True
                if found:
                    ii=i+len(key)
                    tmp=s[ii:] 
                    jj=tmp.find(' ')
                    if jj > 0:
                        found=False
                    tmp=s[ii:jj]    
                    break
        fpdb.close()
    return item

def ReadPDBSSBonds(pdbfile):
    # pick up "REMARK"-"MISSING ATOMS" data in pdb
    # missingatoms: [[chain,resnam,resnmb,[atmnam1,atmnam2,...]],...]
    #d=lib.DateTimeText()
    rem="SSBOND"
    ssbond=[]
    #rem='REMARK'; item=''
    try:
        fpdb=open(pdbfile)
    except IOError:
        print 'Error(ReadPDBRem): File not found. file name=', pdbfile
    else:        
        found=False
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.startswith(rem,0,6): found=True
            else: continue
            if found and not s.startswith(rem,0,6): break
            tmp=s.split()
            if found and len(tmp) <= 2: break
            resnam1=tmp[2].strip()
            chain1=tmp[3].strip()
            resnmb1=int(tmp[4].strip())
            resnam2=tmp[5].strip()
            chain2=tmp[6].strip()
            resnmb2=int(tmp[7].strip())
            ssbond.append([chain1,resnam1,resnmb1,chain2,resnam2,resnmb2])
    fpdb.close()
    
    return ssbond

def ReadPDBSeqRes(pdbfile):
    # pick up "SEQRES" data in pdb
    # resdic: {chain1:[resnam1,resnam2,...],chain2:[resnam1,resnam2,...],   }
    #d=lib.DateTimeText()
    rem="SEQRES"
    seqresdic={}
    #rem='REMARK'; item=''
    try:
        fpdb=open(pdbfile)
    except IOError:
        print 'Error(ReadPDBRem): File not found. file name=', pdbfile
    else:        
        found=False
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if not s.startswith(rem,0,6):
                if found: break
            else:                    
                found=True   
                tmp=s.split()
                chain=tmp[2].strip()       
                if not seqresdic.has_key(chain): seqresdic[chain]=[]
                for i in range(4,len(tmp)):
                    res=tmp[i].strip()    
                    seqresdic[chain].append(res)
    fpdb.close()
    
    return seqresdic

def ReadTinkerXYZ(xyzfile):
    """ Read TINKER xyz file
    
    :param str xyzfile: file name
    :return: tinatm - [[seq,atmnam,xyz,type,con],...]
    :TINKER: http://dasher.wustl.edu/tinker/ 
    """
    tinatm=[]
    #
    f=open(xyzfile,'r')        
    # read the first line and get natm and title
    try:
        i=0
        for s in f.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            s=s.strip()
            if len(s) <= 0: break
            item=s.split()
            i += 1
            if i == 1:                 
                continue
            seq=int(item[0])-1
            atmnam=item[1]
            xyz=[]
            xyz.append(float(item[2])); xyz.append(float(item[3])); xyz.append(float(item[4]))
            type=int(item[5])
            con=[]
            for j in range(6,len(item)): con.append(int(item[j])-1)
            tinatm.append([seq,atmnam,xyz,type,con])          
    except:
        mess='Failed to read TINKER xyz file. file='+xyzfile            
        lib.MessageBoxOK(mess,"")        
    
    f.close()
    return tinatm

def ReadTinkerZmt(zmtfile):
    # read tinker z-matrix file
    # return tinzmt: [[ip1,ip2,ip3,iz,bl,ba,da],...]
    tinzmt=[]
    #
    f=open(zmtfile,'r') 
    # read the first line and get natm and title
    try:
        i=0
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n',''); s=s.strip()
            if len(s) <= 0: break
            item=s.split()
            i += 1
            if i == 1: 
                natm=int(item[0]); continue
            seq=int(item[0]); atm=item[1].strip(); atmtyp=int(item[2])
            if i == 2:
                ip1=0; bl=0.0; ip2=0; ba=0.0; ip3=0; da=0.0; iz=0
            if i >= 3:
                ip1=int(item[3]); bl=float(item[4])               
            if i >= 4:
                ip2=int(item[5]); ba=float(item[6])
            if i >= 5:
                ip3=int(item[7]); da=float(item[8]); iz=int(item[9])
            tinzmt.append([ip1,ip2,ip3,iz,bl,ba,da,atm,atmtyp])

    except:
        mess='Failed to read TINKER internal coordinate file. file='+zmtfile            
        lib.MessageBoxOK(mess,"")

    f.close()            
    return tinzmt

def ReadMolFile(molfile):
    """ Read 'mol' and 'sdf' format file
    
    :param str molfile: file name
    :return: moldat(lst) - list of moldata, [[title(str),comment(str),resnam(str),molatm(lst)],...]
                           molatm [[elm(str*2):coord(lst),bonds)(lst),bondmulti(lst)],...]
                           coord(lst):[[x(float),y(float),z(float)],...]
                           bonds:[[atomi(int),atomj(int)],..]
                           bondmulti: [bondmultiplicity(int),...]
    """
    moldat=[]
    if not os.path.exists(molfile):
        mess='Not found molfile='+molfile
        lib.MessageBoxOK(mess,'lib.ReadMolFile')
        return moldat
    f=open(molfile,'r')
    k=0; coord=[]; elm=[]; bonds=[]; bondmulti=[]; molatm=[]
    title=''; comment=''; resnam=''; done=False
    for s in f.readlines():
        k += 1 
        if k == 1: title=s.strip()
        elif k == 2: comment=s.strip()
        elif k == 3: 
            s=s.strip()
            items=s.split(' ')
            if len(items) > 0: resnam=items[0].strip()
        elif k == 4: # natom,nbonds,...
            natoms=int(s[:3].strip())
            nbonds=int(s[3:6].strip())
        elif k >= 5 and k <= 4+natoms: # x,y,z,elm
            x=float(s[:10])
            y=float(s[10:20])
            z=float(s[20:30])
            coord.append([x,y,z])
            e=s[31:33].upper().strip()
            if len(e) <= 1: e=' '+e
            elm.append(e)
        elif k >= 5+natoms and k <= 4+natoms+nbonds:
            iat=int(s[:3])-1
            jat=int(s[3:6])-1
            ib=max(iat,jat); jb=min(iat,jat)
            bonds.append([ib,jb])
            bondmulti.append(int(s[6:9]))
        else:
            s=s.strip()
            if s[:1] == 'M':
                if s.find('END') >= 0:
                    molatm.append(elm); molatm.append(coord) 
                    molatm.append(bonds); molatm.append(bondmulti)            
                    moldat.append([title,comment,resnam,molatm])                
                    done=True
            if s.strip() == '$$$$':
                k=0; coord=[]; elm=[]; bonds=[]; bondmulti=[]; molatm=[]    
    if not done:
        molatm.append(elm); molatm.append(coord) 
        molatm.append(bonds); molatm.append(bondmulti)            
        moldat.append([title,comment,resnam,molatm])                
    f.close()

    return moldat
    
def WriteMolFile(molfile,molobj,resnam='',title='',comment=''):
    """
    
    :param str molfile: filename
    :param obj molobj: mol object of fu
    """
    countblock='  0  0  0  0  0  0  0  0  1 V2000\n'
    atmblock='  0  0  0  0  0  0  0  0  0  0  0  0\n'
    bndblock='  0  0  0  0\n'
    countsdf='  0  0  0  0  0  0  0  0  0'
    atmsdf='  0  0  0  0  0'
    bndsdf='  0  0  0'
    # .mol or .sdf
    head,tail=os.path.split(molfile)
    base,ext=os.path.splitext(tail)
    if ext == '.sdf':
        countblock=countsdf; atmblock=atmsdf; bndblock=bndsdf
    ff10='%10.4f'; fi3='%3d'
    #
    if len(title) <= 0: tit=molobj.name
    text=tit+'\n'
    text=text+comment+'\n'
    text=text+resnam+'\n'
    natoms=len(molobj.atm)
    coord=''; bonds=''; nbonds=0
    for i in range(natoms):
        atom=molobj.atm[i]; elm=atom.elm
        elm=elm.lstrip(); elm=elm+'   '; elm=elm[:2]
        coord=coord+ff10 % atom.cc[0]+ff10 % atom.cc[1]+ff10 %atom.cc[2]+' '+elm+atmblock
        jj=-1
        for j in atom.conect:
            jj += 1
            if j < i: 
                m=1
                try: m=atom.bndmulti[jj] 
                except: pass
                si=fi3 % (i+1); sj=fi3 % (j+1); sm=fi3 % m
                bonds=bonds+si+sj+sm+bndblock
                nbonds += 1     
    text=text+fi3 % natoms
    text=text+fi3 % nbonds
    text=text+countblock
    text=text+coord
    text=text+bonds    
    text=text+' M  END\n'
    #
    f=open(molfile,'w')
    f.write(text)
    f.close()
            
def WriteFrameFile(molobj,frmfile,resnam='',title='',comment=''):
    """Write frame file
    
    :param str frmfile: filename
    :param obj molobj: mol object of fu
    """
    #head,tail=os.path.split(frmfile)
    #base,ext=os.path.splitext(tail)
    fi3='%03d'; fi4='%4d'; fi5='%5d'; fi6='%6d'
    #
    molnam=molobj.name; natm=len(molobj.atm)
    # check atomnam
    namlst=[]; dupdic={}
    for i in xrange(natm):
        atmnam=molobj.atm[i].atmnam
        if atmnam in namlst: 
            if not dupdic.has_key(atmnam): dupdic[atmnam]=[]
            dupdic[atmnam].append(i+1)
        namlst.append(atmnam)
    if len(dupdic) > 0:
        mess='Duplicated atom names. Unable to contine. dupnam='+str(dupdic)        
        lib.MessageBoxOK(mess,'rwfile.WriteFrameFaile')
        return
    condic={}
    for i in xrange(natm):
        atom=molobj.atm[i]; elm=atom.elm
        if elm == 'XX': continue
        if not condic.has_key(i): condic[i]=[]
        for j in atom.conect: condic[i].append(j)
    natm=len(condic)
    if resnam == '': resnam=molnam[:3].upper()
    text='RESIDUE   '+resnam+' '+fi6 % natm+'\n'
    # heavy atoms
    for i in xrange(len(molobj.atm)):
        atom=molobj.atm[i]; atmnam=atom.atmnam
        if atom.elm == ' H': continue
        contxt=''
        conlst=condic[i]; nb=len(conlst)
        for j in conlst: contxt=contxt+' '+molobj.atm[j].atmnam
        text=text+'CONECT'+5*' '+atmnam+' '+fi4 % nb+contxt[1:]+'\n'
    # hydrogens
    for i in xrange(len(molobj.atm)):
        atom=molobj.atm[i]; atmnam=atom.atmnam
        if atom.elm != ' H': continue
        contxt=''
        conlst=condic[i]; nb=len(conlst)
        for j in conlst: contxt=contxt+' '+molobj.atm[j].atmnam
        text=text+'CONECT'+5*' '+atmnam+fi4 % nb+contxt[1:]+'\n'
   
    text=text+'END\n'
    text=text+'HETNAM'+5*' '+molnam
    #
    f=open(frmfile,'w')
    f.write(text)
    f.close()
            
def ReadXYZAtom(xyzfile):
    # read xyz coordinates
    # the first line : title
    # the second line: a blank line
    # the third line and after: xyz data in FMOXYZ format
    # label,elm or atomic number,x,y,z
    # a blank line terminates
    #"BOND"
    # i,j,k: i:i-th atom, j:j-th atom, k:1 single, 2:double,3:triple,4:aromatic bond
    # a blank lineterminates
    #"RESFRG"
    #atmnam,atmnmb,resnam,resnmb,resnmb,chainnam,charge,frgnam,frgchg,baa 
    # a blank line terminates
    xyzatm=[]; bond=[]; resfrg=[]
    try:
        fxyz=open(xyzfile)
    except IOError:
        print 'Error(ReadXYZAtom): File not found. file name='+xyzfile
        #lib.MessageBoxOK(mess,"")
        return xyzatm,bond,resfrg
    else:        
        natm=0; found=False; kount=0
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            s=s.strip()
            if s[0:1] == '#': continue
            if not found and len(s) == 0:
                found=True; continue # skip title
            if not found: continue
            if found and len(s) == 0: break
            tmp=[]
            s=s.replace(',',' ')
            item=s.split() # label,elm,x,y,z
            label=item[0]; natm +=1
            if len(item) >= 5:
                celm=1; cx=2; cy=3; cz=4 
            else: 
                celm=0; cx=1; cy=2; cz=3 
            try:
                elm=item[celm].strip()
                pd=elm.find('.')
                if pd >= 0: elm=elm[:pd]
                if elm.isdigit():
                    elm=const.ElmSbl[int(elm)]
                else:
                    if len(elm) == 1: elm=' '+elm
                elm=elm[0:2].upper()
            except:
                print 'error(ReadXYZAtom): wrong element data. data= '+s
                #lib.MessageBoxOK(mess,"")
                return xyzatm,bond,resfrg
            try:
                x=float(item[cx])
                y=float(item[cy])
                z=float(item[cz])
                #natm += 1
            except:
                print 'error(ReadXYZAtom): wrong coordinate data. data= '+s
                #lib.MessageBoxOK(mess,"")
                return xyzatm,bond,resfrg
            tmp.append('HETATM')
            tmp.append(natm) # atmnmb
            tmp.append('    ') # atmnam
            tmp.append(' ') # alt
            tmp.append('   ') # resnam
            tmp.append(' ') # chain
            tmp.append(0) # resnmb
            tmp.append([x,y,z]) # coord
            tmp.append(0.0) # focc
            tmp.append(0.0) # fbfc
            tmp.append(elm) # elm
            tmp.append(0.0) # chg
            #tmp.append(elm); tmp.append(x); tmp.append(y); tmp.append(z)
            xyzatm.append(tmp)
        # is "bond" data
        found=False
        fxyz.seek(0)
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            s=s.strip()
            if not found and s == "BOND":
                found=True; continue
            if not found: continue
            if found and len(s) <= 0: break
            tmp=[]
            s=s.replace(',',' '); item=s.split()
            try:
                i=int(item[0]); j=int(item[1]); k=int(item[2])
            except:
                print 'Error(ReadXYZAtom): Wrong bond data. data= '+s
                print 'neglected.'
                #lib.MessageBoxOK(mess,"")
                #return xyzatm,bond,resfrg
            tmp.append(i-1); tmp.append(j-1); tmp.append(k)
            bond.append(tmp)
        # is "sequence" data
        fxyz.seek(0)
        found=False
        ndat=0
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            s=s.strip(); s=s.replace(',',' ')
            if not found and s == "FRGMNT":
                found=True; continue
            if not found: continue
            if found and len(s) <= 0: break
            tmp=[]
            #item=s.split()
            item=lib.GetStringBetweenQuotation(s)
            if len(item) != 12: #9:
                print 'warning(ReadXYZAtom): Wrong RESFRG data. data= '+s
                print 'neglected.'
                #lib.MessageBoxOK(mess,"")
                #return xyzmol,bond,resfrg
            #for i in item:
            ndat += 1
            resfrg.append(item)
        fxyz.close()
    if natm <= 0:
        print 'number of atoms=0. format may be wrong.'
        #lib.MessageBoxOK(mess,"")
        return xyzatm,bond,resfrg
    if found and (ndat != natm):
        print 'warning:(ReadXYZAtom): Numbers of RESFRG and Atoms do not match. ndat='+str(ndat)+', natm='+str(natm)+'.'
        print 'RESFRG data are neglected.'
        #wx.MessageBox(mess,"")
        #return xyzmol,bond,[]
    return xyzatm,bond,resfrg

def ReadXYZsMol(xyzsfile):
    """ Read xyzs coordinate file.
    
    :param str xyzfile: file name
    :return: xyzmol - xyzmol data (lst)
    :return: bond - connect data (lst) (optional)
    :return: resfrg - fragment data (lst) (optional)
    :seealso: molec.Molecule.SetXYZAtoms() for xyzmol list data
    :note: See comments in the source program for the file format.
    """
    # the file format:
    # the first line : title
    # the second line: a blank line
    # the third line and after: xyz data in FMOXYZ format
    # label,elm or atomic number,x,y,z
    # a blank line terminates
    #"BOND"
    # i,j,k: i:i-th atom, j:j-th atom, k:1 single, 2:double,3:triple,4:aromatic bond
    # a blank lineterminates
    #"RESFRG"
    #atmnam,atmnmb,resnam,resnmb,resnmb,chainnam,charge,frgnam,frgchg,baa 
    # a blank line terminates
    
    xyzmollst=[]; xyzmol=[] #; bond=[]; resfrg=[]
    try:
        fxyz=open(xyzsfile)
    except IOError:
        mess='Error(ReadXYZsMol): File not found. file name='+xyzsfile
        lib.MessageBoxOK(mess,"")
        return xyzmollst #,[],[]
    else:        
        natm=0; found=False; kount=0
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            if s[0:1] == '#': continue
            s=s.strip()
            if not found and len(s) == 0:
                found=True; continue # skip title
            if not found: continue
            if found and len(s) == 0:
                found=False; kount=0; natm=0
                xyzmollst.append(xyzmol); xyzmol=[] 
                continue #break
            tmp=[]
            s=s.replace(',',' ')
            item=s.split() # label,elm,x,y,z
            label=item[0]
            if len(item) >= 5:
                celm=1; cx=2; cy=3; cz=4 
            else: 
                celm=0; cx=1; cy=2; cz=3 
            try:
                elm=item[celm].strip()
                pd=elm.find('.')
                if pd >= 0: elm=elm[:pd]
                if elm.isdigit():
                    elm=const.ElmSbl[int(elm)]
                else:
                    if len(elm) == 1: elm=' '+elm
                elm=elm[0:2].upper()
            except:
                mess='Error(ReadXYZsMol): Wrong elment data. data= '+s
                lib.MessageBoxOK(mess,"")
                return xyzmollst
            try:
                x=float(item[cx])
                y=float(item[cy])
                z=float(item[cz])
                natm += 1
            except:
                mess='Error(ReadXYZsMol): Wrong coordinate data. data= '+s
                lib.MessageBoxOK(mess,"")
                return xyzmollst
            tmp.append(elm); tmp.append(x); tmp.append(y); tmp.append(z)
            xyzmol.append(tmp)
        
    return xyzmollst
        
def ReadXYZMol(xyzfile):
    """ Read xyz coordinate file.
    
    :param str xyzfile: file name
    :return: xyzmol - xyzmol data (lst)
    :return: bond - connect data (lst) (optional)
    :return: resfrg - fragment data (lst) (optional)
    :seealso: molec.Molecule.SetXYZAtoms() for xyzmol list data
    :note: See comments in the source program for the file format.
    """
    # the file format:
    # the first line : title
    # the second line: a blank line
    # the third line and after: xyz data in FMOXYZ format
    # label,elm or atomic number,x,y,z
    # a blank line terminates
    #"BOND"
    # i,j,k: i:i-th atom, j:j-th atom, k:1 single, 2:double,3:triple,4:aromatic bond
    # a blank lineterminates
    #"RESFRG"
    #atmnam,atmnmb,resnam,resnmb,resnmb,chainnam,charge,frgnam,frgchg,baa 
    # a blank line terminates
    
    xyzmol=[]; bond=[]; resfrg=[]
    try:
        fxyz=open(xyzfile)
    except IOError:
        mess='Error(ReadXYZMol): File not found. file name='+xyzfile
        lib.MessageBoxOK(mess,"")
        return [],[],[]
    else:        
        natm=0; found=False; kount=0
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            if s[0:1] == '#': continue
            s=s.strip()
            if not found and len(s) == 0:
                found=True; continue # skip title
            if not found: continue
            if found and len(s) == 0: break
            tmp=[]
            s=s.replace(',',' ')
            item=s.split() # label,elm,x,y,z
            label=item[0]
            if len(item) >= 5:
                celm=1; cx=2; cy=3; cz=4 
            else: 
                celm=0; cx=1; cy=2; cz=3 
            try:
                elm=item[celm].strip()
                pd=elm.find('.')
                if pd >= 0: elm=elm[:pd]
                if elm.isdigit():
                    elm=const.ElmSbl[int(elm)]
                else:
                    if len(elm) == 1: elm=' '+elm
                elm=elm[0:2].upper()
            except:
                mess='Error(ReadXYZMol): Wrong elment data. data= '+s
                lib.MessageBoxOK(mess,"")
                return [],[],[]
            try:
                x=float(item[cx])
                y=float(item[cy])
                z=float(item[cz])
                natm += 1
            except:
                mess='Error(ReadXYZMol): Wrong coordinate data. data= '+s
                lib.MessageBoxOK(mess,"")
                return [],[],[]
            tmp.append(elm); tmp.append(x); tmp.append(y); tmp.append(z)
            xyzmol.append(tmp)
        # is "bond" data
        found=False
        fxyz.seek(0)
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            s=s.strip()
            if not found and s == "BOND":
                found=True; continue
            if not found: continue
            if found and len(s) <= 0: break
            tmp=[]
            s=s.replace(',',' '); item=s.split()
            try:
                i=int(item[0]); j=int(item[1]); k=int(item[2])
            except:
                mess='Error(ReadXYZMol): Wrong bond data. data= '+s
                lib.MessageBoxOK(mess,"")
                return [],[],[]
            tmp.append(i-1); tmp.append(j-1); tmp.append(k)
            bond.append(tmp)      
        # is "sequence" data
        fxyz.seek(0)
        found=False
        ndat=0
        for s in fxyz.readlines():
            s=s.replace('\r',''); s=s.replace('\n','') 
            s=s.strip(); s=s.replace(',',' ')
            if not found and s == "FRGMNT":
                found=True; continue
            if not found: continue
            if found and len(s) <= 0: break
            tmp=[]
            #item=s.split()
            item=lib.GetStringBetweenQuotation(s)
            if len(item) != 10: #12
                mess='Error(ReadXYZMol): Wrong RESFRG data. data= '+s
                lib.MessageBoxOK(mess,"")
                return xyzmol,bond,[]
            #for i in item:
            ndat += 1
            resfrg.append(item)
        if found and (ndat != natm):
            mess='Error(ReadXYZMol): Numbers of RESFRG and Atoms do not match. ndat='+str(ndat)+', natm='+str(natm)+'.'
            lib.MessageBoxOK(mess,"")
            return xyzmol,bond,[]
        fxyz.close()
    if natm <= 0:
        mess='Number of atoms=0. Format may be different.'
        lib.MessageBoxOK(mess,"")   
    return xyzmol,bond,resfrg

def ReadFMOCTCharge(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0=' Charge transfer for each fragment:'
    com1=''
    com2='  IFG QFG  DeltaQ' #     and its contributions from JFG, Q(JFG->IFG).
    com3=' ----------'
    data='    1  1  -0.1573 =    2-> -0.1126   32-> -0.0353   33-> -0.0066    3-> -0.0013'    
    newl='\n'
    ctchg=[]; tmpchg=[]
    err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        found0=False; found2=False; found3=False
        for s in fmo.readlines():
            if not found3:
                if s.startswith(com0,0,35): # com0 is found
                    found0=True; continue
                if found0 and s.startswith(com2,0,17): # com1 is found
                    found2=True; continue
                if found2 and s.startswith(com3,0,11): # com3 is found
                    found3=True; continue
            else:
                if s == newl: break
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                tmp=[]
                for c in item: tmp.append(c)
                tmpchg.append(tmp)
        fmo.close()

        for i in range(len(tmpchg)):
            tmp=[]
            idq=float(tmpchg[i][2]); tmp.append(idq)
            for j in range(4,len(tmpchg[i]),2):
                s=tmpchg[i][j]; pos=s.find('-'); s=s[0:pos]
                jnmb=int(s); tmp.append(jnmb)
                jdq=float(tmpchg[i][j+1]); tmp.append(jdq)
            ctchg.append(tmp)    

    return err,version,ctchg

def ReadFMOFragStatics(filename):
    frgstatlist=[]
    "not completed yet"
    return frgstatlist

def ReadFMOPIEDA(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0=' Two-body FMO properties.' # [0:25]
    com1='    I    J DL  Z    R' # [0:21]#   Q(I->J)  EIJ-EI-EJ dDIJ*VIJ    total     Ees      Eex    Ect+mix
    com2=' --------------------' #
    piedadata='    2    1 N1  0   0.00' # -0.1126 -9335.417    1.411 -9334.006 -9144.424 -118.243  -71.340'
    piedata=  '    2    1 N1  0   0.00' # -0.1126   -585.607150283 -14.87692145  0.00224777    1.411
    newl='\n'
    pieda=[]; eof=False; err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        found0=False; found1=False; found2=False
        for s in fmo.readlines():
            if not found2:
                if s.startswith(com0,0,25): # com0 is found
                    found0=True; continue
                if found0 and s.startswith(com1,0,21): # com1 is found
                    found1=True; continue
                if found0 and found1 and s.startswith(com2,0,21): # com2 is found
                    found2=True; continue
            else:
                if s == newl: break
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                tmp=[]
                for c in item: tmp.append(c)
                pieda.append(tmp)
        fmo.close()
     
        for i in range(len(pieda)):
            for j in range(len(pieda[i])):
                if j == 0 or j== 1 or j == 3: pieda[i][j]=int(pieda[i][j])
                elif j == 2: continue
                elif j > 3:  pieda[i][j]=float(pieda[i][j])

    return err,version,pieda

def ReadFMOInput(filename):
    err=0; nfrag=0; icharg=[]; frgnam=[]; indatx=[]; bdabaa=[]
    try:
        fmo=open(filename)
    except IOError:
        err=1 # i/o error
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        return err,nfrag,icharg,frgnam,indatx,bdabaa
    else:
        # read nfrag
        for s in fmo.readlines():
            s=s.strip(); s=s.lower()
            if s[0:5] == 'nfrag':
                ns=s.find('=')
                if ns < 0:
                    err=2 # nfrag not found
                    return err,nfrag,icharg,frgnam,indatx,bdabaa
                else:
                    nfrag=int(s[ns+1:])
                    break
        # icharg
        fmo.seek(0)
        icharg=[]; nchg=0; found=False
        for s in fmo.readlines():
            s=s.strip(); s=s.lower()
            if not found:
                if s[0:9] == 'icharg(1)':
                    ns=s.find('=')
                    if ns < 0: continue
                    found=True
                    s=s[ns+1:]
                    s=s.replace(',',' '); tmp=s.split()
                    for i in tmp:
                        nchg += 1; icharg.append(int(i))         
            else: 
                s=s.replace(',',' ')
                tmp=s.split()
                for i in tmp:                    
                    nchg += 1; icharg.append(int(i))
            if nchg >= nfrag: break
        if nchg != nfrag:
            err=3 # err in icharg
            return err,nfrag,icharg,frgnam,indatx,bdabaa                    
        # read frgnam
        fmo.seek(0)
        frgnam=[]; nnam=0; found=False
        for s in fmo.readlines():
            s=s.strip(); ss=s.lower()
            if not found:
                if ss[0:9] == 'frgnam(1)':
                    ns=s.find('=')
                    if ns < 0: continue
                    found=True
                    s=s[ns+1:]; s=s.replace(',',' ')
                    tmp=s.split() 
                    nnam=len(tmp)
                    frgnam=frgnam+tmp
            else:
                s=s.replace(',',' ')
                tmp=s.split()                    
                nnam += len(tmp); frgnam=frgnam+tmp
            if nnam >= nfrag: break
        if nnam != nfrag:
            err=4 # error in frgnam
            return err,nfrag,icharg,frgnam,indatx,bdabaa
        # read indat 
        fmo.seek(0)
        found=False
        indat=[]; frgatm=[]; nfrg=0; natm=0
        for s in fmo.readlines():
            s=s.strip(); s=s.lower()
            if not found:
                if s[0:8] == 'indat(1)':
                    ns=s.find('=')
                    if ns < 0: continue
                    s=s[ns+1:]; fmt=int(s)
                    if fmt == 0: found=True
            else:
                #if s[0:5] == ' $end': break
                s=s.replace(',',' ')
                tmp=s.split()
                for i in tmp:
                    if i == '0':
                        nfrg += 1; natm += len(frgatm)
                        indat.append(frgatm)
                        frgatm=[]
                    else:
                        frgatm.append(int(i))
            if nfrg >= nfrag: break
        if nfrg != nfrag:
            err=5 # error in indat
            return err,nfrag,icharg,frgnam,indatx,bdabaa
        for i in range(len(indat)):
            tmp=lib.ExpandIntData(indat[i])
            indatx.append(tmp)
        # bda, baa 
        fmo.seek(0)
        bdabaa=[]; nbda=0
        found=False
        for s in fmo.readlines():
            s=s.lower()
            if not found:
                if s[0:8] == ' $fmobnd':
                    found=True; continue
            else:
                if s[0:5] == ' $end': break
                tmp=s.split()
                i=int(tmp[0]); j=int(tmp[1])
                if i < 0:
                    bda=i; nbda += 1
                else: baa=i
                if j < 0:
                    bda=j; nbda += 1
                else: baa=j
                bdabaa.append([-bda,baa])
        fmo.close()
     
        return err,nfrag,icharg,frgnam,indatx,bdabaa

def ReadFMOIterEnergy(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'  
    com0=' FMO iter' # 13,    0 fragment(s) converged, maxD 0.0000015091, maxE 0.0000027590'        
    data=' FMO iter 13,    0 fragment(s) converged, maxD 0.0000015091, maxE 0.0000027590'
    newl='\n'
    jter=[]; denergy=[]; ddensity=[]
    err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        for s in fmo.readlines():
            if s.startswith(com0,0,9):
                s=s.replace('=',' ')
                item=s.split()
                for i in range(len(item)):
                    item[i]=item[i].replace(',','')
                    item[i]=item[i].replace('*','')
                jter.append(int(item[2]))
                if len(item) <= 9: denergy.append(0.0)
                else: denergy.append(float(item[9]))
                ddensity.append(float(item[7]))

    return err,version,jter,denergy,ddensity

def ReadFMOKeyword(filename,keywrd,col1,col2,datcollst):
    # keywrd startswith  col1-col2
    # datcollst: list [[coli,colj,varnam,format],[...],,,,]
    # format: int, float, logical, strings
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    newl='\n'
    err=0; eof=False; valuedic={}  
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        loop=True
        for s in fmo.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')

            
            if s.startswith(keywrd,col1,col2): 
                mess="Failed to read keyword "+"'"+keywrd+"'"+' in file='+filename+'.\n'
                mess=mess+"Fu supports "+version+"."    
                for i in range(len(datcollst)):
                    scol=datcollst[i][0] # start column
                    ecol=datcollst[i][1] # end column
                    vnam=datcollst[i][2] # variable name
                    fmt=datcollst[i][3]  # format of the data
                    dat=s[scol:ecol] 
                    dat=dat.strip()
                    if fmt == 'integer':
                        try: dat=int(dat)
                        except:
                            lib.MessageBoxOK(mess,"")
                            dat=0; pass
                    if fmt == 'float':
                        try: dat=float(dat)
                        except:
                            lib.MessageBoxOK(mess,"")
                            dat=0.0; pass
                    if fmt == 'logical':
                        try: dat=True
                        except:
                            lib.MessageBoxOK(mess,"")
                            dat=False; pass
                    # set value
                    valuedic[vnam]=dat
                loop=False
            if not loop: break
        fmo.close()
    
    return err,version,valuedic

def ReadFMOMulliken(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0=' n-body Mulliken' [0:16] #  atomic charges Q(n)'
    com1=''
    com2='    IAT  IFG' #   Z       Q(1)        Q(2)        Q(3)'
    data='     1    1   7.0   -0.390572   -0.384470'
    
    newl='\n'
    mulchg=[]
    err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        found0=False; found1=False #; found2=False
        for s in fmo.readlines():
            if not found1:
                if s.startswith(com0,0,16): # com0 is found
                    found0=True; continue
                if found0 and s.startswith(com2,0,12): # com2 is found
                    found1=True; continue
            else:
                if s == newl: break
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                tmp=[]
                for c in item: tmp.append(c)
                mulchg.append(tmp)
        fmo.close()
     
        for i in range(len(mulchg)):
            for j in range(len(mulchg[i])):
                if j <= 1: mulchg[i][j]=int(mulchg[i][j])
                else: mulchg[i][j]=float(mulchg[i][j])

    return err,version,mulchg

def ReadFMOOneBody(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0=' One-body FMO properties.' # [0:25]
    com1=' =======================' # [0:24]
    com2=''
    com3='E           DX        DY        DZ' # [28:62]
    com3p='E"          DX        DY        DZ'
    onebodydata='    1(THR001  ,L1)   -230.508181420  35.96337  19.73485 -12.14250' #
    newl='\n'
    onebody=[]; eof=False; err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        found0=False; found1=False; found2=False
        for s in fmo.readlines():
            if not found2:
                if s.startswith(com0,0,25): # com0 is found
                    found0=True; continue
                if found0 and s.startswith(com1,0,24): # com1 is found
                    found1=True; continue
                if found0 and found1 and (s.startswith(com3,28,62) \
                            or s.startswith(com3p,28,62)): # com3 is found
                    found2=True; continue
            else:
                if s == newl: break
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                tmp=[]
                ns=item[0].find('('); nmb=int(item[0][:ns]) #; tmp.append(nmb-1)
                nam=item[0][ns+1:]; tmp.append(nam)
                layer=item[1][1:3]; tmp.append(layer)
                energy=float(item[2]); tmp.append(energy)
                for i in range(3,6):
                    dipi=float(item[i]); tmp.append(dipi)
                onebody.append(tmp)
        fmo.close()
    # onebody:[[1, 'THR001', 'L1', -230.50818142],..] 
    return err,version,onebody

def ReadFMOStatics(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    keywrd=[['*         GAMESS VERSION =',0,26,26,44,'gmsver','str'], #0:GAMESS version
            ['Version',0,8,8,11,'fmover','flt'], #1: FMO version
            ['Number of fragments:',0,21,21,26,'nfrg','int'], #2
            ['Number of layers:',0,18,18,26,'nlayer','int'], #3
            ['N-body FMO method:',0,20,20,26,'nbody','int'], #4
            ['SCFTYP=',0,7,7,15,'scftyp','str'],  #5 SCFTYP=RHF
            ['MPLEVL=',0,7,7,15,'mplevl','int'],  #6 MPLEVL=0
            ['DFTTYP=',0,7,7,15,'dfttyp','str'], #7 DFTTYP=NONE
            ['CITYP=',0,6,6,14,'cityp','str'], #8 CITYP=NONE
            ['CCTYP=',0,6,6,14,'cctyp','str'], #9 CCTYP=NONE
            ['TDDFT=',0,6,6,14,'tddft','str'], #10 TDDFT=NONE
            ['FMO method:',0,11,12,23,'disp','str'],
            ['There are',0,10,9,78,'ndim','man'], #13
            ['FMO iter',0,9,8,14,'niter','???'], # 14 FMO iter 17,  39 fragment(s) ...
            ['Total number of atoms:',0,23,22,44,'natm','int'], # 15
            ['Total number of electrons:',0,27,26,44,'nelec','int'], #16
            ['Total charge:',0,14,13,44,'tchg','int'], # 17
            ['Total spin multiplicity:',0,25,24,44,'tspin','int'], #18
            ['Total number of basis functions:',0,33,32,44,'nbas','int'], #19
            ['Total number of molecular orbitals:',0,36,35,44,'norb','int'], #20
            ['TOTAL WALL CLOCK TIME',0,23,22,34,'wctime','flt'], #23
            ['EXECUTION OF GAMESS',0,40,39,64,'date','str']] # 24
    # option dependent output
    totale=['TOTAL ENERGY =',0,14,14,32,'etotal','flt'] # no FMO job
    options=[['Total energy of the molecule: Euncorr(1)=',0,42,41,60,'escf(1)','flt'], # FMO1e
             ['Total energy of the molecule: Euncorr(2)=',0,42,41,60,'escf(2)','flt'], # FMO2e
             ['Total energy of the molecule: Edelta (1)=',0,42,41,60,'edelta(1)','flt'], # FMO1e
             ['Total energy of the molecule: Edelta (2)=',0,42,41,60,'edelta(2)','flt'], # FMO2e
             #['Total energy of the molecule: Eunco+D(1)=',0,42,41,60,'escfd(1)','flt'], #rhf/dft-D2/D3
             #['Total energy of the molecule: Eunco+D(2)=',0,42,41,60,'escfd(2)','flt'], # rfh/dft-D2/D3
             ['Total energy of the molecule: Edisp  (1)=',0,42,41,60,'edisp(1)','flt'], #rhf/dft-D2/D3
             ['Total energy of the molecule: Edisp  (2)=',0,42,41,60,'edisp(2)','flt'], # rfh/dft-D2/D3                 
             ['Atomic charges will be printed',0,30,30,31,'mulchg','log'], #11  Mulliken charge
             ['(PIEDA) will be done (PL only)',0,30,30,31,'pieda','log'] ] # pieda

    newl='\n'
    err=0; eof=False; prpdic={}  
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        key=0; nbody=2; niter=0
        keyw=keywrd[0][0]; c1=keywrd[0][1]; c2=keywrd[0][2]; c3=keywrd[0][3]
        c4=keywrd[0][4]; name=keywrd[0][5]; fmt=keywrd[0][6]
        keyc=keywrd[14][0]; d1=keywrd[14][1]; d2=keywrd[14][2]; d3=keywrd[14][3]
        d4=keywrd[14][4]; namec=keywrd[14][5]; fmtc=keywrd[14][6]

        for s in fmo.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s.find('\t') >= 0:
                print 'tab found',s.count('\t')
                s=s.replace('\t','        ')
            s=s.lstrip()
            #print 's',s
            #print  's in read',s
            #cs=c2-c1+1
            if s.startswith(keyw,c1,c2): #0,cs): #c1,c2): # com0 is found
                #print 'key,keyw',key,keyw
                #
                mess="Failed to read keyword "+"'"+keyw+"'"+' in file='+filename+'.\n'
                mess=mess+"Fu supports "+version+"."
                #
                #c30=c3-c1; c40=c4-c1
                dat=s[c3:c4]; dat=dat.strip()
                #dat=s[c30:c40]; dat=dat.strip()
        
                if fmt == 'int':
                    try: dat=int(dat)
                    except:
                        dlg=lib.MessageBoxOK(mess,"")
                        dat=0; pass
                if fmt == 'flt':
                    try: dat=float(dat)
                    except:
                        lib.MessageBoxOK(mess,"")
                        dat=0.0; pass
                if fmt == 'log':
                    try: dat=True
                    except:
                        lib.MessageBoxOK(mess,"")
                        dat=False; pass
                if fmt == 'man':
                    # dimer info
                    try:
                        item=dat.split()
                        dat=[int(item[0]),int(item[3])]
                    except:    
                        lib.MessageBoxOK(mess,"")
                        dat=[]; pass      
                if name == 'disp':
                    if dat.find('/D') >=0 : dat=True
                    else: dat=False

                if name == 'nbody':
                    #print 's at nbody',s
                    try:
                        nbody=int(dat)
                        #if nbody == 1: 
                        #    del keywrd[11]; del keywrd[11]; del keywrd[11]
                        #    keywrd[19]=TotalE #[19]=TotalE
                    except:
                        lib.MessageBoxOK(mess,"")
                        nbody=1; pass

                prpdic[name]=dat
                key += 1
                if key >= len(keywrd): break
                # FMO iter
                else:
                    keyw=keywrd[key][0]; c1=keywrd[key][1]; c2=keywrd[key][2]
                    c3=keywrd[key][3]; c4=keywrd[key][4]; name=keywrd[key][5]
                    fmt=keywrd[key][6]
            #ds=d2-d1
            if s.startswith(keyc,d1,d2):
                try:
                    #dat=s[d3-d1:d4-d1]
                    dat=s[d3:d4]
                    dat=dat.split("."); dat=dat[0].split(",")
                    dat=int(dat[0]) # 1.1, 2.1,...
                except:
                    lib.MessageBoxOK(mess,"")
                    dat=0
                prpdic[namec]=dat
        # option dependent output
        fmo.seek(0)
        if not prpdic.has_key('fmover') or prpdic['nbody'] == 1: # this is not a FMO job
            keyw=totale[0]; c1=totale[1]; c2=totale[2]
            c3=totale[3]; c4=totale[4]; name=totale[5]; fmt=totale[6]
            for s in fmo.readlines():
                s=s.replace('\r',''); s=s.replace('\n',''); s=s.lstrip()
                if s.startswith(keyw,c1,c2): #0,cs): #c1,c2): # com0 is found
                    dat=s[c3:c4]; dat=dat.strip()
                    try:
                        prpdic[name]=float(dat)
                    except:
                        print 'dat',dat
                        print 'Error in ReadFMOStatic: total energy is set 0.0'
                        prpdic[name]=0.0
        else:
            for s in fmo.readlines():
                s=s.replace('\r',''); s=s.replace('\n',''); s=s.lstrip()
                for i in range(len(options)):
                    keyw=options[i][0]; c1=options[i][1]; c2=options[i][2]
                    c3=options[i][3]; c4=options[i][4]; name=options[i][5]
                    fmt=options[i][6]
                    if s.startswith(keyw,c1,c2): #0,cs): #c1,c2): # com0 is found
                        dat=s[c3:c4]; dat=dat.strip()
                        if fmt == 'flt': prpdic[name]=float(dat)
                        if fmt == 'log': prpdic[name]=True        

        fmo.close()
    #print 'prpdic',prpdic
    try:
        if prpdic['nfrg'] > 1: prpdic['pieda']=True
    except: pass
    return err,version,prpdic

def ReadFMOXYZ(filename):
    # geometry data in input file
    err=0; geom=[]
    try:
        fmo=open(filename)
    except IOError:
        err=1 # i/o error
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
    else:
        # geom        
        found=False
        for s in fmo.readlines():
            #s=s.lower()
            if not found:
                if s[0:8] == ' $fmoxyz':
                    found=True; continue
            else:
                if s[0:5] == ' $end': break
                tmp=s.split()
                # tmp[0],[1],[2],[3],[4]: label, elm,x,y,z
                tmp[1]=tmp[1].upper()
                if len(tmp[1]) <= 1: tmp[1]=' '+tmp[1]
                tmp[2]=float(tmp[2]); tmp[3]=float(tmp[3]); tmp[4]=float(tmp[4])
                geom.append(tmp)
        
        return err,geom

def ReadFrgDistance(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0=' Two-body FMO properties.' # [0:25]
    com1='    I    J DL  Z    R' # [0:21]#   Q(I->J)  EIJ-EI-EJ dDIJ*VIJ    total     Ees      Eex    Ect+mix
    com2=' --------------------' #
    #piedadata or piedata='    2    1 N1  0   0.00' # 4-th is the distance
    newl='\n'
    frgdist=[]; dist=[]; eof=False; err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1; return frgdist
    #else:
    found0=False; found1=False; found2=False
    for s in fmo.readlines():
        if not found2:
            if s.startswith(com0,0,25): # com0 is found
                found0=True; continue
            if found0 and s.startswith(com1,0,21): # com1 is found
                found1=True; continue
            if found0 and found1 and s.startswith(com2,0,21): # com2 is found
                found2=True; continue
        else:
            if s == newl: break
            s=s.replace('\r',''); s=s.replace('\n','')
            item=s.split()
            if len(item) == 0: break
            tmp=[]
            tmp.append(int(item[0])); tmp.append(int(item[1]))
            tmp.append(float(item[4]))
            dist.append(tmp)
    fmo.close()
    # frgdist:[[[0,dist00],[1,dist01],...],[[0,dist10],[1,dist11],..],...]        
    if len(dist) > 0:
        nfrg=dist[len(dist)-1][0]
        for i in range(nfrg):
            tmp=[]
            for j in range(nfrg): tmp.append([i+1,0.0])
            frgdist.append(tmp)
        for i,j,d in dist:
            frgdist[j-1][i-1][0]=i; frgdist[j-1][i-1][1]=d
            frgdist[i-1][j-1][0]=j; frgdist[i-1][j-1][1]=d
    
    return err,version,frgdist

def ReadFrgIterEnergy(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)' 
    com0=' Iter=' #  1 iFrag=   37 EFMO=  -528.442128759, DD= 0.851726007, '
    data=' Iter=  1 iFrag=   37 EFMO=  -528.442128759, DD= 0.851726007, DE=************'    
    newl='\n'
    jter=[]; efmo=[]; deld=[]; dele=[]
    frgdic={}
    err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        nfrg=0
        for s in fmo.readlines():
            if s.startswith(com0,0,6):
                s=s.replace('=',' ')
                item=s.split()
                for i in range(len(item)):
                    item[i]=item[i].replace(',','')
                    item[i]=item[i].replace('*','')
                if len(item) <= 6: continue
                ifrg=int(item[3])
                if ifrg > nfrg: nfrg=ifrg
                it=item[1]
                ef=float(item[5])
                dd=float(item[7])
                if item[9] == '': de=0.0
                else: de=float(item[9])
                if not frgdic.has_key(ifrg): frgdic[ifrg]=[]
                tmp=[]
                tmp.append(it)
                tmp.append(ef)
                tmp.append(dd)
                tmp.append(de)
                frgdic[ifrg].append(tmp)
    if len(frgdic) > 0:
        for i in range(nfrg):
            tmp=frgdic[i+1]
            itdat=[]; efdat=[]; dedat=[]; dddat=[]
            for it,ef,dd,de in tmp:
                itdat.append(it)
                efdat.append(ef)
                dddat.append(dd)
                dedat.append(de)
            jter.append(itdat)
            efmo.append(efdat)
            deld.append(dddat)
            dele.append(dedat)
    
    return err,version,jter,efmo,dele,deld

def ReadGMSMulliken(filename):
    version=const.GAMESSVER #'FMO Version 4.3 in GAMESS VERSION 1 MAY 2013 (R1)'
    com0='TOTAL MULLIKEN AND LOWDIN ATOMIC POPULATIONS' # [10:54]
    com1='ATOM         MULL.POP.' # [7:29]   CHARGE          LOW.POP.     CHARGE
    data='    1 C             5.682730    0.317270         5.772870    0.227130'
    
    newl='\n'
    mulchg=[]
    err=0
    try:
        fmo=open(filename)
    except IOError:
        lib.MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        found0=False; found1=False #; found2=False
        for s in fmo.readlines():
            if not found1:
                if s.startswith(com0,10,54): # com0 is found
                    found0=True; continue
                if found0 and s.startswith(com1,7,29): # com1 is found
                    found1=True; continue
            else:
                if s == newl: break
                s=s.replace('\r',''); s=s.replace('\n','')
                item=s.split()
                if len(item) == 0: break
                tmp=[]
                item[0]=int(item[0]); tmp.append(item[0])
                if len(item[1]) <= 1: item[1]=' '+item[1]
                tmp.append(item[1])
                item[2]=float(item[2]); tmp.append(item[2])
                item[3]=float(item[3]); tmp.append(item[3])
                mulchg.append(tmp)
        fmo.close()
 
    return err,version,mulchg

def FindFragmentVarName(namvardic,s,find):                
    #namvardic={'$FMOXYZ':'$FMOXYZ','FRGNAM(1)=':'FRGNAM','INDAT(1)=':'INDAT',
    #           'ICHARG(1)=':'ICHARG','$FMOBND':'$FMOBND',
    #           'LAYER(1)=':'LAYER','MULT(1)=':'MULT','SCFTYP(1)=':'SCFTYP','DFTTYP(1)=':'DFTTYP',
    #           'MPLEVL(1)=':'MPLEVL','CITYP(1)=':'CITYP','CCTYP(1)=':'CCTYP','TDTYP(1)=':'TDTYP',
    #           'DOMAIN(1)=':'DOMAIN'}
    found=0
    namvar=''; datlst=[]
    for nam,val in namvardic.iteritems():
        ns=s.find(nam)
        if ns >= 0:
            found=1
            namvar=val
            if nam[:1] != '$':
                s=s.replace(nam,'',1)
                s=s.replace('$END','')
                s=s.strip()
                #datlst=lib.SplitStringData(s)
                #while '' in datlst: datlst.remove('')
                datlst=lib.SplitStringAtSpacesOrCommas(s)
            break
        else: datlst=lib.SplitStringAtSpacesOrCommas(s)
    #
    if found == 0 and s[:1] == '$': found=-1
    if found == 0 and s.find('=') >= 0: found=-1
    #if s[:1] == '$': found=-1
    #if s.find('=') >= 0: found=-1
    
    # 
    return found,namvar,datlst
    
def ReadFMOInputFile(filename):
    """
    
    :return: coord - [[elm,x,y,z],...], elm(str),x(float),y(float),z(float)
    """
    namvardic={'$FMOXYZ':'$FMOXYZ','FRGNAM(1)=':'FRGNAM','INDAT(1)=':'INDAT',
               'ICHARG(1)=':'ICHARG','$FMOBND':'$FMOBND','$DATA':'$DATA','$FMOHYB':'$FMOHYB',
               'LAYER(1)=':'LAYER','MULT(1)=':'MULT','SCFTYP(1)=':'SCFTYP','DFTTYP(1)=':'DFTTYP',
               'MPLEVL(1)=':'MPLEVL','CITYP(1)=':'CITYP','CCTYP(1)=':'CCTYP','TDTYP(1)=':'TDTYP',
               'IACTAT(1)=':'IACTAT','RESNAM(1)=':'RESNAM','RESATM(1)=':'RESATM','ATMNAM(1)=':'ATMNAM'}
    # note: RESNAM and RESATM are supplied data by FU.
    # frgdic['RESNAM']: [resnam1(str),resnam2(str),...]
    # resatm['RESATM']: [i(ints),j(int),...,natm], i is the last atom in the first fragment
    #
    comstr='!'; namegrp=' $'; endstr=' $END'; com='COMMENT'; text='TEXT'
    #
    coord=[]; indat=[]; bdabaa=[]; frgnam=[]; tmpindat=[]
    frgdic={} # all fragment data except coordinate
    #
    if not os.path.exists(filename):
        return coord,frgdic
    #
    find=False; namvar=''; cont=False
    f=open(filename,'r')        
    for s in f.readlines():
        if s[:1] == '!': continue # skip comments
        s=s.rstrip()
        s=s.upper()
        s5=s[:5]; s2=s[:2]; s1=s[:1]
        ss=s[:]; ss=ss.lstrip()
        if ss[:3] == '---':
            find=False
            continue
        ### if s1 == comstr: continue
        if not find: # try to find namvar
            found,nam,datlst=FindFragmentVarName(namvardic,ss,find)
            #if found and nam[:1] == '$': 
            if found == 0:
                find=False; namvar=''
                continue
            elif found == 1:
                find=True; namvar=nam
                if not frgdic.has_key(namvar): frgdic[namvar]=[]
                if nam[:1] != '$': frgdic[namvar]=frgdic[namvar]+datlst
                continue
        #
        if find:
            found,nam,datlst=FindFragmentVarName(namvardic,ss,find)
            if found == -1:
                find=False; continue
            elif found == 1:
                find=True; namvar=nam
                if nam[:1] != '$':
                    if not frgdic.has_key(namvar): frgdic[namvar]=[]
                    frgdic[namvar]=frgdic[namvar]+datlst
                continue
            # found == 0
            if nam[:1] == '$': continue
            s=s.replace('$END','')
            #
            if namvar =='$FMOXYZ':
                #items=s.split(' ')
                items=lib.SplitStringAtSpaces(s)
                if len(items) < 5: continue
                label=items[0]
                elm=items[1]
                if elm.isdigit(): elm=const.ElmSbl[int(elm)]
                x=float(items[2].strip())
                y=float(items[3].strip())
                z=float(items[4].strip())
                coord.append([elm,x,y,z])
            elif namvar =='$FMOBND':
                dat=lib.SplitStringAtSpacesOrCommas(s)
                bdabaa.append([-int(dat[0]),int(dat[1])])
                datlst[0]=int(datlst[0]); datlst[1]=int(datlst[1])
                frgdic[namvar]=frgdic[namvar]+datlst
            elif namvar == 'INDAT':
                items=[]
                dat=lib.SplitStringAtSpacesOrCommas(s)
                for val in dat: items.append(int(val))
                tmpindat.append(items)
            elif namvar == '$FMOHYB' or namvar == '$DATA':
                frgdic[namvar]=frgdic[namvar]+[s.lstrip()]
            else:
                frgdic[namvar]=frgdic[namvar]+datlst                    
    f.close()
    # make indata(add list with non-zero end to the next list)
    dat=[]
    for lst in tmpindat:
        if len(lst) <= 0: continue
        if lst[-1] != 0: dat=dat+lst
        else:
            dat=dat+lst
            dat=lib.ExpandIntData(dat[:-1])
            indat.append(dat)
            dat=[]
    icharg=[]; layer=[]; iactat=[]
    try:
        if frgdic.has_key('ICHARG'):
            for val in frgdic['ICHARG']: icharg.append(int(val.strip()))
            frgdic['ICHARG']=icharg
        if frgdic.has_key('LAYER'):
            for val in frgdic['LAYER']: layer.append(int(val.strip()))
            frgdic['LAYER']=layer
        if frgdic.has_key('IACTAT'):
            for val in frgdic['IACTAT']: iactat.append(int(val.strip()))
            iactat=lib.ExpandIntData(iactat)
            for i in range(len(iactat)): iactat[i]=iactat[i]-1
            frgdic['IACTAT']=iactat

    except: 
        mess='Sorry, unable to read array type data in a line with other data.'
        lib.MessageBoxOK(mess,'rwfile:ReadFMOInput')
        #
    if frgdic.has_key('FRGNAM'): 
        frgnam=frgdic['FRGNAM']; del frgdic['FRGNAM']
    if frgdic.has_key('$FMOXYZ'): del frgdic['$FMOXYZ']
    if frgdic.has_key('INDAT'): del frgdic['INDAT']
    
    # Residue data in coments
    if frgdic.has_key('RESNAM'):
        resnam=[]
        for nam in frgdic['RESNAM']:
            nam=nam.replace('!','')
            nam=nam.lstrip()
            if nam == '': continue
            resnam.append(nam)
        frgdic['RESNAM']=resnam

    if frgdic.has_key('RESATM'):
        resatm=[]
        for val in frgdic['RESATM']:
            val=val.replace('!','')
            val=val.lstrip()
            if val == '': continue
            resatm.append(int(val))
        frgdic['RESATM']=resatm    

    if frgdic.has_key('ATMNAM'):
        atmnam=[]
        for val in frgdic['ATMNAM']:
            val=val.replace('"!','')
            val=val.replace('"','')
            val=val.lstrip()
            if val == '': continue
            atmnam.append(val)
        frgdic['ATMNAM']=atmnam  
    
    return coord,frgnam,indat,bdabaa,frgdic

def ReadCubeFile(filename): # ,property):
    # read density and mep cube file
    # format: a comment and a blank lines are assumed at the head of the file
    # ' $END' line is needed at the end of the file.
    bhtoan=const.PysCon['bh2an']
    #
    info=[]; atmcc=[]; natoms=-1
    if not os.path.exists(filename):
        mess='file: '+filename+ 'not found.'
        lib.MessageBoxOK(mess,"ReadCubeFile")              
        return [],-1,[]
    f=open(filename,'r')
    # title and property
    # skip a comment line
    s=f.readline()
    # skip a blank line
    s=f.readline()
    # natoms,xmin,ymin,zmin
    s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
    item=s.split()
    natoms=int(item[0])
    xmin=float(item[1])
    ymin=float(item[2])
    zmin=float(item[3])
    # nx,dx, the same data for y and z
    s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
    item=s.split(); nx=int(item[0]); dx=float(item[1])
    s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
    item=s.split(); ny=int(item[0]); dy=float(item[2])
    s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
    item=s.split(); nz=int(item[0]); dz=float(item[3])
    xmax=xmin+nx*dx; ymax=ymin+ny*dy; zmax=zmin+nz*dz
    center=[(xmax+xmin)/2.0,(ymax+ymin)/2.0,(zmax+zmin)/2.0]
    # atmcc, [[an, x,y, and z],...]
    for i in range(natoms):
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','')             
        item=s.split()
        atmcc.append([int(item[0]),float(item[2])*bhtoan,float(item[3])*bhtoan,
                      float(item[4])*bhtoan])
    vmin=1000000.0; vmax=-1000000.0
    for s in f.readlines():
        s=s.replace('\r',''); s=s.replace('\n',''); s=s.strip()
        if s == ' $END': break
        item=s.split()
        for val in item:
            try:
                if float(val) > vmax: vmax=float(val)
            except: pass
            try:
                if float(val) < vmin: vmin=float(val)
            except: pass
    f.close()
    #
    info.append(center)
    info.append(xmin); info.append(xmax); info.append(nx)
    info.append(ymin); info.append(ymax); info.append(ny)
    info.append(zmin); info.append(zmax); info.append(nz) 
    info.append(vmin); info.append(vmax)
    #
    return info,natoms,atmcc

def ReadContentsFile(contentsfile,retscript=False):
    """ Read contents file used in HtmlViewerWithIndex_Frm and Tutorial_Frm
    
    :param str contentsfile: filename
    :param bool retscript: True for return 'scriptdic' and 'demodic', False do not  
    :return: contentslst(lst),textdic(dic),htmldic(dic) and optionaly scriptdic(dic) and demodic(dic)
    """
    contentsdir=''
    def ToText(text):
        text=text[:-1] # remove the last "\n"
        if len(text) <= 0: return ''
        if text == 'text=': return ''
        nc=text.find('text=[')
        if nc < 0: return ''
        if nc >= 0: text=text[nc+6:]
        nc=text.rfind(']')
        if nc >= 0: text=text[:nc]
        return text
    
    def ReadTextFile(textfile):
        text=''    
        textfile=os.path.join(contentsdir,textfile)
        if not os.path.exists(textfile): return text
        f=open(textfile,'r')
        text=f.read()
        f.close()
        return text
         
    contentslst=[]; itemlst=[]; grplst=[]
    textdic={}; htmldic={}; scriptdic={}; demodic={}
    if not os.path.exists(contentsfile):
        mess='Not found contentsfile='+contentsfile
        lib.MessageBoxOK(mess,'lib.ReadContentsFile')
        if retscript:
            return contentslst,textdic,htmldic,scriptdic,demodic
        else: return contentslst,textdic,htmldic
    #
    contentsdir=lib.GetFileNameDir(contentsfile)
    #
    foundr=False; foundg=False; foundi=False; text=''; script=''
    f=open(contentsfile,'r') 
    for s in f.readlines():
        if s[:1] == '#': continue
        nc=s.find('#') 
        if nc >= 0: s=s[nc+1:]
        #print 's',s
        if s[:8] == 'ROOT END':
            foundr=False
            text=ToText(text)
            textdic['root']=text
            if rhtml != '': htmldic['root']=rhtml
            if textfile != '': textdic['root']=ReadTextFile(textfile)
            rhtml=''
            continue
        if s[:9] == 'GROUP END':
            foundg=False; grplst.append(itemlst) 
            contentslst.append(grplst); grplst=[]
            text=ToText(text)
            if text != '': textdic[grpnam]=text
            if ghtml != '': htmldic[grpnam]=ghtml
            if textfile != '': textdic[grpnam]=ReadTextFile(textfile)
            text=''; ghtml=''; textfile=''
            continue
        if s[:8] == 'ITEM END':
            text=ToText(text)
            textdic[itemnam]=text
            if script != '': scriptdic[itemnam]=script
            if demo != '': demodic[itemnam]=demo
            if html != '': htmldic[itemnam]=html
            if textfile != '': textdic[itemnam]=ReadTextFile(textfile)
            foundi=False; text=''; html=''; demo=''; textfile=''
            continue
        if s[:4] == 'ROOT':
            foundr=True; foundg=False; foundi=False
            text=''; script=''; demo=''; rhtml=''; textfile=''
            continue
        if s[:5] == 'GROUP':
            foundg=True; foundi=False; itemlst=[]
            grpnam=s[5:].strip()
            grplst.append(grpnam)
            text=''; script=''; demo=''; ghtml=''; textfile=''
            continue
        if s[:4] == 'ITEM':
            if foundg and not foundi:
                text=ToText(text)
                if text != '': textdic[grpnam]=text
                if textfile != '': textdic[grpnam]=ReadTextFile(textfile)
            foundi=True
            itemnam=s[4:].strip()
            text=''; script=''; demo=''; html=''
            itemlst.append(itemnam)
            continue
        if foundg and not foundi:
            text=text+s.strip()+'\n'
            if s[:9] == 'htmlfile=':
                varnam,ghtml=lib.SplitVariableAndValue(s)
            if s[:9] == 'textfile=':
                varnam,textfile=lib.SplitVariableAndValue(s)
            continue
        if foundi:
            s=s.strip()
            if s[:11] == 'scriptfile=':
                varnam,script=lib.SplitVariableAndValue(s)
            if s[:9] == 'demofile=':
                varnam,demo=lib.SplitVariableAndValue(s)
            if s[:9] == 'htmlfile=':
                varnam,html=lib.SplitVariableAndValue(s)
            if s[:9] == 'textfile=':
                varnam,textfile=lib.SplitVariableAndValue(s)
            else: text=text+s+'\n'
            continue
        if foundr:
            text=text+s.strip()+'\n'
            if s[:9] == 'htmlfile=':
                varnam,rhtml=lib.SplitVariableAndValue(s)
            if s[:9] == 'textfile=':
                varnam,textfile=lib.SplitVariableAndValue(s)
            continue
        
    f.close()
    #
    if retscript:
        return contentslst,textdic,htmldic,scriptdic,demodic
    else: return contentslst,textdic,htmldic

def ReadZMTFile(filename,type='GAUSSIAN'):
    """ Read symbolic Z-matrix 
    
    :param str filename: file name
    :return: title(str) - title
    :return: zelm(lst) - list of elements, [elm1(str),...]
    :return: zpnt(lst) - list of points, [[p1(int),p2(int),p3(int)],...]
    :return: zprm(lst) - list of geometrical params, [[length(float),angle(float),torsion(float)],..]
    :return szprm(slt) - list of symbolic params,[[length(str),angle(str),torsion(str)],..]
    """
    def ElmData(elm):
        elm=elm.strip()
        if len(elm) <= 0: elm='  '
        elif len(elm) == 1: 
            elm=' '+elm; elm=elm.upper()
        else: elm=elm[:2].upper()
        return elm
    def ErrorExit(mess):
        print 'Error in Z-matrix data: '+mess
        return mess,'',-1,-1,[],[]
    
    if not os.path.exists(filename):
        mess='not found file='+filename
        ErrorExit(mess)
    # Read symbolic Z-matrix data
    variable='VARIABLES:'; constant='CONSTANTS:'
    zpnt=[]; szprm=[]; zelm=[]; varvaldic={} #; zmtdic={}
    zvardic={}; zactivedic={}
    bndmulti=[]; atmnam=[]; resdat=[]; conect=[]; extdat=[]
    title=''; ielm=0
    nitems=[1,3,5,7]; foundext=False; foundend=False
    foundvar=False; foundconst=False
    #    
    f=open(filename,'r')
    i=0; nblk=0; iatm=-1
    for s in f.readlines():
        i += 1
        ss=s
        s=s.strip()
        ns=s.find('#')
        if ns >= 0: s=s[:ns].strip()
        ns=s.find('/')
        if ns >= 0: s=s[:ns].strip()
        if s == 'EXTDAT':
            #print 'found EXTDAT'
            foundext=True; foundvar=False; foundconst=False; continue
        if s.upper() == constant:
            foundconst=True; foundvar=False; foundext=False; continue
        if s.upper() == variable:
            foundvar=True; foundconst=False; foundext=False; continue       
        if foundext:
            nam=ss[:5]; ss=ss[5:]
            items=lib.SplitStringAtSpaces(ss) 
            res=items[0].strip()
            atmnam.append(nam); resdat.append(res)
            lst1=lib.StringToList(items[1].strip(),True)
            for j in range(len(lst1)): lst1[j] -= 1
            conect.append(lst1)
            lst2=lib.StringToList(items[2].strip(),True)
            bndmulti.append(lst2)
            if len(s) <= 0: 
                foundext=False; foundend=True
                #print 'found END'
        if len(s) <= 0:
            nblk += 1
            if nblk == 1: continue # end title
            #elif nblk >= 3: break # end of symbolic zmat
        if nblk <= 0:
            if i == 1: title=s # title
        elif nblk == 1 and not foundvar and not foundconst:
            if foundend: continue
            #if i == 3: # charge,spin
            #    items=lib.SplitStringAtSpaces(s)
            #    charge=int(items[0])
            #    if len(items) >= 2: spin=int(items[1])
            iatm += 1
            if i >= 3:
                pnt=[-1,-1,-1]; prm=['','','']
                items=lib.SplitStringAtSpaces(s)
                if len(items[0]) <= 0:
                    ErrorExit('No element of '+str(i)+'-th line')
                if i ==3 and len(items) == 2: ielm=1
                ###if i == 3 and len(items) >= nitems[0] +1: ielm=1
                elm=items[ielm]
                if i >= 4: 
                    if len(items) < nitems[1]+ielm: ErrorExit('Error in '+str(i)+'-th line')
                    pnt[0]=items[ielm+1]; prm[0]=items[ielm+2]
                if i >= 5: # second atom   
                    if len(items) < nitems[2]+ielm: ErrorExit('Error in '+str(i)+'-th line')
                    pnt[1]=items[ielm+3]; prm[1]=items[ielm+4]
                if i >= 6:
                    if len(items) < nitems[3]+ielm: ErrorExit('Error in '+str(i)+'-th line')
                    pnt[2]=items[ielm+5]; prm[2]=items[ielm+6]
                zelm.append(elm); zpnt.append(pnt); szprm.append(prm)
                for j in range(3):
                    if len(prm[j]) <= 0: continue
                    try: float(prm[j])
                    except:
                        varnam=str(iatm)+':'+str(j)
                        #zmtdic[varnam]=[prm[j],False]
                        zvardic[varnam]=prm[j]
        else: # read symbolic variable=value data
            if foundend: continue
            ns=s.find('=')
            if ns >= 0:
                var,value=lib.GetKeyAndValue(s)
                if foundvar: 
                    active=True; zactivedic[var]=True
                else: active=False
                varvaldic[var]=[value,active]
    f.close()
    # check element
    elmtxt=''
    for i in range(len(zelm)):
        try: zelm[i]=const.ElmSbl[int(zelm[i])]
        except: zelm[i]=ElmData(zelm[i])
        if not zelm[i] in const.ElmSbl: elmtxt=elmtxt+elm+','
    if len(elmtxt) > 0: elmtxt='Unknown element(s): '+elmtxt[:-1]+'\n'  
    # check point
    pnttxt=''
    for i in range(len(zpnt)):
        for j in range(len(zpnt[i])):
            try: zpnt[i][j]=int(zpnt[i][j])-1
            except: pnttxt=pnttxt+zpnt[i][j]+','
    if len(pnttxt) > 0: pnttxt='Error in point data: '+pnttxt[:-1]+'\n'
    # check varval value
    valtxt=''
    for var,vallst in varvaldic.iteritems():
        try: varvaldic[var][0]=float(vallst[0]) 
        except: valtxt=valtxt+var+'='+vallst[0]+','
    if len(valtxt) > 0: valtxt='Error in variable data: '+valtxt[:-1]+'\n'
    # replace symbolic variables by float values
    prmtxt=''; zprm=[]
    errtxt=elmtxt+pnttxt+valtxt
    #if errtxt <= 0:
    zprm=copy.deepcopy(szprm)
    for i in range(len(zprm)):
        for j in range(len(zprm[i])):
            if len(zprm[i][j]) <= 0: continue
            try: zprm[i][j]=float(zprm[i][j])
            except:
                if varvaldic.has_key(zprm[i][j]): 
                    #varnam=str(i)+':'+str(j)
                    #zmtdic[varnam]=varvaldic[zprm[i][j]]
                    zprm[i][j]=varvaldic[zprm[i][j]][0]
                else: prmtxt=prmtxt+zprm[i][j]+','
    activedic={}
    for keynam,varnam in zvardic.iteritems():
        if zactivedic.has_key(varnam): activedic[keynam]=True
    if len(prmtxt) > 0: prmtxt='Error in geom param(s): '+prmtxt[:-1]+'\n'
    errtxt=elmtxt+pnttxt+valtxt+prmtxt
    if len(errtxt) > 0: print errtxt
    extdat=[atmnam,resdat,conect,bndmulti]
    #
    if type == 'fu': return title,zelm,zpnt,zprm,zvardic,activedic,extdat #szprm,varvaldic,active,extdat
    else: return title,zelm,zpnt,zprm,zvardic,activedic #zmtdic #szprm,varvaldic,active

def WriteZMTFile(filename,title,zelm,zpnt,zprm,zvardic={},activedic={},extdat=[],seqnmb=False):
    """ Write Z-matrix data
    
    :param str filename: file name
    :param lst zelm: list of elements, [elm1(str*2),elm2(str*2),...]
    :param lst zpnt: list of points, [[p0(int),p1(int),p2(int)],...]
    :param lst zprm: list of geometric parmaters, [[length(float),angle(float),torsion(float)],...]
    :param dic vardic: dictionary of variables, {str(iatm)+':'+str(prm):[value(float),active(bool)],...]
    """
    
    def TempText(iatm,zpnt,zprm,zvardic):
        var=['   R','   A','   T']
        temp=''
        nprm=iatm
        if nprm >= 3: nprm=3
        for j in range(nprm):
            temp=temp+(fi5 % (zpnt[iatm][j]+1))+' '
            keynam=str(iatm)+':'+str(j)
            if zvardic.has_key(keynam): 
                #temp=temp+var[j]+'%04d' % (iatm+1)+' '
                temp=temp+zvardic[keynam]+' '
            else: temp=temp+(ff8 % zprm[iatm][j])+' '
        #text=text+temp+'\n'
        return temp
    
    def SortVariable(varlst):
        var=['R','A','T']; srtvarlst=[]
        for i in range(3):
            tmplst=[]
            for j in range(len(varlst)):
                if varlst[j][:1].upper() == var[i]: tmplst.append(varlst[j])
            tmplst.sort()
            srtvarlst=srtvarlst+tmplst
        return srtvarlst

    var=['R','A','T']
    blk=' '; fi5='%5d'; fi4='%04d'; ff8='%8.3f'
    natm=len(zelm)
    #
    text=title+'\n' # titlei text=text+'\n'  # a blank line
    text=text+'\n'  # a blank line
    
    if len(activedic) > 0: 
        for keynam, value in activedic.iteritems():
            if zvardic.has_key(keynam): continue
            items=keynam.split(':'); iatm=int(items[0]); iprm=int(items[1])
            zvardic[keynam]=var[iprm]+'%04d' % (iatm+1)
    # 1st to 3-rd atoms
    if seqnmb: text=text+'0001 '
    text=text+zelm[0]+'\n'
    # 2nd
    if seqnmb: text=text+'0002 '
    text=text+zelm[1]+blk #+(fi5 % zpnt[1][0])+blk
    temp=TempText(1,zpnt,zprm,zvardic)
    text=text+temp+'\n'
    # 3rd
    if seqnmb: text=text+'0003 '
    text=text+zelm[2]+blk #+(fi5 % zpnt[2][0])+blk #+(ff8 % zprm[2][0])
    temp=TempText(2,zpnt,zprm,zvardic)
    text=text+temp+'\n'
    # 4-th and late ratoms
    for i in range(3,natm):
        if seqnmb: temp=(fi4 % (i+1))+' '
        else: temp=''
        temp=temp+zelm[i]+blk #+(fi5 % zpnt[i][0])+blk
        temp=temp+TempText(i,zpnt,zprm,zvardic)
        text=text+temp+'\n'
    if len(zvardic) > 0:
        actdic={}; condic={}
        for keynam,varnam in zvardic.iteritems():
            items=keynam.split(':'); iatm=int(items[0]); prm=int(items[1])
            temp=varnam+'='+ff8 % zprm[iatm][prm]+'\n'
            if activedic.has_key(keynam) and activedic[keynam]:
                actdic[varnam]=temp
            else: condic[varnam]=temp
        #
        activelst=actdic.values()
        constlst=condic.values()
        if len(activelst) > 0:
            activelst=SortVariable(activelst)
            text=text+'Variables:\n'
            for temp in activelst: text=text+temp
        if len(constlst) > 0:
            constlst=SortVariable(constlst)
            text=text+'Constants:\n'
            for temp in constlst: text=text+temp
    text=text+'\n'
    # extra atom data
    if len(extdat):
        text=text+'EXTDAT\n'
        for i in range(len(extdat)):
            for j in range(len(extdat[i][2])): extdat[i][2][j] += 1
            text=text+extdat[i][0]+blk+extdat[i][1]+blk+lib.ListToString(extdat[i][2])+ \
                 blk+lib.ListToString(extdat[i][3])+'\n'            
    #
    f=open(filename,'w')
    f.write(text)
    f.close()
    
    return

def WriteSplitFile(splfile,filelst,title,parfile):
    text='# Created by fu at '+lib.DateTimeText()+'\n'
    text=text+'#　'+title+'\n'
    text=text+'# parent file='+parfile+'\n'
    text=text+'# '
    for file in filelst: 
        file=lib.ReplaceBackslash(file)
        text=text+file+'\n'
    f=open(splfile,'w'); f.write(text); f.close()
    
def ReadGAMESSUserDefault(deffile):
    defaultdic={}
    if not os.path.exists(deffile): return {}
    keylst=['Theory','RunType','Method','Basis','Wavefunction','Dispersion',
            'Node','Core','Memory','Disk','Charge','Spin','JobTitle',
            'Nlayer','Layer1','Layer2','Layer3','Properties','GridData']            
    f=open(deffile,'r')
    for s in f.readlines():
        s=s.strip()
        if len(s) <= 0: continue
        if s[:1] == '#': continue
        ns=s.find('#')
        if ns >= 0: s=s[:ns]
        if s[:1] == '#': continue
        key,value=lib.GetKeyAndValue(s,conv=True)
        if key in keylst:
            if key[:5] == 'Layer' or key[:10] == 'Properties' or \
                    key[:8] == 'GridData':
                items=lib.SplitStringAtSpacesOrCommas(value)
                defaultdic[key]=items
            else: defaultdic[key]=value
    f.close()
    return defaultdic

def ReadAtomCharges(chgfile):
    def ErrorMessage(s,line,filename):
        mess='Wrong data in line='+str(line)+' in '+filename+'\n'
        mess=mess+'s='+s
        lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')

    def FileExist(filename):
        mess=''
        if not os.path.exists(filename):
            mess='Not found file='+filename
            lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')
        return mess
    # check file    
    err=FileExist(chgfile)
    if len(err) > 0: return 'ERROR',[]
    #
    mess='\nRead atom charge. file='+chgfile+'\n'
    atmchglst=[]; scale=1.0
    line=0
    f=open(chgfile,'r')
    for s in f.readlines():
        ss=s; line += 1
        if s[:1] == '#': continue
        nc=s.find('#')
        if nc >= 0: s=s[:nc]
        s=s.strip()
        if len(s) <= 0: continue
        if s[:1] == '@': #file name
            n=1
            subfile=s[1:].strip(); items=subfile.split(',')
            if len(items) > 1:
                subfile=items[0].strip(); n=int(items[1])
            err=FileExist(subfile)
            if len(err) > 0: return 'ERROR',[]
            for i in range(n):
                addmess,addlst=ReadAtomCharges(subfile)
                atmchglst=atmchglst+addlst
            mess=mess+addmess+'Repeat times='+str(n)+'\n'
            continue
        if s[:6] == 'RESNAM':
            key,resnam=lib.GetKeyAndValue(s)
            mess=mess+'RESNAM='+resnam+'\n'
            continue
        if s[:6] == 'CHARGE': # total cgarge. not used
            key,charge=lib.GetKeyAndValue(s); continue
        if s[:5] == 'SCALE':
            key,scale=lib.GetKeyAndValue(s)
            mess=mess+'SCALE='+str(scale)+' at line='+str(line)+'\n'
            continue
        items=lib.SplitStringAtSpacesOrCommas(s)
        if len(items) < 3:
            ErrorMessage(ss,line,chgfile)
            return 'ERROR',[]
        # element
        try: 
            elm=int(items[0]); elm=const.ElmSbl[elm]
        except:
            elm=items[0].upper()
            if len(elm) <= 1: elm=' '+elm
        # atomic charge
        try: chg=float(items[2])
        except:
            ErrorMessage(ss,line,chgfile)
            return 'ERROR',[]
        # params
        atmchglst.append(scale*chg)
    f.close()
    
    return mess,atmchglst
 
def ReadLJParams(ljfile):
    ljprmdic={}
    if not os.path.exists(ljfile):
        mess='Not found ljfile='+ljfile
        const.CONSOLEMESSAGE(mess)
        return ljprmdic
    line=0; elm=''
    f=open(ljfile,'r')
    for s in f.readlines():
        line += 1
        s=s.strip()
        if s[:1] == '#': continue
        nc=s.find('#')
        if nc >= 0: s=s[:nc]
        s=s.strip()
        if len(s) <= 0: continue
        items=lib.SplitStringAtSpacesOrCommas(s)
        if len(items) < 3:
            mess='Wrong data in line='+str(line)
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(ReadvdWParams')
            return ljprmdic
        # element
        try: elm=lib.ElementNameFromString(items[0])
        except: pass
        # params
        try: ljprmdic[elm]=[float(items[1]),float(items[2])]
        except:
            mess='Wrong element name. elm='+elm
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(ReadvdWParams')
            
    f.close()
    
    return ljprmdic
    
def ReadQEqParams(prmfile):
    if not os.path.exists(prmfile):
        mess='Not found QEq parameter file='+prmfile
        lib.MessageBoxOK(mess,'QEq(ReadQEqParams)')
        self.Quit()
    prmdic={}; resnam=''; charge=0.0; scale=1.0
    f=open(prmfile,'r')
    for s in f.readlines():
        ns=s.find('#')
        if ns >= 0: s=s[:ns]
        s=s.strip()
        if len(s) <= 0: continue
        items=lib.SplitStringAtSpacesOrCommas(s)
        if len(items) < 3: continue
        elm=ElementNameFromString(items[0]) 
        chi=float(items[1]); j=float(items[2])
        prmdic[elm]=[chi,j]
    f.close()
    return prmdic

def ReadBDAFile(bdafile):
    """ Read BDA file
    
    :param str bdafile: file name
    :return: natm - number of atoms
    :return: molnam - name of molecule
    :return: frgdat - [bdadic,frgnamlst,frgatmdic,frgattribdic]
                      bdalst:[[bda#,baa#,bda atmnam,baa atmnam,
                               bda resdat,baa resdat],...]
                      frgnamlst: [frgnam1,frgnam2,...]
                      frgatmdic:{frgnam:atmlst,...}
                      frgattribdic:{frgnam:[charge,layer,active],..}
    """
    def ErrorMessage(line,s):
        mess='Error at line='+str(line)+'\n'
        mess=mess+'s='+s
        lib.MessageBoxOK(mess,'rwfile.ReadBDAFile')
    
    bdalst=[]; natm=-1; molnam=''; resnam=''; nbda=-1
    frgnamlst=[]; frgatmdic={}; frgattribdic={}
    if not os.path.exists(bdafile):
        mess='file not found. file='+bdafile
        lib.MessageBoxOK(mess,'rwfile.ReadBDAFile')
        return molnam,resnam,natm,[]
    head,tail=os.path.split(bdafile)
    bdanam,ext=os.path.splitext(tail)
    name=lib.GetResDatFromFileName(bdanam)
    if name is not None: bdanam=name
    f=open(bdafile,'r')
    line=0
    for s in f.readlines():
        line += 1; ss=s
        s=s.strip()
        if len(s) <= 0: continue
        nc=s.find('#')
        if nc >= 0: s=s[:nc].strip()
        if len(s) <= 0: continue
        if s.startswith('MOLNAM',0,6):
            key,molnam=lib.GetKeyAndValue(s)
            continue
        elif s.startswith('RESNAM',0,6):
            key,resnam=lib.GetKeyAndValue(s)
            if resnam[-1] == ':': resnam=resnam+' '
            continue
        elif s.startswith('NATM',0,4):
            key,natm=lib.GetKeyAndValue(s)
            continue
        elif s.startswith('NBDA',0,4):
            key,nbda=lib.GetKeyAndValue(s)
            continue
        elif s.startswith('BDABAA',0,6):
            key,s0=lib.GetKeyAndValue(s,conv=False)
            s1=s0; s2=''; nc=s0.find('"')
            if nc >= 0: 
                s1=s0[:nc]; s2=s0[nc:]
            items=lib.SplitStringAtSpacesOrCommas(s1)
            try:
                bda=int(items[1])-1; baa=int(items[2])-1  
            except:
                ErrorMessage(line,ss)
                return molnam,resnam,natm,[]
            #if not bdadic.has_key(bdanam): bdadic[bdanam]=[]
            bdaatm=None; baaatm=None; bdares=None; baares=None
            items=lib.GetStringBetweenQuotation(s2)
            if len(items) >= 2:
                bdaatm=items[0]; baaatm=items[1]
            if len(items) >= 4:
                bdares=items[2]; baares=items[3]
            bdalst.append([bda,baa,bdaatm,baaatm,bdares,baares])
        elif s.startswith('FRAGMENT',0,8):
            key,s1=lib.GetKeyAndValue(s,conv=False)
            items=s1.split('[',1)
            try:
                dat1=items[0]; dat2=items[1]
                dat2=dat2.strip(); dat2=dat2[:-1]
            except:
                ErrorMessage(line,ss)
                return molnam,resnam,natm,[]
            items=lib.SplitStringAtSpacesOrCommas(dat1)
            frgnam=items[1]; charge=int(items[3]); layer=int(items[4])
            active=int(items[5]); spin=int(items[6])
            frgnamlst.append(frgnam)
            frgattribdic[frgnam]=[charge,layer,active,spin]
            try: atmlst=lib.StringToInteger(dat2)
            except:
                ErrorMessage(lin,ss)
                return molnam,resnam,natm,[]
            atmlst=[x-1 for x in atmlst]
            
            #const.CONSOLEMESSAGE('atmlst='+str(atmlst))
            frgatmdic[frgnam]=atmlst
        else: pass
        
    f.close()
    frgdat=[bdalst,frgnamlst,frgatmdic,frgattribdic]
    return molnam,resnam,natm,frgdat

def WriteBDAFile(filename,frgdat,molnam='',resnam='',natm=-1,inpfile=''):
    """ Write BDA file
    
    :param str filename: file name
    :param lst frgdat: [bdalst,frgnamlst,frgatmdic,frgattribdic]
                       bdalst: [[bda atom #, baa atom#, bda atmnam, baaatmnam,
                         bda resdat, baa resdat],...]
                    frgnamlst: [frgnam1,frgnam2,...]
                    frgatmdic: {frgnam:frgatmlst,...}
                    frgatrribdic: {frgnam:[chrage,layer,active],...}
    :param str molnam: name of molecule
    :param str resnam: residue name, resnam:resnmb:chain
    :param int natm: number of atoms in the molecule
    :param str inpfile: file name of structure file
    """
    fi6='%6d'
    bdalst=frgdat[0]; frgnamlst=frgdat[1]
    frgatmdic=frgdat[2]; frgattribdic=frgdat[3]
    #
    text='# BDA file created by fu at '+lib.DateTimeText()+'\n'
    if len(inpfile) > 0: text=text+'# structure file='+inpfile+'\n'
    text=text+'#\n'
    text=text+'# format: seq.# of data, bda, baa\n'
    if len(molnam) > 0: text=text+'MOLNAM='+molnam+'\n'
    if len(resnam) > 0: text=text+'RESNAM='+resnam+'\n'
    if natm > 0: text=text+'NATM='+str(natm)+'\n'
    text=text+'NBDA='+str(len(bdalst))+'\n'
    for i in range(len(bdalst)):
        bda=bdalst[i][0]; baa=bdalst[i][1]
        text=text+'BDABAA='
        text=text+(fi6 % (i+1))+' '+(fi6 % (bda+1))+' '+(fi6 % (baa+1))
        text=text+'   "'+bdalst[i][2]+'"  "'+bdalst[i][3]+'"'
        text=text+'   "'+bdalst[i][4]+'"  "'+bdalst[i][5]+'"\n'        
    if len(frgnamlst) > 0:
        text=text+'# Fragment data. seq#,name,#atoms,(optional charge,'
        text=text+'layer,active,spin), and atom list\n'
        for i in range(len(frgnamlst)):
            frgnam=frgnamlst[i]
            text=text+'FRAGMENT='
            text=text+('%6d' % (i+1))+' '+frgnam+' '
            text=text+('%4d' % len(frgatmdic[frgnam]))+' '
            if frgattribdic.has_key(frgnam):
                if frgattribdic[frgnam][0] is None:
                    text=text+'   0'
                else: text=text+('%4d' % frgattribdic[frgnam][0])
                if frgattribdic[frgnam][1] is None:
                    text=text+'   1'
                else: text=text+('%4d' % frgattribdic[frgnam][1])
                if frgattribdic[frgnam][2] is None:
                    text=text+'   0'
                else: text=text+('%4d' % frgattribdic[frgnam][2])
                if frgattribdic[frgnam][3] is None:
                    text=text+'   1'
                else: text=text+('%4d' % frgattribdic[frgnam][3])
            text=text+3*' '
            atmlst=frgatmdic[frgnam]
            atmlst=[x+1 for x in atmlst]
            atmtxt=lib.IntegersToString(atmlst)
            text=text+'['+atmtxt+']\n'
    f=open(filename,'w')
    f.write(text)
    f.close()
        
def WriteLayerFile(layfile):
    const.COSOLEMESSAGE('rwfile.WriteLayerFile. not coded')

def ReadLayerFile():
    const.COSOLEMESSAGE('rwfile.ReadLayerFile.  not coded')

def ReadIniFile(inifile):
    """ Read initial setting file, 'fumodel.ini' file in 'FuFilesDirectory' directory.
    
    :return: initial directry
    :rtype: str
    :return: initial project
    :rtype: str
    :return: winpos-initial position of 'mdlwin' window, [xpos(int),ypos(int)] in pixels
    :rtype: lst
    :return: winsize-initial size of 'mdlwin' window, [width(int),height(int)] in pixels
    :rtype: lst
    """
    def TextToList(text):
        text=text.replace(" ","")
        text=text.replace("'",""); text=text.replace('"','')
        hislst=lib.StringToList(text)
        return hislst
    def RemoveQuots(name):
        name=name.strip()
        if name[:1] == "'" or name[:1] == '"': name=name[1:]
        if name [-1:] == "'" or name[-1:] == '"': name=name[:-1]
        return name
    #inifile=os.path.join(self.fudir,self.inifilename)
    inidir=''; iniprj='' #; iniset=''; inicur=''; 
    winpos=[]; winsize=[]; hislst=[]; shlpos=[]; shlsize=[]
    find=False; text=''; fudataset=''
    if os.path.exists(inifile):
        f=open(inifile,'r')
        for s in f.readlines():
            if len(s) <= 0: continue
            if s[:1] == "#": continue
            if find:
                text=text+s.strip()
                if text[-1:] == ']':
                    find=False
                    hislst=TextToList(text)
            items=s.split('=')
            if len(items) >= 2:
                if items[0].strip() == 'inidir': 
                    inidir=RemoveQuots(items[1]) #.strip()
                if items[0].strip() == 'iniprj': 
                    iniprj=RemoveQuots(items[1]) #.strip()
                #if items[0].strip() == 'iniset': iniset=items[1].strip()
                if items[0].strip() == 'winpos':
                    posxy=items[1].split(',')
                    winpos.append(int(posxy[0])) 
                    winpos.append(int(posxy[1]))
                if items[0].strip() == 'winsize':
                    sizexy=items[1].split(',')
                    winsize.append(int(sizexy[0])) 
                    winsize.append(int(sizexy[1]))
                if items[0].strip() == 'pyshellpos':
                    posxy=items[1].split(',')
                    shlpos=[int(posxy[0]),int(posxy[1])]
                if items[0].strip() == 'pyshellsize':
                    sizexy=items[1].split(',')
                    shlsize=[int(sizexy[0]),int(sizexy[1])]
                if items[0].strip() == 'FUDATASET':
                    fudataset=RemoveQuots(items[1]) #.strip()
                if items[0].strip() == 'filehistory':
                    text=text+items[1].strip()
                    if text[-1:] == ']':
                        find=False
                        hislst=TextToList(text)
                    else: find=True
        f.close()         
    
    #if len(winpos) <= 0: winpos=self.winpos
    #if len(winsize) <= 0: winsize=self.params['win-size']
    #if fudataset == '':
    #    import platform as platformos
    #    if platformos.system().upper() == 'WINDOWS': fudataset='C://FUDATASET'
    #    else: fudataset=os.path.expanduser('~//FUDATASET')
        
    initdic={'inifile':inifile,'inidir':inidir,'iniprj':iniprj,'winpos':winpos,
             'winsize':winsize,'shlpos':shlpos,'shlsize':shlsize,
             'FUDATASET':fudataset,'hislst':hislst}
    #
    return initdic
    
