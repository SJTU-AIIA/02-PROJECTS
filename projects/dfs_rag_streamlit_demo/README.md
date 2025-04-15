# Features
This is a streamlit application that allows RAG-based retrieval for LLMs, intended for use in data analysis and document summaries. As of now, it isn't terribly impressive, but it is a great testbed for the applications of RAG-based retrieval techniques and the effectiveness of varying types of vector stores when used in data settings.

### Notes

The tokenizer is downloaded from huggingface. You need one for the chunker in Docling to properly register (unfortunate). It's stored in the folder /tokenizer. Just don't move it and it'd work fine.

Click on run.bat to activate the website. 

Logs are stored in /logs, input files have their root in /input, and database files, loaded_config and loaded_config_metadata are in /database.