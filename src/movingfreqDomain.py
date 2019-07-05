from __future__ import division
import numpy as np
from scipy.special import lpmn

class movingfreqDomain():

    '''
    Module containing methods which do various types of frequency domain calcualtions. The methods here include calculation of antenna patters for a single doppler channel, for the three michelson channels or for the AET TDI channels and calculation of noise power spectra for various channel combinations. All methods are calculated for a moving LISA constellation given a particular set of satellite orbits.
    '''
    def lisa_orbits(self, midpoints):
        '''
        Define LISA orbital positions at the midpoint of each time integration segment using analytic MLDC orbits.
        
        Parameters
        -----------
        
        timearray  :  array
            A numpy array of times in seconds.
            
        Returns
        -----------
        rs1, rs2, rs3  :  array
            Arrays of satellite positions for each segment midpoint in timearray. e.g. rs1[1] is [x1,y1,z1] at t=midpoint[1]=timearray[1]+(segment length)/2. 
        '''

        ## Semimajor axis in m
        a = 1.496e11
        ## LISA arm length in m
        L = 2.5e9
        sats = np.array([1,2,3])
        ## Alpha and beta phases allow for changing of initial satellite orbital phases; default initial conditions are alphaphase=betaphase=0.
        betaphase = 0
        alphaphase = 0
        ## Orbital angle alpha(t)
        at = (2*np.pi/31557600)*midpoints + alphaphase
        ## Eccentricity. L-dependent, so needs to be altered for time-varied arm length case.
        e = L/(2*a*np.sqrt(3))
        
        ph = np.zeros(len(midpoints))
        ## Initialize arrays
        beta_n = (2/3)*np.pi*np.array([0,1,2])+betaphase
        x_n = np.array([ph,ph,ph])
        y_n = np.array([ph,ph,ph])
        z_n = np.array([ph,ph,ph])
        
        ## Calculate inclination and positions for each satellite.
        for n in sats:
            x_n[n-1][:] = a*np.cos(at) + a*e*(np.sin(at)*np.cos(at)*np.sin(beta_n[n-1]) - (1+(np.sin(at))**2)*np.cos(beta_n[n-1]))
            y_n[n-1][:] = a*np.sin(at) + a*e*(np.sin(at)*np.cos(at)*np.cos(beta_n[n-1]) - (1+(np.cos(at))**2)*np.sin(beta_n[n-1]))
            z_n[n-1][:] = -np.sqrt(3)*a*e*np.cos(at-beta_n[n-1])
        
        ## Construct position vectors r_n
        rs1 = np.array([x_n[0],y_n[0],z_n[0]])
        rs2 = np.array([x_n[1],y_n[1],z_n[1]])
        rs3 = np.array([x_n[2],y_n[2],z_n[2]])

        return rs1, rs2, rs3
        
        
    def doppler_response(self, f0, theta, phi, midpoints, rs1, rs2, rs3):
        
        '''
        Calculate Antenna pattern/ detector transfer function for a GW originating in the direction of (theta, phi) for the u doppler channel of an orbiting LISA with satellite position vectors rs1, rs2, rs3 at a given time. Return the detector response for + and x polarization. Note that f0 is (pi*L*f)/c and is input as an array
        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        phi theta  :  float
            Sky position values. 
            
        rs1, rs2, rs3  :  array
            Satellite position vectors.
        
        ti  :  float
            timearray index
    

        Returns
        ---------

        Rplus, Rcross   :   float
            Plus and cross antenna Patterns for the given sky direction
        '''
        
        timeindices = np.arange(len(midpoints))
        
        ## Define cos/sin(theta)
        ct = np.cos(theta)
        st = np.sqrt(1-ct**2)
        
        # Initlize arrays for the detector reponse
        Rplus, Rcross = np.zeros((len(timeindices),f0.size), dtype=complex), np.zeros((len(timeindices),f0.size),dtype=complex)

        for ti in timeindices:
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            
            ## Add if calculating v, w:
            ## x3 = r3[0][ti]
            ## y3 = r3[1][ti]
            ## z3 = r3[2][ti]
            
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            ## Calculate arm length for the u arm
            Lu = np.sqrt(np.dot(uvec,uvec))
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            
            Pcontract = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct- \
                              ((z2-z1)/Lu)*st)**2)
            Ccontract = ((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * \
                          (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct- \
                           ((z2-z1)/Lu)*st))
    
            # Calculate the detector response for each frequency
            for ii in range(0, f0.size):
                # Calculate GW transfer function for the michelson channels
                gammaU = 1/2 * (np.sinc(f0[ii]*(1-udir)/np.pi)*np.exp(-1j*f0[ii]*(3+udir)) + \
                                    np.sinc(f0[ii]*(1+udir)/np.pi)*np.exp(-1j*f0[ii]*(1+udir)))
        
        
                ## Michelson Channel Antenna patterns for + pol: Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
        
                Rplus[ti][ii] = Pcontract*gammaU
                
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
        
                Rcross[ti][ii] = Ccontract*gammaU
        
        import pdb
        pdb.set_trace()
        
        np.savetxt('Rplusarray.txt',Rplus)
        np.savetxt('Rcrossarray.txt',Rcross)
        
        return Rplus, Rcross


    def michelson_response(self, f0, theta, phi, midpoints, rs1, rs2, rs3): 

        '''
        Calculate Antenna pattern/ detector transfer function for a GW originating in the direction of (theta, phi) at a given time for the three Michelson channels of an orbiting LISA. Return the detector response for + and x polarization. Note that f0 is (pi*L*f)/c and is input as an array
        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        phi theta  : float
            Sky position values. 
            
        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index
    

        Returns
        ---------

        R1plus, R1cross, R2plus, R2cross, R3plus, R3cross   :   float
            Plus and cross antenna Patterns for the given sky direction for the three channels
        '''
        timeindices = np.arange(len(midpoints))
        ## Define cos/sin(theta)
        ct = np.cos(theta)
        st = np.sqrt(1-ct**2)
        
        for ti in timeindices:
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            x3 = rs3[0][ti]
            y3 = rs3[1][ti]
            z3 = rs3[2][ti]
            
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            vvec = rs3[:,ti] - rs1[:,ti]
            wvec = rs3[:,ti] - rs2[:,ti]
    
            ## Calculate arm lengths
            Lu = np.sqrt(np.dot(uvec,uvec))
            Lv = np.sqrt(np.dot(vvec,vvec))
            Lw = np.sqrt(np.dot(wvec,wvec))
         
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            vdir = ((x3-x1)/Lv)*np.cos(phi)*st + ((y3-y1)/Lv)*np.sin(phi)*st + ((z3-z1)/Lv)*ct
            wdir = ((x3-x2)/Lw)*np.cos(phi)*st + ((y3-y2)/Lw)*np.sin(phi)*st + ((z3-z2)/Lw)*ct
            
            ## Calculate 1/2(u x u):eplus
            Pcontract_u = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)**2)
            Pcontract_v = 1/2*((((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi))**2 - \
                             (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)**2)
            Pcontract_w = 1/2*((((x3-x2)/Lw)*np.sin(phi)-((y3-y2)/Lw)*np.cos(phi))**2 - \
                             (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)**2)
            
            ## Calculate 1/2(u x u):ecross
            Ccontract_u = (((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * \
                            (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)
            
            Ccontract_v = (((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi)) * \
                            (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)
            
            Ccontract_w = (((x3-x2)/Lw)*np.sin(phi)-((x3-x2)/Lw)*np.cos(phi)) * \
                            (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)


            # Calculate the detector response for each frequency
            for ii in range(0, f0.size):
    
                # Calculate GW transfer function for the michelson channels
                gammaU_p    =    1/2 * (np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(3 + udir)) + \
                                        np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(1 + udir)))
                gammaU_m    =    1/2 * (np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(3 - udir)) + \
                                        np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(1 - udir)))
                
                gammaV_p    =    1/2 * (np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + vdir)) + \
                                        np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(1+vdir)))
                gammaV_m    =    1/2 * (np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - vdir)) + \
                                        np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - vdir)))
                
                gammaW_p    =    1/2 * (np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + wdir)) + \
                                        np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 + wdir)))
                gammaW_m    =    1/2 * (np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - wdir)) + \
                                        np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - wdir)))
                ## Michelson Channel Antenna patterns for + pol
                ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
    
                Fplus_u_p   = Pcontract_u*gammaU_p
                Fplus_u_m   = Pcontract_u*gammaU_m
                Fplus_v_p   = Pcontract_v*gammaV_p
                Fplus_v_m   = Pcontract_v*gammaV_m
                Fplus_w_p   = Pcontract_w*gammaW_p
                Fplus_w_m   = Pcontract_w*gammaW_m
    
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
                Fcross_u_p  = Ccontract_u*gammaU_p
                Fcross_u_m  = Ccontract_u*gammaU_m
                Fcross_v_p  = Ccontract_v*gammaV_p
                Fcross_v_m  = Ccontract_v*gammaV_m
                Fcross_w_p  = Ccontract_w*gammaW_p
                Fcross_w_m  = Ccontract_w*gammaW_m
    
    
                ## First Michelson antenna patterns
                ## Calculate Fplus
                R1plus = (Fplus_u_p - Fplus_v_p)
                R2plus = (Fplus_w_p - Fplus_u_m)
                R3plus = (Fplus_v_m - Fplus_w_m)
    
                ## Calculate Fcross
                R1cross = (Fcross_u_p - Fcross_v_p)
                R2cross = (Fcross_w_p - Fcross_u_m)
                R3cross = (Fcross_v_m - Fcross_w_m)
        import pdb
        pdb.set_trace()
        return R1plus, R1cross, R2plus, R2cross, R3plus, R3cross

    def aet_response(self, f0, theta, phi, ti, rs1, rs2, rs3): 



        '''
        Calculate Antenna pattern/ detector transfer function for a GW originating in the direction of (theta, phi) at a given time for the A, E and T TDI channels of an orbiting LISA. Return the detector response for + and x polarization. Note that f0 is (pi*L*f)/c and is input as an array
        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        phi theta  : float
            Sky position values. 
        
        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index

        Returns
        ---------

        RAplus, RAcross, REplus, REcross, RTplus, RTcross   :   float
            Plus and cross antenna Patterns for the given sky direction for the three channels
        '''


        R1plus, R1cross, R2plus, R2cross, R3plus, R3cross  = self.michelson_response(f0, theta, phi, ti, rs1, rs2, rs3)
        

        ## Calculate antenna patterns for the A, E and T channels
        RAplus = (2/3)*np.sin(2*f0)*(2*R1plus - R2plus - R3plus)
        REplus = (2/np.sqrt(3))*np.sin(2*f0)*(R3plus - R2plus)
        RTplus = (1/3)*np.sin(2*f0)*(R1plus + R3plus + R2plus)

        RAcross = (2/3)*np.sin(2*f0)*(2*R1cross - R2cross - R3cross)
        REcross = (2/np.sqrt(3))*np.sin(2*f0)*(R3cross - R2cross)
        RTcross = (1/3)*np.sin(2*f0)*(R1cross + R3cross + R2cross)

        return RAplus, RAcross, REplus, REcross, RTplus, RTcross

    def tdi_isgwb_xyz_response(self, f0, midpoints, rs1, rs2, rs3): 

        '''
        Calcualte the Antenna pattern/ detector transfer function functions to an isotropic SGWB using X, Y and Z TDI channels for an orbiting LISA. Note that since this is the response to an isotropic background, the response function is integrated over sky direction and averaged over polarozation. The angular integral is a linear and rectangular in the cos(theta) and phi space.  Note that f0 is (pi*L*f)/c and is input as an array

        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index

        Returns
        ---------

        R1, R2 and R3   :   float
            Antenna Patterns for the given sky direction for the three channels, integrated over sky direction and averaged over polarization.
        '''

        timeindices = np.arange(len(midpoints))
        
        tt = np.arange(-1, 1, 0.01)
        pp = np.arange(0, 2*np.pi, np.pi/100)

        [ct, phi] = np.meshgrid(tt,pp)
        dct = ct[0, 1] - ct[0,0]
        dphi = phi[1,0] - phi[0,0]
        st = np.sqrt(1-ct**2)
        
        # Initlize arrays for the detector reponse
        R1 = np.zeros((len(timeindices),f0.size))
        R2 = np.zeros((len(timeindices),f0.size))
        R3 = np.zeros((len(timeindices),f0.size))
        
        for ti in timeindices:
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            x3 = rs3[0][ti]
            y3 = rs3[1][ti]
            z3 = rs3[2][ti]
            
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            vvec = rs3[:,ti] - rs1[:,ti]
            wvec = rs3[:,ti] - rs2[:,ti]
    
            ## Calculate arm lengths
            Lu = np.sqrt(np.dot(uvec,uvec))
            Lv = np.sqrt(np.dot(vvec,vvec))
            Lw = np.sqrt(np.dot(wvec,wvec))
         
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            vdir = ((x3-x1)/Lv)*np.cos(phi)*st + ((y3-y1)/Lv)*np.sin(phi)*st + ((z3-z1)/Lv)*ct
            wdir = ((x3-x2)/Lw)*np.cos(phi)*st + ((y3-y2)/Lw)*np.sin(phi)*st + ((z3-z2)/Lw)*ct
            
            ## Calculate 1/2(u x u):eplus
            Pcontract_u = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)**2)
            Pcontract_v = 1/2*((((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi))**2 - \
                             (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)**2)
            Pcontract_w = 1/2*((((x3-x2)/Lw)*np.sin(phi)-((y3-y2)/Lw)*np.cos(phi))**2 - \
                             (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)**2)
            
            ## Calculate 1/2(u x u):ecross
            Ccontract_u = (((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * \
                            (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)
            
            Ccontract_v = (((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi)) * \
                            (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)
            
            Ccontract_w = (((x3-x2)/Lw)*np.sin(phi)-((x3-x2)/Lw)*np.cos(phi)) * \
                            (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)

            # Calculate the detector response for each frequency
            for ii in range(0, f0.size):
    
                # Calculate GW transfer function for the michelson channels
                gammaU_p    =    1/2 * (np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(3 + udir)) + \
                                        np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(1 + udir)))
                gammaU_m    =    1/2 * (np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(3 - udir)) + \
                                        np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(1 - udir)))
                
                gammaV_p    =    1/2 * (np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + vdir)) + \
                                        np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(1+vdir)))
                gammaV_m    =    1/2 * (np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - vdir)) + \
                                        np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - vdir)))
                
                gammaW_p    =    1/2 * (np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + wdir)) + \
                                        np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 + wdir)))
                gammaW_m    =    1/2 * (np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - wdir)) + \
                                        np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - wdir)))
                ## Michelson Channel Antenna patterns for + pol
                ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
    
                Fplus_u_p   = Pcontract_u*gammaU_p
                Fplus_u_m   = Pcontract_u*gammaU_m
                Fplus_v_p   = Pcontract_v*gammaV_p
                Fplus_v_m   = Pcontract_v*gammaV_m
                Fplus_w_p   = Pcontract_w*gammaW_p
                Fplus_w_m   = Pcontract_w*gammaW_m
    
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
                Fcross_u_p  = Ccontract_u*gammaU_p
                Fcross_u_m  = Ccontract_u*gammaU_m
                Fcross_v_p  = Ccontract_v*gammaV_p
                Fcross_v_m  = Ccontract_v*gammaV_m
                Fcross_w_p  = Ccontract_w*gammaW_p
                Fcross_w_m  = Ccontract_w*gammaW_m
    
    
                ## First Michelson antenna patterns
                ## Calculate Fplus
                Fplus1 = (Fplus_u_p - Fplus_v_p)
                Fplus2 = (Fplus_w_p - Fplus_u_m)
                Fplus3 = (Fplus_v_m - Fplus_w_m)
    
                ## Calculate Fcross
                Fcross1 = (Fcross_u_p - Fcross_v_p)
                Fcross2 = (Fcross_w_p - Fcross_u_m)
                Fcross3 = (Fcross_v_m - Fcross_w_m)
    
                ## Calculate antenna patterns for the A, E and T channels -  We are switiching to doppler channel.
                FXplus = 2*np.sin(2*f0[ii])*Fplus1
                FYplus = 2*np.sin(2*f0[ii])*Fplus2
                FZplus = 2*np.sin(2*f0[ii])*Fplus3
    
                FXcross = 2*np.sin(2*f0[ii])*Fcross1
                FYcross = 2*np.sin(2*f0[ii])*Fcross2
                FZcross = 2*np.sin(2*f0[ii])*Fcross3
    
                ## Detector response for the TDI Channels, summed over polarization
                ## and integrated over sky direction
                R1[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FXplus))**2 + (np.absolute(FXcross))**2)
                R2[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FYplus))**2 + (np.absolute(FYcross))**2)
                R3[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FZplus))**2 + (np.absolute(FZcross))**2)


        import pdb
        pdb.set_trace()
        np.savetxt('R1arrayXYZ.txt',R1)
        np.savetxt('R2arrayXYZ.txt',R2)
        np.savetxt('R3arrayXYZ.txt',R3)
        
        return R1, R2, R3

    def tdi_isgwb_response_ab(self, f0, midpoints, rs1, rs2, rs3): 

        '''
        Calcualte the Antenna pattern/ detector transfer function functions to an isotropic SGWB using A, E and T TDI channels. Note that since this is the response to an isotropic background, the response function is integrated over sky direction and averaged over polarization. The angular integral is a linear and rectangular in the cos(theta) and phi space.  Note that f0 is (pi*L*f)/c and is input as an array

        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index    

        Returns
        ---------

        R1, R2 and R3   :   float
            Antenna Patterns for the given sky direction for the three channels, integrated over sky direction and averaged over polarization.
        '''
        import time
        t0 = time.time()
        print('Calculating detector response functions...')
       
        
        timeindices = np.arange(len(midpoints))
        
        tt = np.arange(-1, 1, 0.01)
        pp = np.arange(0, 2*np.pi, np.pi/100)

        [ct, phi] = np.meshgrid(tt,pp)
        dct = ct[0, 1] - ct[0,0]
        dphi = phi[1,0] - phi[0,0]
        st = np.sqrt(1-ct**2)
        
        # Initlize arrays for the detector reponse
        R1 = np.zeros((len(timeindices),f0.size))
        R2 = np.zeros((len(timeindices),f0.size))
        R3 = np.zeros((len(timeindices),f0.size))

        for ti in timeindices:
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            x3 = rs3[0][ti]
            y3 = rs3[1][ti]
            z3 = rs3[2][ti]
            
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            vvec = rs3[:,ti] - rs1[:,ti]
            wvec = rs3[:,ti] - rs2[:,ti]
    
            ## Calculate arm lengths
            Lu = np.sqrt(np.dot(uvec,uvec))
            Lv = np.sqrt(np.dot(vvec,vvec))
            Lw = np.sqrt(np.dot(wvec,wvec))
         
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            vdir = ((x3-x1)/Lv)*np.cos(phi)*st + ((y3-y1)/Lv)*np.sin(phi)*st + ((z3-z1)/Lv)*ct
            wdir = ((x3-x2)/Lw)*np.cos(phi)*st + ((y3-y2)/Lw)*np.sin(phi)*st + ((z3-z2)/Lw)*ct
            
            ## Calculate 1/2(u x u):eplus
            Pcontract_u = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)**2)
            Pcontract_v = 1/2*((((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi))**2 - \
                             (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)**2)
            Pcontract_w = 1/2*((((x3-x2)/Lw)*np.sin(phi)-((y3-y2)/Lw)*np.cos(phi))**2 - \
                             (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)**2)
            
            ## Calculate 1/2(u x u):ecross
            Ccontract_u = (((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * \
                            (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)
            
            Ccontract_v = (((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi)) * \
                            (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)
            
            Ccontract_w = (((x3-x2)/Lw)*np.sin(phi)-((x3-x2)/Lw)*np.cos(phi)) * \
                            (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)


            # Calculate the detector response for each frequency
            for ii in range(0, f0.size):
    
                # Calculate GW transfer function for the michelson channels
                gammaU_p    =    1/2 * (np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(3 + udir)) + \
                                        np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(1 + udir)))
                gammaU_m    =    1/2 * (np.sinc((f0[ii])*(1 + udir)/np.pi)*np.exp(-1j*f0[ii]*(3 - udir)) + \
                                        np.sinc((f0[ii])*(1 - udir)/np.pi)*np.exp(-1j*f0[ii]*(1 - udir)))
                
                gammaV_p    =    1/2 * (np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + vdir)) + \
                                        np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(1+vdir)))
                gammaV_m    =    1/2 * (np.sinc((f0[ii])*(1 + vdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - vdir)) + \
                                        np.sinc((f0[ii])*(1 - vdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - vdir)))
                
                gammaW_p    =    1/2 * (np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 + wdir)) + \
                                        np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 + wdir)))
                gammaW_m    =    1/2 * (np.sinc((f0[ii])*(1 + wdir)/np.pi)*np.exp(-1j*f0[ii]*(3 - wdir)) + \
                                        np.sinc((f0[ii])*(1 - wdir)/np.pi)*np.exp(-1j*f0[ii]*(1 - wdir)))
                ## Michelson Channel Antenna patterns for + pol
                ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
    
                Fplus_u_p   = Pcontract_u*gammaU_p
                Fplus_u_m   = Pcontract_u*gammaU_m
                Fplus_v_p   = Pcontract_v*gammaV_p
                Fplus_v_m   = Pcontract_v*gammaV_m
                Fplus_w_p   = Pcontract_w*gammaW_p
                Fplus_w_m   = Pcontract_w*gammaW_m
    
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
                Fcross_u_p  = Ccontract_u*gammaU_p
                Fcross_u_m  = Ccontract_u*gammaU_m
                Fcross_v_p  = Ccontract_v*gammaV_p
                Fcross_v_m  = Ccontract_v*gammaV_m
                Fcross_w_p  = Ccontract_w*gammaW_p
                Fcross_w_m  = Ccontract_w*gammaW_m
    
    
                ## First Michelson antenna patterns
                ## Calculate Fplus
                Fplus1 = (Fplus_u_p - Fplus_v_p)
                Fplus2 = (Fplus_w_p - Fplus_u_m)
                Fplus3 = (Fplus_v_m - Fplus_w_m)
    
                ## Calculate Fcross
                Fcross1 = (Fcross_u_p - Fcross_v_p)
                Fcross2 = (Fcross_w_p - Fcross_u_m)
                Fcross3 = (Fcross_v_m - Fcross_w_m)
                
    
                ## Calculate antenna patterns for the A, E and T channels -  We are switiching to doppler channel.
                FAplus = (1/3)*np.sin(2*f0[ii])*(2*Fplus1 - Fplus2 - Fplus3)
                FEplus = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fplus3 - Fplus2)
                FTplus = (1/3)*np.sin(2*f0[ii])*(Fplus1 + Fplus3 + Fplus2)
    
                FAcross = (1/3)*np.sin(2*f0[ii])*(2*Fcross1 - Fcross2 - Fcross3)
                FEcross = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fcross3 - Fcross2)
                FTcross = (1/3)*np.sin(2*f0[ii])*(Fcross1 + Fcross3 + Fcross2)
    
                ## Detector response for the TDI Channels, summed over polarization
                ## and integrated over sky direction
                R1[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FAplus))**2 + (np.absolute(FAcross))**2)
                R2[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FEplus))**2 + (np.absolute(FEcross))**2)
                R3[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FTplus))**2 + (np.absolute(FTcross))**2)


        tall = time.time() - t0
        print("Total time elapsed: %f" % tall)
        import pdb
        pdb.set_trace()
        np.savetxt('R1array.txt',R1)
        np.savetxt('R2array.txt',R2)
        np.savetxt('R3array.txt',R3)
        pdb.set_trace()
        return R1, R2, R3


    def tdi_isgwb_response_timed(self, f0, midpoints, rs1, rs2, rs3): 

        '''
        Calcualte the Antenna pattern/ detector transfer function functions to an isotropic SGWB using A, E and T TDI channels. Note that since this is the response to an isotropic background, the response function is integrated over sky direction and averaged over polarization. The angular integral is a linear and rectangular in the cos(theta) and phi space.  Note that f0 is (pi*L*f)/c and is input as an array

        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index    

        Returns
        ---------

        R1, R2 and R3   :   float
            Antenna Patterns for the given sky direction for the three channels, integrated over sky direction and averaged over polarization.
        '''
        import time
        t0 = time.time()
        print('Calculating detector response functions...')
       
        t1 = time.time()
        timeindices = np.arange(len(midpoints))
        
        tt = np.arange(-1, 1, 0.01)
        pp = np.arange(0, 2*np.pi, np.pi/100)

        [ct, phi] = np.meshgrid(tt,pp)
        dct = ct[0, 1] - ct[0,0]
        dphi = phi[1,0] - phi[0,0]
        st = np.sqrt(1-ct**2)
        
        # Initlize arrays for the detector reponse
        R1 = np.zeros((len(timeindices),f0.size))
        R2 = np.zeros((len(timeindices),f0.size))
        R3 = np.zeros((len(timeindices),f0.size))
        initialize = time.time() - t1
        print("Time to initialize: %f" % initialize)
        print(f0.size)
        efficacy = np.zeros((len(timeindices),13))
        #gammatimes = np.zeros(len(timeindices)*f0.size)
        altgammatimes = np.zeros(len(timeindices)*f0.size)
        ahaha = 0
        import pdb
        pdb.set_trace()
        for ti in timeindices:
            t2 = time.time()
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            x3 = rs3[0][ti]
            y3 = rs3[1][ti]
            z3 = rs3[2][ti]
            xyzs = time.time()-t2
            #print("Time to allocate xyz: %f" % xyzs)
            t3 = time.time()
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            vvec = rs3[:,ti] - rs1[:,ti]
            wvec = rs3[:,ti] - rs2[:,ti]
            vecs = time.time()-t3
            #print("Time to calc vecs: %f" % vecs)
            t4 = time.time()
            ## Calculate arm lengths
            Lu = np.sqrt(np.dot(uvec,uvec))
            Lv = np.sqrt(np.dot(vvec,vvec))
            Lw = np.sqrt(np.dot(wvec,wvec))
            arms = time.time() - t4
            #print("Time to calc arms: %f" % arms)
            t5 = time.time()
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            vdir = ((x3-x1)/Lv)*np.cos(phi)*st + ((y3-y1)/Lv)*np.sin(phi)*st + ((z3-z1)/Lv)*ct
            wdir = ((x3-x2)/Lw)*np.cos(phi)*st + ((y3-y2)/Lw)*np.sin(phi)*st + ((z3-z2)/Lw)*ct
            dirs = time.time() - t5
            #print("Time to calc dirs: %f" % dirs)
            t5a = time.time()
            ## Pre-calculate u/v/w-dir additions
            udir1m = 1 - udir
            udir1p = 1 + udir
            udir3p = 3 + udir
            vdir1m = 1 - vdir
            vdir1p = 1 + vdir
            vdir3p = 3 + vdir
            wdir1m = 1 - wdir
            wdir1p = 1 + wdir
            wdir3p = 3 + wdir
            diradd = time.time()-t5a
            t5b = time.time()
            ## Calculate 1/2(u x u):eplus
            Pcontract_u = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)**2)
            Pcontract_v = 1/2*((((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi))**2 - \
                             (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)**2)
            Pcontract_w = 1/2*((((x3-x2)/Lw)*np.sin(phi)-((y3-y2)/Lw)*np.cos(phi))**2 - \
                             (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)**2)
            pc = time.time()-t5b
            t5c = time.time()
            ## Calculate 1/2(u x u):ecross
            Ccontract_u = (((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)
            
            Ccontract_v = (((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi)) * (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)
            
            Ccontract_w = (((x3-x2)/Lw)*np.sin(phi)-((x3-x2)/Lw)*np.cos(phi)) * (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)
            cc = time.time()-t5c
            # Calculate the detector response for each frequency
            #t6 = time.time()
            for ii in range(0, f0.size):
                t6a = time.time()
                # Calculate GW transfer function for the michelson channels
                gammaU    =    1/2 * (np.sinc((1/np.pi)*(f0[ii])*(udir1m))*np.exp(-1j*f0[ii]*(udir3p)) + \
                                 np.sinc((1/np.pi)*(f0[ii])*(udir1p))*np.exp(-1j*f0[ii]*(udir1p)))
    
                gammaV    =    1/2 * (np.sinc((1/np.pi)*(f0[ii])*(vdir1m))*np.exp(-1j*f0[ii]*(vdir3p)) + \
                                 np.sinc((1/np.pi)*(f0[ii])*(vdir1p))*np.exp(-1j*f0[ii]*(vdir1p)))
    
                gammaW    =    1/2 * (np.sinc((1/np.pi)*(f0[ii])*(wdir1m))*np.exp(-1j*f0[ii]*(wdir3p)) + \
                                 np.sinc((1/np.pi)*(f0[ii])*(wdir1p))*np.exp(-1j*f0[ii]*(wdir1p)))
                
                ## Gamma functions w/ expanded sinc(x) = sinx/x
#                gammaU    =    1/2 * (((np.sin((f0[ii])*(udir1m)))/((f0[ii])*(1 - udir)))*np.exp(-1j*f0[ii]*(udir3p)) + \
#                                      ((np.sin((f0[ii])*(udir1p)))/((f0[ii])*(1 + udir)))*np.exp(-1j*f0[ii]*(udir1p)))
#                
#                gammaV    =    1/2 * (((np.sin((f0[ii])*(1 - vdir)))/((f0[ii])*(1 - vdir)))*np.exp(-1j*f0[ii]*(3+vdir)) + \
#                                      ((np.sin((f0[ii])*(1 + vdir)))/((f0[ii])*(1 + vdir)))*np.exp(-1j*f0[ii]*(1+vdir)))
#                
#                gammaW    =    1/2 * (((np.sin((f0[ii])*(1 - wdir)))/((f0[ii])*(1 - wdir)))*np.exp(-1j*f0[ii]*(3+wdir)) + \
#                                      ((np.sin((f0[ii])*(1 + wdir)))/((f0[ii])*(1 + wdir)))*np.exp(-1j*f0[ii]*(1+wdir)))
                
                #gammas = time.time() - t6
                altgammas = time.time() - t6a
                #print("Time to calc gammas: %f" % gammas)
                t7 = time.time()
                ## Michelson Channel Antenna patterns for + pol
                ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
    
                Fplus_u   = Pcontract_u*gammaU
                
                Fplus_v   = Pcontract_v*gammaV
    
                Fplus_w   = Pcontract_w*gammaW
    
                plus = time.time() - t7
                #print("Time to calc plus: %f" % plus)
                t8 = time.time()
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
                Fcross_u  = Ccontract_u*gammaU
                Fcross_v  = Ccontract_v*gammaV
                Fcross_w  = Ccontract_w*gammaW
                cross = time.time() - t8
                #print("Time to calc cross: %f" % cross)
                t9 = time.time()
    
                ## First Michelson antenna patterns
                ## Calculate Fplus
                Fplus1 = (Fplus_u - Fplus_v)
                Fplus2 = (Fplus_w - Fplus_u)
                Fplus3 = (Fplus_v - Fplus_w)
    
                ## Calculate Fcross
                Fcross1 = (Fcross_u - Fcross_v)
                Fcross2 = (Fcross_w - Fcross_u)
                Fcross3 = (Fcross_v - Fcross_w)
                t123 = time.time() - t9
                #print("Time to calc 123s: %f" % t123)
                t10 = time.time()
                ## Calculate antenna patterns for the A, E and T channels -  We are switiching to doppler channel.
                FAplus = (1/3)*np.sin(2*f0[ii])*(2*Fplus1 - Fplus2 - Fplus3)
                FEplus = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fplus3 - Fplus2)
                FTplus = (1/3)*np.sin(2*f0[ii])*(Fplus1 + Fplus3 + Fplus2)
    
                FAcross = (1/3)*np.sin(2*f0[ii])*(2*Fcross1 - Fcross2 - Fcross3)
                FEcross = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fcross3 - Fcross2)
                FTcross = (1/3)*np.sin(2*f0[ii])*(Fcross1 + Fcross3 + Fcross2)
                
                aet = time.time() - t10
                #print("Time to calc aet: %f" % aet)
                t11 = time.time()
                ## Detector response for the TDI Channels, summed over polarization
                ## and integrated over sky direction
                R1[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FAplus))**2 + (np.absolute(FAcross))**2)
                R2[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FEplus))**2 + (np.absolute(FEcross))**2)
                R3[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FTplus))**2 + (np.absolute(FTcross))**2)
                Rs = time.time() - t11
                #print("Time to calc Rs: %f" % Rs)
                #gammatimes[ahaha] = gammas
                altgammatimes[ahaha] = altgammas
                ahaha = ahaha + 1
                
                if ii == f0.size - 1:
                    counts = np.array([xyzs, vecs, arms, dirs, altgammas, plus, cross, t123, aet, Rs, diradd, pc, cc])
                    efficacy[ti,:] = counts

        tall = time.time() - t0
        print("Total time elapsed: %f" % tall)
        np.savetxt('EfficacyOutput6.txt',efficacy)
        #np.savetxt('GammatimesOutput3.txt',gammatimes)
        np.savetxt('AltGammatimesOutput3.txt',altgammatimes)
        import pdb
        pdb.set_trace()
        np.savetxt('R1array.txt',R1)
        np.savetxt('R2array.txt',R2)
        np.savetxt('R3array.txt',R3)
        
        return R1, R2, R3
    
    def tdi_isgwb_response(self, f0, midpoints, rs1, rs2, rs3): 

        '''
        Calcualte the Antenna pattern/ detector transfer function functions to an isotropic SGWB using A, E and T TDI channels. Note that since this is the response to an isotropic background, the response function is integrated over sky direction and averaged over polarization. The angular integral is a linear and rectangular in the cos(theta) and phi space.  Note that f0 is (pi*L*f)/c and is input as an array

        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

        rs1, rs2, rs3  :  array
            Satellite position vectors.
            
        ti  :  float
            timearray index    

        Returns
        ---------

        R1, R2 and R3   :   float
            Antenna Patterns for the given sky direction for the three channels, integrated over sky direction and averaged over polarization.
        '''
        
        print('Calculating detector response functions...')
       
        
        timeindices = np.arange(len(midpoints))
        
        tt = np.arange(-1, 1, 0.01)
        pp = np.arange(0, 2*np.pi, np.pi/100)

        [ct, phi] = np.meshgrid(tt,pp)
        dct = ct[0, 1] - ct[0,0]
        dphi = phi[1,0] - phi[0,0]
        st = np.sqrt(1-ct**2)
        
        # Initlize arrays for the detector reponse
        R1 = np.zeros((len(timeindices),f0.size))
        R2 = np.zeros((len(timeindices),f0.size))
        R3 = np.zeros((len(timeindices),f0.size))
 
        import pdb
        pdb.set_trace()
        
        for ti in timeindices:
            ## Define x/y/z for each satellite at time given by timearray[ti]
            x1 = rs1[0][ti]
            y1 = rs1[1][ti]
            z1 = rs1[2][ti]
            x2 = rs2[0][ti]
            y2 = rs2[1][ti]
            z2 = rs2[2][ti]
            x3 = rs3[0][ti]
            y3 = rs3[1][ti]
            z3 = rs3[2][ti]
            
            ## Define vector u at time timearray[ti]
            uvec = rs2[:,ti] - rs1[:,ti]
            vvec = rs3[:,ti] - rs1[:,ti]
            wvec = rs3[:,ti] - rs2[:,ti]
    
            ## Calculate arm lengths
            Lu = np.sqrt(np.dot(uvec,uvec))
            Lv = np.sqrt(np.dot(vvec,vvec))
            Lw = np.sqrt(np.dot(wvec,wvec))
         
            ## udir is just u-hat.omega, where u-hat is the u unit vector and omega is the unit vector in the sky direction of the GW signal
            udir = ((x2-x1)/Lu)*np.cos(phi)*st + ((y2-y1)/Lu)*np.sin(phi)*st + ((z2-z1)/Lu)*ct
            vdir = ((x3-x1)/Lv)*np.cos(phi)*st + ((y3-y1)/Lv)*np.sin(phi)*st + ((z3-z1)/Lv)*ct
            wdir = ((x3-x2)/Lw)*np.cos(phi)*st + ((y3-y2)/Lw)*np.sin(phi)*st + ((z3-z2)/Lw)*ct
    

    
            # Calculate the detector response for each frequency
            for ii in range(0, f0.size):
    
                # Calculate GW transfer function for the michelson channels
                gammaU    =    1/2 * (np.sinc((f0[ii])*(1 - udir))*np.exp(-1j*f0[ii]*(3+udir)) + \
                                 np.sinc((f0[ii])*(1 + udir))*np.exp(-1j*f0[ii]*(1+udir)))
    
                gammaV    =    1/2 * (np.sinc((f0[ii])*(1 - vdir))*np.exp(-1j*f0[ii]*(3+vdir)) + \
                                 np.sinc((f0[ii])*(1 + vdir))*np.exp(-1j*f0[ii]*(1+vdir)))
    
                gammaW    =    1/2 * (np.sinc((f0[ii])*(1 - wdir))*np.exp(-1j*f0[ii]*(3+wdir)) + \
                                 np.sinc((f0[ii])*(1 + wdir))*np.exp(-1j*f0[ii]*(1+wdir)))
    
                ## Michelson Channel Antenna patterns for + pol
                ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
    
                Fplus_u   = 1/2*((((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi))**2 - \
                             (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st)**2)*gammaU
    
                Fplus_v   = 1/2*((((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi))**2 - \
                             (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st)**2)*gammaV
    
                Fplus_w   = 1/2*((((x3-x2)/Lw)*np.sin(phi)-((y3-y2)/Lw)*np.cos(phi))**2 - \
                             (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st)**2)*gammaW
    
    
                ## Michelson Channel Antenna patterns for x pol
                ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
                Fcross_u  = (((x2-x1)/Lu)*np.sin(phi)-((y2-y1)/Lu)*np.cos(phi)) * (((x2-x1)/Lu)*np.cos(phi)*ct+((y2-y1)/Lu)*np.sin(phi)*ct-((z2-z1)/Lu)*st) * gammaU
                Fcross_v  = (((x3-x1)/Lv)*np.sin(phi)-((y3-y1)/Lv)*np.cos(phi)) * (((x3-x1)/Lv)*np.cos(phi)*ct+((y3-y1)/Lv)*np.sin(phi)*ct-((z3-z1)/Lv)*st) * gammaV
                Fcross_w  = (((x3-x2)/Lw)*np.sin(phi)-((x3-x2)/Lw)*np.cos(phi)) * (((x3-x2)/Lw)*np.cos(phi)*ct+((y3-y2)/Lw)*np.sin(phi)*ct-((z3-z2)/Lw)*st) * gammaW
    
    
                ## First Michelson antenna patterns
                ## Calculate Fplus
                Fplus1 = (Fplus_u - Fplus_v)
                Fplus2 = (Fplus_w - Fplus_u)
                Fplus3 = (Fplus_v - Fplus_w)
    
                ## Calculate Fcross
                Fcross1 = (Fcross_u - Fcross_v)
                Fcross2 = (Fcross_w - Fcross_u)
                Fcross3 = (Fcross_v - Fcross_w)
    
                ## Calculate antenna patterns for the A, E and T channels -  We are switiching to doppler channel.
                FAplus = (1/3)*np.sin(2*f0[ii])*(2*Fplus1 - Fplus2 - Fplus3)
                FEplus = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fplus3 - Fplus2)
                FTplus = (1/3)*np.sin(2*f0[ii])*(Fplus1 + Fplus3 + Fplus2)
    
                FAcross = (1/3)*np.sin(2*f0[ii])*(2*Fcross1 - Fcross2 - Fcross3)
                FEcross = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fcross3 - Fcross2)
                FTcross = (1/3)*np.sin(2*f0[ii])*(Fcross1 + Fcross3 + Fcross2)
    
                ## Detector response for the TDI Channels, summed over polarization
                ## and integrated over sky direction
                R1[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FAplus))**2 + (np.absolute(FAcross))**2)
                R2[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FEplus))**2 + (np.absolute(FEcross))**2)
                R3[ti][ii] = dct*dphi/(4*np.pi)*np.sum((np.absolute(FTplus))**2 + (np.absolute(FTcross))**2)



        np.savetxt('R1array.txt',R1)
        np.savetxt('R2array.txt',R2)
        np.savetxt('R3array.txt',R3)
        
        return R1, R2, R3

    def tdi_aniso_sph_sgwb_response(self, f0): 

        '''
        Calculate the Antenna pattern/ detector transfer function functions to acSGWB using A, E and T TDI channels, and using a spherical harmonic decomposition. Note that the response function is integrated over sky direction with the appropriate legandre polynomial, and averaged over polarozation. Finally note that the spherical harmonic coeffcients correspond to strain sky distribution, while the legandre polynomials describe the power sky. The angular integral is a linear and rectangular in the cos(theta) and phi space.  Note that f0 is (pi*L*f)/c and is input as an array

        

        Parameters
        -----------

        f0   : float
            A numpy array of scaled frequencies (see above for def)

    

        Returns
        ---------

        R1, R2 and R3   :   float
            Antenna Patterns for the given sky direction for the three channels, integrated over sky direction and averaged over polarization. The arrays are 2-d, one direction corresponds to frequency and the other to the l coeffcient. 
        '''

        
        tt = np.arange(-1, 1, 0.02)
        pp = np.arange(0, 2*np.pi, np.pi/100)

        [ct, phi] = np.meshgrid(tt,pp)
        dct = ct[0, 1] - ct[0,0]
        dphi = phi[1,0] - phi[0,0]

        ## udir is just u.r, where r is the directional vector
        udir = np.sqrt(1-ct**2) * np.sin(phi + np.pi/6)
        vdir = np.sqrt(1-ct**2) * np.sin(phi - np.pi/6)
        wdir = vdir - udir

        # Initlize arrays for the detector reponse
        R1 = np.zeros((f0.size, self.params['lmax'] +1))
        R2 = np.zeros((f0.size, self.params['lmax'] +1))
        R3 = np.zeros((f0.size, self.params['lmax'] +1))

        ## initalize array for plms
        plms = np.zeros((tt.size, self.params['lmax']+1, self.params['lmax'] +1 ))


        ## Get associated legandre polynomials.
        for ii in range(tt.size):
            plms[ii, :, :], _ = lpmn(self.params['lmax'], self.params['lmax'], tt[ii]) 

        ## It is the squares of the polynomials which are relevent. 
        plms = plms**2
        # Calculate the detector response for each frequency
        for ii in range(0, f0.size):

            # Calculate GW transfer function for the michelson channels
            gammaU    =    1/2 * (np.sinc((f0[ii])*(1-udir))*np.exp(-1j*f0[ii]*(3+udir)) + \
                             np.sinc((f0[ii])*(1+udir))*np.exp(-1j*f0[ii]*(1+udir)))

            gammaV    =    1/2 * (np.sinc((f0[ii])*(1-vdir))*np.exp(-1j*f0[ii]*(3+vdir)) + \
                             np.sinc((f0[ii])*(1+vdir))*np.exp(-1j*f0[ii]*(1+vdir)))

            gammaW    =    1/2 * (np.sinc((f0[ii])*(1-wdir))*np.exp(-1j*f0[ii]*(3+wdir)) + \
                             np.sinc((f0[ii])*(1+wdir))*np.exp(-1j*f0[ii]*(1+wdir)))

            ## Michelson Channel Antenna patterns for + pol
            ##  Fplus_u = 1/2(u x u)Gamma(udir, f):eplus
            Fplus_u   = 1/2*(1/4*(1-ct**2) + 1/2*(ct**2)*(np.cos(phi))**2 - np.sqrt(3/16)*np.sin(2*phi)*(1+ct**2) + \
                            0.5*((np.cos(phi))**2 - ct**2))*gammaU

            Fplus_v   = 1/2*(1/4*(1-ct**2) + 1/2*(ct**2)*(np.cos(phi))**2 + np.sqrt(3/16)*np.sin(2*phi)*(1+ct**2)+ \
                         0.5*((np.cos(phi))**2 - ct**2))*gammaV

            Fplus_w   = 1/2*(1 - (1+ct**2)*(np.cos(phi))**2)*gammaW


            ## Michelson Channel Antenna patterns for x pol
            ##  Fcross_u = 1/2(u x u)Gamma(udir, f):ecross
            Fcross_u  = - np.sqrt(1-ct**2)/2 * (np.sin(2*phi + np.pi/3))*gammaU
            Fcross_v  = - np.sqrt(1-ct**2)/2 * (np.sin(2*phi - np.pi/3))*gammaV
            Fcross_w  = 1/2*ct*np.sin(2*phi)*gammaW


            ## First Michelson antenna patterns
            ## Calculate Fplus
            Fplus1 = (Fplus_u - Fplus_v)
            Fplus2 = (Fplus_w - Fplus_u)
            Fplus3 = (Fplus_v - Fplus_w)

            ## Calculate Fcross
            Fcross1 = (Fcross_u - Fcross_v)
            Fcross2 = (Fcross_w - Fcross_u)
            Fcross3 = (Fcross_v - Fcross_w)

            ## Calculate antenna patterns for the A, E and T channels -  We are switiching to doppler channel.
            FAplus = (1/3)*np.sin(2*f0[ii])*(2*Fplus1 - Fplus2 - Fplus3)
            FEplus = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fplus3 - Fplus2)
            FTplus = (1/3)*np.sin(2*f0[ii])*(Fplus1 + Fplus3 + Fplus2)

            FAcross = (1/3)*np.sin(2*f0[ii])*(2*Fcross1 - Fcross2 - Fcross3)
            FEcross = (1/np.sqrt(3))*np.sin(2*f0[ii])*(Fcross3 - Fcross2)
            FTcross = (1/3)*np.sin(2*f0[ii])*(Fcross1 + Fcross3 + Fcross2)

            ## Detector response for the TDI Channels, summed over polarization
            ## and integrated over sky direction
            
            R1[ii, :] = dct*dphi/(4*np.pi)*np.sum(np.tensordot((np.absolute(FAplus))**2 + \
                    (np.absolute(FAcross))**2, plms, axes=1), axis=(0, 1))
            R2[ii, :] = dct*dphi/(4*np.pi)*np.sum(np.tensordot((np.absolute(FEplus))**2 + \
                    (np.absolute(FEcross))**2, plms, axes=1), axis=(0, 1))
            R3[ii, :] = dct*dphi/(4*np.pi)*np.sum(np.tensordot((np.absolute(FTplus))**2 + \
                    (np.absolute(FTcross))**2, plms, axes=1), axis=(0,1))   



        return R1, R2, R3


    def fundamental_noise_spectrum(self, freqs, Np=4e-41, Na=1.44e-48):

        '''
        Creates a frequency array of fundamentla noise estimates for lisa. Currently we consisder only contain only position and acceleration noise sources. The default values are specifications pulled from 2017 Lisa proposal noise estimations.

        Parameters
        -----------

        freqs   : float
            A numpy array of frequencies

        Np (optional) : float
            Position noise value
        
        Na (optional) : float
            Acceleration noise level
    

        Returns
        ---------

        Sp, Sa   :   float
            Frequencies array for position and acceleration noises for each satellite
        ''' 
        
        Sp = Np*(1 + (2e-3/freqs)**4)
        Sa = Na*(1 + 16e-8/freqs**2)*(1 + (freqs/8e-3)**4)*(1.0/(2*np.pi*freqs)**4)

        return Sp, Sa

    def aet_noise_spectrum(self, freqs,f0, Np=4e-41, Na=1.44e-48):

        '''
        Calculates A, E, and T channel noise spectra for a stationary lisa. Following the defintions in
        Adams & Cornish, http://iopscience.iop.org/article/10.1088/0264-9381/18/17/308


        Parameters
        -----------

        freqs   : float
            A numpy array of frequencies

        Np (optional) : float
            Position noise value
        
        Na (optional) : float
            Acceleration noise level
    

        Returns
        ---------

        SAA, SEE, STT   :   float
            Frequencies arrays with the noise PSD for the A, E and T TDI channels


        '''

        # Get Sp and Sa
        Sp, Sa = self.fundamental_noise_spectrum(freqs, Np, Na)


        ## Noise spectra of the TDI Channels
        SAA = (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sp*(np.cos(2*self.f0) + 2) \
            + (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sa*(4*np.cos(2*self.f0) + 2*np.cos(4*self.f0) + 6)


        SEE = (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sp*(2 + np.cos(2*self.f0)) \
            + (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sa*(4 + 4*np.cos(2*self.f0) +  4*(np.cos(2*self.f0))**2 )

        STT = (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sp*(1 - np.cos(2*self.f0)) \
            + (16.0/3.0) * ((np.sin(2*self.f0))**2) * Sa*(2 - 4*np.cos(2*self.f0) + 2*(np.cos(2*self.f0))**2)


        return SAA, SEE, STT


