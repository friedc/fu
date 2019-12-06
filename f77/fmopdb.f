cs---------------------------------------------------------------------
      subroutine pdbmolout(pdbfil,inprot,icprot,iprot,ihprot,ihkeep,
     .                     ihwat,atmnmb0,atmnam0,resnam0,chainnam0,
     .                     resnmb0,cc,an,natm0)
c----------------------------------------------------------------------
c     return pdb atom data with hydrogens attached
c     taken from fmoutil ver 2.2 
ce---------------------------------------------------------------------
      implicit none
      integer     MaxAtm,MaxRes,MaxMol
      parameter(MaxAtm=120000,MaxRes=50000,MaxMol=50000)

      integer     inprot,icprot,iprot,ihprot,ihkeep,ihwat
      character*80 pdbfil,tmpfil
      real*4      cc(MaxAtm,3)
      integer     atmnmb0(MaxAtm),resnmb0(MaxAtm),an(MaxAtm)
      character*4 atmnam0(MaxAtm)
      character*3 resnam0(MaxAtm)
      character*1 chainnam0(MaxAtm)
      integer     natm0
c
      character*3 molnam     
      integer nmol,natmol,istmol,ichmol,nummol
      common/molinf/nmol,natmol,istmol(MaxMol+1),
     .              ichmol(MaxMol),nummol(MaxMol),molnam(MaxMol)
      character*3 resnam
      character*1 chanam
      integer nres,natres,istres,ichres,numres
      common/resinf/nres,natres,istres(MaxRes+1),
     .              ichres(MaxRes),numres(MaxRes),resnam(MaxRes),
     .              chanam(MaxRes)
      character*4 atmnam
      integer natm,ndum1,iatfrg
      common/atminf/natm,ndum1,iatfrg(MaxAtm),atmnam(MaxAtm)
      integer ian
      real*4   x,y,z
      common/atmxyz/ian(MaxAtm),x(MaxAtm),y(MaxAtm),z(MaxAtm)
c
      character*1 chatmp
      character*3 restmp
      character*4 atmtmp
      character*6 labtmp
      integer k,imol,ires,i,ist,ied,istm,iedm,numtmp,iresid
      integer in,iout,ihpos
      integer nresid(20),nrest,nace,nnme,nwater,nonres
      logical yes
c
c     initial setting
      in=1
c     iout will be swited to 2 later
      iout=2
      call defres
      call msgini(iout)
c     open message files
      tmpfil='fmoutil.tmp'
      open (iout,file=tmpfil,form='formatted',status='unknown')
c     open pdb file
      open (in,file=pdbfil,form='formatted',status='old')
c     rewind in
c     read pdb data
      call pdbinp(in,iout,natm0)
      if (natm.le.0) then
          call msgout(0,1,'no atoms in the data.$')
          return
      endif
c
      call prmcbl
      call prmcbr
      call prmvdw
      call prmhbl
c     count each res numbers
      call cnters(nresid,nrest,nace,nnme,nwater,nonres)
c     add h to residues
c     inprot=0
c     icprot=1
c     iprot=1
c     ihprot=0
c     ihkeep=1
      ihpos=0
      call adhpep(iout,inprot,icprot,iprot,ihprot,ihkeep,ihpos)
c     add h to waters moelcules
      if(nwater.gt.0 .and. ihwat.eq.1) call adhwat
c
      chatmp=' '
      k=0
      natm0=natm
      do imol=1,nmol
          istm=istmol(imol)
          iedm=istmol(imol+1)-1
          do ires=istm,iedm
              ist=istres(ires)
              ied=istres(ires+1)-1
              numtmp=numres(ires)
              restmp=resnam(ires)
              chatmp=chanam(ires)
              do i=ist,ied
                  k=k+1
                  atmtmp=atmnam(i)
                  call chcase(4,atmtmp,1)
                  atmnmb0(k)=k
                  atmnam0(k)=atmtmp
                  call chcase(3,restmp,1)
                  resnam0(k)=restmp
                  call chcase(1,chatmp,1)
                  chainnam0(k)=chatmp
                  resnmb0(k)=numtmp
                  cc(k,1)=x(i)
                  cc(k,2)=y(i)
                  cc(k,3)=z(i)
                  an(k)=ian(i)
              enddo
          enddo
          k=k+1
c         insert "TER"
          atmnam0(k)=' TER'
          atmnmb0(k)=k
          resnam0(k)=restmp
          chainnam0(k)=chatmp
          resnmb0(k)=numtmp
          cc(k,1)=0.0
          cc(k,2)=0.0
          cc(k,3)=0.0
          an(k)=-1 
      enddo
c
      close(in)
      close(iout)
     
      return
      end
