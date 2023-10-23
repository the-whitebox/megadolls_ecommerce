from .models import *
from django.urls import reverse


def permission(request):
    model_list = []
    model = ModulePermission.objects.filter(user_id=request.user.id)
    for i in model:
        model_list.append(i.module_id)    
    return model_list


def helper(request):
    module_list = []
    parent_obj = Module.objects.filter(parent_id=0).order_by("id")
    parent_list = list()
    for i in parent_obj:
        obj_dict = dict()
        obj_dict["parent"] = i
        child_obj = Module.objects.filter(parent_id=i.id).order_by("id")
        obj_dict["child"] = child_obj
        if i.url:
            obj_dict["url"] = reverse(i.url)
        for child in child_obj:
            child.child_url = reverse(child.url)
            child.save()
        module_list.append(obj_dict)
    return module_list


def per1(request):
    module = Module.objects.all()
    m = ModulePermission.objects.filter(user_id=request.user.id, module_id__in=module)
    return m


def per(request):
    try:
        path = request.resolver_match.url_name
        fu = Module.objects.get(url=path)
        m = ModulePermission.objects.filter(user_id=request.user.id, module_id=fu.id)
    except:
        m = None
        pass

    return m
