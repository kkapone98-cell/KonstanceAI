def reason(text):
    t=text.lower()
    if any(w in t for w in ['code','script','program']): return {'task_type':'coding','details':text}
    elif any(w in t for w in ['research','info','find']): return {'task_type':'research','details':text}
    elif any(w in t for w in ['run','system','automation']): return {'task_type':'automation','details':text}
    else: return {'task_type':'chat','details':text}
