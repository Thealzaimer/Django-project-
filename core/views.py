from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tools import TOOL_REGISTRY

@csrf_exempt
def call_tool_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # We rely on the middleware having validated the payload and added it to request
    if not hasattr(request, 'mcp_payload'):
        return JsonResponse({"error": "Payload missing. Middleware failure."}, status=500)

    payload = request.mcp_payload
    tool_name = payload["tool_name"]
    arguments = payload["arguments"]

    # Execute the tool
    tool_func = TOOL_REGISTRY[tool_name]["function"]
    try:
        # Since the dictionary is validated, we just unpack
        result = tool_func(**arguments)
        return JsonResponse({"result": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
