c ### module: fortlib
c --- method: find_contact_atoms
      subroutine find_contact_atoms(cc1,cc2,rmin,rmax,natm,iatm,ndim,
     .                              natm1,natm2)
c     calculate distance between atom groups 1 and 2 whose coordinates
c     are in cc1 and cc2, respectively, and
c     return sequence number of atoms in 2 located within threshold 
c     distance from atoms in 1.
      implicit none
      integer ndim,natm1,natm2
      real(8) rmin,rmax
      real(8) cc1(natm1,ndim)
      real(8) cc2(natm2,ndim)
      integer natm
      integer iatm(natm2)
c
      integer itmp(natm2),jtmp(natm2)
      integer i,j
      real(8) rmin2,rmax2,r2,dx,dy,dz

c     write(*,*) ' entered in find_contact_atoms'

      rmin2=rmin*rmin
      rmax2=rmax*rmax
      do j=1,natm2
          jtmp(j)=1
          itmp(j)=0
      enddo
      do j=1,natm2
          do i=1,natm1
              dx=cc1(i,1)-cc2(j,1)
              dy=cc1(i,2)-cc2(j,2)
              dz=cc1(i,3)-cc2(j,3)
              r2=dx*dx+dy*dy+dz*dz
              if (r2.lt.rmax2) then
                  itmp(j)=1
              endif
              if (r2.lt.rmin2) then
                  jtmp(j)=0
              endif
          enddo
      enddo

      do i=1,natm2
          iatm(i)=-1
      enddo
c
      natm=0
      do i=1,natm2
          if (itmp(i).eq.1 .and. jtmp(i).eq.1) then
               natm=natm+1
               iatm(natm)=i-1
          endif
       enddo 
c
       return
       end

c --- method: find_contact_atoms0
      subroutine find_contact_atoms0(cc1,cc2,rmin,rmax,iopt,npair,iatm,
     .                               jatm,rij,ndim,natm1,natm2)
c     calculate distance between atom groups 1 and 2 whose coordinates
c     are in cc1 and cc2, respectively, and
c     return sequence number of atoms in 2 located within threshold 
c     distance from atoms in 1.
      implicit none
      integer ndim,natm1,natm2
      real(8) rmin,rmax
      integer iopt
      real(8) cc1(natm1,ndim)
      real(8) cc2(natm2,ndim)
      integer npair
      integer iatm(natm1*natm2),jatm(natm1*natm2)
      real*8 rij(natm1*natm2)
c
      integer i,j
      real(8) rmin2,rmax2,r2,dx,dy,dz

c     write(*,*) ' entered in find_contact_atoms'

      rmin2=rmin*rmin
      rmax2=rmax*rmax
      npair=0
      do i=1,natm1
          do j=1,natm2
              dx=cc1(i,1)-cc2(j,1)
              dy=cc1(i,2)-cc2(j,2)
              dz=cc1(i,3)-cc2(j,3)
              r2=dx*dx+dy*dy+dz*dz
              if (r2.lt.rmax2 .and. r2.ge.rmin2) then
                  npair=npair+1
                  iatm(npair)=i-1
                  jatm(npair)=j-1
                  rij(npair)=r2
              endif
          enddo
      enddo
c
      if (iopt.eq.0) then
          do j=1,npair
              rij(i)=sqrt(rij(i))
          enddo
       endif 
c
       return
       end

c --- method: find_contact_atoms1
      subroutine find_contact_atoms1(cc,rad,margin,n,iatm,jatm,
     .                               ndim,natm)
c     return contact atom pairis in 'iatm' and 'jatm'. The radii
c     are given in 'rad' and 'margin' is for rad(i)+rad(j)
      implicit none
      integer ndim,natm
      real(8) cc(natm,ndim)
      real(8) rad(natm)
      real(8) margin
      integer n
      integer iatm(10*natm)
      integer jatm(10*natm)
      real(8) vij(ndim), ccj(ndim)
      integer i,j,k,maxpair
      real(8) t2,r2

      maxpair=10*natm
