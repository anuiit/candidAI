class Job:
    """Model class for job listings"""
    
    def __init__(self, title=None, company=None, location=None, link=None, description=None):
        self.title = title
        self.company = company
        self.location = location
        self.link = link
        self.description = description
    
    def to_dict(self):
        """Convert job to dictionary"""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "link": self.link,
            "text": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Job instance from a dictionary"""
        return cls(
            title=data.get("title"),
            company=data.get("company"),
            location=data.get("location"),
            link=data.get("link"),
            description=data.get("text")
        )