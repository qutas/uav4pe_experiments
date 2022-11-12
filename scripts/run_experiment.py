############################### ############################### Libraries ###############################
############################### Author: Piaktipik
import os                               # library to use some system functions
import glob
import shutil                             # Used to get the lastest .txt files from runs
import subprocess                       # library to run command line/bash scripts
from tqdm import tqdm                   # library to track the progress
import numpy as np                      # Matematics    
import matplotlib.pyplot as plt         # Plots
import re                              # Config file edition Python 2
from os import fsync                    # OS managment file sinc
from shutil import copyfile             # Command to copy files (used to register config.cfg)
import atexit

# Libraries to launch ROS files
import roslaunch
import rospy
import time

#  datetime module
from datetime import datetime as dt
experimentTime = dt.now()
experimentTimeStr = experimentTime.strftime("%y-%m-%dT%H-%M-%S")

import git
repo = git.Repo(search_parent_directories=True)
hash = repo.git.rev_parse(repo.head, short=True)
print(f'Repository hash: {hash}')

############################### ############################### Parameters ###############################
### Experiments names
experimentResulFolder="Exp-{}".format(experimentTimeStr)
configurationNumber = 13
configurationName = "conf{}".format(configurationNumber)
configStoreFileName = "{}.cfg".format(configurationName)
configFileName = "configRun.cfg"
numberRuns = 12                   # number of experiments to run and average.
maxRunTime = 720             # 360 -> 6min, 480 -> 7min 540 -> 9min, 600 -> 10min
experimentKind = "simulation"

### Solver hyper-parameters changes (on configFileName, check configROSFile argument) between tests
vars = ['inspectingReward','exploringReward','landedReward','landingReward','hoveringReward','illegalMovePenalty','crashReward','discountFactor']      # posible to add more variables addin values to both 
new_values = ['20','50','-10','-15','-10','-2','0','0.99']

##### Maps to compare
maps =  [['map-16A'],['map-16AD'],['map-16B'],['map-16BD']]

### Array to store results metrics for succesfull/fail for each map: number of takeoffAction actions, total actions and total acumulated explored.
globalTesttakeoffActionSuccess = []
globalTesttakeoffActionFail = []
successRate = []

globalTestActionsSuccess = []
globalTestActionsFail = []

globalTestExploredsSuccess = []
globalTestExploredsFail = []


############################### Problem config / file system management
print("Test parameters...")
############################### Base path 
absolute_path = os.path.dirname(os.path.abspath(__file__))
relative_path = "../.."
basePath = os.path.abspath(os.path.join(absolute_path, relative_path))
outputFolder = f'{basePath}/uav4pe_experiments/data/{experimentKind}/{configurationName}/{experimentResulFolder}'   # Output folder
outputExpFolder = f'{basePath}/uav4pe_navigation/testing/'      # Experiments Output folder
configROSFile = f'{basePath}/uav4pe_mission_planner/config/{configFileName}' # Config file location

### Create a folder for the test results
outputFolderTest = outputFolder

############################### Internal config
outputFileExtension =  ".txt"                   # format of output file for comand console output
outputFileResultsExtension = ".csv"             # format of output file for extracted results

############################### ############################### Functions ###############################
def exit_handler():
    print ('Closing RunNodeTest.py script...')
    killRosGazebo()
    print ('Closed.')

atexit.register(exit_handler)

# function to update configFileName
def updating(filename,dico):

    RE = '(('+'|'.join(dico.keys())+')\s*=)[^\r\n]*?(\r?\n|\r)'
    pat = re.compile(RE)

    def jojo(mat,dic = dico ):
        return dic[mat.group(2)].join(mat.group(1,3))

    with open(filename,'r') as f:
        content = f.read() 

    with open(filename,'w') as f:
        f.write(pat.sub(jojo,content))

# Directory verification
def ensure_dir(f):
    try:
        d = os.path.dirname(f)
        if not os.path.exists(d):
            print("Creating Path: {} ... ".format(f) )
            os.makedirs(d)
            print("Path: {} created.".format(f))
    except ValueError:
        # Error log
        print('Error ensure_dir: {}'.format(ValueError))

def launch_core():
    print("Starting roscore...")
    subprocess.Popen("roscore")
    time.sleep(10)  # Delay to initialize the roscore

