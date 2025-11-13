# from google import genai
from dotenv import load_dotenv
import sys ## BUILT IN
import os ## BUILT IN
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import google.generativeai as genai
from google.generativeai import types
import json ## BUILT IN
import argparse ## BUILT IN
import pathlib
import httpx
import PyPDF2


### For eventual website, nothing too crazy, basic html and css ###
# from flask import Flask
# import pathlib

# # creates an instance of the Flask class
# app = Flask(__name__)

# # this decorator tells Flask what URL needs to trigger the function
# @app.route('/')
# # returns the content we want to display in the browser
# def hello_world():
#     return '<p>Hello, World!</p>'

# @app.route('/testing')
# def testing():
#     return '<h1>TESTING</h1>'

### Simple Testing ###
# load_dotenv()
# client = genai.Client(api_key=load_dotenv("GEMINI_API_KEY"))
# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Explain how AI works in a few words",
# )
# print(response.text)


##______________________________________Finding the URL argument______________________________________
def get_pdf_text(pdf_file):
    with open(pdf_file,'rb') as pdf:
        read = PyPDF2.PdfReader(pdf, strict=False)
        pdf_text = []
        for item in read.pages:
            text = item.extract_text()
            pdf_text.append(text)
        return pdf_text

##______________________________________Main Program, LLM communication and output______________________________________

def main():
    load_dotenv()
    get_api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=get_api_key)

    #getting text from website
    # gained_pdf = find_pdf()
    gained_pdf = 'data/CECS_478_Slides.pdf'
    num_flashcards = 6
    # used_text = url_prosessing()
    ## Checks if there was an erros in the url processing, if error system exit so it doesnt feed None to Gemini
    if gained_pdf == None:
        sys.exit("Check the above error, something went wrong")
    
    # file_path = pathlib.Path(gained_pdf)
    file_text = get_pdf_text(gained_pdf)
    # file = genai.upload_file(path=file_path,)

    # what would client be? model? *shrug* oh she cooking🔥 😵‍💫 *gulp*,


    #configuring using api key, api key stored as env variable
    load_dotenv()

    #spesifying model and other requirments/ restrictions
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config = genai.GenerationConfig(
        # contents = file,
        temperature= 0.2,
        top_p = 0.9,
        top_k = 40,
        max_output_tokens= 8192) , system_instruction= "You are an expert-level educational AI Flashcard card generator that sumirizes text, in question and answer format."
                                                      "Format of JSON is questions are in order and answers are in order so that if you turned it into a list it would be indexable so answer[0] would be the answer to question[0]"
                                                      "You are only able to use the provided pdf, pdf images, and pdf text, nothing else."
                                                      "Generate how may questions by using what the user provided for num_flashcards "
                                                      "You must not and cannot use any outside information other than the text given."
                                                      "Output will be in json format that can be acessed through questions and outputs."
    )

##______________________________________Communication with google gemini______________________________________
    ##Prompt Gemini will use
    instruction = [f"Please generate exactly {num_flashcards} flashcards from the provided file."
    f"Use the the url provided by user named file"
        f"Use the text and images in {file_text}, assume anything on the pdf is fair game"
        f"Generate {num_flashcards} of flashcards ONLY"
        #"Dont include any other subsections, a single paragraph for all types of websites not just articles"
        f"1. questions: generate {num_flashcards} mostly a question that are main points of the slides and a few otheer questions"
        f"2. answers: generate an answer to each generated question using the information provided in the pdf should match order of generated questions"
        "3. references: list refrences used (you should only be)"
        "Do not repeat any questions or answers. Each flashcard should focus on a different topic."
        "Questions should be a clear prompt or term."
        "Answers should be the definition or explanation."
        "You must not and cannot use any outside information other than the text given."
        "Make sure this is all given in TRUE JSON format only so it can be printed separately easily later . Make sure questions and answers are in json format."
        "Only 3 sections should exist per flashcard, no more no less."
        "With the JSON format, I want to be able to load into json and then print out the questions and answers separately."]
    
    response = model.generate_content(instruction)
# ______________________________________Output to the terminal______________________________________
    #striping response
    info = response.text.strip()

    ## preparing for json load (learned gemini likes to wrap it which prevents the text being loaded right away"
    needed = info.strip("```")
    needed = needed.strip("```json")
    # needed = info.strip(" \n```json``` \n")

    ## loading the needed data
    json_data = json.loads(needed)
    print(" ")

    ##Storing each definition in its own variable to easily print
    # url = json_data["url"]
    questions = json_data["questions"]
    answers = json_data["answers"]
    references = json_data["references"]

    ## final terminal print
    # print(f"From URL: {url}\n")
    print(f"Questions: {questions}\n")
    print(f"Answers: {answers}\n")
    print(f"References: {references}\n")

    #output in json format
    for_json_output = json.dumps(json_data)
    
    # list_of_questions = list(questions.values())
    # list_of_answers = list(answers.values())

    if len(questions) != len(answers):
        print("Mismatch between number of questions and numbers.")

    for i in range(len(questions)):
        print(f"Question: {questions[i]}")
        print(f"Answer: {answers[i]}")
        
    for_json_output = json.dumps(json_data, indent=2)
    return for_json_output

main()
### For future website, ignore for now
# if __name__ == '__main__':
#     app.run(debug=True)