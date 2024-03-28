import streamlit as st
import openai
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import json

# OpenAI API key setup
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Custom image for the app icon and the assistant's avatar
company_logo = 'https://media.discordapp.net/attachments/776228323960553494/1220579653048336514/chefmarshall.png?ex=660f7462&is=65fcff62&hm=525117ff881f1853ac95eb1ba90a412fa70921f8b732f2917445bbba8adbd462&=&format=webp&quality=lossless&width=671&height=671'

# Configure streamlit page
st.image(company_logo, width=100)  # Display the company logo at the top
st.title("MungBot - Italian Enthusiast")

# Function to fetch information about food items from the database

def get_food_info(food):
    print(f"This is the parameter that was put into the function: {food}")
    db = SessionLocal()
    print(db.query(models.FoodItem).filter(models.FoodItem.name.ilike(f"%{food}%")).first())
    try:
        # Change contains to ilike for case-insensitive search
        food_item = db.query(models.FoodItem).filter(
            models.FoodItem.name.ilike(f"%{food}%")).first()
        if food_item:
            print(f"Our {food_item.name} is Fantastic! It is {food_item.description}, only costs ${food_item.price}!")
            return f"Our {food_item.name} is Fantastic! It is {food_item.description}, only costs ${food_item.price}!"
        else:
            print("I couldn't find any information on that food item.")
            return "I couldn't find any information on that food item."
    finally:
        db.close()


def update_food_info(food, price):
    db = SessionLocal()
    try:
        # Try to find the food item by name (case-insensitive search)
        food_item = db.query(models.FoodItem).filter(
            models.FoodItem.name.ilike(f"%{food}%")).first()

        # If the food item is found, update its price
        if food_item:
            food_item.price = price
            db.commit()  # Commit the changes to the database
            return f"The price of {food_item.name} has been successfully updated to ${food_item.price}."
        else:
            return "Food item not found."
    except Exception as e:
        # In case of any error, return an error message
        return f"An error occurred: {str(e)}"
    finally:
        db.close()


# Initialize chat history if not already initialized
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "system",
                                     "content": "Hello! I am Marshall. I am here to answer any questions you may have about our Italian Restaurant."}]

# Display chat messages from history
for message in st.session_state.messages:
    if message["role"] == 'assistant':
        with st.container():
            st.image(company_logo, width=50)  # Adjust size as needed
            st.write(message["content"])
    else:
        with st.container():
            st.write(f"You: {message['content']}")

# Chat logic
query = st.text_input("Ask me anything about our food items:", key="query")

if st.button("Send"):
    
    if query:  
        # Add user message to chat history
        # st.session_state.messages is the messages equivalent
        st.session_state.messages.append({"role": "user", "content": query})

        update_info = ["update", "please", "ilikeguys"]
        for info in update_info:
            if info in query:
                intent = "update_food_info"
            else:
                intent = "get_food_info"
                
        st.session_state.messages = [message for message in st.session_state.messages if message["role"] not in ["tool"]]

        # OpenAI call to process the input
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_food_info",
                        "description": "Get information about a food item from Marshall's Spaghetti Factory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "food_item": {
                                    "type": "string",
                                    "description": "The item the person is requesting",
                                }
                            },
                            "required": ["food_item"],
                        },
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "update_food_info",
                        "description": "Update information about a food item from Marshall's Spaghetti Factory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "food_item": {
                                    "type": "string",
                                    "description": "The food item the person is requesting",
                                },
                                "price": {
                                    "type": "integer",
                                    "description": "The price of the item that the person is requesting",
                                }
                            },
                            "required": ["food_item"],
                        },
                    }
                }
            ],
            tool_choice="auto",
        )

        # print(f"This is the response of the message {response}")

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        print(f"This is the tool calls: {tool_calls}")

        # If the AI determines a tool should be used, call the get_food_info function
        # Example tool usage detection, replace with actual logic based on AI response
        available_functions = {
            "get_food_info": get_food_info,
            "update_food_info": update_food_info
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            # Here is where we set the function response, we have to pull the parameteres here as well.
            if function_name == "get_food_info": 
                function_response = function_to_call(
                    food=function_args.get("food_item"),
                )
            else: 
                function_response = function_to_call(
                food=function_args.get("food_item"),
                price=function_args.get("price")
            )

            st.session_state.messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

# Display updated chat messages
for message in st.session_state.messages:
    with st.container():
        if message["role"] == 'assistant':
            st.image(company_logo, width=50)
            st.write(message["content"])
        else:
            st.write(f"You: {message['content']}")
