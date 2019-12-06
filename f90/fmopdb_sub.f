cs---------------------------------------------------------------------
      subroutine pdbout(iout)
c----------------------------------------------------------------------
c     print data in pdb format
ce---------------------------------------------------------------------
      character*6 label(20),labtmp
      character*1 chatmp
      character*3 restmp
      character*4 atmtmp
      parameter (MaxAtm=120000,MaxRes=50000,MaxMol=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*80 title
      common/pdbhed/title
c
c     label 1:atom,2:hetatm,3:conect,4:end,5:ter,6:seqres,7:helix,8:sheet,
c           9:title,10:link,11:remark
cdebug
      call defpdb(label)
      idum=0
      jdum=0
c
      write(iout,1000) title
 1000 format('HEADER ',a72)
      write(iout,1010) natm
 1010 format('REMARK natm : ',i8)
      write(iout,1100) nres
 1100 format('REMARK nres : ',i8)
      write(iout,1200) nmol
 1200 format('REMARK nmol : ',i8)
c
c     count # of s-s bonds
      issbnd=0
      do 80 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
      if(iresid.ne.16) go to 80
      irestmp=ires
      call ssbcys(0,irestmp,jres)
      if(jres.eq.0.or.jres.lt.ires) go to 80
      issbnd=issbnd+1
      call frgmol(ires,imol1,idum,jdum)
      call frgmol(jres,imol2,idum,jdum)
c     ires-cys and jres-cys(ires<jres) has s-s bond
      write(iout,1400) issbnd,ires,jres
 1400 format('SSBOND',i4,1x,'CYS',i7,4x,'CYS',i7)
   80 continue
c
      chatmp=' '
      k=0
      do 160 imol=1,nmol
      istm=istmol(imol)
      iedm=istmol(imol+1)-1
      do 120 ires=istm,iedm
      ist=istres(ires)
      ied=istres(ires+1)-1
      numtmp=numres(ires)
      restmp=resnam(ires)
      chatmp=chanam(ires)
      call chcase(1,chatmp,1)
      call chcase(3,restmp,1)
      call resid(resnam(ires),iresid,0,0)
      if(iresid.eq.0) then
         labtmp=label(2)
      else
         labtmp=label(1)
      endif
      call chcase(6,labtmp,1)
c
      do 100 i=ist,ied
      k=k+1
      atmtmp=atmnam(i)
      call chcase(4,atmtmp,1)
      write(iout,2000) labtmp,k,atmtmp,restmp,chatmp,numtmp,
     .                                 x(i),y(i),z(i)
 2000 format(a6,i5,1x,a4,1x,a3,1x,a1,i4,4x,3f8.3)
  100 continue
  120 continue
      k=k+1
      labtmp=label(5)
      call chcase(6,labtmp,1)
c     write "TER"
      write(iout,2020) labtmp,k
 2020 format(a6,i5)
  160 continue
c
c     connect data
      labtmp=label(3)
      call chcase(6,labtmp,1)
c??? CONECT data
c      do i=1,nbnd
c         nb=nbond(i)
c         write(iout,3000) labtmp,ibond(i,1),(ibond(i,j+1),j=1,nb)
 3000    format(1x,a6,9i5)
c      enddo
c
c     write "END" at the end
      labtmp=label(4)
      call chcase(6,labtmp,1)
      write(iout,3200) labtmp
 3200 format(a6)
c
      return
      end
cs---------------------------------------------------------------------
      subroutine pdbinp(in,iout,nattot)
c----------------------------------------------------------------------
c     read pdb data
c     only ATOM, HETATM, TER, and END data will be picked up
c     the following data format is assumed
cATOM      6  OG1 THR A   5      21.671  27.113 -14.079
cHETATM 2074  O   HOH   514       9.231  46.700  24.182  1.00 29.64
cTER    1721      GLY A 231                                                  
cEND                                                                           
ce---------------------------------------------------------------------
      parameter(MaxAtm=120000,MaxRes=50000,MaxMol=50000)
      character labtmp*6,atmtmp*4,restmp*3,chatmp*1,alt*1
      character line*80
      character*6   label(20)
      character*4   bbnam(4),anmtmp
      common/pdbbnd/nbnd,nbond(MaxAtm),ibond(MaxAtm,9)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*80 title
      common/pdbhed/title
      data  maxc/80/
      data  bbnam/' n  ',' ca ',' c  ',' o  '/
      equivalence (line,labtmp)
      save bbnam
c      
      idebug=0
c
      call defpdb(label)
c
c     note: iatfrg is used for scratch in this routine.
      do 20 i=1,MaxAtm
   20 iatfrg(i)=0
      nalt=0
      natm=0
      nres=0
      nmol=1
      istmol(1)=1
      molnam(nmol)='mol'
      nummol(nmol)=nmol
      ndat=0
      nbnd=0
      natres=0
      natmol=0
ckk
      iawat=0
ckk
      title=' please give comments here'
   40 continue
      read(in,1000,end=100) line
 1000 format(a80)
      ndat=ndat+1
      call strsiz(maxc,line,nc)
      if(nc.le.0) go to 100
      call chcase(nc,line,0)
c     label 1:atom,2:hetatm,3:conect,4:end,5:ter,6:seqres,7:helix,8:sheet,
c           9:title,10:link,11:remark
      if(labtmp.eq.label(4)) go to 100
      if(labtmp.eq.label(5)) then
         nmol=nmol+1
         istmol(nmol)=nres+1
         nummol(nmol)=nmol
         molnam(nmol)='mol'
         natml=natm
         go to 40
      endif
      if(labtmp.eq.'header') then
         title=line(8:80)
         call strsiz(maxc,title,nc)
         go to 40
      endif
c
c     process ATOM
      if(labtmp.eq.label(1).or.labtmp.eq.label(2)) then
         call pdbatm(maxc,line,iatm,iantmp,atmtmp,restmp,chatmp,irest,
     .                    xt,yt,zt,st,bt,alt)
c        if(iantmp.eq.0) go to 40
         if(alt.ne.' '.and.alt.ne.'a') then
c           note: if alternative atoms are, "a"s are picked up
            nalt=nalt+1
            go to 40
         endif
         if(restmp.eq.'cyx') restmp='cys'
         if(restmp.eq.'hip') restmp='his'
         if(restmp.eq.'hie') restmp='his'
         if(restmp.eq.'hid') restmp='his'
         if(restmp.eq.'wat') iawat=iawat+1
         natm=natm+1
         if(iatm.lt.MaxAtm.and.iatm.gt.0) then
            iatfrg(iatm)=natm
         endif
         if(natm.gt.MaxAtm) go to 900
         if(natm.eq.1) then
            nres=1
            resnam(1)=restmp
            chanam(1)=chatmp
            numres(1)=irest
            istres(1)=natm
         else
ckk for water
            if(resnam(nres).eq.'wat'.and.restmp.eq.'wat') then
               if(iawat.eq.4) then
               iawat=1
               nres=nres+1
               if(nres.gt.MaxRes) go to 910
               resnam(nres)=restmp
               chanam(nres)=chatmp
               numres(nres)=irest
               istres(nres)=natm
               endif
            else
            if(resnam(nres).ne.restmp.or.numres(nres).ne.irest) then
               nres=nres+1
               if(nres.gt.MaxRes) go to 910
               resnam(nres)=restmp
               chanam(nres)=chatmp
               numres(nres)=irest
               istres(nres)=natm
            endif
ckk
            endif
ckk
         endif
         ian(natm)=iantmp
         atmnam(natm)=atmtmp
         x(natm)=xt
         y(natm)=yt
         z(natm)=zt
      endif
      go to 40
c
  100 continue
      natres=natm
      istres(nres+1)=natm+1
      if(natm.eq.natml) nmol=nmol-1
      istmol(nmol+1)=nres+1
      nattot=natm
c
c     rearrange residue atoms in the order of N,CA,C,O,....
      ireodr=0
      do ires=1,nres
         call resid(resnam(ires),iresid,0,0)
         if(iresid.ne.0) then
            ist=istres(ires)
            ied=istres(ires+1)-1
            do iba=1,4
               ifnd=0
               do i=ist,ied
                  if(atmnam(i).eq.bbnam(iba)) then
                     ifnd=i
                     anmtmp=atmnam(i)
                     xtmp=x(i)
                     ytmp=y(i)
                     ztmp=z(i)
                     iantmp=ian(i)
                  endif
               enddo
               if(ifnd.le.0) then
                  call msgout(0,1,'warning(pdbinp): missing backborn ato
     .m.$') 
                  call msgou0(0,1,' res # =$',ires)
               elseif(ifnd.ne.ist+iba-1) then
                  ireodr=ireodr+1
                  ib=iba+ist-1
                  il=ifnd
                  do i=ib,il
                     ii=il-i+ib
                     atmnam(ii)=atmnam(ii-1)
                     ian(ii)=ian(ii-1)
                     x(ii)=x(ii-1)
                     y(ii)=y(ii-1)
                     z(ii)=z(ii-1)
                  enddo
                  atmnam(ib)=anmtmp
                  ian(ib)=iantmp
                  x(ib)=xtmp
                  y(ib)=ytmp
                  z(ib)=ztmp
               endif
            enddo
cdebug begin
            if(idebug.eq.1) then
               do j=ist,ied
                 write(iout,*) j,ires,atmnam(j)
               enddo
            endif
cdebug end
         endif
      enddo
c
      if(ireodr.ne.0) then
         call msgout(0,1,'warning(pdbinp): the order of residue atoms ar
     .e changed into N,CA,C,O,....$')
      endif
      if(nalt.gt.0) then
         call msgout(0,1,'warning(pdbinp): there are alternative atoms. 
     .Group A atoms are picked up.$')
         call msgou0(0,1,' number of skipped (non-A) atoms=$',nalt)
      endif
      return
c
c     error exit
  900 call msgout(0,1,'error(pdbinp): too many atoms.$')
      call msgou0(0,1,' MaxAtm=$',MaxAtm)
      call msgout(0,0,' recompile the program with larger MaxAtm.$')
  910 call msgout(0,1,'error(pdbinp): too many residues.$')
      call msgou0(0,1,' MaxRes=$',MaxRes)
      call msgout(0,0,' recompile the program with larger MaxRes.$')
c  930 call msgout(0,1,'error(pdbinp): too many molecules.$')
c      call msgou0(0,1,' MaxMol=$',MaxMol)
c      call msgout(0,0,' recompile the program with larger MaxMol.$')
      return
      end
cs---------------------------------------------------------------------
      subroutine mnufmo(iout,idefil)
c----------------------------------------------------------------------
c     generates input data for fmo calulations with Gamess
ce---------------------------------------------------------------------
      parameter (MaxFrg=50000)
      character*512  mess
      character*80 temp*80
      character*1  temp1(80)
      character*256 laydat(5)
      character*10 basnam(5)
      dimension    nresid(20)
      dimension    nbas(5),nwf(5),nfglay(5),ilay(MaxFrg),idat(5)
      dimension    mxbody(5),levlwf(5)
      equivalence  (temp,temp1),(idef,idat(1))
      data         maxc/80/,mxmess/512/
      data         mxbody/3,3,3,3,2/
      data         levlwf/1,3,3,4,5/
c
c     count hydrogen atoms of resudues
         call cntatm(natall,nhatom,n2atom,nsiatm,0)
         if(nhatom.eq.0) then
            write(*,*) ' 1> ! hydrogen atoms are missing in some residue
     .s.'
            write(*,*) ' 1>   Continue ? (1:yes, 2:no)'
            write(*,*) ' '
            read(*,*) icnt
            if(icnt.eq.2) go to 500
         endif
c     count residue
         call cnters(nresid,nrest,nace,nnme,nwater,nonres)
c   20 continue
      idummy=0
      dummy=0.0
      call inpdef('nnodes  ',idef,dummy,laydat)
      if(idef.eq.0) then
         write(*,*) ' 1> How many computer nodes do you want to use ?'
         write(*,*) ' '
         read(*,*) nnode
         if(nnode.le.0) go to 500
      else
         nnode=idef
      endif
c
      call inpdef('ncpus   ',idef,dummy,laydat)
      if(idef.eq.0) then
         write(*,*) ' 1> How many CPU cores does each node have ?'
         write(*,*) ' '
         read(*,*) ncpu
         if(ncpu.le.0) go to 500
      else
          ncpu=idef
      endif
   30 continue
      call inpdef('memory  ',idummy,def,laydat)
      if(def.eq.0.0) then
         write(*,*) ' 1> How much memory does each node have (in megabyt
     .e) ?'
         write(*,*) ' '
         read(*,1000) temp
 1000    format(a80)
         call strsiz(maxc,temp,nc)
         if(nc.le.0) go to 500
         call strcnv(maxc,temp,ntype,idata,fdata)
         if(ntype.eq.0) then
            smem=idata
         elseif(ntype.eq.1) then
            smem=fdata
         else
            write(*,*) ' 1> wrong data type. re-enter.'
            go to 30
         endif
         if(smem.le.0.0) go to 500
      else
         smem=def
      endif

      call inpdef('nrun    ',idef,dummy,laydat)
   40 continue
      if(idef.eq.0) then
         write(*,*) ' 1> Choose runtyp (1:energy, 2:gradient, 3:geometry
     . optimization)'
         write(*,*) ' '
         read(*,*) nrun
         if(nrun.eq.0) go to 500
      else
         nrun=idef
         idef=0
      endif
      if(nrun.gt.3) then
         write(*,*) ' 1> wrong runtyp. re-enter.'
         go to 40
      endif
c     Gamess default MXATM
      MXATM=2000
      if(nrun.eq.3.and.natall.gt.MXATM) then
         call inpdef('method  ',idef,dummy,laydat)
   50    continue
         nrun=4
         if(idef.eq.0) then
            write(*,*) ' 1> Choose geometry otimization method.'
            write(*,*) '    (1:conjugate gradient, 2:simple Hessian upda
     .te, 3:GMS standard optimizer)'
            write(*,*) ' '
            read(*,*) mgopt
            if(mgopt.le.0) go to 500
            if(mgopt.eq.3) then
               write(*,*) ' '
               write(*,*) '   You have choosen GMS optimizer for more th
     .an 2000 atomic system.'
               write(*,*) '   Are you sure that GMS was compiled with "M
     .XATM" larger than',natall
               write(*,*) '   and related parameters (1:yes, 2:no) ?'
               write(*,*) ' '
               read(*,*) imgopt
               if(imgopt.ne.1) go to 50
               nrun=3
            endif
         else
            mgopt=idef
            if(mgopt.ne.3) nrun=4
            idef=0
         endif
         if(mgopt.gt.3) then
            write(*,*) ' 1> wrong optimization method. re-enter.'
            go to 50
         endif
      endif
c     nlayer
      call inpdef('nlayer  ',idef,dummy,laydat)
   80 continue
      if(idef.eq.0) then
         write(*,*) ' 1> How many layers do you want to define (1-5) ?'
         write(*,*) ' '
         read(*,*) nlayer
         if(nlayer.eq.0) go to 500
      else
         nlayer=idef
         idef=0
      endif
      if(nlayer.le.0.or.nlayer.gt.5) then
         write(*,*) ' 1> wrong number of layers. re-enter.'
         go to 80
      endif
c   90 continue
      if(nlayer.gt.1) then
         call inpdef('layer(2)',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> By default, all fragments are assigned to th
     .e lowest layer 1.'
            do i=2,nlayer
               ii=i
               call stri2c(1,ii,temp1(1),ifig)
               temp1(2)='.'
               write(*,*) ' 1> Enter fragment numbers to be assigned to
     . layer ',temp1(1),temp1(2)
               if(i.eq.2) write(*,*) '       ex. 2 3 - 5 8 10'
               write(*,*) ' '
               read(*,1200) laydat(i)
 1200          format(a256)
               call strsiz(256,laydat(i),nc)
               if(nc.le.0) go to 500
            enddo
         endif
      endif
c     wavefunction
      call inpdef('nwf(1)  ',idef,dummy,laydat)
   60 continue
      if(idef.eq.0) then
         write(*,*) ' 1> Choose wavefunction type (1:RHF, 2:DFT, 3:MP2, 
     .4:CC, 5:MCSCF)'
         if(nlayer.gt.1) write(*,*) '    for each layer, separated by bl
     .anks.'
         write(*,*) ' '
         read(*,*) (nwf(i),i=1,nlayer)
         if(nwf(1).le.0) go to 500
      else
         nwf(1)=idat(1)
         do i=2,nlayer
            nwf(i)=idat(i)
         enddo
         idef=0
      endif
      do i=1,nlayer
         if(nwf(i).gt.5.or.nwf(i).le.0) then
            write(*,*) ' 1> wrong wavefunction number. re-enter.'
            idef=0
            go to 60
         endif
      enddo
      if(nlayer.gt.1) then
         ichk=0
         do i=2,nlayer
c            if(nwf(i-1).gt.nwf(i)) ichk=ichk+1
             if(levlwf(nwf(i-1)).gt.levlwf(nwf(i))) then
                nwfi1=nwf(i-1)
                nwfi2=nwf(i)
                call stri2c(1,nwfi2,temp1(1),ifig)
                temp1(2)=' '
                call stri2c(1,nwfi1,temp1(3),ifig)
                temp1(4)=')'
                temp1(4)='.'
                ichk=ichk+1
             endif
         enddo
         if(ichk.gt.0) then
            call strcle(mxmess,mess)
         mess(1:70)=   ' 1> wrong wavefunction order. The order should b
     .e the opposite,      '
         mess(141:210)='    from a lower to a higher level(e.g., 1 2). 
     .Re-enter.            '
            call prtstr(6,70,mess(1:70))
            call prtstr(6,70,mess(141:210))
            write(*,*) ' '
            idef=0
            go to 60
         endif
      endif
c
      nmp2=0
      do i=1,nlayer
         if(nwf(i).eq.3) nmp2=nmp2+1
      enddo
      imcfrg=0
      ncore=0
      nacorb=0
      nacele=0
      nmcscf=0
      do i=1,nlayer
         if(nwf(i).eq.5) nmcscf=nmcscf+1
      enddo
      if(nmcscf.gt.0) then
         call inpdef('imcscf  ',idef,dummy,laydat)
         if(idef.eq.0) then
             write(*,*) ' 1> Enter the MCSCF fragment number.'
             write(*,*) ' '
             read(*,*) imcfrg
         else
            imcfrg=idef
         endif
         call inpdef('multip  ',idef,dummy,laydat)
         if(idef.eq.0) then
             write(*,*) ' 1> Enter the spin multiplicity of the MCSCF fr
     .agment.'
             write(*,*) ' '
             read(*,*) multip
         else
            multip=idef
         endif
         call inpdef('ncore   ',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> Enter the number of core orbitals, the numbe
     .r of active orbitals,'
            write(*,*) '    and number of active electrons, separated by
     . blanks.'
            write(*,*) ' '
            read(*,*) ncore,nacorb,nacele
         else
            ncore=idef
            call inpdef('nacorb  ',nacorb,dummy,laydat)
            call inpdef('nacele  ',nacele,dummy,laydat)
         endif
      endif
      ncc=0
      do i=1,nlayer
        if(nwf(i).eq.4) ncc=ncc+1
      enddo
c     
      if(ncc.gt.0) then
         if(nrun.gt.1) then
            write(*,*) ' 1> The CC methods are restricted to energy calc
     .ulations.'
            write(*,*) ' 1> Switch runtyp to energy and continue ?'
            write(*,*) '    (1:yes, 2:no, go back to runtyp menu)'
            write(*,*) ' '
            read(*,*) iyes
            if(iyes.eq.0) go to 500
            if(iyes.eq.2) go to 40
            nrun=1
         endif
      endif
c
      call inpdef('basid(1)',idef,dummy,laydat)
  100 continue
      if(idef.eq.0) then
         write(*,*) ' 1> Enter basis set (1:STO-3G, 2:3-21G, 3:6-31G, 4:
     .6-31G*, 5:6-311G*)'
         if(nlayer.gt.1) write(*,*) '    for each layer, separated by bl
     .anks.'
         write(*,*) ' '
         read(*,*) (nbas(i),i=1,nlayer)
         if(nbas(1).le.0) go to 500
      else
         nbas(1)=idef
         do i=2,nlayer
            nbas(i)=idat(i)
         enddo
         idef=0
      endif
      do i=1,nlayer
         if(nbas(i).gt.5) then
            write(*,*) ' 1> wrong basis set number. re-enter.'
            go to 100
         endif
      enddo
      if(nlayer.gt.1) then
         ichk=0
         do i=2,nlayer
            if(nbas(i-1).gt.nbas(i)) ichk=ichk+1
         enddo
         if(ichk.gt.0) then
            write(*,*) ' 1> wrong basis set order. the larger basis set 
     .should be assigned to'
            write(*,*) '    the higher layer. re-enter.'
            go to 100
         endif
      endif
      nsto=0
      nsi6=0
      nxsto=0
      do i=1,nlayer
         if(nbas(i).eq.1) nsto=nsto+1
         if(nbas(i).ne.1) nxsto=nxsto+1
         if(nbas(i).eq.3.or.nbas(i).eq.4) nsi6=nsi6+1
      enddo
c     count 2nd row atoms in the system
      call cntatm(natall,nhatom,n2atom,nsiatm,1)
      i2sto=1
      idef=0
      call inpdef('gmssto  ',idef,dummy,laydat)
      if(idef.eq.0) then
         if(nsto.gt.0.and.n2atom.gt.0) then
            write(*,*) ' 1> The STO-3G basis sets of GAMESS for the 2nd 
     .row atoms are different'
            write(*,*) ' 1> from the original ones. Which basis do you u
     .se ? (1:GAMESS, 2:Original)'
            write(*,*) ' '
            read(*,*) i2sto
            if(i2sto.eq.0.or.i2sto.gt.2) i2sto=1
         endif
      else
         i2sto=idef
      endif
      isi6=1
      idef=0
      call inpdef('gms631  ',idef,dummy,laydat)
      if(idef.eq.0) then
      if(nsi6.gt.0.and.nsiatm.gt.0) then
         write(*,*) ' 1> The 6-31G basis set of GAMESS for Si is differe
     .nt from the orginal one.'
         write(*,*) ' 1> Which basis do you use? (1:GAMESS, 2:Original)'
         write(*,*) ' '
         read(*,*) isi6
         if(isi6.eq.0.or.isi6.gt.2) isi6=1
      endif
      else
         isi6=idef
      endif
c     diffuse functions. on COO- on glu,asp and c-terminus
      idiffs=2
      if(nxsto.gt.0) then
         call inpdef('diffsp  ',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> Do you add diffuse functions on COO- groups 
     .? (1:yes, 2:no)'
            write(*,*) ' '
            read(*,*) idiffs
            if(idiffs.eq.0) go to 500
            if(idiffs.gt.2) idiffs=2
         else
            idiffs=idef
            idef=0
         endif
      endif
c     n-body
      nbody=2
      kbody=3
      do i=1,nlayer
        if(kbody.gt.mxbody(nwf(i))) kbody=mxbody(nwf(i))
      enddo
      if(kbody.eq.3) then
         call inpdef('nbody   ',idef,dummy,laydat)
  105    continue
         if(idef.eq.0) then
            write(*,*) ' 1> Enter the desired n-body expansion (2 or 3) 
     .?'
            write(*,*) ' '
            read(*,*) nbody
            if(nbody.eq.0) go to 500
         else
            nbody=idef
            idef=0
         endif
         if(nbody.ne.2.and.nbody.ne.3) then
            write(*,*) ' 1> wrong n-body. re-enter.'
            go to 105
         endif
         n3acc=2
         if(nbody.eq.3) then
c2.3 3-body accuracy ?
  106      continue
           write(*,*) ' 1> Desired accuracy of FMO3 ? (1:low, 2:medium, 
     .3:high)'
           write(*,*) ' '
           read(*,*) n3acc
           if(n3acc.le.0.or.n3acc.gt.3) then
              write(*,*) ' 1> wrong accuracy level. re-enter.'
              go to 106
           endif
         endif
         if(n3acc.eq.3) then
            call strcle(mxmess,mess)
            mess(1:70)=   ' 1> Warning: the high level of accuracy for F
     .MO3 requies              '
            mess(141:210)='    very considerable CPU time. Production ru
     .ns are usually best      '
            mess(211:280)='    performed at the medium level.              
     .                         '
            call prtstr(6,70,mess(1:70))
            call prtstr(6,70,mess(141:210))
            call prtstr(6,70,mess(211:280))
            write(*,*) ' '
         endif
      endif
c     PIEDA option
      ipieda=0
      if(nlayer.eq.1.and.nbody.eq.2.and.nrun.eq.1.and.(nwf(1).eq.1.or.
     .   nwf(1).eq.3.or.nwf(1).eq.4)) then
         call inpdef('ipieda  ',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> Would you like to perform the pair analysis 
     .(PIEDA) ? (1:yes, 2:no)'
            write(*,*) ' '
            read(*,*) ipieda
            if(ipieda.eq.0) go to 500
         else
            ipieda=idef
            idef=0
         endif
         if(ipieda.ne.1) ipieda=0
      endif
      if(ipieda.ne.0) then
         call strcle(mxmess,mess)
         mess(1:70)=   ' 1> This version of FMOutil enables you to perfo
     .rm PIEDA using the    '
         mess(141:210)='    PL-state (fully polarised state) without BDA
     . corrections (for     '
         mess(211:280)='    connected dimers).                          
     .                      '
         mess(281:350)='    If you want to add the PL0-state and/or BDA 
     .corrections, you      '
         mess(351:420)='    should edit the input files manually. Check 
     . the FMO tools        '
         mess(421:490)='    supplied with GAMESS (usually in ~/gamess/to
     .ols/fmo).             '
            call prtstr(6,70,mess(1:70))
            call prtstr(6,70,mess(141:210))
            call prtstr(6,70,mess(211:280))
            call prtstr(6,70,mess(281:350))
            call prtstr(6,70,mess(351:420))
            call prtstr(6,70,mess(421:490))
            write(*,*) ' '
      endif
c     print Mulliken charges
      mulk=2
      if(nbody.eq.2.and.ncc.eq.0.and.nrun.eq.1) then
         call inpdef('mulliken',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> Would you like to print Mulliken charges (1:
     .yes, 2:no) ?'
            write(*,*) ' '
            read(*,*) mulk
            if(mulk.le.0) go to 500
         else
            mulk=idef
         endif
         if(mulk.gt.2) mulk=2
         if(mulk.eq.1.and.nmp2.gt.0) then
            call strcle(mxmess,mess)
            mess(1:70)=   ' Warning: The defualt is to print RHF Mullike
     .n charges. You can ask   '
            mess(141:210)='    for MP2 charges with $MP2 MP2PRP=.T. (req
     .uires more computations).'
            call prtstr(6,70,mess(1:70))
            call prtstr(6,70,mess(141:210))
            write(*,*) ' '
         endif
      endif
c     cube file
      icube=1
c     skip if MP2 gradient job
      if(nmp2.gt.0.and.nrun.gt.1) go to 118
      if(nrun.le.2) then
         call inpdef('cube    ',idef,dummy,laydat)
  110    continue
         if(idef.eq.0) then
            write(*,*) ' 1> Would you like to produce a cube file with t
     .he total electron density ?'
            write(*,*) '    (1:no, 2:standard, 3:sparse)'
            write(*,*) ' '
            read(*,*) icube
            if(icube.le.0) go to 500
         else
            icube=idef
           idef=0
         endif
         if(icube.gt.3) then
            write(*,*) ' 1> wrong cube option. re-enter.'
            go to 110
         endif
         if(icube.eq.2.or.icube.eq.3) then
            call inpdef('grid    ',idef,def,laydat)
  115       continue
            if(def.eq.0.0) then
               write(*,*) ' 1> Enter grid spacing in Angstrom.'
               write(*,*) ' '
               read(*,*) gspace
            else
               gspace=def
               def=0.0
            endif
            if(gspace.le.0.0) then
               write(*,*) ' 1> wrong grid spacing. re-enter.'
               go to 115
            endif
         endif
      endif
      if(icube.gt.1.and.nmp2.gt.0) then
            call strcle(mxmess,mess)
         mess(1:70)=   ' 1> You have chosen to produce a cube file for a
     .n MP2 calculation.   '
         mess(141:210)='    It is likely that memory will be insufficien
     .t to do both         '
         mess(211:280)='    (or do manual input editing to avoid it).   
     .                     '
         mess(281:350)='    You may consider producing a cube file with 
     .RHF, and then running'
         mess(351:420)='    MP2 separately. The result is the same as RH
     .F density is used in '
         mess(421:490)='    any case.                                   
     .                     '
            call prtstr(6,70,mess(1:70))
            call prtstr(6,70,mess(141:210))
            call prtstr(6,70,mess(211:280))
            call prtstr(6,70,mess(281:350))
            call prtstr(6,70,mess(351:420))
            call prtstr(6,70,mess(421:490))
            write(*,*) ' '
      endif
c
  118 continue
c     PCM data
      ipcm=0
      if(nrun.eq.1.and.ipieda.eq.0) then
         ncorr=nmp2+ncc
         call mnupcm(iout,idefil,nbody,ncorr,ipcm,npcmit)
      endif
c     fragmentation
      call inpdef('nfgsiz  ',idef,dummy,laydat)
  120 continue
      if(idef.eq.0) then
         write(*,*) ' 1> Enter fragment size (1:1res-per-frg, 2:2res-per
     .-frg)'
         write(*,*) ' '
         read(*,*) nsiz
         if(nsiz.eq.0) go to 500
      else
         nsiz=idef
         idef=0
      endif
      if(nsiz.gt.2) then
         write(*,*) ' 1> this version support only 1 or 2. re-enetr.'
         go to 120
      endif
      nfgsiz=1
      if(nsiz.eq.2) nfgsiz=2
c     cys and gly options
      call inpdef('ifcys   ',idef,dummy,laydat)
c  140 continue
      ifcys=0
      if(idef.eq.0) then
         if(nfgsiz.eq.1.and.nresid(16).gt.2) then
            write(*,*) ' 1> are S-S bonded CYSs combined to one ? (1:yes
     ., 2:no)'
            write(*,*) ' '
            read(*,*) iyes
            if(iyes.eq.0) go to 500
         endif
      else
         iyes=idef
      endif
      if(iyes.eq.2) ifcys=1
c
      ifgly=0
      if(nresid(1).gt.0) then
         call inpdef('ifgly   ',idef,dummy,laydat)
         if(idef.eq.0) then
            write(*,*) ' 1> is GLY combined to the neighbor ? (1:yes, 2:
     .no)'
            write(*,*) ' '
            read(*,*) iyes
            if(iyes.eq.0) go to 500
        else
           iyes=idef
        endif
        if(iyes.eq.2) ifgly=1
      endif
c
c     'MINI' for initial guess basis set
      mbas=nlayer+1
      do 180 i=1,nlayer
      if(nbas(i).eq.1) then
         basnam(i)='STO-3G    '
      elseif(nbas(i).eq.2) then
         basnam(i)='3-21G     '
      elseif(nbas(i).eq.3) then
         basnam(i)='6-31G     '
      elseif(nbas(i).eq.4) then
         basnam(i)='6-31G*    '
      elseif(nbas(i).eq.5) then
         basnam(i)='6-311G*   '
      else
         basnam(i)='EXTBAS    '
      endif
  180 continue
      basnam(mbas)='MINI      '
c
c  200 continue
c     fractionation
         call frgpep(nfgsiz,ifcys,ifgly,imlss)
         call layer(iout,nlayer,laydat,ilay,nfglay)
c     fmo input data
c     $contrl, $system, $gddi, $intgl, $scf
      call fmogms(iout,nnode,ncpu,smem,nrun,nwf,nbas,nlayer,
     .            mgopt,icube,gspace,ncore,nacorb,nacele,nintic)
c     $pcm
      if(ipcm.eq.1) call namgrp(iout,'$pcm    ',temp,3)
c     $fmoprp group
         call fmoprp(iout,nnode,nrun,nbody,nwf,nbas,
     .          mulk,icube,ipieda,nintic,nlayer,nfglay,ipcm,npcmit)
         write(iout,2080)
c     $fmo groups
         write(iout,2010)
 2010    format(1x,'$fmo')
         call fmogrp(iout,nrun,nbody,n3acc,nwf,nlayer,ilay,imcfrg,
     .               multip)
         call fmoind(iout)
         write(iout,2080)
c     $fmolmo group
         write(iout,2020)
 2020    format(1x,'$fmohyb')
         ian=6
         do 220 i=1,mbas
         call fmolmo(iout,ian,basnam(i))
  220    continue
         write(iout,2080)
c     $fmobnd group
         write(iout,2040)
 2040    format(1x,'$fmobnd')
         call fmobnd(iout,mbas,basnam)
         write(iout,2080)
c     $data
         call datagr(iout,nbas,nlayer,idiffs,i2sto,isi6)
c     $fmoxyz group
         write(iout,2060)
 2060    format(1x,'$fmoxyz')
         call fmoxyz(iout,idiffs,ndiffs)
         write(iout,2080)
 2080    format(1x,'$end')
c
c     print fragment data (this is not input data for Gamess)
         call prtfrg(iout,nfgsiz,ifcys,ifgly,imlss,ndiffs)
c     check convalent bonds between non-peptide residues
         call rescon(iout,0)
c
  500 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine mnupcm(iout,idefil,nbody,ncorr,ipcm,npcmit)
c----------------------------------------------------------------------
c     read data for fmo/pcm
ce---------------------------------------------------------------------
      character*80 temp
      character*512  mess,mes1,mes2
      data mxmess/512/
c
      npcmit=0
c
c     initialize "namgrp" routine
      call namgrp(iout,'dummy   ',temp,0)
c
      call defval(idefil,'pcm     ',ipcm,idef)
      if(idef.eq.0) then
   20    continue
         write(*,*) ' 1> Whould you like to use PCM ? (1:yes, 2:no)'
         write(*,*) ' '
         read(*,*) ipcm
         if(ipcm.eq.0) go to 500
         if(ipcm.le.0.or.ipcm.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 20
         endif
      endif
      if(ipcm.ne.1) ipcm=0
      if(ipcm.ne.1) go to 500
c      check wavefunction
c      call namget('$fmo      ','MP2',imc)
c      call namget('$fmo      ','CC',icc)
         call strcle(mxmess,mes2)
         mes2(1:70)=   ' Warning: Water is chosen. If you wish, you may 
     .replace SOLVNT=water  '
         mes2(71:140)= ' by one of the predefined solvents manually in t
     .he generated input    '
         mes2(141:210)=' file.                                          
     .                      '
      write(*,1000) mes2(1:70)
      write(*,1000) mes2(71:140)
      write(*,1000) mes2(141:210)
      write(*,*) ' '
c
      if(ncorr.gt.0) then
         call strcle(mxmess,mess)
         mess(1:70)=   ' Warning: MP2/PCM or CC/PCM are implemented, but
     . some people have the '
         mess(71:140)= ' opinion that it is better to perform gas phase 
     .correlation energy    '
         mess(141:210)=' calculations.                                  
     .                      '
          write(*,1000) mess(1:70)
          write(*,1000) mess(71:140)
          write(*,1000) mess(141:210)
          write(*,*) ' '
 1000     format(a70)
      endif
c
      call defval(idefil,'pcmprm  ',ipcmpr,idef)
      if(idef.eq.0) then
   40    continue
         write(*,*) ' 1> Would you like to use the default PCM setting ?
     . (1:yes, 2:no)'
         write(*,*) ' '
         read(*,*) ipcmpr
         if(ipcmpr.eq.0) go to 500
         if(ipcmpr.le.0.or.ipcmpr.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 40
         endif
         if(ipcmpr.eq.1.and.nbody.eq.3) then
            call strcle(mxmess,mess)
            mess(1:70)=   ' Two-body density expansion will be used in P
     .CM (it is usually        '
            mess(71:140)= ' sufficient). You can change it to three-body
     . as $pcm ifmo=2 ->ifmo=3.'
             write(*,1000) mess(1:70)
             write(*,1000) mess(71:140)
             write(*,*) ' '
         endif
      endif
      if(ipcmpr.eq.1) then
         temp='solvnt=water ief=-10 icomp=2 icav=1 idisp=1 ifmo=2/'
         call namgrp(iout,'$pcm    ',temp,1)
         temp='ntsall=240/'
         call namgrp(iout,'$tescav ',temp,1)
         temp='radii=suahf/'
         call namgrp(iout,'$pcmcav ',temp,1)
c         temp='npcmit=2/'
c         call namgrp(iout,'$fmoprp ',temp,1)
         npcmit=2
         icav=1
         call chkrad(icav)
         if(ncorr.eq.0) then
         call strcle(mxmess,mes1)
         mes1(1:70)=   ' Warning: You chose to compute dispersion for so
     .lute-solvent but no   '
         mes1(71:140)= ' dispersion for solute-solute interactions. To h
     .ave a proper balance  '
         mes1(141:210)=' remember to add the gas-phase dispersion contri
     .bution separately     '
         mes1(211:280)=' (which means: run gas phase MP2 or CC calculati
     .on).                  '
         mes1(281:350)=' Alternatively, neglect the solute-solvent dispe
     .rsion (IDISP=0).      '
         write(*,1000) mes1(1:70)
         write(*,1000) mes1(71:140)
         write(*,1000) mes1(141:210)
         write(*,1000) mes1(211:280)
         write(*,1000) mes1(281:350)
         write(*,*) ' '
         endif
         go to 500
      endif
c
      call defval(idefil,'pcmtyp  ',ipcmty,idef)
      if(idef.eq.0) then
   60    continue
         write(*,*) ' 1> Choose PCM type: (1:C-PCM, 2:IEF-PCM)'
         write(*,*) ' '
         read(*,*) ipcmty
         if(ipcmty.eq.0) go to 500
         if(ipcmty.le.0.or.ipcmty.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 60
         endif
      endif
      if(ipcmty.eq.1) then
         temp='ief=-10/'
      else
         temp='ief=-3/'
      endif
      call namgrp(iout,'$pcm    ',temp,1)
c
      call defval(idefil,'pcmlev   ',ipcmlv,idef)
      if(idef.eq.0) then
   80    continue
         if(nbody.gt.2) then
            write(*,*) ' 1> Choose FMO/PCM level: (1:PCM[1], 2:PCM[1(2)]
     ., 3:PCM[2],'
            write(*,*) '                           4:PCM[1(3)], 5:PCM[3]
     .)'
         else
            write(*,*) ' 1> Choose FMO/PCM level: (1:PCM[1], 2:PCM[1(2)]
     ., 3:PCM[2])'
         endif
         write(*,*) ' '
         read(*,*) ipcmlv
         if(ipcmlv.eq.0) go to 500
         if(ipcmlv.le.0.or.ipcmlv.gt.5) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 80
         endif
      endif
      if(ipcmlv.eq.1) then
         temp='ifmo=1/'
      elseif(ipcmlv.eq.2) then
c         temp='npcmit=2/'
c         call namgrp(iout,'$fmoprp ',temp,1)
         temp='ifmo=2/'
         npcmit=2
      elseif(ipcmlv.eq.3) then
         temp='ifmo=2/'
      elseif(ipcmlv.eq.4) then
c         temp='npcmit=2/'
c         call namgrp(iout,'$fmoprp ',temp,1)
         temp='ifmo=3/'
         npcmit=2
      elseif(ipcmlv.eq.5) then
         temp='ifmo=3/'
      endif
      call namgrp(iout,'$pcm    ',temp,1)
c
      call defval(idefil,'icomp   ',ipcmic,idef)
      if(idef.eq.0) then
  100    continue
         write(*,*) ' 1> Choose charge compensation scheme ICOMP (0, 1, 
     .2)'
         write(*,*) ' '
         read(*,*) ipcmic
         if(ipcmic.lt.0.or.ipcmic.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 100
         endif
      endif
      if(ipcmic.eq.0) then
         temp='icomp=0/'
      elseif(ipcmlv.eq.1) then
         temp='icomp=1/'
      elseif(ipcmlv.eq.2) then
         temp='icomp=2/'
      endif
      call namgrp(iout,'$pcm    ',temp,1)
c
      call defval(idefil,'pcmcav  ',ipcmcv,idef)
      if(idef.eq.0) then
  120    continue
         write(*,*) ' 1> Compute cavitation energy (1:yes, 2:no)'
         write(*,*) ' '
         read(*,*) ipcmcv
         if(ipcmcv.eq.0) go to 500
         if(ipcmcv.lt.0.or.ipcmcv.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 120
         endif
      endif
      if(ipcmcv.eq.1) then
         temp='icav=1/'
      else
         temp='icav=0/'
      endif
      call namgrp(iout,'$pcm    ',temp,1)
c
      call defval(idefil,'pcmdsp  ',ipcmds,idef)
      if(idef.eq.0) then
  130    continue
         write(*,*) ' 1> Compute dispersion and repulsion energy (1:yes,
     .2:no)'
         write(*,*) ' '
         read(*,*) ipcmds
         if(ipcmds.eq.0) go to 500
         if(ipcmds.lt.0.or.ipcmds.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 130
         endif
      endif
      if(ipcmds.eq.1) then
         temp='idisp=1/'
      else
         temp='idisp=0/'
      endif
      call namgrp(iout,'$pcm    ',temp,1)
      if(ncorr.eq.0) then
         call strcle(mxmess,mes1)
         mes1(1:70)=   ' Warning: You chose to compute dispersion for so
     .lute-solvent but no   '
         mes1(71:140)= ' dispersion for solute-solute interactions. To h
     .ave a proper balance  '
         mes1(141:210)=' remember to add the gas-phase dispersion contri
     .bution separately     '
         mes1(211:280)=' (which means: run gas phase MP2 or CC calculati
     .on).                  '
         mes1(281:350)=' Alternatively, neglect the solute-solvent dispe
     .rsion (IDISP=0).      '
         write(*,1000) mes1(1:70)
         write(*,1000) mes1(71:140)
         write(*,1000) mes1(141:210)
         write(*,1000) mes1(211:280)
         write(*,1000) mes1(281:350)
         write(*,*) ' '
      endif
c
      call defval(idefil,'pcmtes  ',ipcmts,idef)
      if(idef.eq.0) then
  140    continue
         write(*,*) ' 1> Choose tessera density (1:low, 2:medium, 3:high
     .)'
         write(*,*) ' '
         read(*,*) ipcmts
         if(ipcmts.eq.0) go to 500
         if(ipcmcv.lt.0.or.ipcmts.gt.3) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 140
         endif
      endif
      if(ipcmts.eq.1) then
         temp='ntsall=60/'
      elseif(ipcmts.eq.2) then
         temp='ntsall=240/'
      elseif(ipcmts.eq.3) then
         temp='ntsall=960/'
      endif
      call namgrp(iout,'$tescav ',temp,1)
c
      if(ipcmlv.eq.3.or.ipcmlv.eq.5) then
         ipcmap=2
      else
         call defval(idefil,'pcmapr  ',ipcmap,idef)
         if(idef.eq.0) then
  160       continue
            write(*,*) ' 1> Whould you like to use PCM approximations ? 
     .(1:yes, 2:no)'
            write(*,*) ' '
            read(*,*) ipcmap
            if(ipcmap.eq.0) go to 500
            if(ipcmap.lt.0.or.ipcmap.gt.2) then
               write(*,*) ' 1> wrong input. re-enter.'
               go to 160
            endif
         endif
      endif
      if(ipcmap.eq.2) then
         temp='imul=0 rcut1=9999 rcut2=9999/'
         call namgrp(iout,'$pcmitr ',temp,1)
      endif
c
      call defval(idefil,'pcmrad  ',ipcmra,idef)
      if(idef.eq.0) then
  180    continue
         write(*,*) ' 1> Choose atomic radii for cavitation: (1:SUAHF, 2
     .:vdW)'
         write(*,*) ' '
         read(*,*) ipcmra
         if(ipcmra.eq.0) go to 500
         if(ipcmra.lt.0.or.ipcmra.gt.2) then
            write(*,*) ' 1> wrong input. re-enter.'
            go to 180
         endif
      endif
      if(ipcmra.eq.1) then
         temp='radii=suahf/'
      elseif(ipcmra.eq.2) then
         temp='radii=vandw/'
      endif
      call chkrad(ipcmra)
      call namgrp(iout,'$pcmcav ',temp,1)
c
  500 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine chkrad(icav)
c----------------------------------------------------------------------
c     find elements whose radii are not defined
c     icav=1 suahf, icav=2 vdw radii
c     noelem ... number of elements whose radii are not defined.
c     elmnam  ... missing element names
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*2 elmnam(100)
      dimension   noian(100)
      data nvdw/26/,nsua/6/
      integer radvdw(26),radsua(6)
c     radvdw      'h ','he','b ','c ','n ','o ','f ','ne','na','al',
c                 'si','p ','s ','cl','ar','k ','as','se','br','kr',
c                 'rb','sb','te','i ','cs','bi'
      data radvdw/ 1, 2, 5, 6, 7, 8, 9,10,11,13,
     .            14,15,16,17,18,19,33,34,35,36,
     .            37,51,52,53,55,83/
c     radsua      ' h',' c',' n',' o',' p',' s'
      data radsua/ 1, 6, 7, 8,15,16/
c      
      noelem=0
      do i=1,100
         noian(i)=0
      enddo
      do i=1,natm
         iok=1
         if(icav.eq.1) then
            do j=1,nsua
               if(ian(i).eq.radsua(j)) iok=0
            enddo
         else
            do j=1,nvdw
               if(ian(i).eq.radvdw(j)) iok=0
            enddo
         endif
         if(iok.eq.1) then
            noian(ian(i))=noian(ian(i))+1
         endif
      enddo
      do i=1,100
         iantmp=i
         if(noian(i).gt.0) then
            noelem=noelem+1
            call elmian(elmnam(noelem),iantmp,2)
         endif
      enddo
c     print message
      if(noelem.gt.0) then
         write(*,2000)
 2000    format(' The program will use a rough guess for the radii of t
     .he fillowing atoms ...',/,' Possibly you should manually enter a 
     .different set of values for them.')
         write(*,2200) (elmnam(i),i=1,noelem)
 2200    format(10(2x,a2,2x))
      endif
      return
      end
cs---------------------------------------------------------------------
      subroutine defval(idefil,keywrd,ival,idef)
c----------------------------------------------------------------------
c     find keyword and integer value in "deffil"
c     idefil ... i/o unit for "deffil"
c     keywrd ... keyword of paramter
c     ival ... integer value
c     idef ... =0 not defined, =1 defined.
ce---------------------------------------------------------------------
      character*8  keywrd,keytmp
      character*80 temp,temp1
      data maxc/80/
c
      idef=0
      if(idefil.le.0) return
c
      rewind idefil
   20 continue
         read(idefil,2000,end=100) temp
 2000 format(a80)
         call strsiz(maxc,temp,nc)
         if(temp(1:1).eq.';') go to 20
         if(nc.le.0) go to 20
         call chcase(maxc,temp,0)
c        pick up keywrd
         call strtk1(maxc,temp,nc,temp1,mc,'=')
         if(nc.le.0) go to 20
         keytmp=temp1(1:8)
         if(keywrd.eq.keytmp) then
            call strtok(maxc,temp,nc,temp1,mc)
            if(mc.gt.0) then
c              ntype  (i4) ... 0:integer,1:real,2:character,3:blank.
               call strtyp(maxc,temp1,ntype)
                  if(ntype.eq.0) then
                     call strtoi(maxc,temp1,ival)
                     idef=1
                  else
                     write(*,*) ' Error in deffil. keyword= ',keywrd
                     stop
                  endif
            endif
         endif
      go to 20
  100 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine fmogrp(iout,nrun,nbody,n3acc,nwf,nlayer,ilay,imcfrg,
     .                  multip)
c---------------------------------------------------------------------
c     $fmo groups
ce---------------------------------------------------------------------
      parameter (MaxFrg=50000)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      character*8   frglbl
      character*10  varnam
      character*12  resd
      character*80  line,line1
      dimension nwf(*),ilay(*)
      dimension     imul(MaxFrg)
      data maxc/80/
c
c     $fmo group
      ncorr=0
      do i=1,nlayer
         if(nwf(i).eq.3.or.nwf(i).eq.4) ncorr=ncorr+1
      enddo
c     nbody.eq.2
      if(nbody.eq.2) then
         if(nrun.eq.2.or.nrun.eq.3) then
            line='     resppc=2.5 resdim=2.5'
            call prtstr(iout,maxc,line)
         endif
      endif
c     nbody.eq.3
      if(nbody.eq.3) then
         if(n3acc.eq.1) then
            resd='resdim=2.5  '
            if(nrun.eq.2.or.nrun.eq.3) resd='resdim=0.0  '
            line='     resppc=2.5'
            call strlas(maxc,line,nc)
            line=line(1:nc)//' '//resd(1:10)//' ritrim(1)=0.001,-1,1.25'
            if(ncorr.gt.0) then
c              add ritrim(4) (=ritrim(3))
               call strlas(maxc,line,nc)
               line=line(1:nc)//',1.25'
            endif
         elseif(n3acc.eq.2) then
            resd='resdim=3.25 '
            if(nrun.eq.2.or.nrun.eq.3) resd='resdim=0.0  '
            line='     resppc=2.5'
            call strlas(maxc,line,nc)
            line=line(1:nc)//' '//resd(1:11)//' ritrim(1)=1.25,-1,2'
            if(ncorr.gt.0) then
c              add ritrim(4) (=ritrim(3))
               call strlas(maxc,line,nc)
               line=line(1:nc)//',1.5'
            endif
         elseif(n3acc.eq.3) then
            resd='resdim=4.0  '
            if(nrun.eq.2.or.nrun.eq.3) resd='resdim=0.0  '
            line='     resppc=2.5'
            call strlas(maxc,line,nc)
            line=line(1:nc)//' '//resd(1:10)//' ritrim(1)=2,2,2'
            if(ncorr.gt.0) then
c              add ritrim(4) (=ritrim(3))
               call strlas(maxc,line,nc)
               line=line(1:nc)//',2'
            endif
         endif
         call prtstr(iout,maxc,line)
      endif
c     nbody
      if(nbody.eq.3) then
         call strcle(maxc,line)
         line(1:11)='     nbody='
         call stri2c(maxc,nbody,line1,ifig)
         call strlas(maxc,line,nc)
         line=line(1:nc)//line1(1:ifig)
         call prtstr(iout,maxc,line)
      endif
c     nlayer
      call strcle(maxc,line)
      line(1:12)='     nlayer='
      call stri2c(maxc,nlayer,line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//line1(1:ifig)
      call prtstr(iout,maxc,line)
c     mplevl
      mpl=0
      do i=1,nlayer
         if(nwf(i).eq.3) mpl=mpl+1
      enddo
      if(mpl.ne.0) then
         call strcle(maxc,line)
         line(1:16)='      mplevl(1)='
         do i=1,nlayer
            i1=16+2*(i-1)
            if(nwf(i).eq.3) then
               line=line(1:i1)//'2,'
            else
               line=line(1:i1)//'0,'
            endif
         enddo
         call strlas(maxc,line,nc)
         line(nc:nc)=' '
         call prtstr(iout,maxc,line)
      endif
c     dfttyp
      mdft=0
      do i=1,nlayer
         if(nwf(i).eq.2) mdft=mdft+1
      enddo
      if(mdft.ne.0) then
         call strcle(maxc,line)
         line(1:16)='      dfttyp(1)='
         do i=1,nlayer
            i1=16+6*(i-1)
            if(nwf(i).eq.2) then
               line=line(1:i1)//'B3LYP,'
            else
               line=line(1:i1)//'NONE, '
            endif
         enddo
         call strlas(maxc,line,nc)
         line(nc:nc)=' '
         call prtstr(iout,maxc,line)
      endif
c     cctyp
      mcc=0
      do i=1,nlayer
         if(nwf(i).eq.4) mcc=mcc+1
      enddo
      if(mcc.gt.0) then
         call strcle(maxc,line)
         line(1:16)='       cctyp(1)='
         do i=1,nlayer
            i1=16+8*(i-1)
            if(nwf(i).eq.4) then
               line=line(1:i1)//'CCSD(T),'
            else
               line=line(1:i1)//'NONE,   '
            endif
         enddo
         call strlas(maxc,line,nc)
         line(nc:nc)=' '
         call prtstr(iout,maxc,line)
      endif
c     coroff
c      if(nwf.eq.2) then
c         call strcle(maxc,line)
c         line(1:15)='  coroff=1.0e-3'
c         call prtstr(iout,maxc,line)
c      endif
c     scftyp, scffrg and nopfrg
      mmc=0
      do i=1,nlayer
         if(nwf(i).eq.5) mmc=mmc+1
      enddo
      if(mmc.gt.0) then
         call strcle(maxc,line)
         line(1:16)='      scftyp(1)='
         do i=1,nlayer
            i1=16+6*(i-1)
            if(nwf(i).eq.5) then
               line=line(1:i1)//'MCSCF,'
            else
               line=line(1:i1)//'RHF,  '
            endif
         enddo
         call strlas(maxc,line,nc)
         line(nc:nc)=' '
         call prtstr(iout,maxc,line)
         call strcle(maxc,line)
         call stri2c(maxc,imcfrg,line1,ifig)
         line(1:13)='      scffrg('
         line=line(1:13)//line1(1:ifig)//')=mcscf '
         call strlas(maxc,line,nc)
         line=line(1:nc)//' nopfrg('//line1(1:ifig)//')=1'
         call prtstr(iout,maxc,line)
      endif
c     nfrag
      call strcle(maxc,line)
      line(1:11)='     nfrag='
      call stri2c(maxc,nfrg,line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//line1(1:ifig)
      call strlas(maxc,line,nc)
      call prtstr(iout,maxc,line)
c     layer
      if(nlayer.gt.1) then
         varnam=' layer(1)='
         call prtint(iout,varnam,nfrg,ilay)
      endif
c     multiplicity
      if(mmc.gt.0) then
         do i=1,nfrg
            imul(i)=1
         enddo
         imul(imcfrg)=multip
         varnam='  mult(1)='
         call prtint(iout,varnam,nfrg,imul)
      endif
c     icharg
      varnam='icharg(1)='
      call prtint(iout,varnam,nfrg,ichfrg)
c     frgnam
      call strcle(maxc,line)
      line(1:15)='     frgnam(1)='
      ifg=0
      n=nfrg/5
      ns=mod(nfrg,5)
      nt=5
      if(n.eq.0) nt=ns
      do 240 i=1,nt
      ifg=ifg+1
      frglbl=frgnam(ifg)(1:6)
      call strsft(8,frglbl,-1)
      call strlas(maxc,line,nc)
      line=line(1:nc)//frglbl
      call strlas(maxc,line,nc)
      if(i.ne.nfrg) line=line(1:nc)//','
  240 continue
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
      if(n.le.0) go to 400
      do 300 i=1,n-1
      do 280 j=1,5
      ifg=ifg+1
      frglbl=frgnam(ifg)(1:6)
      call strsft(8,frglbl,-1)
      call strlas(maxc,line,nc)
      line=line(1:nc)//frglbl
      call strlas(maxc,line,nc)
      if(ifg.ne.nfrg) line=line(1:nc)//','
  280 continue
      call strsft(maxc,line,-15)
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
  300 continue
c
      call strcle(maxc,line)
      if(ns.le.0) go to 400
      do 380 i=1,ns
      ifg=ifg+1
      frglbl=frgnam(ifg)(1:6)
      call strsft(8,frglbl,-1)
      call strlas(maxc,line,nc)
      line=line(1:nc)//frglbl
      call strlas(maxc,line,nc)
      if(ifg.ne.nfrg) line=line(1:nc)//','
  380 continue
      call strsft(maxc,line,-15)
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
  400 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine namgrp(iout,namlst,temp,key)
c----------------------------------------------------------------------
c     add "data" to name list data
c     currently only pcm releted name lists are supported.
c     key ... =0 initialize, =1 add data, =2 print data,
c             =3 print data with "$end".
ce---------------------------------------------------------------------
      character*80  temp,temp1
      character*8   namlst
      parameter (MaxLst=4)
      character*256 namd(MaxLst)
c      character*256 namc(MaxLst)
      dimension     nchd(MaxLst)
c      dimension     nchc(MaxLst)
      character*10  name(MaxLst)
      data   name/'$pcm      ','$pcmcav   ','$tescav   ','$pcmitr    '/
      save   namd,nchd,nchc
      data   maxc/80/
c      data   maxd/256/
c
      if(key.eq.0) then
         do i=1,MaxLst
            nchd(i)=0
c            nchc(i)=0
            namd(i)=' '
c            namc(i)=' '
         enddo
      elseif(key.eq.1) then
         ifound=1
         do i=1,MaxLst
            if(namlst.eq.name(i)) then
               ifound=0
               call strtk1(maxc,temp,nc,temp1,mc,'/')
               nchds=nchd(i)+2
               nchd(i)=nchds+mc-1
               namd(i)(nchds:nchd(i))=temp1(1:mc)
c
            endif
         enddo
         if(ifound.eq.1) then
            write(*,*) ' Program error in namlst: missing ',namlst
            stop
         endif
      else
         do i=1,MaxLst
            if(nchd(i).gt.0) then
               if(key.eq.3) then
                  nchds=nchd(i)+2
                  nchde=nchds+4
                  namd(i)(nchds:nchde)='$end'
                  nchd(i)=nchd(i)+5
               endif
               call namout(iout,name(i),namd(i))
c               call prtstr(iout,maxc,line)
            endif
         enddo
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine namout(iout,name,namd)
c----------------------------------------------------------------------
c     print name list data
ce---------------------------------------------------------------------
      character   name*8,namd*256,temp*256
      data maxc/256/
c      data maxl/70/
c
      call strsiz(maxc,namd,nd)
      call strsiz(8,name,nc)
c      nc2=nc+2
      temp=' '//name(1:nc)//' '//namd(1:nd)
      nch=nd+nc+2
         write(iout,2000) (temp(i:i),i=1,nch)
 2000    format(70a1)
c
      return
      end
cs---------------------------------------------------------------------
c     subroutine remout(iout,mess,iquot,nspace,nchlin)
c----------------------------------------------------------------------
c     print messages
c     mess(a256) ... message to be printed
c     iquot ... =1 add "!" at the first column, =0 no
c     nspace ... put nspace " "s from the first column.
c     nchlin ... maximum number of characters per line
ce---------------------------------------------------------------------
c     character   mess*512,temp*512
c     dimension   nlast(10)
c     data        maxc/512/
c
c     if(nspace.ne.0) call strsft(maxc,mess,-nspace)
c     if(iquot.ne.0) mess(1:1)='!'
c     call strlas(maxc,mess,nd)
c     if(nd.le.nchlin) then
c        write(iout,2000) (mess(i:i),i=1,nd)
c2000    format(80a1)
c     else
c        call strfmt(maxc,mess,nchlin,nl,nlast)
c        do i=1,nl
c           is=nlast(i-1)+1
c           if(i.eq.1) is=1
c           ie=nlast(i)
c           write(iout,2000) (mess(j:j),j=is,ie)
c        enddo
c     endif
c
c     return
c     end
cs---------------------------------------------------------------------
c     subroutine strfmt(maxc,mess,nchl,nl,nlast)
c----------------------------------------------------------------------
c     return positions to separate the string "mess" into nchl per line
c     nl ... number of separated data
c     nlast ... nlast(i) tells the last position for the i-th line
c             i.e. nlast(1)=64 means 1-64 belongs to the 1st line.
c     note: "mess" should be made clear at first.
ce----------------------------------------------------------------------
c     character   mess(*)
c     dimension   nlast(*)
c
c     call strlas(maxc,mess,nt)
c     nl=1
c     nlast(1)=nt
c     if(nt.le.nchl) return
c
c     nl=1
c     last=0
c  20 continue
c     do i=1,nchl
c        ii=last+nchl-i+1
c        if(mess(ii).eq.' ') then
c           nlast(nl)=ii-1
c           last=ii
c           go to 40
c        endif
c     enddo
c  40 continue
c     if(last+nchl.ge.nt) then
c        nl=nl+1
c        nlast(nl)=nt
c     else
c        nl=nl+1
c        go to 20
c     endif
c     return
c     end
cs---------------------------------------------------------------------
      subroutine mnuadh(in,iout,iprt)
c----------------------------------------------------------------------
c     add hydrogen atoms to PDB data and 
c     iprt =0 print atomic coordinates in PDB format, =1 don't print
ce---------------------------------------------------------------------
      dimension    nresid(20)
c
      ihkeep=1
c     count hydrogen atoms
         call cntatm(natall,nhatom,n2atom,nsiatm,0)
         if(nhatom.gt.0) then
            write(*,*) ' 2> ! some hydrogen atoms are already attached'
            write(*,*) ' 2>   do you want to keep them ? (1:yes/2:no)'
            write(*,*) ' '
            read(*,*) keep
            if(keep.eq.0) go to 500
            if(keep.eq.1) ihkeep=0
         endif
c     count each res numbers
         call cnters(nresid,nrest,nace,nnme,nwater,nonres)
c     defaults
      idummy=0
      call iprotn(idummy,idummy,0)
      inprot=0
      icprot=0
      iprot=0
      ihprot=0
      if(nrest.eq.0) go to 100
c
      write(*,*) ' 2> Protonate N-terminus (1:yes, 2:no)'
      write(*,*) ' '
      read(*,*) inprot
      if(inprot.eq.0) go to 500
      inprot=inprot-1
c
      write(*,*) ' 2> Protonate C-terminus (1:no, 2:yes)'
      write(*,*) ' '
      read(*,*) icpt
      if(icpt.eq.0) go to 500
      icprot=1
      if(icpt.eq.2) icprot=0
c
      iprot=1
      if(nresid(9).gt.0.or.nresid(10).gt.0) then
         write(*,*) ' 2> Protonate ASP and GLU (1:no, 2:yes, 3:one by on
     .e)'
         write(*,*) ' '
         read(*,*) ipt
         if(ipt.eq.0) go to 500
         if(ipt.eq.2) iprot=0
         if(ipt.eq.3) then
            iprot=3
            call mnuacd('asp')
            call mnuacd('glu')
         endif
      endif
c
      ihprot=0
      if(nresid(19).gt.0) then
         write(*,*) ' 2> Protonate HIS (1:yes, 2:no, 3:one by one)'
         write(*,*) ' '
         read(*,*) ihhis1
         if(ihhis1.eq.0) go to 500
         if(ihhis1.eq.1) then
            ihprot=0
         elseif(ihhis1.eq.2) then
            write(*,*) ' 2> Neutral HIS ... H at D1 or E2 (1:D1, 2:E2)'
ccc default should be reversed, i.e. 1:E2, 2:D1 
ccc            write(*,*) ' 2> Neutral HIS ... H at D1 or E2 (1:D1, 2:E2)'
            write(*,*) ' '
            read(*,*) ihprot
            if(ihprot.eq.0) go to 500
         elseif(ihhis1.eq.3) then
            ihprot=3
c           for protonation at D1
            call mnuhis(1)
c           for protonation at E2
            call mnuhis(2)
         endif
      endif
c
c      write(*,*) ' Insert H atoms after Heavy Atoms (1:yes, 2:no)'
c      write(*,*) ' '
c      read(*,*) ihpos
c      if(ihpos.eq.0) go to 500
c      ihpos=ihpos-1
c
       ihpos=0
c
c     add h to residues
         call adhpep(iout,inprot,icprot,iprot,ihprot,ihkeep,ihpos)
  100 continue
c     add h to waters moelcules
         if(nwater.gt.0) call adhwat
c     add h molecules
         if(nonres.gt.0) call adhmol(in)
c     print atomic coordinates in pdb format
         if(iprt.eq.0) call pdbout(iout)
c     check convalent bonds between non-peptide residues
         call rescon(iout,1)
c
  500 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine mnuacd(res)
c----------------------------------------------------------------------
c     input charge state for "res"
c     iprt =0 print atomic coordinates in PDB format, =1 don't print
ce---------------------------------------------------------------------
      character*80 temp
      character*3  res,restmp
      parameter    (maxacd=50)
      dimension    iprot(maxacd),numbrs(maxacd)
      character*6   resnmi(maxacd)
      data maxc/80/
c
      restmp=res
      call chcase(3,restmp,1)
c     get sequence number of acd
      call lstres(res,maxacd,nacd,numbrs)
      do i=1,nacd
         ires=numbrs(i)
         resnmi(i)='      '
         call resiid(ires,iresid,resnmi(i))
         call iprotn(ires,1,1)
      enddo
      is=1
      nprot=0
   20 continue
      write(*,*) ' '
      write(*,1600) restmp
 1600 format('  ----------------------- ',a3,' list --------------------
     .-----')
      write(*,1000) (i,resnmi(i),i=1,nacd)
      write(*,*) ' -----------------------------------------------------
     .-----'
 1000 format(5('  ',i2,':',a6,','))
      write(*,*) ' 2> input seq. numbers (separated by a blank or i-j) f
     .or protonation.'
      write(*,*) ' '
      read(*,1200) temp
 1200 format(a80)
      maxtmp=maxacd-is+1
      call strint(maxc,temp,maxtmp,nprtmp,iprot(is))
      if(nprtmp.le.0) go to 100
      do i=is,is+nprtmp-1
         if(iprot(i).le.0.or.iprot(i).gt.nacd) then
            write(*,*) ' wrong number (deleted)',iprot(i)
            write(*,*) ' '
         endif
      enddo
      nprot=nprot+nprtmp
      inew=0
      do i=1,nprot
         if(iprot(i).gt.0.and.iprot(i).le.nacd) then
            inew=inew+1
            iprot(inew)=iprot(i)
         endif
      enddo
      nprot=inew
c     delete duplications
      ierrno=0
      call chkdup(nprot,iprot,ierrno,nerr)
c      write(*,*) ' nprot,nerr ',nprot,nerr
c      write(*,*) ' iprot ',(iprot(i),i=1,nprot)
      if(nerr.gt.0) then
         do i=1,nprot
            if(iprot(i).eq.ierrno) then
               do j=i,nprot
                  iprot(j)=iprot(j+1)
               enddo
            endif
         enddo
         write(*,*) ' duplicated numbers. # of deleted data =',nerr
         write(*,*) ' '
         nprot=nprot-nerr
      endif
      if(nprot.le.0) then
         nprot=0
         is=1
         go to 20
      endif
  100 continue
      if(nprot.eq.0) then
         write(*,1300) restmp
 1300    format(' No ',a3,' will be protonated.')
      else
         write(*,1400) restmp
 1400    format(' Protonated ',a3,' will be,')
         write(*,1000) (iprot(i),resnmi(iprot(i)),i=1,nprot)
      endif
      write(*,*) ' '
      write(*,*) ' Are you sure ? (1:yes, 2:add, 3:redo)'
      write(*,*) ' '
      read(*,*) itry
      if(itry.eq.0) stop
      if(itry.eq.3) then
         is=1
         nprot=0
         go to 20
      endif
      if(itry.eq.2) then
         is=nprot+1
         go to 20
      endif
c     set flag
      if(nprot.gt.0) then
         do i=1,nprot
            ires=numbrs(iprot(i))
            call iprotn(ires,0,1)
         enddo
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine mnuhis(ipos)
c----------------------------------------------------------------------
c     input charge state for "his"
c     ipos =1 for proton at D1 and =2 for E2 positions
ce---------------------------------------------------------------------
      character*80 temp
      character*2  d1,e2,pos
      character*3  res,restmp
      parameter    (maxacd=50)
      dimension    iprot(maxacd),numbrs(maxacd)
      character*6  resnmi(maxacd)
      data         d1/'D1'/,e2/'E2'/
      data maxc/80/
c
c      iret=0
      res='his'
      restmp='HIS'
      pos=d1
      if(ipos.eq.2) pos=e2
c     get sequence number of acd
      call lstres(res,maxacd,nacd,numbrs)
      if(ipos.eq.1) then
         do i=1,nacd
            ires=numbrs(i)
            call resiid(ires,iresid,resnmi(i))
            call iprotn(ires,0,1)
         enddo
      else
         ntmp=1
         do i=1,nacd
            ires=numbrs(i)
            call resiid(ires,iresid,resnmi(i))
            call iprotn(ires,ip,2)
            if(ip.eq.1) then
c              skip
            else
               numbrs(ntmp)=numbrs(i)
               resnmi(ntmp)=resnmi(i)
               ntmp=ntmp+1
            endif
         enddo
         nacd=ntmp-1
         if(nacd.le.0) then
c             write(*,*) ' There is no HIS to be neutral H at ',e2
c             write(*,*) ' '
             return
         endif
      endif
      is=1
      nprot=0
   20 continue
      write(*,*) ' '
      write(*,1600) restmp
 1600 format('  ----------------------- ',a3,' list --------------------
     .-----')
      write(*,1000) (i,resnmi(i),i=1,nacd)
      write(*,*) ' -----------------------------------------------------
     .-----'
 1000 format(5('  ',i2,':',a6,','))
      write(*,1100) pos
 1100 format(' 2> input seq. numbers (separated by a blank or i-j)',/,
     .       '    for neutral HISs (proton at ',a2,').')
      write(*,*) ' '
      read(*,1200) temp
 1200 format(a80)
      maxtmp=maxacd-is+1
      call strint(maxc,temp,maxtmp,nprtmp,iprot(is))
      if(nprtmp.le.0) go to 100
      do i=is,is+nprtmp-1
         if(iprot(i).le.0.or.iprot(i).gt.nacd) then
            write(*,*) ' wrong number (deleted)',iprot(i)
            write(*,*) ' '
         endif
      enddo
      nprot=nprot+nprtmp
      inew=0
      do i=1,nprot
         if(iprot(i).gt.0.and.iprot(i).le.nacd) then
            inew=inew+1
            iprot(inew)=iprot(i)
         endif
      enddo
      nprot=inew
c     delete duplications
      ierrno=0
      call chkdup(nprot,iprot,ierrno,nerr)
c      write(*,*) ' nprot,nerr ',nprot,nerr
c      write(*,*) ' iprot ',(iprot(i),i=1,nprot)
      if(nerr.gt.0) then
         do i=1,nprot
            if(iprot(i).eq.ierrno) then
               do j=i,nprot
                  iprot(j)=iprot(j+1)
               enddo
            endif
         enddo
         write(*,*) ' duplicated numbers. # of deleted data =',nerr
         write(*,*) ' '
         nprot=nprot-nerr
      endif
      if(nprot.le.0) then
         nprot=0
         is=1
         go to 20
      endif
  100 continue
      if(nprot.eq.0) then
         write(*,1300) restmp,pos
 1300    format(' No ',a3,' will be neutral with H at ',a2,'.')
      else
         write(*,1400) restmp,pos
 1400    format(' Neutral ',a3,' with H at ',a2,' will be,')
         write(*,1000) (iprot(i),resnmi(iprot(i)),i=1,nprot)
      endif
      write(*,*) ' '
      write(*,*) ' Are you sure ? (1:yes, 2:add, 3:redo)'
      write(*,*) ' '
      read(*,*) itry
      if(itry.eq.0) stop
      if(itry.eq.3) then
         is=1
         nprot=0
         go to 20
      endif
      if(itry.eq.2) then
         is=nprot+1
         go to 20
      endif
c     set flag
      if(nprot.gt.0) then
         do i=1,nprot
            ires=numbrs(iprot(i))
            ip=1
            if(ipos.eq.2) ip=2
            call iprotn(ires,ip,1)
         enddo
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine lstres(res,maxacd,nacd,numbrs)
c----------------------------------------------------------------------
c     find "res" residue and store ther res number in "numbrs".
ce---------------------------------------------------------------------
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      dimension numbrs(maxacd)
      character*3 res
c      
      nacd=0
      do 40 i=1,nres
      if(resnam(i).eq.res) then
         nacd=nacd+1
         if(nacd.gt.maxacd) then
            write(*,1000) res,maxacd
 1000       format(' Program error in lstres : too many ',a3,
     .             'residue. Increase maxacd =',i5)
            stop
         endif
         numbrs(nacd)=i
      endif
   40 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine chkdup(nprot,iprot,ierrno,nerr)
c----------------------------------------------------------------------
c     check duplicated numbesr in iport and set ierrno to them
ce---------------------------------------------------------------------
      dimension iprot(*)
      nerr=0
      if(nprot.eq.1) return
c
      do i=1,nprot-1
         if(iprot(i).ne.ierrno) then
            do j=i+1,nprot
               if(iprot(j).eq.iprot(i)) then
                  nerr=nerr+1
                  iprot(j)=ierrno
               endif
            enddo
         endif
      enddo
      return
      end
cs---------------------------------------------------------------------
      subroutine iprotn(ires,iprot,key)
c----------------------------------------------------------------------
c     set protonation flag for N-,C-terms, asp, glu, and his residues
c     ires ... res number
c     iprot ... protonation flag
c         N-term: =0 protonate, =1 no
c         C-term: =0 protonate, =1 no
c         ASP and GLU: =0 protonate, =1 no
c         HIS: =0 protonate, =1 neutral(H at ND1), =2 neutral(H at NE2)
c     key ... =0 initialize, =1 set flag, =2 get flag.
ce---------------------------------------------------------------------
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      dimension iprtn(MaxRes)
      save iprtn
c
      if(ires.gt.nres) then
         write(*,*) ' Program error in iprotn : res number is larger tha
     .n nres ',ires,nres
         stop
      endif
c
      if(key.eq.0) then
         do i=1,nres
            iprtn(i)=0
         enddo
      elseif(key.eq.1) then
         iprtn(ires)=iprot
      elseif(key.eq.2) then
         iprot=iprtn(ires)
      else
         write(*,*) ' Program error in iprotn : wrong key ',key
         stop
      endif
      return
      end

cs---------------------------------------------------------------------
      subroutine mnudis(iout)
c----------------------------------------------------------------------
c     print resdues which are within rthre distance from specified res.
ce---------------------------------------------------------------------
ckk   dimension    ispres(100)
      dimension    ispres(1000)
      character*80 line
      data maxc/80/
      save maxc
c
c     count # of redisues
         call cntres(nrest,namino,nonres)
c
   20 continue
      write(*,*) ' 4> Enter reference residue numbers.'
      write(*,*) '       ex. 2 3 - 5 8 10 '
      write(*,*) ' '
      read(*,1000) line
 1000 format(a80)
      call strint(maxc,line,100,nspres,ispres)
      if(nspres.eq.0.or.ispres(1).eq.0) go to 500
c
      do 40 i=1,nspres
      if(ispres(i).gt.nrest) then
         write(*,*) ' 4> ! wrong res number. re-enter'
         write(*,*) '      the number of residues is ',nrest
         go to 20
      endif
   40 continue
c     
      write(*,*) ' 4> Enter Thresould Distance'
      write(*,*) '       ex. 2.5 (relative to the vdW radii sum) or 5.0 
     .A (Angstrom)' 
      write(*,*) ' '
      read(*,1000) line
      call strsiz(maxc,line,nc)
      if(nc.eq.0.or.line(1:1).eq.'0') go to 500
      call chcase(nc,line,0)
      key=0
      if(line(nc:nc).eq.'a') then
         key=1
         line(nc:nc)=' '
      endif
      call strtor(maxc,line,rthre)
c
c      write(*,*) ' 4> Save Selected Residues in PDB file ? (1:no, 2:yes)
c     .'
c      write(*,*) ' '
c      read(*,*) iyes
c      isave=0
c      if(iyes.eq.0) go to 500
c      if(iyes.eq.1) isave=1
ctemp
      isave=1
c
c     print or save selected residues in PDB file
         call selres(iout,nspres,ispres,rthre,key,isave)
c
  500 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine mnugeo(iout)
c----------------------------------------------------------------------
c     print geometrical parameters of covalnet bonds and hydrogen bonds
ce---------------------------------------------------------------------
      character*80 line
      character*1  line1(4)
      dimension    iop(4)
      equivalence  (line,line1(1))
      equivalence  (iop(1),ibl),(iop(2),iba),(iop(3),ips),(iop(4),ihb)
      data maxc/80/
      save maxc
c
c   20 continue
      write(*,*) ' 3> Bond Lengths, Bond Angles, Peptide Dihedral angles
     . phi:psi:omega, H-bonds'
      write(*,*) '    (1:yes, 2:yes(only heavy atoms), 3:C-alpha only, 4
     .:no)'
      write(*,*) '       ex. 1111 for all, 4441 for H-bond only'
      write(*,*) ' '
      read(*,1000) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
      if(nc.eq.0) go to 500
      do i=1,4
         iop(i)=0
      enddo
      do i=1,nc
         if(line1(i).eq.'1') iop(i)=1
         if(line1(i).eq.'2') iop(i)=2
         if(line1(i).eq.'3') iop(i)=3
      enddo
c
      if(ibl.eq.1.or.ibl.eq.2) call bndbdl(iout,ibl)
      if(iba.eq.1.or.iba.eq.2) call bndang(iout,iba)
      if(ips.eq.1.or.ips.eq.2) call phipsi(iout)
      if(ihb.eq.1.or.ihb.eq.2) call hbdbdl(iout)
c     Ca only
      if(ibl.eq.3) call carang(iout)
c
  500 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine add1a1(x1,x2,x3,x4,xh,rhx)
c----------------------------------------------------------------------
c     add one H at sp3 atom
c     rhx... bond length H-X
c     x1(H)-x2-x3-x4 where x1 is center of tetrahedron
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),x4(3),xh(3)
      dimension x2t(3),x3t(3),x4t(3)
      data      esp/0.0001/
c     
      do 20 i=1,3
      x2t(i)=x2(i)-x1(i)
      x3t(i)=x3(i)-x1(i)
      x4t(i)=x4(i)-x1(i)
   20 continue
c     unit vectors
      rnorm2=sqrt(x2t(1)**2+x2t(2)**2+x2t(3)**2)
      rnorm3=sqrt(x3t(1)**2+x3t(2)**2+x3t(3)**2)
      rnorm4=sqrt(x4t(1)**2+x4t(2)**2+x4t(3)**2)
      if(rnorm2.lt.esp.or.rnorm3.lt.esp.or.rnorm4.lt.esp) go to 900
c      write(*,*) 'norm ',rnorm2,rnorm3,rnorm4
      do 40 i=1,3
      x2t(i)=x2t(i)/rnorm2
      x3t(i)=x3t(i)/rnorm3
      x4t(i)=x4t(i)/rnorm4
   40 continue
c     center of mass coordinates
      xc=(x2t(1)+x3t(1)+x4t(1))/3.0
      yc=(x2t(2)+x3t(2)+x4t(2))/3.0
      zc=(x2t(3)+x3t(3)+x4t(3))/3.0
      rc=sqrt(xc*xc+yc*yc+zc*zc)
      xc=xc*(rhx/rc)
      yc=yc*(rhx/rc)
      zc=zc*(rhx/rc)
c     h coordinates
      xh(1)=(x1(1)-xc)
      xh(2)=(x1(2)-yc)
      xh(3)=(x1(3)-zc)
c
c      write(*,*) 'xh ',xh(1),xh(2),xh(3)
c      rbd=sqrt((xh(1)-x1(1))**2+(xh(2)-x1(2))**2+(xh(3)-x1(3))**2)
c      write(*,*) 'rhx ',rbd
c
      return
c     error exit
  900 call msgout(0,0,'error(add1a1): norm(xi-x1) is zero.$')
      end
cs---------------------------------------------------------------------
      subroutine add1a2(x1,x2,x3,xh,rhx)
c----------------------------------------------------------------------
c     add one H at sp2 atom
c     rhx... bond length H-X
c     x2-x1(H)-x3 where x1 is center of the three
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),xh(3)
      dimension x2t(3),x3t(3)
      data      esp/0.0001/
c     
      do 20 i=1,3
      x2t(i)=x2(i)-x1(i)
      x3t(i)=x3(i)-x1(i)
   20 continue
c     unit vectors
      rnorm2=sqrt(x2t(1)**2+x2t(2)**2+x2t(3)**2)
      rnorm3=sqrt(x3t(1)**2+x3t(2)**2+x3t(3)**2)
      if(rnorm2.lt.esp.or.rnorm3.lt.esp) go to 900
c      write(*,*) 'norm ',rnorm2,rnorm3
      do 40 i=1,3
      x2t(i)=x2t(i)/rnorm2
      x3t(i)=x3t(i)/rnorm3
   40 continue
c     center of mass coordinates
      xc=(x2t(1)+x3t(1))/2.0
      yc=(x2t(2)+x3t(2))/2.0
      zc=(x2t(3)+x3t(3))/2.0
      rc=sqrt(xc*xc+yc*yc+zc*zc)
      xc=xc*(rhx/rc)
      yc=yc*(rhx/rc)
      zc=zc*(rhx/rc)
c     h coordinates
      xh(1)=(x1(1)-xc)
      xh(2)=(x1(2)-yc)
      xh(3)=(x1(3)-zc)
c
c      write(*,*) 'xh ',xh(1),xh(2),xh(3)
c      rbd=sqrt((xh(1)-x1(1))**2+(xh(2)-x1(2))**2+(xh(3)-x1(3))**2)
c      write(*,*) 'rhx ',rbd
c
      return
c     error exit
  900 call msgout(0,0,'error(add1a2): norm ( xi-x1) is zero.$')
      end
cs---------------------------------------------------------------------
      subroutine add1a3(x1,x2,x3,xh1,rhx,iox,icis)
c----------------------------------------------------------------------
c     add one H to O(sp2) atom for x3-x2-OH
c     or to N(sp2) atom for x3-x2-NH
c     rhx... bond length H-X
c     H-x1-x2-x3 where all atoms are in a plane.
c     icis=0 for cis, =1 for trans 
c     iox=0 for O and S, =1 for N.
c       <H-O(S)-x2 is assumed to be 109.47 degrees
c       <H-N-x2 is assumed to be 119.0  degrees
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),xh1(3)
      dimension x1t(3),x2t(3),x3t(3),xh1t(3)
      dimension xr(3),yr(3),zr(3),xn(3),yn(3),zn(3),ra(3),rb(3),v(3,3)
      data rad61/1.064650844/,rad70/1.230963268/
      data eps/1.0e-4/
      save rad61,rad70,eps
c     
      if(abs(rhx).lt.eps) go to 900
      rad=rad70
      if(iox.ne.0) rad=rad61
      r12=sqrt((x2(1)-x1(1))**2+(x2(2)-x1(2))**2+(x2(3)-x1(3))**2)
      r23=sqrt((x3(1)-x2(1))**2+(x3(2)-x2(2))**2+(x3(3)-x2(3))**2)
      call vector(x1,x2,ra,1,1)
      call vector(x3,x2,rb,1,1)
      call anglet(ra,rb,ang)
      x1t(1)=0.0
      x1t(2)=0.0
      x1t(3)=0.0
      x2t(1)=0.0
      x2t(2)=0.0
      x2t(3)=r12
      x3t(1)=r23*sin(ang)
      x3t(2)=0.0
      x3t(3)=r23*cos(ang)+x2t(3)
      if(icis.ne.0) then
         xh1t(1)=-rhx*sin(rad)
         xh1t(2)=0.0
         xh1t(3)=-rhx*cos(rad)
      else
         xh1t(1)=rhx*sin(rad)
         xh1t(2)=0.0
         xh1t(3)=-rhx*cos(rad)
      endif
c      write(*,*) ' xit '
c      write(*,*) x1t(1),x1t(2),x1t(3)
c      write(*,*) x2t(1),x2t(2),x2t(3)
c      write(*,*) x3t(1),x3t(2),x3t(3)
c      write(*,*) xh1t(1),xh1t(2),xh1t(3)
c     back the original orientation
      nat=3
      call vecpk1(xr(1),yr(1),zr(1),x1t,0)
      call vecpk1(xr(2),yr(2),zr(2),x2t,0)
      call vecpk1(xr(3),yr(3),zr(3),x3t,0)
      call vecpk2(xn(1),yn(1),zn(1),x1,x1,0)
      call vecpk2(xn(2),yn(2),zn(2),x2,x1,0)
      call vecpk2(xn(3),yn(3),zn(3),x3,x1,0)
      call rotvec(nat,xr,yr,zr,xn,yn,zn,v)
      call trcord(xh1,xh1t,x1,v)
c
c      write(*,*) 'xh1 ',xh1(1),xh1(2),xh1(3)
c      rbd1=sqrt((xh1(1)-x1(1))**2+(xh1(2)-x1(2))**2+(xh1(3)-x1(3))**2)
c      write(*,*) 'rhx1 ',rbd1
c
      return
  900 call msgout(0,1,'error(add1a3): too short bond length.$')
      call msgou2(0,0,1,rhx,4,1)
      end
cs---------------------------------------------------------------------
      subroutine add2a1(x1,x2,x3,xh1,xh2,rhx)
c----------------------------------------------------------------------
c     add two H's at C(sp3) atom for x2-CH2-x3
c     rhx... bond length H-X
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),xh1(3),xh2(3)
      dimension x1t(3),x2t(3),x3t(3),xh1t(3),xh2t(3)
      dimension xr(3),yr(3),zr(3),xn(3),yn(3),zn(3),ra(3),rb(3),v(3,3)
      data rad54/0.955314692/,zero/0.0/
      save rad54
c     
      r12=sqrt((x2(1)-x1(1))**2+(x2(2)-x1(2))**2+(x2(3)-x1(3))**2)
      r13=sqrt((x3(1)-x1(1))**2+(x3(2)-x1(2))**2+(x3(3)-x1(3))**2)
      call vector(x2,x1,ra,1,1)
      call vector(x3,x1,rb,1,1)
      call anglet(ra,rb,ang)
      angh=0.5*ang

c      write(*,*) ' r12,r13,ang ',r12,r13,ang

      x1t(1)=0.0
      x1t(2)=0.0
      x1t(3)=0.0
      x2t(1)=r12*sin(angh)
      x2t(2)=0.0
      x2t(3)=-r12*cos(angh)
      x3t(1)=-r13*sin(angh)
      x3t(2)=0.0
      x3t(3)=-r13*cos(angh)
      xh1t(1)=0.0
      xh1t(2)=-rhx*sin(rad54)
      xh1t(3)=rhx*cos(rad54)
      xh2t(1)=0.0
      xh2t(2)=-xh1t(2)
      xh2t(3)=xh1t(3)

c      write(*,*) ' xit '
c      write(*,*) x1t(1),x1t(2),x1t(3)
c      write(*,*) x2t(1),x2t(2),x2t(3)
c      write(*,*) x3t(1),x3t(2),x3t(3)
c      write(*,*) xh1t(1),xh1t(2),xh1t(3)
c      write(*,*) xh2t(1),xh2t(2),xh2t(3)

c     back the original orientation
      nat=3
      do i=1,3
         xr(i)=zero
         yr(i)=zero
         zr(i)=zero
         xn(i)=zero
         yn(i)=zero
         zn(i)=zero
      enddo
      call vecpk1(xr(1),yr(1),zr(1),x1t,0)
      call vecpk1(xr(2),yr(2),zr(2),x2t,0)
      call vecpk1(xr(3),yr(3),zr(3),x3t,0)
      call vecpk2(xn(1),yn(1),zn(1),x1,x1,0)
      call vecpk2(xn(2),yn(2),zn(2),x2,x1,0)
      call vecpk2(xn(3),yn(3),zn(3),x3,x1,0)
      call rotvec(nat,xr,yr,zr,xn,yn,zn,v)
      call trcord(xh1,xh1t,x1,v)
      call trcord(xh2,xh2t,x1,v)
c
c      write(*,*) 'xh1 ',xh1(1),xh1(2),xh1(3)
c      rbd1=sqrt((xh1(1)-x1(1))**2+(xh1(2)-x1(2))**2+(xh1(3)-x1(3))**2)
c      write(*,*) 'rhx1 ',rbd1
c      write(*,*) 'xh2 ',xh2(1),xh2(2),xh2(3)
c      rbd2=sqrt((xh2(1)-x1(1))**2+(xh2(2)-x1(2))**2+(xh2(3)-x1(3))**2)
c      write(*,*) 'rhx2 ',rbd2
c
      return
      end
cs---------------------------------------------------------------------
      subroutine add2a2(x1,x2,x3,xh1,xh2,rhx)
c----------------------------------------------------------------------
c     add two H's at N(sp2) atom for N-C-NH2 of arg.
c     rhx... bond length H-X
c     x3-x2-x1(H2) where x1 is sp2 atom, all atoms are in a plane.
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),xh1(3),xh2(3)
      dimension x1t(3),x2t(3),x3t(3),xh1t(3),xh2t(3)
      dimension xr(3),yr(3),zr(3),xn(3),yn(3),zn(3),ra(3),rb(3),v(3,3)
      data rad59/1.05068821/,zero/0.0/
      save rad59
c     
      r12=sqrt((x2(1)-x1(1))**2+(x2(2)-x1(2))**2+(x2(3)-x1(3))**2)
      r23=sqrt((x3(1)-x2(1))**2+(x3(2)-x2(2))**2+(x3(3)-x2(3))**2)
      call vector(x1,x2,ra,1,1)
      call vector(x3,x2,rb,1,1)
      call anglet(ra,rb,ang)

c      write(*,*) ' r12,r23,ang ',r12,r23,ang

      x1t(1)=0.0
      x1t(2)=0.0
      x1t(3)=0.0
      x2t(1)=0.0
      x2t(2)=0.0
      x2t(3)=r12
      x3t(1)=r23*sin(ang)
      x3t(2)=0.0
      x3t(3)=r23*cos(ang)+x2t(3)
      xh1t(1)=-rhx*sin(rad59)
      xh1t(2)=0.0
      xh1t(3)=-rhx*cos(rad59)
      xh2t(1)=-xh1t(1)
      xh2t(2)=0.0
      xh2t(3)=xh1t(3)

c      write(*,*) ' xit '
c      write(*,*) x1t(1),x1t(2),x1t(3)
c      write(*,*) x2t(1),x2t(2),x2t(3)
c      write(*,*) x3t(1),x3t(2),x3t(3)
c      write(*,*) xh1t(1),xh1t(2),xh1t(3)
c      write(*,*) xh2t(1),xh2t(2),xh2t(3)

c     back the original orientation
      nat=3
      do i=1,3
         xr(i)=zero
         yr(i)=zero
         zr(i)=zero
         xn(i)=zero
         yn(i)=zero
         zn(i)=zero
      enddo
      call vecpk1(xr(1),yr(1),zr(1),x1t,0)
      call vecpk1(xr(2),yr(2),zr(2),x2t,0)
      call vecpk1(xr(3),yr(3),zr(3),x3t,0)
      call vecpk2(xn(1),yn(1),zn(1),x1,x1,0)
      call vecpk2(xn(2),yn(2),zn(2),x2,x1,0)
      call vecpk2(xn(3),yn(3),zn(3),x3,x1,0)
      call rotvec(nat,xr,yr,zr,xn,yn,zn,v)
      call trcord(xh1,xh1t,x1,v)
      call trcord(xh2,xh2t,x1,v)
c
c      write(*,*) 'xh1 ',xh1(1),xh1(2),xh1(3)
c      rbd1=sqrt((xh1(1)-x1(1))**2+(xh1(2)-x1(2))**2+(xh1(3)-x1(3))**2)
c      write(*,*) 'rhx1 ',rbd1
c      write(*,*) 'xh2 ',xh2(1),xh2(2),xh2(3)
c      rbd2=sqrt((xh2(1)-x1(1))**2+(xh2(2)-x1(2))**2+(xh2(3)-x1(3))**2)
c      write(*,*) 'rhx2 ',rbd2
c
      return
      end
cs---------------------------------------------------------------------
      subroutine add3a1(x1,x2,x3,xh1,xh2,xh3,rhx)
c----------------------------------------------------------------------
c     add three H's at sp3 atom. x3-x2-CH3 or x3-x2-NH3(+).
c     rhx... bond length H-X
c     (H3)x1-x2 with c3v symmetry. x3-x2-C-H(1) will be trans.
ce---------------------------------------------------------------------
      dimension x1(3),x2(3),x3(3),xh1(3),xh2(3),xh3(3)
      dimension x1t(3),x2t(3),x3t(3)
      dimension xr(3),yr(3),zr(3),xn(3),yn(3),zn(3),v(3,3)
      dimension h1t(3),h2t(3),h3t(3)
      dimension ex(3),ez(3),h1(3),h2(3),h3(3)
      data ex  / -1.00000, 0.00000, 0.00000/
      data ez  / 0.00000, 0.00000, 1.00000/
      data h1  / 0.94281, 0.00000,-0.33333/
      data h2  /-0.47141,-0.81650,-0.33333/
      data h3  /-0.47141, 0.81650,-0.33333/
      save ex,ez,h1,h2,h3
c
c     scale bond length
      do 20 i=1,3
      h1t(i)=h1(i)*rhx
      h2t(i)=h2(i)*rhx
      h3t(i)=h3(i)*rhx
   20 continue
c     given orientation
      x1t(1)=0.0
      x1t(2)=0.0
      x1t(3)=0.0
      x2t(1)=ez(1)
      x2t(2)=ez(2)
      x2t(3)=ez(3)
      x3t(1)=ex(1)
      x3t(2)=ex(2)
      x3t(3)=ex(3)
      nat=3
      call vecpk1(xr(1),yr(1),zr(1),x1t,0)
      call vecpk1(xr(2),yr(2),zr(2),x2t,0)
      call vecpk1(xr(3),yr(3),zr(3),x3t,0)
      call vecpk2(xn(1),yn(1),zn(1),x1,x1,0)
      call vecpk2(xn(2),yn(2),zn(2),x2,x1,0)
      call vecpk2(xn(3),yn(3),zn(3),x3,x1,0)
      call rotvec(nat,xr,yr,zr,xn,yn,zn,v)
      call trcord(xh1,h1t,x1,v)
      call trcord(xh2,h2t,x1,v)
      call trcord(xh3,h3t,x1,v)
c
c      write(*,*) 'xh1 ',xh1(1),xh1(2),xh1(3)
c      rbd1=sqrt((xh1(1)-x1(1))**2+(xh1(2)-x1(2))**2+(xh1(3)-x1(3))**2)
c      write(*,*) 'rhx1 ',rbd1
c      write(*,*) 'xh2 ',xh2(1),xh2(2),xh2(3)
c      rbd2=sqrt((xh2(1)-x1(1))**2+(xh2(2)-x1(2))**2+(xh2(3)-x1(3))**2)
c      write(*,*) 'rhx2 ',rbd2
c      write(*,*) 'xh3 ',xh3(1),xh3(2),xh3(3)
c      rbd2=sqrt((xh3(1)-x1(1))**2+(xh3(2)-x1(2))**2+(xh3(3)-x1(3))**2)
c      write(*,*) 'rhx2 ',rbd2
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhpep(iout,inprot,icprot,iprot,ihprot,ihkeep,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to residues
c     inprot =0 protonate N-terminus, =1 no
c     icprot =0 protonate C-terminus, =1 no
c     iprot  =0 protonate ASP and GLU, =1 no
c     ihprot =0 protonate, =1 neutral(H at ND1), =2 neutral(H at NE2)
c     ihkeep =0 keep original H's, =1 no. throw out
c     ihpos  =0 insert H atoms after heavy atoms, =1 at standard position
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      dimension iani(30),xi(30),yi(30),zi(30)
      dimension iano(30),xo(30),yo(30),zo(30)
      dimension xh(20),yh(20),zh(20)
      character*4 anmh(20),anmht(20)
      character   restmp*6
      character*4 anmi(30),anmo(30)
      dimension xco(2),yco(2),zco(2)
c
      do 200 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
cbugfix nov.09.2006
      if(ires.gt.1) call resid(resnam(ires-1),iresm1,0,0)
cbugfix nov.09.2006
c     skip non-peptide molecules
      if(iresid.eq.0) go to 200
c     nati,iani,xi,yi,zi excluding h atoms
      natt=istres(ires+1)-istres(ires)
      ist=istres(ires)
      nati=0
      nath=0
      do 40 i=1,natt
      isti=ist+i-1
      if(ian(isti).eq.1) then
         nath=nath+1
         xh(nath)=x(isti)
         yh(nath)=y(isti)
         zh(nath)=z(isti)
         anmh(nath)=atmnam(isti)
         anmht(nath)=anmh(nath)
         call chcase(4,anmht(nath),1)
      else
         nati=nati+1
         iani(nati)=ian(isti)
         xi(nati)=x(isti)
         yi(nati)=y(isti)
         zi(nati)=z(isti)
         anmi(nati)=atmnam(isti)
      endif
   40 continue
      call resmol(ires,imol,ifres,ilres)
c     cys(iresid=16)
      if(iresid.eq.16) then
         irestmp=ires
         call ssbcys(0,irestmp,jresp)
         iss=0
c         if(jresp.eq.0) iss=0
         if(jresp.eq.0) iss=1
      endif
      if(nath.gt.0) then
         if(ihkeep.eq.0) then
            write(iout,1000) ires,(anmht(ii),ii=1,nath)
 1000       format(' original h coordinates in residue #',i4, ' are kept
     ..',/,5x,15(1x,a4))
         else
            write(iout,1010) ires,(anmht(ii),ii=1,nath)
 1010       format(' original h coordinates in residue #',i4, ' are repl
     .aced with model',/,5x,15(1x,a4))
         endif
      endif
c     remove O of -COO at C-terminus, temporally
      ioco=1
      ierr=0
      if(ires.eq.ilres) call trkoco(nati,iani,xi,yi,zi,anmi,ioco,
     .                              0,ierr)
      if(ierr.ne.0) go to 940
c     set coordinates of C=O
      key=1
      if(ires.eq.ifres) key=0
cbugfix nov.09.2006
      if(iresm1.eq.0) key=0
cbugfix nov.09.2006
      call dumyco(ires,nati,iani,xi,yi,zi,xco,yco,zco,key,ierr)
c
c     add h to heavy atoms
      iprott=iprot
      if(iresid.eq.19) iprott=ihprot
      if(iprott.eq.3) then
         call iprotn(ires,iprott,2)
      endif
      call adhres(iout,ires,iresid,nati,iani,xi,yi,zi,
     .       anmi,nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprott,iss)
c
c     cap at n-terminus
      if(ires.eq.ifres) then
         call capntm(inprot,iresid,ihpos,nato,iano,xo,yo,zo,anmo)
      endif
c     recover O of -COO
      if(ires.eq.ilres.and.ioco.eq.0) then
         call trkoco(nato,iano,xo,yo,zo,anmo,ioco,1,ierr)
         nati=nati+1
      endif
c     cap at c-terminus
      if(ires.eq.ilres.and.icprot.eq.0) then
         call capctm(nato,iano,xo,yo,zo,anmo)
      endif
c
c     debug
c     write(iout,*) ' ires,iresid: ',ires,iresid
c     write(iout,*) ' nati,nato ',nati,nato
c     do 320 i=1,nato
c     write(iout,1200) i,iano(i),xo(i),yo(i),zo(i)
c1200 format(2i5,3f12.6)
c 320 continue
c
c     recover original h's if reqired
      if(ihkeep.eq.0.and.nath.gt.0) 
     .   call horigi(iout,ires,nato,iano,xo,yo,zo,anmo,
     .                                         nath,xh,yh,zh,anmh)
c
      call updres(ires,nato,iano,xo,yo,zo,anmo)
      natm=natm+(nato-natt)
      if(natm.gt.MaxAtm) go to 920
      
c      write(iout,*) ' istres after update '
c      write(iout,1300) (istres(i),i=1,nres+1)
c 1300 format(20i4)
c      write(iout,*) ' ian after update '
c      write(iout,1300) (ian(i),i=1,natres)
  
  200 continue
c
      return
c     error exit
c  900 call msgout(0,1,'error(adhpep): wrong residue id.$')
c      call msgou0(0,0,' resid=$',iresid)
  920 call msgout(0,1,'error(adhpep): too many atoms.$')
      call msgou0(0,1,' MaxAtm=$',MaxAtm)
      call msgout(0,0,' recompile the program with larger MaxAtm.$')
  940 call msgout(0,1,'error(adhpep): failed to find N-C-C=O.$')
      call msgou0(0,1,' residue number=$',ires)
      call resiid(ires,idummy,restmp)
      call msgout(0,1,' residue='//restmp//'$')
      call msgout(0,0,'  some bond lengths may be too long?$')
      end
cs----------------------------------------------------------------------
      subroutine adhala(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to ala
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(3),ip0(3),nhatm(3)
      character reslab*3
      character*4 anmh(5)
      data      iresn/2/
      data      ip0/1,3,7/
      data      nhatm/1,1,3/
      data      maxnhp/3/
      data      reslab/'ala'/
      data      anmh/' h  ',' ha ',' hb1',' hb2',' hb3'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(1),yi(1),zi(1),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adharg(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to arg
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension iat1(3),iat2(3),iat3(3)
      dimension ip(8),ip0(8),nhatm(8)
      character reslab*3
      character*4 anmh(13)
      data      iresn/12/
      data      ip0/1,3,7,10,13,16,19,22/
      data      nhatm/1,1,2,2,2,1,2,2/
      data      maxnhp/8/
      data      reslab/'arg'/
cold  data      anmh/' h  ',' ha ','1hb ','2hb ','1hg ','2hg ',
cold .               '1hd ','2hd ',' he ','1hh1','2hh1','1hh2','2hh2'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg2',' hg3',
     .               ' hd2',' hd3',' he ','hh11','hh12','hh21','hh22'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
      save      iat1,iat2,iat3
      data      iat1/5,6,7/,iat2/2,5,6/,iat3/6,7,8/
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB,CG,and CD
      ipj=1
      do 100 i=1,3
      ipi=i+2
      ipj=ipj+2
      ia1=iat1(i)
      ia2=iat2(i)
      ia3=iat3(i)
      call vecpk1(xi(ia1),yi(ia1),zi(ia1),x1,1)
      call vecpk1(xi(ia2),yi(ia2),zi(ia2),x2,1)
      call vecpk1(xi(ia3),yi(ia3),zi(ia3),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(ipi),nhatm(ipi),xh1,xh2,xh3,anmh(ipj),
     .                               natm,iano,xo,yo,zo,anmo)
  100 continue
c     add one h at NE
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(7),yi(7),zi(7),x2,1)
      call vecpk1(xi(9),yi(9),zi(9),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a2(x1,x2,x3,xh1,rn2h)
      call hadres(ip(6),nhatm(6),xh1,xh2,xh3,anmh(9),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at NH1
      call vecpk1(xi(10),yi(10),zi(10),x1,1)
      call vecpk1(xi(9),yi(9),zi(9),x2,1)
      call vecpk1(xi(11),yi(11),zi(11),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add2a2(x1,x2,x3,xh1,xh2,rn2h)
      call hadres(ip(7),nhatm(7),xh1,xh2,xh3,anmh(10),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at NH2
      call vecpk1(xi(11),yi(11),zi(11),x1,1)
      call vecpk1(xi(9),yi(9),zi(9),x2,1)
      call vecpk1(xi(10),yi(10),zi(10),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add2a2(x1,x2,x3,xh1,xh2,rn2h)
      call hadres(ip(8),nhatm(8),xh1,xh2,xh3,anmh(12),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c     write(iout,*) ' res: ',reslab
c     write(iout,*) ' nati,natm ',nati,natm
c     do 120 i=1,natm
c     write(iout,1200) i,anmo(i),xo(i),yo(i),zo(i)
c1200 format(i5,2x,a4,2x,3f12.6)
c 120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhasn(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to asn
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(4),ip0(4),nhatm(4)
      character reslab*3
      character*4 anmh(6)
      data      iresn/17/
      data      ip0/1,3,7,12/
      data      nhatm/1,1,2,2/
      data      maxnhp/4/
      data      reslab/'asn'/
cold  data      anmh/' h  ',' ha ','1hb ','2hb ','1hd2','2hd2'/
      data      anmh/' h  ',' ha ',' hb2',' hb3','hd21','hd22'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at ND2
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(6),yi(6),zi(6),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add2a2(x1,x2,x3,xh1,xh2,rn2h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhasp(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                  natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
c-----------------------------------------------------------------------
c     add hydrogen atoms to asp
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
c     iprot=0 protonated, =1 not protonated
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(4),ip0(4),nhatm(4)
      character reslab*3
      character*4 anmh(5)
      data      iresn/9/
      data      ip0/1,3,7,12/
      data      nhatm/1,1,2,1/
      data      maxnhp/4/
      data      reslab/'asp'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' ho '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms in N,CA,C,O,CB,CG,OD1 and CD2
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c
      if(iprot.eq.0) then
c        add one h at OD2
         icis=0
         call vecpk1(xi(8),yi(8),zi(8),x1,1)
         call vecpk1(xi(6),yi(6),zi(6),x2,1)
         call vecpk1(xi(7),yi(7),zi(7),x3,1)
         call lcvbnd(1,8,1,ro1h,rdum1,rdum2,ifnd)
         call add1a3(x1,x2,x3,xh1,ro1h,0,icis)
         call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                              natm,iano,xo,yo,zo,anmo)
      endif
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhcys(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iss)
c-----------------------------------------------------------------------
c     add hydrogen atoms to cys
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
c     iss=0 s-s bond, =1 no s-s bond
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(4),ip0(4),nhatm(4)
      character reslab*3
      character*4 anmh(5)
      data      iresn/16/
      data      ip0/1,3,7,10/
      data      nhatm/1,1,2,1/
      data      maxnhp/4/
      data      reslab/'cys'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at SG
      if(iss.eq.1) then
         call vecpk1(xi(6),yi(6),zi(6),x1,1)
         call vecpk1(xi(5),yi(5),zi(5),x2,1)
         call vecpk1(xi(2),yi(2),zi(2),x3,1)
         icis=1
         iox=0
         call lcvbnd(1,16,1,rsh,rdum1,rdum2,ifnd)
         call add1a3(x1,x2,x3,xh1,rsh,iox,icis)
         call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                              natm,iano,xo,yo,zo,anmo)
      endif
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhgln(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to gln
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(5),ip0(5),nhatm(5)
      character reslab*3
      character*4 anmh(8)
      data      iresn/18/
      data      ip0/1,3,7,10,15/
      data      nhatm/1,1,2,2,2/
      data      maxnhp/5/
      data      reslab/'gln'/
cold  data      anmh/' h  ',' ha ','1hb ','2hb ','1hg ','2hg ',
cold .               '1he2','2he2'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg2',' hg3',
     .               'he21','he22'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at ND2
      call vecpk1(xi(9),yi(9),zi(9),x1,1)
      call vecpk1(xi(7),yi(7),zi(7),x2,1)
      call vecpk1(xi(8),yi(8),zi(8),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add2a2(x1,x2,x3,xh1,xh2,rn2h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(7),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhglu(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                  natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
c-----------------------------------------------------------------------
c     add hydrogen atoms to glu
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
c     iprot=0 protonated, =1 not protonated
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(5),ip0(5),nhatm(5)
      character reslab*3
      character*4 anmh(7)
      data      iresn/10/
      data      ip0/1,3,7,10,15/
      data      nhatm/1,1,2,2,1/
      data      maxnhp/5/
      data      reslab/'glu'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg2',' hg3',' ho '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms in N,CA,C,O,CB,CG,OD1 and CD2
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                           natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                           natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                           natm,iano,xo,yo,zo,anmo)
c     add two h at CG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                           natm,iano,xo,yo,zo,anmo)
c
      if(iprot.eq.0) then
c        add one h at OE2
         icis=0
         call vecpk1(xi(9),yi(9),zi(9),x1,1)
         call vecpk1(xi(7),yi(7),zi(7),x2,1)
         call vecpk1(xi(8),yi(8),zi(8),x3,1)
         call lcvbnd(1,8,1,ro1h,rdum1,rdum2,ifnd)
         call add1a3(x1,x2,x3,xh1,ro1h,0,icis)
         call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(5),
     .                               natm,iano,xo,yo,zo,anmo)
      endif
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhgly(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to gly
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4 anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(2),ip0(2),nhatm(2)
      character*4 anmh(3)
      character reslab*3
      data      ip0/1,3/
      data      nhatm/1,2/
      data      maxnhp/2/
      data      reslab/'gly'/
      data      iresn/1/
      data      anmh/' h  ',' ha2',' ha3'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms in N,CA,C,O
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhhis(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                  natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
c-----------------------------------------------------------------------
c     add hydrogen atoms to phe
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
c     iprot=0 protonated, =1 with H at ND1, =2 with H at NE2
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(7),ip0(7),nhatm(7)
      character reslab*3
      character*4 anmh(8)
      data      iresn/19/
      data      ip0/1,3,7,11,13,15,17/
      data      nhatm/1,1,2,1,1,1,1/
      data      maxnhp/7/
      data      reslab/'his'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hd1',' hd2',
     .               ' he1',' he2'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at ND1
      if(iprot.eq.0.or.iprot.eq.1) then
         call vecpk1(xi(7),yi(7),zi(7),x1,1)
         call vecpk1(xi(6),yi(6),zi(6),x2,1)
         call vecpk1(xi(9),yi(9),zi(9),x3,1)
         call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
         call add1a2(x1,x2,x3,xh1,rn2h)
         call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                              natm,iano,xo,yo,zo,anmo)
      endif
c     add one h at CD2
c       ip5=ip(5)
c       if(iprot.eq.2.and.ihpos.eq.1) then
c          ip5=ip(5)-1
c       endif
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(6),yi(6),zi(6),x2,1)
      call vecpk1(xi(10),yi(10),zi(10),x3,1)
      call lcvbnd(1,6,2,rc2h,rdum1,rdum2,ifnd)
      call add1a2(x1,x2,x3,xh1,rc2h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(6),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CE1
      ip6=ip(6)
      if(iprot.eq.2.and.ihpos.eq.1) then
         ip6=ip(6)-1
      endif
      call vecpk1(xi(9),yi(9),zi(9),x1,1)
      call vecpk1(xi(7),yi(7),zi(7),x2,1)
      call vecpk1(xi(10),yi(10),zi(10),x3,1)
      call lcvbnd(1,6,2,rc2h,rdum1,rdum2,ifnd)
      call add1a2(x1,x2,x3,xh1,rc2h)
      call hadres(ip6,nhatm(6),xh1,xh2,xh3,anmh(7),
     .                                     natm,iano,xo,yo,zo,anmo)
c     add one h at NE2
      if(iprot.eq.0.or.iprot.eq.2) then
         ip7=ip(7)
         if(iprot.eq.2.and.ihpos.eq.1) then
            ip7=ip(7)-1
         endif
         call vecpk1(xi(10),yi(10),zi(10),x1,1)
         call vecpk1(xi(8),yi(8),zi(8),x2,1)
         call vecpk1(xi(9),yi(9),zi(9),x3,1)
         call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
         call add1a2(x1,x2,x3,xh1,rn2h)
         call hadres(ip7,nhatm(7),xh1,xh2,xh3,anmh(8),
     .                            natm,iano,xo,yo,zo,anmo)
      endif
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      write(iout,*) ' anmh(8) ',anmh(8)
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c1200 format(i5,3f12.6)
c 120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhile(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to ile
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(6),ip0(6),nhatm(6)
      character reslab*3
      character*4 anmh(11)
      data      iresn/5/
      data      ip0/1,3,7,9,12,16/
      data      nhatm/1,1,1,2,3,3/
      data      maxnhp/6/
      data      reslab/'ile'/
cold  data      anmh/' h  ',' ha ',' hb ','1hg1','2hg1','1hg2',
cold .               '2hg2','3hg2','1hd1','2hd1','3hd1'/
      data      anmh/' h  ',' ha ',' hb ','hg11','hg12','hg21',
     .               'hg22','hg23','hd11','hd12','hd13'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call vecpk1(xi(7),yi(7),zi(7),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CG1
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(8),yi(8),zi(8),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(4),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CG2
      call vecpk1(xi(7),yi(7),zi(7),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(6),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CD1
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(6),yi(6),zi(6),x2,1)
      call vecpk1(xi(5),yi(5),zi(5),x3,1)
      call lcvbnd(1,6,2,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(6),nhatm(6),xh1,xh2,xh3,anmh(9),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhleu(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to leu
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(6),ip0(6),nhatm(6)
      character reslab*3
      character*4 anmh(11)
      data      iresn/6/
      data      ip0/1,3,7,10,12,16/
      data      nhatm/1,1,2,1,3,3/
      data      maxnhp/6/
      data      reslab/'leu'/
cold  data      anmh/' h  ',' ha ','1hb ','2hb ',' hg ','1hd1','2hd1',
cold .               '3hd1','1hd2','2hd2','3hd2'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg ','hd11','hd12',
     .               'hd13','hd21','hd22','hd23'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call vecpk1(xi(8),yi(8),zi(8),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CD1
      call vecpk1(xi(7),yi(7),zi(7),x1,1)
      call vecpk1(xi(6),yi(6),zi(6),x2,1)
      call vecpk1(xi(5),yi(5),zi(5),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(6),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CD2
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(6),yi(6),zi(6),x2,1)
      call vecpk1(xi(5),yi(5),zi(5),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(6),nhatm(6),xh1,xh2,xh3,anmh(9),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhlys(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to lys
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension iat1(4),iat2(4),iat3(4)
      dimension ip(7),ip0(7),nhatm(7)
      character reslab*3
      character*4 anmh(13)
      data      iresn/11/
      data      ip0/1,3,7,10,13,16,19/
      data      nhatm/1,1,2,2,2,2,3/
      data      maxnhp/7/
      data      reslab/'lys'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg2',' hg3',
     .               ' hd2',' hd3',' he2',' he3',' hz1',' hz2',' hz3'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
      save      iat1,iat2,iat3
      data      iat1/5,6,7,8/,iat2/2,5,6,7/,iat3/6,7,8,9/
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB,CG,CD, and CE
      ipj=1
      do 100 i=1,4
      ipi=i+2
      ipj=ipj+2
      ia1=iat1(i)
      ia2=iat2(i)
      ia3=iat3(i)
      call vecpk1(xi(ia1),yi(ia1),zi(ia1),x1,1)
      call vecpk1(xi(ia2),yi(ia2),zi(ia2),x2,1)
      call vecpk1(xi(ia3),yi(ia3),zi(ia3),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(ipi),nhatm(ipi),xh1,xh2,xh3,anmh(ipj),
     .                               natm,iano,xo,yo,zo,anmo)
  100 continue
c     add three h at NZ
      call vecpk1(xi(9),yi(9),zi(9),x1,1)
      call vecpk1(xi(8),yi(8),zi(8),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,7,1,rn1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rn1h)
      call hadres(ip(7),nhatm(7),xh1,xh2,xh3,anmh(11),
     .                           natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhmet(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to met
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(5),ip0(5),nhatm(5)
      character reslab*3
      character*4 anmh(9)
      data      iresn/8/
      data      ip0/1,3,7,10,14/
      data      nhatm/1,1,2,2,3/
      data      maxnhp/5/
      data      reslab/'met'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg2',' hg3',
     .               ' he1',' he2',' he3'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CE
      call vecpk1(xi(8),yi(8),zi(8),x1,1)
      call vecpk1(xi(7),yi(7),zi(7),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(7),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhphe(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to phe
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension iat1(5),iat2(5),iat3(5)
      dimension ip(8),ip0(8),nhatm(8)
      character reslab*3
      character*4 anmh(9)
      data      iresn/4/
      data      ip0/1,3,7,11,13,15,17,19/
      data      nhatm/1,1,2,1,1,1,1,1/
      data      maxnhp/8/
      data      reslab/'phe'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hd1',' hd2',' he1',
     .               ' he2',' hz '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
      data      iat1/7,8,9,10,11/
      data      iat2/6,6,7,8,9/
      data      iat3/9,10,11,11,10/
      save      iat1,iat2,iat3
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CD1,CD2,CE1,CE2, and CZ
      do 100 i=1,5
      ia1=iat1(i)
      ia2=iat2(i)
      ia3=iat3(i)
      ipi=i+3
      ipj=i+4
      call vecpk1(xi(ia1),yi(ia1),zi(ia1),x1,1)
      call vecpk1(xi(ia2),yi(ia2),zi(ia2),x2,1)
      call vecpk1(xi(ia3),yi(ia3),zi(ia3),x3,1)
      call lcvbnd(1,6,2,rc2h,rdum1,rdum2,ifnd)
      call add1a2(x1,x2,x3,xh1,rc2h)
      call hadres(ip(ipi),nhatm(ipi),xh1,xh2,xh3,anmh(ipj),
     .                                       natm,iano,xo,yo,zo,anmo)
  100 continue
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhpro(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                               natm,iano,xo,yo,zo,anmo,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to pro
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(4),ip0(4),nhatm(4)
      character reslab*3
      character*4 anmh(7)
      data      iresn/7/
      data      ip0/2,6,9,12/
      data      nhatm/1,2,2,2/
      data      maxnhp/4/
      data      reslab/'pro'/
      data      anmh/' ha ',' hb2',' hb3',' hg2',' hg3',' hd2',' hd3'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(7),yi(7),zi(7),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(4),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CD
      call vecpk1(xi(7),yi(7),zi(7),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(6),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhres(iout,ires,iresid,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot,iss)
c-----------------------------------------------------------------------
c     add hydrogen to residues
c     iresid ... code # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
c     iprot=0 protonated, =1 not protonated
c     inprot=0 NH3+, =1 NH2
c     iss=0 s-s bond, =1 no s-s bond, so add h atom
ce----------------------------------------------------------------------
c     dim. 25 is the max. number of atoms + 1(for protonation) in res.
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4 anmi(*),anmo(*)
      character*6 restmp
      dimension xco(*),yco(*),zco(*)
c
      idummy=0
      if(iresid.le.0.or.iresid.gt.20) go to 900
      call resiid(ires,idummy,restmp)
c
      go to (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20),iresid
    1 continue
      call adhgly(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    2 continue
      call adhala(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    3 continue
      call adhval(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    4 continue
      call adhphe(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    5 continue
      call adhile(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    6 continue
      call adhleu(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    7 continue
      call adhpro(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,ihpos)
      go to 100
    8 continue
      call adhmet(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
    9 continue
      call adhasp(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
      go to 100
   10 continue
      call adhglu(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
      go to 100
   11 continue
      call adhlys(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   12 continue
      call adharg(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   13 continue
      call adhser(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   14 continue
      call adhthr(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   15 continue
      call adhtyr(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   16 continue
      call adhcys(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iss)
      go to 100
   17 continue
      call adhasn(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   18 continue
      call adhgln(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
      go to 100
   19 continue
      call adhhis(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos,iprot)
      go to 100
   20 continue
      call adhtrp(iout,ires,nati,iani,xi,yi,zi,anmi,
     .            nato,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
  100 continue
c
      return
c     error exit
  900 call msgout(0,1,'error(adhres): wrong residue id.$')
      call msgout(0,1,' residure='//restmp//'$')
      call msgou0(0,0,' residure number=$',ires)
      end
cs----------------------------------------------------------------------
      subroutine adhser(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to ser
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(4),ip0(4),nhatm(4)
      character reslab*3
      character*4 anmh(5)
      data      iresn/13/
      data      ip0/1,3,7,10/
      data      nhatm/1,1,2,1/
      data      maxnhp/4/
      data      reslab/'ser'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hg '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at OG
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      icis=1
      iox=0
      call lcvbnd(1,8,1,ro1h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,ro1h,iox,icis)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhthr(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to thr
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(5),ip0(5),nhatm(5)
      character reslab*3
      character*4 anmh(7)
      data      iresn/14/
      data      ip0/1,3,7,9,11/
      data      nhatm/1,1,1,1,3/
      data      maxnhp/5/
      data      reslab/'thr'/
cold  data      anmh/' h  ',' ha ',' hb ',' hg1','1hg2','2hg2','3hg2'/
      data      anmh/' h  ',' ha ',' hb ',' hg1','hg21','hg22','hg23'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call vecpk1(xi(7),yi(7),zi(7),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at OG1
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      icis=1
      iox=0
      call lcvbnd(1,8,1,ro1h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,ro1h,iox,icis)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(4),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add h3 at CG2
      call vecpk1(xi(7),yi(7),zi(7),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(5),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c     write(iout,*) ' res: ',reslab
c     write(iout,*) ' nati,natm ',nati,natm
c     do 120 i=1,natm
c     write(iout,1200) i,xo(i),yo(i),zo(i)
c1200 format(i5,3f12.6)
c 120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhtrp(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to trp
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension iat1(6),iat2(6),iat3(6)
      dimension ip(9),ip0(9),nhatm(9)
      character reslab*3
      character*4 anmh(10)
      data      iresn/20/
      data      ip0/1,3,7,11,14,17,19,21,23/
      data      nhatm/1,1,2,1,1,1,1,1,1/
      data      maxnhp/9/
      data      reslab/'trp'/
      data      anmh/' h  ',' ha ',' hb1',' hb2',' hd1',' he1',' he3',
     .               ' hz2',' hz3',' hh2'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
      data      iat1/7,9,11,12,13,14/
      data      iat2/6,7,8,10,11,12/
      data      iat3/9,10,13,14,14,13/
      save      iat1,iat2,iat3
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CD1,NE1,CE3,CZ2,CZ3, and CH2
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call lcvbnd(1,6,2,rc2h,rdum1,rdum2,ifnd)
      jpi=4
      do 100 i=1,6
      ia1=iat1(i)
      ia2=iat2(i)
      ia3=iat3(i)
      ipi=i+3
      jpi=jpi+1
      if(i.eq.2) then
         rxh=rn2h
      else
         rxh=rc2h
      endif
      call vecpk1(xi(ia1),yi(ia1),zi(ia1),x1,1)
      call vecpk1(xi(ia2),yi(ia2),zi(ia2),x2,1)
      call vecpk1(xi(ia3),yi(ia3),zi(ia3),x3,1)
      call add1a2(x1,x2,x3,xh1,rxh)
      call hadres(ip(ipi),nhatm(ipi),xh1,xh2,xh3,anmh(jpi),
     .                               natm,iano,xo,yo,zo,anmo)
  100 continue
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhtyr(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to tyr
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension iat1(4),iat2(4),iat3(4)
      dimension ip(8),ip0(8),nhatm(8)
      character reslab*3
      character*4 anmh(9)
      data      iresn/15/
      data      ip0/1,3,7,11,13,15,17,20/
      data      nhatm/1,1,2,1,1,1,1,1/
      data      maxnhp/8/
      data      reslab/'tyr'/
      data      anmh/' h  ',' ha ',' hb2',' hb3',' hd1',' hd2',
     .               ' he1',' he2',' hh '/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
      data      iat1/7, 8, 9,10/
      data      iat2/6, 6, 7, 8/
      data      iat3/9,10,11,11/
      save      iat1,iat2,iat3
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add two h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add2a1(x1,x2,x3,xh1,xh2,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CD1,CD2,CE1, and CE2
      jpi=4
      do 100 i=1,4
      ia1=iat1(i)
      ia2=iat2(i)
      ia3=iat3(i)
      ipi=i+3
      jpi=jpi+1
      call vecpk1(xi(ia1),yi(ia1),zi(ia1),x1,1)
      call vecpk1(xi(ia2),yi(ia2),zi(ia2),x2,1)
      call vecpk1(xi(ia3),yi(ia3),zi(ia3),x3,1)
      call lcvbnd(1,6,2,rc2h,rdum1,rdum2,ifnd)
      call add1a2(x1,x2,x3,xh1,rc2h)
      call hadres(ip(ipi),nhatm(ipi),xh1,xh2,xh3,anmh(jpi),
     .                               natm,iano,xo,yo,zo,anmo)
  100 continue
c     add one h at OH
      call vecpk1(xi(12),yi(12),zi(12),x1,1)
      call vecpk1(xi(11),yi(11),zi(11),x2,1)
      call vecpk1(xi(10),yi(10),zi(10),x3,1)
      icis=1
      iox=0
      call lcvbnd(1,8,1,ro1h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,ro1h,iox,icis)
      call hadres(ip(8),nhatm(8),xh1,xh2,xh3,anmh(9),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhval(iout,ires,nati,iani,xi,yi,zi,anmi,
     .                    natm,iano,xo,yo,zo,anmo,xco,yco,zco,ihpos)
c-----------------------------------------------------------------------
c     add hydrogen atoms to asp
c     ires ... seq. # of residue
c     nai,iani,xi,yi,zi...input # of natoms, atomic #, and x,y,z coord.
c     natm,iano,xo,yo,zo...output # of natoms, atomic #, and x,y,z coord.
c     xco,yco,zco ... coord. of C and O of i-1 res.
c     ihpos=0 add H at end, =1 at standard position
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension iano(*),xo(*),yo(*),zo(*)
      character*4  anmi(*),anmo(*)
      dimension xco(2),yco(2),zco(2)
      dimension x1(3),x2(3),x3(3),x4(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension ip(5),ip0(5),nhatm(5)
      character*4 anmh(9)
      character reslab*3
      data      iresn/3/
      data      ip0/1,3,7,9,13/
      data      nhatm/1,1,1,3,3/
      data      maxnhp/5/
      data      reslab/'val'/
cold  data      anmh/' h  ',' ha ',' hb ','1hg1','2hg1','3hg1',
cold .               '1hg2','2hg2','3hg2'/
      data      anmh/' h  ',' ha ',' hb ','hg11','hg12','hg13',
     .               'hg21','hg22','hg23'/
      save      iresn,ip0,nhatm,maxnhp,reslab,anmh
c
      rdum1=0.0
      rdum2=0.0
      natm=nati
      do 20 i=1,maxnhp
      ip(i)=0
      if(ihpos.eq.1) ip(i)=ip0(i)
   20 continue
c     order heavy atoms
      call ordatm(iresn,ires,natm,iani,xi,yi,zi,anmi,
     .                            iano,xo,yo,zo,anmo,iro)
      if(iro.ne.0) then
         write(iout,1000) reslab,ires
 1000    format('  ... atom order of ',a3,'(',i4,') are changed')
         do 40 i=1,natm
         iani(i)=iano(i)
          xi(i)=xo(i)
          yi(i)=yo(i)
          zi(i)=zo(i)
          anmi(i)=anmo(i)
   40    continue
      endif
c     add one h to N
      icis=1
      call vecpk1(xi(1),yi(1),zi(1),x1,1)
      call vecpk1(xco(1),yco(1),zco(1),x2,1)
      call vecpk1(xco(2),yco(2),zco(2),x3,1)
      call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,rn2h,1,icis)
      call hadres(ip(1),nhatm(1),xh1,xh2,xh3,anmh(1),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CA
      call vecpk1(xi(2),yi(2),zi(2),x1,1)
      call vecpk1(xi(1),yi(1),zi(1),x2,1)
      call vecpk1(xi(3),yi(3),zi(3),x3,1)
      call vecpk1(xi(5),yi(5),zi(5),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(2),nhatm(2),xh1,xh2,xh3,anmh(2),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add one h at CB
      call vecpk1(xi(5),yi(5),zi(5),x1,1)
      call vecpk1(xi(2),yi(2),zi(2),x2,1)
      call vecpk1(xi(6),yi(6),zi(6),x3,1)
      call vecpk1(xi(7),yi(7),zi(7),x4,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add1a1(x1,x2,x3,x4,xh1,rc1h)
      call hadres(ip(3),nhatm(3),xh1,xh2,xh3,anmh(3),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CG1
      call vecpk1(xi(6),yi(6),zi(6),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(4),nhatm(4),xh1,xh2,xh3,anmh(4),
     .                                       natm,iano,xo,yo,zo,anmo)
c     add three h at CG2
      call vecpk1(xi(7),yi(7),zi(7),x1,1)
      call vecpk1(xi(5),yi(5),zi(5),x2,1)
      call vecpk1(xi(2),yi(2),zi(2),x3,1)
      call lcvbnd(1,6,1,rc1h,rdum1,rdum2,ifnd)
      call add3a1(x1,x2,x3,xh1,xh2,xh3,rc1h)
      call hadres(ip(5),nhatm(5),xh1,xh2,xh3,anmh(7),
     .                                       natm,iano,xo,yo,zo,anmo)
c
c     debug
c      write(iout,*) ' res: ',reslab
c      write(iout,*) ' nati,natm ',nati,natm
c      do 120 i=1,natm
c      write(iout,1200) i,xo(i),yo(i),zo(i)
c 1200 format(i5,3f12.6)
c  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine adhmol(in)
c-----------------------------------------------------------------------
c     add h atoms to molecules
c     ihkeep =0 keep original Hs, =1 replace with generated ones
c     note: ihkeep is not supported
c     this subroutine will be called if there are the key word
c     "REMARK ADDH" in PDB file. ex.
c     REMARK ADDH 13 1 2 3 0 1.0
c     13: type of h addition.
c      1: sequence # of atom to which hydrogen atom(s) are added
c      2, 3: sequence # of atoms which are referenced for h addition
c      0: cis(0) or trans (1)  only effective when type is 13.
c      1.0: bond length. can be omitted
ce----------------------------------------------------------------------
      parameter (MaxRAT=500)
      dimension     iano(MaxRAT),xo(MaxRAT),yo(MaxRAT),zo(MaxRAT)
      character*4   anmo(MaxRAT)
      character     restmp*6
      character*4 anmh(20),anmht(20)
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      dimension x1(3),x2(3),x3(3),xh1(3),xh2(3),xh3(3)
      character*4 anm(4)
      character*80 temp,temp1
      data  anm/' h  ',' h1 ',' h2 ',' h3 '/
      data  maxc/80/
      save  maxc,anm
c
      rewind in
      nadd=0
      nadd0=0
      nhatm=0
      ires0=0
   20 continue
      read(in,1000,end=500) temp
 1000 format(a80)
      call chcase(maxc,temp,0)
      call strtok(maxc,temp,nc,temp1,mc)
      if(temp1(1:6).ne.'remark') go to 100
      call strtok(maxc,temp,nc,temp1,mc)
      if(temp1(1:4).ne.'addh') go to 100
c     type of atom addition
      call strtok(maxc,temp,nc,temp1,mc)
      if(mc.le.0) then
         call msgout(0,1,'warning(adhmol): missing bond type. skiped.$')
         go to 100
      endif
      call strtoi(maxc,temp1,int)
      itype=int
c     iatm1
      call strtok(maxc,temp,nc,temp1,mc)
      if(mc.le.0) then
         call msgout(0,1,'warning(adhmol): missing atom 1. skiped.$')
         go to 100
      endif
      call strtoi(maxc,temp1,int)
      iatm1=int
      call atmres(iatm1,ires)
      idummy=0
      call resiid(ires,idummy,restmp)
      nadd=nadd+nhatm
      if(ires.ne.ires0) then
c        next res/mol
         if(ires0.ne.0) then
            call updres(ires0,nato,iano,xo,yo,zo,anmo)
            natm=natm+nadd
         endif
         ires0=ires
         nadd0=nadd
c        nati,iani,xi,yi,zi excluding h atoms
         natt=istres(ires+1)-istres(ires)
         ist=istres(ires)
         nato=0
         nath=0
         do 40 i=1,natt
         isti=ist+i-1
         if(ian(isti).eq.1) then
            nath=nath+1
            anmh(nath)=atmnam(isti)
            anmht(nath)=anmh(nath)
            call chcase(4,anmht(nath),1)
         else
            nato=nato+1
            iano(nato)=ian(isti)
            xo(nato)=x(isti)
            yo(nato)=y(isti)
            zo(nato)=z(isti)
            anmo(nato)=atmnam(isti)
         endif
   40    continue
         if(nath.gt.0) then
            call msgou0(0,1,'warning(adhmol): some hydrogen atoms are at
     .tached. nothing is done. iatm1=$',iatm1)
            call msgout(0,1,' residue(molecule) name='//restmp//'$')
            go to 100
         endif
      endif
c     iatm2
      call strtok(maxc,temp,nc,temp1,mc)
      if(mc.le.0) then
         call msgou0(0,1,'warning(adhmol): missing atom 2. skiped.$',
     .       iatm1)
         call msgout(0,1,' residue(molecule) name='//restmp//'$')
         go to 100
      endif
      call strtoi(maxc,temp1,int)
      iatm2=int
c     iatm3
      call strtok(maxc,temp,nc,temp1,mc)
      if(mc.le.0) then
         call msgou0(0,1,'warning(adhmol): missing atom 3. skiped. atom1
     .=$',iatm1)
         call msgout(0,1,' residue(molecule) name='//restmp//'$')
         go to 100
      endif
      call strtoi(maxc,temp1,int)
      iatm3=int
      iatm1=iatm1+nadd0
      iatm2=iatm2+nadd0
      iatm3=iatm3+nadd0
      icis=1
      if(itype.eq.13) then
c        cis or trans for itype.eq.13
         call strtok(maxc,temp,nc,temp1,mc)
         if(mc.le.0) then
            call msgou0(0,1,'warning(adhmol): missing cis/trans data. tr
     .ans is assumed. atom1=$',iatm1)
            call msgout(0,1,' residue(molecule) name='//restmp//'$')
         else
            call strtoi(maxc,temp1,int)
            if(int.eq.0) icis=0
         endif
      endif
c
      ianh=1
      ian1=ian(iatm1)
      call lcvbnd(ianh,ian1,0,rstd,rmin,rmax,ifnd)
      rhx=rstd
      if(nc.gt.0) then
c        bond length
         call strtok(maxc,temp,nc,temp1,mc)
         call strtor(maxc,temp1,rinp)
         rhx=rinp
         ifnd=0
      endif
      if(ifnd.ne.0) then
         call msgou0(0,1,'warning(adhmol): missing h-x bond length. skip
     .ed. iatm1=$',iatm1)
         call msgout(0,1,' residue(molecule) name='//restmp//'$')
         go to 100
      endif
c
c     add hydrogen atoms
      iat1=iatm1-ist+1
      ip=iat1+nadd
      ianm=2
      nhatm=2
      call vecpk1(x(iatm1),y(iatm1),z(iatm1),x1,1)
      call vecpk1(x(iatm2),y(iatm2),z(iatm2),x2,1)
      call vecpk1(x(iatm3),y(iatm3),z(iatm3),x3,1)
      if(itype.eq.11) then
         nhatm=1
         ianm=1
         call add1a3(x1,x2,x3,xh1,rhx,1,icis)
      elseif(itype.eq.12) then
         nhatm=1
         ianm=1
         call add1a2(x1,x2,x3,xh1,rhx)
      elseif(itype.eq.13) then
         nhatm=1
         ianm=1
         call add1a3(x1,x2,x3,xh1,rhx,1,icis)
      elseif(itype.eq.21) then
         call add2a1(x1,x2,x3,xh1,xh2,rhx)
      elseif(itype.eq.22) then
         call add2a2(x1,x2,x3,xh1,xh2,rhx)
      elseif(itype.eq.31) then
         nhatm=3
         call add3a1(x1,x2,x3,xh1,xh2,xh3,rhx)
      else
c        error
         call msgou0(0,1,'warning(adhmol): wrong bond type. skipped. ato
     .m 1=$',iatm1)
         call msgout(0,1,' residue(molecule) name='//restmp//'$')
         go to 100
      endif
      if(nato+nhatm.gt.MaxRAT) go to 900
      call hadres(ip,nhatm,xh1,xh2,xh3,anm(ianm),
     .                                       nato,iano,xo,yo,zo,anmo)
c   80 continue
  100 continue
      go to 20
  500 continue
      if(nadd.gt.0) then
         call updres(ires,nato,iano,xo,yo,zo,anmo)
         natm=natm+nadd
      endif
c
      return
  900 call msgout(0,1,'error(adhmol):too many atoms/mol after addition o
     .f hydrogen atoms.$')
      call msgout(0,1,' residue(molecule) name='//restmp//'$')
      call msgou0(0,0,' recompile the program with larger MaxRAT. MaxRART
     .=$',MaxRAT)
      end
cs----------------------------------------------------------------------
      subroutine adhwat
c-----------------------------------------------------------------------
c     add h atoms to water molecules
c     ihkeep =0 keep original Hs, =1 replace with generated ones
c     note: ihkeep is not supported
ce----------------------------------------------------------------------
      dimension     iani(30),xi(30),yi(30),zi(30)
      character*4   anmi(30)
      character     restmp*6
      dimension     jatm(8),jatmh(8),iatmh(8),ra(3),rb(3)
c      dimension xh(20),yh(20),zh(20)
      character*4 anmh(20),anmht(20)
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      dimension x1(3),x2(3),x3(3),xh1(3),xh2(3)
      dimension x1t(3),x2t(3),x3t(3)
      dimension xr(3),yr(3),zr(3),xn(3),yn(3),zn(3),v(3,3)
      dimension xh1t(3),xh2t(3)
      data  woh/0.957/,whoh/104.5/,todeg/57.2968/
      save  woh,whoh,todeg
c
      do 200 ires=1,nres
c      call resid(resnam(ires),iresid,0,0)
      if(resnam(ires).ne.'wat'.and.resnam(ires).ne.'hoh') go to 200
c     nati,iani,xi,yi,zi excluding h atoms
      natt=istres(ires+1)-istres(ires)
      ist=istres(ires)
      nati=0
      nath=0
      do 40 i=1,natt
      isti=ist+i-1
      if(ian(isti).eq.1) then
         nath=nath+1
c         xh(nath)=x(isti)
c         yh(nath)=y(isti)
c         zh(nath)=z(isti)
         anmh(nath)=atmnam(isti)
         anmht(nath)=anmh(nath)
         call chcase(4,anmht(nath),1)
      else
         nati=nati+1
         iani(nati)=ian(isti)
         xi(nati)=x(isti)
         yi(nati)=y(isti)
         zi(nati)=z(isti)
         anmi(nati)=atmnam(isti)
      endif
   40 continue
      idummy=0
      call resiid(ires,idummy,restmp)
      if(nath.eq.2) then
         call msgout(0,1,'warning(adhwat): two hydrogen atoms are attach
     .ed. nothing is done.$')
         call msgout(0,1,' residue(water) name='//restmp//'$')
         go to 200
      elseif(nath.eq.1) then
         call msgout(0,1,'warning(adhwat): one hydrogen atom is attached
     .. nothing is done.$')
         call msgout(0,1,' residue(water) name='//restmp//'$')
         go to 200
      endif
c
      wang=whoh/todeg
c
      ist=istres(ires)
      ifnd=1
      do 100 i=1,nati
      iatm=ist+i-1
      if(ian(iatm).ne.8) go to 100
      if(ifnd.eq.0) go to 100
      call hbdlst(natm,ian,x,y,z,iatm,iatmh,njatm,jatm,jatmh,0)
      ifnd=0
      nati=nati+2
      iani(2)=1
      iani(3)=1
      anmi(2)=' h1 '
      anmi(3)=' h2 '
      x1t(1)=0.0
      x1t(2)=0.0
      x1t(3)=0.0
      if(njatm.eq.0) then
c        no electronegative atoms close to iatm
         xi(2)=x(iatm)
         yi(2)=y(iatm)
         zi(2)=z(iatm)+woh
         xi(3)=x(iatm)+woh*sin(wang)
         yi(3)=y(iatm)
         zi(3)=z(iatm)+woh*cos(wang)
         go to 80
      endif
      x1(1)=x(iatm)
      x1(2)=y(iatm)
      x1(3)=z(iatm)
      x2(1)=x(jatm(1))
      x2(2)=y(jatm(1))
      x2(3)=z(jatm(1))
      if(njatm.eq.1) then
         nat=2
c        H2O toward or opposite direction of H-bond partner
         r21=(x(jatm(1))-x(iatm))**2+(y(jatm(1))-y(iatm))**2+
     .       (z(jatm(1))-z(iatm))**2
         r21=sqrt(r21)
         x2t(1)=0.0
         x2t(2)=0.0
         x2t(3)=r21
         if(jatmh(1).eq.0) then
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=woh
            xh2t(1)=woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=woh*cos(wang)
         else 
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=-woh
            xh2t(1)=woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=-woh*cos(wang)
         endif
         go to 60
      endif
      x3(1)=x(jatm(2))
      x3(2)=y(jatm(2))
      x3(3)=z(jatm(2))
      if(njatm.ge.2) then
         nat=3
         r21=(x(jatm(1))-x(iatm))**2+(y(jatm(1))-y(iatm))**2+
     .       (z(jatm(1))-z(iatm))**2
         r21=sqrt(r21)
         r31=(x(jatm(2))-x(iatm))**2+(y(jatm(2))-y(iatm))**2+
     .       (z(jatm(2))-z(iatm))**2
         r31=sqrt(r31)
         call vector(x2,x1,ra,1,1)
         call vector(x3,x1,rb,1,1)
         call anglet(ra,rb,ang)
         x2t(1)=0.0
         x2t(2)=0.0
         x2t(3)=r21
         x3t(1)=r31*sin(ang)
         x3t(2)=0.0
         x3t(3)=r31*cos(ang)
         if(jatm(1).eq.0.and.jatm(2).eq.0) then
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=woh
            xh2t(1)=woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=woh*cos(wang)
         elseif(jatm(1).eq.0.and.jatm(2).ne.0) then
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=woh
            xh2t(1)=woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=woh*cos(wang)
         elseif(jatm(2).eq.0.and.jatm(1).ne.0) then
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=-woh
            xh2t(1)=-woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=-woh*cos(wang)
         else
            xh1t(1)=0.0
            xh1t(2)=0.0
            xh1t(3)=-woh
            xh2t(1)=-woh*sin(wang)
            xh2t(2)=0.0
            xh2t(3)=-woh*cos(wang)
         endif
      endif
   60 continue
      call vecpk1(xr(1),yr(1),zr(1),x1t,0)
      call vecpk1(xr(2),yr(2),zr(2),x2t,0)
      if(nat.eq.3) call vecpk1(xr(3),yr(3),zr(3),x3t,0)
      call vecpk2(xn(1),yn(1),zn(1),x1,x1,0)
      call vecpk2(xn(2),yn(2),zn(2),x2,x1,0)
      if(nat.eq.3) call vecpk2(xn(3),yn(3),zn(3),x3,x1,0)
      call rotvec(nat,xr,yr,zr,xn,yn,zn,v)
      call trcord(xh1,xh1t,x1,v)
      call trcord(xh2,xh2t,x1,v)
      xi(2)=xh1(1)
      yi(2)=xh1(2)
      zi(2)=xh1(3)
      xi(3)=xh2(1)
      yi(3)=xh2(2)
      zi(3)=xh2(3)
   80 continue
      call updres(ires,nati,iani,xi,yi,zi,anmi)
      natm=natm+2
  100 continue
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine adjfrg(ifrg,iadjs,iadjl)
c----------------------------------------------------------------------
c     return adjacent fragment of smaller size.
c     iadjs(l) is either ifrg-1 or ifrg+1.
c     iadjs is smaller than iadjl in size.
ce---------------------------------------------------------------------
      parameter (MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      if(ifrg.gt.nfrg) go to 900
c     size of ifrg-1 and ifrg+1 frag
      nsz1=0
      nrfi=nresfg(ifrg-1)
      do 40 i=1,nrfi
      ires=iresfg(i,ifrg-1)
      call resid(resnam(ires),iresid,0,0)
      nsz1=nsz1+iresiz(iresid)
   40 continue
      nsz2=0
      nrfj=nresfg(ifrg+1)
      do 80 i=1,nrfj
      ires=iresfg(i,ifrg+1)
      call resid(resnam(ires),iresid,0,0)
      nsz2=nsz2+iresiz(iresid)
   80 continue
      iadjs=ifrg+1
      iadjl=ifrg-1
      if(nsz2.gt.nsz1) then
         iadjs=ifrg-1
         iadjl=ifrg+1
      endif
c  200 continue
c
      return
  900 call msgout(0,0,'error(updfrg): ifrg .gt. nfrg.$')
      end
cs----------------------------------------------------------------------
      subroutine atmres(iatm,ires)
c-----------------------------------------------------------------------
c     find sequence number of res to which iatm belongs.
c     iatm ... seq. # of the atom in the whole system
c     ires ... seq. # of res to which the atom belongs
ce----------------------------------------------------------------------
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
c
      ires=0
      do 20 i=1,nres
      if(iatm.ge.istres(i).and.iatm.lt.istres(i+1)) then
         ires=i
         go to 40
      endif
   20 continue
   40 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine bakbon(natm,ian,x,y,z,in1,ic2,ic3,io4,ifnd)
c----------------------------------------------------------------------
c     find backborn atoms (N-C-C=O) of a residue
c     natm...number of atoms in the residue
c     ian,x,y,z... atomic number and coordinates of residure
c     in1,ic2,ic3,io4...seq. # of N,C,C and O
c     io5 ... is the extra O in C-terminus res.
c     ifnd...=0 NCCO is found, =1 not found
ce---------------------------------------------------------------------
      dimension ian(*),x(*),y(*),z(*)
      dimension lst1(8),lst2(8),lst3(8),io4tmp(8)
c
      ifnd=1
c
      i=0
   20 i=i+1
      if(ian(i).eq.7.and.ifnd.eq.1) then
c        N1
         in1=i
         call bndlst(natm,ian,x,y,z,in1,nbd1,lst1,0)
c             write(*,*) ' lst1 ',(lst1(ii),ii=1,nbd1)
         if(nbd1.le.0) go to 180
         do 160 j=1,nbd1
         jj=lst1(j)
         if(ian(jj).eq.6.and.ifnd.eq.1) then
c           C2
            ic2=jj
            call bndlst(natm,ian,x,y,z,ic2,nbd2,lst2,0)
c             write(*,*) ' lst2 ',(lst2(ii),ii=1,nbd2)
            if(nbd2.le.0) go to 150
            do 140 k=1,nbd2
            kk=lst2(k)
            if(ian(kk).eq.6.and.ifnd.eq.1) then
c              C3
               ic3=kk
               call bndlst(natm,ian,x,y,z,ic3,nbd3,lst3,0)
c                 write(*,*) ' lst3 ',(lst3(ii),ii=1,nbd3)
               if(nbd3.le.0) go to 130
               no4=0
               do 120 l=1,nbd3
c              possible two NCCO sequence in asp and glu
               ll=lst3(l)
               if(ian(ll).eq.8.and.ifnd.eq.1) then
c               O4
                  no4=no4+1
                  io4tmp(no4)=ll
               endif
  120          continue
c              if(no4.eq.1) then
                  io4=io4tmp(1)
                  ifnd=0
c              elseif(no4.eq.2) then
c                 it1=io4tmp(1)
c                 r1=sqrt((x(ic3)-x(it1))**2+(y(ic3)-y(it1))**2+
c    .                    (z(ic3)-z(it1))**2)
c                 it2=io4tmp(2)
c                 r2=sqrt((x(ic3)-x(it2))**2+(y(ic3)-y(it2))**2+
c    .                    (z(ic3)-z(it2))**2)
c                 io4=it1
c                 if(r2.lt.r1) then
c                    io4=it2
c                 endif
c                 ifnd=0
c              endif
  130          continue
            endif
  140       continue
  150       continue
         endif
  160    continue
  180    continue
      endif
      if(i.lt.natm.and.ifnd.ne.0) go to 20
c  200 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine bndang(iout,iba)
c-----------------------------------------------------------------------
c     print bond angles
c     iba ... 1: for all atoms, 2: only heavy atoms.
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4   atm1,atm2,atm3
      character*2   elm1,elm2,elm3
      dimension     ibdlst(8),ra(3),rb(3)
      data          todeg/57.29578/
      save          todeg
c
      write(iout,1000)
 1000 format(' Covalent Bond Angles',/,
     .'       #,   angle, elm i-j-k, ires,    iatm,   jres,    jatm,   k
     .res,     katm')
c
      kount=0
      do 100 ia=1,natm
      if(iba.eq.2.and.ian(ia).eq.1) go to 100
      call bndlst(natm,ian,x,y,z,ia,nbnd,ibdlst,0)
      if(nbnd.ge.2) then
         ia1=ia
         call atmres(ia1,ires)
         do 60 j=2,nbnd
         ia2=ibdlst(j)
         if(iba.eq.2.and.ian(ia2).eq.1) go to 60
         call atmres(ia2,jres)
         do 40 k=1,j-1
         kount=kount+1
         ia3=ibdlst(k)
         if(iba.eq.2.and.ian(ia3).eq.1) go to 40
         call atmres(ia3,kres)
         atm1=atmnam(ia1)
         call chcase(4,atm1,1)
         atm2=atmnam(ia2)
         call chcase(4,atm2,1)
         atm3=atmnam(ia3)
         call chcase(4,atm3,1)
         call elmian(elm1,ian(ia1),1)
         call elmian(elm2,ian(ia2),1)
         call elmian(elm3,ian(ia3),1)
         ra(1)=x(ia2)-x(ia1)
         ra(2)=y(ia2)-y(ia1)
         ra(3)=z(ia2)-z(ia1)
         rb(1)=x(ia3)-x(ia1)
         rb(2)=y(ia3)-y(ia1)
         rb(3)=z(ia3)-z(ia1)
         call anglet(ra,rb,teta)
         angle=teta*todeg
         write(iout,2000) kount,angle,elm2,elm1,elm3,jres,ia2,atm2,ires,
     .                    ia1,atm1,kres,ia3,atm3
 2000    format(i8,2x,f8.3,2x,a2,'-',a2,'-',a2,i5,i7,2x,a3,
     .          i5,i7,2x,a3,i5,i7,2x,a3)
   40    continue
   60    continue
      endif
  100 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine bndbdl(iout,ibl)
c-----------------------------------------------------------------------
c     print bond lengths
c     ibl ... 1:all atoms, 2:heavy atoms only.
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4   atmi,atmj
      character*2   elmi,elmj,elmt
c
      write(iout,1000)
 1000 format(' Covalent Bond Lengths',/,
     .'       #,    rij(A), elmij, ires,     iatm,  jres,     jatm')
c
      kount=0
      do 100 ia=2,natm
      if(ibl.eq.2.and.ian(ia).eq.1) go to 100
      do 80 ja=1,ia-1
      if(ibl.eq.2.and.ian(ja).eq.1) go to 80
      rij=(x(ia)-x(ja))**2+(y(ia)-y(ja))**2+(z(ia)-z(ja))**2
      if(rij.gt.6.25) go to 80
      rij=sqrt(rij)
      iani=ian(ia)
      ianj=ian(ja)
      call lcvbnd(iani,ianj,1,rstd,rmin,rmax,ifnd)
      if(rij.lt.rmax) then
         kount=kount+1
         call atmres(ia,ires)
         call atmres(ja,jres)
         atmi=atmnam(ia)
         call chcase(4,atmi,1)
         atmj=atmnam(ja)
         call chcase(4,atmj,1)
         call elmian(elmi,iani,1)
         call elmian(elmj,ianj,1)
         if(ianj.gt.iani) then
            elmt=elmi
            elmi=elmj
            elmj=elmt
         endif
         write(iout,2000) kount,rij,elmi,elmj,ires,ia,atmi,jres,ja,atmj
 2000    format(i8,2x,f10.6,2x,a2,'-',a2,i4,i8,2x,a3,i4,i8,2x,a3)
      endif
   80 continue
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine bndlst(natm,ian,x,y,z,iatm,nbnd,ibdlst,key)
c----------------------------------------------------------------------
c     find bonding atoms of iatm
c     ian(i)=0 atoms are skiped
c     natm,ian,x,y,z...number of atoms, atomic number and x,y,z coord.
c     nbnd...number of bonds
c     ibdlst...bonding atom number list of iatm
c     key...=0 search all atoms, =1 search only i > iatm
ce---------------------------------------------------------------------
      dimension ian(*),x(*),y(*),z(*),ibdlst(*)
c
      nbnd=0
      ian1=ian(iatm)
      x1=x(iatm)
      y1=y(iatm)
      z1=z(iatm)
      ist=1
      if(key.eq.1) ist=iatm+1
      do 40 j=ist,natm
      if(j.eq.iatm) go to 40
      if(ian(j).eq.0) go to 40
      ian2=ian(j)
      rij=(x1-x(j))**2+(y1-y(j))**2+(z1-z(j))**2
c     if rij**2 is larger than (2.5)**2, skip
      if(rij.gt.(2.5*2.5)) go to 40
      rdum=0.0
      call lcvbnd(ian1,ian2,0,rdum,rmin,rmax,ifnd)
      if(ifnd.ne.0) go to 900
      if(rij.lt.rmax*rmax) then
         nbnd=nbnd+1
         ibdlst(nbnd)=j
      endif
   40 continue
      return
c     error exit
  900 call msgout(0,1,'error(bndlst): rmin, rmax are not given for i and
     . j atoms.$')
      call msgou0(0,1,' atomic number of i=$',ian1)
      call msgou0(0,0,' atomic number of j=$',ian2)
      end
cs----------------------------------------------------------------------
      subroutine capntm(inprot,iresid,ihpos,nato,iano,xo,yo,zo,anmo)
c-----------------------------------------------------------------------
c     add h's at n-terminus
ce----------------------------------------------------------------------
      dimension iano(30),xo(30),yo(30),zo(30)
      character*4 anmo(30),anmh(3)
      dimension x1(3),x2(3),x3(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension lst1(8)
c
      rdum1=0.0
      rdum2=0.0
         if(ihpos.eq.0) then
            ip=0
         else
            ip=1
         endif
c
         idel=0
         iat1=1
         call bndlst(nato,iano,xo,yo,zo,iat1,nbnd1,lst1,0)
         iat2=lst1(1)
         iat3=lst1(2)
         if(iresid.ne.7) then
            idel=iat2
            if(iano(idel).ne.1) then
               idel=iat3
ccc               if(iano(idel).ne.1) go to ??? error
            endif
            k=0
            do 120 i=1,nato
            if(i.eq.idel) go to 120
            k=k+1
            iano(k)=iano(i)
            xo(k)=xo(i)
            yo(k)=yo(i)
            zo(k)=zo(i)
            anmo(k)=anmo(i)
  120       continue
            nato=nato-1
         endif
         call bakbon(nato,iano,xo,yo,zo,in1,ic2,ic3,io4,ifnd)
         anmh(1)=' h1 '
         anmh(2)=' h2 '
         anmh(3)=' h3 '
         if(inprot.eq.0) then
c           add three h's at N to make NH3 terminus (except PRO)
            if(iresid.ne.7) then
               nhatm=3
               call vecpk1(xo(in1),yo(in1),zo(in1),x1,1)
               call vecpk1(xo(ic2),yo(ic2),zo(ic2),x2,1)
               call vecpk1(xo(ic3),yo(ic3),zo(ic3),x3,1)
               call lcvbnd(1,7,1,rn1h,rdum1,rdum2,ifnd)
               call add3a1(x1,x2,x3,xh1,xh2,xh3,rn1h)
               call hadres(ip,nhatm,xh1,xh2,xh3,anmh,
     .                                       nato,iano,xo,yo,zo,anmo)
            else
c              pro is special
               nhatm=2
               call vecpk1(xo(iat1),yo(iat1),zo(iat1),x1,1)
               call vecpk1(xo(iat2),yo(iat2),zo(iat2),x2,1)
               call vecpk1(xo(iat3),yo(iat3),zo(iat3),x3,1)
               call lcvbnd(1,7,1,rn2h,rdum1,rdum2,ifnd)
               call add2a1(x1,x2,x3,xh1,xh2,rn1h)
               call hadres(ip,nhatm,xh1,xh2,xh3,anmh,
     .                                        nato,iano,xo,yo,zo,anmo)
            endif
         else
c           add two h's at N to make NH2 terminus
            if(iresid.ne.7) then
               nhatm=2
               call vecpk1(xo(in1),yo(in1),zo(in1),x1,1)
               call vecpk1(xo(ic2),yo(ic2),zo(ic2),x2,1)
               call vecpk1(xo(ic3),yo(ic3),zo(ic3),x3,1)
               call lcvbnd(1,7,2,rn2h,rdum1,rdum2,ifnd)
               call add2a2(x1,x2,x3,xh1,xh2,rn2h)
               call hadres(ip,nhatm,xh1,xh2,xh3,anmh,
     .                                        nato,iano,xo,yo,zo,anmo)
            else
c              for pro
               nhatm=1
               call vecpk1(xo(iat1),yo(iat1),zo(iat1),x1,1)
               call vecpk1(xo(iat2),yo(iat2),zo(iat2),x2,1)
               call vecpk1(xo(iat3),yo(iat3),zo(iat3),x3,1)
               call lcvbnd(1,7,2,rn1h,rdum1,rdum2,ifnd)
               call add1a2(x1,x2,x3,xh1,rn1h)
               call hadres(ip,nhatm,xh1,xh2,xh3,anmh,
     .                                        nato,iano,xo,yo,zo,anmo)
            endif
         endif
c
      return
      end
cs----------------------------------------------------------------------
      subroutine capctm(nato,iano,xo,yo,zo,anmo)
c-----------------------------------------------------------------------
c     cap at c-terminus
ce----------------------------------------------------------------------
      dimension iano(30),xo(30),yo(30),zo(30)
      character*4 anmo(30),anmh(3)
      dimension x1(3),x2(3),x3(3)
      dimension xh1(3),xh2(3),xh3(3)
      dimension lst1(8)
c
ccc   if(ihpos.eq.0) then
ccc      ip=0
ccc   else
         ip=nato
ccc   endif
c   
      iat1=1
c     the last atom is O of NCOO
      iat1=nato
      call bndlst(nato,iano,xo,yo,zo,iat1,nbnd1,lst1,0)
      i1=iat1
      i2=lst1(1)
c      if(iano(i2).ne.6) go to error
      i3=lst1(2)
cdebug
c      write(2,*) ' nbnd1,i1,i2,i3 ',nbnd1,i1,i2,i3
      iat1=i2
      call bndlst(nato,iano,xo,yo,zo,iat1,nbnd1,lst1,0)
      i3=lst1(1)
      if(iano(i3).ne.8) then
        i3=lst1(2)
cdebug
c            write(2,*) ' nbnd1,i1,i2,i3 ',nbnd1,i1,i2,i3
c???          error     if(iano(i3).ne.8) go to xxxx
      endif
c
      nhatm=1
      call vecpk1(xo(i1),yo(i1),zo(i1),x1,1)
      call vecpk1(xo(i2),yo(i2),zo(i2),x2,1)
      call vecpk1(xo(i3),yo(i3),zo(i3),x3,1)
      call lcvbnd(1,8,2,ro2h,rdum1,rdum2,ifnd)
      call add1a3(x1,x2,x3,xh1,ro2h,0,0)
      anmh(1)=' ho '
      call hadres(ip,nhatm,xh1,xh2,xh3,anmh,
     .                               nato,iano,xo,yo,zo,anmo)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine catfil(in,iunit,inpfil,nfil,filnam)
c-----------------------------------------------------------------------
c     cat files filnam to inpfil
ce----------------------------------------------------------------------
      character*80 inpfil,filnam(*)
      character*80 temp,temp1
      data maxc/80/
      save maxc
c
      open (iunit,file=inpfil,form='formatted',status='unknown')
      do 100 i=1,nfil
      open (in,file=filnam(i),form='formatted',status='old')
      rewind in
   20 continue
      read(in,1000,end=40) temp
 1000 format(a80)
      temp1=temp
      call chcase(maxc,temp1,0)
      if(temp1(1:3).eq.'end') go to 20
      write(iunit,1000) temp
      go to 20
   40 continue
      close(in)
  100 continue
      close(iunit)
      return
      end
cs---------------------------------------------------------------------
      subroutine chcase(nc,str,key)
c----------------------------------------------------------------------
c     CHCASE: change letter case
c     key = 0 change upper case to lower case.
c         = 1 change lower case to upper case.
ce---------------------------------------------------------------------
      character*1 str(nc)
c     character*(*) str(nc)
c
      if(key.eq.0) then
c        upper to lower
         do 20 i=1,nc
         ic=ichar(str(i))
         if(ic.ge.65.and.ic.le.90) str(i)=char(ic+32)
   20    continue
      else
c        lower to upper
         do 40 i=1,nc
         ic=ichar(str(i))
         if(ic.ge.97.and.ic.le.122) str(i)=char(ic-32)
   40    continue
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine chgres
c----------------------------------------------------------------------
c     assign charges to residues
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
c     charge of residue
      do 200 i=1,nres
      call resid(resnam(i),iresid,0,0)
      call resmol(i,imol,ifres,ilres)
      iterm=0
      if(ifres.eq.i) iterm=1
      if(ilres.eq.i) iterm=2
      if(iresid.ne.0) then
        ist=istres(i)
        nati=istres(i+1)-ist
        call reschg(iresid,iterm,nati,ian(ist),icharg,ierr)
        if(ierr.eq.1) then
           call msgout(0,1,'! warning(chgres): wrong chemical formula.$'
     .)
           call msgou0(0,1,'! residue number=$',i)
           ichres(i)=0
        else
           ichres(i)=icharg
        endif
      else
         if(resnam(i).ne.'wat'.and.resnam(i).ne.'hoh'.
     .         and.resnam(i).ne.'ace'.and.resnam(i).ne.'nme') then
            ichres(i)=0
            call msgout(0,1,'! warning(chgres): non-peptide residue. set
     . correct charge.$')
            call msgou0(0,1,'! residue number=$',i)
         endif
      endif
      if(iresid.eq.16.and.iterm.ne.0) then
         call msgout(0,1,'! warning(chgres): cys at N- or C-terminus. fa
     .iled to assign charge.$')
      endif
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine chmfr1(nat,ian,nc,nh,nn,no,ns,nx,nele)
c----------------------------------------------------------------------
c     return number of elements, C,H,N,O,S,and others, 
c     and number of electrons
ce---------------------------------------------------------------------
      dimension ian(*)
c
c     stoichiometry from ian
      nele=0
      nc=0
      nh=0
      no=0
      nn=0
      ns=0
      nx=0
      do 100 i=1,nat
      nele=nele+ian(i)
      if(ian(i).eq.6) then
         nc=nc+1
      elseif(ian(i).eq.1) then
         nh=nh+1
      elseif(ian(i).eq.7) then
         nn=nn+1
      elseif(ian(i).eq.8) then
         no=no+1
      elseif(ian(i).eq.16) then
         ns=ns+1
      else
         nx=nx+1
      endif
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine cnint(maxc,int,nf,temp)
c----------------------------------------------------------------------
c     convert an integer (int) to characters 
c     int ... integer number
c     nf  ... number of output characters. if fig of int is less than nf
c             '0' is(are) supplied
c     temp ... output string
ce---------------------------------------------------------------------
      character*1 temp(maxc)
      character*1 czero
      data czero/'0'/
      save czero
c
      call stri2c(maxc,int,temp,ifg)
c      write(*,*) ' temp ',(temp(i),i=1,ifg)
      if(nf.gt.ifg) then
         nn=nf-ifg
         call strsft(maxc,temp,-nn)
         do 20 i=1,nn
         temp(i)=czero
   20    continue
      endif
c      write(*,*) ' temp ',(temp(i),i=1,nf)
      return
      end
cs---------------------------------------------------------------------
      subroutine cnters(nresid,nrest,nace,nnme,nwater,nonres)
c----------------------------------------------------------------------
c     count number of each residue
ce---------------------------------------------------------------------
      dimension nresid(*)
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
c      
      nrest=0
      nace=0
      nnme=0
      nwater=0
      nonres=0
      do 20 i=1,20
   20 nresid(i)=0
      do 40 i=1,nres
      call resid(resnam(i),iresid,0,0)
      if(iresid.ne.0) then
         nresid(iresid)=nresid(iresid)+1
         nrest=nrest+1
      else
         if(resnam(i).eq.'wat'.or.resnam(i).eq.'hoh') then
            nwater=nwater+1
         elseif(resnam(i).eq.'ace') then
            nace=nace+1
         elseif(resnam(i).eq.'nme') then
            nnme=nnme+1
         else
            nonres=nonres+1
         endif
      endif
   40 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine cntatm(natall,nhatom,n2atom,nsiatm,key)
c----------------------------------------------------------------------
c     count number of atoms(natall), of H(nhatom), 2nd row atoms(n2atom),
c     and of Si atom (nsiatm).
c     key=0 in residures only, key=1 in whole system.
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c      
      nhatom=0
      n2atom=0
      nsiatm=0
      natall=0
      if(key.eq.0) then
         do 40 i=1,nres
         call resid(resnam(i),iresid,0,0)
         if(iresid.eq.0) go to 40
         ist=istres(i)
         ied=istres(i+1)-1
         do 20 j=ist,ied
         natall=natall+1
         if(ian(j).ge.11.and.ian(j).le.18) n2atom=n2atom+1
   20    if(ian(j).eq.1) nhatom=nhatom+1
   40    continue
      else
         do 140 i=1,natm
         if(ian(i).eq.1) nhatom=nhatom+1
         if(ian(i).ge.11.and.ian(i).le.18) n2atom=n2atom+1
         if(ian(i).eq.14) nsiatm=nsiatm+1
  140    continue
         natall=natm
      endif
      return
      end
cs---------------------------------------------------------------------
      subroutine cntres(nrest,namino,nonres)
c----------------------------------------------------------------------
c     count number of residues and non-peptide molecules
ce---------------------------------------------------------------------
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
c      
      namino=0
      nonres=0
      do 40 i=1,nres
      call resid(resnam(i),iresid,0,0)
      if(iresid.ne.0) namino=namino+1
   40 if(iresid.eq.0) nonres=nonres+1
      nrest=namino+nonres
      return
      end
cs---------------------------------------------------------------------
      subroutine defpdb(label)
c----------------------------------------------------------------------
c     define pdb labels
c     label 1:atom,2:hetatm,3:conect,4:end,5:ter,6:seqres,7:helix,8:sheet,
c           9:title,10:link,11:remark
ce---------------------------------------------------------------------
      character*6   label(20)
      label( 1) = 'atom '
      label( 2) = 'hetatm'
      label( 3) = 'conect'
      label( 4) = 'end   '
      label( 5) = 'ter   '
      label( 6) = 'seqres'
      label( 7) = 'herix '
      label( 8) = 'sheet '
      label( 9) = 'title '
      label(10) = 'link  '
      label(11) = 'remark'
c
      return
      end
cs---------------------------------------------------------------------
      subroutine defres
c----------------------------------------------------------------------
c     set res names in common/reslab/
c     1:GLY(G), 2:ALA(A), 3:VAL(V), 4:PHE(F), 5:ILE(I), 6:LEU(L), 7:PRO(P), 
c     8:MET(M), 9:ASP(D),10:GLU(E),11:LYS(K),12:ARG(R),13:SER(S),14:THR(T),
c     15:TYR(Y),16:CYS(C),17:ASN(N),18:GLU(Q),19:HIS(H),20:TRP(W)
ce---------------------------------------------------------------------
      character resnm3*3,resnm1*1
      common/reslab/kres,resnm3(20),resnm1(20)
c
      kres=20
      resnm3( 1)='gly'
      resnm3( 2)='ala'
      resnm3( 3)='val'
      resnm3( 4)='phe'
      resnm3( 5)='ile'
      resnm3( 6)='leu'
      resnm3( 7)='pro'
      resnm3( 8)='met'
      resnm3( 9)='asp'
      resnm3(10)='glu'
      resnm3(11)='lys'
      resnm3(12)='arg'
      resnm3(13)='ser'
      resnm3(14)='thr'
      resnm3(15)='tyr'
      resnm3(16)='cys'
      resnm3(17)='asn'
      resnm3(18)='gln'
      resnm3(19)='his'
      resnm3(20)='trp'
c
      resnm1( 1)='g'
      resnm1( 2)='a'
      resnm1( 3)='v'
      resnm1( 4)='f'
      resnm1( 5)='i'
      resnm1( 6)='l'
      resnm1( 7)='p'
      resnm1( 8)='m'
      resnm1( 9)='d'
      resnm1(10)='e'
      resnm1(11)='k'
      resnm1(12)='r'
      resnm1(13)='s'
      resnm1(14)='t'
      resnm1(15)='y'
      resnm1(16)='c'
      resnm1(17)='n'
      resnm1(18)='q'
      resnm1(19)='h'
      resnm1(20)='w'
c
      return
      end
cs----------------------------------------------------------------------
      subroutine dumyco(ires,nati,iani,xi,yi,zi,xco,yco,zco,
     .                                     key,ierr)
c-----------------------------------------------------------------------
c     add dummy C=O for N-terminus
c     key=0 the first residue, =1 not the first and nres .gt. 1
ce----------------------------------------------------------------------
      dimension iani(*),xi(*),yi(*),zi(*)
      dimension xco(*),yco(*),zco(*)
      dimension x1(3),x2(3),x3(3)
      dimension xh1(3),xh2(3)
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      rdum1=0.0
      rdum2=0.0
      if(key.eq.0) then
         call bakbon(nati,iani,xi,yi,zi,in1,ic2,ic3,io4,ifnd)
c        C
         call vecpk1(xi(in1),yi(in1),zi(in1),x1,1)
         call vecpk1(xi(ic2),yi(ic2),zi(ic2),x2,1)
         call vecpk1(xi(ic3),yi(ic3),zi(ic3),x3,1)
         call lcvbnd(6,7,1,rc1n,rdum1,rdum2,ifnd)
         call add1a3(x1,x2,x3,xh1,rc1n,1,1)
         call vecpk1(xco(1),yco(1),zco(1),xh1,0)
c        O
         call vecpk1(xi(in1),yi(in1),zi(in1),x2,1)
         call vecpk1(xi(ic2),yi(ic2),zi(ic2),x3,1)
         call lcvbnd(6,8,2,rc2o,rdum1,rdum2,ifnd)
         call add1a3(xh1,x2,x3,xh2,rc2o,1,0)
         call vecpk1(xco(2),yco(2),zco(2),xh2,0)
      elseif(key.eq.1) then
ccc        if(nres.gt.1) then
c           pick up C=O of (ires-1) res and store in xco,yco,zco
c           set tempolally (ires-1) coord to natt,iano,xo,yo,zo
            natt=istres(ires)-istres(ires-1)
            ist=istres(ires-1)
            call bakbon(natt,ian(ist),x(ist),y(ist),z(ist),
     .                       int1,ict2,ict3,iot4,ifnd)
            imc3=istres(ires-1)+ict3-1
            imo4=istres(ires-1)+iot4-1
            xco(1)=x(imc3)
            yco(1)=y(imc3)
            zco(1)=z(imc3)
            xco(2)=x(imo4)
            yco(2)=y(imo4)
            zco(2)=z(imo4)
ccc         endif
      endif
      ierr=ifnd
c
      return
      end
cs---------------------------------------------------------------------
      subroutine elmchr(elm,ielm)
c----------------------------------------------------------------------
c     check the number of character of element name, elm.
c     ielm=1 for 1-character, =2 2-character
ce---------------------------------------------------------------------
      character*2 elm
      character*2 twochr(43)
      data twochr/'li','be','na','mg','al','si','cl','ar','ti',
     .            'cr','mn','fe','co','ni','cu','zn','ga','ge','as',
     .            'se','br','kr','rb','sr','zr','nb','mo','tc','ru',
     .            'rh','pd','ag','in','te','xe','cs','ba','hf','ta',
     .            're','os','ir','pt'/
      data ntwo/43/
      save twochr,ntwo
c
      ielm=1
      do 20 i=1,ntwo
      if(elm.eq.twochr(i)) ielm=2
   20 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine elmian(elem,ian,key)
c----------------------------------------------------------------------
c     covert element name <-> atomic number
c     key=0 element name(elem)  -> atomic number(ian)
c     key=1 atomic number(ian)  -> element name(elem) in upper case
c     key=2 atomic number(ian)  -> element name(elem) in mixed case
c     key=3 atomic number(ian)  -> element name(elem) in lower case
ce---------------------------------------------------------------------
      character*2 elem,elmtmp
      character*2 satm(103)
      data satm  /'h ','he','li','be','b ','c ','n ','o ','f ','ne',
     .            'na','mg','al','si','p ','s ','cl','ar','k ','ca',
     .            'sc','ti','v ','cr','mn','fe','co','ni','cu','zn',
     .            'ga','ge','as','se','br','kr','rb','sr','y ','zr',
     .            'nb','mo','tc','ru','rh','pd','ag','cd','in','sn',
     .            'sb','te','i ','xe','cs','ba','la','ce','pr','nd',
     .            'pm','sm','eu','gd','tb','dy','ho','er','tm','yb',
     .            'lu','hf','ta','w ','re','os','ir','pt','au','hg',
     .            'tl','pb','bi','po','at','rn','fr','ra','ac','th',
     .            'pa','u ','np','pu','am','cm','bk','cf','es','fm',
     .            'md','no','lr'/
      data         maxsbl/103/
c
      if(key.eq.0) then
         elmtmp=elem
         call chcase(2,elmtmp,0)
         do 100 i=1,maxsbl
  100    if(elmtmp.eq.satm(i)) go to 200
         go to 900
  200    ian=i
      else
         if(ian.gt.103) go to 910
         elmtmp=satm(ian)
      endif
      if(key.eq.1) then
         call chcase(2,elmtmp,1)
         elem=elmtmp
      elseif(key.eq.2) then
         call chcase(1,elmtmp(1:1),1)
         elem=elmtmp
      elseif (key.eq.3) then
         elem=elmtmp
      endif
c
      return
c     error exit
  900 call msgout(0,1,'error(elmian): wrong element names. elem=$')
      call msgout(0,0,elem//'$')
  910 call msgout(0,1,'error(elmian): wrong atomic number.$')
      call msgou0(0,0,' ian=$',ian)
      end
cs---------------------------------------------------------------------
      subroutine fmobnd(iout,nbas,basnam)
c----------------------------------------------------------------------
c     print link atoms between fragments. $FMOBND data
ce---------------------------------------------------------------------
      character*10 basnam(*)
      parameter (MaxFrg=50000)
      common/lnkinf/nlnk,nldum,ialnk(MaxFrg),jalnk(MaxFrg)
c
c     bond data
      do 400 i=1,nlnk
      iat1=ialnk(i)
      iat2=jalnk(i)
      iat1=-iat1
      write(iout,3600) iat1,iat2,(basnam(j),j=1,nbas)
 3600 format(i8,i6,2x,5(a10,2x))
  400 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine fmohyb(ian,basnam,nbas,norb,isela,iselb,orb,ierr)
c----------------------------------------------------------------------
c     return hybrid orbitals
ce---------------------------------------------------------------------
      character*10  basnam
      character*10  basdef(12)
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      data basdef/'STO-3G    ',
     .         '3-21G     ','3-21+G    ','3-21G*    ','3-21+G*   ',
     .         '6-31G     ','6-31+G    ','6-31G*    ','6-31+G*   ',
     .         '6-31++G*  ','6-311G*   ','MINI      '/
      data mhyb/12/
      save basdef,mhyb
c    
      ierr=0
      if(ian.ne.6) go to 910
c
      do 20 i=1,mhyb
      if(basnam.eq.basdef(i)) go to 40
   20 continue
      go to 900
   40 ibas=i
c
c     STO-3G
      if(ibas.eq.1) call hsto(nbas,norb,isela,iselb,orb)
c     MINI
      if(ibas.eq.12) call hmini(nbas,norb,isela,iselb,orb)
c     3-21G
      if(ibas.eq.2) call h321a(nbas,norb,isela,iselb,orb)
c     3-21+G
      if(ibas.eq.3) call h321b(nbas,norb,isela,iselb,orb)
c     3-21G*
c      if(ibas.eq.4) call h321c(nbas,norb,isela,iselb,orb)
c     3-21+G*
c      if(ibas.eq.5) call h321d(nbas,norb,isela,iselb,orb)
c     6-31G
      if(ibas.eq.6) call h631a(nbas,norb,isela,iselb,orb)
c     6-31+G
c      if(ibas.eq.7) call h631b(nbas,norb,isela,iselb,orb)
c     6-31G*
      if(ibas.eq.8) call h631c(nbas,norb,isela,iselb,orb)
c     6-31+G*
c      if(ibas.eq.9) call h631d(nbas,norb,isela,iselb,orb)
c     6-31++G**
      if(ibas.eq.10) call h631g(nbas,norb,isela,iselb,orb)
c     6-311G*
      if(ibas.eq.11) call h6311a(nbas,norb,isela,iselb,orb)
c
      if(nbas.eq.0) go to 900
c
c     debug
c     write(*,*) ' ian:    ',ian
c     write(*,*) ' basnam: ',basnam
c     write(*,*) ' nbas:   ',nbas
c     write(*,*) ' norb:   ',norb
c     write(*,*) ' isela:  ',(isela(i),i=1,norb)
c     write(*,*) ' iselb:  ',(iselb(i),i=1,norb)
c     do 100 i=1,norb
c     write(*,*) ' hybrid orbital i =',i
c     write(*,1000) (orb(j,i),j=1,nbas)
c1000 format(5f12.6)
c 100 continue
c
      return
c     error exit
  900 call msgout(0,1,'error(fmohyb): hybrid orbitals are not found.$')
      call msgout(0,1,basnam//'$')
      call msgout(0,1,'Please make the hybrid orbitals from NLMOs.$')
      ierr=1
      return
  910 call msgout(0,1,'error(fmohyb): the atom is not found.$')
      call msgou0(0,1,' ian=$',ian)
      call msgout(0,1,'Please make the hybrid orbitals from NLMOs.$')
      ierr=1
      return
      end
cs---------------------------------------------------------------------
      subroutine fmoind(iout)
c----------------------------------------------------------------------
c     $fmo indata data
c     key =0 normal output, =1 normal+check
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      common/lnkinf/nlnk,nldum,ialnk(MaxFrg),jalnk(MaxFrg)
ckk   dimension lstfss(20)
      dimension lstfss(2000)
      data maxfss/2000/
c
      idum1=0
      idum2=0
      idum4=0
      idum5=0
      write(iout,1200)
 1200 format(6x,'indat(1)= 0')
      do 20 i=1,natm
   20 iatfrg(i)=0
c
      nlnk=0
      do 200 ifrg=1,nfrg
      call frgmol(ifrg,imol,istf,iedf)
      nrf=nresfg(ifrg)
      ifpep=0
      ifss=1
      ncys=0
c     peptide and ss bond ?
      do 40 i=1,nrf
      j=iresfg(i,ifrg)
      call resid(resnam(j),id,0,0)
      if(id.eq.16) then
         ncys=ncys+1
         if(ncys.gt.maxfss) go to 940
         lstfss(ncys)=j
      endif
   40 if(id.eq.0.and.(resnam(j).ne.'ace'.and.resnam(j).ne.'nme'))
     .      ifpep=1
c
      if(ncys.gt.1) then
         do 60 i=2,ncys
         do 60 j=1,i-1
         ii=lstfss(i)
         jj=lstfss(j)
         call ssbond(ii,jj,iss)
         if(iss.eq.0) ifss=0
   60    continue
      endif
      if(ifpep.eq.1) then
c        non-peptide frag
         j=iresfg(1,ifrg)
         ia3=istres(j)
         j=iresfg(nrf,ifrg)
         ia6=istres(j+1)-1
         call indata(iout,ifrg,1,0,idum1,idum2,ia3,idum4,idum5,ia6)
      else
c        peptide frag
         if(ifss.eq.1) then
            if(ifrg.eq.iedf.and.resnam(iresfg(nrf,ifrg)).eq.'nme') then
               j=iresfg(1,ifrg)
               ia3=istres(j)
               j=iresfg(nrf,ifrg)
               ia6=istres(j+1)-1
               ifnd=0
            else
               call frgatm(ifrg,ia3,ia4,ia5,ia6,ifnd)
            endif
         else
            call fssatm(ifrg,ia3,ia4,ia5,ia6,
     .                       ja3,ja4,ja5,ja6,jres,ifnd)
         endif
         if(ifnd.ne.0) go to 900
c
         if(ifrg.eq.istf) then
c           the first fragment in imol
            if(ifss.eq.1) then
               call indata(iout,ifrg,2,0,idum1,idum2,ia3,ia4,ia5,ia6)
            else
               call indata(iout,ifrg,2,1,idum1,idum2,ia3,ia4,ia5,ia6)
               call indata(iout,ifrg,2,0,idum1,idum2,ja3,ja4,ja5,ja6)
            endif
         elseif(ifrg.eq.iedf) then
c           the last frag of imol
            if(ifss.eq.1) then
               iresf=iresfg(1,ifrg)
               call rescco(iresf-1,icalp1,icat1,ioat1,ifnd)
               if(ifnd.ne.0) go to 920
               ia1=icat1
               ia2=ioat1
               nlnk=nlnk+1
               ialnk(nlnk)=icalp1
               jalnk(nlnk)=ia1
               call indata(iout,ifrg,3,0,ia1,ia2,ia3,ia4,ia5,ia6)
            else
               go to 960
            endif
         else
c           the frag in middle
            if(ifss.eq.1) then
               iresf=iresfg(1,ifrg)
               call rescco(iresf-1,icalp1,icat1,ioat1,ifnd)
               if(ifnd.ne.0) go to 920
               ia1=icat1
               ia2=ioat1
               nlnk=nlnk+1
               ialnk(nlnk)=icalp1
               jalnk(nlnk)=ia1
               call indata(iout,ifrg,4,0,ia1,ia2,ia3,ia4,ia5,ia6)
            else
               iresf=iresfg(1,ifrg)
               call rescco(iresf-1,icalp1,icat1,ioat1,ifnd)
               if(ifnd.ne.0) go to 920
               ia1=icat1
               ia2=ioat1
               nlnk=nlnk+1
               ialnk(nlnk)=icalp1
               jalnk(nlnk)=ia1
               call indata(iout,ifrg,4,1,ia1,ia2,ia3,ia4,ia5,ia6)
               iresf=jres
               call rescco(iresf-1,icalp1,icat1,ioat1,ifnd)
               if(ifnd.ne.0) go to 920
               ja1=icat1
               ja2=ioat1
               nlnk=nlnk+1
               ialnk(nlnk)=icalp1
               jalnk(nlnk)=ja1
               call indata(iout,ifrg,4,0,ja1,ja2,ja3,ja4,ja5,ja6)
            endif
         endif
      endif
  200 continue
c
cdebug
c      write(iout,*) ' fmoind iatfrg '
c      do 222 i=1,natm
c  222 write(iout,2222) i,iatfrg(i)
c 2222 format(2i8)
c
      return
  900 call msgout(0,1,'error(fmoind): failed to find NCCO.$')

       write(*,*) ifrg, frgnam(ifrg)

      call msgou0(0,0,' fragment number=$',ifrg)

  920 call msgout(0,1,'error(fmoind): failed to find CO(NCCO).$')
      call msgou0(0,0,' residue number=$',iresf-1)
  940 call msgout(0,0,'error(fmoind): too many s-s bonds/frg. max=20.$')
  960 call msgout(0,1,'warning(fmoind): s-s cys is at the last in molecu
     .le.$')
      call msgout(0,1,' I can not make indat data in this case.$')
      end
cs---------------------------------------------------------------------
      subroutine fmolmo(iout,ian,basnam)
c----------------------------------------------------------------------
c     print hybrid orbitals
ce---------------------------------------------------------------------
      character*10  basnam
      character*80  line,line1
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      data maxc/80/
c     
      call fmohyb(ian,basnam,nbas,norb,isela,iselb,orb,ierr)
      if(ierr.ne.0) go to 900
c
      write(iout,1200) basnam,nbas,norb
 1200 format(2x,a10,2i4)
c
      idgt=6
c
      n=nbas/5
      ns=mod(nbas,5)
      nt=5
      if(n.eq.0) nt=ns
      do 200 k=1,norb
      call strcle(maxc,line)
      call stri2c(maxc,isela(k),line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//line1(1:ifig)
      call stri2c(maxc,iselb(k),line1,ifig)
      call strlas(maxc,line,nc)
      nc=nc+1
      line=line(1:nc)//line1(1:ifig)
      ibs=0
      do 40 i=1,nt
      ibs=ibs+1
      val=orb(ibs,k)
      call strr2c(maxc,val,line1,ifig,idgt)
      
cdebug
c      write(*,*) ' ibs,k,ifig,idgt,val ',ibs,k,ifig,idgt,val
c      write(*,*) ' line1 ',line1
c
      call strlas(maxc,line,nc)
      if(val.ge.0.0) then
         line=line(1:nc)//'   '//line1(1:ifig)
      else
         line=line(1:nc)//'  '//line1(1:ifig)
      endif
   40 continue
      call strsft(maxc,line,-3)
      call prtstr(iout,maxc,line)
      if(n.le.0) go to 200
      do 100 i=1,n-1
      call strcle(maxc,line)
      do 80 j=1,5
      ibs=ibs+1
      val=orb(ibs,k)
      call strr2c(maxc,val,line1,ifig,idgt)
      call strlas(maxc,line,nc)
      if(val.ge.0.0) then
         line=line(1:nc)//'   '//line1(1:ifig)
      else
         line=line(1:nc)//'  '//line1(1:ifig)
      endif
      call strlas(maxc,line,nc)
   80 continue
      call strsft(maxc,line,-6)
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
  100 continue
c
c       write(*,*) ' ns for icharg ',ns
      call strcle(maxc,line)
      if(ns.eq.0) go to 200
      do 180 i=1,ns
      ibs=ibs+1
      val=orb(ibs,k)
      call strr2c(maxc,val,line1,ifig,idgt)
      call strlas(maxc,line,nc)
      if(val.ge.0.0) then
         line=line(1:nc)//'   '//line1(1:ifig)
      else
         line=line(1:nc)//'  '//line1(1:ifig)
      endif
  180 continue
      call strsft(maxc,line,-6)
      call prtstr(iout,maxc,line)
  200 continue
c
cdebug
c      write(*,*) ' ---- print from main -------'
c      write(*,*) ' ian:    ',ian
c      write(*,*) ' basnam: ',basnam
c      write(*,*) ' nbas:   ',nbas
c      write(*,*) ' norb:   ',norb
c      write(*,*) ' isela:  ',(isela(i),i=1,norb)
c      write(*,*) ' iselb:  ',(iselb(i),i=1,norb)
c      do 100 i=1,norb
c      write(*,*) ' hybrid orbital i =',i
c      write(*,1000) (orb(j,i),j=1,nbas)
c 1000 format(5f12.6)
c  100 continue
c
      return
c     error exit
  900 call msgout(0,1,'error(hybout): the basis set is not found.$')
      call msgout(0,1,basnam//'$')
      return
      end
cs---------------------------------------------------------------------
      subroutine frgatm(ifrg,ia3,ia4,ia5,ia6,ifnd)
c----------------------------------------------------------------------
c     return N(ia3)..C..C(ia4)..O(ia5)....Z(ia6) of fragment,ifrg
c     extra atoms for s-s bonded cys's
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      nrf=nresfg(ifrg)
      iresf=iresfg(1,ifrg)
      iresl=iresfg(nrf,ifrg)
c
      ist=istres(iresl)
      nati=istres(iresl+1)-ist
      call bakbon(nati,ian(ist),x(ist),y(ist),z(ist),
     .                                in1,ic2,ic3,io4,ifnd0)
c
      ifnd=ifnd0
      ia3=istres(iresf)
      ia4=ic3+ist-1
      ia5=io4+ist-1
      ia6=istres(iresl+1)-1
c
      return
      end
cs----------------------------------------------------------------------
      subroutine frgmol(ifrg,imol,iffrg,ilfrg)
c-----------------------------------------------------------------------
c     find sequence number of mol to which ifrg fragment belongs.
c     ifrg ... seq. # of fragment(input)
c     imol ... seq. # of mole to which ifrg belongs
c     iffrg ... seq. # of frg of the first fragment of the mol
c     ilfrg ... seq. # of frg of the last fragment of the mol
ce----------------------------------------------------------------------
      parameter (MaxMol=50000,MaxFrg=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      imol=0
      iffrg=0
      ilfrg=0
      nf=nresfg(ifrg)
      iresi1=iresfg(nf,ifrg)
c
      do 60 i=1,nmol
      istm=istmol(i)
      iedm=istmol(i+1)-1
      if(iresi1.ge.istm.and.iresi1.le.iedm) then
         imol=i
         go to 80
      endif
   60 continue
   80 continue
      istr=istmol(imol)
      iedr=istmol(imol+1)-1
      do 120 i=1,nfrg
      nf=nresfg(i)
      do 100 j=1,nf
      if(iresfg(j,i).eq.istr) then
         iffrg=i
      endif
      if(iresfg(j,i).eq.iedr) then
         ilfrg=i
      endif
  100 continue
  120 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine frgpep(nfgsiz,ifcys,ifgly,imlss)
c----------------------------------------------------------------------
c     fragmentation of proteins/polypeptides
c     note: fragmentation of non-peptide molecules is a manual work.
c           the automatic fragmentation of DNA/RNA is possible but is 
c           not implemented in this vesion.
c     nfgsiz ... fragment size. (nfgsiz res)/1frg. nfgsiz=1 or 2.
c     cys's with S-S bond are one frg(i.e. 2res/1frg) even if nfgsize=1.
c     ifcys =0 cys's with s-s bond is combined, =1 is not combined.
c              if nfgsiz=2, ifcys=0 is forced.
c     note: output with ifcys=1 should be edited later for fmo input.
c     ifgly =0 gly is combined with the neighbor, =1 is not combined
c     imlss ... intermolecular s-s bond. =0 exist, =1 not
ce---------------------------------------------------------------------
c
      call chgres
c
c     fragmentation and print fragment atoms for gms-fmo
      if(nfgsiz.le.0.or.nfgsiz.gt.3) go to 900
      if(nfgsiz.eq.1) call oneres(ifcys,ifgly,imlss)
      if(nfgsiz.eq.2) call twores(ifgly,imlss)
c
      return
  900 call msgout(0,0,'error(frgpep): wrong m-res/frg. max=2res/1frg.$')
      end
cs---------------------------------------------------------------------
      subroutine fssatm(ifrg,ia3,ia4,ia5,ia6,
     .                       ja3,ja4,ja5,ja6,jres,ifnd)
c----------------------------------------------------------------------
c     return N(ia3)..C..C(ia4)..O(ia5)....Z(ia6) of fragment,ifrg
c     for s-s bonded cys's extra atoms
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      dimension isep(4),isep1(4)
c
      nrf=nresfg(ifrg)
c     find disconnected frag
      nsep=0
      do 20 i=2,nrf
      i1=iresfg(i-1,ifrg)
      i2=iresfg(i,ifrg)
      if((i2-i1).ne.1) then
         nsep=nsep+1
         isep(nsep)=i2
         isep1(nsep)=i1
      endif
   20 continue
c
      if(nsep.eq.0) then
         iresf=iresfg(1,ifrg)
         iresl=iresfg(nrf,ifrg)
         ist=istres(iresf)
         nati=istres(iresf+1)-ist
         call bakbon(nati,ian(ist),x(ist),y(ist),z(ist),
     .                                   in1,ic2,ic3,io4,ifnd0)
c
         ifnd=ifnd0
         ia3=istres(iresf)
         ia4=ic3+ist-1
         ia5=io4+ist-1
         ia6=istres(iresl+1)-1
         ja3=0
         ja4=0
         ja5=0
         ja6=0
         jres=0
      elseif(nsep.eq.1) then
         iresf=iresfg(1,ifrg)
         iresl=isep1(1)
         ist=istres(iresf)
         nati=istres(iresf+1)-ist
         call bakbon(nati,ian(ist),x(ist),y(ist),z(ist),
     .                                   in1,ic2,ic3,io4,ifnd0)
         ia3=istres(iresf)
         ia4=ic3+ist-1
         ia5=io4+ist-1
         ia6=istres(iresl+1)-1
c         
         iresf=isep(1)
         iresl=iresfg(nrf,ifrg)
         ist=istres(iresf)
         nati=istres(iresf+1)-ist
         call bakbon(nati,ian(ist),x(ist),y(ist),z(ist),
     .                                   in1,ic2,ic3,io4,ifnd1)
         ja3=istres(iresf)
         ja4=ic3+ist-1
         ja5=io4+ist-1
         ja6=istres(iresl+1)-1
         ifnd=ifnd0+ifnd1
         jres=iresf
      else
         go to 900
      endif
c
      return
  900 call msgout(0,1,'error(fssatm): too many separated fragments.$')
      call msgout(0,0,'      up tp 2 is supported in this version.$')
      end
cs---------------------------------------------------------------------
      subroutine h321a(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     3-21G
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(9,5)
      data   ho/
     .  -0.070460,  0.164842,  0.000000,  0.000000,   0.502117,
     .   0.466939,  0.000000,  0.000000,  0.418037,
     .  -0.070466,  0.164858,  0.473392,  0.000000, -0.167360,
     .   0.466968,  0.394111,  0.000000, -0.139327,
     .  -0.070466,  0.164858, -0.236695, -0.409969, -0.167360,
     .   0.466968, -0.197056, -0.341311, -0.139327,
     .  -0.070466,  0.164858, -0.236695,  0.409969, -0.167360,
     .   0.466968, -0.197056,  0.341311, -0.139327,
     .   1.006716,  0.074826,  0.000000,  0.000000,  0.000000,
     .  -0.143831,  0.000000,  0.000000, -0.000004
     .         /
      save ho
c
      nbas=9
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
      subroutine h321b(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     3-21+G
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(13,5)
      data   ho/
     .  -0.068862,  0.158922,  0.000000,  0.000000,  0.488690,
     .   0.470307,  0.000000,  0.000000,  0.405055,  0.024784,
     .   0.000000,  0.000000,  0.034050,
     .  -0.068865,  0.158929,  0.460748,  0.000000, -0.162900,
     .   0.470302,  0.381889,  0.000000, -0.135011,  0.024780,
     .   0.032098,  0.000000, -0.011349,
     .  -0.068865,  0.158929, -0.230374, -0.399020, -0.162900,
     .   0.470302, -0.190944, -0.330725, -0.135011,  0.024780,
     .  -0.016048, -0.027797, -0.011349,
     .  -0.068865,  0.158929, -0.230374,  0.399020, -0.162900,
     .   0.470302, -0.190944,  0.330725, -0.135011,  0.024780,
     .  -0.016048,  0.027797, -0.011349,
     .   1.007087,  0.075762,  0.000000,  0.000000,  0.000001,
     .  -0.151743,  0.000000,  0.000000, -0.000005, -0.009474,
     .   0.000000,  0.000000, -0.000001
     .         /
      save ho
c
      nbas=13
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
      subroutine h631a(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     6-31G
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(9,5)
      data   ho/
     .  -0.067724,  0.300281,  0.000000,  0.000000,  0.606750,
     .   0.306535,  0.000000,  0.000000,  0.309793,
     .  -0.067730,  0.300310,  0.572037,  0.000000, -0.202234,
     .   0.306552,  0.292061,  0.000000, -0.103255,
     .  -0.067730,  0.300310, -0.286019, -0.495398, -0.202234,
     .   0.306552, -0.146031, -0.252933, -0.103255,
     .  -0.067730,  0.300310, -0.286019,  0.495398, -0.202234,
     .   0.306552, -0.146031,  0.252933, -0.103255,
     .   1.011954, -0.016447,  0.000000,  0.000000,  0.000000,
     .  -0.059374,  0.000000,  0.000000, -0.000001
     .         /
      save ho
c
      nbas=9
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
      subroutine h631c(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     6-31G*
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(15,5)
      data   ho/
     .  -0.065034,  0.288264,  0.000000,  0.000000,  0.604413,
     .   0.290129,  0.000000,  0.000000,  0.319045, -0.017106,
     .  -0.017106,  0.057935,  0.000000,  0.000000,  0.000000,
     .  -0.065041,  0.288294,  0.569833,  0.000000, -0.201457,
     .   0.290147,  0.300784,  0.000000, -0.106342,  0.049599,
     .  -0.017106, -0.008771,  0.000000, -0.027223,  0.000000,
     .  -0.065040,  0.288293, -0.284917, -0.493490, -0.201456,
     .   0.290146, -0.150393, -0.260487, -0.106341, -0.000428,
     .   0.032923, -0.008771,  0.033353,  0.013612,  0.023577,
     .  -0.065040,  0.288293, -0.284917,  0.493490, -0.201456,
     .   0.290146, -0.150393,  0.260487, -0.106341, -0.000428,
     .   0.032923, -0.008771, -0.033353,  0.013612, -0.023577,
     .   1.010938, -0.011976,  0.000000,  0.000000,  0.000000,
     .  -0.054085,  0.000000,  0.000000, -0.000001, -0.003175,
     .  -0.003175, -0.003175,  0.000000,  0.000000,  0.000000
     .         /
      save ho
c
      nbas=15
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
c     subroutine h631f(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     6-31G**
ce---------------------------------------------------------------------
c     parameter (MaxHyb=50)
c     dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
c     dimension ho(15,5)
c     data   ho/
c    .  -0.068254,  0.305270,  0.000003,  0.000000,  0.619132,
c    .   0.287030,  0.000002,  0.000000,  0.307201, -0.022701,
c    .  -0.022701,  0.042170,  0.000000,  0.000000,  0.000000,
c    .  -0.068257,  0.305303,  0.583705,  0.000000, -0.206360,
c    .   0.287057,  0.289613,  0.000000, -0.102393,  0.034962,
c    .  -0.022700, -0.015495,  0.000000, -0.023534,  0.000000,
c    .  -0.068257,  0.305306, -0.291851, -0.505502, -0.206358,
c    .   0.287061, -0.144805, -0.250811, -0.102392, -0.008284,
c    .   0.020546, -0.015495,  0.028830,  0.011767,  0.020381,
c    .  -0.068257,  0.305306, -0.291851,  0.505502, -0.206358,
c    .   0.287061, -0.144805,  0.250811, -0.102392, -0.008284,
c    .   0.020546, -0.015495, -0.028830,  0.011767, -0.020381,
c    .   1.010732, -0.013164,  0.000000,  0.000000,  0.000001,
c    .  -0.052063,  0.000000,  0.000000,  0.000000, -0.001621,
c    .  -0.001621, -0.001620,  0.000000,  0.000000,  0.000000
c    .         /
c     save ho
c
c     nbas=15
c     norb=5
c     do 20 i=1,norb
c     isela(i)=0
c     iselb(i)=1
c  20 continue
c     isela(1)=1
c     iselb(1)=0
c     do 40 i=1,norb
c     do 40 j=1,nbas
c  40 orb(j,i)=ho(j,i)
c     return
c     end
cs---------------------------------------------------------------------
      subroutine h631g(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     6-31++G**
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(19,5)
      data   ho/
     .  -0.064922,  0.305919,  0.000000,  0.000000,  0.622220,
     .   0.288564,  0.000000,  0.000000,  0.309676, -0.024300,
     .   0.000000,  0.000000,  0.008101, -0.022838, -0.022838,
     .   0.042186,  0.000000,  0.000000,  0.000000,
     .  -0.064927,  0.305945,  0.586627,  0.000000, -0.207401,
     .   0.288580,  0.291956,  0.000000, -0.103223, -0.024312,
     .   0.007627,  0.000000, -0.002702,  0.034961, -0.022836,
     .  -0.015616,  0.000000, -0.023589,  0.000000,
     .  -0.064927,  0.305944, -0.293315, -0.508035, -0.207399,
     .   0.288578, -0.145978, -0.252842, -0.103223, -0.024312,
     .  -0.003814, -0.006606, -0.002702, -0.008387,  0.020512,
     .  -0.015616,  0.028898,  0.011795,  0.020428,
     .  -0.064927,  0.305944, -0.293315,  0.508035, -0.207399,
     .   0.288578, -0.145978,  0.252842, -0.103223, -0.024312,
     .  -0.003814,  0.006606, -0.002702, -0.008387,  0.020512,
     .  -0.015616, -0.028898,  0.011795, -0.020428,
     .   1.011030, -0.014586,  0.000000,  0.000000,  0.000000,
     .  -0.054140,  0.000000,  0.000000,  0.000000,  0.006441,
     .   0.000000,  0.000000,  0.000000, -0.001572, -0.001572,
     .  -0.001572,  0.000000,  0.000000,  0.000000
     .         /
      save ho
c
      nbas=19
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
      subroutine h6311a(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     6-311G*
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(19,5)
      data   ho/
     .    -0.026794,-0.086612, 0.000000, 0.000000, 0.252561,
     .     0.344233, 0.000000, 0.000000, 0.444258, 0.240985,
     .     0.000000, 0.000000, 0.292724,-0.016321,-0.016321,
     .     0.071305, 0.000000, 0.000000, 0.000000,
     .    -0.026796,-0.086614, 0.238115, 0.000000,-0.084186,
     .     0.344242, 0.418849, 0.000000,-0.148082, 0.240988,
     .     0.275979, 0.000000,-0.097574, 0.061569,-0.016321,
     .    -0.006585, 0.000000,-0.031795, 0.000000,
     .    -0.026796,-0.086614,-0.119057,-0.206214,-0.084186,
     .     0.344242,-0.209425,-0.362733,-0.148082, 0.240989,
     .    -0.137989,-0.239005,-0.097574, 0.003151, 0.042097,
     .    -0.006585, 0.038944, 0.015898, 0.027536,
     .    -0.026796,-0.086614,-0.119057, 0.206214,-0.084186,
     .     0.344242,-0.209425, 0.362733,-0.148082, 0.240989,
     .    -0.137989, 0.239005,-0.097574, 0.003151, 0.042097,
     .    -0.006585,-0.038944, 0.015898,-0.027536,
     .     0.571513, 0.482733, 0.000000, 0.000000, 0.000000,
     .    -0.048217, 0.000000, 0.000000, 0.000000,-0.036258,
     .     0.000000, 0.000000, 0.000000,-0.002854,-0.002854,
     .    -0.002854, 0.000000, 0.000000, 0.000000
     .         /
      save ho
c
      nbas=19
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs----------------------------------------------------------------------
      subroutine hadres(ip,nh,xh1,xh2,xh3,anmh,natm,ian,x,y,z,anm)
c-----------------------------------------------------------------------
c     insert h atoms after ip-th atom
ce----------------------------------------------------------------------
      dimension ian(*),x(*),y(*),z(*)
      dimension xh1(3),xh2(3),xh3(3)
      character*4 anmh(*),anm(*)
c
      if(ip.eq.0) then
         ip1=natm+1
         ian(ip1)=1
         x(ip1)=xh1(1)
         y(ip1)=xh1(2)
         z(ip1)=xh1(3)
         anm(ip1)=anmh(1)
         if(nh.gt.1) then
            ip2=natm+2
            ian(ip2)=1
            x(ip2)=xh2(1)
            y(ip2)=xh2(2)
            z(ip2)=xh2(3)
            anm(ip2)=anmh(2)
         endif
         if(nh.gt.2) then
            ip3=natm+3
            ian(ip3)=1
            x(ip3)=xh3(1)
            y(ip3)=xh3(2)
            z(ip3)=xh3(3)
            anm(ip3)=anmh(3)
         endif
      else
         k=0
         do 20 i=ip+1,natm
         k=k+1
         ii=natm+nh-k+1
         jj=natm-k+1
         ian(ii)=ian(jj)
         x(ii)=x(jj)
         y(ii)=y(jj)
         z(ii)=z(jj)
         anm(ii)=anm(jj)
   20    continue
c
         ip1=ip+1
         ian(ip1)=1
         x(ip1)=xh1(1)
         y(ip1)=xh1(2)
         z(ip1)=xh1(3)
         anm(ip1)=anmh(1)
         if(nh.gt.1) then
            ip2=ip+2
            ian(ip2)=1
            x(ip2)=xh2(1)
            y(ip2)=xh2(2)
            z(ip2)=xh2(3)
            anm(ip2)=anmh(2)
         endif
         if(nh.gt.2) then
            ip3=ip+3
            ian(ip3)=1
            x(ip3)=xh3(1)
            y(ip3)=xh3(2)
            z(ip3)=xh3(3)
            anm(ip3)=anmh(3)
         endif
      endif
c
      natm=natm+nh
c
      return
      end
cs---------------------------------------------------------------------
      subroutine hbdatm(ian,ifnd)
c----------------------------------------------------------------------
c     return ifnd=0 when ian is in the h-bond list(/hbdlen/)
ce---------------------------------------------------------------------
      parameter (MaxHBL=50)
      common/hbdlen/nhbd,nhbdx,iatnum(MaxHBL),jatnum(MaxHBL),
     .              rstdij(MaxHBL),rminij(MaxHBL),rmaxij(MaxHBL)
      ifnd=1
      do 20 i=1,nhbd
      if(ian.eq.iatnum(i).or.ian.eq.jatnum(i)) ifnd=0
   20 continue
      return
      end
cs----------------------------------------------------------------------
      subroutine hbdbdl(iout)
c-----------------------------------------------------------------------
c     print bond lengths
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*4   atm1,atm2
      character*2   elm1,elm2
      dimension     jatm(8),jatmh(8),iatmh(8),ra(3),rb(3)
      data          todeg/57.2968/,angmin/120.0/
      save          todeg,angmin
c
      write(iout,1200)
 1200 format(' Possible Hydrogen Bonding Sites',/,
     .' seq#,   length, angle,  type,     ires,       iatm,      jres,  
     .     jatm')
c
      kount=0
      do 100 ia=1,natm
      iatm=ia
      iani=ian(iatm)
c      if(iani.ne.7.and.iani.ne.8.and.iani.ne.16) go to 100
      call hbdatm(iani,ifnd)
      if(ifnd.ne.0) go to 100
      call hbdlst(natm,ian,x,y,z,iatm,iatmh,njatm,jatm,jatmh,1)
      if(njatm.eq.0) go to 100
      ia1=ia
c
      do 80 j=1,njatm
      ia2=jatm(j)
      ia22=0
         rmin=1000.0
         do 40 i=1,njatm
         iatt=jatmh(i)
         if(iatt.eq.0) go to 40
         rijh=(x(iatt)-x(ia1))**2+(y(iatt)-y(ia1))**2+
     .        (z(iatt)-z(ia1))**2
         rijh=sqrt(rijh)
         if(rijh.lt.rmin) then
            rmin=rijh
            ia22=jatmh(i)
         endif
   40 continue
      ia11=0
         rmin=1000.0
         do 60 i=1,njatm
         iatt=iatmh(i)
         if(iatt.eq.0) go to 60
         rihj=(x(iatt)-x(ia2))**2+(y(iatt)-y(ia2))**2+
     .        (z(iatt)-z(ia2))**2
         rihj=sqrt(rihj)
         if(rihj.lt.rmin) then
            rmin=rihj
            ia11=iatmh(i)
         endif
   60 continue
      atm1=atmnam(ia1)
      call chcase(4,atm1,1)
      call elmian(elm1,ian(ia1),1)
      call atmres(ia1,ires)
      call resid(resnam(ires),iresid,0,0)
      atm2=atmnam(ia2)
      call chcase(4,atm2,1)
      call atmres(ia2,jres)
      call resid(resnam(jres),jresid,0,0)
      call elmian(elm2,ian(ia2),1)
      ihbr1=ihbres(iresid)
      ihbr2=ihbres(jresid)
      if(ia11.ne.0.and.ia22.eq.0) then
c        iatm is proton-donor
         elm1(2:2)='H'
         rij=(x(ia1)-x(ia2))**2+(y(ia1)-y(ia2))**2+(z(ia1)-z(ia2))**2
         rij=sqrt(rij)
         ra(1)=x(ia1)-x(ia11)
         ra(2)=y(ia1)-y(ia11)
         ra(3)=z(ia1)-z(ia11)
         rb(1)=x(ia2)-x(ia11)
         rb(2)=y(ia2)-y(ia11)
         rb(3)=z(ia2)-z(ia11)
         call anglet(ra,rb,teta)
            angle=teta*todeg
            if(ihbr1.ne.0.and.ihbr2.ne.0) then
               if(angle.lt.angmin) go to 80
            endif
      elseif(ia11.eq.0.and.ia22.ne.0) then
c           jatm is proton-donor
            elm2(2:2)=elm2(1:1)
            elm2(1:1)='H'
            rij=(x(ia1)-x(ia2))**2+(y(ia1)-y(ia2))**2+(z(ia1)-z(ia2))**2
            rij=sqrt(rij)
            ra(1)=x(ia1)-x(ia22)
            ra(2)=y(ia1)-y(ia22)
            ra(3)=z(ia1)-z(ia22)
            rb(1)=x(ia2)-x(ia22)
            rb(2)=y(ia2)-y(ia22)
            rb(3)=z(ia2)-z(ia22)
            call anglet(ra,rb,teta)
            angle=teta*todeg
            if(ihbr1.ne.0.and.ihbr2.ne.0) then
               if(angle.lt.angmin) go to 80
            endif
      elseif(ia11.ne.0.and.ia22.ne.0) then
c           iatm or jatm is proton-donor
            rij=(x(ia1)-x(ia2))**2+(y(ia1)-y(ia2))**2+(z(ia1)-z(ia2))**2
            rij=sqrt(rij)
            rihj=(x(ia11)-x(ia2))**2+(y(ia11)-y(ia2))**2+
     .           (z(ia11)-z(ia2))**2
            rijh=(x(ia22)-x(ia1))**2+(y(ia22)-y(ia1))**2+
     .           (z(ia22)-z(ia1))**2
            if(rihj.lt.rijh) then
               elm1(2:2)='H'
               ra(1)=x(ia1)-x(ia11)
               ra(2)=y(ia1)-y(ia11)
               ra(3)=z(ia1)-z(ia11)
               rb(1)=x(ia2)-x(ia11)
               rb(2)=y(ia2)-y(ia11)
               rb(3)=z(ia2)-z(ia11)
            else
               elm2(2:2)=elm2(1:1)
               elm2(1:1)='H'
               ra(1)=x(ia1)-x(ia22)
               ra(2)=y(ia1)-y(ia22)
               ra(3)=z(ia1)-z(ia22)
               rb(1)=x(ia2)-x(ia22)
               rb(2)=y(ia2)-y(ia22)
               rb(3)=z(ia2)-z(ia22)
            endif
            call anglet(ra,rb,teta)
            angle=teta*todeg
            if(ihbr1.ne.0.and.ihbr2.ne.0) then
               if(angle.lt.angmin) go to 80
            endif
      else
         go to 80
      endif
c
      kount=kount+1
      write(iout,2000) kount,rij,angle,elm1,elm2,
     .      ires,resnam(ires),ia1,atm1,jres,resnam(jres),ia2,atm2
 2000 format(i5,f10.4,f8.2,2x,a2,'-',a2,2x,i4,2x,a3,i8,2x,a4,
     .                                     i4,2x,a3,i8,2x,a4)
   80 continue
      
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine hbdlst(natm,ian,x,y,z,iatm,iatmh,
     .                                      njatm,jatm,jatmh,key)
c----------------------------------------------------------------------
c     find hydrogenbonding atoms with iatm
c     ian(i)=0 atoms are skiped
c     natm,ian,x,y,z...number of atoms, atomic number and x,y,z coord.
c     nbnd...number of bonds
c     ibdlst...bonding atom number list of iatm
c     key...=0 search all atoms, =1 search only i > iatm
ce---------------------------------------------------------------------
      dimension ian(*),x(*),y(*),z(*),jatm(*),iatmh(*),jatmh(*)
      dimension ibdlst(8),jbdlst(8)
c
      rdum=0.0
      njatm=0
      ian1=ian(iatm)
c      if(ian1.ne.7.and.ian1.ne.8.and.ian1.ne.16) go to 100
      call hbdatm(ian1,ifnd1)
      if(ifnd1.ne.0) go to 100
      call bndlst(natm,ian,x,y,z,iatm,nbndi,ibdlst,key)
      x1=x(iatm)
      y1=y(iatm)
      z1=z(iatm)
      ist=1
      if(key.eq.1) ist=iatm+1
      do 80 j=ist,natm
      if(j.eq.iatm) go to 80
      if(ian(j).eq.0) go to 80
      ian2=ian(j)
c      if(ian2.ne.7.and.ian2.ne.8.and.ian2.ne.16) go to 80
      call hbdatm(ian2,ifnd2)
      if(ifnd2.ne.0) go to 80
      rij=(x1-x(j))**2+(y1-y(j))**2+(z1-z(j))**2
c     if rij**2 is larger than (4.0)**2, skip
      if(rij.gt.16.0) go to 80
      rij=sqrt(rij)
      call lhbbnd(ian1,ian2,rdum,rmin,rmax,ifnd)
c      if(ifnd.ne.0) go to 900
      if(ifnd.ne.0) go to 100
      if(rij.gt.rmin.and.rij.lt.rmax) then
         njatm=njatm+1
         jatm(njatm)=j
         jatmh(njatm)=0
         call bndlst(natm,ian,x,y,z,j,nbndj,jbdlst,key)
         if(nbndj.gt.0) then
            rmin=1000.0
            do 40 i=1,nbndj
            iatt=jbdlst(i)
            if(ian(iatt).ne.1) go to 40
            rijh=(x(iatm)-x(iatt))**2+(y(iatm)-y(iatt))**2
     .                               +(z(iatm)-z(iatt))**2
            rijh=sqrt(rijh)
            if(rijh.lt.rmin) then
               rmin=rijh
               jatmh(njatm)=iatt
            endif
   40       continue
         endif
      endif
      iatmh(njatm)=0
      if(nbndi.gt.0) then
         rmin=1000.0
         do 60 i=1,nbndi
            iatt=ibdlst(i)
            if(ian(iatt).ne.1) go to 60
            rihj=(x(j)-x(iatt))**2+(y(j)-y(iatt))**2+(z(j)-z(iatt))**2
            rihj=sqrt(rihj)
            if(rihj.lt.rmin) then
               rmin=rihj
               iatmh(njatm)=iatt
            endif
   60    continue
      endif
   80 continue
  100 continue
      return
c     error exit
c  900 call msgout(0,1,'error(hbdlst): rmin, rmax are not given for$')
c      call msgou0(0,1,' atomic number i=$',ian1)
c      call msgou0(0,0,' atomic number j=$',ian2)
      end
cs---------------------------------------------------------------------
      subroutine hmini(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     MINI
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(5,5)
      data   ho/
     .   -0.104883, 0.308874, 0.000000, 0.000000, 0.521806,
     .   -0.104884, 0.308875, 0.491962, 0.000000,-0.173935,
     .   -0.104884, 0.308876,-0.245981,-0.426051,-0.173934,
     .   -0.104884, 0.308876,-0.245981, 0.426051,-0.173934,
     .    0.988209, 0.063992, 0.000000, 0.000000, 0.000000
     .         /
      save ho
c
      nbas=5
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs---------------------------------------------------------------------
      subroutine hsto(nbas,norb,isela,iselb,orb)
c----------------------------------------------------------------------
c     hybrid orbitals of carbon atom
c     STO-3G
ce---------------------------------------------------------------------
      parameter (MaxHyb=50)
      dimension isela(MaxHyb),iselb(MaxHyb),orb(MaxHyb,MaxHyb)
      dimension ho(5,5)
      data   ho/
     .   -0.117784,   0.542251,   0.000000,   0.000000,   0.850774,
     .   -0.117787,   0.542269,   0.802107,   0.000000,  -0.283586,
     .   -0.117787,   0.542269,  -0.401054,  -0.694646,  -0.283586,
     .   -0.117787,   0.542269,  -0.401054,   0.694646,  -0.283586,
     .    1.003621,  -0.015003,   0.000000,   0.000000,   0.000000
     .         /
      save ho
c
      nbas=5
      norb=5
      do 20 i=1,norb
      isela(i)=0
      iselb(i)=1
   20 continue
      isela(1)=1
      iselb(1)=0
      do 40 i=1,norb
      do 40 j=1,nbas
   40 orb(j,i)=ho(j,i)
      return
      end
cs----------------------------------------------------------------------
      subroutine horigi(iout,ires,nato,iano,xo,yo,zo,anmo,
     .                                          nath,xh,yh,zh,anmh)
c-----------------------------------------------------------------------
c     recover original H's
ce----------------------------------------------------------------------
      dimension    iano(*),xo(*),yo(*),zo(*)
      dimension    xh(*),yh(*),zh(*)
      character*4  anmo(*),anmh(*),anmtmp
      dimension    lst(8)
      data rhhmax/0.25/
      save rhhmax
c
      rdum=0.0
c     check bond atoms
      kepth=0
      ianh=1
      do 200 j=1,nath
      do 120 i=1,nato
      if(iano(i).eq.1) go to 120
      iani=iano(i)
      rih=(xo(i)-xh(j))**2+(yo(i)-yh(j))**2+(zo(i)-zh(j))**2
      rih=sqrt(rih)
      call lcvbnd(ianh,iani,0,rdum,rmin,rmax,ifnd1)
      if(rih.gt.rmax) go to 120
      call bndlst(nato,iano,xo,yo,zo,i,nbnd,lst,0)
      if(nbnd.le.0) go to 120
      nbndh=0
      imin=lst(1)
      rmin=1000.0
      do 60 k=1,nbnd
      lstk=lst(k)
      if(iano(lstk).eq.1) then
         nbndh=nbndh+1
         rhh=(xo(lstk)-xh(j))**2+(yo(lstk)-yh(j))**2+(zo(lstk)-zh(j))**2
         if(rhh.lt.rmin) then
            rmin=rhh
            imin=lstk
         endif
      endif
   60 continue
      anmtmp=anmh(j)
      call chcase(4,anmtmp,1)
      if(nbndh.eq.2.and.rmin.gt.rhhmax) then
         write(iout,1000) ires,j,anmtmp
 1000    format(' ! warning(horigi): large difference is found between m
     .odel and original coord.',/,
     .          '   in residue',i4,' original H atom ',i5,2x,a4)
      endif
      kepth=kepth+1
      xo(imin)=xh(j)
      yo(imin)=yh(j)
      zo(imin)=zh(j)
      anmo(imin)=anmh(j)
c      write(iout,1200) ires,j,anmtmp
c 1200 format(' messsge: original H coordinates are kept. residue #=',i3,
c     .       ' atom=',i5,2x,a4)
  120 continue
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      integer function ihbres(iresid)
c----------------------------------------------------------------------
c     return 0 for res#8-10 and 13-16 which has rotatable O-H group
ce---------------------------------------------------------------------
      ihbres=1
      if((iresid.ge.8.and.iresid.le.10).or.
     .                   (iresid.ge.13.and.iresid.le.16)) then
         ihbres=0
      endif
      return
      end
cs---------------------------------------------------------------------
      subroutine indata(iout,ifrg,itype,izero,ia1,ia2,ia3,ia4,ia5,ia6)
c----------------------------------------------------------------------
c     print fragment atoms
c     ifrg ... fragment number
c     itype =1  ia3 -ia6   (non-res frag)
c           =2  ia3 -ia6 but excluding ia4 and ia5 (the first frag)
c           =3  ia1 ia2 ia3 -ia6 (the last frag)
c           =4  ia1 ia2 ia3 -ia6 excudeing ia4 and ia5 (middle frag)
c     izero =0 supply '0' at the end, =1 no zero
ce---------------------------------------------------------------------
      dimension lst(100)
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      data i0/0/
      save i0
c
 2200 format(10x,10i7)
c     itype1
      if(itype.eq.1) then
         if(izero.eq.0) then
            if(ia6.gt.ia3) then
               write(iout,2200) ia3,-ia6,i0
            else
               write(iout,2200) ia6,i0
            endif
         else
            if(ia6.gt.ia3) then
               write(iout,2200) ia3,-ia6
            else
               write(iout,2200) ia3
            endif
         endif
         do 20 j=ia3,ia6
   20    iatfrg(j)=ifrg
      endif
c     itype3
      if(itype.eq.3) then
         if(izero.eq.0) then
            write(iout,2200) ia1,ia2,ia3,-ia6,i0
         else
            write(iout,2200) ia1,ia2,ia3,-ia6
         endif
         iatfrg(ia1)=ifrg
         iatfrg(ia2)=ifrg
         do 40 j=ia3,ia6
   40    iatfrg(j)=ifrg
      endif
c     itype2 and 4
      if(itype.eq.2.or.itype.eq.4) then
         if(itype.eq.4) then
           lst(1)=ia1
           lst(2)=ia2
           iatfrg(ia1)=ifrg
           iatfrg(ia2)=ifrg
           k=2
         else
            k=0
         endif
         if(ia4-ia3.gt.2) then
            k=k+1
            lst(k)=ia3
            k=k+1
            lst(k)=-(ia4-1)
            do 80 j=ia3,ia4-1
   80       iatfrg(j)=ifrg
         elseif(ia4-ia3.eq.2) then
            k=k+1
            lst(k)=ia3
            k=k+1
            lst(k)=ia3+1
            iatfrg(ia3)=ifrg
            iatfrg(ia3+1)=ifrg
         elseif(ia4-ia3.eq.1) then
            k=k+1
            lst(k)=ia3
            iatfrg(ia3)=ifrg
         endif
         if(ia5-ia4.gt.2) then
            k=k+1
            lst(k)=ia4+1
            k=k+1
            lst(k)=-(ia5-1)
            do 100 j=ia4+1,ia5-1
  100       iatfrg(j)=ifrg
         elseif(ia5-ia4.eq.2) then
            k=k+1
            lst(k)=ia4+1
            iatfrg(ia4+1)=ifrg
         endif
         if(ia6-ia5.gt.2) then
            k=k+1
            lst(k)=ia5+1
            k=k+1
            lst(k)=-ia6
            do 120 j=ia5+1,ia6
  120       iatfrg(j)=ifrg
         elseif(ia6-ia5.eq.2) then
            k=k+1
            lst(k)=ia5+1
            k=k+1
            lst(k)=ia6
            iatfrg(ia5+1)=ifrg
            iatfrg(ia6)=ifrg
         elseif(ia6-ia5.eq.1) then
            k=k+1
            lst(k)=ia6
            iatfrg(ia6)=ifrg
         endif
         if(izero.eq.0) then
            k=k+1
            lst(k)=0
         endif
         write(iout,2200) (lst(i),i=1,k)
      endif
c
      return
c  900 call msgout(0,0,'error(indata): expand the dimension lst(100).$')    
      end
cs---------------------------------------------------------------------
      integer function iresiz(iresid)
c----------------------------------------------------------------------
c     return number of atoms of iresid
c     iresid =0 if wrong iresid
ce---------------------------------------------------------------------
      dimension natres(20)
      data natres/ 7,10,16,20,19,19,14,17,12,15,
     .            22,24,11,14,21,11,14,17,18,24/
      save natres
      iresiz=0
      if(iresid.le.0.or.iresid.gt.20) go to 900
      iresiz=natres(iresid)
  900 continue
      return
      end
cs----------------------------------------------------------------------
      subroutine istfgm(imol,iffrg,ilfrg)
c-----------------------------------------------------------------------
c     find the first and the last fragments of imol
c     imol  ... seq.# of molecule(input)
c     iffrg ... seq. # of frg of the first fragment of the mol
c     ilfrg ... seq. # of frg of the last fragment of the mol
ce----------------------------------------------------------------------
      parameter (MaxMol=50000,MaxFrg=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      istr=istmol(imol)
      iedr=istmol(imol+1)-1
      do 120 i=1,nfrg
      nf=nresfg(i)
      do 100 j=1,nf
      if(iresfg(j,i).eq.istr) then
         iffrg=i
      endif
      if(iresfg(j,i).eq.iedr) then
         ilfrg=i
      endif
  100 continue
  120 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine isort(n,ival,iwrk)
c-----------------------------------------------------------------------
c     isort:: arrange interger number in ascending order.
c     n      (i4)   ... number of data.
c     ival   (r4:*) ... data to be ordered. orderd data is stored on exit.
c     iwrk   (i4:*) ... scratch array.
ce----------------------------------------------------------------------
      dimension   ival(*),iwrk(*)
c
      do 50 i=1,n
   50 iwrk(i)=i
c
      do 200 i=1,n
      k=i
      ip=ival(i)
      if(n-i.le.0) go to 120
      do 100 j=i+1,n
      if(ival(j).gt.ip) go to 100
      k=j
      ip=ival(j)
  100 continue
  120 if(k.eq.i) go to 200
      it=iwrk(i)
      iwrk(i)=iwrk(k)
      iwrk(k)=it
      itmp=ival(i)
      ival(i)=ival(k)
      ival(k)=itmp
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine lcvbnd(ian1,ian2,ibdo,rstd,rmin,rmax,ifnd)
c----------------------------------------------------------------------
c     return std,min and max bond length of ian1-ian2 for ibdo bond order.
c     ian1,ian2...atomic number
c     ibdo...bond order. =1 single,=2 double, =3 triple, =4 aromatic,
c                          =0 sum of covalent radii
c     rstd,rmin,rmax...standard, minimum and maximum bond length
c     ifnd=0 rstd,rmin,rmax were set, =1 failed
ce---------------------------------------------------------------------
      parameter (MaxBdL=50)
      common/cbdlen/ncbd,ncbdx,iatnum(MaxBdL),jatnum(MaxBdL),
     .       ijbnd(MaxBdL),rstdij(MaxBdL),rminij(MaxBdL),rmaxij(MaxBdL)
      common/cbdrad/ncvdat,ncbdum,radcbd(100)
      data   rdel/0.3/
      save   rdel
c
      ifnd=1
c
      if(ibdo.eq.0) then
         rstd=radcbd(ian1)+radcbd(ian2)
         rmin=0.0
         rmax=rstd+rdel
         ifnd=0
      else
      rstd=0.0
         rmin=0.0
         rmax=0.0
         ia1=ian1
         ia2=ian2
         if(ia1.gt.ia2) then
            ia1t=ia1
            ia1=ia2
            ia2=ia1t
         endif
         do 20 i=1,ncbd
            if(iatnum(i).eq.ia1.and.jatnum(i).eq.ia2.and.
     .                            ijbnd(i).eq.ibdo) then
               rstd=rstdij(i)
               rmin=rminij(i)
               rmax=rmaxij(i)
               ifnd=0
            endif
   20    continue
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine lhbbnd(ian1,ian2,rstd,rmin,rmax,ifnd)
c----------------------------------------------------------------------
c     return std,min and max hydrogen bond length of ian1-ian2
c     ian1,ian2...atomic number. ian1 < ian2.
c     rstd,rmin,rmax...standard, minimum and maximum bond length
c     ifnd=0 rstd,rmin,rmax were set, =1 failed
ce---------------------------------------------------------------------
      parameter (MaxHBL=50)
      common/hbdlen/nhbd,nhbdx,iatnum(MaxHBL),jatnum(MaxHBL),
     .              rstdij(MaxHBL),rminij(MaxHBL),rmaxij(MaxHBL)
c
      ifnd=1
c
      rstd=0.0
      rmin=0.0
      rmax=0.0
      ia1=ian1
      ia2=ian2
      if(ia1.gt.ia2) then
         ia1t=ia1
         ia1=ia2
         ia2=ia1t
      endif
      do 20 i=1,nhbd
      if(iatnum(i).eq.ia1.and.jatnum(i).eq.ia2) then
         rstd=rstdij(i)
         rmin=rminij(i)
         rmax=rmaxij(i)
         ifnd=0
      endif
   20 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine msgini(iout)
c----------------------------------------------------------------------
c     initialize parameters for "msgout"
c     iout ... i/o unit number for output
ce---------------------------------------------------------------------
      character*72 mess
      common/mesbuf/iomsg,nmess,mess(100)
      iomsg=iout
      nmess=0
      return
      end
cs---------------------------------------------------------------------
      subroutine msgou0(key,istop,text,intd)
c----------------------------------------------------------------------
c     print massage. an integer number.
c     note: call msgini onece befor calling this routine
c     key ... =0 print now, =1 accumulate text, =2 print text in buffer
c     istop ... =0 stop after printing, =1 return.
c     intd ... integer data
ce---------------------------------------------------------------------
      character*72 mess
      common/mesbuf/iomsg,nmess,mess(100)
      character*72 text
      character*72 temp1,temp2,text72
      character*1  text1(72)
      equivalence  (text1,temp1)
      data  maxc/72/,maxmes/100/
      save maxc,maxmes
c
      text72=text
      call strcut(maxc,text72,'$')
      call strlas(maxc,text72,nc)
c     convert int to string and pack them
      nmess=nmess+1
      call strcle(maxc,mess(nmess))
      inttmp=intd
      call stri2c(maxc,inttmp,temp2,ifg)
      mess(nmess)=text72(1:nc)//temp2
c
      if(key.eq.0.or.key.eq.2.or.nmess.ge.maxmes) then
         do 140 i=1,nmess
         temp1=mess(i)
         call strlas(maxc,temp1,nc)
         write(iomsg,1000) (text1(j),j=1,nc)
 1000    format(1x,72a1)
  140    continue
         nmess=0
      endif
c
      if(istop.eq.0) then
         stop
      else
         return
      endif
c
      end
cs---------------------------------------------------------------------
      subroutine msgou1(key,istop,nint,intd,iseq)
c----------------------------------------------------------------------
c     print massage. integer numbers.
c     note: call msgini onece befor calling this routine
c     key ... =0 print now, =1 accumulate text, =2 print text in buffer
c     istop ... =0 stop after printing, =1 return.
c     nint ... number of integer data
c     intd ... integer data
c     ifig ... figures of integer values
c     iseq ... =0 print with seqence number, =1 no sequence number
ce---------------------------------------------------------------------
      character*72 mess
      common/mesbuf/iomsg,nmess,mess(100)
      dimension    intd(nint)
      character*72 temp1,temp2,temp3
      character*1  text1(72)
      equivalence  (text1,temp1)
      data  maxc/72/,maxmes/100/
      save maxc,maxmes
c
c     convert int to string and pack them
      nmess=nmess+1
      call strcle(maxc,mess(nmess))
      nc=0
      do 100 i=1,nint
      ncs=nc+1
      if(iseq.eq.0) then
         call stri2c(maxc,i,temp2,nfg)
         nc=nc+nfg
      endif
      call stri2c(maxc,intd(i),temp3,ifg)
      nc=nc+ifg
      nc1=nc+1
      if(iseq.eq.0) nc1=nc+2
      if(nc1.ge.maxc) then
         if(nmess.ge.maxmes) then
            do 40 j=1,nmess
            temp1=mess(j)
            call strlas(maxc,temp1,nc)
            write(iomsg,1000) (text1(k),k=1,nc)
 1000       format(1x,72a1)
   40       continue
            nmess=0
         endif
         nmess=nmess+1
         call strcle(maxc,mess(nmess))
         nc=nfg+ifg
         ncs=1
      endif
      if(iseq.eq.0) then
         mess(nmess)=mess(nmess)(1:ncs)//temp2(1:nfg)//':'
     .                                       //temp3(1:ifg)//','
         nc=nc+2
      else
         mess(nmess)=mess(nmess)(1:ncs)//temp3(1:ifg)//','
         nc=nc+1
      endif
  100 continue
c
      if(key.eq.0.or.key.eq.2.or.nmess.ge.maxmes) then
         do 140 i=1,nmess
         temp1=mess(i)
         call strlas(maxc,temp1,nc)
         write(iomsg,1000) (text1(j),j=1,nc)
  140    continue
         nmess=0
      endif
c
      if(istop.eq.0) then
         stop
      else
         return
      endif
c
      end
cs---------------------------------------------------------------------
      subroutine msgou2(key,istop,nval,vald,isig,iseq)
c----------------------------------------------------------------------
c     print massage. real*4 numbers
c     note: call msgini onece befor calling this routine
c     key ... =0 print now, =1 accumulate text, =2 print text in buffer
c     istop ... =0 stop after printing, =1 return.
c     nval ... number of data
c     vald ... real number
c     isig ... =n significant figures
c     iseq ... =0 print with seqence number, =1 no sequence number
ce---------------------------------------------------------------------
      character*72 mess
      common/mesbuf/iomsg,nmess,mess(100)
      dimension    vald(nval)
      character*72 temp1,temp2,temp3
      character*1  text1(72)
      equivalence  (text1,temp1)
      data  maxc/72/,maxmes/100/
      save maxc,maxmes
c
c     convert r*4 numbers to string and pack them
      nmess=nmess+1
      call strcle(maxc,mess(nmess))
      nc=0
      do 100 i=1,nval
      ncs=nc+1
      if(iseq.eq.0) then
         call stri2c(maxc,i,temp2,nfg)
         nc=nc+nfg
      endif
      call strr2c(maxc,vald(i),temp3,ifg,isig)
      nc=nc+ifg
      nc1=nc+1
      if(iseq.eq.0) nc1=nc+2
      if(nc1.ge.maxc) then
         if(nmess.ge.maxmes) then
            do 40 j=1,nmess
            temp1=mess(j)
            call strlas(maxc,temp1,nc)
            write(iomsg,1000) (text1(k),k=1,nc)
 1000       format(1x,72a1)
   40       continue
            nmess=0
         endif
         nmess=nmess+1
         call strcle(maxc,mess(nmess))
         nc=nfg+ifg
         ncs=1
      endif
      if(iseq.eq.0) then
         mess(nmess)=mess(nmess)(1:ncs)//temp2(1:nfg)//':'
     .                                       //temp3(1:ifg)//'/'
         nc=nc+2
      else
         mess(nmess)=mess(nmess)(1:ncs)//temp3(1:ifg)//'/'
         nc=nc+1
      endif
  100 continue
c
      if(key.eq.0.or.key.eq.2.or.nmess.ge.maxmes) then
         do 140 i=1,nmess
         temp1=mess(i)
         call strlas(maxc,temp1,nc)
         write(iomsg,1000) (text1(j),j=1,nc)
  140    continue
         nmess=0
      endif
c
      if(istop.eq.0) then
         stop
      else
         return
      endif
c
      end
cs---------------------------------------------------------------------
      subroutine msgout(key,istop,text)
c----------------------------------------------------------------------
c     print massage
c     note: call msgini onece befor calling this routine
c     key ... =0 print now, =1 accumulate text, =2 print text in buffer
c     istop ... =0 stop after printing, =1 return.
ce---------------------------------------------------------------------
      character*72 mess
      common/mesbuf/iomsg,nmess,mess(100)
      character*72 text,text72
      character*1  text1(72)
      equivalence (text72,text1)
      data  maxc/72/,maxmes/100/
      save maxc,maxmes
c
      text72=text
      call strcut(maxc,text72,'$')
      if(key.eq.0) then
         call strlas(maxc,text72,nc)
         write(iomsg,1000) (text1(j),j=1,nc)
 1000    format(1x,72a1)
      elseif(key.eq.1) then
         nmess=nmess+1
         mess(nmess)=text72
         if(nmess.eq.maxmes) then
            write(iomsg,1200)
 1200       format(' message(msgout): buffer full. forced print')
            do 20 i=1,nmess
            text72=mess(i)
            call strlas(maxc,text72,nc)
            write(iomsg,1000) (text1(j),j=1,nc)
   20       continue
            text72=text
            call strlas(maxc,text72,nc)
            write(iomsg,1000) (text1(j),j=1,nc)
            nmess=0
         endif
      else
         do 40 i=1,nmess
         text72=mess(i)
         call strlas(maxc,text72,nc)
         write(iomsg,1000) (text1(j),j=1,nc)
   40    continue
         nmess=0
      endif
c
      if(istop.eq.0) then
         stop
      else
         return
      endif
c
      end
cs---------------------------------------------------------------------
      subroutine oneres(ifcys,ifgly,imlss)
c----------------------------------------------------------------------
c     fragmentation of proteins/polypeptides
c     one res / one fragment
c     cys's with s-s bond is combined if ifcys=0
c     gly is combined with neighbor if ifgly=0
c     ace and nme cap is always attached to the first and the last res, 
c     respectively.
ce---------------------------------------------------------------------
      parameter (MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      character*3   temp
c
      idum=0
      jdum=0
      nfrg=0
      nssbnd=0
      imlss=1
c
c     simple division per one res
      do 40 ires=1,nres
      call resmol(ires,imol,ist,ied)
      nfrg=nfrg+1
      if(nfrg.gt.MaxFrg) go to 920
      nresfg(nfrg)=1
      iresfg(1,nfrg)=ires
      ichfrg(nfrg)=ichres(ires)
      iresn=numres(ires)
      call cnint(3,iresn,3,temp)
      frgnam(nfrg)=resnam(ires)//temp
   40 continue
c     count # of s-s bonds
      do 80 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
      if(iresid.ne.16) go to 80
      irestmp=ires
      call ssbcys(0,irestmp,jres)
      if(jres.eq.0.or.jres.lt.ires) go to 80
      nssbnd=nssbnd+1
      call frgmol(ires,imol1,idum,jdum)
      call frgmol(jres,imol2,idum,jdum)
      if(imol1.ne.imol2) imlss=0
      if(ifcys.eq.0) then
c        ires-cys and jres-cys(ires<jres) has s-s bond
         call resfrg(ires,ifrg)
         call resfrg(jres,jfrg)
         call updfrg(ifrg,jfrg)
      endif
   80 continue
c
c     combine ace and nme caps to the first and the last res,respectively,
c     if they exist.
      do 120 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
      call resmol(ires,imol,ist,ied)
      if(ires.eq.ist.and.resnam(ires).eq.'ace') then
c        ace is combined to the next residue
         call resid(resnam(ires+1),jresid,0,0)
         if(jresid.ne.0) then
            call resfrg(ires,ifrg)
            call resfrg(ires+1,jfrg)
            call updfrg(ifrg,jfrg)
         endif
      elseif(ires.eq.ied.and.resnam(ires).eq.'nme') then
c        nme is combined to the front residue
         call resid(resnam(ires-1),jresid,0,0)
         if(jresid.ne.0) then
            call resfrg(ires-1,ifrg)
            call resfrg(ires,jfrg)
            call updfrg(ifrg,jfrg)
         endif
      endif
  120 continue
c
      if(ifgly.eq.0) then
c        combine gly with neighbor
         do 320 ires=1,nres
         call resid(resnam(ires),iresid,0,0)
         call resmol(ires,imol,ist,ied)
         if(iresid.ne.1) go to 320
            if(ires.eq.ist) then
c              gly at n-termimus is combined to the next residue
               call resid(resnam(ires+1),jresid,0,0)
               if(jresid.ne.0) then
                  call resfrg(ires,ifrg)
                  call resfrg(ires+1,jfrg)
                  call updfrg(ifrg,jfrg)
               endif
            elseif(ires.eq.ied) then
c              gly at c-termimus is combined to the front residue
               call resid(resnam(ires-1),jresid,0,0)
               if(jresid.ne.0) then
                  call resfrg(ires-1,ifrg)
                  call resfrg(ires,jfrg)
                  call updfrg(ifrg,jfrg)
               endif
            else
               idone=1
               call resfrg(ires,ifrg)
               if(nresfg(ifrg).lt.2) then
                  call adjfrg(ifrg,iadjs,iadjl)
                  jres1=iresfg(1,iadjs)
                  nrf1=nresfg(iadjs)
                  call resid(resnam(jres1),jrsid1,0,0)
                  if(jrsid1.ne.0.and.nrf1.lt.2
     .                          .and.iabs(ires-jres1).eq.1) then
                     call updfrg(ifrg,iadjs)
                     idone=0
                  endif
                  if(idone.eq.1) then
                     jres2=iresfg(1,iadjl)
                     nrf2=nresfg(iadjl)
                     call resid(resnam(jres2),jrsid2,0,0)
                     if(jrsid2.ne.0.and.nrf2.lt.2
     .                             .and.iabs(ires-jres2).eq.1) then
                        call updfrg(ifrg,iadjl)
                        idone=0
                     endif
                  endif
               endif
            endif
         call resmol(ires,imol,ist,ied)
  320    continue
      endif
c  400 continue
c
      return
c     error exit
  920 call msgout(0,1,'error(oneres): too many fragments.$')
      call msgou0(0,1,' MaxFrg=$',MaxFrg)
      call msgout(0,0,' recompile the program with larger MaxFrg.$')
      end
cs----------------------------------------------------------------------
      subroutine ordatm(iresn,ires,natr,iani,xi,yi,zi,anmi,
     .                                    iant,xt,yt,zt,anmt,iod)
c-----------------------------------------------------------------------
c     reorder heavy atoms of residues in "standard" order
c     iresn(input): code # of residue
c     natr(input): # of atoms (heavy atoms only)
c     iani(inpit): atomic #
c     xi,yi,zi,anmi(input):xyz coord. and atom label.order may be changed
c     iano(output):atomic # after reordering
c     xt,yt,zt,anmt(output):xyz coord. and atom label after reordering
c     iod=0 not reorderd, =1 orderd
ce----------------------------------------------------------------------
      dimension iani(*),iant(*)
      character*4   anmi(*),anmt(*),atmp
      character*6 restmp
      dimension xi(*),yi(*),zi(*),xt(*),yt(*),zt(*)
      dimension ian0(14),iabnd(14),iord(14),idone(14)
      dimension rbdmax(15),rbdmin(15)
c     katres(i): # of heavy atoms of iresn
      dimension katres(20)
      data      katres/4,5,7,11,8,8,7,8,8,9,9,11,6,7,12,6,8,9,10,14/
      save      katres
c
CCC   if(iresn.le.0.or.iresn.gt.20) go to 900
      if(iresn.le.0.or.iresn.gt.20) return
c
      idummy=0
      rdum=0.0
      call resiid(ires,idummy,restmp)
c      nathev=0
c      do 41 i=1,natr
c   41 if(iani(i).ne.1) nathev=nathev+1
c
      natm=katres(iresn)
c      if(nathev.ne.natm) go to 910
CCC   if(natr.ne.natm) go to 910
      if(natr.ne.natm) return
c
c     set min,max bond length
      rdum=0.0
      call lcvbnd(6,6,1,rdum,rmincc,rmaxcc,ifndcc)
      call lcvbnd(6,7,1,rdum,rmincn,rmaxcn,ifndcn)
      call lcvbnd(6,8,1,rdum,rminco,rmaxco,ifndco)
      call lcvbnd(6,16,1,rdum,rmincs,rmaxcs,ifndcs)
      rmincc=0.0
      rmincn=0.0
      rminco=0.0
      rmincs=0.0
      if(ifndcc+ifndcn+ifndco+ifndcs.ne.0) go to 980
c
c     the first 4 are backborn atoms: N(1)-CA(2)-C(3)-O(4)
c      if(iani(1).ne.7.or.iani(2).ne.6.or.iani(3).ne.6.or.iani(4).ne.8)
c     .                              then
         call bakbon(natm,iani,xi,yi,zi,in1,ic2,ic3,io4,ifnd)
         if(ifnd.ne.0) go to 990
         iord4=0
         if(in1.ne.1.or.ic2.ne.2.or.ic3.ne.3.or.io4.ne.4) then
            iord4=1
            if(in1.ne.1) iord(1)=in1
            if(ic2.ne.2) iord(2)=ic2
            if(ic3.ne.3) iord(3)=ic3
            if(io4.ne.4) iord(4)=io4
            do 42 i=1,4
            ii=iord(i)
            iant(i)=iani(ii)
            xt(i)=xi(ii)
            yt(i)=yi(ii)
            zt(i)=zi(ii)
            anmt(i)=anmi(ii)
   42       continue
            k=4
            do 44 i=1,natm
            if(iord(1).eq.i.or.iord(2).eq.i.or.iord(3).eq.i.
     .                                      or.iord(4).eq.i) go to 44
            k=k+1
            iant(k)=iani(i)
            xt(k)=xi(i)
            yt(k)=yi(i)
            zt(k)=zi(i)
            anmt(k)=anmi(i)
   44       continue
            do 46 i=1,natm
            iani(i)=iant(i)
            xi(i)=xt(i)
            yi(i)=yt(i)
            zi(i)=zt(i)
            anmi(i)=anmt(i)
   46       continue
         endif
c      endif
c
      do 50 i=1,natm
      idone(i)=0
      iord(i)=0
      ian0(i)=6
      iabnd(i)=i-1
      rbdmax(i)=rmaxcc
   50 rbdmin(i)=rmincc
      ian0(1)=7
      ian0(4)=8
      iabnd(5)=2
      rbdmax(2)=rmaxcn
      rbdmax(4)=rmaxco
      rbdmin(2)=rmincn
      rbdmin(4)=rminco
c
c     set atom and bond data for side chain atoms
      go to (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20),iresn
    1 continue
c     gly
      go to 100
    2 continue
c     ala: CB(5)
      go to 100
    3 continue
c     val: CB(5)-CG1(6)-CG2(7)
      iabnd(7)=5
      go to 100
    4 continue
c     phe: CB(5)-CG(6)-CD1(7)-CD2(8)-CE1(9)-CE2(10)-CZ(11)
      iabnd(8)=6
      iabnd(9)=7
      iabnd(10)=8
      go to 100
    5 continue
c     ile: CB(5)-CG1(6)-CG2(7)-CD1(8)
      iabnd(7)=5
      iabnd(8)=6
      go to 100
    6 continue
c     leu: CB(5)-CG(6)-CD1(7)-CD2(8)
      iabnd(8)=6
      go to 100
    7 continue
c     pro: CB(5)-CG(6)-CD(7)
      go to 100
    8 continue
c     met: CB(5)-CG(6)-SD(7)-CE(8)
      ian0(7)=16
      rbdmax(7)=rmaxcs
      rbdmax(8)=rmaxcs
      rbdmin(7)=rmincs
      rbdmin(8)=rmincs
      go to 100
    9 continue
c     asp: CB(1)-CG(2)-OD1(3)-OD2(4)
      ian0(7)=8
      ian0(8)=8
      iabnd(8)=6
      rbdmax(7)=rmaxco
      rbdmax(8)=rmaxco
      rbdmin(7)=rminco
      rbdmin(8)=rminco
      go to 100
   10 continue
c     glu: CB(5)-CG(6)-CD(7)-OE1(8)-OE2(9)
      ian0(8)=8
      ian0(9)=8
      iabnd(9)=7
      rbdmax(8)=rmaxco
      rbdmax(9)=rmaxco
      rbdmin(8)=rminco
      rbdmin(9)=rminco
      go to 100
   11 continue
c     lys: CB(1)-CG(2)-CD(4)-CE(5)-NZ(6)
      ian0(9)=7
      rbdmax(9)=rmaxcn
      rbdmin(9)=rmincn
      go to 100
   12 continue
c     arg: CB(5)-CG(6)-CD(7)-NE(8)-CZ(9)-NH1(10)-NH2(11)
      ian0(8)=7
      ian0(10)=7
      ian0(11)=7
      iabnd(11)=9
      rbdmax(9)=rmaxcn
      rbdmax(10)=rmaxcn
      rbdmax(11)=rmaxcn
      rbdmin(9)=rmincn
      rbdmin(10)=rmincn
      rbdmin(11)=rmincn
      go to 100
   13 continue
c     ser: CB(5)-OG(6)
      ian0(6)=8
      rbdmax(6)=rmaxco
      go to 100
   14 continue
c     thr: CB(5)-OG1(6)-CG2(7)
      ian0(6)=8
      iabnd(7)=5
      rbdmax(6)=rmaxco
      rbdmin(6)=rminco
      go to 100
   15 continue
c     tyr: CB(5)-CG(6)-CD1(7)-CD2(8)-CE1(9)-CE2(10)-CZ(11)-OH(12)
      ian0(12)=8
      iabnd(8)=6
      iabnd(9)=7
      iabnd(10)=8
      rbdmax(12)=rmaxco
      rbdmin(12)=rminco
      go to 100
   16 continue
c     cys: CB(5)-SG(6)
      ian0(6)=16
      rbdmax(6)=rmaxcs
      rbdmin(6)=rmincs
      go to 100
   17 continue
c     asn: CB(5)-CG(6)-OD1(7)-ND2(8)
      ian0(7)=8
      ian0(8)=7
      iabnd(8)=6
      rbdmax(7)=rmaxco
      rbdmax(8)=rmaxcn
      rbdmin(7)=rminco
      rbdmin(8)=rmincn
      go to 100
   18 continue
c     gln: CB(5)-CG(6)-CD(7)-OE1(8)-NE2(9)
      ian0(8)=8
      ian0(9)=7
      iabnd(9)=7
      rbdmax(8)=rmaxco
      rbdmax(9)=rmaxcn
      rbdmin(8)=rminco
      rbdmin(9)=rmincn
      go to 100
   19 continue
c     his: CB(5)-CG(6)-ND1(7)-CD2(8)-CE1(9)-NE2(10)
      ian0(7)=7
      ian0(10)=7
      iabnd(8)=6
      iabnd(9)=7
      rbdmax(7)=rmaxcn
      rbdmax(10)=rmaxcn
      rbdmin(7)=rmincn
      rbdmin(10)=rmincn
      go to 100
   20 continue
c     trp: CB(5)-CG(6)-CD1(7)-CD2(8)-NE1(9)-CE2(10)-CE3(11)-CZ2(12)
c          -CZ3(13)-CH2(14)
      ian0(9)=7
      iabnd(8)=6
      iabnd(9)=7
      iabnd(11)=8
      iabnd(12)=10
      iabnd(13)=11
      rbdmax(9)=rmaxcn
      rbdmax(10)=rmaxcn
      rbdmin(9)=rmincn
      rbdmin(10)=rmincn
  100 continue
c
c     reorder heavy atoms if needed
      iant(1)=iani(1)
      xt(1)=xi(1)
      yt(1)=yi(1)
      zt(1)=zi(1)
      anmt(1)=anmi(1)
      idone(1)=1
      iord(1)=1
      ktry=0
      k=1
  200 continue
      j=iabnd(k+1)
      do 120 i=2,natm
      if(idone(i).ne.0) go to 120
      if(iani(i).eq.ian0(k+1)) then
         r=sqrt((xi(i)-xt(j))**2+(yi(i)-yt(j))**2+(zi(i)-zt(j))**2)
         if(r.lt.rbdmin(k+1)) go to 960
         if(r.lt.rbdmax(k+1)) go to 140
      endif
  120 continue
c     20:trp,15:tyr,4:phe, atoms 7 and 8 can be exchanged
      if(k+1.eq.9.and.(iresn.eq.4.or.iresn.eq.15.or.iresn.eq.20)) then
         iantmp=iant(7)
         xtmp=xt(7)
         ytmp=yt(7)
         ztmp=zt(7)
         atmp=anmt(7)
         iortmp=iord(7)
         iant(7)=iant(8)
         xt(7)=xt(8)
         yt(7)=yt(8)
         zt(7)=zt(8)
         anmt(7)=anmt(8)
         iord(7)=iord(8)
         iant(8)=iantmp
         xt(8)=xtmp
         yt(8)=ytmp
         zt(8)=ztmp
         anmt(8)=atmp
         iord(8)=iortmp
         ktry=ktry+1
         if(ktry.eq.1) go to 200
      endif
      go to 940
c
  140 continue
      ktry=0
      k=k+1
      iant(k)=iani(i)
      xt(k)=xi(i)
      yt(k)=yi(i)
      zt(k)=zi(i)
      anmt(k)=anmi(i)
      idone(i)=1
      iord(k)=i
      if(k.lt.natm) go to 200
c
      iod=0
      do 160 i=1,natm
      if(iord(i).ne.i) iod=1
  160 continue
      if(iord4.ne.0) iod=1
c
      return
c
c     error exit
  900 call msgout(0,1,'error(ordatm): res # should be .ge.1 and .le.20.
     .$')
      call msgout(0,0,' residue='//restmp//'$')
  910 call msgout(0,1,'error(ordatm): wrong number of heavy atoms in res
     .idue.$')
      call msgout(0,1,' residue='//restmp//'$')
      call msgou0(0,1,' residue number=$',ires)
      call msgou0(0,1,' correct number of atoms=$',natm)
      call msgou0(0,0,' input number of atoms  =$', natr)
  940 call msgout(0,1,'error(ordatm): there are atoms with no bond.$')
      call msgou0(0,1,' residue number=$',ires)
      call msgout(0,1,' residue='//restmp//'$')
      call msgout(0,1,' iord=$')
      call msgou1(0,0,natm,iord,1)
  960 call msgout(0,1,'error(ordatm): too short bond length.$')
      call msgou0(0,1,' residue number=$',ires)
      call msgout(0,1,' residue='//restmp//'$')
      call msgou0(0,1,' i=$',i)
      call msgou0(0,1,' j=$',j)
      call msgou2(0,0,1,r,4,1)
  980 call msgout(0,1,'error(ordatm): missing bond lengths.$')
      call msgou0(0,1,' residue number=$',ires)
      call msgout(0,1,' residue='//restmp//'$')
      call msgou0(0,1,' rcc=$',ifndcc)
      call msgou0(0,1,' rcn=$',ifndcn)
      call msgou0(0,1,' rco=$',ifndco)
      call msgou0(0,0,' rcs=$',ifndcs)
  990 call msgout(0,1,'error(ordatm): missing backborn atoms.$')
      call msgou0(0,1,' residue number=$',ires)
      call msgout(0,1,' residue='//restmp//'$')
      end
cs---------------------------------------------------------------------
      subroutine pdbatm(maxc,line,iatm,ian,atm,res,
     .                             chain,ires,x,y,z,sf,bf,alt)
c----------------------------------------------------------------------
c     pdb atomic coordinates (ATOM and HETATM)
c     data is assumed in the following format.
c     0   0    1    1    2    2    3    3    4    4    5    5    6    6    7
c     1234567890123456789012345678901234567890123456789012345678901234567890
c     ATOM      6  OG1 THR A   5      21.671  27.113 -14.079
c     HETATM 1721  C1  RET A 301      14.868  45.136   0.227
c     return ian=0 for an atom te be skipped
ce---------------------------------------------------------------------
      character*80 line,line1
      character*8  xc,yc,zc
      character    sc*5,bc*6
      character    elm*2,atm*4,res*3,elm1*1,elm2*2,atmnum*5,chain*1
      character    atmtmp*4,resnum*3,alt*1
      character    elmsav*2
      equivalence  (atmtmp,elm1),(atmtmp,elm2)
c
      ian=0
      x=0.0
      y=0.0
      z=0.0
      sf=0.0
      bf=0.0
      alt=line(17:17)
      elmsav=line(13:14)
c
      call strdup(maxc,line,7,11,line1)
      atmnum=line1(1:5)
      call strtoi(5,atmnum,iatm)
      call strdup(maxc,line,13,16,line1)
      atm=line1(1:4)
c
      atmtmp=atm
      call strsiz(4,atmtmp,nt)
      call strtyp(1,elm1,ntyp)
      if(ntyp.eq.0) call strsft(4,atmtmp,1)
c     residue
      call strdup(maxc,line,18,20,line1)
      res=line1(1:3)
      call resid(res,iresid,0,0)
c     if DOD, change to HOH
      if(res.eq.'dod') res='hoh'
c     element
      call elmchr(elm2,ielm)
      if(ielm.eq.2) then
         elm(1:2)=atmtmp(1:2)
      else
         elm(1:1)=atmtmp(1:1)
         elm(2:2)=' '
      endif
c     if D, change it to H
      if(elm.eq.'d ') elm='h '
c     ca is spcial
      if(elmsav.eq.'ca') then
         elm=elmsav
      endif
      call elmian(elm,ian,0)
c     chain
      call strdup(maxc,line,22,23,line1)
      chain=line1(1:1)
c     res number
      call strdup(maxc,line,24,26,line1)
      resnum=line1(1:3)
c     x-coord
      call strdup(maxc,line,31,38,line1)
      xc=line1(1:8)
c     y-coord
      call strdup(maxc,line,39,46,line1)
      yc=line1(1:8)
c     z-coord
      call strdup(maxc,line,47,54,line1)
      zc=line1(1:8)
c     sc
      call strdup(maxc,line,56,60,line1)
      sc=line1(1:5)
c     bc
      call strdup(maxc,line,61,66,line1)
      bc=line1(1:6)
c     ires
      call strtoi(3,resnum,ires)
c     store in common
      call strtyp(8,xc,ntypxc)
      call strtyp(8,yc,ntypyc)
      call strtyp(8,zc,ntypzc)
      call strtor(8,xc,x)
      call strtor(8,yc,y)
      call strtor(8,zc,z)
      call strtor(5,sc,sf)
      call strtor(6,bc,bf)

c
c  100 continue
      return
c  900 call msgout(0,0,'error(pdbatm): the input file is not PDB file.$')
      end
cs---------------------------------------------------------------------
      subroutine pdbsel(iout,nspres,ispres,nsel,jatij,isel)
c----------------------------------------------------------------------
c     save reference and selected residues in PDB format
ce---------------------------------------------------------------------
      character*6 label(20),labtmp
      character*2 chatmp
      character*3 restmp
      character*4 atmtmp
      dimension   ispres(*),jatij(*),isel(*)
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      idum=0
      jdum=0
c     comment ; res#, resnam, istatm, iedatm
      write(iout,1000)
 1000 format('REMARK            res #, res name, atom #s (the first and 
     .the last atom)')
      k=0
      do 20 i=1,nspres
      ires=ispres(i)
      ist=istres(ires)
      ied=istres(ires+1)-1
      write(iout,1200) ires,resnam(ires),ist,ied
 1200 format('REMARK reference',i5,2x,a3,2x,2i8)
      k=k+1
      isel(k)=ires
   20 continue
      do 40 i=1,nsel
      iat=jatij(i)
      call atmres(iat,ires)
      ist=istres(ires)
      ied=istres(ires+1)-1
      write(iout,1400) ires,resnam(ires),ist,ied
 1400 format('REMARK selected ',i5,2x,a3,2x,2i8)
      k=k+1
      isel(k)=ires
c     s-s bonded cys's 
      call resmol(ires,imol,idum,jdum)
      call ssbcys(0,ires,jres)
      if(jres.ne.0) then
         k=k+1
         isel(k)=-jres
         jst=istres(jres)
         jed=istres(jres+1)-1
         write(iout,1400) jres,resnam(jres),jst,jed
      endif
   40 continue
      nselt=k
      isel(nselt+1)=0
c
c     label 1:atom,2:hetatm,3:conect,4:end,5:ter,6:seqres,7:helix,8:sheet,
c           9:title,10:link,11:remark
      call defpdb(label)
c
      chatmp='  '
      k=0
      do 160 j=1,nselt
      ires=iabs(isel(j))
      call resmol(ires,imol,idum,jdum)
      ist=istres(ires)
      ied=istres(ires+1)-1
      numtmp=numres(ires)
      restmp=resnam(ires)
      call chcase(3,restmp,1)
      call resid(resnam(ires),iresid,0,0)
      if(iresid.eq.0) then
         labtmp=label(2)
      else
         labtmp=label(1)
      endif
      call chcase(6,labtmp,1)
c
      do 100 i=ist,ied
      k=k+1
      atmtmp=atmnam(i)
      call chcase(4,atmtmp,1)
      write(iout,2000) labtmp,k,atmtmp,restmp,chatmp,numtmp,
     .                                 x(i),y(i),z(i)
 2000 format(a6,i5,1x,a4,1x,a3,1x,a2,i3,4x,3f8.3)
  100 continue
c  120 continue
      if(isel(j+1).lt.0) go to 160
      if(iabs(isel(j)).ne.iabs(isel(j+1))-1) then
         k=k+1
         labtmp=label(5)
         call chcase(6,labtmp,1)
c        write "TER"
         write(iout,2020) labtmp,k
 2020    format(a6,i5)
      endif
  160 continue
c
c     connect data
      labtmp=label(3)
      call chcase(6,labtmp,1)
c??? CONECT data
c      do 220 i=1,nbnd
c      nb=nbond(i)
c      write(iout,3000) labtmp,ibond(i,1),(ibond(i,j+1),j=1,nb)
c 3000 format(1x,a6,9i5)
c  220 continue
c
c     write "END" at the end
      labtmp=label(4)
      call chcase(6,labtmp,1)
      write(iout,3200) labtmp
 3200 format(a6)
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prmcbl
c----------------------------------------------------------------------
c     set covalent bond length in common/cbdlen/
ce---------------------------------------------------------------------
      parameter (MaxBdL=50)
      common/cbdlen/ncbd,ncbdx,iatnum(MaxBdL),jatnum(MaxBdL),
     .       ijbnd(MaxBdL),rstdij(MaxBdL),rminij(MaxBdL),rmaxij(MaxBdL)
      dimension  rch(3),rnh(2),roh(2),rsh(2)
      dimension  rcc(4),rcn(2),rco(2),rcs(2),rss(2)
      data       rdel/0.15/,dss/0.22/
      data       rch/1.09,1.08,1.07/,     nch/3/
      data       rnh/1.01,1.01/,          nnh/2/
      data       roh/0.96,0.96/,          noh/2/
      data       rsh/1.33,0.0/,           nsh/1/
      data       rcc/1.54,1.35,1.24,1.40/,ncc/4/
      data       rcn/1.45,1.40/,          ncn/2/
      data       rco/1.43,1.23/,          nco/2/
      data       rcs/1.81,0.0/,           ncs/1/
      data       rss/2.05,0.0/,           nss/1/
      save       rch,rnh,roh,rsh
      save       rcc,rcn,rco,rcs,rss
      save       ncc,ncn,nco,ncs,nss
      save       nch,nnh,noh,nsh
      save       rdel
c
c     note:iatnum(i) < jatnum(i)
      ncbd=0
c     c-c bonds
      do 20 i=1,ncc
      k=ncbd+i
      iatnum(k)=6
      jatnum(k)=6
      ijbnd(k)=i
      rstdij(k)=rcc(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
   20 continue
      ncbd=ncbd+ncc
c     c-n bond
      do 40 i=1,ncn
      k=ncbd+i
      iatnum(k)=6
      jatnum(k)=7
      ijbnd(k)=i
      rstdij(k)=rcn(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
   40 continue
      ncbd=ncbd+ncn
c     c-o bond
      do 60 i=1,nco
      k=ncbd+i
      iatnum(k)=6
      jatnum(k)=8
      ijbnd(k)=i
      rstdij(k)=rco(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
   60 continue
      ncbd=ncbd+nco
c     c-s bond
      do 80 i=1,ncs
      k=ncbd+i
      iatnum(k)=6
      jatnum(k)=16
      ijbnd(k)=i
      rstdij(k)=rcs(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
   80 continue
      ncbd=ncbd+ncs
c     s-s bond
      do 100 i=1,nss
      k=ncbd+i
      iatnum(k)=16
      jatnum(k)=16
      ijbnd(k)=i
      rstdij(k)=rss(i)
      rminij(k)=rstdij(k)-dss
      rmaxij(k)=rstdij(k)+dss
  100 continue
      ncbd=ncbd+nss
c     ch bond
      do 120 i=1,nch
      k=ncbd+i
      iatnum(k)=1
      jatnum(k)=6
      ijbnd(k)=i
      rstdij(k)=rch(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
  120 continue
      ncbd=ncbd+nch
c     nh bond
      do 140 i=1,nnh
      k=ncbd+i
      iatnum(k)=1
      jatnum(k)=7
      ijbnd(k)=i
      rstdij(k)=rnh(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
  140 continue
      ncbd=ncbd+nnh
c     oh bond
      do 160 i=1,noh
      k=ncbd+i
      iatnum(k)=1
      jatnum(k)=8
      ijbnd(k)=i
      rstdij(k)=roh(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
  160 continue
      ncbd=ncbd+noh
c     sh bond
      do 180 i=1,nsh
      k=ncbd+i
      iatnum(k)=1
      jatnum(k)=16
      ijbnd(k)=i
      rstdij(k)=rsh(i)
      rminij(k)=rstdij(k)-rdel
      rmaxij(k)=rstdij(k)+rdel
  180 continue
      ncbd=ncbd+nsh
c
      return
c     error exit
c  920 call msgout(0,1,'error(prmcbl): wrong covalent bond data.$')
c      call msgou0(0,1,' atomic number i=$',iat)
c      call msgou0(0,1,' atomic number j=$',jat)
c      call msgou0(0,0,' bond multiplicity=$',ijbd)
      end
cs---------------------------------------------------------------------
      subroutine prmcbr
c----------------------------------------------------------------------
c     set covalent radii in common/cbdrad/
ce---------------------------------------------------------------------
      common/cbdrad/ncvdat,ncbdum,radcbd(100)
      dimension cvr(100)
      data      ncvr/100/
      data cvr/0.3,1.5,1.225,1.06,0.88,0.77,0.7,0.66,0.64,1.5,
     . 1.572,1.364,1.248,1.173,1.1,1.04,0.99,1.5,2.025,1.736,
     . 1.439,1.324,1.224,1.176,1.171,1.165,1.162,1.154,1.173,1.249,
     . 1.245,1.223,1.18,1.14,1.11,1.5,2.16,1.914,1.616,1.454,
     . 1.342,1.296,1.271,1.246,1.252,1.283,1.33,1.413,1.497,1.399,
     . 1.36,1.32,1.28,1.5,2.35,1.981,1.69,1.5,1.5,1.5,
     . 1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,
     . 1.442,1.442,1.343,1.304,1.283,1.26,1.265,1.295,1.336,1.44,
     . 1.549,1.538,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,
     . 1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5/
       save ncvr,cvr
c
      ncvdat=ncvr
      do 100 i=1,ncvdat
      radcbd(i) = cvr(i)
  100 continue
c
       return
       end
cs---------------------------------------------------------------------
      subroutine prmhbl
c----------------------------------------------------------------------
c     set hydrogen bond length in common/hbdlen/
ce---------------------------------------------------------------------
      parameter (MaxHBL=50)
      common/hbdlen/nhbd,nhbdx,iatnum(MaxHBL),jatnum(MaxHBL),
     .              rstdij(MaxHBL),rminij(MaxHBL),rmaxij(MaxHBL)
c     note: the following data is temporal
      data       rnnstd/3.0/,rnnmin/2.5/,rnnmax/3.3/
      data       rnostd/3.0/,rnomin/2.5/,rnomax/3.3/
      data       rnsstd/3.3/,rnsmin/2.8/,rnsmax/3.6/
      data       roostd/3.0/,roomin/2.5/,roomax/3.3/
      data       rosstd/3.3/,rosmin/2.8/,rosmax/3.6/
      data       rssstd/3.6/,rssmin/3.0/,rssmax/3.8/
      save       rnnstd,rnostd,rnsstd,roostd,rosstd,rssstd
      save       rnnmin,rnomin,rnsmin,roomin,rosmin,rssmin
      save       rnnmax,rnomax,rnsmax,roomax,rosmax,rssmax
c
c     note:iatnum(i) < jatnum(i)
      nhbd=0
c     n-n bonds
      nhbd=nhbd+1
      iatnum(nhbd)=7
      jatnum(nhbd)=7
      rstdij(nhbd)=rnnstd
      rminij(nhbd)=rnnmin
      rmaxij(nhbd)=rnnmax
c     n-o
      nhbd=nhbd+1
      iatnum(nhbd)=7
      jatnum(nhbd)=8
      rstdij(nhbd)=rnostd
      rminij(nhbd)=rnomin
      rmaxij(nhbd)=rnomax
c     n-s
      nhbd=nhbd+1
      iatnum(nhbd)=7
      jatnum(nhbd)=16
      rstdij(nhbd)=rnsstd
      rminij(nhbd)=rnsmin
      rmaxij(nhbd)=rnsmax
c     o-o
      nhbd=nhbd+1
      iatnum(nhbd)=8
      jatnum(nhbd)=8
      rstdij(nhbd)=roostd
      rminij(nhbd)=roomin
      rmaxij(nhbd)=roomax
c     o-s
      nhbd=nhbd+1
      iatnum(nhbd)=8
      jatnum(nhbd)=16
      rstdij(nhbd)=rosstd
      rminij(nhbd)=rosmin
      rmaxij(nhbd)=rosmax
c     s-s
      nhbd=nhbd+1
      iatnum(nhbd)=16
      jatnum(nhbd)=16
      rstdij(nhbd)=rssstd
      rminij(nhbd)=rssmin
      rmaxij(nhbd)=rssmax
c
      return
c     error exit
c  900 call msgout(0,1,'error(prmhbl): increase MaxBdL. MaxBdL=$')
c      call msgou0(0,0,' MaxBdL=$',MaxBdL)
c  920 call msgout(0,1,'error(prmhbl): wrong covalent bond data.$')
c      call msgou0(0,1,' atomic number i=$',iat)
c      call msgou0(0,0,' atomic number j=$',jat)
      end
cs---------------------------------------------------------------------
      subroutine prmvdw
c----------------------------------------------------------------------
c     set vdw radii /vdwrad/
ce---------------------------------------------------------------------
      common/vdwrad/nvdw,nvdwd,rvdw(100)
      dimension vdwr(100)
c     unknown values are set to 1.8 A
      data      vdwr/1.20,1.20,1.37,1.45,1.45,1.50,1.50,1.40,
     .               1.35,1.30,1.57,1.36,1.24,1.17,1.80,1.75,
     .               1.70,83*1.80/
       data     nv/100/
       save nv,vdwr
c
      nvdw=nv
      nvdwd=36
      do 100 i=1,nvdw
      rvdw(i) = vdwr(i)
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prmset(iunit,iprcbl,iprcbr,iprhbl,iprvdw)
c----------------------------------------------------------------------
c     add or replace paramters, covalent bond length, covalent bond radii
c     hydrogen bond lengths, and vdw radii, with external values.
c     iprxxx ... print flags. =0 print, =1 don't print. actual print will
c                be done at "prtprm"
ce---------------------------------------------------------------------
c
      iprcbl=1
      iprcbr=1
      iprhbl=1
      iprvdw=1
      call redcbl(iunit,iprcbl)
      call redcbr(iunit,iprcbr)
      call redhbl(iunit,iprhbl)
      call redvdw(iunit,iprvdw)
c
      return
      end
cs---------------------------------------------------------------------
      subroutine redcbl(iunit,iprcbl)
c----------------------------------------------------------------------
c     add or replace covalent bond length.
c     data format;
c     element #1, element #2, bond multiplicity, standard bond length, 
c     minimum bond length, and maximum bond length.
c     ex. 1 6 1 1.09 0.9 1.1 for c-h single bond
ce---------------------------------------------------------------------
c     covalent bond lengths
      parameter (MaxBdL=50)
      common/cbdlen/ncbd,ncbdum,iatcbd(MaxBdL),jatcbd(MaxBdL),
     .       mulcbd(MaxBdL),rstcbd(MaxBdL),rmncbd(MaxBdL),rmxcbd(MaxBdL)
      character*80 line,line1
      character head*7,tail*4,print*5,on*2
      data head/'$prmcbl'/,tail/'$end'/
      data print/'print'/,on/'on'/
      data maxc/80/
      save maxc,head,tail,print,on
c
      iprcbl=1
      rewind iunit
   20 continue
      read(iunit,1000,end=100) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
c     skip a blank line and line with ";" at top
      if(nc.le.0) go to 20
      if(line(1:1).eq.';') go to 20
      call chcase(maxc,line,0)
c     find $prmcbl
      if(line(1:7).eq.head) then
         call strtok(maxc,line,nc,line1,mc)
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprcbl=0
         endif
   80    read(iunit,1000,end=100) line
         call strsiz(maxc,line,nc)
c        skip a blank line and line with ";" at top
         if(nc.le.0) go to 80
         if(line(1:1).eq.';') go to 80
         call chcase(maxc,line,0)
c        $end
         if(line(1:4).eq.tail) go to 20
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprcbl=0
            go to 80
         endif
c        element #1, #2, and bond multip
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian1)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian2)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 920
         call strtoi(maxc,line1,mul)
c        rstd,rmin,rmax
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rstd)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rmin)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rmax)
c        replace or add data
         if(ian1.gt.ian2) then
            iant=ian1
            ian1=ian2
            ian2=iant
         endif
         ifnd=0
         do 40 i=1,ncbd
         if(ian1.eq.iatcbd(i).and.ian2.eq.jatcbd(i).
     .                               and.mulcbd(i).eq.mul) then
            ifnd=i
            go to 60
         endif
   40    continue
   60    continue
         if(ifnd.eq.0) then
            ncbd=ncbd+1
            if(ncbd.gt.MaxBdL) go to 960
            iupd=ncbd
         else
            iupd=ifnd
         endif
         iatcbd(iupd)=ian1
         jatcbd(iupd)=ian2
         mulcbd(iupd)=mul
         rstcbd(iupd)=rstd
         rmncbd(iupd)=rmin
         rmxcbd(iupd)=rmax
         go to 80
      endif
      go to 20
c
  100 continue
      return
  900 call msgout(0,1,'error(redcbl): wrong element #.$')
      call msgout(0,0,' input:'//line1(1:mc)//'$')
  920 call msgout(0,1,'error(redcbl): wrong bond multiplicity.$')
      call msgout(0,0,' input:'//line1(1:mc)//'$')
  940 call msgout(0,1,'error(redcbl): wrong bond length data.$')
      call msgout(0,0,' input:'//line1(1:mc)//'$')
  960 call msgout(0,1,'error(redcbl): recompile the program with larger 
     .MaxBdL.$')
      call msgou0(0,0,' MaxBdL=$',MaxBdL)
      end
cs---------------------------------------------------------------------
      subroutine redhbl(iunit,iprhbl)
c----------------------------------------------------------------------
c     add or replace hydrogen bond length.
c     data format;
c     element #1, element #2, standard bond length, minimum bond length,
c     and maximum bond length.
c     ex. 8 8 3.0 2.4 3.2 for o...o hydrogen bond
ce---------------------------------------------------------------------
c     hydrogen bond lengths
      parameter (MaxHBL=50)
      common/hbdlen/nhbd,nhbdum,iathbd(MaxHBL),jathbd(MaxHBL),
     .              rsthbd(MaxHBL),rmnhbd(MaxHBL),rmxhbd(MaxHBL)
      character*80 line,line1
      character head*7,tail*4,print*5,on*2
      data head/'$prmhbl'/,tail/'$end'/
      data print/'print'/,on/'on'/
      data maxc/80/
      save maxc,head,tail,print,on
c
      iprhbl=1
      rewind iunit
   20 continue
      read(iunit,1000,end=100) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
c     skip a blank line and line with ";" at top
      if(nc.le.0) go to 20
      if(line(1:1).eq.';') go to 20
      call chcase(maxc,line,0)
c     find $prmhbl
      if(line(1:7).eq.head) then
         call strtok(maxc,line,nc,line1,mc)
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprhbl=0
         endif
   80    read(iunit,1000,end=100) line
         call strsiz(maxc,line,nc)
c        skip a blank line and line with ";" at top
         if(nc.le.0) go to 80
         if(line(1:1).eq.';') go to 80
         call chcase(maxc,line,0)
c        $end
         if(line(1:4).eq.tail) go to 20
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprhbl=0
            go to 80
         endif
c        element #1, and #2
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian1)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian2)
c        rstd,rmin,rmax
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rstd)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rmin)
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rmax)
c        replace or add data
         if(ian1.gt.ian2) then
            iant=ian1
            ian1=ian2
            ian2=iant
         endif
         ifnd=0
         do 40 i=1,nhbd
         if(ian1.eq.iathbd(i).and.ian2.eq.jathbd(i)) then
            ifnd=i
            go to 60
         endif
   40    continue
   60    continue
         if(ifnd.eq.0) then
            nhbd=nhbd+1
            if(nhbd.gt.MaxHBL) go to 960
            iupd=nhbd
         else
            iupd=ifnd
         endif
         iathbd(iupd)=ian1
         jathbd(iupd)=ian2
         rsthbd(iupd)=rstd
         rmnhbd(iupd)=rmin
         rmxhbd(iupd)=rmax
         go to 80
      endif
      go to 20
c
  100 continue
      return
  900 call msgout(0,1,'error(redhbl): wrong element #.$')
      call msgout(0,0,' input:'//line1(1:mc)//'$')
  940 call msgout(0,1,'error(redhbl): wrong bond length data.$')
      call msgout(0,0,' input:'//line1(1:mc)//'$')
  960 call msgout(0,1,'error(redhbl): recompile the program with larger 
     .MaxBHL.$')
      call msgou0(0,0,' MaxHBL=$',MaxHBL)
      end
cs---------------------------------------------------------------------
      subroutine redcbr(iunit,iprcbr)
c----------------------------------------------------------------------
c     replace covalent bond radius.
c     data format;
c     element #1, covalent bond radius, 
c     ex. 6 0.7 for carbon atom
ce---------------------------------------------------------------------
c     covalent bond radii
      common/cbdrad/ncvr,ncrdum,radcbd(100)
      character*80 line,line1
      character head*7,tail*4,print*5,on*2
      data head/'$prmcbr'/,tail/'$end'/
      data print/'print'/,on/'on'/
      data maxc/80/
      save maxc,head,tail,print,on
c
      iprcbr=1
      rewind iunit
   20 continue
      read(iunit,1000,end=100) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
c     skip a blank line and line with ";" at top
      if(nc.le.0) go to 20
      if(line(1:1).eq.';') go to 20
      call chcase(maxc,line,0)
c     find $prmcbl
      if(line(1:7).eq.head) then
         call strtok(maxc,line,nc,line1,mc)
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprcbr=0
         endif
   80    read(iunit,1000,end=100) line
         call strsiz(maxc,line,nc)
c        skip a blank line and line with ";" at top
         if(nc.le.0) go to 80
         if(line(1:1).eq.';') go to 80
         call chcase(maxc,line,0)
c        $end
         if(line(1:4).eq.tail) go to 20
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprcbr=0
            go to 80
         endif
c        element #
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian1)
         if(ian1.lt.0.or.ian1.gt.ncvr) go to 900
c        r
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rstd)
c        replace data
         radcbd(ian1)=rstd
         go to 80
      endif
      go to 20
c
  100 continue
      return
  900 call msgout(0,1,'error(redcbr): wrong element #.$')
      call msgou0(0,0,' atomic number=$',ian1)
  940 call msgout(0,0,'error(redcbr): missing length data.$')
      end
cs---------------------------------------------------------------------
      subroutine redvdw(iunit,iprvdw)
c----------------------------------------------------------------------
c     replace vdw radius
c     data format;
c     element #1, vdw radius, 
c     ex. 6 1.5 for carbon atom
ce---------------------------------------------------------------------
c     van der waals radii
      common/vdwrad/nvdw,nvddum,rvdw(100)
      character*80 line,line1
      character head*7,tail*4,print*5,on*2
      data head/'$prmvdw'/,tail/'$end'/
      data print/'print'/,on/'on'/
      data maxc/80/
      save maxc,head,tail,print,on
c
      iprvdw=1
      rewind iunit
   20 continue
      read(iunit,1000,end=100) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
c     skip a blank line and line with ";" at top
      if(nc.le.0) go to 20
      if(line(1:1).eq.';') go to 20
      call chcase(maxc,line,0)
c     find $prmcbl
      if(line(1:7).eq.head) then
         call strtok(maxc,line,nc,line1,mc)
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprvdw=0
         endif
   80    read(iunit,1000,end=100) line
         call strsiz(maxc,line,nc)
c        skip a blank line and line with ";" at top
         if(nc.le.0) go to 80
         if(line(1:1).eq.';') go to 80
         call chcase(maxc,line,0)
c        $end
         if(line(1:4).eq.tail) go to 20
         if(line(1:5).eq.print) then
c           check print flag
            call strtk1(maxc,line,nc,line1,mc,'=')
            if(line(1:2).eq.on) iprvdw=0
            go to 80
         endif
c        element #
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 900
         call strtoi(maxc,line1,ian1)
         if(ian1.lt.0.or.ian1.gt.nvdw) go to 900
c        r
         call strtok(maxc,line,nc,line1,mc)
         if(mc.le.0) go to 940
         call strtor(maxc,line1,rstd)
c        replace data
         rvdw(ian1)=rstd
         go to 80
      endif
      go to 20
c
  100 continue
      return
  900 call msgout(0,1,'error(redvdw): wrong element #.$')
      call msgou0(0,0,' atomic number=$',ian1)
  940 call msgout(0,0,'error(redcbr): missing length data.$')
      end
cs---------------------------------------------------------------------
      subroutine prtprm(iout,iprcbl,iprcbr,iprhbl,iprvdw)
c----------------------------------------------------------------------
c     print paramters, covalent bond length, covalent bond radii
c     hydrogen bond lengths, and vdw radii.
c     iprxxx ... print flags. =0 print, =1 don't print
ce---------------------------------------------------------------------
c     covalent bond lengths
      parameter (MaxBdL=50)
      common/cbdlen/ncbd,ncbdum,iatcbd(MaxBdL),jatcbd(MaxBdL),
     .       mulcbd(MaxBdL),rstcbd(MaxBdL),rmncbd(MaxBdL),rmxcbd(MaxBdL)
c     covalent bond radii
      common/cbdrad/ncbr,ncrdum,radcbd(100)
c     hydrogen bond lengths
      parameter (MaxHBL=50)
      common/hbdlen/nhbd,nhbdum,iathbd(MaxHBL),jathbd(MaxHBL),
     .              rsthbd(MaxHBL),rmnhbd(MaxHBL),rmxhbd(MaxHBL)
c     van der waals radii
      common/vdwrad/nvdw,nvddum,rvdw(100)
c
      if(iprcbl.eq.0) then
c        print covelent bond lengths
         write(iout,1000)
 1000    format(' Covalent Bond Lengths (A)')
         write(iout,1200)
 1200    format(' ser#, elem #1, elem #2, bond type, r(std), r(min), r(m
     .ax)')
         do 100 i=1,ncbd
         write(iout,1400) i,iatcbd(i),jatcbd(i),mulcbd(i),rstcbd(i),
     .                    rmncbd(i),rmxcbd(i)
 1400    format(i4,3i6,3f10.3)
  100    continue
      endif
c
      if(iprcbr.eq.0) then
c        print covalent bond radius
         write(iout,2000)
 2000    format(' Covalent Bond Radius (A)')
         write(iout,2200)
 2200    format(' element#, radius(A)')
         do 200 i=1,ncbr
         write(iout,2400) i,radcbd(i)
 2400    format(i10,f10.3)
  200    continue
      endif
c
      if(iprhbl.eq.0) then
c        print h-bond lengths
         write(iout,3000)
 3000    format(' Hydrogen Bond Length (A)')
         write(iout,3200)
 3200    format(' ser#, elem #1, elem #2, r(std), r(min), r(max)')
         do 300 i=1,nhbd
         write(iout,3400) i,iathbd(i),jathbd(i),rsthbd(i),
     .                    rmnhbd(i),rmxhbd(i)
 3400    format(i6,2x,2i6,3f10.3)
  300    continue
      endif
c
      if(iprvdw.eq.0) then
c        print vdw radii
         write(iout,4000)
 4000    format(' van der Waals Radius (A)')
         write(iout,4200)
 4200    format(' element#, radius(A)')
         do 400 i=1,nvdw
         write(iout,4400) i,rvdw(i)
 4400    format(i10,f10.3)
  400    continue
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prtfrg(iout,nfgsiz,ifcys,ifgly,imlss,ndiffs)
c----------------------------------------------------------------------
c     print fragment information
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxMol=50000,MaxFrg=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      character resnm3*3,resnm1*1
      common/reslab/kres,resnm3(20),resnm1(20)
      dimension   nresid(20)
c
      if(imlss.eq.0) then
         write(iout,1010)
 1010    format('; there is intermolecular s-s bond.',/,'; so, informati
     .on of each molecule is not printed out.')
      endif
      write(iout,1000)
 1000 format(';---------------------------------------------------------
     .-------------')
      write(iout,1020)
 1020 format('; frg#, #atm, chg,   frg names,                   res#s of
     . the frg')
      write(iout,1000)
c
      nattot=0
      ichtot=0
      if(imlss.eq.0) then
         istm=1
         iedm=1
      else
         istm=1
         iedm=nmol
      endif
      do 100 imol=istm,iedm
      natmol=0
      ichm=0
      if(imlss.eq.0) then
         ist=1
         ied=nfrg
      else
         call istfgm(imol,ist,ied)
      endif
      do 80 i=ist,ied
      nrf=nresfg(i)
      nati=0
      do 20 j=1,natm
   20 if(iatfrg(j).eq.i) nati=nati+1
      write(iout,2000) i,nati,ichfrg(i),frgnam(i),(iresfg(j,i),j=1,nrf)
 2000 format(';',3i5,5x,a24,5x,8i5)
      natmol=natmol+nati
      nattot=nattot+nati
      ichm=ichm+ichfrg(i)
      ichtot=ichtot+ichfrg(i)
   80 continue
      if(imlss.ne.0) then
         write(iout,2200) imol
 2200    format('; imol = ',i5)
         write(iout,2210) natmol,ichm
 2210    format('; total # of atoms = ',i5,2x,/,'; total charge = ',i3)
      endif
      write(iout,1000)
  100 continue
c
      write(iout,3040) ichtot
 3040 format('; charge of total system =',i5)
      write(iout,3000) nssbnd
 3000 format('; s-s bond in the system =',i5)
      call cnters(nresid,nrest,nace,nnme,nwater,nonres)
      write(iout,3005)
 3005 format('; number of each residue in the system')
      write(iout,3010) (resnm3(i),i=1,14)
 3010 format(';',14(2x,a3))
      write(iout,3015) (nresid(i),i=1,14)
 3015 format(';',14(1x,i4))
      write(iout,3011) (resnm3(i),i=15,20)
 3011 format(';',6(2x,a3),'  ace  nme  hoh  non-peptide')
      write(iout,3015) (nresid(i),i=15,20),nace,nnme,nwater,nonres
c     diffuse functions on COO- groups
      if(ndiffs.gt.0) then
         ndfgrp=ndiffs/3
         write(iout,4020) ndfgrp
 4020    format('; the number of COO- groups where diffuse functions wer
     .e put =',i5)
      endif
      write(iout,3020) nfgsiz,ifcys+1,ifgly+1
 3020 format('; fragmentation options: nfgsiz,ifcys,ifgly ',3i5)
c     check total number of atoms
      if(nattot.ne.natm) then
         write(iout,9000) natm,nattot
 9000    format(';',/,1x,
     .          'ERROR: automatic fragmentation was failed. ',
     .                 'natm =',i6,2x,'nattot =',i6,/,
     .          '  please check data. unassingned atoms are,')
         do 120 i=1,natm
         if(iatfrg(i).eq.0) then
            call atmres(i,ires)
            write(iout,9010) i,ires
 9010       format(i8,2x,'in residue',i5)
         endif
  120    continue
      endif
c
      if(nssbnd.gt.0.and.ifcys.eq.1) then
         write(iout,9200)
 9200    format(';',/,
     .          '; !!! WARNING: The system has S-S bonded cysteins.',/,
     .          ';     This output can not be used as the input data for
     . FMO calculations.')
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prtsel(iout,nspres,ispres,rthre,iodr,key,
     .                                  nsel,iatij,jatij,dminij)
c----------------------------------------------------------------------
c     print res distance from ispres
c     nspres ... number of residues to be measured
c     ispres ... res number from which distance of othre res are measured
c     rthre ... threshould distance in vdw (key=0) or in A (key=1)
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxMol=50000)
      dimension     ispres(*),iatij(*),jatij(*),dminij(*)
      character*3   temp
      character*6   rstmpi,rstmpj
      character*1   sy
      character*2   ciatm,cjatm
      dimension     iord(MaxRes),scr(MaxRes)
      dimension     idone(MaxRes)
      equivalence   (iord,idone)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
c     count number of atoms
      ichsel=0
      ichref=0
      nspt=0
      nsphv=0
      nsph=0
      do 220 ii=1,nspres
      i=ispres(ii)
      ichref=ichref+ichres(i)
      ist=istres(i)
      ied=istres(i+1)-1
      nspt=nspt+ied-ist+1
      do 210 j=ist,ied
      if(ian(j).eq.1) then
         nsph=nsph+1
      else
         nsphv=nsphv+1
      endif
  210 continue
  220 continue
      nselt=0
      nselhv=0
      nselh=0
      do 240 ii=1,nsel
      iat=jatij(ii)
      call atmres(iat,i)
      ichsel=ichsel+ichres(i)
      ist=istres(i)
      ied=istres(i+1)-1
      nselt=nselt+ied-ist+1
      do 230 j=ist,ied
      if(ian(j).eq.1) then
         nselh=nselh+1
      else
         nselhv=nselhv+1
      endif
  230 continue
  240 continue
      ichtot=ichref+ichsel
c
c     order with distance key
      if(iodr.eq.0) then
         call rsort1(nsel,dminij,scr,iord)
      else
         do 260 i=1,nsel
  260    iord(i)=i
      endif
c
c      write(iout,*) ' iord ',(iord(k),k=1,nsel)
c
c     print out
      write(iout,1200) (ispres(k),k=1,nspres)
 1200 format(' # of reference residue(s) ',10i5)
      if(key.eq.0) then
         write(iout,1000) rthre,nsel
 1000    format(' # of selected residues within ',f10.3,' vdw  ',i5)
      elseif(key.eq.1) then
         write(iout,1100) rthre,nsel
 1100    format(' # of selected residues within ',f10.3,' A ',i5)
      endif
      write(iout,1300) nspt,nsphv,nsph
 1300 format(' # of atoms in ref res(total,heavy,hydrogen) ',3i5)
      write(iout,1400) nselt,nselhv,nselh
 1400 format(' # of atoms in selected res                  ',3i5)
      write(iout,1500) nselt+nspt,nselhv+nsphv,nselh+nsph
 1500 format(' total number of atoms in ref+sel            ',3i5)
      write(iout,1510) ichref,ichsel,ichtot
 1510 format(' charges of ref, selected, and ref+sel       ',3i5)
      write(iout,*) ' '
      write(iout,1600)
 1600 format(' #, ref res & mol, sel res & mol, ref atm#, sel atm#,  r(A
     .),  r(vdw), elms, # atms')
      nrat=0
      do 320 k=1,nsel
         j=iord(k)
         iatm=iatij(j)
         jatm=jatij(j)
         rvdw=rwaals(ian(iatm))+rwaals(ian(jatm))
         if(key.eq.0) then
            dvdw=dminij(j)
            dmin=dvdw*rvdw
         else
            dmin=dminij(j)
            dvdw=dmin/rvdw
         endif
         call atmres(iatm,ires)
         call resmol(ires,imol,ifres,ilres)
         call atmres(jatm,jres)
         call resmol(jres,jmol,jfres,jlres)
         int=numres(ires)
         call cnint(3,int,3,temp)
         rstmpi=resnam(ires)//temp(1:3)
         int=nummol(imol)
         moli=int
         call cnint(3,int,3,temp)
c         mltmpi=molnam(ires)//temp(1:3)
         call cnint(3,jmol,3,temp)
c         mltmpj=molnam(jmol)//temp(1:3)
         molj=nummol(jmol)
         j1=jatm-istres(jres)+1
         i1=iatm-istres(ires)+1
         int=numres(jres)
         call cnint(3,int,3,temp)
         rstmpj=resnam(jres)//temp(1:3)
         nrat=nrat+istres(jres+1)-istres(jres)
         call elmian(ciatm,ian(iatm),1)
         call elmian(cjatm,ian(jatm),1)
         call chcase(2,ciatm,1)
         call chcase(2,cjatm,1)
         sy=' '
         if(ichres(jres).gt.0) sy='+'
         if(ichres(jres).lt.0) sy='-'
         write(iout,3000) k,ires,rstmpi,moli,jres,sy,rstmpj,molj,
     .                    iatm,i1,jatm,j1,dmin,dvdw,ciatm,cjatm,nrat
 3000    format(i3,i5,1x,a6,1x,i2,1x,i3,1x,a1,a6,1x,i2,1x,i5,1x,i3,1x,
     .          i5,1x,i3,2f8.3,1x,a2,1x,a2,i5)
  320 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prtstr(iout,maxc,line)
c----------------------------------------------------------------------
c     print string
ce---------------------------------------------------------------------
      character*1  line(maxc)
      call strlas(maxc,line,nc)
      write(iout,1000) (line(i),i=1,nc)
 1000 format(1x,80a1)
      return
      end
cs---------------------------------------------------------------------
      subroutine rescco(ires,ica,ic,io,ifnd)
c----------------------------------------------------------------------
c     return seq # of Calpha(ica), and C(ic) and O (io) of NCCO
c     ifnd =0 found, =1 not found
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      ist=istres(ires)
      nati=istres(ires+1)-ist
      call bakbon(nati,ian(ist),x(ist),y(ist),z(ist),
     .                                       in1,ic2,ic3,io4,ifnd0)
      ica=ic2+ist-1
      ic=ic3+ist-1
      io=io4+ist-1
      ifnd=ifnd0
c
      return
      end
cs---------------------------------------------------------------------
      subroutine reschg(iresid,iterm,nat,ian,icharg,ierr)
c----------------------------------------------------------------------
c     return residue charge
c     iterm ... terminal redidue?
c               =0 no, =1 N-terminus, =2 C-terminus
c     ierr =0 residue, =1 non residue
ce---------------------------------------------------------------------
      dimension ian(*)
c     standard stoichiometry of res.
c     asp,glu(-COO(-)),lys(-NH3(+)),arg(-C(NH2)2(+)),and his(prot(+))
      dimension n0c(20),n0h(20),n0n(20),n0o(20),n0s(20)
c              1 2 3 4  5  6 7 8 9 0  1  2 3 4 5 6 7 8 9 0
      data n0c/2,3,5,9, 6, 6,5,5,4,5, 6, 6,3,4,9,3,4,5,6,11/
      data n0h/3,5,9,9,11,11,7,9,4,6,13,13,5,7,9,5,6,8,8,10/
      data n0n/1,1,1,1 ,1, 1,1,1,1,1, 2, 4,1,1,1,1,2,2,3, 2/
      data n0o/1,1,1,1, 1, 1,1,1,3,3, 1, 1,2,2,2,1,2,2,1, 1/
      data n0s/0,0,0,0, 0, 0,0,1,0,0, 0, 0,0,0,0,1,0,0,0, 0/
      save n0c,n0h,n0n,n0o,n0s
c
      icharg=0
c     non-peptide residue
      if(iresid.le.0.or.iresid.gt.20) go to 920
      call chmfr1(nat,ian,nc,nh,nn,no,ns,nx,nele)
c      iout=2
c      write(iout,*) ' iresid ',iresid
c      write(iout,*) ' nc,nh,nn,no,ns,nx,nele ',
c     .                          nc,nh,nn,no,ns,nx,nele
c      write(iout,*) ' n0c,n0h,n0n,n0o,n0s',
c     .    n0c(iresid),n0h(iresid),n0n(iresid),n0o(iresid),n0s(iresid)
      icharg=0
      nh0=n0h(iresid)
c     check the number of heavy atoms
      if(nx.gt.0) go to 900
      if(nc.ne.n0c(iresid)) go to 900
      if(nn.ne.n0n(iresid)) go to 900
      if(ns.ne.n0s(iresid)) go to 900
      if(iterm.eq.2) then
         if(no.ne.n0o(iresid)+1) then
            call msgout(0,1,'! warning(reschg): missing OXT at C-terminu
     .s. charge may not be correct.$')
         endif
      else
         if(no.ne.n0o(iresid)) go to 900
      endif
c
      ierr=0
      if(iresid.eq.9.or.iresid.eq.10) then
c        asp and glu
         if(iterm.eq.0) then
            if(nh.eq.nh0) then
               icharg=-1
            elseif(nh.eq.nh0+1) then
               icharg=0
            else
               go to 900
            endif
         elseif(iterm.eq.1) then
            if(nh.eq.nh0+1) then
               icharg=-1
            elseif(nh.eq.nh0+2) then
               icharg=0
            elseif(nh.eq.nh0+3) then
               icharg=1
            else
               go to 900
            endif
         elseif(iterm.eq.2) then
            if(nh.eq.nh0) then
               icharg=-2
            elseif(nh.eq.nh0+1) then
               icharg=-1
            elseif(nh.eq.nh0+2) then
               icharg=0
            else
               go to 900
            endif
         endif
      elseif(iresid.eq.11.or.iresid.eq.12) then
c        lys and arg
         if(iterm.eq.0) then
            if(nh.eq.nh0) then
               icharg=1
            elseif(nh.eq.nh0-1) then
               icharg=0
            else
               go to 900
            endif
         elseif(iterm.eq.1) then
            if(nh.eq.nh0+1) then
               icharg=1
            elseif(nh.eq.nh0+2) then
               icharg=2
            else
               go to 900
            endif
         elseif(iterm.eq.2) then
            if(nh.eq.nh0) then
               icharg=0
            elseif(nh.eq.nh0+1) then
               icharg=1
            else
               go to 900
            endif
         endif
      elseif(iresid.eq.19) then
c        his
         if(iterm.eq.0) then
            if(nh.eq.nh0) then
               icharg=1
            elseif(nh.eq.nh0-1) then
               icharg=0
            else
               go to 900
            endif
         elseif(iterm.eq.1) then
            if(nh.eq.nh0) then
               icharg=0
            elseif(nh.eq.nh0+1) then
               icharg=1
            elseif(nh.eq.nh0+2) then
               icharg=2
            else
               go to 900
            endif
         elseif(iterm.eq.2) then
            if(nh.eq.nh0) then
               icharg=0
            elseif(nh.eq.nh0-1) then
               icharg=-1
            elseif(nh.eq.nh0+1) then
               icharg=1
            else
               go to 900
            endif
         endif
      elseif(iresid.eq.16) then
c        cys
c        note: cys at N- or C-terminun is assmed to have no S-S bond
         if(iterm.eq.0) then
            if(nh.eq.nh0.or.nh.eq.nh0-1) then
               icharg=0
            else
               go to 900
            endif
         elseif(iterm.eq.1) then
            if(nh.eq.nh0+1) then
               icharg=0
            elseif(nh.eq.nh0+2) then
               icharg=1
            else
               go to 900
            endif
         elseif(iterm.eq.2) then
            if(nh.eq.nh0) then
               icharg=-1
            elseif(nh.eq.nh0+1) then
               icharg=0
            else
               go to 900
            endif
         else
            go to 900
         endif
      else
c        other residues
         if(iterm.eq.0) then
            icharg=0
         elseif(iterm.eq.1) then
c           n-terminus
            if(nh.eq.nh0+2) then
               icharg=1
            elseif(nh.eq.nh0+1) then
               icharg=0
            else
               go to 900
            endif
         elseif(iterm.eq.2) then
c           c-terminus
            if(nh.eq.nh0) then
               icharg=-1
            elseif(nh.eq.nh0+1) then
               icharg=0
            else
               go to 900
            endif
         else
            go to 900
         endif
      endif
c
      return
c
  900 ierr=1
      return
  920 ierr=2
      return
      end
cs---------------------------------------------------------------------
      subroutine rescon (iout,key)
c----------------------------------------------------------------------
c     check covalent bonds between peptide and non-pepide residures
c     key=0 messege for fragmentation, =1 for h tom addition
ce---------------------------------------------------------------------
      character   resnmi*6,resnmj*6,temp*3,atmnmi*4,atmnmj*4
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      rdum=0.0
      k=0
      kk=0
      do 120 i=2,nres
      ires=i
      call resid(resnam(i),iresid,0,0)
      if(resnam(i).eq.'ace'.or.resnam(i).eq.'nme') go to 120
      do 100 j=1,i
      jres=j
      call resid(resnam(j),jresid,0,0)
      if(resnam(j).eq.'ace'.or.resnam(j).eq.'nme') go to 100
      if(iresid.ne.0.and.jresid.ne.0) go to 100
      call rijres(ires,jres,rijmin,iatm,jatm)
      if(ires.eq.jres) go to 100
      iani=ian(iatm)
      ianj=ian(jatm)
      call lcvbnd(iani,ianj,0,rdum,rmin,rmax,ifnd)
      if(rijmin.lt.rmax) then
         k=k+1
         if(iresid.ne.0.or.jresid.ne.0) kk=kk+1
         if(k.eq.1) then
            if(key.eq.0) then
               write(iout,*) ' '
               write(iout,1000)
 1000          format(1x,'WARNING: this protein has covalent bonds of no
     .n-peptide residues.')
               write(iout,1010)
 1010          format(1x,' I do not know how to divide them.')
               write(iout,1011)
 1011          format(1x,' Please fractionate them yourself.')
            endif
         endif
         if(kk.eq.1) then
            if(key.eq.1.and.(iresid.ne.0.or.jresid.ne.0)) then
               write(iout,1000)
               write(iout,1020)
 1020          format(1x,' Hydrogen atom may be added to unnecessary sit
     .e of amino acid residue.')
               write(iout,1021)
 1021          format(1x,' Please remove them before FMO input data gene
     .ration.')
            endif
         endif
         if((key.eq.0.and.k.eq.1).or.(key.eq.1.and.kk.eq.1)) then
               write(iout,1200)
 1200          format(1x,' covalent bonds(?) are found between,',
     ./,'   res#1,resnam1,res#2,resnam2, iatm,iatmnam,jatm,jatmnam,    r
     .ij(A)') 
         endif
         if(key.eq.0.or.
     .            (key.eq.1.and.(iresid.ne.0.or.jresid.ne.0))) then
            ire=numres(i)
            call cnint(3,ire,3,temp)
            resnmi=resnam(ires)//temp
            ire=numres(j)
            call cnint(3,ire,3,temp)
            resnmj=resnam(jres)//temp
            atmnmi=atmnam(iatm)
            call chcase(4,atmnmi,1)
            atmnmj=atmnam(jatm)
            call chcase(4,atmnmj,1)
            write(iout,1400) ires,resnmi,jres,resnmj,iatm,atmnmi,
     .                       jatm,atmnmj,rijmin
 1400       format(2x,i5,1x,a6,2x,i5,1x,a6,2x,i8,1x,a4,i8,1x,a4,2x,
     .             f10.4)
         endif
      endif
  100 continue
  120 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine ressel(nspres,ispres,rthre,key,
     .                                   nsel,iatij,jatij,dminij)
c----------------------------------------------------------------------
c     report res distance from ispres
c     nspres ... number of residues to be measured
c     ispres ... res number from which distance of othre res are measured
c     rthre ... threshould distance in vdw (key=0) or in A (key=1)
c     iodr ... =0 decending order, =1 don't order
c     nsel ... # of selected res
c     iatij,jatij ... seq # of closest atoms
c     dminij ... distance between iatij and jatij in vdw (key=0) or
c                in A (key=1)
ce---------------------------------------------------------------------
      dimension     ispres(*)
      dimension     iatij(*),jatij(*),dminij(*)
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      nsel=0
c
      do 200 j=1,nres
      jres=j
      do 40 ii=1,nspres
      if(jres.eq.ispres(ii)) go to 200
   40 continue
      rmin=1000.0
      do 100 ii=1,nspres
      ires=ispres(ii)
      call rijres(ires,jres,rijmin,iatm,jatm)
      if(key.eq.0) then
         rvdw=rwaals(ian(iatm))+rwaals(ian(jatm))
         if(rvdw.lt.1.0d-4) then
c            write(iout,*) ' error(ressel): rvdw is not defined for
c    .       ian ',ian(iatm),ian(jatm)
         endif
         dvdw=rijmin/rvdw
         dc=dvdw
      else
         dc=rijmin
      endif
      if(dc.lt.rmin) then
         rmin=dc
         imina=iatm
         jmina=jatm
      endif
  100 continue
      if(rmin.lt.rthre) then
         nsel=nsel+1
         dminij(nsel)=rmin
         iatij(nsel)=imina
         jatij(nsel)=jmina
      endif
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine resfrg(ires,ifrg)
c----------------------------------------------------------------------
c     return seq. # of frag to which ires belongs
c     ifrg =0 ires does not belong to any fragment.
ce---------------------------------------------------------------------
      parameter (MaxFrg=50000)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      ifrg=0
      if(nfrg.le.0) go to 100
      do 80 i=1,nfrg
      nrf=nresfg(i)
      if(nrf.gt.0) then
         do 40 j=1,nrf
            if(iresfg(j,i).eq.ires) then
               ifrg=i
               go to 100
            endif
   40    continue
      endif
   80 continue
  100 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine resid(resnam,iresid,icha,key)
c----------------------------------------------------------------------
c     res name <---> res id
c     resnam ... ='   ' failed (key=1 case)
c     iresid ...=n normal exit, =0 failed (key=0 case)
c     icha ... =0 3 characters res name, =1 one character
c     key ... =0 resnam -> res id, =1 res id -> resnam
ce---------------------------------------------------------------------
      character    resnam*3,res3*3,res1*1
      character    resnm3*3,resnm1*1
      common/reslab/kres,resnm3(20),resnm1(20)
      equivalence  (res3,res1)
c
      if(key.eq.0) then
c        name -> id
         res3=resnam
         iresid=0
         if(icha.eq.0) then
            iresid=0
            do 20 i=1,kres
            if(res3.eq.resnm3(i)) then
               iresid=i
               go to 100
            endif
   20       continue
         else
            do 40 i=1,kres
            if(res1.eq.resnm1(i)) then
               iresid=i
               go to 100
            endif
   40       continue
         endif
      else
c        id -> name
         resnam='   '
         if(iresid.le.0.or.iresid.gt.20) go to 900
         if(icha.eq.0) then
            res3=resnm3(iresid)
            resnam=res3
         else
            res1=resnm1(iresid)
            resnam=res1
         endif
      endif
  100 continue
c
      return
c     error exit
  900 call msgout(0,1,'error(resid): wrong residue id number.$')
      call msgou0(0,0,' residue id=$',iresid)
      end
cs---------------------------------------------------------------------
      subroutine resiid(ires,iresid,resnmi)
c----------------------------------------------------------------------
c     return resid and residue name of ires residue
ce---------------------------------------------------------------------
      character resnmi*6,temp*3
      parameter (MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
c
      call resid(resnam(ires),iresid,0,0)
      ire=numres(ires)
      call cnint(3,ire,3,temp)
      resnmi=resnam(ires)//temp
c
      return
      end
cs----------------------------------------------------------------------
      subroutine resmol(ires,imol,ifres,ilres)
c-----------------------------------------------------------------------
c     find sequence number of mol to which ires residue belongs.
c     ires ... seq. # of res in the whole system
c     imol ... seq. # of mol to which ires belongs
c     ifres ... seq. # of res of the first res of the mol
c     ilres ... seq. # of res of the last res of the mol
ce----------------------------------------------------------------------
      parameter (MaxMol=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
c
      imol=0
      ifres=0
      ilres=0
      do 20 i=1,nmol
      if(ires.ge.istmol(i).and.ires.lt.istmol(i+1)) then
         imol=i
         ifres=istmol(i)
         ilres=istmol(i+1)-1
         go to 40
      endif
   20 continue
   40 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine rijres(ires,jres,rijmin,iatm,jatm)
c----------------------------------------------------------------------
c     min. distance between ires and jres
c     ires,jres ... sequence numners of res ires and jres
c     rijmin ... min. dictance between ires and others (A)
c     iatm,jatm ... closest contact atoms of ires and jres,respectively
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      ist=istres(ires)
      ied=istres(ires+1)-1
      jst=istres(jres)
      jed=istres(jres+1)-1
      rijmin=0.0
      iatm=ist
      jatm=jst
      if(ires.eq.jres) go to 100
      rijmin=1000.0
c
      do 80 j=jst,jed
         if(ian(j).eq.0) go to 80
         xj=x(j)
         yj=y(j)
         zj=z(j)
         do 40 i=ist,ied
            if(ian(i).eq.0) go to 40
            xi=x(i)
            yi=y(i)
            zi=z(i)
            d=(xi-xj)**2+(yi-yj)**2+(zi-zj)**2
            d=sqrt(d)
            if(d.lt.rijmin) then
               rijmin=d
               iatm=i
               jatm=j
             endif
   40    continue
   80 continue
  100 continue
c
      return
      end
cs----------------------------------------------------------------------
      subroutine rsort1(n,rr,tt,iord)
c-----------------------------------------------------------------------
c     rsort1:: arrange floating point data in ascending order.
c     maxn   (i4)      ... size  of arrays.
c     n      (i4)      ... number of data.
c     rr     (r8:maxn) ... data to be ordered.
c     tt     (r8:maxn) ... ordered data.
c     iord   (i4:maxn) ... ascending order of data.
ce----------------------------------------------------------------------
      dimension    rr(*),tt(*),iord(*)
c
      do 50 i=1,n
      tt(i)=rr(i)
   50 iord(i)=i
c
      do 200 i=1,n
      k=i
      p=tt(i)
      if(n-i.le.0) go to 120
      do 100 j=i+1,n
      if(tt(j).gt.p) go to 100
      k=j
      p=tt(j)
  100 continue
  120 if(k.eq.i) go to 200
      it=iord(k)
      iord(k)=iord(i)
      iord(i)=it
      tmp=tt(i)
      tt(i)=tt(k)
      tt(k)=tmp
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      real function rwaals(ian)
c----------------------------------------------------------------------
c     return vdw radius of ian atomic number
ce---------------------------------------------------------------------
      common/vdwrad/nvdw,nvdwd,rvdw(100)
      if(ian.le.0.or.ian.gt.nvdw) go to 900
      rwaals=rvdw(ian)
      return
c     error exit
  900 continue
c???
      call msgout(0,1,'error(rwaals): wrong atomic number.$')
      call msgou0(0,0,' atomic number=$',ian)
      end
cs---------------------------------------------------------------------
      subroutine selres(iout,nspres,ispres,rthre,key,isave)
c----------------------------------------------------------------------
c     save selected residues in PDB formatt
c     nspres ... number of residues to be measured
c     ispres ... res number from which distance of othre res are measured
c     rthre ... threshould distance in vdw (key=0) or in A (key=1)
c     isave ... =0 output pdb file, =1 just print
ce---------------------------------------------------------------------
      parameter (MaxRes=50000)
      dimension     ispres(*)
      dimension     iatij(MaxRes),jatij(MaxRes),dminij(MaxRes)
c
c     assign charges to residues
      call chgres
c     select residues within the threshould distance
      call ressel(nspres,ispres,rthre,key,nsel,iatij,jatij,dminij)
c
      if(isave.eq.0) then
c        output reference and selected residues in PDB format         
         call pdbsel(iout,nspres,ispres,nsel,jatij,iatij)
      else
         iodr=0
c        print selected residues
         call prtsel(iout,nspres,ispres,rthre,iodr,key,
     .                                     nsel,iatij,jatij,dminij)
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine ssbcys(imol,ires,jres)
c----------------------------------------------------------------------
c     find partner res number of S-S bond with ires in imol molecule
c     imol <> 0 search res within imol, =0 all molecules
c     ires... input cys res number
c     jres... =i, partner cys res number, =0 no S-S bond
ce---------------------------------------------------------------------
      parameter (MaxRes=50000,MaxMol=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
c
      jres=0
c
      if(imol.ne.0) then
         istr=istmol(imol)
         iedr=istmol(imol+1)-1
      else
         istr=1
         iedr=nres
      endif
      do 120 j=istr,iedr
      if(j.eq.ires) go to 120
      call resid(resnam(j),iresid,0,0)
      if(iresid.eq.16) then
         call ssbond(ires,j,iss)
         if(iss.eq.0) jres=j
      endif
  120 continue
c
c  200 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine ssbond(ires,jres,iss)
c----------------------------------------------------------------------
c     check s-s bond between ires(cys) and jres(cys)
c     iss =0 yes they have ss bond, =1 no
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      rdum1=0.0
      rdum2=0.0
      iss=1
      if(ires.eq.jres) go to 200
c
      ist=istres(ires)
      nati=istres(ires+1)-ist
      do 20 i=1,nati
      ii=ist+i-1
      if(ian(ii).eq.16) then
         is=ii
         go to 40
      endif
   20 continue
      go to 200
   40 continue
c
      call lcvbnd(16,16,1,rdum1,rdum2,rssmax,ifnd)
      jst=istres(jres)
      natj=istres(jres+1)-jst
      do 100 k=1,natj
      kk=jst+k-1
      if(ian(kk).eq.16) then
         js=kk
         rij=sqrt((x(is)-x(js))**2+(y(is)-y(js))**2+(z(is)-z(js))**2)
         if(rij.le.rssmax) iss=0
      endif
  100 continue
c
  200 continue
      return
      end
cs----------------------------------------------------------------------
      subroutine trkoco(nati,iani,xi,yi,zi,anmi,ioco,key,ierr)
c-----------------------------------------------------------------------
c     remove and recover O of -COO at C-terminus
c     key =0 remove, =1 recover
ce----------------------------------------------------------------------
      dimension    iani(*),xi(*),yi(*),zi(*)
      character*4  anmi(*),anmoco
      dimension    lst1(8)
      save         io5,xoco,yoco,zoco,anmoco
c
      ierr=0
      if(key.eq.0) then
c        remove O of -COO
c        find O of NCOO in ires
         ioco=1
         call bakbon(nati,iani,xi,yi,zi,in1,ic2,ic3,io4,ifnd)
         if(ifnd.ne.0) go to 940
         iat1=ic3
         ianic2=iani(ic2)
         ianio4=iani(io4)
         iani(ic2)=0
         iani(io4)=0
         call bndlst(nati,iani,xi,yi,zi,iat1,nbnd,lst1,0)
         iani(ic2)=ianic2
         iani(io4)=ianio4
            if(nbnd.ge.1) then
            if(iani(lst1(1)).eq.8) then
               ioco=0
               io5=lst1(1)
            else
               call msgout(0,1,' ! warning(trkoco): C-terminus does not 
     .end with -COO.$')       
            endif
         else
c           warning
            call msgout(0,1,' ! warning(trkoco): C-terminus does not end
     . with -COO.$')       
         endif
         if(ioco.eq.0) then
            xoco=xi(io5)
            yoco=yi(io5)
            zoco=zi(io5)
            anmoco=anmi(io5)
            k=0
            do 60 i=1,nati
            if(i.eq.io5) go to 60
            k=k+1
            iani(k)=iani(i)
            xi(k)=xi(i)
            yi(k)=yi(i)
            zi(k)=zi(i)
            anmi(k)=anmi(i)
   60       continue
            nati=nati-1
         endif
      else
c        recover O of -COO
         k=0
         do 140 i=io5,nati
         k=k+1
         ii=nati-k+2
         iani(ii)=iani(ii-1)
         xi(ii)=xi(ii-1)
         yi(ii)=yi(ii-1)
         zi(ii)=zi(ii-1)
         anmi(ii)=anmi(ii-1)
  140    continue
         iani(io5)=8
         xi(io5)=xoco
         yi(io5)=yoco
         zi(io5)=zoco
         anmi(io5)=anmoco
         nati=nati+1
      endif
c
      return
  940 ierr=1
      return
      end
cs---------------------------------------------------------------------
      subroutine twores(ifgly,imlss)
c----------------------------------------------------------------------
c     fragmentation of proteins/polypeptides
c     two res/one fragment
c     ifgly =0 first, gly is combined with neighbor, then other res
c     imlss =0 intermolecular s-s bond is exist, =1 not
ce---------------------------------------------------------------------
      parameter (MaxRes=50000,MaxFrg=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      character*3   temp
c
      idum=0
      jdum=0
      nfrg=0
      imlss=1
      nssbnd=0
c
c     temporally division one res per one frag

      do 40 ires=1,nres
      nfrg=nfrg+1
      if(nfrg.gt.MaxFrg) go to 920
      nresfg(nfrg)=1
      iresfg(1,nfrg)=ires
      ichfrg(nfrg)=ichres(ires)
      iresn=numres(ires)
      call cnint(3,iresn,3,temp)
      frgnam(nfrg)=resnam(ires)//temp
   40 continue
c     combine two cys's with s-s bond
      do 80 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
      if(iresid.ne.16) go to 80
      irestmp=ires
      call ssbcys(0,irestmp,jres)
      if(jres.eq.0.or.jres.lt.ires) go to 80
      nssbnd=nssbnd+1
      call frgmol(ires,imol1,idum,jdum)
      call frgmol(jres,imol2,idum,jdum)
      if(imol1.ne.imol2) imlss=0
c     ires-cys and jres-cys(ires<jres) has s-s bond
      call resfrg(ires,ifrg)
      call resfrg(jres,jfrg)
      call updfrg(ifrg,jfrg)
   80 continue
c
c       combine ace and nme caps to the first and the last res,respectively,
c     if they exist.
      do 120 ires=1,nres
      call resid(resnam(ires),iresid,0,0)
      call resmol(ires,imol,ist,ied)
      if(ires.eq.ist.and.resnam(ires).eq.'ace') then
c        ace is combined to the next residue
         call resid(resnam(ires+1),jresid,0,0)
         if(jresid.ne.0) then
            call resfrg(ires,ifrg)
            call resfrg(ires+1,jfrg)
            call updfrg(ifrg,jfrg)
         endif
      elseif(ires.eq.ied.and.resnam(ires).eq.'nme') then
c        nme is combined to the front residue
         call resid(resnam(ires-1),jresid,0,0)
         if(jresid.ne.0) then
            call resfrg(ires-1,ifrg)
            call resfrg(ires,jfrg)
            call updfrg(ifrg,jfrg)
         endif
      endif
  120 continue
c
      if(ifgly.eq.0) then
c        first, combine gly with neighbor
         do 200 ires=1,nres
         call resid(resnam(ires),iresid,0,0)
         call resmol(ires,imol,ist,ied)
         if(iresid.ne.1) go to 200
            if(ires.eq.ied) then
c              gly at c-termimus is combined to the front residue
               call resid(resnam(ires-1),jresid,0,0)
               call resfrg(ires-1,ifrg)
               if(jresid.ne.0.and.nresfg(ifrg).eq.1) then
                  call resfrg(ires,jfrg)
                  call updfrg(ifrg,jfrg)
               endif
            else
               idone=1
               call resfrg(ires,ifrg)
               if(nresfg(ifrg).lt.2) then
                  call adjfrg(ifrg,iadjs,iadjl)
                  jres1=iresfg(1,iadjs)
                  nrf1=nresfg(iadjs)
                  call resid(resnam(jres1),jrsid1,0,0)
                  if(jrsid1.ne.0.and.nrf1.lt.2
     .                          .and.iabs(ires-jres1).eq.1) then
                     call updfrg(ifrg,iadjs)
                     idone=0
                  endif
                  if(idone.eq.1.and.iadjl.ne.0) then
                     jres2=iresfg(1,iadjl)
                     nrf2=nresfg(iadjl)
                     call resid(resnam(jres2),jrsid2,0,0)
                     if(jrsid2.ne.0.and.nrf2.lt.2
     .                             .and.iabs(ires-jres2).eq.1) then
                        call updfrg(ifrg,iadjl)
                        idone=0
                     endif
                  endif
               endif
            endif
  200    continue
      endif
c     fractionation for two res per fragment
      ires=0
  220 continue
      istdum=0
      ieddum=0
      ires=ires+1
      call resmol(ires,imol,ist,ied)
      call resid(resnam(ires),iresid,0,0)
      if(iresid.ne.0) then
         call resfrg(ires,ifrg)
         if(nresfg(ifrg).eq.1) then
            call resfrg(ires+1,jfrg)
            call resmol(ires+1,jmol,istdum,ieddum)
            call resid(resnam(ires+1),jresid,0,0)
            if(jresid.ne.0.and.nresfg(jfrg).eq.1.and.imol.eq.jmol) then
               call updfrg(ifrg,jfrg)
               ires=ires+1
            endif
         endif
      endif
      if(ires.lt.nres) go to 220
c  300 continue
c
      return
c     error exit
  920 call msgout(0,1,'error(twores): too many fargments.$')
      call msgou0(0,1,' MaxFrg=$',MaxFrg)
      call msgout(0,0,' recompile the program with larger MaxFrg.$')
      end
cs----------------------------------------------------------------------
      subroutine updfrg(ifrg,jfrg)
c-----------------------------------------------------------------------
c     update /frginf/
c     jfrg is combined with ifrg and is deleted.
c     nfrg is reduced by one.
ce----------------------------------------------------------------------
      parameter (MaxFrg=50000)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c
      if(ifrg.eq.jfrg) go to 200
      ifg=ifrg
      jfg=jfrg
      if(ifg.gt.jfg) then
         ifg=jfrg
         jfg=ifrg
      endif
      if(ifg.eq.nfrg) go to 200
      nrfi=nresfg(ifg)
      nrfj=nresfg(jfg)
      nrfic=6*nrfi
      nrfjc=6*nrfj
      if(nrfi+nrfj.gt.4) go to 920
      nresfg(ifg)=nrfi+nrfj
      if(nrfj.le.0) go to 200
      do 100 i=1,nrfj
      ii=i+nrfi
      iresfg(ii,ifg)=iresfg(i,jfg)
  100 continue
      ichfrg(ifg)=ichfrg(ifg)+ichfrg(jfg)
      frgnam(ifg)=frgnam(ifg)(1:nrfic)//frgnam(jfg)(1:nrfjc)
      k=ifg
      do 140 i=ifg+1,nfrg
      if(i.eq.jfg) go to 140
      k=k+1
      nresfg(k)=nresfg(i)
      ichfrg(k)=ichfrg(i)
      frgnam(k)=frgnam(i)
      nrfi=nresfg(i)
      do 120 j=1,nrfi
      iresfg(j,k)=iresfg(j,i)
  120 continue
  140 continue
      nresfg(nfrg)=0
      nfrg=nfrg-1
  200 continue
      return
  920 call msgout(0,0,'error(updfrg): too many residues per fragment. ma
     .x=2.$')
c  940 call msgout(0,0,'error(updfrg): ifrg/jfrg .gt. nfrg.$')
      end
cs----------------------------------------------------------------------
      subroutine updres(ires,nati,iani,xi,yi,zi,anmi)
c-----------------------------------------------------------------------
c     update residure atoms
c     ires ... sequence number of residures
c     iani,xi,yi,zi ... atomic # , x,y z, coord.
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      dimension     iani(*),xi(*),yi(*),zi(*)
      character*4   anmi(*)
c
      isto=istres(ires)
      nato=istres(ires+1)-isto
      if(nato.eq.nati) then
         do 20 i=1,nati
         ii=isto+i-1
         ian(ii)=iani(i)
         x(ii)=xi(i)
         y(ii)=yi(i)
         z(ii)=zi(i)
         atmnam(ii)=anmi(i)
   20    continue
c         write(*,*) ' nati=nato:ires,nati,natres ',ires,nati,natres
c         write(*,2000) (istres(i),i=1,nres+1)
      elseif(nati.lt.nato) then
         inc=nati-nato
         do 40 i=1,nati
         ii=isto+i-1
         ian(ii)=iani(i)
         x(ii)=xi(i)
         y(ii)=yi(i)
         z(ii)=zi(i)
         atmnam(ii)=anmi(i)
   40    continue
         if(ires.eq.nres) go to 100
         do 80 i=ires+1,nres
         jsto=istres(i)
         natj=istres(i+1)-jsto
         do 60 j=1,natj
         jj=jsto+j-1
         ian(jj+inc)=ian(jj)
         x(jj+inc)=x(jj)
         y(jj+inc)=y(jj)
         z(jj+inc)=z(jj)
         atmnam(jj+inc)=atmnam(jj)
   60    continue
         istres(i)=istres(i)+inc
   80    continue
  100    continue
         natres=natres+inc
         istres(nres+1)=natres+1
c         write(*,*) ' nati<nato:ires,nati,natres ',ires,nati,natres
c         write(*,2000) (istres(i),i=1,nres+1)
      elseif(nati.gt.nato) then
         inc=nati-nato
         ist=istres(nres)
         if(ires.eq.nres) go to 200
         kr=0
         do 180 i=ires+1,nres
         kr=kr+1
         ii=nres-kr+1
         iist=istres(ii)
         natii=istres(ii+1)-iist
         do 160 j=1,natii
         jj=iist+natii-j
         ian(jj+inc)=ian(jj)
         x(jj+inc)=x(jj)
         y(jj+inc)=y(jj)
         z(jj+inc)=z(jj)
         atmnam(jj+inc)=atmnam(jj)
  160    continue
         istres(ii+1)=istres(ii+1)+inc
  180    continue
         ist=istres(ires)
  200    continue
         do 220 i=1,nati
         ii=ist+i-1
         ian(ii)=iani(i)
         x(ii)=xi(i)
         y(ii)=yi(i)
         z(ii)=zi(i)
         atmnam(ii)=anmi(i)
  220    continue
         istres(ires+1)=ist+nati
         natres=natres+inc

c         write(*,*) ' nati>nato:ires,nati,natres ',ires,nati,natres
c         write(*,2000) (istres(i),i=1,nres+1)
c 2000    format(20i4)

      endif
c
      return
      end
cs----------------------------------------------------------------------
      subroutine vecpk1(x,y,z,v,key)
c-----------------------------------------------------------------------
c     restore vector
c     key=0 v(1,2,3) -> x,y,z
c        =1 x,y,z -> v(1,2,3)
ce----------------------------------------------------------------------
      dimension v(3)
c
      if(key.eq.0) then
         x=v(1)
         y=v(2)
         z=v(3)
      else
         v(1)=x
         v(2)=y
         v(3)=z
      endif
c
      return
      end
cs----------------------------------------------------------------------
      subroutine vecpk2(x,y,z,v,v0,key)
c-----------------------------------------------------------------------
c     restore vector with origin shift
c     key=0 v(1,2,3)-v0(1,2,3) -> x,y,z
c        =1 x-v(1),y-v(2),z-v(3) -> v(1,2,3)
ce----------------------------------------------------------------------
      dimension v(3),v0(3)
c
      if(key.eq.0) then
         x=v(1)-v0(1)
         y=v(2)-v0(2)
         z=v(3)-v0(3)
      else
         v(1)=x-v0(1)
         v(2)=y-v0(2)
         v(3)=z-v0(3)
      endif
c
      return
      end
cs----------------------------------------------------------------------
      subroutine anglet(ra,rb,teta)
c-----------------------------------------------------------------------
c*    ANGLET:: angle between vectors ra and rb.
cag   ra   (r4:3)  ... vector 1.
c     rb   (r4:3)  ... vector 2.
c     teta (r4)    ... angle between ra and rb in unit of radians.
ce----------------------------------------------------------------------
      dimension ra(3),rb(3)
      data two /2.0/,eps1/1.0e-12/,eps2/1.0e-18/,tone/0.9999999999/
c
      teta=0.0
      rra2=ra(1)*ra(1)+ra(2)*ra(2)+ra(3)*ra(3)
      rra =sqrt(rra2)
      rrb2=rb(1)*rb(1)+rb(2)*rb(2)+rb(3)*rb(3)
      rrb =sqrt(rrb2)
      rab2=(ra(1)-rb(1))**2+(ra(2)-rb(2))**2+(ra(3)-rb(3))**2
      if(rab2.lt.eps2) return
      rarb=rra*rrb
      if(rarb.lt.eps1) return
      teta=(rra2+rrb2-rab2)/(two*rarb)
      if(teta.gt.tone) teta=tone
      if(teta.lt.-tone) teta=-tone
      if(abs(teta).lt.eps1) teta=0.0
      teta=acos(teta)
c
      return
      end

cs----------------------------------------------------------------------
      subroutine prout(ra,rb,rc)
c-----------------------------------------------------------------------
c*    PROUT:: outer products of vectors ra and rb.
cag   ra  (r4:3)  ... vector 1.
c     rb  (r4:3)  ... vector 2.
c     rc  (r4:3)  ... result vector.
ce----------------------------------------------------------------------
      dimension ra(3),rb(3),rc(3)
      data eps/1.0e-12/,zero/0.0/
c
      rc(1)=ra(2)*rb(3)-ra(3)*rb(2)
      rc(2)=ra(3)*rb(1)-ra(1)*rb(3)
      rc(3)=ra(1)*rb(2)-ra(2)*rb(1)
      do 10 i=1,3
   10 if(abs(rc(i)).lt.eps) rc(i)=zero
c
      return
      end
cs----------------------------------------------------------------------
      subroutine rotvec(nat,xr,yr,zr,xn,yn,zn,v)
c-----------------------------------------------------------------------
c*    ROTVEC:: transformation matrix between xyzr and xyzn.
c     nat (i4)          ... number of atoms.
c     xr  (r4:nat)     ... reference x  coordinates.
c     yr  (r4:nat)     ... reference y  coordinates.
c     zr  (r4:nat)     ... reference z  coordinates.
c     xn  (r4:nat)     ... x  coordinates of molecule.
c     yn  (r4:nat)     ... y  coordinates of molecule.
c     zn  (r4:nat)     ... z  coordinates of molecule.
c     v   (r4:3*3)      ... transformaton matrix.
ce----------------------------------------------------------------------
      dimension xr(*),yr(*),zr(*),v(3,3)
      dimension xn(*),yn(*),zn(*)
      dimension ra(3),rb(3),rc(3),u1(3,3),u2(3,3),u(3,3)
      data      zero/0.0/
      data      epst/1.e-9/,pi/3.14159265358979/
c
      call unimat(v)
      if(nat.le.1) return
c
      call unimat(u1)
      call unimat(u2)
      ra(1)=xr(2)-xr(1)
      ra(2)=yr(2)-yr(1)
      ra(3)=zr(2)-zr(1)
      rb(1)=xn(2)-xn(1)
      rb(2)=yn(2)-yn(1)
      rb(3)=zn(2)-zn(1)
      call anglet(ra,rb,t)
      if(abs(t).le.epst) go to 10
      call prout(ra,rb,rc)
      call trnmat(rc,ra,rb,u1)
   10 if(nat.le.2) go to 50
      rb(1)=xr(2)-xr(1)
      rb(2)=yr(2)-yr(1)
      rb(3)=zr(2)-zr(1)
      do 20 ii=3,nat
      ra(1)=xr(ii)-xr(1)
      ra(2)=yr(ii)-yr(1)
      ra(3)=zr(ii)-zr(1)
      call anglet(ra,rb,t)
      if(abs(t).le.epst.or.abs(t-pi).lt.epst) go to 20
      go to 40
   20 continue
      go to 50
   40 continue
      call trnvec(u1,ra)
      rb(1)=xn(2)-xn(1)
      rb(2)=yn(2)-yn(1)
      rb(3)=zn(2)-zn(1)
      rc(1)=xn(ii)-xn(1)
      rc(2)=yn(ii)-yn(1)
      rc(3)=zn(ii)-zn(1)
      call trnmat(rb,ra,rc,u2)
   50 continue
      do 70 ii=1,3
      do 70 jj=1,3
      u(ii,jj)=zero
      do 60 k=1,3
   60 u(ii,jj)=u(ii,jj)+u2(ii,k)*u1(k,jj)
   70 continue
c
      do 80 i=1,3
      do 80 j=1,3
   80 v(i,j)=u(i,j)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strcat(maxchr,line,ns,strng,nc,char)
c----------------------------------------------------------------------
c*    strcat : combines two strings with characters between them.
c     maxchr (i4)        ... size of 'line'.
c     line   (c1:maxchr) ... the first string array to be combined.
c     ns     (i4)        ... size of 'strng'.
c     strng  (c1:ns)     ... the second string array to be combined.
c     nc     (i4)        ... size of 'char'.
c     char   (c1:nc)     ... characters to be inserted.
c----------------------------------------------------------------------
c     ex.
c                 <input>                <output>
c     maxchr :  10
c     line   :  'abcde_____'		 'abcde+fgh_'
c     ns     :  3
c     strng  :	'fgh'
c     nc     :	1
c     char   :	+
ce---------------------------------------------------------------------
      character*1  line(maxchr),strng(ns),char(nc)
c
      call strsiz(maxchr,line,nchr)
      call strsiz(ns,strng,mchr)
      if(nchr+mchr+1.gt.maxchr) go to 900
      is=0
      if(nchr.le.0) go to 20
      is=nchr
      if(nc.le.0) go to 20
      do 10 i=1,nc
      is=is+1
   10 line(is)=char(i)
   20 continue
      if(mchr.le.0) return
      do 30 i=1,mchr
      ii=is+i
   30 line(ii)=strng(i)
      return
c
c     error message
  900 call msgout(0,1,'error(strcat): string is too long.$')
      return
      end
cs----------------------------------------------------------------------
      subroutine strcle(maxchr,line)
c----------------------------------------------------------------------
c*    strcle : blank clear a string.
c     maxchr (i4)        ... size of 'line'.
c     line   (c1:maxchr) ... strage to be cleared.
c----------------------------------------------------------------------
c     ex.
c                 <input>                <output>
c     maxchr :  10
c     line   :  'abcde_____'		 '__________'
ce---------------------------------------------------------------------
      character*1 line(maxchr)
c
      do 10 i=1,maxchr
   10 line(i)=' '
      return
      end
cs---------------------------------------------------------------------
      subroutine strcnv(maxc,line,ntype,idata,fdata)
c----------------------------------------------------------------------
c*    STRCNV:: find data type and converts characters to int or real.
cag   note   : maximum 20 figures.
c     maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string to be converted.
c     ntype  (i4)        ... 0:integer,1:real,2:character,3:blank.
c     idata  (i4)        ... integer data after conversion.
c     fdata  (r4)        ... floating point data after conversion.
cex
c     call strcnv(10,'123       ',ntype,idata,fdata)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '123_______'             ?
c     ntype  :  ?                        0
c     idata  :  ?                        123
c     fdata  :  ?                        ?
c
c     call strcnv(10,'1.234     ',ntype,idata,fdata)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '1.234_____'             ?
c     ntype  :  ?                        1
c     idata  :  ?                        ?
c     fdata  :  ?                        1.234
c
c     call strcnv(10,' abcd     ',ntype,idata,fdata)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '_abcd_____'             '_abcd____'
c     ntype  :  ?                        2
c     idata  :  ?                        ?
c     fdata  :  ?                        ?
crf   strtyp,strtoi,strtow
ce---------------------------------------------------------------------
      character*1 line(maxc)
c
      idata=0
      fdata=0.0
      call strtyp(maxc,line,ntype)
      if(ntype.eq.0) call strtoi(maxc,line,idata)
      if(ntype.eq.1) call strtor(maxc,line,fdata)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strcut(maxc,line,char)
c-----------------------------------------------------------------------
c*    STRCUT:: cut after a character of 'char'.
cag   maxc   (i4)        ... size of array 'line'.
c     line   (c1:maxc)   ... string.
c     char   (c1)        ... a character.
cex
c     call strcut(10,' bc de/fg ','/')
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '_bc_de/fg_'             '_bc_de_____'
c     char   :  '/'                      '/'
ce----------------------------------------------------------------------
      character*1  line(maxc),char
c
      do 10 i=1,maxc
   10 if(line(i).eq.char) go to 20
      return
   20 is=i
      do 30 i=is,maxc
   30 line(i)=' '
      return
      end
cs----------------------------------------------------------------------
      subroutine strdat(line,maxd,nstr,str)
c-----------------------------------------------------------------------
c     extract string data from line and store in str
c     maxd ... dimension size of str
c     nstr ... number of string data
c     str  ... string data
ce----------------------------------------------------------------------
      character*80 line,str(*)
      data maxc/80/
      save maxc
c
      nstr=0
      call strsiz(maxc,line,nc)
      if(nc.le.0) go to 40
   20 continue
      nstr=nstr+1
      if(nstr.gt.maxd) go to 900
      call strtok(maxc,line,nc,str(nstr),mc)
      if(nc.gt.0) go to 20
   40 continue
c
      return
  900 call msgou0(0,1,'warning(strdat): too many data. max=$',maxd)
      return
      end
cs----------------------------------------------------------------------
      subroutine strdup(maxc,line1,ncol,mcol,line2)
c----------------------------------------------------------------------
c*    STRCPY:: copy characters form ncol to mcol column.
cag   maxc   (i4)        ... array size of line
c     line1  (c1:maxc)   ... input string.
c     ncol   (i4)        ... the first colmn of copy.
c     mcol   (i4)        ... the last colmn.
c     line2  (c1:maxc)   ... output string.
cex               <input>                <output>
c     maxc   :  10
c     line1  :  'abcdefg___'
c     ncol   :  2
c     mcol   :  5
ce---------------------------------------------------------------------
      character*1  line1(maxc),line2(maxc)
c
      if(ncol.gt.mcol) go to 900
      is=ncol
      ie=mcol
      do 10 i=1,maxc
   10 line2(i)=' '
      if(ncol*mcol.ne.0) go to 20
      is=1
      ie=maxc
   20 k=0
      do 30 i=is,ie
      k=k+1
   30 line2(k)=line1(i)
      return
c
c     program error
  900 call msgout(0,1,'error(strdup): wrong colmun parameter.$')
      return
      end
cs----------------------------------------------------------------------
      subroutine stri2c(maxl,ival,line,ifig)
ce----------------------------------------------------------------------
      character*1  line(maxl),ten(10),mns,blk
      data         ten/'0','1','2','3','4','5','6','7','8','9'/
      data         eps/1.0e-6/
      data         mns/'-'/,blk/' '/
c
      do 10 i=1,maxl
   10 line(i)=blk
      line(1)=mns
      ist=0
      if(ival.lt.0) ist=1
      ival1=iabs(ival)
      val=ival1
      val=val+eps
      fig=alog10(val)
      ifg=fig
      if(ifg.le.0) go to 30
      do 20 i=1,ifg
      ii=ifg-i+1
      iden=10**ii
      ith=ival1/iden
      ival1=ival1-ith*iden
      ist=ist+1
   20 line(ist)=ten(ith+1)
   30 ist=ist+1
      line(ist)=ten(ival1+1)
      ifig=ist
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strint(maxc,line,maxn,nint,intg)
c-----------------------------------------------------------------------
c*    STRINT:: resolve positive integers.
c     input: '1 2 5-8 10- 12 15 -17 19 - 22' are all allowed.
cnote positive integers are assumed!!!!
cag   maxc   (i4)        ... size of 'line','temp1', and 'temp2'.
c     line   (c1:maxc)   ... string.
c     maxn   (i4)        ... size of 'int'.
c     nint   (i4)        ... number of integers in 'int'.
c     int    (i4:maxn)   ... integer number.
cex
c     call strint(10,' 123 8-10 ',10,nint,int)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '_123_8-10_'             ?
c     maxn   :  10                       10
c     nint   :  ?                        4
c     int    :  ?                        123,8,9,10,0,0,0,0,0,0
crf   strtoi,strcnv
ce----------------------------------------------------------------------
      character*1  line(maxc),mns,blk
      character*256 temp1,temp2
      integer      intg(maxn)
      data         mns/'-'/,blk/' '/
c
      if(maxc.gt.256) go to 980
c
      nint=0
      do 20 i=1,maxn
   20 intg(i)=0
c
   40 continue
      call strtok(maxc,line,nc,temp1,mc)
      if(mc.le.0) go to 100
c     call strfdf(maxc,line,1,mns,is,ie)
      is=0
      do 50 i=1,mc
   50 if(temp1(i:i).eq.mns) is=i
      if(nint.eq.0.and.is.eq.1) go to 960
      if(mc.eq.1) then
         if(is.ne.0) then
            call strtok(maxc,line,nc,temp1,mc)
            call strsft(maxc,temp1,-1)
            temp1(1:1)=mns
            is=1
         endif
      elseif(mc.gt.1) then
         if(mc.eq.is) then
            temp1(mc:mc)=blk
            call strsft(maxc,line,-1)
            line(1)=mns
            is=0
         endif
      endif
      if(is.eq.0) then
c     '-' is not found
         nint=nint+1
         if(nint.gt.maxn) go to 920
         call strtoi(maxc,temp1,int1)
         intg(nint)=int1
      elseif(is.eq.1) then
c     '-' at the first column
         call strsft(maxc,temp1,1)
         call strsiz(maxc,temp1,n)
         if(n.le.0) call strtok(maxc,line,nc,temp1,mc)
         call strtoi(maxc,temp1,int2)
         if(int1.gt.int2) go to 940
         do 60 i=int1+1,int2
         nint=nint+1
         if(nint.gt.maxn) go to 920
   60    intg(nint)=i
      else
c     '-' is found
         call strtk1(maxc,temp1,nc,temp2,mc,mns)
         call strtoi(maxc,temp2,int1)
         call strtoi(maxc,temp1,int2)
         if(int1.gt.int2) go to 940
         do 80 i=int1,int2
         nint=nint+1
         if(nint.gt.maxn) go to 920
         intg(nint)=i
   80    continue
      endif
      go to 40
  100 continue
c
      return
c
c     error exit
  920 call msgout(0,0,'error(strint): too many integers.$')
  940 call msgout(0,0,'error(strint): int2.lt.int1 in int1-int2.$')
  960 call msgout(0,0,'error(strint): wrong format.$')
  980 call msgout(0,0,'error(strint): too long string. max =80.$')
      end
cs----------------------------------------------------------------------
      subroutine strlas(maxc,line,nchr)
c-----------------------------------------------------------------------
c*    STRLAS:: counts number of chrs. cut blanks after chrs.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     nchr   (i4)        ... number of characters in 'line'.
cex
c     call strsiz(10,'    ab cd ',nchr)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '____ab_cd_'             '____ab_cd___'
c     nchr   :  ?                         9
crf   strln1
ce----------------------------------------------------------------------
      character*1 line(maxc)
c
      nchr=0
      do 30 i=1,maxc
      ii=maxc-i+1
   30 if(line(ii).ne.' ') go to 40
      return
   40 continue
      nchr=maxc-i+1
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strr2c(maxc,val,line,ifig,idgt)
c-----------------------------------------------------------------------
c     STRR2C:: converts a floating number to a string.
c     note: idgt.le.9 (june 1996, k.kitaura)
cag   maxc  (i4)      ... max. number of characters in 'line'.
c     val   (r8)      ... an floating number.
c     line  (c1:maxc) ... resulted string.
c     ifig  (i4)      ... figure.
c     idgt  (i4)      ... degit.
cex
c     call strr2c(10,3.45,'??????????',ifig,2)
c               <input>                  <output>
c     maxc   :  10                       10
c     ival   :  3.45                     ?
c     line   :  '??????????'             '3.45______'
c     ifig   :  ?                        4
c     idgt   :  3                        3
crf   strito
ce----------------------------------------------------------------------
      character*1  line(maxc),mns,zer,dot,blk
      character*1  line1(20),line2(20)
      data         maxd/20/
      data         mns/'-'/,zer/'0'/,dot/'.'/,blk/' '/
c
      isg=0
      if(val.lt.0.0) isg=1
      idg=idgt
      if(idg.le.0) idg=0
      call strcle(maxc,line)
      i1=val
      i2=(val-dble(i1))*10.0**idg
      i2=iabs(i2)
      call stri2c(maxd,i1,line1,ifg)
      if(isg.eq.1) then
         call strsft(maxd,line1,-1)
         line1(1)=mns
      endif
      call strcat(maxc,line,maxd,line1,1,blk)
      call strcle(maxd,line2)
      if(idg.le.0) go to 20
      call stri2c(maxd,i2,line2,ifg)
      if(ifg.lt.idg) then
        isft=idg-ifg
        call strsft(maxd,line2,-isft)
        do 10 i=1,isft
   10   line2(i)=zer
      endif
   20 call strcat(maxc,line,maxd,line2,1,dot)
      call strsiz(maxc,line,ifig)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strrmv(maxc,line,nfrom,nto)
c-----------------------------------------------------------------------
c*    STRRMV:: remove characters from nfrom-th to nto-th column.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     nfrom  (i4)        ... the start column.
c     nto    (i4)        ... the last column to be removed.
cex
c     call strrmv(10,'abc de fg ',4,6)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  'abc_de_fg_'             'abcfg_____'
c     nfrom  :  4                        4
c     nto    :  6                        6
ce----------------------------------------------------------------------
      character*1  line(maxc)
c
      if(nto.gt.maxc) go to 900
      if(nfrom.gt.nto)  go to 900
      if(nto.lt.maxc) go to 20
      do 10 i=nfrom,maxc
   10 line(i)=' '
      return
   20 nto1=nto+1
      do 30 i=nto1,maxc
      k=nfrom+i-nto1
   30 line(k)=line(i)
      if(k.ge.maxc) return
      k1=k+1
      do 40 i=k1,maxc
   40 line(i)=' '
      return
c
c     error exit
  900 call msgout(0,0,'error(strrmv): form or to is outof range.$')
      end
cs----------------------------------------------------------------------
      subroutine strsft(maxc,line,nchr)
c-----------------------------------------------------------------------
c*    STRSFT:: shift string either to left or right.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     nchr               ... >0 shift nchr characters to the left.
c                            <0 shift to the right
cex
c     call strsft(10,'abc de fg ',-2)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  'abc_de_fg_'             '__abc_de_f'
c     nchr   :  -2                       ?
ce----------------------------------------------------------------------
      character*1  line(maxc)
c
      if(nchr.eq.0) return
      if(nchr.lt.0) go to 30
      nc=nchr
      n=maxc-nc
      if(n.le.0) go to 60
      do 10 i=1,n
      ii=nc+i
   10 line(i)=line(ii)
      n1=n+1
      do 20 i=n1,maxc
   20 line(i)=' '
      return
c
   30 nc=-nchr
      n=maxc-nc
      if(n.le.0) go to 60
      do 40 i=1,n
      ii=maxc-i+1
      jj=ii-nc
   40 line(ii)=line(jj)
      do 50 i=1,nc
   50 line(i)=' '
      return
c
   60 do 70 i=1,maxc
   70 line(i)=' '
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strsiz(maxc,line,nchr)
c-----------------------------------------------------------------------
c*    STRLEN:: counts number of chrs. cut blanks before and after chrs.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     nchr   (i4)        ... number of characters in 'line'.
cex
c     call strsiz(10,'    ab cd ',nchr)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '____ab_cd_'             'ab_cd_____'
c     nchr   :  ?                        5
crf   strln1
ce----------------------------------------------------------------------
      character*1 line(maxc)
c
      do 10 i=1,maxc
   10 if(line(i).ne.' ') go to 20
      nchr=0
      return
   20 is=i
      do 30 i=1,maxc
      ii=maxc-i+1
   30 if(line(ii).ne.' ') go to 40
      return
   40 ie=ii
      nchr=ie-is+1
      do 50 i=1,nchr
      ii=is+i-1
   50 if(i.ne.ii) line(i)=line(ii)
      if(nchr.ge.maxc) return
      nchr1=nchr+1
      do 60 i=nchr1,maxc
   60 line(i)=' '
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strtk1(maxc,line1,nchr1,line2,nchr2,char)
c-----------------------------------------------------------------------
c*    STRTK1:: pick up string before a character 'char'.
cag   maxc   (i4)        ... size of 'line1' and 'line2'.
c     line1  (c1:maxc)   ... string.
c     nchr1  (i4)        ... number of characters in line1 after picked
c     line2  (c1:maxc)   ... pickuped string.
c     nchr2  (i4)        ... number of characters in line2.
c     char   (c1)        ... a character.
cex
c     call strtk1(10,'abc de/fg ',nchr1,line2,nchr2,'/')
c               <input>                  <output>
c     maxc   :  10                       10
c     line1  :  'abc_de/fg_'             'fg_________'
c     nchr1  :  ?                        2
c     line2  :  ?                        'abc_de_____'
c     nchr2  :  ?                        5
c     char   :  '/'                      '/'
crf   strtok
ce----------------------------------------------------------------------
      character*1  line1(maxc),line2(maxc),char
c
      nchr1=0
      nchr2=0
      do 10 i=1,maxc
   10 line2(i)=' '
      call strsiz(maxc,line1,nchr)
      if(nchr.le.0) return
      do 20 i=1,nchr
      if(line1(i).eq.char) go to 50
   20 line2(i)=line1(i)
      nchr2=0
      nchr1=nchr
      do 30 i=1,maxc
   30 line2(i)=' '
      return
c
   50 call strsiz(maxc,line2,nchr2)
      is=i
      call strsft(maxc,line1,is)
      call strsiz(maxc,line1,nchr1)
c
      return
      end
cs---------------------------------------------------------------------
      subroutine strtoc(maxc,line,maxl,char)
c----------------------------------------------------------------------
c*    STRTOC:: copy string to a strage of different size.
cag   maxc   (i4)        ... size of 'line'.
c     line1  (c1:maxc) ... string.
c     maxl   (i4)        ... size of 'char'.
c     char   (c1:maxl)   ... destination strage.
cex
c     call strtoc(10,'abc de fg ',5,char)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  'abc_de_fg_'             'abc_de_fg__'
c     maxl   :  5                        5
c     char   :  ?                        'abc_d'
crf   strdup
ce---------------------------------------------------------------------
      character*1  line(maxc),char(maxl)
c
      do 10 i=1,maxl
   10 char(i)=line(i)
      return
      end
cs----------------------------------------------------------------------
      subroutine strtoi(maxc,line,int)
c-----------------------------------------------------------------------
c*    STRTOI:: converts string to an integer.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     int    (i4)        ... integer number.
cex
c     call strtoi(10,' 123      ',int)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '_123______'             ?
c     int    :  ?                        123
crf   strcnv
ce----------------------------------------------------------------------
      character*1  line(maxc)
      character*1  ten(11),mns,pls
      data         ten/'0','1','2','3','4','5','6','7','8','9',' '/
      data         num/11/
      data         mns/'-'/,pls/'+'/
c
      int=0
      call strsiz(maxc,line,n)
      if(n.le.0) go to 50
      isign=1
      if(line(1).eq.mns) isign=-1
      if(line(1).eq.mns.or.line(1).eq.pls) then
        call strsft(maxc,line,1)
        call strsiz(maxc,line,n)
        if(n.le.0) go to 50
      endif
      do 30 i=1,n
      do 10 j=1,num
   10 if(line(i).eq.ten(j)) go to 20
      go to 900
   20 j=j-1
      if(j.eq.10) j=0
      np=n-i
   30 int=int+j*10**np
   50 continue
      int=int*isign
      return
c
c     error exit
  900 call msgout(0,0,'error(strtoi): wrong data format.$')
      end
cs----------------------------------------------------------------------
      subroutine strtok(maxc,line1,nchr1,line2,nchr2)
c-----------------------------------------------------------------------
c*    STRTOK:: pick up string before ' ' or ','.
cag   maxc   (i4)        ... size of and 'line1' and 'line2'.
c     line1  (c1:maxc)   ... string.
c     nchr1  (i4)        ... number of characters in line1 after picked
c     line2  (c1:maxc)   ... pickuped string.
c     nchr2  (i4)        ... number of characters in line2.
cex
c     call strtok(10,'abc de fg ',nchr1,line2,nchr2)
c               <input>                  <output>
c     maxc   :  10                       10
c     line1  :  'abc_de_fg_'             'de_fg______'
c     nchr1  :  ?                        5
c     line2  :  ?                        'abc________'
c     nchr2  :  ?                        3
crf   strtk1
ce----------------------------------------------------------------------
      character*1  line1(maxc),line2(maxc)
      character*1  blank,comma
      data         blank/' '/,comma/','/
c
      icomm=0
      nchr1=0
      nchr2=0
      do 10 i=1,maxc
   10 line2(i)=blank
      call strsiz(maxc,line1,nchr)
      if(nchr.le.0) return
      k=0
      do 20 i=1,nchr
      if(line1(i).eq.comma) go to 40
      if(line1(i).eq.blank) go to 50
      k=k+1
   20 line2(k)=line1(i)
      nchr1=0
      nchr2=k
      do 30 i=1,maxc
   30 line1(i)=blank
      return
c
   40 icomm=1
   50 nchr2=k
      is=i
      call strsft(maxc,line1,is)
      call strsiz(maxc,line1,nchr)
      if(nchr.gt.0) go to 60
      nchr1=0
      return
   60 if(line1(1).eq.comma.and.icomm.eq.0) call strsft(maxc,line1,1)
      call strsiz(maxc,line1,nchr1)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine strtor(maxc,line,val)
c----------------------------------------------------------------------
c*    STRTOR : converts string to a real*4 data.
c*    note   : maximum 20 figures.
cag   maxc (i4)        ... size of 'line'.
c     line (c1:maxc)   ... string.
c     val  (r4)        ... floating point number.
cex
c     call strtor(10,'1.234e-2  ',val)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '1.234e-2__'             ?
c     val    :  ?                        1.234e-2
crf   strtow,strcnv
ce---------------------------------------------------------------------
      character*1  line(maxc),temp(40)
      character*1  ten(11),e,d,ue,ud,blank,pls,mns,dot
      data         ten/'0','1','2','3','4','5','6','7','8','9',' '/
      data         e/'e'/,d/'d'/,ue/'E'/,ud/'D'/,blank/' '/
      data         num/11/,maxe/4/
      data         pls/'+'/,mns/'-'/,dot/'.'/
c
      val=0.0
      ie=0
      call strsiz(maxc,line,n)
      if(n.le.0) go to 210
c     call strfdf(maxc,line,1,'.',ncol,mcol)
      ncol=0
      do 5 i=1,n
    5 if(line(i).eq.'.') ncol=i
      if(ncol.eq.0) then
         line(n+1)='.'
         line(n+2)='0'
         n=n+2
      endif
      do 10 i=1,n
      if(line(i).eq.e.or.line(i).eq.d) go to 20
   10 if(line(i).eq.ue.or.line(i).eq.ud) go to 20
      go to 100
   20 n2=n
      ii=i
      n=i-1
      n1=i+1
      if(n1.gt.n2) go to 100
      do 30 i=1,maxe
   30 temp(i)=blank
      k=0
      do 40 i=n1,n2
      k=k+1
   40 temp(k)=line(i)
      do 50 i=ii,n2
   50 line(i)=blank
      call strsiz(maxe,temp,m)
      if(m.gt.maxe) go to 900
      isign=1
      if(temp(1).eq.mns) isign=-1
      if(temp(1).eq.mns.or.temp(1).eq.pls) then
        call strsft(maxe,temp,1)
        call strsiz(maxe,temp,m)
        if(m.le.0) go to 100
      endif
      ie=0
      do 80 i=1,m
      do 60 j=1,num
   60 if(temp(i).eq.ten(j)) go to 70
      go to 900
   70 if(j.eq.11) j=1
      j=j-1
      np=m-i
   80 ie=ie+j*10**np
      ie=ie*isign
c
  100 sign=1
      if(line(1).eq.mns) sign=-1.0
      if(line(1).eq.mns.or.line(1).eq.pls) then
        call strsft(maxc,line,1)
        call strsiz(maxc,line,n)
        if(n.le.0) go to 200
      endif
      do 110 i=1,n
  110 if(line(i).eq.dot) go to 120
      go to 900
  120 ndot=i
      call strrmv(maxc,line,ndot,ndot)
      n1=n-1
      val=0.0
      do 150 i=1,n1
      do 130 j=1,num
  130 if(line(i).eq.ten(j)) go to 140
      go to 900
  140 if(j.eq.11) j=1
      j=j-1
      np=n1-i
  150 val=val+dble(j)*10.0**np
      npw=n-ndot
      val=val/10.0**npw
  200 val=val*sign
      val=val*10.0**ie
  210 continue
      return
c
c     error exit
  900 call msgout(0,1,'error(strtor): wrong data format.$')
      return
      end
cs----------------------------------------------------------------------
      subroutine strtow(maxc,line,val)
c----------------------------------------------------------------------
c*    STRTOW : converts string to a real*8 data.
c*    note   : maximum 20 figures.
cag   maxc (i4)        ... size of 'line'.
c     line (c1:maxc)   ... string.
c     val  (r8)        ... floating point number.
cex
c     call strtow(10,'1.234e-2  ',val)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '1.234e-2__'             ?
c     val    :  ?                        1.234e-2
crf   strtor,strcnv
ce---------------------------------------------------------------------
      character*1  line(maxc),temp(40)
      character*1  ten(11),e,d,ue,ud,blank,pls,mns,dot
      real*8       val
      data         ten/'0','1','2','3','4','5','6','7','8','9',' '/
      data         e/'e'/,d/'d'/,ue/'E'/,ud/'D'/,blank/' '/
      data         num/11/,maxe/4/
      data         pls/'+'/,mns/'-'/,dot/'.'/
c
      val=0.0d0
      ie=0
      call strsiz(maxc,line,n)
      if(n.le.0) go to 210
      do 10 i=1,n
      if(line(i).eq.e.or.line(i).eq.d) go to 20
   10 if(line(i).eq.ue.or.line(i).eq.ud) go to 20
      go to 100
   20 n2=n
      ii=i
      n=i-1
      n1=i+1
      if(n1.gt.n2) go to 100
      do 30 i=1,maxe
   30 temp(i)=blank
      k=0
      do 40 i=n1,n2
      k=k+1
   40 temp(k)=line(i)
      do 50 i=ii,n2
   50 line(i)=blank
      call strsiz(maxe,temp,m)
      if(m.gt.maxe) go to 900
      isign=1
      if(temp(1).eq.mns) isign=-1
      if(temp(1).eq.mns.or.temp(1).eq.pls) then
        call strsft(maxe,temp,1)
        call strsiz(maxe,temp,m)
        if(m.le.0) go to 100
      endif
      ie=0
      do 80 i=1,m
      do 60 j=1,num
   60 if(temp(i).eq.ten(j)) go to 70
      go to 900
   70 if(j.eq.11) j=1
      j=j-1
      np=m-i
   80 ie=ie+j*10**np
      ie=ie*isign
c
  100 sign=1
      if(line(1).eq.mns) sign=-1.0
      if(line(1).eq.mns.or.line(1).eq.pls) then
        call strsft(maxc,line,1)
        call strsiz(maxc,line,n)
        if(n.le.0) go to 200
      endif
      do 110 i=1,n
  110 if(line(i).eq.dot) go to 120
      go to 900
  120 ndot=i
      call strrmv(maxc,line,ndot,ndot)
      n1=n-1
      val=0.0d0
      do 150 i=1,n1
      do 130 j=1,num
  130 if(line(i).eq.ten(j)) go to 140
      go to 900
  140 if(j.eq.11) j=1
      j=j-1
      np=n1-i
  150 val=val+dble(j)*10.0**np
      npw=n-ndot
      val=val/10.0**npw
  200 val=val*sign
      val=val*10.0**ie
  210 continue
      return
c
c     error exit
  900 call msgout(0,1,'error(strtow): wrong data format.$')
      return
      end
cs----------------------------------------------------------------------
      subroutine strtyp(maxc,line,ntype)
c-----------------------------------------------------------------------
c*    STRTYP:: find data type of a string.
cag   maxc   (i4)        ... size of 'line'.
c     line   (c1:maxc)   ... string.
c     ntype  (i4)        ... 0:integer,1:real,2:character,3:blank.
cex
c     call strtyp(10,'  1.23    ',ntype)
c               <input>                  <output>
c     maxc   :  10                       10
c     line   :  '__1.23____'             '1.23_______'
c     ntype  :  ?                        1
crf   strcnv
ce----------------------------------------------------------------------
      character*1 line(maxc)
      character*1 anum(13)
      data        anum /'0','1','2','3','4','5','6','7','8','9',
     .                  '.','+','-'/
c
      ntype=3
      call strsiz(maxc,line,maxx)
      if(maxx.le.0) return
      ntype=2
      do 10 i=1,13
   10 if(line(1).eq.anum(i)) go to 20
      return
   20 ntype=0
      if=i
      if(i.eq.11.or.i.eq.12.or.i.eq.13) ntype=2
      if(maxx.le.1) return
      do 30 i=2,maxx
   30 if(line(i).ne.' ') go to 40
      return
   40 is=i
      ntype=2
      if(if.eq.11.and.is.ne.2) return
      id=0
      do 70 i=is,maxx
      do 50 j=1,11
   50 if(line(i).eq.anum(j)) go to 60
      return
   60 if(j.eq.11) id=id+1
      if(id.gt.1) return
   70 continue
      ntype=0
      if(id.eq.1) ntype=1
c
      return
      end
cs----------------------------------------------------------------------
      subroutine trcord(x,xt,x0,v)
c-----------------------------------------------------------------------
c     transform xt by v and store in x. x0 is the coord. of origin
ce----------------------------------------------------------------------
      dimension xt(3),x(3),x0(3),v(3,3)
      xx=xt(1)
      yy=xt(2)
      zz=xt(3)
      x(1)=xx*v(1,1)+yy*v(1,2)+zz*v(1,3)+x0(1)
      x(2)=xx*v(2,1)+yy*v(2,2)+zz*v(2,3)+x0(2)
      x(3)=xx*v(3,1)+yy*v(3,2)+zz*v(3,3)+x0(3)
      return
      end
cs----------------------------------------------------------------------
      subroutine trnmat(ra,ri,rf,u)
c-----------------------------------------------------------------------
c*    TRNMAT:: transformation matrix for the rotation of ri to rf around
c              ra.
cag   ra (r4:3)    ... axis vector of rotation.
c     ri (r4:3)    ... initial vector.
c     rf (r4:3)    ... final vector.
c     u  (r4:3*3)  ... transformation matrix.
ce----------------------------------------------------------------------
      dimension ra(3),ri(3),rf(3),u(3,3)
      dimension ey(3),ez(3),vec(3)
      dimension v1(3,3),v2(3,3),v3(3,3),u1(3,3)
      dimension raxyz(3),rixyz(3),rfxyz(3)
      data      zero/0.0d0/,two/2.0/
      data      pi/3.14159265358979/
      data      ey/0.0,1.0,0.0/
      data      ez/0.0,0.0,1.0/
c
      call unimat(v1)
      raxyz(1)=ra(1)
      raxyz(2)=ra(2)
      raxyz(3)=zero
      call anglet(raxyz,ey,t)
      call prout(raxyz,ey,vec)
      if(vec(3).lt.zero) t=two*pi-t
      cost=cos(t)
      sint=sin(t)
      v1(1,1)=cost
      v1(1,2)=-sint
      v1(2,1)= sint
      v1(2,2)= cost
      call trnvec(v1,ra)
      call trnvec(v1,ri)
      call trnvec(v1,rf)
      call unimat(v2)
      call anglet(ra,ez,t)
      call prout(ra,ez,vec)
      if(vec(1).lt.zero) t=two*pi-t
      cost=cos(t)
      sint=sin(t)
      v2(2,2)= cost
      v2(2,3)=-sint
      v2(3,2)= sint
      v2(3,3)= cost
      call trnvec(v2,ri)
      call trnvec(v2,rf)
      call unimat(v3)
      rixyz(1)=ri(1)
      rixyz(2)=ri(2)
      rixyz(3)=zero
      rfxyz(1)=rf(1)
      rfxyz(2)=rf(2)
      rfxyz(3)=zero
      call anglet(rixyz,rfxyz,t)
      call prout(rixyz,rfxyz,vec)
      if(vec(3).lt.zero) t=two*pi-t
      cost=cos(t)
      sint=sin(t)
      v3(1,1)= cost
      v3(1,2)=-sint
      v3(2,1)= sint
      v3(2,2)= cost
c     forms the transformation matrix
      do 100 i=1,3
      do 100 j=1,3
      u1(i,j)=zero
      do 100 k=1,3
  100 u1(i,j)=u1(i,j)+v1(k,i)*v2(j,k)
      do 110 i=1,3
      do 110 j=1,3
      u(i,j)=zero
      do 110 k=1,3
  110 u(i,j)=u(i,j)+u1(i,k)*v3(k,j)
      do 120 i=1,3
      do 120 j=1,3
      u1(i,j)=zero
      do 120 k=1,3
  120 u1(i,j)=u1(i,j)+u(i,k)*v2(k,j)
      do 130 i=1,3
      do 130 j=1,3
      u(i,j)=zero
      do 130 k=1,3
  130 u(i,j)=u(i,j)+u1(i,k)*v1(k,j)
      return
      end
cs----------------------------------------------------------------------
      subroutine trnvec(u,r)
c-----------------------------------------------------------------------
c*    TRNVEC:: transforms vector r by u, rr=u*r. rr is a scratch array.
cag   u  (r4:3*3) ... transformation matrix.
c     r  (r4:3)   ... original vector (input) and result vector(output).
ce----------------------------------------------------------------------
      dimension   r(3),rr(3),u(3,3)
      data     zero/0.0/,eps/1.0e-12/
c
      rr(1)=r(1)*u(1,1)+r(2)*u(1,2)+r(3)*u(1,3)
      rr(2)=r(1)*u(2,1)+r(2)*u(2,2)+r(3)*u(2,3)
      rr(3)=r(1)*u(3,1)+r(2)*u(3,2)+r(3)*u(3,3)
      do 10 i=1,3
      if(abs(rr(i)).lt.eps) rr(i)=zero
   10 r(i)=rr(i)
c
      return
      end
cs----------------------------------------------------------------------
      subroutine unimat(v)
c-----------------------------------------------------------------------
c*    SETMAT:: set 3*3 matrix v to unity.
cag   v (r4:3*3)  ... matrix.
ce----------------------------------------------------------------------
      dimension   v(3,3)
      data     zero/0.0/,one/1.0/
c
      do 20 i=1,3
      do 10 j=1,3
   10 v(i,j)=zero
   20 v(i,i)=one
c
      return
      end
cs----------------------------------------------------------------------
      subroutine vector(v1,v2,vp,knorm,key)
c-----------------------------------------------------------------------
c*    VECTOR:: vectr manipulation. sum,differece,inner and outer product
cag   v1    (r4:3) ... vecter.
c     v2    (r4:3) ... vector.
c     vp    (r4:3) ... result vector.(note:inner product in vp(1))
c     knorm (i4)   ... 0:normarize, 1:not normarize.
c     key   (i4)   ... 0:sum,1:difference,2:inner product,3:outer produc
ce----------------------------------------------------------------------
      dimension  vp(3),v1(3),v2(3)
      data       one/1.0/,eps/1.0e-12/
c
      if(key.lt.0.or.key.gt.3) go to 900
      k=key+1
      go to (10,20,30,40),k
   10 vp(1)=v1(1)+v2(1)
      vp(2)=v1(2)+v2(2)
      vp(3)=v1(3)+v2(3)
      go to 50
   20 vp(1)=v1(1)-v2(1)
      vp(2)=v1(2)-v2(2)
      vp(3)=v1(3)-v2(3)
      go to 50
   30 vp(1)=v1(1)*v2(1)+v1(2)*v2(2)+v1(3)*v2(3)
      go to 100
   40 vp(1)=v1(2)*v2(3)-v1(3)*v2(2)
      vp(2)=v1(3)*v2(1)-v1(1)*v2(3)
      vp(3)=v1(1)*v2(2)-v1(2)*v2(1)
   50 if(knorm.ne.0) go to 100
      vnorm=vp(1)*vp(1)+vp(2)*vp(2)+vp(3)*vp(3)
      if(abs(vnorm).lt.eps) go to 910
      vnorm=one/sqrt(vnorm)
      vp(1)=vp(1)*vnorm
      vp(2)=vp(2)*vnorm
      vp(3)=vp(3)*vnorm
  100 continue
      return
c
c     error exit
  900 call msgout(0,1,'error(vector): wrong key.$')
      call msgou0(0,0,' key=$',key)
  910 call msgout(0,1,'error(vector): norm is too small.$')
      call msgou2(0,0,1,vnorm,6,1)
      end
cs---------------------------------------------------------------------
      subroutine fmogms(iout,nnode,ncpu,smem,nrun,nwf,nbas,
     .                  nlayer,mgopt,icube,gspace,ncore,nacorb,nacele,
     .                  nintic)
c----------------------------------------------------------------------
c     create input data for fmo calulations with Gamess.
c     $contrl, $system, $gddi, $intgl, $scf
ce---------------------------------------------------------------------
      dimension  nbas(*),nwf(*)
      character  line*80,temp*80
      data maxc/80/
c
c     $contrl
      line='$contrl'
      temp='energy'
      if(nrun.eq.2) temp='gradient'
      if(nrun.eq.3) temp='optimize'
      if(nrun.eq.4) temp='optfmo'
      call strsiz(maxc,temp,mc)
      call strlas(maxc,line,nc)
      line=line(1:nc)//' runtyp='//temp(1:mc)
      call strlas(maxc,line,nc)
      ndfunc=0
      nmp2=0
      do i=1,nlayer
         if(nbas(i).eq.4.or.nbas(i).eq.5) ndfunc=ndfunc+1
         if(nwf(i).eq.3) nmp2=nmp2+1
      enddo
      ndft=0
      do i=1,nlayer
         if(nwf(i).eq.2) ndft=ndft+1
      enddo
      if(ndfunc.gt.0) then
         line=line(1:nc)//' ispher=1'
         call strlas(maxc,line,nc)
      endif
      if(ndft.eq.0) then
         line=line(1:nc)//' nprint=-5 $end'
      else
         line=line(1:nc)//' dfttyp=B3LYP nprint=-5 $end'
      endif
      call prtstr(iout,maxc,line)
c     $system
      n1=(smem-75.0)/8.0/float(ncpu)
c2.3      n2=0
c2.3      if(nmp2.gt.0) then
c2.3         n1=25
c2.3         n2=((smem-75.0)/8.0-25.0*float(ncpu))*float(nnode)
c2.3      endif
      call stri2c(maxc,n1,temp,ifig)
      line='$system'//' mwords='//temp(1:ifig)//' $end'
c2.3      line='$system'//' mwords='//temp(1:ifig)
c2.3      call strlas(maxc,line,nc)
c2.3      call stri2c(maxc,n2,temp,ifig)
c2.3      line=line(1:nc)//' memddi='//temp(1:ifig)//' $end'
      call prtstr(iout,maxc,line)
c     $gddi
      call stri2c(maxc,nnode,temp,ifig)
      line='$gddi'//' ngroup='//temp(1:ifig)//' $end'
      call prtstr(iout,maxc,line)
c     $intgrl
      nintic=0
      ncorr=0
      nmp2=0
      do i=1,nlayer
         if(nwf(i).gt.3) ncorr=ncorr+1
         if(nwf(i).eq.3) nmp2=nmp2+1
      enddo
      if(ncorr.le.0) then
         n3=-(n1-20)
c        nintic should be given in words not in mega words !
         nintic=n3*1000000
         if(nintic.gt.0) nintic=0
         if(icube.ne.1) nintic=0
         line='$intgrl'
         call stri2c(maxc,nintic,temp,ifig)
         line='$intgrl'//' nintic='//temp(1:ifig)//' $end'
         if(nintic.ne.0) call prtstr(iout,maxc,line)
      endif
c     $scf
c      if(nintic.eq.0) then
      if(ncorr.gt.0.or.nintic.eq.0.or.icube.ne.1) then
         line='$scf dirscf=.t. npunch=0 $end'
      else
         line='$scf dirscf=.f. npunch=0 $end'
      endif
      call prtstr(iout,maxc,line)
c     $dft
      if(ndft.gt.0) then
ccc         line='$dft dfttyp=B3LYP nrad0=96 nthe0=12 nphi0=24 $end'
         line='$dft nrad0=96 nthe0=12 nphi0=24 $end'
         call prtstr(iout,maxc,line)
      endif
c     $det
      nmc=0
      do i=1,nlayer
         if(nwf(i).eq.5) nmc=nmc+1
      enddo
      if(nmc.gt.0) then
         call stri2c(maxc,ncore,temp,ifig)
         line='$det ncore='//temp(1:ifig)//' nact='
         call strsiz(maxc,line,nc)
         call stri2c(maxc,nacorb,temp,ifig)
         line=line(1:nc)//temp(1:ifig)//' nels='
         call strsiz(maxc,line,nc)
         call stri2c(maxc,nacele,temp,ifig)
         line=line(1:nc)//temp(1:ifig)//' $end'
         call prtstr(iout,maxc,line)
      endif
c     $statpt
      if(nrun.eq.3) then
         line='$statpt nstep=200 nprt=-2 npun=-2 kdiagh=2 $end'
         call prtstr(iout,maxc,line)
      endif
c     $optfmo
      if(nrun.eq.4.and.mgopt.ne.0) then
         line=' '
         if(mgopt.eq.1) line='$optfmo method=cg $end'
         if(mgopt.eq.2) line='$optfmo method=hssupd $end'
         if(mgopt.eq.3) line='$optfmo method=qa $end'
         call prtstr(iout,maxc,line)
      endif
c     $grid
      if(icube.gt.1) then
         idg=2
         call strr2c(maxc,gspace,temp,ifig,idg)
         line='$grid size='//temp(1:ifig)//' $end'
         call prtstr(iout,maxc,line)
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine fmoprp(iout,nnode,nrun,nbody,nwf,nbas,
     .             mulk,icube,ipieda,nintic,nlayer,nfglay,ipcm,npcmit)
c---------------------------------------------------------------------
c     $fmo groups
ce---------------------------------------------------------------------
      dimension nbas(*),nwf(*),nfglay(*)
      character*80  line
      data maxc/80/
c
c     $fmoprp group
      nmc=0
      do i=1,nlayer
         if(nwf(i).eq.5) nmc=nmc+1
      enddo
      if(nmc.gt.0) then
         write(iout,2000)
 2000    format('! You should provide monomer MCSCF initial orbitals bef
     .ore running the job.'/'! See REFS.DOC for more details') 
      endif
      line='$fmoprp'
      call prtstr(iout,maxc,line)
      if(nmc.gt.0) then
         line='  nguess=18 irest=2 modorb=3'
         call prtstr(iout,maxc,line)
      endif
c     ngrfmo
      call ngrfmo(iout,nbody,nlayer,nfglay,nrun,nwf,nnode)
c     cube
      if(icube.eq.2) then
         line='  modprp=20'
      elseif(icube.eq.3) then
         line='  modprp=24'
      endif
      if(icube.gt.1) call prtstr(iout,maxc,line)
c     pieda
      if(ipieda.ne.0) then
         line='  ipieda=1'
         call prtstr(iout,maxc,line)
      endif
c     naodir
      mxbas=0
      do i=1,nlayer
         if(nbas(i).gt.mxbas) mxbas=nbas(i)
      enddo
      if(nintic.ne.0) then
         if(mxbas.eq.1) line='  naodir=220'
         if(mxbas.eq.2) line='  naodir=210'
         if(mxbas.eq.3) line='  naodir=210'
         if(mxbas.eq.4) line='  naodir=200'
         if(mxbas.eq.5) line='  naodir=190'
         call prtstr(iout,maxc,line)
      endif
c     nprint
      if(mulk.eq.1) then
         line='  nprint=9'
         call prtstr(iout,maxc,line)
      endif
c     npcmit
      if(ipcm.ne.0.and.npcmit.gt.0) then
         line='  npcmit=2'
         call prtstr(iout,maxc,line)
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine chmelm(nelm,kelm)
c----------------------------------------------------------------------
c     return unique elements
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      dimension kelm(*)
c
      nelm=1
      kelm(1)=ian(1)
      if(natm.le.1) go to 120
      do 100 i=2,natm
      do 80 j=1,nelm
      if(kelm(j).eq.ian(i)) go to 100
   80 continue
      nelm=nelm+1
      kelm(nelm)=ian(i)
  100 continue
  120 continue
      return
      end
cs---------------------------------------------------------------------
      subroutine polfnc(ian,nbas,polgau)
c----------------------------------------------------------------------
c     return shell type, # of gauissian, exponents, and contraction
c     coefficients of ploarization functions for the element of ian.
c     nbas=4 for 6-31G and =5 for 6-311G
ce---------------------------------------------------------------------
      parameter (ndef=4)
      character*17 pol31(ndef+1),pol311(ndef+1),polgau
      dimension ianum(ndef)
      data ianum/6,7,8,16/
c c,n,o,s, and other elements
      data pol31 /'d 1 ; 1 0.800 1.0', 
     .            'd 1 ; 1 0.800 1.0', 
     .            'd 1 ; 1 0.800 1.0', 
     .            'd 1 ; 1 0.650 1.0', 
     .            'add data yourself'/
c c,n,o,s, and other elements
      data pol311 /'d 1 ; 1 0.626 1.0', 
     .             'd 1 ; 1 0.913 1.0', 
     .             'd 1 ; 1 1.292 1.0', 
     .             'd 1 ; 1 0.650 1.0', 
     .             'add data yourself'/
c
      if(nbas.eq.4) then
         polgau=pol31(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               polgau=pol31(i)
            endif
         enddo
      elseif(nbas.eq.5) then
         polgau=pol311(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               polgau=pol311(i)
            endif
         enddo
      else
         polgau=pol31(ndef+1)
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine diffnc(ian,nbas,difgau)
c----------------------------------------------------------------------
c     return shell type, # of gauissian, exponents, and contraction
c     coefficients of diffuse functions for the element of ian=6 and 8.
c     nbas=1 for sto-3g, nbas=2 for 3-21G, nbas=3 or 4 for 6-31G and
c     nbas=5 for 6-311G.
ce---------------------------------------------------------------------
      parameter (ndef=2)
      character*22 difsto(ndef+1),dif321(ndef+1)
      character*22 dif31(ndef+1),dif311(ndef+1),difgau
      dimension ianum(ndef)
      data ianum/6,8/
c c
      data difsto/'l 1 ; 1 0.0438 1.0 1.0',
c o
     .            'l 1 ; 1 0.0845 1.0 1.0',
c for other elements, supply data yourself
     .            'add data yourself     '/
c c
      data dif321 /'l 1 ; 1 0.0438 1.0 1.0',
c o
     .             'l 1 ; 1 0.0845 1.0 1.0',
c for other elements, supply data yourself
     .             'add data yourself     '/
c c
      data dif31  /'l 1 ; 1 0.0438 1.0 1.0',
c o
     .             'l 1 ; 1 0.0845 1.0 1.0',
c for other elements, supply data yourself
     .             'add data yourself     '/
c c
      data dif311 /'l 1 ; 1 0.0438 1.0 1.0',
c o
     .             'l 1 ; 1 0.0845 1.0 1.0',
c for other elements, supply data yourself
     .             'add data yourself     '/
c
      if(nbas.eq.1) then
         difgau=difsto(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               difgau=difsto(i)
            endif
         enddo
      elseif(nbas.eq.2) then
         difgau=dif321(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               difgau=dif321(i)
            endif
         enddo
      elseif(nbas.eq.3.or.nbas.eq.4) then
         difgau=dif31(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               difgau=dif31(i)
            endif
         enddo
      elseif(nbas.eq.5) then
         difgau=dif311(ndef+1)
         do i=1,ndef
            if(ian.eq.ianum(i)) then
               difgau=dif311(i)
            endif
         enddo
      else
         difgau=dif31(ndef+1)
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine layer(iout,nlayer,laydat,ilay,nfglay)
c----------------------------------------------------------------------
c     make layer data.
ce---------------------------------------------------------------------
      parameter (MaxFrg=50000)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      character*256 laydat(*)
      dimension     ilay(*),itemp(MaxFrg)
      dimension     nfglay(*)
      data maxc/256/
c
   10 continue
      ierr=0
      do 20 i=1,nfrg
   20 ilay(i)=1
      do 100 i=2,nlayer
      call strsiz(maxc,laydat(i),nc)
      if(nc.le.0) then
          ierr=1
          go to 200
      endif
      if(laydat(i)(1:1).eq.'*') then
         irem=i
      else
         call strint(maxc,laydat(i),MaxFrg,ntemp,itemp)
         if(ntemp.gt.0) then
            do 40 j=1,ntemp
            if(itemp(j).le.0.or.itemp(i).gt.nfrg) then
               ierr=2
               go to 200
            else
               if(ilay(itemp(j)).ne.1) then
                  ierr=3
                  go to 200
               else
                  ilay(itemp(j))=i
               endif
            endif
   40       continue
         else
            ierr=4
            go to 200
         endif
      endif
  100 continue
      if(irem.ne.0) then
         do 120 i=1,nfrg
         if(ilay(i).eq.0) ilay(i)=irem
  120    continue
      endif
c     check if all fragments are assigned to a layer
      do 140 i=1,nfrg
      if(ilay(i).eq.0) then
         ierr=5
         go to 200
      endif
  140 continue
      go to 300
c
  200 continue
c     input error. re-enter.
      ioutsv=iout
      iout=6
      call msgini(iout)
      if(ierr.eq.1) write(iout,*) ' empty layer is found. layer=',i
      if(ierr.eq.2) write(iout,*) ' wrong fragment # for layer i=',i,
     .itemp(j)
      if(ierr.eq.2) write(iout,*) ' number of fragmnts is',nfrg
      if(ierr.eq.3) write(iout,*) ' there is doubly assigned fragment. i
     .fg=',itemp(j)
      if(ierr.eq.4) write(iout,*) ' empty layer i=',i
      if(ierr.eq.5) write(iout,*) ' unassigned fragments are found. ifg=
     .',i
      write(*,*) ' !!! re-enter layer data.'
         do 220 i=2,nlayer
         write(*,*) ' 1> Enter fragment numbers to be assigned to layer 
     .',i
         if(i.eq.2) write(*,*) '       ex. 2 3 - 5 8 10.'
         write(*,*) ' '
         read(*,1200) laydat(i)
 1200    format(a256)
         call strsiz(256,laydat(i),nc)
         if(nc.le.0) then
            write(*,*) ' ! quit with wrong layer data.'
            stop
         endif
  220    continue
      iout=ioutsv
      call msgini(iout)
      go to 10
  300 continue
c
      do i=1,nlayer
         nfglay(i)=0
      enddo
      do i=1,nfrg
         nfglay(ilay(i))=nfglay(ilay(i))+1
      enddo
c
      return
      end
cs---------------------------------------------------------------------
      subroutine prtint(iout,varnam,ndat,idat)
c----------------------------------------------------------------------
c     print out i1 data in the format for icharg, layer etc.
c      icharg(1)= 1, 1, 1, 1, 1,   2, 1, 1,-1, 1,
c                 ....
c                 1, 1, 1
c     where 'icharg(1)=' is varnam.
ce---------------------------------------------------------------------
      dimension idat(*)
      character*10 varnam
      character*80 line,line1
      data maxc/80/
c
      call strcle(maxc,line)
      line(1:15)='     '//varnam
      idt=0
      n=ndat/10
      ns=mod(ndat,10)
      nt=10
      if(n.eq.0) nt=ns
      do 40 i=1,nt
      idt=idt+1
      call strlas(maxc,line,nc)
      if(mod(i,6).eq.0) line=line(1:nc)//'  '
      call stri2c(maxc,idat(idt),line1,ifig)
      call strlas(maxc,line,nc)
      if(i.eq.6) nc=nc+2
      if(idat(idt).ge.0) then
         line=line(1:nc)//' '//line1(1:ifig)
      else
         line=line(1:nc)//line1(1:ifig)
      endif
      call strlas(maxc,line,nc)
      if(idt.ne.ndat) line=line(1:nc)//','
   40 continue
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
      if(n.le.0) go to 200
      do 100 i=1,n-1
      do 80 j=1,10
      idt=idt+1
      call strlas(maxc,line,nc)
      if(mod(j,6).eq.0) line=line(1:nc)//'  '
      call stri2c(maxc,idat(idt),line1,ifig)
      call strlas(maxc,line,nc)
      if(mod(j,6).eq.0) nc=nc+2
      if(idat(idt).ge.0) then
         line=line(1:nc)//' '//line1(1:ifig)
      else
         line=line(1:nc)//line1(1:ifig)
      endif
      call strlas(maxc,line,nc)
      if(idt.ne.ndat) line=line(1:nc)//','
   80 continue
      call strsft(maxc,line,-15)
      call prtstr(iout,maxc,line)
      call strcle(maxc,line)
  100 continue
c
      if(ns.eq.0) go to 200
      do 180 i=1,ns
      idt=idt+1
      call strlas(maxc,line,nc)
      if(mod(i,6).eq.0) line=line(1:nc)//'  '
      call stri2c(maxc,idat(idt),line1,ifig)
      call strlas(maxc,line,nc)
      if(mod(i,6).eq.0) nc=nc+2
      if(idat(idt).ge.0) then
         line=line(1:nc)//' '//line1(1:ifig)
      else
         line=line(1:nc)//line1(1:ifig)
      endif
      call strlas(maxc,line,nc)
      if(idt.ne.ndat) line=line(1:nc)//','
  180 continue
      call strsft(maxc,line,-15)
      call prtstr(iout,maxc,line)
  200 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine ngrfmo(iout,nbody,nlayer,nfglay,nrun,nwf,nnode)
c----------------------------------------------------------------------
c     print ngrfmo parametrs
ce---------------------------------------------------------------------
      dimension nwf(*),nfglay(*)
      character*80 line,line1
      data maxc/80/
c
c     if nlayer=1 and wavefunction=CC, then force to single processer.
c2.3      if(nlayer.eq.1.and.nwf(1).eq.4) return
c
c     ngrfmo(1)
      call strcle(maxc,line)
      line(1:12)='  ngrfmo(1)='
c
      do 100 i=1,nlayer
      nfgi=0
      do j=i,nlayer
         nfgi=nfgi+nfglay(j)
      enddo
c      n1=(smem-75.0)/8.0/float(ncpu)
c2.3      n2=0
c2.3      if(nwf(i).eq.3.or.nwf(i).eq.4) then
c         n1=25
c2.3         n2=((smem-75.0)/8.0-25.0*float(ncpu))*float(nnode)
c2.3      endif
      n4=min(nfgi/4,nnode)
      n5=min(nfgi,nnode)
      if(nwf(i).eq.3.or.nwf(i).eq.4) then
c2.3         if(nfgsiz.eq.1) then
c2.3            mnmem1=100
c2.3            mnmem2=400
c2.3         else
c2.3            mnmem1=400
c2.3            mnmem2=1600
c2.3         endif
c2.3         mnnod1=(float(mnmem1-1))/(float(n2)/float(nnode))+1
c2.3         mnnod2=(float(mnmem2-1))/(float(n2)/float(nnode))+1
c2.3         if(mnnod1.lt.nnode.or.mnnod2.lt.nnode) then
c            if(mnnod2.lt.nnode) mnmod2=nnode
c            if(mnnod1.lt.nnode) mnmod1=nnode
            if(nwf(i).eq.3.and.nrun.gt.1) write(iout,2010)
 2010       format('! Probably you need to provide more nodes to have en
     .ough memory.')
            if(nwf(i).eq.4) write(iout,2020)
 2020       format('! The parallel CC code requires expert setting of me
     .mory (mwords/memddi).')
c2.3         endif
c2.3         m1=float(nnode)/float(mnnod1)
c2.3         m2=float(nnode)/float(mnnod2)
c2.3         n4=min(nfgi/4,m1)
c2.3         n5=min(nfgi,m2)
      endif
      if(nwf(i).eq.5) n5=min(n5,nfgi-1)
      if(n4.le.0) n4=1
      if(n5.le.0) n5=1
c2.3     CC runs only on single processor
c2.3      if(nwf(i).eq.4) then
c2.3         n4=nnode
c2.3         n5=nnode
c2.3      endif
c     nbody=3
      n6=0
      if(nbody.eq.3) then
         n6=0
      endif
c???
      call stri2c(maxc,n4,line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//line1(1:ifig)
      call stri2c(maxc,n5,line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//','//line1(1:ifig)
      call stri2c(maxc,n6,line1,ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//','//line1(1:ifig)
      call strlas(maxc,line,nc)
      line=line(1:nc)//',0,0,  0,0,0,0,0,'
      if(i.eq.nlayer) then
         call strlas(maxc,line,nc)
         line(nc:nc)=' '
      endif
      if(nlayer.gt.1.and.i.gt.1) then
         call strsft(maxc,line,-12)
      endif
      call prtstr(iout,maxc,line)
      if(i.ge.1) then
         call strcle(maxc,line)
      endif
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine datagr(iout,nbas,nlayer,idiffs,i2sto,isi6)
c----------------------------------------------------------------------
c     $data group
ce---------------------------------------------------------------------
      character*80 title
      common/pdbhed/title
      dimension  kelm(100),ktmp(100)
      dimension  nbas(*)
      character*6 basnms(5)
      character*17 polgau,poltmp
      character*22 difgau,diftmp
      character*53 basfnc(20)
      data        basnms/'sto 3 ','n21 3 ','n31 6 ','n31 6 ','n311 6'/
      character  line*80,temp*80
      data maxc/80/
c      idummy=0
c     count unique elements in the system
      call chmelm(nelm,kelm)
      call isort(nelm,kelm,ktmp)
c      n2nd=0
c      do i=1,nelm
c         if(kelm(i).ge.11.and.kelm(i).le.18) n2nd=n2nd+1
c      enddo
c      nsto=0
c      do i=1,nlayer
c         if(nbas(i).eq.1) nsto=nsto+1
c      enddo
c      if(n2nd.gt.0.and.nsto.gt.0) then
c         write(iout,*) '! NOTE: the STO-3G basis set of 2nd raw atoms in
c     . GAMESS is different'
c         write(iout,*) '! from original one. Here the original basis fun
c     .ction is used.'
c      endif
      write(iout,2200)
 2200 format(1x,'$data')
      call strsiz(maxc,title,nc)
      if(nc.gt.0) then
         call prtstr(iout,nc,title)
      else
         write(iout,2400)
 2400    format(1x,'<Enter your job title here>')
      endif
      write(iout,2600)
 2600 format(1x,'C1')
      do 120 ilay=1,nlayer
      ii=ilay
         do 100 i=1,nelm
         call elmian(line,kelm(i),3)
         call strsiz(2,line,nc)
         call stri2c(maxc,ii,temp,ifg)
         line=line(1:nc)//'.1-'//temp(1:ifg)
         write(iout,2800) line,kelm(i)
 2800    format(1x,a6,i4)
         if(nbas(ilay).eq.1) then
            call bassto(kelm(i),nl,basfnc,i2sto)
         elseif(nbas(ilay).eq.2) then
            call bas321(kelm(i),nl,basfnc)
         elseif(nbas(ilay).eq.3) then
            call bas631(kelm(i),nl,basfnc,isi6)
         elseif(nbas(ilay).eq.4) then
            call bas631(kelm(i),nl,basfnc,isi6)
         elseif(nbas(ilay).eq.5) then
            call bs6311(kelm(i),nl,basfnc)
         endif
         do j=1,nl
            line=basfnc(j)
            jj=-8
            if(j.eq.1) jj=-6
            call strsft(maxc,line,jj)
            call prtstr(iout,maxc,line)
         enddo
         if(nbas(ilay).ge.4.and.kelm(i).ne.1) then
            call polfnc(kelm(i),nbas(ilay),poltmp)
            call strtk1(17,poltmp,nc,polgau,mc,';')
            write(iout,2950) polgau
            write(iout,2950) poltmp
 2950       format(8x,a17)
         endif
         write(iout,*) ' '
  100    continue
  120 continue
c     diffuse functions on C and O of COO- functional groups 
      if(idiffs.eq.1) then
         do 160 ilay=1,nlayer
         ii=ilay
         call stri2c(maxc,ii,temp,ifg)
         line='c.2-'//temp(1:ifg)//'   6'
         call prtstr(iout,maxc,line)
         write(iout,2900) basnms(nbas(ilay))
 2900    format(3x,a10)
         if(nbas(ilay).gt.1) then
            call diffnc(6,nbas(ilay),diftmp)
            call strtk1(22,diftmp,nc,difgau,mc,';')
            write(iout,2960) difgau
            write(iout,2960) diftmp
 2960       format(8x,a22)
         endif
         if(nbas(ilay).ge.4) then
            call polfnc(6,nbas(ilay),poltmp)
            call strtk1(17,poltmp,nc,polgau,mc,';')
            write(iout,2950) polgau
            write(iout,2950) poltmp
         endif
         write(iout,*) ' '
         line='o.2-'//temp(1:ifg)//'   8'
         call prtstr(iout,maxc,line)
         write(iout,2900) basnms(nbas(ilay))
         if(nbas(ilay).gt.1) then
            call diffnc(8,nbas(ilay),diftmp)
            call strtk1(22,diftmp,nc,difgau,mc,';')
            write(iout,2960) difgau
            write(iout,2960) diftmp
         endif
         if(nbas(ilay).ge.4) then
            call polfnc(8,nbas(ilay),poltmp)
            call strtk1(17,poltmp,nc,polgau,mc,';')
            write(iout,2950) polgau
            write(iout,2950) poltmp
         endif
         write(iout,*) ' '
  160    continue
      endif
      write(iout,3000)
 3000 format(1x,'$end')
      return
      end
cs---------------------------------------------------------------------
      subroutine rdjob1(iunit)
c----------------------------------------------------------------------
c     read default values for job #1 in fmoutil.def file
ce---------------------------------------------------------------------
      real    memory,grids
      integer frgsiz,sscys,gly
      character*256 lay
      common/input1/nnodes,ncpus,nrun,method,nbody,nlayer,layer(5),
     .              nwf(5),imcscf,ncore,nacorb,nacele,idbas(5),
     .              mullk,icube,frgsiz,sscys,gly,idiffs,i2sto,isi6,
     .              multip,memory,grids,ipieda,lay(5)
      parameter (MaxDef=40)
      integer       idata(MaxDef-2)
      equivalence   (idata(1),nnodes)
      character*8   keywrd(MaxDef)
      data          keywrd/'nnodes  ','ncpus   ','nrun    ','method  ',
     .                     'nbody   ','nlayer  ','layer(1)','layer(2)',
     .                     'layer(3)','layer(4)','layer(5)','nwf(1)  ',
     .                     'nwf(2)  ','nwf(3)  ','nwf(4)  ','nwf(5)  ',
     .                     'imcscf  ','ncore   ','nacorb  ','nacele  ',
     .                     'basid(1)','basid(2)','basid(3)','basid(4)',
     .                     'basid(5)','mulliken','cube    ','nfgsiz  ',
     .                     'ifcys   ','ifgly   ','diffsp  ','gmssto  ',
     .                     'gms631  ','multip  ','memory  ','grid    ',
     .                     'ipieda  ','        ','        ','        '/
      integer       intdat(5)
      character*256 line,line1
      data maxc/256/
c
      do i=1,MaxDef-2
         idata(i)=0
      enddo
      memory=0.0
      grids=0.0
      do i=1,5
         lay(i)=' '
      enddo
c
      rewind iunit
   20 continue
      read(iunit,1000,end=100) line
 1000 format(a80)
      call strsiz(maxc,line,nc)
c     skip a blank line and line with ";" at top
      if(nc.le.0) go to 20
      if(line(1:1).eq.';') go to 20
      call chcase(maxc,line,0)
c     pick up keywrd
      call strtk1(maxc,line,nc,line1,mc,'=')
      if(nc.le.0) go to 20
      if(mc.le.0) then
         write(*,*) ' error in fmoutil.def keyword.',line
         stop
      endif
      do 40 i=1,MaxDef
      if(line1(1:8).eq.keywrd(i)) then
         if(i.eq.3) then
            call strtoi(maxc,line,nrun)
         elseif(i.ge.7.and.i.le.11) then
c           layer(1)-(5)
            jj=i-6
            layer(jj)=1
            lay(jj)=line
         elseif(i.ge.12.and.i.le.16) then
c           nwf(1)-(5)
            call strint(maxc,line,5,nint,intdat)
            ist=i-12
            do j=1,nint
               jj=ist+j
               nwf(jj)=intdat(j)
            enddo
         elseif(i.ge.21.and.i.le.25) then
c           basid(1)-(5)
            call strint(maxc,line,5,nint,intdat)
            ist=i-21
            do j=1,nint
               jj=ist+j
               idbas(jj)=intdat(j)
            enddo
         elseif(i.eq.35) then
c           memory ... real
            call strtor(maxc,line,memory)
         elseif(i.eq.36) then
c           grid ... real
            call strtor(maxc,line,grids)
         elseif(i.eq.37) then
            call strtoi(maxc,line,ipieda)
         else
c           other positive integer data
            call strint(maxc,line,5,nint,intdat)
            idata(i)=intdat(1)
         endif
      endif
   40 continue
      go to 20
  100 continue
c
      return
      end
cs---------------------------------------------------------------------
      subroutine inpdef(kword,idat,rdat,cdat)
c----------------------------------------------------------------------
c     pick up default data read in from fmoutil.def file
ce---------------------------------------------------------------------
      character*8 kword
      character*256 cdat(*)
      dimension     idat(*)
      real    memory,grids
      integer frgsiz,sscys,gly
      character*256 lay
      common/input1/nnodes,ncpus,nrun,method,nbody,nlayer,layer(5),
     .              nwf(5),imcscf,ncore,nacorb,nacele,idbas(5),
     .              mullk,icube,frgsiz,sscys,gly,idiffs,i2sto,isi6,
     .              multip,memory,grids,ipieda,lay(5)
      parameter (MaxDef=40)
      integer       idata(MaxDef-2)
      equivalence   (idata(1),nnodes)
      character*8   keywrd(MaxDef)
      data          keywrd/'nnodes  ','ncpus   ','nrun    ','method  ',
     .                     'nbody   ','nlayer  ','layer(1)','layer(2)',
     .                     'layer(3)','layer(4)','layer(5)','nwf(1)  ',
     .                     'nwf(2)  ','nwf(3)  ','nwf(4)  ','nwf(5)  ',
     .                     'imcscf  ','ncore   ','nacorb  ','nacele  ',
     .                     'basid(1)','basid(2)','basid(3)','basid(4)',
     .                     'basid(5)','mulliken','cube    ','nfgsiz  ',
     .                     'ifcys   ','ifgly   ','diffsp  ','gmssto  ',
     .                     'gms631  ','multip  ','memory  ','grid    ',
     .                     'ipieda  ','        ','        ','        '/
c
      idat(1)=0
      rdat=0.0
      do 20 i=1,MaxDef
         if(kword.eq.keywrd(i)) go to 40
   20 continue
      write(*,*) ' program error: wrong keywrd ',kword
      stop
   40 continue
      if(i.le.MaxDef-2) then
         idat(1)=idata(i)
      endif
      if(i.eq.35) then
         rdat=memory
      endif
      if(i.eq.36) then
         rdat=grids
      endif
      if(i.eq.37) then
         idat(1)=ipieda
      endif
      if(i.ge.7.and.i.le.11) then
         do j=1,5
            cdat(j)=lay(j)
         enddo
      endif
      if(i.ge.12.and.i.le.16) then
         do j=1,5
            jj=j+11
            idat(j)=idata(jj)
         enddo
      endif
      if(i.ge.21.and.i.le.25) then
         do j=1,5
            jj=j+20
            idat(j)=idata(jj)
         enddo
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine fmoxyz(iout,idiffs,ndiffs)
c----------------------------------------------------------------------
c     print $fmoxyz for GMS
ce---------------------------------------------------------------------
      character elem*2
      parameter (MaxAtm=120000,MaxFrg=50000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*8 frgnam
      common/frgin1/nfrg,ndum4,istfrg(MaxFrg+1),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
c      dimension     ilay(*)
      character*10  label
c      character*10  temp
      data           maxc/10/
c
      key=0
      if(key.eq.0) then
         ndiffs=0
         do 100 i=1,natm
         iantmp=ian(i)
         call elmian(elem,iantmp,1)
         ii=i
         call stri2c(maxc,ii,label,ifig)
         call strsft(maxc,label,-6+ifig)
c         ifg=iatfrg(i)
c         ii=ilay(ifg)
c         call stri2c(maxc,ii,temp,ifig)
c         label=label(1:6)
         if(idiffs.eq.1) then
            call ocoatm(i,iyes)
            if(iyes.eq.0) then
               ndiffs=ndiffs+1
               label=label(1:6)//'.2'
            endif
         endif
         write(iout,2000) label,elem,x(i),y(i),z(i)
 2000    format(1x,a10,2x,a2,3x,3f18.8)
  100    continue
      else
         write(iout,*) ' '
         write(iout,*) ' atom #,frag #,frg,elem and x,y,z coordinates'
         do 120 i=1,natm
         iantmp=ian(i)
         call elmian(elem,iantmp,1)
         ii=iatfrg(i)
         write(iout,2010) i,ii,frgnam(ii),elem,x(i),y(i),z(i)
 2010    format(2x,i5,2x,i3,2x,a8,2x,a2,3x,3f12.4)
  120    continue
      endif
      return
      end
cs---------------------------------------------------------------------
      subroutine ocoatm(iatm,iyes)
c----------------------------------------------------------------------
c     does iatm belong to COO- group ? iyes=0 for yes, iyes=1 for no.
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxFrg=50000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*24 frgnam
      common/frginf/nfrg,nssbnd,nresfg(MaxFrg),iresfg(4,MaxFrg),
     .              ichfrg(MaxFrg),frgnam(MaxFrg)
      dimension     ibdlst(8),ibndo(8)
c
      iyes=1
      ifrg=iatfrg(iatm)
      nrf=nresfg(ifrg)
      iresf=iresfg(1,ifrg)
      iresl=iresfg(nrf,ifrg)
c     does ifrg fragment have ASP, GLU or C-teminus
      do i=iresf,iresl
         if(ichres(i).lt.0) then
            call resid(resnam(i),iresid,0,0)
            if(iresid.ge.1.and.iresid.le.20) then
               ist=istres(i)
               nati=istres(i+1)-ist
               do j=1,nati
                  jj=ist+j-1
                  if(ian(jj).eq.6) then
                     call bndlst(nati,ian(ist),x(ist),y(ist),z(ist),
     .                           j,nbnd,ibdlst,0)
                     if(nbnd.eq.3) then
                         icatm=jj
                         nbndo=0
                         do k=1,nbnd
                            kk=ibdlst(k)+ist-1
                            if(ian(kk).eq.8) then
                               nbndo=nbndo+1
                               ibndo(nbndo)=ibdlst(k)
                            endif
                            if(nbndo.eq.2) then
                                call bndlst(nati,ian(ist),x(ist),
     .                             y(ist),z(ist),ibndo(1),nbd1,ibdlst,0)
                                call bndlst(nati,ian(ist),x(ist),
     .                             y(ist),z(ist),ibndo(2),nbd2,ibdlst,0)
                                if(nbd1+nbd2.eq.2) then
                                   if(iatm.eq.icatm) iyes=0
                                   if(iatm.eq.ibndo(1)+ist-1) iyes=0
                                   if(iatm.eq.ibndo(2)+ist-1) iyes=0
                                endif
                            endif
                         enddo
                     endif
                  endif
               enddo
            endif
         endif
      enddo
c
      return
      end
cs---------------------------------------------------------------------
      subroutine bassto(ian,nl,bas,i2sto)
c----------------------------------------------------------------------
c     the sto-3g basis sets
c     i2sto=1 for GAMESS standard basis functions
c     i2sto=2 for Pople's STO basis functions.
c     Note: Only the basis set of S is defined for 2nd row elements
ce---------------------------------------------------------------------
      character*53 bas(*)
c
      if(ian.eq.16) then
       if(i2sto.eq.1) then
          nl=1
          bas( 1)='sto 3'
       else
         nl=12
         bas( 1)='s 3                                                  '
         bas( 2)='1  .5331257359E+03   .1543289673E+00                 '
         bas( 3)='2  .9710951830E+02   .5353281423E+00                 '
         bas( 4)='3  .2628162542E+02   .4446345422E+00                 '
         bas( 5)='l 3                                                  '
         bas( 6)='1  .3332975173E+02  -.9996722919E-01  .1559162750E+00'
         bas( 7)='2  .7745117521E+01   .3995128261E+00  .6076837186E+00'
         bas( 8)='3  .2518952599E+01   .7001154689E+00  .3919573931E+00'
         bas( 9)='l 3                                                  '
         bas(10)='1  .2029194274E+01  -.2196203690E+00  .1058760429E-01'
         bas(11)='2  .5661400518E+00   .2255954336E+00  .5951670053E+00'
         bas(12)='3  .2215833792E+00   .9003984260E+00  .4620010120E+00'
       endif
      elseif(ian.le.18) then
         nl=1
         bas( 1)='sto 3'
      else
         nl=3
         bas( 1)=' The basis set is not defined in FMOutil. GAMESS may '
         bas( 2)='have it. If not, you will search the following site, '
         bas( 3)='http://www.emsl.pnl.gov/docs/data.html               '
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine bas321(ian,nl,bas)
c----------------------------------------------------------------------
c     the 3-21g basis sets. H-Ar
ce---------------------------------------------------------------------
      character*53 bas(*)
      if(ian.le.18) then
         nl=1
         bas( 1)='n21 3'
      else
         nl=3
         bas( 1)=' The basis set is not defined in FMOutil. GAMESS may '
         bas( 2)='have it. If not, you will search the following site, '
         bas( 3)='http://www.emsl.pnl.gov/docs/data.html               '
      endif
      return
      end
cs---------------------------------------------------------------------
      subroutine bas631(ian,nl,bas,isi6)
c----------------------------------------------------------------------
c     the 6-31g basis sets. 
c     the basis set of Si in GAMESS is different from the original one.
c     isi6=1 for GAMESS standard basis functions
c     isi6=2 for Pople's basis functions.
ce---------------------------------------------------------------------
      character*53 bas(*)
c
c     Si (ian=14)
      if(ian.eq.14) then
       if(isi6.eq.1) then
          bas( 1)='n31 6'
          nl=1
       else
         nl=20
         bas( 1)='S   6                                                '
         bas( 2)='1  16115.90000   0.1959480000E-02                    '
         bas( 3)='2  2425.580000   0.1492880000E-01                    '
         bas( 4)='3  553.8670000   0.7284780000E-01                    '
         bas( 5)='4  156.3400000   0.2461300000                        '
         bas( 6)='5  50.06830000   0.4859140000                        '
         bas( 7)='6  17.01780000   0.3250020000                        '
         bas( 8)='L   6                                                '
         bas( 9)='1  292.7180000  -0.2780940000E-02  0.4438260000E-02  '
         bas(10)='2  69.87310000  -0.3571460000E-01  0.3266790000E-01  '
         bas(11)='3  22.33630000  -0.1149850000      0.1347210000      '
         bas(12)='4  8.150390000   0.9356340000E-01  0.3286780000      '
         bas(13)='5  3.134580000   0.6030170000      0.4496400000      '
         bas(14)='6  1.225430000   0.4189590000      0.2613720000      '
         bas(15)='L   3                                                '
         bas(16)='1  1.727380000  -0.2446300000     -0.1779510000E-01  '
         bas(17)='2  0.5729220000  0.4315720000E-02  0.2535390000      '
         bas(18)='3  0.2221920000  1.098180000       0.8006690000      '
         bas(19)='L   1                                                '
         bas(20)='1  0.7783690000E-01 1.000000000     1.000000000      '
        endif
      else
       if(ian.le.18) then
         bas( 1)='n31 6'
         nl=1
       else
         nl=3
         bas( 1)=' The basis set is not defined in FMOutil. GAMESS may '
         bas( 2)='have it. If not, you will search the following site, '
         bas( 3)='http://www.emsl.pnl.gov/docs/data.html               '
       endif
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine bs6311(ian,nl,bas)
c----------------------------------------------------------------------
c     the 6-311g basis sets. 
c     GAMESS does not have the 6-311G basis set for 2nd row elements.
c     only the basis set of S is defined in this routine which were
c     obtained from http://www.emsl.pnl.gov/docs/data.html.
ce---------------------------------------------------------------------
      character*53 bas(*)
c
c     S (ian=16)
      if(ian.le.10) then
          bas( 1)='n311 6'
          nl=1
      elseif(ian.eq.16) then
         nl=20
         bas( 1)='S   6                                                '
         bas( 2)='1  16115.90000   0.1959480000E-02                    '
         bas( 3)='2  2425.580000   0.1492880000E-01                    '
         bas( 4)='3  553.8670000   0.7284780000E-01                    '
         bas( 5)='4  156.3400000   0.2461300000                        '
         bas( 6)='5  50.06830000   0.4859140000                        '
         bas( 7)='6  17.01780000   0.3250020000                        '
         bas( 8)='L   6                                                '
         bas( 9)='1  292.7180000  -0.2780940000E-02  0.4438260000E-02  '
         bas(10)='2  69.87310000  -0.3571460000E-01  0.3266790000E-01  '
         bas(11)='3  22.33630000  -0.1149850000      0.1347210000      '
         bas(12)='4  8.150390000   0.9356340000E-01  0.3286780000      '
         bas(13)='5  3.134580000   0.6030170000      0.4496400000      '
         bas(14)='6  1.225430000   0.4189590000      0.2613720000      '
         bas(15)='L   3                                                '
         bas(16)='1  1.727380000  -0.2446300000     -0.1779510000E-01  '
         bas(17)='2  0.5729220000  0.4315720000E-02  0.2535390000      '
         bas(18)='3  0.2221920000  1.098180000       0.8006690000      '
         bas(19)='L   1                                                '
         bas(20)='1  0.7783690000E-01 1.000000000     1.000000000      '
      else
         nl=3
         bas( 1)=' The basis set is not defined in FMOutil. GAMESS may '
         bas( 2)='have it. If not, you will search the following site, '
         bas( 3)='http://www.emsl.pnl.gov/docs/data.html               '
      endif
c
      return
      end
cs---------------------------------------------------------------------
      subroutine tstamp(iout,msgtyp,filnam,ixyz,xyzfil)
c----------------------------------------------------------------------
c     write time stamp
c     note: the "fdate" function used in this routine should be changed
c           depending on compiler.
ce---------------------------------------------------------------------
      character*80 filnam,xyzfil
      character*24 stamp
c
      call fdate(stamp)
c
      if(msgtyp.eq.1) then
         write(iout,2000)
 2000    format('!',71('-'))
         write(iout,2020) stamp
 2020    format('! Created by FMOutil ... ',a24)
         write(iout,2040) filnam
 2040    format('! Input File: ',a60)
         if(ixyz.eq.1) write(iout,5020) xyzfil
         write(iout,2000)
      elseif(msgtyp.eq.2) then
         write(iout,3000)
 3000    format('REMARK',66('-'))
         write(iout,3020) stamp
 3020    format('REMARK Created by FMOutil ... ',a24)
         write(iout,3040) filnam
 3040    format('REMARK Input File: ',a60)
         if(ixyz.eq.1) write(iout,5040) xyzfil
         write(iout,3000)
      else
         write(iout,4000)
 4000    format(72('-'))
         write(iout,4020) stamp
 4020    format(' Created by FMOutil ... ',a24)
         write(iout,4040) filnam
 4040    format(' Input File: ',a60)
         if(ixyz.eq.1) write(iout,5000) xyzfil
         write(iout,4000)
      endif
 5000 format(' The coordinates were replaced with: ',a40)
 5020 format('! The coordinates were replaced with: ',a40)
 5040 format('REMARK The coordinates were replaced with: ',a34)
      return
      end
cs---------------------------------------------------------------------
      subroutine xyzinp(iu,filnam)
c----------------------------------------------------------------------
c     read xyz coordinates and overide /atmxyz/
c     (1) comment card
c     (2) label ian x,y,z (in angstroms)
c         as many lines
ce---------------------------------------------------------------------
      parameter (MaxAtm=120000)
      character*4 atmnam
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*80 filnam
      character*256 temp,temp1,temp2
      character*2 elm
      data maxc/256/
c
c     open file
      open(iu,file=filnam,form='formatted',status='old')
      nat=0
c     skip the first line (a comment)
      read(iu,*)
   20 continue
      read(iu,1000,end=40) temp
 1000 format(a256)
      temp2=temp
      call strsiz(maxc,temp,nc)
      if(nc.le.0) go to 40
      nat=nat+1
      if(nat.gt.natm) then
         go to 900
      endif
c     skip label
      call strtok(maxc,temp,nc,temp1,mc)
c     ian
      call strtok(maxc,temp,nc,temp1,mc)
c     ntype  (i4)        ... 0:integer,1:real,2:character,3:blank.
      call strtyp(maxc,temp1,ntype)
      if(ntype.eq.0) then
         call strtoi(maxc,temp1,jan)
      elseif(ntype.eq.1) then
         call strtor(maxc,temp1,xian)
         jan=(xian+0.0001)
      elseif(ntype.eq.2) then
         call strtoc(maxc,temp1,2,elm)
         call elmian(elm,jan,0)
      else
         go to 910
      endif
c     check jan
      if(jan.ne.ian(nat)) go to 920
c     get x,y and z
      call strtok(maxc,temp,nc,temp1,mc)
      call strtor(maxc,temp1,x(nat))
      call strtok(maxc,temp,nc,temp1,mc)
      call strtor(maxc,temp1,y(nat))
      call strtok(maxc,temp,nc,temp1,mc)
      call strtor(maxc,temp1,z(nat))
c         write(*,*) nat,jan,x(nat),y(nat),z(nat)
      go to 20
   40 continue
c     close file
      close(iu)
      return
c     error exit
  900 call msgout(0,1,'error(xyzinp): number of atoms is larger than nat
     .m.$')
      call msgou0(0,0,' natm=$',natm)
  910 call msgout(0,1,'error(xyzinp): format error in xyz coordinate fil
     .e.$')
      call msgout(0,0,' input:'//temp2(1:nc)//'$')
  920 call msgout(0,1,'error(xyzinp): input atomic number disagrees.$')
      call msgou0(0,1,' nat=$',nat)
      call msgou0(0,1,' original ian=$',ian)
      call msgou0(0,0,' input ian=$',jan)
      end
cs----------------------------------------------------------------------
      subroutine phipsi(iout)
c-----------------------------------------------------------------------
c     print phi and psi
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxMol=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      character*6   resnmi
c
      write(iout,1000)
 1000 format(' Phi, Psi and Omega (degrees)',/,
     .'   phi is the dihedral angle of C(i-1)-N(i)-Ca(i)-C(i),',/,
     .'   psi is the dihedral angle of N(i)-Ca(i)-C(i)-N(i+1),',/,
     .'   omega is the dihedral angle of Ca(i)-C(i)-N(i+1)-Ca(i+1).')
      write(iout,1400)
 1400 format('   #,mol,      phi,        psi,      omega, ires, resnam, 
     .C(i-1)-N(i)-Ca(i)-C(i)-N(i+1)-Ca(i+1)')
c
      kount=0
      do 160 imol=1,nmol
      istm=istmol(imol)
      iedm=istmol(imol+1)-1
      if(iedm-1.lt.istm+1) go to 160
      do 120 ires=istm+1,iedm-1
ccc      ist=istres(ires)
ccc      ied=istres(ires+1)-1
ccc      call resid(resnam(ires),iresid,0,0)
      call resiid(ires,iresid,resnmi)
      if(iresid.ne.0) then
         kount=kount+1
c        assume N-Ca-C'-N(ires+1) sequence. 
c        phi=diheral(C'(ires-1)-N-Ca-C'))
         icm1=istres(ires-1)+2
         in=istres(ires)
         ica=in+1
         ic=in+2
         x1=x(icm1)
         y1=y(icm1)
         z1=z(icm1)
         x2=x(in)
         y2=y(in)
         z2=z(in)
         x3=x(ica)
         y3=y(ica)
         z3=z(ica)
         x4=x(ic)
         y4=y(ic)
         z4=z(ic)
         call dangle(x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4,phi)
c        psi=dihedral(N-Ca-C'-N(ires+1))
         in=istres(ires)
c         ica=in+1
c         ic=in+2
         in1=istres(ires+1)
         x1=x(in)
         y1=y(in)
         z1=z(in)
         x2=x(ica)
         y2=y(ica)
         z2=z(ica)
         x3=x(ic)
         y3=y(ic)
         z3=z(ic)
         x4=x(in1)
         y4=y(in1)
         z4=z(in1)
         call dangle(x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4,psi)
c     omega=Ca-C'-N(ires+1)-Ca(ires+1)
c         in=istres(ires)
c         ica=in+1
c         ic=in+2
         in1=istres(ires+1)
         ica1=in1+1
         x1=x(ica)
         y1=y(ica)
         z1=z(ica)
         x2=x(ic)
         y2=y(ic)
         z2=z(ic)
         x3=x(in1)
         y3=y(in1)
         z3=z(in1)
         x4=x(ica1)
         y4=y(ica1)
         z4=z(ica1)
         call dangle(x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4,omega)
         if(omega.lt.-100.0) omega=360.0+omega
         write(iout,2000) kount,imol,phi,psi,omega,ires,resnmi,icm1,in,
     .                    ica,ic,in1,ica1
 2000    format(i4,i4,2x,f10.4,2x,f10.4,2x,f10.4,i5,2x,a6,6i6)
      endif
  120 continue
  160 continue
c
      return
      end
cs--------------------------------------------------------------------
      subroutine dangle(x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4,angl)
c---------------------------------------------------------------------
c     calculate dihedral angle in degrees of an four-atoms assembly,
c     1-2-3-4.
ce--------------------------------------------------------------------
      a1=x2
      b1=y2
      c1=z2
      x1=x1-a1
      y1=y1-b1
      z1=z1-c1
      x3=x3-a1
      y3=y3-b1
      z3=z3-c1
      x4=x4-a1
      y4=y4-b1
      z4=z4-c1
      a1=y1*z3-y3*z1
      b1=x3*z1-x1*z3
      c1=x1*y3-x3*y1
      a2=y4*z3-y3*z4
      b2=x3*z4-x4*z3
      c2=x4*y3-x3*y4
      ang=(a1*a2+b1*b2+c1*c2)/(sqrt(a1*a1+b1*b1+c1*c1)*
     .     sqrt(a2*a2+b2*b2+c2*c2))
      if(abs(ang).gt.1.0) ang=abs(ang)/ang
      ang=acos(ang)
      angl=57.29578*ang
      sign=x1*a2+y1*b2+z1*c2
      if(sign.lt.0.0) angl=-angl
c
      return
      end
cs----------------------------------------------------------------------
      subroutine carang(iout)
c-----------------------------------------------------------------------
c     print interatomic distances, angles and dihedral angles for 
c     Ca atoms.
ce----------------------------------------------------------------------
      parameter (MaxAtm=120000,MaxRes=50000,MaxMol=50000,MaxFrg=50000)
      character*3 molnam
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
      dimension     ra(3),rb(3)
      character*6   resnmi
      data          todeg/57.29578/
      save          todeg
c
      write(iout,1000)
 1000 format(' Distance, angle and dihedral angle of Ca atoms',/,
     .'       r(i,i+1), ba(i-1,i,i+1), da(i,i+1,i+2,i+3)')
c
      kount=0
      do 160 imol=1,nmol
      istm=istmol(imol)
      iedm=istmol(imol+1)-1
      if(iedm-1.lt.istm+1) go to 160
      do 120 ires=istm,iedm-1
ccc      ist=istres(ires)
ccc      ied=istres(ires+1)-1
ccc      call resid(resnam(ires),iresid,0,0)
      call resiid(ires,iresid,resnmi)
      if(iresid.ne.0) then
         kount=kount+1
c        assume N-Ca-C'-N(ires+1) sequence. 
         ica1=istres(ires)+1
         ica2=istres(ires+1)+1
         x1=x(ica1)
         y1=y(ica1)
         z1=z(ica1)
         x2=x(ica2)
         y2=y(ica2)
         z2=z(ica2)
         if(ires.le.iedm-3) then
            ica3=istres(ires+2)+1
            ica4=istres(ires+3)+1
            x3=x(ica3)
            y3=y(ica3)
            z3=z(ica3)
            x4=x(ica4)
            y4=y(ica4)
            z4=z(ica4)
         elseif(ires.le.iedm-2) then
            ica3=istres(ires+2)+1
            ica4=0
            x3=x(ica3)
            y3=y(ica3)
            z3=z(ica3)
         else
            ica3=0
            ica4=0
         endif
         rij=(x1-x2)**2+(y1-y2)**2+(z1-z2)**2
c        distance ca(i)-ca(i+1)
         rij=sqrt(rij)
         angle=0.0
c        angle ca(i)-ca(i+1)-ca(i+2)
         if(ica3.ne.0) then
            ra(1)=x(ica1)-x(ica2)
            ra(2)=y(ica1)-y(ica2)
            ra(3)=z(ica1)-z(ica2)
            rb(1)=x(ica3)-x(ica2)
            rb(2)=y(ica3)-y(ica2)
            rb(3)=z(ica3)-z(ica2)
            call anglet(ra,rb,teta)
            angle=teta*todeg
         endif
c        dihedral angle ca(i)-ca(i+1)-ca(i+2)-ca(i+3)
         dang=0.0
         if(ica3.gt.0.and.ica4.gt.0) then
            x1=x(ica1)
            y1=y(ica1)
            z1=z(ica1)
            x2=x(ica2)
            y2=y(ica2)
            z2=z(ica2)
            x3=x(ica3)
            y3=y(ica3)
            z3=z(ica3)
            x4=x(ica4)
            y4=y(ica4)
            z4=z(ica4)
            call dangle(x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4,dang)
         endif
         write(iout,2000) kount,imol,rij,angle,dang,ires,resnmi,
     .                    ires+1,ires+2,ires+3
 2000    format(i4,i4,2x,f10.4,2x,f10.4,2x,f10.4,2x,i5,2x,a6,3i6)
      endif
  120 continue
  160 continue
c
      return
      end
