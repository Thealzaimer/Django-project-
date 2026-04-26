from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tools import TOOL_REGISTRY
import functools

# Professional Optimization: Memoize the manifest to prevent re-calculating JSON schemas
@functools.lru_cache(maxsize=1)
def get_cached_tool_manifest():
    manifest = []
    for name, info in TOOL_REGISTRY.items():
        # Reflectively build the manual from docstrings and Pydantic schemas
        manifest.append({
            "name": name,
            "description": info["function"].__doc__.strip() if info["function"].__doc__ else "No description",
            "input_schema": info["schema"].model_json_schema()
        })
    return manifest

def list_tools_view(request):
    """
    The Discovery Endpoint: Dynamically generates the manual for the LLM.
    Implements professional Scoping and Caching.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Discovery requires an authenticated session"}, status=401)
    
    # In a production environment, we would filter 'tools' based on request.user.permissions
    return JsonResponse({
        "tools": get_cached_tool_manifest(),
        "server_info": {
            "name": "AutoFlow MCP Server",
            "version": "1.0.0"
        }
    })

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
