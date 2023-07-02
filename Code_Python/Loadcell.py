import data_acquisition as daq


doit = False
if doit == True:
    arduino = daq.serial_mma_data_stream("COM9", 57600,16384,177)
    while i<300:


        data = arduino.get_next_loadcell()
        if(data is not None):
            (loadcell_raw,loadcell_timeVal,val3,bool) = data 
            if bool:
    #    print(rot_pos,";",timeVal,";",''.join(format(x, '02x') for x in databyt))
                print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:", ''.join(format(x, '02x') for x in val3))


        data = arduino.get_next_loadcell()
        if(data is not None):
            (loadcell_raw,loadcell_timeVal,val3,bool) = data 
            if bool:
    #    print(rot_pos,";",timeVal,";",''.join(format(x, '02x') for x in databyt))
                print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:", ''.join(format(x, '02x') for x in val3))


            else:
                loadcell_raw_ls.append(loadcell_raw)
                loadcell_timeVal_ls.append(loadcell_timeVal)
                if ((i%100)==0):
                    print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:",  ''.join(format(x, '02x') for x in val3),"i",i)
                print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:",  ''.join(format(x, '02x') for x in val3),"i",i)

                i = loadcell_timeVal/1e6 
       

       
for r in loadcell_raw_ls:
    loadcell_converted_ls.append((r - arduino.offset)*arduino.calibration_factor)
save_data = False
if save_data == True:
    loadcell_csv = pd.DataFrame([loadcell_timeVal_ls,loadcell_converted_ls]).T
    loadcell_csv.to_csv(path + "\\Rotary Encoder\\loadcell_csv_data\\resolution_test_300s.csv", sep= ";")


plot = False
if plot ==True:    
    plt.scatter(np.array(loadcell_timeVal_ls)/1e6,loadcell_raw_ls)

    plt.show()
    plt.cla()
    plt.plot(np.array(loadcell_timeVal_ls)/1e6,loadcell_converted_ls, "b-",label= f"calibration_factor={arduino.calibration_factor},offset={arduino.offset}" )
    plt.legend(loc="best")
    plt.show()
