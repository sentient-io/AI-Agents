import pymysql
import json
from typing import Dict, List, Optional, Any, Union

class VideoMetaDataManager:
    """
    A class for managing video metadata in a MySQL database.
    
    This class provides methods to insert, update, and retrieve video metadata
    stored as JSON strings in a MySQL database.
    """
    
    def __init__(self, db_name: str = 'video_database', host: str = 'localhost', user: str = 'root', password: str = '', port: int = 3306):
        """
        Initialize the VideoMetaDataManager with a database connection.
        
        Args:
            db_name (str): Name of the database (default: 'video_database')
            host (str): Hostname or IP address of the MySQL server (default: 'localhost')
            user (str): MySQL username (default: 'root')
            password (str): MySQL password (default: '')
        """
        self.db_name = db_name
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self._create_table()
    
    def _get_connection(self, use_db: bool = True) -> pymysql.connections.Connection:
        """
        Create a database connection with timeout and retry logic.
        
        Args:
            use_db (bool): Whether to connect to a specific database
            
        Returns:
            pymysql.connections.Connection: Database connection object
            
        Raises:
            pymysql.Error: If connection fails after retries
        """
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                return pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.db_name if use_db else None,
                    cursorclass=pymysql.cursors.DictCursor,
                    charset='utf8mb4',
                    connect_timeout=10,  # 10 seconds connection timeout
                    read_timeout=30,     # 30 seconds read timeout
                    write_timeout=30,    # 30 seconds write timeout
                    client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
                )
            except pymysql.Error as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Failed to connect to database after {max_retries} attempts")
                    print(f"Host: {self.host}, Database: {self.db_name if use_db else 'None'}")
                    print(f"Error: {e}")
                    raise
                print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} second(s)...")
                import time
                time.sleep(retry_delay)

    def _create_table(self) -> None:
        """Private method to create the video_metadata table if it doesn't exist."""
        try:
            # First create database if not exists
            with self._get_connection(use_db=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.db_name}')
                    cursor.execute(f'USE {self.db_name}')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS video_metadata (
                            video_id VARCHAR(255) PRIMARY KEY,
                            metadata TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            INDEX (created_at)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    ''')
                    conn.commit()
        except pymysql.Error as err:
            print(f"Error creating table: {err}")
    
    def insert_video_data(self, video_id: str, metadata: Dict) -> Optional[int]:
        """
        Insert a new video record into the database.
        
        Args:
            video_id (str): Unique identifier for the video
            metadata (dict): Dictionary containing video metadata
            
        Returns:
            int | None: ID of the inserted row, or None if insertion failed
        """
        try:
            metadata_json = json.dumps(metadata)
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO video_metadata (video_id, metadata) VALUES (%s, %s)',
                        (video_id, metadata_json)
                    )
                    conn.commit()
                    return cursor.lastrowid
        except pymysql.Error as e:
            print(f"Error inserting video data: {e}")
            return None
    
    def update_video_metadata(self, video_id: str, new_metadata: Dict) -> int:
        """
        Update metadata for an existing video record.
        
        Args:
            video_id (str): Unique identifier for the video
            new_metadata (dict): Updated metadata dictionary
            
        Returns:
            int: Number of rows updated (0 if not found, 1 if updated)
        """
        try:
            new_metadata_json = json.dumps(new_metadata)
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'UPDATE video_metadata SET metadata = %s WHERE video_id = %s',
                        (new_metadata_json, video_id)
                    )
                    conn.commit()
                    return cursor.rowcount
        except pymysql.Error as e:
            print(f"Error updating video metadata: {e}")
            return 0
    
    def get_video_metadata(self, video_id: str) -> Optional[Dict]:
        """
        Retrieve metadata for a specific video ID.
        
        Args:
            video_id (str): The unique identifier of the video
            
        Returns:
            dict | None: Dictionary containing the video metadata if found, None otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM video_metadata WHERE video_id = %s',
                        (video_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        return {
                            'video_id': row['video_id'],
                            'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                        }
                    return None
                    
        except (pymysql.Error, json.JSONDecodeError) as e:
            print(f"Error retrieving video metadata: {e}")
            return None

    def get_all_videos(self) -> List[Dict]:
        """
        Retrieve all video records from the database.
        
        Returns:
            list[dict]: List of dictionaries containing all video data
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM video_metadata')
                    rows = cursor.fetchall()
                    
                    result = []
                    for row in rows:
                        try:
                            video_data = {
                                'video_id': row['video_id'],
                                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                            }
                            result.append(video_data)
                        except json.JSONDecodeError as e:
                            print(f"Error parsing metadata for video {row.get('ID')}: {e}")
                    
                    return result
        except pymysql.Error as e:
            print(f"Error retrieving all videos: {e}")
            return []
