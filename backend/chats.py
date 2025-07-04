from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Chat, Message
from config import Config
import openai
import anthropic
from sqlalchemy import desc

chats_bp = Blueprint('chats', __name__)

# Initialize LLM clients
openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) if Config.ANTHROPIC_API_KEY else None

@chats_bp.route('/chats', methods=['GET'])
@login_required
def get_chats():
    try:
        chats = Chat.query.filter_by(user_id=current_user.id).order_by(desc(Chat.updated_at)).all()
        
        return jsonify({
            'chats': [chat.to_dict() for chat in chats]
        }), 200
        
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
        valid_models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
        if model not in valid_models:
            return jsonify({'error': 'Invalid model selected'}), 400
        
        chat = Chat(
            user_id=current_user.id,
            title=title,
            model=model
        )
        
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            'message': 'Chat created successfully',
            'chat': chat.to_dict()
        }), 201
        
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
        
        return jsonify({
            'chat': chat.to_dict(),
            'messages': [message.to_dict() for message in messages]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get chat'}), 500

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
            
            # Update chat title if it's the first message
            if message_count == 0:
                chat.title = content[:50] + ('...' if len(content) > 50 else '')
            
            db.session.commit()
            
            return jsonify({
                'user_message': user_message.to_dict(),
                'ai_message': ai_message.to_dict(),
                'chat': chat.to_dict()
            }), 201
            
        except Exception as ai_error:
            db.session.rollback()
            return jsonify({'error': 'Failed to generate AI response'}), 500
        
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
        
        return jsonify({
            'chats': [chat.to_dict() for chat in chats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to search chats'}), 500

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
        return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
    try:
        # Convert to OpenAI format
        openai_messages = []
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
        return f"Error generating response: {str(e)}"

def generate_claude_response(model, messages, user_message):
    if not anthropic_client:
        return "Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable."
    
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
            messages=claude_messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"Error generating response: {str(e)}"