c     write(*,*) ' entered in find_contact_atoms1'

      do i=1,natm
          iatm(i)=-1
          jatm(i)=-1
      enddo
      k=0
      do j=1,natm
          ccj(1)=cc(j,1)
          ccj(2)=cc(j,2)
          ccj(3)=cc(j,3)
          do i=1,j-1
              vij(1)=cc(i,1)-ccj(1)
              vij(2)=cc(i,2)-ccj(2)
              vij(3)=cc(i,3)-ccj(3)
              r2=vij(1)*vij(1)+vij(2)*vij(2)+vij(3)*vij(3)
              t2=margin*(rad(i)+rad(j))**2
              if (r2 < t2) then
                  k=k+1
                  if ( k > maxpair) then
                       write(*,*) 'Program error(find_contact_atoms):
     . insufficient dimension'
                       exit
                  endif
                 iatm(k)=i-1
                 jatm(k)=j-1
              endif
          enddo
      enddo
      n=k
      return
      end

c --- method: find_contact_atoms2
      subroutine find_contact_atoms2(cc,rmin,rmax,iopt,npair,
     .                               iatm,jatm,rij,natm,ndim)
c     return short contact atoms within rmin < r < rmax.
c     usage: npair,iatm,jatm,rij=fuflib.find_contact_atoms2(cc,rmin,rmax,0)
c     the atomic pair in iatm and jatm and diatance in rij.
c     iopt: =0,retrun distance in rij, =1 square of distance
      implicit none
      integer ndim,natm
      real(8) cc(natm,ndim)
      real(8) rmin,rmax
      integer iopt
      integer npair
      integer iatm(10*natm),jatm(10*natm)
      real(8) rij(10*natm)
c
      integer i,j,maxpair
      real(8) rmin2,rmax2,r2,dx,dy,dz
c
c     write(*,*) ' entered in find_contact_atoms2'

      maxpair=10*natm

      rmin2=rmin*rmin
      rmax2=rmax*rmax
      npair=0
      do i=1,natm-1
          do j=i+1,natm
              dx=cc(i,1)-cc(j,1)
              dy=cc(i,2)-cc(j,2)
              dz=cc(i,3)-cc(j,3)
              r2=dx*dx+dy*dy+dz*dz
              if (r2.lt.rmax2 .and. r2.ge.rmin2) then
                  npair=npair+1
                  if (npair .gt. maxpair) then
                       write(*,*) 'napir exceeded maxpair!'
                       exit
                  endif
                  iatm(npair)=i-1
                  jatm(npair)=j-1
                  rij(npair)=r2
              endif
          enddo
      enddo
c     iopt.eq.0, return sqrt(r2)
      if (iopt.eq.0) then
           do i=1,npair
               rij(i)=sqrt(rij(i))
           enddo
       endif
c
       return
       end

c --- method: find_contact_atoms3
      subroutine find_contact_atoms3(x,y,z,cc,rmin,rmax,iopt,
     .                              npnt,iatm,rij,natm,ndim)
c     return atoms locating within threshold ditance from x,y,z point.
c     iopt: =0, return distance, =1, distance**2
      implicit none
      integer ndim,natm
      real(8) x,y,z
      real(8) cc(natm,ndim)
      real(8) rmin,rmax
      integer iopt
      integer npnt
      integer iatm(natm)
      real(8) rij(natm)

      integer i
      real(8) rmin2,rmax2,r2,dx,dy,dz

c     write(*,*) ' entered in find_contact_atoms3'

      rmin2=rmin*rmin 
      rmax2=rmax*rmax
      npnt=0
      do i=1,natm
          dx=x-cc(i,1)
          dy=y-cc(i,2)
          dz=z-cc(i,3)
          r2=dx*dx+dy*dy+dz*dz
          if (r2.lt.rmax2 .and. r2.ge.rmin2) then
              npnt=npnt+1
              iatm(npnt)=i-1
              rij(npnt)=r2
          endif
      enddo
c     iopt.eq.0, return sqrt(r2)
      if (iopt.eq.0) then
           do i=1,npnt
               rij(i)=sqrt(rij(i))
           enddo
       endif
c
       return
       end

