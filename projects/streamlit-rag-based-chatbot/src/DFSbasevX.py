from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langgraph.graph import START, END, StateGraph, MessagesState
from transformers import AutoTokenizer
from docling.chunking import HybridChunker
import json, logging, pymupdf4llm, markdown
from logging.handlers import RotatingFileHandler
import pandas as pd
import numpy as np
import math, time, os
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.graph import END
from langgraph.checkpoint.memory import MemorySaver
from toolsbase import *
import asyncio

class LoadedConfig:
    """
    Saves the processed files in a json file.
    Also saves metadata filters by Interface instance for use in streamlit (or other) applications.
        Acts like a global meta-variable in this case, and is auto-generated (path not specified).
    Both the config_file's keys and the metadata's filenames are the filenames with relative paths, but without extensions.
    Include a __str__ method that returns all processed files and their metadata in a debug format.

    ...

    Attributes
    ----------
    config_file : str
        The path to the json file that contains the processed files. Filename: loaded_configs.json
    metadata_file : str
        The path to the json file that contains the metadata filters. Saved along with the config_file path. Filename: loaded_configs_metadata.json
    
    Methods
    -------
    read_processed_files()
        Returns all processed files and their metadata in a dict from the config file.
    write_processed_file(filename: str, metadata: dict)
        Writes a single new processed file associated with its metadata into the config file.
    check_process_file(filename: str) -> bool
        Checks if a file is in the config file, i.e. if the file has already been processed.
    remove_processed_file(filename: str)
        Removes a processed file from the config file.
    get_dataframe()
        Returns a pandas DataFrame of the processed files and their metadata, aka the read_processed_files dict.
        Indices are the filenames (without extensions) themselves.
    reset_file()
        Deletes the config file (not the metadata file).
        Functionally, it resets the config file to an empty dict.
    """

    def __init__(self, config_dir: str):
        """
        Parameters
        ----------
        config_dir : str
            The directory to the two config files.
        """
        self.config_file = os.path.join(config_dir, "loaded_configs.json")
        self.metadata_file = os.path.join(config_dir, "loaded_configs_metadata.json")

    def __str__(self):
        output = "This database contains: \n"
        processed = self.read_processed_files()
        for filename, metadata in processed.items():
            output += f"  {filename}: {metadata}\n"
        return output

    def read_processed_files(self) -> dict:
        """
        Returns all processed files and their metadata in a dict from the config file.
        If the file doesn't exist, returns an empty dict.
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return data.get('processed_files', {})
        return {}

    def write_processed_file(self, filename: str, metadata: dict) -> None:
        """
        Writes a single new processed file associated with its metadata into the config file.

        Parameters
        ----------
        filename : str
            The name of the file that was processed. Includes relative paths.
        metadata : dict
            The metadata associated with the file.
        """
        processed_files = self.read_processed_files()

        # Use the filename (without extension) as the key and add metadata
        processed_files[os.path.splitext(filename)[0]] = metadata

        with open(self.config_file, 'w') as f:
            json.dump({'processed_files': processed_files}, f, indent=4)

    def check_process_file(self, filename: str) -> bool:
        """
        Checks if a file is in the config file, i.e. if the file has already been processed.
        Uses a robust system that will handle differently styled paths.

        Parameters
        ----------
        filename : str
            The name of the file to check. Includes relative paths.
        """

        for path in self.read_processed_files().keys():
            if os.path.abspath(os.path.normpath(path)) == os.path.abspath(os.path.normpath(filename)):
                return True
        return False

    def remove_processed_file(self, filename: str) -> None:
        """
        Removes a processed file from the config file.

        Parameters
        ----------
        filename : str
            The path of the file to remove.        
        """
        processed_files = self.read_processed_files()

        if self.check_process_file(filename):
            del processed_files[filename]
            with open(self.config_file, 'w') as f:
                json.dump({'processed_files': processed_files}, f, indent=4)
    
    def get_dataframe(self):
        """
        Returns a pandas DataFrame of the processed files and their metadata, aka the read_processed_files dict.
        Indices are the filenames (without extensions) themselves.
        """
        return pd.DataFrame.from_dict(self.read_processed_files(), orient="index")

    def reset_file(self):
        """
        Deletes the config file (not the metadata file).
        Functionally, it resets the config file to an empty dict.
        """
        # delete the config file
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

class LoggerSingleton:
    """A singleton class to provide a single logger instance."""
    
    _instances = {}

    @staticmethod
    def get_logger(name: str, path: str, setlevel: int = logging.DEBUG) -> logging.Logger:
        if name not in LoggerSingleton._instances:
            logger = logging.getLogger(name)
            logger.setLevel(setlevel)

            # Create logs directory if it doesn't exist
            if not os.path.exists(path):
                os.makedirs(path)

            # Set file handler with rotation
            file_handler = RotatingFileHandler(
                os.path.join(path, f"{name}.log"),
                maxBytes=1024 * 1024,
                backupCount=5,
                delay=True,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)

            # Add a duplicate log filter
            class DuplicateLogFilter(logging.Filter):
                def __init__(self):
                    super().__init__()
                    self.last_record = None

                def filter(self, record):
                    current_record = (record.msg, record.created)
                    if self.last_record == current_record:
                        return False
                    self.last_record = current_record
                    return True

            file_handler.addFilter(DuplicateLogFilter())
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)

            # Add the file handler to the logger
            if not logger.hasHandlers():
                logger.addHandler(file_handler)

            LoggerSingleton._instances[name] = logger
        
        return LoggerSingleton._instances[name]

class LoggingBase:
    """
    A class to handle logging operations.

    ...

    Attributes
    ----------
    logger : logging.Logger
        The logger instance. It is a singleton: only one instance of the logger is ever created. This prevents file usage conflicts.
    filename : str
        The path to the log file. It is created in the specified directory with the name of the logger.
        Filename: {name}.log (rotated up to 5 times, as {name}.log.1, {name}.log.2, etc.)

    Methods
    -------
    newline()
        Add a newline to the log file.
    debug(message: str)
        Log a debug message.
    info(message: str)
        Log an info message.
    warning(message: str)
        Log a warning message.
    error(message: str)
        Log an error message.
    critical(message: str)
        Log a critical message.
    """
    def __init__(self, name: str, path: str, setlevel: int = logging.DEBUG):
        """
        Parameters
        ----------
        name : str
            The name of the logger. Used to identify the logger. Usually the class name by convention.
        path : str
            The path to the directory where the log file is stored.
        setlevel : int
            The logging level to set the logger to. Default is DEBUG.
        """
        # Use the singleton logger
        self.logger = LoggerSingleton.get_logger(name, path, setlevel=setlevel)
        self.filename = os.path.join(path, f"{name}.log")
    
    def newline(self):
        """Add a newline to the log file."""
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 40 + " Starting New Log Session " + "=" * 40 + "\n\n")

    def debug(self, message):
        self._log_message(self.logger.debug, message)

    def info(self, message):
        self._log_message(self.logger.info, message)

    def warning(self, message):
        self._log_message(self.logger.warning, message)

    def error(self, message):
        self._log_message(self.logger.error, message)

    def critical(self, message):
        self._log_message(self.logger.critical, message)

    def _log_message(self, log_method, message):
        try:
            log_method(message)
        except Exception as e:
            self.logger.error(f"Error in logging: {e}.")


class CoreModel:
    """
    A class to handle core functionalities: embedding data and queries through Retrieval-Based-Generation (RAG).

    ...

    Attributes
    ----------
    base_url: str
        The base URL for the OpenAI API.
    api_key: str
        The OpenAI API key. 
    chat_model_name: str
        The name of the chat model to use.
    chat_model: ChatOpenAI
        The chat model to use.
    embedding_model: OpenAIEmbeddings
        The embedding model to use.
    database_dir: str
        The directory where the database is stored.
    logger: LoggingBase
        The logger instance.
    database: Chroma
        The database instance.
    loadedconfig: LoadedConfig
        The loaded config instance.
    memory: MemorySaver
        The memory saver instance.
    memory_config: dict
        The configuration for the memory saver.
    chunk_size: int
        The size of each chunk for splitting files. Defaults to 1000. Max Tokens are set to half that size.
    chunk_overlap: int
        The overlap between chunks. Defaults to 200. Used in the RecursiveTextSplitter.
    metadata_filter: dict
        The metadata filter to use for the database. Defaults to none but is updated as a psuedo-global variable by get_response().
    """
    def __init__(self, *, api_key = os.environ["OPENAI_API_KEY"],	
                 base_url = r'https://api.gptsapi.net/v1', 
                 base_dir = os.getcwd(),
                 chat_model_name = "gpt-4o-mini", embedding_model_name = "text-embedding-3-small",
                 logging_level=logging.INFO):
        """
        Parameters
        ----------
        api_key : str
            The OpenAI API key.
        base_url : str
            The OpenAI API base URL.
        base_dir: str
            The base directory for the database and logs. Defaults to where this program itself is located.
        chat_model_name : str
            The name of the chat model to use.
        embedding_model_name : str
            The name of the embedding model to use.
        logging_level : int
            The logging level to set the logger to. Default is INFO.
        """

        database_dir = os.path.join(base_dir, "database")
        logs_dir = os.path.join(base_dir, "logs")

        self.base_url = base_url
        self.api_key = api_key
        self.chat_model_name = chat_model_name
        self.chat_model = ChatOpenAI(model=chat_model_name, api_key=self.api_key, base_url=base_url)
        self.embedding_model = OpenAIEmbeddings(model=embedding_model_name, api_key=self.api_key, base_url=base_url)
        self.database_dir = database_dir
        
        self.logger = LoggingBase(name="CoreModel", path=logs_dir, setlevel=logging_level)
        self.logger.newline()  # sets a divider from previous logs
        self.logger.info("OpenAI Loaded.")

        self.database = Chroma(embedding_function=self.embedding_model, persist_directory=database_dir)
        self.loadedconfig = LoadedConfig(database_dir)

        self.memory = MemorySaver()
        self.memory_config = {"configurable": {"thread_id": self.__class__.__name__}}

        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.metadata_filter = None

        self._generate_graph()

        self.logger.info("Initialization Complete.")
        return

    def _generate_graph(self):
        """
        Generates the graph for the agent to follow.
        """
        
        @tool(response_format="content_and_artifact")
        async def _retrieve(query: str):
            """Retrieve information related to a query."""
            retrieved_docs = await self.database.asimilarity_search(query, k=10, filter=self.metadata_filter)
            serialized = "\n\n".join(
                (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs
        
        all_tools = [_retrieve] + included_tools  # These are all the tools our agent will have access to.
        
        graph_builder = StateGraph(MessagesState)
        tools = ToolNode(all_tools)

        graph_builder.add_node(self._query_or_respond)
        graph_builder.add_node(tools)
        graph_builder.add_node(self._generate)

        graph_builder.set_entry_point("_query_or_respond")
        graph_builder.add_edge("_query_or_respond", "tools")
        graph_builder.add_edge("tools", "_generate")
        graph_builder.add_edge("_generate", END)

        self.graph = graph_builder.compile(checkpointer=self.memory)  # this saves historical messages in memory for the session.

        # agent executor
        self.agent = create_react_agent(self.chat_model, all_tools, checkpointer=self.memory)
        return

    async def _split_file(self, filename, tokenizer_path=r"D:\1. Workflow\1. Projects\2025-2-5, Project, big server go brrrrr\tokenizer") -> list[list]:
        """
        (Async) Splits a file into chunks of text for processing.

        Important Note: Some files (notably xlsx and csv) are transposed before splitting. 
        This technically creates two files.
        For this reason, the function returns a list of lists of strings, where each inner list is a list of chunks from a single file.
        The outer list contains the chunks from all files.
        
        Parameters
        ----------
        filename : str
            The path to the file to split.
        tokenizer_path : str
            The path to the tokenizer to use. Default is the tokenizer in the specified directory.
        """

        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        chunker = HybridChunker(
            tokenizer=tokenizer,
            max_tokens=self.chunk_size//2,
            merge_peers=True,
        )
    
        if filename.split(".")[-1] == "pdf":
            html_filename = os.path.splitext(filename)[0]+".html"
            if not os.path.isfile(html_filename):
                md_text = pymupdf4llm.to_markdown(filename)
                tempHTML = markdown.markdown(md_text)
                with open(html_filename, 'w', encoding="utf-8") as f:
                    f.write(tempHTML)
            filename = html_filename
            process_list = [(filename, False)] # if it's False, use the default processing system
        
        elif filename.split(".")[-1] in ("xlsx", "csv"):
            # read file and swap rows and columns, save into a new file
            if filename.split(".")[-1] == "xlsx":
                df = pd.read_excel(filename)
            else:
                df = pd.read_csv(filename)
            df.T.to_excel(''.join(filename.split(".")[:-1]) + "_transposed.xlsx", header=False)
            process_list = [(filename, True), (''.join(filename.split(".")[:-1]) + "_transposed.xlsx", True)]
            # if it's True, use the proprietary processing system
        
        else:
            process_list = [(filename, False)] # if it's False, use the default processing system

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        output_splits = []
        for file, is_xlsx in process_list:
            if not is_xlsx:
                splits = []
                loader = DoclingLoader(file_path=file, chunker=chunker, export_type=ExportType.MARKDOWN)
                docs = loader.load()
                
                markdown_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on, strip_headers=False
                )
                for doc in docs:
                    md_header_splits = markdown_splitter.split_text(doc.page_content)
                    # Character splitter
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
                    )
                    # Split
                    splits.extend(text_splitter.split_documents(md_header_splits)) 
                new_splits = []
                for document in splits:
                    new_splits.append(document.page_content)  #langchain textsplitters all return Document objects - this converts them to strings
                splits = new_splits

            if is_xlsx:
                splits = []
                if file.split(".")[-1] == "xlsx":
                    df = pd.read_excel(file, index_col=0)
                else:
                    df = pd.read_csv(file, index_col=0)
                formatted_string = ""
                for index, row in df.iterrows():
                    formatted_string = ""
                    for col in df.columns:
                        cell_value = str(row[col])  # Convert cell value to string
                        if cell_value == "":  # Standardize to nan for easier understanding by LLMs
                            cell_value = "nan"
                        # Create a formatted string with row and column headers
                        formatted_string += f"({index},{col}):{cell_value},"
                        
                        # Ensure the formatted string does not exceed max_length
                        if len(formatted_string) > self.chunk_size:
                            splits.append(formatted_string)
                            formatted_string = ""
                    splits.append(formatted_string)
            output_splits.append(splits)
        return output_splits
    
    async def delete_from_filter(self):
        """
        (Async) Deletes all files specified by the filter.
        """

        try:
            raw_metadata_list = MetadataConfig(self.loadedconfig.metadata_file).read()
            file_list = self.loadedconfig.read_processed_files()
            id_list = []
            to_del_file_list = []
            for filename, metadata in file_list.items():
                satisfy_requirements = True
                for key, value in metadata.items(): # test if this item satisfies metadata requirements
                    if key in raw_metadata_list:
                        if metadata[key] not in raw_metadata_list[key]["$in"]:
                            satisfy_requirements = False
                            break
                if not satisfy_requirements:
                    continue
                id_list.extend(metadata["ids"])
                to_del_file_list.append(filename)
            self.logger.info(f"Deleting {len(id_list)} chunks from database and loadedconfig.")
            for i in range(0, len(id_list), 1000):  # Deletes by chunks of 1000 as ChromaDB cannot support deletion of more than 5000 embeddings at once
                try:
                    self.database.delete(id_list[i: i+1000])  # Deleting by chunks is usually faster
                except:
                    self.logger.error(f"Error: an ID within {i}-{i+1000} cannot be located. Performing individual deletions.")
                    for id in id_list[i: i+1000]:  # if the ID check failed, delete them individually
                        try:
                            self.database.delete(id)
                        except:
                            self.logger.warning(f"ID {id} cannot be located (might have just been deleted). Skipping.")
                    self.logger.error(f"Deletion of IDs {i}-{i+1000} complete.")
            for file in to_del_file_list:
                if self.loadedconfig.check_process_file(file):
                    self.loadedconfig.remove_processed_file(file)
                else:
                    self.logger.error(f"File {file} not found in loadedconfig. Skipping.")
            self.logger.info(f"Deleted {len(id_list)} chunks from database and loadedconfig.")
            return len(id_list)
        except Exception as e:
            self.logger.error(f"Error in deletion: {e}.")
            return -1               
                
    def delete_entire_database(self):
        """
        DELETES THE ENTIRE DATABASE AND RESETS IT.

        USE WITH CAUTION. THIS CANNOT BE UNDONE.
        """

        self.loadedconfig.reset_file()
        self.database.delete_collection()
        
        self.database = Chroma(embedding_function=self.embedding_model, persist_directory=self.database_dir)
        self.logger.warning("ALL DATA RESET.")
        return

    async def insert_to_database(self, filename, *, metadata = None):
        """
        (Async) Inserts a file into the database with the corresponding metadata.

        If the file has already been processed, it will be skipped, and a warning will be logged.

        If the file does not exist, an error will be logged.

        Files will be chunked and processed as needed, and metadatas will receive filenames and, for the LoadedConfig object, the generated IDs.
        
        The loadedconfig object will keep track of what has been processed, and serves as a manifest of what's in the database.

        Returns 0 on successful insertion, 1 if the file was already processed, 2 if the file was not found, and -1 if the file contained no text.
        """

        # checks for all premature exits
        if self.loadedconfig.check_process_file(filename):
            self.logger.warning(f"{filename} has already been processed. Skipping.")
            return 1
        elif not os.path.exists(filename):
            self.logger.error(f"File {filename} not found.")
            return 2

        splits_list = await self._split_file(filename)  # note: splits_list is a list of lists of strings (see reasoning in the docstring of _splits_file)

        if metadata:
            metadata["filename"] = os.path.splitext(filename)[0]  # adds the filename to the metadata, as the filename itself can act as a filter

        async def _insert_document(documents, metadata):
            id_list = set() # this stores the IDs. in the event of aadd_texts failures, the same generated IDs will be filtered by the set.

            async def _count_aadd_texts(tasks):
                """Packages the ChromaDB aadd_texts function, and saves its return_val (all generated IDs) to id_list."""
                return_val = await self.database.aadd_texts(texts=tasks, metadatas=[metadata]*len(tasks))
                # note: aadd_texts in this case can take a list of chunked strings (a list of strings)
                id_list.update(return_val)
                return len(return_val)
            
            async def run_task_with_retries(tasks):
                """Run a task with retry logic. Only retry if the previous attempt failed."""
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        result = await _count_aadd_texts(tasks)
                        return result  # Return on success
                    except Exception as e:
                        self.logger.error(f"Caught an exception on attempt {attempt}: {e}.")
                        if attempt == max_attempts:
                            self.logger.critical(f"Task failed after {max_attempts} attempts. Cancelling.")
                            return
                        await asyncio.sleep(20)  # Delay before retry

            async def _run_all_tasks(task_args):
                """Run all tasks concurrently with retries."""
                results = await asyncio.gather(
                    *(run_task_with_retries(task) for task in task_args),
                    return_exceptions=False  # Collect exceptions to handle them easily
                )
                return results

            tasks = []  # temporary variable to store the pending tasks (chunks)
            task_args_list = []  # stores all the tasks to be run
            task_size = min([max([len(documents)//30 + 1, 20]), self.chunk_size//2])  
            # task_size regulates how many chunks are processed per task. The idea is to keep at least 30 tasks, but it will prioritize not having overly long tasks.
            for i in range(len(documents)):
                text = documents[i]
                tasks.append(text)
                if len(tasks) == task_size or i == len(documents) - 1:
                    task_args_list.append(tasks[:])
                    tasks = []
            _ = await _run_all_tasks(task_args_list)
            return 0, list(id_list)  # lists are more useful than sets in this case
        
        # end of _insert_document definition, now continuing the insert_to _database main function
        no_effect = False  # this means the database didn't get inserted with anything
        for i, splits in enumerate(splits_list):  # each splits represent all the chunks from a single file (recall that up to two files can be generated from certain files)
            return_val, id_list = await _insert_document(splits, metadata)  # the _insert_document pulls the weight here, the main function is a wrapper almost
            if len(id_list) > 0:  # indicates the minimum ID list length from all the chunks
                self.logger.info(f"File {filename} ({i+1}/{len(splits_list)}) successfully inserted into database.")
                return_val = 0
            else:
                self.logger.critical(f"No visible text in {filename} ({i+1}/{len(splits_list)}). Database NOT inserted.")
                return_val = -1
                no_effect = True
                while True:
                    try:
                        os.remove(filename)
                        self.logger.critical(f"File {filename} deleted due to null content.")
                        break
                    except:
                        self.logger.critical(f"Delete failed. File {filename} may be in use. Retrying in 5 seconds.")
                        await asyncio.sleep(5)
                if os.path.splitext(filename)[1] == '.pdf':
                    os.remove(os.path.splitext(filename)[0] + ".html")
                    self.logger.critical(f"File {os.path.splitext(filename)[0] + '.html'} deleted due to null content.")
        if not no_effect:
            if metadata:
                metadata["ids"] = id_list  # add the IDs to the metadata for future deletion
            self.loadedconfig.write_processed_file(filename, metadata=metadata)
        return return_val
    
    async def _query_or_respond(self, state: MessagesState):
        """Generates tool call for retrieval or respond."""
        @tool(response_format="content_and_artifact")
        async def _retrieve(query: str):
            """Retrieve information related to a query."""
            retrieved_docs = self.database.asimilarity_search(query, k=10, filter=self.metadata_filter)
            serialized = "\n\n".join(
                (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs
        tools_list = [_retrieve] + included_tools

        llm_with_tools = self.chat_model.bind_tools(tools_list)
        response = await llm_with_tools.ainvoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}
    
    async def _generate(self, state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question, and supplant it with your own knowledge whenever necessary."
            "Retrieved context of tables are stored in this format:"
            "(row header, column header): cell value."
            "Use the provided tools to calculate statistics instead of doing it yourself."
            "If you don't know the answer, say that you don't know."
            "Use as long as a response as you see fit."
            "Use statistical data and numbers whenever possible to back up your claims."
            "Do not use latex formulas when outputting."
            "Only include variance data when analyzing relatively small statistics."
            "Provided monetary data values, unless otherwise specified, are in RMB."
            "Cite all references in the original text verbatim, in the appropriate location in the response."
            "Reponses should be made in Chinese unless otherwise specified."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages
        self.logger.info(prompt)

        # Run
        response = await self.chat_model.ainvoke(prompt)
        return {"messages": [response]}
    
    async def get_response(self, query, metadata = None):
        """
        (Async) Gets a response from the chat model.

        Parameters
        ----------
        query : str
            The query to ask the chat model.
        metadata : dict
            The metadata filter to use for the database. Default is None.
        """
        self.metadata_filter = metadata
        self.logger.debug(f"User submitted query: {query}, metadata: {metadata}")
        result = await self.agent.ainvoke({"messages": [{"role": "user", "content": query}]}, config=self.memory_config)
        return result["messages"]

if __name__ == "__main__":
    core = CoreModel()