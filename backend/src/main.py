import sys
from chatbot import ChatBot

def main():
    try:
        chatbot = ChatBot()
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        sys.exit(1)

    print(f"Connected to Azure OpenAI at {chatbot.endpoint}")
    print("Type 'quit' or 'exit' to end the conversation.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("Exiting chatbot. Goodbye!")
                break

            assistant_response = chatbot.chat(user_input)
            print(f"Assistant: {assistant_response}\n")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            break

if __name__ == "__main__":
    main()
