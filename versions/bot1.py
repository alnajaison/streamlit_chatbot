import pandas as pd

# Load the troubleshooting guide CSV
df = pd.read_csv("troubleshooting.csv")

def chatbot():
    print("Welcome to the Troubleshooting Assistant!")
    
    # Step 1: Ask for equipment
    equipment_options = df['Equipment'].unique()
    print("\nWhich equipment are you having issues with?")
    for idx, eq in enumerate(equipment_options, 1):
        print(f"{idx}. {eq}")
    eq_choice = int(input("Enter the number: ")) - 1
    selected_eq = equipment_options[eq_choice]

    # Step 2: Ask for error type
    error_options = df[df['Equipment'] == selected_eq]['ERROR'].unique()
    print(f"\nWhat issue are you facing with {selected_eq}?")
    for idx, err in enumerate(error_options, 1):
        print(f"{idx}. {err}")
    err_choice = int(input("Enter the number: ")) - 1
    selected_error = error_options[err_choice]

    # Step 3: Ask for description
    desc_options = df[(df['Equipment'] == selected_eq) & 
                      (df['ERROR'] == selected_error)]['ERROR DESCRIPTION'].unique()
    print("\nCan you describe the problem more specifically?")
    for idx, desc in enumerate(desc_options, 1):
        print(f"{idx}. {desc}")
    desc_choice = int(input("Enter the number: ")) - 1
    selected_desc = desc_options[desc_choice]

    # Step 4: Show troubleshooting steps
    steps = df[(df['Equipment'] == selected_eq) & 
               (df['ERROR'] == selected_error) & 
               (df['ERROR DESCRIPTION'] == selected_desc)]['ACTION POINTS / TROUBLE SHOOTING'].tolist()
    
    print("\n🔧 Try the following troubleshooting steps:")
    for step in steps:
        print(f"- {step}")

    # Step 5: Ask if resolved
    resolved = input("\nDid that fix the issue? (yes/no): ").strip().lower()
    if resolved == 'yes':
        print(" Glad to help!")
    else:
        # Step 6: Provide final solution
        solution = df[(df['Equipment'] == selected_eq) & 
                      (df['ERROR'] == selected_error) & 
                      (df['ERROR DESCRIPTION'] == selected_desc)]['FINAL SOLUTIONS'].iloc[0]
        print(f" Final Solution: {solution}")

    print("\nType 'exit' to quit or press Enter to try again.")
    if input().strip().lower() in ['exit','bye','quit']:
        chatbot()

# Run the chatbot
chatbot()
