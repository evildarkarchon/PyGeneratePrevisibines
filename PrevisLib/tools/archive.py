"""Archive tool wrapper for Archive2 and BSArch."""

import shutil
from enum import Enum
from pathlib import Path

from loguru import logger

from ..utils.process import ProcessRunner


class ArchiveTool(Enum):
    """Available archive tools."""
    ARCHIVE2 = "Archive2"
    BSARCH = "BSArch"


class ArchiveWrapper:
    """Wrapper for archive operations using Archive2 or BSArch."""
    
    def __init__(self, tool: ArchiveTool, tool_path: Path):
        self.tool = tool
        self.tool_path = tool_path
        self.process_runner = ProcessRunner()
        # File system operations will use module functions directly
        
    def create_archive(self, 
                      archive_path: Path, 
                      source_dir: Path,
                      file_list: list[str] | None = None,
                      compress: bool = True) -> bool:
        """Create a new BA2 archive.
        
        Args:
            archive_path: Path for the output archive
            source_dir: Directory containing files to archive
            file_list: Optional list of specific files to include
            compress: Whether to compress the archive
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating archive {archive_path.name} using {self.tool.value}")
        
        if self.tool == ArchiveTool.ARCHIVE2:
            return self._create_archive2(archive_path, source_dir, file_list, compress)
        return self._create_bsarch(archive_path, source_dir, file_list, compress)
            
    def extract_archive(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract a BA2 archive.
        
        Args:
            archive_path: Path to the archive to extract
            output_dir: Directory to extract files to
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Extracting archive {archive_path.name} using {self.tool.value}")
        
        if not archive_path.exists():
            logger.error(f"Archive not found: {archive_path}")
            return False
            
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.tool == ArchiveTool.ARCHIVE2:
            return self._extract_archive2(archive_path, output_dir)
        return self._extract_bsarch(archive_path, output_dir)
            
    def add_to_archive(self, 
                      archive_path: Path, 
                      files_to_add: list[Path],
                      base_dir: Path | None = None) -> bool:
        """Add files to an existing archive.
        
        Args:
            archive_path: Path to the archive
            files_to_add: List of files to add
            base_dir: Base directory for relative paths
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Adding {len(files_to_add)} files to {archive_path.name}")
        
        # For both tools, we need to extract, add files, and recreate
        temp_dir = archive_path.parent / f"{archive_path.stem}_temp"
        
        try:
            # Extract existing archive
            if archive_path.exists():
                if not self.extract_archive(archive_path, temp_dir):
                    return False
                    
            # Copy new files
            for file_path in files_to_add:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                    
                if base_dir:
                    relative_path = file_path.relative_to(base_dir)
                    dest_path = temp_dir / relative_path
                else:
                    dest_path = temp_dir / file_path.name
                    
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)
                
            # Recreate archive
            archive_path.unlink(missing_ok=True)
            success = self.create_archive(archive_path, temp_dir)
            
            return success
            
        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    def _create_archive2(self, 
                        archive_path: Path, 
                        source_dir: Path,
                        file_list: list[str] | None,
                        compress: bool) -> bool:
        """Create archive using Archive2.exe."""
        args = [
            str(self.tool_path),
            str(archive_path),
            "-create"
        ]
        
        if compress:
            args.append("-compress")
            
        if file_list:
            # Create a file list
            list_file = archive_path.parent / f"{archive_path.stem}_files.txt"
            with open(list_file, 'w') as f:
                f.writelines(f"{file_name}\n" for file_name in file_list)
            args.extend(["-filelist", str(list_file)])
        else:
            # Add all files from source directory
            args.extend(["-root", str(source_dir)])
            
        success = self.process_runner.run_process(args, timeout=600)
        
        # Cleanup file list if created
        if file_list and 'list_file' in locals():
            list_file.unlink(missing_ok=True)
            
        if success and archive_path.exists():
            logger.success(f"Archive created successfully: {archive_path.name}")
            return True
        logger.error("Archive2 creation failed")
        return False
            
    def _create_bsarch(self, 
                      archive_path: Path, 
                      source_dir: Path,
                      file_list: list[str] | None,
                      compress: bool) -> bool:
        """Create archive using BSArch.exe."""
        args = [
            str(self.tool_path),
            "pack",
            str(source_dir),
            str(archive_path)
        ]
        
        if compress:
            args.extend(["-z", "1"])  # Enable compression
        else:
            args.extend(["-z", "0"])  # No compression
            
        # BSArch always uses Fallout 4 format
        args.extend(["-fo4"])
        
        if file_list:
            # BSArch doesn't support file lists directly, need to create temp dir
            temp_dir = source_dir.parent / f"{archive_path.stem}_temp"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                for file_name in file_list:
                    src = source_dir / file_name
                    if src.exists():
                        dst = temp_dir / file_name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                        
                # Pack from temp directory
                args[2] = str(temp_dir)
                success = self.process_runner.run_process(args, timeout=600)
                
            finally:
                # Cleanup temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            success = self.process_runner.run_process(args, timeout=600)
            
        if success and archive_path.exists():
            logger.success(f"Archive created successfully: {archive_path.name}")
            return True
        logger.error("BSArch creation failed")
        return False
            
    def _extract_archive2(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract archive using Archive2.exe."""
        args = [
            str(self.tool_path),
            str(archive_path),
            "-extract",
            str(output_dir)
        ]
        
        success = self.process_runner.run_process(args, timeout=300)
        
        if success:
            logger.success(f"Archive extracted successfully to {output_dir}")
            return True
        logger.error("Archive2 extraction failed")
        return False
            
    def _extract_bsarch(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract archive using BSArch.exe."""
        args = [
            str(self.tool_path),
            "unpack",
            str(archive_path),
            str(output_dir)
        ]
        
        success = self.process_runner.run_process(args, timeout=300)
        
        if success:
            logger.success(f"Archive extracted successfully to {output_dir}")
            return True
        logger.error("BSArch extraction failed")
        return False