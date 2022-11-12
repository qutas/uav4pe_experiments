############################### ############################### Libraries ###############################
############################### Author: Piaktipik
import os                               # library to use some system functions
import glob
import shutil                           # Used to get the lastest .txt files from runs
from tqdm import tqdm                   # library to track the progress
import numpy as np                      # Matematics    
import matplotlib.pyplot as plt         # Plots
from collections import Counter         # Used to analyse the actions recorded

#  datetime module
from datetime import datetime as dt
experimentTime = dt.now()
experimentDataTimeStr = experimentTime.strftime("%y-%m-%dT%H-%M-%S")

############################### ############################### Parameters Plot ###############################
############################### Base path 
absolute_path = os.path.dirname(os.path.abspath(__file__))
relative_path = ".."
experimentsBaseFolder = os.path.abspath(os.path.join(absolute_path, relative_path))
print(f'Using path: {experimentsBaseFolder}, as base path folder...')

############################### Input Data Format
inputFileExtension =  ".txt"                   # input file format for console input commands (navLogs to process)
############################### Output Data Format
outputFileResultsExtension = ".csv"             # format of output file for extracted results
globalResultsFileName = "planetExpGlobalResults"

############################### Variables experiments analysis
##### Maps to compare
maps =  [['map-16A'],['map-16AD'],['map-16B'],['map-16BD']]     # needs to be readed from the folders
actionList = ['Stay','Hover','Explore','Inspect','Land']

reprocessAllConfigurations = False
reprocessAllExperimentConf = False
autoExpNumber = True            # Used to load dinamically the number of experiments for each configuration.
plotResults = True
############################### ############################### Functions ###############################
# function to print list values with Mean and STD
def printInfoList(name,lista):
    print (f'{name}: {lista}, Mean: {np.mean(lista)}, Std: {np.std(lista)}')

# Directory verification
def ensure_dir(file):
    try:
        d = os.path.dirname(file)
        if not os.path.exists(d):
            print(f'Creating Path: {file} ... ')
            os.makedirs(d)
            print(f'Path: {file} created.')
    except ValueError:
        # Error log
        print(f'Error ensure_dir: {ValueError}')

# Plot 
def boxplotdata(all_data1,labels,labelPlot,fileName):
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(4, 4))
    plt.subplots_adjust(left=0.20, bottom=0.14, right=0.95, top=0.92, wspace=0.2, hspace=0.29)

    # rectangular box plot
    bplot1 = axes.boxplot(all_data1,
                            vert=True,  # vertical box alignment
                            patch_artist=True,  # fill with color
                            labels=labels)  # will be used to label x-ticks
    axes.set_title(f'Results Configuration {configurationNumber}')

    # fill with colors
    colors = ['lightblue','pink','lightblue','pink','lightblue','pink','lightblue','pink']
    for patch, color in zip(bplot1['boxes'], colors):
        patch.set_facecolor(color)

    # adding horizontal grid lines
    axes.yaxis.grid(True)
    axes.set_xlabel('Maps')
    axes.set_ylabel(labelPlot)
    axes.legend((bplot1['boxes'][0], bplot1['boxes'][1]), ('Success', 'Fail'))

    for tick in axes.get_xticklabels():
        tick.set_rotation(45)
        tick.set_fontsize(7)

    plt.savefig(f'{outputFolder}/{fileName}.pdf')
    plt.close()

# Plot 
def boxplotSuccess(dataTest0,labels,labelPlot,fileName):

    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(4, 4))
    plt.subplots_adjust(left=0.20, bottom=0.14, right=0.95, top=0.92, wspace=0.2, hspace=0.29)

    # rectangular box plot
    bplot1 = axes.bar(labels,dataTest0)
    axes.set_title(f'Results Configuration {configurationNumber}')

    # adding horizontal grid lines
    axes.yaxis.grid(True)
    axes.set_xlabel('Maps')
    axes.set_ylabel(labelPlot)

    for tick in axes.get_xticklabels():
        tick.set_rotation(45)
        tick.set_fontsize(7)

    plt.savefig(f'{outputFolder}/{fileName}.pdf')
    plt.close()

