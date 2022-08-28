from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np

# Paste the directory here
primDir = r"G:\Coding\Matlab\Fixed Pack vs. Reconfigurable\Results\23-Jul-2022 15-00-10.056"
resultDir = primDir+"\Plots"

# In main directory where the below excel is located
os.chdir(os.path.dirname(os.path.realpath(__file__)))
dfFiles = pd.read_excel("plotDataInput.xlsx")

if not os.path.isdir(resultDir) :
    os.mkdir(resultDir)

# In primary directory
os.chdir(primDir)

dfIp = pd.read_excel("Simulation Summary.xlsx", sheet_name="Input Variables")
dfOp = pd.read_excel("Simulation Summary.xlsx", sheet_name="OutPut")

# In results directory
os.chdir(resultDir)

def processData(dfIp, dfOp, dfFiles):
    lastGroup = []
    numGrp = 0 # Number of different variations in ratedCapacitySigma and voltageSigma
    for i in range(len(dfIp)):
        row = [dfIp.ID[i], dfIp.RatedCapacitySigma[i], dfIp.VoltageSigma[i]]
        if lastGroup == []:
            lastGroup = row
            numGrp += 1
        
        if row[1:] != lastGroup[1:]:
            lastGroup = row
            numGrp += 1

    resVar = len(np.unique(dfIp.loadRes.to_numpy())) # Number of variations in load resistance
    sameSigRuns = int(len(dfIp)/(resVar*numGrp)) # Number of simulations per group at same sigma for capacity and voltage
    numSimMod = int(len(dfOp)/len(dfIp)) # Number of simulink models ran
    totalRuns = len(dfIp)

    print("Num of variations in load : ", resVar)
    print("Num of groups             : ", numGrp)
    print("Num of runs at same sigma : ", sameSigRuns)
    print("Num of Simulink Models    : ", numSimMod)
    print("Number of simulation runs : ", totalRuns)
    print()

    # print(resVar, numGrp, sameSigRuns, numSimMod, totalRuns)

    outAhArr = []
    outWhArr = []
    for run in range(sameSigRuns * numGrp):
        filedictAh = {} # [[Fixed Model data, Reconfigurable model data]]
        filedictWh = {}
        for file in range(numSimMod):
            ahArr = []
            whArr = []
            for idx in range(resVar):
                index = file + idx*numSimMod + run*numSimMod*resVar
                id = dfOp.ID[index]
                fileName = dfOp["Simulink File"][index]
                ah = dfOp["Ah Delivered"][index]
                wh = dfOp["Wh Delivered"][index]
                ahArr.append(ah)
                whArr.append(wh)
                # print(id, fileName, ah, wh)
                fixIdx = np.where(dfFiles.fixedModel == fileName)[0]  # This is in the form of [5] or []
                rcfgIdx = np.where(dfFiles.reconfModel == fileName)[0]  # This is in the form of [5] or []
                # print(fileName, np.where(dfFiles.fixedModel == fileName)[0], np.where(dfFiles.reconfModel == fileName)[0])

            if np.size(fixIdx) > 0:
                fixIdx = fixIdx[0]

                arr = filedictAh.get(fixIdx, [None, None])
                arr[0] = ahArr
                filedictAh[fixIdx] = arr

                arr1 = filedictWh.get(fixIdx, [None, None])
                arr1[0] = whArr
                filedictWh[fixIdx] = arr1
            else:
                rcfgIdx = rcfgIdx[0]

                arr = filedictAh.get(rcfgIdx, [None, None])
                arr[1] = ahArr
                filedictAh[rcfgIdx] = arr

                arr1 = filedictWh.get(rcfgIdx, [None, None])
                arr1[1] = whArr
                filedictWh[rcfgIdx] = arr1

        outAhArr.append(filedictAh)
        outWhArr.append(filedictWh)
    
    return outAhArr, outWhArr, resVar

def plotFigures(dfIp, j, runDict, mode, run):
    print("Run: ",run, " Mode: ", mode, " F/R: ", j)

    plt.figure(figsize=(16,8)) 
    for i in runDict:
        fixedArr = runDict[i][j]
        # print(i, fixedArr, dfFiles.fixedModel[i])

        if j == 0 :
            label1 = dfFiles.fixedModel[i]
            marker1 = "X"
            plotName = "fixed"
        else:
            label1 = dfFiles.reconfModel[i]
            marker1 = "."
            plotName = "reconf"

        plt.plot(loadResArr, fixedArr, label = label1, marker = marker1)
    plt.legend(loc='lower left', fontsize = 10)
    plt.grid()

    cap = " Capacity: " +  str(dfIp.RatedCapacityMu[run])
    capSigma = " Cap Sigma: " +  str(dfIp.RatedCapacitySigma[run])
    volt = " Nom. Volt: " +  str(dfIp.VoltageMu[run])
    voltSigma = " Volt Sigma: " +  str(dfIp.VoltageSigma[run])

    plt.title(plotName + " " + mode + " plot      Run: " + str(run) + cap + capSigma + volt + voltSigma)
    plt.xlabel("Load Resistance (Ohms) ---->")
    plt.ylabel(mode + "Delivered")
    plt.savefig(plotName+" "+ mode+" "+str(run)+ ".png", dpi = 350)
    plt.close()

outAhArr, outWhArr, resVar = processData(dfIp, dfOp, dfFiles)

# Loading the different resistances values for x axis
loadResArr = dfIp.loadRes[:resVar].to_numpy()

# print(outWhArr)
for j in range(2):
    for mode in ["Ah", "Wh"]:
        if mode == "Ah":
            tempArr = outAhArr
        else:
            tempArr = outWhArr

        for run in range(len(outAhArr)):
            runDict = tempArr[run]
            plotFigures(dfIp, j, runDict, mode, run*resVar)

