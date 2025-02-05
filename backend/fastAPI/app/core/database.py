import supabase
from dotenv import load_dotenv
import os

load_dotenv()
from asyncio import to_thread
class Database:
    def __init__(self):
        self.client: supabase.Client = supabase.create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

    async def execute(self, query: str, params: dict = None):
        """Execute SQL query asynchronously"""
        try:
            # Parameter verarbeiten
            if params:
                for key, value in params.items():
                    if isinstance(value, list):
                        placeholders = ','.join([f"'{v}'" for v in value])
                        query = query.replace(f":{key}", f"ARRAY[{placeholders}]")
                    else:
                        query = query.replace(f":{key}", f"'{value}'")

            # Wrapping sync call in async
            response = await to_thread(
                self.client.rpc('exec_sql', {'query': query}).execute
            )

            return response.data

        except Exception as e:
            print(f"Database error: {str(e)}")
            raise