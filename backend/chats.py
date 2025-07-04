from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Chat, Message
from config import Config
import openai
import anthropic
from sqlalchemy import desc

chats_bp = Blueprint('chats', __name__)

# Valid models for chat creation and updates
VALID_MODELS = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307']

# System prompts for different AI providers
OPENAI_SYSTEM_PROMPT = """
You are a helpful AI assistant. Always provide responses in markdown format with proper structure. Use bullet points, numbered lists, and emojis to make your responses engaging and easy to read.

Guidelines:
- Use markdown headers (##, ###) to organize content
- Use bullet points (•) or numbered lists for key information
- Include relevant emojis to enhance readability and engagement
- Keep responses concise but informative
- Use **bold** text for emphasis when appropriate
- Use `code blocks` for technical terms or code snippets
- Structure your responses with clear sections when applicable

Example format:
## 📝 Response Title

• **Key Point 1**: Important information here
• **Key Point 2**: More details with emojis 🎯
• **Key Point 3**: Additional context

### 💡 Tips
1. First tip with emoji
2. Second helpful suggestion
3. Third point for clarity
"""

CLAUDE_SYSTEM_PROMPT = """
You are a knowledgeable and helpful AI assistant. Always format your responses using markdown with clear structure, bullet points, and appropriate emojis to enhance readability and engagement.

Formatting requirements:
- Use markdown headers (##, ###) to organize your response
- Utilize bullet points (•) or numbered lists for key information
- Include relevant emojis throughout your response to make it more engaging
- Keep responses concise yet comprehensive
- Use **bold** formatting for important terms
- Use `code formatting` for technical terms, file names, or code snippets
- Structure responses with logical sections when appropriate

Response structure example:
## 🚀 Main Topic

• **Important Point**: Clear explanation with context 📌
• **Another Key Point**: Additional details with emoji 🔍
• **Final Point**: Conclusion or next steps

### ✨ Additional Information
1. First helpful detail
2. Second useful point
3. Third supporting fact

Always aim to be helpful, accurate, and engaging in your responses.
"""

# Initialize LLM clients
openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) if Config.ANTHROPIC_API_KEY else None

@chats_bp.route('/chats', methods=['GET'])
@login_required
def get_chats():
    try:
        chats = Chat.query.filter_by(user_id=current_user.id).order_by(desc(Chat.updated_at)).all()
        
        return jsonify([chat.to_dict() for chat in chats]), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get chats'}), 500

