### Code incorporated into website form for easier access

import streamlit as st
from dotenv import load_dotenv
import PyPDF2
import google.generativeai as genai
import json
import sys
import os
import re

def get_pdf_text(pdf_file):
    #reads the pdf and stores it as an object, strict set to false so it doesn't crash easily 
    read = PyPDF2.PdfReader(pdf_file, strict=False)
    #empty list for text
    pdf_text = []
    #going through each page and getting the text, then adding that text to the list
    for item in read.pages:
        text = item.extract_text()
        pdf_text.append(text)
    #returning extracted text
    return pdf_text

def generate_flashcards(pdf_text, num_flashcards):
    #laoding enviornment
    load_dotenv()
    
    #retrieving the API key that is stored in an enviornment variable
    get_api_key = os.getenv("GEMINI_API_KEY")
    #coudln't find an API key
    if get_api_key == None: 
        # sytem exists 
        st.write("Exiting...")
        st.error("No API key found with that name")
        st.stop()
    #configuring the model using the api key it got
    genai.configure(api_key=get_api_key)

    pdf_content = "\n".join(pdf_text)

    #defining the model, using low randomnees because we want the AI to focus on the information in the slides
    #more than outside information so that the user gets help with what was gone over in class
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config = genai.GenerationConfig(
       
        temperature= 0.2,
        top_p = 0.9,
        top_k = 40,
        #Some instructions for the model to follow
        max_output_tokens= 8192) , system_instruction= " You are an expert-level educational AI Flashcard card generator that sumirizes text, in question and answer format."
                                                       "Questions are random"
                                                       "Format of JSON is questions are in order and answers are in order so that if you turned it into a list it would be indexable so answer[0] would be the answer to question[0]"
                                                       "JSON has 3 keys named questions (store questions), answers(store matching answers), and references(cite where you got the info)"
                                                       "You are only able to use the provided pdf, pdf images, and pdf text, nothing else."
                                                       "Generate how may questions by using what the user provided for num_flashcards "
                                                       "You must not and cannot use any outside information other than the text given."
                                                       "Output will be in json format that can be acessed through questions and outputs."
                                                       "You will then get a second call, this will be of questions the user struggled with"
                                                    
    )

##______________________________________Communication with google gemini______________________________________
    #letting the user know that their request is being process as it takes a min for the AI to spit out the sflashcards to the user
    # print("Working on flashcards...\n")
    # More specific instructions for flashcard genration, gave it a name so that we can distinguish 
    # What instructions this for
    flashcard_instruction = [
        f"Please generate exactly {num_flashcards} flashcards from the provided file."
        f"Use the the url provided by user named file"
        f"Use the text {pdf_content}, assume anything on the pdf is fair game"
        f"Generate {num_flashcards} of flashcards ONLY"
        f"1. questions: generate {num_flashcards} mostly a question that are main points of the slides and a few otheer questions"
        f"2. answers: generate an answer to each generated question using the information provided in the pdf should match order of generated questions"
        "3. references: list refrences used (you should only be)"
        "Do not repeat any questions or answers. Each flashcard should focus on a different topic."
        "Questions should be a clear prompt or term."
        "Answers should be the definition or explanation."
        "You must not and cannot use any outside information other than the text given."
        "Make sure this is all given in TRUE JSON format only so it can be printed separately easily later . Make sure questions and answers are in json format."
        "Only 3 sections should exist per flashcard, no more no less."
        "With the JSON format, I want to be able to load into json and then print out the questions and answers separately."
        ]
    
    #feeds task prompt into the model
    response = model.generate_content(flashcard_instruction)
# ______________________________________Output to the terminal______________________________________
    
    info = response.text.strip()
    #Looking for the json format and taking what is in side (more effective from the other way I was doing it and avoids capturing something that would mess up prints)
    searching_for_json_object = re.search(r"```json\s*(\{.*?\})\s*```", info, re.DOTALL)
    
    #string place holder
    wanted_text = ""
    #checking if we found json
    if searching_for_json_object:
        #takes that group, without json wrap and puts it into wanted text
        wanted_text = searching_for_json_object.group(1) 
    else:
        #due to AI putting out the output chance that AI might not do the wrapper (doubtful tho lol), lastly checks if there was at least somethin returned that resembles json
        if info.startswith("{"):
                #if found, assigned that to wanted text
                wanted_text = info
        else:
            #means it didn't find the right format, system exits 
            st.write("Exiting...")
            st.error("AI did not return valid JSON or wasn't found.")
            st.stop()

    
    try:
        #loads into json
        json_data = json.loads(wanted_text)
    except json.JSONDecodeError as e:
        # if user gor here this means our inital check didn't catch this
        st.error(f"{e}")
        st.error("Exiting...")
        st.error("Invalid")
        st.stop()

    # print(" ")

    #storing just questions
    questions = json_data["questions"]
    #storing just answers
    answers = json_data["answers"]

    #means that some where there is a mix up, wither wrong number of questions or wrong number of answers
    if len(questions) != len(answers):
        print("Exiting...")
        st.error("Mismatch between number of questions and numbers. Google Gemini did not match number of questions with number of answers")
        st.stop()
    
    return questions, answers

    # #goes through how mnay questions were generated and prints ou8t its mathcing answer
    # for i in range(len(questions)):
    #     print(f"---------- Flashcard {i+1} ----------")
    #     print(f"Question: {questions[i]}")
    #     print(f"Answer: {answers[i]}")
    #     print("-"*50 + "\n")

