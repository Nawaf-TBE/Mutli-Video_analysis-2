"""
Section generation for video content using AI.

This module provides intelligent video section generation using LangChain
and AI-powered analysis of video transcripts. It creates meaningful
section breaks based on content analysis and topic changes.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .qa_manager import QAManager, QAConfig

# Configure logging
logger = logging.getLogger(__name__)


class SectionStrategy(Enum):
    """Strategies for section generation."""
    AI_ANALYSIS = "ai_analysis"
    TIME_BASED = "time_based"
    FALLBACK = "fallback"


@dataclass
class SectionConfig:
    """Configuration for section generation."""
    min_sections: int = 3
    max_sections: int = 8
    default_duration: int = 300  # 5 minutes in seconds
    min_section_duration: int = 30  # Minimum 30 seconds per section
    strategy: SectionStrategy = SectionStrategy.AI_ANALYSIS
    qa_config: Optional[QAConfig] = None


@dataclass
class Section:
    """Represents a video section."""
    title: str
    start_time: float
    end_time: float
    duration: float
    confidence: float = 1.0
    strategy_used: SectionStrategy = SectionStrategy.AI_ANALYSIS


@dataclass
class SectionGenerationResult:
    """Result of section generation."""
    success: bool
    sections: List[Section]
    total_duration: float
    strategy_used: SectionStrategy
    processing_time: Optional[float] = None
    error_message: Optional[str] = None


class SectionGenerator:
    """
    Generates intelligent video sections using AI.
    
    This class analyzes video transcripts to create meaningful section breaks
    based on content analysis, topic changes, and natural speech patterns.
    """
    
    # Default prompt template for section generation
    SECTION_PROMPT_TEMPLATE = """Analyze this video transcript and create 3-8 main sections that best organize the content.

For each section, provide a clear, descriptive title (3-8 words) that captures the main topic.

Look for natural breaks in content, topic changes, or different phases of discussion.

Format your response as a numbered list like this:
1. Introduction and Overview
2. Main Topic Discussion  
3. Key Examples and Case Studies
4. Practical Applications
5. Summary and Conclusions

