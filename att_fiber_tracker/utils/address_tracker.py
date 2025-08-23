"""
Address Tracker Utility - Prevents duplicate processing to save BatchData costs
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class AddressTracker:
    """Tracks processed addresses to prevent duplicates and save API costs"""
    
    def __init__(self, tracking_file: str = "data/processed_addresses.json"):
        self.tracking_file = tracking_file
        self.processed_addresses = self.load_tracking_data()
        
    def load_tracking_data(self) -> Dict:
        """Load existing tracking data"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('addresses', {}))} previously processed addresses")
                    return data
        except Exception as e:
            logger.error(f"Error loading tracking data: {e}")
        
        return {
            "addresses": {},  # address_hash -> processing_info
            "last_updated": None,
            "stats": {
                "total_processed": 0,
                "duplicates_prevented": 0,
                "cost_savings": 0.0
            }
        }
    
    def save_tracking_data(self):
        """Save tracking data to file"""
        try:
            os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
            self.processed_addresses["last_updated"] = datetime.now().isoformat()
            
            with open(self.tracking_file, 'w') as f:
                json.dump(self.processed_addresses, f, indent=2)
            logger.info(f"Saved tracking data for {len(self.processed_addresses['addresses'])} addresses")
        except Exception as e:
            logger.error(f"Error saving tracking data: {e}")
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for consistent comparison"""
        normalized = address.lower().strip()
        normalized = normalized.replace(" apt ", " ").replace(" unit ", " ").replace(" #", " ")
        normalized = " ".join(normalized.split())
        
        replacements = {
            " street": " st", " avenue": " ave", " boulevard": " blvd",
            " drive": " dr", " road": " rd", " lane": " ln", " court": " ct",
            " circle": " cir", " place": " pl", " way": " way"
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
            
        return normalized
    
    def get_address_hash(self, address: str, city: str = "", state: str = "") -> str:
        """Generate consistent hash for address"""
        normalized_address = self.normalize_address(address)
        full_address = f"{normalized_address}, {city.lower()}, {state.lower()}".strip(", ")
        return hashlib.md5(full_address.encode()).hexdigest()
    
    def is_address_processed(self, address: str, city: str = "", state: str = "", 
                           days_threshold: int = 30) -> bool:
        """Check if address was recently processed"""
        address_hash = self.get_address_hash(address, city, state)
        
        if address_hash not in self.processed_addresses["addresses"]:
            return False
        
        processed_info = self.processed_addresses["addresses"][address_hash]
        processed_date = datetime.fromisoformat(processed_info["last_processed"])
        
        if datetime.now() - processed_date < timedelta(days=days_threshold):
            logger.info(f"Address already processed recently: {address} (last: {processed_date.date()})")
            self.processed_addresses["stats"]["duplicates_prevented"] += 1
            self.processed_addresses["stats"]["cost_savings"] += 0.10
            return True
        
        return False
    
    def mark_address_processed(self, address: str, city: str = "", state: str = "", 
                             processing_stage: str = "redfin", additional_data: Dict = None):
        """Mark address as processed"""
        address_hash = self.get_address_hash(address, city, state)
        
        processing_info = {
            "original_address": address,
            "city": city,
            "state": state,
            "last_processed": datetime.now().isoformat(),
            "processing_stage": processing_stage,
            "processing_count": 1
        }
        
        if address_hash in self.processed_addresses["addresses"]:
            existing = self.processed_addresses["addresses"][address_hash]
            processing_info["processing_count"] = existing.get("processing_count", 0) + 1
            processing_info["first_processed"] = existing.get("first_processed", processing_info["last_processed"])
        else:
            processing_info["first_processed"] = processing_info["last_processed"]
            self.processed_addresses["stats"]["total_processed"] += 1
        
        if additional_data:
            processing_info.update(additional_data)
        
        self.processed_addresses["addresses"][address_hash] = processing_info
        logger.debug(f"Marked address as processed: {address}")
    
    def filter_new_addresses(self, addresses_df: pd.DataFrame, 
                           address_col: str = "ADDRESS", 
                           city_col: str = "CITY", 
                           state_col: str = "STATE OR PROVINCE") -> pd.DataFrame:
        """Filter out already processed addresses from DataFrame"""
        if addresses_df.empty:
            return addresses_df
        
        new_addresses_mask = []
        
        for _, row in addresses_df.iterrows():
            address = str(row.get(address_col, ""))
            city = str(row.get(city_col, ""))
            state = str(row.get(state_col, ""))
            
            is_new = not self.is_address_processed(address, city, state)
            new_addresses_mask.append(is_new)
        
        new_addresses_df = addresses_df[new_addresses_mask].copy()
        
        duplicates_count = len(addresses_df) - len(new_addresses_df)
        if duplicates_count > 0:
            logger.info(f"Filtered out {duplicates_count} duplicate addresses, {len(new_addresses_df)} new addresses remain")
        
        return new_addresses_df
    
    def mark_batch_processed(self, addresses_df: pd.DataFrame, 
                           address_col: str = "ADDRESS",
                           city_col: str = "CITY", 
                           state_col: str = "STATE OR PROVINCE",
                           processing_stage: str = "redfin"):
        """Mark a batch of addresses as processed"""
        for _, row in addresses_df.iterrows():
            address = str(row.get(address_col, ""))
            city = str(row.get(city_col, ""))
            state = str(row.get(state_col, ""))
            
            additional_data = {
                "source": "redfin_batch",
                "sale_date": str(row.get("SOLD DATE", "")),
                "price": str(row.get("PRICE", ""))
            }
            
            self.mark_address_processed(address, city, state, processing_stage, additional_data)
        
        self.save_tracking_data()
    
    def get_stats(self) -> Dict:
        """Get processing statistics"""
        stats = self.processed_addresses.get("stats", {})
        stats["total_addresses_tracked"] = len(self.processed_addresses.get("addresses", {}))
        stats["estimated_cost_savings"] = f"${stats.get('cost_savings', 0):.2f}"
        return stats
    
    def cleanup_old_addresses(self, days_to_keep: int = 90):
        """Remove very old address records to keep file size manageable"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        addresses = self.processed_addresses.get("addresses", {})
        
        to_remove = []
        for addr_hash, info in addresses.items():
            last_processed = datetime.fromisoformat(info["last_processed"])
            if last_processed < cutoff_date:
                to_remove.append(addr_hash)
        
        for addr_hash in to_remove:
            del addresses[addr_hash]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old address records")
            self.save_tracking_data()
    
    def export_processed_addresses(self, output_file: str = "data/processed_addresses_export.csv"):
        """Export processed addresses to CSV for review"""
        try:
            addresses_data = []
            for addr_hash, info in self.processed_addresses.get("addresses", {}).items():
                addresses_data.append({
                    "hash": addr_hash,
                    "address": info.get("original_address", ""),
                    "city": info.get("city", ""),
                    "state": info.get("state", ""),
                    "first_processed": info.get("first_processed", ""),
                    "last_processed": info.get("last_processed", ""),
                    "processing_count": info.get("processing_count", 0),
                    "processing_stage": info.get("processing_stage", ""),
                    "source": info.get("source", "")
                })
            
            df = pd.DataFrame(addresses_data)
            df.to_csv(output_file, index=False)
            logger.info(f"Exported {len(addresses_data)} processed addresses to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error exporting addresses: {e}")
            return None 