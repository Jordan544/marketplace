from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
  path('', views.listing_list, name='listing_list'),
  path('create/', views.listing_create, name='listing_create'),
  path('<int:pk>/', views.listing_detail, name='listing_detail'),
  path('<int:pk>/edit', views.listing_update, name='listing_update'),
  path('<int:pk>/delete', views.listing_delete, name='listing_delete'),
  path('dashboard/', views.dashboard, name='dashboard'),
  path('inquiries/<int:pk>/toggle-read/', views.toggle_inquiry_read, name='toggle_inquiry_read'),
  path('inquiries/<int:pk>/delete/', views.delete_inquiry, name='delete_inquiry'),


  path('', views.listing_list, name='listing_list'),
  path('dashboard/', views.dashboard, name='dashboard'),


  path('signup/', views.signup_view, name='signup'),
  path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
  path('logout/', auth_views.LogoutView.as_view(next_page='listing_list'), name='logout'),
  

  path('profile/edit/', views.profile_edit, name='profile_edit'),
  path('listing/<int:pk>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
  path('notifications/', views.notification_list, name='notification_list'),
  path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
  path('notifications/', views.notification_list, name='notification_list'),
  path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
  path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),

  #Admin login in view(admin login page) admin properties
  path('campus-admin/login/', views.admin_login_view, name='admin_login'),
  path('admin-panel/dashboard/', views.manage_categories, name='manage_categories'),
  path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
  path('admin-panel/listings/<int:listing_id>/delete/', views.admin_delete_listing, name='admin_delete_listing'),
]
