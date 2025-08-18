# utils.py

def conv_to_gradio_format(conv_list):
    """Convert internal conversation format to Gradio messages format"""
    messages = []
    for speaker, content in conv_list:
        if speaker == "GM":
            messages.append({"role": "assistant", "content": content})
        elif speaker == "Player":
            messages.append({"role": "user", "content": content})
    return messages

def validate_gm_response(response):
    """Check if GM response has at least 4 numbered options"""
    if not response:
        return False
    count = 0
    for i in range(1, 5):
        if f"{i}." in response or f"{i})" in response:
            count += 1
    return count >= 4
