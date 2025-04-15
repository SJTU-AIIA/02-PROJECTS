import streamlit as st
import time, os
import logging
import pandas as pd
import asyncio, traceback
from streamlit_file_browser import st_file_browser
from toolsbase import MetadataConfig

MAINPAGE = 0
FILTERPAGE = 1

# When debugging, if you change the code in this page, you can rerun the page with the rerun button.
# However, if you change the code in any of the modules, due to the cache mechanic, you would have to press C to clear cache, and then rerun.
# Alternatively, restart the entire streamlit application.

@st.cache_resource
def load_client():  # Loads the DFSinterface class from the DFSinterface.py file (you can only cache functions as far as I know)
    import DFSinterface
    return DFSinterface
DFSinterface = load_client()

@st.cache_resource
def load_interface(api_key, base_url, chat_model_name, embedding_model_name):
    interface = DFSinterface.Interface(api_key, base_url, chat_model_name, embedding_model_name, logging_level=logging.DEBUG)
    return interface

api_key = os.environ["OPENAI_API_KEY"]
base_url = r'https://api.gptsapi.net/v1'

st.sidebar.title("Options")

default_values = {
    "history": [],  # message history
    "log": [],  # logs
    "awaiting_response": True,  # a flag used when waiting for a response from the model
    "selected_models": ["gpt-4o-mini", "text-embedding-3-small"],  # [chat_model_name, embedding_model_name]
    "in_progress": 0,  # a flag used when the embedding process is in progress, and locks most buttons
    "selected_embed_file": set(),  # the selected files to be embedded
    "message": None,  # a message to be displayed
    "scroll_to_top": False,  # a flag that, when True, scrolls to the top of the page (or attempts to, it's very buggy)
    "delete_prompt_active": False,  # a flag that, when True, activates the delete checkbox
    "dev_mode": False,  # developer mode flag
}

# Initialize session states based on the default values
for key, default_value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

def render_filter_list(interface):
    """
    Renders the metadata filters and their multiselect widgets in the main page.
    """

    all_metadata_dict = {} # a dictionary with all metadata keys and their values
    filtered_metadata_dict = {}
    filter_list = MetadataConfig(interface.loadedconfig.metadata_file)  # all selected metadata filters
    metadata_tag_dict = interface.loadedconfig.read_processed_files()  # all current filenames to metadata dict
    # finds all metadata options from existing files/metadata and add them to all_metadata_dict
    for value in metadata_tag_dict.values(): #key: filename, value: metadata dict
        if value != {} and value != None:
            for metadata_key, metadata_value in value.items():
                if metadata_key == 'ids':
                    continue
                if metadata_key not in all_metadata_dict:
                    all_metadata_dict[metadata_key] = set()
                all_metadata_dict[metadata_key].add(metadata_value)
    # iterates through all metadata keys and renders a multiselect widget for each
    for metadata_key in all_metadata_dict:
        default_list = []
        if metadata_key in filter_list.read():
            list_1 = filter_list.read()[metadata_key]["$in"]
            list_2 = list(all_metadata_dict[metadata_key])
            default_list = list(set(list_1).intersection(list_2))  # finds all metadata filters that are still valid
            if len(default_list) != len(list_1):  # if there are any invalid filters, update the filter list
                new_filter_list = filter_list.read()
                new_filter_list[metadata_key]["$in"] = default_list
                filter_list.write(new_filter_list)
        selected_metadata = st.multiselect(
            f"Query Filter by {metadata_key}",
            options=list(all_metadata_dict[metadata_key]),
            default=default_list, # default is all the filters that exist in the database
            disabled=st.session_state.in_progress
        )
        if len(selected_metadata) > 0:
            filtered_metadata_dict[metadata_key] = {"$in": selected_metadata} # this is the list we pass to the core model
    filter_list.write(filtered_metadata_dict)

