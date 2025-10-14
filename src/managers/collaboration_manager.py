"""
Real-time Collaboration Module
Provides real-time features like live editing, notifications, and collaboration
"""

import json
import asyncio
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import threading
import time
from collections import defaultdict
import uuid

class CollaborationManager:
    """Real-time collaboration features"""
    
    def __init__(self):
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_sessions: Dict[str, Dict] = {}
        self.room_participants: Dict[str, Set[str]] = defaultdict(set)
        self.document_states: Dict[str, Dict] = {}
        self.collaboration_history: Dict[str, List[Dict]] = defaultdict(list)
        self.notification_queue: Dict[str, List[Dict]] = defaultdict(list)
        
        # Collaboration features
        self.features = {
            'live_cursor': True,
            'live_editing': True,
            'real_time_notifications': True,
            'presence_indicator': True,
            'comment_system': True,
            'version_control': True,
            'conflict_resolution': True
        }
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_message(websocket, data)
        except websockets.exceptions.ConnectionClosed:
            await self.handle_disconnection(websocket)
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    async def process_message(self, websocket, data: Dict):
        """Process incoming WebSocket message"""
        message_type = data.get('type')
        
        if message_type == 'join':
            await self.handle_join(websocket, data)
        elif message_type == 'leave':
            await self.handle_leave(websocket, data)
        elif message_type == 'cursor_move':
            await self.handle_cursor_move(websocket, data)
        elif message_type == 'text_edit':
            await self.handle_text_edit(websocket, data)
        elif message_type == 'comment':
            await self.handle_comment(websocket, data)
        elif message_type == 'presence':
            await self.handle_presence(websocket, data)
        elif message_type == 'notification':
            await self.handle_notification(websocket, data)
        elif message_type == 'ping':
            await self.handle_ping(websocket, data)
    
    async def handle_join(self, websocket, data: Dict):
        """Handle user joining a room"""
        user_id = data.get('user_id')
        room_id = data.get('room_id')
        user_info = data.get('user_info', {})
        
        if not user_id or not room_id:
            await self.send_error(websocket, "Missing user_id or room_id")
            return
        
        # Store connection
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.user_sessions[connection_id] = {
            'user_id': user_id,
            'room_id': room_id,
            'user_info': user_info,
            'joined_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        # Add to room
        self.room_participants[room_id].add(connection_id)
        
        # Send current document state
        if room_id in self.document_states:
            await self.send_message(websocket, {
                'type': 'document_state',
                'state': self.document_states[room_id]
            })
        
        # Notify other participants
        await self.broadcast_to_room(room_id, {
            'type': 'user_joined',
            'user_id': user_id,
            'user_info': user_info,
            'participants': self.get_room_participants(room_id)
        }, exclude=connection_id)
        
        # Send join confirmation
        await self.send_message(websocket, {
            'type': 'join_success',
            'room_id': room_id,
            'participants': self.get_room_participants(room_id)
        })
    
    async def handle_leave(self, websocket, data: Dict):
        """Handle user leaving a room"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        room_id = session['room_id']
        user_id = session['user_id']
        
        # Remove from room
        self.room_participants[room_id].discard(connection_id)
        
        # Clean up
        del self.user_sessions[connection_id]
        del self.active_connections[connection_id]
        
        # Notify other participants
        await self.broadcast_to_room(room_id, {
            'type': 'user_left',
            'user_id': user_id,
            'participants': self.get_room_participants(room_id)
        })
    
    async def handle_cursor_move(self, websocket, data: Dict):
        """Handle cursor movement"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        room_id = session['room_id']
        user_id = session['user_id']
        
        cursor_data = {
            'user_id': user_id,
            'position': data.get('position'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast cursor position to other participants
        await self.broadcast_to_room(room_id, {
            'type': 'cursor_update',
            'cursor': cursor_data
        }, exclude=connection_id)
    
    async def handle_text_edit(self, websocket, data: Dict):
        """Handle text editing"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        room_id = session['room_id']
        user_id = session['user_id']
        
        # Apply edit to document state
        edit_result = self.apply_text_edit(room_id, data)
        
        if edit_result['success']:
            # Broadcast edit to other participants
            await self.broadcast_to_room(room_id, {
                'type': 'text_edit',
                'edit': {
                    'user_id': user_id,
                    'operation': data.get('operation'),
                    'position': data.get('position'),
                    'text': data.get('text'),
                    'timestamp': datetime.now().isoformat()
                },
                'document_state': self.document_states[room_id]
            }, exclude=connection_id)
            
            # Log collaboration history
            self.log_collaboration_event(room_id, 'text_edit', {
                'user_id': user_id,
                'operation': data.get('operation'),
                'position': data.get('position'),
                'text': data.get('text')
            })
        else:
            await self.send_error(websocket, edit_result['error'])
    
    async def handle_comment(self, websocket, data: Dict):
        """Handle comments"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        room_id = session['room_id']
        user_id = session['user_id']
        
        comment = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'text': data.get('text'),
            'position': data.get('position'),
            'timestamp': datetime.now().isoformat(),
            'resolved': False
        }
        
        # Store comment
        if 'comments' not in self.document_states[room_id]:
            self.document_states[room_id]['comments'] = []
        
        self.document_states[room_id]['comments'].append(comment)
        
        # Broadcast comment to all participants
        await self.broadcast_to_room(room_id, {
            'type': 'comment_added',
            'comment': comment
        })
        
        # Log collaboration history
        self.log_collaboration_event(room_id, 'comment_added', comment)
    
    async def handle_presence(self, websocket, data: Dict):
        """Handle presence updates"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        # Update last activity
        session['last_activity'] = datetime.now().isoformat()
        
        # Broadcast presence update
        await self.broadcast_to_room(session['room_id'], {
            'type': 'presence_update',
            'user_id': session['user_id'],
            'status': data.get('status', 'active'),
            'timestamp': datetime.now().isoformat()
        }, exclude=connection_id)
    
    async def handle_notification(self, websocket, data: Dict):
        """Handle notifications"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if not session:
            return
        
        notification = {
            'id': str(uuid.uuid4()),
            'type': data.get('notification_type'),
            'message': data.get('message'),
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        # Store notification
        user_id = session['user_id']
        self.notification_queue[user_id].append(notification)
        
        # Send notification to user
        await self.send_message(websocket, {
            'type': 'notification_received',
            'notification': notification
        })
    
    async def handle_ping(self, websocket, data: Dict):
        """Handle ping/pong for connection health"""
        await self.send_message(websocket, {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    async def handle_disconnection(self, websocket):
        """Handle WebSocket disconnection"""
        connection_id = self.get_connection_id(websocket)
        if not connection_id:
            return
        
        session = self.user_sessions.get(connection_id)
        if session:
            room_id = session['room_id']
            user_id = session['user_id']
            
            # Remove from room
            self.room_participants[room_id].discard(connection_id)
            
            # Clean up
            del self.user_sessions[connection_id]
            del self.active_connections[connection_id]
            
            # Notify other participants
            await self.broadcast_to_room(room_id, {
                'type': 'user_disconnected',
                'user_id': user_id,
                'participants': self.get_room_participants(room_id)
            })
    
    def apply_text_edit(self, room_id: str, edit_data: Dict) -> Dict:
        """Apply text edit to document state"""
        if room_id not in self.document_states:
            self.document_states[room_id] = {
                'content': '',
                'version': 0,
                'last_modified': datetime.now().isoformat()
            }
        
        operation = edit_data.get('operation')
        position = edit_data.get('position', 0)
        text = edit_data.get('text', '')
        
        try:
            if operation == 'insert':
                content = self.document_states[room_id]['content']
                new_content = content[:position] + text + content[position:]
                self.document_states[room_id]['content'] = new_content
            elif operation == 'delete':
                content = self.document_states[room_id]['content']
                length = edit_data.get('length', 1)
                new_content = content[:position] + content[position + length:]
                self.document_states[room_id]['content'] = new_content
            elif operation == 'replace':
                content = self.document_states[room_id]['content']
                length = edit_data.get('length', 0)
                new_content = content[:position] + text + content[position + length:]
                self.document_states[room_id]['content'] = new_content
            
            # Update version and timestamp
            self.document_states[room_id]['version'] += 1
            self.document_states[room_id]['last_modified'] = datetime.now().isoformat()
            
            return {'success': True}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def log_collaboration_event(self, room_id: str, event_type: str, data: Dict):
        """Log collaboration event"""
        event = {
            'id': str(uuid.uuid4()),
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.collaboration_history[room_id].append(event)
        
        # Keep only last 1000 events
        if len(self.collaboration_history[room_id]) > 1000:
            self.collaboration_history[room_id] = self.collaboration_history[room_id][-1000:]
    
    def get_connection_id(self, websocket) -> Optional[str]:
        """Get connection ID for WebSocket"""
        for conn_id, conn in self.active_connections.items():
            if conn == websocket:
                return conn_id
        return None
    
    def get_room_participants(self, room_id: str) -> List[Dict]:
        """Get room participants info"""
        participants = []
        
        for conn_id in self.room_participants[room_id]:
            session = self.user_sessions.get(conn_id)
            if session:
                participants.append({
                    'user_id': session['user_id'],
                    'user_info': session['user_info'],
                    'joined_at': session['joined_at'],
                    'last_activity': session['last_activity']
                })
        
        return participants
    
    async def broadcast_to_room(self, room_id: str, message: Dict, exclude: str = None):
        """Broadcast message to all participants in room"""
        for conn_id in self.room_participants[room_id]:
            if exclude and conn_id == exclude:
                continue
            
            websocket = self.active_connections.get(conn_id)
            if websocket:
                try:
                    await self.send_message(websocket, message)
                except websockets.exceptions.ConnectionClosed:
                    # Clean up closed connection
                    await self.handle_disconnection(websocket)
    
    async def send_message(self, websocket, message: Dict):
        """Send message to WebSocket"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to WebSocket"""
        await self.send_message(websocket, {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_collaboration_history(self, room_id: str, limit: int = 100) -> List[Dict]:
        """Get collaboration history for room"""
        return self.collaboration_history[room_id][-limit:]
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user notifications"""
        return self.notification_queue[user_id][-limit:]
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        notifications = self.notification_queue[user_id]
        for notification in notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                return True
        return False
    
    def get_active_rooms(self) -> Dict[str, Dict]:
        """Get all active rooms with participant count"""
        active_rooms = {}
        
        for room_id, participants in self.room_participants.items():
            if participants:
                active_rooms[room_id] = {
                    'participant_count': len(participants),
                    'participants': self.get_room_participants(room_id),
                    'last_activity': max(
                        session['last_activity'] 
                        for conn_id in participants 
                        for session in [self.user_sessions.get(conn_id)] 
                        if session
                    )
                }
        
        return active_rooms
    
    def cleanup_inactive_sessions(self):
        """Clean up inactive sessions"""
        current_time = datetime.now()
        inactive_threshold = timedelta(minutes=30)
        
        inactive_connections = []
        
        for conn_id, session in self.user_sessions.items():
            last_activity = datetime.fromisoformat(session['last_activity'])
            if current_time - last_activity > inactive_threshold:
                inactive_connections.append(conn_id)
        
        for conn_id in inactive_connections:
            websocket = self.active_connections.get(conn_id)
            if websocket:
                asyncio.create_task(self.handle_disconnection(websocket))
    
    def start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup_loop():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self.cleanup_inactive_sessions()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

# Global instance
collaboration_manager = CollaborationManager()
