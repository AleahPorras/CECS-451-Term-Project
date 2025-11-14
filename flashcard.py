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


    
    file_name = input("Please enter a file name: ")
    print("")
    
    try:
        gained_pdf = f'data/{file_name}.pdf'
        file_text = get_pdf_text(gained_pdf)
    except FileNotFoundError:
        print("You entered an invalid file name, using CECS_478_Slides.pdf in place (will fix this later) \n") 
        file_name ='CECS_478_Slides'
        gained_pdf = f'data/{file_name}.pdf'
        file_text = get_pdf_text(gained_pdf)

    
    load_dotenv()
    
    get_api_key = os.getenv("GEMINI_API_KEY")
    if get_api_key == None: 
        print("Exiting...")
        sys.exit("No API key found with that name")
    genai.configure(api_key=get_api_key)

    #getting text from website
    # gained_pdf = find_pdf()
  
    num_flashcards = 6
    # used_text = url_prosessing()
    ## Checks if there was an erros in the url processing, if error system exit so it doesnt feed None to Gemini
   
    
    # file_path = pathlib.Path(gained_pdf)
    pdf_content = "\n".join(file_text)
    # file = genai.upload_file(path=file_path,)

    # what would client be? model? *shrug* oh she cooking🔥 😵‍💫 *gulp*,


    # #configuring using api key, api key stored as env variable
   

  
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config = genai.GenerationConfig(
       
        temperature= 0.2,
        top_p = 0.9,
        top_k = 40,
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
    
    print("Working on flashcards...\n")
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
    
    response = model.generate_content(flashcard_instruction)
# ______________________________________Output to the terminal______________________________________
    
    info = response.text.strip()
    searching_for_symbols = re.search(r"```json\s*(\{.*?\})\s*```", info, re.DOTALL)
    
    wanted_text = ""
    if searching_for_symbols:
        wanted_text = searching_for_symbols.group(1) 
    else:
        if info.startswith("{"):
                wanted_text = info
        else:
            print("Google JSON Error")
            print(info)
            print("Exiting...")
            sys.exit("AI did not return valid JSON.")

    
    try:
        json_data = json.loads(wanted_text)
    except json.JSONDecodeError as e:
        print(f"JSON Error")
        print(wanted_text)
        print("Exiting...")
        sys.exit("invalid")

    print(" ")

    
    questions = json_data["questions"]
    answers = json_data["answers"]
    references = json_data["references"]
    
    if len(questions) != len(answers):
        print("Exiting...")
        sys.exit("Mismatch between number of questions and numbers. Google Gemini did not match number of questions with number of answers")

    for i in range(len(questions)):
        print(f"---------- Flashcard {i+1} ----------")
        print(f"Question: {questions[i]}")
        print(f"Answer: {answers[i]}")
        print("-"*50 + "\n")
    
    #for testing and debugging
    for_json_output = json.dumps(json_data, indent=2)

    print(f"------------------------------ *Office Hours Section* ------------------------------")
    any_problems = input("How did studying go? Any flashcards you struggled with? (no/yes): ")
    while any_problems != 'no' and any_problems != 'yes':
        print("ERROR: you didn't answer with yes or no (please enter in lower case and as show)")
        any_problems = input("How did studying go? Any flashcards you struggled with? (no/yes): ")

    if any_problems == 'yes':
        try:
            problem_flashcards = input("Enter the flashcard numbers you struggled with: ")
            problem_numbers = [int(n.strip()) for n in problem_flashcards.split(',') if n.strip().isdigit()]
           
            
            while len(problem_numbers) == 0:
                problem_flashcards = input("Error, please enter flashcard numbers you struggled with: ")
                problem_numbers = [int(n.strip()) for n in problem_flashcards.split(',') if n.strip().isdigit()]
                
              

        except ValueError:
            print("Exiting...")
            sys.exit("You didn't enter any flashcard numbers or your numbers weren't processed correctly.")
        print(" ")
        hard_flashcards = []
        for i in range(len(questions)):
            if (i+1)  in problem_numbers:
               hard_flashcards.append(questions[i])
        
        while len(hard_flashcards) == 0:
             try:
                print("You entered a flashcard number that doesn't exist or is out of range...")
                problem_flashcards = input("Enter the flashcard numbers you struggled with: ")
                problem_numbers = []
                for problem in problem_flashcards.split(','):
                    if problem.strip().isdigit():
                        problem_num = int(problem.strip()) 
                        problem_numbers.append(problem_num)
           
            
                while len(problem_numbers) == 0:
                    problem_flashcards = input("You didn't enter integers, please enter flashcard integer number you struggled with: ")
                    problem_numbers = [int(n.strip()) for n in problem_flashcards.split(',') if n.strip().isdigit()]
             except ValueError:
                print("Exiting...")
                sys.exit("You didn't enter any flashcard numbers or your numbers weren't processed correctly.")
             for i in range(len(questions)):
                if (i+1)  in problem_numbers:
                    hard_flashcards.append(questions[i])


        num_questions = len(hard_flashcards)
        hard_flashcard_text = str(hard_flashcards)
        print(" ")
        print("Working on office hours questions...\n")
        office_hours_instruction = [f"Please generate exactly {num_questions} questions or examples to have the professor  walk through about challenging material."
            f"Use the provied list of questions that the the user had an issue with "
            f"Use the questions in {hard_flashcard_text} do not just provided questions that are the flashcard questions"
            f"reread the powerpoint and match up where the user is confused from the text in {pdf_content}"
            f"1. questions: generate {num_questions} go through and look at the material the questions they struggled with were on and generate questions for a professor"
             "You must not and cannot use any outside information other than the text given and questions. This is one office hours question question per hard_flashcard_text question"
             "Make sure this is all given in TRUE JSON format only so it can be printed separately easily later . Make sure questions are in json format."
                "With the JSON format, I want to be able to load into json and then print out the questions separately."
            ]
        
        response = model.generate_content(office_hours_instruction)
        info = response.text.strip()
        match = re.search(r"```json\s*(\{.*?\})\s*```", info, re.DOTALL)
        
        needed = ""
        if match:
            needed = match.group(1) 
        else:
            if info.startswith("{"):
                    needed = info
            else:
                print("Google JSON Error")
                print(info)
                print("Exiting...")
                sys.exit("AI did not return valid JSON.")

        try:
            json_data = json.loads(needed)
        except json.JSONDecodeError as e:
            print(f"JSON Error")
            print(needed)
            print("Exiting...")
            sys.exit("invalid")

        print(" ")
        print(" ")
        print(" ")

        all_questions = json_data["questions"]
        questions = all_questions[:num_questions]
        # print(f"Questions: {questions}\n")
        for i in range(len(questions)):
            print(f"---------- Office Hours Question {i+1} ----------")
            print(f"Question: {questions[i]}")
            print("-"*50 + "\n")
        

    else: 
        print("Cool! Program will exit now!")


main()
