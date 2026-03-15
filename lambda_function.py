import json
import boto3
from botocore.config import Config

# --- 1. TOOL DEFINITIONS ---
TOOLS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Get current weather for a specific location in Kenya.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The town or county, e.g., Kakamega"}
                    },
                    "required": ["location"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "notify_officer",
            "description": "Sends an alert to the local agricultural officer about a pest/disease.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "report": {"type": "string", "description": "Short summary of the farmer's issue"}
                    },
                    "required": ["report"]
                }
            }
        }
    }
]

def process_kilimonova_logic(text, phone, source):
    # Keep the static USSD menu for speed
    if text == "" or text == "0":
        return "Karibu KilimoNova.\n1. Ripoti Wadudu\n2. Hali ya Hewa"
    if text == "1":
        return "Taja zao na dalili (mfano: Mahindi yana matundu)."
    if text == "2":
        return "Taja eneo lako unapotaka kujua hali ya hewa."

    try:
        # --- 2. THE AI AGENT CALL ---
        native_request = {
            "system": [{
                "text": "You are a Kenyan Agri-Agent. Answer in short Swahili. "
                        "If a farmer mentions weather, use get_weather. "
                        "If they report a serious pest/disease, use notify_officer."
            }],
            "messages": [{"role": "user", "content": [{"text": text}]}],
            "toolConfig": {"tools": TOOLS},
            "inferenceConfig": {"maxTokens": 300, "temperature": 0}
        }

        response = client.invoke_model(
            modelId="amazon.nova-micro-v1:0", 
            body=json.dumps(native_request)
        )
        
        response_body = json.loads(response.get('body').read())
        content_blocks = response_body['output']['message']['content']

        # --- 3. THE AGENTIC TOOL HANDLER ---
        for block in content_blocks:
            # Check if Nova wants to use a Tool
            if "toolUse" in block:
                tool_name = block['toolUse']['name']
                tool_input = block['toolUse']['input']
                
                if tool_name == "get_weather":
                    location = tool_input.get('location', 'Kakamega')
                    # Simulated API call result
                    return f"Hali ya hewa {location}: Mvua inatarajiwa jioni. Linda mbolea yako."
                
                if tool_name == "notify_officer":
                    # Here you could trigger an AWS SNS/SMS notification
                    print(f"ALERT: Officer notified for {phone} about {tool_input['report']}")
                    return "Tumemjulisha afisa wa kilimo. Atakupigia kwa nambari hii hivi karibuni."

            # If Nova just returns plain text
            if "text" in block:
                return block['text']

        return "Samahani, sijakuelewa vizuri. Jaribu tena."

    except Exception as e:
        print(f"AGENT_ERROR: {str(e)}")
        return "Huduma ina tatizo kwa sasa. Jaribu baadaye."
