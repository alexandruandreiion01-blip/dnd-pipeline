import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

def run_pipeline():
    logging.info("D&D Spell Pipeline started")
    
    try:
        from extract import extract_all_spells
        from transform import transform_spells
        from load import load_spells, query_spells
        
        raw = extract_all_spells(use_cache=True)
        df = transform_spells(raw)
        load_spells(df)
        query_spells()
        
        logging.info("Pipeline completed successfully")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_pipeline()