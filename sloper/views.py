import json
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from adminpanel.models import *
from web_app.email import mail_send_verify_otp, mail_send_user_credential
from web_app.views import random_with_N_digits, subscription
from sloper.s3_bucket import BucketFiles


def get_sloper_data():
    return {
        'sloper_templates': SloperTemplate.objects.all(),
        'textures': SloperTexture.objects.all(),
        'elements': SloperElement.objects.all(),
        'svg_icons': SloperMulticolorIconSVG.objects.all()
    }


def view_sloper(request):
    return render(request, 'sloper-tool/sloper.html', get_sloper_data())


def send_otp(request):
    if request.method == "POST":
        email = request.POST.get('email', '').lower()
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})
        otp = random_with_N_digits(4)
        user, is_created = User.objects.update_or_create(email=email)
        user.otp = otp
        user.save()
        mail_send_verify_otp(email, otp)
        return JsonResponse({'success': True, 'message': 'OTP Send on Email'})


def sloper_register_guest_user(request):
    if request.method == "POST":
        email = request.POST.get('email', '').lower()
        otp = request.POST.get('otp')
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})
        elif not otp:
            return JsonResponse({'success': False, 'message': 'OTP is required.'})
        try:
            user = User.objects.get(email=email)
            if not user.otp == otp:
                return JsonResponse({'success': False, 'message': 'otp not match please try again'})

            password = random_with_N_digits(8)
            request.session["guest_user"] = {"email": email}
            request.session.modified = True

            user.password = password
            user.is_verified = True
            user.otp = None
            user.save()
            mail_send_user_credential(email, password)
            return JsonResponse({'success': True, 'message': 'Registered Successfully'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Email is not Registered'})


# @login_required(login_url='web_login')
@csrf_exempt
def save_design(request):
    # try:
    if request.method == "POST":
        body_data = json.loads(request.body.decode())
        canvas_data = json.dumps(body_data.get('canvas_data'))
        design_name = body_data.get('design_name')
        data = body_data.get('data')
        try:
            guest_user_email = request.session.get('guest_user').get('email')
            user = User.objects.get(email=guest_user_email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Email Not Found', 'redirect_url': reverse('render_design', args=[design.slug])})

        # user = request.user
        folder_slug = body_data.get('folder_slug')

        file_name = f'{user.email}{datetime.now()}.json'
        file_path = f'sloper_designs/{file_name}'
        buck = BucketFiles(file_path)
        if buck.save(canvas_data):
            messages.success(request, 'Design Saved Successfully')

        try:
            user_folder = SloperUserFolder.objects.get(slug=folder_slug)
            design = SloperUserDesign.objects.create(user_id=user.id, name=design_name, data=data, file_name=file_path, folder_id=user_folder.id)
        except:
            design = SloperUserDesign.objects.create(user_id=user.id, name=design_name, data=data, file_name=file_path)

        return JsonResponse({'success': True, 'message': 'Design Saved', 'redirect_url': reverse('render_design', args=[design.slug])})
    return render(request, 'sloper-tool/pages/sloper.html', get_sloper_data())
    # except:
    #     return JsonResponse({'success': False, 'message': 'Something Went Wrong', 'redirect_url': reverse('view_sloper')})


# @login_required(login_url='web_login')
def render_design(request, slug):
    # try:
        design = SloperUserDesign.objects.get(slug=slug)
        buck = BucketFiles(design.file_name)
        sloper_data = get_sloper_data()
        sloper_data.update(
            {'design': design, 'design_data': json.dumps(buck.get_file_data().decode())})
        return render(request, 'sloper-tool/pages/sloper-with-data.html', sloper_data)
    # except:
    #     messages.error(request, 'Something Went Wrong')
    #     return redirect('view_sloper')


@login_required(login_url='web_login')
def view_designs(request):
    designs = SloperUserDesign.objects.filter(user_id=request.user.id)
    return render(request, '', {'designs': designs})


@csrf_exempt
def update_design(request, slug):
    try:
        if request.user.is_authenticated:
            design = SloperUserDesign.objects.filter(slug=slug)
            if design.exists():
                buck = BucketFiles(design.first().file_name)
                body_data = json.loads(request.body.decode())
                canvas_data = json.dumps(body_data.get('canvas_data'))
                data = body_data.get('data')
                if buck.save(canvas_data):
                    obj = design.first()
                    obj.data = data
                    obj.save()
                    return JsonResponse({'success': True, 'design': design.values().get(), 'design_data': buck.get_file_data().decode(), 'message': 'Design Saved'}, safe=False)
                return JsonResponse({'success': False, 'design': design.values().get(), 'design_data': buck.get_file_data().decode(), 'message': 'Failed to Save'}, safe=False)
            else:
                return JsonResponse({'success': False, 'design': None, 'message': 'Design Not Exists'})
        else:
            return JsonResponse({'success': False, 'design_data': None, 'message': 'Please Sign In or Sign Up'})
    except:
        return JsonResponse({'success': False, 'design_data': None, 'message': 'Something Went Wrong'})


@login_required(login_url='web_login')
def view_my_folders(request):
    try:
        folders = SloperUserFolder.objects.filter(
            user_id=request.user.id, is_trash=False)
        return render(request, 'sloper-tool/pages/design-folder/my-folder.html', {'folders': folders})
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('view_sloper')


@login_required(login_url='web_login')
def add_folder(request):
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            if SloperUserFolder.objects.filter(user_id=request.user.id, folder_name=name).exists():
                messages.error(request, "Folder Name Already Exist")
                return redirect('view_my_folders')

            SloperUserFolder.objects.create(
                user_id=request.user.id, folder_name=name)
            messages.success(request, "folder Created")
        except:
            messages.error(request, "Something Went Wrong")
    return redirect('view_my_folders')


def view_designs_in_folder(request, name, slug):
    designs = SloperUserDesign.objects.filter(
        user_id=request.user.id, folder__slug=slug, is_trash=False, folder__is_trash=False)
    return render(request, 'sloper-tool/pages/design-folder/designs-in-folder.html', {'designs': designs, 'folder_name': name})


@login_required(login_url='web_login')
def rename_folder(request):
    if request.method == "POST":
        try:
            name = request.POST.get('name')
            slug = request.POST.get('slug')
            folder = SloperUserFolder.objects.get(
                user_id=request.user.id, slug=slug)
            folder.folder_name = name
            folder.save()
            messages.success(request, "Folder Renamed Successfully")
        except:
            messages.error(request, "Something Went Wrong")
    return redirect('view_my_folders')


def add_folder_to_trash(request, slug):
    try:
        folder = SloperUserFolder.objects.get(
            user_id=request.user.id, slug=slug)
        folder.is_trash = True
        folder.save()
        messages.success(request, "Folder in trash now")
    except:
        messages.error(request, "Something Went Wrong")
    return redirect('view_my_folders')


def add_design_to_trash(request, slug):
    try:
        design = SloperUserDesign.objects.get(slug=slug)
        design.is_trash = True
        design.save()
        messages.success(request, "Design Added to Trash")
        return redirect('view_designs_in_folder', design.folder.folder_name, design.folder.slug)
    except:
        messages.error(request, "Something Went Wrong")
        return redirect('view_my_folders')


def view_trash(request):
    try:
        folders = SloperUserFolder.objects.filter(
            user_id=request.user.id, is_trash=True).order_by('-id')
        designs = SloperUserDesign.objects.filter(
            user_id=request.user.id, is_trash=True).exclude(folder_id__in=folders).order_by('-id')
        return render(request, 'sloper-tool/pages/design-folder/trash.html', {'folders': folders, 'designs': designs})
    except:
        messages.success(request, "Something Went Wrong")
        return redirect('view_my_folders')


def restore_folder(request, slug):
    try:
        folder = SloperUserFolder.objects.get(slug=slug)
        folder.is_trash = False
        folder.save()
        messages.success(request, "Folder Restored")
    except:
        messages.error(request, "Something Went Wrong")
    return redirect('view_trash')


def restore_design(request, slug):
    try:
        design = SloperUserDesign.objects.get(
            slug=slug, folder__is_trash=False)
        design.is_trash = False
        design.save()
        messages.success(request, "Folder Restored")
    except:
        messages.error(request, "Something Went Wrong")
    return redirect('view_trash')


def empty_trash(request):
    try:
        SloperUserDesign.objects.filter(
            user_id=request.user.id, is_trash=True).delete()
        SloperUserFolder.objects.filter(
            user_id=request.user.id, is_trash=True).delete()
        messages.success(request, "Trash Deleted")
    except:
        messages.success(request, "Something Went Wrong")
    return redirect('view_trash')


def hospital_patients(request):
    hospital_email = request.user.email
    hospital = SloperHospital.objects.get(management_email=hospital_email)
    registered_patient = HospitalRegisteredPatients.objects.filter(
        hospital_id=hospital.id)
    unregistered_patient = HospitalUnregisteredPatients.objects.filter(
        hospital_id=hospital.id)
    subscribed_patient = HospitalRegisteredPatients.objects.filter(
        hospital_id=hospital.id, has_subscription=True)
    return render(request, "sloper-tool/pages/hospital_patient/patients_list.html",
                  {"registered_patient": registered_patient,
                   "unregistered_patient": unregistered_patient,
                   "subscribed_patient": subscribed_patient
                   })


def subscribe_patient_to_sloper(request):
    time = timezone.now()
    patient_id = request.POST["patient_id"]
    registered_patient = HospitalRegisteredPatients.objects.get(id=patient_id)
    registered_patient.has_subscription = True
    registered_patient.received_at = time
    registered_patient.save()
    return JsonResponse({"success": True})


def unsubscribe_patient_to_sloper(request):
    patient_id = request.POST["patient_id"]
    registered_patient = HospitalRegisteredPatients.objects.get(id=patient_id)
    registered_patient.has_subscription = False
    registered_patient.save()
    return JsonResponse({"success": True})


def add_patients(request):
    hospital_email = request.user.email
    time = timezone.now()
    name = request.POST["name"]
    email = request.POST["email"].lower()
    phone_number = request.POST["phone_number"]
    hospital = SloperHospital.objects.get(management_email=hospital_email)
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        HospitalRegisteredPatients.objects.create(
            user_id=user.id,
            created_at=time,
            hospital_id=hospital.id
        )
    else:
        HospitalUnregisteredPatients.objects.create(
            email=email,
            name=name,
            phone_number=phone_number,
            created_at=time,
            hospital_id=hospital.id
        )
    return JsonResponse({"success": True})


def edit_unregistered_patient(request):
    name = request.POST["name"]
    email = request.POST["email"].lower()
    phone_number = request.POST["phone_number"]
    patient_id = request.POST["patient_id"]
    patient = HospitalUnregisteredPatients.objects.get(id=patient_id)
    patient.name = name
    patient.email = email
    patient.phone_number = phone_number
    patient.save()
    return JsonResponse({"success": True})


def delete_unregistered_patient(request):
    patient_id = request.POST["patient_id"]
    HospitalUnregisteredPatients.objects.get(id=patient_id).delete()
    return JsonResponse({"success": True})


def delete_sloper_patient(request):
    patient_id = request.POST["patient_id"]
    HospitalRegisteredPatients.objects.get(id=patient_id).delete()
    return JsonResponse({"success": True})


def my_sloper_subscription(request):
    user_id = request.user.id
    user_email = request.user.email
    try:
        individual_subscription = UserSloperSubscription.objects.get(user_id=user_id, category = "Individual", is_active = True)
    except:
        individual_subscription = None
    subscription_that_user_got_gift = UserGiftSloperPlan.objects.filter(receiver_email=user_email,user_sloper_subscription__is_active=False, is_wasted=False, user_sloper_subscription__is_ended=False, user_sloper_subscription__is_canceled=False) 
    individual_gifted_subscription = UserGiftSloperPlan.objects.filter(sender_user_id=user_id, user_sloper_subscription__category = "Individual")
    hospital_gifted_subscription = UserGiftSloperPlan.objects.filter(sender_user_id=user_id, user_sloper_subscription__category = "Hospital")
    school_gifted_subscription = UserGiftSloperPlan.objects.filter(sender_user_id=user_id, user_sloper_subscription__category = "School")
    return render(request, "sloper-tool/pages/my_account_sloper_subscription/my_sloper_subscription.html", 
                                                    {"subscription_that_user_got_gift":subscription_that_user_got_gift,
                                                     "individual_subscription": individual_subscription, 
                                                     "individual_gifted_subscription": individual_gifted_subscription,
                                                     "hospital_gifted_subscription": hospital_gifted_subscription, 
                                                     "school_gifted_subscription": school_gifted_subscription
                                                    }) 
