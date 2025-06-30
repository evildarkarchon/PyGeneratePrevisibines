"""Archive tool wrapper for Archive2 and BSArch."""

import shutil
from pathlib import Path

from loguru import logger

from PrevisLib.models.data_classes import ArchiveTool, BuildMode
from PrevisLib.utils.process import ProcessRunner


class ArchiveWrapper:
    """Wrapper for archive operations using Archive2 or BSArch."""

    def __init__(self, tool: ArchiveTool, tool_path: Path, build_mode: BuildMode) -> None:
        self.tool = tool
        self.tool_path = tool_path
        self.build_mode = build_mode
        self.process_runner = ProcessRunner()
        # File system operations will use module functions directly

    def create_archive(self, archive_path: Path, source_dir: Path, file_list: list[str] | None = None, compress: bool = True) -> bool:
        """
        Creates an archive file from the specified files and directory.

        This function creates an archive file using the specified tool, either by
        calling the `_create_archive2` method or the `_create_bsarch` method,
        depending on the selected tool. The archive can include specific files
        from the directory and can be compressed if desired.

        :param archive_path: The path of the archive file to create.
        :type archive_path: Path
        :param source_dir: The directory containing the files to be archived.
        :type source_dir: Path
        :param file_list: A list of files to include in the archive. If None, the entire
            source directory will be archived.
        :type file_list: list[str] | None
        :param compress: If True, the archive will be compressed. Defaults to True.
        :type compress: bool
        :return: True if the archive was successfully created, False otherwise.
        :rtype: bool
        """
        logger.info(f"Creating archive {archive_path.name} using {self.tool.value}")

        if self.tool == ArchiveTool.ARCHIVE2:
            return self._create_archive2(archive_path, source_dir, file_list, compress)
        return self._create_bsarch(archive_path, source_dir, file_list, compress)

    def extract_archive(self, archive_path: Path, output_dir: Path) -> bool:
        """
        Extracts a given archive file to the specified output directory using the selected
        archive tool. Ensures the archive exists and the output directory is created prior
        to extraction. Returns whether the extraction was successful.

        :param archive_path: Path to the archive file to be extracted.
        :param output_dir: Path to the directory where the archive contents should
            be extracted.
        :return: A boolean value indicating whether the extraction was successful.
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

    def add_to_archive(self, archive_path: Path, files_to_add: list[Path], base_dir: Path | None = None) -> bool:
        """
        Add a list of files to an existing archive, extracting the archive first, then updating
        its contents, and finally recreating it. If the archive does not already exist, an empty
        archive is created and the files are added. Temporary directories are used during the
        process and are cleaned up upon completion.

        :param archive_path: The path to the archive file to which files should be added.
        :type archive_path: Path
        :param files_to_add: A list of file paths that need to be added to the archive.
        :type files_to_add: list[Path]
        :param base_dir: An optional base directory from which relative paths of files
            to be added will be determined. If None, files are added with their original
            names in the archive's root.
        :type base_dir: Path | None
        :return: True if the operation completes successfully, otherwise False.
        :rtype: bool
        """
        logger.info(f"Adding {len(files_to_add)} files to {archive_path.name}")

        # For both tools, we need to extract, add files, and recreate
        temp_dir: Path = archive_path.parent / f"{archive_path.stem}_temp"

        try:
            # Extract existing archive
            if archive_path.exists() and not self.extract_archive(archive_path, temp_dir):
                return False

            # Copy new files
            for file_path in files_to_add:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                if base_dir:
                    relative_path: Path = file_path.relative_to(base_dir)
                    dest_path: Path = temp_dir / relative_path
                else:
                    dest_path = temp_dir / file_path.name

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)

            # Recreate archive
            archive_path.unlink(missing_ok=True)
            return self.create_archive(archive_path, temp_dir)

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _create_archive2(self, archive_path: Path, source_dir: Path, file_list: list[str] | None, compress: bool) -> bool:
        """
        Creates an archive using the Archive2 tool with the specified options. This method
        can handle both directory-based sources and file lists. Additionally, it supports
        configuration for compression modes based on the build mode and cleans up temporary
        files after execution.

        :param archive_path: The file path for the archive to be created.
        :param source_dir: The root directory path of the source files or directories.
        :param file_list: A list of source file paths to be added to the archive. Default is None.
        :param compress: A boolean flag indicating whether the archive should be compressed.
        :return: A boolean value indicating whether the archive creation process was successful.

        """
        # Archive2 expects files/folders as positional args, then options
        args: list[str] = [str(self.tool_path)]
        list_file: Path | None = None

        if file_list:
            # Create a source file list
            list_file = archive_path.parent / f"{archive_path.stem}_files.txt"
            with list_file.open("w") as f:
                f.writelines(f"{file_name}\n" for file_name in file_list)
            args.extend(["-sourceFile=" + str(list_file)])
        else:
            # Add source directory as positional argument
            args.append(str(source_dir))

        # Add create option with archive path
        args.append(f"-create={archive_path}")

        # Add root directory option
        args.append(f"-root={source_dir}")

        # Set compression option based on build mode
        if compress:
            if self.build_mode == BuildMode.XBOX:
                args.append("-compression=XBox")
            else:
                args.append("-compression=Default")
        else:
            args.append("-compression=None")

        success: bool = self.process_runner.execute(args, timeout=600)

        # Cleanup file list if created
        if list_file is not None:
            list_file.unlink(missing_ok=True)

        if success and archive_path.exists():
            logger.success(f"Archive created successfully: {archive_path.name}")
            return True
        logger.error("Archive2 creation failed")
        return False

    def _create_bsarch(self, archive_path: Path, source_dir: Path, file_list: list[str] | None, compress: bool) -> bool:
        """
        Creates an archive using the BSArch tool. This method can handle optional file lists by creating a temporary directory
        to store only the specified files to include in the archive. Compression can be enabled or disabled, and the method
        always uses Fallout 4 format for the archive creation.

        :param archive_path: The path to the output archive to be created.
        :param source_dir: The source directory containing the files to archive.
        :param file_list: A list of filenames to include in the archive, or None to include all files from the source directory.
        :param compress: A boolean flag indicating whether compression should be enabled (True) or disabled (False).
        :return: True if the archive was created successfully; otherwise, False.
        """
        args: list[str] = [str(self.tool_path), "pack", str(source_dir), str(archive_path)]

        if compress:
            args.extend(["-z", "1"])  # Enable compression
        else:
            args.extend(["-z", "0"])  # No compression

        # BSArch always uses Fallout 4 format
        args.extend(["-fo4"])

        if file_list:
            # BSArch doesn't support file lists directly, need to create temp dir
            temp_dir: Path = source_dir.parent / f"{archive_path.stem}_temp"
            temp_dir.mkdir(exist_ok=True)

            try:
                for file_name in file_list:
                    src: Path = source_dir / file_name
                    if src.exists():
                        dst: Path = temp_dir / file_name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)

                # Pack from temp directory
                args[2] = str(temp_dir)
                success: bool = self.process_runner.execute(args, timeout=600)

            finally:
                # Cleanup temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            success = self.process_runner.execute(args, timeout=600)

        if success and archive_path.exists():
            logger.success(f"Archive created successfully: {archive_path.name}")
            return True
        logger.error("BSArch creation failed")
        return False

    def _extract_archive2(self, archive_path: Path, output_dir: Path) -> bool:
        """
        Extracts a given archive to a specified output directory using the Archive2 tool.

        This method utilizes the process runner to execute the Archive2 tool with the
        appropriate arguments to perform the extraction. The extraction process is
        monitored for success, and a log message is recorded accordingly.

        :param archive_path: Path to the archive file to be extracted.
        :param output_dir: Directory where the extracted contents will be stored.
        :return: True if the archive was successfully extracted, False otherwise.
        :rtype: bool
        """
        args: list[str] = [str(self.tool_path), str(archive_path), f"-extract={output_dir}"]

        success: bool = self.process_runner.execute(args, timeout=300)

        if success:
            logger.success(f"Archive extracted successfully to {output_dir}")
            return True
        logger.error("Archive2 extraction failed")
        return False

    def _extract_bsarch(self, archive_path: Path, output_dir: Path) -> bool:
        """
        Extracts the contents of an archive using the BSArch tool.

        This method invokes the BSArch tool with the provided archive path and
        output directory using the process_runner. It returns a boolean indicating
        the success of the extraction operation. In case of a success, the archive
        contents are extracted to the specified output directory. Otherwise, an
        error message is logged.

        :param archive_path: The path to the archive file that needs to be extracted.
        :param output_dir: The directory where the extracted contents will be placed.
        :return: True if the extraction succeeds, False otherwise.
        :rtype: bool
        """
        args: list[str] = [str(self.tool_path), "unpack", str(archive_path), str(output_dir)]

        success: bool = self.process_runner.execute(args, timeout=300)

        if success:
            logger.success(f"Archive extracted successfully to {output_dir}")
            return True
        logger.error("BSArch extraction failed")
        return False