def render_sidebar_filter_list(interface):
    """
    Renders the metadata filters and their multiselect widgets in the sidebar.
    """

    all_metadata_dict = {} # a dictionary with all metadata keys and their values
    filtered_metadata_dict = {}
    filter_list = MetadataConfig(interface.loadedconfig.metadata_file)
    metadata_tag_dict = interface.loadedconfig.read_processed_files()
    for key, value in metadata_tag_dict.items(): #key: filename, value: metadata dict
        if value != {} and value != None:
            for metadata_key, metadata_value in value.items():
                if metadata_key == 'ids':
                    continue
                if metadata_key not in all_metadata_dict:
                    all_metadata_dict[metadata_key] = set()
                all_metadata_dict[metadata_key].add(metadata_value)
        
    for metadata_key in all_metadata_dict:
        default_list = []
        if metadata_key in filter_list.read():
            list_1 = filter_list.read()[metadata_key]["$in"]
            list_2 = list(all_metadata_dict[metadata_key])
            default_list = list(set(list_1).intersection(list_2))  # finds all metadata filters that are still valid
            if len(default_list) != len(list_1):  # if there are any invalid filters, update the filter list
                new_filter_list = filter_list.read()
                new_filter_list[metadata_key]["$in"] = default_list
                filter_list.write(new_filter_list)
        selected_metadata = st.sidebar.multiselect(
            f"Query Filter by {metadata_key}",
            options=list(all_metadata_dict[metadata_key]),
            default=default_list, # default is all the filters that exist in the database
            disabled=st.session_state.in_progress
        )
        if len(selected_metadata) > 0:
            filtered_metadata_dict[metadata_key] = {"$in": selected_metadata} # this is the list we pass to the core model
    filter_list.write(filtered_metadata_dict)

def show_logs():
    with st.sidebar.expander("LOGS", expanded=True):  # the logs expander
        if len(st.session_state.log) == 0:
            st.write("Logs Empty.")
        else:
            for i, log in enumerate(reversed(st.session_state.log)):
                if i > 5:
                    break
                st.write(log)

def scroll_to_top():
    time.sleep(1)
    scroll_js = "<script>window.parent.document.querySelector('section.main').scrollTo(0, 0);</script>"
    # print("scrolled")
    st.components.v1.html(scroll_js)  # the idea is it would scroll to the top of the page, but it doesn't work very well

def dev_mode_toggle():
    new_dev_mode = st.sidebar.checkbox("Developer Mode", value=st.session_state.dev_mode)
    if new_dev_mode != st.session_state.dev_mode:
        st.session_state.dev_mode = new_dev_mode
        st.rerun()

