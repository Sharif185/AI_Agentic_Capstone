import json
import os
from .base_tool import BaseTool


class CourseTool(BaseTool):
    def __init__(self, data_path="data/courses.json"):
        self.data_path = data_path
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.data_path):
            self.courses = None
            return
        with open(self.data_path, "r") as f:
            self.courses = json.load(f)

    @property
    def name(self):
        return "get_course_info"

    @property
    def description(self):
        return (
            "Get information about a specific course including prerequisites, "
            "credits, schedule, and description. Use this when a student asks "
            "about course details."
        )

    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "The course code (e.g., BSE4104)"
                },
                "info_type": {
                    "type": "string",
                    "enum": ["prerequisites", "credits", "schedule", "description", "all"],
                    "description": "Type of information needed",
                    "default": "all"
                }
            },
            "required": ["course_code"]
        }

    @property
    def requires_approval(self):
        return False

    def execute(self, course_code=None, info_type="all"):
        if not course_code:
            return {"success": False, "error": "course_code is required"}

        valid_types = ["prerequisites", "credits", "schedule", "description", "all"]
        if info_type not in valid_types:
            return {"success": False, "error": f"info_type must be one of: {', '.join(valid_types)}"}

        if self.courses is None:
            return {"success": False, "error": "Course database unavailable"}

        course_code = course_code.upper().strip()
        if course_code not in self.courses:
            return {"success": False, "error": f"Course {course_code} not found"}

        course = self.courses[course_code]

        if info_type == "all":
            data = course
        else:
            data = {info_type: course.get(info_type)}

        return {
            "success": True,
            "course_code": course_code,
            "info_type": info_type,
            "data": data
        }