Only provide the titles, one per line, numbered. Do not include any other text."""

    # Fallback section templates
    FALLBACK_SECTIONS = [
        "Introduction",
        "Main Content", 
        "Key Points",
        "Conclusion"
    ]
    
    DEFAULT_SECTIONS = [
        "Video Introduction",
        "Main Discussion",
        "Key Points", 
        "Summary"
    ]
    
    def __init__(self, config: Optional[SectionConfig] = None):
        """
        Initialize the section generator.
        
        Args:
            config: Optional configuration object. If None, uses default settings.
        """
        self.config = config or SectionConfig()
        self.qa_manager = QAManager(self.config.qa_config)
        
        logger.info(f"SectionGenerator initialized with strategy: {self.config.strategy.value}")
    
    def _create_section_prompt(self) -> str:
        """Create the prompt for section generation."""
        return self.SECTION_PROMPT_TEMPLATE
    
    def generate_sections(self, video_id: int, duration: Optional[float] = None) -> SectionGenerationResult:
        """
        Generate intelligent sections for a video.
        
        Args:
            video_id: The ID of the video to generate sections for.
            duration: Optional video duration in seconds. If None, uses default.
            
        Returns:
            SectionGenerationResult with generated sections and metadata.
        """
        import time
        start_time = time.time()
        
        logger.info(f"Generating sections for video {video_id}")
        
        # Determine video duration
        total_duration = duration or self.config.default_duration
        
        try:
            # Try AI-based section generation first
            if self.config.strategy == SectionStrategy.AI_ANALYSIS:
                result = self._generate_sections_with_ai(video_id, total_duration)
                if result.success:
                    processing_time = time.time() - start_time
                    result.processing_time = processing_time
                    return result
            
            # Fallback to time-based generation
            logger.warning(f"AI section generation failed for video {video_id}, using time-based fallback")
            result = self._generate_sections_time_based(total_duration)
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error generating sections: {str(e)}"
            logger.error(error_msg)
            
            return SectionGenerationResult(
                success=False,
                sections=self._create_fallback_sections(total_duration),
                total_duration=total_duration,
                strategy_used=SectionStrategy.FALLBACK,
                processing_time=processing_time,
                error_message=error_msg
            )
    
    def _generate_sections_with_ai(self, video_id: int, duration: float) -> SectionGenerationResult:
        """Generate sections using AI analysis."""
        qa_chain = self.qa_manager.get_qa_chain(video_id)
        
        if not qa_chain:
            logger.warning(f"No QA chain available for video {video_id}")
            return SectionGenerationResult(
                success=False,
                sections=[],
                total_duration=duration,
                strategy_used=SectionStrategy.AI_ANALYSIS,
                error_message="No QA chain available"
            )
        
        try:
            # Use the structured prompt
            sections_query = self._create_section_prompt()
            result = qa_chain({"query": sections_query})
            answer = result["result"]
            
            # Parse AI response
            section_titles = self._parse_ai_response(answer)
            
            if not section_titles:
                logger.warning("Failed to parse AI response, using fallback")
                return SectionGenerationResult(
                    success=False,
                    sections=[],
                    total_duration=duration,
                    strategy_used=SectionStrategy.AI_ANALYSIS,
                    error_message="Failed to parse AI response"
                )
            
            # Create sections with timing
            sections = self._create_sections_with_timing(section_titles, duration, SectionStrategy.AI_ANALYSIS)
            
            return SectionGenerationResult(
                success=True,
                sections=sections,
                total_duration=duration,
                strategy_used=SectionStrategy.AI_ANALYSIS
            )
            
        except Exception as e:
            logger.error(f"Error in AI section generation: {e}")
            return SectionGenerationResult(
                success=False,
                sections=[],
                total_duration=duration,
                strategy_used=SectionStrategy.AI_ANALYSIS,
                error_message=str(e)
            )
    
    def _generate_sections_time_based(self, duration: float) -> SectionGenerationResult:
        """Generate sections based on time intervals."""
        logger.info("Using time-based section generation")
        
        # Calculate number of sections based on duration
        num_sections = max(
            self.config.min_sections,
            min(self.config.max_sections, int(duration / self.config.min_section_duration))
        )
        
        section_duration = duration / num_sections
        sections = []
        
        for i in range(num_sections):
            start_time = i * section_duration
            end_time = (i + 1) * section_duration
            
            # Use different titles based on position
            if i == 0:
                title = "Introduction"
            elif i == num_sections - 1:
                title = "Conclusion"
            else:
                title = f"Section {i + 1}"
            
            sections.append(Section(
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration=section_duration,
                confidence=0.8,
                strategy_used=SectionStrategy.TIME_BASED
            ))
        
        return SectionGenerationResult(
            success=True,
            sections=sections,
            total_duration=duration,
            strategy_used=SectionStrategy.TIME_BASED
        )
    
    def _parse_ai_response(self, response: str) -> List[str]:
        """Parse AI response to extract section titles."""
        section_titles = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering and clean up
            cleaned_line = self._clean_section_title(line)
            
            # Validate title
            if self._is_valid_section_title(cleaned_line):
                section_titles.append(cleaned_line)
        
        # Ensure we have the right number of sections
        if len(section_titles) < self.config.min_sections:
            logger.warning(f"Only found {len(section_titles)} sections, using fallback")
            return []
        
        return section_titles[:self.config.max_sections]
    
    def _clean_section_title(self, title: str) -> str:
        """Clean and normalize section title."""
        # Remove numbering (1., 2., etc.)
        if re.match(r'^\d+\.', title):
            title = re.sub(r'^\d+\.\s*', '', title)
        elif title.startswith('-') or title.startswith('•'):
            title = title[1:].strip()
        
        # Clean up extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _is_valid_section_title(self, title: str) -> bool:
        """Validate if a title is suitable for a section."""
        if not title or len(title) < 3:
            return False
        
        if len(title) > 100:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^\d+$',  # Just numbers
            r'^[^\w\s]+$',  # Only special characters
            r'^(section|part|chapter)\s*\d+$',  # Generic section names
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return False
        
        return True
    
    def _create_sections_with_timing(self, titles: List[str], duration: float, strategy: SectionStrategy) -> List[Section]:
        """Create Section objects with proper timing."""
        sections = []
        section_duration = duration / len(titles)
        
        for i, title in enumerate(titles):
            start_time = i * section_duration
            end_time = (i + 1) * section_duration
            
            sections.append(Section(
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration=section_duration,
                confidence=1.0 if strategy == SectionStrategy.AI_ANALYSIS else 0.8,
                strategy_used=strategy
            ))
        
        return sections
    
    def _create_fallback_sections(self, duration: float) -> List[Section]:
        """Create fallback sections when all else fails."""
        titles = self.FALLBACK_SECTIONS
        return self._create_sections_with_timing(titles, duration, SectionStrategy.FALLBACK)
    
    def generate_sections_legacy(self, video_id: int) -> List[Dict[str, Any]]:
        """
        Legacy method for backward compatibility.
        
        Args:
            video_id: The ID of the video to generate sections for.
            
        Returns:
            List of dictionaries with section information (legacy format).
        """
        result = self.generate_sections(video_id)
        
        # Convert to legacy format
        legacy_sections = []
        for section in result.sections:
            legacy_sections.append({
                "title": section.title,
                "start_time": section.start_time,
                "end_time": section.end_time
            })
        
        return legacy_sections
    
    def update_config(self, new_config: SectionConfig) -> None:
        """
        Update the configuration.
        
        Args:
            new_config: New configuration object.
        """
        self.config = new_config
        if new_config.qa_config:
            self.qa_manager.update_config(new_config.qa_config)
        logger.info("SectionGenerator configuration updated")
    
    def get_section_at_time(self, sections: List[Section], timestamp: float) -> Optional[Section]:
        """
        Get the section that contains a specific timestamp.
        
        Args:
            sections: List of sections to search in.
            timestamp: Time in seconds to find section for.
            
        Returns:
            Section containing the timestamp, or None if not found.
        """
        for section in sections:
            if section.start_time <= timestamp < section.end_time:
                return section
        return None
    
    def validate_sections(self, sections: List[Section]) -> Tuple[bool, List[str]]:
        """
        Validate a list of sections for consistency.
        
        Args:
            sections: List of sections to validate.
            
        Returns:
            Tuple of (is_valid, list_of_issues).
        """
        issues = []
        
        if not sections:
            issues.append("No sections provided")
            return False, issues
        
        # Check for overlapping sections
        for i, section in enumerate(sections):
            if section.start_time >= section.end_time:
                issues.append(f"Section {i} has invalid timing: start >= end")
            
            if section.duration <= 0:
                issues.append(f"Section {i} has zero or negative duration")
            
            # Check for overlaps with next section
            if i < len(sections) - 1:
                next_section = sections[i + 1]
                if section.end_time > next_section.start_time:
                    issues.append(f"Sections {i} and {i+1} overlap")
        
        # Check total coverage
        total_duration = sections[-1].end_time - sections[0].start_time
        expected_duration = sum(section.duration for section in sections)
        
        if abs(total_duration - expected_duration) > 0.1:  # Allow small floating point errors
            issues.append("Section durations don't match total duration")
        
        return len(issues) == 0, issues
    
    def merge_sections(self, sections: List[Section], max_sections: int) -> List[Section]:
        """
        Merge sections to reduce the total number.
        
        Args:
            sections: List of sections to merge.
            max_sections: Maximum number of sections after merging.
            
        Returns:
            List of merged sections.
        """
        if len(sections) <= max_sections:
            return sections
        
        # Simple merging strategy: combine adjacent sections
        merged = []
        sections_per_merge = len(sections) // max_sections
        
        for i in range(0, len(sections), sections_per_merge):
            group = sections[i:i + sections_per_merge]
            
            if group:
                # Create merged section
                merged_section = Section(
                    title=f"{group[0].title} & More",
                    start_time=group[0].start_time,
                    end_time=group[-1].end_time,
                    duration=group[-1].end_time - group[0].start_time,
                    confidence=min(section.confidence for section in group),
                    strategy_used=group[0].strategy_used
                )
                merged.append(merged_section)
        
        return merged 