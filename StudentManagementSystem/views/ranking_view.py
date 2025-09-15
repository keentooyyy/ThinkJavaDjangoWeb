from django.core.paginator import Paginator


def get_common_params(request):
    """Extract common GET parameters for ranking views."""
    return {
        "department_name": request.GET.get("department"),
        "section_filter": request.GET.get("filter_by"),
        "sort_by": request.GET.get("sort_by", ""),
        "sort_order": request.GET.get("sort_order", "desc"),
        "page_number": request.GET.get("page", 1),
        "per_page": int(request.GET.get("per_page", 25)),
    }


def paginate_queryset(queryset, per_page, page_number):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def build_ranking_context(rankings, page_obj, params, user_context, extra_context=None):
    """Build the final render context for ranking views."""
    context = {
        "rankings": page_obj.object_list,
        "page_obj": page_obj,
        "sort_by": params["sort_by"],
        "sort_order": params["sort_order"],
        "per_page": params["per_page"],
        "username": user_context["username"],
        "role": user_context["role"],
    }
    if extra_context:
        context.update(extra_context)
    return context


def deduplicate_sections(sections):
    """Remove duplicate sections by year+letter (ignoring department)."""
    unique = []
    seen_keys = set()
    for section in sections:
        key = f"{section.year_level.year}{section.letter}"
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(section)
    return unique