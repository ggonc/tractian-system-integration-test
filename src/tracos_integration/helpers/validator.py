class Validator:
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list[str]) -> list[str]:
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] in ["", " ", None, [], {}]:
                    missing_fields.append(field)
        
        return missing_fields