c---- method: chisq_cc
      subroutine chisq_cc(cc0,cc1,chisq,natm)
c     compute chi square between two coordinate sets, cc0 and cc1
      implicit none
      real(8)  cc0(natm,3),cc1(natm,3)
      integer  natm

      real(8) chisq
      integer i,j

      chisq=0.0
      do i=1,3
          do j=1,natm
              chisq=chisq+(cc0(j,i)-cc1(j,i))*(cc0(j,i)-cc1(j,i))
          enddo
      enddo
      return
      end

c --- method: dist_cc
      subroutine dist_cc(cc0,cc1,rmin,rmax,na,iatm,r,natm)
c     return atomic distance r between two coordinates, cc0 and cc1
c     distances within rmin and rmax are returned
      real(8) cc0(natm,3),cc1(natm,3)
      real(8) r(natm)
      real(8) rmin,rmax
      integer na,natm
      integer iatm(natm)
 
      integer i,j,k
      real(8) r2,rmin2,rmax2

      rmin2=rmin*rmin
      rmax2=rmax*rmax
      do i=1,natm
          iatm(i)=-1
          r(i)=-1.0
      enddo
      k=0
      do i=1,natm
          r2=0.0
          do j=1,3
              r2=r2+(cc0(i,j)-cc1(i,j))**2
          enddo
          if (r2 .gt. rmin2 .and. r2 .lt. rmax2) then
              k=k+1
              iatm(k)=i
              r(k)=sqrt(r2)
          endif
      enddo
      na=k

      return
      end

c --- method: get_atom_at_raspos
      subroutine get_atom_at_raspos(x,y,atmseq,rasterx,rastery,iatm,
     .                              nsiz)
c     find sequence number of atom at raster position (x,y) 
      implicit none
      integer nsiz
      real(8) x,y
      integer atmseq(nsiz)
      real(8) rasterx(nsiz)
      real(8) rastery(nsiz)
      integer iatm
      integer i

c     write(*,*) ' entered in get_atom_at_raspos'

      iatm=-1
      do i=1,nsiz
          if (abs(x-rasterx(i)) < 5 .and. abs(y-rastery(i)) < 5) then
              iatm=atmseq(i) 
              exit
          endif
      enddo
      return
      end

c --- potential function for flatten molecule
      subroutine flatten_func(cc,ibnd,jbnd,rbnd,ifix,ccfix,
     .                       fb,fnb1,fnb2,fz,fix,
     .                       e,natm,ndim,nbnd,nfix)
      implicit none
      real*8 cc(natm,ndim),rbnd(nbnd),ccfix(nfix,ndim)
      integer ibnd(nbnd),jbnd(nbnd),ifix(nfix)
      real*8 fb,fnb1,fnb2,fz,fix
      integer ndim,natm,nbnd,nfix
      real*8 e
c
      integer i,j,ii,jj
      real*8 dx,dy,dz,zi,dr,rij,rij0,rij2,rij4
c
c     write(*,*) ' entered in flatten_func'

      e=0.0
c     fix atom potential; harmomic constraint at a positon
      do i=1,nfix
          ii=ifix(i)
          if (ii .le. 0) exit
          dx=cc(ii,1)-ccfix(i,1)
          dy=cc(ii,2)-ccfix(i,2)
          dz=cc(ii,3)-ccfix(i,3)
          e=e+fix*(dx*dx+dy*dy+dz*dz)
      enddo
