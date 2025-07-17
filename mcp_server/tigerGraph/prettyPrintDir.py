#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# PrettyPrintDir.py: This modelue defines the class to perform pretty printing
# file directory
#******************************************************************************
from pathlib import Path
from datetime import datetime
from typing import List
from mcp_server.mcp_logger import setErrorHandler, logger

class PrettyPrintDirectory():

    def __init__(self, dirPath:str):
        setErrorHandler()
        self.output_path = Path(dirPath)

    def getFormatedFileDir(self):
        """Basic file listing with sizes"""
        LENGTH=61
        query_output = []  
        try:
            listOfFiles = self.get_list_files(self.output_path)
            if len(listOfFiles) == 0:
                return query_output
            else:
                query_output.append("=" * LENGTH)
                query_output.append(f"{'Filename':<30} {'Size':<10} {'Modified':<15}")
                query_output.append("-" * LENGTH)
                
                total_size = 0                
                for item in listOfFiles:
                        file_info = self.get_file_info(item)
                        #query_output.append(file_info)
                        
                        if 'error' not in file_info:
                            total_size += file_info['size_bytes']
                            query_output.append(f"{file_info['name']:<25} {file_info['size_formatted']:>9} {file_info['modified']:>25}")
                        else:
                            query_output.append(f"{file_info['name']:<30} {'ERROR':<15} {file_info['modified']:<20}")
                
                query_output.append("-" * LENGTH)
                query_output.append(f"Total files: {len(query_output)-4}")
                query_output.append(f"Total size: {self.format_file_size(total_size)}")
                
                return query_output
        
        except PermissionError:
            logger.error("Error: Permission denied accessing the Output folder")
            return []
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def get_file_info(self, file:Path):
        """Get detailed information about a file"""
        
        try:    
                if (not file.is_dir()):
                    stat = file.stat()
                    return {
                        'name': file.name,
                        'size_bytes': stat.st_size,
                        'size_formatted': self.format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'extension': file.suffix.lower()
                    }
                else:
                    return {}
                
        except (OSError, IOError) as e:
            return {
                'name': file.name,
                'error': str(e)
            }

    def format_file_size(self, size_bytes):
        """Convert bytes to human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
    
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def get_list_files(self, bash_path_dir:Path)-> List[Path]:
        listOfFiles = []
        # Get all files in directory
        if self.output_path.exists():                  
            for item in bash_path_dir.iterdir():
                if item.is_file() and not item.name.startswith('.DS_Store'):
                    listOfFiles.append(bash_path_dir/item.name)
            
        return listOfFiles
