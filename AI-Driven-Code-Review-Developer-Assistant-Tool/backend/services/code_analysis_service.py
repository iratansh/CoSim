import openai
import anthropic
from typing import List, Dict, Any, Optional
import tree_sitter
from tree_sitter import Language, Parser
import subprocess
import json

from core.config import get_settings

class CodeAnalysisService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = openai.OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self.anthropic_client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key) if self.settings.anthropic_api_key else None

    async def analyze_code_snippet(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a code snippet and provide suggestions."""
        # Combine static analysis with LLM analysis
        static_results = await self._run_static_analysis(code, language, filename)
        llm_results = await self._run_llm_analysis(code, language, context)

        # Merge results
        return {
            "summary": llm_results.get("summary", ""),
            "suggestions": static_results.get("suggestions", []) + llm_results.get("suggestions", []),
            "test_suggestions": llm_results.get("test_suggestions", []),
            "documentation_suggestions": llm_results.get("documentation_suggestions", [])
        }

    async def analyze_pr_changes(
        self,
        repo_full_name: str,
        base_sha: str,
        head_sha: str,
        changed_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze changes in a pull request."""
        analysis_results = {
            "summary": "",
            "overall_score": 7,  # Default score
            "suggestions": [],
            "security_issues": [],
            "test_suggestions": [],
            "file_suggestions": []
        }

        # Analyze each changed file
        for file_data in changed_files:
            if file_data.get("content") and self._is_code_file(file_data["filename"]):
                file_analysis = await self._analyze_file_changes(file_data)
                analysis_results["file_suggestions"].append(file_analysis)

        # Generate overall summary
        analysis_results["summary"] = await self._generate_pr_summary(changed_files, analysis_results)

        return analysis_results

    async def explain_code(
        self,
        code: str,
        language: str,
        context: Optional[str] = None
    ) -> str:
        """Provide natural language explanation of code."""
        prompt = f"""
        Please explain the following {language} code in simple terms:

        ```{language}
        {code}
        ```

        {f"Context: {context}" if context else ""}

        Provide a clear explanation of what this code does, how it works, and any important details.
        """

        return await self._query_llm(prompt)

    async def generate_tests(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> List[str]:
        """Generate unit tests for the provided code."""
        prompt = f"""
        Generate comprehensive unit tests for the following {language} code:

        ```{language}
        {code}
        ```

        {f"Filename: {filename}" if filename else ""}

        Please provide:
        1. Test cases for normal functionality
        2. Edge cases and error conditions
        3. Mock objects if needed
        4. Use appropriate testing framework for {language}

        Return the test code as a list of test functions.
        """

        response = await self._query_llm(prompt)
        # Parse response to extract individual test cases
        return [response]  # Simplified for now

    async def generate_documentation(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> str:
        """Generate documentation for the provided code."""
        prompt = f"""
        Generate comprehensive documentation for the following {language} code:

        ```{language}
        {code}
        ```

        {f"Filename: {filename}" if filename else ""}

        Please provide:
        1. Function/class descriptions
        2. Parameter descriptions
        3. Return value descriptions
        4. Usage examples
        5. Any important notes or warnings

        Format the documentation appropriately for {language}.
        """

        return await self._query_llm(prompt)

    async def _run_static_analysis(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run static analysis tools on the code."""
        suggestions = []

        if language == "python":
            # Run flake8, black, mypy
            suggestions.extend(await self._run_python_linters(code, filename))
        elif language == "javascript" or language == "typescript":
            # Run eslint, prettier
            suggestions.extend(await self._run_js_linters(code, filename))

        return {"suggestions": suggestions}

    async def _run_python_linters(self, code: str, filename: Optional[str]) -> List[Dict[str, Any]]:
        """Run Python-specific linters."""
        suggestions = []

        # Simple checks for demo purposes
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                suggestions.append({
                    "line_number": i,
                    "suggestion": f"Line too long ({len(line)} characters). Consider breaking it up.",
                    "severity": "warning",
                    "category": "style"
                })

            if "print(" in line:
                suggestions.append({
                    "line_number": i,
                    "suggestion": "Consider using logging instead of print statements.",
                    "severity": "info",
                    "category": "style"
                })

        return suggestions

    async def _run_js_linters(self, code: str, filename: Optional[str]) -> List[Dict[str, Any]]:
        """Run JavaScript/TypeScript-specific linters."""
        suggestions = []

        # Simple checks for demo purposes
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if "console.log(" in line:
                suggestions.append({
                    "line_number": i,
                    "suggestion": "Remove console.log statements before production.",
                    "severity": "warning",
                    "category": "style"
                })

            if "var " in line:
                suggestions.append({
                    "line_number": i,
                    "suggestion": "Consider using 'let' or 'const' instead of 'var'.",
                    "severity": "info",
                    "category": "style"
                })

        return suggestions

    async def _run_llm_analysis(
        self,
        code: str,
        language: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run LLM-based analysis on the code."""
        prompt = f"""
        Analyze the following {language} code and provide suggestions for improvement:

        ```{language}
        {code}
        ```

        {f"Context: {context}" if context else ""}

        Please provide:
        1. A brief summary of what the code does
        2. Suggestions for improvement (performance, readability, security)
        3. Test suggestions
        4. Documentation suggestions

        Format your response as JSON with the following structure:
        {{
            "summary": "Brief description",
            "suggestions": [
                {{
                    "line_number": 1,
                    "suggestion": "Suggestion text",
                    "severity": "info|warning|error",
                    "category": "style|performance|security|bug"
                }}
            ],
            "test_suggestions": ["Test suggestion 1", "Test suggestion 2"],
            "documentation_suggestions": ["Doc suggestion 1", "Doc suggestion 2"]
        }}
        """

        response = await self._query_llm(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "summary": "Code analysis completed",
                "suggestions": [],
                "test_suggestions": [],
                "documentation_suggestions": []
            }

    async def _analyze_file_changes(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze changes in a specific file."""
        filename = file_data["filename"]
        content = file_data.get("content", "")
        patch = file_data.get("patch", "")

        # Determine file language
        language = self._detect_language(filename)

        # Analyze the current content
        analysis = await self.analyze_code_snippet(content, language, filename)

        return {
            "filename": filename,
            "language": language,
            "suggestions": analysis.get("suggestions", []),
            "summary": analysis.get("summary", "")
        }

    async def _generate_pr_summary(
        self,
        changed_files: List[Dict[str, Any]],
        analysis_results: Dict[str, Any]
    ) -> str:
        """Generate a summary of the PR changes."""
        file_count = len(changed_files)
        code_files = [f for f in changed_files if self._is_code_file(f["filename"])]

        summary = f"This PR modifies {file_count} file(s), including {len(code_files)} code file(s). "

        if analysis_results["file_suggestions"]:
            suggestion_count = sum(len(f.get("suggestions", [])) for f in analysis_results["file_suggestions"])
            summary += f"Found {suggestion_count} suggestions for improvement."

        return summary

    async def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the given prompt."""
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                print(f"Anthropic API error: {e}")

        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {e}")

        # Fallback response if no LLM is available
        return "AI analysis unavailable. Please configure API keys."

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        ext = filename.split('.')[-1].lower()
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'swift': 'swift',
            'kt': 'kotlin'
        }
        return language_map.get(ext, 'text')

    def _is_code_file(self, filename: str) -> bool:
        """Check if the file is a code file."""
        code_extensions = {
            'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'h',
            'go', 'rs', 'php', 'rb', 'swift', 'kt', 'cs', 'scala'
        }
        ext = filename.split('.')[-1].lower()
        return ext in code_extensions