from django.urls import path
from sloper import views

urlpatterns = [
    path("send-otp/", views.send_otp, name="send_otp"),
    path("register/guest-user/", views.sloper_register_guest_user, name="sloper_register_guest_user"),

    # design
    path("view/", views.view_sloper, name="view_sloper"),
    path("design/save/", views.save_design, name="save_design"),
    path("design/render/<slug:slug>/", views.render_design, name="render_design"),
    path("design/update/<slug:slug>/", views.update_design, name="update_design"),
    # design
    
    # folder
    path("my-folder/view-folders/", views.view_my_folders, name="view_my_folders"),
    path("my-folder/folder/add/", views.add_folder, name="add_folder"),
    path("my-folder/folder/rename/", views.rename_folder, name="rename_folder"),
    path("my-folder/folder/view-designs/<str:name>/<slug:slug>/", views.view_designs_in_folder, name="view_designs_in_folder"),
    # folder

    # trash
    path("trash/folder/add/<slug:slug>/", views.add_folder_to_trash, name="add_folder_to_trash"),
    path("trash/design/add/<slug:slug>/", views.add_design_to_trash, name="add_design_to_trash"),
    path("trash/view/", views.view_trash, name="view_trash"),
    path("trash/folder/restore/<slug:slug>/", views.restore_folder, name="restore_folder"),
    path("trash/design/restore/<slug:slug>/", views.restore_design, name="restore_design"),
    path("trash/empty/", views.empty_trash, name="empty_trash"),
    # trash

    # hospital_patients
    path("hospital-patients", views.hospital_patients, name="hospital_patients"),
    path("add-patients", views.add_patients, name="add_patients"),
    path("subscribe-patient-to-sloper", views.subscribe_patient_to_sloper, name="subscribe_patient_to_sloper"),
    path("unsubscribe-patient-to-sloper", views.unsubscribe_patient_to_sloper, name="unsubscribe_patient_to_sloper"),
    path("delete-unregistered-patient", views.delete_unregistered_patient, name="delete_unregistered_patient"),
    path("edit-unregistered-patient", views.edit_unregistered_patient, name="edit_unregistered_patient"),
    path("delete-sloper-patient", views.delete_sloper_patient, name="delete_sloper_patient"),
    path("my-sloper-subscription", views.my_sloper_subscription, name="my_sloper_subscription"),

]
