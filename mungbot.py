import streamlit as st
import openai
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

username = ""
password= ""
table = ""
host = ""

DATABASE_URL = f"mysql+pymysql://{username}:{password}@{host}/{table}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_food_info(food):
    # print(f"This is the parameter that was put into the function: {food}")
    db = SessionLocal()
    # print(db.query(models.FoodItem).filter(models.FoodItem.name.ilike(f"%{food}%")).first())
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

def execute_sql_command(sql_command):
    """
    Executes an arbitrary SQL command on the database. For debugging.
    WARNING: Use with extreme caution. Directly executing SQL can be risky and lead to SQL injection attacks if not properly sanitized.
    This function should only be used in controlled environments or with trusted input.
    
    :param sql_command: The SQL command to be executed.
    :return: The result of the execution or an error message.
    """
    db = SessionLocal()
    try:
        # Use the session's execute method for arbitrary SQL commands
        result = db.execute(sql_command)
        db.commit()  # Commit the changes to the database
        
        # For SELECT queries, fetch results
        if sql_command.strip().lower().startswith("select"):
            return result.fetchall()
        else:
            return "Command executed successfully."
    except Exception as e:
        db.rollback()  # Rollback in case of error
        return f"An error occurred: {str(e)}"
    finally:
        db.close()

def write_message(message):
    full_response = ""
    # Simulate stream of response with milliseconds delay
    for chunk in message:
        full_response += chunk + ""
        time.sleep(0.03)
        # Add a blinking cursor to simulate typing
        message_placeholder.markdown(full_response + "▌")
    
    message_placeholder.markdown(full_response)

# Custom image for the app icon and the assistant's avatar
company_logo = 'https://media.discordapp.net/attachments/776228323960553494/1220579653048336514/chefmarshall.png?ex=660f7462&is=65fcff62&hm=525117ff881f1853ac95eb1ba90a412fa70921f8b732f2917445bbba8adbd462&=&format=webp&quality=lossless&width=671&height=671'
gif_url = "https://media.discordapp.net/attachments/1202751965088579634/1221297791024894023/IMG_0132.gif?ex=66121133&is=65ff9c33&hm=a4b9391199a99d7b8dd87472476905135fa9a5a3821e80e7dc9600777d4becec&=&width=225&height=300"  # Example GIF URL

# Configure streamlit page
st.set_page_config(
    page_title="MungBot",
    page_icon=company_logo
)

# Initialize chat history if not already initialized
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "system", 
                                     "content": "Hello! I Mung, I am here to answer any of your questions about the SWIFT Itallian Restauraunt."}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == 'assistant':
        with st.chat_message(message["role"], avatar=company_logo):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat logic
if query := st.chat_input("Ask me anything"):
    
    # Add user message to chat history
    # st.session_state.messages.append({"role": "user", "content": query})
    message = {"role": "user", "content": query}
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(query)
        
    # Check for specific keywords in the query
    sensitive_keywords = ["admin", "phone number", "password", "minh"]
    if any(keyword in query.lower() for keyword in sensitive_keywords):
        # Display the GIF without sending the query to the chain
        with st.chat_message("assistant", avatar=company_logo):
            st.image(gif_url, caption="Oops, let's not talk about that here!")
            
        # Add a generic assistant message to chat history to maintain flow
        st.session_state.messages.append({"role": "assistant", "content": "Oops, let's not talk about that here!"})
    else:
        # Process query normally if no sensitive keywords are found
        with st.chat_message("assistant", avatar=company_logo):
            message_placeholder = st.empty()
            # Send user's question to our chain
            # result = st.session_state['chain']({"question": query})
            # response = result['answer']
            st.session_state.messages.append({"role": "user", "content": query})
            messages = [{"role": "user", "content": query}]

        # OpenAI call to process the input
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
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
                },
                {
                    "type": "function",
                    "function": {
                        "name": "execute_sql_command",
                        "description": "Execute a command for a food item from Marshall's Spaghetti Factory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql_command": {
                                    "type": "string",
                                    "description": "SQL Command that they want to run.",
                                }
                            },
                            "required": ["sql_command"],
                        },
                    }
                }
            ],
            tool_choice="auto",
        )

        # print(f"This is the response of the message {response}")

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        # print(f"This is the tool calls: {tool_calls}")

        # If the AI determines a tool should be used, call the get_food_info function
        # Example tool usage detection, replace with actual logic based on AI response
        available_functions = {
            "get_food_info": get_food_info,
            "update_food_info": update_food_info,
            "execute_sql_command": execute_sql_command
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
                write_message(function_response)
            else: 
                function_response = function_to_call(
                food=function_args.get("food_item"),
                price=function_args.get("price")
                )
                write_message(function_response)

            st.session_state.messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            ) 
            
            # Add assistant message to chat history
            # st.session_state.messages.append({"role": "assistant", "content": response})