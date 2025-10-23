# VideoMetaDataManager

A Python library for managing video metadata using MySQL or RAPIDs database with PyMySQL.

## Features

- MySQL & RAPIDs based storage for video metadata with PyMySQL
- JSON serialization for flexible metadata storage
- Simple CRUD operations (Create, Read, Update)
- Type hints and comprehensive documentation
- Connection pooling and retry mechanism
- Sharded database support

## Installation

### 1. Development Installation
```bash
- git clone https://github.com/sentient-io/AI-Agents.git
```
```bash
- cd libraries/video-metadata
```
```bash
- pip install -e .
```


## Requirements

- Python 3.6+
- PyMySQL>=1.0.2
- MySQL 5.7+ or compatible (tested with Vitess/Sharded MySQL)

## Usage

```python
from video_metadata_manager import VideoMetaDataManager

# Initialize the manager with your database credentials
manager = VideoMetaDataManager(
    host="your_database_host",
    user="your_username",
    password="your_password",
    db_name="your_database_name",
    port=3306  # default MySQL port
)

# Insert video data
video_id = manager.insert_video_data(
    "DqZrV53Vbhk",
    "https://www.youtube.com/watch?v=DqZrV53Vbhk"
    {
        "video_id" : "DqZrV53Vbhk",
        "title": "IRO Lecture on",
        "description" : "In this lecture, Dr Phyllis Chew, Professor at Singapore National Institute of Education"
        "duration": "60"
    }
)
print(f"Inserted video with ID: {video_id}")

# Update metadata
updated_count = manager.update_video_metadata(
    "DqZrV53Vbhk",
    {
        "video_id" : "DqZrV53Vbhk",
        "title": "IRO Lecture on",
        "description" : "In this lecture, Dr Phyllis Chew, Professor at Singapore National Institute of Education"
        "duration": "60",
        "people" : {{"speakers": [{"name": "Dr Phyllis Chew"}]}}
    }
)
print(f"Updated {updated_count} record(s)")

# Get metadata for a specific video
video_data = manager.get_video_metadata("video_001")
print(f"Video data: {video_data}")

# Get all videos
all_videos = manager.get_all_videos()
print(f"Total videos: {len(all_videos)}")
```

## API Reference

### VideoMetaDataManager

#### `__init__(db_name='video_database', host='localhost', user='root', password='', port=3306)`
Initialize the VideoMetaDataManager with database connection parameters.

#### `insert_video_data(video_id: str, metadata: Dict) -> Optional[int]`
Insert a new video record with the given metadata.
- Returns: The ID of the inserted row, or None if insertion failed

#### `update_video_metadata(video_id: str, new_metadata: Dict) -> int`
Update metadata for an existing video.
- Returns: Number of rows updated (0 if not found, 1 if updated)

#### `get_video_metadata(video_url: str) -> Optional[Dict]`
Retrieve metadata for a specific video.
- Returns: Dictionary containing video data or None if not found

#### `get_all_videos() -> List[Dict]`
Retrieve all video records from the database.
- Returns: List of video dictionaries

## Database Schema

The library creates a `video_metadata` table with:
- `video_id`: VARCHAR(255) PRIMARY KEY (unique video identifier)
- `metadata`: TEXT (JSON string containing video metadata)
- `created_at`: TIMESTAMP (automatically set on record creation)
- `updated_at`: TIMESTAMP (automatically updated on record modification)

## Error Handling

The library provides detailed error messages for common database operations. All database operations are wrapped in try-catch blocks to prevent crashes.

