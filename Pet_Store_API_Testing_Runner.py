'''
Created on Sep 7, 2018

@author: agagaleza
feature file path
#for console
featureFilePath = './features/feature_pet/ '
#for eclipse
featureFilePath = 'Pet_Store_API_Testing.feature'

tagOptions = ' --tags=@smoke '

python Pet_Store_API_Testing_Runner.py ./features/feature_pet/  --tags=@smoke

Traceback (most recent call last):
  File "Pet_Store_API_Testing_Runner.py", line 56, in <module>
    fullRunnerOptions = tagOptions + featureFilePath + reportingRelated + commonRunnerOptions
NameError: name 'featureFilePath' is not defined

'''

import glob
import sys
import os
from shutil import rmtree
from behave import __main__ as runner_with_options
import json
from reporting.report_generator import ReportGenerator
from datetime import datetime
import collections
import logging
from reporting.report_constants import ReportConstants

if __name__ == '__main__':
    #read feature file path from console
    logger = logging.getLogger(__name__)

    tagOptions = ''
    try:
        featureFilePath = sys.argv[1]
        tagOptions = ' ' + sys.argv[2] + ' ' 
    except IndexError:
        logger.error('tag or feature file was not provided')
        
    sys.stdout.flush()
    test_date = str(datetime.now().strftime("%Y_%m_%d_%H%M"))
    reporting_folder_name = './reporting/results/' + test_date
    #
    # remove if any reporting folder exists
    if os.path.exists(reporting_folder_name):
        rmtree(reporting_folder_name)
    os.makedirs(reporting_folder_name)
    #
    # allure reporting related command line arguments
    reportingRelated = ' -f allure_behave.formatter:AllureFormatter -o ' + reporting_folder_name + '  '

    # command line argument to capture console output
    commonRunnerOptions = ' --no-capture --no-capture-stderr -f plain '
    #
    # full list of command line options
    fullRunnerOptions = tagOptions + featureFilePath + reportingRelated + commonRunnerOptions
    #
    # run Behave + BDD + Python code
    runner_with_options.main(fullRunnerOptions)
    
    # read resultant json file
    listOfJsonFiles = glob.glob(reporting_folder_name + "/*.json")
    scenario_dict = {}
    for cnt in range(0, len(listOfJsonFiles)):
        scenario_data = json.loads(open(listOfJsonFiles[cnt], 'r').read())
        start_time = int(scenario_data[ReportConstants.START])
        scenario_dict[start_time] = scenario_data
    data = []
    index = 0
    for start_time in collections.OrderedDict(sorted(scenario_dict.items())):
        logger.info(str(start_time))
        logger.info(scenario_dict[start_time][ReportConstants.NAME])
        scenario_data = {}
        scenario_data[ReportConstants.SCENARIO + str(index)] = scenario_dict[start_time]
        data.append(scenario_data)
        index +=1

    output = open(reporting_folder_name + '/' + str(datetime.now().strftime("%Y_%m_%d_%H%M_pet_store_api_report.html")), 'wb')
    generator = ReportGenerator(stream = output)
    report = generator.generate_report(data)