def killRosGazebo():
    print("Killing ros and gazebo...")
    try:
        subprocess.run("killall rosmaster", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Close error: {}".format(e))

    try:
        subprocess.run("killall roscore", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Close error: {}".format(e))

    try:
        subprocess.run("killall julia", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Close error: {}".format(e))

    try:
        subprocess.run("killall gazebo gzclient gzserver mavros_server", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Close error: {}".format(e))
        
    time.sleep(10)  # Delay to ensure kill is done
    
############################### Run Test ###############################
# Traverse experiments
print("Running code {} times...".format(numberRuns))

for experiment in tqdm(range(0,numberRuns)):
    for mapSelected in maps:
        #### Output Path files generation
        mapName = mapSelected[0]
        outputFile = mapName +"_logRun"                           # output header of comand
        outputFileResults = mapName + "_results"                   # output header of results
        # Create a folder for the mapTestResuls
        outputFolderTestRun = outputFolderTest + '/{}/'.format(mapName)
        ensure_dir(outputFolderTestRun)
        print("Map {} selected.\n".format(mapName))
        experimentNameMap = configurationName + " " + mapName

        ############ Change variables in configFileName for Runs ########
        # Add map
        vars.append('map')      
        new_values.append(mapSelected[0])
        # Add output log file for solver
        vars.append('pathLog')      
        new_values.append(outputFolderTestRun)
        # Zip vars and values.
        what_to_change = dict(zip(vars,new_values))
        # Update config File
        updating(configROSFile,what_to_change)
        # save configuration
        copyfile(configROSFile, outputFolderTest + '/{}'.format(configStoreFileName))

        ##### Variables to analyse results
        # Variables for succefull runs
        takeoffActionSuccess = []
        actionsSuccess = []
        exploredSuccess = []
        sucessVec = []
        # Variables for Unsuccefull runs
        takeoffActionUnsuccess = []
        actionsUnsuccess = []
        exploredUnsuccess = []

        ##### generate file names for results runs
        experimentName = experimentNameMap + " Run " + str(experiment)
        experimentNumber = "_N" + str(experiment) + "_"
        fileName1 = outputFolderTestRun + outputFile + experimentNumber + outputFileExtension
        outputRun = ""      # Initialise output from code run

        ############################### Run the code ###############################
        launch_core()

        try:
            rospy.init_node('runTestSim', anonymous=False)
            uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
            roslaunch.configure_logging(uuid)

            launchEmu = roslaunch.parent.ROSLaunchParent(uuid, [f'{basePath}/uav4pe_environments/launch/load_{mapName}.launch'])
            launchEmu.start()
            rospy.loginfo("SimEmuStarted")
            rospy.sleep(1)
            launchNav = roslaunch.parent.ROSLaunchParent(uuid, [f'{basePath}/uav4pe_navigation/launch/load_navigation.launch'])
            launchNav.start()
            rospy.loginfo("TestNavtarted")
            rospy.sleep(1)
            launchJMP = roslaunch.parent.ROSLaunchParent(uuid, [f'{basePath}/uav4pe_mission_planner/launch/load_planner.launch'])
            launchJMP.start()
            rospy.loginfo("TestJMPtarted")
            
            print("Run sim for {} sec...".format(maxRunTime))
            rospy.sleep(maxRunTime)


            # 10 seconds later
            print("Killing simulation session in 5 sec...")
            rospy.sleep(5)
            launchEmu.shutdown()

            # later
            print("Killing nav ...")
            rospy.sleep(1)
            launchNav.shutdown()

            # later
            print("Killing JMP ...")
            rospy.sleep(1)
            launchJMP.shutdown()
            
            rospy.sleep(1)
            killRosGazebo()

        except OSError as e:
            print("Execution failed, error: {}".format(e))

        # Detect new file in testing planetExp_nav move and rename.
        list_of_files = glob.glob('{}*.txt'.format(outputExpFolder))
        latest_file = max(list_of_files, key=os.path.getctime)
        print(latest_file)
        shutil.copyfile(latest_file,fileName1)

## Store experiment run times
print ("\n----------- ------------------ -------------")
endExperimentTime = dt.now()
startTimeStr = "Experiment start time: {}".format(experimentTime)
endTimeStr = "Experiment  end  time: {}".format(endExperimentTime)
durationStr = "Experiment  Duration:  {}".format(endExperimentTime-experimentTime)
durationExpStr = "Experiment  maxRunTime:  {}".format(maxRunTime)
print(endTimeStr)
print(durationStr)

with open(outputFolder + "/times.txt",'w') as file:
    file.write(startTimeStr + "\n")
    file.write(endTimeStr + "\n")
    file.write(durationStr + "\n")
    file.write(durationExpStr + "\n")

print ("----------- ------------------ -------------")
print("End python script")