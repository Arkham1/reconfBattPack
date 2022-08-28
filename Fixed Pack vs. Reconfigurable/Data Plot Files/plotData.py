from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np
from alive_progress import alive_bar

def getData(primDir):
    # Paste the directory here
    # primDir = r"G:\Coding\Matlab\Fixed Pack vs. Reconfigurable\Results\23-Jul-2022 15-00-10.056"
    resultDir = primDir+"\Plots"

    # In main directory where the below excel is located
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # dfFiles = pd.read_excel("plotDataInput.xlsx", sheet_name= "Sheet1")
    dfModule = pd.read_excel("plotDataInput.xlsx", sheet_name= "module")

    if not os.path.isdir(resultDir) :
        os.mkdir(resultDir)

    # In primary directory
    os.chdir(primDir)

    dfIp = pd.read_excel("Simulation Summary.xlsx", sheet_name="Input Variables")
    dfOp = pd.read_excel("Simulation Summary.xlsx", sheet_name="OutPut")

    # Taking in first four columns
    dfOp = dfOp.iloc[:,0:4]
    # In results directory
    os.chdir(resultDir)
    return dfIp, dfOp, dfModule

def processData(dfIp, dfOp):

    # dfSigma is a dataframe with unique sigma value pairs of voltage and capacity sigma, axis = 1 means side by side concatenation
    dfSigma = pd.concat([dfIp.RatedCapacitySigma, dfIp.VoltageSigma], axis = 1).drop_duplicates() 

    # loadResval is an array that contains all the unique load resistances
    loadResval = dfIp.loadRes.unique()
    runsWithLoadVar = int(len(dfIp)/len(loadResval)) # Also = sameSigmaRuns * len(dfSigma)
    sameSigmaRuns = int(len(dfIp)/(len(dfSigma) * len(loadResval)))
    simFileNum = len(dfOp)//len(dfIp) # Number of total simulink files

    dfOpSort = dfOp.sort_values(["Simulink File", "ID"]) # ID is given second preference in sorting
    # print(dfOpSort[40:60])
    simFileOrder = dfOpSort["Simulink File"].unique() # Order of simulink files in dfOpSort
    
    fileDfAhArr = [] # fileDfAhArr is array od df_temp(s) for each simulink file in the order they appear in dfOpSort
    fileDfWhArr = [] # fileDfWhArr is array od df_temp(s) for each simulink file in the order they appear in dfOpSort

    for fNo in range(simFileNum):
        # df_temp by the end of the for loop will have the shape (len(loadResval), runsWithLoadVar)
        df_temp1 = pd.DataFrame()
        df_temp2 = pd.DataFrame()
        for i in range(runsWithLoadVar):
            dfRes = dfOpSort["Ah Delivered"]
            dfWh = dfOpSort["Wh Delivered"]

            fromIdx = len(loadResval)*i + fNo*len(dfIp)
            toIdx = len(loadResval)*(i+1) + fNo*len(dfIp)

            df_temp1[i] = np.array(dfRes[fromIdx : toIdx])
            df_temp2[i] = np.array(dfWh[fromIdx : toIdx])

        fileDfAhArr.append(df_temp1)
        fileDfWhArr.append(df_temp2)
    
    return fileDfAhArr, fileDfWhArr, loadResval, simFileOrder, sameSigmaRuns, dfSigma
    