@chats_bp.route('/chats', methods=['POST'])
@login_required
def create_chat():
    try:
        data = request.get_json()
        
        if not data or not data.get('model'):
            return jsonify({'error': 'Model is required'}), 400
        
        model = data['model']
        title = data.get('title', 'New Chat')
        
        # Validate model
        if model not in VALID_MODELS:
            return jsonify({'error': 'Invalid model selected'}), 400
        
        chat = Chat(
            user_id=current_user.id,
            title=title,
            model=model
        )
        
        db.session.add(chat)
        db.session.commit()
        
        return jsonify(chat.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create chat'}), 500

@chats_bp.route('/chats/<int:chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        
        chat_dict = chat.to_dict()
        chat_dict['messages'] = [message.to_dict() for message in messages]
        return jsonify(chat_dict), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get chat'}), 500

@chats_bp.route('/chats/<int:chat_id>', methods=['PUT'])
@login_required
def update_chat(chat_id):
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            chat.title = data['title']
        
        if 'model' in data:
            if data['model'] in VALID_MODELS:
                chat.model = data['model']
        
        db.session.commit()
        
        return jsonify(chat.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update chat'}), 500

@chats_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({'message': 'Chat deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete chat'}), 500

@chats_bp.route('/chats/<int:chat_id>/messages', methods=['POST'])
@login_required
def send_message(chat_id):
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'error': 'Message content is required'}), 400
        
        content = data['content'].strip()
        
        if len(content) == 0:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Check message limit
        message_count = Message.query.filter_by(chat_id=chat_id).count()
        if message_count >= Config.MAX_MESSAGES_PER_CHAT:
            return jsonify({'error': f'Maximum {Config.MAX_MESSAGES_PER_CHAT} messages per chat exceeded'}), 400
        
        # Add user message
        user_message = Message(
            chat_id=chat_id,
            role='user',
            content=content
        )
        db.session.add(user_message)
        
        # Generate AI response
        try:
            ai_response = generate_ai_response(chat.model, chat_id, content)
            
            # Add AI message
            ai_message = Message(
                chat_id=chat_id,
                role='assistant',
                content=ai_response
            )
            db.session.add(ai_message)
            
            # Update chat title intelligently
            try:
                if message_count == 0:
                    # For the first exchange, always generate LLM summary from the conversation
                    # This ensures even the first title is meaningful and context-aware
                    chat.title = generate_chat_title_summary(chat_id, chat.model)
                elif message_count % 4 == 1:
                    # Update title every 4 messages to keep it relevant as conversation evolves
                    chat.title = generate_chat_title_summary(chat_id, chat.model)
                # Otherwise, keep existing title
            except Exception as e:
                # If LLM summarization fails, fallback to traditional method
                chat.title = content[:50] + ('...' if len(content) > 50 else '')
            
            db.session.commit()
            
            return jsonify({
                'user_message': user_message.to_dict(),
                'ai_message': ai_message.to_dict()
            }), 200
            
        except Exception as ai_error:
            db.session.rollback()
            error_message = str(ai_error)
            if 'invalid_api_key' in error_message or 'Incorrect API key' in error_message:
                return jsonify({'error': f'Invalid API key configured. Please check your OpenAI API key in the environment variables. Error: {error_message}'}), 401
            elif 'API key not configured' in error_message:
                return jsonify({'error': error_message}), 401
            else:
                return jsonify({'error': f'Error generating response: {error_message}'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500

@chats_bp.route('/chats/search', methods=['GET'])
@login_required
def search_chats():
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in chat titles and message content
        chats = db.session.query(Chat).filter(
            Chat.user_id == current_user.id,
            db.or_(
                Chat.title.ilike(f'%{query}%'),
                Chat.id.in_(
                    db.session.query(Message.chat_id).filter(
                        Message.content.ilike(f'%{query}%')
                    )
                )
            )
        ).order_by(desc(Chat.updated_at)).all()
        
        return jsonify([chat.to_dict() for chat in chats]), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to search chats'}), 500

@chats_bp.route('/chats/<int:chat_id>/regenerate-title', methods=['POST'])
@login_required
def regenerate_chat_title(chat_id):
    """Regenerate chat title using LLM summarization"""
    try:
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Generate new title using LLM
        try:
            new_title = generate_chat_title_summary(chat_id, chat.model)
            chat.title = new_title
            db.session.commit()
            
            return jsonify({
                'message': 'Chat title regenerated successfully',
                'chat': chat.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to regenerate title: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': 'Failed to regenerate chat title'}), 500

def generate_ai_response(model, chat_id, user_message):
    # Get chat history
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    
    if model.startswith('gpt-'):
        return generate_openai_response(model, messages, user_message)
    elif model.startswith('claude-'):
        return generate_claude_response(model, messages, user_message)
    else:
        raise ValueError(f"Unsupported model: {model}")

def generate_openai_response(model, messages, user_message):
    if not openai_client:
        raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
    
    try:
        # Convert to OpenAI format with system prompt
        openai_messages = [
            {
                "role": "system",
                "content": OPENAI_SYSTEM_PROMPT
            }
        ]
        
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        openai_messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise Exception(f"Error generating response: {str(e)}")

def generate_claude_response(model, messages, user_message):
    if not anthropic_client:
        raise ValueError("Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable.")
    
    try:
        # Convert to Claude format
        claude_messages = []
        for msg in messages:
            claude_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        claude_messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=1000,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=claude_messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        raise Exception(f"Error generating response: {str(e)}")

def generate_chat_title_summary(chat_id, model):
    """Generate a summarized title for a chat based on all messages using LLM"""
    try:
        # Get all messages from the chat
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        
        if not messages:
            return "New Chat"
        
        # Always use LLM for summarization when we have messages
        # Create conversation summary for the LLM
        conversation_text = ""
        for msg in messages:
            role_label = "Human" if msg.role == "user" else "Assistant"
            # Truncate very long messages to avoid token limits
            content = msg.content[:500] + ('...' if len(msg.content) > 500 else '')
            conversation_text += f"{role_label}: {content}\n\n"
        
        # Prepare the summarization prompt
        summarization_prompt = f"""Please create a concise, descriptive title (maximum 6 words) for this conversation. The title should capture the main topic or purpose of the conversation. Do not include quotation marks in your response.

Conversation:
{conversation_text}

Title:"""
        
        # Use the same model family as the chat for consistency, but use faster models
        if model.startswith('gpt-'):
            return generate_title_with_openai(summarization_prompt, model)
        elif model.startswith('claude-'):
            return generate_title_with_claude(summarization_prompt, model)
        else:
            # Fallback to first message if model not supported
            first_user_msg = next((msg for msg in messages if msg.role == 'user'), None)
            if first_user_msg:
                return first_user_msg.content[:50] + ('...' if len(first_user_msg.content) > 50 else '')
            return "New Chat"
            
    except Exception as e:
        # Fallback to traditional method if LLM fails
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        first_user_msg = next((msg for msg in messages if msg.role == 'user'), None)
        if first_user_msg:
            return first_user_msg.content[:50] + ('...' if len(first_user_msg.content) > 50 else '')
        return "New Chat"

def generate_title_with_openai(prompt, model):
    """Generate title using OpenAI"""
    if not openai_client:
        raise ValueError("OpenAI API key not configured")
    
    # Use a fast, cost-effective model for title generation
    title_model = "gpt-3.5-turbo" if model.startswith('gpt-') else "gpt-3.5-turbo"
    
    response = openai_client.chat.completions.create(
        model=title_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0.3
    )
    
    title = response.choices[0].message.content.strip()
    # Clean up the title - remove quotes and limit length
    title = title.strip('"\'').strip()
    return title[:60] if len(title) > 60 else title

def generate_title_with_claude(prompt, model):
    """Generate title using Claude"""
    if not anthropic_client:
        raise ValueError("Anthropic API key not configured")
    
    # Use a fast, cost-effective model for title generation  
    title_model = "claude-3-haiku-20240307" if model.startswith('claude-') else "claude-3-haiku-20240307"
    
    response = anthropic_client.messages.create(
        model=title_model,
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}]
    )
    
    title = response.content[0].text.strip()
    # Clean up the title - remove quotes and limit length
    title = title.strip('"\'').strip()
    return title[:60] if len(title) > 60 else title