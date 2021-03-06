# Copyright (C) 2017 Feedvay (Gagandeep Singh: singh.gagan144@gmail.com) - All Rights Reserved
# Content in this document can not be copied and/or distributed without the express
# permission of Gagandeep Singh.
from django.shortcuts import render

from brands.forms import *
from brands import operations as ops
from brands.models import Brand, BrandOwner

from utilities.decorators import registered_user_only, brand_console
from utilities.api_utils import ApiResponse

# ==================== Console ====================
@registered_user_only
def console_brands(request):
    """
    View to display all user brands; owned as well as associated.

    **Type**: GET

    **Authors**: Gagandeep Singh
    """
    data = {}
    return render(request, 'brands/console/my_brands.html', data)

# ----- Brand CRUD -----
@registered_user_only
def console_brand_new(request):
    """
    View to add new brand. Newly created brand is marked for verification which is then
    published after manual verification.

    **Type**: GET

    **Authors**: Gagandeep Singh
    """
    data = {
        "app_name": "app_create_brand"
    }
    return render(request, 'brands/console/create_brand.html', data)

@registered_user_only
def console_brand_create(request):
    """
    An API view to create a NEW brand. User fills a form and submit data.

    **Type**: POST

    **Authors**: Gagandeep Singh
    """

    if request.method.lower() == 'post':
        form_brand = BrandCreateEditForm(request.POST, request.FILES)

        if form_brand.is_valid():
            form_data = form_brand.cleaned_data

            ops.create_new_brand(form_data, request.user.registereduser)
            return ApiResponse(status=ApiResponse.ST_SUCCESS, message='Your request has been send for verification.').gen_http_response()
        else:
            errors = dict(form_brand.errors)
            return ApiResponse(status=ApiResponse.ST_FAILED, message='Please correct marked errors.', errors=errors).gen_http_response()
    else:
        # GET Forbidden
        return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='Use post.').gen_http_response()

@registered_user_only
@brand_console
def console_brand_request_update(request):
    """
    An API view to submit changes in brand details. This view can be called to edit brand details or
    re-submit brand details after verification of brand has been failed.

    **Type**: POST

    **Authors**: Gagandeep Singh
    """
    if request.method.lower() == 'post':
        brand = request.curr_brand

        # Check status and act accordingly
        if brand.status == Brand.ST_DELETED:
            # Brand deleted. Not allowed
            return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message="Denied! Brand '{}' has been deleted.".format(brand.name)).gen_http_response()
        elif brand.status == Brand.ST_VERIFIED:
            # Create Change log
            try:
                is_valid, errors = ops.create_brand_change_log(brand, request.user.registereduser, request.POST, request.FILES)
                if is_valid:
                    return ApiResponse(status=ApiResponse.ST_SUCCESS, message='Your change request has been queued for verification.').gen_http_response()
                else:
                    return ApiResponse(status=ApiResponse.ST_FAILED, message='Please correct marked errors.', errors=errors).gen_http_response()

            except Exception as ex:
                return ApiResponse(status=ApiResponse.ST_FAILED, message=ex.message).gen_http_response()
        else:
            # Inplace update
            try:
                ops.reregister_or_update_brand(brand, request.POST, request.FILES)
                return ApiResponse(status=ApiResponse.ST_SUCCESS, message='All updates made successfully').gen_http_response()
            except Exception as ex:
                return ApiResponse(status=ApiResponse.ST_FAILED, message=ex.message).gen_http_response()
    else:
        # GET Forbidden
        return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='Use post.').gen_http_response()

# ----- /Brand CRUD -----

@registered_user_only
@brand_console
def console_brand_settings(request):
    """
    View for brand settings. Only applicable for brand console.

    **Type**: GET

    **Authors**: Gagandeep Singh
    """
    data = {
        "app_name": "app_brand_settings",
        "list_other_owners": request.curr_brand.owners.all().exclude(user_id=request.user.id).select_related('user')
    }
    return render(request, 'brands/console/brand_settings.html', data)

@registered_user_only
@brand_console
def console_brand_disassociate(request):
    """
    API view to disassociate current user from the brand. Only applicable for brand console.

    **Points**:

        - **Registered user** is obtained from current session.
        - **Brand** is obtained from ``request.curr_brand``.

    **Type**: POST

    **Authors**: Gagandeep Singh
    """
    if request.method.lower() == 'post':
        brand = request.curr_brand
        reg_user = request.user.registereduser

        confirm = request.POST.get('confirm', False)
        if confirm == 'true':
            try:
                brand.delete_owner(reg_user, send_owls=True)
                return ApiResponse(status=ApiResponse.ST_SUCCESS, message='Ok').gen_http_response()
            except BrandOwner.DoesNotExist:
                # No association found; Invalid request
                return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='You are not associated with this brand.').gen_http_response()
        else:
            # Confirmation missing.
            return ApiResponse(status=ApiResponse.ST_FAILED, message='Please confirm your action.').gen_http_response()
    else:
        # GET Forbidden
        return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='Use post.').gen_http_response()

@registered_user_only
@brand_console
def console_toggle_brand_active(request):
    """
    An API view to toggle brand activeness. Only ``verified`` brand's activeness can be toggled.

    **Type**: POST

    **Authors**: Gagandeep Singh
    """
    if request.method.lower() == 'post':
        brand = request.curr_brand

        if brand.status == Brand.ST_VERIFIED:
            active = True if request.POST['active'] == 'true' else False

            brand.active = active
            brand.save()
            return ApiResponse(status=ApiResponse.ST_SUCCESS, message='Ok').gen_http_response()
        else:
            return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='You cannot change active property of unverified brand.').gen_http_response()
    else:
        # GET Forbidden
        return ApiResponse(status=ApiResponse.ST_FORBIDDEN, message='Use post.').gen_http_response()

# ==================== /Console ====================