async def main_page():  # the page where you do queries
    st.title("Chat Interface")
    # select the two models
    chat_model_name = st.sidebar.selectbox("Chat Model", ["gpt-4o", "gpt-4o-mini"],
                                        index=["gpt-4o", "gpt-4o-mini"].index(st.session_state.selected_models[0]),
                                        disabled=st.session_state.in_progress)
    embedding_model_name = st.sidebar.selectbox("Embedding Model", ["text-embedding-3-small", "text-embedding-3-large"],
                                            index=["text-embedding-3-small", "text-embedding-3-large"].index(st.session_state.selected_models[1]),
                                            disabled=st.session_state.in_progress)
    st.session_state.selected_models = [chat_model_name, embedding_model_name]
    interface = load_interface(api_key, base_url, chat_model_name, embedding_model_name)

    def get_metadata():
        metadata = MetadataConfig(interface.loadedconfig.metadata_file).read()
        if metadata == {}:
            metadata = None
        return metadata

    async def chat(query="Hi!"):  # the chat function
        if query == None:
            query = "Hi!"
        try:
            filter_list = get_metadata()
            response = await interface.get_response(query, metadata=filter_list)
            formatted_response = f"{response[-1].content}"
            additional_info = ""

            additional_info += f"*Tokens: {response[-1].usage_metadata['total_tokens']}↑{response[-1].usage_metadata['input_tokens']}↓{response[-1].usage_metadata['output_tokens']}*"
            return formatted_response, additional_info
        except Exception as e:
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            tb_log = ''.join(tb_str)
            st.session_state.log.append(f"[SYSYEM] Error. Check logs.")
            interface.core_model.logger.error(tb_log)
            return "[SYSTEM] An error occurred when processing the query. Please try again.", ""
    
    render_sidebar_filter_list(interface)

    # render message history
    for i, message in enumerate(st.session_state.history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"][0])
            if message["content"][1] != "":
                # with st.expander("Additional Info"):
                #     st.markdown(message["content"][1])
                st.markdown(message["content"][1])

    # render query chatbox
    if prompt := st.chat_input("Query: ", disabled=st.session_state.in_progress):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.history.append({"role": "user", "content": [prompt, ""]})
        st.session_state.awaiting_response = True

    # if user has submitted message, get response ONLY ONCE (awaiting_response flag toggles off)
    if st.session_state.awaiting_response:
        with st.chat_message("assistant"):
            response, additional_info = await chat(query=prompt)
            st.markdown(response)
            if additional_info != "":
                st.markdown(additional_info)
            st.session_state.history.append({"role": "assistant", "content": [response, additional_info]})
            st.session_state.awaiting_response = False

    if st.sidebar.button("Clear Logs", disabled=st.session_state.in_progress, type="secondary"):
        st.session_state.log = []
    
    if st.sidebar.button("Clear Chat History", disabled=st.session_state.in_progress, type="secondary"):
        st.session_state.history = []

    show_logs()
    dev_mode_toggle()

async def embed_page():  # the page that handles embedding files
    st.title("Database Management")
    chat_model_name = st.sidebar.selectbox("Chat Model", ["gpt-4o", "gpt-4o-mini"],
                                        index=["gpt-4o", "gpt-4o-mini"].index(st.session_state.selected_models[0]),
                                        disabled=st.session_state.in_progress)
    embedding_model_name = st.sidebar.selectbox("Embedding Model", ["text-embedding-3-small", "text-embedding-3-large"],
                                            index=["text-embedding-3-small", "text-embedding-3-large"].index(st.session_state.selected_models[1]),
                                            disabled=st.session_state.in_progress)
    st.session_state.selected_models = [chat_model_name, embedding_model_name]
    
    interface = load_interface(api_key, base_url, chat_model_name, embedding_model_name)

    render_sidebar_filter_list(interface)

    # the database viewing window and deletion prompt    
    with st.expander("Relevant Database / Deleting Files", expanded=st.session_state.delete_prompt_active):
        # filter selection
        show_all = st.checkbox("Show All", value=False)
        dataframe = interface.loadedconfig.get_dataframe()
        if show_all:  # show_all will show all files in the database
            if not dataframe.empty:
                dataframe['year'] = dataframe['year'].astype(str)
                del dataframe['filename']
                dataframe.reset_index(inplace=True)
                dataframe.rename(columns={'index': 'Filename'}, inplace=True)
                dataframe.index += 1
        else:  # else, it only shows the files that are in the filter
            if not dataframe.empty:
                dataframe['year'] = dataframe['year'].astype(str)
                del dataframe['filename']
                dataframe.reset_index(inplace=True)
                dataframe.rename(columns={'index': 'Filename'}, inplace=True)
                dataframe.index += 1

                filter_list = MetadataConfig(interface.loadedconfig.metadata_file)
                for metadata_key in filter_list.read().keys():
                    whitelist = filter_list.read()[metadata_key]["$in"]  # whitelist filter for this metadata tag
                    dataframe = dataframe[dataframe[metadata_key].isin(whitelist)]  # filters out a wave based on the metadata_key in the for loop
        st.markdown(f"**Total Files Loaded**: {len(dataframe)}")
        st.dataframe(dataframe, width=1000)  # renders dataframe
        if st.session_state.delete_prompt_active == False:  # when the user hasn't clicked on the delete button yet
            if st.button("Delete Selected Files", disabled=st.session_state.in_progress):
                st.session_state.delete_prompt_active = True

        if st.session_state.delete_prompt_active:  # when the user has clicked on the button once and is waiting on confirmation
            if st.button("Cancel Deletion", disabled=st.session_state.in_progress):
                st.session_state.delete_prompt_active = False
            confirm_deletion = st.checkbox("Are you sure you want to delete this item?")
            if confirm_deletion:
                return_val = await interface.core_model.delete_from_filter()
                if return_val == -1:
                    st.error("An error occured. Refer to the logs for details.")
                    st.session_state.log.append("An error occured. Refer to the logs for details.")
                else:
                    st.success(f"Successfully deleted {return_val} chunks from database.")
                    st.session_state.log.append(f"Successfully deleted {return_val} chunks from database.")
                st.session_state.delete_prompt_active = False
                st.rerun()
            else:
                st.warning("Please check the box to confirm deletion.")
        if st.session_state.dev_mode:  # big button go boom
            if st.button("DELETE ENTIRE DATABASE", type="primary"):
                interface.core_model.delete_entire_database()
                st.rerun()

    directory_path = r"input"
    base_dir = r""

    st.subheader("Selected Files")  # the selected files to be embedded will be shown in a dataframe
    file_list = list(st.session_state.selected_embed_file)
    index_list = list(range(1, len(file_list)+1))
    data = {
        "Index": index_list,
        "Filename": file_list
    }
    df = pd.DataFrame(data).style.set_table_attributes('style="width: 100%;"') \
                   .set_properties(**{'max-width': '50px'}, subset=['Index'])
    st.dataframe(df, hide_index=True, use_container_width=True)

    year = st.number_input("Year of Creation:", min_value=1900, max_value=2050, step=1, value=2025,
                                   disabled=st.session_state.in_progress)
    file_type = st.text_input("File Type:", disabled=st.session_state.in_progress)

    # load folder integration
    folders = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
    def find_all_files(directory, base_dir): # finds all files in a directory and *its subdirectories*
        file_paths = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                absolute_path = os.path.join(root, file)
                relative_path = os.path.relpath(absolute_path, base_dir)
                file_paths.append(relative_path)
        return file_paths
    
    # the two columns make it so the multiselect and the load folders button appear on the same row
    load_col1, load_col2 = st.columns([4,1], vertical_alignment="bottom")
    with load_col1:
        selected_folders = st.multiselect("Select Folder(s)", folders)
    with load_col2:
        if st.button("Load Folders", type="primary"):
            st.session_state.message = []
            if selected_folders:
                cnt = 0
                for folder in selected_folders:
                    file_path_list = find_all_files(directory_path+"\\"+folder, base_dir)
                    for file_path in file_path_list:
                        base_name, ext = os.path.splitext(file_path)
                        if base_name.endswith("_transposed"):
                            continue
                        if ext.lower() == '.html':
                            if base_name + ".pdf" in file_path_list:
                                continue
                        st.session_state.selected_embed_file.add(file_path)
                        cnt += 1  # a counter for the number of files added
                st.session_state.message.append((f"Folders loaded: {', '.join(selected_folders)}, {cnt} files added.", "success"))
            else:
                st.session_state.message.append(("No folders selected.", "warning"))
            st.rerun()
    if st.session_state.message: # message display is after the rerun in a session_state so both the message and dataframe can update on the same page
        for msg, msg_type in st.session_state.message:
            if msg_type == "success":
                st.success(msg)
            elif msg_type == "warning":
                st.warning(msg)
        st.session_state.message = None

    if st.button("Reset Selection", disabled=st.session_state.in_progress, type="secondary"):
        st.session_state.selected_embed_file = set()
        st.session_state.scroll_to_top = True
        st.rerun()
    if st.session_state.dev_mode:
        if st.button("EMERGENCY RESET", type="primary"):  # this button will stop embedding immediately
            st.session_state.in_progress = 0
            st.session_state.scroll_to_top = True
            st.session_state.selected_embed_file = set()
            st.rerun()
    if st.button("Submit Selected Files", disabled=st.session_state.in_progress, type="primary"):
        if not file_type:
            st.session_state.log.append("Please fill in all fields before submitting.")
            st.error("Please fill in all fields before submitting.")
        if len(st.session_state.selected_embed_file) == 0:
            st.session_state.log.append("No folders or files loaded.")
            st.error("No folders or files loaded.")
        else:
            st.session_state.in_progress = 1
            st.rerun()
    show_logs()
    
    if st.sidebar.button("Clear Logs", disabled=st.session_state.in_progress):
        st.session_state.log = []

    if st.session_state.in_progress:
        filtered_files = []
        # Create a set to hold names of PDF files for quick lookup
        pdf_files = {os.path.splitext(filename)[0] for filename in st.session_state.selected_embed_file if filename.endswith('.pdf')}
        for filename in st.session_state.selected_embed_file:
            # Get the base name without extension
            base_name, ext = os.path.splitext(filename)            
            # Check if the file is transposed
            if base_name.endswith('_transposed'):
                continue            
            # Check if the file is an HTML file and has a corresponding PDF
            if ext.lower() == '.html':
                if base_name in pdf_files:
                    continue            
            # If it passes all checks, add it to the filtered list
            filtered_files.append(filename)

        _ = await interface.insert_files_to_database(filtered_files, metadata={"year": year, "file_type": file_type}, log_results=True)
        st.session_state.in_progress = 0
        st.session_state.selected_embed_file = set()
        st.rerun()
        
    st.markdown("---")
    st.subheader("Loaded Files")
    selected = st.write(st_file_browser(path=directory_path, 
                    show_upload_file=True,
                    show_choose_file=True, 
                    show_delete_file=True, 
                    show_new_folder=True,
                    show_preview=False,
                    show_rename_file=True,))
    if selected:
        st.session_state.selected_embed_file.add(selected["target"]["path"])
    
    if st.session_state.scroll_to_top: # the idea is to scroll to top after the rerun if the state is active - it doesn't really work
        scroll_to_top()
        st.session_state.scroll_to_top = False

    dev_mode_toggle()

async def filter_page(): # you can pick filters here (but all of the sidebars work too and are synced)
    st.title("Filter Settings")
    chat_model_name = st.sidebar.selectbox("Chat Model", ["gpt-4o", "gpt-4o-mini"],
                                        index=["gpt-4o", "gpt-4o-mini"].index(st.session_state.selected_models[0]),
                                        disabled=st.session_state.in_progress)
    embedding_model_name = st.sidebar.selectbox("Embedding Model", ["text-embedding-3-small", "text-embedding-3-large"],
                                            index=["text-embedding-3-small", "text-embedding-3-large"].index(st.session_state.selected_models[1]),
                                            disabled=st.session_state.in_progress)
    st.session_state.selected_models = [chat_model_name, embedding_model_name]
    interface = load_interface(api_key, base_url, chat_model_name, embedding_model_name)
    # filter selection

    render_filter_list(interface)
    st.subheader("Instructions")
    st.markdown("- Select the metadata tags you want to filter by. The tags are based on the metadata of the files in the database."
    "\n- If all the filters are left blank, all files will be included in the filter."
    "\n- The filters will apply immediately.")
    # printing the dataframe
    st.header("Current Database")
    show_all = st.checkbox("Show All", value=False)
    if show_all:
        dataframe = interface.loadedconfig.get_dataframe()
        if not dataframe.empty:
            dataframe['year'] = dataframe['year'].astype(str)
            del dataframe['filename']
            dataframe.reset_index(inplace=True)
            dataframe.rename(columns={'index': 'Filename'}, inplace=True)
            dataframe.index += 1
    else:
        dataframe = interface.loadedconfig.get_dataframe()
        if not dataframe.empty:
            dataframe['year'] = dataframe['year'].astype(str)
            del dataframe['filename']
            dataframe.reset_index(inplace=True)
            dataframe.rename(columns={'index': 'Filename'}, inplace=True)
            dataframe.index += 1

            filter_list = MetadataConfig(interface.loadedconfig.metadata_file)
            for metadata_key in filter_list.read().keys():
                whitelist = filter_list.read()[metadata_key]["$in"]
                dataframe = dataframe[dataframe[metadata_key].isin(whitelist)]
    st.dataframe(dataframe, width=1000)

    show_logs()
    
    if st.sidebar.button("Clear Logs", disabled=st.session_state.in_progress):
        st.session_state.log = []
        
    dev_mode_toggle()

async def file_page():  # you can add files to a specified folder (or none at all) into the working directory
    st.title("File Manager")
    st.header("Upload Files")
    directory_path = os.path.join(os.getcwd(), "input")
    entries = os.listdir(directory_path)
    folders = [entry for entry in entries if os.path.isdir(os.path.join(directory_path, entry))]
    sel_temp = st.selectbox("Select Folder to Upload to", ["<NONE>"]+folders+["<NEW>"], index=0)
    if sel_temp == "<NEW>":
        sel_folder = st.text_input("Enter Folder Name", value="", key="folder_name")
    else:
        sel_folder = sel_temp
    button_press = st.button("Begin Upload", disabled=(sel_folder in ("<NEW>")))
    uploaded_files = st.file_uploader("Upload File", type=["docx", "pdf", "pptx", "ppt", "xlsx", "csv"], accept_multiple_files=True, disabled=(sel_folder in ("<NEW>")))
    if button_press:
        if sel_folder != "<NONE>":
            for file in uploaded_files:
                os.makedirs(f"{directory_path}\\{sel_folder}", exist_ok=True)
                with open(f"{directory_path}\\{sel_folder}\\{file.name}", "wb") as f:
                    f.write(file.getbuffer())
            st.info(f"{len(uploaded_files)} files uploaded.")
        if sel_folder == "<NONE>":
            for file in uploaded_files:
                with open(f"{directory_path}\\{file.name}", "wb") as f:
                    f.write(file.getbuffer())
            st.info(f"{len(uploaded_files)} files uploaded.")
    st.subheader("Instructions")
    st.markdown("- Choose folder to upload to, or create a new folder. <NONE> will put the uploaded files in the root directory."
    "\n- Upload files by selecting the files and clicking the 'Begin Upload' button."
    "\n- A pop up will appear to confirm the upload.")
    st.header("File Browser")
    test = st_file_browser(path=directory_path, 
                    show_upload_file=True,
                    show_choose_file=True, 
                    show_delete_file=True, 
                    show_new_folder=True,
                    show_preview=False,
                    show_rename_file=True,)
    # test
        
    dev_mode_toggle()

def amain_page():
    asyncio.run(main_page())

def afilter_page():
    asyncio.run(filter_page())

def afile_page():
    asyncio.run(file_page())

def aembed_page():
    asyncio.run(embed_page())

main_pg = st.Page(
    amain_page,
    title="Queries",
)

embed_pg = st.Page(
    aembed_page,
    title="Database Management",
)

filter_pg = st.Page(
    afilter_page,
    title="Filter Settings",
)

file_pg = st.Page(
    afile_page,
    title="File Manager",
)

pg = st.navigation([main_pg, embed_pg, filter_pg, file_pg])
pg.run()
