from __future__ import annotations
import os
import json
import tarfile
from pathlib import *

from VipLauncher import VipLauncher

import vip

"""
Main Features (leading to public methods)
A. Manage a Session from start to finish, *i.e.*:
    A.1. Login to VIP
    A.2. Upload the input data on VIP
    A.3. Launch executions on VIP
    A.4. Monitor executions on VIP
    A.5. Download the results from VIP
    A.6. Clean up the inputs/outputs on VIP.
B. Additional features for avanced use:
    B.1 Display session properties to the user
    B.2 Clone a session to avoid uploading the same dataset twice

Background Specifications:
C. A VIP session should persist in time:
    C.1 Session attributes are backed up at each session step
    C.2 A backup can be resumed at instanciation
D. A VIP session should be user-friendly:
    D.1 Hide VIP paths to the user and allow multi-OS use (Unix, Windows)
    D.2 Prevent common mistakes in session / pipeline settings
    D.3 Interpret common API exceptions ("Error 8000", etc.)
"""

class VipSession(VipLauncher):
    """
    Python class to run VIP pipelines on local datasets.

    1 "session" allows to run 1 pipeline on 1 dataset with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `input_dir` (str | os.PathLike) Path to the local dataset.
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters required to run the pipeline.

    N.B.: all instance methods require that `VipSession.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

    # --- Overriden from the parent class ---

    # Class name
    __name__ = "VipSession"
    # Properties to save / display for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id",
        "local_input_dir",
        "local_output_dir", 
        "vip_input_dir",
        "vip_output_dir",
        "input_settings", 
        "workflows"
    ]
    # Verbose state for display
    _VERBOSE = True

    # --- New Attributes ---

    # Default path to upload and download data on VIP servers
    _SERVER_DEFAULT_PATH = PurePosixPath("/vip/Home/API/")
    # Default path to save session outputs on the current machine
    _LOCAL_DEFAULT_PATH = Path("./vip_outputs")

                    #################
    ################ Main Properties ##################
                    ################# 

    # --- Overriden from the parent class ---

    # Alias `output_dir` refers to the *local* output directory
    @property
    def output_dir(self) -> str:
        """Same as `local_output_dir`"""
        return self.local_output_dir
    
    @output_dir.setter
    def output_dir(self, new_dir: str) -> None:
        self.local_output_dir = new_dir

    @output_dir.deleter
    def output_dir(self) -> None:
        del self.local_output_dir
    # ------------------------------------------------

    # --- New Properties ---

    # Local input directory
    @property
    def local_input_dir(self):
        """Local path to the input data"""
        return str(self._local_input_dir) if self._is_defined("_local_input_dir") else None
    
    @local_input_dir.setter
    def local_input_dir(self, new_dir) -> None:
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("Property `local_input_dir` should be a string or os.PathLike object")
        # Path-ify to account for relative paths
        new_path = Path(new_dir)
        # Check conflicts with instance value
        if self._is_defined("_local_input_dir") and (new_path.resolve() != self._local_input_dir.resolve()):
            raise ValueError(f"Input directory is already set for session: {self._session_name} ('{self._local_input_dir}' -> '{new_dir}').")
        # File existence is not checked for session portability between machines
        # Assign
        self._local_input_dir = new_path
        # Update the `input_settings` with this new input directory
        self._update_input_settings()

    @local_input_dir.deleter
    def local_input_dir(self) -> None:
        del self._local_input_dir
    # ------------------------------------------------

    # Alias for the local input directory
    @property
    def input_dir(self) -> str:
        """Same as `local_input_dir`"""
        return self.local_input_dir
    
    @input_dir.setter
    def input_dir(self, new_dir: str) -> None:
        self.local_input_dir = new_dir

    @input_dir.deleter
    def input_dir(self) -> None:
        del self.local_input_dir
    # ------------------------------------------------

    # Input directory on VIP
    @property
    def vip_input_dir(self) -> str:
        """VIP path to the input data"""
        return str(self._vip_input_dir) if self._is_defined("_vip_input_dir") else None

    @vip_input_dir.setter
    def vip_input_dir(self, new_dir) -> None:
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("Property `vip_input_dir` should be a string or os.PathLike object")
        # Check conflicts with instance value
        if self._is_defined("_vip_input_dir") and (new_dir != self.vip_input_dir):
            raise ValueError(f"Input directory is already set for session: {self._session_name} ('{self.vip_input_dir}' -> '{new_dir}').")
        # Assign
        self._vip_input_dir = PurePosixPath(new_dir)
        # Update the `input_settings` with this new input directory
        self._update_input_settings()

    @vip_input_dir.deleter
    def vip_input_dir(self) -> None:
        del self._vip_input_dir
    # ------------------------------------------------

    # Local output directory
    @property
    def local_output_dir(self) -> str:
        """Local path to the output data"""
        return str(self._local_output_dir) if self._is_defined("_local_output_dir") else None
    
    @local_output_dir.setter
    def local_output_dir(self, new_dir) -> None:
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("Property `local_output_dir` should be a string or os.PathLike object")
        # Path-ify to account for relative paths
        new_path = Path(new_dir)
        # Check conflicts with instance value
        if self._is_defined("_local_output_dir") and (new_path.resolve() != self._local_output_dir.resolve()):
            raise ValueError(f"Output directory is already set for session: {self._session_name} ('{self._local_output_dir}' -> '{new_dir}').")
        # Assign
        self._local_output_dir = new_path

    @local_output_dir.deleter
    def local_output_dir(self) -> None:
        del self._local_output_dir
    # ------------------------------------------------
    
    # VIP path to all session data
    @property
    def _vip_dir(self) -> str:
        """Default VIP path containing all session data"""
        return self._SERVER_DEFAULT_PATH / self._session_name
    # ------------------------------------------------

                    #############
    ################ Constructor ##################
                    #############
    def __init__(
            self, session_name="",  input_dir="", pipeline_id="",  
            input_settings:dict={}, output_dir="", verbose=True
        ) -> None:
        """
        Create a VipSession instance from keyword arguments. 
        Displays informations unless `verbose` is False.

        Available keywords:
        - `session_name` (str) A name to identify this session.
            Default value: 'VipSession_[date]-[time]'

        - `input_dir` (str | os.PathLike) Local path to your full dataset.
            This directory must be uploaded on VIP servers before pipeline runs.

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary should contain only strings or os.PathLike objects (including PathLib objects), 
                or lists of both types. 
            - Lists of parameters launch parallel workflows on VIP.

        - `output_dir` (str | os.PathLike) Local path to the directory where: 
            - session properties will be saved; 
            - pipeline outputs will be downloaded from VIP servers.

            Default value: './vip_outputs/[`session_name`]'
        
        If `session_name` or `output_dir` lead to data from a previous session, 
        all properties will be loaded from the session file ('session_data.json').
        """
        # Initiate parameters from the parent class
        super().__init__(
            session_name = session_name,
            pipeline_id = pipeline_id,
            input_settings = input_settings,
            verbose = verbose
        )
        # Set the local output directory
        if output_dir:
            self.local_output_dir = output_dir
        else:
            self.local_output_dir = self._LOCAL_DEFAULT_PATH / self._session_name
        # Check existence of data from a previous session
        if not self._load_session(verbose=verbose):
            # Set the VIP input directory (default value)
            self.vip_input_dir = self._vip_dir / "INPUTS"
            # Set the VIP output directory (default value, masked to the user)
            self.vip_output_dir = self._vip_dir / "OUTPUTS"
            # Set the local input directory
            if input_dir:
                print("Input Directory:", input_dir, end="")
                self.local_input_dir = input_dir
                if verbose and self._exists(input_dir, "local"):
                    print(" [checked]")
                elif verbose: 
                    print(f"\n(!) `input_dir` does not exist in the local file system.")
                    print(f"    This will throw an error during upload_inputs().")
        # Display the output directory
        if verbose:
            print("Output Path:", self._local_output_dir)
        # End display if we're in this class
        if verbose and (self.__name__ == "VipSession"): print()
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # Overwrite VipLauncher.init() to be compatible with new kwargs
    @classmethod
    def init(cls, api_key: str, verbose=True, **kwargs) -> VipSession:
        """
        Handshakes with VIP using your API key. 
        Prints a list of pipelines available with the API key, unless `verbose` is False.
        Returns a VipSession instance which properties can be provided as keyword arguments (`kwargs`).

        Input `api_key` can be either:
        A. (unsafe) a string litteral containing your API key, or
        B. (safer) a path to some local file containing your API key, or
        C. (safer) the name of some environment variable containing your API key.

        In cases B or C, the API key will be loaded from the local file or the environment variable.        
        """
        # Handshake with VIP
        super().init(api_key=api_key, verbose=verbose)
        # Return a VipSession instance for method cascading
        return VipSession(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------
   
    # ($A.2) Upload a dataset on VIP servers
    def upload_inputs(self, input_dir="", update_files=True, verbose=_VERBOSE) -> VipSession:
        """
        Uploads to VIP servers a dataset contained in the local directory `input_dir` (if needed).
        - If `input_dir` is not provided, `self.input_dir` will be used.
        - If `update_files` is True, the input directory on VIP will be checked in depth for missing files.
        - Set `verbose` to False to run silently.

        Error profile:
        - Raises TypeError is `input_dir` is missing;
        - Raises ValueError if `input_dir` conflicts with session properties;
        - Raises FilenotFoundError if `input_dir` could not be found on this machine;
        - Raises RuntimeError if the client fails to communicate with VIP;

        Session is backed up at the end of the procedure.
        """
        # Update the verbose state for private methods
        self._VERBOSE = verbose
        # First Display
        if verbose: print("\n<<< UPLOAD INPUTS >>>\n")
        # Check the distant (VIP) input directory        
        try: 
            # Check connection with VIP 
            exists = self._exists(self._vip_input_dir, location="vip")
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        # Return if `update_files` is False and input data are already on VIP
        if exists and not update_files:
            if verbose: 
                print("Skipped : There are already input data on VIP.")
            # Return 
            return self
        # Set local input directory
        if input_dir:
            self.local_input_dir = input_dir
        elif not self._is_defined("_local_input_dir"): 
            raise TypeError(f"Session >{self._session_name}>: Please provide an input directory.")
        # Check local input directory
        if not self._exists(self._local_input_dir, location="local"): 
            raise FileNotFoundError(f"Session '{self._session_name}': Input directory does not exist.")
        # Check the local values of `input_settings` before uploading
        if self._is_defined("_input_settings"):
            if verbose: print("Checking references to the dataset within Input Settings ... ", end="")
            try: 
                self._check_input_settings(location="local")
                print("OK.")
            except FileNotFoundError as fe:
                raise fe from None
            except AttributeError:
                if verbose: print("Skipped (missing properties).")
            except(TypeError, ValueError, RuntimeError) as e:
                if verbose: 
                    print("Skipped. The following exception was raised:")
                    print("\t", e)
                    print("This will throw an error during launch_pipeline().")
            if verbose: print()
        # Initial display
        if verbose:
            print("Uploading the dataset on VIP")
            print("-----------------------------")
        # Upload the input repository
        try:
            failures = self._upload_dir(self._local_input_dir, self._vip_input_dir)
            # Display report
            if verbose:
                print("-----------------------------")
                if not failures :
                    print( "Everything is on VIP.")
                else: 
                    print("End of the process.") 
                    print( "The following files could not be uploaded on VIP:\n\t")
                    print( "\n\t".join(failures))
        except Exception as e:
            # An unexpected error occurred
            if verbose:
                print("-----------------------------")
                print("\n(!) Upload was stopped following an unexpected error.")
            raise e from None
        finally:
            # In any case, save session properties
            self._save_session()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.3) Launch executions on VIP 
    def launch_pipeline(
            self, pipeline_id="", input_settings:dict={}, nb_runs=1, verbose=True
        ) -> VipSession:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary should contain only strings or os.PathLike objects (including PathLib objects), 
                or lists of both types. 
            - Lists of parameters launch parallel workflows on VIP.
        - `nb_runs` (int) Number of parallel workflows to launch with the same `pipeline_id`/`input_settings`.
        - Set `verbose` to False to run silently.
        
        Error profile:
        - Raises TypeError:
            - if some argmuent could not be checked;
            - if some argument is missing; 
            - if some parameter is missing in `input_settings`.
        - Raises ValueError:
            - if some argument conflicts with session properties;
            - if some parameter in `input_settings` does not the fit the pipeline definition.
        - Raises FilenotFoundError if an input file is missing on VIP servers.
        - Raises RuntimeError in case of failure from the VIP API.
        
        Session is backed up at the end of the procedure.
        """
        try :
            super().launch_pipeline(
                pipeline_id = pipeline_id, # default
                input_settings = input_settings, # default
                output_dir = self.vip_output_dir, # VIP output directory
                nb_runs = nb_runs, # default
                verbose = verbose # default
            )
        except Exception as e:
            raise e
        finally:
            # In any case, save session properties
            self._save_session()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30, verbose=_VERBOSE) -> VipSession:
        """
        Updates and displays the status for each execution launched in the current session.
        - If an execution is still running, updates status every `refresh_time` (seconds) until all runs are finished.
        - Set `verbose` to False to run silently.

        Session is backed up at the end of the procedure.
        """
        # Monitor the workflows
        super().monitor_workflows(refresh_time=refresh_time, verbose=verbose)
        # Session properties are automatically saved within super() through the call to `update_workflows()`
        if verbose: print(f"\nSession properties were saved.\n")
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.5) Download execution outputs from VIP servers 
    def download_outputs(self, get_status=["Finished"], unzip=True, verbose=_VERBOSE) -> VipSession:
        """
        Downloads all session outputs from VIP servers.
        - If `unzip` is True, extracts the data if any output is a .tar file.
        - Set `verbose` to False to download silently.
        """
        # Update the verbose state for private methods
        self._VERBOSE = verbose
        # First display
        if verbose: print("\n<<< DOWNLOAD OUTPUTS >>>\n")
        # Check if current session has existing workflows
        if not self._workflows:
            if verbose:
                print("This session has not yet launched any execution.")
                print("Run launch_pipeline() to launch workflows on VIP.")
                print("Current session properties are:")
                self.display()
            return self
        # Update the worflow inventory
        if verbose: print("Updating workflow status ... ", end="")
        self._update_workflows(save_session=False)
        if verbose: print("Done.\n")
        # Initial display
        if verbose:
            print("Downloading pipeline outputs to:\n\t", self._local_output_dir)
            print("--------------------------------")
        # Get execution report
        report = self._execution_report(display=False)
        # Count the number of executions to process
        nb_exec = len(report['Removed']) if "Removed" in report else 0
        assert 'Removed' not in get_status, "Cannot download removed data."
        for status in get_status:
            nb_exec += len(report[status]) if status in report else 0
        nExec=0
        # Browse workflows with removed data and check if files are missing
        if "Removed" in report :
            for wid in report["Removed"]:
                nExec+=1
                # Display current execution
                if verbose: 
                    print(f"[{nExec}/{nb_exec}] Outputs from:", wid, "-> REMOVED from VIP servers")
                # Get the path of the returned files on VIP
                vip_outputs = self._workflows[wid]["outputs"]
                # If there is no output file, go to the next execution
                if not vip_outputs: 
                    if verbose: print("\tNothing to download.")
                    continue
                # Browse the output files to check if they have already been downloaded
                missing_file = False
                for output in vip_outputs:
                    # Get the output path on VIP
                    vip_file = PurePosixPath(output["path"])
                    # Get the local equivalent path
                    local_file = self._get_local_output_path(vip_file)
                    # Check file existence on the local machine
                    if not local_file.exists(): 
                        missing_file = True
                # After checking all files, update the display
                if verbose: 
                    if not missing_file: 
                        print("\tOutput files are already in:", local_file.parent.resolve())
                    else: 
                        print("(!)\tCannot download the missing files.")
        # Check if any workflow with the desired status is available
        if not any([status in report for status in get_status]):
            if verbose:
                print("--------------------------------")
                print("Nothing to download for the current session.") 
                print("Run monitor_workflows() for more information.") 
            return self
        # Download each output file for each execution and keep track of failed downloads
        failures = []
        for wid in self._workflows:
            # Check if the workflow should be processed
            if self._workflows[wid]["status"] not in get_status:
                continue
            nExec+=1 
            # Display current execution
            if verbose: 
                print(f"[{nExec}/{nb_exec}] Outputs from: ", wid, 
                    " | Started on: ", self._workflows[wid]["start"],
                    " | Status: ", self._workflows[wid]["status"], sep='')
            # Get the path of the returned files on VIP
            vip_outputs = self._workflows[wid]["outputs"]
            # If there is no output file, go to the next execution
            if not vip_outputs: 
                if verbose: print("\tNothing to download.")
                continue
            # Browse the output files
            nFile = 0 # File count
            missing_file = False # Will be True if local files are missing
            for output in vip_outputs:
                nFile+=1
                # Get the output path on VIP
                vip_file = PurePosixPath(output["path"])
                # TODO: implement the case in which the output is a directory (mirror _upload_dir ?)
                if output["isDirectory"]:
                    raise NotImplementedError(f"{vip_file} is a directory: cannot be handled for now.")
                # Get the local equivalent path
                local_file = self._get_local_output_path(vip_file)
                # Check file existence on the local machine
                if self._exists(local_file, "local"): 
                    continue
                # If not, update the output data
                missing_file = True
                # Make the parent directory (if needed)
                local_dir = local_file.parent
                if self._mkdirs(local_dir, location= "local") and verbose: print("\tNew directory:", local_dir)
                # Get the file size in Megabytes
                try: 
                    size = f"{output['size']/(1<<20):,.1f}MB"
                except:
                    size = "size unknown"
                # Display the process
                if verbose: print(f"\t[{nFile}/{len(vip_outputs)}] Downloading file ({size}):", 
                                local_file.name, end=" ... ")
                # Download the file from VIP servers
                if self._download_file(vip_path=vip_file, local_path=local_file):
                    # Display success
                    if verbose: print("Done.")
                    # If the output is a tarball, extract the files and delete the tarball
                    if unzip and output["mimeType"]=="application/gzip" and tarfile.is_tarfile(local_file):
                        if verbose: print("\t\tExtracting archive content ...", end=" ")
                        if self._extract_tarball(local_file):
                            if verbose: print("Done.") # Display success
                        elif verbose: 
                            print("Extraction failed.") # Display failure
                else: # failure while downloading the output file
                    # Update display
                    if verbose: print(f"\n(!)\tSomething went wrong in the process. Please retry later.")
                    # Update missing files
                    failures.append(str(vip_file))
            # End of file loop
            if verbose:
                if not missing_file: # All files were already there
                    print("\tAlready in:", local_file.parent) 
                else:  # Some missing files were succesfully downloaded
                    print("\tDone for all files.")
        # End of worflow loop    
        if verbose:
            print("--------------------------------")
            if not failures :
                print("Done for all executions.")
            else:
                print("End of the procedure.") 
                print("The following files could not be downloaded from VIP: \n\t", end="")
                print("\n\t".join(failures))
            print()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.2->A.5) Run a full VIP session 
    def run_session(
            self, update_files=True, nb_runs=1, refresh_time=30, 
            get_status=["Finished"], unzip=True, verbose=True
        ) -> VipSession:
        """
        Runs a full session without the finish() step.
        1. Uploads the database on VIP or check the uploaded files;
        2. Launches pipeline executions on VIP;
        3. Monitors pipeline executions until they are all over;
        4. Downloads execution results from VIP.

        /!\ This method assumes that all session properties are already set.
        Optional arguments can still be provided:
        - Set `update_files` to False to avoid checking the input data on VIP;
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `refresh_time` to modify the default monitoring time;
        - Set `get_status` to download files from workflows with a specific status
        - Set unzip to False to avoid extracting .tgz files during the download. 
        
        Set `verbose` to False to run silently. 
        """
        return (
            # 1. Upload the database on VIP or check the uploaded files
            self.upload_inputs(update_files=update_files, verbose=verbose)
            # 2. Launche `nb_runs` pipeline executions on VIP
            .launch_pipeline(nb_runs=nb_runs, verbose=verbose)
            # 3. Monitor pipeline executions until they are all over
            .monitor_workflows(refresh_time=refresh_time, verbose=verbose)
            # 4. Download execution results from VIP
            .download_outputs(get_status=get_status, unzip=unzip, verbose=verbose)
        )

    # ($A.6) Clean session data on VIP
    def finish(self, timeout=300, verbose=_VERBOSE) -> VipSession:
        """
        Removes session's data from VIP servers (INPUTS and OUTPUTS). 
        The downloaded outputs and the input dataset are kept on the local machine.

        Detailed behaviour:
        - This process checks for actual deletion on VPI servers until `timeout` (seconds) is reached.
            If deletion could not be verified, the procedure ends with a warning message.
        - Workflows status are set to "Removed" when the corresponding outputs have been removed from VIP servers.
        
        Set `verbose` to False to run silently. 
        """
        # Finish the session based on self._path_to_delete()
        super().finish(timeout=timeout, verbose=verbose)
        # Check if the input data have been erased (this is not the case when get_inputs have been used)
        if (self._vip_input_dir != self._vip_dir / "INPUTS"
            and self._exists(self._vip_input_dir, location="vip") 
            and verbose
            ):
            print(f"(!) The input data are still on VIP:\n\t{self.vip_input_dir}")
            print("They belong to another session.")
            print("Please run finish() from the original session or remove them manually through the VIP portal:")
            print(f"\t{self._VIP_PORTAL}")         
        # Return for method cascading
        return self
    # ------------------------------------------------

    ###########################################
    # ($B) Additional Features for Advanced Use
    ###########################################

    # ($B.1) Display session properties in their current state
    def display(self) -> VipSession:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `input_dir`: path to the input data *on your local machine*
        - `output_dir`: path to pipeline outputs *on your local machine*
        - `vip_input_dir`: path to the input data *in your VIP Home directory*
        - `vip_output_dir` : path to the pipeline outputs *in your VIP Home directory*
        - `input_settings` : input parameters sent to VIP (file locations are bound to `vip_input_dir`).
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Return for method cascading
        return super().display()
    # ------------------------------------------------

    # ($B.2) Get inputs from another session to avoid double uploads
    def get_inputs(self, session: VipSession, get_pipeline=False, get_settings=False, verbose=_VERBOSE) -> VipSession:
        """
        Binds the current session to the inputs of another (`session`), to avoid re-uploading the same dataset on VIP servers.
        
        This method can be used to efficiently run different *pipeline_id* or *input_settings* on the same dataset.
        One session is used to 

        Detailed behaviour and inputs:
        - Current session will point to `session`'s input directories locally and on VIP 
            (i.e, `session.local_input_dir` and `session.vip_input_dir`);
        - If `get_pipeline` is True, the current *pipeline_id* is also synchronized with `session`;
        - If `get_settings` is True, the current *input_settings* are also synchronized with `session`.
        - Set `verbose` to False to run silently. 

        Error profile:
        - Raises FileExistsError if the current session has temporary data on VIP ;
        - Raises FileNotFoundError if the other `session` do not have input data on VIP.
        """
        # End the procedure if both sessions already share the same inputs
        if self._vip_input_dir == session._vip_input_dir:
            # Display
            if verbose: 
                print(f"\nSessions '{self._session_name}' and '{session._session_name}' already share the same inputs on VIP.")
            # Return for method cascading
            return self
        # Check if current session do not have data on VIP
        if self._exists(self._vip_dir, location="vip"):
            msg = f"Session '{self._session_name}' has temporary data on VIP.\n"
            msg += "Please finish this session or start another one."
            raise FileExistsError(msg)
        # Check if the data actually exist on VIP
        if not self._exists(session._vip_input_dir, location="vip"):
            raise FileNotFoundError(f"Input data for session '{session._session_name}' do not exist on VIP.")
        # Get the VIP inputs from the other session
        self._set(
            local_input_dir=session.local_input_dir, # Local data
            vip_input_dir=session.vip_input_dir, # Distant data 
        )
        # Get the pipeline identifier from the other session
        if get_pipeline:
            self._set(pipeline_id=session.pipeline_id)
        # Get the input settings from the other session
        if get_settings:
            self._set(input_settings=session.input_settings)
        # Display success
        if verbose : 
            print(
                f"\nSession '{self._session_name}' now shares its inputs "\
                + f"with session '{session._session_name}'." )
        # Save new properties
        self._save_session()
        # Return for method cascading
        return self
    # -----------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    ###################################################################
    # Methods that must be overwritten to adapt VipLauncher methods to
    # new location: "local"
    ###################################################################

    # Method to check existence of a distant or local resource.
    @classmethod
    def _exists(cls, path: PurePath, location="local") -> bool:
        """
        Checks existence of a distant (`location`="vip") or local (`location`="local") resource.
        `path` can be a string or path-like object.
        """
        # Check path existence in `location`
        if location=="local":
            return os.path.exists(path)
        else: 
            return super()._exists(path=path, location=location)
    # ------------------------------------------------
    
    # Method to create a distant or local directory
    @classmethod
    def _create_dir(cls, path: PurePath, location="local", **kwargs) -> None:
        """
        Creates a directory at `path` :
        - locally if `location` is "local";
        - on VIP if `location` is "vip".

        `kwargs` are passed as keyword arguments to `Path.mkdir()`.
        Returns the VIP or local path of the newly created folder.
        """
        if location == "local": 
            # Check input type
            path=Path(path)
            # Check the parent is a directory
            assert path.parent.is_dir(),\
                f"Cannot create subdirectories in '{path.parent}': not a folder"
            # Create the new directory with additional keyword arguments
            path.mkdir(**kwargs)
        else: 
            return super()._create_dir(path=path, location=location, **kwargs)
    # ------------------------------------------------

    # Path to delete during session finish
    def _path_to_delete(self) -> dict:
        """Returns the folders to delete during session finish, with appropriate location."""
        return {
            self._vip_dir: "vip"
        }
    
    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.2/A.5) Upload (/download) data on (/from) VIP Servers
    ###########################################################

    # Function to upload all files from a local directory
    @classmethod
    def _upload_dir(cls, local_path: Path, vip_path: PurePosixPath) -> list:
        """
        Uploads all files in `local_path` to `vip_path` (if needed).
        Displays what it does if _VERBOSE is set to True.
        Returns a list of files which failed to be uploaded on VIP.
        """
        # Scan the local directory
        assert cls._exists(local_path), f"{local_path} does not exist."
        # First display
        if cls._VERBOSE: print(f"Cloning: {local_path} ", end="... ")
        # Look for subdirectories
        subdirs = [
            elem for elem in local_path.iterdir() 
            if elem.is_dir()
        ]
        # Scan the distant directory and look for files to upload
        if cls._mkdirs(vip_path, location="vip"):
            # The distant directory did not exist before call
            # -> upload all the data (no scan to save time)
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file()
            ]
            if cls._VERBOSE:
                print("(Created on VIP)")
                if files_to_upload:
                    print(f"\t{len(files_to_upload)} files to upload.")
        else: # The distant directory already exists
            # Scan it to check if there are more files to upload
            vip_filenames = {
                PurePosixPath(element["path"]).name
                for element in vip.list_elements(str(vip_path))
            }
            # Get the files to upload
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file() and (elem.name not in vip_filenames)
            ]
            # Update the display
            if cls._VERBOSE:
                if files_to_upload: 
                    print(f"\n\tVIP clone already exists and will be updated with {len(files_to_upload)} files.")
                else:
                    print("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_upload :
            nFile+=1
            # Display the current file
            if cls._VERBOSE:
                size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
                print(f"\t[{nFile}/{len(files_to_upload)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if cls._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                if cls._VERBOSE: print("Done.")
            else:
                # Update display
                if cls._VERBOSE: print(f"\n(!) Something went wrong during the upload.")
                # Update missing files
                failures.append(str(local_file))
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += cls._upload_dir(
                local_path=subdir,
                vip_path=vip_path/subdir.name
            )
        # Return the list of failures
        return failures
    # ------------------------------------------------

    # Function to upload a single file on VIP
    @classmethod
    def _upload_file(cls, local_path: Path, vip_path: PurePosixPath) -> bool:
        """
        Uploads a single file in `local_path` to `vip_path`.
        Returns a success flag.
        """
        # Check
        assert local_path.exists(), f"{local_path} does not exist."
        # Upload
        done = vip.upload(str(local_path), str(vip_path))
        # Return
        return done
    # ------------------------------------------------   

    # Function to download a single file from VIP
    @classmethod
    def _download_file(cls, vip_path: PurePosixPath, local_path: Path) -> bool:
        """
        Downloads a single file in `vip_path` to `local_path`.
        Returns a success flag.
        """
        # Download (file existence is not checked to save time)
        return vip.download(str(vip_path), str(local_path))
    # ------------------------------------------------    

    # Method to extract content from a tarball
    @classmethod
    def _extract_tarball(cls, local_file: Path):
        """
        Replaces tarball `local_file` by a directory with the same name 
        and extracted content.
        Returns success flag.
        """
        # Rename current archive
        archive = local_file.parent / "tmp.tgz"
        os.rename(local_file, archive) # pathlib version does not work it in Python 3.7
        # Create a new directory to store archive content
        cls._mkdirs(local_file, location="local")
        # Extract archive content
        try:
            with tarfile.open(archive) as tgz:
                tgz.extractall(path=local_file)
            success = True
        except:
            success = False
        # Deal with the temporary archive
        if success:
            # Remove the archive
            os.remove(archive)
        else:
            # Rename the archive
            os.rename(archive, local_file)
        # Return the flag
        return success
    # ------------------------------------------------
    
    ###################################
    # ($C) Backup / Resume Session Data 
    ###################################

    # ($C.1) Save session properties in a JSON file
    def _save_session(self, session_data:dict) -> bool:
        """
        Saves `session_data` as a JSON file in the LOCAL output directory.
        Returns a success flag.
        Also displays this path is `_VERBOSE` is True.
        """
        # Return if the local input directory is not defined
        if not self._is_defined("_local_output_dir"):
            return False
        # Default location
        file = self._local_output_dir / self._SAVE_FILE
        # Make the output directory if it does not exist
        is_new = self._mkdirs(file.parent, location="local")
        # Save the data in JSON format
        with file.open("w") as outfile:
            json.dump(session_data, outfile, indent=4)
        # Display
        if self._VERBOSE:
            if is_new: print(f"\nSession properties are saved in:\n\t{file}\n")
            else: print(f"\nSession properties have been saved.")
        return True
    # ------------------------------------------------

    # ($C.2) Load session properties from a JSON file
    def _load_session(self) -> dict:
        """
        Loads session properties from the local output directory.
        Returns properties as a dictionary. 
        Displays success message unless `_VERBOSE` is False.
        """
        # Return if the local input directory is not defined
        if not self._is_defined("_local_output_dir"):
            return None
        # Check existence of data from a previous session
        file = self._local_output_dir / self._SAVE_FILE
        if not file.is_file():
            return None
        # Load the JSON file
        with file.open() as fid:
            session_data = json.load(fid)
        # Update the local output directory
        session_data["local_output_dir"] = file.parent
        # Display success & return
        if self._VERBOSE:
            print("Session properties were loaded from:\n\t", self._local_output_dir)
        return session_data
    # ------------------------------------------------

    # Overwrite _update_workflows() to automatically save the session 
    # once worflows are updated
    def _update_workflows(self, save_session=True) -> None:
        """
        Updates the status of each workflow in the inventory. 
        Saves the session silently unless `save_session` is False.
        """
        # Update the workflow
        super()._update_workflows()
        # Save the session silently
        if save_session:

            self._VERBOSE = False
            self._save_session(display=False)
    # ------------------------------------------------

    ######################################
    # ($D) Make VipSession user-friendly
    ######################################
    
    # ($D.1) Hide VIP paths to the user and allow multi-OS use (Unix, Windows)
    ###########################################################################

    # Write the VIP and local paths relatively to the input directories.
    # This enables portability between sessions and terminals.
    def _parse_input_settings(self, input_settings) -> dict:
        """
        Parses the input settings, i.e.:
        - Converts all input paths (local or VIP) to PathLib objects 
            and write them relatively to their input directory ;
        - Leave the other parameters untouched.

        Prerequisites: 
        - `input_settings` must contain only strings or os.PathLike objects (incl. PathLib), or lists of both types. 
            (Otherwise: Raises TypeError).
        """
        # Function to convert local / VIP path to relative paths
        def parse_value(input):
            """
            When possible, writes `input` relatively to the input directories (local or VIP), *if possible*.
            `input` can be a single string / os.PathLike object or a list of both types.
            """
            # Case: multiple inputs
            if isinstance(input, list):
                return [ parse_value(element) for element in input ]
            # Case: single input, string or path-like
            elif isinstance(input, (str, os.PathLike)):
                # Case: VIP path
                if str(input).startswith(self._SERVER_PATH_PREFIX): # PurePath.is_relative_to() is unavailable for Python <3.9
                    if self._is_defined('_vip_input_dir'): 
                        input_dir = self._vip_input_dir
                        input_path = PurePosixPath(input)
                    else: # Return input if `_vip_input_dir` is unset
                        return input
                # Case: local path or any other input
                else:     
                    if self._is_defined('_local_input_dir'): 
                        # We must use absolute paths to find the relative parts
                        input_dir = self._local_input_dir.resolve()
                        input_path = Path(input).resolve()
                    else: # Return input if `_local_input_dir` is unset
                        return input
                # Return the part of `input_path` that is relative to `input_dir` (if relevant)
                try: # PurePath.is_relative_to() is unavailable for Python <3.9
                    return input_path.relative_to(input_dir)
                except ValueError:
                    # This is the case when no relative part could be found
                    return input
            # Case not string or path-like: raise an error
            else:
                # (this case may be updated in the future)
                raise TypeError(f"`input_settings` can contain only strings or os.PathLike objects"
                                +" (including PathLib objects), or lists of both types.")
        # -- End of parse_value() --
        # Return the parsed value of each parameter
        return {
            key: parse_value(value)
            for key, value in input_settings.items()
        }
    # ------------------------------------------------

    # Get the input settings after they are parsed
    def _get_input_settings(self, target="vip") -> dict:
        """
        Fits `self._input_settings` to `target`, i.e. write the input paths relatively to `target`.
        Returns the modified settings.

        Prerequisites:
        - input_settings is defined and contains only strings, PathLib objects or lists of both types
        - input directories are defined depending on `target`
        """
        def get_input(value, target) -> str:
            """
            If `value` is a path, binds this path to `target`.
            Value can be a single input or a list of inputs.
            """
            # Case: multiple inputs
            if isinstance(value, list):
                return [ get_input(element, target) for element in value ]
            # Case : not a path
            elif not isinstance(value, PurePath):
                return value
            # Case : Path relative to any `input_dir` => Cannot be distinguished from other parameters when parsing
            # Case : VIP path
            elif (target == "vip") and self._is_defined("_vip_input_dir"):
                return str(self._vip_input_dir / value) 
            # Case: local path
            elif (target == "local") and self._is_defined("_local_input_dir"):
                return str(self._local_input_dir / value)
            else: 
                # for data inspection (this should not happen to users)
                return str(value)
        # -----------------------
        # Raise an error if `target` cannot be parsed
        if target not in ("vip", "local"):
            raise NotImplementedError(f"Unknown target: {target}")
        # Browse input settings
        return {
            key: get_input(value, target)
            for key, value in self._input_settings.items()
        }
    # ------------------------------------------------

    def _update_input_settings(self) -> None:
        """
        Parses self._input_settings relatively to the input directories.
        This method does nothing if `input_settings` is unset.
        """
        if self._is_defined('_input_settings'):
            self._input_settings = self._parse_input_settings(self._input_settings)
    # ------------------------------------------------

    def _check_input_settings(self, input_settings: dict={}, location="") -> None:
        """
        Checks `input_settings` with respect to pipeline descriptor. 
        
        `location` refers to the storage infrastructure where input files should be found (e.g., VIP).
        Use the same nomenclature as defined in self._exists() (e.g., `location="vip"`).
        
        Detailed output:
            - Prints warnings unless `_VERBOSE` is False.
            - Raises AttributeError if the input settings or pipeline identifier were not found.
            - Raises TypeError if some input parameter is missing.
            - Raises ValueError if some input value does not the fit with the pipeline definition.
            - Raises FileNotFoundError some input file does not exist. 
            - Raises RuntimeError if communication failed with VIP servers.
        """
        # If input_settings are provided, parse them 
        if input_settings:
            input_settings = self._parse_input_settings(input_settings)
        # If input_settings are defined, get them
        elif self._is_defined("_input_settings"):
            input_settings = self._get_input_settings(target=location)
        # Check the input settings
        return super()._check_input_settings(input_settings, location)
    # ------------------------------------------------

    # Function to convert a VIP path to local output directory
    def _get_local_output_path(self, vip_output_path: PurePosixPath) -> Path:
        """
        Converts a VIP path in local format for VIP outputs. 
        `vip_output_path` can be a single string or a list of strings.
        Assumes `vip_output_path` belongs to to self._vip_output_dir.
        """
        # Replace `vip_output_dir`" by `local_output_dir` in the path
        new = self._local_output_dir / vip_output_path.relative_to(self._vip_output_dir)
        # Replace forbidden characters by '-' if current OS is windows
        invalid_for_windows = '<>:"?* '
        new_str = str(new.resolve())
        if isinstance(new, WindowsPath):
            for char in invalid_for_windows: new_str = new_str.replace(char, '-')
        # Return
        return Path(new_str).resolve()
    # ------------------------------------------------

#######################################################

if __name__=="__main__":
    pass