import json
import os

from tools.base_tool import BaseTool

VALID_INFO_TYPES = ["prerequisites", "credits", "schedule", "description", "all"]


class CourseTool(BaseTool):
    """
    Read-only tool: get_course_info

    Retrieves structured information about a specific course from
    data/courses.json. Never invents course information — if the course
    or the requested field isn't in the data file, it returns a
    structured error instead of guessing.
    """

    name = "get_course_info"
    description = (
        "Retrieve structured information about a specific university course "
        "(prerequisites, credits, schedule, description, or all of these) "
        "by its course code, e.g. BSE4104. Use this whenever a student asks "
        "about a specific course's prerequisites, credit load, schedule, or "
        "what a course covers."
    )
    schema = {
        "type": "object",
        "properties": {
            "course_code": {
                "type": "string",
                "description": "The course code to look up, e.g. 'BSE4104'.",
            },
            "info_type": {
                "type": "string",
                "enum": VALID_INFO_TYPES,
                "description": "Which piece of course information to return. Defaults to 'all'.",
            },
        },
        "required": ["course_code"],
    }
    requires_approval = False

    def __init__(self, data_path="data/courses.json"):
        self.data_path = data_path

    def execute(self, **kwargs) -> dict:
        course_code = kwargs.get("course_code")
        info_type = kwargs.get("info_type", "all")

        # 1. Validate course_code
        if not course_code or not isinstance(course_code, str) or not course_code.strip():
            return {"success": False, "error": "Missing or invalid 'course_code'. A non-empty course code string is required."}

        # 2. Validate info_type
        if info_type not in VALID_INFO_TYPES:
            return {
                "success": False,
                "error": f"Invalid 'info_type': '{info_type}'. Must be one of: {', '.join(VALID_INFO_TYPES)}.",
            }

        # 3. Load course database
        if not os.path.exists(self.data_path):
            return {"success": False, "error": f"Course database is unavailable (not found at '{self.data_path}')."}

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return {"success": False, "error": f"Course database is unavailable (could not read/parse '{self.data_path}': {e})."}

        courses = data.get("courses", [])

        # 4. Normalize course code (case/whitespace-insensitive match)
        normalized = course_code.strip().upper()
        match = next((c for c in courses if c.get("course_code", "").strip().upper() == normalized), None)

        # 5. Not found
        if match is None:
            return {"success": False, "error": f"No course found with code '{course_code}'."}

        # 6/7. Build structured result — never invent fields not present in the data
        if info_type == "all":
            result_data = {k: v for k, v in match.items() if not k.startswith("_")}
        else:
            if info_type not in match:
                return {
                    "success": False,
                    "error": f"'{info_type}' is not available for course '{match.get('course_code', course_code)}'.",
                }
            result_data = {info_type: match[info_type]}

        return {
            "success": True,
            "course_code": match.get("course_code", normalized),
            "info_type": info_type,
            "data": result_data,
        }