def generate_office_hour_questions(pdf_text, any_problems):
    #laoding enviornment
    load_dotenv()

    #retrieving the API key that is stored in an enviornment variable
    get_api_key = os.getenv("GEMINI_API_KEY")
    #coudln't find an API key
    if get_api_key == None: 
        # sytem exists 
        print("Exiting...")
        sys.exit("No API key found with that name")
    #configuring the model using the api key it got
    genai.configure(api_key=get_api_key)


    pdf_content = "\n".join(pdf_text)
    #gets how many questions for office hours to generate, one per problem flashcard
    num_questions = len(any_problems)
    #turing into a string to feed into API
    hard_flashcard_text = str(any_problems)
    # print(" ")

    #defining the model, using low randomnees because we want the AI to focus on the information in the slides
    #more than outside information so that the user gets help with what was gone over in class
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config = genai.GenerationConfig(
       
        temperature= 0.2,
        top_p = 0.9,
        top_k = 40,
        #Some instructions for the model to follow
        max_output_tokens= 8192) , system_instruction= " You are an expert-level educational AI Flashcard card generator that sumirizes text, in question and answer format."
                                                       "Questions are random"
                                                       "Format of JSON is questions are in order and answers are in order so that if you turned it into a list it would be indexable so answer[0] would be the answer to question[0]"
                                                       "JSON has 3 keys named questions (store questions), answers(store matching answers), and references(cite where you got the info)"
                                                       "You are only able to use the provided pdf, pdf images, and pdf text, nothing else."
                                                       "Generate how may questions by using what the user provided for num_flashcards "
                                                       "You must not and cannot use any outside information other than the text given."
                                                       "Output will be in json format that can be acessed through questions and outputs."
                                                       "You will then get a second call, this will be of questions the user struggled with"
                                                    
    )

    #telling the user that the AI is working on the Office hours flashcards
    print("Working on office hours questions...\n")
    #instructions for AI for the Office hours task
    office_hours_instruction = [f"Please generate exactly {num_questions} questions or examples to have the professor  walk through about challenging material."
        f"Use the provied list of questions that the the user had an issue with "
        f"Use the questions in {hard_flashcard_text} do not just provided questions that are the flashcard questions"
        f"reread the powerpoint and match up where the user is confused from the text in {pdf_content}"
        f"1. questions: generate {num_questions} go through and look at the material the questions they struggled with were on and generate questions for a professor"
            "You must not and cannot use any outside information other than the text given and questions. This is one office hours question question per hard_flashcard_text question"
            "Make sure this is all given in TRUE JSON format only so it can be printed separately easily later . Make sure questions are in json format."
            "With the JSON format, I want to be able to load into json and then print out the questions separately."
        ]
    
    #feeding into the AI
    response = model.generate_content(office_hours_instruction)
    info = response.text.strip()

    #----------------------------------same json look up as before------------------------
    searching_for_json_object = re.search(r"```json\s*(\{.*?\})\s*```", info, re.DOTALL)
    
    wanted_text = ""
    if searching_for_json_object:
        wanted_text = searching_for_json_object.group(1) 
    else:
        if info.startswith("{"):
                wanted_text = info
        else:
            print("Exiting...")
            st.error("AI did not return valid JSON or wasn't found.")
            st.stop()

    try:
        json_data = json.loads(wanted_text)
    except json.JSONDecodeError as e:
        st.write(f"{e}")
        st.write("Exiting...")
        st.error("invalid")
        st.stop()

    #getting the questions created
    all_questions = json_data["questions"]
    #problem where it sometimes skipped the heading so we put this in order to make sure its printing the number of questions needed
    questions = all_questions[:num_questions]

    return questions

def main():

    st.title("AI Flashcard Generator")

    #user types in a name of a file in data folder
    pdf_text = st.file_uploader("Upload your PDF: ", type = "pdf")
    num_flashcards = st.number_input("How many flashcards would you like to generate?",min_value = 1, value = 5, max_value = 10)
    # print("")

    if st.button("Generate Flashcards"):
        # checks if the pdf is valid
        if pdf_text is not None:
            st.write("File uploaded successfully!")
            print("Reading pdf...") # prints to terminal

            st.write("Working on flashcards...")
            # session_state saves the pdf_text so the data isnt lost whenever a button is clicked
            st.session_state['file_text'] = get_pdf_text(pdf_text)

            #calls the generate_flashcards function
            print("Generating flashcards...") # print to terminal

            # generated flashcards are saved so they can be read later for office hour questions
            st.session_state['questions'], st.session_state['answers'] = generate_flashcards(st.session_state['file_text'], num_flashcards)
            
        else:
            st.error("Upload a file to continue.")    

    # checks if there is data saved in the session state
    if 'questions' in st.session_state:
        # st.session_state['questions'] = 'value'

        # displays the flashcards one by one 
        for i, (q,a) in enumerate(zip(st.session_state['questions'], st.session_state['answers'])):
            with st.expander(f"Flashcard {i+1}"):
                st.write(f"**Question:** {q}")
                with st.expander(f"**Answer**"):
                    st.write(f"{a}")

        print("Finished generating flashcards.")

        ###-------------Office Hour Questions-------------###
            
        st.title("Office Hour Questions")
        any_problems = st.multiselect("How did studying go? Any flashcards you struggled with?", options = st.session_state['questions'])

        if st.button("Generate Office Hour Questions"):
            # checks if a flashcard has been chosen
            if any_problems:
                st.write("Working on questions...")
                print("Generating extra questions...")

                # calls the generate_office_hour_questions
                office_hour_questions = generate_office_hour_questions(st.session_state['file_text'],any_problems)

                # displays the questions
                for i in office_hour_questions:
                    st.write(f"**Question:** {i}")
                
                print("Finished generating questions.") # prints to terminal

                st.write("**Good luck with your studying!**")
            else:
                st.error("Select a flashcard to continue.")


main()