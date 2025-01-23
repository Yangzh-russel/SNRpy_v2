# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
# Name:        GPS_file
# Purpose:     This software compute the satellite coordinate positiong and returns
#              the elevation and azimut form the coordinates of the station
#
# Author:      Angel Martin
#
# Created:     14/07/2014
# Final Modification:
#              03/04/2020  
# Copyright:   (c) AngelMartin 2014
# References: 
#               Leick,A. (2004): GPS satellite surveying
#               https://gssc.esa.int/navipedia/index.php/Main_Page
#-------------------------------------------------------------------------------

def nav (fichero_nav,num_lin_cab_eph,hora_epoca,sv,observa_cion_str,matriz_approx_pos):
    import numpy
    import time_lib
    import coor_trans
    
    omegae_dot = 7.2921151467e-5#Earth rotation speed
    GM = 3.986005e14 # Earth's universal gravitational
    v_light=299792458 #Speed of light

    #INPUT DATA
    p2_obs=float(observa_cion_str)
    num_lin_cab=float(num_lin_cab_eph)
    sv=int(sv)
    hora_epoca=float(hora_epoca)
    x_aprox2=[]
    x_aprox2.append(float((matriz_approx_pos[0])[0]))
    x_aprox2.append(float((matriz_approx_pos[1])[0]))
    x_aprox2.append(float((matriz_approx_pos[2])[0]))
    naveg_obs=open(fichero_nav,'r')
    cont=0
    while cont<num_lin_cab:#We jump the header
        linea=naveg_obs.readline()
        linea=linea
        cont +=1

    while True:
        linea2=naveg_obs.readline()
        if not linea2:break

        obs_nav = linea2
        
        ###Search for the navigation information closest to the observation time 
        
        #To acount for observations at the begginig or end of the navigation file
        if hora_epoca==0 or hora_epoca==23:
            hora_top=2.1
        else:
            hora_top=1.1
            
        try:
            hora_ref=int(obs_nav[15:17])+float(obs_nav[17:20])/60+float(obs_nav[20:23])/3600-hora_epoca

            if (int(obs_nav[1:3])==sv) and abs(hora_ref)<hora_top:
                year_eph=int(obs_nav[4:8])
                month_eph=int(obs_nav[9:11])
                day_eph=int(obs_nav[12:14])
                linea3=naveg_obs.readline()
                linea4=naveg_obs.readline()
                linea5=naveg_obs.readline()
                linea6=naveg_obs.readline()
                linea7=naveg_obs.readline()
                
                #Emission time calculation
                jde=time_lib.jd(year_eph,month_eph,day_eph,hora_epoca)
                sec_of_week=time_lib.gps_time(jde)
    
                t_emision=sec_of_week-p2_obs/v_light
                
                toe=(float((linea5[0:23].replace("D","e"))))
                dt_eph=time_lib.check_dt(t_emision-toe)
                t_corr=(float((obs_nav[23:42].replace("D","e"))))+ \
                       (float((obs_nav[42:61].replace("D","e"))))*dt_eph+ \
                       (float((obs_nav[61:80].replace("D","e"))))*dt_eph*dt_eph                 
                dt_eph_corr=time_lib.check_dt((t_emision-t_corr)-toe)
                t_corr=(float((obs_nav[23:42].replace("D","e"))))+ \
                       (float((obs_nav[42:61].replace("D","e"))))*dt_eph_corr+ \
                       (float((obs_nav[61:80].replace("D","e"))))*dt_eph_corr*dt_eph_corr
                tx_GPS=time_lib.check_dt((t_emision-t_corr)-toe) 
                
                semi_eje=(float((linea4[61:80].replace("D","e"))))**2
                mean_motion=numpy.sqrt(GM/(semi_eje**3))+float((linea3[42:61].replace("D","e")))
                mean_anomaly=float((linea3[61:80].replace("D","e")))+mean_motion*tx_GPS
                ano_ecc=mean_anomaly
                ecc=float((linea4[23:42].replace("D","e")))
                for i_ano_ecc in range(10):
                    ano_ecc = mean_anomaly+ecc*numpy.sin(ano_ecc)
                true_ano = numpy.arctan2((numpy.sqrt(1-ecc**2)*numpy.sin(ano_ecc)), \
                          (numpy.cos(ano_ecc)-ecc))
                phi = true_ano+float((linea6[42:61].replace("D","e")))
                
                #parameters readed from navigation file
                cuc=float((linea4[0:23].replace("D","e")))
                cus=float((linea4[42:61].replace("D","e")))
                crc=float((linea6[23:42].replace("D","e")))
                crs=float((linea3[23:42].replace("D","e")))
                i0=float((linea6[0:23].replace("D","e")))
                idot=float((linea7[0:23].replace("D","e")))                
                cic=float((linea5[23:42].replace("D","e")))
                cis=float((linea5[61:80].replace("D","e")))
                omega0=float((linea5[42:61].replace("D","e")))
                omegadot=float((linea6[61:80].replace("D","e")))
                
                ### Satellite coordinates
                du=cuc*numpy.cos(2*phi)+cus*numpy.sin(2*phi)
                dr=crc*numpy.cos(2*phi)+crs*numpy.sin(2*phi)
                di=cic*numpy.cos(2*phi)+cis*numpy.sin(2*phi)
                u_eph=phi+du
                r_eph=semi_eje*(1-ecc*numpy.cos(ano_ecc))+dr
                i_eph=i0+idot*tx_GPS+di
                omega=omega0+(omegadot-omegae_dot)*tx_GPS-omegae_dot*toe
                x1=numpy.cos(u_eph)*r_eph
                y1=numpy.sin(u_eph)*r_eph
                sat_x=x1*numpy.cos(omega)-y1*numpy.cos(i_eph)*numpy.sin(omega)
                sat_y=x1*numpy.sin(omega)+y1*numpy.cos(i_eph)*numpy.cos(omega)
                sat_z=y1*numpy.sin(i_eph)
                ###Rotated satellite coordinates
                omegatau=(p2_obs/v_light)*omegae_dot
                sat_x_rot=sat_x*numpy.cos(omegatau)+sat_y*numpy.sin(omegatau)
                sat_y_rot=-sat_x*numpy.sin(omegatau)+sat_y*numpy.cos(omegatau)
                sat_z_rot=sat_z
        
                (lat_ECEF,lon_ECEF,h_ECEF)=coor_trans.geod(x_aprox2)
                
                (el_sat,azi_sat)=coor_trans.horiz(lat_ECEF,lon_ECEF,h_ECEF,x_aprox2,sat_x_rot,sat_y_rot,sat_z_rot)
                el_sat=(el_sat*180/numpy.pi)
                azi_sat=(azi_sat*180/numpy.pi)
                naveg_obs.close()
                
                return(sat_x_rot,sat_y_rot,sat_z_rot,el_sat,azi_sat)
                                
                break

        except:
            pass

