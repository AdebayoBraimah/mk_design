#!/usr/bin/env python

# Import modules/packages
import pytest
import subprocess
import logging
import os
import shutil
import sys
import glob

# Define global variables
scripts_dir = os.path.dirname(os.path.realpath(__file__))

# Change to working directory
os.chdir(scripts_dir)

# Define class(es)
class Command(object):
    """
    Creates a command and an empty command list for UNIX command line programs/applications. Primary use and
    use-cases are intended for the subprocess module and its associated classes (i.e. Popen/call/run).
    
    Attributes (class and instance attributes):
        command (instance): Command to be performed on the command line.
        cmd_list (instance): Mutable list that can be appended to.
    
    Modules/Packages required:
        - os
        - logging
        - subprocess
    """

    def __init__(self,command):
        """
        Init doc-string for Command class. Initializes a command to be used on UNIX command line.
        The input argument is a command (string), and a mutable list is returned (, that can later
        be appended to).
        
        Usage:
            echo = Command("echo")
            echo.cmd_list.append("Hi!")
            echo.cmd_list.append("I have arrived!")
        
        Arguments:
            command (string): Command to be used. Note: command used must be in system path
        Returns:
            cmd_list (list): Mutable list that can be appended to.
        """
        self.command = command
        self.cmd_list = [f"{self.command}"]
        
    def log(self,log_file="log_file.log",log_cmd=""):
        """
        Log function for logging commands and messages to some log file.
        
        Usage:
            # Initialize the `log` function command
            log_msg = Command("log")
            
            # Specify output file and message
            log_msg.log("sub.log","test message 1")
            
            # Record message, however - no need to re-initialize `log` funcion command or log output file
            log_msg.log("test message 2")
        
        NOTE: The input `log_file` only needs to be specified once. Once specified,
            this log is written to each time this or the `run` function is invoked.
        
        Arguments:
            log_file(file): Log file to be written to. 
            log_cmd(str): Message to be written to log file
        """
        
        # Set-up logging to file
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%d-%m-%y %H:%M:%S',
                            filename=log_file,
                            filemode='a')
        
        # Define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        # Add the handler to the root logger
        logging.getLogger().addHandler(console)
        
        # Define logging
        logger = logging.getLogger(__name__)
        
        # Log command/message
        logger.info(f"{log_cmd}")
        
    def run(self,log_file="log_file.log",debug=False,dryrun=False,env=None,stdout="",shell=False):
        """
        Uses python's built-in subprocess class to execute (run) a command from an input command list.
        The standard output and error can optionally be written to file.
        
        Usage:
            echo.run() # This will return tuple (returncode,log,None,None), but will echo "Hi!" to screen.
            
        NOTE: 
            - The contents of the 'stdout' output file will be empty if 'shell' is set to True.
            - Once the log file name 'log_file' has been set, that value is stored and cannot be changed.
                - This log file will continue to be appended to for each invocation of this class.
        Arguments:
            log_file(file): Output log file name.
            debug(bool): Sets logging function verbosity to DEBUG level
            dryrun(bool): Dry run -- does not run task. Command is recorded to log file.
            env(dict): Dictionary of environment variables to add to subshell.
            stdout(file): Output file to write standard output to.
            shell(bool): Use shell to execute command.
        Returns:
            p.returncode(int): Return code for command execution should the 'log_file' option be used.
            log_file(file): Output log file with appended information should the 'log_file' option be used.
            stdout(file): Standard output writtent to file should the 'stdout' option be used.
            stderr(file): Standard error writtent to file should the 'stdout' option be used.
        """
        
        # Define logging
        logger = logging.getLogger(__name__)
        cmd = ' '.join(self.cmd_list) # Join list for logging purposes
        
        if debug:
            logger.debug(f"Running: {cmd}")
        else:
            logger.info(f"Running: {cmd}")
        
        if dryrun:
            logger.info("Performing command as dryrun")
            return 0
        
        # Define environment variables
        merged_env = os.environ
        if env:
            merged_env.update(env)
        
        # Execute/run command
        p = subprocess.Popen(self.cmd_list,shell=shell,env=merged_env,
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        # Write log files
        out,err = p.communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')

        # Write std output/error files
        if stdout:
            stderr = os.path.splitext(stdout)[0] + ".err"
            with open(stdout,"w") as f_out:
                with open(stderr,"w") as f_err:
                    f_out.write(out)
                    f_err.write(err)
                    f_out.close(); f_err.close()
        else:
            stdout = None
            stderr = None

        if p.returncode:
            logger.error(f"command: {cmd} \n Failed with returncode {p.returncode}")

        if len(out) > 0:
            if debug:
                logger.debug(out)
            else:
                logger.info(out)

        if len(err) > 0:
            if debug:
                logger.info(err)
            else:
                logger.warning(err)
        return p.returncode,log_file,stdout,stderr

# Writes functions
def write_design_files(out_dir):
    """
    Wrapper function for `test.design.sh` script
    NOTE: scripts_dir is assumed to be a global variable
    """
    test = Command(os.path.join(scripts_dir,"test.design.sh"))
    test.cmd_list.append(out_dir)
    [returncode,log_file,stdout,stderr] = test.run(log_file="log_file.log",shell=False)
    return returncode,log_file,stdout,stderr

def compare_file(file1,file2):
    """
    Compares two different files line-by-line
    NOTE: The second file (file2) is the file in which differences 
        should be identified.
    """
    lines = []
    with open(file1,'r') as f1:
        with open(file2,'r') as f2:
            for line1,line2 in zip(f1,f2):
                if line1 != line2:
                    lines = line2
            f1.close(); f2.close()
    return lines

def directory_file_lists(bench_dir,out_dir):
    """
    Inputs are top-level parent directories
    """
    
    bench_list = glob.glob(os.path.join(bench_dir,"*grp*/*"),recursive=False)
    test_list = glob.glob(os.path.join(out_dir,"*grp*/*"),recursive=False)
    return [bench_list,test_list]

def design_matrices_test(out_dir,bench_dir="benchmark"):
    """
    Tests if design files in each directory are the same
    """
    [returncode,log_file,stdout,stderr] = write_design_files(out_dir)
    if returncode != 0:
        print("")
        print("Non-zero error code writing test matrices")
        sys.exit(18)

    if not os.path.exists(out_dir):
        print("")
        print("Output test design matrix directories do not exist")
        sys.exit(65)
    else:
        out_dir = os.path.abspath(out_dir)

    if not os.path.exists(bench_dir):
        print("")
        print("Benchmark design matrix directories do not exist")
        sys.exit(65)
    else:
        bench_dir = os.path.abspath(bench_dir)
    
    [bench_files,test_files] = directory_file_lists("benchmark",out_dir)
    
    files = []
    for f1,f2 in zip(bench_files,test_files):
        lines = compare_file(f1,f2)
        if len(lines) > 0:
            tmp_list = [f2]
            files.append(tmp_list)
    
    # Clean-up (local)
    os.remove("test.log")
    shutil.rmtree(out_dir)
    
    if len(files) > 0:
        print("Test failure. Output design matrices appear to be different")
        return False
    else:
        print("Tests passed.")
        return True

tmpdir = "test.results"
result = design_matrices_test(tmpdir,"benchmark")

def test_passed(tmpdir):
    assert result == True

