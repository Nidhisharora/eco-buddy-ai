import logging
import time
from typing import List, Dict, Any
from .delta_models import EcoLogDelta
from .sync_db import sync_db

logger = logging.getLogger(__name__)

class SyncController:
    """
    Conflict Resolution Engine for Offline Mobile Sync (Issue #1473).
    Implements a strict 'Latest Timestamp Wins' CRDT-style delta sync protocol.
    """

    @staticmethod
    def process_sync(user_id: str, last_sync_timestamp: int, client_deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes the 3-step synchronization algorithm.
        """
        logger.info(f"Initiating Sync for User {user_id}. Client Last Sync: {last_sync_timestamp}")

        # 1. Parse client payloads into strongly-typed models
        parsed_client_deltas = [EcoLogDelta.from_dict(d) for d in client_deltas]
        
        # We will build an array of server updates that the client must apply locally
        server_updates_for_client = []
        
        # 2. Iterate and Resolve Conflicts
        for client_delta in parsed_client_deltas:
            server_record = sync_db.get_record(user_id, client_delta.id)
            
            if not server_record:
                # Scenario A: New record created offline by client. Always wins.
                logger.debug(f"Inserting new offline record: {client_delta.id}")
                sync_db.apply_delta(client_delta)
                
            else:
                # Scenario B: Conflict Detected! Both server and client have modified this record.
                # Apply 'Latest Timestamp Wins' Resolution
                if client_delta.last_modified > server_record.last_modified:
                    logger.debug(f"Conflict Resolved (Client Wins): {client_delta.id}")
                    sync_db.apply_delta(client_delta)
                else:
                    logger.debug(f"Conflict Resolved (Server Wins): {client_delta.id}")
                    # The client lost the conflict. We must send the server's truth back down to them.
                    server_updates_for_client.append(server_record)

        # 3. Append all other server-side changes that occurred since the client was last online
        server_changes = sync_db.get_server_deltas_since(user_id, last_sync_timestamp)
        
        for sc in server_changes:
            # Avoid sending back records we *just* processed and resolved in the loop above
            if not any(update.id == sc.id for update in server_updates_for_client) and not any(cd.id == sc.id for cd in parsed_client_deltas):
                 server_updates_for_client.append(sc)

        new_sync_timestamp = int(time.time() * 1000)
        
        logger.info(f"Sync Complete. Sending {len(server_updates_for_client)} patches to client.")

        return {
            "status": "SUCCESS",
            "new_sync_timestamp": new_sync_timestamp,
            "server_deltas": [delta.to_dict() for delta in server_updates_for_client]
        }
