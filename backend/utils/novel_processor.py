import re
from typing import List, Dict, Optional
import jieba
import MeCab
from langdetect import detect
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize


class NovelProcessor:
    """Utility class for processing novel text content."""
    
    def __init__(self):
        # Initialize language-specific tools
        self.mecab = None
        try:
            self.mecab = MeCab.Tagger()
        except:
            pass  # MeCab not available
        
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the text."""
        try:
            return detect(text)
        except:
            return "en"  # Default to English
    
    def extract_chapters(self, text: str) -> List[str]:
        """Extract chapters from novel text."""
        # Common chapter patterns
        chapter_patterns = [
            r'第\s*[一二三四五六七八九十百千万\d]+\s*[章节回]',  # Chinese
            r'Chapter\s+\d+',  # English
            r'第\d+話',  # Japanese
            r'CHAPTER\s+\d+',  # English uppercase
            r'\n\s*\d+\s*\n',  # Simple number
        ]
        
        # Try to find chapter breaks
        chapters = []
        current_chapter = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a chapter header
            is_chapter_header = False
            for pattern in chapter_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_chapter_header = True
                    break
            
            if is_chapter_header and current_chapter:
                # Save previous chapter
                chapters.append(current_chapter.strip())
                current_chapter = line + '\n'
            else:
                current_chapter += line + '\n'
        
        # Add the last chapter
        if current_chapter:
            chapters.append(current_chapter.strip())
        
        # If no chapters found, split by length
        if len(chapters) <= 1:
            chapters = self._split_by_length(text)
        
        return chapters
    
    def _split_by_length(self, text: str, max_length: int = 3000) -> List[str]:
        """Split text into chunks by length."""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_key_phrases(self, text: str, language: str = None) -> List[str]:
        """Extract key phrases from text for illustration prompts."""
        if not language:
            language = self.detect_language(text)
        
        key_phrases = []
        
        if language == 'zh':
            # Chinese text processing
            words = jieba.cut(text)
            # Filter for nouns and adjectives (simplified)
            key_phrases = [word for word in words if len(word) > 1 and word.isalpha()]
        
        elif language == 'ja' and self.mecab:
            # Japanese text processing
            parsed = self.mecab.parse(text)
            lines = parsed.split('\n')
            for line in lines:
                if '\t' in line:
                    word, features = line.split('\t', 1)
                    if '名詞' in features or '形容詞' in features:  # Nouns or adjectives
                        key_phrases.append(word)
        
        else:
            # English and other languages
            words = word_tokenize(text.lower())
            # Simple filtering for meaningful words
            key_phrases = [word for word in words if len(word) > 3 and word.isalpha()]
        
        # Remove duplicates and limit
        return list(set(key_phrases))[:20]
    
    def extract_scene_descriptions(self, text: str) -> List[str]:
        """Extract scene descriptions for illustration generation."""
        # Look for descriptive sentences
        sentences = sent_tokenize(text)
        scene_descriptions = []
        
        # Keywords that often indicate scene descriptions
        scene_keywords = [
            'room', 'house', 'building', 'street', 'forest', 'mountain', 'ocean',
            'sky', 'sunset', 'sunrise', 'night', 'day', 'dark', 'bright',
            'beautiful', 'magnificent', 'ancient', 'modern', 'old', 'new',
            '房间', '房子', '建筑', '街道', '森林', '山', '海洋', '天空',
            '部屋', '家', '建物', '道', '森', '山', '海', '空'
        ]
        
        for sentence in sentences:
            # Check if sentence contains scene keywords
            if any(keyword in sentence.lower() for keyword in scene_keywords):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    scene_descriptions.append(sentence.strip())
        
        return scene_descriptions[:5]  # Limit to 5 descriptions
    
    def extract_character_descriptions(self, text: str) -> List[Dict[str, str]]:
        """Extract character descriptions."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated NLP
        
        characters = []
        sentences = sent_tokenize(text)
        
        # Look for sentences with character description patterns
        character_patterns = [
            r'(he|she|they)\s+(was|were|is|are)\s+.*?(tall|short|beautiful|handsome|young|old)',
            r'(他|她|它)\s*.*?(高|矮|美|帅|年轻|老)',
            r'(彼|彼女)\s*.*?(高い|低い|美しい|若い|古い)'
        ]
        
        for sentence in sentences:
            for pattern in character_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    characters.append({
                        "description": sentence.strip(),
                        "type": "character"
                    })
                    break
        
        return characters[:3]  # Limit to 3 characters
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff.,!?;:()"\'-]', '', text)
        
        return text.strip()
    
    def get_text_summary(self, text: str, max_length: int = 200) -> str:
        """Get a summary of the text."""
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 2:
            return text[:max_length]
        
        # Take first and last sentences, plus middle if space allows
        summary = sentences[0]
        if len(summary) < max_length - 50 and len(sentences) > 2:
            summary += " " + sentences[-1]
        
        return summary[:max_length] + "..." if len(summary) > max_length else summary