def plotData_Load(dfAhArr, dfWhArr, dfIp, loadResval, simFileOrder, sameSigmaRuns, dfModule): # Here the load resistance variation is the x axis
    
    print("Working in plotData_Load")
    colLen = len(dfIp) // len(loadResval)
    temp = [dfAhArr, dfWhArr]

    with alive_bar(colLen * len(temp)) as bar:
        temp = [dfAhArr, dfWhArr]
        names = ["Ah", "Wh"]
        lineStyleArr = ["solid", "--", "-.", ":"]
        markerArr = ['*', '.', '+']

        for i in range(len(temp)): # i = 0 -> Ah and i = 1 -> Wh
            dfArr = temp[i]
            name = names[i]

            for j in range(colLen):
                
                # print("Working on " + str(i*colLen + j + 1) + " of " + str(len(temp) * colLen) + " plotData_Load")

                ipRow = j*len(loadResval)
                fig = plt.figure(figsize=(16,8)) 
                # fig, axs = plt.subplots(1, 2, figsize=(20, 8))

                capSD = dfIp.loc[ipRow].RatedCapacitySigma
                volSD = dfIp.loc[ipRow].VoltageSigma
                fig.suptitle("Performance on " + name + " Delivered --- Capacity SD : " + str(capSD) + " Ah, Voltage SD : " + str(volSD) + " V --- Iteration " +  str((j%sameSigmaRuns) + 1) + " of " + str(sameSigmaRuns) + " at this SD value pair", fontsize=16)
                
                ax1 = fig.add_subplot(1, 2, 1)
                ax2 = fig.add_subplot(1, 2, 2)

                max_ylim = 0
                min_ylim = 100000

                fixed_f = 0
                reconf_f = 0

                for fNo in range(len(dfArr)):

                    tokens = simFileOrder[fNo].split("_")
                    
                    if len(tokens) == 2:
                        modName = tokens[1] # Ex: Fixed_Module5
                    else:
                        modName = tokens[1] + "_" +  tokens[2] # Ex: Fixed_Module5_Cross
                    
                    modName = str(dfModule[dfModule.ModuleName == modName].configuration.to_numpy()[0])
                    
                    max_ylim = max(max_ylim, max(dfArr[fNo][j]))
                    min_ylim = min(min_ylim, min(dfArr[fNo][j]))

                    if simFileOrder[fNo].startswith("Fixed"):
                        ax1.plot(loadResval, dfArr[fNo][j], label = modName, marker = markerArr[fixed_f//10], linestyle = lineStyleArr[fixed_f//10]) # Because after 10 plots the colours repeat
                        fixed_f += 1
                    else:
                        ax2.plot(loadResval, dfArr[fNo][j], label = modName, marker = markerArr[reconf_f//10], linestyle = lineStyleArr[reconf_f//10])# Because after 10 plots the colours repeat
                        reconf_f += 1

                max_ylim *= 1.001
                min_ylim *= 0.999

                ax1.set_ylim( [min_ylim, max_ylim] ) # align axes
                ax2.set_ylim( [min_ylim, max_ylim] ) # align axes
                # ax2.set_yticks() # set ticks to be empty (no ticks, no tick-labels)

                ax1.title.set_text('Fixed Battery Pack')   
                ax2.title.set_text('Reconfigurable Battery Pack')    
                ax1.set_ylabel(name + " Delivered -- >")

                ax1.legend(loc='best', fontsize = 8)
                ax2.legend(loc='best', fontsize = 8)
                ax1.set_xlabel("Load Resistance -- >")
                ax2.set_xlabel("Load Resistance -- >")
                
                ax2.grid()
                ax1.grid()

                fig.tight_layout()
                plt.savefig("plot " + name + " " + str(j) + ".png", dpi = 350, bbox_inches='tight')
                plt.close(fig = fig)
                bar()
                          
def plotData_Model(dfAhArr, dfWhArr, loadResval, simFileOrder, sameSigmaRuns, dfModule, dfSigma, noStd):
    
    print("Working in plotData_Model")

    # Initial check of mid splitting of fixed and reconfigurable models

    moduleArr = [] # Only one module array is needed as both splits are sorted so same modules occur at a specific index

    midIndex = len(simFileOrder)//2 
    for i in range(midIndex):
        fixed_name = simFileOrder[i]
        reconf_name = simFileOrder[i + midIndex]

        fixed_tokens = fixed_name.split("_")
        reconf_tokens = reconf_name.split("_")
        
        if fixed_tokens[0] != "Fixed" or reconf_tokens[0] != "Reconfigurable":
            raise Exception("Incorrect mid point : Model Error")
        
        if len(fixed_tokens) == 2:
            fixed_module = fixed_tokens[1] # Ex: Fixed_Module5
        else:
            fixed_module = fixed_tokens[1] + "_" +  fixed_tokens[2] # Ex: Fixed_Module5_Cross

        if len(reconf_tokens) == 2:
            reconf_module = reconf_tokens[1] # Ex: Fixed_Module5
        else:
            reconf_module = reconf_tokens[1] + "_" +  reconf_tokens[2] # Ex: Fixed_Module5_Cross
        
        if fixed_module != reconf_module:
            raise Exception("Module Mismatch : Either incorrect mid point or name sort incorrect")

        moduleArr.append(fixed_module)

    # Initial check completed, Mid split correct

    temp = [dfAhArr, dfWhArr]
    names = ["Ah", "Wh"]

    with alive_bar( len(temp) * midIndex * len(dfSigma) ) as bar:
        for m in range(len(temp)):
            dfArr = temp[m] # dfArr is an array of dataFrames of all simulink models
            name = names[m]

            fixed_dfArr = dfArr[ : midIndex]
            reconf_dfArr = dfArr[midIndex : ]

            for sdPair in range(len(dfSigma)):

                for fNo in range(midIndex):
                    f_meanArr = []
                    r_meanArr = []
                    f_stdArr = []
                    r_stdArr = []

                    f_dfFile = fixed_dfArr[fNo]
                    r_dfFile = reconf_dfArr[fNo]

                    max_ylim = 0
                    min_ylim = 100000

                    modName = moduleArr[fNo]

                    modName = str(dfModule[dfModule.ModuleName == modName].configuration.to_numpy()[0])

                    for i in range(len(f_dfFile)):
                        sameSigmaArr = f_dfFile.iloc[i, sdPair*sameSigmaRuns : (sdPair+1)*sameSigmaRuns]
                        f_meanArr.append(np.mean(sameSigmaArr))
                        f_stdArr.append(np.std(sameSigmaArr))
                    
                    for i in range(len(r_dfFile)):
                        sameSigmaArr = r_dfFile.iloc[i, sdPair*sameSigmaRuns : (sdPair+1)*sameSigmaRuns]
                        r_meanArr.append(np.mean(sameSigmaArr))
                        r_stdArr.append(np.std(sameSigmaArr))

                    fig, (f_ax, r_ax) = plt.subplots(1,2, figsize=(12,6))

                    for i in range(sameSigmaRuns): # Plotting all the runs of fixed model
                        idx = i + sdPair*sameSigmaRuns

                        max_ylim = max(max_ylim, max(f_dfFile[idx]))
                        min_ylim = min(min_ylim, min(f_dfFile[idx]))

                        if i == sameSigmaRuns - 1:
                            f_ax.plot(loadResval, f_dfFile[idx], label = str(sameSigmaRuns) + " Runs", color = "lightskyblue", linestyle = "--")
                        else:
                            f_ax.plot(loadResval, f_dfFile[idx], color = "lightskyblue", linestyle = "--")
                    
                    for i in range(sameSigmaRuns): # Plotting all the runs of reconfigurable model
                        idx = i + sdPair*sameSigmaRuns

                        max_ylim = max(max_ylim, max(r_dfFile[idx]))
                        min_ylim = min(min_ylim, min(r_dfFile[idx]))
                        
                        if i == sameSigmaRuns - 1:
                            r_ax.plot(loadResval, r_dfFile[idx], label = str(sameSigmaRuns) + " Runs", color = "lightskyblue", linestyle = "--")
                        else:
                            r_ax.plot(loadResval, r_dfFile[idx], color = "lightskyblue", linestyle = "--")

                    f_ax.plot(loadResval, f_meanArr, label = "Mean", color = "r", marker = 'x')
                    r_ax.plot(loadResval, r_meanArr, label = "Mean", color = "r", marker = 'x')

                    colorArr = ['g','m']
                    for i in range(noStd): # Plot upto 2 standard deviations
                        stArr = np.multiply(f_stdArr, i+1)
                        f_ax.plot(loadResval, np.add(f_meanArr, stArr), color = colorArr[i], label = str(i+1) + " standard deviation", marker = '*', alpha = 0.6)
                        f_ax.plot(loadResval, np.subtract(f_meanArr, stArr), color = colorArr[i], marker = '*', alpha = 0.6)
                    
                    for i in range(noStd): # Plot upto 2 standard deviations
                        stArr = np.multiply(r_stdArr, i+1)
                        r_ax.plot(loadResval, np.add(r_meanArr, stArr), color = colorArr[i], label = str(i+1) + " standard deviation", marker = '*', alpha = 0.6)
                        r_ax.plot(loadResval, np.subtract(r_meanArr, stArr), color = colorArr[i], marker = '*', alpha = 0.6)

                    f_ax.title.set_text('Fixed Battery Pack')   
                    r_ax.title.set_text('Reconfigurable Battery Pack')    
                    f_ax.set_ylabel(name + " Delivered -- >")

                    f_ax.legend(loc='best', fontsize = 8)
                    r_ax.legend(loc='best', fontsize = 8)
                    f_ax.set_xlabel("Load Resistance -- >")
                    r_ax.set_xlabel("Load Resistance -- >")

                    max_ylim *= 1.001
                    min_ylim *= 0.999

                    f_ax.set_ylim( [min_ylim, max_ylim] ) # align axes
                    r_ax.set_ylim( [min_ylim, max_ylim] ) # align axes

                    fig.suptitle(modName + " " + name + " -- Capacity SD : " + str(dfSigma.RatedCapacitySigma.iloc[sdPair]) + " Voltage SD : " + str(dfSigma.VoltageSigma.iloc[sdPair]))
                    # print(f"Model: {modName}")
                    # print("Fixed Mean:")
                    # print(f_meanArr)
                    # print("Reconf Mean:")
                    # print(r_meanArr)
                    # print()

                    r_ax.grid()
                    f_ax.grid()

                    fig.tight_layout()
                    plt.savefig("Model plot " + name + " " + str(sdPair) + str(fNo) + ".png", dpi = 350, bbox_inches='tight')
                    plt.close(fig = fig)
                    bar()

def main():
    noStd = 1 # Keep 1 or 2 (No of standard deviations to be plotted)
    dfIp, dfOp, dfModule = getData(r"G:\Coding\Matlab\Fixed Pack vs. Reconfigurable\Models and Results - Discharge Only\Results\20 Sim Runs")
    dfAhArr, dfWhArr,loadResval, simFileOrder, sameSigmaRuns, dfSigma = processData(dfIp, dfOp)
    plotData_Load(dfAhArr, dfWhArr, dfIp, loadResval, simFileOrder, sameSigmaRuns, dfModule)
    plotData_Model(dfAhArr, dfWhArr, loadResval, simFileOrder, sameSigmaRuns, dfModule, dfSigma, noStd)

main()
