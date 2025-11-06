Run the following commands before running the files

1.pip install spacy (This will download spacy library)

2.python -m spacy download en_core_web_lg

3.python -m spacy download en_core_web_sm

Step 2 and 3 is needed to download the nlp models that are with small and large size dataset

4.pip install pymupdf mammoth beautifulsoup4 

Step 4 is needed for parsing the pdfs, text, docx and html files

5.pip install gradio

Gradio is for the GUI

Now after installing these libraries

run the main.py file

Upload the file and the result will be extracted text, texts marked with issues and recommendations provided
We can also see the number of ambiguous pronouns and missing information provided in SRS document