c     non-bond term ... fnb1/r**4 fnb2/r**2 and two-d projection
c     potential fz*z**2
      do i=1,natm
          zi=cc(i,3)
          e=e+fz*zi*zi
      enddo
      do i=1,natm-1
          do j=i+1,natm
              dx=cc(j,1)-cc(i,1)
              dy=cc(j,2)-cc(i,2)
              dz=cc(j,3)-cc(i,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij4=rij2*rij2
              e=e+fnb1/rij4
              e=e+fnb2/rij2
          enddo
      enddo
c     bond term ... fb*(r-r0)**2
      do i=1,nbnd
          ii=ibnd(i)
          jj=jbnd(i)
          rij0=rbnd(i)
          dx=cc(ii,1)-cc(jj,1)
          dy=cc(ii,2)-cc(jj,2)
          dz=cc(ii,3)-cc(jj,3)
          rij2=dx*dx+dy*dy+dz*dz
          rij=sqrt(rij2)
          dr=rij-rij0 
          e=e+fb*dr*dr
          rij4=rij2*rij2
c         remove contribution of bonds to non-bond term
          e=e-fnb1/rij4
          e=e-fnb2/rij2
      enddo

      return
      end

c --- gradient function for 2d-projection of molecule
      subroutine flatten_func_grad(cc,ibnd,jbnd,rbnd,ifix,ccfix,
     .                         fb,fnb1,fnb2,fz,fix,e,de,
     .                         natm,ndim,nbnd,nfix)
      implicit none
      real*8   cc(natm,ndim),rbnd(nbnd),ccfix(nfix,ndim)
      integer  ibnd(nbnd),jbnd(nbnd),ifix(nfix)
      real*8   fb,fnb1,fnb2,fz,fix
      integer  ndim,natm,nbnd,nfix
      real*8   e,de(natm,ndim)
c
      integer i,j,ii,jj
      real*8 dx,dy,dz,zi,dr,rij,rij0,rij2,rij4,gx,gy,gz,fc,fc2,fc4
c
c     write(*,*) ' entered in flattten_func_grad'

      e=0.0
      do i=1,natm
          de(i,1)=0.0
          de(i,2)=0.0
          de(i,3)=0.0
      enddo
c     fix atom potential
      fc=2.0*fix
      do i=1,nfix
          ii=ifix(i)
          if (ii .le. 0) exit
          dx=cc(ii,1)-ccfix(i,1)
          dy=cc(ii,2)-ccfix(i,2)
          dz=cc(ii,3)-ccfix(i,3)
          e=e+fix*(dx*dx+dy*dy+dz*dz)
          de(ii,1)=de(ii,1)+fc*dx
          de(ii,2)=de(ii,2)+fc*dy
          de(ii,3)=de(ii,3)+fc*dz
      enddo
c     non-bond term ... fnb1/r**4 fnb2/r**2 and two-d projection 
c     potential fz*z**2
      do i=1,natm
          zi=cc(i,3)
          e=e+fz*zi*zi
          gz=2.0*fz*zi
          de(i,3)=de(i,3)+gz
      enddo
      do i=1,natm-1
          do j=i+1,natm
              dx=cc(i,1)-cc(j,1)
              dy=cc(i,2)-cc(j,2)
              dz=cc(i,3)-cc(j,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij=sqrt(rij2)
              rij4=rij2*rij2
              e=e+fnb1/rij4
              e=e+fnb2/rij2
              fc4=-4.0*fnb1/(rij4*rij2)
              fc2=-2.0*fnb2/rij4
              fc=fc2+fc4
              gx=fc*dx
              gy=fc*dy
              gz=fc*dz
              de(i,1)=de(i,1)+gx
              de(i,2)=de(i,2)+gy
              de(i,3)=de(i,3)+gz
              de(j,1)=de(j,1)-gx
              de(j,2)=de(j,2)-gy
              de(j,3)=de(j,3)-gz
          enddo
      enddo
c     bond term ... fb*(r-r0)**2
      do i=1,nbnd
          ii=ibnd(i)
          jj=jbnd(i)
          rij0=rbnd(i)
          dx=cc(ii,1)-cc(jj,1)
          dy=cc(ii,2)-cc(jj,2)
          dz=cc(ii,3)-cc(jj,3)
          rij2=dx*dx+dy*dy+dz*dz
          rij=sqrt(rij2)
          dr=rij-rij0 
          e=e+fb*dr*dr
          fc=2.0*fb*dr/rij
          gx=fc*dx
          gy=fc*dy
          gz=fc*dz
          de(ii,1)=de(ii,1)+gx
          de(ii,2)=de(ii,2)+gy
          de(ii,3)=de(ii,3)+gz
          de(jj,1)=de(jj,1)-gx
          de(jj,2)=de(jj,2)-gy
          de(jj,3)=de(jj,3)-gz
c         remove contribution of bonds to non-bond term
          rij4=rij2*rij2
          e=e-fnb1/rij4
          e=e-fnb2/rij2
          fc4=-4.0*fnb1/(rij4*rij2)
          fc2=-2.0*fnb2/rij4
          fc=fc2+fc4
          gx=fc*dx
          gy=fc*dy
          gz=fc*dz
          de(ii,1)=de(ii,1)-gx
          de(ii,2)=de(ii,2)-gy
          de(ii,3)=de(ii,3)-gz
          de(jj,1)=de(jj,1)+gx
          de(jj,2)=de(jj,2)+gy
          de(jj,3)=de(jj,3)+gz
      enddo

      return
      end
c --- function for Hb hydrogen position optimization
      subroutine hb_func(cc,q,ibnd,jbnd,rbnd,ifix,ccfix,
     .                        fb,fx,e,natm,ndim,nfix,nbnd)
      implicit none
      real*8   cc(natm,ndim),rbnd(nbnd),ccfix(nfix,ndim)
      real*8   q(natm)
      integer  ibnd(nbnd),jbnd(nbnd),ifix(nfix)
      real*8   fb,fx
      integer  ndim,natm,nbnd,nfix
      real*8   e
c
      integer i,j,ii,jj
      real*8 dx,dy,dz,zi,dr,rij,rij0,rij2,rij4,gx,gy,gz,fc,fc2,fc4,qu
c
      qu=505.4
c
      e=0.0
c     fix atom potential
      do i=1,nfix
          ii=ifix(i)+1
          if (ii .le. 0) exit
          dx=cc(ii,1)-ccfix(i,1)
          dy=cc(ii,2)-ccfix(i,2)
          dz=cc(ii,3)-ccfix(i,3)
          e=e+fx*(dx*dx+dy*dy+dz*dz)
      enddo
c     subtract charge interactions between fixed atoms
      do i=1,nfix-1
          ii=ifix(i)+1
          do j=i+1,nfix
              jj=ifix(j)+1
              dx=cc(ii,1)-cc(jj,1)
              dy=cc(ii,2)-cc(jj,2)
              dz=cc(ii,3)-cc(jj,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij=sqrt(rij2)
              e=e-qu*q(ii)*q(jj)/rij
          enddo
      enddo
c     charge-charge interactions 
      do i=1,natm-1
          do j=i+1,natm
              dx=cc(i,1)-cc(j,1)
              dy=cc(i,2)-cc(j,2)
              dz=cc(i,3)-cc(j,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij=sqrt(rij2)
              fc=qu*q(i)*q(j)
              e=e+fc/rij
          enddo
      enddo
c     bond term ... fb*(r-r0)**2
      do i=1,nbnd
          ii=ibnd(i)+1
          jj=jbnd(i)+1
          rij0=rbnd(i)
          dx=cc(ii,1)-cc(jj,1)
          dy=cc(ii,2)-cc(jj,2)
          dz=cc(ii,3)-cc(jj,3)
          rij2=dx*dx+dy*dy+dz*dz
          rij=sqrt(rij2)
          dr=rij-rij0 
          e=e+fb*dr*dr
c         subtract contribution of bonds to cgarhe-charge int
          fc=qu*q(ii)*q(jj)
          e=e-fc/rij
      enddo

      return
      end

c --- gradient function for Hb hydrogen position optimization
      subroutine hb_func_grad(cc,q,ibnd,jbnd,rbnd,ifix,ccfix,
     .                        fb,fx,e,de,natm,ndim,nfix,nbnd)
      implicit none
      real*8   cc(natm,ndim),rbnd(nbnd),ccfix(nfix,ndim)
      real*8   q(natm)
      integer  ibnd(nbnd),jbnd(nbnd),ifix(nfix)
      real*8   fb,fx
      integer  ndim,natm,nbnd,nfix
      real*8   e,de(natm,ndim)
c
      integer i,j,ii,jj
      real*8 dx,dy,dz,zi,dr,rij,rij0,rij2,rij4,gx,gy,gz,fc,fc2,fc4,qu
c
      qu=505.4
c
      e=0.0
      do i=1,natm
          de(i,1)=0.0
          de(i,2)=0.0
          de(i,3)=0.0
      enddo
c     fix atom potential
      fc=2.0*fx
      do i=1,nfix
          ii=ifix(i)+1
          if (ii .le. 0) exit
          dx=cc(ii,1)-ccfix(i,1)
          dy=cc(ii,2)-ccfix(i,2)
          dz=cc(ii,3)-ccfix(i,3)
          e=e+fx*(dx*dx+dy*dy+dz*dz)
          de(ii,1)=de(ii,1)+fc*dx
          de(ii,2)=de(ii,2)+fc*dy
          de(ii,3)=de(ii,3)+fc*dz
      enddo
c     subtract charge interactions between fixed atoms
      do i=1,nfix-1
          ii=ifix(i)+1
          do j=i+1,nfix
              jj=ifix(j)+1
              dx=cc(ii,1)-cc(jj,1)
              dy=cc(ii,2)-cc(jj,2)
              dz=cc(ii,3)-cc(jj,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij=sqrt(rij2)
              fc=qu*q(ii)*q(jj)
              e=e-fc/rij
              fc=-1.0*fc/(rij2*rij)
              gx=fc*dx
              gy=fc*dy
              gz=fc*dz
              de(ii,1)=de(ii,1)-gx
              de(ii,2)=de(ii,2)-gy
              de(ii,3)=de(ii,3)-gz
              de(jj,1)=de(jj,1)+gx
              de(jj,2)=de(jj,2)+gy
              de(jj,3)=de(jj,3)+gz
          enddo
      enddo
c     charge-charge interactions
      do i=1,natm-1
          do j=i+1,natm
              dx=cc(i,1)-cc(j,1)
              dy=cc(i,2)-cc(j,2)
              dz=cc(i,3)-cc(j,3)
              rij2=dx*dx+dy*dy+dz*dz
              rij=sqrt(rij2)
              fc=qu*q(i)*q(j)
              e=e+fc/rij
              fc=-1.0*fc/(rij2*rij)
              gx=fc*dx
              gy=fc*dy
              gz=fc*dz
              de(i,1)=de(i,1)+gx
              de(i,2)=de(i,2)+gy
              de(i,3)=de(i,3)+gz
              de(j,1)=de(j,1)-gx
              de(j,2)=de(j,2)-gy
              de(j,3)=de(j,3)-gz
          enddo
      enddo
c     bond term ... fb*(r-r0)**2
      do i=1,nbnd
          ii=ibnd(i)+1
          jj=jbnd(i)+1
          rij0=rbnd(i)
          dx=cc(ii,1)-cc(jj,1)
          dy=cc(ii,2)-cc(jj,2)
          dz=cc(ii,3)-cc(jj,3)
          rij2=dx*dx+dy*dy+dz*dz
          rij=sqrt(rij2)
          dr=rij-rij0 
          e=e+fb*dr*dr
          fc=2.0*fb*dr/rij
          gx=fc*dx
          gy=fc*dy
          gz=fc*dz
          de(ii,1)=de(ii,1)+gx
          de(ii,2)=de(ii,2)+gy
          de(ii,3)=de(ii,3)+gz
          de(jj,1)=de(jj,1)-gx
          de(jj,2)=de(jj,2)-gy
          de(jj,3)=de(jj,3)-gz
c         subtract contribution of bonds to cgarhe-charge int
          fc=qu*q(ii)*q(jj)
          e=e-fc/rij
          fc=-1.0*fc/(rij2*rij)
          gx=fc*dx
          gy=fc*dy
          gz=fc*dz
          de(ii,1)=de(ii,1)-gx
          de(ii,2)=de(ii,2)-gy
          de(ii,3)=de(ii,3)-gz
          de(jj,1)=de(jj,1)+gx
          de(jj,2)=de(jj,2)+gy
          de(jj,3)=de(jj,3)+gz
      enddo

      return
      end
