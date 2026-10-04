def execute(operation, payload):
    if operation == "sum":
        values = payload.get("values", [])
        if not isinstance(values, list) or not all(isinstance(v, (int,float)) for v in values):
            raise ValueError("payload.values must be a numeric list")
        return {"sum": sum(values), "count": len(values)}
    if operation == "normalize":
        text = str(payload.get("text", ""))
        return {"text": " ".join(text.strip().lower().split())}
    if operation == "echo":
        return {"echo": payload}
    raise ValueError(f"Unsupported operation: {operation}")
