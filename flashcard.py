from dotenv import load_dotenv
import sys 
import os 
import google.generativeai as genai
import json 
import PyPDF2
import re

"""
    Kristen: Once it prints out the flash cards, 
    we should prompt the user to enter which Flashcard number they had issues with, 
    and then index it based with the questions and feed it back into an API to generate 
    questions for the student to ask the professor based on the flashcards the student got wrong.
"""



##______________________________________stripping the Pdf text______________________________________
def get_pdf_text(pdf_file):
    #opening the file using raw binary mode
    with open(pdf_file,'rb') as pdf:
        #reads the pdf and stores it as an object, strict set to false so it doesn't crash easily 
        read = PyPDF2.PdfReader(pdf, strict=False)
        #empty list for text
        pdf_text = []
        #going through each page and getting the text, then adding that text to the list
        for item in read.pages:
            text = item.extract_text()
            pdf_text.append(text)
        #returning extracted text
        return pdf_text

##______________________________________Main Program, LLM communication and output______________________________________

def main():
    #Giving the user what to expect and an over view of what the system is expecting
    print(f"------------------------------ *Flashcard Generator Section* ------------------------------")
    print("Welcome to your flashcard generator!\n")
    print("File upload information: ")
    print("   - Model currently only takes ONE pdf document and only a pdf document (for now)")
    print("   - Make sure to drag and drop NEW files in the data section")
    print("   - You can use one of these existing files: CECS_478_Slides.pdf, CECS_327_Slides.pdf, CECS_456_Slides.pdf, CECS_451_Slides.pdf")
    print("   - Input will ask for a file name, exclude .pdf from name and must be exactly as it is int he system")
    print("For example file CECS_478_Slides.pdf path should look like data/CECS_478_Slides.pdf or else this will not work!\n")

    print("Office hours questions information: ")
    print("   - will ask you if sudying went well will ask you yes or no")
    print("        * if input no, this will then ask you what flashcards you struggled with")
    print("        * if input yes, the program will exit and not continue ")
    print("   - if you continue, it will then prompt you to enter in the flashcards you struggled with")
    print("   - Enter numbers (integers) of the flas cards you struggled with like 1,2,3,4...")
    print("        * will not except strign values like one,two, three")
    print("        * must make sure you seperate integers with commas inputs like 1 2 3 won't work (unless its just one question)\n")
    print("        * if you enter a flashcard number out of range, it just won't add it to the the quiestions to put into the API")


    #user types in a name of a file in data folder
    file_name = input("Please enter a file name: ")
    print("")
    
    try:
        #gets the full path to that pdf
        gained_pdf = f'data/{file_name}.pdf'
        #feeds that file into our pdf text stripper
        file_text = get_pdf_text(gained_pdf)
    except FileNotFoundError:
        # if the user got here, that means they didn't enter a valid file
        #thats fine, temp using a random file and will run, this keeps the code from breaking and dontinuing on with a demo
        print("You entered an invalid file name, using CECS_478_Slides.pdf in place (will fix this later) \n") 
        file_name ='CECS_478_Slides'
        gained_pdf = f'data/{file_name}.pdf'
        file_text = get_pdf_text(gained_pdf)

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

    #set number of flashcards to be created
    num_flashcards = 6
   
    # making one string for the text provided to hand off to the model
    pdf_content = "\n".join(file_text)
 
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
    print("Working on flashcards...\n")
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
            print("Exiting...")
            sys.exit("AI did not return valid JSON or wasn't found.")

    
    try:
        #loads into json
        json_data = json.loads(wanted_text)
    except json.JSONDecodeError as e:
        # if user gor here this means our inital check didn't catch this
        print(f"{e}")
        print("Exiting...")
        sys.exit("invalid")

    print(" ")

    #storing just questions
    questions = json_data["questions"]
    #storing just answers
    answers = json_data["answers"]

    #means that some where there is a mix up, wither wrong number of questions or wrong number of answers
    if len(questions) != len(answers):
        print("Exiting...")
        sys.exit("Mismatch between number of questions and numbers. Google Gemini did not match number of questions with number of answers")
    
    #goes through how mnay questions were generated and prints ou8t its mathcing answer
    for i in range(len(questions)):
        print(f"---------- Flashcard {i+1} ----------")
        print(f"Question: {questions[i]}")
        print(f"Answer: {answers[i]}")
        print("-"*50 + "\n")
    
    #Office hour questions section
    print(f"------------------------------ *Office Hours Section* ------------------------------")
    #ask the user if they struggled answering any of the questions on the flashcards
    any_problems = input("How did studying go? Any flashcards you struggled with? (no/yes): ")
    #error handling in case they didn't answer yes or no
    while any_problems != 'no' and any_problems != 'yes':
        print("ERROR: you didn't answer with yes or no (please enter in lower case and as show)")
        #re asks the user
        any_problems = input("How did studying go? Any flashcards you struggled with? (no/yes): ")

    #means they had some problems understanding the code
    if any_problems == 'yes':
        try:
            #asks the user which flashcards they had a problem with
            problem_flashcards = input("Enter the flashcard numbers you struggled with: ")
            problem_numbers = []
            #stores each digit in the list 
            for problem in problem_flashcards.split(','):
                    #only grabs a valid digit
                    if problem.strip().isdigit():
                        problem_num = int(problem.strip()) 
                        problem_numbers.append(problem_num)
           
            
            while len(problem_numbers) == 0:
                problem_flashcards = input("Error, please enter flashcard numbers you struggled with: ")
                problem_numbers = []
                for problem in problem_flashcards.split(','):
                    if problem.strip().isdigit():
                        problem_num = int(problem.strip()) 
                        problem_numbers.append(problem_num)
        except ValueError:
            print("Exiting...")
            sys.exit("You didn't enter any flashcard numbers or your numbers weren't processed correctly.")
        print(" ")
        #getting read to fetch those flashcards
        hard_flashcards = []
        #going through each number in the length of questions
        for i in range(len(questions)):
            #checks if that question was one the user struggled with
            if (i+1)  in problem_numbers:
               #appends that to the list
               hard_flashcards.append(questions[i])
        
        #means it didn't find any questions based on what the user entered
        while len(hard_flashcards) == 0:
             try:
                #-------------------------relooping basically same as before----------------------
                print("You entered a flashcard number that doesn't exist or is out of range...")
                problem_flashcards = input("Enter the flashcard numbers you struggled with: ")
                problem_numbers = []
                for problem in problem_flashcards.split(','):
                    if problem.strip().isdigit():
                        problem_num = int(problem.strip()) 
                        problem_numbers.append(problem_num)

              
                while len(problem_numbers) == 0:
                    problem_flashcards = input("You didn't enter integers, please enter flashcard integer number you struggled with: ")
                    problem_numbers = []
                    for problem in problem_flashcards.split(','):
                        if problem.strip().isdigit():
                            problem_num = int(problem.strip()) 
                            problem_numbers.append(problem_num)
             except ValueError:
                print("Exiting...")
                sys.exit("You didn't enter any flashcard numbers or your numbers weren't processed correctly.")
             for i in range(len(questions)):
                if (i+1)  in problem_numbers:
                    hard_flashcards.append(questions[i])

            #----------------------------------end of relooping-----------------------------------
        #gets how many questions for office hours to generate, one per problem flashcard
        num_questions = len(hard_flashcards)
        #turing into a string to feed into API
        hard_flashcard_text = str(hard_flashcards)
        print(" ")
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
                sys.exit("AI did not return valid JSON or wasn't found.")

        try:
            json_data = json.loads(wanted_text)
        except json.JSONDecodeError as e:
             print(f"{e}")
             print("Exiting...")
             sys.exit("invalid")

        #----------------------------------end of repearting code-------------------------------
        print(" ")
        print(" ")
        print(" ")

        #getting the questions created
        all_questions = json_data["questions"]
        #problem where it sometimes skipped the heading so we put this in order to make sure its printing the number of questions needed
        questions = all_questions[:num_questions]
        
        #printing out each question for office hours
        for i in range(len(questions)):
            print(f"---------- Office Hours Question {i+1} ----------")
            print(f"Question: {questions[i]}")
            print("-"*50 + "\n")
        
    #since the user got a good understanding, exits and can be reran if wanted
    else: 
        print("Cool! Program will exit now!")


main()