# Prepare Data Plot
def plotData(dataOk,dataFail,labelPlot,fileName):
    labels = ['AS','AF', 'ADS','ADF', 'BS','BF', 'BDS','BDF']
    # Values 1
    testOkMap1 = dataOk[0]
    testFailMap1 = dataFail[0]

    testOkMap2 = dataOk[1]
    testFailMap2 = dataFail[1]

    testOkMap3 = dataOk[2]
    testFailMap3 = dataFail[2]

    testOkMap4 = dataOk[3]
    testFailMap4 = dataFail[3]

    ## Data test 1
    all_data1 = [testOkMap1,testFailMap1,testOkMap2,testFailMap2,testOkMap3,testFailMap3,testOkMap4,testFailMap4]

    boxplotdata(all_data1,labels,labelPlot,fileName)

# Prepare succes rates data plot
def plotSuccess(results,labelPlot,fileName):
    labels = ['A','AD','B','BD']
    
    # Values 1
    testOkMap1 = results[0]

    testOkMap2 = results[1]

    testOkMap3 = results[2]

    testOkMap4 = results[3]


    ## Data test 1
    all_data1 = [testOkMap1,testOkMap2,testOkMap3,testOkMap4]


    boxplotSuccess(all_data1,labels,labelPlot,fileName)

# Function to scan the expected action values
def decodeActionReceived(receivedAction):
    for action in actionList:
        if receivedAction.startswith(action):
            return action


############################### Autonmatic Experiment Selection tool ###############################
experimentTypes = ["simulation","emulation","real"]

print(f'Select experiment type from: {experimentTypes}')
for number, experimentType in enumerate(experimentTypes):
    print(f'[{number}] -> {experimentType}') 
selection = int(input("Enter selection: \n"))
if selection < 0 or selection > 2:
    print(f'Invalid range... {selection}')
    quit() 
else:
    experimentKind = experimentTypes[selection]

# Experiment type folder:
experimentTypeFolder = f'{experimentsBaseFolder}/data/{experimentKind}'

# Generate global experiment store data
# Load output file
resultsFolder = f'{experimentsBaseFolder}/results/experiments/{experimentKind}'
outputGlobalFile = f'{resultsFolder}/{globalResultsFileName}-{experimentDataTimeStr}{outputFileResultsExtension}'
outputGlobalFileHandler = open(outputGlobalFile, 'w')
# Print header csv file.
outputGlobalFileHandler.write(f'type\tconf\texpFolder\tmap\texpNumber\ttargetFound\texploredArea\ttakeoffsCount\tactionsTotal\tactionsCount\tactionSequence\n')

############# Automatic check for configurations:
listOfConfsExperiments = glob.glob(f'{experimentTypeFolder}/*/', recursive = True) # Get the list of experiments 
lenListConfsExp = len(listOfConfsExperiments)
experimentsConfsNameList = []
configurationNameList = []
############# list and ask configs to process:
if lenListConfsExp > 1:
    if not reprocessAllConfigurations:
        print(f'{lenListConfsExp} Configurations found in {experimentKind} experiments... select one')
    for number, experimentConfsFolder in enumerate(listOfConfsExperiments):
        experimentsConfName  = experimentConfsFolder.split('/')[-2]
        experimentsConfsNameList.append(experimentsConfName)
        print(f'[{number}] -> {experimentsConfName}') 
    if not reprocessAllConfigurations:
        print(f'[-1] -> Proccess All')
        selection = int(input("Enter selection: \n"))
        if selection < -1 or selection > lenListConfsExp:
            print(f'Invalid range... {selection}')
            quit()
        elif (selection == -1):
            configurationNameList = experimentsConfsNameList
            reprocessAllConfigurations = True
            reprocessAllExperimentConf = True
        else:
            configurationNameList.append(experimentsConfsNameList[selection])
    else:
        configurationNameList = experimentsConfsNameList
elif(lenListConfsExp == 1):
    configurationNameList.append(listOfConfsExperiments[0].split('/')[-2])
else:
    print('No experiments found.')
    quit()

