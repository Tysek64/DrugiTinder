from datetime import datetime
import populate
import settings

if __name__ == "__main__":
    start_time = datetime.now()
    print("--- START GENERATORA ---")
    print(f"Baza: {settings.DB_NAME}")
    
    populate.run()
    
    end_time = datetime.now()
    total_docs = sum(settings.COUNTS.values()) + 3
    
    print("\n--- ZAKOŃCZONO SUKCESEM ---")
    print(f"Czas trwania: {end_time - start_time}")
    print(f"Wygenerowano ok. {total_docs} dokumentów.")