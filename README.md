<h1>SLEEC-ADAPT</h1>
Instructions to Install the Eclipse-Based Java 21 Version of SLEEC-ADAPT

### Development platform requirements ###

* Java 21
* Eclipse 2025-09
* Xtext SDK 2.40
* The SLEEC-TK


### Setup ###

* Download the eclipse modelling framework 2025-09 and create a workspace.

* Open eclipse marketplace and install xtext

* Clone the SLEECADAPT repository

* Select import, select the plugins and fragments wizard, and then import all components of the AgentAdaption directory into the workspace

* Find the pre-existing SLEEC-TK Repository at https://github.com/UoY-RoboStar/SLEEC-TK and clone the branch fix-mvn-build
git clone -b fix-mvn-build git@github.com:UoY-RoboStar/SLEEC-TK.git

* Delete from sleec-core/circus.robocalc.sleec.tests/src/circus/robocalc/sleec/tests/ the file CSPGenerationTest.xtend

* Open the file SLEECParsingTest.xtend, and delete all but the first test from the file. Save the file.
  
* Go to the top of the SLEEC-TK directory in terminal and do:
`mvn clean install`

* In the workspace, select import, select the plugins and fragments wizard. Choose the sleec-core directory as the directory for import, and import all components.

### Running SLEEC-ADAPT ###

Find Implementation.java inside agentAdaptionCode/src/agentAdaptionCode. Run Implementation.java to run the SLEEC-ADAPT algorithm. It is pre-set up to run the Chatbot case study with universal sleec rules. The output will be placed in the directory agentAdaptionCode/outputWorkflows. The files for this example, and all case study examples can be found in the directory agentAdaptionCode/inputFiles/caseStudy.

If you wish to change the files used as input, add your files to the inputFiles folder. Next, navigate to the main class of Implement.java and change the first parameter of runAlgorithm to "inputFiles/&lt;Your Workflow file.workflowspec&gt;" and the second parameter to "inputfiles/&lt;Your sleec file.sleec&gt;". If you want to change the name of the output workflow file, change the third variable.

### Running Scalability Analysis and Unit Tests

AdaptionUnitTest.java in agentAdaptionCode/src/agentAdaptionCode implements the unit tests for SLEEC-ADAPT. The test files are pre-installed in the repository and will be loaded when AdaptionUnitTest is run.

Find the scalability data collector in agentAdaptionCode/src/Scalability.java. Workflow files consisting of up to 5000 tasks are included, with large sleec files included. Should you want to run with larger workflows, find the LargeWorkflowGenerator.py located in this repository under Scalability/InputGenerators. The x variable on line 135 and line 103 is used to iterate over the workflows: change the limits from 5000 to the new limit.

To run, check either ExperimentSLEECRules() or ExperimentDefeaterRules() is called in the main function of the Scalability class, and run Scalability.java. Data will be stored in the scalability/csvFiles, as .csv files.

### Creating Input Files ###

To access the workflow validation tools in an Eclipse runtime interface, navigate to AgentAdaption/agent.adaption.xtext.workflow/src/agent/adaption/xtext/workflow and right click on GenerateWorkflow.mwe2. Select run as, and then run configurations. Select launch runtime eclipse, with the execution environment set to JavaSE-21 or equivalent.

Click file, new, and chose the file option. Create a file with a name that ends with .workflowspec. This will enable the workflow grammar checking functionality. You can then create new workflows aided by syntax highlighting and grammar checking.

See the documentation of your chosen SLEEC tool to access the validation functionality.


<h1>E-Commerce Chatbot</h1>