############################### ############################### Atomatic Results Processing
############################### Process Configurations:
for configurationName in configurationNameList:
    print(f'Procesing Configuration {configurationName}...')
    configurationNumber = configurationName.split("conf")[-1]

    # Experiment Configruation Result folder:
    configurationFolder = f'{experimentTypeFolder}/{configurationName}'
    ############# Automatic check of experiments to compute for a configuration:
    listOfExperiments = glob.glob(f'{configurationFolder}/*/', recursive = True) # Get the list of experiments 
    lenListExp = len(listOfExperiments)
    experimentResulFolders = []
    experimentsNameList = []
    ############# list and ask experiments to process:
    if lenListExp > 1:
        if not reprocessAllExperimentConf:
            print(f'{lenListExp} Experiments found... pick the one you want to plot...')
        for number, experimentFolder in enumerate(listOfExperiments):
            experimentsName  = experimentFolder.split('/')[-2]
            experimentsNameList.append(experimentsName)
            print(f'[{number}] -> {experimentsName}')
        if not reprocessAllExperimentConf:
            print(f'[-1] -> Proccess All')
            selection = int(input("Enter selection: \n"))
            if selection < -1 or selection > lenListExp:
                print(f'Invalid range... {selection}')
                quit() 
            elif (selection == -1):
                experimentResulFolders = experimentsNameList
                reprocessAllExperimentConf = True
            else:
                experimentResulFolders.append(experimentsNameList[selection])
        else:
            experimentResulFolders = experimentsNameList
    elif(lenListExp == 1):
        experimentResulFolders.append(listOfExperiments[0].split('/')[-2])
    else:
        print('No experiments found.')
        quit()

    ############################### Process experiments:
    for experimentResulFolder in experimentResulFolders:
        print(f'Processing Experiment result: {experimentResulFolder} ....')
        numberRuns = 1
        if(not autoExpNumber):
            numberRuns = int(input("Enter number experiments to read: \n"))                  # Number of Experiments to read

        ############################### Input Data
        inputFolderExperiment =  f'{configurationFolder}/{experimentResulFolder}'
        print(f'Procesing test {inputFolderExperiment}...')

        ############################### Output Data
        ### Create a folder for the test results
        outputFolder = f'{resultsFolder}/{configurationName}/{experimentResulFolder}'       # Output folder

        ### Array to store results metrics for succesfull/fail for each map: number of takeoffAction actions, total actions and total acumulated explored.
        globalTesttakeoffActionSuccess = []
        globalTesttakeoffActionFail = []
        successRate = []
        globalActionsListCount = []

        globalTestActionsSuccess = []
        globalTestActionsFail = []

        globalTestExploredsSuccess = []
        globalTestExploredsFail = []

        ############################### ############################### Run Test ###############################
        for mapSelected in maps:
            #### Output Path files generation
            mapName = mapSelected[0]
            outputFileResults =  f'{mapName}_results'                   # output header of results
            # Create a folder for the mapTestResuls
            outputFolderTestRun = outputFolder + f'/{mapName}/'
            ensure_dir(outputFolderTestRun)
            # Load output file
            outputFile = outputFolderTestRun + outputFileResults + outputFileResultsExtension
            outputFileHandler = open(outputFile, 'w')

            # Detect number of experiments in the mapFolder.
            experimentFilesList = []
            if (autoExpNumber):
                experimentFilesList = sorted(glob.glob(f'{inputFolderExperiment}/{mapName}/*{inputFileExtension}'), key=os.path.getmtime) # Get the list of experiments to process
                numberRuns = len(experimentFilesList)

            ##### Variables to analyse results
            actionsListRecord = []
            # Variables for succefull runs
            takeoffActionSuccess = []
            actionsSuccess = []
            exploredSuccess = []
            sucessVec = []
            # Variables for Unsuccefull runs
            takeoffActionUnsuccess = []
            actionsUnsuccess = []
            exploredUnsuccess = []
            

            ############################### Process results for each Map
            print(f'----------- Map {mapName} selected ----------- ')
            experimentNameMap = f'Configuration {configurationNumber}, {mapName}'

            # Traverse experiments    
            for experiment in tqdm(range(0,numberRuns)):
                ##### load file names of run result
                experimentName =  f'{experimentNameMap}, Run {experiment}'
                
                if experimentKind == "real":
                    # Use real experiment filename
                    experimentFile = experimentFilesList[experiment]
                    inputExprimentFileName = experimentFile.split('/')[-1]
                else:
                    # Build name navlog to fetch and analyse
                    inputExprimentFileName = f'{mapName}_logRun_N{experiment}_{inputFileExtension}'
                    experimentFile = f'{inputFolderExperiment}/{mapName}/{inputExprimentFileName}'


                ############################## Read and Extract data ############################### 
                #### Open saved logs to process
                try:
                    print(f'\nExtracting results {experimentName}')
                    print(f'File: {experimentFile}')
                    inputFileHandler = open(experimentFile,"r")
                except OSError as e:
                    print(f'Results error: {e}')

                #### Values to save for each test
                actionsCounter = 0
                takeoffAction = 0
                exploredPercentage = 0
                sucess = 0
                missionCompleted = 0    # Used to stop actions counter.
                actionsRecord = []

                # reading each line from original 
                print(f'Analysing {inputExprimentFileName}...')
                for line in inputFileHandler.readlines(): 
                    
                    # The step start again
                    if (line.startswith('Exploration Completed.')): 
                        missionCompleted = 1 
                        if missionCompleted and exploredPercentage == 100:
                            print("Exploration Completed. analysis stopted")
                            break

                    if (line.startswith('received: ')): 
                        actionsCounter = actionsCounter + 1
                        receivedAction = line.split()[1]
                        # Decode the action received 
                        actionsRecord.append(decodeActionReceived(receivedAction))

                    # Count number of take-off
                    if (line.startswith('Take-off complete!')):
                        takeoffAction = takeoffAction + 1

                    if (line.startswith('Explored: ')): 
                        exploredPercentage = float(line.split()[1])

                    if (line.startswith("Reached cell")):
                        sucess = 1      # used to flush previus detected T and use only the case one from last map

                    if (line.startswith('X')):
                        for char in line:
                            if char == "T":
                                # Target still not detected on the Map (T not removed from the map)
                                sucess = 0

                
                ############ Analyse actions recorded.
                # Extract unique actions counts
                uniqueActionList = np.array(actionsRecord)
                uniqueActions, countsActions = np.unique(uniqueActionList, return_counts=True)
                # Format actions counts as provided list
                actionsListCount = []   # the order to store the counts is defined in the top list
                dicActions = dict(zip(uniqueActions,countsActions))
                for action in actionList:
                    count = 0
                    indexfound = np.where(uniqueActions == action)
                    if len(indexfound[0]) > 0:
                        count = countsActions[indexfound[0]][0]
                    actionsListCount.append(count)

                reps = {k: v for v, k in enumerate(actionList)}         # Get value, index dictionary
                actionsRecordEncoded = [reps.get(x,x) for x in actionsRecord]   # Replace actions string for index 

                print ("----------- Results -------------")
                print (f'Target founded:     {sucess}')
                print (f'Total area explored:{exploredPercentage}')
                print (f'Number of takeoffs: {takeoffAction}')
                print (f'Number of actions:  {actionsCounter}')
                print (f'Actions Count:      {actionsListCount}')
                print (f'Actions Record:     {actionsRecordEncoded}')

                # Compute percentages
                ############################## Store experiment in global csv:
                ############ Save test result
                print(f'Saving results into: {outputGlobalFile}')
                outputGlobalFileHandler.write(f'{experimentKind}\t{configurationName}\t{experimentResulFolder}\t{mapName}\t{experiment}\t{sucess}\t{exploredPercentage}\t{takeoffAction}\t{actionsCounter}\t{actionsListCount}\t{actionsRecordEncoded}\n') 
                print(f'{experimentName} recorded in global file {outputGlobalFile}... \n')

                if not plotResults:
                    continue        # If results are not plotted, jump from here to next experiment run.
                ############ Average results
                if sucess :
                    takeoffActionSuccess.append(takeoffAction)
                    actionsSuccess.append(actionsCounter)
                    exploredSuccess.append(exploredPercentage)
                    sucessVec.append(sucess)
                    actionsListRecord.append(actionsListCount)
                else:
                    takeoffActionUnsuccess.append(takeoffAction)
                    actionsUnsuccess.append(actionsCounter)
                    exploredUnsuccess.append(exploredPercentage)

                ############ Save test result
                print(f'Saving results into: {outputFile}')
                outputFileHandler.write(f'{actionsCounter},{takeoffAction},{exploredPercentage},{sucess},{actionsListCount}\n') 
                print(f'End {experimentName} analysis.\n')

            if not plotResults:
                continue            # If results are not plotted, jump from here to next map.

            print ("Appending results to global analysis...")
            globalTesttakeoffActionSuccess.append(takeoffActionSuccess)
            globalTestActionsSuccess.append(actionsSuccess)
            globalTestExploredsSuccess.append(exploredSuccess)
            globalActionsListCount.append(actionsListRecord)
            
            if(numberRuns>0):
                successR = float(len(exploredSuccess))/numberRuns*100.0  # convert into %
            else:
                successR = 0
            successRate.append(successR)

            globalTesttakeoffActionFail.append(takeoffActionUnsuccess)
            globalTestActionsFail.append(actionsUnsuccess)
            globalTestExploredsFail.append(exploredUnsuccess)


            print (f'\n----------- {experimentNameMap} analysis Summary -------------')
            print (f'success Rate: {successR}%')
            printInfoList("takeoffActionSuccess",takeoffActionSuccess)
            printInfoList("actionsSuccess",actionsSuccess)
            printInfoList("exploredSuccess",exploredSuccess)
            print(" ---------- ")
            printInfoList("takeoffActionUnsuccess",takeoffActionUnsuccess)
            printInfoList("actionsUnsuccess",actionsUnsuccess)
            printInfoList("exploredUnsuccess",exploredUnsuccess)
            print ("\n")

        if not plotResults:
            continue        # If results are not plotted, jump from here to next experiment folder.
        ############################### ############################### Save and Plot Global Results ###############################
        print ("\n----------- Global Results analisys -------------")

        # Load output file
        fileNameTRes = f'{outputFolder}/globalResults-' + experimentResulFolder + outputFileResultsExtension
        fileTRes = open(fileNameTRes, 'w')
        print(f'Saving results into: {fileNameTRes}')

        # Print the results at the end
        for cont in range(len(globalTesttakeoffActionSuccess)):
            fileTRes.write("{}\t{}\t{}\t{}\n".format(globalTesttakeoffActionSuccess[cont],
                                                globalTestActionsSuccess[cont],
                                                globalTestExploredsSuccess[cont],
                                                successRate[cont],
                                                globalTesttakeoffActionFail[cont],
                                                globalTestActionsFail[cont],
                                                globalTestExploredsFail[cont]
                                                )) 
            print (f'\n----------- Global Analisys {maps[cont%len(maps)][0]}, TestSet {cont//len(maps)}-------------')
            printInfoList("successRate",successRate[cont])
            printInfoList("globalTesttakeoffActionSuccess",globalTesttakeoffActionSuccess[cont])
            printInfoList("globalTestActionsSuccess",globalTestActionsSuccess[cont])
            printInfoList("globalTestExploredsSuccess",globalTestExploredsSuccess[cont])
            print(" ---------- ")
            printInfoList("globalTesttakeoffActionFail",globalTesttakeoffActionFail[cont])
            printInfoList("globalTestActionsFail",globalTestActionsFail[cont])
            printInfoList("globalTestExploredsFail",globalTestExploredsFail[cont])
            

        ################################ Exploreds
        print ("\n Plotting Data... \n")
        plotData(globalTestExploredsSuccess,globalTestExploredsFail,'Total Area Explored [%]',f'explored_{experimentResulFolder}')
        plotData(globalTestActionsSuccess,globalTestActionsFail,'Taken Actions Count',f'actions_{experimentResulFolder}')
        plotData(globalTesttakeoffActionSuccess,globalTesttakeoffActionFail,'Takeoffs Count',f'takeoffs_{experimentResulFolder}')

        plotSuccess(successRate,'Success Rate [%]',f'success_{experimentResulFolder}')

        print ("----------- ------------------ -------------")
        print(f'Experiment processing completed, results saved on: {outputFolder}')
        print("End python script")

