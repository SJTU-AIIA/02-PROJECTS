from DFSbasevX import CoreModel
import time, os, asyncio, logging
from colorama import init, Fore, Style

class Interface:
    """
    Interface class for the DFS client. This class is used to interact with the DFS client in the terminal.
    It also serves as a "function augmenting kit" for the base CoreModel class, allowing certain more advanced features.
    In short, it is a wrapper class for the CoreModel class, with additional functionalities.

    Attributes
    ----------
    api_key : str
        The API key for the models.
    base_url : str
        The base URL for the models.
    core_model : CoreModel
        The CoreModel object for the client. It's what truly does the calculations.
    loadedconfig : LoadedConfig
        A mirror of the loadedconfig attribute in the CoreModel object. Saves on code length.

    Methods
    -------
    get_response(query, metadata)
        Get a response from the chat model.
    insert_to_database(file_path, metadata)
        Insert a file into the database.
    insert_files_to_database(files, metadata, log_results)
        Insert a list of files into the database.
    text_based_client()
        A text-based client for bug testing and debugging.
    """

    def __init__(self, api_key, base_url, chat_model_name, embedding_model_name, *, 
                 logging_level=logging.INFO):
        """
        Parameters
        ----------
        api_key : str
            The API key for the models.
        base_url : str
            The base URL for the models.
        chat_model_name : str
            The name of the chat model to use.
        embedding_model_name : str
            The name of the embedding model to use.
        logging_level : int
            The logging level for the DFS client. Default is logging.INFO.
        """
        self.api_key = api_key  # it would be prudent to use a .env file for this, to disable memory sapping
        self.base_url = base_url

        self.core_model = CoreModel(api_key=api_key, base_url=base_url, 
                                    embedding_model_name=embedding_model_name, 
                                    chat_model_name=chat_model_name,
                                    logging_level=logging_level)
        self.loadedconfig = self.core_model.loadedconfig
        return
    
    async def get_response(self, query, metadata):
        """
        (Async) Get a response from the chat model.

        Parameters
        ----------
        query : str
            The query to send to the chat model.
        metadata : dict
            Metadata filter to send to the chat model. Default is an empty dictionary (not recommend, might cause errors).
        """
        if metadata == {}:
            metadata = None # a patch, in theory, it should not be run at all
        response = await self.core_model.get_response(query=query, metadata=metadata)
        # print(metadata)
        return response
    
    async def insert_to_database(self, file_path, metadata={}):
        """
        Insert a file into the database. This function is asynchronous and will return a return code.

        Return code 0: File successfully inserted into database.

        Return code 1: File was already in the database, but no errors occured.

        Return code 2: File was not found in the directory.

        Parameters
        ----------
        file_path : str
            File path to insert into the database.
        metadata : dict
            Metadata to insert with the file. Default is an empty dictionary (not recommend, might cause errors).
        """
        if metadata == {}:
            metadata = None
        return await self.core_model.insert_to_database(file_path, metadata=metadata)
    
    async def insert_files_to_database(self, files, metadata:dict={}, log_results=False):
        """
        Insert a list of files into the database. This function is asynchronous and will return a return code.

        Return code 0: All files successfully inserted into database.
        
        Return code 1: Some files were already in the database, but no errors occured.

        Return code 2: Some files were not found in the directory.

        Parameters
        ----------
        files : list of str
            List of file paths to insert into the database.
        metadata : dict
            Metadata to insert with the files. Default is an empty dictionary (not recommend, might cause errors).
        log_results : bool
            Whether to return the logs of the insertion RESULT (the process is logged regardless). Default is False.
        """
        cnt = 0 # counts progress
        async def _task_insert_file_to_database(index):
            """A helper function to insert a file into the database."""

            self.core_model.logger.debug(f"Initializing loading of file ({index+1}/{len(files)})")
            filename = files[index]
            return_val = await self.insert_to_database(filename, metadata=metadata.copy())
            nonlocal cnt
            cnt += 1
            if return_val == 0:
                self.core_model.logger.info(f"File {index+1}/{len(files)} successfully inserted into database.")
                self.core_model.logger.info(f"Progress: {cnt}/{len(files)}")
            elif return_val == 1:
                self.core_model.logger.warning(f"File {index+1}/{len(files)} already in database. No changes made.")
            elif return_val == 2:
                self.core_model.logger.error(f"File {filename} not found in directory.")
            await asyncio.sleep(0.1)
            
            return return_val
        
        task_list = []
        for i in range(len(files)):
            task_list.append(_task_insert_file_to_database(i))  # build the task list
        return_list = await asyncio.gather(*task_list, return_exceptions=False)  # collect all the return values
        max_return_val = max(return_list)  # more urgent errors return with higher return values
        null_file_counts = return_list.count(-1)
        if log_results:
            # when no empty files
            if max_return_val == 0 and null_file_counts == 0:
                self.core_model.logger.info(f"All {len(files)} files inserted into database.")
            elif max_return_val == 1 and null_file_counts == 0:
                self.core_model.logger.warning("Some files were already in the database, but no errors occured.")
            elif max_return_val == 2 and null_file_counts == 0:
                self.core_model.logger.error("Some files were not found in the directory.")
            # when there are empty files
            elif max_return_val == 0 and null_file_counts > 0:
                self.core_model.logger.warning(f"{len(files)-null_file_counts} files inserted into database. {null_file_counts} empty files deleted.")
            elif max_return_val == 1 and null_file_counts > 0:
                self.core_model.logger.warning(f"{len(files)-null_file_counts} files inserted/already existed. {null_file_counts} empty files deleted.")
            elif max_return_val == 2 and null_file_counts > 0:
                self.core_model.logger.error(f"{len(files)-null_file_counts} files inserted into database. At least {null_file_counts} files empty or not found.")
        return max_return_val

    def text_based_client(self):
        """
        A text-based client for bug testing and debugging.

        Press Enter after each input.
        """

        init(autoreset=True)
        while True:
            user_input = input(f"COMMAND | (e{Fore.RED}x{Style.RESET_ALL}it/{Fore.RED}q{Style.RESET_ALL}uery/{Fore.RED}e{Style.RESET_ALL}mbed/{Fore.RED}c{Style.RESET_ALL}urdb> ")
            if user_input == "exit" or user_input == "x":
                break
            elif user_input == "query" or user_input == "q":
                query = input("QUERY | Enter your query (x to cancel): ")
                if query == "x":
                    continue
                output = self.get_response(query, metadata={})[-1].content
                print(f"QUERY | {self.core_model.chat_model_name}: {output}")
                self.core_model.logger.debug(f"Response: {output}")

            elif user_input == "embed" or user_input == "e":
                cancelFlag = False
                while True:
                    try:
                        file_path = input("EMBED | Enter file path (x to cancel): ")
                        if file_path == "x":
                            cancelFlag = True
                            break
                        assert os.path.exists(file_path)
                        break
                    except:
                        print("EMBED | Error: Invalid file path.")
                if cancelFlag:
                    continue
                return_code = self.core_model.insert_to_database(file_path)
                print(f"EMBED | File successfully inserted into database with return code {return_code}.")
            elif user_input == "curdb" or user_input == "c":
                print("CURDB | ", end='')
                print(self.core_model.loadedconfig)
            else:
                print("COMMAND | Input not recognized. Try again.")
            time.sleep(0.1)

if __name__ == '__main__':
    api_key = os.environ['OPENAI_API_KEY']
    base_url = r'https://api.gptsapi.net/v1'
    # interface = Interface(api_key, base_url, "gpt-4o-mini", "text-embedding-3-large")
    interface = Interface(api_key, base_url, "gpt-4o", "text-embedding-3-small")
    interface.text_based_client()
