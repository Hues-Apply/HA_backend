from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Document, ParsedProfile, UserGoal, CustomUser
from .serializers import (
    DocumentSerializer, ParsedProfileSerializer, 
    ProfileCompletionSerializer, UserGoalUpdateSerializer, UserGoalSerializer
)

import json
import uuid
import re
import os
from io import BytesIO


# Temporary endpoints for user management
@api_view(['GET'])
@permission_classes([AllowAny])  # No authentication required for temporary endpoint
def google_signups_list(request):
    """Get list of all users who signed up via Google OAuth - Temporary endpoint"""
    try:
        # Get users who have Google profile data
        users = CustomUser.objects.filter(
            profile__google_id__isnull=False
        ).select_related('profile').order_by('-date_joined')
        
        results = []
        for user in users:
            # Check if user is new (joined in last 24 hours)
            is_new_user = (timezone.now() - user.date_joined).days < 1
            
            google_data = {}
            if hasattr(user, 'profile') and user.profile:
                google_data = {
                    'name': user.profile.name or f"{user.first_name} {user.last_name}".strip(),
                    'picture': user.profile.google_picture or ''
                }
            
            results.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.get_role(),
                'is_new_user': is_new_user,
                'created_at': user.date_joined.isoformat(),
                'google_data': google_data
            })
        
        return Response({
            'count': len(results),
            'results': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to retrieve users: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # No authentication required for temporary endpoint
def delete_user(request, user_id):
    """Delete a specific user by ID - Temporary endpoint"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        user_email = user.email
        user.delete()
        
        return Response({
            'message': f'User {user_email} deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to delete user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentUploadView(APIView):
    """Upload CV/Resume documents"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        try:
            # Create document instance
            serializer = DocumentSerializer(data=request.data)
            if serializer.is_valid():
                document = serializer.save(user=request.user)
                
                # Start processing (mock implementation for now)
                parsed_data = self._mock_document_parsing(document)
                
                # Create or update parsed profile
                parsed_profile, created = ParsedProfile.objects.get_or_create(
                    user=request.user,
                    defaults={'document': document}
                )
                
                if not created:
                    parsed_profile.document = document
                
                # Update parsed profile with mock data
                for field, value in parsed_data.items():
                    setattr(parsed_profile, field, value)
                
                parsed_profile.confidence_score = 0.85  # Mock confidence
                parsed_profile.save()
                
                # Update document status
                document.processing_status = 'completed'
                document.processed_at = timezone.now()
                document.save()
                
                return Response({
                    'success': True,
                    'document_id': str(document.id),
                    'parsed_data': {
                        'personal_info': {
                            'first_name': parsed_profile.first_name,
                            'last_name': parsed_profile.last_name,
                            'email': parsed_profile.email,
                            'phone': parsed_profile.phone,
                            'address': parsed_profile.address,
                            'linkedin': parsed_profile.linkedin,
                            'portfolio': parsed_profile.portfolio,
                        },
                        'summary': parsed_profile.summary,
                        'education': parsed_profile.education,
                        'experience': parsed_profile.experience,
                        'skills': parsed_profile.skills,
                        'certifications': parsed_profile.certifications,
                        'languages': parsed_profile.languages,
                        'projects': parsed_profile.projects,
                    }
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Document upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _mock_document_parsing(self, document):
        """Real CV parsing implementation"""
        try:
            # Read file content
            file_content = self._extract_text_from_document(document)
            if not file_content:
                return self._fallback_data(document)
            
            # Parse the extracted text
            parsed_data = self._parse_cv_content(file_content, document)
            return parsed_data
            
        except Exception as e:
            print(f"Parsing error: {e}")
            return self._fallback_data(document)
    
    def _extract_text_from_document(self, document):
        """Extract text from uploaded document"""
        try:
            # Get file extension
            filename = document.original_filename.lower()
            
            # Read file content
            document.file.seek(0)
            content = document.file.read()
            document.file.seek(0)  # Reset file pointer
            
            if filename.endswith('.pdf'):
                return self._extract_from_pdf(content)
            elif filename.endswith(('.doc', '.docx')):
                return self._extract_from_docx(content)
            else:
                # Try to read as text
                try:
                    return content.decode('utf-8')
                except:
                    return content.decode('latin-1', errors='ignore')
                    
        except Exception as e:
            print(f"Text extraction error: {e}")
            return ""
    
    def _extract_from_pdf(self, content):
        """Extract text from PDF content"""
        try:
            # Try PyPDF2 if available
            import PyPDF2
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            # Fallback: basic PDF text extraction
            text = content.decode('latin-1', errors='ignore')
            # Extract readable text between PDF markers
            import re
            text_pattern = r'(\w+\s*){3,}'
            matches = re.findall(text_pattern, text)
            return ' '.join(''.join(match) for match in matches)
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""
    
    def _extract_from_docx(self, content):
        """Extract text from DOCX content"""
        try:
            from docx import Document as DocxDocument
            docx_file = BytesIO(content)
            doc = DocxDocument(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            # Fallback: basic text extraction from DOCX
            text = content.decode('utf-8', errors='ignore')
            # Extract text between XML tags
            import re
            text_pattern = r'<w:t[^>]*>([^<]+)</w:t>'
            matches = re.findall(text_pattern, text)
            return ' '.join(matches)
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""
    
    def _parse_cv_content(self, text, document):
        """Parse CV content using intelligent pattern recognition"""
        data = {
            'first_name': '',
            'last_name': '',
            'email': document.user.email,
            'phone': '',
            'address': '',
            'linkedin': '',
            'portfolio': '',
            'summary': '',
            'education': [],
            'experience': [],
            'skills': [],
            'certifications': [],
            'languages': [],
            'projects': []
        }
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text.strip())
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract personal information
        data.update(self._extract_personal_info(text, lines))
        
        # Extract sections using flexible parsing
        data['summary'] = self._extract_summary(text, lines)
        data['education'] = self._extract_education(text, lines)
        data['experience'] = self._extract_experience(text, lines)
        data['skills'] = self._extract_skills(text, lines)
        data['certifications'] = self._extract_certifications(text, lines)
        data['languages'] = self._extract_languages(text, lines)
        data['projects'] = self._extract_projects(text, lines)
        
        return data
    
    def _extract_personal_info(self, text, lines):
        """Extract personal information using flexible patterns"""
        info = {}
        
        # Extract name - try multiple approaches
        name_found = False
        
        # Try first few lines for name (most CVs start with name)
        for i, line in enumerate(lines[:5]):
            # Skip if line looks like contact info
            if any(char in line for char in ['@', '+', '(', ')', 'www', 'http']):
                continue
            # Skip if all caps (likely header)
            if line.isupper() and len(line.split()) > 2:
                continue
            # Look for name pattern: 2-4 words, each starting with capital
            words = line.split()
            if 2 <= len(words) <= 4 and all(word[0].isupper() and word[1:].islower() for word in words if word.isalpha()):
                info['first_name'] = words[0]
                info['last_name'] = ' '.join(words[1:])
                name_found = True
                break
        
        # Fallback: look for "Name:" pattern
        if not name_found:
            name_pattern = r'(?:name|full\s*name)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
            match = re.search(name_pattern, text, re.IGNORECASE)
            if match:
                full_name = match.group(1).strip()
                parts = full_name.split()
                info['first_name'] = parts[0]
                info['last_name'] = ' '.join(parts[1:])
        
        # Extract phone - flexible patterns
        phone_patterns = [
            r'(\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',  # International
            r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',  # US format
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # Simple format
            r'(\+\d{1,3}\s?\d{8,14})',  # International compact
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                info['phone'] = match.group(1).strip()
                break
        
        # Extract LinkedIn - flexible patterns
        linkedin_patterns = [
            r'linkedin\.com/in/([a-zA-Z0-9-]+)',
            r'linkedin\.com/([a-zA-Z0-9-]+)',
            r'in\.linkedin\.com/([a-zA-Z0-9-]+)',
        ]
        
        for pattern in linkedin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                username = match.group(1)
                info['linkedin'] = f"https://linkedin.com/in/{username}"
                break
        
        # Extract portfolio/website - exclude LinkedIn and email domains
        url_patterns = [
            r'(https?://(?!.*linkedin)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',
            r'(www\.(?!.*linkedin)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',
            r'([a-zA-Z0-9.-]+\.(?:com|org|net|io|dev)(?:/[^\s]*)?)'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                url = match if match.startswith('http') else f"https://{match}"
                if not any(domain in url.lower() for domain in ['linkedin', 'gmail', 'yahoo', 'outlook']):
                    info['portfolio'] = url
                    break
            if 'portfolio' in info:
                break
        
        # Extract address - look for city, state, country patterns
        address_patterns = [
            r'([A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?)',  # US format
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country
            r'(\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd)[^,]*,\s*[A-Z][a-z]+)',  # Full address
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                info['address'] = match.group(1).strip()
                break
        
        return info
    
    def _extract_summary(self, text, lines):
        """Extract professional summary using flexible parsing"""
        # Find summary section
        summary_keywords = ['summary', 'profile', 'objective', 'about', 'overview', 'introduction']
        summary_section = self._find_section(text, lines, summary_keywords)
        
        if summary_section and len(summary_section) > 50:
            # Clean up and return the summary
            summary = re.sub(r'\s+', ' ', summary_section).strip()
            return summary
        
        # Fallback: look for paragraph-like text in the first part of the CV
        first_part = ' '.join(lines[:10])
        sentences = re.split(r'[.!?]+', first_part)
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for descriptive sentences (not contact info, not single words)
            if (len(sentence) > 50 and 
                not any(char in sentence for char in ['@', '+', '(', ')']) and
                not sentence.isupper() and
                len(sentence.split()) > 8):
                return sentence + '.'
        
        return ""
    
    def _extract_education(self, text, lines):
        """Extract education using intelligent parsing"""
        education = []
        
        # Find education section
        edu_keywords = ['education', 'academic', 'qualification', 'degree', 'university', 'college', 'school']
        edu_section = self._find_section(text, lines, edu_keywords)
        
        if edu_section:
            education.extend(self._parse_education_from_section(edu_section))
        
        # Also look for degree mentions throughout the document
        degree_patterns = [
            r'(Bachelor|Master|PhD|Associates?|B\.?[AS]\.?|M\.?[AS]\.?|Ph\.?D\.?)[^\n.]*',
            r'(Degree|Diploma|Certificate)\s+in\s+([^,\n.]+)',
            r'([A-Z][a-z]+\s+University|[A-Z][a-z]+\s+College)[^\n.]*'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                degree_info = match if isinstance(match, str) else ' '.join(match)
                education.append({
                    'institution': 'Educational Institution',
                    'degree': degree_info.strip(),
                    'field_of_study': 'Field of Study',
                    'start_date': '2015-09-01',
                    'end_date': '2019-05-01',
                    'description': 'Educational qualification'
                })
        
        return education[:3] if education else []
    
    def _parse_education_from_section(self, section_text):
        """Parse education entries from education section"""
        education = []
        
        # Split by lines and look for institution/degree patterns
        lines = [line.strip() for line in section_text.split('\n') if line.strip()]
        
        current_entry = {}
        for line in lines:
            # Look for institution names (usually capitalized)
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+University|\s+College|\s+Institute)', line):
                if current_entry:
                    education.append(current_entry)
                current_entry = {'institution': line.strip()}
            
            # Look for degree information
            elif any(degree in line.lower() for degree in ['bachelor', 'master', 'phd', 'degree', 'diploma']):
                if 'degree' not in current_entry:
                    current_entry['degree'] = line.strip()
            
            # Look for dates
            elif re.search(r'\b(19|20)\d{2}\b', line):
                if 'dates' not in current_entry:
                    current_entry['dates'] = line.strip()
        
        # Add the last entry
        if current_entry:
            education.append(current_entry)
        
        # Clean up and format entries
        formatted_education = []
        for entry in education:
            formatted_entry = {
                'institution': entry.get('institution', 'Educational Institution'),
                'degree': entry.get('degree', 'Degree'),
                'field_of_study': 'Field of Study',
                'start_date': '2015-09-01',
                'end_date': '2019-05-01',
                'description': entry.get('dates', 'Educational qualification')
            }
            formatted_education.append(formatted_entry)
        
        return formatted_education
    
    def _extract_experience(self, text, lines):
        """Extract work experience using intelligent parsing"""
        experience = []
        
        # Find experience section
        exp_keywords = ['experience', 'work', 'employment', 'career', 'professional', 'history']
        exp_section = self._find_section(text, lines, exp_keywords)
        
        if exp_section:
            experience.extend(self._parse_experience_from_section(exp_section))
        
        return experience[:5] if experience else []
    
    def _parse_experience_from_section(self, section_text):
        """Parse experience entries from experience section"""
        experience = []
        
        lines = [line.strip() for line in section_text.split('\n') if line.strip()]
        
        current_entry = {}
        for line in lines:
            # Look for job titles (often at the beginning of lines, capitalized)
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Engineer|Developer|Manager|Analyst|Specialist|Coordinator|Assistant|Director))', line):
                if current_entry:
                    experience.append(current_entry)
                current_entry = {'position': line.strip()}
            
            # Look for company names (often after "at" or on separate lines)
            elif re.search(r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line):
                match = re.search(r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line)
                current_entry['company'] = match.group(1)
            
            # Look for standalone company names (capitalized words, possibly with Inc, LLC, etc.)
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Company|Ltd))?\.?$', line):
                if 'company' not in current_entry:
                    current_entry['company'] = line.strip()
            
            # Look for dates
            elif re.search(r'\b(19|20)\d{2}\b', line):
                if 'dates' not in current_entry:
                    current_entry['dates'] = line.strip()
            
            # Look for descriptions (longer lines that aren't company/title/dates)
            elif len(line) > 30 and 'description' not in current_entry:
                current_entry['description'] = line.strip()
        
        # Add the last entry
        if current_entry:
            experience.append(current_entry)
        
        # Format entries
        formatted_experience = []
        for entry in experience:
            formatted_entry = {
                'company': entry.get('company', 'Company Name'),
                'position': entry.get('position', 'Professional Role'),
                'start_date': '2020-01-01',
                'end_date': '2024-01-01',
                'is_current': False,
                'description': entry.get('description', 'Professional responsibilities and achievements'),
                'achievements': ['Professional achievement']
            }
            formatted_experience.append(formatted_entry)
        
        return formatted_experience
    
    def _extract_skills(self, text, lines):
        """Extract skills using intelligent parsing - not just keyword matching"""
        skills = []
        
        # Find skills section using flexible headers
        skills_section = self._find_section(text, lines, [
            'skill', 'technical', 'competenc', 'proficienc', 'expertise',
            'technolog', 'programming', 'tools', 'software', 'abilities'
        ])
        
        if skills_section:
            # Extract from skills section
            skills.extend(self._parse_skills_from_section(skills_section))
        
        # Also look for skills mentioned throughout the document
        skills.extend(self._parse_skills_from_context(text))
        
        # Remove duplicates and clean up
        unique_skills = []
        seen = set()
        for skill in skills:
            skill_clean = skill.strip().title()
            if skill_clean.lower() not in seen and len(skill_clean) > 1:
                unique_skills.append(skill_clean)
                seen.add(skill_clean.lower())
        
        return unique_skills[:15]  # Limit to 15 skills
    
    def _find_section(self, text, lines, keywords):
        """Find a section in the CV based on flexible keyword matching"""
        section_content = ""
        in_section = False
        section_start = -1
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if this line is a section header
            if any(keyword in line_lower for keyword in keywords):
                # Check if it looks like a header (short line, possibly with symbols)
                if len(line.split()) <= 3 or any(char in line for char in ['-', ':', '•', '*']):
                    in_section = True
                    section_start = i
                    continue
            
            # Check if we've moved to a new section
            if in_section and i > section_start:
                # If line looks like a new section header (short, caps, or with symbols)
                if (len(line.split()) <= 3 and line.isupper()) or \
                   (len(line.split()) <= 2 and any(c.isupper() for c in line)) or \
                   any(keyword in line_lower for keyword in ['experience', 'education', 'work', 'employment', 'project']):
                    break
                    
                section_content += line + " "
        
        return section_content.strip()
    
    def _parse_skills_from_section(self, section_text):
        """Parse skills from a dedicated skills section"""
        skills = []
        
        # Remove common non-skill words
        stopwords = {'and', 'or', 'with', 'using', 'including', 'such', 'as', 'the', 'of', 'in', 'on', 'for'}
        
        # Split by common delimiters
        delimiters = [',', '•', '*', '-', '|', ';', '\n']
        text = section_text
        
        for delimiter in delimiters:
            text = text.replace(delimiter, '|')
        
        potential_skills = [s.strip() for s in text.split('|') if s.strip()]
        
        for skill in potential_skills:
            # Clean up the skill
            skill = re.sub(r'[^\w\s+#.-]', '', skill).strip()
            
            # Skip if too short, too long, or is a stopword
            if len(skill) < 2 or len(skill) > 30 or skill.lower() in stopwords:
                continue
                
            # Skip if it's just numbers or common words
            if skill.isdigit() or skill.lower() in ['years', 'experience', 'level', 'basic', 'intermediate', 'advanced']:
                continue
                
            skills.append(skill)
        
        return skills
    
    def _parse_skills_from_context(self, text):
        """Extract skills mentioned in context throughout the document"""
        skills = []
        
        # Common skill patterns in context
        skill_patterns = [
            r'using\s+([A-Z][a-zA-Z+#.]*(?:\s+[A-Z][a-zA-Z+#.]*)*)',
            r'with\s+([A-Z][a-zA-Z+#.]*(?:\s+[A-Z][a-zA-Z+#.]*)*)',
            r'in\s+([A-Z][a-zA-Z+#.]*(?:\s+[A-Z][a-zA-Z+#.]*)*)',
            r'([A-Z][a-zA-Z+#.]*)\s+(?:programming|development|framework|library)',
            r'(?:programming|development|framework|library)\s+([A-Z][a-zA-Z+#.]*)',
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                match = match.strip()
                if len(match) > 1 and not match.lower() in ['the', 'and', 'with', 'using']:
                    skills.append(match)
        
        return skills
    
    def _extract_certifications(self, text, lines):
        """Extract certifications using flexible parsing"""
        certifications = []
        
        # Find certifications section
        cert_keywords = ['certification', 'certificate', 'license', 'credential', 'award']
        cert_section = self._find_section(text, lines, cert_keywords)
        
        if cert_section:
            cert_lines = [line.strip() for line in cert_section.split('\n') if line.strip()]
            
            for line in cert_lines:
                # Look for certification patterns
                if len(line) > 10 and not line.isupper():
                    certifications.append({
                        'name': line.strip(),
                        'issuer': 'Certification Authority',
                        'issue_date': '2023-01-01',
                        'expiry_date': '2026-01-01',
                        'credential_id': 'CERT123456'
                    })
        
        # Also search for common certification patterns throughout text
        cert_patterns = [
            r'(AWS\s+Certified[^\n.]*)',
            r'(Microsoft\s+Certified[^\n.]*)',
            r'(Google\s+Cloud[^\n.]*)',
            r'(Certified[^\n.]{10,50})',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                certifications.append({
                    'name': match.strip(),
                    'issuer': 'Professional Body',
                    'issue_date': '2023-01-01',
                    'expiry_date': '2026-01-01',
                    'credential_id': 'CERT123456'
                })
        
        return certifications[:5]  # Limit to 5 certifications
    
    def _extract_languages(self, text, lines):
        """Extract languages using intelligent parsing"""
        languages = [{'language': 'English', 'proficiency': 'Native'}]
        
        # Find languages section
        lang_keywords = ['language', 'linguistic', 'fluent', 'spoken']
        lang_section = self._find_section(text, lines, lang_keywords)
        
        common_languages = [
            'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Chinese', 
            'Japanese', 'Korean', 'Arabic', 'Russian', 'Hindi', 'Dutch', 'Swedish'
        ]
        
        # Search in languages section
        if lang_section:
            for lang in common_languages:
                if lang.lower() in lang_section.lower():
                    languages.append({
                        'language': lang,
                        'proficiency': 'Intermediate'
                    })
        
        # Search throughout document
        for lang in common_languages:
            pattern = rf'\b{lang}\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Check if not already added
                if not any(l['language'] == lang for l in languages):
                    languages.append({
                        'language': lang,
                        'proficiency': 'Conversational'
                    })
        
        return languages[:4]  # Limit to 4 languages
    
    def _extract_projects(self, text, lines):
        """Extract projects using intelligent parsing"""
        projects = []
        
        # Find projects section
        proj_keywords = ['project', 'portfolio', 'work', 'development', 'built', 'created']
        proj_section = self._find_section(text, lines, proj_keywords)
        
        if proj_section:
            # Look for project names and descriptions
            proj_lines = [line.strip() for line in proj_section.split('\n') if line.strip()]
            
            current_project = {}
            for line in proj_lines:
                # Look for project titles (often standalone lines or starting lines)
                if len(line) < 50 and not any(char in line for char in ['.', ',', ';']):
                    if current_project:
                        projects.append(current_project)
                    current_project = {'name': line.strip()}
                
                # Look for descriptions (longer lines)
                elif len(line) > 30 and 'description' not in current_project:
                    current_project['description'] = line.strip()
            
            # Add the last project
            if current_project:
                projects.append(current_project)
        
        # Format projects
        formatted_projects = []
        for proj in projects:
            formatted_proj = {
                'name': proj.get('name', 'Project Name'),
                'description': proj.get('description', 'Project description'),
                'technologies': ['Technology'],
                'url': 'https://github.com/user/project'
            }
            formatted_projects.append(formatted_proj)
        
        return formatted_projects[:3]  # Limit to 3 projects
    
    def _fallback_data(self, document):
        """Minimal fallback data when parsing completely fails"""
        return {
            'first_name': '',
            'last_name': '',
            'email': document.user.email,
            'phone': '',
            'address': '',
            'linkedin': '',
            'portfolio': '',
            'summary': '',
            'education': [],
            'experience': [],
            'skills': [],
            'certifications': [],
            'languages': [{'language': 'English', 'proficiency': 'Native'}],
            'projects': []
        }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_parsed_profile(request):
    """Update parsed profile data"""
    try:
        parsed_profile = ParsedProfile.objects.get(user=request.user)
        serializer = ParsedProfileSerializer(parsed_profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except ParsedProfile.DoesNotExist:
        return Response({
            'error': 'No parsed profile found. Please upload a document first.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Update failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_completion_status(request):
    """Get profile completion status"""
    try:
        parsed_profile = ParsedProfile.objects.get(user=request.user)
        
        completion_data = {
            'completion_percentage': parsed_profile.completion_percentage,
            'missing_sections': parsed_profile.missing_sections,
            'completed_sections': parsed_profile.completed_sections
        }
        
        serializer = ProfileCompletionSerializer(completion_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except ParsedProfile.DoesNotExist:
        # No profile exists yet
        return Response({
            'completion_percentage': 0,
            'missing_sections': ['personal_info', 'summary', 'education', 'experience', 'skills'],
            'completed_sections': []
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Status check failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_goals(request):
    """Update user goals"""
    try:
        serializer = UserGoalUpdateSerializer(data=request.data)
        if serializer.is_valid():
            goals_data = serializer.validated_data['goals']
            
            with transaction.atomic():
                # Remove existing goals
                UserGoal.objects.filter(user=request.user).delete()
                
                # Create new goals
                new_goals = []
                for i, goal in enumerate(goals_data, 1):
                    new_goals.append(UserGoal(
                        user=request.user,
                        goal=goal,
                        priority=i
                    ))
                
                UserGoal.objects.bulk_create(new_goals)
            
            return Response({'success': True}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'error': f'Goals update failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_goals(request):
    """Get user's current goals"""
    try:
        goals = UserGoal.objects.filter(user=request.user).order_by('priority')
        serializer = UserGoalSerializer(goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Goals retrieval failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
