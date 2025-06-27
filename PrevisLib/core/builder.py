"""Main builder orchestration for previs generation."""

from datetime import datetime
from pathlib import Path

from loguru import logger

from ..config.settings import Settings
from ..models.data_classes import ArchiveTool, BuildStep
from ..tools import ArchiveWrapper, CKPEConfigHandler, CreationKitWrapper, XEditWrapper
from ..utils import file_system as fs


class PrevisBuilder:
    """Main orchestrator for the previs build process."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.plugin_name = settings.plugin_name
        self.build_mode = settings.build_mode
        self.start_time = None
        self.current_step = None
        self.completed_steps = []
        self.failed_step = None
        
        # Initialize tool wrappers
        self.ck_wrapper = CreationKitWrapper(
            settings.tool_paths.creation_kit,
            self.plugin_name,
            self.build_mode
        )
        
        self.xedit_wrapper = XEditWrapper(
            settings.tool_paths.xedit,
            self.plugin_name
        )
        
        # Choose archive tool
        if settings.archive_tool == ArchiveTool.BSARCH:
            self.archive_wrapper = ArchiveWrapper(
                ArchiveTool.BSARCH,
                settings.tool_paths.bsarch
            )
        else:
            self.archive_wrapper = ArchiveWrapper(
                ArchiveTool.ARCHIVE2,
                settings.tool_paths.archive2
            )
            
        # CKPE config handler
        self.ckpe_handler = CKPEConfigHandler(settings.tool_paths.fallout4)
        
        # Paths
        self.fo4_path = settings.tool_paths.fallout4
        self.data_path = self.fo4_path / "Data"
        self.output_path = self.data_path / "PreCombined"
        self.temp_path = self.data_path / "Temp"
        
    def _get_plugin_base_name(self) -> str:
        """Extract base name from plugin, validating extension.
        
        Returns:
            Base name without extension
            
        Raises:
            ValueError: If plugin has invalid extension
        """
        valid_extensions = {'.esp', '.esm', '.esl'}
        
        # Check if plugin has a valid extension
        plugin_path = Path(self.plugin_name)
        extension = plugin_path.suffix.lower()
        
        if extension not in valid_extensions:
            raise ValueError(
                f"Invalid plugin extension '{extension}'. "
                f"Must be one of: {', '.join(valid_extensions)}"
            )
            
        return plugin_path.stem
        
    def build(self, start_from_step: BuildStep | None = None) -> bool:
        """Execute the full build process.
        
        Args:
            start_from_step: Optional step to resume from
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting previs build for {self.plugin_name}")
        logger.info(f"Build mode: {self.build_mode.value}")
        self.start_time = datetime.now()
        
        # Load CKPE config if available
        plugin_base = self._get_plugin_base_name()
        ckpe_config = self.ckpe_handler.load_config(plugin_base)
        if ckpe_config:
            self.settings.ckpe_config = ckpe_config
            logger.info("Loaded CKPE configuration")
        
        # Determine which steps to run
        steps_to_run = self._get_steps_to_run(start_from_step)
        
        # Execute each step
        for step in steps_to_run:
            self.current_step = step
            logger.info(f"Executing step: {step}")
            
            try:
                success = self._execute_step(step)
                
                if success:
                    self.completed_steps.append(step)
                    logger.success(f"Completed step: {step}")
                else:
                    self.failed_step = step
                    logger.error(f"Failed at step: {step}")
                    return False
                    
            except Exception as e:
                self.failed_step = step
                logger.error(f"Exception during step {step}: {e}")
                return False
                
        # Build completed successfully
        elapsed = datetime.now() - self.start_time
        logger.success(f"Build completed successfully in {elapsed}")
        return True
        
    def _get_steps_to_run(self, start_from: BuildStep | None) -> list[BuildStep]:
        """Get the list of steps to run based on start point.
        
        Args:
            start_from: Optional step to start from
            
        Returns:
            List of steps to execute
        """
        all_steps = list(BuildStep)
        
        if start_from is None:
            return all_steps
            
        try:
            start_index = all_steps.index(start_from)
            return all_steps[start_index:]
        except ValueError:
            logger.warning(f"Invalid start step: {start_from}, running all steps")
            return all_steps
            
    def _execute_step(self, step: BuildStep) -> bool:
        """Execute a single build step.
        
        Args:
            step: The build step to execute
            
        Returns:
            True if successful, False otherwise
        """
        step_map = {
            BuildStep.GENERATE_PRECOMBINED: self._step_generate_precombined,
            BuildStep.MERGE_COMBINED_OBJECTS: self._step_merge_combined_objects,
            BuildStep.ARCHIVE_MESHES: self._step_archive_meshes,
            BuildStep.COMPRESS_PSG: self._step_compress_psg,
            BuildStep.BUILD_CDX: self._step_build_cdx,
            BuildStep.GENERATE_PREVIS: self._step_generate_previs,
            BuildStep.MERGE_PREVIS: self._step_merge_previs,
            BuildStep.FINAL_PACKAGING: self._step_final_packaging
        }
        
        step_func = step_map.get(step)
        if step_func:
            return step_func()
        logger.error(f"No implementation for step: {step}")
        return False
            
    def _step_generate_precombined(self) -> bool:
        """Step 1: Generate precombined meshes."""
        logger.info("Step 1: Generating precombined meshes")
        
        # Clean output directory
        fs.clean_directory(self.output_path)
        
        # Run Creation Kit
        success = self.ck_wrapper.generate_precombined(
            self.data_path,
            self.output_path
        )
        
        if success:
            # Check if files were generated
            mesh_count = fs.count_files(self.output_path, "*.nif", recursive=True)
            if mesh_count == 0:
                logger.error("No precombined meshes were generated")
                return False
            logger.info(f"Generated {mesh_count} precombined mesh files")
            
            # Check for CombinedObjects.esp output file
            combined_objects_path = self.data_path / "CombinedObjects.esp"
            if not fs.wait_for_output_file(combined_objects_path, timeout=60.0, check_interval=1.0):
                logger.error("CombinedObjects.esp was not created by Creation Kit")
                raise FileNotFoundError
            logger.info("CombinedObjects.esp successfully created")
            
        return success
        
    def _step_merge_combined_objects(self) -> bool:
        """Step 2: Merge combined objects using xEdit."""
        logger.info("Step 2: Merging combined objects")
        
        # Find the merge script
        script_path = self._find_xedit_script("Merge Combined Objects")
        if not script_path:
            logger.error("Could not find Merge Combined Objects script")
            return False
            
        # Run xEdit merge
        return self.xedit_wrapper.merge_combined_objects(
            self.data_path,
            script_path
        )
        
    def _step_archive_meshes(self) -> bool:
        """Step 3: Archive precombined meshes."""
        logger.info("Step 3: Archiving precombined meshes")
        
        plugin_base = self._get_plugin_base_name()
        archive_path = self.data_path / f"{plugin_base} - Geometry.ba2"
        
        # Create archive from precombined directory
        success = self.archive_wrapper.create_archive(
            archive_path,
            self.output_path,
            compress=True
        )
        
        if success:
            # Clean up loose files after archiving
            fs.clean_directory(self.output_path, create=False)
            logger.info(f"Created archive: {archive_path.name}")
            
        return success
        
    def _step_compress_psg(self) -> bool:
        """Step 4: Compress PSG files."""
        logger.info("Step 4: Compressing PSG files")
        
        return self.ck_wrapper.compress_psg(self.data_path)
        
    def _step_build_cdx(self) -> bool:
        """Step 5: Build CDX files."""
        logger.info("Step 5: Building CDX files")
        
        return self.ck_wrapper.build_cdx(self.data_path)
        
    def _step_generate_previs(self) -> bool:
        """Step 6: Generate visibility data."""
        logger.info("Step 6: Generating visibility data")
        
        # Clean temp directory for previs output
        fs.clean_directory(self.temp_path)
        
        # Run Creation Kit
        success = self.ck_wrapper.generate_previs_data(
            self.data_path,
            self.temp_path
        )
        
        if success:
            # Check if files were generated
            vis_count = fs.count_files(self.temp_path, "*.uvd", recursive=True)
            if vis_count == 0:
                logger.error("No visibility data files were generated")
                return False
            logger.info(f"Generated {vis_count} visibility data files")
            
            # Check for Previs.esp output file
            previs_path = self.data_path / "Previs.esp"
            if not fs.wait_for_output_file(previs_path, timeout=120.0, check_interval=2.0):
                logger.error("Previs.esp was not created by Creation Kit")
                raise FileNotFoundError
            logger.info("Previs.esp successfully created")
            
        return success
        
    def _step_merge_previs(self) -> bool:
        """Step 7: Merge previs data using xEdit."""
        logger.info("Step 7: Merging previs data")
        
        # Find the merge script
        script_path = self._find_xedit_script("Merge Previs")
        if not script_path:
            logger.error("Could not find Merge Previs script")
            return False
            
        # Run xEdit merge
        return self.xedit_wrapper.merge_previs(
            self.data_path,
            script_path
        )
        
    def _step_final_packaging(self) -> bool:
        """Step 8: Final packaging and cleanup."""
        logger.info("Step 8: Final packaging")
        
        plugin_base = self._get_plugin_base_name()
        vis_archive_path = self.data_path / f"{plugin_base} - Vis.ba2"
        
        # Archive visibility data
        if self.temp_path.exists() and not fs.is_directory_empty(self.temp_path):
            success = self.archive_wrapper.create_archive(
                vis_archive_path,
                self.temp_path,
                compress=True
            )
            
            if not success:
                logger.error("Failed to create visibility archive")
                return False
                
            # Clean up temp directory
            fs.clean_directory(self.temp_path, create=False)
            logger.info(f"Created archive: {vis_archive_path.name}")
            
        # Verify final output
        geometry_archive = self.data_path / f"{plugin_base} - Geometry.ba2"
        if not geometry_archive.exists():
            logger.error("Geometry archive not found")
            return False
            
        if not vis_archive_path.exists():
            logger.error("Visibility archive not found")
            return False
            
        logger.success("All previs files packaged successfully")
        return True
        
    def _find_xedit_script(self, script_name: str) -> Path | None:
        """Find an xEdit script by name.
        
        Args:
            script_name: Name of the script to find
            
        Returns:
            Path to the script if found, None otherwise
        """
        # Common script locations
        possible_paths = [
            self.settings.tool_paths.xedit.parent / "Edit Scripts",
            self.data_path / "Edit Scripts",
            self.fo4_path / "Edit Scripts"
        ]
        
        for base_path in possible_paths:
            if base_path.exists():
                # Try different extensions
                for ext in ['.pas', '.psc', '.txt']:
                    script_path = base_path / f"{script_name}{ext}"
                    if script_path.exists():
                        return script_path
                        
        return None
        
    def get_resume_options(self) -> list[BuildStep]:
        """Get list of steps that can be resumed from.
        
        Returns:
            List of valid resume steps
        """
        if self.failed_step:
            # Can resume from the failed step or any step after
            all_steps = list(BuildStep)
            failed_index = all_steps.index(self.failed_step)
            return all_steps[failed_index:]
        # Can start from any step
        return list(BuildStep)
            
    def cleanup(self) -> bool:
        """Clean up all generated files and directories.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Cleaning up previs files")
        
        plugin_base = self._get_plugin_base_name()
        
        # Files to delete
        files_to_clean = [
            self.data_path / f"{plugin_base} - Geometry.ba2",
            self.data_path / f"{plugin_base} - Vis.ba2",
            self.data_path / f"{plugin_base}.psg"
        ]
        
        # Directories to clean
        dirs_to_clean = [
            self.output_path,
            self.temp_path
        ]
        
        success = True
        
        # Delete files
        for file_path in files_to_clean:
            if file_path.exists():
                if fs.safe_delete(file_path):
                    logger.info(f"Deleted: {file_path.name}")
                else:
                    logger.error(f"Failed to delete: {file_path.name}")
                    success = False
                    
        # Clean directories
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                fs.clean_directory(dir_path, create=False)
                logger.info(f"Cleaned directory: {dir_path.name}")
                
        return success