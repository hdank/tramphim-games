import httpx
import hmac
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending webhook callbacks to tramphim backend"""
    
    @staticmethod
    def generate_signature(payload: dict, secret: str) -> str:
        """Generate HMAC SHA256 signature for webhook payload"""
        message = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    async def send_game_result(
        webhook_url: str,
        webhook_secret: str,
        game_id: int,
        player_email: str,
        won: bool,
        score: int,
        moves: int,
        time_taken: float,
        matches_found: int,
        level_id: str = None,
        points_change: int = 0
    ) -> bool:
        """
        Send game completion result to tramphim backend
        
        Returns True if webhook was successfully sent, False otherwise
        """
        if not webhook_url or not webhook_secret:
            logger.warning("Webhook URL or secret not configured, skipping webhook")
            return False
        
        # Prepare payload
        payload = {
            "event": "game_completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "game_id": game_id,
            "data": {
                "player_email": player_email,
                "won": won,
                "score": score,
                "moves": moves,
                "time_taken": round(time_taken, 2),
                "matches_found": matches_found,
                "level_id": level_id,
                "points_change": points_change
            }
        }
        
        # Generate signature
        signature = WebhookService.generate_signature(payload, webhook_secret)
        
        # Send webhook
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully for game {game_id}")
                    return True
                else:
                    print(f"[WEBHOOK] ERROR: Status {response.status_code} from {webhook_url}")
                    print(f"[WEBHOOK] Response: {response.text}", flush=True)
                    logger.error(
                        f"Webhook failed for game {game_id}: "
                        f"Status {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            print(f"[WEBHOOK] EXCEPTION: {str(e)}", flush=True)
            logger.error(f"Error sending webhook for game {game_id}: {str(e)}")
            return False
    
    @staticmethod
    async def test_webhook(webhook_url: str, webhook_secret: str) -> Dict[str, Any]:
        """
        Test webhook connection with a dummy payload
        
        Returns dict with success status and message
        """
        test_payload = {
            "event": "game_completed",  # Changed to match backend expectation
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "game_id": 0,
            "data": {
                "player_email": "test@tramphim.com",  # Use valid test email
                "won": True,
                "score": 100,
                "moves": 15,
                "time_taken": 45.5,
                "matches_found": 8
            }
        }
        
        signature = WebhookService.generate_signature(test_payload, webhook_secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=test_payload,
                    headers=headers
                )
                
                # Get response text
                try:
                    response_text = response.text
                except:
                    response_text = "Could not read response"
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": f"Status: {response.status_code}, Response: {response_text[:500]}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "message": f"Error: {str(e)}"
            }
